#!/usr/bin/env python3
"""Correlate retained five-solver UTC intervals with archived macOS power events.

Standalone standard-library audit, intended to run AFTER native timing stops.
It never adjusts, removes or reclassifies a performance observation. This is
power-log correlation, not a substitute for analyze_mst_search.py or proof that
sleep prevention worked. All parsed event lines and the complete log survive.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

NS = 1_000_000_000
EPOCH = dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)
EVENT = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\s+([+-]\d{4})\s+(Sleep|Wake|DarkWake)(?=\s|$)(.*)$")
EVENT_LIKE = re.compile(r"^\d{4}-\d\d-\d\d\s+\S+\s+(?:\S+\s+)?(?:Sleep|Wake|DarkWake)(?=\s|$)")
FIELDS = ("case_id", "family", "n", "m", "density", "intrusion_per_mille", "graph_seed", "kkt_seed",
          "input_fingerprint", "topology_fingerprint", "phase", "repetition", "order", "warmups", "algorithm",
          "elapsed_ns", "utc_start_ns", "utc_end_ns", "process_cpu_start_ns", "process_cpu_end_ns",
          "process_cpu_elapsed_ns", "validation")
ALGORITHMS = ("kkt", "compacting_boruvka", "kruskal", "prim", "boruvka")


def require(condition, message):
    if not condition: raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_read(text):
    def pairs(values):
        result = {}
        for key, value in values:
            require(key not in result, "duplicate JSON key: " + key)
            result[key] = value
        return result
    def invalid(value): raise ValueError("nonfinite JSON constant: " + value)
    def finite_float(value):
        result = float(value)
        require(math.isfinite(result), "nonfinite JSON number")
        return result
    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid, parse_float=finite_float)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+"\n")


def datetime_ns(value):
    require(value.utcoffset() is not None, "a timestamp needs an explicit UTC offset")
    difference = value.astimezone(dt.timezone.utc)-EPOCH
    return ((difference.days*86400+difference.seconds)*1_000_000+difference.microseconds)*1000


def iso_ns(value):
    require(type(value) is str, "timestamp must be text")
    return datetime_ns(dt.datetime.fromisoformat(value))


def unsigned(value, name):
    require(type(value) is str and re.fullmatch(r"[0-9]+", value), "invalid integer " + name)
    return int(value)


def read_capture(path):
    metadata_path = path.with_suffix(".json")
    info = json_read(metadata_path.read_text())
    require(info.get("schema") == "mst_search_capture_v1" and info.get("validation") == "pass"
            and "error" not in info, "power audit requires a completed successful capture")
    require(info.get("output_sha256") == sha(path), "capture CSV differs from sidecar hash")
    require(type(info.get("rows_removed")) is int and info["rows_removed"] == 0 and
            type(info.get("rows_adjusted")) is int and info["rows_adjusted"] == 0, "capture claims modified rows")
    require(info.get("algorithms") == list(ALGORITHMS), "wrong algorithm matrix")
    rows = []; keys = set()
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        require(tuple(reader.fieldnames or ()) == FIELDS, "unexpected capture CSV header")
        for number, row in enumerate(reader, 2):
            require(None not in row and all(v is not None for v in row.values()), f"malformed row {number}")
            require(row["validation"] == "pass" and row["phase"] in ("warmup", "timed") and
                    row["algorithm"] in ALGORITHMS, f"failed/unknown call at row {number}")
            for field in FIELDS:
                if field not in ("case_id", "family", "phase", "algorithm", "validation"):
                    row[field] = unsigned(row[field], field)
            require(row["elapsed_ns"] > 0 and row["utc_start_ns"] > 0 and row["utc_end_ns"] > 0 and
                    row["process_cpu_end_ns"]-row["process_cpu_start_ns"] == row["process_cpu_elapsed_ns"] > 0,
                    "invalid recorded clock endpoints or durations")
            key = tuple(row[f] for f in ("case_id", "graph_seed", "kkt_seed", "phase", "repetition", "algorithm"))
            require(key not in keys, "duplicate call identity"); keys.add(key); rows.append(row)
    for field, expected in (("checked_rows", len(rows)), ("checked_timed_rows", sum(r["phase"] == "timed" for r in rows)),
                             ("checked_warmup_rows", sum(r["phase"] == "warmup" for r in rows))):
        require(type(info.get(field)) is int and info[field] == expected, "incorrect metadata " + field)
    require(rows, "empty completed capture")
    # Full protocol, independent certificate and child-file verification belongs
    # to the strict analyzer. This adjunct binds to the same immutable raw file.
    return info, rows, {str(path): sha(path), str(metadata_path): sha(metadata_path)}


def parse_events(text):
    events = []; malformed = []; previous = None; reversals = []
    for number, line in enumerate(text.splitlines(), 1):
        match = EVENT.match(line)
        if not match:
            if EVENT_LIKE.match(line): malformed.append({"line_number": number, "raw": line})
            continue
        try:
            stamp = dt.datetime.strptime(match[1]+" "+match[2], "%Y-%m-%d %H:%M:%S %z")
        except ValueError:
            malformed.append({"line_number": number, "raw": line}); continue
        instant = datetime_ns(stamp)
        if previous is not None and instant < previous:
            reversals.append({"line_number": number, "previous_utc_ns": previous, "utc_ns": instant})
        previous = instant
        durations = re.findall(r"\b(\d+)\s+secs\b", match[4])
        events.append({"line_number": number, "event": match[3], "utc": stamp.astimezone(dt.timezone.utc).isoformat(),
            "utc_ns": instant, "logged_duration_seconds": int(durations[-1]) if durations else None, "raw": line})
    # Preserve original line indices/raw text while using chronological UTC to
    # correlate intervals. A reversed source order is explicitly disclosed.
    return sorted(events, key=lambda e: (e["utc_ns"], e["line_number"])), malformed, reversals


def sleep_intervals(events):
    """Potential logged Sleep→first Wake/DarkWake intervals, never CPU-idle time."""
    intervals = []; pending = None
    for event in events:
        if event["event"] == "Sleep":
            if pending is None:
                pending = {"start_ns": event["utc_ns"], "sleep_event_lines": [event["line_number"]]}
            else:
                # Do not silently replace an earlier unmatched sleep. Duplicate
                # or repeated records remain linked to the potential interval.
                pending["sleep_event_lines"].append(event["line_number"])
        elif pending is not None:
            intervals.append({**pending, "end_ns": event["utc_ns"], "end_event": event["event"],
                              "wake_event_line": event["line_number"], "open_end": False})
            pending = None
    if pending is not None:
        intervals.append({**pending, "end_ns": None, "end_event": None, "wake_event_line": None, "open_end": True})
    return intervals


def intersection(start, end, other_start, other_end):
    return max(0, min(end, other_end)-max(start, other_start))


def correlate(rows, events, intervals):
    results = []
    for row in rows:
        start, finish = row["utc_start_ns"], row["utc_end_ns"]
        identifiable = finish >= start
        nearby = [event["line_number"] for event in events
                  if min(start, finish)-NS <= event["utc_ns"] <= max(start, finish)+NS]
        overlaps = []
        if identifiable:
            for index, interval in enumerate(intervals):
                end = interval["end_ns"] if interval["end_ns"] is not None else finish
                amount = intersection(start, finish, interval["start_ns"], end)
                if amount:
                    overlaps.append({"interval_index": index, "nominal_overlap_ns": amount,
                                     "open_end": interval["open_end"]})
        results.append({**{field: row[field] for field in ("case_id", "graph_seed", "kkt_seed", "phase", "repetition",
                          "order", "algorithm", "elapsed_ns", "process_cpu_elapsed_ns", "utc_start_ns", "utc_end_ns")},
            "utc_alignable": identifiable,
            "nominal_logged_sleep_overlap_ns": sum(r["nominal_overlap_ns"] for r in overlaps) if identifiable else None,
            "sleep_interval_indices": ";".join(str(r["interval_index"]) for r in overlaps),
            "overlap_has_unclosed_sleep": any(r["open_end"] for r in overlaps),
            "nearby_power_event_lines": ";".join(str(line) for line in nearby), "excluded": False})
    return results


def inhibition_records(paths):
    result = []
    for path in paths:
        path = path.resolve(strict=True); record = json_read(path.read_text())
        require(type(record) is dict, "sleep-inhibition record must be an object")
        text = json.dumps(record, ensure_ascii=False)
        failed = "Failed to create PreventUserIdleSystemSleep assertion" in text
        verified = record.get("idle_sleep_prevention_verified") is True and not failed
        result.append({"path": str(path), "sha256": sha(path), "record": record,
                       "explicit_assertion_failure": failed, "record_claims_verified_prevention": verified})
    return result


def self_test():
    raw = "\n".join((
        "2026-10-13 00:00:00 -0700 Sleep  Entering Sleep state due to 'Maintenance Sleep' 10 secs",
        "2026-10-13 00:00:10 -0700 DarkWake DarkWake from Deep Idle",
        "2026-10-13 00:00:12 -0700 Sleep  Entering Sleep state 8 secs",
        "2026-10-13 07:00:20 +0000 Wake Wake from Deep Idle",
        "2026-10-13 07:00:25 +0000 Sleep Entering Sleep state",
        "2026-10-13 07:00:40 BADZONE Sleep malformed offset"))
    events, malformed, reversed_order = parse_events(raw); intervals = sleep_intervals(events)
    require(len(events) == 5 and len(malformed) == 1 and not reversed_order, "event parser check failed")
    require(intervals[0]["end_event"] == "DarkWake" and intervals[-1]["open_end"], "Sleep/DarkWake state check failed")
    origin = events[0]["utc_ns"]
    def row(start, finish):
        return {"case_id": "synthetic", "graph_seed": 1, "kkt_seed": 2, "phase": "timed", "repetition": 0,
                "order": 0, "algorithm": "kkt", "elapsed_ns": 1, "process_cpu_elapsed_ns": 1,
                "utc_start_ns": origin+start*NS, "utc_end_ns": origin+finish*NS}
    result = correlate([row(5, 15), row(21, 22), row(28, 30), row(15, 5)], events, intervals)
    require(result[0]["nominal_logged_sleep_overlap_ns"] == 8*NS, "preceding sleep or multiple intervals lost")
    require(result[1]["nominal_logged_sleep_overlap_ns"] == 0 and
            result[2]["nominal_logged_sleep_overlap_ns"] == 2*NS and result[2]["overlap_has_unclosed_sleep"],
            "closed/open interval check failed")
    require(result[3]["nominal_logged_sleep_overlap_ns"] is None and not result[3]["excluded"], "reversed UTC was dropped")
    require(all(not r["excluded"] for r in result), "power audit removed observations")
    return {"validation": "pass", "checks": ["offset conversion", "malformed event retained", "DarkWake closes sleep",
            "preceding sleep and multiple overlaps", "unclosed sleep labeled", "reversed UTC retained", "no row removal"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timing-csv", type=Path)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--power-log", type=Path, help="already archived complete pmset -g log output")
    source.add_argument("--query-pmset", action="store_true", help="query once after timing; archive stdout/stderr and exit status")
    parser.add_argument("--inhibition-json", type=Path, action="append", default=[])
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2)); return
    require(args.timing_csv is not None and args.output_dir is not None and (args.power_log or args.query_pmset),
            "--timing-csv, --output-dir and one power-log source are required")
    timing = args.timing_csv.resolve(strict=True)
    info, rows, inputs = read_capture(timing)
    attempts = inhibition_records(args.inhibition_json)
    output = args.output_dir.resolve()
    require(not output.exists(), "refusing to overwrite power evidence")
    output.mkdir(parents=True)
    log = output/"pmset.log"; stderr_path = output/"pmset.stderr"
    if args.query_pmset:
        query = {"command": ["/usr/bin/pmset", "-g", "log"], "started_utc": dt.datetime.now(dt.timezone.utc).isoformat()}
        with log.open("x") as stdout, stderr_path.open("x") as stderr:
            try:
                result = subprocess.run(query["command"], stdout=stdout, stderr=stderr, check=False, timeout=120)
                status = result.returncode
            except (OSError, subprocess.SubprocessError) as error:
                status = None; query["error"] = repr(error); stderr.write(repr(error)+"\n")
        query.update(exit_status=status, finished_utc=dt.datetime.now(dt.timezone.utc).isoformat())
        query_ok = status == 0
    else:
        source_path = args.power_log.resolve(strict=True)
        log.write_bytes(source_path.read_bytes()); stderr_path.write_text("")
        inputs[str(source_path)] = sha(source_path)
        query = {"command": None, "exit_status": None, "provided_log": str(source_path),
                 "limitation": "External log supplied; this helper did not observe its query or retention window."}
        query_ok = True
    inputs[str(log)] = sha(log); inputs[str(stderr_path)] = sha(stderr_path)
    for attempt in attempts: inputs[attempt["path"]] = attempt["sha256"]
    events, malformed, reversed_order = parse_events(log.read_text(errors="replace"))
    intervals = sleep_intervals(events)
    calls = correlate(rows, events, intervals)
    capture_start, capture_finish = iso_ns(info["started_utc"]), iso_ns(info["finished_utc"])
    low = min(capture_start, capture_finish, *(r["utc_start_ns"] for r in rows), *(r["utc_end_ns"] for r in rows))
    high = max(capture_start, capture_finish, *(r["utc_start_ns"] for r in rows), *(r["utc_end_ns"] for r in rows))
    preceding = [e for e in events if e["utc_ns"] < low]
    preceding_sleep = preceding[-1] if preceding and preceding[-1]["event"] == "Sleep" else None
    relevant_intervals = [{"interval_index": index, **interval,
        "nominal_envelope_overlap_ns": intersection(low, high, interval["start_ns"], interval["end_ns"] or high)}
        for index, interval in enumerate(intervals)
        if intersection(low, high, interval["start_ns"], interval["end_ns"] or high)]
    records = {"events": events, "malformed_event_lines": malformed, "source_event_timestamp_reversals": reversed_order,
               "potential_sleep_intervals": intervals}
    write_json(output/"events.json", records)
    with (output/"call_power_associations.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(calls[0])); writer.writeheader(); writer.writerows(calls)
    assert_failed = any(attempt["explicit_assertion_failure"] for attempt in attempts)
    limitation = ("The archived caffeinate attempt explicitly failed to create PreventUserIdleSystemSleep. "
                  "Do not describe this campaign as sleep-inhibited or sleep-controlled." if assert_failed else
                  "This audit does not verify a persistent sleep-prevention assertion. An attempted or recorded assertion "
                  "does not prevent every kind of sleep, and its absence from logs proves no power-control claim.")
    monotonic = info.get("monotonic_elapsed_seconds")
    require(type(monotonic) in (int, float) and math.isfinite(monotonic) and monotonic > 0, "invalid capture duration")
    audit = {"schema": "mst_search_power_audit_v1", "validation": "pass" if query_ok and not malformed else "incomplete",
        "query": query, "raw_capture_validation": info["validation"], "raw_protocol_recertified_by_this_helper": False,
        "started_utc": info["started_utc"], "finished_utc": info["finished_utc"],
        "utc_elapsed_seconds": (capture_finish-capture_start)/NS, "monotonic_elapsed_seconds": monotonic,
        "utc_minus_monotonic_seconds": (capture_finish-capture_start)/NS-monotonic,
        "utc_correlation_envelope_ns": [low, high], "capture_clock_flags": info.get("capture_clock_flags", []),
        "recorded_clock_flagged_calls": info["flagged_calls"], "checked_calls": len(calls),
        "timed_calls": sum(r["phase"] == "timed" for r in calls), "warmup_calls": sum(r["phase"] == "warmup" for r in calls),
        "calls_with_nominal_sleep_overlap": sum(bool(r["nominal_logged_sleep_overlap_ns"]) for r in calls),
        "timed_calls_with_nominal_sleep_overlap": sum(r["phase"] == "timed" and bool(r["nominal_logged_sleep_overlap_ns"]) for r in calls),
        "calls_near_power_event": sum(bool(r["nearby_power_event_lines"]) for r in calls),
        "utc_unalignable_calls": sum(not r["utc_alignable"] for r in calls),
        "parsed_power_events": len(events), "malformed_event_lines": len(malformed),
        "power_events_within_envelope": [e for e in events if low <= e["utc_ns"] <= high],
        "last_preceding_event_if_sleep": preceding_sleep, "sleep_intervals_overlapping_envelope": relevant_intervals,
        "assertion_attempts": attempts, "power_control_limitation": limitation,
        "interpretation": "Timestamp correlations only. pmset event timestamps have one-second resolution; nearby-event "
            "columns allow a one-second boundary margin. Sleep-to-first-Wake/DarkWake intervals describe logged transitions, "
            "not measured CPU inactivity. Unclosed intervals may reflect missing log records; source timestamp reversals "
            "and native UTC reversals weaken alignment. Absence of events is not proof of no sleep or stable frequency, "
            "thermal state, contention or core placement. Overlaps do not attribute an entire solver duration to sleep.",
        "rows_removed": 0, "rows_adjusted": 0, "input_sha256": inputs, "script_sha256": sha(Path(__file__).resolve()),
        "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}}
    require(all(sha(Path(p)) == value for p, value in inputs.items()), "input changed during audit")
    write_json(output/"audit.json", audit)
    print(f"Power audit {audit['validation']}: {len(calls)} retained calls; "
          f"{audit['calls_with_nominal_sleep_overlap']} nominal logged-sleep overlaps. {limitation}")


if __name__ == "__main__":
    main()
