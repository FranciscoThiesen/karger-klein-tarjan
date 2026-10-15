#!/usr/bin/env python3
"""Fresh paired tuple/Edge-view KKT experiment; never launches without --released.

The frozen six-solver row, certificate, clock and bounded-monitor helpers remain
unchanged. Only their seed configuration is temporarily scoped while validating
a child. This module owns the variant-aware schedule, provenance and analysis.
"""
import argparse
from collections import defaultdict
import contextlib
import csv
import json
from pathlib import Path
import platform
import signal
import statistics
import subprocess
import time

import run_retention_control as control

native, analysis, monitor = control.native, control.analysis, control.monitor
power = control.power
require, write_json = control.require, control.write_json
HERE = Path(__file__).resolve()
PARENT_SHA256 = "57459498d3a87d6b128ec7ca9cb89a5cda809350865b1c83208ad39f50b92359"
VARIANTS = ("tuple", "edge")
ALGORITHMS = control.ALGORITHMS
GRAPH_SEEDS = (4000037, 4000063)
SAMPLING_SEED, REPETITIONS, WARMUPS = 1013, 6, 1
FIELDS = ["variant", *control.FIELDS]
RULE = control.RULE
CHANGED_NATIVE = {"kkt/kkt.cpp", "verifier/verifier_v2.cpp", "verifier/verifier_v2.hpp"}
NEW_NATIVE = {"test/edge_verifier_view_test.cpp"}
RECIPES = (*control.RECIPES, "benchmark/build_edge_verifier.py")
SHARED_SOURCES = ("boruvka/boruvka.cpp", "kruskal/kruskal.cpp", "prim/prim.cpp", "lca/lca.cpp",
                  "union_find/union_find.cpp", "graph_utils/graph_utils.cpp", "verifier/verifier_v2.cpp")
FLAGS = control.previous.BASE_FLAGS + ["-DKKT_EXPERIMENT_RETAIN_PARALLEL"]
SEMANTICS = {
    **control.SEMANTICS,
    "campaign": "paired_edge_verifier_view_v1",
    "schedule": "Fresh graph seed then case then adjacent tuple/edge children; second graph seed reverses both case and variant order. Six timed repetitions balance every algorithm position in each child.",
    "comparison": "Edge/tuple ratios pair each of all six algorithms by graph seed, sampling seed and repetition across adjacent children, retaining unchanged-solver drift alongside KKT gain. Each variant also compares KKT directly against all five competitors in its own child. Case medians pool all twelve paired ratios; graph medians use six. Both clocks, all trials and losses remain included.",
    "purpose": "Remove the verifier input tuple materialization only. Both binaries use the refactored verifier, identical shared production objects and the unchanged six-solver driver; only kkt.o dispatches through the Edge-view macro. Historical control timings are not pooled or used as the refactored tuple baseline.",
}


@contextlib.contextmanager
def configured():
    """Seed overrides are restored after nesting or any exception; import is inert."""
    replacements = {"GRAPH_SEEDS": GRAPH_SEEDS, "SAMPLING_SEED": SAMPLING_SEED}
    before = {name: getattr(control, name) for name in replacements}
    try:
        for name, value in replacements.items(): setattr(control, name, value)
        yield
    finally:
        for name, value in before.items(): setattr(control, name, value)


def check_rows(path, spec, seed):
    with configured(): return control.check_rows(path, spec, seed)


def command(binary, spec, identity):
    with configured(): return control.command(binary, spec, identity)


def helpers():
    return {**control.helpers(), str(HERE): native.sha(HERE)}


def parent_record(path):
    path = Path(path).resolve(strict=True)
    analysis.hash_check(path, PARENT_SHA256)
    parent = analysis.read_json(path)
    analysis.equal(parent, "schema", "retention_control_freeze_v1", "parent control")
    old_helpers = {Path(name).name: digest for name, digest in parent["python_source_sha256"].items()}
    current = {Path(name).name: digest for name, digest in control.helpers().items()}
    require(len(old_helpers) == len(parent["python_source_sha256"]) and old_helpers == current,
            "frozen control helpers changed")
    for field in ("binary", "protocol", "manifest"):
        analysis.hash_check(Path(parent[field]), parent[field + "_sha256"])
    analysis.hash_check(Path(parent["build"]["path"]), parent["build"]["sha256"])
    analysis.equal(parent["build"], "record", analysis.read_json(Path(parent["build"]["path"])), "parent build")
    return parent


def source_inventory(root, parent):
    sources = native.source_inventory(root)
    require(set(sources) == set(parent["source_sha256"]) | NEW_NATIVE, "unexpected native source inventory")
    changed = {name for name, digest in parent["source_sha256"].items() if sources[name] != digest}
    require(changed == CHANGED_NATIVE, "native changes differ from declared verifier optimization")
    return sources


