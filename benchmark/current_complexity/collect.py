#!/usr/bin/env python3
"""Fixed 24-curve Google Benchmark capture with strict native provenance.

Requires a separately reviewed build validator and a real linked schema-smoke
receipt. Those are release prerequisites, not evidence manufactured here.
"""
import argparse
import csv
import importlib.util
import json
import math
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = Path.cwd().resolve()
sys.path.insert(0, str(ROOT / "benchmark"))
import run_eighth_sampling as parent_engine

control = parent_engine.control
native, analysis, monitor = control.native, control.analysis, control.monitor
require, write_json = control.require, control.write_json
PARENT_SHA256 = "2be7556d15b58f3f65cc380ac22b67c57fdf8aea747d651b9d648c6a1aa59d2f"
GOOGLE_COMMIT = "73d4d5e8d6d449fc8663765a42aa8aeeee844489"
FAMILIES = ("leaf_hierarchy4", "leaf_shuffled4", "gnm_random")
ALGORITHMS = ("kkt", "multigraph_boruvka")
GRAPH_SEEDS, SAMPLING_SEEDS = (19000013, 19000043), (3001, 3011)
SIZES = tuple(1 << exponent for exponent in range(10, 21))
DEADLINE_SECONDS = 3600
RULE = control.RULE
FIELDS = tuple("family,algorithm,n,m,N,graph_seed,sampling_seed,input_fingerprint,topology_fingerprint,size_order,invocation,phase,iteration,elapsed_ns,utc_start_ns,utc_end_ns,process_cpu_start_ns,process_cpu_end_ns,process_cpu_elapsed_ns,validation".split(","))
TEXT_FIELDS = {"family", "algorithm", "size_order", "phase", "validation"}
CERTIFICATE_FIELDS = {"family", "algorithm", "n", "m", "graph_seed", "sampling_seed", "invocation", "input_fingerprint", "topology_fingerprint", "validation"}
MAX_NS, UINT64_MAX = (1 << 63) - 1, (1 << 64) - 1


def strict_json(text):
    def pairs(values):
        result = {}
        for key, value in values:
            require(key not in result, "duplicate JSON key: " + key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("nonfinite JSON: " + value)
    value = json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)
    def finite(item):
        if type(item) is float: require(math.isfinite(item), "nonfinite JSON numeric overflow")
        elif type(item) is dict:
            for child in item.values(): finite(child)
        elif type(item) is list:
            for child in item: finite(child)
    finite(value)
    return value


def read_json(path):
    return strict_json(Path(path).read_text())


def exact(actual, expected, label):
    require(type(actual) is type(expected) and actual == expected, label)
    if type(expected) is dict:
        for key in expected: exact(actual[key], expected[key], label + ": " + str(key))
    elif type(expected) in (list, tuple):
        for index, value in enumerate(expected): exact(actual[index], value, label + ": " + str(index))


def digest(path, expected=None):
    path = Path(path).resolve(strict=True)
    value = native.sha(path)
    if expected is not None: exact(value, expected, "artifact changed: " + str(path))
    return value


def recheck(bound):
    for source, expected in bound.items():
        require(type(source) is str and Path(source).is_absolute(), "bound path must be absolute")
        require(type(expected) is str and re.fullmatch(r"[0-9a-f]{64}", expected), "invalid bound digest")
        digest(source, expected)


def module(path, name):
    path = Path(path).resolve(strict=True)
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "cannot load reviewed validation source")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def schedule():
    return [dict(family=family, algorithm=algorithm, graph_seed=graph,
                 sampling_seed=sampling, size_order="ascending" if gi == 0 else "descending")
            for family in FAMILIES for gi, graph in enumerate(GRAPH_SEEDS)
            for si, sampling in enumerate(SAMPLING_SEEDS)
            for algorithm in (ALGORITHMS if (gi + si) % 2 == 0 else ALGORITHMS[::-1])]


