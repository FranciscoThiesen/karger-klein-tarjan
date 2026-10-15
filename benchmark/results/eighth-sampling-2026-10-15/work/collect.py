#!/usr/bin/env python3
"""Untimed fixed 48-child half/eighth sampling work matrix.

Reuse the unchanged three-solver diagnostic driver and bounded group monitor.
Neither process durations nor sampled RSS are algorithm performance measurements.
"""
import argparse
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
import run_eighth_sampling as timing

native, analysis, monitor = timing.native, timing.analysis, timing.monitor
require, write_json, RULE = timing.require, timing.write_json, timing.RULE
ALGORITHMS = ("kkt", "compacting_boruvka", "multigraph_boruvka")
FIELDS = re.findall(r'\{"(\w+)", &kkt_work::WorkStats::\w+, (?:true|false)\}',
                    (ROOT / "benchmark/work_metrics.hpp").read_text())
DEADLINE_SECONDS = 1800
SOURCE = "benchmark/results/retention-control-2026-10-15/work/driver.cpp"
SOURCE_SHA256 = "ae08c5d199d83668d81f41a573452fea099c7e7cd5bd9bb4807c4a8ba9120e25"
BOUNDARY = "Includes tuple-to-Edge input construction, solver, and temporary input destruction; certification and round replay are outside WorkStats."
TESTS = ("test/compressed_query_test.cpp", "test/edge_verifier_view_test.cpp",
         "test/multigraph_contraction_test.cpp", "test/regression_test.cpp",
         "test/contraction_test.cpp", "test/simple_test.cpp", "benchmark/core_attachment_test.cpp",
         "benchmark/certificate_test.cpp", "test/eighth_sampling_test.cpp",
         "test/eighth_sampling_integration_test.cpp")


def instrumented_layout(root, sdk):
    """Independent complete recipe: seven shared objects, two KKT objects, eleven targets."""
    base = ["/usr/bin/arch", "-arm64", "/usr/bin/clang++", "-isysroot", sdk,
            *timing.FLAGS, "-DKKT_ENABLE_WORK_STATS", "-I."]
    build = root / ".build/eighth-sampling/native-correctness"
    shared = {source.replace(".cpp", ".o"): str(build / "shared" / source.replace(".cpp", ".o"))
              for source in timing.SHARED_SOURCES}
    objects = {variant: {**shared, "kkt/kkt.o": str(build / variant / "kkt/kkt.o")}
               for variant in timing.VARIANTS}
    commands = [base + (["-DKKT_EXPERIMENT_COMPRESSED_QUERIES"] if source == "verifier/verifier_v2.cpp" else []) +
                ["-c", source, "-o", shared[source.replace(".cpp", ".o")]] for source in timing.SHARED_SOURCES]
    for variant in timing.VARIANTS:
        extra = ["-DKKT_EXPERIMENT_EIGHTH_SAMPLING"] if variant == "eighth" else []
        commands.append(base + extra + ["-c", "kkt/kkt.cpp", "-o", objects[variant]["kkt/kkt.o"]])
    executables = {variant: [] for variant in timing.VARIANTS}
    for source in (*TESTS, SOURCE):
        integration = source == "test/eighth_sampling_integration_test.cpp"
        main = str(build / "shared" / source.replace(".cpp", ".o"))
        if not integration: commands.append(base + ["-c", source, "-o", main])
        for variant in timing.VARIANTS:
            if integration:
                main = str(build / variant / source.replace(".cpp", ".o"))
                extra = ["-DKKT_EXPERIMENT_EIGHTH_SAMPLING"] if variant == "eighth" else []
                commands.append(base + extra + ["-c", source, "-o", main])
            name = "retention_work" if source == SOURCE else Path(source).stem
            binary = str(root / "bin/eighth-sampling/native-correctness" / variant / name)
            selected = shared if integration else objects[variant]
            link = base + list(selected.values()) + [main, f"-L{sdk}/usr/lib", "-Wl,-stack_size,0x20000000", "-o", binary]
            commands.append(link)
            executables[variant].append(dict(source=source, main_object=main, binary=binary, link_command=link,
                sampling_policy=variant, private_acceptance_mask=7 if variant == "eighth" else 1,
                sampling_words_per_visited_edge=1, verifier_policy="compressed",
                role="untimed_work_never_executed" if source == SOURCE else "correctness"))
    require(len(commands) == 43, "unexpected instrumented command count")
    return commands, objects, executables


