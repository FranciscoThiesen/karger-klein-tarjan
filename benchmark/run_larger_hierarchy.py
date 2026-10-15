#!/usr/bin/env python3
"""Fixed prospective larger hierarchy/shuffled screen.

Requires reviewed validation, a prospective freeze and an explicit quiet native
release. This six-case matrix is separate from the 72-child held-out study and
does not extend or modify its protocol. Capture requires --released.
"""
import argparse
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
ALGORITHMS = control.ALGORITHMS
GRAPH_SEEDS = (11000009, 11000027)
SAMPLING_SEED, REPETITIONS, WARMUPS = 2203, 6, 1
FIELDS = control.FIELDS
RULE = control.RULE
SIZES = (65536, 1048576, 4194304)
PAIRS = (("leaf_hierarchy4", "leaf_shuffled4"),)
# Sizes ascend with adjacent weight twins; graph two reverses the whole list.
DECLARED_CASES = tuple((family, n, 32, 0) for n in SIZES for family in PAIRS[0])
EXPECTED_CASES = set(DECLARED_CASES)
TABLE_COUNTS = {"paired_ratios": 720, "comparisons": 60, "graph_comparisons": 120,
                "summary": 72, "graph_summary": 144}
SEMANTICS = {
    **control.SEMANTICS,
    "campaign": "compressed_larger_hierarchy_v1",
    "schedule": "Graph seed then six fixed manifest cases. Sizes 65536,1048576,4194304 ascend with hierarchy/shuffled twins adjacent. Graph seed two reverses the complete order, including twin order. Each child runs one checked warmup and six timed repetitions, balancing every solver once in every position. Seed and order remain confounded.",
    "purpose": "Test the existing leaf_hierarchy4/leaf_shuffled4 twins at all three declared sizes and density32, using the exact frozen compressed-query candidate and unchanged five controls. Twins preserve topology, IDs, labels, physical order and cheap leaves; core weights change. The largest input exactly reaches the existing n and m limits. No domain or resource-ceiling relaxation, new generator, historical pooling or change to the independent held-out study.",
    "comparison": "Compare KKT directly with all five competitors in the same child, graph seed, sampling seed and repetition. Pool all twelve paired trial ratios per case and retain each graph's six-trial median. No historical timing is pooled, normalized or replaced.",
    "crossover": "Evaluate every earlier/later measured size pair with exact rational graph medians. All four graph/clock medians must exceed one at the lower endpoint, be at most 0.90 at the upper endpoint, and remain at most 0.90 at every larger measured size. Keep all 30 endpoint pairs, all 30 point classifications and 10 family/comparator summaries. No monotonicity or interpolation assumption.",
}


def check_rows(path, spec, graph_seed):
    """Frozen six-position validation with this study's explicit local seeds.

    This is the retention-control row validator's unchanged checks and clock
    semantics, copied locally to avoid modifying any parent-module globals.
    """
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


def command(binary, spec, identity):
    require(identity["kkt_seed"] == SAMPLING_SEED and identity["graph_seed"] in GRAPH_SEEDS,
            "command seed differs from prospective declaration")
    return [str(binary), "--family", spec["family"], "--n", str(spec["n"]), "--density", str(spec["density"]),
            "--graph-seed", str(identity["graph_seed"]), "--kkt-seed", str(SAMPLING_SEED),
            "--repetitions", str(REPETITIONS), "--warmups", str(WARMUPS)]


def helpers():
    return {**parent_engine.helpers(), str(HERE): native.sha(HERE)}


def parent_record(path):
    path = Path(path).resolve(strict=True)
    analysis.hash_check(path, PARENT_SHA256)
    # Reuse the parent's complete native source/build/object/helper proof. This
    # checks the already frozen binaries, not a new build or timing observation.
    parent, _ = parent_engine.check_freeze(path)
    return parent


def cases_from_manifest(path):
    cases = native.load_manifest(path)
    require(tuple(tuple(spec[field] for field in native.base.MANIFEST_FIELDS)
                  for spec in cases.values()) == DECLARED_CASES,
            "manifest differs from declared 6 larger-hierarchy cases/order")
    return cases


def schedule(cases):
    return [{"case_id": case, "graph_seed": seed, "kkt_seed": SAMPLING_SEED}
            for index, seed in enumerate(GRAPH_SEEDS)
            for case in (list(cases) if index == 0 else list(reversed(cases)))]


def inherited_fields(parent):
    variant = parent["variants"]["compressed"]
    return {**variant, **{name: parent[name] for name in ("source_sha256", "build_recipe_sha256")}}


