#!/usr/bin/env python3
"""Focused producer-control mocks; no Git, compiler, library or solver launches."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import build_library_main as producer


class ProducerTests(unittest.TestCase):
    def test_guarded_exact_argv_forwarding_and_bounded_failure_intervals(self):
        guard=mock.Mock(); stream=io.StringIO(); stderr=io.StringIO()
        state=dict(attempted_commands=[],recipe_sha256={}); intervals=[]; command=["/synthetic/not-executed","with space"]
        with mock.patch.object(producer.time,"monotonic_ns",side_effect=[10,20]),mock.patch.object(producer,"recipes",return_value={}):
            producer.guarded(guard,command,stream,intervals,state,stderr=stderr,env={"SAFE":"value"})
        guard.run.assert_called_once_with(command,stdout=stream,stderr=stderr,env={"SAFE":"value"})
        self.assertEqual(state["attempted_commands"],[command])
        self.assertEqual(state["command_intervals"],intervals)
        self.assertEqual(intervals[0]["finished_monotonic_ns"],20)
        for error,finish in ((RuntimeError("synthetic guard failure"),30),(None,300*10**9+11)):
            guard.reset_mock(); guard.run.side_effect=error; failed=[]; status=dict(attempted_commands=[],recipe_sha256={})
            with mock.patch.object(producer.time,"monotonic_ns",side_effect=[10,finish]),mock.patch.object(producer,"recipes",return_value={}),self.assertRaises((RuntimeError,ValueError)):
                producer.guarded(guard,command,io.StringIO(),failed,status)
            self.assertEqual(guard.run.call_count,1)
            self.assertEqual(failed[0]["finished_monotonic_ns"],finish)
            self.assertEqual(status["command_intervals"],failed)
        guard.reset_mock()
        with mock.patch.object(producer,"recipes",return_value={"drift":"b"*64}),self.assertRaisesRegex(ValueError,"before next child"):
            producer.guarded(guard,command,io.StringIO(),[],dict(attempted_commands=[],recipe_sha256={}))
        guard.run.assert_not_called()

    def test_failed_phase_preserves_receipt_and_exclusive_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            destination=Path(directory)/"attempt"
            argv=["build_library_main.py","build","--parent-freeze","/synthetic/freeze",
                  "--library-source","/synthetic/source","--build-directory","/synthetic/build",
                  "--output",str(destination),"--released"]
            with mock.patch.object(producer.sys,"argv",argv),mock.patch.object(producer,"recipes",return_value={"synthetic":"a"*64}), \
                 mock.patch.object(producer.inherited,"ROOT",producer.ROOT),mock.patch.object(producer,"build",side_effect=RuntimeError("synthetic phase failure")) as run:
                with self.assertRaisesRegex(RuntimeError,"synthetic phase failure"): producer.main()
                receipt=json.loads((destination/"attempt.json").read_text())
                self.assertEqual(receipt["validation"],"failed")
                self.assertIs(receipt["all_owned_groups_verified_empty"],False)
                self.assertTrue((destination/"invocation.json").is_file())
                with self.assertRaises(FileExistsError): producer.main()
                self.assertEqual(run.call_count,1)

    def test_source_drift_and_missing_release_never_report_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            destination=Path(directory)/"attempt"
            argv=["build_library_main.py","smoke","--build-record","/synthetic/record","--output",str(destination)]
            with mock.patch.object(producer.sys,"argv",argv),mock.patch.object(producer,"smoke") as run:
                with self.assertRaisesRegex(ValueError,"release"): producer.main()
                run.assert_not_called(); self.assertFalse(destination.exists())
            with mock.patch.object(producer.sys,"argv",argv+["--released"]),mock.patch.object(producer.inherited,"ROOT",producer.ROOT), \
                 mock.patch.object(producer,"recipes",side_effect=[{"source":"a"*64},{"source":"b"*64}]), \
                 mock.patch.object(producer,"smoke") as run:
                with self.assertRaisesRegex(ValueError,"source recipe changed"): producer.main()
                self.assertEqual(run.call_count,1)
            receipt=json.loads((destination/"attempt.json").read_text())
            self.assertEqual(receipt["validation"],"failed")
            self.assertIn("source recipe changed",receipt["error"])


if __name__=="__main__": unittest.main(verbosity=2)
