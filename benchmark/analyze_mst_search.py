#!/usr/bin/env python3
"""Strict, standard-library analysis of one contemporaneous five-solver capture.

Validates every child, warmup, timed call, independent-certificate marker and RSS
observation before aggregating. Wall/CPU and paired ratios remain separate.
No observations are removed; repeated calls are not independent graph samples.
"""
import argparse
from collections import defaultdict
import copy
import csv
import datetime
import json
import math
import os
from pathlib import Path
import re
import statistics
import tempfile

import run_mst_search as capture

base = capture.base
METRICS = {"wall": "elapsed_ns", "cpu": "process_cpu_elapsed_ns"}
IDENTITY = ("case_id", "family", "n", "m", "density", "intrusion_per_mille")
HELPER_NAMES = {"run_mst_search.py", "analyze_mst_search.py", "run_crossover.py",
                "analyze_continuation.py", "crossover_clocks.py", "run_crossover_baselines.py"}
ATTACHMENT_NATIVE_FILE = "benchmark/core_attachment_fixtures.hpp"
NATIVE_FILES = {f"{name}/{name}.{suffix}" for name in ("kkt", "boruvka", "kruskal", "prim", "lca", "union_find", "graph_utils")
                for suffix in ("cpp", "hpp")} | {"common/edge.hpp", "common/work_stats.hpp", "kkt/random_sampling.hpp",
                "verifier/verifier_v2.cpp", "verifier/verifier_v2.hpp", "verifier/median_table.hpp",
                "benchmark/mst_search.cpp", "benchmark/search_fixtures.hpp", "benchmark/crossover_fixtures.hpp",
                "benchmark/continuation_fixtures.hpp", "benchmark/graph_fixtures.hpp", "benchmark/mst_certificate.hpp",
                ATTACHMENT_NATIVE_FILE}


def equal(record, field, expected, context):
    def same(left, right):
        if type(left) is not type(right): return False
        if type(left) is dict:
            return left.keys() == right.keys() and all(same(left[k], right[k]) for k in left)
        if type(left) is list:
            return len(left) == len(right) and all(same(a, b) for a, b in zip(left, right))
        return left == right
    base.require(field in record and same(record[field], expected),
                 f"{context}: incorrect {field}")


def read_json(path):
    return capture.clocks.parse_json(path.read_text())