def check_instrumented_recipe(build, root):
    commands, objects, targets = instrumented_layout(root, build["sdk"])
    analysis.equal(build, "build_commands", commands,
                   "complete instrumented compile/link sequence")
    variant = build["variant"]
    require(variant in timing.VARIANTS, "unknown instrumented variant")
    analysis.equal(build, "object_paths", objects[variant], "exact production objects")
    require(set(build["object_sha256"]) == set(objects[variant]), "incorrect object hash inventory")
    require(len(build["executables"]) == 11, "incorrect instrumented target count")
    for actual, expected in zip(build["executables"], targets[variant]):
        require(set(actual) == set(expected) | {"main_object_sha256", "binary_sha256", "binary_profile"},
                "incorrect instrumented target schema")
        for field, value in expected.items():
            require(type(actual[field]) is type(value), "incorrect target metadata type")
            analysis.equal(actual, field, value, "exact instrumented target")
        profile = actual["binary_profile"]
        require(profile["file_description"] == "Mach-O 64-bit executable arm64" and
                type(profile["main_stack_bytes"]) is int and profile["main_stack_bytes"] == 536870912,
                "invalid native diagnostic profile")
    return build["executables"][-1]


def provenance(timing_capture):
    info, cases, rows, _, _, paths = timing.load(timing_capture)
    require(len(FIELDS) == len(set(FIELDS)) == 65, "unexpected work counter schema")
    frozen = info["frozen_protocol"]
    current_sources = native.source_inventory(ROOT)
    require(current_sources == frozen["source_sha256"], "timing and diagnostic native sources differ")
    paths = merge_paths(paths, timing.helpers(), {str(HERE): native.sha(HERE),
        str(WORK / "PROTOCOL.md"): native.sha(WORK / "PROTOCOL.md"), str(ROOT / SOURCE): SOURCE_SHA256,
        **{str(ROOT / name): digest for name, digest in current_sources.items()}})
    # Pin the independently completed correctness/readiness review and every input
    # it checked. Do not rerun native tests during work preparation or strict load.
    review_path = WORK.parent / "validation/independent-readiness-attempt01.stdout"
    review_sha = native.sha(review_path); review = analysis.read_json(review_path)
    for field, expected in dict(schema="eighth_independent_readiness_v1", validation="pass",
            review_native_execution=False, parent_freeze_sha256=timing.PARENT_SHA256,
            seven_non_kkt_objects_and_timing_main_shared=True).items():
        analysis.equal(review, field, expected, "independent native readiness")
    for profile in ("native-correctness", "sanitizer-correctness"):
        coverage = review["coverage"][profile]
        for field, expected in dict(positive=20, negative=4, records=1344, counter_fields=65,
                                    half_parent_replay="exact").items():
            analysis.equal(coverage, field, expected, "completed native correctness")
        require(type(coverage["changed_recursive_work_pairs"]) is int and
                0 < coverage["changed_recursive_work_pairs"] <= 1344, "missing changed-rate witness")
    analysis.equal(review, "final_object_coverage", dict(positive=4, negative=2, byte_identical_rebuilds=2),
                   "actual final-object correctness")
    analysis.equal(review, "timing_binary_sha256", {v: frozen["variants"][v]["binary_sha256"] for v in timing.VARIANTS},
                   "readiness timing artifacts")
    paths = merge_paths(paths, review["input_sha256"], {str(review_path): review_sha})
    variants, builds = {}, {}
    for variant in timing.VARIANTS:
        build_path = WORK.parent / "validation" / ("native-correctness-" + variant + "-build-record.json")
        build_sha = native.sha(build_path); build = analysis.read_json(build_path); builds[variant] = build
        paths = merge_paths(paths, {str(build_path): build_sha})
        inherited = frozen["variants"][variant]["build"]["record"]
        for key, value in dict(schema="eighth_sampling_build_v1", profile="native-correctness", variant=variant,
                working_directory=str(ROOT), source_sha256=current_sources, build_exit_status=0,
                common_compile_flags=[*timing.FLAGS, "-DKKT_ENABLE_WORK_STATS"],
                seven_non_kkt_objects_identical_by_construction=True, compressed_queries_fixed=True,
                public_scalar_sampling_fixed=True, reference_note=timing.REFERENCE_NOTE,
                source_overlay_sha256=timing.OVERLAY, work_driver=str(ROOT / SOURCE), work_driver_sha256=SOURCE_SHA256,
                sampling_policy=variant, private_acceptance_mask=7 if variant == "eighth" else 1,
                sampling_words_per_visited_edge=1).items():
            require(type(build.get(key)) is type(value), "incorrect build metadata type")
            analysis.equal(build, key, value, "instrumented build")
        for key in ("compiler", "compiler_command", "sdk", "build_recipe_sha256",
                    "parent_compressed_freeze", "parent_compressed_freeze_sha256"):
            analysis.equal(build, key, inherited[key], "same production source/toolchain")
        expected_build = [inherited["build_command"][0], "-B", str(ROOT / "benchmark/build_eighth_sampling.py"),
                          "--profile", "native-correctness", "--output", str(build_path.parent),
                          "--parent-freeze", build["parent_compressed_freeze"]]
        analysis.equal(build, "build_command", expected_build, "exact diagnostic build invocation")
        analysis.equal(build, "build_log", str(build_path.parent / "native-correctness-build.log"), "build log path")
        executable = check_instrumented_recipe(build, ROOT)
        paths = merge_paths(paths, {str(ROOT / name): digest for name, digest in build["build_recipe_sha256"].items()},
            {build["build_log"]: build["build_log_sha256"]},
            {path: build["object_sha256"][name] for name, path in build["object_paths"].items()},
            {target[field]: target[field + "_sha256"] for target in build["executables"] for field in ("main_object", "binary")})
        variants[variant] = {**executable, "instrumented_build_record": str(build_path),
            "instrumented_build_record_sha256": build_sha,
            "object_paths": build["object_paths"], "object_sha256": build["object_sha256"]}
    require(list(variants) == list(timing.VARIANTS), "incomplete/reordered variant proof")
    first, second = (builds[variant] for variant in timing.VARIANTS)
    require(first["build_log_sha256"] == second["build_log_sha256"], "shared build log digest differs")
    for name in timing.control.previous.OBJECTS - {"kkt/kkt.o"}:
        for key in ("object_paths", "object_sha256"):
            require(first[key][name] == second[key][name], "non-KKT diagnostic object differs")
    require(first["object_sha256"]["kkt/kkt.o"] != second["object_sha256"]["kkt/kkt.o"],
            "instrumented KKT variants unexpectedly identical")
    for left, right in zip(first["executables"], second["executables"]):
        if left["source"] != "test/eighth_sampling_integration_test.cpp":
            require((left["main_object"], left["main_object_sha256"]) ==
                    (right["main_object"], right["main_object_sha256"]), "nonintegration main not shared")
    fingerprints = {}
    for row in rows:
        key = tuple(row[k] for k in ("variant", "case_id", "graph_seed", "kkt_seed"))
        value = {k: row[k] for k in ("input_fingerprint", "topology_fingerprint")}
        require(key not in fingerprints or fingerprints[key] == value, "timing graph identity varies")
        fingerprints[key] = value
    schedule = [{**identity, **cases[identity["case_id"]], **fingerprints[tuple(identity[k] for k in
                 ("variant", "case_id", "graph_seed", "kkt_seed"))]} for identity in timing.schedule(cases)]
    require(len(schedule) == len(fingerprints) == 48, "incomplete prospective work matrix")
    for path, digest in paths.items(): analysis.hash_check(Path(path), digest)
    return variants, schedule, paths


