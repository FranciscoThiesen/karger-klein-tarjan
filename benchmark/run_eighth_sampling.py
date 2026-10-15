#!/usr/bin/env python3
"""Paired half/eighth sampling with compressed verifier queries fixed.

Requires reviewed correctness/build evidence and a prospectively frozen protocol.
Never launches performance children without --released. Parent helpers are
unchanged; local row/command validation never mutates their seed configuration.
"""
import argparse
from collections import defaultdict
import csv
from fractions import Fraction
import json
from pathlib import Path
import platform
import signal
import statistics
import subprocess
import time

import run_compressed_queries as parent_engine

control = parent_engine.control

native, analysis, monitor = control.native, control.analysis, control.monitor
power = control.power
require, write_json = control.require, control.write_json
HERE = Path(__file__).resolve()
PARENT_SHA256 = "bd65da13058d3e9cfa58919a0fe5e02b8a46b1d0b8fe7f05801692d5a0866df9"
VARIANTS = ("half", "eighth")
ALGORITHMS = control.ALGORITHMS
GRAPH_SEEDS = (15000011, 15000031)
SAMPLING_SEEDS = (2609, 2617)
REPETITIONS, WARMUPS = 6, 1
FIELDS = ["variant", *control.FIELDS]
RULE = control.RULE
CHANGED_NATIVE = {"kkt/kkt.cpp"}
NEW_NATIVE = {"kkt/experimental_eighth_sampling.hpp", "test/eighth_sampling_test.cpp", "test/eighth_sampling_integration_test.cpp"}
OVERLAY = {
    "kkt/kkt.cpp": "f5681b0384fb26ee6af5a23e4f7109b990393d831fc6ceb5385ce43643f5fd9a",
    "kkt/experimental_eighth_sampling.hpp": "dc58872c0f6c8542ce67d8c9f3a1c5c5c4fd9f2b1e5ae9c1bb65b5e6c70293bd",
    "test/eighth_sampling_test.cpp": "f7d4cb33d5359f15b525a8572d76bfde619df7fffd03712dc4bf84e69c7e5fae",
    "test/eighth_sampling_integration_test.cpp": "b323122c31b1a09f31915f4e246f3b57655337e358d06921c5f8c449bb79270a",
}
RECIPES = (*parent_engine.RECIPES, "benchmark/build_eighth_sampling.py")
SHARED_SOURCES = ("boruvka/boruvka.cpp", "kruskal/kruskal.cpp", "prim/prim.cpp", "lca/lca.cpp",
                  "union_find/union_find.cpp", "graph_utils/graph_utils.cpp", "verifier/verifier_v2.cpp")
FLAGS = control.previous.BASE_FLAGS + ["-DKKT_EXPERIMENT_RETAIN_PARALLEL", "-DKKT_EXPERIMENT_EDGE_VIEW"]
DECLARED_CASES = (("leaf_hierarchy4", 65536, 32, 0), ("leaf_shuffled4", 65536, 32, 0),
                  ("leaf_hierarchy4", 1048576, 32, 0), ("leaf_shuffled4", 1048576, 32, 0),
                  ("gnm_random", 4096, 16, 0), ("gnm_random", 1048576, 16, 0))
EXPECTED_CASES = set(DECLARED_CASES)
REFERENCE_NOTE = "Fresh predicate-refactored half sampling with compressed verifier queries; not the historical parent timing binary."
SEMANTICS = {
    **control.SEMANTICS,
    "campaign": "paired_eighth_sampling_v1",
    "schedule": "Graph seed then sampling seed then case then adjacent half/eighth children. Graph seed two reverses case order. Variant order reverses when graph-index plus sampler-index is odd. Six timed repetitions balance solver positions within every child.",
    "comparison": "Pair all six half/eighth solver durations by case, graph seed, sampling seed and repetition; compare KKT directly with all five controls within each variant. Case medians pool 24 paired ratios; four graph/sampler realization medians use six each; graph and sampler marginal medians use twelve each. Both clocks, all trials and losses remain included.",
    "purpose": "Test private scalar sampling with acceptance mask 7 instead of mask 1, with compressed verifier queries fixed in both fresh variants. The same compressed verifier object, six other non-KKT objects and harness object are shared. Only eighth kkt.o selects EIGHTH_SAMPLING; both variants contain the same pure-predicate refactor. Public sampling remains the legacy scalar half stream. Both policies draw once per edge and reserve m/2. Private samples and recursive work differ; identical cumulative counters across rates are neither expected nor required. No packed sampling, set-bit iteration, reserve change or historical timing pooling. Smaller samples can weaken filtering; no speedup is assumed.",
    "crossover": "For each variant/family/control, all four graph/sampler realization medians on both clocks must exceed one at the smaller endpoint and be at most 9/10 at the larger endpoint. Medians and thresholds are reconstructed as exact Fractions of integer endpoints. Keep all 30 classifications, including narrow leads, mixed outcomes and reversals. Two endpoints do not establish persistence beyond the measured larger size or an asymptotic crossover.",
}


