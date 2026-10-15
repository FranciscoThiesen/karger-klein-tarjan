#!/usr/bin/env python3
"""Fresh density/weight-order search using the frozen direct-Edge binary only.

No parent helper/native source is changed. The independent schema owns an eight
case declaration, fresh seed scope and sixteen-child capture; existing native
row, certificate, clock and bounded group-monitor validators remain unchanged.
"""
import argparse
import contextlib
import csv
import json
from pathlib import Path
import platform
import signal
import subprocess
import time

import run_edge_view_experiment as parent_engine

control = parent_engine.control
native, analysis, monitor = control.native, control.analysis, control.monitor
power = control.power
require, write_json = control.require, control.write_json
HERE = Path(__file__).resolve()
PARENT_SHA256 = "f976a7d61650f5aaf8e7221c7684461e36bcb51492347f45a56497b6b1cee306"
ALGORITHMS = control.ALGORITHMS
GRAPH_SEEDS = (5000011, 5000081)
SAMPLING_SEED, REPETITIONS, WARMUPS = 1217, 6, 1
FIELDS = control.FIELDS
RULE = control.RULE
EXPECTED_CASES = {(family, n, density, 0) for family in ("leaf_hierarchy4", "leaf_shuffled4")
                  for density in (32, 64) for n in (65536, 1048576)}
SEMANTICS = {
    **control.SEMANTICS,
    "campaign": "direct_edge_density_search_v1",
    "schedule": "Graph seed then eight manifest cases. Second graph seed reverses case order. Each child runs one checked warmup and six timed repetitions, balancing each solver once in every position.",
    "purpose": "Test denser leaf-attachment graphs with ordered versus shuffled core ranks using the exact frozen direct-Edge KKT binary. Matched hierarchy/shuffled cases have identical topology, IDs, labels and physical edge order; both retain cheap leaf attachments. Shuffled core ranks do not mean globally random edge weights.",
    "comparison": "Compare KKT directly with all five competitors in the same child, graph seed, sampling seed and repetition. Pool all twelve paired trial ratios per case and retain each graph's six-trial median. No historical timing is pooled, normalized or replaced.",
}


@contextlib.contextmanager
def configured():
    before = {name: getattr(control, name) for name in ("GRAPH_SEEDS", "SAMPLING_SEED")}
    try:
        control.GRAPH_SEEDS, control.SAMPLING_SEED = GRAPH_SEEDS, SAMPLING_SEED
        yield
    finally:
        for name, value in before.items(): setattr(control, name, value)


def check_rows(path, spec, seed):
    with configured(): return control.check_rows(path, spec, seed)


def command(binary, spec, identity):
    with configured(): return control.command(binary, spec, identity)


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
    require(len(cases) == 8 and {tuple(spec[field] for field in native.base.MANIFEST_FIELDS)
                                for spec in cases.values()} == EXPECTED_CASES,
            "manifest differs from declared eight density cases")
    return cases


def schedule(cases):
    return [{"case_id": case, "graph_seed": seed, "kkt_seed": SAMPLING_SEED}
            for index, seed in enumerate(GRAPH_SEEDS)
            for case in (list(cases) if index == 0 else list(reversed(cases)))]


def inherited_fields(parent):
    variant = parent["variants"]["edge"]
    return {**variant, **{name: parent[name] for name in ("source_sha256", "build_recipe_sha256")}}


