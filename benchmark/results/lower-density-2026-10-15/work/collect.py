#!/usr/bin/env python3
"""Untimed complete lower-density work matrix using the existing eighth artifact.

Preparation is separate from native release. Instrumented durations are resource
evidence, never performance measurements. No frozen parent globals are changed.
"""
import argparse
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve()
WORK = HERE.parent
ROOT = WORK.parents[3]
sys.path.insert(0, str(ROOT / "benchmark"))
import run_lower_density as timing

PARENT_WORK = ROOT / "benchmark/results/eighth-sampling-2026-10-15/work"
_spec = importlib.util.spec_from_file_location("lower_density_existing_eighth_work", PARENT_WORK / "collect.py")
parent = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(parent)
native, analysis, monitor = parent.native, parent.analysis, parent.monitor
require, write_json, RULE = parent.require, parent.write_json, parent.RULE
FIELDS, ALGORITHMS, BOUNDARY = parent.FIELDS, parent.ALGORITHMS, parent.BOUNDARY
DEADLINE_SECONDS = parent.DEADLINE_SECONDS
merge_paths, command, child_paths = parent.merge_paths, parent.command, parent.child_paths
resources, cleanup_owned_group = parent.resources, parent.cleanup_owned_group
query_diagnostics = parent.query_diagnostics
SELECTED_FIELDS = ("sampled_edges", "filtered_edges", "contraction_edge_visits",
    "sampling_edge_visits", "verifier_edge_visits", "path_query_visits",
    "initialized_slots", "edge_materializations")
COUNTS = dict(expected_children=60, expected_solver_outputs=180, counter_cells=11700,
              unmeasured_hash_cells=120, replay_chains=120, query_rows=60, topology_twins=30)


def digest_text(value):
    require(type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value),
            "invalid supplied artifact digest")
    return value


def provenance(timing_capture, timing_audit, parent_freeze, parent_freeze_sha256):
    """Run both existing complete proofs without replacing their entry points."""
    timing_capture = Path(timing_capture).resolve(strict=True)
    timing_audit = Path(timing_audit).resolve(strict=True)
    parent_freeze = Path(parent_freeze).resolve(strict=True)
    timing_capture_sha = native.sha(timing_capture)
    timing_audit_sha = native.sha(timing_audit)
    require(parent_freeze == (PARENT_WORK / "freeze.json").resolve(strict=True), "wrong existing work freeze")
    analysis.hash_check(parent_freeze, digest_text(parent_freeze_sha256))
    inherited = parent.check_freeze(parent_freeze)
    info, cases, rows, _, _, inputs = timing.load(timing_capture)
    require(len(FIELDS) == len(set(FIELDS)) == 65, "wrong work field inventory")
    require(len(rows) == 2520 and len(info["captures"]) == 60, "incomplete timing matrix")
    require(info["frozen_protocol"]["parent_freeze_sha256"] == timing.PARENT_SHA256,
            "new timing uses a different eighth parent")
    # This historical proof itself strict-loads the original completed timing
    # capture and reconstructs every instrumented build command and target.
    old_info, _, _, _, _, _ = parent.timing.load(Path(inherited["timing_capture"]))
    analysis.equal(old_info, "freeze_sha256", timing.PARENT_SHA256, "exact common eighth timing parent")
    artifact = inherited["variants"]["eighth"]
    for key, value in dict(sampling_policy="eighth", private_acceptance_mask=7,
                           sampling_words_per_visited_edge=1, verifier_policy="compressed").items():
        require(type(artifact.get(key)) is type(value) and artifact[key] == value, "wrong reused diagnostic policy")
    audit = analysis.read_json(timing_audit)
    for key, value in dict(schema="independent_lower_density_numerical_audit_v1", validation="pass",
            collector_imported=False, raw_native_children=60, checked_outputs=2520,
            timed_outputs=2160, warmup_outputs=360, matched_topology_twins=30, certificates=60,
            owned_groups_verified_empty=60, strict_analyzer_pairs_medians_ranges_counts_agree=True).items():
        require(type(audit.get(key)) is type(value) and audit[key] == value, "incomplete independent timing audit")
    analysis.equal(audit, "table_counts", {**timing.TABLE_COUNTS, "crossover_points":150,
        "crossover_brackets":490, "crossover_summary":20}, "complete timing audit tables")
    analysis.equal(audit, "supplied_freeze", info["freeze"], "audit timing freeze path")
    analysis.equal(audit, "supplied_freeze_sha256", info["freeze_sha256"], "audit timing freeze digest")
    audit_inputs = audit["input_sha256"]
    require(audit_inputs.get(str(timing_capture)) == timing_capture_sha, "audit did not bind timing capture")
    audit_source = WORK.parent / "validation/independent_numerical_audit.py"
    require(audit_inputs.get(str(audit_source)) == native.sha(audit_source), "audit source identity missing")
    paths = merge_paths(inherited["bound_sha256"], inputs, timing.helpers(), audit_inputs,
        {str(parent_freeze): parent_freeze_sha256, str(timing_capture): timing_capture_sha,
         str(timing_audit): timing_audit_sha, str(HERE): native.sha(HERE),
         str(WORK / "PROTOCOL.md"): native.sha(WORK / "PROTOCOL.md")})
    fingerprints = {}
    for row in rows:
        key = row["case_id"], row["graph_seed"], row["kkt_seed"]
        value = {field:row[field] for field in ("input_fingerprint", "topology_fingerprint")}
        require(key not in fingerprints or fingerprints[key] == value, "timing fingerprint changed")
        fingerprints[key] = value
    schedule = [{"variant":"eighth", **identity, **cases[identity["case_id"]],
                 **fingerprints[tuple(identity[key] for key in ("case_id", "graph_seed", "kkt_seed"))]}
                for identity in timing.schedule(cases)]
    require(len(schedule) == len(fingerprints) == 60, "wrong new diagnostic schedule")
    for path, digest in paths.items(): analysis.hash_check(Path(path), digest)
    return artifact, schedule, paths


