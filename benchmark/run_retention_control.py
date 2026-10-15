#!/usr/bin/env python3
"""Serial six-solver retention control, with frozen evidence and strict analysis.

No historical helper is changed. New row validation handles six balanced solver
positions; certificate checking, clock-flag definitions and bounded RSS/group
verification retain the prior study's semantics. No sample is adjusted/removed.
"""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import platform
import shlex
import signal
import statistics
import subprocess
import time

import run_multigraph_experiment as previous

native, analysis, monitor = previous.native, previous.analysis, previous.monitor
power = previous.corrected_power
require, write_json = previous.require, previous.write_json
HERE = Path(__file__).resolve()
PARENT_SHA256 = "7269bc0c92e6decb6355fc8cd1e95f471dcdad2d463cc66a45306ac80d7edc9a"
ALGORITHMS = ("kkt", "compacting_boruvka", "multigraph_boruvka", "kruskal", "prim", "boruvka")
GRAPH_SEEDS = (3000001, 3000029)
SAMPLING_SEED, REPETITIONS, WARMUPS = 809, 6, 1
FIELDS = native.FIELDS
EXPECTED_CASES = {(family, n, 16, 0) for family in ("leaf_hierarchy4", "leaf_distance4")
                  for n in (65536, 262144, 2097152)} \
    | {("gnm_random", n, 16, 0) for n in (4096, 1048576)} \
    | {("gnm_random", n, 128, 0) for n in (4096, 262144)}
NEW_NATIVE_FILES = {"benchmark/retention_control.cpp", "benchmark/retention_boruvka.hpp", "test/retention_control_test.cpp"}
RECIPES = ("Makefile", "benchmark/retention_control.mk")
RULE = previous.RULE
SEMANTICS = {
    "campaign": "six_solver_retention_control_v1",
    "schedule": "Graph seed then case. Second graph seed reverses case order. Six timed repetitions balance each algorithm once in every position; algorithm=(order+repetition)%6.",
    "timing_boundary": "Original tuple-input/native-result boundaries. KKT and both Boruvka continuations time problem conversion and temporary input destruction; returned-result validation/destruction are outside the interval. UTC/CPU envelopes are slightly wider than steady elapsed.",
    "comparison": "Compare KKT with all five competitors within the same graph, starting KKT seed and repetition. Case median uses all twelve paired ratios; each graph also has its own six-trial median. No historical observations are pooled.",
    "purpose": "Multigraph Boruvka uses the same retained-parallel contraction as candidate KKT; this separates repeated retained-edge contraction from KKT's sampling/filtering continuation. It is a whole-strategy comparison, not isolated phase timing.",
    "clock_semantics": previous.SEMANTICS["clock_semantics"],
    "power_semantics": previous.SEMANTICS["power_semantics"],
    "certificate_scope": previous.SEMANTICS["certificate_scope"],
}


def helpers():
    return {**previous.helpers(), str(HERE): native.sha(HERE)}


def cases_from_manifest(path):
    cases = native.load_manifest(path)
    require(len(cases) == 10 and {tuple(spec[field] for field in native.base.MANIFEST_FIELDS)
                                 for spec in cases.values()} == EXPECTED_CASES, "manifest differs from declared ten cases")
    return cases


def schedule(cases):
    return [{"case_id": case, "graph_seed": seed, "kkt_seed": SAMPLING_SEED}
            for index, seed in enumerate(GRAPH_SEEDS)
            for case in (list(cases) if index == 0 else list(reversed(cases)))]


def command(binary, spec, identity):
    return [str(binary), "--family", spec["family"], "--n", str(spec["n"]), "--density", str(spec["density"]),
            "--graph-seed", str(identity["graph_seed"]), "--kkt-seed", str(SAMPLING_SEED),
            "--repetitions", str(REPETITIONS), "--warmups", str(WARMUPS)]