def cases_from_manifest(path):
    return control.cases_from_manifest(path)


def schedule(cases):
    return [{"variant": variant, "case_id": case, "graph_seed": seed, "kkt_seed": SAMPLING_SEED}
            for index, seed in enumerate(GRAPH_SEEDS)
            for case in (list(cases) if index == 0 else list(reversed(cases)))
            for variant in (VARIANTS if index == 0 else tuple(reversed(VARIANTS)))]


def expected_commands(root, sdk):
    """Reconstruct every timing compile and link; no arbitrary flags are accepted."""
    base = ["/usr/bin/arch", "-arm64", "/usr/bin/clang++", "-isysroot", sdk, *FLAGS, "-I."]
    build = root / ".build/edge-verifier/timing-build"
    shared = {name.replace(".cpp", ".o"): str(build / "shared" / name.replace(".cpp", ".o")) for name in SHARED_SOURCES}
    objects = {variant: {**shared, "kkt/kkt.o": str(build / variant / "kkt/kkt.o")}
               for variant in VARIANTS}
    binaries = {variant: str(root / "bin/edge-verifier/timing-build" / variant / "retention_control") for variant in VARIANTS}
    main = str(build / "shared/benchmark/retention_control.o")
    commands = [base + ["-c", name, "-o", shared[name.replace(".cpp", ".o")]] for name in SHARED_SOURCES]
    for variant in VARIANTS:
        commands.append(base + (["-DKKT_EXPERIMENT_EDGE_VIEW"] if variant == "edge" else []) +
                        ["-c", "kkt/kkt.cpp", "-o", objects[variant]["kkt/kkt.o"]])
    commands.append(base + ["-c", "benchmark/retention_control.cpp", "-o", main])
    links = {variant: base + list(objects[variant].values()) + [main, f"-L{sdk}/usr/lib", "-Wl,-stack_size,0x20000000", "-o", binaries[variant]] for variant in VARIANTS}
    commands.extend(links.values())
    return commands, objects, binaries, main, links


def build_record(path, binary, root, parent, parent_path, variant):
    path = Path(path).resolve(strict=True); record = analysis.read_json(path)
    sources = source_inventory(root, parent)
    recipes = {name: native.sha(root / name) for name in RECIPES}
    for name in control.RECIPES:
        require(recipes[name] == parent["build_recipe_sha256"][name], "parent recipe changed: " + name)
    for field, expected in (("schema", "edge_verifier_build_v1"), ("profile", "timing-build"),
                            ("variant", variant), ("working_directory", str(root)),
                            ("binary", str(binary)), ("binary_sha256", native.sha(binary)),
                            ("source_sha256", sources), ("build_recipe_sha256", recipes), ("build_exit_status", 0),
                            ("parent_control_freeze", str(parent_path)), ("parent_control_freeze_sha256", PARENT_SHA256),
                            ("common_compile_flags", FLAGS)):
        analysis.equal(record, field, expected, "timing build")
    inherited = parent["build"]["record"]
    for field in ("compiler", "compiler_command", "sdk"):
        analysis.equal(record, field, inherited[field], "parent native toolchain")
    argv = record["build_command"]
    require(type(argv) is list and len(argv) == 9 and Path(argv[0]).name.startswith("python") and
            argv[1:] == ["-B", str(root / "benchmark/build_edge_verifier.py"), "--profile", "timing-build", "--output", str(path.parent), "--parent-freeze", str(parent_path)],
            "unexpected build recipe invocation")
    commands, objects, binaries, main, links = expected_commands(root, record["sdk"])
    for field, expected in (("build_commands", commands), ("object_paths", objects[variant]),
                            ("binary", binaries[variant]), ("main_object", main), ("link_command", links[variant])):
        analysis.equal(record, field, expected, "exact compiler/link argv")
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
    freeze = {"schema": "edge_view_experiment_freeze_v1", "created_utc": native.now(),
              "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "working_directory": str(root), "platform": platform.platform(), "machine": platform.machine(),
              "parent_freeze": str(parent_path), "parent_freeze_sha256": PARENT_SHA256,
              "variants": variants, "source_sha256": source_inventory(root, parent), "python_source_sha256": helpers(),
              "build_recipe_sha256": {name: native.sha(root / name) for name in RECIPES},
              "manifest": str(manifest), "manifest_sha256": native.sha(manifest),
              "protocol": str(protocol), "protocol_sha256": native.sha(protocol),
              "algorithms": list(ALGORITHMS), "graph_seeds": list(GRAPH_SEEDS), "sampling_seeds": [SAMPLING_SEED],
              "repetitions": REPETITIONS, "warmups": WARMUPS, "schedule": schedule(cases),
              "resource_rule": RULE, "semantics": SEMANTICS}
    args.freeze.parent.mkdir(parents=True, exist_ok=True); write_json(args.freeze, freeze, exclusive=True)
    print("Preflight passed; no native solver executed; frozen 40 children / 1680 outputs")


