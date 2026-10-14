#!/usr/bin/env python3
"""Synthetic monitor/capture tests. Never builds or executes an MST binary."""
import contextlib
import copy
import csv
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

import recover_mst_search as recovery

capture, analysis = recovery.capture, recovery.analysis


def member(group, rss=1024):
    return {"process_group": group, "members": [{"pid": group, "rss_kib": rss, "command": "synthetic-only"}]}


class FakeProcess:
    def __init__(self, pid=424242, exits=True):
        self.pid = pid; self.returncode = None; self.exits = exits; self.waits = []
    def poll(self):
        return self.returncode
    def wait(self, timeout):
        self.waits.append(timeout)
        if self.exits:
            self.returncode = 0
            return 0
        raise subprocess.TimeoutExpired("synthetic-only", timeout)


class MonitorTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform == "darwin", "macOS libproc ABI smoke")
    def test_libproc_reads_only_disposable_owned_python_group(self):
        # This independently exercises the real Darwin ABI without /bin/ps,
        # global inventories, native MST execution, or an inherited group.
        process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
        sampler = recovery.BoundedSampler(recovery.LibprocProvider(), .5)
        try:
            observation = sampler.sample(process.pid)
            self.assertEqual(observation["validation"], "pass", observation)
            self.assertEqual([m["pid"] for m in observation["members"]], [process.pid])
            self.assertGreater(observation["rss_kib"], 0)
        finally:
            result = recovery.bounded_terminate(process, sampler, .5, .5)
            self.assertFalse(result["native_process_may_still_be_running"], result)

    def test_success_and_scoped_group(self):
        provider = mock.Mock(side_effect=member)
        sampler = recovery.BoundedSampler(provider, .1)
        rows = [sampler.sample(77), sampler.sample(77)]
        self.assertTrue(all(row["validation"] == "pass" for row in rows))
        self.assertEqual(provider.call_args_list, [mock.call(77), mock.call(77)])
        self.assertEqual(sampler.workers_started, 2)
        self.assertGreater(sampler.events[77][1]["previous_request_gap_ns"], 0)
        for event in sampler.events[77]:
            self.assertLessEqual(event["provider_finished_monotonic_ns"], event["returned_monotonic_ns"])

    def test_wrong_group_and_provider_failure(self):
        for provider in (lambda group: member(group + 1), mock.Mock(side_effect=OSError("synthetic unavailable"))):
            sampler = recovery.BoundedSampler(provider, .1)
            self.assertEqual(sampler.sample(77)["validation"], "unavailable")
            self.assertFalse(sampler.poisoned)

    def test_stuck_worker_has_no_thread_growth_and_late_result_is_discarded(self):
        gate = threading.Event()
        def blocked(group):
            gate.wait(); return member(group)
        sampler = recovery.BoundedSampler(blocked, .02)
        begin = time.monotonic()
        try:
            first = sampler.sample(77)
            self.assertLess(time.monotonic() - begin, 1)
            self.assertEqual(first["validation"], "unavailable")
            for _ in range(20):
                self.assertEqual(sampler.sample(77)["validation"], "unavailable")
            self.assertEqual(sampler.workers_started, 1)
            snapshot = copy.deepcopy(sampler.events)
            gate.set()
            # Wait for provider completion explicitly in the test, never via
            # production cleanup or an interpreter worker join.
            time.sleep(.02)
            self.assertEqual(sampler.events, snapshot)
            self.assertEqual(sampler.sample(88)["validation"], "unavailable")
            self.assertEqual(sampler.workers_started, 1)
            self.assertEqual(sampler.events[77][0]["outcome"], "timeout")
            self.assertIsNone(sampler.events[77][0]["provider_finished_monotonic_ns"])
        finally:
            gate.set()

    def test_cleanup_known_exit_and_unknown_exit(self):
        empty = recovery.BoundedSampler(lambda group: {"process_group": group, "members": []}, .02)
        process = FakeProcess(exits=True)
        with mock.patch.object(recovery.os, "getpgid", return_value=process.pid), \
             mock.patch.object(recovery.os, "getsid", return_value=process.pid), \
             mock.patch.object(recovery.os, "killpg") as kill:
            result = recovery.bounded_terminate(process, empty, .01, .01)
        self.assertEqual(kill.call_args_list, [mock.call(process.pid, signal.SIGTERM)])
        self.assertFalse(result["native_process_may_still_be_running"])
        self.assertEqual(process.waits, [.01])
        process = FakeProcess(exits=False)
        with mock.patch.object(recovery.os, "getpgid", return_value=process.pid), \
             mock.patch.object(recovery.os, "getsid", return_value=process.pid), \
             mock.patch.object(recovery.os, "killpg") as kill:
            result = recovery.bounded_terminate(process, empty, .01, .02)
        self.assertEqual(process.waits, [.01, .02])
        self.assertEqual([call.args[1] for call in kill.call_args_list], [signal.SIGTERM, signal.SIGKILL])
        self.assertTrue(result["native_process_may_still_be_running"])
        self.assertFalse(result["native_exit_known"])

    def test_cleanup_rejects_foreign_group_and_surviving_members(self):
        sampler = recovery.BoundedSampler(member, .02)
        process = FakeProcess()
        with mock.patch.object(recovery.os, "getpgid", return_value=1), \
             mock.patch.object(recovery.os, "killpg") as kill:
            result = recovery.bounded_terminate(process, sampler, .01, .01)
        kill.assert_not_called()
        self.assertTrue(result["native_process_may_still_be_running"])
        process.returncode = 0
        result = recovery.bounded_terminate(process, sampler, .01, .01)
        self.assertTrue(result["native_exit_known"])
        self.assertFalse(result["group_exit_known"])

    def test_cleanup_does_not_join_timed_out_worker(self):
        gate = threading.Event()
        sampler = recovery.BoundedSampler(lambda group: (gate.wait(), member(group))[1], .02)
        process = FakeProcess(); process.returncode = 0
        try:
            sampler.sample(process.pid)
            begin = time.monotonic()
            result = recovery.bounded_terminate(process, sampler, .01, .01)
            self.assertLess(time.monotonic() - begin, .2)
            self.assertTrue(result["native_process_may_still_be_running"])
            self.assertEqual(sampler.workers_started, 1)
        finally:
            gate.set()

    def test_real_interpreter_exit_does_not_join_daemon(self):
        # This launches only the Python interpreter and a blocked synthetic
        # provider. It does not inspect processes or launch native benchmarks.
        program = ("import sys, threading; sys.path.insert(0, " + repr(str(recovery.ADAPTER.parent)) + "); "
                   "import recover_mst_search as r; "
                   "s=r.BoundedSampler(lambda g: threading.Event().wait(), .02); "
                   "assert s.sample(7)['validation']=='unavailable'; print('daemon-exit-pass',flush=True)")
        result = subprocess.run([sys.executable, "-c", program], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "daemon-exit-pass")