def source_inventory():
    # Freeze the installed package, including tests and the future real build
    # validator. Results live in subdirectories and cannot change this list.
    sources = sorted(path for path in HERE.iterdir() if path.suffix in (".py", ".cpp", ".md"))
    for name in ("collect.py", "current_complexity.cpp", "PROTOCOL.md", "validate_build.py", "analyze_complexity.py"):
        require(HERE / name in sources, "unfulfilled source prerequisite: " + name)
    return {str(path): digest(path) for path in sources}


def artifact_proof(parent_path, build_path, smoke_path):
    """Use complete parent proof and future real build/smoke gates, unscoped.

    validate_build.py is deliberately not supplied as a placeholder that passes.
    Its reviewed check_record(path) must verify actual library acquisition/build,
    commands, toolchain/profile, correctness and group cleanup, returning the
    record plus its complete absolute bound_sha256 inventory. No compile or
    native launch may occur in that read-only validator.
    """
    parent_path, build_path, smoke_path = (Path(path).resolve(strict=True) for path in (parent_path, build_path, smoke_path))
    digest(parent_path, PARENT_SHA256)
    parent, _ = parent_engine.check_freeze(parent_path)
    exact(str(ROOT), parent["working_directory"], "run from the frozen eighth worktree")
    parent_build = parent["variants"]["eighth"]["build"]["record"]
    validator_path, analyzer_path = HERE / "validate_build.py", HERE / "analyze_complexity.py"
    validator_hash, analyzer_hash = digest(validator_path), digest(analyzer_path)
    validator = module(validator_path, "current_complexity_build_validation")
    build = validator.check_record(build_path)
    require(type(build) is dict, "build validator did not return a record")
    exact(build["parent_freeze"], str(parent_path), "wrong parent freeze path")
    exact(build["parent_freeze_sha256"], PARENT_SHA256, "wrong parent freeze")
    for key in ("object_paths", "object_sha256", "compiler", "compiler_command", "sdk"):
        exact(build[key], parent_build[key], "changed frozen production artifact: " + key)
    require(len(build["object_paths"]) == 8, "not all eight physical solver objects")
    for name, path in build["object_paths"].items(): digest(path, build["object_sha256"][name])
    exact(build["driver"], str(HERE / "current_complexity.cpp"), "different main source")
    for stem in ("driver", "binary", "library"):
        digest(build[stem], build[stem + "_sha256"])
    exact(build["google_benchmark_commit"], GOOGLE_COMMIT, "different Google Benchmark source")
    exact(build["validation"], "pass", "build not validated")
    exact(build["owned_groups_verified_empty"], True, "build/correctness exit unverified")
    require(type(build["bound_sha256"]) is dict and build["bound_sha256"], "missing complete build inventory")
    bound = dict(build["bound_sha256"])
    for stem in ("driver", "binary", "library"):
        exact(bound.get(build[stem]), build[stem + "_sha256"], "build inventory misses " + stem)
    recheck(bound)
    analyzer = module(analyzer_path, "current_complexity_analysis_contract")
    smoke_hash = digest(smoke_path); smoke = read_json(smoke_path)
    for key, value in {"schema": "current_complexity_schema_smoke_v1", "validation": "pass",
                       "google_benchmark_commit": GOOGLE_COMMIT, "native_execution": True,
                       "owned_groups_verified_empty": True, "schema_contract": analyzer.SCHEMA_CONTRACT,
                       **{key: build[key] for key in ("driver_sha256", "binary_sha256", "library_sha256")}}.items():
        exact(smoke.get(key), value, "actual linked schema smoke differs: " + key)
    require(type(smoke.get("bound_sha256")) is dict and smoke["bound_sha256"], "missing actual smoke evidence")
    # The real validator must independently read smoke raw/library JSON, lifecycle
    # and logs. Merely setting pass/true in a receipt is insufficient.
    validator.check_schema_smoke(smoke_path, build, analyzer.SCHEMA_CONTRACT)
    for key, value in smoke["bound_sha256"].items():
        require(key not in bound or bound[key] == value, "inconsistent bound evidence")
        bound[key] = value
    bound.update({str(parent_path): PARENT_SHA256, str(build_path): digest(build_path),
                  str(smoke_path): smoke_hash, str(validator_path): validator_hash,
                  str(analyzer_path): analyzer_hash})
    recheck(bound)
    return build, bound