def preflight(args):
    root = Path.cwd().resolve(); parent_path = args.parent_freeze.resolve(strict=True)
    parent = parent_record(parent_path)
    require(str(root) == parent["working_directory"], "larger-hierarchy study must use the parent worktree")
    manifest = args.manifest.resolve(strict=True); protocol = args.protocol.resolve(strict=True)
    require(manifest != Path(parent["manifest"]) and protocol != Path(parent["protocol"]), "new search requires its own declaration")
    cases = cases_from_manifest(manifest)
    freeze = {"schema": "larger_hierarchy_freeze_v1", "created_utc": native.now(),
              "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "working_directory": str(root), "platform": platform.platform(), "machine": platform.machine(),
              "parent_freeze": str(parent_path), "parent_freeze_sha256": PARENT_SHA256,
              **inherited_fields(parent), "python_source_sha256": helpers(),
              "manifest": str(manifest), "manifest_sha256": native.sha(manifest),
              "protocol": str(protocol), "protocol_sha256": native.sha(protocol),
              "algorithms": list(ALGORITHMS), "graph_seeds": list(GRAPH_SEEDS), "sampling_seeds": [SAMPLING_SEED],
              "repetitions": REPETITIONS, "warmups": WARMUPS, "schedule": schedule(cases),
              "resource_rule": RULE, "semantics": SEMANTICS}
    args.freeze.parent.mkdir(parents=True, exist_ok=True); write_json(args.freeze, freeze, exclusive=True)
    print("Preflight passed; no native solver executed; frozen 12 children / 504 outputs")


def check_freeze(path):
    frozen = analysis.read_json(Path(path))
    for field, expected in (("schema", "larger_hierarchy_freeze_v1"), ("parent_freeze_sha256", PARENT_SHA256),
                            ("algorithms", list(ALGORITHMS)), ("graph_seeds", list(GRAPH_SEEDS)),
                            ("sampling_seeds", [SAMPLING_SEED]), ("repetitions", REPETITIONS), ("warmups", WARMUPS),
                            ("resource_rule", RULE), ("semantics", SEMANTICS)):
        analysis.equal(frozen, field, expected, "frozen larger-hierarchy protocol")
    parent = parent_record(frozen["parent_freeze"])
    analysis.equal(frozen, "working_directory", parent["working_directory"], "same parent worktree")
    for field, expected in inherited_fields(parent).items():
        analysis.equal(frozen, field, expected, "exact inherited compressed artifact")
    for name in ("manifest", "protocol"):
        analysis.hash_check(Path(frozen[name]), frozen[name + "_sha256"])
    analysis.equal(frozen, "python_source_sha256", helpers(), "current helper inventory")
    cases = cases_from_manifest(Path(frozen["manifest"]))
    analysis.equal(frozen, "schedule", schedule(cases), "frozen larger-hierarchy schedule")
    return frozen, cases


def check_fingerprints(rows, complete=False):
    native.check_fingerprints(rows)
    pair_of = {family: index for index, families in enumerate(PAIRS) for family in families}
    controls = {}
    for row in rows:
        require(row["family"] in pair_of, "unknown matched family")
        key = pair_of[row["family"]], row["n"], row["density"], row["graph_seed"]
        pair = controls.setdefault(key, {})
        pair[row["family"]] = row["input_fingerprint"], row["topology_fingerprint"]
    for key, pair in controls.items():
        if len(pair) == 2:
            first, second = (pair[family] for family in PAIRS[key[0]])
            require(first[1] == second[1], "matched weight controls have different topology/order")
            require(first[0] != second[0], "matched weight controls have identical weighted input")
    if complete:
        expected = {(index,n,32,seed) for index in range(len(PAIRS)) for n in SIZES for seed in GRAPH_SEEDS}
        require(set(controls) == expected and all(set(pair) == set(PAIRS[key[0]]) for key,pair in controls.items()),
                "incomplete 6-pair matched control matrix")


