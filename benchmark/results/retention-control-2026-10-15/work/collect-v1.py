#!/usr/bin/env python3
"""Supplementary logical-work capture. Native durations are not benchmark data."""
import argparse
import csv
import json
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve()
WORK = HERE.parent
ROOT = WORK.parents[3]
sys.path.insert(0, str(ROOT / "benchmark"))
import run_retention_control as control

native, analysis, monitor = control.native, control.analysis, control.monitor
require, write_json, RULE = control.require, control.write_json, control.RULE
ALGORITHMS = ("kkt", "compacting_boruvka", "multigraph_boruvka")
FIELDS = re.findall(r'\{"(\w+)", &kkt_work::WorkStats::\w+, (?:true|false)\}',
                    (ROOT / "benchmark/work_metrics.hpp").read_text())


def provenance():
    record_path = WORK / "build-record.json"
    record = analysis.read_json(record_path)
    require(record["build_exit_status"] == 0 and record["file_description"] == "Mach-O 64-bit executable arm64",
            "diagnostic build is not successful native ARM")
    paths = {str(ROOT / p): s for p, s in record["frozen_source_sha256"].items()}
    paths.update({str(ROOT / p): s for p, s in record["supplementary_source_sha256"].items()})
    paths.update({str(ROOT / ".build/retention-control-work" / p): s for p, s in record["object_sha256"].items()})
    paths.update({record["binary"]: record["binary_sha256"], str(record_path): native.sha(record_path),
                  str(WORK / "build.log"): record["build_log_sha256"], str(HERE): native.sha(HERE),
                  **control.helpers()})
    timing = WORK.parent / "followup.json"
    info, cases, rows, _, _, inputs = control.load(timing)
    paths.update(inputs)
    for p, s in paths.items(): analysis.hash_check(Path(p), s)
    return record, info, cases, rows, paths


def expected_schedule(mode, info, cases, rows):
    if mode == "gate":
        return [dict(family=f, n=n, density=d, graph_seed=3000001, kkt_seed=809,
                     case_id=f"{f}_n{n}_d{d}_p0", m=n*d)
                for f, n, d in (("leaf_hierarchy4", 512, 16), ("leaf_distance4", 512, 16),
                                ("gnm_random", 64, 16), ("gnm_random", 512, 128))]
    schedule = []
    for item in info["captures"]:
        identity = {k: item[k] for k in ("case_id", "graph_seed", "kkt_seed")}
        row = next(r for r in rows if all(r[k] == v for k, v in identity.items()))
        schedule.append({**cases[identity["case_id"]], **identity,
                         **{k: row[k] for k in ("m", "input_fingerprint", "topology_fingerprint")}})
    require(len(schedule) == 20, "missing fingerprinted inputs")
    return schedule


def command(binary, spec):
    return [binary, spec["family"], *[str(spec[k]) for k in ("n", "density", "graph_seed", "kkt_seed")]]


