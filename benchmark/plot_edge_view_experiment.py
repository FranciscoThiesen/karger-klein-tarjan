#!/usr/bin/env python3
"""Plot strictly revalidated paired Edge-view results after native timing ends.

All six Edge/tuple ratios expose unchanged-solver drift without normalizing KKT.
Separate figures compare Edge KKT directly with every solver in the same child.
No native process is launched, and no historical timings enter the figures.
"""
import argparse
import json
import math
from pathlib import Path

import run_edge_view_experiment as study
import plot_retention_control as style

METRICS = {"wall": "Steady elapsed time", "cpu": "Process CPU time"}
KINDS = ("variant_gains", "edge_ratios")


def prepare(cases, tables):
    require = study.require
    require(len(cases) == 10, "all ten declared cases are required")
    require({(r['family'], r['n'], r['density'], r['intrusion_per_mille']) for r in cases.values()}
            == study.control.EXPECTED_CASES, "unexpected graph matrix")
    pooled = {
        "variant_gains": style.indexed(tables["variant_comparisons"], ("case_id", "algorithm", "metric")),
        "edge_ratios": style.indexed([r for r in tables["comparisons"] if r["variant"] == "edge"],
                                     ("case_id", "competitor", "metric")),
    }
    graphs = {
        "variant_gains": style.indexed(tables["graph_variant_comparisons"],
                                       ("case_id", "algorithm", "metric", "graph_seed")),
        "edge_ratios": style.indexed([r for r in tables["graph_comparisons"] if r["variant"] == "edge"],
                                     ("case_id", "competitor", "metric", "graph_seed")),
    }
    for kind in KINDS:
        names = study.ALGORITHMS if kind == "variant_gains" else study.ALGORITHMS[1:]
        expected = {(case, name, metric) for case in cases for name in names for metric in METRICS}
        require(set(pooled[kind]) == expected, "missing case, solver or clock in " + kind)
        require(set(graphs[kind]) == {(*key, seed) for key in expected for seed in study.GRAPH_SEEDS},
                "missing graph-seed median in " + kind)
        for key, row in pooled[kind].items():
            require(row["trials"] == 12, "pooled ratio must use twelve paired trials")
            values = [row[field] for field in ("median_paired_ratio", "trial_min", "trial_max", "graph_min", "graph_max")]
            require(all(type(v) in (int, float) and math.isfinite(v) and v > 0 for v in values),
                    "nonpositive or nonfinite plot value")
            require(row["trial_min"] <= row["median_paired_ratio"] <= row["trial_max"], "invalid trial range")
            medians = []
            for seed in study.GRAPH_SEEDS:
                graph = graphs[kind][(*key, seed)]
                require(graph["trials"] == 6 and row["trial_min"] <= graph["trial_min"] <=
                        graph["median_paired_ratio"] <= graph["trial_max"] <= row["trial_max"],
                        "graph summary outside full trial range")
                medians.append(graph["median_paired_ratio"])
            require(min(medians) == row["graph_min"] and max(medians) == row["graph_max"],
                    "graph median range differs")
    grouped = []
    for family, density, title in style.GROUPS:
        selected = sorted((case for case in cases.values() if case["family"] == family and
                           case["density"] == density), key=lambda case: case["n"])
        require(len(selected) == (3 if family.startswith("leaf_") else 2), "incomplete size curve")
        grouped.append((title, selected))
    require(sum(len(selected) for _, selected in grouped) == 10, "unplotted case")
    return pooled, graphs, grouped