def merge_paths(*inventories):
    result = {}
    for inventory in inventories:
        for path, digest in inventory.items():
            require(path not in result or result[path] == digest, "conflicting provenance hash: " + path)
            result[path] = digest
    return result


def prepare(args):
    variants, schedule, paths = provenance(args.timing_capture.resolve(strict=True))
    data = dict(schema="eighth_sampling_work_freeze_v1", timing_capture=str(args.timing_capture.resolve()),
                variants=variants, schedule=schedule, bound_sha256=paths, counter_fields=FIELDS,
                counter_boundary=BOUNDARY, resource_rule=RULE, child_deadline_seconds=DEADLINE_SECONDS,
                expected_children=48, expected_solver_outputs=144, created_utc=native.now())
    write_json(args.freeze, data, exclusive=True)
    print("Prepared fixed 48-child / 144-output untimed matrix; no native execution")


def check_freeze(path):
    data = analysis.read_json(path)
    variants, schedule, paths = provenance(Path(data["timing_capture"]))
    for key, value in dict(schema="eighth_sampling_work_freeze_v1", variants=variants, schedule=schedule,
                           bound_sha256=paths, counter_fields=FIELDS, counter_boundary=BOUNDARY,
                           resource_rule=RULE, child_deadline_seconds=DEADLINE_SECONDS,
                           expected_children=48, expected_solver_outputs=144).items():
        analysis.equal(data, key, value, "prospective work freeze")
    return data