def child_paths(output, index, identity):
    raw = output.with_name(output.stem + "_cases") / f"{index:04d}_{identity['case_id']}_g{identity['graph_seed']}_s{SAMPLING_SEED}.csv"
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
    info = {"schema": "larger_hierarchy_capture_v1", "validation": "running", "freeze": str(freeze_path),
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
                child_rows, child_diagnostics = check_rows(raw, spec, identity["graph_seed"])
                certificate = native.check_certificate(log, child_rows)
                check_fingerprints([*rows, *child_rows])
                item.update(validation="pass", rows=len(child_rows), certificate=certificate,
                            flagged_calls=sum(bool(row["diagnostic_flags"]) for row in child_diagnostics))
                analysis.check_rss(rss, item, RULE); monitor.validate_monitor(item)
                rows.extend(child_rows); diagnostics.extend(child_diagnostics)
                writer.writerows(child_rows); combined.flush(); write_json(sidecar, info)
        check_fingerprints(rows, complete=True)
        require(len(rows) == 504, "incomplete larger-hierarchy capture matrix")
        info.update(validation="pass", checked_rows=len(rows), checked_timed_rows=432, checked_warmup_rows=72,
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
    print("Validated 12 native children: 432 timed outputs + 72 checked warmups")
    return info


def load(path):
    path = Path(path).resolve(strict=True); info = analysis.read_json(path)
    for field, expected in (("schema", "larger_hierarchy_capture_v1"), ("validation", "pass"), ("rows_removed", 0),
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
    require(len(info["captures"]) == 12, "incomplete native child schedule")
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
    check_fingerprints(rows, complete=True)
    actual = [row for _, row in native.base.read_csv(output, FIELDS)]
    require(actual == [{field: str(row[field]) for field in FIELDS} for row in rows], "combined CSV differs from exact ordered child concatenation")
    analysis.equal(info, "call_diagnostics", diagnostics, "clock diagnostics")
    analysis.equal(info, "capture_clock_flags", native.capture_clock_flags(info), "capture flags")
    for field, value in (("checked_rows", 504), ("checked_timed_rows", 432), ("checked_warmup_rows", 72),
                         ("flagged_calls", sum(bool(row["diagnostic_flags"]) for row in diagnostics))):
        analysis.equal(info, field, value, "capture counts")
    return info, cases, rows, diagnostics, resources, inputs


def aggregate(rows):
    tables = control.aggregate(rows)
    require({name:len(values) for name,values in tables.items()} == TABLE_COUNTS,
            "incomplete larger-hierarchy analysis tables")
    return tables


def crossovers(tables, cases):
    """Use raw integer pair endpoints, retaining every measured size relation."""
    groups = {}
    for row in tables["paired_ratios"]:
        require(row["case_id"] in cases and row["competitor"] in ALGORITHMS[1:] and
                row["metric"] in analysis.METRICS and row["graph_seed"] in GRAPH_SEEDS and
                row["kkt_seed"] == SAMPLING_SEED and row["repetition"] in range(6),
                "unknown crossover pair identity")
        require(type(row["kkt_ns"]) is int and type(row["competitor_ns"]) is int and
                row["kkt_ns"] > 0 and row["competitor_ns"] > 0, "invalid paired duration")
        key = tuple(row[name] for name in ("case_id","competitor","metric","graph_seed"))
        values = groups.setdefault(key,{})
        require(row["repetition"] not in values, "duplicate crossover trial")
        values[row["repetition"]] = Fraction(row["kkt_ns"],row["competitor_ns"])
    expected = {(case,competitor,metric,graph) for case in cases for competitor in ALGORITHMS[1:]
                for metric in analysis.METRICS for graph in GRAPH_SEEDS}
    require(set(groups) == expected and all(set(values) == set(range(6)) for values in groups.values()),
            "incomplete crossover graph/clock/trial matrix")
    medians = {key:statistics.median(values.values()) for key,values in groups.items()}
    def state(values):
        if all(value <= Fraction(9,10) for value in values): return "strong_lead"
        if all(value < 1 for value in values): return "narrow_lead"
        if all(value > 1 for value in values): return "loss"
        return "mixed_or_tied"
    points, brackets, summaries = [], [], []
    families = [family for pair in PAIRS for family in pair]
    for family in families:
        identities = [(spec["n"],case) for case,spec in cases.items() if spec["family"] == family]
        identities.sort()
        require(tuple(n for n,_ in identities) == SIZES, "missing/repeated size endpoint")
        for competitor in ALGORITHMS[1:]:
            states = []
            for n,case in identities:
                values = {(metric,graph):medians[(case,competitor,metric,graph)]
                          for metric in analysis.METRICS for graph in GRAPH_SEEDS}
                classification = state(values.values()); states.append(classification)
                row = {"family":family,"density":32,"competitor":competitor,"case_id":case,"n":n,"state":classification}
                for (metric,graph),value in values.items():
                    field = f"{metric}_g{graph}"
                    row.update({field:float(value),field+"_numerator":value.numerator,field+"_denominator":value.denominator})
                points.append(row)
            valid = []
            for lower in range(len(SIZES)):
                for upper in range(lower+1,len(SIZES)):
                    later_hold = all(value == "strong_lead" for value in states[upper+1:])
                    strong = states[lower] == "loss" and states[upper] == "strong_lead" and later_hold
                    row = {"family":family,"density":32,"competitor":competitor,
                           "lower_n":SIZES[lower],"upper_n":SIZES[upper],
                           "lower_state":states[lower],"upper_state":states[upper],
                           "all_larger_measured_points_strong":later_hold,"strong_crossover":strong}
                    brackets.append(row)
                    if strong: valid.append(row)
            # Earliest qualifying upper endpoint, then closest measured loss
            # below it. All other brackets and any earlier reversals remain.
            primary = min(valid,key=lambda row:(row["upper_n"],-row["lower_n"])) if valid else None
            summaries.append({"family":family,"density":32,"competitor":competitor,
                "strong_crossover":bool(valid),"qualifying_brackets":len(valid),
                "primary_lower_n":primary["lower_n"] if primary else None,
                "primary_upper_n":primary["upper_n"] if primary else None,
                "smallest_state":states[0],"largest_state":states[-1],
                "strong_lead_at_every_measured_size":all(value=="strong_lead" for value in states),
                "loss_at_every_measured_size":all(value=="loss" for value in states)})
    require((len(points),len(brackets),len(summaries)) == (30,30,10), "incomplete crossover tables")
    return {"crossover_points":points,"crossover_brackets":brackets,"crossover_summary":summaries}


def analyze(args):
    info, cases, rows, diagnostics, resources, inputs = load(args.capture)
    output = args.output_dir.resolve(); require(not output.exists(), "refusing to overwrite analysis"); output.mkdir(parents=True)
    tables = aggregate(rows)
    tables.update(crossovers(tables,cases))
    for name, values in {**tables, "validated_calls": rows, "call_diagnostics": diagnostics, "resources": resources}.items():
        analysis.write_csv(output / (name + ".csv"), values)
    power_audit = {"status": "not_audited", "sleep_inhibition_verified": False}
    if args.power_log:
        source = args.power_log.resolve(strict=True); inputs[str(source)] = native.sha(source)
        events, malformed, reversals = power.parse_events(source.read_text(errors="replace"))
        associations = power.original.correlate(rows, events, power.original.sleep_intervals(events))
        require(len(associations) == len(rows), "power association count differs")
        analysis.write_csv(output / "call_power_associations.csv", associations)
        power_audit.update(status="archived_log_correlated", parser=power.PARSER, source=str(source), source_sha256=inputs[str(source)],
                           logged_overlap_calls=sum(bool(row["nominal_logged_sleep_overlap_ns"]) for row in associations),
                           unalignable_calls=sum(not row["utc_alignable"] for row in associations),
                           malformed_event_lines=len(malformed), source_order_reversals=len(reversals),
                           limitation="External log provided; query success/retention coverage not established here. No raw private power events are copied into the analysis.")
    write_json(output / "provenance.json", {"schema": "larger_hierarchy_analysis_v1", "validation": "pass",
               "checked_rows": len(rows), "capture": info, "input_sha256": inputs, "power_audit": power_audit,
               "rows_removed": 0, "rows_adjusted": 0, "aggregation": SEMANTICS["comparison"]}, exclusive=True)
    text = ["# Larger hierarchy/shuffled screen with frozen compressed KKT", "", "All 504 solver outputs passed exact MST validation: "
            "432 timed calls and 72 checked warmups. Each algorithm occupies every timed position once per child. "
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
             "This separately declared campaign uses the exact frozen compressed binary, two weight twins, three sizes and fresh seeds. "
             "The largest n=4194304,d=32 input exactly reaches the existing n/m limits; no domain or RSS-ceiling relaxation was made. "
             "Finite measurements do not prove asymptotic dominance.", "", SEMANTICS["crossover"], "",
             "crossover_points.csv retains all sizes; crossover_brackets.csv retains every earlier/later endpoint pair. "
             "The primary bracket selects the earliest qualifying upper endpoint and then the closest measured loss below it. "
             "Earlier wins/reversals are not hidden. A win against multigraph Boruvka is not a win against Prim or original Boruvka. "
             "A lead only at the largest point has no measured persistence beyond it. Six repetitions reuse each of two graph/sampling realizations; "
             "a single sampler seed does not establish robustness across sampled forests.", ""]
    (output / "README.md").write_text("\n".join(text))
    print("Strict analysis passed: 504 outputs, 720 paired wall/CPU comparisons, 30 measured endpoint pairs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    prepare = actions.add_parser("preflight")
    for name in ("parent-freeze", "manifest", "protocol", "freeze"):
        prepare.add_argument("--" + name, type=Path, required=True)
    run = actions.add_parser("capture")
    run.add_argument("--freeze", type=Path, required=True); run.add_argument("--output", type=Path, required=True)
    run.add_argument("--released", action="store_true")
    report = actions.add_parser("analyze")
    report.add_argument("--capture", type=Path, required=True); report.add_argument("--output-dir", type=Path, required=True)
    report.add_argument("--power-log", type=Path)
    args = parser.parse_args(); {"preflight": preflight, "capture": capture, "analyze": analyze}[args.action](args)


if __name__ == "__main__": main()