def synthetic_rows(command):
    args = dict(zip(command[3::2], command[4::2]))
    spec = {"family": args["--family"], "n": int(args["--n"]), "density": int(args["--density"]), "intrusion_per_mille": 0}
    spec.update(m=spec["n"] * spec["density"], case_id=capture.base.case_id(spec))
    rows = []; cpu = 0; utc = 1_000_000_000
    for phase, count in (("warmup", 1), ("timed", 5)):
        for rep in range(count):
            for order in range(5):
                algorithm = capture.ALGORITHMS[(order + rep) % 5]; duration = 1000 * (capture.ALGORITHMS.index(algorithm) + 1)
                rows.append({**spec, "graph_seed": int(args["--graph-seed"]), "kkt_seed": int(args["--kkt-seed"]),
                    "input_fingerprint": 9, "topology_fingerprint": 8, "phase": phase, "repetition": rep, "order": order,
                    "warmups": 1, "algorithm": algorithm, "elapsed_ns": duration, "utc_start_ns": utc, "utc_end_ns": utc + duration,
                    "process_cpu_start_ns": cpu, "process_cpu_end_ns": cpu + duration, "process_cpu_elapsed_ns": duration, "validation": "pass"})
                cpu += duration + 10; utc += duration + 10
    return rows


class CaptureTests(unittest.TestCase):
    def test_capture_cli_accepts_only_declared_tail(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest = Path(folder) / "manifest.csv"
            manifest.write_text("family,n,density,intrusion_per_mille\nleaf_hierarchy4,262144,16,0\nleaf_distance4,1048576,16,0\n")
            arguments = ["--binary", str(Path(folder) / "never-executed"), "--manifest", str(manifest),
                         "--output", str(Path(folder) / "never-created.csv"), "--graph-seeds", "1000039,1000081,1000099",
                         "--sampling-seeds", "401,503", "--rss-poll-seconds", "2"]
            with mock.patch.object(capture, "sha", return_value=recovery.EXPECTED_BINARY_SHA256):
                recovery.capture_arguments(arguments)
                changed = list(arguments); changed[changed.index("401,503")] = "503,401"
                with self.assertRaisesRegex(ValueError, "seeds"):
                    recovery.capture_arguments(changed)
                manifest.write_text("family,n,density,intrusion_per_mille\nleaf_distance4,1048576,16,0\nleaf_hierarchy4,262144,16,0\n")
                with self.assertRaisesRegex(ValueError, "manifest"):
                    recovery.capture_arguments(arguments)

    def run_synthetic(self, folder, provider, exits=True):
        folder = Path(folder); manifest = folder / "manifest.csv"; binary = folder / "synthetic-not-executable"
        manifest.write_text("family,n,density,intrusion_per_mille\nleaf_hierarchy4,262144,16,0\nleaf_distance4,1048576,16,0\n")
        binary.write_text("This file is never executed.\n")
        output = folder / "capture.csv"; children = []
        def popen(command, **kwargs):
            self.assertEqual(command[:2], ["/usr/bin/time", "-l"])
            self.assertTrue(kwargs["start_new_session"])
            rows = synthetic_rows(command)
            writer = csv.DictWriter(kwargs["stdout"], fieldnames=capture.FIELDS); writer.writeheader(); writer.writerows(rows)
            kwargs["stdout"].flush()
            kwargs["stderr"].write(capture.CERTIFICATE_PREFIX + json.dumps({f: rows[0][f] for f in capture.CERTIFICATE_FIELDS}) + "\n")
            kwargs["stderr"].flush()
            process = FakeProcess(424242 + len(children), exits=exits); children.append(process); return process
        sampler = recovery.BoundedSampler(provider, .02)
        profile = {"file_description": "Mach-O 64-bit executable arm64", "main_stack_bytes": 536870912,
                   "otool_load_commands": "cmd LC_MAIN\ncmdsize 24\nentryoff 0\nstacksize 536870912"}
        argv = ["synthetic-capture", "--binary", str(binary), "--manifest", str(manifest), "--output", str(output),
                "--graph-seeds", "1000039,1000081,1000099", "--sampling-seeds", "401,503"]
        error = None
        with contextlib.ExitStack() as stack:
            for name in ("helpers", "sample_rss", "terminate", "write_json"):
                stack.enter_context(mock.patch.object(capture, name, getattr(capture, name)))
            recovery.install_capture(sampler)
            real_sha = capture.sha
            stack.enter_context(mock.patch.object(capture, "sha", side_effect=lambda path:
                recovery.EXPECTED_BINARY_SHA256 if Path(path).resolve() == binary.resolve() else real_sha(path)))
            stack.enter_context(mock.patch.object(capture, "binary_profile", return_value=profile))
            stack.enter_context(mock.patch.object(capture.subprocess, "Popen", side_effect=popen))
            stack.enter_context(mock.patch.object(capture.subprocess, "check_output", return_value="synthetic-revision\n"))
            stack.enter_context(mock.patch.object(capture.platform, "platform", return_value="synthetic macOS"))
            stack.enter_context(mock.patch.object(capture.signal, "signal"))
            stack.enter_context(mock.patch.object(recovery.os, "getpgid", side_effect=lambda pid: pid))
            stack.enter_context(mock.patch.object(recovery.os, "getsid", side_effect=lambda pid: pid))
            stack.enter_context(mock.patch.object(recovery.os, "killpg"))
            stack.enter_context(mock.patch.object(sys, "argv", argv))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            try:
                capture.main()
            except (ValueError, RuntimeError) as exception:
                error = exception
        return output, json.loads(output.with_suffix(".json").read_text()), children, sampler, error

    def test_success_reuses_complete_strict_capture_and_analysis(self):
        with tempfile.TemporaryDirectory() as folder:
            output, info, children, sampler, error = self.run_synthetic(folder, member)
            self.assertIsNone(error)
            self.assertEqual(info["validation"], "pass")
            self.assertEqual(len(children), 12)
            self.assertEqual((info["checked_timed_rows"], info["checked_warmup_rows"]), (300, 60))
            self.assertEqual(len(info["python_source_sha256"]), 7)
            with mock.patch.object(analysis, "HELPER_NAMES", {Path(p).name for p in recovery.helpers()}):
                loaded = recovery.load(output)
                self.assertEqual(len(loaded[2]), 360)
                # The frozen original-only inventory cannot accept recovery.
            with self.assertRaisesRegex(ValueError, "helper inventory"):
                recovery.ORIGINAL_LOAD(output)
            for mutate in (lambda x: x.pop("recovery_protocol"),
                           lambda x: x["captures"][0]["recovery_monitor"]["observations"][0].update(process_group=7),
                           lambda x: x["captures"][0]["recovery_monitor"]["observations"][0].update(sampler_duration_ns=1),
                           lambda x: x["captures"][0]["recovery_monitor"]["observations"][0].update(outcome="timeout"),
                           lambda x: x["resource_rule"].update(measure="ps RSS"),
                           lambda x: x.update(native_process_may_still_be_running=True)):
                changed = copy.deepcopy(info); mutate(changed); recovery.ORIGINAL_WRITE_JSON(output.with_suffix(".json"), changed)
                with mock.patch.object(analysis, "HELPER_NAMES", {Path(p).name for p in recovery.helpers()}), self.assertRaises(ValueError):
                    recovery.load(output)

    def test_standalone_analysis_rejects_otherwise_valid_changed_protocol(self):
        with tempfile.TemporaryDirectory() as folder:
            output, info, children, sampler, error = self.run_synthetic(folder, member)
            self.assertIsNone(error)
            with mock.patch.object(analysis, "HELPER_NAMES", {Path(p).name for p in recovery.helpers()}):
                self.assertEqual(len(recovery.load(output)[2]), 360)
                for field, mutate in (("binary_sha256", lambda x: x.update(binary_sha256="b" * 64)),
                                      ("rss_limit_kib", lambda x: x["resource_rule"].update(rss_limit_kib=39 * 1024**2)),
                                      ("poll interval", lambda x: x["resource_rule"].update(poll_seconds=3))):
                    changed = copy.deepcopy(info); mutate(changed)
                    recovery.ORIGINAL_WRITE_JSON(output.with_suffix(".json"), changed)
                    # These complete bundles pass the original generic capture
                    # contract; only the declared recovery contract rejects them.
                    self.assertEqual(len(recovery.ORIGINAL_LOAD(output)[2]), 360)
                    with self.assertRaisesRegex(ValueError, "fixed recovery protocol: .*" + field):
                        recovery.load(output)

    def test_three_unavailable_samples_stop_before_second_child(self):
        with tempfile.TemporaryDirectory() as folder:
            output, info, children, sampler, error = self.run_synthetic(folder, mock.Mock(side_effect=OSError("synthetic failure")), exits=False)
            self.assertIn("three consecutive", str(error))
            self.assertEqual(info["validation"], "failed")
            self.assertEqual(len(children), 1)
            self.assertEqual(info["captures"][0]["rss_unavailable"], 3)
            self.assertTrue(info["native_process_may_still_be_running"])

    def test_ceiling_stops_before_second_child(self):
        with tempfile.TemporaryDirectory() as folder:
            output, info, children, sampler, error = self.run_synthetic(folder, lambda group: member(group, 40 * 1024**2 + 1), exits=False)
            self.assertIn("ceiling", str(error))
            self.assertEqual(len(children), 1)
            self.assertEqual(info["captures"][0]["sampled_peak_rss_kib"], 40 * 1024**2 + 1)

    def test_native_exit_during_timed_out_sample_cannot_authorize_next_child(self):
        gate = threading.Event()
        try:
            with tempfile.TemporaryDirectory() as folder:
                output, info, children, sampler, error = self.run_synthetic(folder, lambda group: (gate.wait(), member(group))[1])
                self.assertEqual(info["validation"], "failed")
                self.assertIn("unresolved timed-out", str(error))
                self.assertEqual(len(children), 1)
                self.assertEqual(info["captures"][0]["exit_status"], 0)
                self.assertEqual(sampler.workers_started, 1)
        finally:
            gate.set()

    def test_native_running_after_timeout_has_bounded_unknown_cleanup(self):
        gate = threading.Event()
        try:
            with tempfile.TemporaryDirectory() as folder:
                output, info, children, sampler, error = self.run_synthetic(folder, lambda group: (gate.wait(), member(group))[1], exits=False)
                self.assertIn("three consecutive", str(error))
                self.assertEqual(len(children), 1)
                self.assertEqual(info["captures"][0]["rss_unavailable"], 3)
                self.assertTrue(info["native_process_may_still_be_running"])
                self.assertEqual(sampler.workers_started, 1)
        finally:
            gate.set()


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({"schema": "mst_search_recovery_synthetic_tests_v1", "validation": "pass" if result.wasSuccessful() else "failed",
        "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "native_mst_executions": 0, "native_builds": 0,
        "adapter_sha256": capture.sha(recovery.ADAPTER), "test_sha256": capture.sha(__file__),
        "frozen_helpers_sha256": recovery.ORIGINAL_HELPERS()}, indent=2))
    sys.exit(0 if result.wasSuccessful() else 1)
