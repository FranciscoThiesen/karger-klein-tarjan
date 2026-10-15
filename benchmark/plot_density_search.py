#!/usr/bin/env python3
"""Render the complete density screen only after native timing has ended.

Reuses the immutable retention-control renderer; scoped module bindings are
restored even on exceptions. Strict density capture validation is mandatory.
No old observations are pooled and no solver is omitted or normalized.
"""
import argparse
import contextlib
import json
import math
from pathlib import Path

import plot_retention_control as style
import run_density_search as study

GROUPS = (("leaf_hierarchy4", 32, "Ordered leaf hierarchy · m = 32n"),
          ("leaf_shuffled4", 32, "Shuffled core ranks · m = 32n"),
          ("leaf_hierarchy4", 64, "Ordered leaf hierarchy · m = 64n"),
          ("leaf_shuffled4", 64, "Shuffled core ranks · m = 64n"))
LABELS = {**style.LABELS, "kkt": "Direct-Edge KKT"}
METRICS = style.METRICS
require, indexed = style.require, style.indexed


def prepare(cases, tables):
    require(len(cases) == 8, "plot requires all eight declared cases")
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
        require(len(selected) == 2, "incomplete family/density curve")
        grouped.append((title, selected))
    require(sum(len(selected) for _, selected in grouped) == len(cases), "unplotted cases")
    return summaries, graphs, grouped


@contextlib.contextmanager
def configured_style():
    replacements = {"study": study, "GROUPS": GROUPS, "LABELS": LABELS, "prepare": prepare}
    before = {name: getattr(style, name) for name in replacements}
    try:
        for name, value in replacements.items(): setattr(style, name, value)
        yield
    finally:
        for name, value in before.items(): setattr(style, name, value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--released", action="store_true", help="Root confirms native timing ended and rendering may begin")
    args = parser.parse_args()
    require(args.released, "rendering requires scheduling --released after native timing ends")
    output = args.output.resolve(); require(not output.exists(), "refusing to overwrite figures")
    info, cases, rows, diagnostics, resources, inputs = study.load(args.capture)
    require(len(rows) == 672 and len(info["captures"]) == 16 and
            sum(row["phase"] == "timed" for row in rows) == 576 and
            sum(row["phase"] == "warmup" for row in rows) == 96,
            "capture is not the complete density screen")
    tables = study.aggregate(rows)
    require({name: len(values) for name, values in tables.items()} ==
            {"paired_ratios": 960, "comparisons": 80, "graph_comparisons": 160, "summary": 96, "graph_summary": 192},
            "incomplete density plot summaries")
    prepare(cases, tables)
    source = Path(__file__).resolve(); renderer = Path(style.__file__).resolve()
    inputs = {**inputs, **study.helpers(), str(source): study.native.sha(source), str(renderer): study.native.sha(renderer)}
    output.mkdir(parents=True)
    plotted = {name: tables[name] for name in ("comparisons", "graph_comparisons", "summary", "graph_summary")}
    study.write_json(output / "plotted_values.json", plotted, exclusive=True)
    with configured_style():
        generated, coverage, version = style.render(cases, tables, info, output)
    require(len(coverage) == 16 and all(row["all_points_in_bounds"] for row in coverage), "missing plot coverage")
    limits = {(row["figure"], row["group"]): row["y_limits"] for row in coverage}
    for kind in ("ratios", "times"):
        for _, _, title in GROUPS:
            require(limits[(kind + "_wall", title)] == limits[(kind + "_cpu", title)], "clock axes are not matched")
    for path, digest in inputs.items(): require(study.native.sha(path) == digest, "plot input changed: " + path)
    generated.append(output / "plotted_values.json")
    record = {"schema": "density_search_figures_v1", "validation": "pass", "capture": str(args.capture.resolve()),
              "input_sha256": inputs, "matplotlib_version": version, "checked_outputs": 672,
              "timed_outputs": 576, "warmup_outputs": 96, "flagged_calls_retained": info["flagged_calls"],
              "rows_removed": 0, "rows_adjusted": 0, "coverage": coverage,
              "ratio_aggregation": "Median of all twelve within-graph/repetition ratios; graph markers are each seed's six-trial median.",
              "absolute_aggregation": "Median of all twelve durations; graph markers are each seed's six-trial median.",
              "graph_ranges_are_confidence_intervals": False, "control_normalization": False,
              "matched_clock_axes": True, "interpolated_crossover": False,
              "output_sha256": {path.name: study.native.sha(path) for path in generated},
              "visual_review": "pending: inspect all four PNGs before publishing"}
    study.write_json(output / "provenance.json", record, exclusive=True)
    (output / "README.md").write_text(
        "# Direct-Edge density-search figures\n\n"
        "Strictly revalidated all 672 outputs from 16 native children. Both clocks, all eight cases, "
        "all five KKT comparators and all six absolute runtimes remain visible.\n\n"
        "- [Elapsed-time ratios](ratios_wall.png)\n"
        "- [Process-CPU ratios](ratios_cpu.png)\n"
        "- [Absolute elapsed times](times_wall.png)\n"
        "- [Absolute process-CPU times](times_cpu.png)\n\n"
        "Each figure has four family/density panels: ordered or shuffled core ranks at m/n = 32 or 64. "
        "Both families retain cheap leaf attachments; shuffled core ranks are not globally random weights. "
        "Matched families share topology, IDs, labels and edge order.\n\n"
        "Solid points are pooled twelve-trial medians; triangles are the two graph medians; thin spans "
        "show every trial-range endpoint. Ranges are descriptive, not confidence intervals. "
        "All losses and clock-flagged observations remain included. Ratio values below one favor KKT. "
        "Each absolute-time median is computed from durations directly; controls never normalize KKT.\n\n"
        "Axes include every trial-range endpoint and use the same limits across clocks within each panel. "
        "Lines connect only the two tested sizes; no exact crossing point is interpolated. "
        "Two endpoints provide exploratory brackets, not evidence of durable asymptotic dominance. "
        "The prior density-16 data is not pooled. Each graph/sampling realization is timed six times.\n\n"
        "PNG, SVG and PDF versions are retained. `plotted_values.json` preserves graph and case summaries; "
        "`provenance.json` binds raw evidence, source, immutable renderer, outputs and coverage checks. "
        "Visual review remains pending until all four PNGs are inspected.\n")
    print(json.dumps({"validation": "pass", "output": str(output), "figures": 4,
                      "formats": ["png", "svg", "pdf"], "visual_review": "pending"}))


if __name__ == "__main__": main()