def parent_record(path):
    path = Path(path).resolve(strict=True)
    analysis.hash_check(path, PARENT_SHA256)
    parent = analysis.read_json(path)
    analysis.equal(parent, "schema", "multigraph_experiment_freeze_v1", "parent screen")
    parent_helpers = {Path(name).name: value for name, value in parent["python_source_sha256"].items()}
    current = {Path(name).name: value for name, value in previous.helpers().items()}
    require(len(parent_helpers) == len(parent["python_source_sha256"]) and parent_helpers == current,
            "frozen parent helpers changed")
    build = parent["variants"]["multigraph"]["build"]
    analysis.hash_check(Path(build["path"]), build["sha256"])
    analysis.equal(build, "record", analysis.read_json(Path(build["path"])), "parent candidate build")
    return parent


def build_record(path, binary, root, parent):
    path = Path(path).resolve(strict=True)
    record = analysis.read_json(path)
    sources = native.source_inventory(root)
    for name, digest in parent["source_sha256"].items():
        require(sources.get(name) == digest, "parent native source changed: " + name)
    require(set(sources) - set(parent["source_sha256"]) == NEW_NATIVE_FILES, "unexpected new native source inventory")
    recipes = {name: native.sha(root / name) for name in RECIPES}
    require(recipes["Makefile"] == parent["build_recipe_sha256"]["Makefile"], "parent Makefile changed")
    for field, expected in (("schema", "retention_control_build_v1"), ("working_directory", str(root)),
                            ("binary", str(binary)), ("binary_sha256", native.sha(binary)),
                            ("source_sha256", sources), ("build_recipe_sha256", recipes), ("build_exit_status", 0)):
        analysis.equal(record, field, expected, "native build")
    inherited = parent["variants"]["multigraph"]["build"]
    for field in ("compiler", "compiler_command", "sdk", "object_sha256"):
        analysis.equal(record, field, inherited["record"][field], "same eight production objects and toolchain")
    analysis.equal(record, "parent_candidate_build_record", inherited["path"], "parent build")
    analysis.equal(record, "parent_candidate_build_record_sha256", inherited["sha256"], "parent build")
    analysis.equal(record, "all_eight_production_objects_equal_parent_candidate", True, "parent objects")
    argv = record.get("build_command")
    require(type(argv) is list and len(argv) == 13 and argv[:7] ==
            ["/usr/bin/arch", "-arm64", "/usr/bin/make", "-f", "benchmark/retention_control.mk", "-B", "-j4"]
            and argv[-2:] == ["retention-control", "retention-control-test"], "unexpected six-solver build argv")
    variables = dict(arg.split("=", 1) for arg in argv[7:11] if type(arg) is str and "=" in arg)
    require(set(variables) == {"CXX", "BUILD_DIR", "BIN_DIR", "CXXFLAGS"} and
            variables["CXX"] == "/usr/bin/clang++" and
            shlex.split(variables["CXXFLAGS"]) == previous.BASE_FLAGS + ["-DKKT_EXPERIMENT_RETAIN_PARALLEL"],
            "unexpected compiler/optimization/instrumentation flags")
    require((root / variables["BIN_DIR"] / "retention_control").resolve() == binary, "binary differs from declared build directory")
    for name, digest in record["object_sha256"].items():
        analysis.hash_check(root / variables["BUILD_DIR"] / name, digest)
    analysis.hash_check(Path(record["build_log"]), record["build_log_sha256"])
    return {"path": str(path), "sha256": native.sha(path), "record": record}


def preflight(args):
    root = Path.cwd().resolve()
    parent_path = args.parent_freeze.resolve(strict=True)
    parent = parent_record(parent_path)
    binary = args.binary.resolve(strict=True)
    manifest = args.manifest.resolve(strict=True); protocol = args.protocol.resolve(strict=True)
    cases = cases_from_manifest(manifest)
    build = build_record(args.build_record, binary, root, parent)
    profile = native.binary_profile(binary)
    analysis.equal(build["record"], "binary_profile", profile, "recorded native profile")
    freeze = {"schema": "retention_control_freeze_v1", "created_utc": native.now(),
              "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "working_directory": str(root), "platform": platform.platform(), "machine": platform.machine(),
              "parent_freeze": str(parent_path), "parent_freeze_sha256": PARENT_SHA256,
              "binary": str(binary), "binary_sha256": native.sha(binary), "binary_profile": profile,
              "build": build, "source_sha256": native.source_inventory(root), "python_source_sha256": helpers(),
              "build_recipe_sha256": build["record"]["build_recipe_sha256"],
              "manifest": str(manifest), "manifest_sha256": native.sha(manifest),
              "protocol": str(protocol), "protocol_sha256": native.sha(protocol),
              "algorithms": list(ALGORITHMS), "graph_seeds": list(GRAPH_SEEDS), "sampling_seeds": [SAMPLING_SEED],
              "repetitions": REPETITIONS, "warmups": WARMUPS, "schedule": schedule(cases),
              "resource_rule": RULE, "semantics": SEMANTICS}
    args.freeze.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.freeze, freeze, exclusive=True)
    print(f"Preflight passed; no native solver executed; frozen {len(freeze['schedule'])} children / 840 outputs")


