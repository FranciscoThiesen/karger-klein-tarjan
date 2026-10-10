#!/usr/bin/env python3
"""Validate and plot the four-algorithm diverse-graph benchmark.

Aggregation gives each graph seed equal weight: median over repetitions, then
median over KKT sampling seeds within each graph, then median over graph seeds.
Ratios use matched algorithm/reference timing ratios with the same hierarchy.
Error bars span the three graph-level medians; they are not confidence intervals.
"""

import argparse
import csv
import json
import math
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.ticker import FuncFormatter, LogLocator
import numpy as np


ALGORITHMS = ("kkt", "kruskal", "prim", "boruvka")
ALGORITHM_NAMES = {"kkt": "KKT", "kruskal": "Kruskal", "prim": "Prim", "boruvka": "Borůvka"}
COLORS = {"kkt": "#7437A5", "kruskal": "#2774AE", "prim": "#087F75", "boruvka": "#D07916"}
MARKERS = {"kkt": "o", "kruskal": "s", "prim": "^", "boruvka": "D"}
GRAPH_SEEDS = (17, 42, 999)
KKT_SEEDS = (0, 1, 7)
PROFILES = (
    "random_4", "random_32", "random_128", "random_dense_anchor", "grid",
    "geometric_grid", "hub", "clustered", "planted_tree", "random_tree",
    "star", "hierarchical_path", "complete",
)
PROFILE_NAMES = {
    "random_4": "Random · m = 4n", "random_32": "Random · m = 32n",
    "random_128": "Random · m = 128n", "random_dense_anchor": "Dense random anchor",
    "grid": "Grid", "geometric_grid": "Geometric grid", "hub": "Hub",
    "clustered": "Clustered", "planted_tree": "Planted tree",
    "random_tree": "Random tree", "star": "Star",
    "hierarchical_path": "Hierarchical path", "complete": "Complete graph",
}
FIELDS = (
    "case_id", "family", "n", "m", "graph_seed", "kkt_seed", "repetition",
    "order", "warmups", "algorithm", "elapsed_ns", "validation",
)
INTEGER_FIELDS = ("n", "m", "graph_seed", "kkt_seed", "repetition", "order", "warmups", "elapsed_ns")
AGGREGATION = (
    "Median of repetitions for each graph/sampling-seed pair; median of the three "
    "sampling-seed values per graph; median of the three graph values. Paired ratios "
    "apply the same hierarchy to matched algorithm/reference elapsed-time ratios. "
    "Error bars span graph-level medians and are not confidence intervals."
)


def profile_of(case_id, n):
    suffix = f"_n{n}"
    if not case_id.endswith(suffix):
        raise ValueError(f"case_id must end in {suffix}: {case_id}")
    return case_id[:-len(suffix)]


def case_sort_key(case):
    profile = case["profile"]
    return (PROFILES.index(profile) if profile in PROFILES else len(PROFILES), profile, case["n"], case["m"])


