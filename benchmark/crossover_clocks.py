#!/usr/bin/env python3
"""Validate per-call clocks without deleting or correcting timing observations.

UTC and process CPU readings enclose the original steady-clock interval. Their
small boundary overhead differs. Large differences are descriptive flags, not
proof of host sleep or reasons to trim rows. CPU summaries are secondary and do
not replace the predeclared steady-clock performance metric.
"""
import argparse
import hashlib
import json
from pathlib import Path

import analyze_continuation as base

PREFIX = "call_clock_v1 "
FIELDS = {"case_id", "graph_seed", "sampling_seed", "phase", "repetition", "order",
          "algorithm", "utc_start_ns", "utc_end_ns", "process_cpu_start_ns",
          "process_cpu_end_ns", "process_cpu_elapsed_ns", "steady_elapsed_ns", "validation"}
IDENTITY = ("case_id", "graph_seed", "sampling_seed", "phase", "repetition", "order", "algorithm")
INTEGER_FIELDS = FIELDS - {"case_id", "phase", "algorithm", "validation"}
MAX_NS = 2**63 - 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        base.require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json(value):
    def invalid_constant(value):
        raise ValueError(f"nonfinite JSON constant: {value}")
    return json.loads(value, object_pairs_hook=unique_object, parse_constant=invalid_constant)


def protocol(metadata, metadata_path):
    base.require(isinstance(metadata, dict), "metadata must be a JSON object")
    command = metadata.get("command")
    base.require(isinstance(command, list) and command and
                 all(isinstance(value, str) and value for value in command), "invalid metadata command")
    base.require(len(command) % 2 == 1, "command options must have values")
    options = {}
    for index in range(1, len(command), 2):
        key, value = command[index:index+2]
        base.require(key not in options, "duplicate command option")
        options[key] = value
    expected = {"--manifest", "--mode", "--graph-seeds", "--sampling-seeds", "--repetitions", "--warmups"}
    base.require(set(options) == expected and options["--mode"] == "timing", "unexpected timing command options")
    base.require(metadata.get("mode") == "timing" and type(metadata.get("exit_status")) is int and
                 metadata["exit_status"] == 0 and metadata.get("interruption") is None,
                 "capture did not complete timing successfully")
    manifest = Path(options["--manifest"])
    if not manifest.is_absolute():
        working_directory = metadata.get("working_directory")
        base.require(isinstance(working_directory, str) and Path(working_directory).is_absolute(),
                     "relative manifest needs an absolute metadata working_directory")
        manifest = Path(working_directory) / manifest
    return (manifest, base.seed_bank(options["--graph-seeds"]),
            base.seed_bank(options["--sampling-seeds"]),
            base.integer(options["--repetitions"], "repetitions", 100),
            base.integer(options["--warmups"], "warmups", 100))


def schedule(cases, graph_seeds, sampling_seeds, repetitions, warmups):
    for case in cases:
        for gi, graph in enumerate(graph_seeds):
            for si, seed in enumerate(sampling_seeds):
                for phase, count in (("warmup", warmups), ("timed", repetitions)):
                    for repetition in range(count):
                        for order in (0, 1):
                            yield {"case_id": case, "graph_seed": graph, "sampling_seed": seed,
                                   "phase": phase, "repetition": repetition, "order": order,
                                   "algorithm": base.ALGORITHMS[(order+repetition+gi+si) % 2]}


def timing_key(row, clock=False):
    return (row["case_id"], row["graph_seed"], row["sampling_seed" if clock else "kkt_seed"],
            row["repetition"], row["algorithm"])


def clock_records(path):
    records = []
    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.startswith(PREFIX):
            base.require(not line.startswith("call_clock"), f"line {line_number}: unknown/malformed call-clock prefix")
            continue
        record = parse_json(line[len(PREFIX):])
        base.require(isinstance(record, dict) and set(record) == FIELDS,
                     f"line {line_number}: incorrect call-clock schema")
        for field in INTEGER_FIELDS:
            base.require(type(record[field]) is int and 0 <= record[field] <= MAX_NS,
                         f"line {line_number}: invalid integer {field}")
        base.require(record["validation"] == "pass" and record["phase"] in ("warmup", "timed") and
                     record["algorithm"] in base.ALGORITHMS and isinstance(record["case_id"], str),
                     f"line {line_number}: failed or invalid call identity")
        cpu = record["process_cpu_end_ns"] - record["process_cpu_start_ns"]
        base.require(cpu == record["process_cpu_elapsed_ns"] and cpu > 0 and record["steady_elapsed_ns"] > 0,
                     f"line {line_number}: invalid CPU delta or steady duration")
        records.append(record)
    return records


