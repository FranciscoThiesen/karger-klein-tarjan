#!/usr/bin/env python3
"""Run ONE frozen confirmation campaign after explicit scheduling release.

This orchestration controller is outside the six immutable capture helpers. It does
not alter algorithms, timings, orders, seeds, rows, clock flags or native limits.
It must not be executed while another native measurement is active.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import signal
import statistics
import subprocess
import sys
import time

GRAPHS = [1000039, 1000081, 1000099]
SAMPLES = [401, 503]
COMPARATORS = ["compacting_boruvka", "kruskal", "prim", "boruvka"]
HELPERS = ("run_mst_search.py", "analyze_mst_search.py", "run_crossover.py",
           "analyze_continuation.py", "crossover_clocks.py", "run_crossover_baselines.py")
DECLARATION_REVISION = "d641ca8"


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(path):
    with Path(path).open("rb") as stream:
        h = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def append(path, data):
    with path.open("a") as stream:
        stream.write(json.dumps(data, allow_nan=False) + "\n")


def equal(actual, expected, context):
    if type(actual) is not type(expected) or actual != expected:
        raise ValueError(context + " differs from the required value")


def bind_hashes(registry, label):
    if not isinstance(registry, dict) or not registry:
        raise ValueError(label + " has no hash inventory")
    for name, digest in registry.items():
        if sha(Path(name)) != digest:
            raise ValueError(label + " changed: " + name)


def validated_prior(root, raw, analysis, case_count, graph_seeds, sampling_seeds):
    """Bind a completed strict analysis before consuming any fresh seed.

    This checks the prior analyzer's complete hash registry, not a substitute
    implementation of its native certificate/clock/schema checks.
    """
    metadata_path = raw.with_suffix(".json")
    provenance_path = analysis / "provenance.json"
    info = json.loads(metadata_path.read_text())
    provenance = json.loads(provenance_path.read_text())
    children = case_count * len(graph_seeds) * len(sampling_seeds)
    timed, warmups = children * 25, children * 5
    for field, value in (("schema", "mst_search_capture_v1"), ("validation", "pass"),
                         ("checked_rows", timed + warmups), ("checked_timed_rows", timed),
                         ("checked_warmup_rows", warmups), ("rows_removed", 0), ("rows_adjusted", 0),
                         ("graph_seeds", graph_seeds), ("sampling_seeds", sampling_seeds),
                         ("repetitions", 5), ("warmups", 1)):
        equal(info.get(field), value, str(raw) + " " + field)
    if "error" in info or len(info.get("captures", [])) != children:
        raise ValueError("prior capture is failed or incomplete")
    for child in info["captures"]:
        equal(child.get("exit_status"), 0, "prior child exit status")
        equal(child.get("validation"), "pass", "prior child validation")
        equal(child.get("rows"), 30, "prior child rows")
        equal(child.get("interruption"), None, "prior child interruption")
    for field, value in (("schema", "mst_search_analysis_v1"), ("validation", "pass"),
                         ("cases", case_count), ("checked_rows", timed + warmups),
                         ("timed_rows", timed), ("warmup_rows", warmups),
                         ("rows_removed", 0), ("rows_adjusted", 0)):
        equal(provenance.get(field), value, str(analysis) + " " + field)
    snapshot = dict(provenance.get("capture_metadata", {}))
    equal(snapshot.pop("raw_csv", None), str(raw), "prior analysis raw CSV")
    snapshot.pop("raw_csv_link", None)
    equal(snapshot, info, "prior analysis capture metadata")
    inputs = provenance.get("input_sha256", {})
    equal(inputs.get(str(raw)), sha(raw), "prior analysis raw hash")
    equal(inputs.get(str(metadata_path)), sha(metadata_path), "prior analysis metadata hash")
    equal(inputs.get(info["manifest"]), info["manifest_sha256"], "prior analysis manifest binding")
    equal(info["output_sha256"], sha(raw), "prior capture output hash")
    bind_hashes(inputs, "prior analysis input")
    derived = {str(analysis / name): digest for name, digest in provenance.get("derived_sha256", {}).items()}
    bind_hashes(derived, "prior analysis output")
    current_sources = {str(p.relative_to(root)): sha(p) for pattern in ("*/*.cpp", "*/*.hpp")
                       for p in sorted(root.glob(pattern))}
    current_helpers = {str(root / "benchmark" / name): sha(root / "benchmark" / name) for name in HELPERS}
    equal(info.get("source_sha256"), current_sources, "current complete C++ inventory")
    equal(info.get("build_recipe_sha256"), {"Makefile": sha(root / "Makefile")}, "current Makefile")
    equal(info.get("python_source_sha256"), current_helpers, "current six helper files")
    equal(provenance.get("analysis_source_sha256"), current_helpers, "prior analysis helper inventory")
    binary = root / "bin/large_stack/mst_search"
    equal(info.get("binary"), str(binary), "prior binary path")
    equal(info.get("binary_sha256"), sha(binary), "current binary hash")
    equal(info.get("binary_profile", {}).get("main_stack_bytes"), 536870912, "prior stack size")
    equal(info.get("machine"), "arm64", "prior native machine")
    bound = {**inputs, **derived, str(provenance_path): sha(provenance_path)}
    return info, bound


def frozen_declaration(root, folder):
    """Git reads run once before capture, never while native solvers are active."""
    bound = {}
    for name in ("ATTACHMENT_CONFIRMATION.md", "attachment-confirmation-a.csv", "attachment-confirmation-b.csv"):
        path = folder / name
        relative = path.relative_to(root).as_posix()
        original = subprocess.check_output(["git", "show", DECLARATION_REVISION + ":" + relative], cwd=root)
        digest = hashlib.sha256(original).hexdigest()
        equal(sha(path), digest, "frozen declaration " + name)
        bound[str(path)] = digest
    return bound


def observation(command):
    try:
        p = subprocess.run(command, text=True, capture_output=True, timeout=10)
        return {"command": command, "exit_status": p.returncode,
                "stdout": p.stdout, "stderr": p.stderr}
    except Exception as error:
        return {"command": command, "error": repr(error)}


def completed_case_ratios(captures, case_id):
    """Lightweight descriptive progress only; final strict analyzer is mandatory."""
    rows = []
    selected = [c for c in captures if c["case_id"] == case_id and c.get("validation") == "pass"]
    if len(selected) != 6:
        raise ValueError("completed case lacks six validated native children")
    for child in selected:
        with Path(child["csv"]).open(newline="") as stream:
            rows.extend(r for r in csv.DictReader(stream)
                        if r["case_id"] == case_id and r["phase"] == "timed")
    by_key = {(int(r["graph_seed"]), int(r["kkt_seed"]), int(r["repetition"]), r["algorithm"]): r
              for r in rows}
    if len(rows) != 150 or len(by_key) != 150:
        raise ValueError("completed case does not contain 150 distinct timed rows")
    result = {}
    for metric, field in (("wall", "elapsed_ns"), ("cpu", "process_cpu_elapsed_ns")):
        result[metric] = {}
        for competitor in COMPARATORS:
            graph_medians = []
            individual = []
            for g in GRAPHS:
                sampling_medians = []
                for s in SAMPLES:
                    ratios = [int(by_key[(g, s, r, "kkt")][field]) /
                              int(by_key[(g, s, r, competitor)][field]) for r in range(5)]
                    individual.extend(ratios)
                    sampling_medians.append(statistics.median(ratios))
                graph_medians.append(statistics.median(sampling_medians))
            result[metric][competitor] = {
                "median_paired_ratio": statistics.median(graph_medians),
                "graph_medians": graph_medians,
                "trial_min_ratio": min(individual), "trial_max_ratio": max(individual),
                "trial_wins": sum(r < 1 for r in individual), "pairs": len(individual)}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--campaign", choices=("a", "b"), required=True)
    parser.add_argument("--released", action="store_true", help="operator has explicitly released this serial native slot")
    parser.add_argument("--preflight-only", action="store_true", help="validate all prerequisites and exit without creating campaign files or launching capture")
    args = parser.parse_args()
    if not args.released and not args.preflight_only:
        parser.error("explicit parent scheduling RELEASE is required before execution")
    root = args.repo.resolve(strict=True)
    folder = root / "benchmark/results/search-2026-10-13"
    stem = "attachment-confirmation-" + args.campaign
    raw = folder / (stem + "-timing.csv")
    manifest = folder / (stem + ".csv")
    analysis = folder / (stem + "-analysis")
    power = folder / (stem + "-power-audit")
    binary = root / "bin/large_stack/mst_search"
    controller = folder / (stem + "-controller.json")
    progress = folder / (stem + "-progress.jsonl")
    environment = folder / (stem + "-environment.jsonl")
    inhibition = folder / (stem + "-power-inhibition.json")
    capture_log = folder / (stem + "-capture.log")
    analyze_log = folder / (stem + "-analysis.log")
    audit_log = folder / (stem + "-power-audit.log")
    outputs = [raw, raw.with_suffix(".json"), raw.with_name(raw.stem + "_cases"),
               analysis, power, controller, progress, environment, inhibition,
               capture_log, analyze_log, audit_log]
    if any(p.exists() for p in outputs):
        raise ValueError("refusing to overwrite any campaign evidence")
    with manifest.open(newline="") as stream:
        cases = list(csv.DictReader(stream))
    expected = {(family, str(n), "16", "0") for family in ("leaf_hierarchy4", "leaf_distance4")
                for n in (65536, 262144, 524288, 1048576, 2097152)}
    expected.update((family, "2097152", "16", "0") for family in ("leaf_shuffled4", "leaf_random4"))
    fields = ("family", "n", "density", "intrusion_per_mille")
    if len(cases) != 12 or {tuple(r[k] for k in fields) for r in cases} != expected:
        raise ValueError("manifest differs from the frozen twelve-case confirmation grid")
    with (folder / "attachment-confirmation-a.csv").open(newline="") as stream:
        order_a = list(csv.DictReader(stream))
    with (folder / "attachment-confirmation-b.csv").open(newline="") as stream:
        order_b = list(csv.DictReader(stream))
    if order_b != list(reversed(order_a)):
        raise ValueError("campaign B is not the exact reverse of campaign A")
    declaration = frozen_declaration(root, folder)
    prior, prerequisite_hashes = validated_prior(root, folder / "attachment-large-timing.csv",
        folder / "attachment-large-analysis", 10, [5009], [149])
    if args.campaign == "b":
        a_controller_path = folder / "attachment-confirmation-a-controller.json"
        a_controller = json.loads(a_controller_path.read_text())
        for field, value in (("schema", "attachment_confirmation_controller_v1"),
            ("validation", "pass"), ("campaign", "attachment-confirmation-a"),
            ("capture_exit_status", 0), ("analysis_exit_status", 0),
            ("power_audit_exit_status", 0), ("power_audit_validation", "pass")):
            equal(a_controller.get(field), value, "campaign A controller " + field)
        if ("error" in a_controller or "termination_warning" in a_controller or
                a_controller.get("native_process_may_still_be_running")):
            raise ValueError("campaign A controller has an error or potentially active process")
        equal(a_controller.get("controller_sha256"), sha(__file__), "A/B controller source")
        bind_hashes(a_controller.get("retained_artifact_sha256"), "campaign A controller artifact")
        a_info, a_bound = validated_prior(root, folder / "attachment-confirmation-a-timing.csv",
            folder / "attachment-confirmation-a-analysis", 12, GRAPHS, SAMPLES)
        for field in ("binary_sha256", "binary_profile", "profile", "source_sha256",
                      "python_source_sha256", "build_recipe_sha256"):
            equal(a_info[field], prior[field], "A/large pilot " + field)
        a_audit_path = folder / "attachment-confirmation-a-power-audit/audit.json"
        a_audit = json.loads(a_audit_path.read_text())
        equal(a_audit.get("validation"), "pass", "campaign A power audit")
        equal(a_audit.get("checked_calls"), 2160, "campaign A power audit count")
        bind_hashes(a_audit.get("input_sha256"), "campaign A power audit inputs")
        prerequisite_hashes.update(a_bound)
        prerequisite_hashes.update({str(a_controller_path): sha(a_controller_path), str(a_audit_path): sha(a_audit_path)})
    if args.preflight_only:
        print(json.dumps({"schema": "attachment_confirmation_preflight_v1", "validation": "pass",
            "campaign": stem, "native_capture_started": False, "campaign_files_created": False,
            "controller_sha256": sha(__file__), "binary_sha256": sha(binary),
            "frozen_declaration_revision": DECLARATION_REVISION,
            "frozen_declaration_sha256": declaration, "prerequisite_sha256": prerequisite_hashes},
            indent=2, allow_nan=False))
        return
    source_inhibition = folder / "attachment-large-power-inhibition.json"
    inherited = json.loads(source_inhibition.read_text())
    save(inhibition, {"utc": now(), "campaign": stem,
        "idle_sleep_prevention_verified": False,
        "message": inherited["message"],
        "action": "Earlier idle and AC assertions failed. No fresh successful assertion is claimed; execute directly and audit logged events.",
        "inherited_from": str(source_inhibition), "inherited_sha256": sha(source_inhibition),
        "inherited_record": inherited})
    command = [sys.executable, str(root / "benchmark/run_mst_search.py"),
        "--binary", str(binary), "--manifest", str(manifest), "--output", str(raw),
        "--graph-seeds", ",".join(map(str, GRAPHS)),
        "--sampling-seeds", ",".join(map(str, SAMPLES)),
        "--repetitions", "5", "--warmups", "1", "--rss-limit-gib", "40", "--rss-poll-seconds", "2"]
    state = {"schema": "attachment_confirmation_controller_v1", "validation": "running",
        "campaign": stem, "started_utc": now(), "command": command,
        "controller_sha256": sha(__file__), "binary_sha256": sha(binary),
        "manifest_sha256": sha(manifest), "inhibition_json": str(inhibition),
        "frozen_declaration_revision": DECLARATION_REVISION,
        "frozen_declaration_sha256": declaration, "prerequisite_sha256": prerequisite_hashes,
        "environment_observations": str(environment), "progress_log": str(progress),
        "progress_is_provisional_until_strict_analysis": True}
    save(controller, state)
    process = None
    reported = set(); last_info = {}
    def interrupted(signum, frame):
        raise KeyboardInterrupt("controller received signal " + str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    try:
        with capture_log.open("x") as stream:
            process = subprocess.Popen(command, cwd=root, stdout=stream, stderr=subprocess.STDOUT)
            while True:
                fresh = False
                try:
                    last_info = json.loads(raw.with_suffix(".json").read_text()); fresh = True
                except (FileNotFoundError, json.JSONDecodeError):
                    pass
                info = last_info
                passed = [r for r in (info or {}).get("captures", []) if r.get("validation") == "pass"]
                completed = [c for c in (info or {}).get("case_order", [])
                             if sum(r["case_id"] == c for r in passed) == 6]
                event = {"utc": now(), "monotonic_ns": time.monotonic_ns(), "campaign": stem,
                    "completed_seed_pairs": len(passed), "total_seed_pairs": 72,
                    "completed_cases": len(completed), "total_cases": 12,
                    "metadata_snapshot_fresh": fresh,
                    "retained_flagged_calls": sum(r.get("flagged_calls", 0) for r in passed)}
                append(progress, event)
                print(json.dumps(event), flush=True)
                for case_id in completed:
                    if case_id not in reported:
                        result = {"utc": now(), "campaign": stem, "case_id": case_id,
                            "scope": "completed case, provisional until strict campaign analysis",
                            "ratios": completed_case_ratios(passed, case_id)}
                        append(progress, result); print(json.dumps(result), flush=True)
                        reported.add(case_id)
                append(environment, {**event,
                    "swap": observation(["/usr/sbin/sysctl", "vm.swapusage"]),
                    "power": observation(["/usr/bin/pmset", "-g", "batt"])})
                try:
                    status = process.wait(timeout=50)
                    break
                except subprocess.TimeoutExpired:
                    pass
        state["capture_exit_status"] = status
        save(controller, state)
        if type(status) is not int or status != 0:
            raise RuntimeError("capture failed; partial artifacts retained; no subsequent campaign permitted")
        info = json.loads(raw.with_suffix(".json").read_text())
        if (info.get("validation"), info.get("checked_timed_rows"), info.get("checked_warmup_rows")) != ("pass", 1800, 360):
            raise ValueError("capture did not pass the complete 1800+360-call matrix")
        for case_id in info["case_order"]:
            if case_id not in reported:
                result = {"utc": now(), "campaign": stem, "case_id": case_id,
                    "scope": "completed case, provisional until strict campaign analysis",
                    "ratios": completed_case_ratios(info["captures"], case_id)}
                append(progress, result); print(json.dumps(result), flush=True)
                reported.add(case_id)
        for kind, cmd, log in (
            ("analysis", [sys.executable, str(root / "benchmark/analyze_mst_search.py"),
                "--timing-csv", str(raw), "--manifest", str(manifest), "--output-dir", str(analysis)], analyze_log),
            ("power_audit", [sys.executable, str(root / "benchmark/audit_mst_search_power.py"),
                "--timing-csv", str(raw), "--query-pmset", "--inhibition-json", str(inhibition),
                "--output-dir", str(power)], audit_log)):
            print(kind + " started outside native measurement", flush=True)
            with log.open("x") as stream:
                result = subprocess.run(cmd, cwd=root, stdout=stream, stderr=subprocess.STDOUT)
            state[kind + "_command"] = cmd; state[kind + "_exit_status"] = result.returncode
            save(controller, state)
            if result.returncode:
                raise RuntimeError(kind + " failed; evidence retained; do not advance automatically")
        final_info, final_bound = validated_prior(root, raw, analysis, 12, GRAPHS, SAMPLES)
        for field in ("binary_sha256", "binary_profile", "profile", "source_sha256",
                      "python_source_sha256", "build_recipe_sha256"):
            equal(final_info[field], prior[field], "completed confirmation/large pilot " + field)
        final_audit = json.loads((power / "audit.json").read_text())
        equal(final_audit.get("checked_calls"), 2160, "completed power audit count")
        bind_hashes(final_audit.get("input_sha256"), "completed power audit inputs")
        state["analysis_bound_sha256"] = final_bound
        audit_validation = final_audit["validation"]
        state["power_audit_validation"] = audit_validation
        if audit_validation != "pass":
            raise ValueError("power-log audit is incomplete; retain results and inspect before campaign B")
        state.update(validation="pass", analysis_dir=str(analysis), power_audit_dir=str(power))
    except BaseException as error:
        state.update(validation="failed", error=repr(error))
        if process is not None and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                state["termination_warning"] = "Wrapper did not exit within 30 seconds; native processes may still be running. Do not start another capture until its owned process group is confirmed stopped."
                state["native_process_may_still_be_running"] = True
            except BaseException as cleanup_error:
                state["termination_warning"] = "Cleanup did not complete: " + repr(cleanup_error) + "; do not start another capture until the owned process group is confirmed stopped."
                state["native_process_may_still_be_running"] = True
        raise
    finally:
        state["finished_utc"] = now()
        state["retained_artifact_sha256"] = {str(p): sha(p) for p in
            (raw, raw.with_suffix(".json"), inhibition, progress, environment, capture_log, analyze_log, audit_log,
             analysis / "provenance.json", power / "audit.json") if p.is_file()}
        save(controller, state)
    print(json.dumps({"campaign": stem, "validation": state["validation"],
        "power_audit_validation": state["power_audit_validation"], "timed": 1800, "warmups": 360}), flush=True)


if __name__ == "__main__":
    main()