def preflight(args):
    build, bound = artifact_proof(args.parent_freeze, args.build_record, args.schema_smoke)
    sources = source_inventory()
    for path in bound.keys() & sources.keys(): exact(bound[path], sources[path], "source changed during preflight")
    recheck(bound); recheck(sources)
    frozen = dict(schema="current_complexity_freeze_v1", created_utc=native.now(),
                  working_directory=str(ROOT), parent_freeze=str(args.parent_freeze.resolve()),
                  parent_freeze_sha256=PARENT_SHA256, build_record=str(args.build_record.resolve()),
                  build_record_sha256=digest(args.build_record), schema_smoke=str(args.schema_smoke.resolve()),
                  schema_smoke_sha256=digest(args.schema_smoke), source_sha256=sources,
                  parent_helpers=parent_engine.helpers(), bound_sha256=bound,
                  schedule=schedule(), sizes=list(SIZES), deadline_seconds=DEADLINE_SECONDS,
                  resource_rule=RULE, iterations=2, repetitions=3, warmups_per_callback=1,
                  **{key: build[key] for key in ("driver", "driver_sha256", "binary", "binary_sha256", "library", "library_sha256")})
    args.freeze.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.freeze, frozen, exclusive=True)
    print("Prospective freeze ready: 24 curves / 2376 checked calls; no capture executed")


def check_freeze(path):
    path = Path(path).resolve(strict=True); initial = digest(path); frozen = read_json(path)
    for key, value in dict(schema="current_complexity_freeze_v1", working_directory=str(ROOT),
                           parent_freeze_sha256=PARENT_SHA256, schedule=schedule(), sizes=list(SIZES),
                           deadline_seconds=DEADLINE_SECONDS, resource_rule=RULE, iterations=2,
                           repetitions=3, warmups_per_callback=1).items():
        exact(frozen.get(key), value, "frozen declaration differs: " + key)
    exact(frozen["source_sha256"], source_inventory(), "package source changed")
    exact(frozen["parent_helpers"], parent_engine.helpers(), "frozen ancestor helper changed")
    digest(frozen["build_record"], frozen["build_record_sha256"])
    digest(frozen["schema_smoke"], frozen["schema_smoke_sha256"])
    build, bound = artifact_proof(frozen["parent_freeze"], frozen["build_record"], frozen["schema_smoke"])
    exact(frozen["bound_sha256"], bound, "artifact proof inventory differs")
    for key in ("driver", "driver_sha256", "binary", "binary_sha256", "library", "library_sha256"):
        exact(frozen[key], build[key], "different linked artifact: " + key)
    digest(path, initial)
    return frozen


def directed_sizes(spec):
    require(spec in schedule(), "undeclared curve")
    return SIZES if spec["size_order"] == "ascending" else SIZES[::-1]