def check_freeze(path):
    frozen = analysis.read_json(Path(path))
    for field, expected in (("schema", "retention_control_freeze_v1"), ("parent_freeze_sha256", PARENT_SHA256),
                            ("algorithms", list(ALGORITHMS)), ("graph_seeds", list(GRAPH_SEEDS)),
                            ("sampling_seeds", [SAMPLING_SEED]), ("repetitions", REPETITIONS), ("warmups", WARMUPS),
                            ("resource_rule", RULE), ("semantics", SEMANTICS)):
        analysis.equal(frozen, field, expected, "frozen six-solver protocol")
    parent = parent_record(frozen["parent_freeze"])
    root = Path(frozen["working_directory"])
    for name in ("manifest", "protocol", "binary"):
        analysis.hash_check(Path(frozen[name]), frozen[name + "_sha256"])
    cases = cases_from_manifest(Path(frozen["manifest"]))
    analysis.equal(frozen, "schedule", schedule(cases), "frozen schedule")
    analysis.equal(frozen, "source_sha256", native.source_inventory(root), "current source inventory")
    analysis.equal(frozen, "python_source_sha256", helpers(), "current helper inventory")
    analysis.equal(frozen, "build_recipe_sha256", {name: native.sha(root / name) for name in RECIPES}, "current build recipe")
    checked = build_record(frozen["build"]["path"], Path(frozen["binary"]), root, parent)
    analysis.equal(frozen, "build", checked, "build provenance")
    analysis.equal(frozen, "binary_profile", checked["record"]["binary_profile"], "binary profile")
    analysis.equal(frozen["binary_profile"], "main_stack_bytes", 536870912, "native stack")
    require("Mach-O 64-bit executable arm64" in frozen["binary_profile"]["file_description"], "wrong native architecture")
    return frozen, cases


