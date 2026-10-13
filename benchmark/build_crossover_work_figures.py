#!/usr/bin/env python3
"""Render hash-bound logical-work figures from successful crossover diagnostics.

Consumes only provenance.json, work_graphs.csv and work_summary.csv from the
strict diagnostic analysis. No raw capture, timing data or native executable is
read or run. Matplotlib is imported only after validation, when rendering.
"""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import sys

import analyze_continuation as base
import analyze_crossover_diagnostics as diagnostics
import compare_crossover as comparison

METRICS = ("contraction_calls", "contraction_edges", "contraction_edge_visits", "contraction_vertices",
           "verifier_edges", "sampling_calls", "filtered_edges", "initialized_slots", "edge_materializations",
           "total_work_proxy")
COUNTS = tuple("mean_" + field for field in METRICS) + ("mean_contraction_edges_after_shared_prefix",)
RATIOS = ("contraction_edges_over_m", "mean_heavy_fraction")
IDENTITY = ("family", "n", "density", "intrusion_per_mille", "m", "case_id", "algorithm")
LABELS = {"line_metric": "Line · length weights", "line_wide_metric": "Line · wide-gap length weights",
          "line_random": "Line · random weights", "grid2d_metric": "Grid · distance weights",
          "grid2d_random": "Grid · random weights", "gnm_random": "Connected G(n,m) · random weights",
          "hierarchical_path": "Dyadic hierarchy · path"}
ALGORITHM_LABELS = {"kkt": "KKT", "compacting_boruvka": "Compacting Borůvka"}
COLORS = {"kkt": "#7946A5", "compacting_boruvka": "#277BA8"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(path):
    return {"path": str(path.resolve()), "sha256": sha(path)}


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)


def load_table(path, cases, graph_level):
    required = set(IDENTITY + COUNTS + RATIOS + (("graph_seed",) if graph_level else ()))
    result = {}
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        header = reader.fieldnames or []
        base.require(len(header) == len(set(header)) and set(header) == required,
                     f"{path}: unexpected or duplicate columns")
        for number, raw in enumerate(reader, 2):
            context = f"{path}:{number}"
            base.require(None not in raw and all(value is not None for value in raw.values()), context + ": malformed row")
            row = dict(raw)
            for name in ("n", "m", "density", "intrusion_per_mille") + (("graph_seed",) if graph_level else ()):
                row[name] = base.integer(raw[name], context + " " + name)
            spec = cases.get(row["case_id"])
            base.require(spec is not None and all(row[name] == value for name, value in spec.items()),
                         context + ": fixture differs from the fixed diagnostic plan")
            base.require(row["algorithm"] in base.ALGORITHMS and (not graph_level or row["graph_seed"] == 3037),
                         context + ": unexpected algorithm or graph seed")
            for name in COUNTS:
                row[name] = float(raw[name])
                base.require(math.isfinite(row[name]) and row[name] >= 0 and row[name].is_integer(),
                             context + ": singleton count must be a finite nonnegative integer: " + name)
            for name in RATIOS:
                row[name] = None if raw[name] == "" else float(raw[name])
                base.require(row[name] is None or math.isfinite(row[name]), context + ": nonfinite ratio")
            base.require(row["mean_contraction_edges"] >= row["m"] and row["mean_edge_materializations"] >= row["m"] and
                         row["mean_contraction_edges_after_shared_prefix"] <= row["mean_contraction_edges"] and
                         row["contraction_edges_over_m"] is not None and
                         close(row["contraction_edges_over_m"], row["mean_contraction_edges"] / row["m"]),
                         context + ": contraction/materialization normalization mismatch")
            verifier, retained = row["mean_verifier_edges"], row["mean_filtered_edges"]
            base.require(0 <= retained <= verifier, context + ": retained incidences exceed verifier inputs")
            base.require((row["mean_heavy_fraction"] is None) if verifier == 0 else
                         (row["mean_heavy_fraction"] is not None and close(row["mean_heavy_fraction"], 1-retained/verifier)),
                         context + ": undefined or incorrect heavy-incidence fraction")
            if row["algorithm"] == "compacting_boruvka":
                base.require(verifier == retained == row["mean_sampling_calls"] == 0,
                             context + ": compactor unexpectedly samples or verifies")
            key = row["case_id"], row["algorithm"]
            base.require(key not in result, context + ": duplicate case/algorithm")
            result[key] = row
    expected = [(case, algorithm) for case in cases for algorithm in base.ALGORITHMS]
    base.require(list(result) == expected, f"{path}: missing, extra or reordered diagnostic cases")
    return result