def check_rows(path, spec):
    rows, diagnostics = [], []
    with Path(path).open(newline="") as source:
        reader = csv.DictReader(source)
        exact(reader.fieldnames, list(FIELDS), "wrong native trace header")
        for raw in reader:
            require(set(raw) == set(FIELDS) and None not in raw.values(), "malformed native row")
            row = dict(raw)
            for key in set(FIELDS) - TEXT_FIELDS:
                require(re.fullmatch(r"0|[1-9][0-9]*", raw[key]) is not None, "noncanonical integer: " + key)
                row[key] = int(raw[key])
                require(row[key] <= (MAX_NS if key.endswith("_ns") else UINT64_MAX), "integer outside domain")
            rows.append(row)
    expected = [(n, invocation, phase, iteration) for n in directed_sizes(spec) for invocation in range(3)
                for phase, iteration in (("warmup", 0), ("timed", 0), ("timed", 1))]
    require(len(rows) == len(expected) == 99, "incomplete 99-call curve")
    previous_cpu = previous_utc = None; fingerprints = {}
    for row, identity in zip(rows, expected):
        exact(tuple(row[key] for key in ("n", "invocation", "phase", "iteration")), identity, "wrong native call order")
        for key, value in spec.items(): exact(row[key], value, "native curve identity differs: " + key)
        exact(row["validation"], "pass", "native solver certificate failed")
        m = row["n"] * (16 if spec["family"] == "gnm_random" else 32)
        exact(row["m"], m, "wrong edge count"); exact(row["N"], row["n"] + m, "wrong complexity N")
        steady, cpu = row["elapsed_ns"], row["process_cpu_elapsed_ns"]
        require(steady > 0 and cpu > 0 and row["utc_start_ns"] > 0 and row["utc_end_ns"] > 0, "invalid positive clock")
        require(row["process_cpu_end_ns"] - row["process_cpu_start_ns"] == cpu, "CPU interval mismatch")
        require(previous_cpu is None or row["process_cpu_start_ns"] >= previous_cpu, "overlapping CPU intervals")
        previous_cpu = row["process_cpu_end_ns"]
        pair = row["input_fingerprint"], row["topology_fingerprint"]
        require(row["n"] not in fingerprints or fingerprints[row["n"]] == pair, "callback input changed")
        fingerprints[row["n"]] = pair
        utc = row["utc_end_ns"] - row["utc_start_ns"]; threshold4 = max(2_000_000_000, cpu); flags = []
        if utc < 0: flags.append("realtime_reversed_within_call")
        if previous_utc is not None and row["utc_start_ns"] < previous_utc: flags.append("realtime_reversed_between_calls")
        if 4 * (steady - cpu) > threshold4: flags.append("steady_exceeds_process_cpu")
        if 4 * (cpu - steady) > threshold4: flags.append("process_cpu_exceeds_steady")
        if 4 * abs(utc - steady) > threshold4: flags.append("utc_steady_duration_disagreement")
        previous_utc = row["utc_end_ns"]
        diagnostics.append({**spec, **{key: row[key] for key in ("n", "invocation", "phase", "iteration")},
                            "diagnostic_flags": flags, "excluded": False})
    return rows, diagnostics


def certificates(path, rows):
    markers = [line for line in Path(path).read_text().splitlines() if "complexity_certificate" in line]
    require(len(markers) == 33, "missing/duplicate native callback certificate")
    result = []
    for marker, row in zip(markers, (row for row in rows if row["phase"] == "warmup")):
        require(marker.startswith("complexity_certificate_v1 "), "unsupported certificate marker")
        value = strict_json(marker[len("complexity_certificate_v1 "):])
        require(type(value) is dict and set(value) == CERTIFICATE_FIELDS, "wrong certificate schema")
        for key in CERTIFICATE_FIELDS: exact(value[key], row[key], "native certificate differs: " + key)
        result.append(value)
    return result


def fingerprint_matrix(rows, complete=False):
    values = {}
    for row in rows:
        key = row["family"], row["n"], row["graph_seed"]
        pair = row["input_fingerprint"], row["topology_fingerprint"]
        require(key not in values or values[key] == pair, "algorithm/sampler input changed")
        values[key] = pair
    for n in SIZES:
        for graph in GRAPH_SEEDS:
            a, b = (values.get((family, n, graph)) for family in FAMILIES[:2])
            if a is not None and b is not None:
                require(a[1] == b[1] and a[0] != b[0], "hierarchy/shuffled topology twin mismatch")
    if complete:
        exact(set(values), {(family, n, graph) for family in FAMILIES for n in SIZES for graph in GRAPH_SEEDS}, "incomplete fingerprint matrix")


def paths(output, index):
    prefix = output.with_name(output.stem + "_curves") / f"{index:02d}"
    return {"raw_csv": prefix.with_suffix(".csv"), "benchmark_json": prefix.with_suffix(".benchmark.json"),
            "log": prefix.with_suffix(".log"), "console": prefix.with_suffix(".console.txt"),
            "rss_log": prefix.with_suffix(".rss.jsonl")}


def command(binary, spec, files):
    directed_sizes(spec)
    return ["/usr/bin/arch", "-arm64", binary, spec["family"], spec["algorithm"], str(spec["graph_seed"]),
            str(spec["sampling_seed"]), spec["size_order"], str(files["raw_csv"]), str(files["benchmark_json"])]