def check_rows(path, spec, graph_seed):
    rows = []
    for context, raw in native.base.read_csv(path, FIELDS):
        row = dict(raw)
        for field in FIELDS:
            if field not in native.TEXT_FIELDS:
                row[field] = native.base.integer(raw[field], context + " " + field,
                                                native.MAX_NS if field.endswith("_ns") else native.base.UINT64_MAX)
        require(all(row[field] == value for field, value in spec.items()), context + ": fixture differs from manifest")
        require(row["graph_seed"] == graph_seed and row["kkt_seed"] == SAMPLING_SEED and
                row["warmups"] == WARMUPS and row["validation"] == "pass", context + ": seed or validation mismatch")
        require(row["elapsed_ns"] > 0 and row["utc_start_ns"] > 0 and row["utc_end_ns"] > 0 and
                row["process_cpu_end_ns"] - row["process_cpu_start_ns"] == row["process_cpu_elapsed_ns"] > 0,
                context + ": invalid clock endpoints/duration")
        rows.append(row)
    expected = [(phase, repetition, order, ALGORITHMS[(order + repetition) % 6])
                for phase, count in (("warmup", WARMUPS), ("timed", REPETITIONS))
                for repetition in range(count) for order in range(6)]
    require(len(rows) == len(expected), "incomplete six-solver matrix")
    diagnostics = []; previous_cpu = previous_utc = None
    for row, identity in zip(rows, expected):
        require(tuple(row[field] for field in ("phase", "repetition", "order", "algorithm")) == identity,
                "duplicate/missing/incorrectly ordered six-solver call")
        require(previous_cpu is None or row["process_cpu_start_ns"] >= previous_cpu, "process CPU clock reversed or overlapped")
        previous_cpu = row["process_cpu_end_ns"]
        cpu, steady = row["process_cpu_elapsed_ns"], row["elapsed_ns"]
        utc = row["utc_end_ns"] - row["utc_start_ns"]
        threshold_times_four = max(2_000_000_000, cpu)
        flags = []
        if utc < 0: flags.append("realtime_reversed_within_call")
        if previous_utc is not None and row["utc_start_ns"] < previous_utc: flags.append("realtime_reversed_between_calls")
        if 4 * (steady - cpu) > threshold_times_four: flags.append("steady_exceeds_process_cpu")
        if 4 * (cpu - steady) > threshold_times_four: flags.append("process_cpu_exceeds_steady")
        if 4 * abs(utc - steady) > threshold_times_four: flags.append("utc_steady_duration_disagreement")
        previous_utc = row["utc_end_ns"]
        diagnostics.append({"case_id": spec["case_id"], "graph_seed": graph_seed, "kkt_seed": SAMPLING_SEED,
                            **dict(zip(("phase", "repetition", "order", "algorithm"), identity)),
                            "elapsed_ns": steady, "process_cpu_elapsed_ns": cpu, "utc_elapsed_ns": utc,
                            "steady_minus_cpu_ns": steady - cpu, "utc_minus_steady_ns": utc - steady,
                            "diagnostic_flags": flags, "excluded": False})
    require(len({(row["input_fingerprint"], row["topology_fingerprint"]) for row in rows}) == 1,
            "solvers/phases received different fingerprints")
    return rows, diagnostics


def child_paths(output, index, identity):
    raw = output.with_name(output.stem + "_cases") / f"{index:04d}_{identity['case_id']}_g{identity['graph_seed']}_s{SAMPLING_SEED}.csv"
    return raw, raw.with_suffix(".log"), raw.with_suffix(".rss.jsonl")


