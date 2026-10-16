#!/usr/bin/env python3
"""Capture up to three selected classical checks, serially and without trimming.

This adjunct retains the existing public tuple-input/API boundaries: KKT returns
an ID set, while Kruskal, Prim and ordinary Boruvka return edge tuples. Ordinary
Boruvka is not the separately measured production compacting-Boruvka continuation.
Warmups, every timed observation and diagnostic clock discrepancies are retained.
"""
import argparse
import csv
import datetime
import json
import os
from pathlib import Path
import platform
import signal
import statistics
import subprocess
import time

import analyze_continuation as base
from run_crossover import sha, source_inventory


ALGORITHMS = ("kkt", "kruskal", "prim", "boruvka")
FIELDS = ("case_id", "family", "n", "m", "density", "intrusion_per_mille", "graph_seed", "kkt_seed",
          "input_fingerprint", "topology_fingerprint", "phase", "repetition", "order", "warmups", "algorithm",
          "elapsed_ns", "utc_start_ns", "utc_end_ns", "process_cpu_start_ns", "process_cpu_end_ns",
          "process_cpu_elapsed_ns", "validation")
TEXT_FIELDS = {"case_id", "family", "phase", "algorithm", "validation"}
MAX_NS = 2**63 - 1


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_metadata(path, info):
    path.write_text(json.dumps(info, indent=2, allow_nan=False)+"\n")


def source_helpers():
    return {str(Path(__file__).with_name(name).resolve()): sha(Path(__file__).with_name(name))
            for name in (Path(__file__).name, "run_crossover.py", "crossover_clocks.py", "analyze_continuation.py")}


def reference_fingerprints(path, cases, graph_seed):
    """Bind selected inputs; do not claim to revalidate the full pilot protocol."""
    if path is None:
        return {}
    result = {}
    for context, raw in base.read_csv(path, base.TIMING_FIELDS):
        if raw["case_id"] not in cases or raw["graph_seed"] != str(graph_seed):
            continue
        row = base.parse_prefix(raw, cases, (graph_seed,), context)
        value = (row["input_fingerprint"], row["topology_fingerprint"])
        base.require(row["case_id"] not in result or result[row["case_id"]] == value,
                     context+": reference input fingerprints differ")
        result[row["case_id"]] = value
    base.require(set(result) == set(cases), "reference timing CSV does not cover every selected graph")
    return result


