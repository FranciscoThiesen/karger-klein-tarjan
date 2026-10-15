#!/usr/bin/env python3
"""Post-screen untimed work capture; serial, bounded, and independently checked."""
import argparse
import csv
import json
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "benchmark"))
import run_mst_search as capture
import recover_mst_search as recovery

OUT = Path(__file__).resolve().parent
STUDY = OUT.parent
FIELDS = ("contraction_edges", "contraction_edge_visits", "initialized_slots",
          "sampling_edge_visits", "verifier_edges", "verifier_tree_edges",
          "edge_materializations", "root_after_two_vertices", "root_after_two_edges",
          "filtered_edges", "kkt_calls", "max_depth")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def fingerprint_lookup():
    lookup = {}
    with (STUDY / "screen.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            key = row["variant"], row["case_id"], int(row["graph_seed"]), int(row["kkt_seed"])
            fingerprints = int(row["input_fingerprint"]), int(row["topology_fingerprint"])
            require(key not in lookup or lookup[key] == fingerprints, "inconsistent screen fingerprint")
            lookup[key] = fingerprints
    return lookup


def analyze(metadata):
    require(metadata["validation"] == "pass" and len(metadata["children"]) == 20,
            "work capture incomplete")
    lookup = fingerprint_lookup()
    cases = capture.load_manifest(STUDY / "manifest.csv")
    records = {}
    expected_fields = set(re.findall(r'\{"([a-z_]+)",',
                                    (ROOT / "benchmark/work_metrics.hpp").read_text()))
    require(expected_fields and all(field in expected_fields for field in FIELDS), "invalid work field inventory")
    for child in metadata["children"]:
        require(child["exit_status"] == 0, "nonzero diagnostic child")
        path = Path(child["output"])
        require(capture.sha(path) == child["output_sha256"], "raw output changed")
        data = json.loads(path.read_text())
        variant, case_id = child["variant"], child["case_id"]
        case = cases[case_id]
        require(data["schema"] == "multigraph_work_v1" and data["validation"] == "pass" and
                data["variant"] == variant, "invalid diagnostic result")
        for field in ("family", "n", "density", "m"):
            require(data[field] == case[field], "case identity mismatch: " + field)
        require(data["graph_seed"] == 2000003 and data["kkt_seed"] == 607, "wrong diagnostic seed")
        require((data["input_fingerprint"], data["topology_fingerprint"]) ==
                lookup[(variant, case_id, 2000003, 607)], "diagnostic differs from timed input")
        require(set(data["algorithms"]) == {"kkt", "compacting_boruvka"}, "unexpected diagnostic algorithms")
        for stats in data["algorithms"].values():
            require(set(stats) == expected_fields and all(type(value) is int and value >= 0 for value in stats.values()),
                    "invalid stats field inventory or counter")
            require(stats["current_depth"] == 0 and stats["hash_insert_items"] == data["n"] - 1,
                    "invalid recursion/result counters")
        key = case_id, variant
        require(key not in records, "duplicate work case/variant")
        records[key] = data
    require(set(records) == {(case_id, variant) for case_id in cases for variant in ("reference", "multigraph")},
            "incomplete work matrix")
    rows = []
    for case_id in cases:
        reference, candidate = (records[(case_id, variant)] for variant in ("reference", "multigraph"))
        require(reference["algorithms"]["compacting_boruvka"] == candidate["algorithms"]["compacting_boruvka"],
                "unchanged compactor counters differ: " + case_id)
        for field in FIELDS:
            first, second = (item["algorithms"]["kkt"][field] for item in (reference, candidate))
            rows.append({"case_id": case_id, "counter": field, "reference": first, "multigraph": second,
                         "ratio": second / first if first else None})
    with (OUT / "counter_comparisons.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=("case_id", "counter", "reference", "multigraph", "ratio"))
        writer.writeheader(); writer.writerows(rows)
    flattened = []
    for (case_id, variant), data in records.items():
        for algorithm, stats in data["algorithms"].items():
            flattened.append({"case_id": case_id, "variant": variant, "algorithm": algorithm, **stats})
    with (OUT / "all_counters.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=("case_id", "variant", "algorithm", *sorted(expected_fields)))
        writer.writeheader(); writer.writerows(flattened)
    summary = {"validation": "pass", "diagnostic_children": len(records), "cases": len(cases),
               "solver_outputs": 2 * len(records), "screen_fingerprints_matched": len(records),
               "all_compactor_fields_equal": True, "work_counter_fields": len(expected_fields),
               "metadata_sha256": capture.sha(OUT / "capture.json"),
               "screen_sha256": capture.sha(STUDY / "screen.csv"),
               "comparisons_sha256": capture.sha(OUT / "counter_comparisons.csv"),
               "all_counters_sha256": capture.sha(OUT / "all_counters.csv")}
    write_json(OUT / "analysis.json", summary)
    return summary


def run():
    require(not (OUT / "capture.json").exists(), "refusing to overwrite work capture")
    builds = {variant: json.loads((OUT / (variant + "-build.json")).read_text())
              for variant in ("reference", "multigraph")}
    sources = capture.source_inventory(ROOT)
    for variant, record in builds.items():
        require(record["source_sha256"] == sources and capture.sha(record["binary"]) == record["binary_sha256"],
                "stale diagnostic build: " + variant)
    cases = capture.load_manifest(STUDY / "manifest.csv")
    require(len(cases) == 10, "expected the frozen ten-case screen")
    sampler = recovery.BoundedSampler(recovery.LibprocProvider())
    def interrupted(signum, _frame):
        raise KeyboardInterrupt("work capture received signal " + str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    metadata = {"schema": "multigraph_untimed_work_capture_v1", "started_utc": capture.now(),
                "validation": "running", "source_sha256": sources, "build_records": builds,
                "capture_script_sha256": capture.sha(__file__), "manifest_sha256": capture.sha(STUDY / "manifest.csv"),
                "screen_sha256": capture.sha(STUDY / "screen.csv"),
                "resource_rule": {"rss_limit_kib": 40 * 1024**2, "poll_seconds": 2,
                                  "child_timeout_seconds": 600, "unavailable_limit": 3},
                "children": [], "note": "Untimed logical counters only; process duration is capture diagnostics, not solver timing."}
    process = None
    try:
        (OUT / "cases").mkdir()
        for case_id, case in cases.items():
            for variant, build in builds.items():
                require(not sampler.poisoned, "sampler poisoned before child")
                require(capture.source_inventory(ROOT) == sources and capture.sha(build["binary"]) == build["binary_sha256"],
                        "source or binary changed during diagnostic capture")
                prefix = OUT / "cases" / (case_id + "_" + variant)
                command = [build["binary"], case["family"], str(case["n"]), str(case["density"]), "2000003", "607"]
                child = {"variant": variant, "case_id": case_id, "command": command,
                         "started_utc": capture.now(), "output": str(prefix.with_suffix(".json")),
                         "stderr": str(prefix.with_suffix(".stderr")), "rss_log": str(prefix.with_suffix(".rss.jsonl"))}
                metadata["children"].append(child)
                write_json(OUT / "capture.json", metadata)
                with Path(child["output"]).open("w") as output, Path(child["stderr"]).open("w") as stderr, \
                        Path(child["rss_log"]).open("w") as rss:
                    started = time.monotonic()
                    process = subprocess.Popen(command, stdout=output, stderr=stderr, start_new_session=True)
                    child["pid"] = process.pid
                    unavailable = 0
                    peak = 0
                    while process.poll() is None:
                        require(time.monotonic() - started < 600, "diagnostic child timed out")
                        observation = sampler.sample(process.pid)
                        rss.write(json.dumps(observation) + "\n"); rss.flush()
                        require(not sampler.poisoned, "diagnostic RSS sampler timed out")
                        if observation["validation"] == "pass":
                            unavailable = 0
                            peak = max(peak, observation["rss_kib"])
                            require(observation["rss_kib"] <= 40 * 1024**2, "diagnostic RSS limit exceeded")
                        else:
                            unavailable += 1
                            require(unavailable < 3, "three unavailable diagnostic RSS observations")
                        try:
                            process.wait(timeout=min(2, max(.001, 600 - (time.monotonic() - started))))
                        except subprocess.TimeoutExpired:
                            pass
                    child.update(exit_status=process.returncode, finished_utc=capture.now(),
                                 capture_duration_seconds=time.monotonic() - started,
                                 sampled_peak_rss_kib=peak,
                                 rss_monitor=recovery.recovery_monitor(sampler.events[process.pid]))
                    process = None
                for label in ("output", "stderr", "rss_log"):
                    child[label + "_sha256"] = capture.sha(child[label])
                require(child["exit_status"] == 0, "diagnostic child failed")
                require(json.loads(Path(child["output"]).read_text())["validation"] == "pass", "diagnostic rejected its result")
                write_json(OUT / "capture.json", metadata)
                print(case_id, variant, "pass", flush=True)
        require(capture.source_inventory(ROOT) == sources, "source changed at capture completion")
        metadata["validation"] = "pass"
    except BaseException as error:
        metadata.update(validation="failed", error=repr(error))
        if process is not None:
            metadata["termination"] = recovery.bounded_terminate(process, sampler)
        raise
    finally:
        metadata["finished_utc"] = capture.now()
        write_json(OUT / "capture.json", metadata)
    print(json.dumps(analyze(metadata)), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reanalyze", action="store_true")
    args = parser.parse_args()
    if args.reanalyze:
        print(json.dumps(analyze(json.loads((OUT / "capture.json").read_text()))))
    else:
        run()
