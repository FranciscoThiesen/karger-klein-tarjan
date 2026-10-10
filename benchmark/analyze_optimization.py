#!/usr/bin/env python3
"""Compare complete before/after KKT campaigns without dropping cases or losses.

The diverse pair requires all 39 cases, four repetitions, and one warmup.
An optional large pair requires all 18 cases, one repetition, and no warmups.
Each suite is analyzed separately. Matching trial labels aligns fixtures and
sampling seeds, not machine state or simultaneous observations.
"""

import argparse
import hashlib
import json
import math
import os
import statistics
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import quote

import analyze_diverse as common
import analyze_large as large
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.ticker import FuncFormatter
import numpy as np


AGGREGATION = (
    "Match by case, graph seed, KKT seed, repetition, and algorithm; divide final "
    "elapsed time by baseline elapsed time for each matched trial. Take the median "
    "over repetitions, then sampling seeds within each graph, then graph seeds. "
    "Final-run KKT/competitor ratios use the same hierarchy on contemporaneous "
    "four-algorithm trial blocks. Values below one favor final KKT for its "
    "before/after comparison or KKT versus its competitor. Graph ranges span "
    "three graph-level medians and are not confidence intervals."
)


def diverse_dimensions():
    result = {}
    for family in ("random_4", "random_32", "random_128", "grid", "geometric_grid",
                   "hub", "clustered", "planted_tree", "random_tree", "star", "hierarchical_path"):
        for n in (1024, 4096, 16384):
            if family.startswith("random_") and family != "random_tree":
                m = int(family.split("_")[1]) * n
            elif family == "grid":
                m = 2 * n - 2 * math.isqrt(n)
            elif family == "geometric_grid":
                m = 4 * n - 6 * math.isqrt(n) + 2
            elif family in ("hub", "planted_tree"):
                m = 4 * n
            elif family == "clustered":
                cluster_size = n // 16
                m = min(16 * n, 16 * cluster_size * (cluster_size - 1) // 4) + 15
            else:
                m = n - 1
            result[f"{family}_n{n}"] = (family, n, m)
    for n in (256, 512, 1024):
        result[f"complete_n{n}"] = ("complete", n, n * (n - 1) // 2)
    for density in (4, 32):
        result[f"random_{density}_n65536"] = (f"random_{density}", 65536, density * 65536)
    result["random_dense_anchor_n1000"] = ("random_dense_anchor", 1000, 400000)
    return result


def load_pair(suite, baseline_path, final_path):
    if suite == "diverse":
        repetitions, warmups = 4, 1
        baseline, baseline_cases, baseline_warmups = common.load_measurements(baseline_path, 39, repetitions)
        final, final_cases, final_warmups = common.load_measurements(final_path, 39, repetitions)
        if baseline_warmups != warmups or final_warmups != warmups:
            raise ValueError("the diverse campaign requires exactly one warmup in both phases")
        # The reusable diverse validator accepts arbitrary intentional subsets.
        # This campaign additionally pins its complete original 39-case matrix.
        expected = diverse_dimensions()
        for cases in (baseline_cases, final_cases):
            actual = {case["case_id"]: (case["family"], case["n"], case["m"]) for case in cases}
            if actual != expected:
                raise ValueError("diverse input differs from the complete original 39-case matrix")
    else:
        repetitions, warmups = 1, 0
        baseline, baseline_cases = large.load_measurements(baseline_path, 18, repetitions, warmups)
        final, final_cases = large.load_measurements(final_path, 18, repetitions, warmups)
    if baseline_cases != final_cases or baseline.keys() != final.keys():
        raise ValueError(f"{suite}: before/after case metadata or trial keys differ")
    for key, row in baseline.items():
        match = final[key]
        if any(row[field] != match[field] for field in common.FIELDS if field != "elapsed_ns"):
            raise ValueError(f"{suite}: before/after trial metadata differs for {key}")
        graph_index = common.GRAPH_SEEDS.index(row["graph_seed"])
        sample_index = common.KKT_SEEDS.index(row["kkt_seed"])
        expected_order = (common.ALGORITHMS.index(row["algorithm"]) - row["repetition"] - graph_index - sample_index) % 4
        if row["order"] != expected_order:
            raise ValueError(f"{suite}: trial order differs from the harness schedule for {key}")
    return {"suite": suite, "baseline_path": baseline_path, "final_path": final_path,
            "baseline": baseline, "final": final, "cases": baseline_cases,
            "repetitions": repetitions, "warmups": warmups}


def compare_pair(pair):
    suite, cases = pair["suite"], pair["cases"]
    baseline, final, repetitions = pair["baseline"], pair["final"], pair["repetitions"]
    phase_summaries, phase_graphs, phase_comparisons = [], [], []
    summaries_by_phase, comparisons_by_phase = {}, {}
    for phase, rows in (("baseline", baseline), ("final", final)):
        summaries, graphs, comparisons = common.aggregate(rows, cases, repetitions)
        phase_summaries.extend({"suite": suite, "phase": phase, **row} for row in summaries)
        phase_graphs.extend({"suite": suite, "phase": phase, **row} for row in graphs)
        phase_comparisons.extend({"suite": suite, "phase": phase, **row} for row in comparisons)
        summaries_by_phase[phase] = {(row["case_id"], row["algorithm"]): row for row in summaries}
        comparisons_by_phase[phase] = {(row["case_id"], row["algorithm"], row["reference"]): row for row in comparisons}

    changes, graph_changes, trials, assessments = [], [], [], []
    for case in cases:
        case_id = case["case_id"]
        for algorithm in common.ALGORITHMS:
            graph_values, individual = [], []
            for graph_seed in common.GRAPH_SEEDS:
                sample_values = []
                for sampling_seed in common.KKT_SEEDS:
                    repeated = []
                    for repetition in range(repetitions):
                        key = (case_id, graph_seed, sampling_seed, repetition, algorithm)
                        before, after = baseline[key], final[key]
                        ratio = after["elapsed_ns"] / before["elapsed_ns"]
                        repeated.append(ratio)
                        individual.append(ratio)
                        trials.append({"suite": suite, **case, "algorithm": algorithm,
                                       "graph_seed": graph_seed, "kkt_seed": sampling_seed,
                                       "repetition": repetition, "order": after["order"], "warmups": after["warmups"],
                                       "baseline_elapsed_ns": before["elapsed_ns"], "final_elapsed_ns": after["elapsed_ns"],
                                       "final_over_baseline": ratio})
                    sample_values.append(statistics.median(repeated))
                ratio = statistics.median(sample_values)
                graph_values.append(ratio)
                graph_changes.append({"suite": suite, **case, "algorithm": algorithm,
                                      "graph_seed": graph_seed, "paired_final_over_baseline": ratio})
            changes.append({"suite": suite, **case, "algorithm": algorithm,
                            "baseline_median_ms": summaries_by_phase["baseline"][(case_id, algorithm)]["median_ms"],
                            "final_median_ms": summaries_by_phase["final"][(case_id, algorithm)]["median_ms"],
                            "paired_final_over_baseline": statistics.median(graph_values),
                            "graph_min_ratio": min(graph_values), "graph_max_ratio": max(graph_values),
                            "slower_observations": sum(ratio > 1 for ratio in individual),
                            "equal_observations": sum(ratio == 1 for ratio in individual),
                            "matched_observations": len(individual)})
        kkt_change = changes[-len(common.ALGORITHMS)]
        final_times = {algorithm: summaries_by_phase["final"][(case_id, algorithm)]["median_ms"] for algorithm in common.ALGORITHMS}
        best_time = min(final_times.values())
        fastest = [algorithm for algorithm in common.ALGORITHMS if final_times[algorithm] == best_time]
        comparisons = [comparisons_by_phase["final"][(case_id, "kkt", reference)] for reference in common.ALGORITHMS[1:]]
        assessment = {"suite": suite, **case,
                      "kkt_paired_final_over_baseline": kkt_change["paired_final_over_baseline"],
                      "kkt_change_graph_min": kkt_change["graph_min_ratio"],
                      "kkt_change_graph_max": kkt_change["graph_max_ratio"],
                      "fastest_by_final_runtime_median": ";".join(fastest),
                      "kkt_below_all_competitors_by_paired_medians": all(row["paired_runtime_ratio"] < 1 for row in comparisons),
                      "kkt_below_all_competitors_on_every_graph": all(row["graph_max_ratio"] < 1 for row in comparisons)}
        for row in comparisons:
            reference = row["reference"]
            assessment[f"final_kkt_over_{reference}"] = row["paired_runtime_ratio"]
            assessment[f"final_kkt_over_{reference}_graph_min"] = row["graph_min_ratio"]
            assessment[f"final_kkt_over_{reference}_graph_max"] = row["graph_max_ratio"]
        assessments.append(assessment)
    return {**pair, "changes": changes, "graph_changes": graph_changes, "trials": trials,
            "phase_summaries": phase_summaries, "phase_graphs": phase_graphs,
            "phase_comparisons": phase_comparisons, "assessments": assessments}


def plot_suite(result, output_dir):
    cases, changes, suite = result["cases"], result["changes"], result["suite"]
    lookup = {(row["case_id"], row["algorithm"]): row for row in changes}
    height = max(7.0, len(cases) * 0.27 + 2.1)
    figure, axes = plt.subplots(1, 2, figsize=(13.7, height), sharey=True, gridspec_kw={"width_ratios": [1, 1]})
    positions = np.arange(len(cases))
    for index, case in enumerate(cases):
        row = lookup[(case["case_id"], "kkt")]
        value = row["paired_final_over_baseline"]
        color = "#087F75" if value < 1 else "#B64F53"
        axes[0].errorbar(value, index, xerr=[[value - row["graph_min_ratio"]], [row["graph_max_ratio"] - value]],
                         fmt="o", color=color, capsize=2, markersize=4)
        for offset, algorithm in zip((-0.22, 0, 0.22), common.ALGORITHMS[1:]):
            row = lookup[(case["case_id"], algorithm)]
            value = row["paired_final_over_baseline"]
            axes[1].errorbar(value, index + offset,
                             xerr=[[value - row["graph_min_ratio"]], [row["graph_max_ratio"] - value]],
                             fmt=common.MARKERS[algorithm], color=common.COLORS[algorithm], capsize=2, markersize=3.5,
                             label=common.ALGORITHM_NAMES[algorithm] if index == 0 else None)
    axes[0].set_yticks(positions, [case["case_id"] for case in cases])
    axes[0].invert_yaxis()
    axes[0].set_title("KKT change", loc="left", fontweight="bold", pad=14)
    axes[1].set_title("Unchanged algorithms: timing controls", loc="left", fontweight="bold", pad=36)
    axes[1].legend(loc="lower center", bbox_to_anchor=(0.5, 1.001), ncol=3, frameon=False, fontsize=8)
    for axis in axes:
        axis.set_xscale("log")
        axis.axvline(1, color="#17232E", linestyle="--", linewidth=1)
        axis.set_xlabel("Final runtime / baseline runtime · lower is faster")
        axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}×"))
        axis.xaxis.set_minor_formatter(FuncFormatter(lambda value, _: f"{value:g}×"))
        common.style_axis(axis)
        axis.tick_params(axis="y", labelsize=8.5)
        axis.set_ylim(len(cases) - 0.5, -0.9)
    figure.suptitle(f"{suite.capitalize()} campaign: all before/after changes", x=0.02, ha="left", fontsize=18, fontweight="bold", y=0.99)
    figure.text(0.02, 0.016, "Matched trial ratios, then medians over repetitions → sampling seeds → graphs. Bars: graph-level ranges, not confidence intervals. All losses retained.", fontsize=9)
    figure.tight_layout(rect=(0, 0.045, 1, 0.965), w_pad=2.5)
    common.save_figure(figure, output_dir, f"{suite}_before_after")

    final_lookup = {(row["case_id"], row["reference"]): row for row in result["phase_comparisons"]
                    if row["phase"] == "final" and row["algorithm"] == "kkt"}
    values = np.array([[final_lookup[(case["case_id"], reference)]["paired_runtime_ratio"]
                        for reference in common.ALGORITHMS[1:]] for case in cases])
    logs = np.log2(values)
    limit = max(0.5, float(np.max(np.abs(logs))))
    figure, axis = plt.subplots(figsize=(9.0, height))
    heatmap = axis.imshow(logs, cmap="RdBu_r", norm=TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit), aspect="auto")
    axis.set_yticks(positions, [case["case_id"] for case in cases], fontsize=8.5)
    axis.set_xticks(range(3), [f"KKT / {common.ALGORITHM_NAMES[a]}" for a in common.ALGORITHMS[1:]], fontsize=10)
    axis.xaxis.tick_top()
    axis.tick_params(axis="x", length=0, pad=10)
    axis.tick_params(axis="y", length=0)
    for row in range(len(cases)):
        for column in range(3):
            color = "white" if abs(logs[row, column]) > 0.55 * limit else "#17232E"
            axis.text(column, row, f"{values[row, column]:.2f}×", ha="center", va="center", color=color, fontsize=9)
    colorbar = figure.colorbar(heatmap, ax=axis, shrink=0.55, pad=0.035)
    ticks = np.linspace(-limit, limit, 5)
    colorbar.set_ticks(ticks)
    colorbar.set_ticklabels([f"{2**value:.2g}×" for value in ticks])
    colorbar.set_label("Final KKT / final competitor runtime · logarithmic colors", fontsize=9)
    figure.suptitle(f"{suite.capitalize()}: does final KKT beat the competitors?", x=0.02, ha="left", fontsize=17, fontweight="bold", y=0.99)
    figure.text(0.02, 0.016, "Below 1× (blue): KKT faster. Above 1× (red): KKT slower. Paired hierarchical medians; every case is shown.\nThese ratios compare final-run algorithms, independently of how much KKT improved from its baseline.", fontsize=9)
    figure.tight_layout(rect=(0, 0.055, 1, 0.955))
    common.save_figure(figure, output_dir, f"{suite}_final_competition")


