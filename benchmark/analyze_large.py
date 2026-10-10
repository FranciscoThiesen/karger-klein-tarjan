#!/usr/bin/env python3
"""Analyze one large-instance experiment without mixing earlier measurements.

Run with --repetitions 1 --warmups 0 for the large sweep. Analyze confirmation
runs separately with their actual counts. Hierarchical medians give graph seeds
equal weight; graph-level ranges are descriptive, not confidence intervals.
"""

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

import analyze_diverse as common
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, LogLocator
import numpy as np


ALGORITHMS = common.ALGORITHMS
GRAPH_SEEDS = common.GRAPH_SEEDS
KKT_SEEDS = common.KKT_SEEDS
PROFILES = ("random_4", "random_32", "random_128", "random_512", "hub", "star", "complete")
PROFILE_NAMES = {**common.PROFILE_NAMES, "random_512": "Random · m = 512n"}
LARGE_CASE_DIMENSIONS = {
    **{f"random_4_n{n}": (n, 4 * n) for n in (65536, 262144, 1048576)},
    **{f"random_32_n{n}": (n, 32 * n) for n in (65536, 262144, 1048576)},
    **{f"random_128_n{n}": (n, 128 * n) for n in (65536, 262144)},
    "random_512_n65536": (65536, 512 * 65536),
    **{f"hub_n{n}": (n, 4 * n) for n in (65536, 262144, 1048576)},
    **{f"star_n{n}": (n, n - 1) for n in (65536, 262144, 1048576)},
    **{f"complete_n{n}": (n, n * (n - 1) // 2) for n in (2048, 4096, 8192)},
}


def load_measurements(path, expected_cases, repetitions, warmups):
    observations = {}
    cases = {}
    with path.open(newline="") as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != common.FIELDS:
            raise ValueError("input CSV header does not match the benchmark schema")
        for line, raw in enumerate(reader, 2):
            if None in raw or any(value is None for value in raw.values()):
                raise ValueError(f"line {line}: malformed CSV record")
            if raw["validation"] != "pass":
                raise ValueError(f"line {line}: result did not pass validation")
            row = dict(raw)
            for field in common.INTEGER_FIELDS:
                try:
                    row[field] = int(raw[field])
                except ValueError as error:
                    raise ValueError(f"line {line}: invalid integer {field}") from error
            if row["n"] < 2 or row["m"] < row["n"] - 1 or row["elapsed_ns"] <= 0:
                raise ValueError(f"line {line}: invalid dimensions or nonpositive elapsed time")
            if row["graph_seed"] not in GRAPH_SEEDS or row["kkt_seed"] not in KKT_SEEDS:
                raise ValueError(f"line {line}: unexpected seed")
            if row["algorithm"] not in ALGORITHMS or row["repetition"] not in range(repetitions):
                raise ValueError(f"line {line}: unexpected algorithm or repetition")
            if row["warmups"] != warmups:
                raise ValueError(f"line {line}: expected {warmups} warmups, got {row['warmups']}")
            graph_index = GRAPH_SEEDS.index(row["graph_seed"])
            sampling_index = KKT_SEEDS.index(row["kkt_seed"])
            expected_order = (ALGORITHMS.index(row["algorithm"]) - row["repetition"] - graph_index - sampling_index) % 4
            if row["order"] != expected_order:
                raise ValueError(f"line {line}: execution order does not match the harness schedule")
            profile = common.profile_of(row["case_id"], row["n"])
            if profile not in PROFILES or row["family"] != profile:
                raise ValueError(f"line {line}: unexpected large-experiment profile or inconsistent family")
            expected_dimensions = LARGE_CASE_DIMENSIONS.get(row["case_id"])
            if expected_dimensions is None:
                raise ValueError(f"line {line}: case is not in the 18-case large preset: {row['case_id']}")
            if (row["n"], row["m"]) != expected_dimensions:
                raise ValueError(f"line {line}: {row['case_id']} requires n,m={expected_dimensions}, "
                                 f"got {(row['n'], row['m'])}")
            case = {"case_id": row["case_id"], "family": row["family"], "profile": profile, "n": row["n"], "m": row["m"]}
            if case["case_id"] in cases and cases[case["case_id"]] != case:
                raise ValueError(f"line {line}: inconsistent case metadata")
            cases[case["case_id"]] = case
            key = (row["case_id"], row["graph_seed"], row["kkt_seed"], row["repetition"], row["algorithm"])
            if key in observations:
                raise ValueError(f"line {line}: duplicate observation {key}")
            observations[key] = row
    if len(cases) != expected_cases:
        raise ValueError(f"expected {expected_cases} cases, got {len(cases)}")
    expected_rows = expected_cases * len(GRAPH_SEEDS) * len(KKT_SEEDS) * repetitions * len(ALGORITHMS)
    if len(observations) != expected_rows:
        raise ValueError(f"expected {expected_rows} observations, got {len(observations)}")
    for case_id in cases:
        for graph_seed in GRAPH_SEEDS:
            for sampling_seed in KKT_SEEDS:
                for repetition in range(repetitions):
                    orders = set()
                    for algorithm in ALGORITHMS:
                        key = (case_id, graph_seed, sampling_seed, repetition, algorithm)
                        if key not in observations:
                            raise ValueError(f"missing observation {key}")
                        orders.add(observations[key]["order"])
                    if orders != set(range(4)):
                        raise ValueError(f"nonunique execution positions in block {key[:-1]}")
    return observations, sorted(cases.values(), key=lambda case: (PROFILES.index(case["profile"]), case["n"]))


def configure_axes(axis, title, vertices):
    axis.set_xscale("log", base=2)
    axis.set_yscale("log")
    axis.set_xticks(vertices, [f"{n:,}" for n in vertices])
    if len(vertices) == 1:
        axis.set_xlim(vertices[0] / 1.25, vertices[0] * 1.25)
    axis.minorticks_off()
    axis.set_xlabel("Vertices n", fontsize=9)
    axis.set_title(title, loc="left", fontsize=11, fontweight="bold", pad=10)
    common.style_axis(axis)
    axis.tick_params(axis="x", labelsize=8)


def error_array(records, center, minimum, maximum):
    return np.array([[row[center] - row[minimum] for row in records], [row[maximum] - row[center] for row in records]])


def plot_scaling(cases, summary, output_dir):
    profiles = list(dict.fromkeys(case["profile"] for case in cases))
    columns = min(3, len(profiles))
    rows_count = math.ceil(len(profiles) / columns)
    figure, axes = plt.subplots(rows_count, columns, figsize=(15.0, rows_count * 3.55), squeeze=False)
    lookup = {(row["case_id"], row["algorithm"]): row for row in summary}
    handles = []
    for index, profile in enumerate(profiles):
        axis = axes.flat[index]
        selected = [case for case in cases if case["profile"] == profile]
        vertices = [case["n"] for case in selected]
        for algorithm in ALGORITHMS:
            records = [lookup[(case["case_id"], algorithm)] for case in selected]
            handle = axis.errorbar(vertices, [row["median_ms"] for row in records],
                                   yerr=error_array(records, "median_ms", "graph_min_ms", "graph_max_ms"),
                                   color=common.COLORS[algorithm], marker=common.MARKERS[algorithm],
                                   linewidth=2.3 if algorithm == "kkt" else 1.7, markersize=5, capsize=3)
            if index == 0:
                handles.append(handle)
        configure_axes(axis, PROFILE_NAMES[profile], vertices)
        axis.set_ylabel("Runtime (ms)", fontsize=9)
    for axis in list(axes.flat)[len(profiles):]:
        axis.set_visible(False)
    figure.suptitle("Large instances: measured runtime", x=0.055, ha="left", fontsize=19, fontweight="bold", y=1.10 if rows_count == 1 else 1.005)
    figure.legend(handles, [common.ALGORITHM_NAMES[a] for a in ALGORITHMS], loc="upper left", bbox_to_anchor=(0.05, 1.005 if rows_count == 1 else 0.98), ncol=4, frameon=False)
    figure.text(0.055, 0.01, "Current input file only. Logarithmic axes; independent panel scales. Points: hierarchical medians. Bars: range of three graph-level medians, not confidence intervals.", fontsize=8.5, color="#52616D")
    figure.tight_layout(rect=(0.015, 0.045, 1, 0.95), h_pad=2.3, w_pad=2.2)
    common.save_figure(figure, output_dir, "large_scaling")


def plot_ratios(cases, comparisons, output_dir):
    profiles = list(dict.fromkeys(case["profile"] for case in cases))
    columns = min(3, len(profiles))
    rows_count = math.ceil(len(profiles) / columns)
    figure, axes = plt.subplots(rows_count, columns, figsize=(15.0, rows_count * 3.55), squeeze=False)
    lookup = {(row["case_id"], row["reference"]): row for row in comparisons if row["algorithm"] == "kkt"}
    handles = []
    for index, profile in enumerate(profiles):
        axis = axes.flat[index]
        selected = [case for case in cases if case["profile"] == profile]
        vertices = [case["n"] for case in selected]
        for baseline in ALGORITHMS[1:]:
            records = [lookup[(case["case_id"], baseline)] for case in selected]
            handle = axis.errorbar(vertices, [row["paired_runtime_ratio"] for row in records],
                                   yerr=error_array(records, "paired_runtime_ratio", "graph_min_ratio", "graph_max_ratio"),
                                   color=common.COLORS[baseline], marker=common.MARKERS[baseline], linewidth=1.9, markersize=5, capsize=3)
            if index == 0:
                handles.append(handle)
        axis.axhline(1, color="#17232E", linewidth=1, linestyle="--")
        configure_axes(axis, PROFILE_NAMES[profile], vertices)
        axis.yaxis.set_major_locator(LogLocator(base=2))
        axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: common.ratio_label(value)))
        axis.set_ylabel("KKT runtime / baseline runtime", fontsize=9)
    for axis in list(axes.flat)[len(profiles):]:
        axis.set_visible(False)
    figure.suptitle("Does KKT overtake the other implementations?", x=0.055, ha="left", fontsize=19, fontweight="bold", y=1.10 if rows_count == 1 else 1.005)
    figure.legend(handles, [f"KKT / {common.ALGORITHM_NAMES[a]}" for a in ALGORITHMS[1:]], loc="upper left", bbox_to_anchor=(0.05, 1.005 if rows_count == 1 else 0.98), ncol=3, frameon=False)
    figure.text(0.055, 0.01, "Below 1×: KKT faster. Paired hierarchical medians; bars span graph-level medians. Lines join measured sizes and do not establish an unmeasured crossover.", fontsize=8.5, color="#52616D")
    figure.tight_layout(rect=(0.015, 0.045, 1, 0.95), h_pad=2.3, w_pad=2.2)
    common.save_figure(figure, output_dir, "large_ratios")