def capture(args, sampler=None, popen=None):
    require(args.released, "capture requires explicit parent scheduling --released")
    freeze_path = args.freeze.resolve(strict=True); freeze_hash = native.sha(freeze_path)
    frozen, cases = check_freeze(freeze_path)
    output = args.output.resolve(); sidecar = output.with_suffix(".json")
    folder = output.with_name(output.stem + "_cases")
    require(output.suffix == ".csv" and not any(path.exists() for path in (output, sidecar, folder)), "refusing to overwrite raw evidence")
    sampler = sampler if sampler is not None else monitor.BoundedSampler(monitor.LibprocProvider())
    popen = popen if popen is not None else subprocess.Popen
    output.parent.mkdir(parents=True, exist_ok=True); folder.mkdir()
    info = {"schema": "retention_control_capture_v1", "validation": "running", "freeze": str(freeze_path),
            "freeze_sha256": freeze_hash, "frozen_protocol": frozen, "output": str(output),
            "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "started_utc": native.now(), "started_monotonic_ns": time.monotonic_ns(), "rows_removed": 0,
            "rows_adjusted": 0, "captures": [], "cleanup": [], "native_process_may_still_be_running": False}
    write_json(sidecar, info)
    rows, diagnostics = [], []
    old_handler = signal.getsignal(signal.SIGTERM)
    def interrupted(signum, frame):
        raise KeyboardInterrupt(f"capture received signal {signum}")
    signal.signal(signal.SIGTERM, interrupted)
    try:
        with output.open("x", newline="") as combined:
            writer = csv.DictWriter(combined, fieldnames=FIELDS); writer.writeheader(); combined.flush()
            for index, identity in enumerate(frozen["schedule"], 1):
                require(not sampler.poisoned, "sampler timeout forbids launching another native child")
                analysis.hash_check(freeze_path, freeze_hash); check_freeze(freeze_path)
                raw, log, rss = child_paths(output, index, identity)
                spec = cases[identity["case_id"]]
                argv = command(frozen["binary"], spec, identity)
                item = {**identity, "command": argv, "launch_command": ["/usr/bin/time", "-l", *argv],
                        "csv": str(raw), "log": str(log), "rss_log": str(rss),
                        "started_utc": native.now(), "started_monotonic_ns": time.monotonic_ns()}
                info["captures"].append(item); write_json(sidecar, info)
                process = None; failure = None; observations = []; unavailable = 0
                try:
                    with raw.open("x") as stdout, log.open("x") as stderr, rss.open("x") as resource:
                        process = popen(item["launch_command"], cwd=frozen["working_directory"],
                                        stdout=stdout, stderr=stderr, start_new_session=True)
                        item["process_group"] = process.pid
                        def observe():
                            observation = sampler.sample(process.pid); observations.append(observation)
                            resource.write(json.dumps(observation, allow_nan=False) + "\n"); resource.flush()
                            return observation
                        while True:
                            observation = observe()
                            require(not sampler.poisoned, "RSS sampler timed out; no next native child permitted")
                            if observation["validation"] == "pass":
                                unavailable = 0
                                require(observation["rss_kib"] <= RULE["rss_limit_kib"], "sampled RSS exceeded ceiling")
                            else:
                                unavailable += 1
                                require(unavailable < 3, "three consecutive RSS observations unavailable")
                            try:
                                process.wait(timeout=RULE["poll_seconds"])
                                item["wrapper_exit_monotonic_ns"] = time.monotonic_ns(); break
                            except subprocess.TimeoutExpired:
                                pass
                        require(process.returncode == 0, "native child failed; no next native child permitted")
                        observation = observe(); item["group_exit_verification"] = observation
                        require(not sampler.poisoned and observation["validation"] == "pass" and not observation["members"],
                                "owned group exit is not verified; no next native child permitted")
                except BaseException as error:
                    failure = error; cleanup = monitor.bounded_terminate(process, sampler)
                    info["cleanup"].append(cleanup)
                    info["native_process_may_still_be_running"] |= cleanup["native_process_may_still_be_running"]
                item.update(exit_status=process.returncode if process else None, interruption=repr(failure) if failure else None,
                            finished_utc=native.now(), finished_monotonic_ns=time.monotonic_ns(),
                            output_sha256=native.sha(raw), log_sha256=native.sha(log), rss_sha256=native.sha(rss),
                            rss_observations=len(observations), rss_unavailable=sum(row["validation"] != "pass" for row in observations),
                            rss_nonempty_observations=sum(row["validation"] == "pass" and bool(row["members"]) for row in observations),
                            sampled_peak_rss_kib=max((row["rss_kib"] for row in observations if row["validation"] == "pass"), default=None),
                            recovery_monitor=monitor.recovery_monitor(sampler.events.get(process.pid, [])[:len(observations)] if process else []))
                item["monotonic_elapsed_seconds"] = (item["finished_monotonic_ns"] - item["started_monotonic_ns"]) / 1e9
                write_json(sidecar, info)
                if failure: raise failure
                analysis.hash_check(freeze_path, freeze_hash); check_freeze(freeze_path)
                child_rows, child_diagnostics = check_rows(raw, spec, identity["graph_seed"])
                certificate = native.check_certificate(log, child_rows)
                native.check_fingerprints([*rows, *child_rows])
                item.update(validation="pass", rows=len(child_rows), certificate=certificate,
                            flagged_calls=sum(bool(row["diagnostic_flags"]) for row in child_diagnostics))
                analysis.check_rss(rss, item, RULE); monitor.validate_monitor(item)
                rows.extend(child_rows); diagnostics.extend(child_diagnostics)
                writer.writerows(child_rows); combined.flush(); write_json(sidecar, info)
        info.update(validation="pass", checked_rows=len(rows), checked_timed_rows=720, checked_warmup_rows=120,
                    flagged_calls=sum(bool(row["diagnostic_flags"]) for row in diagnostics))
    except BaseException as error:
        info.update(validation="failed", error=repr(error)); raise
    finally:
        signal.signal(signal.SIGTERM, old_handler)
        info.update(finished_utc=native.now(), finished_monotonic_ns=time.monotonic_ns(), call_diagnostics=diagnostics)
        info["monotonic_elapsed_seconds"] = (info["finished_monotonic_ns"] - info["started_monotonic_ns"]) / 1e9
        info["capture_clock_flags"] = native.capture_clock_flags(info)
        if output.exists(): info["output_sha256"] = native.sha(output)
        write_json(sidecar, info)
    print("Validated 20 native children: 720 timed outputs + 120 checked warmups")
    return info