def source_info(path, output_dir):
    relative = Path(os.path.relpath(path.resolve(), output_dir.resolve())).as_posix()
    return {"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def write_report(results, output_dir):
    data = {"aggregation": AGGREGATION, "suites": {}}
    lines = ["# KKT optimization: before/after evidence", "", AGGREGATION, "",
             "Improving KKT and beating another MST implementation are separate outcomes. "
             "This report retains all cases, including regressions and final-run losses. "
             "There is no pooled mean speedup or workload-frequency interpretation of case counts."]
    for result in results:
        suite, cases = result["suite"], result["cases"]
        selected = [row for row in result["changes"] if row["algorithm"] == "kkt"]
        assessment = result["assessments"]
        controls = {}
        for algorithm in common.ALGORITHMS[1:]:
            rows = [row for row in result["changes"] if row["algorithm"] == algorithm]
            controls[algorithm] = {"minimum_case_ratio": min(row["paired_final_over_baseline"] for row in rows),
                                   "maximum_case_ratio": max(row["paired_final_over_baseline"] for row in rows),
                                   "cases_outside_0_95_to_1_05": [row["case_id"] for row in rows if not 0.95 <= row["paired_final_over_baseline"] <= 1.05]}
        info = {
            "baseline_csv": source_info(result["baseline_path"], output_dir),
            "final_csv": source_info(result["final_path"], output_dir),
            "case_count": len(cases), "observations_per_phase": len(result["baseline"]),
            "repetitions": result["repetitions"], "warmups": result["warmups"],
            "kkt_faster_cases": [row["case_id"] for row in selected if row["paired_final_over_baseline"] < 1],
            "kkt_regression_cases": [row["case_id"] for row in selected if row["paired_final_over_baseline"] > 1],
            "kkt_equal_cases": [row["case_id"] for row in selected if row["paired_final_over_baseline"] == 1],
            "kkt_change_ratio_range": [min(row["paired_final_over_baseline"] for row in selected), max(row["paired_final_over_baseline"] for row in selected)],
            "final_kkt_below_all_by_paired_medians": [row["case_id"] for row in assessment if row["kkt_below_all_competitors_by_paired_medians"]],
            "final_kkt_below_all_on_every_graph": [row["case_id"] for row in assessment if row["kkt_below_all_competitors_on_every_graph"]],
            "final_fastest_by_runtime_median_counts": dict(Counter(row["fastest_by_final_runtime_median"] for row in assessment)),
            "control_timing_changes": controls,
        }
        data["suites"][suite] = info
        links = [f'[{phase} raw CSV]({quote(info[f"{phase}_csv"]["path"])})' for phase in ("baseline", "final")]
        lines += ["", f"## {suite.capitalize()} suite", "",
                  f"Validated {len(cases)} identical cases and {len(result['baseline']):,} complete, matched timed observations per phase "
                  f"({result['repetitions']} repetitions, {result['warmups']} warmups per seed pair and algorithm). " + " · ".join(links) + ".", "",
                  f"KKT has a lower matched median runtime in **{len(info['kkt_faster_cases'])}/{len(cases)} cases**, "
                  f"a higher runtime in **{len(info['kkt_regression_cases'])}**, and equal runtime in **{len(info['kkt_equal_cases'])}**. "
                  f"Final/baseline ratios range from **{info['kkt_change_ratio_range'][0]:.3f}× to {info['kkt_change_ratio_range'][1]:.3f}×**.", "",
                  "| Unchanged timing control | Final/baseline case-ratio range | Cases outside ±5% |",
                  "|---|---:|---:|"]
        for algorithm, control in controls.items():
            lines.append(f'| {common.ALGORITHM_NAMES[algorithm]} | {control["minimum_case_ratio"]:.3f}–{control["maximum_case_ratio"]:.3f}× | {len(control["cases_outside_0_95_to_1_05"])} |')
        lines += ["", "The ±5% screen is a descriptive stability check, not a significance threshold or an automatic correction. "
                  "Control movement can reflect scheduling, cache, allocator, thermal, or clock effects. It does not uniquely identify their cause.", "",
                  "Final KKT is below all three competitors by paired case medians in: " +
                  (", ".join(f"`{case}`" for case in info["final_kkt_below_all_by_paired_medians"]) or "none of the cases") + ".", "",
                  "The stronger descriptive check—below every competitor on every graph-level median—holds in: " +
                  (", ".join(f"`{case}`" for case in info["final_kkt_below_all_on_every_graph"]) or "none of the cases") + ". "
                  "Neither check establishes statistical certainty or performance on unmeasured inputs.", "",
                  "| Case | KKT final/baseline | Graph range | Final KKT/Kruskal | Final KKT/Prim | Final KKT/Borůvka |",
                  "|---|---:|---:|---:|---:|---:|"]
        for row in assessment:
            lines.append(f'| {row["case_id"]} | {row["kkt_paired_final_over_baseline"]:.3f} | '
                         f'{row["kkt_change_graph_min"]:.3f}–{row["kkt_change_graph_max"]:.3f} | '
                         f'{row["final_kkt_over_kruskal"]:.3f} | {row["final_kkt_over_prim"]:.3f} | {row["final_kkt_over_boruvka"]:.3f} |')
        lines += ["", f"![All {suite} before/after changes]({suite}_before_after.png)", "",
                  f"![Final {suite} KKT comparison]({suite}_final_competition.png)"]
        if result["repetitions"] == 1:
            lines += ["", "The large suite is exploratory: one call per graph/sampling-seed pair cannot "
                      "estimate repeatability for that exact stream. Close races require separate repeated "
                      "confirmation. Its points are not pooled with the four-repetition diverse suite."]
    lines += ["", "## Interpretation and provenance", "",
              "- Three graph seeds are the independent graph-level units. Sampling seeds and repetitions "
              "do not create additional independent graphs. Star sampling-seed labels do not change its KKT path.",
              "- Before/after pairing aligns graph and sampling-seed labels plus repetition/order labels. "
              "It does not pair clock noise, temperature, or simultaneous machine state. Ratios of separately "
              "aggregated runtimes need not equal the matched-ratio medians reported here.",
              "- Both phases retain the common tuple-edge-list timing boundary, including KKT conversion "
              "and temporary-input destruction. Source/certificate validation and returned-result destruction "
              "remain outside timing. The CSVs validate exact MST results through the unchanged harness.",
              "- CSV validation cannot establish compiler, binary, fixture-source, or core-source identity. "
              "Consult the campaign metadata for exact revisions, hashes, flags, executable order, and host. "
              "Any algorithm intentionally changed beyond KKT must be identified before treating it as an unchanged control.",
              "- These are repository implementations on synthetic graphs. A lead over Kruskal alone is "
              "not a lead over Prim and Borůvka. Small observed advantages warrant confirmation; neither "
              "these ratios nor fitted curves prove asymptotic complexity or an eventual crossover.", "",
              "## Derived data", "",
              "- `before_after.csv` and `graph_before_after.csv`: changes for all four algorithms, including losses.",
              "- `matched_trials.csv`: every matched pair of raw durations and its final/baseline ratio.",
              "- `phase_summary.csv`, `phase_graph_summary.csv`, and `phase_comparisons.csv`: reusable per-phase aggregates.",
              "- `assessment.csv`: KKT changes and final-run comparisons against all three competitors for every case.",
              "- `analysis.json`: input hashes, counts, retained regressions, descriptive winners, and control movement.",
              "- Figures are also saved as SVG and PDF. The raw input CSVs are linked above; no old-run values are silently added."]
    (output_dir / "analysis.json").write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    (output_dir / "report.md").write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-csv", type=Path, required=True)
    parser.add_argument("--final-csv", type=Path, required=True)
    parser.add_argument("--large-baseline-csv", type=Path)
    parser.add_argument("--large-final-csv", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if bool(args.large_baseline_csv) != bool(args.large_final_csv):
        parser.error("both large-phase CSV paths are required when either is supplied")
    try:
        pairs = [load_pair("diverse", args.baseline_csv, args.final_csv)]
        if args.large_baseline_csv:
            pairs.append(load_pair("large", args.large_baseline_csv, args.large_final_csv))
        results = [compare_pair(pair) for pair in pairs]
        args.output_dir.mkdir(parents=True, exist_ok=True)
        tables = {"before_after.csv": "changes", "graph_before_after.csv": "graph_changes",
                  "matched_trials.csv": "trials", "phase_summary.csv": "phase_summaries",
                  "phase_graph_summary.csv": "phase_graphs", "phase_comparisons.csv": "phase_comparisons",
                  "assessment.csv": "assessments"}
        for filename, key in tables.items():
            common.write_csv(args.output_dir / filename, [row for result in results for row in result[key]])
        write_report(results, args.output_dir)
        plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "svg.fonttype": "none", "pdf.fonttype": 42})
        for result in results:
            plot_suite(result, args.output_dir)
            print(f"{result['suite']}: validated {len(result['cases'])} complete matched cases, {len(result['baseline'])} observations per phase")
        print(f"Wrote optimization analysis to {args.output_dir}")
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        print(f"optimization analysis failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
