#!/usr/bin/env python3
"""Exercise capture failure handling with a fake solver in isolated repositories.

No MST solver or performance measurement is invoked. Synthetic clock values
exist only to exercise validation and evidence retention around child processes.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time


RUNNER = Path(__file__).with_name("run_crossover.py").resolve()
FAKE = r'''
import csv
import json
import os
from pathlib import Path
import sys
import time

action = os.environ.get("CROSSOVER_FAKE_ACTION", "good")
Path("launched").write_text(str(os.getpid()))
if action == "sleep":
    while True:
        time.sleep(1)
if action == "nonzero":
    print("retained partial output", flush=True)
    print("synthetic solver failure", file=sys.stderr, flush=True)
    sys.exit(7)
if action == "source_changed":
    Path("src/probe.cpp").write_text("// changed during capture\n")
if action == "source_added":
    Path("src/added.hpp").write_text("// added during capture\n")
if action == "source_deleted":
    Path("src/probe.cpp").unlink()

fields = "case_id,family,n,m,density,intrusion_per_mille,graph_seed,input_fingerprint,topology_fingerprint,kkt_seed,repetition,order,warmups,algorithm,elapsed_ns,validation".split(",")
writer = csv.DictWriter(sys.stdout, fieldnames=fields)
writer.writeheader()
cpu, utc = 1_000_000, 1_800_000_000_000_000_000
case = "gnm_random_n128_d16_p0"
for phase, repetitions in (("warmup", 1), ("timed", 2)):
    for repetition in range(repetitions):
        for order in (0, 1):
            algorithm = ("kkt", "compacting_boruvka")[(order+repetition) % 2]
            elapsed = 1000 if algorithm == "kkt" else 2000
            record = {"case_id": case, "graph_seed": 17, "sampling_seed": 0,
                      "phase": phase, "repetition": repetition, "order": order,
                      "algorithm": algorithm, "utc_start_ns": utc, "utc_end_ns": utc+elapsed,
                      "process_cpu_start_ns": cpu, "process_cpu_end_ns": cpu+elapsed,
                      "process_cpu_elapsed_ns": elapsed, "steady_elapsed_ns": elapsed,
                      "validation": "pass"}
            if action != "missing_clocks":
                print("call_clock_v1 "+json.dumps(record), file=sys.stderr)
            if phase == "timed":
                writer.writerow(dict(case_id=case, family="gnm_random", n=128, m=2048,
                    density=16, intrusion_per_mille=0, graph_seed=17, input_fingerprint=123,
                    topology_fingerprint=456, kkt_seed=0, repetition=repetition, order=order,
                    warmups=1, algorithm=algorithm, elapsed_ns=elapsed, validation="pass"))
            cpu += elapsed+100
            utc += elapsed+100
'''


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def metadata(output):
    return json.loads(output.with_suffix(".json").read_text())


def command(binary, manifest, output):
    return [sys.executable, str(RUNNER), "--binary", str(binary), "--manifest", str(manifest),
            "--output", str(output), "--graph-seeds", "17", "--sampling-seeds", "0",
            "--repetitions", "2", "--warmups", "1"]


def main():
    checks = []
    with tempfile.TemporaryDirectory(prefix="crossover-runner-test-") as directory:
        root = Path(directory)
        subprocess.run(["git", "init", "--quiet", str(root)], check=True, capture_output=True)
        subprocess.run(["git", "-c", "user.name=Runner Test", "-c", "user.email=runner@example.invalid",
                        "commit", "--quiet", "--allow-empty", "-m", "Synthetic runner test"],
                       cwd=root, check=True, capture_output=True)
        (root/"src").mkdir()
        probe = root/"src/probe.cpp"
        probe.write_text("// baseline synthetic source\n")
        binary = root/"fake_solver"
        binary.write_text("#!"+sys.executable+"\n"+FAKE)
        binary.chmod(0o755)
        manifest = root/"manifest.csv"
        manifest.write_text("family,n,density,intrusion_per_mille\ngnm_random,128,16,0\n")
        evidence = root/"evidence"
        evidence.mkdir()

        def run(name, action="good", suffix=".csv"):
            output = evidence/(name+suffix)
            completed = subprocess.run(command(binary, manifest, output), cwd=root,
                env={**os.environ, "CROSSOVER_FAKE_ACTION": action}, text=True, capture_output=True, timeout=20)
            return output, completed

        output, completed = run("positive")
        require(completed.returncode == 0, "valid synthetic capture failed: "+completed.stderr)
        info = metadata(output)
        clocks = json.loads(output.with_name("positive_clocks.json").read_text())
        require(info["basic_validated_rows"] == 4 and info["checked_warmup_calls"] == 2 and
                clocks["timed_calls"] == 4 and clocks["warmup_calls"] == 2 and
                clocks["rows_removed"] == clocks["rows_adjusted"] == 0,
                "positive row/clock accounting failed")
        checks.append({"case": "complete fake capture and strict clock audit", "status": "pass"})

        # Each companion file independently protects an existing capture path.
        for extension in (".csv", ".log", ".json", "_clocks.json"):
            name = "existing_"+extension.replace(".", "_")
            output = evidence/(name+".csv")
            protected = (evidence/(name+extension))
            protected.write_text("preserve exactly\n")
            (root/"launched").unlink(missing_ok=True)
            _, completed = run(name)
            require(completed.returncode != 0 and "refusing to overwrite evidence" in completed.stderr and
                    protected.read_text() == "preserve exactly\n" and not (root/"launched").exists(),
                    "existing evidence was overwritten or child launched: "+extension)
            checks.append({"case": "existing companion "+extension, "status": "rejected"})
        for extension in (".json", ".log", ".txt"):
            (root/"launched").unlink(missing_ok=True)
            _, completed = run("bad_suffix_"+extension[1:], suffix=extension)
            require(completed.returncode != 0 and "--output must end in .csv" in completed.stderr and
                    not (root/"launched").exists(), "unsafe output suffix accepted")
            checks.append({"case": "non-CSV output "+extension, "status": "rejected"})

        output, completed = run("nonzero", "nonzero")
        info = metadata(output)
        require(completed.returncode != 0 and info["exit_status"] == 7 and
                "retained partial output" in output.read_text() and
                "synthetic solver failure" in output.with_suffix(".log").read_text() and
                "basic_validated_rows" not in info, "failed child evidence was lost or marked successful")
        checks.append({"case": "nonzero child retains partial output/log/exit status", "status": "rejected"})

        output, completed = run("missing_clocks", "missing_clocks")
        info = metadata(output)
        require(completed.returncode != 0 and info["exit_status"] == 0 and
                "incomplete warmup/timed call-clock sequence" in info.get("clock_audit_error", "") and
                not output.with_name("missing_clocks_clocks.json").exists(),
                "missing clocks were not rejected after otherwise valid CSV")
        checks.append({"case": "missing per-call clocks", "status": "rejected"})

        for action in ("source_changed", "source_added", "source_deleted"):
            probe.write_text("// baseline synthetic source\n")
            (root/"src/added.hpp").unlink(missing_ok=True)
            output, completed = run(action, action)
            info = metadata(output)
            require(completed.returncode != 0 and "C++ source changed during campaign" in completed.stderr and
                    info["exit_status"] == 0 and "basic_validated_rows" not in info,
                    action+" was not rejected with retained capture metadata")
            checks.append({"case": action, "status": "rejected"})

        probe.write_text("// baseline synthetic source\n")
        (root/"src/added.hpp").unlink(missing_ok=True)
        (root/"launched").unlink(missing_ok=True)
        output = evidence/"interrupted.csv"
        capture = subprocess.Popen(command(binary, manifest, output), cwd=root,
            env={**os.environ, "CROSSOVER_FAKE_ACTION": "sleep"}, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic()+10
            while not (root/"launched").exists():
                require(capture.poll() is None and time.monotonic() < deadline, "fake sleeping child did not start")
                time.sleep(0.01)
            child = int((root/"launched").read_text())
            capture.send_signal(signal.SIGTERM)
            _, error = capture.communicate(timeout=15)
            info = metadata(output)
            require(capture.returncode != 0 and info["interruption"] and "signal 15" in info["interruption"] and
                    "basic_validated_rows" not in info, "SIGTERM did not preserve interruption metadata: "+error)
            deadline = time.monotonic()+3
            while True:
                try:
                    os.kill(child, 0)
                except ProcessLookupError:
                    break
                require(time.monotonic() < deadline, "interrupted child process remained alive")
                time.sleep(0.01)
            checks.append({"case": "SIGTERM retains metadata and terminates child process group", "status": "rejected"})
        finally:
            if capture.poll() is None:
                capture.kill()
                capture.communicate()

    print(json.dumps({"validation": "pass", "scope": "fake processes only; no MST or performance runs",
                      "positive_checks": sum(c["status"] == "pass" for c in checks),
                      "negative_checks": sum(c["status"] == "rejected" for c in checks),
                      "checks": checks}, indent=2))


if __name__ == "__main__":
    main()
