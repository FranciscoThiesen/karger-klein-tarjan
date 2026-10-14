#!/usr/bin/env python3
"""Strict untimed attachment-work/model join; standard library only, no plots.

Run only outside native timing windows. The capture manifest and output contract
are documented in results/search-2026-10-13/ATTACHMENT_WORK_ANALYSIS.md.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import importlib
import json
import math
from pathlib import Path
import re
import sys

U64 = (1 << 64) - 1
IDENTITY = ("case_id", "family", "n", "m", "density", "intrusion_per_mille",
            "graph_seed", "kkt_seed", "input_fingerprint", "topology_fingerprint")
TOP_FIELDS = {*IDENTITY, "schema", "mst_edge_count", "mst_total_weight",
              "validation", "algorithms", "trace"}
ROUND_FIELDS = {"round", "input_vertices", "input_edges", "selected_edges",
                "output_vertices", "output_edges", "component_count",
                "sum_squared_sizes", "largest_component"}
WORK_HELPERS = {"benchmark/search_work.cpp", "benchmark/work_metrics.hpp",
                "benchmark/component_moments.hpp"}
EXTRA_HELPERS = ("analyze_mst_search.py", "run_mst_search.py", "run_crossover.py",
                 "analyze_continuation.py", "crossover_clocks.py",
                 "run_crossover_baselines.py", "attachment_occupancy.py")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, name, minimum=0, maximum=U64):
    require(type(value) is int and minimum <= value <= maximum,
            f"{name}: expected integer in [{minimum}, {maximum}]")
    return value


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"nonfinite JSON token: {value}")


def read_json(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=object_pairs,
                      parse_constant=reject_constant)


def inventory(value, name):
    require(type(value) is dict and value and all(type(k) is str and k and digest(v)
            for k, v in value.items()), f"{name}: malformed SHA-256 inventory")
    return value


def tracked(path, inputs, expected=None):
    path = Path(path).resolve(strict=True)
    value = sha(path)
    require(expected is None or (digest(expected) and value == expected),
            f"SHA-256 mismatch: {path}")
    require(str(path) not in inputs or inputs[str(path)] == value,
            f"input changed during analysis: {path}")
    inputs[str(path)] = value
    return path


def from_manifest(value, manifest):
    require(type(value) is str and value, "capture path must be nonempty text")
    path = Path(value)
    return path if path.is_absolute() else manifest.parent / path


def timestamp(value, name):
    require(type(value) is str, f"{name}: missing UTC timestamp")
    stamp = dt.datetime.fromisoformat(value)
    require(stamp.utcoffset() == dt.timedelta(0), f"{name}: timestamp is not UTC")
    return stamp


def dependencies(repo):
    # Avoid generating pycache files alongside frozen helpers. No module imports
    # or input hashing happen until this program is explicitly executed.
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(repo / "benchmark"))
    analysis = importlib.import_module("analyze_mst_search")
    occupancy = importlib.import_module("attachment_occupancy")
    require(Path(analysis.__file__).resolve() == repo / "benchmark/analyze_mst_search.py"
            and Path(occupancy.__file__).resolve() == repo / "benchmark/attachment_occupancy.py",
            "imports did not resolve to the requested repository")
    return analysis, occupancy


def registry(repo, work_sources, inputs):
    name = "benchmark/work_metrics.hpp"
    path = tracked(repo / name, inputs, work_sources[name])
    entries = re.findall(r'\{"([a-z_]+)",\s*&kkt_work::WorkStats::([a-z_]+),\s*(true|false)\}',
                         path.read_text())
    require(len(entries) == 65 and len({a for a, _, _ in entries}) == 65
            and all(a == b for a, b, _ in entries), "work registry schema changed or is malformed")
    return [a for a, _, _ in entries], {a for a, _, flag in entries if flag == "true"}


def key(record):
    return record["case_id"], record["graph_seed"], record["kkt_seed"]


def load_timings(paths, analysis, inputs):
    index = {}
    campaigns = []
    seen_paths = set()
    for ordinal, requested in enumerate(paths, 1):
        path = Path(requested).resolve(strict=True)
        require(path not in seen_paths, f"duplicate timing CSV: {path}")
        seen_paths.add(path)
        info, cases, rows, clock_flags, resources, capture_inputs = analysis.load(path)
        del cases, resources
        for name, value in capture_inputs.items():
            tracked(name, inputs, value)
        campaign = {"campaign": f"{ordinal:02d}_{path.stem}", "timing_csv": str(path),
                    "timing_sha256": sha(path), "metadata": str(path.with_suffix(".json")),
                    "revision": info["revision"], "profile": info["profile"],
                    "binary_sha256": info["binary_sha256"],
                    "source_sha256": info["source_sha256"],
                    "build_recipe_sha256": info["build_recipe_sha256"],
                    "timed_rows": info["checked_timed_rows"],
                    "warmup_rows": info["checked_warmup_rows"],
                    "flagged_calls": info["flagged_calls"],
                    "capture_clock_flags": info["capture_clock_flags"]}
        campaigns.append(campaign)
        local = {}
        for row in rows:
            identity = {field: row[field] for field in IDENTITY}
            item = local.setdefault(key(row), {"identity": identity, "timed_rows": 0, "warmup_rows": 0})
            require(item["identity"] == identity, "inconsistent timing identity within capture")
            item[row["phase"] + "_rows"] += 1
        for k, item in local.items():
            if k in index:
                first = index[k][0]
                require(first["identity"] == item["identity"], f"{k}: mixed timing fingerprints/dimensions")
                require(first["campaign"]["source_sha256"] == info["source_sha256"]
                        and first["campaign"]["profile"] == info["profile"],
                        f"{k}: repeated timing key has different native inventory/profile")
            index.setdefault(k, []).append({**item, "campaign": campaign})
    return index, campaigns


def check_command(record, data, manifest_info, manifest_path, repo):
    command = record.get("command")
    require(type(command) is list and command and all(type(v) is str and v for v in command),
            "work command must be a nonempty string array")
    cwd_value = manifest_info.get("working_directory", str(repo))
    require(type(cwd_value) is str and Path(cwd_value).is_absolute(), "working_directory must be absolute")
    cwd = Path(cwd_value)
    executable = Path(command[0])
    executable = executable if executable.is_absolute() else cwd / executable
    binary = from_manifest(manifest_info["binary"], manifest_path)
    require(executable.resolve() == binary.resolve(), "work command uses an unexpected binary")
    require(len(command) == 11, "work command must contain all five explicit case/seed options")
    options = {}
    for flag, value in zip(command[1::2], command[2::2]):
        require(flag not in options, "duplicate work command option")
        options[flag] = value
    expected = {"--family": data["family"], "--n": str(data["n"]),
                "--density": str(data["density"]), "--graph-seed": str(data["graph_seed"]),
                "--kkt-seed": str(data["kkt_seed"])}
    # The native interface has five options, i.e. ten arguments plus executable.
    # Exact spelling avoids an ambiguous command/default-seed provenance record.
    require(options == expected, "work command differs from its emitted fixture/seed identity")


def dimensions(data):
    require(type(data) is dict and set(data) == TOP_FIELDS, "incorrect search_work_v1 fields")
    require(data["schema"] == "search_work_v1" and data["validation"] == "pass", "failed work validation")
    require(type(data["family"]) is str, "work family must be text")
    match = re.fullmatch(r"(leaf|community)_(hierarchy|distance|shuffled|random)(4|16)", data["family"])
    require(match is not None, "work record is not a supported attachment family")
    endpoint, mode, b = match.group(1), match.group(2), int(match.group(3))
    for field in IDENTITY:
        if field not in ("case_id", "family"):
            integer(data[field], field)
    n, m, d = data["n"], data["m"], data["density"]
    require(32 <= n <= 2**22 and n & (n-1) == 0 and 1 <= d <= 512
            and m == n*d <= 2**27 and m < 0x3f3f3f3f and data["intrusion_per_mille"] == 0,
            "work dimensions exceed the attachment domain")
    require(data["graph_seed"] < 2**32 and data["kkt_seed"] < 2**32, "invalid seed width")
    require(data["case_id"] == f"{data['family']}_n{n}_d{d}_p0", "case_id disagrees with dimensions")
    q, local = n//b, n-n//b
    require(q-1 <= m-local <= q*(q-1)//2, "attachment core is not a feasible connected simple graph")
    integer(data["mst_edge_count"], "mst_edge_count", 1)
    integer(data["mst_total_weight"], "mst_total_weight", 1)
    require(data["mst_edge_count"] == n-1 and n*(n-1)//2 <= data["mst_total_weight"] <= (n-1)*m,
            "invalid certified MST size/rank-cost bound")
    return endpoint, mode, b, q, local


def balanced_minimum(total, count):
    if count == 0:
        require(total == 0, "nonzero vertices in an empty partition")
        return 0
    base, extra = divmod(total, count)
    return (count-extra)*base*base + extra*(base+1)*(base+1)


def check_moments(n, count, squares, largest):
    require(1 <= count <= n and (n+count-1)//count <= largest <= n-count+1,
            "invalid original-component count/largest size")
    require(balanced_minimum(n, count) <= squares <= (n-count+1)**2 + count-1
            and squares <= largest*n,
            "component sum of squares violates integer-partition bounds")
    remainder, other = n-largest, count-1
    require(other <= remainder <= other*largest,
            "largest component is incompatible with remaining positive components")
    require(squares >= largest*largest + balanced_minimum(remainder, other),
            "sum of squares is too small for the stated largest component")
    require((squares-n) % 2 == 0, "integer component squares have wrong parity")


def check_counters(data, fields, proxy_fields):
    algorithms = data["algorithms"]
    require(type(algorithms) is dict and set(algorithms) == {"kkt", "compacting_boruvka"},
            "missing or unexpected work algorithm")
    for name, stats in algorithms.items():
        require(type(stats) is dict and set(stats) == {*fields, "total_work_proxy"},
                f"{name}: incomplete/unknown counter schema")
        for field, value in stats.items():
            integer(value, f"{name}.{field}")
        require(sum(stats[f] for f in proxy_fields) == stats["total_work_proxy"],
                f"{name}: total_work_proxy does not match the frozen registry")
        require(stats["current_depth"] == 0 and stats["contraction_calls"] > 0
                and stats["contraction_edges"] >= data["m"]
                and stats["edge_materializations"] >= data["m"]
                and stats["hash_insert_items"] == data["n"]-1
                and stats["sampled_edges"] <= stats["sampling_edge_visits"]
                and stats["filtered_edges"] <= stats["verifier_edges"], f"{name}: inconsistent work counters")
    kkt = algorithms["kkt"]
    require(kkt["kkt_calls"] > 0 and kkt["max_depth"] > 0
            and kkt["kkt_edges"] >= data["m"] and kkt["kkt_vertices"] >= data["n"]
            and kkt["sampling_calls"] == kkt["verifier_calls"]
            and kkt["sampling_edge_visits"] == kkt["verifier_edges"]
            and kkt["verifier_queries"] <= 2*kkt["verifier_edges"], "KKT sampling/verifier counters disagree")
    compact = algorithms["compacting_boruvka"]
    allowed = {f for f in fields if f.startswith("contraction_")} | {
        "kkt_edge_visits", "initialized_slots", "edge_materializations", "hash_insert_items"}
    require(all(compact[f] == 0 for f in fields if f not in allowed),
            "compactor records recursion/sampling/verifier or other unexpected work")
    require(compact["kkt_edge_visits"] == data["m"], "compactor constructor edge visits differ from input m")


def check_trace(data, mode, b, q, local, prediction):
    trace = data["trace"]
    n, m = data["n"], data["m"]
    require(type(trace) is list and 1 <= len(trace) <= n.bit_length()-1, "invalid trace length")
    if prediction is not None:
        require(len(trace) == len(prediction["rounds"]), "ordered trace misses a deterministic dyadic round")
    previous_v, previous_m, previous_count = n, m, n
    previous_squares, previous_largest = n, 1
    selected_total = 0
    for number, row in enumerate(trace, 1):
        require(type(row) is dict and set(row) == ROUND_FIELDS, "incorrect trace round fields")
        for field, value in row.items():
            integer(value, "trace." + field)
        v, edges, out_v, out_m = (row[f] for f in ("input_vertices", "input_edges", "output_vertices", "output_edges"))
        require(row["round"] == number and (v, edges) == (previous_v, previous_m),
                "trace is reordered, duplicated, or fails to chain")
        require(2 <= v and v-1 <= edges <= v*(v-1)//2 and out_v <= v//2
                and (out_v == 0) == (out_m == 0), "invalid connected-simple contraction dimensions")
        count = out_v if out_v else 1
        require(out_v == 0 or (2 <= out_v and out_v-1 <= out_m <= out_v*(out_v-1)//2),
                "output is not an edge-bearing connected quotient or the empty terminal representation")
        selected = row["selected_edges"]
        require(selected == v-count > 0 and out_m <= edges-selected
                and row["component_count"] == previous_count-selected == count,
                "selected forest sizes disagree with quotient/component reduction")
        check_moments(n, count, row["sum_squared_sizes"], row["largest_component"])
        require(row["sum_squared_sizes"] > previous_squares and row["largest_component"] >= previous_largest,
                "component moments reverse under merging")
        if number == 1 and mode != "random":
            require((out_v, out_m, selected, row["sum_squared_sizes"], row["largest_component"])
                    == (q, m-local, local, n*b, b), "cheap-star first quotient is incorrect")
        if prediction is not None:
            expected = prediction["rounds"][number-1]
            require(v == expected["input_vertices"] and out_v == expected["output_vertices"]
                    and count == expected["original_component_count"]
                    and row["largest_component"] == expected["original_component_size"]
                    and row["sum_squared_sizes"] == n*expected["original_component_size"],
                    "ordered trace does not have the deterministic dyadic partition moments")
            if number <= 2:
                require(edges == expected["expected_input_edges"], "exact original/core input count differs")
            if count <= 2:
                require(out_m == expected["expected_output_edges"], "exact terminal quotient differs")
        selected_total += selected
        previous_v, previous_m, previous_count = out_v, out_m, count
        previous_squares, previous_largest = row["sum_squared_sizes"], row["largest_component"]
    require(previous_v == previous_m == 0 and previous_count == 1 and selected_total == n-1,
            "trace is incomplete or does not span the original graph")
    compact = data["algorithms"]["compacting_boruvka"]
    require(compact["contraction_calls"] == len(trace), "compactor call count differs from trace")
    for counter, column in (("contraction_vertices", "input_vertices"), ("contraction_edges", "input_edges"),
                            ("contraction_output_vertices", "output_vertices"), ("contraction_output_edges", "output_edges")):
        require(compact[counter] == sum(row[column] for row in trace), f"{counter} differs from trace sum")
    kkt = data["algorithms"]["kkt"]
    second = trace[1] if len(trace) > 1 else {"output_vertices": 0, "output_edges": 0}
    require(kkt["root_after_two_vertices"] == second["output_vertices"]
            and kkt["root_after_two_edges"] == second["output_edges"], "KKT root-two counters differ from compactor prefix")
    require(kkt["contraction_calls"] >= min(2, len(trace)) and
            kkt["contraction_edges"] >= sum(row["input_edges"] for row in trace[:2]),
            "KKT counters omit mandatory root contractions")


def derive(data, work_path, mode, b, prediction):
    identity = {field: data[field] for field in IDENTITY}
    m, n = data["m"], data["n"]
    kkt, compact = data["algorithms"]["kkt"], data["algorithms"]["compacting_boruvka"]
    expected_volume = prediction["expected_edge_input_volume"] if prediction is not None else None
    summary = {**identity, "work_json": str(work_path), "block_size": b, "weight_mode": mode,
        "occupancy_prediction": prediction is not None, "compactor_rounds": len(data["trace"]),
        "compactor_contraction_edges": compact["contraction_edges"],
        "compactor_contraction_edges_per_m": compact["contraction_edges"]/m,
        "kkt_contraction_edges": kkt["contraction_edges"], "kkt_contraction_edges_per_m": kkt["contraction_edges"]/m,
        "expected_compactor_edges": expected_volume,
        "expected_compactor_edges_per_m": None if prediction is None else expected_volume/m,
        "observed_minus_expected_edges": None if prediction is None else compact["contraction_edges"]-expected_volume,
        "model_volume_truncation_bound": None if prediction is None else prediction["absolute_volume_truncation_bound"],
        "root_after_two_vertices": kkt["root_after_two_vertices"], "root_after_two_edges": kkt["root_after_two_edges"],
        "root_after_two_edge_fraction": kkt["root_after_two_edges"]/m,
        "kkt_calls": kkt["kkt_calls"], "kkt_recursive_edges": kkt["kkt_edges"],
        "kkt_recursive_edges_per_m": kkt["kkt_edges"]/m,
        "sampling_calls": kkt["sampling_calls"], "sampled_edges": kkt["sampled_edges"],
        "verifier_calls": kkt["verifier_calls"], "verifier_input_edges": kkt["verifier_edges"],
        "retained_verifier_edges": kkt["filtered_edges"],
        "heavy_verifier_edges": kkt["verifier_edges"]-kkt["filtered_edges"],
        "heavy_fraction": None if kkt["verifier_edges"] == 0 else
            (kkt["verifier_edges"]-kkt["filtered_edges"])/kkt["verifier_edges"],
        "kkt_materializations_per_m": kkt["edge_materializations"]/m,
        "compactor_materializations_per_m": compact["edge_materializations"]/m,
        "kkt_initialized_slots_per_m": kkt["initialized_slots"]/m,
        "compactor_initialized_slots_per_m": compact["initialized_slots"]/m}
    rounds = []
    for observed in data["trace"]:
        number = observed["round"]
        predicted = prediction["rounds"][number-1] if prediction is not None else None
        row = {**identity, **observed, "model_applicable": predicted is not None,
               "model_phase": ("original_star" if number == 1 else "core") if predicted else None,
               "core_round_index": number-1 if predicted and number >= 2 else None,
               "core_input_block_exponent": number-2 if predicted and number >= 2 else None,
               "core_input_block_size": 1 << (number-2) if predicted and number >= 2 else None,
               "core_output_block_size": 1 << (number-1) if predicted else None,
               "effective_original_components": n*n/observed["sum_squared_sizes"]}
        for direction in ("input", "output"):
            expected = predicted[f"expected_{direction}_edges"] if predicted else None
            row[f"expected_{direction}_edges"] = expected
            row[f"observed_minus_expected_{direction}_edges"] = None if predicted is None else observed[f"{direction}_edges"]-expected
            row[f"{direction}_truncation_bound"] = predicted[f"{direction}_absolute_truncation_bound"] if predicted else None
        rounds.append(row)
    counters = [{**identity, "algorithm": name, **values} for name, values in data["algorithms"].items()]
    return summary, rounds, counters


def collect(repo, timing_paths, manifest_path):
    inputs = {}
    manifest_path = tracked(manifest_path, inputs)
    manifest = read_json(manifest_path)
    require(type(manifest) is dict and manifest.get("schema") == "attachment_work_capture_v1"
            and manifest.get("validation") == "pass" and manifest.get("instrumented") is True
            and "error" not in manifest,
            "not a successful instrumented attachment work capture")
    for field in ("rows_removed", "rows_adjusted"):
        require(type(manifest.get(field)) is int and manifest[field] == 0, "removed or adjusted work rows")
    require(type(manifest.get("profile")) is str and manifest["profile"] and
            digest(manifest.get("binary_sha256")), "missing work profile/binary SHA-256")
    sources = inventory(manifest.get("source_sha256"), "work sources")
    build = inventory(manifest.get("build_recipe_sha256"), "work build recipe")
    require(set(build) == {"Makefile"}, "missing or unexpected work build recipe")
    require(digest(manifest.get("build_log_sha256")), "missing work build-log SHA-256")
    tracked(from_manifest(manifest.get("build_log"), manifest_path), inputs, manifest.get("build_log_sha256"))
    require(WORK_HELPERS <= set(sources), "work producer/registry/moment source hashes are missing")
    for name in EXTRA_HELPERS:
        tracked(repo / "benchmark" / name, inputs)
    tracked(Path(__file__), inputs)
    analysis, occupancy = dependencies(repo)
    fields, proxy_fields = registry(repo, sources, inputs)
    timing_index, campaigns = load_timings(timing_paths, analysis, inputs)
    shared = analysis.NATIVE_FILES - {"benchmark/mst_search.cpp"}
    require(shared <= set(sources), "work inventory lacks production/fixture sources")
    records = manifest.get("records")
    require(type(records) is list and records, "work capture has no selected records")
    seen, physical_inputs, used_files = set(), {}, set()
    summaries, rounds, counters, links, model_records, source_comparisons, capture_flags = [], [], [], [], [], [], []
    for record in records:
        require(type(record) is dict and type(record.get("exit_status")) is int and record["exit_status"] == 0
                and "error" not in record, "failed or malformed work capture record")
        require(digest(record.get("json_sha256")) and digest(record.get("log_sha256")),
                "missing work stdout/stderr SHA-256")
        work_path = tracked(from_manifest(record.get("json"), manifest_path), inputs, record.get("json_sha256"))
        log_path = tracked(from_manifest(record.get("log"), manifest_path), inputs, record.get("log_sha256"))
        require(work_path not in used_files and log_path not in used_files and work_path != log_path,
                "duplicate or reused work/log file")
        used_files.update((work_path, log_path))
        data = read_json(work_path)
        _, mode, b, q, local = dimensions(data)
        k = key(data)
        require(k not in seen, f"duplicate selected work key: {k}")
        seen.add(k)
        require(k in timing_index, f"work fixture/seed has no completed timed counterpart: {k}")
        check_command(record, data, manifest, manifest_path, repo)
        if "started_utc" in record or "finished_utc" in record:
            start = timestamp(record.get("started_utc"), "work start")
            finish = timestamp(record.get("finished_utc"), "work finish")
            if finish < start:
                capture_flags.append({"key": list(k), "flag": "work_utc_reversed", "retained": True})
        analysis.capture.check_certificate(log_path, [data])
        for match in timing_index[k]:
            campaign = match["campaign"]
            require(match["identity"] == {field: data[field] for field in IDENTITY},
                    f"{k}: work and timing fingerprints/dimensions differ")
            require(all(campaign["source_sha256"].get(name) == sources[name] for name in shared),
                    f"{k}: work and timing production/fixture source hashes differ")
            for name in WORK_HELPERS & set(campaign["source_sha256"]):
                require(campaign["source_sha256"][name] == sources[name], "work producer changed after timing freeze")
            source_comparisons.append({"work_json": str(work_path), "campaign": campaign["campaign"],
                                       "matched_native_files": sorted(shared | (WORK_HELPERS & set(campaign["source_sha256"])))})
            links.append({**match["identity"], "work_json": str(work_path), "campaign": campaign["campaign"],
                          "timing_csv": campaign["timing_csv"], "timed_calls": match["timed_rows"],
                          "retained_warmups": match["warmup_rows"], "timing_sha256": campaign["timing_sha256"]})
        check_counters(data, fields, proxy_fields)
        prediction = occupancy.attachment_expectation(data["n"], data["density"], b) if mode in ("hierarchy", "distance") else None
        check_trace(data, mode, b, q, local, prediction)
        physical = (data["case_id"], data["graph_seed"])
        deterministic = (data["input_fingerprint"], data["topology_fingerprint"], data["mst_total_weight"],
                         data["algorithms"]["compacting_boruvka"], data["trace"])
        require(physical not in physical_inputs or physical_inputs[physical] == deterministic,
                "repeated sampling seeds changed the graph or deterministic compactor diagnostics")
        physical_inputs[physical] = deterministic
        summary, trace_rows, counter_rows = derive(data, work_path, mode, b, prediction)
        summaries.append(summary); rounds.extend(trace_rows); counters.extend(counter_rows)
        model_records.append({"case_id": data["case_id"], "graph_seed": data["graph_seed"],
                              "kkt_seed": data["kkt_seed"], "prediction": prediction})
    return {"summary": summaries, "rounds": rounds, "counters": counters, "timing_links": links}, {
        "schema": "attachment_work_analysis_v1", "validation": "pass", "work_records": len(seen),
        "distinct_case_graphs": len(physical_inputs), "trace_rounds": len(rounds),
        "timing_campaigns": campaigns, "work_capture_manifest": str(manifest_path),
        "work_capture_metadata": manifest, "native_source_comparisons": source_comparisons,
        "work_capture_clock_flags": capture_flags, "input_sha256": inputs,
        "rows_removed": 0, "rows_adjusted": 0, "timings_pooled": False,
        "independently_recertifies_mst_from_edges": False,
        "certificate_scope": "successful captured native cycle-certificate marker and exact work/timing fingerprints",
        "partition_scope": "checks counts and moments; selected original edge IDs are not present in search_work_v1",
        "model_scope": "ideal uniform shortcut subsets with deterministic dyadic partitions, not a fitted or elapsed-time model",
        "roundoff_scope": "reported model bounds cover truncation only, not ordinary floating-point roundoff",
        "counter_scope": "logical events/incidences, not instructions, bytes, distinct original edges, or timed measurements",
    }, model_records


def write_csv(path, rows):
    require(rows, "refusing an empty output table")
    with path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def report(tables, provenance):
    text = ["# Attachment logical-work and occupancy comparison", "",
        f"Validated {provenance['work_records']} selected work records and {provenance['trace_rounds']} "
        f"compactor rounds against {len(provenance['timing_campaigns'])} complete timing capture(s). "
        "Every selected fixture/seed matches both timed fingerprints and the required native source hashes. "
        "Campaigns remain separate; no times are pooled or inferred from work counts.", "",
        "The occupancy column is an ideal random-subset expectation. A single observed graph need not equal it; "
        "signed differences are descriptive, not test failures or statistical residual scores. Controls have no "
        "dyadic occupancy prediction. Repeated sampling seeds are not additional graph draws.", "",
        "| Case | Graph seed | KKT seed | Compactor volume/m | KKT volume/m | Model compactor volume/m | Sampling calls | Verifier incidence heavy fraction |",
        "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in tables["summary"]:
        expected = row["expected_compactor_edges_per_m"]
        heavy = row["heavy_fraction"]
        text.append(f"| {row['case_id']} | {row['graph_seed']} | {row['kkt_seed']} | "
                    f"{row['compactor_contraction_edges_per_m']:.6f} | {row['kkt_contraction_edges_per_m']:.6f} | "
                    f"{'n/a' if expected is None else format(expected, '.6f')} | {row['sampling_calls']} | "
                    f"{'n/a' if heavy is None else format(100*heavy, '.4f')+'%'} |")
    text.extend(["", "Original round 1 consumes the expanded graph and contracts the cheap stars in ordered modes. "
        "Original round j>=2 is core round j-1, consuming blocks of 2^(j-2) core vertices. The terminal "
        "stored quotient has zero vertices/edges while the original partition has one component. "
        "[rounds.csv](rounds.csv) retains every observed round, its explicit indices, model expectation, signed "
        "difference and truncation budget. Budgets exclude floating-point roundoff and graph-sampling variation.", "",
        "[summary.csv](summary.csv) keeps recursive volumes, materializations, initialized slots, sampling and "
        "verifier counts. Heavy fractions use recursive verifier input incidences, not distinct root edges; "
        "a zero verifier denominator is n/a. [counters.csv](counters.csv) retains the complete registered schema "
        "and checks its mixed-event proxy against the frozen registry. These event classes have different costs "
        "and cannot predict elapsed time by treating every unit equally.", "",
        "[timing_links.csv](timing_links.csv) identifies every matching complete campaign without combining its "
        "durations. [models.json](models.json) archives complete model outputs; [provenance.json](provenance.json) "
        "binds raw work/log/build records, timing inputs, source inventories, helper hashes and derived files. "
        "This joiner verifies the captured native certificate marker; it does not reconstruct input edges or "
        "independently recompute the MST. Moment checks cannot prove vertex membership because selected-edge "
        "ledgers are absent from search_work_v1.", ""])
    return "\n".join(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--timing-csv", type=Path, action="append", required=True)
    parser.add_argument("--work-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        repo = args.repo_root.resolve(strict=True)
        require(not args.output_dir.exists(), "output directory already exists; refusing replacement")
        tables, provenance, models = collect(repo, args.timing_csv, args.work_manifest)
        for name, expected in provenance["input_sha256"].items():
            require(sha(name) == expected, f"input mutated while validating: {name}")
        args.output_dir.mkdir(parents=True, exist_ok=False)
        for name, rows in tables.items():
            write_csv(args.output_dir / (name + ".csv"), rows)
        (args.output_dir / "models.json").write_text(json.dumps(models, indent=2, allow_nan=False) + "\n")
        (args.output_dir / "report.md").write_text(report(tables, provenance))
        provenance["derived_sha256"] = {path.name: sha(path) for path in sorted(args.output_dir.iterdir())}
        (args.output_dir / "provenance.json").write_text(json.dumps(provenance, indent=2, allow_nan=False) + "\n")
        print(json.dumps({"validation": "pass", "work_records": provenance["work_records"],
                          "trace_rounds": provenance["trace_rounds"], "output_dir": str(args.output_dir.resolve())}))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f"attachment work analysis: {error}\n")


if __name__ == "__main__":
    main()