def load_measurements(path, expected_cases, repetitions):
    rows = {}
    cases = {}
    warmup_counts = set()
    with path.open(newline="") as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError("input CSV header does not match the diverse benchmark schema")
        for line, raw in enumerate(reader, 2):
            if None in raw or any(value is None for value in raw.values()):
                raise ValueError(f"line {line}: malformed CSV record")
            if raw["validation"] != "pass":
                raise ValueError(f"line {line}: measured result did not pass validation")
            row = dict(raw)
            for field in INTEGER_FIELDS:
                try:
                    row[field] = int(raw[field])
                except ValueError as error:
                    raise ValueError(f"line {line}: {field} is not an integer") from error
            if row["n"] < 2 or row["m"] < row["n"] - 1 or row["elapsed_ns"] <= 0:
                raise ValueError(f"line {line}: invalid graph dimensions or nonpositive elapsed time")
            if row["algorithm"] not in ALGORITHMS or row["order"] not in range(4):
                raise ValueError(f"line {line}: invalid algorithm or execution order")
            if row["graph_seed"] not in GRAPH_SEEDS or row["kkt_seed"] not in KKT_SEEDS:
                raise ValueError(f"line {line}: unexpected graph or KKT seed")
            if row["repetition"] not in range(repetitions) or row["warmups"] < 0:
                raise ValueError(f"line {line}: unexpected repetition or warmup count")
            warmup_counts.add(row["warmups"])
            case = {
                "case_id": row["case_id"], "family": row["family"],
                "profile": profile_of(row["case_id"], row["n"]), "n": row["n"], "m": row["m"],
            }
            if case["case_id"] in cases and cases[case["case_id"]] != case:
                raise ValueError(f"line {line}: inconsistent metadata for {case['case_id']}")
            cases[case["case_id"]] = case
            key = (row["case_id"], row["graph_seed"], row["kkt_seed"], row["repetition"], row["algorithm"])
            if key in rows:
                raise ValueError(f"line {line}: duplicate observation {key}")
            rows[key] = row
    if len(cases) != expected_cases:
        raise ValueError(f"expected {expected_cases} complete cases, got {len(cases)}")
    expected_rows = expected_cases * len(GRAPH_SEEDS) * len(KKT_SEEDS) * repetitions * len(ALGORITHMS)
    if len(rows) != expected_rows:
        raise ValueError(f"expected {expected_rows} observations, got {len(rows)}")
    if len(warmup_counts) != 1:
        raise ValueError("warmup counts differ across observations")
    for case_id in cases:
        for graph_seed in GRAPH_SEEDS:
            for sampling_seed in KKT_SEEDS:
                positions = {algorithm: Counter() for algorithm in ALGORITHMS}
                for repetition in range(repetitions):
                    block = []
                    for algorithm in ALGORITHMS:
                        key = (case_id, graph_seed, sampling_seed, repetition, algorithm)
                        if key not in rows:
                            raise ValueError(f"missing observation {key}")
                        row = rows[key]
                        block.append(row)
                        positions[algorithm][row["order"]] += 1
                    if {row["order"] for row in block} != set(range(4)):
                        raise ValueError(f"execution positions are not unique in block {key[:-1]}")
                expected_positions = Counter({position: repetitions // 4 for position in range(4)})
                if any(counts != expected_positions for counts in positions.values()):
                    raise ValueError(f"unbalanced algorithm order for {case_id}/{graph_seed}/{sampling_seed}")
    return rows, sorted(cases.values(), key=case_sort_key), warmup_counts.pop()


def graph_values(rows, case_id, algorithm, repetitions, reference=None):
    values = []
    for graph_seed in GRAPH_SEEDS:
        sample_values = []
        for sampling_seed in KKT_SEEDS:
            repeated = []
            for repetition in range(repetitions):
                prefix = (case_id, graph_seed, sampling_seed, repetition)
                value = rows[prefix + (algorithm,)]["elapsed_ns"]
                if reference:
                    value /= rows[prefix + (reference,)]["elapsed_ns"]
                else:
                    value /= 1e6
                repeated.append(value)
            sample_values.append(statistics.median(repeated))
        values.append(statistics.median(sample_values))
    return values


def aggregate(rows, cases, repetitions):
    summaries = []
    graphs = []
    comparisons = []
    for case in cases:
        case_id = case["case_id"]
        for algorithm in ALGORITHMS:
            elapsed = graph_values(rows, case_id, algorithm, repetitions)
            ratios = graph_values(rows, case_id, algorithm, repetitions, "kruskal")
            summaries.append({
                **case, "algorithm": algorithm, "graph_count": len(GRAPH_SEEDS),
                "sampling_seeds_per_graph": len(KKT_SEEDS), "repetitions_per_seed_pair": repetitions,
                "observations": len(GRAPH_SEEDS) * len(KKT_SEEDS) * repetitions,
                "edges_per_vertex": case["m"] / case["n"],
                "median_ms": statistics.median(elapsed), "graph_min_ms": min(elapsed), "graph_max_ms": max(elapsed),
                "relative_to_kruskal": statistics.median(ratios),
                "relative_to_kruskal_graph_min": min(ratios), "relative_to_kruskal_graph_max": max(ratios),
            })
            for graph_seed, milliseconds, ratio in zip(GRAPH_SEEDS, elapsed, ratios):
                graphs.append({
                    **case, "algorithm": algorithm, "graph_seed": graph_seed,
                    "median_ms": milliseconds, "relative_to_kruskal": ratio,
                })
            for reference in ALGORITHMS:
                matched = graph_values(rows, case_id, algorithm, repetitions, reference)
                individual = [
                    row["elapsed_ns"] / rows[key[:-1] + (reference,)]["elapsed_ns"]
                    for key, row in rows.items() if key[0] == case_id and key[-1] == algorithm
                ]
                comparisons.append({
                    **case, "algorithm": algorithm, "reference": reference,
                    "paired_runtime_ratio": statistics.median(matched),
                    "graph_min_ratio": min(matched), "graph_max_ratio": max(matched),
                    "slower_observations": sum(value > 1 for value in individual),
                    "equal_observations": sum(value == 1 for value in individual),
                    "paired_observations": len(individual),
                })
    return summaries, graphs, comparisons


def write_csv(path, rows):
    with path.open("w", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def save_figure(figure, output_dir, name):
    for extension in ("png", "svg", "pdf"):
        destination = output_dir / f"{name}.{extension}"
        figure.savefig(destination, dpi=190, bbox_inches="tight", facecolor="white")
        if extension == "svg":
            # Matplotlib's path data contains trailing spaces before newlines.
            # Normalize those without changing the SVG's whitespace separators.
            destination.write_text("\n".join(line.rstrip() for line in destination.read_text().splitlines()) + "\n")
    plt.close(figure)


def style_axis(axis):
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(True, which="major", color="#DCE2E8", linewidth=0.7, alpha=0.85)
    axis.set_axisbelow(True)
    axis.tick_params(labelsize=9)


def ratio_label(value):
    if value >= 100:
        return f"{value:.0f}×"
    if value >= 10:
        return f"{value:.1f}×"
    return f"{value:.2f}×"


def plot_heatmap(cases, summaries, output_dir):
    lookup = {(row["case_id"], row["algorithm"]): row for row in summaries}
    values = np.array([[lookup[(case["case_id"], algorithm)]["relative_to_kruskal"] for algorithm in ALGORITHMS] for case in cases])
    logged = np.log2(values)
    limit = max(1.0, float(np.max(np.abs(logged))))
    figure, axis = plt.subplots(figsize=(10.8, max(6.0, len(cases) * 0.34 + 2.4)))
    rendered = axis.imshow(logged, cmap="RdBu_r", norm=TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit), aspect="auto")
    axis.set_xticks(range(4), [ALGORITHM_NAMES[algorithm] for algorithm in ALGORITHMS], fontsize=11)
    axis.xaxis.tick_top()
    axis.tick_params(axis="both", length=0)
    labels = [f"{PROFILE_NAMES.get(case['profile'], case['profile'])}   ·   n = {case['n']:,}" for case in cases]
    axis.set_yticks(range(len(cases)), labels, fontsize=9)
    for index, case in enumerate(cases):
        for column in range(4):
            color = "white" if abs(logged[index, column]) > limit * 0.55 else "#17232E"
            axis.text(column, index, ratio_label(values[index, column]), ha="center", va="center", fontsize=9, color=color)
        if index and case["profile"] != cases[index - 1]["profile"]:
            axis.axhline(index - 0.5, color="white", linewidth=2.3)
    for spine in axis.spines.values():
        spine.set_visible(False)
    colorbar = figure.colorbar(rendered, ax=axis, pad=0.035, fraction=0.045)
    exponents = sorted(set([0] + list(range(-int(limit), int(limit) + 1, max(1, math.ceil(limit / 3))))))
    colorbar.set_ticks(exponents)
    colorbar.set_ticklabels([ratio_label(2.0 ** exponent) for exponent in exponents])
    colorbar.set_label("Runtime / Kruskal runtime · logarithmic color scale", fontsize=10, labelpad=11)
    figure.suptitle("MST runtime relative to Kruskal", x=0.02, ha="left", fontsize=19, fontweight="bold", y=1.015)
    figure.text(0.02, 0.994, "Lower is faster  ·  blue < 1×  ·  red > 1×  ·  all measured cases retained", fontsize=10, color="#52616D")
    figure.text(0.02, -0.015, "Paired ratios: median over repetitions → sampling seeds → graph seeds. No confidence intervals.", fontsize=9, color="#52616D")
    figure.tight_layout(rect=(0, 0.02, 1, 0.975))
    save_figure(figure, output_dir, "relative_runtime")


def compact_vertices(value):
    return f"{value:,}"


def plot_family_scaling(cases, summaries, output_dir):
    profiles = list(dict.fromkeys(case["profile"] for case in cases))
    columns = 3
    rows_count = math.ceil(len(profiles) / columns)
    figure, axes = plt.subplots(rows_count, columns, figsize=(15.0, rows_count * 3.05), squeeze=False)
    lookup = {(row["case_id"], row["algorithm"]): row for row in summaries}
    legend_handles = []
    for index, profile in enumerate(profiles):
        axis = axes.flat[index]
        selected = [case for case in cases if case["profile"] == profile]
        for algorithm in ALGORITHMS:
            records = [lookup[(case["case_id"], algorithm)] for case in selected]
            x = np.array([row["n"] for row in records])
            y = np.array([row["median_ms"] for row in records])
            errors = np.array([[row["median_ms"] - row["graph_min_ms"] for row in records], [row["graph_max_ms"] - row["median_ms"] for row in records]])
            line = axis.errorbar(x, y, yerr=errors, color=COLORS[algorithm], marker=MARKERS[algorithm],
                                 linewidth=2.3 if algorithm == "kkt" else 1.7, markersize=5,
                                 capsize=3, label=ALGORITHM_NAMES[algorithm])
            if index == 0:
                legend_handles.append(line)
        axis.set_xscale("log", base=2)
        axis.set_yscale("log")
        axis.set_xticks([case["n"] for case in selected], [compact_vertices(case["n"]) for case in selected])
        if len(selected) == 1:
            axis.set_xlim(selected[0]["n"] / 1.25, selected[0]["n"] * 1.25)
        axis.minorticks_off()
        axis.set_xlabel("Vertices n", fontsize=9)
        axis.set_ylabel("Runtime (ms)", fontsize=9)
        axis.set_title(PROFILE_NAMES.get(profile, profile), loc="left", fontsize=11, fontweight="bold", pad=10)
        style_axis(axis)
    for axis in list(axes.flat)[len(profiles):]:
        axis.set_visible(False)
    figure.suptitle("How runtime changes with graph size and structure", x=0.055, ha="left", fontsize=19, fontweight="bold", y=0.997)
    figure.legend(handles=legend_handles, labels=[ALGORITHM_NAMES[algorithm] for algorithm in ALGORITHMS],
                  loc="upper left", bbox_to_anchor=(0.055, 0.98), ncol=4, frameon=False)
    figure.text(0.055, 0.012, "Logarithmic axes; independent panel scales. Points: hierarchical medians. Bars: min/max across three graph-level medians, not confidence intervals.", fontsize=9, color="#52616D")
    figure.tight_layout(rect=(0.02, 0.035, 1, 0.955), h_pad=2.2, w_pad=2.0)
    save_figure(figure, output_dir, "runtime_by_family")


def plot_density(cases, comparisons, output_dir):
    selected = [case for case in cases if re.fullmatch(r"random_(4|32|128)", case["profile"])]
    if not selected:
        return False
    sizes = sorted({case["n"] for case in selected})
    columns = min(2, len(sizes))
    figure, axes = plt.subplots(math.ceil(len(sizes) / columns), columns,
                               figsize=(12.0, math.ceil(len(sizes) / columns) * 3.8), squeeze=False)
    lookup = {(row["case_id"], row["algorithm"], row["reference"]): row for row in comparisons}
    handles = []
    for index, n in enumerate(sizes):
        axis = axes.flat[index]
        by_density = sorted((case for case in selected if case["n"] == n), key=lambda case: case["m"] / case["n"])
        for reference in ALGORITHMS[1:]:
            records = [lookup[(case["case_id"], "kkt", reference)] for case in by_density]
            x = [case["m"] / case["n"] for case in by_density]
            y = np.array([row["paired_runtime_ratio"] for row in records])
            errors = np.array([[row["paired_runtime_ratio"] - row["graph_min_ratio"] for row in records], [row["graph_max_ratio"] - row["paired_runtime_ratio"] for row in records]])
            line = axis.errorbar(x, y, yerr=errors, label=f"KKT / {ALGORITHM_NAMES[reference]}",
                                 color=COLORS[reference], marker=MARKERS[reference], linewidth=1.9, capsize=3, markersize=5)
            if index == 0:
                handles.append(line)
        axis.axhline(1, color="#17232E", linewidth=1.1, linestyle="--")
        axis.set_xscale("log", base=2)
        axis.set_yscale("log")
        densities = sorted({case["m"] / case["n"] for case in by_density})
        axis.set_xticks(densities, [f"{value:g}" for value in densities])
        axis.minorticks_off()
        axis.yaxis.set_major_locator(LogLocator(base=2))
        axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: ratio_label(value)))
        axis.set_xlabel("Edges per vertex (m/n)", fontsize=10)
        axis.set_ylabel("KKT runtime / baseline runtime", fontsize=10)
        axis.set_title(f"n = {n:,}", loc="left", fontsize=12, fontweight="bold")
        style_axis(axis)
    for axis in list(axes.flat)[len(sizes):]:
        axis.set_visible(False)
    figure.suptitle("Where graph density changes the comparison", x=0.055, ha="left", fontsize=18, fontweight="bold", y=1.01)
    figure.legend(handles=handles, labels=[f"KKT / {ALGORITHM_NAMES[algorithm]}" for algorithm in ALGORITHMS[1:]],
                  loc="upper left", bbox_to_anchor=(0.05, 0.984), ncol=3, frameon=False)
    figure.text(0.055, 0.01, "Below 1×: KKT faster. Lines only connect measured densities; they do not establish a crossover threshold. Bars span graph-level paired medians.", fontsize=8.8, color="#52616D")
    figure.tight_layout(rect=(0.015, 0.045, 1, 0.94), h_pad=2.4)
    save_figure(figure, output_dir, "density_comparison")
    return True


