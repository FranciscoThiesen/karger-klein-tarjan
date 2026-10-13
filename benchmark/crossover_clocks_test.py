#!/usr/bin/env python3
"""Synthetic clock-audit regressions; no solver invocation or wall-time tests."""
import copy
import csv
import json
from pathlib import Path
import tempfile

import analyze_continuation as base
import crossover_clocks as clocks


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def write_csv(path, fields, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def synthetic(cases):
    rows, records = [], []
    cpu_now, utc_now = 1_000_000, 1_800_000_000_000_000_000
    for case_index, (case, spec) in enumerate(cases.items()):
        for gi, graph in enumerate((42, 17)):
            for si, seed in enumerate((7, 0)):
                for phase in ("warmup", "timed"):
                    for repetition in (0, 1):
                        for order in (0, 1):
                            algorithm = ("kkt", "compacting_boruvka")[(gi+si+repetition+order) % 2]
                            duration = (100 if repetition == 0 else 10000) * (gi+1) * (1 if si == 0 else 3)
                            if algorithm == "kkt":
                                duration = duration//2 if repetition == 0 else duration*3//2
                            record = {"case_id": case, "graph_seed": graph, "sampling_seed": seed,
                                      "phase": phase, "repetition": repetition, "order": order,
                                      "algorithm": algorithm, "utc_start_ns": utc_now,
                                      "utc_end_ns": utc_now+duration,
                                      "process_cpu_start_ns": cpu_now,
                                      "process_cpu_end_ns": cpu_now+duration,
                                      "process_cpu_elapsed_ns": duration,
                                      "steady_elapsed_ns": duration, "validation": "pass"}
                            records.append(record)
                            if phase == "timed":
                                rows.append({**spec, "graph_seed": graph, "input_fingerprint": 1000*case_index+graph,
                                             "topology_fingerprint": 1000*case_index+graph,
                                             "kkt_seed": seed, "repetition": repetition, "order": order,
                                             "warmups": 2, "algorithm": algorithm,
                                             "elapsed_ns": duration, "validation": "pass"})
                            cpu_now += duration+1000
                            utc_now += duration+1000
    return rows, records


def main():
    checks = []
    with tempfile.TemporaryDirectory(prefix="crossover-clock-test-") as temporary:
        folder = Path(temporary)
        manifest, raw, meta = [folder/name for name in ("manifest.csv", "timing.csv", "timing.json")]
        write_csv(manifest, base.MANIFEST_FIELDS,
                  [{"family": "hierarchical_path", "n": n, "density": 2, "intrusion_per_mille": 0}
                   for n in (64, 32)])
        cases = base.load_manifest(manifest)
        rows, records = synthetic(cases)
        original_metadata = {"command": ["/synthetic/solver", "--manifest", str(manifest), "--mode", "timing",
                                         "--graph-seeds", "42,17", "--sampling-seeds", "7,0",
                                         "--repetitions", "2", "--warmups", "2"],
                             "mode": "timing", "exit_status": 0, "interruption": None}

        def save(changed_rows=None, changed_records=None, metadata=None, log_text=None):
            write_csv(raw, base.TIMING_FIELDS, rows if changed_rows is None else changed_rows)
            selected = records if changed_records is None else changed_records
            log = "setup diagnostic unrelated to call clocks\n" + "".join(
                clocks.PREFIX+json.dumps(record)+"\n" for record in selected)
            raw.with_suffix(".log").write_text(log if log_text is None else log_text)
            info = copy.deepcopy(original_metadata if metadata is None else metadata)
            info.update(output_sha256=clocks.sha(raw), log_sha256=clocks.sha(raw.with_suffix(".log")),
                        manifest_sha256=clocks.sha(manifest))
            meta.write_text(json.dumps(info))
            return clocks.audit(raw, meta)

        answer = save()
        check(answer["timed_calls"] == 32 and answer["warmup_calls"] == 32 and
              answer["clock_records"] == 64 and answer["flagged_calls"] == 0,
              "incorrect complete clock counts")
        check(answer["rows_removed"] == answer["rows_adjusted"] == 0, "audit changed observations")
        for case in answer["cpu_case_summaries"]:
            check(case["paired_cpu_ratio"] == 1 and case["graph_min_cpu_ratio"] == case["graph_max_cpu_ratio"] == 1,
                  "incorrect paired CPU hierarchy")
            check(case["kkt_cpu_median_ns"] == 22575 and case["compacting_boruvka_cpu_median_ns"] == 15150,
                  "incorrect independent CPU time medians")
            check(case["kkt_higher_cpu_observations"] == 4 and case["paired_observations"] == 8,
                  "CPU losses missing")
        checks.append({"case": "complete nonnumeric seed/case order and paired-vs-independent CPU medians", "status": "pass"})

        # Add a known long suspension-like interval to an actual timed call.
        changed_records, changed_rows = copy.deepcopy(records), copy.deepcopy(rows)
        index = next(i for i,r in enumerate(changed_records) if r["phase"] == "timed")
        delay = 918_000_000_000
        changed_records[index]["steady_elapsed_ns"] += delay
        changed_records[index]["utc_end_ns"] += delay
        for record in changed_records[index+1:]:
            record["utc_start_ns"] += delay
            record["utc_end_ns"] += delay
        changed_rows[0]["elapsed_ns"] += delay
        suspended = save(changed_rows, changed_records)
        flagged = [r for r in suspended["records"] if r["diagnostic_flags"]]
        check(len(flagged) == 1 and flagged[0]["diagnostic_flags"] == ["steady_exceeds_process_cpu"] and
              flagged[0]["steady_minus_cpu_ns"] == delay and not flagged[0]["excluded"], "known sleep-like call was lost")
        check(suspended["cpu_case_summaries"] == answer["cpu_case_summaries"] and suspended["timed_calls"] == 32,
              "secondary CPU summaries or row retention changed")
        checks.append({"case": "known918-second sleep-like timed observation retained and CPU summary unchanged", "status": "pass"})

        changed = copy.deepcopy(records)
        changed[0]["utc_end_ns"] = changed[0]["utc_start_ns"]-1
        reversed_clock = save(changed_records=changed)
        check("realtime_reversed_within_call" in reversed_clock["records"][0]["diagnostic_flags"],
              "realtime reversal was not retained")
        changed = copy.deepcopy(records)
        changed[1]["utc_start_ns"] = changed[0]["utc_start_ns"]-100
        changed[1]["utc_end_ns"] = changed[1]["utc_start_ns"]+changed[1]["steady_elapsed_ns"]
        reversed_clock = save(changed_records=changed)
        check("realtime_reversed_between_calls" in reversed_clock["records"][1]["diagnostic_flags"],
              "inter-call realtime reversal was not retained")
        checks.append({"case": "within-call and between-call realtime reversals retained as flags", "status": "pass"})

        def reject(name, action):
            try:
                action()
            except (ValueError, OSError) as error:
                checks.append({"case": name, "status": "rejected", "message": str(error)})
            else:
                raise AssertionError(name+" was accepted")

        def mutate_record(field, value, index=0):
            changed = copy.deepcopy(records)
            changed[index][field] = value
            return save(changed_records=changed)

        for field, value in [("case_id", "unknown"), ("graph_seed", 999), ("sampling_seed", 999),
                             ("phase", "setup"), ("repetition", 2), ("order", 2), ("algorithm", "kruskal"),
                             ("validation", "fail"), ("process_cpu_elapsed_ns", 0),
                             ("process_cpu_elapsed_ns", -1), ("process_cpu_elapsed_ns", 1),
                             ("steady_elapsed_ns", 0), ("utc_start_ns", -1), ("utc_end_ns", 2**63),
                             ("graph_seed", True), ("utc_start_ns", 1.0), ("process_cpu_end_ns", "4")]:
            reject(f"invalid record {field}={value!r}", lambda f=field,v=value:mutate_record(f,v))
        reject("missing warmup record", lambda:save(changed_records=records[1:]))
        reject("duplicate record", lambda:save(changed_records=records+[records[0]]))
        reject("same-count duplicate identity", lambda:save(changed_records=[records[1]]+records[1:]))
        reject("reordered records", lambda:save(changed_records=[records[1],records[0]]+records[2:]))
        reject("extra JSON field", lambda:mutate_record("unexpected", 1))
        incomplete = copy.deepcopy(records)
        del incomplete[0]["utc_start_ns"]
        reject("missing JSON field", lambda:save(changed_records=incomplete))
        overlap = copy.deepcopy(records)
        cpu_delta = overlap[1]["process_cpu_elapsed_ns"]
        overlap[1]["process_cpu_start_ns"] = overlap[0]["process_cpu_end_ns"]-1
        overlap[1]["process_cpu_end_ns"] = overlap[1]["process_cpu_start_ns"]+cpu_delta
        reject("CPU clock overlap between calls", lambda:save(changed_records=overlap))
        reverse_cpu = copy.deepcopy(records)
        reverse_cpu[0]["process_cpu_end_ns"] = reverse_cpu[0]["process_cpu_start_ns"]-1
        reject("CPU clock reversal within call", lambda:save(changed_records=reverse_cpu))
        reject("CSV/clock duration mismatch", lambda:mutate_record("steady_elapsed_ns", 12345,index))
        reject("CSV missing row", lambda:save(changed_rows=rows[1:]))
        reject("CSV duplicate row", lambda:save(changed_rows=rows+[rows[0]]))
        reject("CSV order mismatch", lambda:save(changed_rows=[rows[1],rows[0]]+rows[2:]))
        good_log = "".join(clocks.PREFIX+json.dumps(record)+"\n" for record in records)
        for name, text in [("invalid JSON", "call_clock_v1 {\n"),
                           ("nonobject JSON", "call_clock_v1 []\n"),
                           ("unknown clock version", good_log.replace("call_clock_v1", "call_clock_v2", 1)),
                           ("malformed clock prefix", good_log.replace("call_clock_v1 ", "call_clock_v1", 1)),
                           ("duplicate JSON key", good_log.replace('{"case_id":', '{"case_id":"duplicate","case_id":', 1)),
                           ("nonfinite JSON", good_log.replace('"graph_seed": 42', '"graph_seed": NaN', 1))]:
            reject(name, lambda text=text:save(log_text=text))
        for field, value in [("mode", "trace"), ("exit_status", 1), ("exit_status", False), ("interruption", "signal")]:
            info = copy.deepcopy(original_metadata)
            info[field] = value
            reject("bad capture "+field, lambda info=info:save(metadata=info))
        for name, option, value in [("timing mode", "--mode", "work"), ("odd repetitions", "--repetitions", "3"),
                                     ("zero warmups", "--warmups", "0"), ("duplicate graph seeds", "--graph-seeds", "42,42"),
                                     ("seed order differs", "--graph-seeds", "17,42"),
                                     ("unknown seed bank", "--sampling-seeds", "7,1")]:
            info = copy.deepcopy(original_metadata)
            info["command"][info["command"].index(option)+1] = value
            reject(name, lambda info=info:save(metadata=info))
        info = copy.deepcopy(original_metadata)
        info["command"] += ["--warmups", "2"]
        reject("duplicate command flag", lambda:save(metadata=info))
        info = copy.deepcopy(original_metadata)
        info["command"] = info["command"][:-2]
        reject("missing command flag", lambda:save(metadata=info))
        info = copy.deepcopy(original_metadata)
        info["command"][2] = "manifest.csv"
        reject("ambiguous relative manifest", lambda:save(metadata=info))
        info["working_directory"] = str(folder)
        relative = save(metadata=info)
        check(relative["timed_calls"] == 32, "explicit working-directory manifest failed")
        checks.append({"case": "relative manifest resolved through explicit absolute working_directory", "status": "pass"})
        save()
        raw.write_text(raw.read_text()+"\n")
        reject("raw hash mismatch", lambda:clocks.audit(raw,meta))
        save()
        raw.with_suffix(".log").write_text(good_log+"changed\n")
        reject("log hash mismatch", lambda:clocks.audit(raw,meta))
        save()
        manifest.write_text(manifest.read_text()+"\n")
        reject("manifest hash mismatch", lambda:clocks.audit(raw,meta))
    print(json.dumps({"validation": "pass", "positive_checks": sum(c["status"] == "pass" for c in checks),
                      "negative_checks": sum(c["status"] == "rejected" for c in checks), "checks": checks}, indent=2))


if __name__ == "__main__":
    main()
