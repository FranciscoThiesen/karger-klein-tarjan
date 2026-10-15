#!/usr/bin/env python3
"""Plot a complete, strictly revalidated six-solver capture after timing ends.

No native solver is invoked. Ratios are paired within graph/repetition, then
pooled across all twelve trials. Full trial ranges, both graph medians, every
comparator, every case, and both clocks remain visible and hash-bound.
"""
import argparse
import json
import math
from pathlib import Path

import run_retention_control as study

GROUPS = (("leaf_hierarchy4", 16, "Ordered leaf hierarchy · m = 16n"),
          ("leaf_distance4", 16, "Ordered leaf distance · m = 16n"),
          ("gnm_random", 16, "Connected G(n,m) · m = 16n"),
          ("gnm_random", 128, "Connected G(n,m) · m = 128n"))
LABELS = {"kkt": "Candidate KKT", "compacting_boruvka": "Compacting Borůvka",
          "multigraph_boruvka": "Retained-edge Borůvka", "kruskal": "Kruskal",
          "prim": "Prim", "boruvka": "Original Borůvka"}
COLORS = {"kkt": "#171717", "compacting_boruvka": "#AA4499",
          "multigraph_boruvka": "#0077BB", "kruskal": "#EE7733",
          "prim": "#009988", "boruvka": "#CC3311"}