def write_report(output_dir, source, cases, summaries, comparisons, repetitions, warmups, density_plot):
    wins = {}
    losses = {}
    ranges = {}
    for reference in ALGORITHMS[1:]:
        relevant = [row for row in comparisons if row["algorithm"] == "kkt" and row["reference"] == reference]
        wins[reference] = sum(row["paired_runtime_ratio"] < 1 for row in relevant)
        losses[reference] = [row["case_id"] for row in relevant if row["paired_runtime_ratio"] > 1]
        ranges[reference] = [min(row["paired_runtime_ratio"] for row in relevant), max(row["paired_runtime_ratio"] for row in relevant)]
    data = {
        "input_csv": str(source.resolve()), "case_count": len(cases),
        "observation_count": len(cases) * 9 * repetitions * 4,
        "graph_seeds": list(GRAPH_SEEDS), "kkt_seeds": list(KKT_SEEDS),
        "repetitions_per_seed_pair": repetitions, "warmups": warmups, "aggregation": AGGREGATION,
        "kkt_cases_faster_by_paired_hierarchical_median": wins,
        "kkt_cases_slower": losses, "kkt_runtime_ratio_ranges": ranges,
    }
    (output_dir / "analysis.json").write_text(json.dumps(data, indent=2) + "\n")
    lines = [
        "# Diverse-graph benchmark analysis", "",
        f"Validated **{data['observation_count']:,} observations across {len(cases)} cases**. "
        "Every measured result passed; all graph/sample/repetition/algorithm cells and balanced execution positions are present.", "",
        "| Baseline | Cases where KKT is faster | KKT / baseline runtime range |",
        "| --- | ---: | ---: |",
    ]
    for reference in ALGORITHMS[1:]:
        lower, upper = ranges[reference]
        lines.append(f"| {ALGORITHM_NAMES[reference]} | {wins[reference]}/{len(cases)} | {lower:.3f}–{upper:.3f}× |")
    lines.extend([
        "", "Ratios below one favor KKT. Case counts describe this chosen matrix; they are not a weighted overall ranking or estimates of production workload frequency.",
        "", "## Aggregation", "", AGGREGATION,
        "", "Only three graph seeds contribute to each case. Sampling seeds and repeated timings do not create additional independent graphs. "
        "For deterministic topologies, graph seeds may vary weights or input order rather than topology. "
        "KKT seed labels have no effect on deterministic baselines. Paired ratios align workloads and trial blocks, not simultaneous machine state.",
        "", "## Timing and limits", "",
        "The harness times the common edge-list entry boundary, including KKT's conversion to its problem representation and each algorithm's internal preparation. "
        "Fixture generation, oracle work, validation, output, and return-value destruction are outside timing. "
        "The algorithms retain their native output representations: KKT returns an ID hash set; the others return edge vectors.",
        "", "Execution order is balanced, but desktop scheduling, cache state, allocator state, power, and temperature can still affect measurements. "
        "Graph-level min/max bars describe the observed spread and are not confidence intervals. "
        "Nanosecond clock units do not imply nanosecond measurement accuracy. "
        "Results compare these implementations and synthetic fixtures on the measured machine; they do not prove asymptotic complexity or locate unmeasured crossover thresholds.",
        "", "## Files", "",
        "- `summary.csv`: one row per case/algorithm, with hierarchical runtime medians and graph-level ranges.",
        "- `graph_summary.csv`: graph-level aggregates, preserving all three seeds.",
        "- `comparisons.csv`: matched runtime ratios against every baseline, including all slower observations.",
        "- `relative_runtime.{png,svg,pdf}`: every case relative to Kruskal; blue is faster, red is slower.",
        "- `runtime_by_family.{png,svg,pdf}`: scaling by graph family, with independent logarithmic panel scales.",
    ])
    if density_plot:
        lines.append("- `density_comparison.{png,svg,pdf}`: KKT's paired ratio against each baseline at measured random-graph densities.")
    lines.extend(["", "## Retained KKT losses", ""])
    for reference in ALGORITHMS[1:]:
        lines.append(f"**{ALGORITHM_NAMES[reference]}:** " + (", ".join(f"`{case_id}`" for case_id in losses[reference]) or "None in this matrix.") + "\n")
    (output_dir / "report.md").write_text("\n".join(lines).rstrip() + "\n")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="raw diverse-benchmark CSV")
    parser.add_argument("--output-dir", required=True, type=Path, help="destination for summaries and PNG/SVG/PDF plots")
    parser.add_argument("--expected-cases", type=int, default=39, help="complete case count; override only for an intentional smaller matrix")
    parser.add_argument("--repetitions", type=int, default=4, help="repetitions per seed pair; must be a positive multiple of four")
    args = parser.parse_args()
    try:
        if args.expected_cases <= 0 or args.repetitions <= 0 or args.repetitions % 4:
            raise ValueError("expected cases must be positive and repetitions must be a positive multiple of four")
        for filename in ("summary.csv", "graph_summary.csv", "comparisons.csv"):
            if args.input.resolve() == (args.output_dir / filename).resolve():
                raise ValueError("output must not overwrite the raw input CSV")
        rows, cases, warmups = load_measurements(args.input, args.expected_cases, args.repetitions)
        summaries, graphs, comparisons = aggregate(rows, cases, args.repetitions)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_csv(args.output_dir / "summary.csv", summaries)
        write_csv(args.output_dir / "graph_summary.csv", graphs)
        write_csv(args.output_dir / "comparisons.csv", comparisons)
        plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.labelcolor": "#263541", "text.color": "#17232E", "svg.fonttype": "none", "pdf.fonttype": 42})
        plot_heatmap(cases, summaries, args.output_dir)
        plot_family_scaling(cases, summaries, args.output_dir)
        density_plot = plot_density(cases, comparisons, args.output_dir)
        data = write_report(args.output_dir, args.input, cases, summaries, comparisons, args.repetitions, warmups, density_plot)
        print(f"Validated {len(rows):,} observations in {len(cases)} cases; wrote {args.output_dir}")
        for reference in ALGORITHMS[1:]:
            lower, upper = data["kkt_runtime_ratio_ranges"][reference]
            print(f"KKT / {ALGORITHM_NAMES[reference]}: {lower:.3f}–{upper:.3f}×; faster in {data['kkt_cases_faster_by_paired_hierarchical_median'][reference]}/{len(cases)} cases")
    except (OSError, ValueError) as error:
        print(f"analysis error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