def load(path):
    path = Path(path).resolve(strict=True); info = analysis.read_json(path)
    for field, expected in (("schema", "retention_control_capture_v1"), ("validation", "pass"), ("rows_removed", 0),
                            ("rows_adjusted", 0), ("cleanup", []), ("native_process_may_still_be_running", False)):
        analysis.equal(info, field, expected, "capture")
    require("error" not in info, "failed capture cannot be summarized")
    freeze = Path(info["freeze"]); analysis.hash_check(freeze, info["freeze_sha256"])
    frozen, cases = check_freeze(freeze); analysis.equal(info, "frozen_protocol", frozen, "capture freeze")
    output = Path(info["output"])
    require(output.with_suffix(".json") == path, "sidecar differs from captured raw path")
    analysis.hash_check(output, info["output_sha256"])
    analysis.timestamp(info["started_utc"]); analysis.timestamp(info["finished_utc"])
    begin, end = analysis.monotonic_interval(info)
    analysis.equal(info, "monotonic_elapsed_seconds", (end - begin) / 1e9, "capture duration")
    require(len(info["captures"]) == 20, "incomplete native child schedule")
    previous_end = begin; rows = []; diagnostics = []; resources = []
    inputs = {str(source): native.sha(source) for source in (path, output, freeze, Path(frozen["parent_freeze"]))}
    for index, (identity, item) in enumerate(zip(frozen["schedule"], info["captures"]), 1):
        for field, value in {**identity, "exit_status": 0, "interruption": None, "validation": "pass", "rows": 42}.items():
            analysis.equal(item, field, value, f"child {index}")
        start, finish = analysis.monotonic_interval(item)
        require(previous_end <= start < finish <= end, "overlapping/invalid child interval"); previous_end = finish
        analysis.timestamp(item["started_utc"]); analysis.timestamp(item["finished_utc"])
        analysis.equal(item, "monotonic_elapsed_seconds", (finish - start) / 1e9, "child duration")
        raw, log, rss = child_paths(output, index, identity)
        for field, source, hash_field in (("csv", raw, "output_sha256"), ("log", log, "log_sha256"), ("rss_log", rss, "rss_sha256")):
            analysis.equal(item, field, str(source), "child path")
            analysis.hash_check(source, item[hash_field]); inputs[str(source)] = native.sha(source)
        argv = command(frozen["binary"], cases[identity["case_id"]], identity)
        analysis.equal(item, "command", argv, "native argv")
        analysis.equal(item, "launch_command", ["/usr/bin/time", "-l", *argv], "launched argv")
        child_rows, child_diagnostics = check_rows(raw, cases[identity["case_id"]], identity["graph_seed"])
        analysis.equal(item, "certificate", native.check_certificate(log, child_rows), "native certificate")
        analysis.equal(item, "flagged_calls", sum(bool(row["diagnostic_flags"]) for row in child_diagnostics), "child flags")
        observations = analysis.check_rss(rss, item, RULE)
        require(all(row["process_group"] == item["process_group"] for row in observations), "RSS group differs from launched child")
        analysis.equal(item, "group_exit_verification", observations[-1], "post-exit group observation")
        exit_time = item.get("wrapper_exit_monotonic_ns")
        require(type(exit_time) is int and start <= exit_time <= observations[-1]["monotonic_ns"] <= finish,
                "group verification is not after wrapper exit")
        require(observations[-1]["validation"] == "pass" and not observations[-1]["members"], "owned group exit not verified")
        monitor.validate_monitor(item)
        rows.extend(child_rows); diagnostics.extend(child_diagnostics)
        resources.append({**identity, **{key: item[key] for key in ("rss_observations", "rss_unavailable", "rss_nonempty_observations", "sampled_peak_rss_kib")},
                          **{key: item["recovery_monitor"][key] for key in ("max_sampler_duration_ns", "max_request_gap_ns")}})
    native.check_fingerprints(rows)
    actual = [row for _, row in native.base.read_csv(output, FIELDS)]
    require(actual == [{field: str(row[field]) for field in FIELDS} for row in rows], "combined CSV differs from exact ordered child concatenation")
    analysis.equal(info, "call_diagnostics", diagnostics, "clock diagnostics")
    analysis.equal(info, "capture_clock_flags", native.capture_clock_flags(info), "capture flags")
    for field, value in (("checked_rows", 840), ("checked_timed_rows", 720), ("checked_warmup_rows", 120),
                         ("flagged_calls", sum(bool(row["diagnostic_flags"]) for row in diagnostics))):
        analysis.equal(info, field, value, "capture counts")
    return info, cases, rows, diagnostics, resources, inputs


