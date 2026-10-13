#!/usr/bin/env python3
"""Validate the fixed ten-case untimed crossover diagnostic capture.

Requires the original discovery, extension and precision screen configuration
solely for capture validation and graph-identity checks. No timing values are
exported or pooled. Reuses the production work registry, continuation loaders,
work/trace crosschecks and component-moment validator. No plotting imports.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys

import analyze_continuation as base
import analyze_crossover_moments as moments
import compare_crossover as comparison

GRAPH_SEEDS = (3037,)
SAMPLING_SEEDS = (101,)
PLAN = (
    ("line_metric", 1048576, "discovery"),
    ("line_wide_metric", 1048576, "precision"),
    ("line_random", 1048576, "discovery"),
    ("grid2d_metric", 1048576, "discovery"),
    ("grid2d_random", 1048576, "discovery"),
    ("gnm_random", 1048576, "discovery"),
    ("hierarchical_path", 1048576, "discovery"),
    ("line_metric", 8388608, "extension"),
    ("line_wide_metric", 8388608, "precision"),
    ("hierarchical_path", 4194304, "precision"),
)
DESCRIPTION = (
    "Untimed logical-work diagnostics for ten predeclared cases, one graph "
    "seed and one KKT sampling seed. Both algorithms' contraction input volume "
    "uses contraction_edges / original m. Other counts remain separate: they "
    "are not instructions, bytes, allocator costs or elapsed-time predictions. "
    "All recursive verifier edges are incidences, so retained/heavy fractions "
    "do not describe distinct original edges or only the root call."
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_record(path):
    return {"path": str(path.resolve()), "sha256": sha(path)}


def load_plan(path):
    cases = base.load_manifest(path)
    expected = []
    for family, n, _ in PLAN:
        spec = {"family": family, "n": n, "density": 16, "intrusion_per_mille": 0}
        expected.append(base.case_id(spec))
    base.require(list(cases) == expected, "manifest differs from the fixed ten-case diagnostic order")
    return cases


def load_capture_metadata(csv_path, log_path, manifest, mode, row_count):
    path = csv_path.with_suffix(".json")
    data = comparison.read_json(path)
    base.require(type(data) is dict and data.get("mode") == mode and
                 type(data.get("exit_status")) is int and data["exit_status"] == 0 and
                 "interruption" in data and data["interruption"] is None,
                 f"{path}: incomplete or failed {mode} capture")
    for field, source in (("output_sha256", csv_path), ("log_sha256", log_path),
                          ("manifest_sha256", manifest)):
        base.require(data.get(field) == sha(source), f"{path}: {field} differs from the input")
    base.require(type(data.get("basic_validated_rows")) is int and
                 data["basic_validated_rows"] == row_count, f"{path}: row count mismatch")
    command = data.get("command")
    base.require(type(command) is list and command and all(type(x) is str for x in command),
                 f"{path}: missing capture command")
    expected = ["--manifest", str(manifest.resolve()), "--mode", mode,
                "--graph-seeds", "3037", "--sampling-seeds", "101",
                "--repetitions", "2", "--warmups", "1"]
    base.require(command[1:] == expected, f"{path}: command differs from the fixed diagnostic protocol")
    for field in ("binary_sha256", "runner_sha256", "analyzer_sha256", "clock_auditor_sha256"):
        base.require(type(data.get(field)) is str and re.fullmatch(r"[0-9a-f]{64}", data[field]),
                     f"{path}: invalid {field}")
    sources = data.get("source_sha256")
    base.require(type(sources) is dict and sources and all(
        type(name) is str and type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value)
        for name, value in sources.items()), f"{path}: malformed source inventory")
    base.require(all(name in sources for name in comparison.prior.PRODUCTION_FILES),
                 f"{path}: incomplete production source inventory")
    registry_path = Path(base.__file__).with_name("work_metrics.hpp")
    base.require(sources.get("benchmark/work_metrics.hpp") == sha(registry_path),
                 f"{path}: capture work registry differs from the parser's registry")
    for field in ("revision", "profile", "platform", "machine"):
        base.require(type(data.get(field)) is str and data[field], f"{path}: missing {field}")
    started = comparison.prior.timestamp(data.get("started_utc"), f"{path}: start")
    finished = comparison.prior.timestamp(data.get("finished_utc"), f"{path}: finish")
    base.require(finished > started, f"{path}: invalid capture interval")
    return data, file_record(path)


def load_references(config_path):
    campaigns, confirmation, selection = comparison.collect(
        comparison.read_json(config_path), config_path.parent)
    base.require(confirmation is None and selection is None,
                 "diagnostic references must be the three original screens, not confirmation")
    expected_counts = {"discovery": 19, "extension": 3, "precision": 5}
    base.require({c["name"] for c in campaigns} == set(expected_counts),
                 "references must contain discovery, extension and precision exactly once")
    for campaign in campaigns:
        base.require(campaign["role"] == "screen" and
                     len(campaign["cases"]) == expected_counts[campaign["name"]] and
                     campaign["graph_seeds"] == GRAPH_SEEDS and
                     campaign["sampling_seeds"] == SAMPLING_SEEDS and
                     campaign["repetitions"] == 2 and campaign["warmups"] == 1,
                     f"{campaign['name']}: original screen protocol differs")
    return {c["name"]: c for c in campaigns}


def check_identity(cases, work, traces, references, work_metadata, trace_metadata):
    base.require(work_metadata["source_sha256"] == trace_metadata["source_sha256"],
                 "work and trace source inventories differ")
    precision = references["precision"]["provenance"]
    base.require(work_metadata["source_sha256"] == precision["source_sha256"],
                 "diagnostic C++ source inventory differs from the frozen precision capture")
    base.require(trace_metadata["binary_sha256"] == precision["binary_sha256"],
                 "native trace binary differs from the frozen precision timing binary")
    for field in ("profile", "platform", "machine", "runner_sha256", "analyzer_sha256", "clock_auditor_sha256"):
        base.require(work_metadata[field] == trace_metadata[field], f"work/trace {field} differs")
    for campaign in references.values():
        provenance = campaign["provenance"]
        for field in ("profile", "platform", "machine"):
            base.require(work_metadata[field] == provenance[field],
                         f"{campaign['name']}: diagnostic {field} differs from the screen")
        base.require(all(work_metadata["source_sha256"][name] == provenance["source_sha256"][name]
                         for name in comparison.prior.PRODUCTION_FILES),
                     f"{campaign['name']}: production source differs from the screen")
    result = []
    for (case, spec), (_, _, source_name) in zip(cases.items(), PLAN):
        campaign = references[source_name]
        base.require(campaign["cases"].get(case) == spec,
                     f"{case}: absent or altered in designated {source_name} screen")
        source_rows = [r for r in campaign["timing"].values() if r["case_id"] == case]
        base.require(len(source_rows) == 4, f"{case}: expected both algorithms and two original repetitions")
        diagnostic_rows = [work[case, 3037, 101, "kkt"], work[case, 3037, "na", "compacting_boruvka"]]
        identities = base.check_fingerprints([*source_rows, *diagnostic_rows, *traces[case, 3037]])
        weighted, topology = identities[case, 3037]
        result.append({**spec, "graph_seed": 3037, "sampling_seed": 101,
                       "input_fingerprint": weighted, "topology_fingerprint": topology,
                       "reference_campaign": source_name, "reference_timed_rows_checked": len(source_rows),
                       "validation": "pass"})
    return result


def normalize_verifier_fractions(work_summary, work_graphs):
    # The shared historical helper uses zero when no verifier was called.
    # This report treats that undefined denominator as unavailable, keeping
    # both the shared helper and all original counter rows unchanged.
    # The fixed single graph/sampling seed makes each aggregate a single row.
    for row in [*work_summary, *work_graphs]:
        if row["mean_verifier_edges"] == 0:
            row["mean_heavy_fraction"] = None


def summarize(cases, work, work_summary, component_graphs):
    aggregated = {(r["case_id"], r["algorithm"]): r for r in work_summary}
    components = {r["case_id"]: r for r in component_graphs}
    summary, normalized = [], []
    for case, spec in cases.items():
        m = spec["m"]
        common = {**spec, "graph_seed": 3037, "kkt_seed": 101,
                  "input_fingerprint": work[case, 3037, 101, "kkt"]["input_fingerprint"],
                  "topology_fingerprint": work[case, 3037, 101, "kkt"]["topology_fingerprint"]}
        pair = dict(common)
        for algorithm, seed in (("kkt", 101), ("compacting_boruvka", "na")):
            row = work[case, 3037, seed, algorithm]
            aggregate = aggregated[case, algorithm]
            for field in ("contraction_edges", "edge_materializations", "initialized_slots", "verifier_edges", "filtered_edges"):
                base.require(aggregate["mean_" + field] == row[field],
                             f"{case}/{algorithm}: singleton work aggregation mismatch for {field}")
            record = {**common, "algorithm": algorithm, "kkt_seed": seed,
                      "contraction_calls": row["contraction_calls"],
                      "sampling_calls": row["sampling_calls"],
                      "root_after_two_vertices": row["root_after_two_vertices"] if algorithm == "kkt" else None,
                      "root_after_two_edges": row["root_after_two_edges"] if algorithm == "kkt" else None}
            for field in ("contraction_edges", "contraction_edge_visits", "contraction_vertices",
                          "edge_materializations", "initialized_slots", "verifier_edges", "filtered_edges",
                          "sampling_edge_visits", "sampled_edges", "kkt_edges", "kkt_vertices",
                          "lca_queries", "verifier_queries", "path_query_visits", "total_work_proxy"):
                record[field] = row[field]
                record[field + "_over_m"] = row[field] / m
            denominator = row["verifier_edges"]
            record["retained_light_incidence_fraction"] = row["filtered_edges"] / denominator if denominator else None
            record["removed_heavy_incidence_fraction"] = 1 - record["retained_light_incidence_fraction"] if denominator else None
            record["validation"] = "pass"
            normalized.append(record)
            for field in ("contraction_edges_over_m", "edge_materializations_over_m", "initialized_slots_over_m",
                          "verifier_edges_over_m", "filtered_edges_over_m", "retained_light_incidence_fraction"):
                pair[algorithm + "_" + field] = record[field]
        component = components[case]
        pair.update(compactor_rounds=component["rounds"],
                    compactor_trace_contraction_edges_over_m=component["contraction_input_over_m"],
                    root_after_two_vertices=work[case, 3037, 101, "kkt"]["root_after_two_vertices"],
                    root_after_two_edges=work[case, 3037, 101, "kkt"]["root_after_two_edges"],
                    root_after_two_edge_fraction=component["after_two_edge_fraction"],
                    root_after_two_component_count=component["after_two_component_count"],
                    root_after_two_effective_count=component["after_two_effective_count"],
                    root_after_two_effective_over_actual=component["after_two_effective_over_actual"],
                    root_after_two_largest_fraction=component["after_two_largest_fraction"], validation="pass")
        base.require(pair["compacting_boruvka_contraction_edges_over_m"] == pair["compactor_trace_contraction_edges_over_m"],
                     f"{case}: normalized compactor volume disagrees with its trace")
        summary.append(pair)
    base.require(len(summary) == 10 and len(normalized) == 20, "derived diagnostic coverage is incomplete")
    for row in [*summary, *normalized]:
        base.require(all(type(value) is not float or math.isfinite(value) for value in row.values()),
                     "nonfinite derived diagnostic value")
    return summary, normalized


def write_report(output, summary, normalized, metadata):
    def fraction(value):
        return "n/a" if value is None else f"{value:.4f}"
    lines = ["# Untimed crossover mechanism diagnostics", "", DESCRIPTION, "",
        "Validated all ten declared cases, 20 work rows and ten complete compactor traces. "
        "Each trace stage has one valid original-component moment record. All graph fingerprints "
        "match their designated complete screen; these FNV fingerprints are consistency checks, "
        "not collision-proof graph equality certificates. Native captures independently certify the MST.", "",
        "The common denominator is the original edge count m=16n. K/C below means KKT / compacting "
        "Borůvka columns, not a runtime ratio. Contraction volume uses the same input-edge counter "
        "for both algorithms; KKT recursive input volume is a separate metric. Instrumented and "
        "native capture binary hashes remain distinct in provenance.", "",
        "| Case | Contraction edges/m K | C | Materializations/m K | C | Initialized slots/m K | C |",
        "|---|---:|---:|---:|---:|---:|---:|"]
    for row in summary:
        values = [row[a + "_" + field] for field in ("contraction_edges_over_m", "edge_materializations_over_m",
                  "initialized_slots_over_m") for a in base.ALGORITHMS]
        lines.append("| " + row["case_id"] + " | " + " | ".join(f"{value:.4f}" for value in values) + " |")
    lines += ["", "| KKT case | Recursive input edges/m | Verifier edges/m | Retained light / verifier incidences | Removed heavy / verifier incidences |",
              "|---|---:|---:|---:|---:|"]
    for row in normalized:
        if row["algorithm"] == "kkt":
            lines.append(f"| {row['case_id']} | {row['kkt_edges_over_m']:.4f} | {row['verifier_edges_over_m']:.4f} | "
                         f"{fraction(row['retained_light_incidence_fraction'])} | {fraction(row['removed_heavy_incidence_fraction'])} |")
    lines += ["", "`filtered_edges` counts retained F-light incidences after verification, not removed edges. "
        "An edge can occur in more than one recursive verifier input. A zero verifier denominator "
        "is n/a (including deterministic compaction), not a measured zero retention fraction.", "",
        "| Case | Compactor rounds | Root edges/m after two | q after two | q_eff after two | q_eff/q | Largest original component/n |",
        "|---|---:|---:|---:|---:|---:|---:|"]
    for row in summary:
        lines.append(f"| {row['case_id']} | {row['compactor_rounds']} | {row['root_after_two_edge_fraction']:.4f} | "
                     f"{row['root_after_two_component_count']} | {row['root_after_two_effective_count']:.2f} | "
                     f"{row['root_after_two_effective_over_actual']:.4f} | {row['root_after_two_largest_fraction']:.6f} |")
    lines += ["", "Stage zero is the original graph. Stage r follows r compactor rounds; the final "
        "original partition has q=1 even though production stores an empty quotient with zero vertices. "
        "q_eff=n²/Σ(size²), and q_eff/q=1 only for equal component sizes. The first two residual "
        "dimensions match KKT's root counters; every compactor input/output volume matches its trace.", "",
        "One graph and one sampling seed provide case-specific diagnostics. These ten cases do not "
        "cover intermediate spatial sizes, the density-four controls, random-tree control or 8M G(n,m). "
        "No intermediate transition or elapsed-time cause is inferred. Wider gaps change their relative "
        "ordering as well as tie frequency, so the precision ablation is not an isolated tie-rule change. "
        "The comparison concerns whole continuation strategies, not an isolated causal effect of sampling.", "",
        "[Per-case table](case_summary.csv), [normalized algorithm work](normalized_work.csv), "
        "[complete validated work rows](validated_work.csv), [shared work aggregation](work_summary.csv), "
        "[original graph identities](input_matches.csv), [per-stage components](component_stages.csv), "
        "[component graph summaries](component_graphs.csv), [complete contraction rounds](contraction_rounds.csv), "
        "[provenance](provenance.json).", "", "Inputs:", ""]
    for name, item in metadata["inputs"].items():
        lines.append(f"- [{name}]({os.path.relpath(item['path'], output.resolve())})")
    (output / "report.md").write_text("\n".join(lines).rstrip() + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("work-csv", "trace-csv", "log", "manifest", "reference-config"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--graph-seeds", type=base.seed_bank, default=GRAPH_SEEDS)
    parser.add_argument("--sampling-seeds", type=base.seed_bank, default=SAMPLING_SEEDS)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    base.require(args.graph_seeds == GRAPH_SEEDS and args.sampling_seeds == SAMPLING_SEEDS,
                 "this diagnostic plan requires graph seed3037 and sampling seed101")
    base.require(args.validate_only or args.output_dir is not None, "--output-dir is required unless --validate-only")
    cases = load_plan(args.manifest)
    work = base.load_work(args.work_csv, cases, GRAPH_SEEDS, SAMPLING_SEEDS)
    traces = base.load_traces(args.trace_csv, cases, GRAPH_SEEDS)
    base.crosscheck({}, work, traces, SAMPLING_SEEDS)
    moment_rows = moments.load_moments(args.log, traces)
    stages, component_graphs, component_summary = moments.derive(cases, GRAPH_SEEDS, traces, moment_rows)
    work_summary, work_graphs, trace_summary, rounds = base.aggregate_work(work, traces, cases, GRAPH_SEEDS, SAMPLING_SEEDS)
    normalize_verifier_fractions(work_summary, work_graphs)
    work_log = args.work_csv.with_suffix(".log")
    base.require(args.log.resolve() == args.trace_csv.with_suffix(".log").resolve(),
                 "trace moment log must be the capture's adjacent log")
    work_meta, work_record = load_capture_metadata(args.work_csv, work_log, args.manifest, "work", len(work))
    trace_meta, trace_record = load_capture_metadata(args.trace_csv, args.log, args.manifest, "trace", len(moment_rows))
    references = load_references(args.reference_config.resolve())
    identities = check_identity(cases, work, traces, references, work_meta, trace_meta)
    summary, normalized = summarize(cases, work, work_summary, component_graphs)
    metadata = {"schema": "crossover_diagnostics_v1", "validation": "pass", "description": DESCRIPTION,
        "case_count": len(cases), "work_rows": len(work), "trace_graphs": len(traces), "trace_stages": len(moment_rows),
        "derived_stages_including_zero": len(stages), "graph_seeds": GRAPH_SEEDS, "sampling_seeds": SAMPLING_SEEDS,
        "rows_removed": 0, "rows_adjusted": 0, "timing_observations_exported": 0,
        "clock_scope": "Original reference screens fully clock-validated; untimed diagnostic durations are not solver measurements.",
        "inputs": {name: file_record(getattr(args, name)) for name in
                   ("work_csv", "trace_csv", "log", "manifest", "reference_config")},
        "capture_metadata": {"work": work_record, "trace": trace_record},
        "capture_binaries": {"work": work_meta["binary_sha256"], "trace": trace_meta["binary_sha256"]},
        "capture_source_sha256": work_meta["source_sha256"],
        "reference_inputs": {name: {field: file_record(path) for field, path in c["paths"].items()}
                             for name, c in references.items()},
        "source_sha256": {Path(module.__file__).name: sha(Path(module.__file__))
                          for module in (base, moments, comparison, comparison.prior, comparison.clocks)},
        "script_sha256": sha(Path(__file__)),
        "work_registry_sha256": sha(Path(base.__file__).with_name("work_metrics.hpp"))}
    metadata["inputs"]["work_log"] = file_record(work_log)
    if args.validate_only:
        print(json.dumps(metadata, indent=2, allow_nan=False)); return
    args.output_dir.mkdir(parents=True, exist_ok=True)
    metadata["derived_csv_sha256"] = {}
    for name, rows in (("case_summary", summary), ("normalized_work", normalized), ("input_matches", identities),
                       ("validated_work", list(work.values())), ("work_summary", work_summary), ("work_graphs", work_graphs),
                       ("trace_summary", trace_summary), ("contraction_rounds", rounds), ("component_stages", stages),
                       ("component_graphs", component_graphs), ("component_summary", component_summary)):
        destination = args.output_dir / (name + ".csv")
        moments.write_csv(destination, rows)
        metadata["derived_csv_sha256"][destination.name] = sha(destination)
    (args.output_dir / "provenance.json").write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n")
    write_report(args.output_dir, summary, normalized, metadata)
    print(f"Validated {len(cases)} diagnostic cases, {len(work)} work rows and {len(moment_rows)} trace stages; wrote {args.output_dir}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as error:
        print("crossover diagnostics: " + str(error), file=sys.stderr)
        sys.exit(1)