def cleanup_owned_group(process, sampler, info):
    prior_unknown = info["native_process_may_still_be_running"]
    info["native_process_may_still_be_running"] = True
    previous = signal.getsignal(signal.SIGTERM)
    receipt = dict(process_group=process.pid if process else None, native_exit_known=False,
                   group_exit_known=False, native_process_may_still_be_running=True)
    try:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        try: receipt = monitor.bounded_terminate(process, sampler)
        except BaseException as error: receipt.update(error=repr(error))
        finally:
            info["cleanup"].append(receipt)
            proved = (receipt.get("native_exit_known") is True and receipt.get("group_exit_known") is True and
                      receipt.get("native_process_may_still_be_running") is False)
            info["native_process_may_still_be_running"] = prior_unknown or not proved
    finally: signal.signal(signal.SIGTERM, previous)


def resources(item):
    require(type(item["process_group"]) is int and item["process_group"] > 0, "invalid owned group")
    observations = analysis.check_rss(Path(item["rss_log"]), item, RULE)
    begin, end = analysis.monotonic_interval(item)
    exited = item.get("wrapper_exit_monotonic_ns")
    require(type(exited) is int and begin <= exited <= observations[-1]["monotonic_ns"] <= end, "exit/group proof ordering")
    require(exited - begin <= DEADLINE_SECONDS * 1_000_000_000, "native-exit deadline exceeded")
    require(all(row["process_group"] == item["process_group"] for row in observations), "wrong observed group")
    exact(item["group_exit_verification"], observations[-1], "wrong final group proof")
    require(observations[-1]["validation"] == "pass" and observations[-1]["members"] == [], "owned group not empty")
    monitor.validate_monitor(item)


def validate_curve(item, spec, analyzer):
    rows, flags = check_rows(item["raw_csv"], spec)
    certs = certificates(item["log"], rows)
    # Full field/name/unit identities and native/manual joins are independently
    # reconstructed by the analyzer; no fitted result is used to accept a run.
    analyzer.validate_curve_library(read_json(item["benchmark_json"]), spec, rows)
    return rows, flags, certs


