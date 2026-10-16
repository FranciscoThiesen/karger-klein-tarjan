#!/usr/bin/env python3
"""Explicit recovery adapter for the two unstarted attachment-confirmation B cases.

The six frozen helpers remain byte-for-byte unchanged. Their capture loop, native
command, row/certificate validation and analysis are reused. Only monitoring,
bounded error cleanup, provenance and recovery-specific validation are adapted.
This file is a seventh captured/analysis helper, never an original-only campaign.
"""
import argparse
import copy
import ctypes
import errno
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

import run_mst_search as capture
import analyze_mst_search as analysis

ORIGINAL_HELPERS = capture.helpers
ORIGINAL_WRITE_JSON = capture.write_json
ORIGINAL_LOAD = analysis.load
ORIGINAL_REPORT = analysis.report
ADAPTER = Path(__file__).resolve()
TIMEOUT_SECONDS = 5.0
TERM_SECONDS = 10.0
KILL_SECONDS = 5.0
EXPECTED_BINARY_SHA256 = "8188f6b8717a0a4b4261369ac589ca0a65f2247ebfbfb8c56f98a544bd156faf"
EXPECTED_CASES = [("leaf_hierarchy4", 262144, 16, 0), ("leaf_distance4", 1048576, 16, 0)]
RSS_MEASURE = "Sum of libproc resident bytes rounded up per member to KiB over owned process group; sampled, not continuous peak"
PROTOCOL = {
    "schema": "mst_search_monitor_recovery_v1",
    "campaign": "attachment-confirmation-b-monitor-recovery",
    "original_b_status": "failed; never relabeled, rewritten or resumed in place",
    "provider": "macOS libproc proc_listpids(PROC_PGRP_ONLY), PROC_PIDTASKINFO resident bytes",
    "scope": "Only the owned native child's newly created process group; no global process inventory",
    "rss_conversion": "Each member's resident bytes rounded upward to KiB; sum members; shared pages may repeat",
    "sampler": "One daemon worker at a time; no worker/context-manager joins; timed-out result permanently discarded",
    "sample_wait_limit_seconds": TIMEOUT_SECONDS,
    "timeout_policy": "Timeout disables this sampler permanently. Three consecutive unavailable observations stop an active child; a completed child cannot advance to another child after a timeout.",
    "ordinary_failure_policy": "Terminate above 40 GiB or after three consecutive unavailable observations; retain partial artifacts",
    "cleanup": "Owned session/group TERM then bounded wait, KILL then bounded wait; group verification bounded by sampler; unknown exit fails closed",
    "term_wait_seconds": TERM_SECONDS,
    "kill_wait_seconds": KILL_SECONDS,
    "native_measurement_change": "None: original binary, commands, clocks, boundaries, solver order, rows and certificate checks",
    "protocol_deviation": "Recovery-only replacement of blocked ps RSS monitoring and unbounded cleanup; seven-helper inventory includes this adapter; sampler durations and gaps are descriptive, not native elapsed-time adjustments",
}


def helpers():
    return {**ORIGINAL_HELPERS(), str(ADAPTER): capture.sha(ADAPTER)}


class TaskInfo(ctypes.Structure):
    # Darwin SDK sys/proc_info.h, struct proc_taskinfo (96 bytes).
    _fields_ = [(name, ctypes.c_uint64) for name in
                ("virtual_size", "resident_size", "total_user", "total_system", "threads_user", "threads_system")]
    _fields_ += [(name, ctypes.c_int32) for name in
                 ("policy", "faults", "pageins", "cow_faults", "messages_sent", "messages_received",
                  "syscalls_mach", "syscalls_unix", "csw", "threadnum", "numrunning", "priority")]


