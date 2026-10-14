#!/usr/bin/env python3
"""Validate interrupted native evidence without changing a failed capture.

prefix validates B's exact first 60 children, including the completed native
child whose wrapper validation was interrupted. power correlates that prefix
with one separately archived power query. compose requires a successful NEW
12-child recovery capture. Original B is never assigned validation=pass.
No command here launches a native solver or edits an existing artifact.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
from pathlib import Path
import statistics

import analyze_mst_search as analysis
import assess_attachment_confirmation as rule
import audit_mst_search_power as power
import run_mst_search as capture

require, same, track, read_json = rule.require, rule.same, rule.track, analysis.read_json
PREFIX_CHILDREN = 60
ROW_KEY = ("case_id", "graph_seed", "kkt_seed", "phase", "repetition", "algorithm")
SOURCE_FIELDS = ("binary_sha256", "binary_profile", "profile", "source_sha256", "build_recipe_sha256")


def save(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write("\n")


def check_inputs(inputs):
    for name, digest in inputs.items():
        same(rule.sha(name), digest, "immutable input " + name)


def bind_inventory(root, info, inputs):
    require(analysis.NATIVE_FILES <= set(info["source_sha256"]), "missing native source inventory")
    for name, digest in info["source_sha256"].items():
        require(not Path(name).is_absolute() and ".." not in Path(name).parts, "unsafe native inventory path")
        track(root/name, inputs, digest)
    same(set(info["build_recipe_sha256"]), {"Makefile"}, "build recipe inventory")
    track(root/"Makefile", inputs, info["build_recipe_sha256"]["Makefile"])
    same(set(info["python_source_sha256"]), set(capture.helpers()), "frozen helper paths")
    rule.bind(info["python_source_sha256"], inputs)
    track(info["binary"], inputs, info["binary_sha256"])


def serialized(rows):
    return [{field: str(row[field]) for field in capture.FIELDS} for row in rows]


def prefix_evidence(root, folder):
    """Read-only native certification; deliberately NOT a successful B loader."""
    inputs = {}; track(__file__, inputs); track(rule.__file__, inputs)
    expected, plans = rule.frozen_plans(root, folder, inputs)
    raw = folder/"attachment-confirmation-b-timing.csv"
    info = read_json(track(raw.with_suffix(".json"), inputs))
    controller = read_json(track(folder/"attachment-confirmation-b-controller.json", inputs))
    for field, value in (("schema", "mst_search_capture_v1"), ("validation", "failed"),
                         ("case_order", plans["b"]), ("graph_seeds", list(rule.GRAPHS)),
                         ("sampling_seeds", list(rule.SAMPLES)), ("algorithms", list(capture.ALGORITHMS)),
                         ("repetitions", 5), ("warmups", 1), ("rows_removed", 0), ("rows_adjusted", 0)):
        analysis.equal(info, field, value, "interrupted capture")
    require(type(info.get("error")) is str and "KeyboardInterrupt" in info["error"], "missing recorded capture interruption")
    for field, value in (("schema", "attachment_confirmation_controller_v1"), ("validation", "failed"),
                         ("campaign", "attachment-confirmation-b"), ("capture_exit_status", -2),
                         ("frozen_declaration_revision", rule.REVISION)):
        analysis.equal(controller, field, value, "interrupted controller")
    require(not controller.get("native_process_may_still_be_running"), "unknown native exit")
    rule.bind(controller["retained_artifact_sha256"], inputs)
    rule.bind(controller["frozen_declaration_sha256"], inputs)
    track(folder/"run_attachment_confirmation.py", inputs, controller["controller_sha256"])
    same(controller["binary_sha256"], info["binary_sha256"], "controller/native binary")
    same(controller["manifest_sha256"], info["manifest_sha256"], "controller/manifest")
    manifest = track(folder/"attachment-confirmation-b.csv", inputs, info["manifest_sha256"])
    same(info["manifest"], str(manifest), "recorded manifest path")
    same(list(capture.load_manifest(manifest)), plans["b"], "native manifest order")
    bind_inventory(root, info, inputs)
    track(raw, inputs, info["output_sha256"])
    interventions = {}
    for name in ("attachment-monitor-recovery-probe.json", "attachment-monitor-recovery-action.json",
                 "attachment-monitor-recovery-result.json", "attachment-monitor-stop.json"):
        path = track(folder/"validation"/name, inputs)
        interventions[name] = read_json(path)
    stop = interventions["attachment-monitor-stop.json"]
    for field, value in (("signal", "SIGTERM"), ("native_measurements_modified", False), ("native_cases_rerun", False)):
        analysis.equal(stop, field, value, "wrapper stop evidence")
    # The initial stop record predates exit confirmation. Native exit 0 and the
    # controller's finalized failure are required separately above/below.
    require(analysis.timestamp(info["started_utc"]) <= analysis.timestamp(stop["utc"]) <=
            analysis.timestamp(info["finished_utc"]) <= analysis.timestamp(controller["finished_utc"]),
            "stop/exit evidence chronology differs")
    matrix = list(itertools.product(plans["b"], rule.GRAPHS, rule.SAMPLES))
    require(len(info["captures"]) == PREFIX_CHILDREN, "prefix is not exactly 60 native children")
    start, finish = analysis.monotonic_interval(info); previous_finish = start
    rows, diagnostics, resources, parts, certificates = [], [], [], [], []
    for index, ((case, g, s), item) in enumerate(zip(matrix, info["captures"]), 1):
        context = f"prefix child {index}"
        for field, value in (("case_id", case), ("graph_seed", g), ("kkt_seed", s), ("exit_status", 0)):
            analysis.equal(item, field, value, context)
        require(not item.get("native_process_may_still_be_running"), "unknown child exit")
        if index < PREFIX_CHILDREN:
            for field, value in (("validation", "pass"), ("interruption", None), ("rows", 30)):
                analysis.equal(item, field, value, context)
        else:
            require("validation" not in item and "rows" not in item and "certificate" not in item,
                    "last wrapper status no longer matches interrupted evidence")
            require(type(item.get("interruption")) is str and "KeyboardInterrupt" in item["interruption"],
                    "last child lacks recorded wrapper interruption")
        child_start, child_finish = analysis.monotonic_interval(item)
        require(previous_finish <= child_start < child_finish <= finish, "invalid native child monotonic schedule")
        previous_finish = child_finish
        for key in ("started_utc", "finished_utc"): analysis.timestamp(item[key])
        analysis.positive(item["monotonic_elapsed_seconds"], "child elapsed interval")
        child = raw.with_name(raw.stem+"_cases")/f"{index:04d}_{case}_g{g}_s{s}.csv"
        paths = {"csv": (child, "output_sha256"), "log": (child.with_suffix(".log"), "log_sha256"),
                 "rss_log": (child.with_suffix(".rss.jsonl"), "rss_sha256")}
        for field, (path, hash_field) in paths.items():
            same(item[field], str(path), "child artifact path"); track(path, inputs, item[hash_field])
        spec = expected[case]
        command = [info["binary"], "--family", spec["family"], "--n", str(spec["n"]), "--density", "16",
                   "--graph-seed", str(g), "--kkt-seed", str(s), "--repetitions", "5", "--warmups", "1"]
        same(item["command"], command, "native command")
        child_rows, child_diagnostics = capture.check_rows(child, spec, g, s, 5, 1)
        certificate = capture.check_certificate(paths["log"][0], child_rows)
        if index < PREFIX_CHILDREN:
            same(item["certificate"], certificate, "recorded reference certificate")
            same(item["flagged_calls"], sum(bool(x["diagnostic_flags"]) for x in child_diagnostics), "child flag count")
        observations = analysis.check_rss(paths["rss_log"][0], item, info["resource_rule"])
        resources.append({"original_child_index": index, "case_id": case, "graph_seed": g, "kkt_seed": s,
                          **{key: item[key] for key in ("rss_observations", "rss_unavailable", "sampled_peak_rss_kib")},
                          "last_rss_monotonic_ns": observations[-1]["monotonic_ns"],
                          "wrapper_finish_minus_last_observation_ns": child_finish-observations[-1]["monotonic_ns"],
                          "continuous_resource_coverage_claimed": False})
        parts.extend({**{key: row[key] for key in ROW_KEY}, "source_part": "interrupted_prefix",
                      "original_child_index": index, "source_csv": str(child), "source_csv_sha256": item["output_sha256"]}
                     for row in child_rows)
        certificates.append({"original_child_index": index, "native_exit_status": 0,
                             "original_wrapper_validation": item.get("validation", "not_finalized"),
                             "independent_post_stop_certificate_validation": "pass", "certificate": certificate})
        rows.extend(child_rows); diagnostics.extend(child_diagnostics)
    require(len(rows) == 1800 and len(parts) == 1800, "prefix call matrix differs")
    capture.check_fingerprints(rows)
    same(info["capture_clock_flags"], capture.capture_clock_flags(info), "retained capture flags")
    same(rule.read_csv(raw, capture.FIELDS), serialized(rows[:-30]), "original combined CSV must contain exactly first 59 children")
    same(info["call_diagnostics"], diagnostics[:-30], "original combined diagnostics must cover first 59 children")
    check_inputs(inputs)
    return {"info": info, "controller": controller, "interventions": interventions, "rows": rows,
            "diagnostics": diagnostics, "resources": resources, "source_parts": parts,
            "certificates": certificates, "inputs": inputs, "expected": expected, "plans": plans}


def diagnostic_rows(rows):
    return [{**row, "diagnostic_flags": ";".join(row["diagnostic_flags"])} for row in rows]


def write_tables(output, rows, diagnostics, parts, resources):
    tables = analysis.aggregate(rows)
    tables.update(validated_calls=rows, call_diagnostics=diagnostic_rows(diagnostics),
                  source_parts=parts, resources=resources)
    for name, values in tables.items(): analysis.write_csv(output/(name+".csv"), values)
    return tables


def prefix(root, folder, output):
    require(not output.exists(), "refusing to overwrite prefix evidence")
    data = prefix_evidence(root, folder); output.mkdir(parents=True)
    write_tables(output, data["rows"], data["diagnostics"], data["source_parts"], data["resources"])
    save(output/"native_certificates.json", data["certificates"])
    (output/"README.md").write_text("# Validated interrupted B prefix\n\n"
        "All 60 native children exited zero and each of their 1,800 calls passed the frozen row and certificate checks. "
        "This post-stop validation includes native child 60, whose wrapper validation never finalized. Original B "
        "remains failed; its unmodified combined CSV contains only children 1–59 (1,770 calls). No call is rerun, "
        "changed, excluded, or attributed to a successful frozen campaign.\n\n"
        "The RSS records are retained but do not establish continuous coverage: the sampler stalled and caused "
        "the wrapper interruption. The last child’s wrapper interval includes the post-native stall. "
        "Native per-call clocks, not that wrapper duration, are used in timing tables. Every clock flag and "
        "control remains in these tables. Recovery of children 61–72 is a separate declared execution.\n")
    record = {"schema": "attachment_interrupted_prefix_v1", "validation": "pass",
              "validation_scope": "completed native evidence only", "original_capture_validation": "failed",
              "original_controller_validation": "failed", "frozen_execution_completed": False,
              "native_children": 60, "checked_rows": 1800, "timed_rows": 1500, "warmup_rows": 300,
              "original_combined_children": 59, "original_combined_rows": 1770,
              "last_wrapper_child_finalized": False, "flagged_calls": sum(bool(r["diagnostic_flags"]) for r in data["diagnostics"]),
              "capture_metadata": data["info"], "controller_metadata": data["controller"],
              "intervention_evidence": data["interventions"], "rows_removed": 0, "rows_adjusted": 0,
              "input_sha256": data["inputs"], "derived_sha256": {p.name: rule.sha(p) for p in output.iterdir()}}
    save(output/"provenance.json", record)
    print(json.dumps({"validation": "pass", "native_children": 60, "calls": 1800, "original_capture_validation": "failed"}))


def load_prefix(root, folder, output):
    data = prefix_evidence(root, folder)
    provenance = read_json(track(output/"provenance.json", data["inputs"]))
    for field, value in (("schema", "attachment_interrupted_prefix_v1"), ("validation", "pass"),
                         ("original_capture_validation", "failed"), ("frozen_execution_completed", False),
                         ("native_children", 60), ("checked_rows", 1800), ("rows_removed", 0), ("rows_adjusted", 0)):
        analysis.equal(provenance, field, value, "validated prefix")
    same(provenance["capture_metadata"], data["info"], "prefix capture snapshot")
    same(provenance["controller_metadata"], data["controller"], "prefix controller snapshot")
    rule.bind(provenance["input_sha256"], data["inputs"])
    for name, digest in provenance["derived_sha256"].items():
        require(Path(name).name == name, "nonlocal prefix derived path"); track(output/name, data["inputs"], digest)
    same(rule.read_csv(output/"validated_calls.csv", capture.FIELDS), serialized(data["rows"]), "prefix calls versus native originals")
    return data


def audit_power(root, folder, prefix_dir, output):
    data = load_prefix(root, folder, prefix_dir); inputs = data["inputs"]
    require(not (output/"audit.json").exists(), "refusing to overwrite prefix power audit")
    query = read_json(track(output/"query.json", inputs))
    for field, value in (("schema", "scoped_prefix_power_query_v1"), ("query_count", 1),
                         ("validation", "pass"), ("exit_status", 0)):
        analysis.equal(query, field, value, "single archived power query")
    require(analysis.timestamp(query["started_utc"]) >= analysis.timestamp(data["info"]["finished_utc"]),
            "power query predates final interruption")
    for name in ("pmset.log", "pmset.stderr"): track(output/name, inputs, query["output_sha256"][name])
    track(power.__file__, inputs)
    events, malformed, reversals = power.parse_events((output/"pmset.log").read_text(errors="replace"))
    intervals = power.sleep_intervals(events)
    calls = power.correlate(data["rows"], events, intervals)
    low = min(min(r["utc_start_ns"], r["utc_end_ns"]) for r in data["rows"])
    high = max(max(r["utc_start_ns"], r["utc_end_ns"]) for r in data["rows"])
    scoped_intervals = [{"interval_index": i, **interval} for i, interval in enumerate(intervals)
                        if power.intersection(low, high, interval["start_ns"], interval["end_ns"] or high)]
    referenced = {int(value) for call in calls for value in call["nearby_power_event_lines"].split(";") if value}
    for item in scoped_intervals:
        referenced.update(item["sleep_event_lines"])
        if item["wake_event_line"] is not None: referenced.add(item["wake_event_line"])
    scoped_events = [event for event in events if low <= event["utc_ns"] <= high or event["line_number"] in referenced]
    save(output/"events.json", {"events": events, "potential_sleep_intervals": intervals,
                               "malformed_event_lines": malformed, "source_event_timestamp_reversals": reversals})
    analysis.write_csv(output/"call_power_associations.csv", calls)
    attempts = power.inhibition_records([folder/"attachment-confirmation-b-power-inhibition.json"])
    for attempt in attempts: track(attempt["path"], inputs, attempt["sha256"])
    info = data["info"]
    utc_elapsed = (power.iso_ns(info["finished_utc"])-power.iso_ns(info["started_utc"]))/1e9
    record = {"schema": "interrupted_prefix_power_audit_v1", "validation": "pass" if not malformed else "incomplete",
              "scope": "all 1800 certified native calls from original B children 1 through 60",
              "original_capture_validation": "failed", "frozen_execution_completed": False,
              "checked_calls": len(calls), "timed_calls": 1500, "warmup_calls": 300,
              "calls_with_nominal_sleep_overlap": sum(bool(r["nominal_logged_sleep_overlap_ns"]) for r in calls),
              "timed_calls_with_nominal_sleep_overlap": sum(r["phase"] == "timed" and bool(r["nominal_logged_sleep_overlap_ns"]) for r in calls),
              "calls_near_power_event": sum(bool(r["nearby_power_event_lines"]) for r in calls),
              "utc_unalignable_calls": sum(not r["utc_alignable"] for r in calls),
              "recorded_clock_flagged_calls": sum(bool(r["diagnostic_flags"]) for r in data["diagnostics"]),
              "query": query, "native_call_envelope_ns": [low, high], "scoped_events": scoped_events,
              "scoped_sleep_intervals": scoped_intervals, "malformed_event_lines_count": len(malformed),
              "source_timestamp_reversals_count": len(reversals), "assertion_attempts": attempts,
              "failed_wrapper_utc_elapsed_seconds": utc_elapsed,
              "failed_wrapper_monotonic_elapsed_seconds": info["monotonic_elapsed_seconds"],
              "failed_wrapper_utc_minus_monotonic_seconds": utc_elapsed-info["monotonic_elapsed_seconds"],
              "capture_clock_flags": info["capture_clock_flags"],
              "interpretation": "Timestamp correlation only; no call excluded or corrected. The failed wrapper interval includes a post-native sampler stall and is not solver elapsed time. Sleep-to-first-Wake/DarkWake intervals are logged transitions, not measured CPU inactivity. One-second timestamp resolution, missing/reversed records and UTC reversals limit attribution. Absence of events does not prove stable frequency, no contention or a quiet host. Sleep inhibition was not verified; retained caffeinate failure records remain applicable.",
              "rows_removed": 0, "rows_adjusted": 0, "input_sha256": inputs,
              "output_sha256": {name: rule.sha(output/name) for name in ("call_power_associations.csv", "events.json")}}
    check_inputs(inputs); save(output/"audit.json", record)
    (output/"README.md").write_text(f"# Interrupted-prefix power correlation\n\n{len(calls)} native calls retained; "
        f"{record['calls_with_nominal_sleep_overlap']} overlap a nominal logged Sleep–Wake/DarkWake interval; "
        f"{record['recorded_clock_flagged_calls']} carry clock flags. These counts include checked warmups. "
        "Original B remains failed. No performance observation is adjusted or removed.\n\n"+record["interpretation"]+"\n\n"
        "The full machine power history and complete event inventory remain local and ignored. "
        "Published audit.json scopes events to these calls and their enclosing sleep intervals; it retains full-source hashes.\n")
    print(json.dumps({"validation": record["validation"], "calls": len(calls), "sleep_overlap_calls": record["calls_with_nominal_sleep_overlap"]}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prefix", "power"))
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--prefix-dir", type=Path)
    args = parser.parse_args()
    try:
        root = args.repo_root.resolve(strict=True); folder = root/"benchmark/results/search-2026-10-13"
        output = args.output_dir.resolve()
        if args.operation == "prefix": prefix(root, folder, output)
        else:
            require(args.prefix_dir is not None, "power requires --prefix-dir")
            audit_power(root, folder, args.prefix_dir.resolve(strict=True), output)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, "attachment recovery assessment: "+str(error)+"\n")


if __name__ == "__main__": main()