def check_freeze(path):
    frozen = analysis.read_json(Path(path))
    for field, expected in (("schema", "edge_view_experiment_freeze_v1"), ("parent_freeze_sha256", PARENT_SHA256),
                            ("algorithms", list(ALGORITHMS)), ("graph_seeds", list(GRAPH_SEEDS)),
                            ("sampling_seeds", [SAMPLING_SEED]), ("repetitions", REPETITIONS), ("warmups", WARMUPS),
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
    raw = output.with_name(output.stem + "_cases") / f"{index:04d}_{identity['variant']}_{identity['case_id']}_g{identity['graph_seed']}_s{SAMPLING_SEED}.csv"
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
    info = {"schema": "edge_view_experiment_capture_v1", "validation": "running", "freeze": str(freeze_path),
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
                rows.extend({"variant": identity["variant"], **row} for row in child_rows)
                diagnostics.extend({"variant": identity["variant"], **row} for row in child_diagnostics)
                writer.writerows({"variant": identity["variant"], **row} for row in child_rows); combined.flush(); write_json(sidecar, info)
        info.update(validation="pass", checked_rows=len(rows), checked_timed_rows=1440, checked_warmup_rows=240,
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
    print("Validated 40 native children: 1440 timed outputs + 240 checked warmups")
    return info


def load(path):
    path = Path(path).resolve(strict=True); info = analysis.read_json(path)
    for field, expected in (("schema", "edge_view_experiment_capture_v1"), ("validation", "pass"), ("rows_removed", 0),
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
    require(len(info["captures"]) == 40, "incomplete native child schedule")
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
        rows.extend({"variant": identity["variant"], **row} for row in child_rows)
        diagnostics.extend({"variant": identity["variant"], **row} for row in child_diagnostics)
        resources.append({**identity, **{key: item[key] for key in ("rss_observations", "rss_unavailable", "rss_nonempty_observations", "sampled_peak_rss_kib")},
                          **{key: item["recovery_monitor"][key] for key in ("max_sampler_duration_ns", "max_request_gap_ns")}})
    native.check_fingerprints(rows)
    actual = [row for _, row in native.base.read_csv(output, FIELDS)]
    require(actual == [{field: str(row[field]) for field in FIELDS} for row in rows], "combined CSV differs from exact ordered child concatenation")
    analysis.equal(info, "call_diagnostics", diagnostics, "clock diagnostics")
    analysis.equal(info, "capture_clock_flags", native.capture_clock_flags(info), "capture flags")
    for field, value in (("checked_rows", 1680), ("checked_timed_rows", 1440), ("checked_warmup_rows", 240),
                         ("flagged_calls", sum(bool(row["diagnostic_flags"]) for row in diagnostics))):
        analysis.equal(info, field, value, "capture counts")
    return info, cases, rows, diagnostics, resources, inputs


def aggregate(rows):
    require({row['variant'] for row in rows} == set(VARIANTS), 'missing/unknown variant')
    tables = defaultdict(list)
    for variant in VARIANTS:
        selected = [row for row in rows if row['variant'] == variant]
        for name, values in control.aggregate(selected).items():
            tables[name].extend({'variant': variant, **row} for row in values)
    blocks = defaultdict(dict)
    for row in rows:
        if row['phase'] == 'timed':
            key = row['case_id'], row['graph_seed'], row['kkt_seed'], row['repetition'], row['algorithm']
            require(row['variant'] not in blocks[key], 'duplicate variant in solver pair')
            blocks[key][row['variant']] = row
    ratios = defaultdict(lambda: defaultdict(list)); identities = {}
    for (case, graph, seed, rep, algorithm), block in blocks.items():
        require(set(block) == set(VARIANTS), 'incomplete paired solver block')
        first, second = block['tuple'], block['edge']
        for field in (*analysis.IDENTITY, 'input_fingerprint', 'topology_fingerprint'):
            require(first[field] == second[field], 'paired native input identity differs: ' + field)
        identities[case] = {field: first[field] for field in analysis.IDENTITY}
        for metric, field in analysis.METRICS.items():
            ratio = second[field] / first[field]
            ratios[(case, algorithm, metric)][graph].append(ratio)
            tables['variant_pairs'].append({**identities[case], 'graph_seed': graph, 'kkt_seed': seed,
                'repetition': rep, 'algorithm': algorithm, 'metric': metric, 'tuple_ns': first[field],
                'edge_ns': second[field], 'edge_over_tuple': ratio})
    for (case, algorithm, metric), graphs in ratios.items():
        require(set(graphs) == set(GRAPH_SEEDS), 'missing graph seed in solver pair')
        all_values = []; medians = []
        for graph, values in graphs.items():
            require(len(values) == REPETITIONS, 'incomplete six-trial solver pair')
            median = statistics.median(values); medians.append(median); all_values.extend(values)
            tables['graph_variant_comparisons'].append({**identities[case], 'algorithm': algorithm, 'metric': metric, 'graph_seed': graph,
                'median_paired_ratio': median, 'trial_min': min(values), 'trial_max': max(values),
                'trials': len(values), 'individual_wins': sum(value < 1 for value in values)})
        tables['variant_comparisons'].append({**identities[case], 'algorithm': algorithm, 'metric': metric,
            'median_paired_ratio': statistics.median(all_values), 'graph_min': min(medians), 'graph_max': max(medians),
            'trial_min': min(all_values), 'trial_max': max(all_values), 'trials': len(all_values),
            'individual_wins': sum(value < 1 for value in all_values)})
    return dict(tables)


def analyze(args):
    info, cases, rows, diagnostics, resources, inputs = load(args.capture)
    output = args.output_dir.resolve(); require(not output.exists(), 'refusing to overwrite analysis')
    tables = aggregate(rows)
    counts = {'paired_ratios': 2400, 'comparisons': 200, 'graph_comparisons': 400,
              'summary': 240, 'graph_summary': 480, 'variant_pairs': 1440,
              'variant_comparisons': 120, 'graph_variant_comparisons': 240}
    require({name: len(values) for name, values in tables.items()} == counts, 'incomplete aggregate tables')
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
    write_json(output / 'provenance.json', {'schema': 'edge_view_experiment_analysis_v1', 'validation': 'pass',
               'checked_rows': len(rows), 'capture': info, 'input_sha256': inputs, 'power_audit': power_audit,
               'rows_removed': 0, 'rows_adjusted': 0, 'aggregation': SEMANTICS['comparison']}, exclusive=True)
    text = ['# Paired Edge-view verifier experiment', '',
            'All 1,680 solver outputs passed exact MST validation: 1,440 timed calls and 240 checked warmups. '
            'Every solver occupies every timed position once per child. Historical timings are not pooled.', '',
            SEMANTICS['purpose'], '', SEMANTICS['comparison'], '',
            f"All {info['flagged_calls']} clock-flagged calls and {len(info['capture_clock_flags'])} UTC flags remain included. "
            'RSS is a sampled process-group sum, not a continuous peak. '
            f"Power audit: `{power_audit['status']}`. Verified sleep inhibition is not claimed.", '',
            '| Case | Clock | Edge / tuple KKT | Graph median minimum | Graph median maximum |',
            '|---|---|---:|---:|---:|']
    for row in tables['variant_comparisons']:
        if row['algorithm'] != 'kkt': continue
        text.append(f"| {row['case_id']} | {row['metric']} | {row['median_paired_ratio']:.5f} | {row['graph_min']:.5f} | {row['graph_max']:.5f} |")
    text += ['', 'Ratios below one favor the Edge path. Each variant’s direct KKT comparisons with all five solvers, '
             'absolute runtimes, every paired trial, all graph medians and diagnostics remain in the CSV tables. '
             'The variant_pairs, variant_comparisons and graph_variant_comparisons tables include all six algorithms '
             'so unchanged-solver drift is visible alongside KKT improvement. '
             'Graph/trial ranges are descriptive, not confidence intervals; finite measurements do not establish asymptotic dominance.', '']
    (output / 'README.md').write_text('\n'.join(text))
    print('Strict analysis passed: 1680 outputs, 1440 Edge/tuple all-solver ratios, 2400 within-variant comparator ratios')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest='action', required=True)
    prepare = actions.add_parser('preflight')
    for name in ('tuple-binary', 'edge-binary', 'tuple-build-record', 'edge-build-record', 'parent-freeze', 'manifest', 'protocol', 'freeze'):
        prepare.add_argument('--' + name, type=Path, required=True)
    run = actions.add_parser('capture')
    run.add_argument('--freeze', type=Path, required=True); run.add_argument('--output', type=Path, required=True)
    run.add_argument('--released', action='store_true')
    report = actions.add_parser('analyze')
    report.add_argument('--capture', type=Path, required=True); report.add_argument('--output-dir', type=Path, required=True)
    report.add_argument('--power-log', type=Path)
    args = parser.parse_args(); {'preflight': preflight, 'capture': capture, 'analyze': analyze}[args.action](args)


if __name__ == '__main__': main()