def audit(csv_path, meta_path):
    csv_path, meta_path = Path(csv_path), Path(meta_path)
    log_path = csv_path.with_suffix(".log")
    metadata = parse_json(meta_path.read_text())
    manifest, graph_seeds, sampling_seeds, repetitions, warmups = protocol(metadata, meta_path)
    for path, field in ((csv_path, "output_sha256"), (log_path, "log_sha256"), (manifest, "manifest_sha256")):
        base.require(sha(path) == metadata.get(field), f"{field}: source differs from capture metadata")
    cases = base.load_manifest(manifest)
    timing = base.load_timing(csv_path, cases, graph_seeds, sampling_seeds, repetitions, warmups)
    expected = list(schedule(cases, graph_seeds, sampling_seeds, repetitions, warmups))
    timed_schedule = [timing_key(record, clock=True) for record in expected if record["phase"] == "timed"]
    base.require(list(timing) == timed_schedule, "CSV rows do not follow the actual command/manifest schedule")
    records = clock_records(log_path)
    base.require(len(records) == len(expected), "incomplete warmup/timed call-clock sequence")
    cpu_timing = {}
    annotated = []
    previous_cpu = None
    previous_utc = None
    for index, (record, identity) in enumerate(zip(records, expected)):
        base.require(all(record[field] == identity[field] for field in IDENTITY),
                     f"call {index}: duplicate, missing or incorrectly ordered identity")
        base.require(previous_cpu is None or record["process_cpu_start_ns"] >= previous_cpu,
                     f"call {index}: cumulative process CPU clock moved backward/overlapped")
        previous_cpu = record["process_cpu_end_ns"]
        utc_delta = record["utc_end_ns"] - record["utc_start_ns"]
        cpu = record["process_cpu_elapsed_ns"]
        steady = record["steady_elapsed_ns"]
        # Use integer arithmetic for the declared max(0.5 seconds, 25% CPU)
        # threshold, retaining fractional-nanosecond comparisons exactly.
        four_threshold = max(2_000_000_000, cpu)
        flags = []
        if utc_delta < 0:
            flags.append("realtime_reversed_within_call")
        if previous_utc is not None and record["utc_start_ns"] < previous_utc:
            flags.append("realtime_reversed_between_calls")
        if 4 * (steady-cpu) > four_threshold:
            flags.append("steady_exceeds_process_cpu")
        if 4 * (cpu-steady) > four_threshold:
            flags.append("process_cpu_exceeds_steady")
        if 4 * abs(utc_delta-steady) > four_threshold:
            flags.append("utc_steady_duration_disagreement")
        previous_utc = record["utc_end_ns"]
        annotated.append({**record, "utc_elapsed_ns": utc_delta,
                          "steady_minus_cpu_ns": steady-cpu, "utc_minus_steady_ns": utc_delta-steady,
                          "diagnostic_flags": flags, "excluded": False})
        if record["phase"] == "timed":
            key = timing_key(record, clock=True)
            base.require(record["steady_elapsed_ns"] == timing[key]["elapsed_ns"],
                         f"call {index}: clock record differs from CSV steady duration")
            cpu_timing[key] = {**timing[key], "elapsed_ns": cpu}
    cpu_cases, cpu_graphs, _, cpu_orders = base.aggregate_timing(
        cpu_timing, cases, graph_seeds, sampling_seeds, repetitions)
    def cpu_names(row):
        rename = {"paired_runtime_ratio": "paired_cpu_ratio", "kkt_median_ns": "kkt_cpu_median_ns",
                  "compacting_boruvka_median_ns": "compacting_boruvka_cpu_median_ns",
                  "graph_min_ratio": "graph_min_cpu_ratio", "graph_max_ratio": "graph_max_cpu_ratio",
                  "kkt_slower_observations": "kkt_higher_cpu_observations"}
        return {rename.get(key, key): value for key, value in row.items()}
    return {"schema": "crossover_clock_audit_v1", "validation": "pass",
            "timing_csv": str(csv_path.resolve()), "timing_sha256": sha(csv_path),
            "metadata": str(meta_path.resolve()), "metadata_sha256": sha(meta_path),
            "log": str(log_path.resolve()), "log_sha256": sha(log_path),
            "manifest": str(manifest.resolve()), "manifest_sha256": sha(manifest),
            "graph_seeds": list(graph_seeds), "sampling_seeds": list(sampling_seeds),
            "repetitions": repetitions, "warmups": warmups,
            "case_count": len(cases), "timed_calls": len(timing),
            "warmup_calls": len(records)-len(timing), "clock_records": len(records),
            "flagged_calls": sum(bool(row["diagnostic_flags"]) for row in annotated),
            "rows_removed": 0, "rows_adjusted": 0,
            "diagnostic_rule": "Flag duration gaps > max(500000000ns, 0.25*process_cpu_elapsed_ns); also flag realtime reversals. Flags retain all rows and do not prove sleep, interference or algorithm cost.",
            "clock_boundaries": "CLOCK_REALTIME and CLOCK_PROCESS_CPUTIME_ID enclose the unchanged steady-clock interval; validation and logging are outside all three. Envelope overhead differs slightly.",
            "cpu_summary_scope": "Secondary process-CPU metric. Pair KKT/compactor within a timed repetition, then median over repetitions, sampling seeds, graph seeds. Graph ranges are not confidence intervals. No flagged calls excluded; steady-clock CSV remains the primary timing evidence.",
            "records": annotated, "cpu_case_summaries": [cpu_names(row) for row in cpu_cases],
            "cpu_graph_summaries": [cpu_names(row) for row in cpu_graphs],
            "cpu_order_summaries": [cpu_names(row) for row in cpu_orders]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timing-csv", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.timing_csv, args.metadata)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(f"Validated {result['timed_calls']} timed and {result['warmup_calls']} warmup clocks; "
          f"{result['flagged_calls']} descriptive flags; no rows excluded")


if __name__ == "__main__":
    main()