METRICS = {"wall": "Steady elapsed time", "cpu": "Process CPU time"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def indexed(rows, fields):
    result = {}
    for row in rows:
        key = tuple(row[field] for field in fields)
        require(key not in result, "duplicate plot summary: " + str(key))
        result[key] = row
    return result


def prepare(cases, tables):
    require(len(cases) == 10, "plot requires all ten declared cases")
    expected_cases = {(case["family"], case["n"], case["density"], case["intrusion_per_mille"])
                      for case in cases.values()}
    require(expected_cases == study.EXPECTED_CASES, "plot matrix differs from declared study")
    require(set(study.ALGORITHMS) == set(LABELS) and len(study.GRAPH_SEEDS) == 2,
            "unexpected solver or graph-seed inventory")
    comparators = study.ALGORITHMS[1:]
    summaries = {
        "ratios": indexed(tables["comparisons"], ("case_id", "competitor", "metric")),
        "times": indexed(tables["summary"], ("case_id", "algorithm", "metric")),
    }
    graphs = {
        "ratios": indexed(tables["graph_comparisons"], ("case_id", "competitor", "metric", "graph_seed")),
        "times": indexed(tables["graph_summary"], ("case_id", "algorithm", "metric", "graph_seed")),
    }
    for kind, names in (("ratios", comparators), ("times", study.ALGORITHMS)):
        expected = {(case, name, metric) for case in cases for name in names for metric in METRICS}
        require(set(summaries[kind]) == expected, "missing case, comparator or clock in " + kind)
        require(set(graphs[kind]) == {(*key, seed) for key in expected for seed in study.GRAPH_SEEDS},
                "missing graph-median point in " + kind)
        value_field = "median_paired_ratio" if kind == "ratios" else "median_ns"
        for key, row in summaries[kind].items():
            require(row["trials"] == 12, "plot summary must include twelve trials")
            values = [row[field] for field in (value_field, "trial_min", "trial_max", "graph_min", "graph_max")]
            require(all(type(value) in (int, float) and math.isfinite(value) and value > 0 for value in values),
                    "nonpositive or nonfinite plot value")
            require(row["trial_min"] <= row[value_field] <= row["trial_max"] and
                    row["trial_min"] <= row["graph_min"] <= row["graph_max"] <= row["trial_max"],
                    "summary range does not contain its observations")
            medians = []
            for seed in study.GRAPH_SEEDS:
                graph = graphs[kind][(*key, seed)]
                require(graph["trials"] == 6 and graph["trial_min"] <= graph[value_field] <= graph["trial_max"],
                        "invalid graph-median point")
                require(row["trial_min"] <= graph["trial_min"] <= graph["trial_max"] <= row["trial_max"],
                        "case range excludes a graph range")
                medians.append(graph[value_field])
            require(min(medians) == row["graph_min"] and max(medians) == row["graph_max"],
                    "graph range disagrees with graph medians")
    grouped = []
    for family, density, title in GROUPS:
        selected = sorted((case for case in cases.values() if case["family"] == family and
                           case["density"] == density), key=lambda case: case["n"])
        require(len(selected) == (3 if family.startswith("leaf_") else 2), "incomplete family/density curve")
        grouped.append((title, selected))
    require(sum(len(selected) for _, selected in grouped) == len(cases), "unplotted cases")
    return summaries, graphs, grouped


def limits(values, anchors=()):
    all_values = [*values, *anchors]
    require(all_values and all(math.isfinite(value) and value > 0 for value in all_values),
            "logarithmic axes require finite positive observations")
    low, high = min(all_values), max(all_values)
    pad = max(0.08, 0.08 * math.log(high / low))
    return low / math.exp(pad), high * math.exp(pad)


def render(cases, tables, info, output):
    summaries, graphs, grouped = prepare(cases, tables)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "svg.fonttype": "none", "pdf.fonttype": 42})
    generated = []
    coverage = []
    for kind in ("ratios", "times"):
        names = study.ALGORITHMS[1:] if kind == "ratios" else study.ALGORITHMS
        value_field = "median_paired_ratio" if kind == "ratios" else "median_ns"
        scale = 1.0 if kind == "ratios" else 1e-9
        # Match the two clock figures' axes for a given panel. Every trial
        # range endpoint participates; no clipping or fixed ratio cutoff.
        bounds = {}
        for title, selected in grouped:
            values = [summaries[kind][(case["case_id"], name, metric)][field] * scale
                      for case in selected for name in names for metric in METRICS
                      for field in ("trial_min", "trial_max")]
            bounds[title] = limits(values, (0.9, 1.0) if kind == "ratios" else ())
        for metric, clock_label in METRICS.items():
            figure, axes = plt.subplots(2, 2, figsize=(14.0, 10.4))
            for axis, (title, selected) in zip(axes.flat, grouped):
                sizes = [case["n"] for case in selected]
                plotted_values = []
                for name in names:
                    color = COLORS[name]
                    pooled = [summaries[kind][(case["case_id"], name, metric)][value_field] * scale
                              for case in selected]
                    lower = [summaries[kind][(case["case_id"], name, metric)]["trial_min"] * scale
                             for case in selected]
                    upper = [summaries[kind][(case["case_id"], name, metric)]["trial_max"] * scale
                             for case in selected]
                    # Faint vertical spans retain all twelve observations'
                    # range. They describe variability, not confidence bounds.
                    axis.vlines(sizes, lower, upper, color=color, linewidth=1.3, alpha=.22, zorder=1)
                    for seed_index, seed in enumerate(study.GRAPH_SEEDS):
                        medians = [graphs[kind][(case["case_id"], name, metric, seed)][value_field] * scale
                                   for case in selected]
                        axis.scatter(sizes, medians, s=32, marker=("^", "v")[seed_index],
                                     color=color, alpha=.42, linewidths=.3, zorder=2)
                        plotted_values.extend(medians)
                    axis.plot(sizes, pooled, color=color, linewidth=2.3 if name in
                              ("kkt", "multigraph_boruvka") else 1.8,
                              marker="o", markersize=4.5, zorder=3)
                    plotted_values.extend([*pooled, *lower, *upper])
                if kind == "ratios":
                    axis.axhline(1.0, color="#555555", linestyle="--", linewidth=1.1, zorder=0)
                    axis.axhline(.9, color="#888888", linestyle=":", linewidth=1.1, zorder=0)
                axis.set_xscale("log", base=2)
                axis.set_yscale("log", base=2 if kind == "ratios" else 10)
                axis.set_xticks(sizes, [f"{size:,}" for size in sizes])
                axis.set_xlim(min(sizes) / 1.18, max(sizes) * 1.18)
                axis.set_ylim(*bounds[title])
                axis.yaxis.set_major_locator(LogLocator(base=2 if kind == "ratios" else 10,
                                                       subs=(1.0,) if kind == "ratios" else (1.0, 2.0, 5.0)))
                axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
                axis.yaxis.set_minor_formatter(NullFormatter())
                axis.set_title(title, loc="left", fontsize=12, pad=10)
                axis.set_xlabel("Vertices n · logarithmic scale")
                axis.set_ylabel("KKT / comparator time · logarithmic scale" if kind == "ratios"
                                else "Seconds · logarithmic scale")
                axis.grid(which="major", alpha=.16)
                actual_low, actual_high = axis.get_ylim()
                require(all(actual_low <= value <= actual_high for value in plotted_values),
                        "figure axis excludes a plotted graph median or trial range")
                coverage.append({"figure": kind + "_" + metric, "group": title,
                                 "case_ids": [case["case_id"] for case in selected],
                                 "algorithms": list(names), "pooled_points": len(selected) * len(names),
                                 "graph_median_points": len(selected) * len(names) * 2,
                                 "trial_range_endpoints": len(selected) * len(names) * 2,
                                 "y_limits": [actual_low, actual_high], "all_points_in_bounds": True})
            title = ("Candidate KKT against all five MST comparators" if kind == "ratios"
                     else "Absolute runtime of all six MST implementations")
            figure.suptitle(title + "\n" + clock_label, fontsize=16, y=.985)
            handles = [Line2D([], [], color=COLORS[name], marker="o", linewidth=2, markersize=4,
                              label=LABELS[name]) for name in names]
            handles += [Line2D([], [], color="#666666", marker="^", alpha=.42, linestyle="none",
                               label="Graph medians (two seeds)"),
                        Line2D([], [], color="#777777", alpha=.3, linewidth=2,
                               label="Full trial range")]
            figure.legend(handles=handles, loc="lower center", bbox_to_anchor=(.5, .06),
                          ncol=4, frameon=False, fontsize=9)
            if kind == "ratios":
                caption = ("Solid points: median of all 12 paired KKT/comparator ratios. Below 1 favors KKT. "
                           "Dashed: parity; dotted: 0.90.\n")
            else:
                caption = "Solid points: median of all 12 measured durations; graph points: each seed's six-trial median.\n"
            caption += ("All cases and observations retained. Ranges are descriptive, not confidence intervals. "
                        "Lines connect tested sizes only; no interpolated crossover is claimed.\n"
                        f"{info['flagged_calls']} flagged calls remain included. Each algorithm occupies every timed position once per child.")
            figure.text(.5, .01, caption, ha="center", va="bottom", fontsize=8.4, linespacing=1.5)
            figure.tight_layout(rect=(0, .16, 1, .93), h_pad=2.8, w_pad=2.3)
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
    parser.add_argument("--released", action="store_true",
                        help="Root confirms native timing has ended and rendering may begin")
    args = parser.parse_args()
    require(args.released, "rendering requires root scheduling --released after native timing ends")
    output = args.output.resolve()
    require(not output.exists(), "refusing to overwrite figures")
    # Strict collector validation rereads every raw child, certificate, resource
    # observation and provenance hash. Summary CSVs are not trusted as inputs.
    info, cases, rows, diagnostics, resources, inputs = study.load(args.capture)
    require(len(rows) == 840 and len(info["captures"]) == 20, "capture is not the complete six-solver study")
    tables = study.aggregate(rows)
    prepare(cases, tables)
    inputs = {**inputs, **study.helpers(), str(Path(__file__).resolve()): study.native.sha(__file__)}
    output.mkdir(parents=True)
    plotted = {name: tables[name] for name in ("comparisons", "graph_comparisons", "summary", "graph_summary")}
    study.write_json(output / "plotted_values.json", plotted, exclusive=True)
    generated, coverage, version = render(cases, tables, info, output)
    for path, digest in inputs.items():
        require(study.native.sha(path) == digest, "plot input changed while rendering: " + path)
    generated.append(output / "plotted_values.json")
    record = {"schema": "retention_control_figures_v1", "validation": "pass",
              "capture": str(args.capture.resolve()), "input_sha256": inputs,
              "matplotlib_version": version, "checked_outputs": len(rows),
              "timed_outputs": sum(row["phase"] == "timed" for row in rows),
              "warmup_outputs": sum(row["phase"] == "warmup" for row in rows),
              "flagged_calls_retained": info["flagged_calls"],
              "rows_removed": 0, "rows_adjusted": 0, "coverage": coverage,
              "ratio_aggregation": "Median of all twelve within-graph/repetition ratios; each graph marker is its six-trial median.",
              "absolute_aggregation": "Median of all twelve durations; each graph marker is its six-trial median.",
              "graph_ranges_are_confidence_intervals": False,
              "output_sha256": {path.name: study.native.sha(path) for path in generated},
              "visual_review": "pending: inspect all four PNGs before publishing"}
    study.write_json(output / "provenance.json", record, exclusive=True)
    (output / "README.md").write_text(
        "# Six-solver retention-control figures\n\n"
        "The plotter strictly rereads and validates the complete 840-output capture. "
        "Both clocks, all ten cases, all five KKT comparators and all six absolute runtimes are retained.\n\n"
        "- [Elapsed-time ratios](ratios_wall.png)\n"
        "- [Process-CPU ratios](ratios_cpu.png)\n"
        "- [Absolute elapsed times](times_wall.png)\n"
        "- [Absolute process-CPU times](times_cpu.png)\n\n"
        "Each PNG also has SVG and PDF versions. Solid ratio points are medians of all twelve "
        "paired trial ratios; faint triangles are each graph's six-trial median. Thin spans show "
        "the full trial range. Absolute-time medians use the corresponding durations directly. "
        "All ranges are descriptive, not confidence intervals. Curves connect tested sizes only; "
        "crossovers are not interpolated. Axes include every trial-range endpoint and share "
        "their limits across clocks within each family/density panel.\n\n"
        "`plotted_values.json` contains exact graph and pooled summaries; `provenance.json` binds "
        "the raw evidence, helpers, plotting source, figure outputs and axis-coverage checks. "
        "Visual review is pending until all four PNGs have been inspected.\n")
    print(json.dumps({"validation": "pass", "output": str(output), "figures": 4,
                      "formats": ["png", "svg", "pdf"], "visual_review": "pending"}))


if __name__ == "__main__":
    main()