def check_rows(path, spec, graph_seed, kkt_seed, repetitions, warmups, reference):
    rows = []
    for context, raw in base.read_csv(path, FIELDS):
        row = dict(raw)
        for field in FIELDS:
            if field not in TEXT_FIELDS:
                row[field] = base.integer(raw[field], context+" "+field,
                    MAX_NS if field.endswith("_ns") else base.UINT64_MAX)
        for field in ("case_id", "family", "n", "m", "density", "intrusion_per_mille"):
            base.require(row[field] == spec[field], context+": fixture identity differs from manifest")
        base.require(row["graph_seed"] == graph_seed and row["kkt_seed"] == kkt_seed and
                     row["warmups"] == warmups and row["validation"] == "pass",
                     context+": seed, warmup or exact-MST validation mismatch")
        base.require(row["elapsed_ns"] > 0 and row["utc_start_ns"] > 0 and row["utc_end_ns"] > 0 and
                     row["process_cpu_start_ns"] >= 0 and
                     row["process_cpu_end_ns"]-row["process_cpu_start_ns"] == row["process_cpu_elapsed_ns"] > 0,
                     context+": invalid steady/process-CPU duration or clock endpoint")
        rows.append(row)
    expected = [(phase, repetition, order, ALGORITHMS[(order+repetition) % 4])
                for phase, count in (("warmup", warmups), ("timed", repetitions))
                for repetition in range(count) for order in range(4)]
    base.require(len(rows) == len(expected), "incomplete selected-case warmup/timing matrix")
    diagnostics = []
    previous_cpu = previous_utc = None
    for row, identity in zip(rows, expected):
        base.require(tuple(row[field] for field in ("phase", "repetition", "order", "algorithm")) == identity,
                     "duplicate, missing or incorrectly ordered classical measurement")
        base.require(previous_cpu is None or row["process_cpu_start_ns"] >= previous_cpu,
                     "process CPU clock reversed or overlapped between measurements")
        previous_cpu = row["process_cpu_end_ns"]
        utc = row["utc_end_ns"]-row["utc_start_ns"]
        cpu, steady = row["process_cpu_elapsed_ns"], row["elapsed_ns"]
        four_threshold = max(2_000_000_000, cpu)
        flags = []
        if utc < 0:
            flags.append("realtime_reversed_within_call")
        if previous_utc is not None and row["utc_start_ns"] < previous_utc:
            flags.append("realtime_reversed_between_calls")
        if 4*(steady-cpu) > four_threshold:
            flags.append("steady_exceeds_process_cpu")
        if 4*(cpu-steady) > four_threshold:
            flags.append("process_cpu_exceeds_steady")
        if 4*abs(utc-steady) > four_threshold:
            flags.append("utc_steady_duration_disagreement")
        previous_utc = row["utc_end_ns"]
        diagnostics.append({"case_id": row["case_id"], "graph_seed": graph_seed, "kkt_seed": kkt_seed,
            **dict(zip(("phase", "repetition", "order", "algorithm"), identity)),
            "elapsed_ns": steady, "process_cpu_elapsed_ns": cpu, "utc_elapsed_ns": utc,
            "steady_minus_cpu_ns": steady-cpu, "utc_minus_steady_ns": utc-steady,
            "diagnostic_flags": flags, "excluded": False})
    fingerprints = {(r["input_fingerprint"], r["topology_fingerprint"]) for r in rows}
    base.require(len(fingerprints) == 1, "selected-case algorithms/phases received different inputs")
    if reference:
        base.require(next(iter(fingerprints)) == reference[spec["case_id"]],
                     "selected-case input differs from the reference pilot")
    return rows, diagnostics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--graph-seed", default="17")
    parser.add_argument("--kkt-seed", default="0")
    parser.add_argument("--repetitions", type=int, default=4)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--reference-timing-csv", type=Path)
    args = parser.parse_args()
    graph_seed = base.integer(args.graph_seed, "graph seed", 2**32-1)
    kkt_seed = base.integer(args.kkt_seed, "KKT seed", 2**32-1)
    base.require(4 <= args.repetitions <= 100 and args.repetitions % 4 == 0,
                 "repetitions must be a multiple of four in [4,100]")
    base.require(1 <= args.warmups <= 100, "warmups must be in [1,100]")
    root = Path.cwd().resolve()
    binary, manifest = args.binary.resolve(strict=True), args.manifest.resolve(strict=True)
    reference_path = args.reference_timing_csv.resolve(strict=True) if args.reference_timing_csv else None
    cases = base.load_manifest(manifest)
    base.require(len(cases) <= 3, "classical adjunct is limited to at most three selected cases")
    base.require(all(c["intrusion_per_mille"] == 0 and c["family"] != "legacy_random" for c in cases.values()),
                 "classical adjunct supports crossover/continuation fixtures with p=0, excluding legacy_random")
    reference = reference_fingerprints(reference_path, cases, graph_seed)
    output = args.output.resolve()
    base.require(output.suffix == ".csv", "--output must end in .csv")
    metadata = output.with_suffix(".json")
    case_folder = output.with_name(output.stem+"_cases")
    base.require(not any(path.exists() for path in (output, metadata, case_folder)),
                 "refusing to overwrite classical evidence")
    output.parent.mkdir(parents=True, exist_ok=True)
    case_folder.mkdir()
    sources, helpers = source_inventory(root), source_helpers()
    immutable = {str(binary): sha(binary), str(manifest): sha(manifest), **helpers}
    if reference_path:
        immutable[str(reference_path)] = sha(reference_path)

    def unchanged():
        base.require(source_inventory(root) == sources, "C++ source inventory changed during classical capture")
        base.require(all(Path(path).exists() and sha(path) == value for path, value in immutable.items()),
                     "binary, manifest, reference or Python capture/validation source changed")

    info = {"schema": "crossover_classical_capture_v1", "validation": "running",
            "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "working_directory": str(root), "platform": platform.platform(), "machine": platform.machine(),
            "profile": "Native Make Apple clang C++17 -O3 -march=native; assertions enabled; no work counters",
            "binary": str(binary), "binary_sha256": immutable[str(binary)],
            "manifest": str(manifest), "manifest_sha256": immutable[str(manifest)],
            "source_sha256": sources, "python_source_sha256": helpers,
            "reference_timing_csv": str(reference_path) if reference_path else None,
            "reference_timing_sha256": immutable[str(reference_path)] if reference_path else None,
            "reference_scope": "Selected graph fingerprints only; full pilot protocol validation is separate.",
            "graph_seed": graph_seed, "kkt_seed": kkt_seed, "repetitions": args.repetitions,
            "warmups": args.warmups, "case_order": list(cases), "algorithms": list(ALGORITHMS),
            "schedule": "manifest order; warmup then timed phase; increasing repetition, then order0..3; algorithm=(order+repetition)%4",
            "timing_boundary": "Original public tuple-input boundaries. KKT input conversion and temporary input destruction are timed; returned ID-set or tuple-vector destruction and exact validation are outside. UTC/process-CPU reads enclose the unchanged steady interval.",
            "baseline_scope": "boruvka is the original public baseline, not compacting_boruvka. No timing or result-type normalization is added.",
            "validation_scope": "Exact native certificate/ID validation flags, dimensions, schedule, fingerprints and clocks; wrapper does not rerun the MST oracle.",
            "diagnostic_rule": "Flag duration gaps > max(500000000ns,0.25*process_cpu_elapsed_ns), and realtime reversals. Retain every row; flags do not prove sleep or algorithm cost.",
            "rows_removed": 0, "rows_adjusted": 0, "started_utc": now(), "captures": []}
    with metadata.open("x") as stream:
        stream.write(json.dumps(info, indent=2)+"\n")
    start = time.monotonic()
    all_rows, all_diagnostics = [], []

    def interrupted(signum, frame):
        raise KeyboardInterrupt(f"classical capture received signal {signum}")

    signal.signal(signal.SIGTERM, interrupted)
    try:
        with output.open("x", newline="") as combined:
            writer = csv.DictWriter(combined, fieldnames=FIELDS)
            writer.writeheader()
            combined.flush()
            for index, spec in enumerate(cases.values(), 1):
                unchanged()
                raw = case_folder/f"{index:02d}_{spec['case_id']}.csv"
                log = raw.with_suffix(".log")
                command = [str(binary), "--family", spec["family"], "--n", str(spec["n"]),
                    "--density", str(spec["density"]), "--graph-seed", str(graph_seed),
                    "--kkt-seed", str(kkt_seed), "--repetitions", str(args.repetitions), "--warmups", str(args.warmups)]
                capture = {"case_id": spec["case_id"], "command": command,
                           "csv": str(raw), "log": str(log), "started_utc": now()}
                info["captures"].append(capture)
                write_metadata(metadata, info)
                process, failure = None, None
                case_start = time.monotonic()
                with raw.open("x") as stdout, log.open("x") as stderr:
                    try:
                        process = subprocess.Popen(["/usr/bin/time", "-l", *command], cwd=root,
                            stdout=stdout, stderr=stderr, start_new_session=True)
                        exit_status = process.wait()
                    except BaseException as error:
                        failure = error
                        if process is not None:
                            try:
                                os.killpg(process.pid, signal.SIGTERM)
                            except ProcessLookupError:
                                pass
                            try:
                                exit_status = process.wait(timeout=10)
                            except subprocess.TimeoutExpired:
                                os.killpg(process.pid, signal.SIGKILL)
                                exit_status = process.wait()
                        else:
                            exit_status = -1
                capture.update(exit_status=exit_status, interruption=repr(failure) if failure else None,
                    finished_utc=now(), monotonic_elapsed_seconds=time.monotonic()-case_start,
                    output_sha256=sha(raw), log_sha256=sha(log))
                capture["utc_elapsed_seconds"] = (datetime.datetime.fromisoformat(capture["finished_utc"])-
                                                  datetime.datetime.fromisoformat(capture["started_utc"])).total_seconds()
                capture["utc_minus_monotonic_seconds"] = capture["utc_elapsed_seconds"]-capture["monotonic_elapsed_seconds"]
                write_metadata(metadata, info)
                if failure:
                    raise failure
                base.require(exit_status == 0, "classical child failed; raw output and log retained")
                unchanged()
                rows, diagnostics = check_rows(raw, spec, graph_seed, kkt_seed, args.repetitions, args.warmups, reference)
                base.check_fingerprints([*all_rows, *rows])
                capture.update(validation="pass", rows=len(rows),
                    input_fingerprint=rows[0]["input_fingerprint"], topology_fingerprint=rows[0]["topology_fingerprint"],
                    flagged_calls=sum(bool(r["diagnostic_flags"]) for r in diagnostics))
                capture["timed_medians"] = {algorithm: {
                    "elapsed_ns": statistics.median(r["elapsed_ns"] for r in rows if r["phase"] == "timed" and r["algorithm"] == algorithm),
                    "process_cpu_elapsed_ns": statistics.median(r["process_cpu_elapsed_ns"] for r in rows if r["phase"] == "timed" and r["algorithm"] == algorithm)}
                    for algorithm in ALGORITHMS}
                writer.writerows(rows)
                combined.flush()
                all_rows.extend(rows)
                all_diagnostics.extend(diagnostics)
                write_metadata(metadata, info)
        unchanged()
        info.update(validation="pass", checked_rows=len(all_rows),
                    checked_timed_rows=len(cases)*args.repetitions*4,
                    checked_warmup_rows=len(cases)*args.warmups*4,
                    flagged_calls=sum(bool(r["diagnostic_flags"]) for r in all_diagnostics))
    except BaseException as error:
        info.update(validation="failed", error=repr(error))
        raise
    finally:
        info.update(finished_utc=now(), monotonic_elapsed_seconds=time.monotonic()-start,
                    call_diagnostics=all_diagnostics)
        info["utc_elapsed_seconds"] = (datetime.datetime.fromisoformat(info["finished_utc"])-
                                       datetime.datetime.fromisoformat(info["started_utc"])).total_seconds()
        info["utc_minus_monotonic_seconds"] = info["utc_elapsed_seconds"]-info["monotonic_elapsed_seconds"]
        if output.exists():
            info["output_sha256"] = sha(output)
        write_metadata(metadata, info)
    print(f"Validated {len(cases)} selected classical cases: {info['checked_timed_rows']} timed and "
          f"{info['checked_warmup_rows']} warmup rows; {info['flagged_calls']} clock flags; no observations removed")


if __name__ == "__main__":
    main()