def check_rows(path, spec, seed, sampling_seed):
    """Unchanged six-position/clock semantics with explicit study-local seeds."""
    require(seed in GRAPH_SEEDS and sampling_seed in SAMPLING_SEEDS, "unknown child seed")
    rows = []
    for context, raw in native.base.read_csv(path, control.FIELDS):
        row = dict(raw)
        for field in control.FIELDS:
            if field not in native.TEXT_FIELDS:
                row[field] = native.base.integer(raw[field], context + " " + field,
                                                native.MAX_NS if field.endswith("_ns") else native.base.UINT64_MAX)
        require(all(row[field] == value for field, value in spec.items()), context + ": fixture differs from manifest")
        require(row["graph_seed"] == seed and row["kkt_seed"] == sampling_seed and
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
        require(previous_cpu is None or row["process_cpu_start_ns"] >= previous_cpu,
                "process CPU clock reversed or overlapped")
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
        diagnostics.append({"case_id": spec["case_id"], "graph_seed": seed, "kkt_seed": sampling_seed,
                            **dict(zip(("phase", "repetition", "order", "algorithm"), identity)),
                            "elapsed_ns": steady, "process_cpu_elapsed_ns": cpu, "utc_elapsed_ns": utc,
                            "steady_minus_cpu_ns": steady - cpu, "utc_minus_steady_ns": utc - steady,
                            "diagnostic_flags": flags, "excluded": False})
    require(len({(row["input_fingerprint"], row["topology_fingerprint"]) for row in rows}) == 1,
            "solvers/phases received different fingerprints")
    return rows, diagnostics


def command(binary, spec, identity):
    require(identity["graph_seed"] in GRAPH_SEEDS and identity["kkt_seed"] in SAMPLING_SEEDS,
            "command seed differs from prospective declaration")
    return [str(binary), "--family", spec["family"], "--n", str(spec["n"]), "--density", str(spec["density"]),
            "--graph-seed", str(identity["graph_seed"]), "--kkt-seed", str(identity["kkt_seed"]),
            "--repetitions", str(REPETITIONS), "--warmups", str(WARMUPS)]


def helpers():
    return {**parent_engine.helpers(), str(HERE): native.sha(HERE)}


def parent_record(path):
    path = Path(path).resolve(strict=True)
    analysis.hash_check(path, PARENT_SHA256)
    parent = analysis.read_json(path)
    expected = parent["python_source_sha256"]
    current = parent_engine.helpers()
    old_names = {Path(name).name: digest for name, digest in expected.items()}
    new_names = {Path(name).name: digest for name, digest in current.items()}
    require(len(old_names) == len(expected) and len(new_names) == len(current) and old_names == new_names,
            "frozen compressed-query helper copies changed")
    for name, digest in expected.items(): analysis.hash_check(Path(name), digest)
    # Only path spelling changes between immutable helper copies. The parent's
    # full checker still reads all original sources, recipes, objects and binaries.
    previous = parent_engine.helpers
    try:
        parent_engine.helpers = lambda: expected
        checked, _ = parent_engine.check_freeze(path)
    finally:
        parent_engine.helpers = previous
    return checked


def source_inventory(root, parent):
    sources = native.source_inventory(root)
    require(set(sources) == set(parent["source_sha256"]) | NEW_NATIVE, "unexpected native source inventory")
    changed = {name for name, digest in parent["source_sha256"].items() if sources[name] != digest}
    require(changed == CHANGED_NATIVE, "native changes differ from declared eighth sampling experiment")
    require({name:sources[name] for name in OVERLAY} == OVERLAY, "declared eighth overlay source changed")
    return sources


def cases_from_manifest(path):
    cases = native.load_manifest(path)
    require(tuple(tuple(spec[field] for field in native.base.MANIFEST_FIELDS)
                  for spec in cases.values()) == DECLARED_CASES,
            "manifest differs from declared six eighth-sampling cases/order")
    return cases


def schedule(cases):
    return [{"variant": variant, "case_id": case, "graph_seed": graph, "kkt_seed": sampling}
            for gi, graph in enumerate(GRAPH_SEEDS)
            for si, sampling in enumerate(SAMPLING_SEEDS)
            for case in (list(cases) if gi == 0 else list(reversed(cases)))
            for variant in (VARIANTS if (gi + si) % 2 == 0 else tuple(reversed(VARIANTS)))]


def check_fingerprints(rows, complete=False):
    native.check_fingerprints(rows)
    controls = {}
    for row in rows:
        if row["family"] not in ("leaf_hierarchy4", "leaf_shuffled4"): continue
        key = row["n"], row["density"], row["graph_seed"]
        controls.setdefault(key, {})[row["family"]] = row["input_fingerprint"], row["topology_fingerprint"]
    for pair in controls.values():
        if len(pair) == 2:
            first, second = pair["leaf_hierarchy4"], pair["leaf_shuffled4"]
            require(first[1] == second[1], "matched weight controls have different topology/order")
            require(first[0] != second[0], "matched weight controls have identical weighted input")
    if complete:
        require(len(controls) == 4 and all(len(pair) == 2 for pair in controls.values()), "incomplete matched control matrix")


def expected_commands(root, sdk):
    """Reconstruct every timing compile and link; no arbitrary flags are accepted."""
    base = ["/usr/bin/arch", "-arm64", "/usr/bin/clang++", "-isysroot", sdk, *FLAGS, "-I."]
    build = root / ".build/eighth-sampling/timing-build"
    shared = {name.replace(".cpp", ".o"): str(build / "shared" / name.replace(".cpp", ".o")) for name in SHARED_SOURCES}
    objects = {variant: {**shared, "kkt/kkt.o": str(build / variant / "kkt/kkt.o")}
               for variant in VARIANTS}
    binaries = {variant: str(root / "bin/eighth-sampling/timing-build" / variant / "retention_control") for variant in VARIANTS}
    main = str(build / "shared/benchmark/retention_control.o")
    commands = [base + (["-DKKT_EXPERIMENT_COMPRESSED_QUERIES"] if name == "verifier/verifier_v2.cpp" else []) +
                ["-c", name, "-o", shared[name.replace(".cpp", ".o")]] for name in SHARED_SOURCES]
    for variant in VARIANTS:
        commands.append(base + (["-DKKT_EXPERIMENT_EIGHTH_SAMPLING"] if variant == "eighth" else []) +
                        ["-c", "kkt/kkt.cpp", "-o", objects[variant]["kkt/kkt.o"]])
    commands.append(base + ["-c", "benchmark/retention_control.cpp", "-o", main])
    links = {variant: base + list(objects[variant].values()) + [main, f"-L{sdk}/usr/lib", "-Wl,-stack_size,0x20000000", "-o", binaries[variant]] for variant in VARIANTS}
    commands.extend(links.values())
    return commands, objects, binaries, main, links


def build_record(path, binary, root, parent, parent_path, variant):
    path = Path(path).resolve(strict=True); record = analysis.read_json(path)
    sources = source_inventory(root, parent)
    recipes = {name: native.sha(root / name) for name in RECIPES}
    for name in parent_engine.RECIPES:
        require(recipes[name] == parent["build_recipe_sha256"][name], "parent recipe changed: " + name)
    for field, expected in (("schema", "eighth_sampling_build_v1"), ("profile", "timing-build"),
                            ("variant", variant), ("working_directory", str(root)),
                            ("binary", str(binary)), ("binary_sha256", native.sha(binary)),
                            ("source_sha256", sources), ("build_recipe_sha256", recipes), ("build_exit_status", 0),
                            ("parent_compressed_freeze", str(parent_path)), ("parent_compressed_freeze_sha256", PARENT_SHA256),
                            ("common_compile_flags", FLAGS),
                            ("role", "timing_never_executed"),
                            ("verifier_policy", "compressed"), ("source_overlay_sha256", OVERLAY),
                            ("seven_non_kkt_objects_identical_by_construction", True),
                            ("compressed_queries_fixed", True), ("public_scalar_sampling_fixed", True),
                            ("reference_note", REFERENCE_NOTE)):
        analysis.equal(record, field, expected, "timing build")
    predicate = {"sampling_policy": variant, "private_acceptance_mask": 1 if variant == "half" else 7,
                 "sampling_words_per_visited_edge": 1}
    for field, expected in predicate.items():
        require(type(record.get(field)) is type(expected) and record[field] == expected,
                "timing build predicate policy differs: " + field)
    inherited = parent["variants"]["compressed"]["build"]["record"]
    for field in ("compiler", "compiler_command", "sdk"):
        analysis.equal(record, field, inherited[field], "parent native toolchain")
    argv = record["build_command"]
    require(type(argv) is list and len(argv) == 9 and Path(argv[0]).name.startswith("python") and
            argv[1:] == ["-B", str(root / "benchmark/build_eighth_sampling.py"), "--profile", "timing-build", "--output", str(path.parent), "--parent-freeze", str(parent_path)],
            "unexpected build recipe invocation")
    commands, objects, binaries, main, links = expected_commands(root, record["sdk"])
    for field, expected in (("build_commands", commands), ("object_paths", objects[variant]),
                            ("binary", binaries[variant]), ("main_object", main), ("link_command", links[variant])):
        analysis.equal(record, field, expected, "exact compiler/link argv")
    executable = {"source": "benchmark/retention_control.cpp", **{field: record[field] for field in
        ("main_object", "main_object_sha256", "binary", "binary_sha256", "binary_profile", "link_command", "role", "verifier_policy",
         "sampling_policy", "private_acceptance_mask", "sampling_words_per_visited_edge")}}
    analysis.equal(record, "source", executable["source"], "timing harness source")
    analysis.equal(record, "executables", [executable], "exact timing executable inventory")
    for field, expected in predicate.items():
        require(type(record["executables"][0].get(field)) is type(expected) and
                record["executables"][0][field] == expected, "executable predicate policy differs: " + field)
    require(set(record["object_sha256"]) == set(objects[variant]), "incorrect eight production object inventory")
    for name, source in objects[variant].items(): analysis.hash_check(Path(source), record["object_sha256"][name])
    analysis.hash_check(Path(main), record["main_object_sha256"])
    analysis.hash_check(Path(record["build_log"]), record["build_log_sha256"])
    profile = record["binary_profile"]
    analysis.equal(profile, "main_stack_bytes", 536870912, "native stack")
    require(profile["file_description"] == "Mach-O 64-bit executable arm64", "wrong native architecture")
    return {"path": str(path), "sha256": native.sha(path), "record": record}


def check_pair(variants):
    first, second = (variants[name]["build"]["record"] for name in VARIANTS)
    for field in ("source_sha256", "build_recipe_sha256", "compiler", "compiler_command", "sdk",
                  "build_command", "build_commands", "main_object", "main_object_sha256"):
        analysis.equal(first, field, second[field], "same-source paired builds")
    for name in control.previous.OBJECTS - {"kkt/kkt.o"}:
        require(first["object_sha256"][name] == second["object_sha256"][name] and
                first["object_paths"][name] == second["object_paths"][name], "shared production object differs: " + name)
    require(first["object_sha256"]["kkt/kkt.o"] != second["object_sha256"]["kkt/kkt.o"], "KKT objects unexpectedly identical")
    require(first["binary_sha256"] != second["binary_sha256"], "paired binaries unexpectedly identical")


def preflight(args):
    root = Path.cwd().resolve(); parent_path = args.parent_freeze.resolve(strict=True)
    parent = parent_record(parent_path)
    manifest = args.manifest.resolve(strict=True); protocol = args.protocol.resolve(strict=True)
    require(manifest != Path(parent["manifest"]) and protocol != Path(parent["protocol"]), "new experiment requires its own declaration")
    cases = cases_from_manifest(manifest); variants = {}
    for variant in VARIANTS:
        binary = getattr(args, variant + "_binary").resolve(strict=True)
        build = build_record(getattr(args, variant + "_build_record"), binary, root, parent, parent_path, variant)
        profile = native.binary_profile(binary)
        analysis.equal(build["record"], "binary_profile", profile, "native binary profile")
        variants[variant] = {"binary": str(binary), "binary_sha256": native.sha(binary), "binary_profile": profile, "build": build}
    check_pair(variants)
    freeze = {"schema": "eighth_sampling_freeze_v1", "created_utc": native.now(),
              "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "working_directory": str(root), "platform": platform.platform(), "machine": platform.machine(),
              "parent_freeze": str(parent_path), "parent_freeze_sha256": PARENT_SHA256,
              "variants": variants, "source_sha256": source_inventory(root, parent), "python_source_sha256": helpers(),
              "build_recipe_sha256": {name: native.sha(root / name) for name in RECIPES},
              "manifest": str(manifest), "manifest_sha256": native.sha(manifest),
              "protocol": str(protocol), "protocol_sha256": native.sha(protocol),
              "algorithms": list(ALGORITHMS), "graph_seeds": list(GRAPH_SEEDS), "sampling_seeds": list(SAMPLING_SEEDS),
              "repetitions": REPETITIONS, "warmups": WARMUPS, "schedule": schedule(cases),
              "resource_rule": RULE, "semantics": SEMANTICS}
    args.freeze.parent.mkdir(parents=True, exist_ok=True); write_json(args.freeze, freeze, exclusive=True)
    print("Preflight passed; no native solver executed; frozen 48 children / 2016 outputs")


def check_freeze(path):
    frozen = analysis.read_json(Path(path))
    for field, expected in (("schema", "eighth_sampling_freeze_v1"), ("parent_freeze_sha256", PARENT_SHA256),
                            ("algorithms", list(ALGORITHMS)), ("graph_seeds", list(GRAPH_SEEDS)),
                            ("sampling_seeds", list(SAMPLING_SEEDS)), ("repetitions", REPETITIONS), ("warmups", WARMUPS),
                            ("resource_rule", RULE), ("semantics", SEMANTICS)):
        analysis.equal(frozen, field, expected, "frozen paired six-solver protocol")
    parent_path = Path(frozen["parent_freeze"]); parent = parent_record(parent_path)
    root = Path(frozen["working_directory"])
    for name in ("manifest", "protocol"):
        analysis.hash_check(Path(frozen[name]), frozen[name + "_sha256"])
    cases = cases_from_manifest(Path(frozen["manifest"]))
    analysis.equal(frozen, "schedule", schedule(cases), "frozen adjacent paired schedule")
    analysis.equal(frozen, "source_sha256", source_inventory(root, parent), "current source inventory")
    analysis.equal(frozen, "python_source_sha256", helpers(), "current helper inventory")
    analysis.equal(frozen, "build_recipe_sha256", {name: native.sha(root / name) for name in RECIPES}, "current build recipe")
    require(set(frozen["variants"]) == set(VARIANTS), "wrong variant inventory")
    for variant in VARIANTS:
        item = frozen["variants"][variant]; binary = Path(item["binary"])
        analysis.hash_check(binary, item["binary_sha256"])
        checked = build_record(item["build"]["path"], binary, root, parent, parent_path, variant)
        analysis.equal(item, "build", checked, "build provenance")
        analysis.equal(item, "binary_profile", checked["record"]["binary_profile"], "binary profile")
    check_pair(frozen["variants"])
    return frozen, cases


def child_paths(output, index, identity):
    raw = output.with_name(output.stem + "_cases") / f"{index:04d}_{identity['variant']}_{identity['case_id']}_g{identity['graph_seed']}_s{identity['kkt_seed']}.csv"
    return raw, raw.with_suffix(".log"), raw.with_suffix(".rss.jsonl")


def cleanup_owned_group(process, sampler, info):
    """Keep exit unknown until bounded cleanup supplies an empty-group proof."""
    prior_unknown = info["native_process_may_still_be_running"]
    info["native_process_may_still_be_running"] = True
    previous = signal.getsignal(signal.SIGTERM)
    receipt = {"process_group": process.pid if process else None,
               "started_monotonic_ns": time.monotonic_ns(), "native_exit_known": False,
               "group_exit_known": False, "native_process_may_still_be_running": True}
    try:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        try:
            receipt = monitor.bounded_terminate(process, sampler)
        except BaseException as error:
            receipt.update(error=repr(error), finished_monotonic_ns=time.monotonic_ns())
        finally:
            info["cleanup"].append(receipt)
            proved_empty = (receipt.get("native_exit_known") is True and
                            receipt.get("group_exit_known") is True and
                            receipt.get("native_process_may_still_be_running") is False)
            info["native_process_may_still_be_running"] = prior_unknown or not proved_empty
    finally:
        signal.signal(signal.SIGTERM, previous)
    return receipt


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
    info = {"schema": "eighth_sampling_capture_v1", "validation": "running", "freeze": str(freeze_path),
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
                argv = command(frozen["variants"][identity["variant"]]["binary"], spec, identity)
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
                    failure = error
                    cleanup_owned_group(process, sampler, info)
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
                child_rows, child_diagnostics = check_rows(raw, spec, identity["graph_seed"], identity["kkt_seed"])
                certificate = native.check_certificate(log, child_rows)
                check_fingerprints([*rows, *child_rows])
                item.update(validation="pass", rows=len(child_rows), certificate=certificate,
                            flagged_calls=sum(bool(row["diagnostic_flags"]) for row in child_diagnostics))
                analysis.check_rss(rss, item, RULE); monitor.validate_monitor(item)
                rows.extend({"variant": identity["variant"], **row} for row in child_rows)
                diagnostics.extend({"variant": identity["variant"], **row} for row in child_diagnostics)
                writer.writerows({"variant": identity["variant"], **row} for row in child_rows); combined.flush(); write_json(sidecar, info)
        check_fingerprints(rows, complete=True)
        require(len(rows) == 2016, "incomplete capture matrix")
        info.update(validation="pass", checked_rows=len(rows), checked_timed_rows=1728, checked_warmup_rows=288,
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
    print("Validated 48 native children: 1728 timed outputs + 288 checked warmups")
    return info


def load(path):
    path = Path(path).resolve(strict=True); info = analysis.read_json(path)
    for field, expected in (("schema", "eighth_sampling_capture_v1"), ("validation", "pass"), ("rows_removed", 0),
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
    require(len(info["captures"]) == 48, "incomplete native child schedule")
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
        argv = command(frozen["variants"][identity["variant"]]["binary"], cases[identity["case_id"]], identity)
        analysis.equal(item, "command", argv, "native argv")
        analysis.equal(item, "launch_command", ["/usr/bin/time", "-l", *argv], "launched argv")
        child_rows, child_diagnostics = check_rows(raw, cases[identity["case_id"]], identity["graph_seed"], identity["kkt_seed"])
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
        rows.extend({"variant": identity["variant"], **row} for row in child_rows)
        diagnostics.extend({"variant": identity["variant"], **row} for row in child_diagnostics)
        resources.append({**identity, **{key: item[key] for key in ("rss_observations", "rss_unavailable", "rss_nonempty_observations", "sampled_peak_rss_kib")},
                          **{key: item["recovery_monitor"][key] for key in ("max_sampler_duration_ns", "max_request_gap_ns")}})
    check_fingerprints(rows, complete=True)
    actual = [row for _, row in native.base.read_csv(output, FIELDS)]
    require(actual == [{field: str(row[field]) for field in FIELDS} for row in rows], "combined CSV differs from exact ordered child concatenation")
    analysis.equal(info, "call_diagnostics", diagnostics, "clock diagnostics")
    analysis.equal(info, "capture_clock_flags", native.capture_clock_flags(info), "capture flags")
    for field, value in (("checked_rows", 2016), ("checked_timed_rows", 1728), ("checked_warmup_rows", 288),
                         ("flagged_calls", sum(bool(row["diagnostic_flags"]) for row in diagnostics))):
        analysis.equal(info, field, value, "capture counts")
    return info, cases, rows, diagnostics, resources, inputs


def aggregate(rows):
    require({row['variant'] for row in rows} == set(VARIANTS), 'missing/unknown variant')
    blocks = defaultdict(dict); variant_blocks = defaultdict(dict); identities = {}
    tables = defaultdict(list)
    durations = defaultdict(lambda: defaultdict(list))
    within = defaultdict(lambda: defaultdict(list)); between = defaultdict(lambda: defaultdict(list))
    for row in rows:
        identities[row['case_id']] = {field: row[field] for field in analysis.IDENTITY}
        if row['phase'] != 'timed': continue
        case, graph, seed, rep, variant, algorithm = (row[field] for field in
            ('case_id', 'graph_seed', 'kkt_seed', 'repetition', 'variant', 'algorithm'))
        require(graph in GRAPH_SEEDS and seed in SAMPLING_SEEDS and rep in range(REPETITIONS), 'unknown realization/trial')
        block = blocks[(variant, case, graph, seed, rep)]
        require(algorithm not in block, 'duplicate algorithm in paired block'); block[algorithm] = row
        pair = variant_blocks[(case, graph, seed, rep, algorithm)]
        require(variant not in pair, 'duplicate variant in solver pair'); pair[variant] = row
        for metric, field in analysis.METRICS.items():
            durations[(variant, case, algorithm, metric)][(graph, seed)].append(row[field])
    for (variant, case, graph, seed, rep), block in blocks.items():
        require(set(block) == set(ALGORITHMS), 'incomplete six-algorithm paired block')
        for competitor in ALGORITHMS[1:]:
            for metric, field in analysis.METRICS.items():
                ratio = block['kkt'][field] / block[competitor][field]
                within[(variant, case, competitor, metric)][(graph, seed)].append(ratio)
                tables['paired_ratios'].append({'variant': variant, **identities[case], 'graph_seed': graph,
                    'kkt_seed': seed, 'repetition': rep, 'competitor': competitor, 'metric': metric,
                    'kkt_ns': block['kkt'][field], 'competitor_ns': block[competitor][field], 'kkt_over_competitor': ratio})
    for (case, graph, seed, rep, algorithm), block in variant_blocks.items():
        require(set(block) == set(VARIANTS), 'incomplete paired solver block')
        first, second = block['half'], block['eighth']
        for field in (*analysis.IDENTITY, 'input_fingerprint', 'topology_fingerprint'):
            require(first[field] == second[field], 'paired native input identity differs: ' + field)
        for metric, field in analysis.METRICS.items():
            ratio = second[field] / first[field]
            between[(case, algorithm, metric)][(graph, seed)].append(ratio)
            tables['variant_pairs'].append({**identities[case], 'graph_seed': graph, 'kkt_seed': seed,
                'repetition': rep, 'algorithm': algorithm, 'metric': metric, 'half_ns': first[field],
                'eighth_ns': second[field], 'eighth_over_half': ratio})

    def summarize(collection, name, identity_field, value_field, paired, variant_specific):
        for key, realizations in collection.items():
            variant, case, solver, metric = key if variant_specific else (None, *key)
            common = {**({'variant': variant} if variant_specific else {}), **identities[case], identity_field: solver, 'metric': metric}
            require(set(realizations) == {(graph, seed) for graph in GRAPH_SEEDS for seed in SAMPLING_SEEDS},
                    'missing graph/sampler realization')
            require(all(len(values) == REPETITIONS for values in realizations.values()), 'incomplete six-trial realization')
            def item(values, **extra):
                result = {**common, **extra, value_field: statistics.median(values),
                          'trial_min': min(values), 'trial_max': max(values), 'trials': len(values)}
                if paired: result['individual_wins'] = sum(value < 1 for value in values)
                return result
            for (graph, seed), values in realizations.items():
                tables['realization_' + name].append(item(values, graph_seed=graph, kkt_seed=seed))
            marginal_medians = {}
            for dimension, seeds, index, field in (('graph', GRAPH_SEEDS, 0, 'graph_seed'),
                                                   ('sampling', SAMPLING_SEEDS, 1, 'kkt_seed')):
                medians = []
                for seed in seeds:
                    values = [value for realization, group in realizations.items() if realization[index] == seed for value in group]
                    result = item(values, **{field: seed}); medians.append(result[value_field])
                    tables[dimension + '_' + name].append(result)
                marginal_medians[dimension + '_min'] = min(medians)
                marginal_medians[dimension + '_max'] = max(medians)
            all_values = [value for group in realizations.values() for value in group]
            medians = [statistics.median(group) for group in realizations.values()]
            tables[name].append(item(all_values, realization_min=min(medians), realization_max=max(medians), **marginal_medians))
    summarize(within, 'comparisons', 'competitor', 'median_paired_ratio', True, True)
    summarize(durations, 'summary', 'algorithm', 'median_ns', False, True)
    summarize(between, 'variant_comparisons', 'algorithm', 'median_paired_ratio', True, False)
    return dict(tables)


TABLE_COUNTS = {'paired_ratios': 2880, 'comparisons': 120, 'realization_comparisons': 480,
                'graph_comparisons': 240, 'sampling_comparisons': 240,
                'summary': 144, 'realization_summary': 576, 'graph_summary': 288, 'sampling_summary': 288,
                'variant_pairs': 1728, 'variant_comparisons': 72, 'realization_variant_comparisons': 288,
                'graph_variant_comparisons': 144, 'sampling_variant_comparisons': 144}


def crossovers(tables, cases):
    """Recompute thresholds from integer endpoints, never rounded summaries."""
    pairs = {}
    for row in tables['paired_ratios']:
        require(row['variant'] in VARIANTS and row['case_id'] in cases and
                row['competitor'] in ALGORITHMS[1:] and row['metric'] in analysis.METRICS and
                row['graph_seed'] in GRAPH_SEEDS and row['kkt_seed'] in SAMPLING_SEEDS and
                type(row['repetition']) is int and row['repetition'] in range(REPETITIONS),
                'unknown crossover trial identity')
        require(type(row['kkt_ns']) is int and type(row['competitor_ns']) is int and
                row['kkt_ns'] > 0 and row['competitor_ns'] > 0, 'invalid crossover integer endpoint')
        key = tuple(row[field] for field in ('variant','case_id','competitor','metric','graph_seed','kkt_seed'))
        group = pairs.setdefault(key,{})
        require(row['repetition'] not in group, 'duplicate crossover trial')
        group[row['repetition']] = Fraction(row['kkt_ns'],row['competitor_ns'])
    expected = {(variant,case,competitor,metric,graph,seed) for variant in VARIANTS for case in cases
                for competitor in ALGORITHMS[1:] for metric in analysis.METRICS
                for graph in GRAPH_SEEDS for seed in SAMPLING_SEEDS}
    require(set(pairs) == expected and all(set(group) == set(range(REPETITIONS)) for group in pairs.values()),
            'incomplete crossover realization/trial matrix')
    medians = {key:statistics.median(group.values()) for key,group in pairs.items()}
    groups = sorted({(case['family'], case['density']) for case in cases.values()})
    result = []
    for variant in VARIANTS:
        for family, density in groups:
            endpoints = sorted((case['n'],name) for name,case in cases.items()
                               if case['family'] == family and case['density'] == density)
            require(len(endpoints) == 2, 'crossover requires exactly two fixed endpoints')
            for competitor in ALGORITHMS[1:]:
                low, high = [[medians[(variant,case,competitor,metric,graph,seed)]
                              for metric in analysis.METRICS for graph in GRAPH_SEEDS for seed in SAMPLING_SEEDS]
                             for _,case in endpoints]
                def state(values):
                    if all(value <= Fraction(9,10) for value in values): return 'strong_lead'
                    if all(value < 1 for value in values): return 'narrow_lead'
                    if all(value > 1 for value in values): return 'loss'
                    return 'mixed_or_tied'
                item = {'variant': variant, 'family': family, 'density': density, 'competitor': competitor,
                    'small_n': endpoints[0][0], 'large_n': endpoints[1][0], 'small_state': state(low), 'large_state': state(high),
                    'strong_crossover': state(low) == 'loss' and state(high) == 'strong_lead'}
                for prefix,values in (('small',low),('large',high)):
                    for label,value in (('min',min(values)),('max',max(values))):
                        field = prefix + '_realization_clock_' + label
                        item.update({field:float(value),field+'_numerator':value.numerator,field+'_denominator':value.denominator})
                result.append(item)
    require(len(result) == 30, 'incomplete crossover classification matrix')
    return result

def analyze(args):
    info, cases, rows, diagnostics, resources, inputs = load(args.capture)
    output = args.output_dir.resolve(); require(not output.exists(), 'refusing to overwrite analysis')
    tables = aggregate(rows)
    require({name: len(values) for name, values in tables.items()} == TABLE_COUNTS, 'incomplete aggregate tables')
    tables['strong_crossover_classifications'] = crossovers(tables, cases)
    output.mkdir(parents=True)
    for name, values in {**tables, 'validated_calls': rows, 'call_diagnostics': diagnostics, 'resources': resources}.items():
        analysis.write_csv(output / (name + '.csv'), values)
    power_audit = {'status': 'not_audited', 'sleep_inhibition_verified': False}
    if args.power_log:
        source = args.power_log.resolve(strict=True); inputs[str(source)] = native.sha(source)
        events, malformed, reversals = power.parse_events(source.read_text(errors='replace'))
        associations = power.original.correlate(rows, events, power.original.sleep_intervals(events))
        require(len(associations) == len(rows), 'power association count differs')
        for row, association in zip(rows, associations): association['variant'] = row['variant']
        analysis.write_csv(output / 'call_power_associations.csv', associations)
        power_audit.update(status='archived_log_correlated', parser=power.PARSER, source=str(source), source_sha256=inputs[str(source)],
                           logged_overlap_calls=sum(bool(row['nominal_logged_sleep_overlap_ns']) for row in associations),
                           unalignable_calls=sum(not row['utc_alignable'] for row in associations),
                           malformed_event_lines=len(malformed), source_order_reversals=len(reversals),
                           limitation='External log provided; query success/retention coverage not established here. No raw private power events are copied into analysis.')
    for name, digest in inputs.items(): analysis.hash_check(Path(name), digest)
    write_json(output / 'provenance.json', {'schema': 'eighth_sampling_analysis_v1', 'validation': 'pass',
               'checked_rows': len(rows), 'capture': info, 'input_sha256': inputs, 'power_audit': power_audit,
               'rows_removed': 0, 'rows_adjusted': 0, 'aggregation': SEMANTICS['comparison']}, exclusive=True)
    text = ['# Eighth sampling with compressed verifier queries fixed', '',
            'All 2,016 solver outputs passed exact MST validation: 1,728 timed calls and 288 checked warmups. '
            'Every solver occupies every timed position once per child. Historical timings are not pooled.', '',
            SEMANTICS['purpose'], '', SEMANTICS['comparison'], '', SEMANTICS['crossover'], '',
            f"All {info['flagged_calls']} clock-flagged calls and {len(info['capture_clock_flags'])} UTC flags remain included. "
            'RSS is a sampled process-group sum, not a continuous peak. '
            f"Power audit: `{power_audit['status']}`. Verified sleep inhibition is not claimed.", '',
            '| Case | Clock | Eighth / half KKT | Realization median minimum | Realization median maximum |',
            '|---|---|---:|---:|---:|']
    for row in tables['variant_comparisons']:
        if row['algorithm'] != 'kkt': continue
        text.append(f"| {row['case_id']} | {row['metric']} | {row['median_paired_ratio']:.5f} | {row['realization_min']:.5f} | {row['realization_max']:.5f} |")
    text += ['', 'Ratios below one favor eighth sampling. Each variant’s direct KKT comparisons with all five solvers, '
             'absolute runtimes, every paired trial, all realization, graph and sampling marginal medians and diagnostics remain in the CSV tables. '
             'The variant_pairs, variant_comparisons and realization_variant_comparisons tables include all six algorithms '
             'so unchanged-solver drift is visible alongside KKT improvement. '
             'Realization/trial ranges are descriptive, not confidence intervals; finite measurements do not establish asymptotic dominance.', '']
    (output / 'README.md').write_text('\n'.join(text))
    print('Strict analysis passed: 2016 outputs, 1728 eighth/half all-solver ratios, 2880 within-variant comparator ratios')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest='action', required=True)
    prepare = actions.add_parser('preflight')
    for name in ('half-binary', 'eighth-binary', 'half-build-record', 'eighth-build-record', 'parent-freeze', 'manifest', 'protocol', 'freeze'):
        prepare.add_argument('--' + name, type=Path, required=True)
    run = actions.add_parser('capture')
    run.add_argument('--freeze', type=Path, required=True); run.add_argument('--output', type=Path, required=True)
    run.add_argument('--released', action='store_true')
    report = actions.add_parser('analyze')
    report.add_argument('--capture', type=Path, required=True); report.add_argument('--output-dir', type=Path, required=True)
    report.add_argument('--power-log', type=Path)
    args = parser.parse_args(); {'preflight': preflight, 'capture': capture, 'analyze': analyze}[args.action](args)


if __name__ == '__main__': main()