def command(binary, spec):
    return ["/usr/bin/arch", "-arm64", binary, spec["family"],
            *[str(spec[k]) for k in ("n", "density", "graph_seed", "kkt_seed")]]


def check_output(path, spec):
    value = analysis.read_json(path)
    require(type(spec["intrusion_per_mille"]) is int and spec["intrusion_per_mille"] == 0,
            "diagnostic driver supports only zero intrusion")
    expected_output = {"schema": "retention_control_work_v1", "validation": "pass",
                          "certified_output_items": spec["n"] - 1,
                          **{k: v for k, v in spec.items() if k not in ("variant", "intrusion_per_mille")}}
    require(set(value) == set(expected_output) | {"algorithms", "rounds"}, "incorrect diagnostic output schema")
    for key, expected in expected_output.items():
        require(type(value[key]) is type(expected), "incorrect diagnostic identity type")
        analysis.equal(value, key, expected, "diagnostic output")
    require(set(value["algorithms"]) == set(ALGORITHMS), "incorrect solver set")
    require(set(value["rounds"]) == set(ALGORITHMS[1:]), "incorrect replay set")
    for name, data in value["algorithms"].items():
        require(set(data) == {"work", "hash_insert_items_status"}, "incorrect algorithm record schema")
        work = data["work"]
        require(set(work) == set(FIELDS), "counter schema changed")
        for key, count in work.items():
            if name != "kkt" and key == "hash_insert_items": require(count is None, "unmeasured hash count invented")
            else: require(type(count) is int and 0 <= count < 2**64, "invalid counter type/value")
        analysis.equal(data, "hash_insert_items_status", "measured" if name == "kkt" else "unmeasured", "hash scope")
        analysis.equal(work, "current_depth", 0, "unwound recursion")
        require(work["contraction_edge_visits"] <= (4 if name == "compacting_boruvka" else 3) * work["contraction_edges"], "contraction scan bound")
        if name == "kkt":
            analysis.equal(work, "hash_insert_items", spec["n"] - 1, "certified unique output size")
            require(work["sampling_calls"] == work["verifier_calls"] and
                    work["sampling_edge_visits"] == work["verifier_edges"] and
                    work["sampled_edges"] <= work["sampling_edge_visits"], "invalid sample/verifier work")
            require(work["sampling_calls"] > 0 or work["sampling_edge_visits"] == 0, "sample volume without call")
            query_diagnostics(work)
            continue
        require(all(work[k] == 0 for k in ("kkt_calls", "verifier_calls", "sampling_calls")), "comparator invoked KKT")
        rounds = value["rounds"][name]
        require(len(rounds) == work["contraction_calls"], "round count differs")
        n, m, selected = spec["n"], spec["m"], 0
        for index, row in enumerate(rounds):
            require(set(row) == {"round", "vertices", "edges", "selected", "output_vertices", "output_edges"}
                    and all(type(v) is int and 0 <= v < 2**64 for v in row.values()), "invalid replay row")
            require((row["round"], row["vertices"], row["edges"]) == (index, n, m), "broken replay chain")
            require(row["output_vertices"] <= n // 2 and row["output_edges"] <= m, "replay did not shrink")
            require((row["output_edges"] == 0) == (row["output_vertices"] == 0), "invalid terminal replay graph")
            remaining = row["output_vertices"] if row["output_edges"] else 1
            require(row["selected"] == row["vertices"] - remaining, "selected edges differ from connected contraction")
            n, m = row["output_vertices"], row["output_edges"]
            selected += row["selected"]
        require(m == 0 and selected == spec["n"] - 1, "replay not spanning")
        for field, counter in (("vertices", "contraction_vertices"), ("edges", "contraction_edges"),
                               ("output_vertices", "contraction_output_vertices"), ("output_edges", "contraction_output_edges")):
            analysis.equal(work, counter, sum(row[field] for row in rounds), "replay aggregate")
    retained = value["rounds"]["multigraph_boruvka"]
    if len(retained) >= 2:
        for field in ("vertices", "edges"):
            analysis.equal(value["algorithms"]["kkt"]["work"], "root_after_two_" + field,
                           retained[1]["output_" + field], "common first two contractions")
    else:
        require(value["algorithms"]["kkt"]["work"]["root_after_two_vertices"] == 0 and
                value["algorithms"]["kkt"]["work"]["root_after_two_edges"] == 0, "early root exit dimensions differ")
    return value


def check_comparators(spec, value, seen):
    key = spec["case_id"], spec["graph_seed"]
    signature = {"algorithms": {k: value["algorithms"][k] for k in ALGORITHMS[1:]}, "rounds": value["rounds"]}
    require(key not in seen or seen[key] == signature, "unchanged comparator work/replay varies with sampler or variant")
    seen[key] = signature


def query_diagnostics(work):
    q, m, t, n = (work[field] for field in ("verifier_queries", "verifier_tree_edges", "verifier_tree_calls", "fbt_output_vertices"))
    u = work["path_query_visits"] - 2*q
    require(0 <= u <= q, "compressed cumulative U outside [0,Q]")
    return dict(Q=q, U=u, M=m, T=t, Nsum=n, U_over_Q=u/q if q else None,
                query_fraction_status="defined" if q else "both_zero", collapsed_requests=q-u,
                sampling_calls=work["sampling_calls"], sampling_edge_visits=work["sampling_edge_visits"],
                engine_words=work["sampling_edge_visits"], engine_word_method="exact_scalar_one_draw_per_visited_edge")


def complete(values):
    require(len(values) == 48 and len({tuple(spec[k] for k in ("variant", "case_id", "graph_seed", "kkt_seed"))
                                    for spec, value in values}) == 48, "incomplete/duplicate diagnostic inputs")
    timing.check_fingerprints([{**value, "variant": spec["variant"]} for spec, value in values], complete=True)
    require(any(query_diagnostics(value["algorithms"]["kkt"]["work"])["Q"] > 0 for spec, value in values),
            "no positive compressed-query input in full matrix")


def resources(item):
    observations = analysis.check_rss(Path(item["rss_log"]), item, RULE)
    require(all(r["process_group"] == item["process_group"] for r in observations), "wrong owned group")
    analysis.equal(item, "group_exit_verification", observations[-1], "post-exit observation")
    require(type(item["wrapper_exit_monotonic_ns"]) is int and
            item["wrapper_exit_monotonic_ns"] - item["started_monotonic_ns"] <= DEADLINE_SECONDS * 10**9,
            "diagnostic native exit exceeded deadline")
    require(item["started_monotonic_ns"] <= item["wrapper_exit_monotonic_ns"] <= observations[-1]["monotonic_ns"] <= item["finished_monotonic_ns"]
            and observations[-1]["validation"] == "pass" and not observations[-1]["members"], "group exit unknown")
    monitor.validate_monitor(item)


def child_paths(output, index, spec):
    stem = f"{index:04d}_{spec['variant']}_{spec['case_id']}_g{spec['graph_seed']}_s{spec['kkt_seed']}"
    folder = output.with_name(output.stem + "_cases")
    return tuple(folder / (stem + suffix) for suffix in (".json", ".log", ".rss.jsonl"))


def cleanup_owned_group(process, sampler, info):
    prior_unknown = info["native_process_may_still_be_running"]
    info["native_process_may_still_be_running"] = True
    prior_handler = signal.getsignal(signal.SIGTERM)
    receipt = dict(process_group=process.pid if process else None, started_monotonic_ns=time.monotonic_ns(),
                   native_exit_known=False, group_exit_known=False, native_process_may_still_be_running=True)
    try:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        try: receipt = monitor.bounded_terminate(process, sampler)
        except BaseException as error: receipt.update(error=repr(error), finished_monotonic_ns=time.monotonic_ns())
        finally:
            info["cleanup"].append(receipt)
            proved_empty = receipt.get("native_exit_known") is True and receipt.get("group_exit_known") is True and receipt.get("native_process_may_still_be_running") is False
            info["native_process_may_still_be_running"] = prior_unknown or not proved_empty
    finally: signal.signal(signal.SIGTERM, prior_handler)
    return receipt


def capture(args, sampler=None, popen=None):
    require(args.released, "work capture requires explicit root --released scheduling")
    freeze_path = args.freeze.resolve(strict=True)
    frozen = check_freeze(freeze_path)
    paths = merge_paths(frozen["bound_sha256"], {str(freeze_path): native.sha(freeze_path)})
    output = args.output.resolve()
    folder = output.with_name(output.stem + "_cases")
    require(output.suffix == ".json" and not output.exists() and not folder.exists(), "refusing to overwrite evidence")
    output.parent.mkdir(parents=True, exist_ok=True); folder.mkdir()
    sampler = sampler if sampler is not None else monitor.BoundedSampler(monitor.LibprocProvider())
    popen = popen if popen is not None else subprocess.Popen
    info = dict(schema="eighth_sampling_work_capture_v1", validation="running", freeze=str(freeze_path),
                freeze_sha256=paths[str(freeze_path)], bound_sha256=paths, captures=[], cleanup=[],
                native_process_may_still_be_running=False, started_utc=native.now(),
                started_monotonic_ns=time.monotonic_ns(), counter_boundary=BOUNDARY,
                purpose="Untimed logical work; process durations are not benchmark data.")
    write_json(output, info)
    old = signal.getsignal(signal.SIGTERM)
    def interrupted(signum, frame): raise KeyboardInterrupt(f"signal {signum}")
    signal.signal(signal.SIGTERM, interrupted)
    seen = {}; values = []
    try:
        for index, spec in enumerate(frozen["schedule"], 1):
            for path, digest in paths.items(): analysis.hash_check(Path(path), digest)
            require(not sampler.poisoned, "poisoned sampler forbids another child")
            raw, log, rss = child_paths(output, index, spec)
            argv = command(frozen["variants"][spec["variant"]]["binary"], spec)
            item = dict(spec=spec, command=argv, launch_command=argv, raw=str(raw), log=str(log), rss_log=str(rss),
                        started_utc=native.now(), started_monotonic_ns=time.monotonic_ns())
            info["captures"].append(item); write_json(output, info)
            process = None; failure = None; observations = []; unavailable = 0
            try:
                with raw.open("x") as stdout, log.open("x") as stderr, rss.open("x") as resource:
                    process = popen(argv, cwd=ROOT, stdout=stdout, stderr=stderr, start_new_session=True)
                    item["process_group"] = process.pid
                    def observe():
                        observation = sampler.sample(process.pid); observations.append(observation)
                        resource.write(json.dumps(observation, allow_nan=False) + "\n"); resource.flush()
                        return observation
                    while True:
                        observation = observe()
                        require(not sampler.poisoned, "sampler timed out")
                        if observation["validation"] == "pass":
                            unavailable = 0
                            require(observation["rss_kib"] <= RULE["rss_limit_kib"], "sampled RSS ceiling exceeded")
                        else:
                            unavailable += 1
                            require(unavailable < 3, "three consecutive unavailable resource samples")
                        remaining_ns = DEADLINE_SECONDS * 10**9 - (time.monotonic_ns() - item["started_monotonic_ns"])
                        require(remaining_ns > 0, "diagnostic deadline exceeded")
                        try:
                            process.wait(timeout=min(RULE["poll_seconds"], remaining_ns / 1e9))
                            item["wrapper_exit_monotonic_ns"] = time.monotonic_ns()
                            require(item["wrapper_exit_monotonic_ns"] - item["started_monotonic_ns"] <= DEADLINE_SECONDS * 10**9,
                                    "diagnostic native exit exceeded deadline")
                            break
                        except subprocess.TimeoutExpired: pass
                    require(process.returncode == 0, "diagnostic child failed")
                    item["group_exit_verification"] = observe()
                    require(not sampler.poisoned and observations[-1]["validation"] == "pass" and not observations[-1]["members"], "owned group exit unknown")
            except BaseException as error:
                failure = error
                cleanup_owned_group(process, sampler, info)
            item.update(exit_status=process.returncode if process else None, interruption=repr(failure) if failure else None,
                        finished_utc=native.now(), finished_monotonic_ns=time.monotonic_ns(),
                        raw_sha256=native.sha(raw) if raw.exists() else None,
                        log_sha256=native.sha(log) if log.exists() else None,
                        rss_sha256=native.sha(rss) if rss.exists() else None,
                        rss_observations=len(observations), rss_unavailable=sum(r["validation"] != "pass" for r in observations),
                        rss_nonempty_observations=sum(r["validation"] == "pass" and bool(r["members"]) for r in observations),
                        sampled_peak_rss_kib=max((r["rss_kib"] for r in observations if r["validation"] == "pass"), default=None),
                        recovery_monitor=monitor.recovery_monitor(sampler.events.get(process.pid, [])[:len(observations)] if process else []))
            item["monotonic_elapsed_seconds"] = (item["finished_monotonic_ns"] - item["started_monotonic_ns"]) / 1e9
            write_json(output, info)
            if failure: raise failure
            for path, digest in paths.items(): analysis.hash_check(Path(path), digest)
            value = check_output(raw, spec)
            item["certificate"] = native.check_certificate(log, [value])
            resources(item); check_comparators(spec, value, seen)
            values.append((spec, value))
            item["validation"] = "pass"; write_json(output, info)
            print(f"Untimed work {index}/48 certified", flush=True)
        complete(values)
        info.update(validation="pass", checked_children=48, checked_solver_outputs=144)
    except BaseException as error:
        info.update(validation="failed", error=repr(error)); raise
    finally:
        signal.signal(signal.SIGTERM, old)
        info.update(finished_utc=native.now(), finished_monotonic_ns=time.monotonic_ns())
        write_json(output, info)
    try: load(output)
    except BaseException as error:
        info.update(validation="failed", error=repr(error))
        write_json(output, info)
        raise


def load(path):
    info = analysis.read_json(path)
    for key, value in dict(schema="eighth_sampling_work_capture_v1", validation="pass", cleanup=[],
                           native_process_may_still_be_running=False, checked_children=48,
                           checked_solver_outputs=144, counter_boundary=BOUNDARY).items():
        analysis.equal(info, key, value, "work capture")
    require("error" not in info, "failed capture")
    freeze_path = Path(info["freeze"]); analysis.hash_check(freeze_path, info["freeze_sha256"])
    frozen = check_freeze(freeze_path)
    paths = merge_paths(frozen["bound_sha256"], {str(freeze_path): native.sha(freeze_path)})
    analysis.equal(info, "bound_sha256", paths, "frozen work provenance")
    require(len(info["captures"]) == len(frozen["schedule"]) == 48, "incomplete diagnostic matrix")
    begin, end = analysis.monotonic_interval(info)
    analysis.timestamp(info["started_utc"]); analysis.timestamp(info["finished_utc"])
    previous = begin; values = []; seen = {}
    for index, (spec, item) in enumerate(zip(frozen["schedule"], info["captures"]), 1):
        argv = command(frozen["variants"][spec["variant"]]["binary"], spec)
        for key, value in dict(spec=spec, validation="pass", exit_status=0, interruption=None, command=argv, launch_command=argv).items():
            analysis.equal(item, key, value, "diagnostic identity")
        start, finish = analysis.monotonic_interval(item)
        analysis.timestamp(item["started_utc"]); analysis.timestamp(item["finished_utc"])
        require(previous <= start < finish <= end, "child overlap/interval invalid")
        analysis.equal(item, "monotonic_elapsed_seconds", (finish - start) / 1e9, "diagnostic duration")
        previous = finish
        raw, log, rss = child_paths(Path(path).resolve(), index, spec)
        for field, expected, digest in (("raw", raw, "raw_sha256"), ("log", log, "log_sha256"), ("rss_log", rss, "rss_sha256")):
            analysis.equal(item, field, str(expected), "diagnostic raw path")
            analysis.hash_check(expected, item[digest])
        value = check_output(raw, spec)
        analysis.equal(item, "certificate", native.check_certificate(log, [value]), "independent certificate")
        resources(item); check_comparators(spec, value, seen)
        values.append((spec, value))
    complete(values)
    return info, values


def summarize(args):
    capture_path = args.capture.resolve(strict=True)
    initial_capture_sha = native.sha(capture_path)
    info, values = load(capture_path)
    output = args.output_dir.resolve(); require(not output.exists(), "refusing to overwrite work analysis")
    rows, rounds, queries, chains, pairs = [], [], [], [], {}
    for spec, value in values:
        for name in ALGORITHMS:
            work = value["algorithms"][name]["work"]
            rows.append({**spec, "algorithm": name, "hash_insert_items_status": value["algorithms"][name]["hash_insert_items_status"], **work})
            if name != "kkt":
                replay = value["rounds"][name]
                rounds.extend({**spec, "algorithm": name, **row} for row in replay)
                chains.append({**spec, "algorithm": name, "rounds": len(replay),
                    **{field + "_sum": sum(row[field] for row in replay)
                       for field in ("vertices", "edges", "selected", "output_vertices", "output_edges")}})
        work = value["algorithms"]["kkt"]["work"]
        queries.append({**spec, **query_diagnostics(work)})
        key = tuple(spec[k] for k in ("case_id", "graph_seed", "kkt_seed"))
        pairs.setdefault(key, {})[spec["variant"]] = (spec, work)
    comparisons = []
    for pair in pairs.values():
        require(set(pair) == set(timing.VARIANTS), "missing counter variant")
        spec, half = pair["half"]; _, eighth = pair["eighth"]
        for field in FIELDS:
            a, b = half[field], eighth[field]
            comparisons.append({**{k: v for k, v in spec.items() if k != "variant"}, "counter": field,
                                "half": a, "eighth": b, "eighth_minus_half": b - a,
                                "eighth_over_half": b / a if a else None,
                                "ratio_status": "defined" if a else "both_zero" if b == 0 else "half_zero"})
    require(len(rows) == 144 and len(queries) == 48 and len(chains) == 96 and len(comparisons) == 24 * 65,
            "incomplete counter summaries")
    output.mkdir(parents=True)
    for name, data in (("work", rows), ("rounds", rounds), ("round_chains", chains),
                       ("query_work", queries), ("paired_kkt_work", comparisons)):
        analysis.write_csv(output / (name + ".csv"), data)
    for path, digest in info["bound_sha256"].items(): analysis.hash_check(Path(path), digest)
    for item in info["captures"]:
        for field, digest in (("raw", "raw_sha256"), ("log", "log_sha256"), ("rss_log", "rss_sha256")):
            analysis.hash_check(Path(item[field]), item[digest])
    analysis.hash_check(capture_path, initial_capture_sha)
    write_json(output / "provenance.json", dict(validation="pass", capture=str(args.capture.resolve()),
        capture_sha256=initial_capture_sha, bound_sha256=info["bound_sha256"], counter_boundary=BOUNDARY,
        solver_rows=144, paired_kkt_counter_rows=1560, query_rows=48, replay_chains=96,
        engine_words_exact=True, performance_claim=False), exclusive=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    prepare_parser = actions.add_parser("prepare")
    prepare_parser.add_argument("--timing-capture", type=Path, required=True)
    prepare_parser.add_argument("--freeze", type=Path, required=True)
    capture_parser = actions.add_parser("capture")
    capture_parser.add_argument("--freeze", type=Path, required=True)
    capture_parser.add_argument("--output", type=Path, required=True)
    capture_parser.add_argument("--released", action="store_true")
    verify_parser = actions.add_parser("verify")
    verify_parser.add_argument("--capture", type=Path, required=True)
    analyze_parser = actions.add_parser("analyze")
    analyze_parser.add_argument("--capture", type=Path, required=True)
    analyze_parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "prepare": prepare(args)
    elif args.action == "capture": capture(args)
    elif args.action == "verify": load(args.capture.resolve(strict=True)); print("Verified all 48 untimed diagnostic children")
    else: summarize(args)
