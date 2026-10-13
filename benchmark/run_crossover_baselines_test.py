#!/usr/bin/env python3
"""Synthetic row/protocol and fake-process checks; no real benchmark invocation."""
import copy
import csv
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import analyze_continuation as base
import run_crossover_baselines as capture


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def synthetic(spec):
    result = []
    utc, cpu = 1_800_000_000_000_000_000, 1_000_000
    for phase, repetitions in (("warmup", 1), ("timed", 4)):
        for repetition in range(repetitions):
            for order in range(4):
                algorithm = capture.ALGORITHMS[(order+repetition) % 4]
                duration = (capture.ALGORITHMS.index(algorithm)+1)*1000
                result.append({**spec, "graph_seed": 17, "kkt_seed": 0,
                    "input_fingerprint": 123, "topology_fingerprint": 456,
                    "phase": phase, "repetition": repetition, "order": order, "warmups": 1,
                    "algorithm": algorithm, "elapsed_ns": duration,
                    "utc_start_ns": utc, "utc_end_ns": utc+duration,
                    "process_cpu_start_ns": cpu, "process_cpu_end_ns": cpu+duration,
                    "process_cpu_elapsed_ns": duration, "validation": "pass"})
                cpu += duration+100
                utc += duration+100
    return result


def csv_text(rows, fields=capture.FIELDS):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def main():
    checks = []
    with tempfile.TemporaryDirectory(prefix="classical-capture-test-") as directory:
        root = Path(directory)
        manifest = root/"manifest.csv"
        manifest.write_text("family,n,density,intrusion_per_mille\ngnm_random,128,16,0\n")
        cases = base.load_manifest(manifest)
        spec = next(iter(cases.values()))
        rows = synthetic(spec)
        raw = root/"rows.csv"

        def validate(changed=rows, reference=None, fields=capture.FIELDS):
            raw.write_text(csv_text(changed, fields))
            return capture.check_rows(raw, spec, 17, 0, 4, 1, reference or {})

        good, diagnostics = validate(reference={spec["case_id"]: (123, 456)})
        require(len(good) == len(diagnostics) == 20 and not any(r["diagnostic_flags"] for r in diagnostics),
                "valid 4-algorithm matrix or clocks rejected")
        checks.append({"case": "complete warmup/timed schedule and input binding", "status": "pass"})
        changed = copy.deepcopy(rows)
        changed[4]["elapsed_ns"] += 918_000_000_000
        changed[4]["utc_end_ns"] += 918_000_000_000
        for row in changed[5:]:
            row["utc_start_ns"] += 918_000_000_000
            row["utc_end_ns"] += 918_000_000_000
        retained, flags = validate(changed)
        require(len(retained) == 20 and flags[4]["diagnostic_flags"] == ["steady_exceeds_process_cpu"] and
                not any(row["excluded"] for row in flags), "long anomalous observation not retained")
        checks.append({"case": "long steady/UTC observation retained with CPU diagnostic", "status": "pass"})
        changed = copy.deepcopy(rows)
        changed[0]["utc_end_ns"] = changed[0]["utc_start_ns"]-1
        _, flags = validate(changed)
        require("realtime_reversed_within_call" in flags[0]["diagnostic_flags"], "realtime reversal lost")
        checks.append({"case": "realtime reversal retained as diagnostic", "status": "pass"})

        def reject(name, action):
            try:
                action()
            except ValueError as error:
                checks.append({"case": name, "status": "rejected", "message": str(error)})
            else:
                raise AssertionError(name+" was accepted")

        def mutate(field, value, index=0):
            changed = copy.deepcopy(rows)
            changed[index][field] = value
            return validate(changed)

        for field, value in (("phase", "timed"), ("algorithm", "compacting_boruvka"),
                ("order", 1), ("repetition", 4), ("case_id", "wrong"), ("family", "line_metric"),
                ("n", 256), ("m", 2049), ("density", 32), ("intrusion_per_mille", 1),
                ("graph_seed", 42), ("kkt_seed", 7), ("warmups", 0), ("validation", "fail"),
                ("input_fingerprint", 124), ("topology_fingerprint", 457), ("elapsed_ns", 0),
                ("utc_start_ns", 0), ("utc_end_ns", 2**63), ("process_cpu_elapsed_ns", 0),
                ("process_cpu_end_ns", 999), ("graph_seed", True)):
            reject(f"bad {field}={value!r}", lambda f=field,v=value: mutate(f,v))
        reject("missing warmup row", lambda: validate(rows[1:]))
        reject("same-count duplicate row", lambda: validate([rows[1]]+rows[1:]))
        reject("reordered rows", lambda: validate([rows[1],rows[0]]+rows[2:]))
        reject("extra row", lambda: validate(rows+[rows[0]]))
        reject("wrong pilot fingerprint", lambda: validate(reference={spec["case_id"]: (124,456)}))
        changed = copy.deepcopy(rows)
        changed[1]["process_cpu_start_ns"] = rows[0]["process_cpu_end_ns"]-1
        changed[1]["process_cpu_end_ns"] = changed[1]["process_cpu_start_ns"]+changed[1]["process_cpu_elapsed_ns"]
        reject("inter-call process CPU overlap", lambda: validate(changed))

        # Exercise real runner subprocess/fresh-path/metadata logic with a fake
        # executable that emits the synthetic rows above; no MST code is linked.
        subprocess.run(["git", "init", "--quiet", str(root)], check=True, capture_output=True)
        subprocess.run(["git", "-c", "user.name=Runner Test", "-c", "user.email=runner@example.invalid",
                        "commit", "--quiet", "--allow-empty", "-m", "Synthetic classical runner test"],
                       cwd=root, check=True, capture_output=True)
        (root/"src").mkdir()
        (root/"src/probe.cpp").write_text("// baseline\n")
        payload = root/"payload.csv"
        payload.write_text(csv_text(rows))
        binary = root/"fake_solver"
        binary.write_text("#!"+sys.executable+"\n"+r'''
import os
from pathlib import Path
import sys
Path("launched").write_text("yes")
action = os.environ.get("CLASSICAL_FAKE_ACTION", "good")
if action == "add_source":
    Path("src/new.hpp").write_text("// changed inventory\n")
sys.stdout.buffer.write(Path("payload.csv").read_bytes())
sys.stdout.buffer.flush()
if action == "nonzero":
    print("synthetic failure", file=sys.stderr)
    sys.exit(7)
''')
        binary.chmod(0o755)
        evidence = root/"evidence"
        evidence.mkdir()

        def run(name, action="good"):
            output = evidence/(name+".csv")
            result = subprocess.run([sys.executable, str(Path(capture.__file__).resolve()),
                "--binary", str(binary), "--manifest", str(manifest), "--output", str(output)],
                cwd=root, env={**os.environ, "CLASSICAL_FAKE_ACTION": action},
                text=True, capture_output=True, timeout=20)
            return output, result

        output, process = run("positive")
        require(process.returncode == 0, "positive wrapper failed: "+process.stderr)
        info = json.loads(output.with_suffix(".json").read_text())
        require(info["validation"] == "pass" and info["checked_timed_rows"] == 16 and
                info["checked_warmup_rows"] == 4 and len(info["call_diagnostics"]) == 20 and
                info["output_sha256"] == capture.sha(output) and info["rows_removed"] == 0,
                "wrapper success metadata/count/hash incorrect")
        native = Path(info["captures"][0]["csv"])
        require(native.read_bytes() == payload.read_bytes(), "raw native CSV was rewritten")
        checks.append({"case": "fake-child full capture, raw preservation and metadata", "status": "pass"})

        for suffix in (".csv", ".json", "_cases"):
            name = "existing"+suffix.replace(".", "_")
            protected = evidence/(name+suffix)
            if suffix == "_cases":
                protected.mkdir()
            else:
                protected.write_text("preserve\n")
            (root/"launched").unlink(missing_ok=True)
            _, process = run(name)
            require(process.returncode != 0 and "refusing to overwrite classical evidence" in process.stderr and
                    not (root/"launched").exists(), "existing classical evidence accepted")
            checks.append({"case": "existing classical companion "+suffix, "status": "rejected"})
        for action in ("nonzero", "add_source"):
            output, process = run(action, action)
            info = json.loads(output.with_suffix(".json").read_text())
            require(process.returncode != 0 and info["validation"] == "failed" and
                    len(info["captures"]) == 1 and Path(info["captures"][0]["csv"]).exists() and
                    info["captures"][0]["exit_status"] == (7 if action == "nonzero" else 0),
                    action+" did not retain failed raw capture")
            require(("child failed" if action == "nonzero" else "source inventory changed") in info["error"],
                    action+" failed for an unexpected reason")
            checks.append({"case": "fake child "+action, "status": "rejected"})
    print(json.dumps({"validation": "pass", "scope": "synthetic rows and fake processes only",
                      "positive_checks": sum(c["status"] == "pass" for c in checks),
                      "negative_checks": sum(c["status"] == "rejected" for c in checks),
                      "checks": checks}, indent=2))


if __name__ == "__main__":
    main()
