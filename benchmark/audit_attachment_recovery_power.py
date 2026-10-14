#!/usr/bin/env python3
"""Supplement the frozen power auditor with correct Wake Requests handling.

Uses unchanged capture validation, interval correlation and retained raw files.
Only actual Wake/DarkWake transitions close Sleep; scheduling notices do not.
Outputs stay separate from every original audit. Run only after native timing.
"""
import argparse
import json
from pathlib import Path
import re
import sys

import audit_mst_search_power as original

ORIGINAL_PARSE = original.parse_events
PARSER = "wake_requests_excluded_v1"
REQUEST = re.compile(r"^\d{4}-\d\d-\d\d\s+\d\d:\d\d:\d\d\s+[+-]\d{4}\s+Wake\s+Requests\b")


def parse_events(text):
    events,malformed,reversals=ORIGINAL_PARSE(text)
    return [e for e in events if not REQUEST.match(e["raw"])],malformed,reversals


def self_test():
    text="\n".join(("2026-10-14 00:00:00 +0000 Sleep Entering Sleep state 803 secs",
                    "2026-10-14 00:00:01 +0000 Wake Requests request=Maintenance",
                    "2026-10-14 00:13:23 +0000 Wake Wake from Deep Idle"))
    events,malformed,reversals=parse_events(text)
    original.require(len(events)==2 and not malformed and not reversals,"transition filtering failed")
    interval=original.sleep_intervals(events)[0]
    original.require(interval["end_ns"]-interval["start_ns"]==803_000_000_000,"request prematurely ended sleep")
    original.parse_events=parse_events
    checks=original.self_test()
    return {**checks,"power_event_parser":PARSER,"additional_check":"Wake Requests does not close the 803-second interval"}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timing-csv",type=Path)
    source=parser.add_mutually_exclusive_group()
    source.add_argument("--power-log",type=Path);source.add_argument("--query-pmset",action="store_true")
    parser.add_argument("--inhibition-json",type=Path,action="append",default=[])
    parser.add_argument("--output-dir",type=Path)
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(),indent=2));return
    original.require(args.timing_csv and args.output_dir and (args.power_log or args.query_pmset),
                     "timing CSV, output directory and one power source are required")
    original.parse_events=parse_events
    # The original CLI consumes this same explicitly compatible argument list.
    # Its strict successful-capture loader still rejects the original failed B.
    original.main()
    path=args.output_dir.resolve()/"audit.json"
    record=original.json_read(path.read_text())
    record["power_event_parser"]=PARSER
    record["parser_difference"]="Wake Requests are scheduling records, not wake transitions; retained in the complete raw log, excluded only from event-state construction. No native observation is excluded or corrected."
    record["underlying_auditor_sha256"]=original.sha(original.__file__)
    record["script_sha256"]=original.sha(__file__)
    record["input_sha256"].update({str(Path(__file__).resolve()):original.sha(__file__),
                                   str(Path(original.__file__).resolve()):original.sha(original.__file__)})
    original.write_json(path,record)


if __name__=="__main__":main()