def prepare(args):
    artifact, schedule, paths = provenance(args.timing_capture, args.timing_audit,
                                          args.parent_work_freeze, args.parent_work_freeze_sha256)
    value = dict(schema="lower_density_work_freeze_v1", timing_capture=str(args.timing_capture.resolve()),
        timing_audit=str(args.timing_audit.resolve()), parent_work_freeze=str(args.parent_work_freeze.resolve()),
        parent_work_freeze_sha256=args.parent_work_freeze_sha256, variants={"eighth":artifact},
        schedule=schedule, bound_sha256=paths, counter_fields=FIELDS, counter_boundary=BOUNDARY,
        resource_rule=RULE, child_deadline_seconds=DEADLINE_SECONDS, selected_fields=list(SELECTED_FIELDS),
        **COUNTS, created_utc=native.now())
    write_json(args.freeze, value, exclusive=True)
    print("Prepared 60 untimed inputs / 180 certified outputs; no native execution")


def check_freeze(path):
    value = analysis.read_json(Path(path))
    artifact, schedule, paths = provenance(value["timing_capture"], value["timing_audit"],
                                          value["parent_work_freeze"], value["parent_work_freeze_sha256"])
    for key, expected in dict(schema="lower_density_work_freeze_v1", variants={"eighth":artifact},
            schedule=schedule, bound_sha256=paths, counter_fields=FIELDS, counter_boundary=BOUNDARY,
            resource_rule=RULE, child_deadline_seconds=DEADLINE_SECONDS,
            selected_fields=list(SELECTED_FIELDS), **COUNTS).items():
        analysis.equal(value, key, expected, "prospective untimed work freeze")
    return value


def check_output(path, spec):
    value = parent.check_output(path, spec)
    if spec["family"] == "leaf_distance4":
        work = value["algorithms"]["kkt"]["work"]
        require(work["root_after_two_vertices"] == spec["n"] // 8 and
                work["root_after_two_edges"] == spec["m"] - 7 * spec["n"] // 8,
                "ordered distance root differs from exact two-step dimensions")
    return value


def complete(values):
    expected = {(f"{family}_n{n}_d{density}_p0", graph, 3407)
                for density, sizes in timing.SIZE_LADDERS.items() for n in sizes
                for family in ("leaf_distance4", "leaf_shuffled4") for graph in (23000003,23000029)}
    actual = [tuple(spec[k] for k in ("case_id", "graph_seed", "kkt_seed")) for spec, _ in values]
    require(len(values) == len(set(actual)) == 60 and set(actual) == expected and
            all(spec["variant"] == "eighth" for spec, _ in values), "incomplete/duplicate work matrix")
    timing.check_fingerprints([value for _,value in values], complete=True)
    require(any(query_diagnostics(value["algorithms"]["kkt"]["work"])["Q"] > 0 for _,value in values),
            "no positive query witness in complete matrix")