def digest(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def hash_check(path, expected):
    base.require(digest(expected) and capture.sha(path) == expected, f"hash mismatch: {path}")


def inventory(value, context):
    base.require(type(value) is dict and value and all(type(p) is str and p and digest(v)
                 for p, v in value.items()), context + ": invalid hash inventory")


def positive(value, context):
    base.require(type(value) in (int, float) and math.isfinite(value) and value > 0,
                 context + ": expected a positive finite number")


def timestamp(value):
    base.require(type(value) is str, "timestamp must be text")
    result = datetime.datetime.fromisoformat(value)
    base.require(result.utcoffset() == datetime.timedelta(0), "timestamp must be UTC")
    return result


def monotonic_interval(record):
    start, finish = record.get("started_monotonic_ns"), record.get("finished_monotonic_ns")
    base.require(type(start) is int and type(finish) is int and 0 < start < finish,
                 "invalid monotonic capture interval")
    return start, finish


def bank(value, context):
    base.require(type(value) is list and value and all(type(v) is int and 0 <= v < 2**32 for v in value)
                 and len(value) == len(set(value)), context + ": invalid seed bank")
    return value


def check_rss(path, recorded, rule):
    observations = [capture.clocks.parse_json(line) for line in path.read_text().splitlines()]
    base.require(observations, "missing resource observations")
    consecutive = unavailable = nonempty = 0
    peaks = []; previous = -1; group = None
    for row in observations:
        base.require(type(row) is dict, "RSS observation must be an object")
        timestamp(row.get("utc"))
        base.require(type(row.get("monotonic_ns")) is int and row["monotonic_ns"] > previous,
                     "RSS monotonic clock reversed or duplicated")
        base.require(recorded["started_monotonic_ns"] <= row["monotonic_ns"] <= recorded["finished_monotonic_ns"],
                     "RSS observation lies outside its child interval")
        previous = row["monotonic_ns"]
        base.require(type(row.get("process_group")) is int and row["process_group"] > 0,
                     "invalid RSS process group")
        if group is None: group = row["process_group"]
        base.require(group == row["process_group"], "resource observations changed process group")
        if row.get("validation") == "unavailable":
            base.require(set(row) == {"utc", "monotonic_ns", "process_group", "validation", "error"}
                         and type(row["error"]) is str and row["error"], "invalid unavailable RSS observation")
            consecutive += 1; unavailable += 1
            base.require(consecutive < 3, "successful capture contains three consecutive RSS failures")
            continue
        equal(row, "validation", "pass", "resource observation")
        base.require(set(row) == {"utc", "monotonic_ns", "process_group", "validation", "members", "rss_kib"}
                     and type(row["members"]) is list, "invalid resource observation fields")
        consecutive = 0; members = row["members"]; pids = set()
        for member in members:
            base.require(type(member) is dict and set(member) == {"pid", "rss_kib", "command"}
                         and type(member["pid"]) is int and member["pid"] > 0 and member["pid"] not in pids
                         and type(member["rss_kib"]) is int and member["rss_kib"] >= 0
                         and type(member["command"]) is str and member["command"], "invalid RSS process member")
            pids.add(member["pid"])
        equal(row, "rss_kib", sum(member["rss_kib"] for member in members), "resource observation")
        base.require(row["rss_kib"] <= rule["rss_limit_kib"], "successful capture exceeds RSS ceiling")
        peaks.append(row["rss_kib"]); nonempty += bool(members)
    for field, expected in (("rss_observations", len(observations)), ("rss_unavailable", unavailable),
                             ("rss_nonempty_observations", nonempty),
                             ("sampled_peak_rss_kib", max(peaks, default=None))):
        equal(recorded, field, expected, "resource capture")
    return observations


def load(timing_path, manifest_path=None):
    timing_path = timing_path.resolve(strict=True)
    metadata_path = timing_path.with_suffix(".json")
    info = read_json(metadata_path)
    base.require(type(info) is dict, "metadata must be an object")
    for field, expected in (("schema", "mst_search_capture_v1"), ("validation", "pass"),
                             ("rows_removed", 0), ("rows_adjusted", 0)):
        equal(info, field, expected, "capture")
    base.require("error" not in info, "failed capture cannot be summarized")
    for field in ("revision", "profile", "platform", "machine", "working_directory", "binary",
                  "schedule", "timing_boundary", "certificate_scope"):
        base.require(type(info.get(field)) is str and info[field], "missing capture " + field)
    base.require(digest(info.get("binary_sha256")), "invalid captured binary hash")
    inventory(info.get("source_sha256"), "C++ source inventory")
    inventory(info.get("python_source_sha256"), "Python source inventory")
    base.require({Path(p).name for p in info["python_source_sha256"]} == HELPER_NAMES
                 and len(info["python_source_sha256"]) == len(HELPER_NAMES), "incorrect Python helper inventory")
    # Keep old frozen campaigns analyzable; they predate the attachment header.
    # The extra fixture source is mandatory for every attachment campaign below.
    base.require(NATIVE_FILES-{ATTACHMENT_NATIVE_FILE} <= set(info["source_sha256"]),
                 "missing native search/production sources")
    inventory(info.get("build_recipe_sha256"), "build recipe")
    base.require(set(info["build_recipe_sha256"]) == {"Makefile"}, "incorrect build recipe inventory")
    profile = info.get("binary_profile")
    base.require(type(profile) is dict and type(profile.get("file_description")) is str and
                 "Mach-O 64-bit executable arm64" in profile["file_description"], "invalid binary architecture profile")
    equal(profile, "main_stack_bytes", 536870912, "binary profile")
    base.require(type(profile.get("otool_load_commands")) is str and
                 re.findall(r"cmd LC_MAIN\s+cmdsize \d+\s+entryoff \d+\s+stacksize (\d+)",
                            profile["otool_load_commands"]) == ["536870912"], "inconsistent Mach-O stack record")
    timestamp(info.get("started_utc")); timestamp(info.get("finished_utc"))
    start, finish = monotonic_interval(info)
    positive(info.get("monotonic_elapsed_seconds"), "capture duration")
    manifest_path = (manifest_path or Path(info["manifest"])).resolve(strict=True)
    base.require(str(manifest_path) == info["manifest"], "manifest path differs from capture")
    hash_check(manifest_path, info.get("manifest_sha256")); hash_check(timing_path, info.get("output_sha256"))
    cases = capture.load_manifest(manifest_path)
    if any(spec["family"] in capture.ATTACHMENT_FAMILIES for spec in cases.values()):
        base.require(ATTACHMENT_NATIVE_FILE in info["source_sha256"], "missing attachment fixture source")
    equal(info, "case_order", list(cases), "capture")
    equal(info, "algorithms", list(capture.ALGORITHMS), "capture")
    graph_seeds = bank(info.get("graph_seeds"), "graph seeds")
    sampling_seeds = bank(info.get("sampling_seeds"), "sampling seeds")
    reps, warmups = info.get("repetitions"), info.get("warmups")
    capture.protocol(reps, warmups)
    rule = info.get("resource_rule")
    base.require(type(rule) is dict and type(rule.get("rss_limit_kib")) is int and
                 1024**2 <= rule["rss_limit_kib"] <= 40*1024**2, "invalid resource ceiling")
    positive(rule.get("poll_seconds"), "resource poll interval")
    base.require(.25 <= rule["poll_seconds"] <= 60, "invalid resource poll interval")
    matrix = [(case, g, s) for case in cases for g in graph_seeds for s in sampling_seeds]
    base.require(type(info.get("captures")) is list and len(info["captures"]) == len(matrix), "incomplete child matrix")
    rows, diagnostics, resources = [], [], []
    inputs = {str(timing_path): capture.sha(timing_path), str(metadata_path): capture.sha(metadata_path),
              str(manifest_path): capture.sha(manifest_path)}
    previous_finish = start
    for index, ((case, g, s), item) in enumerate(zip(matrix, info["captures"]), 1):
        context = f"child {index}"
        for field, expected in (("case_id", case), ("graph_seed", g), ("kkt_seed", s), ("exit_status", 0),
                                 ("interruption", None), ("validation", "pass"), ("rows", 5*(reps+warmups))):
            equal(item, field, expected, context)
        timestamp(item.get("started_utc")); timestamp(item.get("finished_utc"))
        child_start, child_finish = monotonic_interval(item)
        base.require(previous_finish <= child_start < child_finish <= finish, "overlapping or invalid monotonic child interval")
        previous_finish = child_finish
        positive(item.get("monotonic_elapsed_seconds"), context + " duration")
        raw = timing_path.with_name(timing_path.stem + "_cases") / f"{index:04d}_{case}_g{g}_s{s}.csv"
        log, rss = raw.with_suffix(".log"), raw.with_suffix(".rss.jsonl")
        for field, path, hash_field in (("csv", raw, "output_sha256"), ("log", log, "log_sha256"), ("rss_log", rss, "rss_sha256")):
            equal(item, field, str(path), context); hash_check(path, item.get(hash_field)); inputs[str(path)] = capture.sha(path)
        spec = cases[case]
        command = [info["binary"], "--family", spec["family"], "--n", str(spec["n"]), "--density", str(spec["density"]),
                   "--graph-seed", str(g), "--kkt-seed", str(s), "--repetitions", str(reps), "--warmups", str(warmups)]
        equal(item, "command", command, context)
        child_rows, child_diagnostics = capture.check_rows(raw, spec, g, s, reps, warmups)
        certificate = capture.check_certificate(log, child_rows)
        equal(item, "certificate", certificate, context)
        equal(item, "flagged_calls", sum(bool(r["diagnostic_flags"]) for r in child_diagnostics), context)
        check_rss(rss, item, rule)
        resources.append({"case_id": case, "graph_seed": g, "kkt_seed": s,
            **{key: item[key] for key in ("rss_observations", "rss_unavailable", "rss_nonempty_observations", "sampled_peak_rss_kib")},
            "rss_ceiling_kib": rule["rss_limit_kib"], "sampling_scope": "periodic process-group RSS sum; not continuous peak"})
        rows.extend(child_rows); diagnostics.extend(child_diagnostics)
    capture.check_fingerprints(rows)
    equal(info, "capture_clock_flags", capture.capture_clock_flags(info), "capture")
    actual = [raw for _, raw in base.read_csv(timing_path, capture.FIELDS)]
    expected = [{field: str(row[field]) for field in capture.FIELDS} for row in rows]
    base.require(actual == expected, "combined CSV is not the exact ordered concatenation of successful children")
    equal(info, "call_diagnostics", diagnostics, "capture")
    for field, expected in (("checked_rows", len(rows)), ("checked_timed_rows", len(matrix)*reps*5),
                             ("checked_warmup_rows", len(matrix)*warmups*5),
                             ("flagged_calls", sum(bool(r["diagnostic_flags"]) for r in diagnostics))):
        equal(info, field, expected, "capture")
    return info, cases, rows, diagnostics, resources, inputs


def aggregate(rows):
    """Median repetitions, then sampling seeds, then graph seeds; never pool graphs."""
    timed = [row for row in rows if row["phase"] == "timed"]
    case_info = {row["case_id"]: {f: row[f] for f in IDENTITY} for row in timed}
    summaries, graph_rows, comparisons, graph_comparisons, pairs = [], [], [], [], []
    for metric, field in METRICS.items():
        grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        blocks = defaultdict(dict)
        for row in timed:
            grouped[(row["case_id"], row["algorithm"])][row["graph_seed"]][row["kkt_seed"]].append(row[field])
            blocks[(row["case_id"], row["graph_seed"], row["kkt_seed"], row["repetition"])][row["algorithm"]] = row[field]
        for (case, algorithm), graphs in grouped.items():
            medians = []; raw = []
            for g, samples in graphs.items():
                graph_values = [v for values in samples.values() for v in values]
                median = statistics.median(statistics.median(values) for values in samples.values())
                medians.append(median); raw.extend(graph_values)
                graph_rows.append({**case_info[case], "metric": metric, "algorithm": algorithm, "graph_seed": g,
                    "median_ns": median, "trial_min_ns": min(graph_values), "trial_max_ns": max(graph_values),
                    "sampling_seeds": len(samples), "timed_calls": len(graph_values)})
            summaries.append({**case_info[case], "metric": metric, "algorithm": algorithm,
                "median_ns": statistics.median(medians), "graph_min_ns": min(medians), "graph_max_ns": max(medians),
                "trial_min_ns": min(raw), "trial_max_ns": max(raw), "graph_seeds": len(graphs), "timed_calls": len(raw)})
        ratios = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        for (case, g, s, rep), values in blocks.items():
            base.require(set(values) == set(capture.ALGORITHMS), "incomplete paired timing block")
            for competitor in capture.ALGORITHMS[1:]:
                ratio = values["kkt"] / values[competitor]
                ratios[(case, competitor)][g][s].append(ratio)
                pairs.append({**case_info[case], "metric": metric, "competitor": competitor, "graph_seed": g,
                    "kkt_seed": s, "repetition": rep, "kkt_ns": values["kkt"], "competitor_ns": values[competitor],
                    "kkt_over_competitor": ratio})
        for (case, competitor), graphs in ratios.items():
            graph_medians = []; raw = []
            for g, samples in graphs.items():
                values = [v for samples_values in samples.values() for v in samples_values]
                median = statistics.median(statistics.median(v) for v in samples.values())
                graph_medians.append(median); raw.extend(values)
                graph_comparisons.append({**case_info[case], "metric": metric, "competitor": competitor, "graph_seed": g,
                    "median_paired_ratio": median, "trial_min_ratio": min(values), "trial_max_ratio": max(values),
                    "individual_wins": sum(v < 1 for v in values), "individual_losses": sum(v > 1 for v in values),
                    "individual_ties": sum(v == 1 for v in values), "pairs": len(values)})
            comparisons.append({**case_info[case], "metric": metric, "competitor": competitor,
                "median_paired_ratio": statistics.median(graph_medians), "graph_min_ratio": min(graph_medians),
                "graph_max_ratio": max(graph_medians), "trial_min_ratio": min(raw), "trial_max_ratio": max(raw),
                "individual_wins": sum(v < 1 for v in raw), "individual_losses": sum(v > 1 for v in raw),
                "individual_ties": sum(v == 1 for v in raw), "graph_seeds": len(graphs), "pairs": len(raw)})
    return {"summary": summaries, "graph_summary": graph_rows, "comparisons": comparisons,
            "graph_comparisons": graph_comparisons, "paired_ratios": pairs}


def write_csv(path, rows):
    base.require(rows, "refusing empty output table")
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def report(info, cases, tables):
    rows = tables["comparisons"]
    text = ["# Five-solver capture", "", f"Strict validation passed for {len(cases)} cases, "
        f"{len(info['graph_seeds'])} graph seeds and {len(info['sampling_seeds'])} sampling seeds: "
        f"{info['checked_timed_rows']} timed calls and {info['checked_warmup_rows']} retained warmup calls. "
        f"Each child has {info['repetitions']} timed repetitions and {info['warmups']} warmups per algorithm.", "",
        "All five positions are balanced within each timed seed pair. Every native reference has an independent MST "
        "certificate; every returned result must match that exact unique MST. Warmups are validated and retained, "
        "but excluded from timing summaries.", "",
        "Ratios below one favor KKT. Each ratio is paired within the same graph, sampling seed and repetition, then "
        "aggregated by median over repetitions, sampling seeds and graphs in that order. Runtime summaries apply "
        "the same hierarchy separately to each algorithm; a ratio of those summaries is a different statistic. "
        "Graph and individual-trial ranges are descriptive spreads, not confidence intervals. Sampling seeds repeat "
        "identical inputs for deterministic competitors; they are not additional graph samples.", "",
        "`compacting_boruvka` repeatedly uses production contraction; `boruvka` is the original public baseline. "
        "No other campaign is mixed into these comparisons, and no finite result establishes asymptotic dominance.", "",
        f"{info['flagged_calls']} calls carry diagnostic clock flags, and {len(info['capture_clock_flags'])} "
        "capture/child UTC interval flags are retained in provenance; all calls remain in every relevant table. "
        "Wall and process-CPU results are separate. Resource observations are periodic sums of process-group RSS "
        "in KiB, not continuous peaks or unique physical footprints. Polling itself can perturb measurements; "
        "the same rule is applied throughout this campaign.", "",
        "| Case | Metric | KKT / compacting Borůvka | KKT / Kruskal | KKT / Prim | KKT / original Borůvka |", "|---|---|---:|---:|---:|---:|"]
    index = {(r["case_id"], r["metric"], r["competitor"]): r for r in rows}
    for case in cases:
        for metric in METRICS:
            values = [index[(case, metric, a)]["median_paired_ratio"] for a in capture.ALGORITHMS[1:]]
            text.append(f"| {case} | {metric} | " + " | ".join(f"{v:.4f}" for v in values) + " |")
    text.extend(["", "Every individual ratio, including losses, is in [paired_ratios.csv](paired_ratios.csv). "
        "[comparisons.csv](comparisons.csv) and [graph_comparisons.csv](graph_comparisons.csv) retain spreads and "
        "win/loss counts. [summary.csv](summary.csv) reports separate algorithm runtimes in nanoseconds. "
        "[validated_calls.csv](validated_calls.csv) includes warmups; [call_diagnostics.csv](call_diagnostics.csv) "
        "contains every clock flag. [resources.csv](resources.csv) reports sampled resource observations.", "",
        f"Raw capture: [{Path(info['raw_csv']).name}]({info['raw_csv_link']}). "
        "Exact raw/child/log/manifest hashes and the captured source/binary inventories are retained in "
        "[provenance.json](provenance.json).", ""])
    return "\n".join(text)


def self_test():
    """Bounded semantic checks; no native execution and no performance claim."""
    results = {"validation": "pass", "positive_checks": [], "rejected_mutations": []}
    with tempfile.TemporaryDirectory(prefix="mst-search-check-") as folder:
        folder = Path(folder).resolve(); path = folder/"rows.csv"; log = folder/"rows.log"
        spec = {"family": "hierarchical_path", "n": 32, "density": 4, "intrusion_per_mille": 0, "m": 128}
        spec["case_id"] = base.case_id(spec); rows = []; cpu = 0; utc = 1_000_000_000
        for phase, count in (("warmup", 1), ("timed", 5)):
            for rep in range(count):
                for order in range(5):
                    algorithm = capture.ALGORITHMS[(order+rep)%5]; duration = 1000*(capture.ALGORITHMS.index(algorithm)+1)
                    rows.append({**spec, "graph_seed": 17, "kkt_seed": 101, "input_fingerprint": 9,
                        "topology_fingerprint": 8, "phase": phase, "repetition": rep, "order": order, "warmups": 1,
                        "algorithm": algorithm, "elapsed_ns": duration, "utc_start_ns": utc, "utc_end_ns": utc+duration,
                        "process_cpu_start_ns": cpu, "process_cpu_end_ns": cpu+duration,
                        "process_cpu_elapsed_ns": duration, "validation": "pass"})
                    cpu += duration+10; utc += duration+10
        def save(values):
            with path.open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=capture.FIELDS); writer.writeheader(); writer.writerows(values)
        def reject(name, action):
            try: action()
            except (ValueError, KeyError, TypeError): results["rejected_mutations"].append(name)
            else: raise AssertionError("accepted malformed " + name)
        save(rows); parsed, _ = capture.check_rows(path, spec, 17, 101, 5, 1)
        certificate = {f: parsed[0][f] for f in capture.CERTIFICATE_FIELDS}
        diagnostic = "generation_seconds=0.001 reference_certificate_seconds=0.002\n"
        log.write_text(diagnostic+capture.CERTIFICATE_PREFIX+json.dumps(certificate)+"\n")
        capture.check_certificate(log, parsed); results["positive_checks"].append("complete calls and exact certificate")
        results["positive_checks"].append("benign generation/certificate-duration diagnostic retained")
        tables = aggregate(parsed)
        base.require(all(r["median_paired_ratio"] == 1/(capture.ALGORITHMS.index(r["competitor"])+1)
                         for r in tables["comparisons"]), "paired arithmetic self-test failed")
        results["positive_checks"].append("independent expected paired ratios")
        hierarchical = []
        for g, values in enumerate(((1, 2, 100), (3, 4, 5), (6, 7, 8))):
            for s, value in enumerate(values):
                for row in parsed:
                    if row["phase"] != "timed": continue
                    duration = value if row["algorithm"] == "kkt" else 10
                    hierarchical.append({**row, "graph_seed": g, "kkt_seed": s,
                                         "elapsed_ns": duration, "process_cpu_elapsed_ns": duration})
        hierarchy_table = aggregate(hierarchical)
        base.require(all(r["median_ns"] == 4 for r in hierarchy_table["summary"] if r["algorithm"] == "kkt") and
                     all(r["median_paired_ratio"] == .4 for r in hierarchy_table["comparisons"]),
                     "hierarchical median accidentally pooled graph samples")
        results["positive_checks"].append("graph/sampling medians differ from pooled median")
        paired = []
        for row in parsed:
            if row["phase"] != "timed": continue
            duration = row["repetition"]+1 if row["algorithm"] == "kkt" else (5, 1, 2, 3, 4)[row["repetition"]]
            paired.append({**row, "elapsed_ns": duration, "process_cpu_elapsed_ns": duration})
        paired_table = aggregate(paired)
        base.require(all(r["median_ns"] == 3 for r in paired_table["summary"]) and
                     all(r["median_paired_ratio"] == 4/3 for r in paired_table["comparisons"]),
                     "paired ratio was replaced with a ratio of separate medians")
        results["positive_checks"].append("paired ratio differs from ratio of separate medians")
        for name, mutate in (("missing row", lambda r: r.pop()), ("duplicate row", lambda r: r.append(r[-1])),
            ("wrong order", lambda r: r[7].update(algorithm="kkt")),
            ("CPU duration", lambda r: r[7].update(process_cpu_elapsed_ns=1)),
            ("failed validation", lambda r: r[7].update(validation="fail")),
            ("fingerprint mismatch", lambda r: r[7].update(input_fingerprint=99)),
            ("unbalanced repetitions", lambda r: r[7].update(repetition=5))):
            changed = copy.deepcopy(rows); mutate(changed); save(changed)
            reject(name, lambda: capture.check_rows(path, spec, 17, 101, 5, 1))
        for name, changed in (("missing certificate", None), ("boolean certificate", {**certificate, "graph_seed": True}),
                               ("extra certificate field", {**certificate, "extra": 1})):
            log.write_text("" if changed is None else capture.CERTIFICATE_PREFIX+json.dumps(changed)+"\n")
            reject(name, lambda: capture.check_certificate(log, parsed))
        first = {**rows[0], "family": "lifted_hierarchy2", "case_id": "a"}
        second = {**rows[0], "family": "lifted_distance4", "case_id": "b", "topology_fingerprint": 17}
        capture.check_fingerprints([first, second]); results["positive_checks"].append("lift factors not conflated")
        second.update(family="lifted_distance2")
        reject("paired lifted topology", lambda: capture.check_fingerprints([first, second]))
        for family, n, d in (("lifted_hierarchy4", 32, 4), ("lifted_distance4", 64, 31), ("gnm_random", 32, 4),
                             ("grid2d_random", 64, 1), ("not_a_fixture", 64, 4)):
            manifest = folder/"manifest.csv"
            manifest.write_text("family,n,density,intrusion_per_mille\n"+f"{family},{n},{d},0\n")
            reject("manifest "+family, lambda: capture.load_manifest(manifest))
        # Attachment-domain checks are independent of native helper metadata.
        # At b=4,n=64,d=4, E=208 exceeds C(16,2)=120 and is NOT feasible;
        # n=128,d=4 instead has E=416 <= C(32,2)=496. At b=16,n=64,d=1,
        # E=4 <= C(4,2)=6, while n=32,d=1 has E=2 > C(2,2)=1.
        for family in capture.ATTACHMENT_FAMILIES:
            b = 16 if family.endswith("16") else 4
            for n, d in (((32, 1), (64, 2), (128, 4)) if b == 4 else ((64, 1), (1024, 2), (2048, 4))):
                manifest.write_text("family,n,density,intrusion_per_mille\n"+f"{family},{n},{d},0\n")
                parsed_case = next(iter(capture.load_manifest(manifest).values()))
                q = n//b; expected_external = n*d-n+q
                base.require(parsed_case["m"] == n*d and expected_external == q*(b*(d-1)+1)
                             and q >= 2*b*(d-1)+3, "attachment count identity failed")
        results["positive_checks"].append("all sixteen attachment families and independent core count identity")
        for family, n, d, p in (("leaf_hierarchy4", 32, 2, 0), ("community_distance4", 64, 4, 0),
                ("leaf_random16", 32, 1, 0), ("community_hierarchy16", 512, 2, 0),
                ("leaf_distance16", 256, 16, 0), ("community_random16", 2**22, 64, 0),
                ("leaf_hierarchy4", 128, 4, 1), ("community_random8", 128, 4, 0)):
            manifest.write_text("family,n,density,intrusion_per_mille\n"+f"{family},{n},{d},{p}\n")
            reject(f"attachment domain {family}/{n}/{d}/{p}", lambda: capture.load_manifest(manifest))
        # Accept the global edge budget exactly without allocating any graph.
        for family in capture.ATTACHMENT_FAMILIES:
            manifest.write_text("family,n,density,intrusion_per_mille\n"+f"{family},{2**22},32,0\n")
            base.require(next(iter(capture.load_manifest(manifest).values()))["m"] == 2**27,
                         "valid maximum attachment edge budget rejected")
        results["positive_checks"].append("attachment maximum count boundary without graph allocation")
        leaf = {**rows[0], "family": "leaf_hierarchy4", "case_id": "leaf_h"}
        leaf_twin = {**rows[0], "family": "leaf_distance4", "case_id": "leaf_d", "input_fingerprint": 10}
        leaf_shuffled = {**rows[0], "family": "leaf_shuffled4", "case_id": "leaf_s", "input_fingerprint": 11}
        leaf_random = {**rows[0], "family": "leaf_random4", "case_id": "leaf_r", "input_fingerprint": 12}
        community = {**rows[0], "family": "community_hierarchy4", "case_id": "community_h", "topology_fingerprint": 88}
        bigger = {**rows[0], "family": "leaf_hierarchy16", "case_id": "leaf16", "topology_fingerprint": 188}
        capture.check_fingerprints([leaf, leaf_twin, leaf_shuffled, leaf_random, community, bigger])
        results["positive_checks"].append("attachment endpoint modes and block sizes are separate topology groups")
        leaf_twin["topology_fingerprint"] = 89
        reject("attachment paired topology", lambda: capture.check_fingerprints([leaf, leaf_twin]))
        leaf_shuffled["topology_fingerprint"] = 90
        reject("attachment shuffled-core paired topology", lambda: capture.check_fingerprints([leaf, leaf_shuffled]))
        # A complete synthetic evidence bundle exercises the provenance loader;
        # mutants below recompute hashes so rejection is semantic, not stale SHA.
        manifest.write_text("family,n,density,intrusion_per_mille\nhierarchical_path,32,4,0\n")
        combined = folder/"capture.csv"; child_folder = folder/"capture_cases"; child_folder.mkdir()
        raw = child_folder/f"0001_{spec['case_id']}_g17_s101.csv"
        child_log, rss_log = raw.with_suffix(".log"), raw.with_suffix(".rss.jsonl")
        save(rows); combined.write_bytes(path.read_bytes()); raw.write_bytes(path.read_bytes())
        child_log.write_text(diagnostic+capture.CERTIFICATE_PREFIX+json.dumps(certificate)+"\n")
        observation = {"utc": "2026-10-13T00:00:01+00:00", "monotonic_ns": 1500, "process_group": 7,
            "validation": "pass", "members": [{"pid": 7, "rss_kib": 1024, "command": "synthetic"}], "rss_kib": 1024}
        rss_log.write_text(json.dumps(observation)+"\n")
        _, diag = capture.check_rows(raw, spec, 17, 101, 5, 1)
        child = {"case_id": spec["case_id"], "graph_seed": 17, "kkt_seed": 101, "exit_status": 0,
            "interruption": None, "validation": "pass", "rows": 30,
            "started_utc": "2026-10-13T00:00:01+00:00", "finished_utc": "2026-10-13T00:00:02+00:00",
            "started_monotonic_ns": 1000, "finished_monotonic_ns": 2000,
            "monotonic_elapsed_seconds": 1, "csv": str(raw), "log": str(child_log), "rss_log": str(rss_log),
            "output_sha256": capture.sha(raw), "log_sha256": capture.sha(child_log), "rss_sha256": capture.sha(rss_log),
            "command": ["/synthetic", "--family", spec["family"], "--n", "32", "--density", "4", "--graph-seed", "17",
                        "--kkt-seed", "101", "--repetitions", "5", "--warmups", "1"],
            "certificate": certificate, "flagged_calls": 0, "rss_observations": 1, "rss_unavailable": 0,
            "rss_nonempty_observations": 1, "sampled_peak_rss_kib": 1024}
        info = {"schema": "mst_search_capture_v1", "validation": "pass", "rows_removed": 0, "rows_adjusted": 0,
            "revision": "synthetic", "profile": "synthetic validation only", "platform": "synthetic", "machine": "arm64",
            "working_directory": str(folder), "binary": "/synthetic", "schedule": "synthetic", "timing_boundary": "synthetic",
            "certificate_scope": "synthetic", "binary_sha256": "a"*64,
            "source_sha256": {p: "b"*64 for p in NATIVE_FILES},
            "python_source_sha256": {"/synthetic/"+p: "c"*64 for p in HELPER_NAMES},
            "build_recipe_sha256": {"Makefile": "d"*64},
            "binary_profile": {"file_description": "Mach-O 64-bit executable arm64", "main_stack_bytes": 536870912,
                               "otool_load_commands": "cmd LC_MAIN\ncmdsize 24\nentryoff 0\nstacksize 536870912"},
            "started_utc": "2026-10-13T00:00:00+00:00", "finished_utc": "2026-10-13T00:00:03+00:00",
            "started_monotonic_ns": 100, "finished_monotonic_ns": 3000,
            "monotonic_elapsed_seconds": 3, "manifest": str(manifest), "manifest_sha256": capture.sha(manifest),
            "output_sha256": capture.sha(combined), "case_order": [spec["case_id"]], "algorithms": list(capture.ALGORITHMS),
            "graph_seeds": [17], "sampling_seeds": [101], "repetitions": 5, "warmups": 1,
            "resource_rule": {"rss_limit_kib": 40*1024**2, "poll_seconds": 2}, "captures": [child],
            "call_diagnostics": diag, "checked_rows": 30, "checked_timed_rows": 25, "checked_warmup_rows": 5,
            "flagged_calls": 0, "capture_clock_flags": []}
        sidecar = combined.with_suffix(".json")
        capture.write_json(sidecar, info); load(combined)
        results["positive_checks"].append("complete provenance, clocks, certificate and resource bundle")
        old_inventory = copy.deepcopy(info)
        old_inventory["source_sha256"].pop(ATTACHMENT_NATIVE_FILE)
        capture.write_json(sidecar, old_inventory); load(combined)
        results["positive_checks"].append("old non-attachment capture remains valid without new fixture header")
        reversed_utc = copy.deepcopy(info)
        reversed_utc["captures"][0]["finished_utc"] = "2026-10-12T23:59:59+00:00"
        reversed_utc["capture_clock_flags"] = capture.capture_clock_flags(reversed_utc)
        capture.write_json(sidecar, reversed_utc); load(combined)
        results["positive_checks"].append("UTC reversal retained and flagged; monotonic sequence intact")
        for name, mutate in (("failed capture metadata", lambda r: r.update(validation="failed")),
            ("missing capture child", lambda r: r.update(captures=[])),
            ("boolean seed metadata", lambda r: r.update(graph_seeds=[True])),
            ("recorded certificate boolean", lambda r: r["captures"][0]["certificate"].update(graph_seed=True)),
            ("ordinary stack profile", lambda r: r["binary_profile"].update(main_stack_bytes=0)),
            ("missing production source", lambda r: r["source_sha256"].pop("kkt/kkt.cpp")),
            ("incorrect raw count", lambda r: r.update(checked_rows=29)),
            ("monotonic child reversal", lambda r: r["captures"][0].update(finished_monotonic_ns=999)),
            ("RSS peak mismatch", lambda r: r["captures"][0].update(sampled_peak_rss_kib=1023))):
            changed = copy.deepcopy(info); mutate(changed); capture.write_json(sidecar, changed)
            reject(name, lambda: load(combined))
        for name, mutate in (("RSS sum", lambda r: r.update(rss_kib=1000)),
            ("RSS boolean member", lambda r: r["members"][0].update(rss_kib=True)),
            ("RSS over ceiling", lambda r: (r.update(rss_kib=41*1024**2), r["members"][0].update(rss_kib=41*1024**2))),
            ("RSS monotonic invalid", lambda r: r.update(monotonic_ns=False))):
            changed = copy.deepcopy(observation); mutate(changed); rss_log.write_text(json.dumps(changed)+"\n")
            metadata = copy.deepcopy(info); metadata["captures"][0]["rss_sha256"] = capture.sha(rss_log)
            capture.write_json(sidecar, metadata); reject(name, lambda: load(combined))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timing-csv", type=Path); parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output-dir", type=Path); parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2)); return
    base.require(args.timing_csv is not None and args.output_dir is not None, "--timing-csv and --output-dir are required")
    info, cases, rows, diagnostics, resources, inputs = load(args.timing_csv, args.manifest)
    output = args.output_dir.resolve()
    base.require(not output.exists(), "refusing to overwrite analysis evidence")
    tables = aggregate(rows); output.mkdir(parents=True)
    tables.update(validated_calls=rows, resources=resources,
        call_diagnostics=[{**r, "diagnostic_flags": ";".join(r["diagnostic_flags"])} for r in diagnostics])
    for name, values in tables.items(): write_csv(output/(name+".csv"), values)
    info["raw_csv"] = str(args.timing_csv.resolve())
    info["raw_csv_link"] = os.path.relpath(args.timing_csv.resolve(), output)
    (output/"report.md").write_text(report(info, cases, tables))
    provenance = {"schema": "mst_search_analysis_v1", "validation": "pass", "cases": len(cases),
        "checked_rows": len(rows), "timed_rows": info["checked_timed_rows"], "warmup_rows": info["checked_warmup_rows"],
        "rows_removed": 0, "rows_adjusted": 0, "input_sha256": inputs,
        "capture_metadata": info, "analysis_source_sha256": capture.helpers(),
        "aggregation": "median repetitions, then sampling seeds, then graph seeds; paired ratios aggregated independently",
        "derived_sha256": {p.name: capture.sha(p) for p in sorted(output.iterdir()) if p.is_file()}}
    capture.write_json(output/"provenance.json", provenance)
    print(f"Validated {len(cases)} cases; {len(rows)} calls; {len(tables['paired_ratios'])} wall/CPU pairs")


if __name__ == "__main__":
    main()