def plot_density(cases, comparisons, output_dir):
    selected = [case for case in cases if re.fullmatch(r"random_\d+", case["profile"])]
    if not selected:
        return False
    sizes = sorted({case["n"] for case in selected})
    columns = min(3, len(sizes))
    rows_count = math.ceil(len(sizes) / columns)
    figure, axes = plt.subplots(rows_count, columns, figsize=(15.0, rows_count * 4.2), squeeze=False)
    lookup = {(row["case_id"], row["reference"]): row for row in comparisons if row["algorithm"] == "kkt"}
    handles = []
    for index, n in enumerate(sizes):
        axis = axes.flat[index]
        by_density = sorted((case for case in selected if case["n"] == n), key=lambda case: case["m"])
        x = [case["m"] / case["n"] for case in by_density]
        for baseline in ALGORITHMS[1:]:
            records = [lookup[(case["case_id"], baseline)] for case in by_density]
            handle = axis.errorbar(x, [row["paired_runtime_ratio"] for row in records],
                                   yerr=error_array(records, "paired_runtime_ratio", "graph_min_ratio", "graph_max_ratio"),
                                   color=common.COLORS[baseline], marker=common.MARKERS[baseline], linewidth=1.9, markersize=5, capsize=3)
            if index == 0:
                handles.append(handle)
        axis.axhline(1, color="#17232E", linewidth=1, linestyle="--")
        axis.set_xscale("log", base=2)
        axis.set_yscale("log")
        axis.set_xticks(x, [f"{value:g}" for value in x])
        if len(x) == 1:
            axis.set_xlim(x[0] / 1.25, x[0] * 1.25)
        axis.minorticks_off()
        axis.yaxis.set_major_locator(LogLocator(base=2))
        axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: common.ratio_label(value)))
        axis.set_xlabel("Edges per vertex (m/n)", fontsize=10)
        axis.set_ylabel("KKT runtime / baseline runtime", fontsize=10)
        axis.set_title(f"n = {n:,}", loc="left", fontsize=12, fontweight="bold")
        common.style_axis(axis)
    for axis in list(axes.flat)[len(sizes):]:
        axis.set_visible(False)
    figure.suptitle("Density changes at fixed vertex counts", x=0.055, ha="left", fontsize=19, fontweight="bold", y=1.055)
    figure.legend(handles, [f"KKT / {common.ALGORITHM_NAMES[a]}" for a in ALGORITHMS[1:]], loc="upper left", bbox_to_anchor=(0.05, 1.015), ncol=3, frameon=False)
    figure.text(0.055, -0.015, "Below 1×: KKT faster. Every panel holds n fixed. Ratios and graph-level ranges use only this experiment; no older observations are added.", fontsize=9, color="#52616D")
    figure.tight_layout(rect=(0.015, 0.065, 1, 0.91), h_pad=2.3)
    common.save_figure(figure, output_dir, "density")
    return True