def preflight(args):
    root = Path.cwd().resolve(); parent_path = args.parent_freeze.resolve(strict=True)
    parent = parent_record(parent_path)
    require(str(root) == parent["working_directory"], "density search must use the parent worktree")
    manifest = args.manifest.resolve(strict=True); protocol = args.protocol.resolve(strict=True)
    require(manifest != Path(parent["manifest"]) and protocol != Path(parent["protocol"]), "new search requires its own declaration")
    cases = cases_from_manifest(manifest)
    freeze = {"schema": "density_search_freeze_v1", "created_utc": native.now(),
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
    print("Preflight passed; no native solver executed; frozen 16 children / 672 outputs")


def check_freeze(path):
    frozen = analysis.read_json(Path(path))
    for field, expected in (("schema", "density_search_freeze_v1"), ("parent_freeze_sha256", PARENT_SHA256),
                            ("algorithms", list(ALGORITHMS)), ("graph_seeds", list(GRAPH_SEEDS)),
                            ("sampling_seeds", [SAMPLING_SEED]), ("repetitions", REPETITIONS), ("warmups", WARMUPS),
                            ("resource_rule", RULE), ("semantics", SEMANTICS)):
        analysis.equal(frozen, field, expected, "frozen density-search protocol")
    parent = parent_record(frozen["parent_freeze"])
    analysis.equal(frozen, "working_directory", parent["working_directory"], "same parent worktree")
    for field, expected in inherited_fields(parent).items():
        analysis.equal(frozen, field, expected, "exact inherited direct-Edge artifact")
    for name in ("manifest", "protocol"):
        analysis.hash_check(Path(frozen[name]), frozen[name + "_sha256"])
    analysis.equal(frozen, "python_source_sha256", helpers(), "current helper inventory")
    cases = cases_from_manifest(Path(frozen["manifest"]))
    analysis.equal(frozen, "schedule", schedule(cases), "frozen density schedule")
    return frozen, cases


def check_fingerprints(rows, complete=False):
    native.check_fingerprints(rows)
    controls = {}
    for row in rows:
        key = row["n"], row["density"], row["graph_seed"]
        pair = controls.setdefault(key, {})
        pair[row["family"]] = row["input_fingerprint"], row["topology_fingerprint"]
    for pair in controls.values():
        if len(pair) == 2:
            first, second = pair["leaf_hierarchy4"], pair["leaf_shuffled4"]
            require(first[1] == second[1], "matched weight controls have different topology/order")
            require(first[0] != second[0], "matched weight controls have identical weighted input")
    if complete:
        require(len(controls) == 8 and all(set(pair) == {"leaf_hierarchy4", "leaf_shuffled4"} for pair in controls.values()),
                "incomplete hierarchy/shuffled control matrix")


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
    info = {"schema": "density_search_capture_v1", "validation": "running", "freeze": str(freeze_path),
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
                check_fingerprints([*rows, *child_rows])
                item.update(validation="pass", rows=len(child_rows), certificate=certificate,
                            flagged_calls=sum(bool(row["diagnostic_flags"]) for row in child_diagnostics))
                analysis.check_rss(rss, item, RULE); monitor.validate_monitor(item)
                rows.extend(child_rows); diagnostics.extend(child_diagnostics)
                writer.writerows(child_rows); combined.flush(); write_json(sidecar, info)
        check_fingerprints(rows, complete=True)
        info.update(validation="pass", checked_rows=len(rows), checked_timed_rows=576, checked_warmup_rows=96,
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
    print("Validated 16 native children: 576 timed outputs + 96 checked warmups")
    return info


def load(path):
    path = Path(path).resolve(strict=True); info = analysis.read_json(path)
    for field, expected in (("schema", "density_search_capture_v1"), ("validation", "pass"), ("rows_removed", 0),
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
    require(len(info["captures"]) == 16, "incomplete native child schedule")
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
    for field, value in (("checked_rows", 672), ("checked_timed_rows", 576), ("checked_warmup_rows", 96),
                         ("flagged_calls", sum(bool(row["diagnostic_flags"]) for row in diagnostics))):
        analysis.equal(info, field, value, "capture counts")
    return info, cases, rows, diagnostics, resources, inputs


def aggregate(rows):
    return control.aggregate(rows)


def analyze(args):
    info, cases, rows, diagnostics, resources, inputs = load(args.capture)
    output = args.output_dir.resolve(); require(not output.exists(), "refusing to overwrite analysis"); output.mkdir(parents=True)
    tables = aggregate(rows)
    require({name: len(values) for name, values in tables.items()} ==
            {"paired_ratios": 960, "comparisons": 80, "graph_comparisons": 160, "summary": 96, "graph_summary": 192},
            "incomplete density analysis tables")
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
    write_json(output / "provenance.json", {"schema": "density_search_analysis_v1", "validation": "pass",
               "checked_rows": len(rows), "capture": info, "input_sha256": inputs, "power_audit": power_audit,
               "rows_removed": 0, "rows_adjusted": 0, "aggregation": SEMANTICS["comparison"]}, exclusive=True)
    text = ["# Direct-Edge density and core-weight-order search", "", "All 672 solver outputs passed exact MST validation: "
            "576 timed calls and 96 checked warmups. Each algorithm occupies every timed position once per child. "
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
             "This campaign uses the exact prior direct-Edge binary with fresh graph/sampling seeds and denser cases. Finite measurements do not prove asymptotic dominance.", ""]
    (output / "README.md").write_text("\n".join(text))
    print("Strict analysis passed: 672 outputs, 960 paired wall/CPU comparisons")


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