def render(cases, tables, info, output):
    pooled, graphs, grouped = prepare(cases, tables)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FuncFormatter, LogLocator, MaxNLocator, NullFormatter

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "svg.fonttype": "none", "pdf.fonttype": 42})
    labels = {**style.LABELS, "kkt": "KKT"}
    generated, coverage = [], []
    for kind in KINDS:
        names = study.ALGORITHMS if kind == "variant_gains" else study.ALGORITHMS[1:]
        bounds = {title: style.limits([pooled[kind][(case["case_id"], name, metric)][field]
                                      for case in selected for name in names for metric in METRICS
                                      for field in ("trial_min", "trial_max")], (.9, 1.0))
                  for title, selected in grouped}
        for metric, clock_label in METRICS.items():
            figure, axes = plt.subplots(2, 2, figsize=(14.0, 10.5))
            for axis, (title, selected) in zip(axes.flat, grouped):
                sizes = [case["n"] for case in selected]
                all_values = []
                for name in names:
                    color = style.COLORS[name]
                    values = [pooled[kind][(case["case_id"], name, metric)]["median_paired_ratio"] for case in selected]
                    lower = [pooled[kind][(case["case_id"], name, metric)]["trial_min"] for case in selected]
                    upper = [pooled[kind][(case["case_id"], name, metric)]["trial_max"] for case in selected]
                    axis.vlines(sizes, lower, upper, color=color, linewidth=1.3, alpha=.22, zorder=1)
                    for seed_index, seed in enumerate(study.GRAPH_SEEDS):
                        medians = [graphs[kind][(case["case_id"], name, metric, seed)]["median_paired_ratio"]
                                   for case in selected]
                        axis.scatter(sizes, medians, s=32, marker=("^", "v")[seed_index],
                                     color=color, alpha=.42, linewidths=.3, zorder=2)
                        all_values.extend(medians)
                    axis.plot(sizes, values, color=color, linewidth=2.4 if name in ("kkt", "multigraph_boruvka") else 1.8,
                              marker="o", markersize=4.5, zorder=3)
                    all_values.extend([*values, *lower, *upper])
                axis.axhline(1, color="#555555", linestyle="--", linewidth=1.1, zorder=0)
                axis.axhline(.9, color="#888888", linestyle=":", linewidth=1.1, zorder=0)
                axis.set_xscale("log", base=2)
                if kind == "edge_ratios":
                    axis.set_yscale("log", base=2)
                axis.set_xticks(sizes, [f"{size:,}" for size in sizes])
                axis.set_xlim(min(sizes) / 1.18, max(sizes) * 1.18)
                axis.set_ylim(*bounds[title])
                axis.yaxis.set_major_locator(LogLocator(base=2) if kind == "edge_ratios"
                                            else MaxNLocator(nbins=6))
                axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
                axis.yaxis.set_minor_formatter(NullFormatter())
                axis.set_title(title, loc="left", fontsize=12, pad=10)
                axis.set_xlabel("Vertices n · logarithmic scale")
                axis.set_ylabel("Edge / tuple time" if kind == "variant_gains"
                                else "Edge KKT / comparator time · logarithmic scale")
                axis.grid(which="major", alpha=.16)
                low, high = axis.get_ylim()
                study.require(all(low <= value <= high for value in all_values), "plot clips an observed range")
                coverage.append({"figure": kind + "_" + metric, "group": title,
                                 "case_ids": [case["case_id"] for case in selected], "algorithms": list(names),
                                 "pooled_points": len(selected) * len(names),
                                 "graph_median_points": len(selected) * len(names) * 2,
                                 "trial_range_endpoints": len(selected) * len(names) * 2,
                                 "all_points_in_bounds": True, "y_limits": [low, high]})
            title = ("Direct Edge / refactored tuple: all six solvers" if kind == "variant_gains"
                     else "Direct Edge KKT against all five MST comparators")
            figure.suptitle(title + "\n" + clock_label, fontsize=16, y=.985)
            handles = [Line2D([], [], color=style.COLORS[name], marker="o", linewidth=2,
                              markersize=4, label=labels[name]) for name in names]
            handles += [Line2D([], [], color="#666666", marker="^", linestyle="none", alpha=.42,
                               label="Graph medians (two seeds)"),
                        Line2D([], [], color="#777777", linewidth=2, alpha=.3, label="Full trial range")]
            figure.legend(handles=handles, loc="lower center", bbox_to_anchor=(.5, .075), ncol=4,
                          frameon=False, fontsize=9)
            caption = ("Edge/tuple pairs share graph, sampling seed, solver and repetition across adjacent children. "
                       "Controls expose drift; no normalization.\n" if kind == "variant_gains" else
                       "KKT/comparator pairs share a graph and repetition in the same Edge child. "
                       "Below 1 favors KKT; dotted line: 0.90.\n")
            caption += ("Solid points: median of all 12 paired ratios; faint triangles: six-trial graph medians. "
                        "All cases, losses and full trial ranges retained.\n"
                        "Ranges are descriptive, not confidence intervals. Lines connect tested sizes; no threshold interpolation. "
                        f"All {info['flagged_calls']} flagged calls remain included.")
            figure.text(.5, .01, caption, ha="center", va="bottom", fontsize=8.4, linespacing=1.5)
            figure.tight_layout(rect=(0, .175, 1, .93), h_pad=2.8, w_pad=2.3)
            for extension in ("png", "svg", "pdf"):
                path = output / f"{kind}_{metric}.{extension}"
                figure.savefig(path, dpi=180, bbox_inches="tight")
                generated.append(path)
            plt.close(figure)
    return generated, coverage, matplotlib.__version__


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--released", action="store_true")
    args = parser.parse_args()
    study.require(args.released, "plotting requires root release after native timing ends")
    output = args.output.resolve()
    study.require(not output.exists(), "refusing to overwrite plot evidence")
    info, cases, rows, _, _, inputs = study.load(args.capture)
    study.require(len(rows) == 1680 and len(info["captures"]) == 40, "incomplete paired study")
    tables = study.aggregate(rows)
    prepare(cases, tables)
    inputs = {**inputs, **study.helpers(), str(Path(__file__).resolve()): study.native.sha(__file__),
              str(Path(style.__file__).resolve()): study.native.sha(style.__file__)}
    output.mkdir(parents=True)
    study.write_json(output / "plotted_values.json", tables, exclusive=True)
    generated, coverage, version = render(cases, tables, info, output)
    for path, digest in inputs.items(): study.analysis.hash_check(Path(path), digest)
    generated.append(output / "plotted_values.json")
    study.write_json(output / "provenance.json", {
        "schema": "edge_view_figures_v1", "validation": "pass", "capture": str(args.capture.resolve()),
        "input_sha256": inputs, "matplotlib_version": version, "checked_outputs": 1680,
        "timed_outputs": 1440, "warmup_outputs": 240, "rows_removed": 0, "rows_adjusted": 0,
        "flagged_calls_retained": info["flagged_calls"], "coverage": coverage,
        "aggregation": "Median of twelve paired ratios; each graph median uses six; no control normalization.",
        "graph_ranges_are_confidence_intervals": False,
        "output_sha256": {path.name: study.native.sha(path) for path in generated},
        "visual_review": "pending: inspect all four PNGs before publication"}, exclusive=True)
    (output / "README.md").write_text(
        "# Paired Edge-query verifier figures\n\n"
        "The strict collector rereads all 1,680 outputs, raw certificates, process-group observations, "
        "source/build bindings and clock flags before plotting. Historical timings are absent.\n\n"
        "- [All six Edge/tuple elapsed-time ratios](variant_gains_wall.png)\n"
        "- [All six Edge/tuple CPU-time ratios](variant_gains_cpu.png)\n"
        "- [Edge KKT / all five comparators, elapsed](edge_ratios_wall.png)\n"
        "- [Edge KKT / all five comparators, CPU](edge_ratios_cpu.png)\n\n"
        "Each figure also has SVG and PDF versions. Solid points pool all twelve paired ratios; "
        "faint graph points use six ratios each. Thin spans show the full trial range. "
        "All losses and flagged calls remain included. Axes contain every trial range and share "
        "limits across clocks. Unchanged-solver drift is shown without normalizing KKT. "
        "Ranges are descriptive, not confidence intervals; connecting lines do not interpolate crossovers. "
        "Exact source values and hashes are preserved alongside the figures. Visual review is pending.\n")
    print(json.dumps({"validation": "pass", "figures": 4, "output": str(output), "visual_review": "pending"}))


if __name__ == "__main__":
    main()
