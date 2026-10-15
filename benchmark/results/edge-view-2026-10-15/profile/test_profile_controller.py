"""Mocked lifecycle gates: no native driver, profiler, libproc or subprocess runs."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).with_name("profile_controller.py")
spec = importlib.util.spec_from_file_location("profile_controller", SOURCE)
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)


class Lifecycle(unittest.TestCase):
    def exercise(self, mode):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); output = root / "capture"
            here = root / "profile_controller.py"; here.write_text("mock controller\n")
            obj = root / "kkt_profile.o"; obj.write_bytes(b"mock object")
            binary = root / "kkt_profile"; binary.write_bytes(b"mock executable, never run")
            prepared_path = root / "prepared.json"; prepared_path.write_text("{}\n")
            build_path = root / "build.json"; build_path.write_text("{}\n")
            prepared = {"binary": str(binary)}
            build = {"binary_sha256": controller.native.sha(binary), "driver_object_sha256": controller.native.sha(obj)}
            clock = [0.0]; children = {}; cleanup = []; sample_reads = []; sampler = None
            def marker(event, rep=-1): return {"event": event, "repetition": rep, "utc_ns": 1}
            def write_markers(child, rows):
                for row in rows: child.stdout.write(("profile_v1 " + json.dumps(row) + "\n").encode())
                child.stdout.flush()
            def finish_driver():
                child = children["driver"]
                if child.returncode is not None: return
                rows = [marker(event, rep) for rep in range(4) for event in ("KKT_BEGIN", "KKT_END", "VALIDATED")]
                if mode != "missing_done": rows.append(marker("DONE"))
                write_markers(child, rows); child.returncode = 0
                (output / "sample.txt").write_text("mock sample report\n")
                if mode == "prepared_drift": prepared_path.write_text('{"drift":true}\n')
            class Pipe:
                closed = False
                def write(self, data):
                    if mode in ("broken_pipe", "unknown_exit"): raise BrokenPipeError("mock write failure")
                    assert data == b"G"; children["driver"].released = True
                def flush(self): pass
                def close(self):
                    if mode in ("broken_pipe", "unknown_exit"): raise BrokenPipeError("mock close failure")
                    self.closed = True
            class Process:
                def __init__(self, argv, **kwargs):
                    self.name = "sample" if argv[0] == "/usr/bin/sample" else "driver"
                    assert kwargs["start_new_session"] is True
                    self.pid = 10001 if self.name == "driver" else 10002
                    self.returncode = None; self.released = False
                    self.stdin = Pipe() if self.name == "driver" else None
                    self.stdout = kwargs["stdout"]; children[self.name] = self
                    if self.name == "driver":
                        ready = {**{k: v for k, v in controller.FIXTURE.items() if k != "intrusion_per_mille"},
                                 "event": "READY", "pid": self.pid, "validation": "pass",
                                 "input_fingerprint": 1, "topology_fingerprint": 2}
                        write_markers(self, [marker("GENERATION_BEGIN"), marker("CERTIFICATE_BEGIN"), ready])
                    else:
                        self.stdout.write(b"Sampling process 10001 for 60 seconds\n"); self.stdout.flush()
                        if mode == "sample_failure": self.returncode = 1
                def poll(self):
                    if children["driver"].released and clock[0] >= 4: finish_driver()
                    if self.name == "sample" and children["driver"].returncode == 0: self.returncode = 0
                    return self.returncode
            class Sampler:
                poisoned = False
                events = {}
                def __init__(self, provider): pass
                def sample(self, group):
                    sample_reads.append((clock[0], group))
                    if mode == "poisoned":
                        self.poisoned = True
                        return {"process_group": group, "validation": "unavailable", "error": "mock timeout"}
                    child = next(c for c in children.values() if c.pid == group)
                    alive = child.returncode is None
                    rss = 21 * 1024**2 if mode == "combined_rss" and alive else (100 if alive else 0)
                    return {"process_group": group, "validation": "pass", "rss_kib": rss,
                            "members": [{"pid": group, "rss_kib": rss, "command": "mock"}] if alive else []}
            def terminate(child, observed):
                cleanup.append(child.name); child.returncode = -15
                unknown = mode in ("unknown_exit", "poisoned")
                return {"native_process_may_still_be_running": unknown, "native_exit_known": True,
                        "group_exit_known": not unknown, "process_group": child.pid}
            def sleep(seconds): clock[0] += max(seconds, 0.1)
            with patch.object(controller, "HERE", here), \
                 patch.object(controller, "preparation", return_value=(prepared, prepared_path)), \
                 patch.object(controller, "build_record", return_value=build), \
                 patch.object(controller.subprocess, "Popen", Process), \
                 patch.object(controller.monitor, "LibprocProvider", return_value=None), \
                 patch.object(controller.monitor, "BoundedSampler", Sampler), \
                 patch.object(controller.monitor, "bounded_terminate", terminate), \
                 patch.object(controller.time, "monotonic", side_effect=lambda: clock[0]), \
                 patch.object(controller.time, "sleep", side_effect=sleep), \
                 patch("sys.stdout", new_callable=io.StringIO):
                args = SimpleNamespace(released=True, output=output, build_record=build_path)
                if mode == "success": controller.capture(args)
                else:
                    with self.assertRaises(BaseException): controller.capture(args)
            info = json.loads((output / "profile.json").read_text())
            self.assertEqual(info["validation"], "pass" if mode == "success" else "failed")
            self.assertEqual(info["native_process_may_still_be_running"], mode in ("unknown_exit", "poisoned"))
            if mode == "success":
                self.assertEqual(set(info["groups"]), {"driver", "sample"})
                self.assertEqual(len(info["markers"]), 16)
                self.assertTrue(all(not group["group_exit_verification"]["members"] for group in info["groups"].values()))
                self.assertEqual({pid for tick, pid in sample_reads if tick == 2}, {10001, 10002})
            if mode in ("broken_pipe", "unknown_exit"):
                self.assertEqual(cleanup, ["sample", "driver"])
                self.assertEqual(info["stdin_close_errors"][0]["name"], "driver")
            if mode == "combined_rss": self.assertIn("combined sampled RSS", info["error"])
            if mode == "poisoned":
                self.assertEqual(set(children), {"driver"})
                self.assertIn("mock timeout", (output / "resources.jsonl").read_text())
            return info

    def test_all_lifecycle_modes(self):
        for mode in ("success", "combined_rss", "broken_pipe", "unknown_exit", "prepared_drift", "missing_done", "sample_failure", "poisoned"):
            with self.subTest(mode=mode): self.exercise(mode)

    def test_no_release_no_launch(self):
        with patch.object(controller, "preparation") as preparation, patch.object(controller.subprocess, "Popen") as popen:
            with self.assertRaises(Exception): controller.capture(SimpleNamespace(released=False))
            preparation.assert_not_called(); popen.assert_not_called()


if __name__ == "__main__": unittest.main(verbosity=2)