class LibprocProvider:
    """Enumerate one explicitly supplied group; every listed member must be read."""
    def __init__(self):
        capture.base.require(sys.platform == "darwin", "recovery requires macOS libproc")
        self.lib = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
        self.lib.proc_listpids.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_int]
        self.lib.proc_listpids.restype = ctypes.c_int
        self.lib.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
        self.lib.proc_pidinfo.restype = ctypes.c_int
        self.lib.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
        self.lib.proc_pidpath.restype = ctypes.c_int
        capture.base.require(ctypes.sizeof(TaskInfo) == 96, "unexpected Darwin proc_taskinfo layout")

    def __call__(self, group):
        capture.base.require(type(group) is int and group > 0, "invalid owned process group")
        # Native MST children do not fork. A generous fixed buffer avoids a
        # global sizing query and fails closed rather than truncating members.
        pids = (ctypes.c_int * 1024)()
        ctypes.set_errno(0)
        count = self.lib.proc_listpids(2, group, pids, ctypes.sizeof(pids))
        error = ctypes.get_errno()
        if count < 0 or (count == 0 and error not in (0, errno.ESRCH)):
            raise OSError(error, "proc_listpids for owned group failed")
        if count >= ctypes.sizeof(pids) or count % ctypes.sizeof(ctypes.c_int):
            raise ValueError("owned group PID buffer incomplete or malformed")
        listed = [pid for pid in pids[:count // ctypes.sizeof(ctypes.c_int)] if pid > 0]
        if len(set(listed)) != len(listed):
            raise ValueError("duplicate owned group PID")
        members = []
        for pid in listed:
            if os.getpgid(pid) != group:
                raise ValueError("process left owned group during observation")
            info = TaskInfo()
            size = self.lib.proc_pidinfo(pid, 4, 0, ctypes.byref(info), ctypes.sizeof(info))
            if size != ctypes.sizeof(info):
                raise OSError(ctypes.get_errno(), "incomplete PROC_PIDTASKINFO")
            name = ctypes.create_string_buffer(4096)
            if self.lib.proc_pidpath(pid, name, len(name)) <= 0:
                raise OSError(ctypes.get_errno(), "owned member command unavailable")
            if os.getpgid(pid) != group:
                raise ValueError("process changed group during observation")
            members.append({"pid": pid, "rss_kib": (info.resident_size + 1023) // 1024,
                            "command": os.fsdecode(name.value)})
        return {"process_group": group, "members": members}


class BoundedSampler:
    """A timed-out worker can never provide a future observation or cause a join."""
    def __init__(self, provider, timeout=TIMEOUT_SECONDS):
        self.provider = provider
        self.timeout = timeout
        self.poisoned = False
        self.events = {}
        self.workers_started = 0

    def sample(self, group):
        requested = time.monotonic_ns()
        observation = {"utc": capture.now(), "monotonic_ns": requested, "process_group": group}
        history = self.events.setdefault(group, [])
        event = {"process_group": group, "requested_monotonic_ns": requested,
                 "previous_request_gap_ns": requested - history[-1]["requested_monotonic_ns"] if history else None,
                 "provider_started_monotonic_ns": None, "provider_finished_monotonic_ns": None}
        box = {}; ready = threading.Event()
        if self.poisoned:
            event["outcome"] = "disabled_after_timeout"
            observation.update(validation="unavailable", error="sampler disabled after timeout; no late result is accepted")
        else:
            def work():
                box["start"] = time.monotonic_ns()
                try:
                    result = self.provider(group)
                    capture.base.require(type(result) is dict and result.get("process_group") == group,
                                         "provider returned wrong or stale process group")
                    members = result.get("members")
                    capture.base.require(type(members) is list, "invalid provider members")
                    seen = set()
                    for member in members:
                        capture.base.require(type(member) is dict and set(member) == {"pid", "rss_kib", "command"}
                            and type(member["pid"]) is int and member["pid"] > 0 and member["pid"] not in seen
                            and type(member["rss_kib"]) is int and member["rss_kib"] >= 0
                            and type(member["command"]) is str and member["command"], "invalid provider member")
                        seen.add(member["pid"])
                    box["result"] = copy.deepcopy(members)
                except BaseException as error:
                    box["error"] = repr(error)
                finally:
                    box["finish"] = time.monotonic_ns(); ready.set()
            self.workers_started += 1
            worker = threading.Thread(target=work, name="mst-recovery-rss", daemon=True)
            worker.start()
            if not ready.wait(self.timeout):
                self.poisoned = True
                event["outcome"] = "timeout"
                event["provider_started_monotonic_ns"] = box.get("start")
                observation.update(validation="unavailable", error="libproc sampler timed out; late result discarded permanently")
            else:
                event.update(provider_started_monotonic_ns=box["start"], provider_finished_monotonic_ns=box["finish"])
                if "error" in box:
                    event["outcome"] = "unavailable"
                    observation.update(validation="unavailable", error=box["error"])
                else:
                    event["outcome"] = "pass"
                    observation.update(validation="pass", members=box["result"], rss_kib=sum(m["rss_kib"] for m in box["result"]))
        event["returned_monotonic_ns"] = time.monotonic_ns()
        event["sampler_duration_ns"] = event["returned_monotonic_ns"] - requested
        history.append(event)
        return observation


def bounded_terminate(process, sampler, term_seconds=TERM_SECONDS, kill_seconds=KILL_SECONDS):
    """Never wait without a timeout; never signal a process outside the owned session."""
    result = {"started_monotonic_ns": time.monotonic_ns(), "process_group": process.pid if process else None,
              "signals": [], "native_exit_known": False, "group_exit_known": False}
    if process is None:
        result.update(native_exit_known=True, group_exit_known=True, returncode=None)
    else:
        try:
            for sig, budget in ((signal.SIGTERM, term_seconds), (signal.SIGKILL, kill_seconds)):
                if process.poll() is not None:
                    break
                if os.getpgid(process.pid) != process.pid or os.getsid(process.pid) != process.pid:
                    raise ValueError("refusing to signal process outside its owned new session/group")
                try:
                    os.killpg(process.pid, sig)
                    result["signals"].append(sig.name)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=budget)
                except subprocess.TimeoutExpired:
                    pass
            result["returncode"] = process.poll()
            result["native_exit_known"] = type(result["returncode"]) is int
            verification = sampler.sample(process.pid)
            result["group_verification"] = verification
            result["group_exit_known"] = verification["validation"] == "pass" and not verification["members"]
        except BaseException as error:
            result["error"] = repr(error)
    result["finished_monotonic_ns"] = time.monotonic_ns()
    result["native_process_may_still_be_running"] = not (result["native_exit_known"] and result["group_exit_known"])
    return result


def recovery_monitor(events):
    return {"observations": copy.deepcopy(events),
            "max_sampler_duration_ns": max((e["sampler_duration_ns"] for e in events), default=0),
            "max_request_gap_ns": max((e["previous_request_gap_ns"] or 0 for e in events), default=0)}


def install_capture(sampler):
    cleanup = []
    groups = []
    def sample(group):
        if group not in groups:
            groups.append(group)
        return sampler.sample(group)
    def terminate(process):
        # A separate sampler for cleanup is unnecessary and could accumulate
        # stuck workers. A poisoned sampler means group exit remains unknown.
        cleanup.append(bounded_terminate(process, sampler))
    def save(path, info):
        if info.get("schema") == "mst_search_capture_v1":
            info["recovery_protocol"] = copy.deepcopy(PROTOCOL)
            info["recovery_cleanup"] = copy.deepcopy(cleanup)
            info["native_process_may_still_be_running"] = any(r["native_process_may_still_be_running"] for r in cleanup)
            info["resource_rule"].update(
                measure=RSS_MEASURE,
                failure=PROTOCOL["ordinary_failure_policy"], sample_wait_limit_seconds=TIMEOUT_SECONDS)
            for item, group in zip(info["captures"], groups):
                # Cleanup verification is separate from capture RSS observations.
                count = item.get("rss_observations", len(sampler.events[group]))
                item["recovery_monitor"] = recovery_monitor(sampler.events[group][:count])
            failed_completion = sampler.poisoned and info["captures"] and info["captures"][-1].get("validation") == "pass"
            if failed_completion:
                info.update(validation="failed", error="Completed native child has an unresolved timed-out RSS sampler; no next child may launch")
            ORIGINAL_WRITE_JSON(path, info)
            if failed_completion:
                raise RuntimeError(info["error"])
        else:
            ORIGINAL_WRITE_JSON(path, info)
    capture.helpers = helpers
    capture.sample_rss = sample
    capture.terminate = terminate
    capture.write_json = save


def validate_monitor(item):
    observations = [capture.clocks.parse_json(line) for line in Path(item["rss_log"]).read_text().splitlines()]
    monitor = item.get("recovery_monitor")
    capture.base.require(type(monitor) is dict and type(monitor.get("observations")) is list,
                         "missing recovery sampler telemetry")
    events = monitor["observations"]
    capture.base.require(len(events) == len(observations), "sampler/RSS observation count differs")
    previous = None
    for observation, event in zip(observations, events):
        analysis.equal(event, "process_group", observation["process_group"], "sampler")
        analysis.equal(event, "requested_monotonic_ns", observation["monotonic_ns"], "sampler")
        request, returned = event["requested_monotonic_ns"], event.get("returned_monotonic_ns")
        capture.base.require(type(returned) is int and request <= returned <= item["finished_monotonic_ns"], "invalid sampler return time")
        analysis.equal(event, "previous_request_gap_ns", None if previous is None else request - previous, "sampler")
        analysis.equal(event, "sampler_duration_ns", returned - request, "sampler")
        started, finished = event.get("provider_started_monotonic_ns"), event.get("provider_finished_monotonic_ns")
        capture.base.require(event.get("outcome") in ("pass", "unavailable"), "successful recovery contains a timed-out or disabled sampler")
        capture.base.require(type(started) is int and type(finished) is int and request <= started <= finished <= returned,
                             "invalid provider interval")
        analysis.equal(event, "outcome", observation["validation"], "sampler")
        previous = request
    analysis.equal(item, "recovery_monitor", recovery_monitor(events), "sampler summary")


def validate_fixed_protocol(cases, info):
    """Bind this recovery label to the declared tail at capture and analysis."""
    fields = ("family", "n", "density", "intrusion_per_mille")
    capture.base.require([tuple(spec[field] for field in fields) for spec in cases.values()] == EXPECTED_CASES,
                         "recovery manifest must contain exactly the two unstarted B cases in order")
    for field, value in (("graph_seeds", [1000039, 1000081, 1000099]), ("sampling_seeds", [401, 503]),
                         ("repetitions", 5), ("warmups", 1), ("binary_sha256", EXPECTED_BINARY_SHA256)):
        analysis.equal(info, field, value, "fixed recovery protocol")
    analysis.equal(info["resource_rule"], "rss_limit_kib", 40 * 1024**2, "fixed recovery protocol")
    poll = info["resource_rule"].get("poll_seconds")
    capture.base.require(type(poll) in (int, float) and poll == 2,
                         "fixed recovery protocol: poll interval must be two seconds")


def load(timing_path, manifest_path=None):
    result = ORIGINAL_LOAD(timing_path, manifest_path)
    info = result[0]
    validate_fixed_protocol(result[1], info)
    analysis.equal(info, "recovery_protocol", PROTOCOL, "recovery")
    analysis.equal(info, "recovery_cleanup", [], "successful recovery")
    analysis.equal(info, "native_process_may_still_be_running", False, "successful recovery")
    analysis.equal(info, "python_source_sha256", helpers(), "recovery helpers")
    analysis.equal(info["resource_rule"], "measure", RSS_MEASURE, "recovery resource rule")
    analysis.equal(info["resource_rule"], "failure", PROTOCOL["ordinary_failure_policy"], "recovery resource rule")
    analysis.equal(info["resource_rule"], "sample_wait_limit_seconds", TIMEOUT_SECONDS, "recovery resource rule")
    for item in info["captures"]:
        validate_monitor(item)
    return result


def report(info, cases, tables):
    return ("# Separately labeled monitor recovery\n\n"
            "The original confirmation B remains failed. This capture covers only its two unstarted cases. "
            "RSS monitoring uses the recorded libproc recovery adapter; native timing and row validation are unchanged. "
            "Per-observation sampler duration and sampling gaps are retained in provenance.\n\n" +
            ORIGINAL_REPORT(info, cases, tables))


def install_analysis():
    capture.helpers = helpers
    analysis.HELPER_NAMES = {Path(path).name for path in helpers()}
    analysis.load = load
    analysis.report = report


def capture_arguments(arguments):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("binary", "manifest", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("graph-seeds", "sampling-seeds"):
        parser.add_argument("--" + name, type=capture.base.seed_bank, required=True)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--rss-limit-gib", type=int, default=40)
    parser.add_argument("--rss-poll-seconds", type=float, default=2)
    args = parser.parse_args(arguments)
    cases = capture.load_manifest(args.manifest.resolve(strict=True))
    validate_fixed_protocol(cases, {"graph_seeds": list(args.graph_seeds), "sampling_seeds": list(args.sampling_seeds),
        "repetitions": args.repetitions, "warmups": args.warmups, "binary_sha256": capture.sha(args.binary),
        "resource_rule": {"rss_limit_kib": args.rss_limit_gib * 1024**2, "poll_seconds": args.rss_poll_seconds}})
    return args


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("capture", "analyze"))
    parser.add_argument("--released", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    args, rest = parser.parse_known_args()
    if args.action == "capture":
        options = capture_arguments(rest)
        if args.preflight_only:
            print(json.dumps({"validation": "pass", "native_capture_started": False,
                "recovery_protocol": PROTOCOL, "python_source_sha256": helpers(),
                "binary_sha256": capture.sha(options.binary), "manifest_sha256": capture.sha(options.manifest)}, indent=2))
            return
        capture.base.require(args.released, "explicit parent scheduling --released is required")
        install_capture(BoundedSampler(LibprocProvider()))
        sys.argv = [str(ADAPTER), *rest]
        capture.main()
    else:
        capture.base.require(not args.released and not args.preflight_only, "release/preflight only apply to capture")
        install_analysis()
        sys.argv = [str(ADAPTER), *rest]
        analysis.main()


if __name__ == "__main__":
    main()