def capture(args, sampler=None, popen=None):
    require(args.released, "capture requires explicit quiet --released")
    freeze = args.freeze.resolve(strict=True); frozen = check_freeze(freeze); freeze_hash = digest(freeze)
    output = args.output.resolve(); folder = output.with_name(output.stem + "_curves")
    require(output.suffix == ".json" and not output.exists() and not folder.exists(), "refusing to overwrite capture")
    output.parent.mkdir(parents=True, exist_ok=True); folder.mkdir()
    sampler = sampler if sampler is not None else monitor.BoundedSampler(monitor.LibprocProvider())
    popen = popen if popen is not None else subprocess.Popen
    analyzer = module(HERE / "analyze_complexity.py", "current_complexity_curve_validation")
    info = dict(schema="current_complexity_capture_v1", validation="running", freeze=str(freeze), freeze_sha256=freeze_hash,
                frozen_protocol=frozen, output=str(output), started_utc=native.now(), started_monotonic_ns=time.monotonic_ns(),
                captures=[], cleanup=[], rows_removed=0, rows_adjusted=0, native_process_may_still_be_running=False)
    write_json(output, info, exclusive=True)
    rows, flags = [], []; previous = signal.getsignal(signal.SIGTERM)
    def interrupted(signum, frame): raise KeyboardInterrupt("capture received signal " + str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    try:
        for index, spec in enumerate(schedule(), 1):
            require(not sampler.poisoned, "poisoned sampler forbids another child")
            digest(freeze, freeze_hash); check_freeze(freeze)
            files = paths(output, index)
            item = dict(spec=spec, command=command(frozen["binary"], spec, files), **{key: str(path) for key, path in files.items()},
                        started_utc=native.now(), started_monotonic_ns=time.monotonic_ns())
            info["captures"].append(item); write_json(output, info)
            process = None; failure = None; observations = []; unavailable = 0
            try:
                with files["console"].open("x") as stdout, files["log"].open("x") as stderr, files["rss_log"].open("x") as resource:
                    process = popen(item["command"], cwd=frozen["working_directory"], stdout=stdout, stderr=stderr, start_new_session=True)
                    item["process_group"] = process.pid
                    def observe():
                        observation = sampler.sample(process.pid); observations.append(observation)
                        resource.write(json.dumps(observation, allow_nan=False) + "\n"); resource.flush()
                        return observation
                    while True:
                        observation = observe()
                        require(not sampler.poisoned, "RSS sampler poisoned; no next child")
                        if observation["validation"] == "pass":
                            unavailable = 0
                            require(observation["rss_kib"] <= RULE["rss_limit_kib"], "sampled group RSS exceeded 40 GiB")
                        else:
                            unavailable += 1; require(unavailable < 3, "three unavailable RSS observations")
                        remaining = DEADLINE_SECONDS - (time.monotonic_ns() - item["started_monotonic_ns"]) / 1e9
                        require(remaining > 0, "curve exceeded native-exit deadline")
                        try:
                            process.wait(timeout=min(RULE["poll_seconds"], remaining))
                            item["wrapper_exit_monotonic_ns"] = time.monotonic_ns(); break
                        except subprocess.TimeoutExpired: pass
                    require(item["wrapper_exit_monotonic_ns"] - item["started_monotonic_ns"] <= DEADLINE_SECONDS * 1_000_000_000,
                            "native completion observed beyond deadline")
                    require(type(process.returncode) is int and process.returncode == 0, "native driver failed")
                    item["group_exit_verification"] = observe()
                    require(not sampler.poisoned and item["group_exit_verification"]["validation"] == "pass" and
                            not item["group_exit_verification"]["members"], "native group exit not verified")
            except BaseException as error:
                failure = error; cleanup_owned_group(process, sampler, info)
            finally:
                item.update(exit_status=process.returncode if process else None, interruption=repr(failure) if failure else None,
                            finished_utc=native.now(), finished_monotonic_ns=time.monotonic_ns(), rss_observations=len(observations),
                            rss_unavailable=sum(row["validation"] != "pass" for row in observations),
                            rss_nonempty_observations=sum(row["validation"] == "pass" and bool(row["members"]) for row in observations),
                            sampled_peak_rss_kib=max((row["rss_kib"] for row in observations if row["validation"] == "pass"), default=None),
                            recovery_monitor=monitor.recovery_monitor(sampler.events.get(process.pid, [])[:len(observations)] if process else []))
                item["monotonic_elapsed_seconds"] = (item["finished_monotonic_ns"] - item["started_monotonic_ns"]) / 1e9
                for key, path in files.items():
                    if path.exists(): item[("raw" if key == "raw_csv" else "benchmark" if key == "benchmark_json" else "rss" if key == "rss_log" else key) + "_sha256"] = digest(path)
                write_json(output, info)
            if failure: raise failure
            digest(freeze, freeze_hash); check_freeze(freeze)
            child_rows, child_flags, certs = validate_curve(item, spec, analyzer)
            resources(item); fingerprint_matrix(rows + child_rows)
            item.update(validation="pass", checked_raw_rows=99, certificates=certs, flagged_calls=sum(bool(row["diagnostic_flags"]) for row in child_flags))
            rows.extend(child_rows); flags.extend(child_flags); write_json(output, info)
        fingerprint_matrix(rows, complete=True)
        require(len(rows) == 2376, "incomplete native curve matrix")
        info.update(validation="pass", checked_curves=24, checked_raw_rows=2376, checked_timed_rows=1584, checked_warmup_rows=792)
    except BaseException as error:
        info.update(validation="failed", error=repr(error)); raise
    finally:
        signal.signal(signal.SIGTERM, previous)
        info.update(finished_utc=native.now(), finished_monotonic_ns=time.monotonic_ns(), call_diagnostics=flags,
                    flagged_calls=sum(bool(row["diagnostic_flags"]) for row in flags))
        info["monotonic_elapsed_seconds"] = (info["finished_monotonic_ns"] - info["started_monotonic_ns"]) / 1e9
        info["capture_clock_flags"] = native.capture_clock_flags(info)
        write_json(output, info)
    try: load(output)
    except BaseException as error:
        info.update(validation="failed", error=repr(error)); write_json(output, info); raise
    print("Validated 24 curves / 2376 native calls; all owned groups empty")


def load(path):
    path = Path(path).resolve(strict=True); initial = digest(path); info = read_json(path)
    for key, value in dict(schema="current_complexity_capture_v1", validation="pass", rows_removed=0, rows_adjusted=0,
                           cleanup=[], native_process_may_still_be_running=False, checked_curves=24, checked_raw_rows=2376,
                           checked_timed_rows=1584, checked_warmup_rows=792, output=str(path)).items():
        exact(info.get(key), value, "capture differs: " + key)
    require("error" not in info, "failed capture cannot be analyzed")
    digest(info["freeze"], info["freeze_sha256"]); frozen = check_freeze(info["freeze"])
    exact(info["frozen_protocol"], frozen, "capture freeze differs")
    bound = {**frozen["bound_sha256"], **frozen["source_sha256"], **frozen["parent_helpers"],
             str(path): initial, info["freeze"]: info["freeze_sha256"]}
    analysis.timestamp(info["started_utc"]); analysis.timestamp(info["finished_utc"])
    begin, end = analysis.monotonic_interval(info)
    exact(info["monotonic_elapsed_seconds"], (end - begin) / 1e9, "capture monotonic duration")
    require(type(info["captures"]) is list and len(info["captures"]) == 24, "incomplete curve schedule")
    analyzer = module(HERE / "analyze_complexity.py", "current_complexity_curve_reload")
    previous_end = begin; rows = []; flags = []
    for index, (spec, item) in enumerate(zip(schedule(), info["captures"]), 1):
        for key, value in dict(spec=spec, validation="pass", checked_raw_rows=99, exit_status=0, interruption=None).items():
            exact(item.get(key), value, "curve differs: " + key)
        files = paths(path, index)
        exact(item["command"], command(frozen["binary"], spec, files), "different native command")
        for key, source in files.items():
            exact(item[key], str(source), "wrong raw evidence path")
            hash_key = ("raw" if key == "raw_csv" else "benchmark" if key == "benchmark_json" else "rss" if key == "rss_log" else key) + "_sha256"
            bound[str(source)] = digest(source, item[hash_key])
        start, finish = analysis.monotonic_interval(item)
        require(previous_end <= start < finish <= end, "overlapping curve groups")
        previous_end = finish
        analysis.timestamp(item["started_utc"]); analysis.timestamp(item["finished_utc"])
        exact(item["monotonic_elapsed_seconds"], (finish - start) / 1e9, "curve monotonic duration")
        resources(item)
        child_rows, child_flags, certs = validate_curve(item, spec, analyzer)
        exact(item["certificates"], certs, "stored certificates differ")
        exact(item["flagged_calls"], sum(bool(row["diagnostic_flags"]) for row in child_flags), "stored clock flag count")
        rows.extend(child_rows); flags.extend(child_flags)
    fingerprint_matrix(rows, complete=True)
    exact(info["call_diagnostics"], flags, "clock diagnostics differ")
    exact(info["flagged_calls"], sum(bool(row["diagnostic_flags"]) for row in flags), "global flags differ")
    exact(info["capture_clock_flags"], native.capture_clock_flags(info), "capture clock diagnostics differ")
    recheck(bound)
    return info, info["captures"], bound


def main():
    parser = argparse.ArgumentParser(description=__doc__); commands = parser.add_subparsers(dest="mode", required=True)
    pre = commands.add_parser("preflight")
    for field in ("parent-freeze", "build-record", "schema-smoke", "freeze"): pre.add_argument("--" + field, type=Path, required=True)
    cap = commands.add_parser("capture"); cap.add_argument("--freeze", type=Path, required=True)
    cap.add_argument("--output", type=Path, required=True); cap.add_argument("--released", action="store_true")
    check = commands.add_parser("check"); check.add_argument("capture", type=Path)
    args = parser.parse_args()
    if args.mode == "preflight": preflight(args)
    elif args.mode == "capture": capture(args)
    else:
        load(args.capture); print("Complete capture/provenance/resource validation passed")


if __name__ == "__main__": main()
