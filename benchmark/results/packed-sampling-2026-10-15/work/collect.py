#!/usr/bin/env python3
"""Untimed fixed 48-child work matrix. SOURCE PREPARATION: not yet executed/tested.

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
import run_packed_sampling as timing

native, analysis, monitor = timing.native, timing.analysis, timing.monitor
require, write_json, RULE = timing.require, timing.write_json, timing.RULE
ALGORITHMS = ("kkt", "compacting_boruvka", "multigraph_boruvka")
FIELDS = re.findall(r'\{"(\w+)", &kkt_work::WorkStats::\w+, (?:true|false)\}',
                    (ROOT / "benchmark/work_metrics.hpp").read_text())
DEADLINE_SECONDS = 1800
SOURCE = "benchmark/results/retention-control-2026-10-15/work/driver.cpp"
BOUNDARY = "Includes tuple-to-Edge input construction, solver, and temporary input destruction; certification and round replay are outside WorkStats."


def instrumented_commands(root, sdk):
    """Reconstruct the full correctness build; later overwrites cannot hide in a receipt."""
    base = ["/usr/bin/arch", "-arm64", "/usr/bin/clang++", "-isysroot", sdk,
            *timing.FLAGS, "-DKKT_ENABLE_WORK_STATS", "-I."]
    build = root / ".build/packed-sampling/native-correctness"
    shared = [str(build / "shared" / source.replace(".cpp", ".o")) for source in timing.SHARED_SOURCES]
    commands = [base + ["-c", source, "-o", obj] for source, obj in zip(timing.SHARED_SOURCES, shared)]
    kkt = {variant: str(build / variant / "kkt/kkt.o") for variant in timing.VARIANTS}
    for variant in timing.VARIANTS:
        extra = ["-DKKT_EXPERIMENT_PACKED_SAMPLING"] if variant == "packed" else []
        commands.append(base + extra + ["-c", "kkt/kkt.cpp", "-o", kkt[variant]])
    tests = ("test/edge_verifier_view_test.cpp", "test/multigraph_contraction_test.cpp",
             "test/regression_test.cpp", "test/contraction_test.cpp", "test/simple_test.cpp",
             "benchmark/core_attachment_test.cpp", "test/packed_sampling_test.cpp",
             "test/packed_sampling_integration_test.cpp")
    for source in tests:
        integration = source == "test/packed_sampling_integration_test.cpp"
        main = str(build / "shared" / source.replace(".cpp", ".o"))
        if not integration: commands.append(base + ["-c", source, "-o", main])
        for variant in timing.VARIANTS:
            if integration:
                main = str(build / variant / source.replace(".cpp", ".o"))
                extra = ["-DKKT_EXPERIMENT_PACKED_SAMPLING"] if variant == "packed" else []
                commands.append(base + extra + ["-c", source, "-o", main])
            binary = str(root / "bin/packed-sampling/native-correctness" / variant / Path(source).stem)
            commands.append(base + shared + ([] if integration else [kkt[variant]]) +
                            [main, f"-L{sdk}/usr/lib", "-Wl,-stack_size,0x20000000", "-o", binary])
    return commands


def check_instrumented_recipe(build, root):
    analysis.equal(build, "build_commands", instrumented_commands(root, build["sdk"]),
                   "complete instrumented compile/link sequence")


def provenance(timing_capture):
    info, cases, rows, _, _, paths = timing.load(timing_capture)
    require(len(FIELDS) == len(set(FIELDS)) == 65, "unexpected work counter schema")
    record_path = WORK / "build-record.json"
    record = analysis.read_json(record_path)
    for key, value in dict(schema="packed_sampling_work_build_v1", status="pass",
                           performance_executed=False, large_matrix_executed=False,
                           source=SOURCE, counter_boundary=BOUNDARY).items():
        analysis.equal(record, key, value, "diagnostic build")
    paths = {**paths, **timing.helpers(), str(HERE): native.sha(HERE),
             str(WORK / "PROTOCOL.md"): native.sha(WORK / "PROTOCOL.md"),
             str(record_path): native.sha(record_path),
             str(ROOT / SOURCE): record["source_sha256"],
             str(WORK.parent / "validation/build_work.py"): record["script_sha256"],
             record["main_object"]: record["main_object_sha256"],
             record["build_log"]: record["build_log_sha256"]}
    frozen = info["frozen_protocol"]
    current_sources = native.source_inventory(ROOT)
    require(current_sources == frozen["source_sha256"], "timing and diagnostic native sources differ")
    paths.update({str(ROOT / name): digest for name, digest in current_sources.items()})
    variants = {}
    expected_commands = []
    for executable in record["executables"]:
        variant = executable["variant"]
        require(variant in timing.VARIANTS and variant not in variants, "duplicate/unknown work variant")
        variants[variant] = executable
        build_path = Path(executable["instrumented_build_record"])
        paths[str(build_path)] = executable["instrumented_build_record_sha256"]
        build = analysis.read_json(build_path)
        flags = [*timing.FLAGS, "-DKKT_ENABLE_WORK_STATS"]
        inherited = frozen["variants"][variant]["build"]["record"]
        for key, value in dict(schema="packed_sampling_build_v1", profile="native-correctness",
                               variant=variant, working_directory=str(ROOT), source_sha256=current_sources,
                               common_compile_flags=flags, build_exit_status=0).items():
            analysis.equal(build, key, value, "instrumented build")
        for key in ("compiler", "compiler_command", "sdk", "build_recipe_sha256",
                    "parent_edge_freeze", "parent_edge_freeze_sha256"):
            analysis.equal(build, key, inherited[key], "same production source/toolchain")
        for name, digest in build["build_recipe_sha256"].items(): paths[str(ROOT / name)] = digest
        paths[build["build_log"]] = build["build_log_sha256"]
        for key in ("object_paths", "object_sha256"):
            analysis.equal(executable, key, build[key], "linked instrumented objects")
        require(set(build["object_paths"]) == timing.control.previous.OBJECTS, "wrong object inventory")
        paths.update({path: build["object_sha256"][name] for name, path in build["object_paths"].items()})
        base = ["/usr/bin/arch", "-arm64", "/usr/bin/clang++", "-isysroot", build["sdk"], *flags, "-I."]
        check_instrumented_recipe(build, ROOT)
        object_root = ROOT / ".build/packed-sampling/native-correctness"
        for name in timing.SHARED_SOURCES:
            object_name = name.replace(".cpp", ".o")
            expected = base + ["-c", name, "-o", str(object_root / "shared" / object_name)]
            require(expected in build["build_commands"], "missing exact shared compile")
        own_kkt = base + (["-DKKT_EXPERIMENT_PACKED_SAMPLING"] if variant == "packed" else []) + [
            "-c", "kkt/kkt.cpp", "-o", str(object_root / variant / "kkt/kkt.o")]
        require(own_kkt in build["build_commands"], "wrong instrumented KKT dispatch compile")
        expected_objects = {name.replace(".cpp", ".o"): str(object_root / "shared" / name.replace(".cpp", ".o"))
                            for name in timing.SHARED_SOURCES}
        expected_objects["kkt/kkt.o"] = str(object_root / variant / "kkt/kkt.o")
        analysis.equal(build, "object_paths", expected_objects, "exact production objects")
        binary = str(ROOT / "bin/packed-sampling/work" / variant / "retention_work")
        analysis.equal(executable, "binary", binary, "diagnostic binary")
        paths[binary] = executable["binary_sha256"]
        profile = executable["binary_profile"]
        require(profile["file_description"] == "Mach-O 64-bit executable arm64" and
                profile["main_stack_bytes"] == 536870912, "invalid native diagnostic profile")
        main = str(ROOT / ".build/packed-sampling/work/driver.o")
        analysis.equal(record, "main_object", main, "shared diagnostic driver")
        link = base + list(expected_objects.values()) + [main, f"-L{build['sdk']}/usr/lib",
                                                       "-Wl,-stack_size,0x20000000", "-o", binary]
        analysis.equal(executable, "link_command", link, "exact diagnostic link")
        if not expected_commands: expected_commands.append(base + ["-c", SOURCE, "-o", main])
        expected_commands.append(link)
    require(list(variants) == list(timing.VARIANTS), "incomplete/reordered variant proof")
    analysis.equal(record, "build_commands", expected_commands, "complete diagnostic build")
    for name in timing.control.previous.OBJECTS - {"kkt/kkt.o"}:
        for key in ("object_paths", "object_sha256"):
            require(variants["scalar"][key][name] == variants["packed"][key][name], "non-KKT diagnostic object differs")
    require(variants["scalar"]["object_sha256"]["kkt/kkt.o"] != variants["packed"]["object_sha256"]["kkt/kkt.o"],
            "instrumented KKT variants unexpectedly identical")
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


def prepare(args):
    variants, schedule, paths = provenance(args.timing_capture.resolve(strict=True))
    data = dict(schema="packed_sampling_work_freeze_v1", timing_capture=str(args.timing_capture.resolve()),
                variants=variants, schedule=schedule, bound_sha256=paths, counter_fields=FIELDS,
                counter_boundary=BOUNDARY, resource_rule=RULE, child_deadline_seconds=DEADLINE_SECONDS,
                expected_children=48, expected_solver_outputs=144, created_utc=native.now())
    write_json(args.freeze, data, exclusive=True)
    print("Prepared fixed 48-child / 144-output untimed matrix; no native execution")


def check_freeze(path):
    data = analysis.read_json(path)
    variants, schedule, paths = provenance(Path(data["timing_capture"]))
    for key, value in dict(schema="packed_sampling_work_freeze_v1", variants=variants, schedule=schedule,
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
    for key, expected in {"schema": "retention_control_work_v1", "validation": "pass",
                          "certified_output_items": spec["n"] - 1,
                          **{k: v for k, v in spec.items() if k not in ("variant", "intrusion_per_mille")}}.items():
        analysis.equal(value, key, expected, "diagnostic output")
    require(set(value["algorithms"]) == set(ALGORITHMS), "incorrect solver set")
    require(set(value["rounds"]) == set(ALGORITHMS[1:]), "incorrect replay set")
    for name, data in value["algorithms"].items():
        work = data["work"]
        require(set(work) == set(FIELDS), "counter schema changed")
        for key, count in work.items():
            if name != "kkt" and key == "hash_insert_items": require(count is None, "unmeasured hash count invented")
            else: require(type(count) is int and count >= 0, "invalid counter type/value")
        analysis.equal(data, "hash_insert_items_status", "measured" if name == "kkt" else "unmeasured", "hash scope")
        analysis.equal(work, "current_depth", 0, "unwound recursion")
        require(work["contraction_edge_visits"] <= (4 if name == "compacting_boruvka" else 3) * work["contraction_edges"], "contraction scan bound")
        if name == "kkt":
            analysis.equal(work, "hash_insert_items", spec["n"] - 1, "certified unique output size")
            require(work["sampling_calls"] == work["verifier_calls"] and
                    work["sampling_edge_visits"] == work["verifier_edges"] and
                    work["sampled_edges"] <= work["sampling_edge_visits"], "invalid sample/verifier work")
            require(work["sampling_calls"] > 0 or work["sampling_edge_visits"] == 0, "sample volume without call")
            continue
        require(all(work[k] == 0 for k in ("kkt_calls", "verifier_calls", "sampling_calls")), "comparator invoked KKT")
        rounds = value["rounds"][name]
        require(len(rounds) == work["contraction_calls"], "round count differs")
        n, m, selected = spec["n"], spec["m"], 0
        for index, row in enumerate(rounds):
            require(set(row) == {"round", "vertices", "edges", "selected", "output_vertices", "output_edges"}
                    and all(type(v) is int and v >= 0 for v in row.values()), "invalid replay row")
            require((row["round"], row["vertices"], row["edges"]) == (index, n, m), "broken replay chain")
            require(row["output_vertices"] <= n // 2 and row["output_edges"] <= m, "replay did not shrink")
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
    return value


def check_comparators(spec, value, seen):
    key = spec["case_id"], spec["graph_seed"]
    signature = {"algorithms": {k: value["algorithms"][k] for k in ALGORITHMS[1:]}, "rounds": value["rounds"]}
    require(key not in seen or seen[key] == signature, "unchanged comparator work/replay varies with sampler or variant")
    seen[key] = signature


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


def capture(args, sampler=None, popen=None):
    require(args.released, "work capture requires explicit root --released scheduling")
    freeze_path = args.freeze.resolve(strict=True)
    frozen = check_freeze(freeze_path)
    paths = {**frozen["bound_sha256"], str(freeze_path): native.sha(freeze_path)}
    output = args.output.resolve()
    folder = output.with_name(output.stem + "_cases")
    require(output.suffix == ".json" and not output.exists() and not folder.exists(), "refusing to overwrite evidence")
    output.parent.mkdir(parents=True, exist_ok=True); folder.mkdir()
    sampler = sampler if sampler is not None else monitor.BoundedSampler(monitor.LibprocProvider())
    popen = popen if popen is not None else subprocess.Popen
    info = dict(schema="packed_sampling_work_capture_v1", validation="running", freeze=str(freeze_path),
                freeze_sha256=paths[str(freeze_path)], bound_sha256=paths, captures=[], cleanup=[],
                native_process_may_still_be_running=False, started_utc=native.now(),
                started_monotonic_ns=time.monotonic_ns(), counter_boundary=BOUNDARY,
                purpose="Untimed logical work; process durations are not benchmark data.")
    write_json(output, info)
    old = signal.getsignal(signal.SIGTERM)
    def interrupted(signum, frame): raise KeyboardInterrupt(f"signal {signum}")
    signal.signal(signal.SIGTERM, interrupted)
    seen = {}
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
                cleanup = monitor.bounded_terminate(process, sampler)
                info["cleanup"].append(cleanup)
                info["native_process_may_still_be_running"] |= cleanup["native_process_may_still_be_running"]
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
            item["validation"] = "pass"; write_json(output, info)
            print(f"Untimed work {index}/48 certified", flush=True)
        info.update(validation="pass", checked_children=48, checked_solver_outputs=144)
    except BaseException as error:
        info.update(validation="failed", error=repr(error)); raise
    finally:
        signal.signal(signal.SIGTERM, old)
        info.update(finished_utc=native.now(), finished_monotonic_ns=time.monotonic_ns())
        write_json(output, info)
    load(output)


def load(path):
    info = analysis.read_json(path)
    for key, value in dict(schema="packed_sampling_work_capture_v1", validation="pass", cleanup=[],
                           native_process_may_still_be_running=False, checked_children=48,
                           checked_solver_outputs=144, counter_boundary=BOUNDARY).items():
        analysis.equal(info, key, value, "work capture")
    require("error" not in info, "failed capture")
    freeze_path = Path(info["freeze"]); analysis.hash_check(freeze_path, info["freeze_sha256"])
    frozen = check_freeze(freeze_path)
    paths = {**frozen["bound_sha256"], str(freeze_path): native.sha(freeze_path)}
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
    return info, values


def engine_bounds(work, variant):
    m, calls = work["sampling_edge_visits"], work["sampling_calls"]
    if variant == "scalar": return m, m, "exact_from_scalar_one_draw_per_edge"
    return m // 32 + (m % 32 != 0), min(m, (m + 31 * calls) // 32), "bounds_only_individual_call_sizes_unobserved"


def summarize(args):
    info, values = load(args.capture.resolve(strict=True))
    output = args.output_dir.resolve(); require(not output.exists(), "refusing to overwrite work analysis")
    rows, rounds, bounds, pairs = [], [], [], {}
    for spec, value in values:
        for name in ALGORITHMS:
            work = value["algorithms"][name]["work"]
            rows.append({**spec, "algorithm": name, "hash_insert_items_status": value["algorithms"][name]["hash_insert_items_status"], **work})
            if name != "kkt": rounds.extend({**spec, "algorithm": name, **row} for row in value["rounds"][name])
        work = value["algorithms"]["kkt"]["work"]
        lower, upper, method = engine_bounds(work, spec["variant"])
        bounds.append({**spec, "sampling_calls": work["sampling_calls"], "sampling_edge_visits": work["sampling_edge_visits"],
                       "engine_words_lower": lower, "engine_words_upper": upper, "method": method})
        key = tuple(spec[k] for k in ("case_id", "graph_seed", "kkt_seed"))
        pairs.setdefault(key, {})[spec["variant"]] = (spec, work)
    comparisons = []
    for pair in pairs.values():
        require(set(pair) == set(timing.VARIANTS), "missing counter variant")
        spec, scalar = pair["scalar"]; _, packed = pair["packed"]
        for field in FIELDS:
            a, b = scalar[field], packed[field]
            comparisons.append({**{k: v for k, v in spec.items() if k != "variant"}, "counter": field,
                                "scalar": a, "packed": b, "packed_minus_scalar": b - a,
                                "packed_over_scalar": b / a if a else None,
                                "ratio_status": "defined" if a else "both_zero" if b == 0 else "scalar_zero"})
    require(len(rows) == 144 and len(bounds) == 48 and len(comparisons) == 24 * 65, "incomplete counter summaries")
    output.mkdir(parents=True)
    for name, data in (("work", rows), ("rounds", rounds), ("engine_word_bounds", bounds), ("paired_kkt_work", comparisons)):
        analysis.write_csv(output / (name + ".csv"), data)
    for path, digest in info["bound_sha256"].items(): analysis.hash_check(Path(path), digest)
    for item in info["captures"]:
        for field, digest in (("raw", "raw_sha256"), ("log", "log_sha256"), ("rss_log", "rss_sha256")):
            analysis.hash_check(Path(item[field]), item[digest])
    write_json(output / "provenance.json", dict(validation="pass", capture=str(args.capture.resolve()),
        capture_sha256=native.sha(args.capture), bound_sha256=info["bound_sha256"], counter_boundary=BOUNDARY,
        solver_rows=144, paired_kkt_counter_rows=1560, engine_bound_rows=48, performance_claim=False), exclusive=True)


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