def load(folder):
    provenance_path = folder / "provenance.json"
    provenance = comparison.read_json(provenance_path)
    for field, expected in (("schema", "crossover_diagnostics_v1"), ("validation", "pass"),
                            ("case_count", 10), ("work_rows", 20), ("trace_graphs", 10),
                            ("graph_seeds", [3037]), ("sampling_seeds", [101]), ("rows_removed", 0),
                            ("rows_adjusted", 0), ("timing_observations_exported", 0)):
        base.require(type(provenance.get(field)) is type(expected) and provenance[field] == expected,
                     "diagnostic provenance: incorrect " + field)
    stages = provenance.get("trace_stages")
    base.require(type(stages) is int and 10 <= stages <= 208 and
                 type(provenance.get("derived_stages_including_zero")) is int and
                 provenance["derived_stages_including_zero"] == stages + 10,
                 "diagnostic provenance: incomplete trace-stage accounting")
    cases = {}
    for family, n, _ in diagnostics.PLAN:
        spec = {"family": family, "n": n, "density": 16, "intrusion_per_mille": 0, "m": 16*n}
        spec["case_id"] = base.case_id(spec)
        cases[spec["case_id"]] = spec
    digests = provenance.get("derived_csv_sha256")
    base.require(type(digests) is dict, "diagnostic provenance lacks derived CSV hashes; rerun the strict analyzer")
    paths = {"provenance": provenance_path}
    for name in ("work_graphs", "work_summary"):
        path = folder / (name + ".csv")
        base.require(digests.get(path.name) == sha(path), "derived CSV differs from successful analysis: " + path.name)
        paths[name] = path
    graphs = load_table(paths["work_graphs"], cases, True)
    summary = load_table(paths["work_summary"], cases, False)
    for key, row in summary.items():
        base.require(all(value == graphs[key][name] for name, value in row.items()),
                     f"{key}: single-graph summary differs from graph-level values")
    return cases, summary, {name: record(path) for name, path in paths.items()}


def values(cases, summary):
    result = []
    for case, spec in cases.items():
        for algorithm in base.ALGORITHMS:
            row = summary[case, algorithm]
            fields = [("contraction_input_edges", "mean_contraction_edges", row["mean_contraction_edges"]),
                      ("edge_materializations", "mean_edge_materializations", row["mean_edge_materializations"])]
            if algorithm == "kkt":
                fields += [("verifier_input_incidences", "mean_verifier_edges", row["mean_verifier_edges"]),
                           ("retained_light_incidences", "mean_filtered_edges", row["mean_filtered_edges"]),
                           ("removed_heavy_incidences", "mean_verifier_edges - mean_filtered_edges",
                            row["mean_verifier_edges"] - row["mean_filtered_edges"])]
            for measure, source, numerator in fields:
                result.append({**spec, "graph_seed": 3037, "kkt_seed": 101 if algorithm == "kkt" else "na",
                               "algorithm": algorithm, "measure": measure, "source_counter": source,
                               "numerator": int(numerator), "original_m": spec["m"], "value_over_m": numerator/spec["m"]})
    return result