def write_report(output_dir, source, cases, summary, comparisons, repetitions, warmups, density_plot):
    ratio_ranges = {}
    wins = {}
    slower = {}
    for baseline in ALGORITHMS[1:]:
        selected = [row for row in comparisons if row["algorithm"] == "kkt" and row["reference"] == baseline]
        ratio_ranges[baseline] = [min(row["paired_runtime_ratio"] for row in selected), max(row["paired_runtime_ratio"] for row in selected)]
        wins[baseline] = sum(row["paired_runtime_ratio"] < 1 for row in selected)
        slower[baseline] = [row["case_id"] for row in selected if row["paired_runtime_ratio"] > 1]
    runtimes = {(row["case_id"], row["algorithm"]): row["median_ms"] for row in summary}
    fastest = {case["case_id"]: min(ALGORITHMS, key=lambda algorithm: runtimes[(case["case_id"], algorithm)]) for case in cases}
    winning_all = [case["case_id"] for case in cases if all(
        next(row["paired_runtime_ratio"] for row in comparisons if row["case_id"] == case["case_id"] and row["algorithm"] == "kkt" and row["reference"] == baseline) < 1
        for baseline in ALGORITHMS[1:]
    )]
    phase = "exploratory sweep" if repetitions == 1 else "repeated measurement"
    data = {
        "input_csv": str(source.resolve()), "measurement_type": phase,
        "case_count": len(cases), "observation_count": len(cases) * 9 * repetitions * 4,
        "graph_seeds": list(GRAPH_SEEDS), "kkt_seeds": list(KKT_SEEDS),
        "repetitions_per_seed_pair": repetitions, "warmups": warmups,
        "aggregation": common.AGGREGATION,
        "kkt_cases_faster_by_paired_hierarchical_median": wins,
        "kkt_cases_slower": slower, "kkt_runtime_ratio_ranges": ratio_ranges,
        "fastest_by_hierarchical_runtime_median": fastest,
        "fastest_case_counts": dict(Counter(fastest.values())),
        "kkt_faster_than_all_three_by_paired_medians": winning_all,
    }
    (output_dir / "analysis.json").write_text(json.dumps(data, indent=2) + "\n")
    lines = ["# Large-instance benchmark analysis", "",
             f"This **{phase}** contains {len(cases)} cases and {data['observation_count']:,} validated timed observations. "
             f"Each case has three graph seeds, three KKT seeds, {repetitions} measured repetition(s) per seed pair, and {warmups} warmup(s) per algorithm/seed pair.", "",
             "| Baseline | Cases where KKT has lower paired median | KKT / baseline runtime range |",
             "| --- | ---: | ---: |"]
    for baseline in ALGORITHMS[1:]:
        lower, upper = ratio_ranges[baseline]
        lines.append(f"| {common.ALGORITHM_NAMES[baseline]} | {wins[baseline]}/{len(cases)} | {lower:.3f}–{upper:.3f}× |")
    lines.extend(["", "Lower ratios are better for KKT. Ratios are aggregated from matched timings, not calculated by dividing the displayed aggregate runtimes.", "",
                  "KKT is below all three baselines by paired hierarchical medians in: " + (", ".join(f"`{case}`" for case in winning_all) or "none of these cases") + ".", "",
                  "Case counts refer only to the chosen matrix, not a workload-weighted ranking or a claim of statistical significance.", "", "## Aggregation and interpretation", "", common.AGGREGATION])
    if repetitions == 1:
        lines.extend(["", "**There is only one timing per graph/KKT-seed pair.** The graph and KKT seeds vary, but within-pair repeatability is unmeasured. "
                      "Close races require a separate repeated run; this sweep alone does not confirm a crossover. "
                      "The nine trial blocks do not give every algorithm exactly the same number of appearances in every timed position, although the schedule rotates positions across graph/sampling seeds."])
    else:
        lines.extend(["", "Repeated observations measure within-pair variation, but only three graph seeds contribute to each case. "
                      "If the repetition count is a multiple of four, each algorithm occupies all four timed positions equally within every seed pair. "
                      "Graph-level ranges remain descriptive and are not confidence intervals."])
    if warmups == 0:
        lines.extend(["", "There are no dedicated warmups. Fixture construction and certified-reference computation precede timing, so these are not controlled cold-cache measurements. "
                      "The Kruskal reference call may affect cache/allocator state. Rotation limits systematic order effects but cannot remove them."])
    lines.extend(["", "Deterministic baselines ignore the KKT-seed label; those observations are repeated timings of the same graph. "
                  "Fixed topologies can vary only through labels, weights, or input order. "
                  "Matched ratios align fixture/seed/trial blocks, not simultaneous execution or machine state.", "",
                  "Only observations from the supplied CSV are used. Earlier experiments and separate confirmation runs are never mixed automatically. "
                  "A density sweep holds vertex count fixed; a size sweep holds the profile's edge/vertex ratio fixed where applicable. "
                  "Complete graphs increase both vertex count and density. Lines connect measured points and do not establish an unmeasured crossover or an asymptotic bound.", "",
                  "## Timing boundary", "",
                  "All algorithms start from the same tuple edge list. KKT's problem conversion and temporary-input destruction are included, as are the baselines' internal preparation and all return-value construction. "
                  "Fixture generation, certified-reference computation, output checking, CSV writing, and returned-output destruction are excluded. "
                  "Outputs retain native representations: an ID hash set for KKT and edge vectors for the other implementations.", "",
                  "These results compare the repository implementations on the measured machine. Desktop scheduling, memory/cache behavior, allocator state, and power/thermal state remain possible influences. "
                  "Nanosecond clock units are not a guarantee of nanosecond accuracy.", "", "## Artifacts", "",
                  "- `summary.csv`: per-case/algorithm hierarchical runtime medians, graph-level ranges, and relative Kruskal timings.",
                  "- `graph_summary.csv`: all graph-level summaries.",
                  "- `comparisons.csv`: paired ratios against every baseline and individual loss counts.",
                  "- `large_scaling.{png,svg,pdf}`: runtime by size and profile.",
                  "- `large_ratios.{png,svg,pdf}`: KKT/baseline ratios, with the 1× crossing marked."])
    if density_plot:
        lines.append("- `density.{png,svg,pdf}`: ratios at fixed vertex counts as density changes.")
    lines.extend(["", "## Retained KKT losses", ""])
    for baseline in ALGORITHMS[1:]:
        lines.append(f"**{common.ALGORITHM_NAMES[baseline]}:** " + (", ".join(f"`{case}`" for case in slower[baseline]) or "None in this input.") + "\n")
    (output_dir / "report.md").write_text("\n".join(lines).rstrip() + "\n")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--expected-cases", required=True, type=int)
    parser.add_argument("--repetitions", default=1, type=int)
    parser.add_argument("--warmups", default=0, type=int)
    args = parser.parse_args()
    try:
        if args.expected_cases <= 0 or args.repetitions <= 0 or args.warmups < 0:
            raise ValueError("case/repetition counts must be positive and warmups nonnegative")
        for filename in ("summary.csv", "graph_summary.csv", "comparisons.csv"):
            if args.input.resolve() == (args.output_dir / filename).resolve():
                raise ValueError("output must not overwrite raw input")
        observations, cases = load_measurements(args.input, args.expected_cases, args.repetitions, args.warmups)
        summary, graphs, comparisons = common.aggregate(observations, cases, args.repetitions)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        common.write_csv(args.output_dir / "summary.csv", summary)
        common.write_csv(args.output_dir / "graph_summary.csv", graphs)
        common.write_csv(args.output_dir / "comparisons.csv", comparisons)
        plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.labelcolor": "#263541", "text.color": "#17232E", "svg.fonttype": "none", "pdf.fonttype": 42})
        plot_scaling(cases, summary, args.output_dir)
        plot_ratios(cases, comparisons, args.output_dir)
        density_plot = plot_density(cases, comparisons, args.output_dir)
        data = write_report(args.output_dir, args.input, cases, summary, comparisons, args.repetitions, args.warmups, density_plot)
        print(f"Validated {len(observations):,} observations in {len(cases)} cases; wrote {args.output_dir}")
        for baseline in ALGORITHMS[1:]:
            lower, upper = data["kkt_runtime_ratio_ranges"][baseline]
            print(f"KKT / {common.ALGORITHM_NAMES[baseline]}: {lower:.3f}–{upper:.3f}×; lower paired median in {data['kkt_cases_faster_by_paired_hierarchical_median'][baseline]}/{len(cases)} cases")
    except (OSError, ValueError) as error:
        print(f"analysis error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