def check_output(path, spec):
    value = analysis.read_json(path)
    for k, v in {"schema": "retention_control_work_v1", "validation": "pass",
                 "certified_output_items": spec["n"] - 1,
                 **{k: v for k, v in spec.items() if k != "parameter"}}.items():
        analysis.equal(value, k, v, "diagnostic output")
    require(set(value["algorithms"]) == set(ALGORITHMS), "incorrect algorithm set")
    for name, data in value["algorithms"].items():
        work = data["work"]
        require(set(work) == set(FIELDS), "counter schema changed")
        require(all(type(v) is int and v >= 0 for k, v in work.items()
                    if k != "hash_insert_items" or name == "kkt"), "invalid counter")
        analysis.equal(work, "current_depth", 0, "unwound KKT recursion")
        require(work["contraction_edge_visits"] <= (4 if name == "compacting_boruvka" else 3) *
                work["contraction_edges"], "scan bound differs")
        if name == "kkt":
            analysis.equal(data, "hash_insert_items_status", "measured", "hash instrumentation")
            analysis.equal(work, "hash_insert_items", spec["n"] - 1, "public-set insertion")
            require(work["sampling_edge_visits"] == work["verifier_edges"] and
                    work["sampling_calls"] == work["verifier_calls"], "sample/verifier volume mismatch")
        else:
            analysis.equal(data, "hash_insert_items_status", "unmeasured", "hash instrumentation")
            analysis.equal(work, "hash_insert_items", None, "unmeasured final result-set inserts")
            require(all(work[k] == 0 for k in ("kkt_calls", "verifier_calls", "sampling_calls")), "wrong solver continuation")
            rounds = value["rounds"][name]
            require(len(rounds) == work["contraction_calls"] and rounds, "round count differs")
            expected_n, expected_m, selected = spec["n"], spec["m"], 0
            for index, r in enumerate(rounds):
                require(set(r) == {"round", "vertices", "edges", "selected", "output_vertices", "output_edges"}
                        and all(type(v) is int and v >= 0 for v in r.values()), "invalid round")
                require((r["round"], r["vertices"], r["edges"]) == (index, expected_n, expected_m), "round chain differs")
                require(r["output_vertices"] <= r["vertices"] // 2 and r["output_edges"] <= r["edges"], "round does not shrink")
                expected_n, expected_m = r["output_vertices"], r["output_edges"]
                selected += r["selected"]
            require(expected_m == 0 and selected == spec["n"] - 1, "trace not spanning")
            for field, counter in (("vertices", "contraction_vertices"), ("edges", "contraction_edges"),
                                   ("output_vertices", "contraction_output_vertices"), ("output_edges", "contraction_output_edges")):
                analysis.equal(work, counter, sum(r[field] for r in rounds), "replay aggregate")
    require(set(value["rounds"]) == set(ALGORITHMS[1:]), "round solver set differs")
    rounds = value["rounds"]["multigraph_boruvka"]
    if len(rounds) >= 2:
        for field in ("vertices", "edges"):
            analysis.equal(value["algorithms"]["kkt"]["work"], "root_after_two_" + field,
                           rounds[1]["output_" + field], "shared first two rounds")
    return value


def resources(item):
    observations = analysis.check_rss(Path(item["rss_log"]), item, RULE)
    require(all(r["process_group"] == item["process_group"] for r in observations), "wrong owned group")
    analysis.equal(item, "group_exit_verification", observations[-1], "post-exit group verification")
    require(item["started_monotonic_ns"] <= item["wrapper_exit_monotonic_ns"] <=
            observations[-1]["monotonic_ns"] <= item["finished_monotonic_ns"] and
            observations[-1]["validation"] == "pass" and not observations[-1]["members"], "owned group exit unknown")
    monitor.validate_monitor(item)


def capture(mode):
    record, timed, cases, rows, paths = provenance()
    schedule = expected_schedule(mode, timed, cases, rows)
    folder = WORK / (mode + "_cases"); sidecar = WORK / (mode + ".json")
    require(not folder.exists() and not sidecar.exists(), "refusing to overwrite evidence")
    if mode == "capture": load(WORK / "gate.json")
    folder.mkdir()
    sampler = monitor.BoundedSampler(monitor.LibprocProvider())
    info = dict(schema="retention_control_work_capture_v1", validation="running", mode=mode,
                schedule=schedule, bound_sha256=paths, captures=[], cleanup=[],
                native_process_may_still_be_running=False,
                started_utc=native.now(), started_monotonic_ns=time.monotonic_ns(),
                purpose="Supplementary untimed logical counts; process durations and resource logs are not performance measurements.")
    write_json(sidecar, info)
    old = signal.getsignal(signal.SIGTERM)
    def interrupted(signum, frame): raise KeyboardInterrupt(f"signal {signum}")
    signal.signal(signal.SIGTERM, interrupted)
    try:
        for index, spec in enumerate(schedule, 1):
            for p, s in paths.items(): analysis.hash_check(Path(p), s)
            require(not sampler.poisoned, "poisoned sampler forbids child")
            stem = f"{index:04d}_{spec['case_id']}_g{spec['graph_seed']}_s{spec['kkt_seed']}"
            raw, log, rss = (folder / (stem + suffix) for suffix in (".json", ".log", ".rss.jsonl"))
            argv = command(record["binary"], spec)
            item = dict(spec=spec, command=argv, launch_command=["/usr/bin/time", "-l", *argv],
                        raw=str(raw), log=str(log), rss_log=str(rss),
                        started_utc=native.now(), started_monotonic_ns=time.monotonic_ns())
            info["captures"].append(item); write_json(sidecar, info)
            process = None; failure = None; observations = []; unavailable = 0
            try:
                with raw.open("x") as output, log.open("x") as error, rss.open("x") as resource:
                    process = subprocess.Popen(item["launch_command"], cwd=ROOT, stdout=output, stderr=error, start_new_session=True)
                    item["process_group"] = process.pid
                    def observe():
                        result = sampler.sample(process.pid); observations.append(result)
                        resource.write(json.dumps(result, allow_nan=False) + "\n"); resource.flush()
                        return result
                    while True:
                        observation = observe()
                        require(not sampler.poisoned, "sampler timed out")
                        if observation["validation"] == "pass":
                            unavailable = 0
                            require(observation["rss_kib"] <= RULE["rss_limit_kib"], "40 GiB resource ceiling exceeded")
                        else:
                            unavailable += 1
                            require(unavailable < 3, "three consecutive unavailable RSS samples")
                        try:
                            process.wait(timeout=RULE["poll_seconds"])
                            item["wrapper_exit_monotonic_ns"] = time.monotonic_ns(); break
                        except subprocess.TimeoutExpired: pass
                    require(process.returncode == 0, "diagnostic child failed")
                    item["group_exit_verification"] = observe()
                    require(not sampler.poisoned and observations[-1]["validation"] == "pass" and
                            not observations[-1]["members"], "owned group exit unknown")
            except BaseException as error:
                failure = error; cleanup = monitor.bounded_terminate(process, sampler)
                info["cleanup"].append(cleanup)
                info["native_process_may_still_be_running"] |= cleanup["native_process_may_still_be_running"]
            item.update(exit_status=process.returncode if process else None, interruption=repr(failure) if failure else None,
                        finished_utc=native.now(), finished_monotonic_ns=time.monotonic_ns(),
                        raw_sha256=native.sha(raw), log_sha256=native.sha(log), rss_sha256=native.sha(rss),
                        rss_observations=len(observations), rss_unavailable=sum(r["validation"] != "pass" for r in observations),
                        rss_nonempty_observations=sum(r["validation"] == "pass" and bool(r["members"]) for r in observations),
                        sampled_peak_rss_kib=max((r["rss_kib"] for r in observations if r["validation"] == "pass"), default=None),
                        recovery_monitor=monitor.recovery_monitor(sampler.events.get(process.pid, [])[:len(observations)] if process else []))
            write_json(sidecar, info)
            if failure: raise failure
            for p, s in paths.items(): analysis.hash_check(Path(p), s)
            value = check_output(raw, spec)
            item["certificate"] = native.check_certificate(log, [value]); resources(item)
            item["validation"] = "pass"; write_json(sidecar, info)
            print(f"{mode} {index}/{len(schedule)} certified: {stem}", flush=True)
        info["validation"] = "pass"
    except BaseException as error:
        info.update(validation="failed", error=repr(error)); raise
    finally:
        signal.signal(signal.SIGTERM, old)
        info.update(finished_utc=native.now(), finished_monotonic_ns=time.monotonic_ns())
        write_json(sidecar, info)
    load(sidecar)


def load(sidecar):
    info = analysis.read_json(sidecar)
    for k, v in dict(schema="retention_control_work_capture_v1", validation="pass", cleanup=[],
                     native_process_may_still_be_running=False).items(): analysis.equal(info, k, v, "capture")
    require("error" not in info, "failed capture")
    record, timed, cases, rows, paths = provenance()
    analysis.equal(info, "bound_sha256", paths, "frozen provenance")
    schedule = expected_schedule(info["mode"], timed, cases, rows)
    analysis.equal(info, "schedule", schedule, "exact diagnostic schedule")
    require(len(info["captures"]) == len(schedule), "incomplete capture")
    previous = info["started_monotonic_ns"]; values = []
    for spec, item in zip(schedule, info["captures"]):
        for k, v in dict(spec=spec, validation="pass", exit_status=0, interruption=None,
                         command=command(record["binary"], spec),
                         launch_command=["/usr/bin/time", "-l", *command(record["binary"], spec)]).items():
            analysis.equal(item, k, v, "child identity")
        require(previous <= item["started_monotonic_ns"] < item["finished_monotonic_ns"] <= info["finished_monotonic_ns"],
                "child overlap or bad interval")
        previous = item["finished_monotonic_ns"]
        for field, digest in (("raw", "raw_sha256"), ("log", "log_sha256"), ("rss_log", "rss_sha256")):
            analysis.hash_check(Path(item[field]), item[digest])
        value = check_output(Path(item["raw"]), spec)
        analysis.equal(item, "certificate", native.check_certificate(Path(item["log"]), [value]), "native certificate")
        resources(item); values.append(value)
    return values


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("mode", choices=("gate", "capture", "verify"))
    args = parser.parse_args()
    if args.mode == "verify":
        values = load(WORK / "capture.json"); print(f"Strictly reloaded {len(values)} certified diagnostic children")
    else: capture(args.mode)