def render(cases, summary, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10, "svg.fonttype": "none", "pdf.fonttype": 42})
    files = []
    labels = [f"{LABELS[s['family']]}\nn={s['n']:,}" for s in cases.values()]

    def finish(fig, axis, stem, title, xlabel, footer):
        axis.set_yticks(range(len(cases)), labels, fontsize=9)
        axis.invert_yaxis()
        axis.set_xlabel(xlabel)
        axis.set_xlim(left=0)
        axis.spines[["top", "right", "left"]].set_visible(False)
        axis.tick_params(axis="y", length=0)
        axis.grid(axis="x", alpha=.22)
        axis.set_axisbelow(True)
        fig.suptitle(title, fontsize=15, y=.985)
        handles, names = axis.get_legend_handles_labels()
        fig.legend(handles, names, loc="upper center", bbox_to_anchor=(.64,.945), ncol=2, frameon=False)
        fig.text(.025,.022, "Untimed · graph seed 3037 · KKT sampling seed 101 · m=16n for every case.\n" + footer,
                 fontsize=8)
        fig.tight_layout(rect=(0,.085,1,.915))
        for extension in ("png", "svg", "pdf"):
            path = output / (stem + "." + extension)
            fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
            if extension == "svg":
                path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
            files.append(path.name)
        plt.close(fig)

    for field, stem, title, xlabel in (
        ("mean_contraction_edges", "contraction_volume", "Contraction input volume · all ten diagnostic cases",
         "Sum of contraction-call input edges / original m"),
        ("mean_edge_materializations", "edge_materializations", "Edge materializations · all ten diagnostic cases",
         "Logical edge materializations / original m"),
    ):
        fig, axis = plt.subplots(figsize=(11.8,9.4))
        largest = max(summary[case, algorithm][field]/spec["m"] for case,spec in cases.items() for algorithm in base.ALGORITHMS)
        for offset, algorithm in zip((-.18,.18), base.ALGORITHMS):
            amounts = [summary[case, algorithm][field]/spec["m"] for case,spec in cases.items()]
            positions = [index+offset for index in range(len(cases))]
            axis.barh(positions, amounts, height=.31, color=COLORS[algorithm], label=ALGORITHM_LABELS[algorithm])
            for y, amount in zip(positions, amounts):
                axis.text(amount+.012*largest, y, f"{amount:.3f}", va="center", fontsize=8)
        axis.set_xlim(0, largest*1.17)
        finish(fig, axis, stem, title, xlabel,
               "One graph and one KKT sampling seed per case; no variability estimate. Each figure shows a separate logical counter, not elapsed time or bytes.")

    fig, axis = plt.subplots(figsize=(11.8,9.4))
    retained = [summary[case,"kkt"]["mean_filtered_edges"]/spec["m"] for case,spec in cases.items()]
    removed = [(summary[case,"kkt"]["mean_verifier_edges"]-summary[case,"kkt"]["mean_filtered_edges"])/spec["m"]
               for case,spec in cases.items()]
    axis.barh(range(len(cases)), retained, height=.56, color="#138478", label="Retained F-light incidences")
    axis.barh(range(len(cases)), removed, left=retained, height=.56, color="#B38CCB", label="Removed F-heavy incidences")
    largest = max(a+b for a,b in zip(retained,removed))
    for y, (a,b) in enumerate(zip(retained,removed)):
        axis.text(a+b+.012*largest, y, f"{a+b:.3f}", va="center", fontsize=8)
    axis.set_xlim(0, max(1,largest*1.17))
    finish(fig, axis, "verifier_incidences", "KKT verifier input incidences · all ten diagnostic cases",
           "Recursive verifier input edge incidences / original m",
           "Stacked parts partition the same verifier inputs; an original edge may appear in several calls. Not unique edges, bytes, or a runtime estimate.")
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    base.require(args.validate_only or args.output_dir is not None, "--output-dir is required unless --validate-only")
    cases, summary, inputs = load(args.analysis_dir.resolve())
    points = values(cases, summary)
    base.require(len(points) == 70, "incomplete figure-point matrix")
    metadata = {"schema": "crossover_work_figures_v1", "validation": "pass", "cases": 10, "algorithm_rows": 20,
                "figure_points": len(points), "inputs": inputs, "source_sha256": sha(Path(__file__)),
                "rows_removed": 0, "rows_adjusted": 0, "timing_observations": 0,
                "scope": "Untimed logical counters, one graph seed and one KKT sampling seed; all ten declared cases retained."}
    if args.validate_only:
        print(json.dumps(metadata, indent=2, allow_nan=False)); return
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    diagnostics.moments.write_csv(output / "figure_points.csv", points)
    metadata["figures"] = render(cases, summary, output)
    metadata["artifact_sha256"] = {name: sha(output/name) for name in ["figure_points.csv", *metadata["figures"]]}
    (output / "provenance.json").write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n")
    lines = ["# Untimed crossover work figures", "", metadata["scope"], "",
             "All figures use the same declared case order and original-edge denominator m=16n. "
             "The paired bars use the same counter for KKT and compacting Borůvka. Materializations "
             "are logical counted events, not bytes or allocator costs. The verifier figure partitions "
             "its own recursive input incidences into retained F-light and removed F-heavy parts; it "
             "does not count unique original edges. Counters from different figures are not summed. "
             "There are no error bars, confidence claims or timing estimates.", "",
             "The renderer requires successful strict diagnostic provenance and matching derived CSV hashes. "
             "It checks all twenty graph/algorithm rows and their identical singleton case summaries. "
             "It does not independently recertify an MST or reload the native capture.", "",
             "[Exact figure points](figure_points.csv), [provenance](provenance.json).", "", "Analysis inputs:", ""]
    for name, item in inputs.items():
        lines.append(f"- [{name}]({os.path.relpath(item['path'],output.resolve())})")
    for name in metadata["figures"]:
        if name.endswith(".png"): lines += ["", f"![{name}]({name})"]
    (output / "README.md").write_text("\n".join(lines).rstrip() + "\n")
    print(f"Validated all ten cases and rendered three work figures in {output}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as error:
        print("crossover work figures: " + str(error), file=sys.stderr)
        sys.exit(1)