def check_comparators(spec, value, seen):
    # Single policy/seed means no cross-rate equality assertion is appropriate.
    # The inherited output gate already checks each complete deterministic replay.
    require(spec["variant"] == "eighth", "foreign work policy")


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
    info = dict(schema="lower_density_work_capture_v1", validation="running", freeze=str(freeze_path),
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
            print(f"Untimed work {index}/60 certified", flush=True)
        complete(values)
        info.update(validation="pass", checked_children=60, checked_solver_outputs=180)
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
    for key, value in dict(schema="lower_density_work_capture_v1", validation="pass", cleanup=[],
                           native_process_may_still_be_running=False, checked_children=60,
                           checked_solver_outputs=180, counter_boundary=BOUNDARY).items():
        analysis.equal(info, key, value, "work capture")
    require("error" not in info, "failed capture")
    freeze_path = Path(info["freeze"]); analysis.hash_check(freeze_path, info["freeze_sha256"])
    frozen = check_freeze(freeze_path)
    paths = merge_paths(frozen["bound_sha256"], {str(freeze_path): native.sha(freeze_path)})
    analysis.equal(info, "bound_sha256", paths, "frozen work provenance")
    require(len(info["captures"]) == len(frozen["schedule"]) == 60, "incomplete diagnostic matrix")
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


def tables(values):
    complete(values)
    rows, rounds, chains, queries, normalized = [], [], [], [], []
    for spec, value in values:
        for algorithm in ALGORITHMS:
            record = value["algorithms"][algorithm]
            work = record["work"]
            rows.append({**spec, "algorithm":algorithm,
                         "hash_insert_items_status":record["hash_insert_items_status"], **work})
            for field in FIELDS:
                count = work[field]
                fraction = Fraction(count, spec["m"]) if count is not None else None
                normalized.append({**spec, "algorithm":algorithm, "counter":field, "count":count,
                    "per_original_edge":float(fraction) if fraction is not None else None,
                    "numerator":fraction.numerator if fraction is not None else None,
                    "denominator":fraction.denominator if fraction is not None else None,
                    "status":"defined" if fraction is not None else "unmeasured"})
            if algorithm != "kkt":
                replay = value["rounds"][algorithm]
                rounds.extend({**spec, "algorithm":algorithm, **row} for row in replay)
                chains.append({**spec, "algorithm":algorithm, "rounds":len(replay),
                    **{field + "_sum":sum(row[field] for row in replay)
                       for field in ("vertices", "edges", "selected", "output_vertices", "output_edges")}})
        work = value["algorithms"]["kkt"]["work"]
        queries.append({**spec, **query_diagnostics(work)})
    require((len(rows),len(chains),len(queries),len(normalized)) == (180,120,60,11700),
            "wrong complete work table counts")
    require(sum(row["status"] == "unmeasured" for row in normalized) == 120,
            "wrong unmeasured comparator hash count")
    return dict(work=rows, rounds=rounds, round_chains=chains, query_work=queries,
                normalized_work=normalized)


def recheck(info, capture, digest):
    for path, expected in info["bound_sha256"].items(): analysis.hash_check(Path(path), expected)
    for item in info["captures"]:
        for field, key in (("raw","raw_sha256"),("log","log_sha256"),("rss_log","rss_sha256")):
            analysis.hash_check(Path(item[field]), item[key])
    analysis.hash_check(capture, digest)


def summarize(args):
    capture_path = args.capture.resolve(strict=True); initial = native.sha(capture_path)
    info, values = load(capture_path)
    output = args.output_dir.resolve(); require(not output.exists(), "refusing to overwrite analysis")
    result = tables(values)
    recheck(info, capture_path, initial)
    output.mkdir(parents=True)
    for name, rows in result.items(): analysis.write_csv(output / (name + ".csv"), rows)
    recheck(info, capture_path, initial)
    write_json(output / "provenance.json", dict(schema="lower_density_work_analysis_v1", validation="pass",
        capture=str(capture_path), capture_sha256=initial, bound_sha256=info["bound_sha256"],
        table_counts={name:len(rows) for name,rows in result.items()}, counter_boundary=BOUNDARY,
        selected_fields=list(SELECTED_FIELDS), **COUNTS, engine_words_exact=True,
        performance_claim=False), exclusive=True)
    print("Strict work analysis: 60 inputs, 180 solver records, 11700 cells, 120 chains")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    prepare_parser = actions.add_parser("prepare")
    for name in ("timing-capture", "timing-audit", "parent-work-freeze", "freeze"):
        prepare_parser.add_argument("--" + name, type=Path, required=True)
    prepare_parser.add_argument("--parent-work-freeze-sha256", required=True)
    run = actions.add_parser("capture")
    run.add_argument("--freeze", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--released", action="store_true")
    verify = actions.add_parser("verify"); verify.add_argument("--capture", type=Path, required=True)
    report = actions.add_parser("analyze")
    report.add_argument("--capture", type=Path, required=True)
    report.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "prepare": prepare(args)
    elif args.action == "capture": capture(args)
    elif args.action == "verify": load(args.capture.resolve(strict=True)); print("Verified 60 untimed inputs")
    else: summarize(args)


if __name__ == "__main__": main()