def aggregate(rows):
    blocks = defaultdict(dict); runtimes = defaultdict(lambda: defaultdict(list))
    identities = {row["case_id"]: {field: row[field] for field in analysis.IDENTITY} for row in rows}
    for row in rows:
        if row["phase"] != "timed": continue
        key = (row["case_id"], row["graph_seed"], row["kkt_seed"], row["repetition"])
        require(row["algorithm"] not in blocks[key], "duplicate algorithm in paired block")
        blocks[key][row["algorithm"]] = row
        for metric, field in analysis.METRICS.items():
            runtimes[(row["case_id"], row["algorithm"], metric)][row["graph_seed"]].append(row[field])
    pairs = []; ratios = defaultdict(lambda: defaultdict(list))
    for (case, graph, seed, rep), block in blocks.items():
        require(set(block) == set(ALGORITHMS), "incomplete six-algorithm paired block")
        for competitor in ALGORITHMS[1:]:
            for metric, field in analysis.METRICS.items():
                ratio = block["kkt"][field] / block[competitor][field]
                pairs.append({**identities[case], "graph_seed": graph, "kkt_seed": seed, "repetition": rep,
                              "competitor": competitor, "metric": metric, "kkt_ns": block["kkt"][field],
                              "competitor_ns": block[competitor][field], "kkt_over_competitor": ratio})
                ratios[(case, competitor, metric)][graph].append(ratio)
    comparisons = []; graph_comparisons = []; summary = []; graph_summary = []
    for collection, identity_field, graph_table, case_table, value_field in (
        (ratios, "competitor", graph_comparisons, comparisons, "median_paired_ratio"),
        (runtimes, "algorithm", graph_summary, summary, "median_ns")):
        for (case, name, metric), graphs in collection.items():
            medians = []; all_values = []
            for graph, values in graphs.items():
                median = statistics.median(values); medians.append(median); all_values.extend(values)
                item = {**identities[case], identity_field: name, "metric": metric, "graph_seed": graph,
                        value_field: median, "trial_min": min(values), "trial_max": max(values), "trials": len(values)}
                if identity_field == "competitor": item.update(individual_wins=sum(value < 1 for value in values))
                graph_table.append(item)
            item = {**identities[case], identity_field: name, "metric": metric,
                    value_field: statistics.median(all_values), "graph_min": min(medians), "graph_max": max(medians),
                    "trial_min": min(all_values), "trial_max": max(all_values), "trials": len(all_values)}
            if identity_field == "competitor": item.update(individual_wins=sum(value < 1 for value in all_values))
            case_table.append(item)
    return {"paired_ratios": pairs, "comparisons": comparisons, "graph_comparisons": graph_comparisons,
            "summary": summary, "graph_summary": graph_summary}


