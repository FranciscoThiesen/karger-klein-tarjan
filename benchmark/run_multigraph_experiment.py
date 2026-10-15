#!/usr/bin/env python3
"""Fresh, serial paired-binary screen; historical capture helpers stay unchanged.

Preflight freezes both builds and the entire schedule. Capture needs --released.
Every child retains the original five-solver native interface and certificate.
Analysis rereads raw children, certificates, monitor evidence and combined rows.
No run adjusts/removes samples or treats a clock flag as proof of host sleep.
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

import run_mst_search as native
import analyze_mst_search as analysis
import recover_mst_search as monitor
import audit_attachment_recovery_power as corrected_power

HERE = Path(__file__).resolve()
VARIANTS = ("reference", "multigraph")
GRAPH_SEEDS = (2000003, 2000029)
SAMPLING_SEED = 607
REPETITIONS, WARMUPS = 5, 1
BASE_FLAGS = ["-std=c++17", "-O3", "-Wall", "-Wextra", "-march=native"]
OBJECTS = {f"{name}/{name}.o" for name in ("boruvka", "kruskal", "prim", "lca", "union_find", "graph_utils", "kkt")} | {"verifier/verifier_v2.o"}
FIELDS = ("variant", *native.FIELDS)
EXPECTED_CASES = {
    (family, n, 16, 0) for family in ("leaf_hierarchy4", "leaf_distance4")
    for n in (65536, 1048576)
} | {(family, 262144, 16, 0) for family in ("leaf_shuffled4", "leaf_random4")} \
  | {(family, 262144, 64, 0) for family in ("lifted_hierarchy4", "lifted_random4")} \
  | {("gnm_random", 65536, 128, 0), ("gnm_random", 262144, 16, 0)}
RULE = {"rss_limit_kib": 40 * 1024**2, "poll_seconds": 2,
        "sample_wait_limit_seconds": monitor.TIMEOUT_SECONDS,
        "measure": monitor.RSS_MEASURE,
        "failure": "Stop above 40 GiB, after three consecutive unavailable observations, or immediately after a sampler timeout; retain all partial evidence. Unknown native/group exit blocks every subsequent child."}
SEMANTICS = {
    "schedule": "graph seed; case; adjacent reference/multigraph children. Second graph seed reverses both case order and variant order. Native algorithm=(order+repetition)%5; five timed repetitions balance positions.",
    "timing_boundary": "Original native tuple interface and native return types. KKT/compactor input conversion and temporary input destruction timed; returned-result destruction and exact validation excluded. UTC and process CPU envelopes are slightly wider than steady elapsed.",
    "certificate_scope": "Independent native reference certificate once per child, then exact unique-MST ID/tuple validation for every warmup and timed call.",
    "clock_semantics": "Steady elapsed and process CPU remain separate. Clock flags are descriptive, never a reason to trim or correct data. UTC reversals remain in raw endpoints. Power-log correlation uses actual Sleep/Wake/DarkWake transitions; Wake Requests do not close sleep.",
    "power_semantics": "No verified sleep inhibition is inferred. An absent logged overlap is not proof of an awake, quiet host. Power auditing is post-capture only and never launches pmset automatically.",
    "sampling_semantics": "Variants share input and starting seed; different edge retention/order can change the internal RNG trajectory. This is a whole-implementation comparison, not a matched sampled-subgraph ablation.",
    "comparison_aggregation": "Variant case summary: median of ten paired trial ratios; graph summary: median of five ratios. Original per-variant KKT/competitor tables separately retain medians over repetitions, sampling seeds, then graph seeds.",
}
require = native.base.require


def write_json(path, value, exclusive=False):
    mode = "x" if exclusive else "w"
    with Path(path).open(mode) as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def helpers():
    extra = (HERE, Path(monitor.__file__).resolve(), Path(corrected_power.__file__).resolve(),
             Path(corrected_power.original.__file__).resolve())
    return {**native.helpers(), **{str(path): native.sha(path) for path in extra}}


def cases_from_manifest(path):
    cases = native.load_manifest(path)
    actual = {tuple(spec[field] for field in native.base.MANIFEST_FIELDS) for spec in cases.values()}
    require(actual == EXPECTED_CASES and len(cases) == 10, "manifest must contain exactly the ten declared screen cases")
    return cases


def schedule(cases):
    result = []
    for seed_index, graph_seed in enumerate(GRAPH_SEEDS):
        ordered_cases = list(cases) if seed_index == 0 else list(reversed(cases))
        variants = VARIANTS if seed_index == 0 else tuple(reversed(VARIANTS))
        for case in ordered_cases:
            for variant in variants:
                result.append({"variant": variant, "case_id": case,
                               "graph_seed": graph_seed, "kkt_seed": SAMPLING_SEED})
    return result


def command(binary, spec, item):
    return [str(binary), "--family", spec["family"], "--n", str(spec["n"]),
            "--density", str(spec["density"]), "--graph-seed", str(item["graph_seed"]),
            "--kkt-seed", str(item["kkt_seed"]), "--repetitions", str(REPETITIONS),
            "--warmups", str(WARMUPS)]


def normalized_build_command(argv, variant):
    require(type(argv) is list and len(argv) == 10 and
            argv[:5] == ["/usr/bin/arch", "-arm64", "/usr/bin/make", "-B", "-j4"] and
            argv[-1] == "mst-search-large-stack" and all(type(arg) is str for arg in argv),
            "expected the declared native arm64 Make build argv")
    variables = dict(arg.split("=", 1) for arg in argv[5:9] if "=" in arg)
    require(set(variables) == {"CXX", "BUILD_DIR", "BIN_DIR", "CXXFLAGS"} and
            variables["CXX"] == "/usr/bin/clang++" and variables["BUILD_DIR"] and variables["BIN_DIR"],
            "unexpected build variable or compiler")
    expected_flags = BASE_FLAGS + (["-DKKT_EXPERIMENT_RETAIN_PARALLEL"] if variant == "multigraph" else [])
    require(shlex.split(variables["CXXFLAGS"]) == expected_flags, "unexpected optimization/instrumentation/macro flags")
    return ["BUILD_DIR=<variant>" if arg.startswith("BUILD_DIR=") else
            "BIN_DIR=<variant>" if arg.startswith("BIN_DIR=") else
            "CXXFLAGS=" + " ".join(BASE_FLAGS) if arg.startswith("CXXFLAGS=") else arg for arg in argv]


def build_record(path, variant, binary, sources, recipe):
    path = Path(path).resolve(strict=True)
    record = analysis.read_json(path)
    for field, expected in (("variant", variant), ("binary", str(binary)),
                            ("binary_sha256", native.sha(binary)), ("source_sha256", sources),
                            ("build_recipe_sha256", {"Makefile": recipe})):
        analysis.equal(record, field, expected, "build record")
    normalized_build_command(record.get("build_command"), variant)
    analysis.equal(record, "build_exit_status", 0, "build exit")
    analysis.equal(record, "compiler_command", ["/usr/bin/arch", "-arm64", "/usr/bin/clang++", "--version"], "compiler probe")
    require(type(record.get("sdk")) is str and record["sdk"], "missing SDK")
    analysis.inventory(record.get("object_sha256"), "build objects")
    require(set(record["object_sha256"]) == OBJECTS, "incorrect native object inventory")
    compiler = record.get("compiler")
    require(type(compiler) is str and "Apple clang" in compiler and "arm64" in compiler,
            "build record must identify native Apple clang arm64")
    log = Path(record["build_log"]).resolve(strict=True)
    analysis.equal(record, "build_log", str(log), "build record")
    analysis.hash_check(log, record.get("build_log_sha256"))
    return {"path": str(path), "sha256": native.sha(path), "record": record}


def check_build_pair(variants):
    reference, candidate = (variants[variant]["build"]["record"] for variant in VARIANTS)
    for field in ("compiler", "compiler_command", "sdk", "source_sha256", "build_recipe_sha256"):
        analysis.equal(candidate, field, reference[field], "paired build provenance")
    require(normalized_build_command(reference["build_command"], "reference") ==
            normalized_build_command(candidate["build_command"], "multigraph"), "build commands differ beyond macro/directories")
    for name in OBJECTS - {"kkt/kkt.o"}:
        analysis.equal(candidate["object_sha256"], name, reference["object_sha256"][name], "unchanged production object")
    for variable in ("BUILD_DIR=", "BIN_DIR="):
        require(next(arg for arg in reference["build_command"] if arg.startswith(variable)) !=
                next(arg for arg in candidate["build_command"] if arg.startswith(variable)), "variants must use distinct build/bin directories")


def preflight(args):
    root = Path.cwd().resolve()
    manifest = args.manifest.resolve(strict=True)
    protocol = args.protocol.resolve(strict=True)
    cases = cases_from_manifest(manifest)
    sources = native.source_inventory(root)
    recipe = native.sha(root / "Makefile")
    variants = {}
    for variant in VARIANTS:
        binary = getattr(args, variant + "_binary").resolve(strict=True)
        variants[variant] = {"binary": str(binary), "binary_sha256": native.sha(binary),
                             "binary_profile": native.binary_profile(binary),
                             "build": build_record(getattr(args, variant + "_build_record"),
                                                   variant, binary, sources, recipe)}
    require(variants["reference"]["binary"] != variants["multigraph"]["binary"], "variants need distinct binary paths")
    require(variants["reference"]["binary_sha256"] != variants["multigraph"]["binary_sha256"],
            "reference and candidate binaries are identical")
    check_build_pair(variants)
    freeze = {"schema": "multigraph_experiment_freeze_v1", "created_utc": native.now(),
              "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "working_directory": str(root), "platform": platform.platform(), "machine": platform.machine(),
              "manifest": str(manifest), "manifest_sha256": native.sha(manifest),
              "protocol": str(protocol), "protocol_sha256": native.sha(protocol),
              "source_sha256": sources, "python_source_sha256": helpers(),
              "build_recipe_sha256": {"Makefile": recipe}, "variants": variants,
              "graph_seeds": list(GRAPH_SEEDS), "sampling_seeds": [SAMPLING_SEED],
              "repetitions": REPETITIONS, "warmups": WARMUPS,
              "algorithms": list(native.ALGORITHMS), "resource_rule": RULE,
              "semantics": SEMANTICS, "schedule": schedule(cases)}
    args.freeze.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.freeze, freeze, exclusive=True)
    print(json.dumps({"validation": "pass", "native_capture_started": False,
                      "freeze": str(args.freeze.resolve()), "freeze_sha256": native.sha(args.freeze),
                      "children": len(freeze["schedule"]), "checked_calls_if_complete": 1200}, indent=2))


def check_freeze(path, verify_current=True):
    path = Path(path).resolve(strict=True)
    frozen = analysis.read_json(path)
    for field, expected in (("schema", "multigraph_experiment_freeze_v1"),
                            ("graph_seeds", list(GRAPH_SEEDS)), ("sampling_seeds", [SAMPLING_SEED]),
                            ("repetitions", REPETITIONS), ("warmups", WARMUPS),
                            ("algorithms", list(native.ALGORITHMS)), ("resource_rule", RULE),
                            ("semantics", SEMANTICS)):
        analysis.equal(frozen, field, expected, "frozen protocol")
    manifest = Path(frozen["manifest"]).resolve(strict=True)
    analysis.hash_check(manifest, frozen["manifest_sha256"])
    analysis.hash_check(Path(frozen["protocol"]), frozen["protocol_sha256"])
    cases = cases_from_manifest(manifest)
    analysis.equal(frozen, "schedule", schedule(cases), "frozen protocol")
    require(set(frozen["variants"]) == set(VARIANTS), "incorrect variant matrix")
    analysis.inventory(frozen["source_sha256"], "native sources")
    require(analysis.NATIVE_FILES <= frozen["source_sha256"].keys(), "missing native source inventory")
    if verify_current:
        root = Path(frozen["working_directory"])
        analysis.equal(frozen, "source_sha256", native.source_inventory(root), "current source inventory")
        analysis.equal(frozen, "python_source_sha256", helpers(), "current helper inventory")
        analysis.equal(frozen, "build_recipe_sha256", {"Makefile": native.sha(root / "Makefile")}, "current build recipe")
    for variant, info in frozen["variants"].items():
        binary = Path(info["binary"])
        analysis.hash_check(binary, info["binary_sha256"])
        analysis.equal(info["binary_profile"], "main_stack_bytes", 536870912, "native stack")
        require("Mach-O 64-bit executable arm64" in info["binary_profile"]["file_description"], "wrong binary architecture")
        build = info["build"]
        analysis.hash_check(Path(build["path"]), build["sha256"])
        analysis.equal(build, "record", analysis.read_json(Path(build["path"])), "build provenance")
        checked = build_record(build["path"], variant, binary, frozen["source_sha256"], frozen["build_recipe_sha256"]["Makefile"])
        analysis.equal(info, "build", checked, "build provenance")
    require(frozen["variants"]["reference"]["binary_sha256"] != frozen["variants"]["multigraph"]["binary_sha256"],
            "identical variant binaries")
    check_build_pair(frozen["variants"])
    return frozen, cases


def child_paths(output, index, item):
    folder = output.with_name(output.stem + "_cases")
    name = f"{index:04d}_{item['variant']}_{item['case_id']}_g{item['graph_seed']}_s{item['kkt_seed']}"
    raw = folder / (name + ".csv")
    return raw, raw.with_suffix(".log"), raw.with_suffix(".rss.jsonl")


def tagged(rows, variant):
    return [{"variant": variant, **row} for row in rows]


def capture(args, sampler=None, popen=None):
    require(args.released, "capture requires explicit parent scheduling --released")
    freeze_path = args.freeze.resolve(strict=True)
    frozen, cases = check_freeze(freeze_path)
    freeze_hash = native.sha(freeze_path)
    output = args.output.resolve()
    sidecar = output.with_suffix(".json")
    folder = output.with_name(output.stem + "_cases")
    require(output.suffix == ".csv" and not any(p.exists() for p in (output, sidecar, folder)),
            "output must be a new .csv; refusing to overwrite raw evidence")
    sampler = sampler if sampler is not None else monitor.BoundedSampler(monitor.LibprocProvider())
    popen = popen if popen is not None else subprocess.Popen
    output.parent.mkdir(parents=True, exist_ok=True)
    folder.mkdir()
    info = {"schema": "multigraph_experiment_capture_v1", "validation": "running",
            "freeze": str(freeze_path), "freeze_sha256": freeze_hash,
            "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "output": str(output), "frozen_protocol": frozen,
            "started_utc": native.now(), "started_monotonic_ns": time.monotonic_ns(),
            "rows_removed": 0, "rows_adjusted": 0, "captures": [], "cleanup": [],
            "native_process_may_still_be_running": False}
    write_json(sidecar, info)
    rows, diagnostics = [], []
    old_handler = signal.getsignal(signal.SIGTERM)
    def interrupted(signum, frame):
        raise KeyboardInterrupt(f"capture received signal {signum}")
    signal.signal(signal.SIGTERM, interrupted)
    try:
        with output.open("x", newline="") as combined:
            writer = csv.DictWriter(combined, fieldnames=FIELDS)
            writer.writeheader(); combined.flush()
            for index, identity in enumerate(frozen["schedule"], 1):
                require(not sampler.poisoned, "sampler timeout forbids launching another native child")
                analysis.hash_check(freeze_path, freeze_hash)
                check_freeze(freeze_path)
                spec = cases[identity["case_id"]]
                variant = identity["variant"]
                argv = command(frozen["variants"][variant]["binary"], spec, identity)
                raw, log, rss = child_paths(output, index, identity)
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
                        while True:
                            observation = sampler.sample(process.pid)
                            observations.append(observation)
                            resource.write(json.dumps(observation, allow_nan=False) + "\n"); resource.flush()
                            require(not sampler.poisoned, "RSS sampler timed out; no subsequent native child permitted")
                            if observation["validation"] == "pass":
                                unavailable = 0
                                require(observation["rss_kib"] <= RULE["rss_limit_kib"], "sampled RSS exceeded ceiling")
                            else:
                                unavailable += 1
                                require(unavailable < 3, "three consecutive RSS observations unavailable")
                            try:
                                process.wait(timeout=RULE["poll_seconds"])
                                item["wrapper_exit_monotonic_ns"] = time.monotonic_ns()
                                break
                            except subprocess.TimeoutExpired:
                                pass
                        require(process.returncode == 0, "native child failed; no subsequent child permitted")
                        # Reaping /usr/bin/time alone does not establish that
                        # its owned group is empty. Bind a bounded, post-exit
                        # observation before permitting another native child.
                        observation = sampler.sample(process.pid)
                        observations.append(observation)
                        resource.write(json.dumps(observation, allow_nan=False) + "\n"); resource.flush()
                        item["group_exit_verification"] = observation
                        require(not sampler.poisoned and observation["validation"] == "pass" and
                                not observation["members"], "owned group exit is not verified; no next native child permitted")
                except BaseException as error:
                    failure = error
                    cleanup = monitor.bounded_terminate(process, sampler)
                    info["cleanup"].append(cleanup)
                    info["native_process_may_still_be_running"] |= cleanup["native_process_may_still_be_running"]
                item.update(exit_status=process.returncode if process else None,
                            interruption=repr(failure) if failure else None,
                            finished_utc=native.now(), finished_monotonic_ns=time.monotonic_ns(),
                            output_sha256=native.sha(raw), log_sha256=native.sha(log), rss_sha256=native.sha(rss),
                            rss_observations=len(observations),
                            rss_unavailable=sum(row["validation"] != "pass" for row in observations),
                            rss_nonempty_observations=sum(row["validation"] == "pass" and bool(row["members"]) for row in observations),
                            sampled_peak_rss_kib=max((row["rss_kib"] for row in observations if row["validation"] == "pass"), default=None),
                            recovery_monitor=monitor.recovery_monitor(sampler.events.get(process.pid, [])[:len(observations)] if process else []))
                item["monotonic_elapsed_seconds"] = (item["finished_monotonic_ns"] - item["started_monotonic_ns"]) / 1e9
                write_json(sidecar, info)
                if failure:
                    raise failure
                require(item["exit_status"] == 0, "native child failed; no subsequent child permitted")
                analysis.hash_check(freeze_path, freeze_hash); check_freeze(freeze_path)
                child_rows, child_diagnostics = native.check_rows(raw, spec, identity["graph_seed"],
                                                                 identity["kkt_seed"], REPETITIONS, WARMUPS)
                certificate = native.check_certificate(log, child_rows)
                native.check_fingerprints([*rows, *child_rows])
                item.update(validation="pass", rows=len(child_rows), certificate=certificate,
                            flagged_calls=sum(bool(row["diagnostic_flags"]) for row in child_diagnostics))
                analysis.check_rss(rss, item, RULE); monitor.validate_monitor(item)
                rows.extend(tagged(child_rows, variant)); diagnostics.extend(tagged(child_diagnostics, variant))
                writer.writerows(tagged(child_rows, variant)); combined.flush()
                write_json(sidecar, info)
        info.update(validation="pass", checked_rows=len(rows), checked_timed_rows=1000,
                    checked_warmup_rows=200, flagged_calls=sum(bool(row["diagnostic_flags"]) for row in diagnostics))
    except BaseException as error:
        info.update(validation="failed", error=repr(error))
        raise
    finally:
        signal.signal(signal.SIGTERM, old_handler)
        info.update(finished_utc=native.now(), finished_monotonic_ns=time.monotonic_ns(), call_diagnostics=diagnostics)
        info["monotonic_elapsed_seconds"] = (info["finished_monotonic_ns"] - info["started_monotonic_ns"]) / 1e9
        info["capture_clock_flags"] = native.capture_clock_flags(info)
        if output.exists():
            info["output_sha256"] = native.sha(output)
        write_json(sidecar, info)
    print("Validated 40 native children: 1000 timed outputs + 200 checked warmups")
    return info


def load(path):
    path = Path(path).resolve(strict=True)
    info = analysis.read_json(path)
    for field, expected in (("schema", "multigraph_experiment_capture_v1"), ("validation", "pass"),
                            ("rows_removed", 0), ("rows_adjusted", 0), ("cleanup", []),
                            ("native_process_may_still_be_running", False)):
        analysis.equal(info, field, expected, "capture")
    require("error" not in info, "failed capture cannot be summarized")
    freeze = Path(info["freeze"])
    analysis.hash_check(freeze, info["freeze_sha256"])
    frozen, cases = check_freeze(freeze)
    analysis.equal(info, "frozen_protocol", frozen, "capture freeze")
    output = Path(info["output"])
    require(output.with_suffix(".json") == path, "sidecar path differs from raw capture")
    analysis.hash_check(output, info["output_sha256"])
    analysis.timestamp(info["started_utc"]); analysis.timestamp(info["finished_utc"])
    begin, end = analysis.monotonic_interval(info)
    analysis.equal(info, "monotonic_elapsed_seconds", (end - begin) / 1e9, "capture duration")
    require(len(info["captures"]) == len(frozen["schedule"]), "incomplete child schedule")
    previous = begin
    rows, diagnostics, resources = [], [], []
    inputs = {str(path): native.sha(path), str(output): native.sha(output), str(freeze): native.sha(freeze)}
    for index, (expected, item) in enumerate(zip(frozen["schedule"], info["captures"]), 1):
        for field, value in {**expected, "exit_status": 0, "interruption": None, "validation": "pass", "rows": 30}.items():
            analysis.equal(item, field, value, f"child {index}")
        start, finish = analysis.monotonic_interval(item)
        require(previous <= start < finish <= end, "overlapping/invalid native child interval")
        previous = finish
        analysis.timestamp(item["started_utc"]); analysis.timestamp(item["finished_utc"])
        analysis.equal(item, "monotonic_elapsed_seconds", (finish - start) / 1e9, "child duration")
        raw, log, rss = child_paths(output, index, expected)
        for field, source, hash_field in (("csv", raw, "output_sha256"), ("log", log, "log_sha256"), ("rss_log", rss, "rss_sha256")):
            analysis.equal(item, field, str(source), "child path")
            analysis.hash_check(source, item[hash_field]); inputs[str(source)] = native.sha(source)
        argv = command(frozen["variants"][expected["variant"]]["binary"], cases[expected["case_id"]], expected)
        analysis.equal(item, "command", argv, "native argv")
        analysis.equal(item, "launch_command", ["/usr/bin/time", "-l", *argv], "launched argv")
        child_rows, child_diagnostics = native.check_rows(raw, cases[expected["case_id"]],
                                                         expected["graph_seed"], expected["kkt_seed"], REPETITIONS, WARMUPS)
        analysis.equal(item, "certificate", native.check_certificate(log, child_rows), "native certificate")
        analysis.equal(item, "flagged_calls", sum(bool(row["diagnostic_flags"]) for row in child_diagnostics), "child flags")
        observations = analysis.check_rss(rss, item, RULE)
        require(all(row["process_group"] == item["process_group"] for row in observations), "RSS group differs from launched child")
        analysis.equal(item, "group_exit_verification", observations[-1], "post-exit group observation")
        exit_time = item.get("wrapper_exit_monotonic_ns")
        require(type(exit_time) is int and start <= exit_time <= observations[-1]["monotonic_ns"] <= finish,
                "group verification is not after recorded wrapper exit")
        require(observations[-1]["validation"] == "pass" and not observations[-1]["members"],
                "successful child lacks verified empty owned group")
        monitor.validate_monitor(item)
        rows.extend(tagged(child_rows, expected["variant"])); diagnostics.extend(tagged(child_diagnostics, expected["variant"]))
        resources.append({**expected, **{key: item[key] for key in ("rss_observations", "rss_unavailable", "rss_nonempty_observations", "sampled_peak_rss_kib")},
                          **{key: item["recovery_monitor"][key] for key in ("max_sampler_duration_ns", "max_request_gap_ns")}})
    native.check_fingerprints(rows)
    actual = [row for _, row in native.base.read_csv(output, FIELDS)]
    require(actual == [{field: str(row[field]) for field in FIELDS} for row in rows], "combined CSV differs from exact raw child concatenation")
    analysis.equal(info, "call_diagnostics", diagnostics, "retained clock diagnostics")
    analysis.equal(info, "capture_clock_flags", native.capture_clock_flags(info), "capture flags")
    for field, expected in (("checked_rows", len(rows)), ("checked_timed_rows", 1000), ("checked_warmup_rows", 200),
                            ("flagged_calls", sum(bool(row["diagnostic_flags"]) for row in diagnostics))):
        analysis.equal(info, field, expected, "capture counts")
    return info, cases, rows, diagnostics, resources, inputs


def paired_variants(rows):
    groups = defaultdict(dict)
    for row in rows:
        if row["phase"] == "timed":
            key = tuple(row[field] for field in ("case_id", "graph_seed", "kkt_seed", "repetition", "algorithm"))
            require(row["variant"] not in groups[key], "duplicate variant call")
            groups[key][row["variant"]] = row
    pairs = []; by_case = defaultdict(lambda: defaultdict(list))
    for key, variants in groups.items():
        require(set(variants) == set(VARIANTS), "incomplete reference/candidate pair")
        reference, candidate = (variants[v] for v in VARIANTS)
        for field in (*analysis.IDENTITY, "graph_seed", "kkt_seed", "repetition", "algorithm", "input_fingerprint", "topology_fingerprint"):
            analysis.equal(candidate, field, reference[field], "paired variants")
        for metric, field in analysis.METRICS.items():
            ratio = candidate[field] / reference[field]
            pair = {**{f: reference[f] for f in analysis.IDENTITY}, "graph_seed": key[1], "kkt_seed": key[2],
                    "repetition": key[3], "algorithm": key[4], "metric": metric,
                    "reference_ns": reference[field], "multigraph_ns": candidate[field], "multigraph_over_reference": ratio}
            pairs.append(pair)
            by_case[(key[0], key[4], metric)][key[1]].append(ratio)
    graphs, summaries = [], []
    for (case, algorithm, metric), seeds in by_case.items():
        values = []; medians = []
        for graph, ratios in seeds.items():
            median = statistics.median(ratios); medians.append(median); values.extend(ratios)
            graphs.append({"case_id": case, "algorithm": algorithm, "metric": metric, "graph_seed": graph,
                           "median_paired_ratio": median, "trial_min_ratio": min(ratios), "trial_max_ratio": max(ratios),
                           "individual_wins": sum(r < 1 for r in ratios), "pairs": len(ratios)})
        summaries.append({"case_id": case, "algorithm": algorithm, "metric": metric,
                          "median_paired_ratio": statistics.median(values), "graph_min_ratio": min(medians),
                          "graph_max_ratio": max(medians), "trial_min_ratio": min(values), "trial_max_ratio": max(values),
                          "individual_wins": sum(r < 1 for r in values), "pairs": len(values)})
    return {"variant_pairs": pairs, "variant_graph_comparisons": graphs, "variant_comparisons": summaries}


def analyze(args):
    info, cases, rows, diagnostics, resources, inputs = load(args.capture)
    output = args.output_dir.resolve()
    require(not output.exists(), "refusing to overwrite analysis")
    output.mkdir(parents=True)
    tables = paired_variants(rows)
    for name, values in tables.items():
        analysis.write_csv(output / (name + ".csv"), values)
    for variant in VARIANTS:
        selected = [{key: value for key, value in row.items() if key != "variant"} for row in rows if row["variant"] == variant]
        variant_dir = output / variant; variant_dir.mkdir()
        for name, values in analysis.aggregate(selected).items():
            analysis.write_csv(variant_dir / (name + ".csv"), values)
    for name, values in (("validated_calls", rows), ("call_diagnostics", diagnostics), ("resources", resources)):
        analysis.write_csv(output / (name + ".csv"), values)
    power = {"status": "not_audited", "sleep_inhibition_verified": False}
    if args.power_log:
        source = args.power_log.resolve(strict=True)
        inputs[str(source)] = native.sha(source)
        events, malformed, reversals = corrected_power.parse_events(source.read_text(errors="replace"))
        intervals = corrected_power.original.sleep_intervals(events)
        correlated = corrected_power.original.correlate(rows, events, intervals)
        correlated = [{"variant": row["variant"], **result} for row, result in zip(rows, correlated)]
        analysis.write_csv(output / "call_power_associations.csv", correlated)
        power.update(status="archived_log_correlated", parser=corrected_power.PARSER,
                     source=str(source), source_sha256=inputs[str(source)],
                     logged_overlap_calls=sum(bool(row["nominal_logged_sleep_overlap_ns"]) for row in correlated),
                     unalignable_calls=sum(not row["utc_alignable"] for row in correlated),
                     malformed_event_lines=len(malformed), source_order_reversals=len(reversals),
                     limitation="External log provided; query success and retention coverage are not established here. No raw events or private log text copied into public analysis.")
    provenance = {"schema": "multigraph_experiment_analysis_v1", "validation": "pass", "checked_rows": len(rows),
                  "input_sha256": inputs, "capture": info, "power_audit": power,
                  "rows_removed": 0, "rows_adjusted": 0,
                  "ratio_summary": "Variant case summaries use the median of all ten paired trial ratios; graph summaries use each graph's five ratios. Per-variant comparisons against the four competitors retain original aggregation: median repetitions, then sampling seeds, then graph seeds. Graph/trial ranges are descriptive, not confidence intervals."}
    write_json(output / "provenance.json", provenance, exclusive=True)
    text = ["# Paired KKT multigraph-contraction screen", "",
            "All 1,200 native outputs passed exact MST validation: 1,000 timed calls and 200 retained warmups. "
            "This is a fresh two-graph-seed screen; it does not reuse historical timing samples.", "",
            "Ratios below one favor the multigraph build. Each pair shares graph, starting KKT seed and repetition. "
            "Variant case summaries take the median of all ten trial ratios; each graph has its own five-trial median. "
            "Ranges are not confidence intervals. Internal sampling "
            "trajectories can differ. Unchanged competitors are retained as controls, never used to normalize timings.", "",
            f"All {info['flagged_calls']} flagged calls and {len(info['capture_clock_flags'])} capture/child UTC flags remain included. "
            "Wall and process CPU clocks are separate. RSS is a periodic process-group sum, not a continuous peak. "
            f"Power audit status: `{power['status']}`; sleep inhibition is not asserted.", "",
            "| Case | Clock | Candidate KKT / reference KKT | Graph median range |", "|---|---|---:|---:|"]
    for row in tables["variant_comparisons"]:
        if row["algorithm"] == "kkt":
            text.append(f"| {row['case_id']} | {row['metric']} | {row['median_paired_ratio']:.4f} | {row['graph_min_ratio']:.4f}–{row['graph_max_ratio']:.4f} |")
    text += ["", "All five same-algorithm variant comparisons are in `variant_comparisons.csv`; "
             "the complete trial pairs are in `variant_pairs.csv`. Each variant's KKT versus all four MST "
             "competitors is retained in its `reference/` or `multigraph/` tables; these separately labeled tables "
             "keep the original median-over-repetitions, then sampling-seeds, then graph-seeds aggregation. No finite pilot establishes "
             "asymptotic dominance or justifies selecting only favorable families.", ""]
    (output / "README.md").write_text("\n".join(text))
    print(json.dumps({"validation": "pass", "checked_rows": len(rows), "analysis": str(output)}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    prepare = actions.add_parser("preflight")
    prepare.add_argument("--manifest", type=Path, required=True)
    prepare.add_argument("--protocol", type=Path, required=True)
    prepare.add_argument("--freeze", type=Path, required=True)
    for variant in VARIANTS:
        prepare.add_argument("--" + variant + "-binary", type=Path, required=True)
        prepare.add_argument("--" + variant + "-build-record", type=Path, required=True)
    run = actions.add_parser("capture")
    run.add_argument("--freeze", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--released", action="store_true")
    report = actions.add_parser("analyze")
    report.add_argument("--capture", type=Path, required=True)
    report.add_argument("--output-dir", type=Path, required=True)
    report.add_argument("--power-log", type=Path)
    args = parser.parse_args()
    {"preflight": preflight, "capture": capture, "analyze": analyze}[args.action](args)


if __name__ == "__main__":
    main()