def analyze(args):
    info, cases, rows, diagnostics, resources, inputs = load(args.capture)
    output = args.output_dir.resolve(); require(not output.exists(), "refusing to overwrite analysis"); output.mkdir(parents=True)
    tables = aggregate(rows)
    for name, values in {**tables, "validated_calls": rows, "call_diagnostics": diagnostics, "resources": resources}.items():
        analysis.write_csv(output / (name + ".csv"), values)
    power_audit = {"status": "not_audited", "sleep_inhibition_verified": False}
    if args.power_log:
        source = args.power_log.resolve(strict=True); inputs[str(source)] = native.sha(source)
        events, malformed, reversals = power.parse_events(source.read_text(errors="replace"))
        associations = power.original.correlate(rows, events, power.original.sleep_intervals(events))
        analysis.write_csv(output / "call_power_associations.csv", associations)
        power_audit.update(status="archived_log_correlated", parser=power.PARSER, source=str(source), source_sha256=inputs[str(source)],
                           logged_overlap_calls=sum(bool(row["nominal_logged_sleep_overlap_ns"]) for row in associations),
                           unalignable_calls=sum(not row["utc_alignable"] for row in associations),
                           malformed_event_lines=len(malformed), source_order_reversals=len(reversals),
                           limitation="External log provided; query success/retention coverage not established here. No raw private power events are copied into the analysis.")
    write_json(output / "provenance.json", {"schema": "retention_control_analysis_v1", "validation": "pass",
               "checked_rows": len(rows), "capture": info, "input_sha256": inputs, "power_audit": power_audit,
               "rows_removed": 0, "rows_adjusted": 0, "aggregation": SEMANTICS["comparison"]}, exclusive=True)
    text = ["# Six-solver retained-edge Boruvka control", "", "All 840 solver outputs passed exact MST validation: "
            "720 timed calls and 120 checked warmups. Each algorithm occupies every timed position once per child. "
            "This is a fresh, separately declared two-graph-seed campaign; historical timing is not pooled.", "",
            SEMANTICS["purpose"], "", SEMANTICS["comparison"] + " Graph/trial ranges are descriptive, not confidence intervals.", "",
            f"All {info['flagged_calls']} clock-flagged calls and {len(info['capture_clock_flags'])} capture/child UTC flags remain included. "
            "Wall and CPU clocks are separate; neither flags nor power events change the observations. "
            "RSS is a sampled process-group sum, not a continuous peak. "
            f"Power-audit status: `{power_audit['status']}`; verified sleep inhibition is not claimed.", "",
            "| Case | Clock | KKT / compacting Boruvka | KKT / multigraph Boruvka | KKT / Kruskal | KKT / Prim | KKT / original Boruvka |",
            "|---|---|---:|---:|---:|---:|---:|"]
    index = {(row["case_id"], row["metric"], row["competitor"]): row for row in tables["comparisons"]}
    for case in cases:
        for metric in analysis.METRICS:
            values = [index[(case, metric, solver)]["median_paired_ratio"] for solver in ALGORITHMS[1:]]
            text.append(f"| {case} | {metric} | " + " | ".join(f"{value:.4f}" for value in values) + " |")
    text += ["", "Ratios below one favor KKT. Every trial pair, all five comparisons, both graph-seed medians, "
             "absolute runtimes, warmups, clock diagnostics and resource observations remain in the adjacent CSV tables. "
             "The code improvement versus reference KKT belongs to the separate earlier pilot; this campaign contains "
             "only candidate KKT and its five competitors. Finite measurements do not prove asymptotic dominance.", ""]
    (output / "README.md").write_text("\n".join(text))
    print("Strict analysis passed: 840 outputs, 1200 paired wall/CPU comparisons")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    prepare = actions.add_parser("preflight")
    for name in ("binary", "build-record", "parent-freeze", "manifest", "protocol", "freeze"):
        prepare.add_argument("--" + name, type=Path, required=True)
    run = actions.add_parser("capture")
    run.add_argument("--freeze", type=Path, required=True); run.add_argument("--output", type=Path, required=True)
    run.add_argument("--released", action="store_true")
    report = actions.add_parser("analyze")
    report.add_argument("--capture", type=Path, required=True); report.add_argument("--output-dir", type=Path, required=True)
    report.add_argument("--power-log", type=Path)
    args = parser.parse_args(); {"preflight": preflight, "capture": capture, "analyze": analyze}[args.action](args)


if __name__ == "__main__": main()
