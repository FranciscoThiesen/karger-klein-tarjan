#!/usr/bin/env python3
"""Run the fixed shape campaign serially; never overwrite existing evidence.

Usage from repository root: python3 THIS_FILE TIMING_BINARY WORK_BINARY NEW_DIR
Build and validate both binaries before running. Do not run other performance
work, builds, or plots concurrently. This script cannot control desktop load.
"""
import csv
import datetime
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
import time


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if len(sys.argv) != 4:
        raise ValueError(__doc__)
    timing, work = (Path(p).resolve(strict=True) for p in sys.argv[1:3])
    output = Path(sys.argv[3]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    protected = [output / (tag + suffix) for tag in ("work", "primary", "repeat")
                 for suffix in (".csv", ".log")]
    protected.append(output / "metadata.json")
    if any(p.exists() for p in protected):
        raise ValueError("refusing to overwrite campaign evidence")
    root = Path.cwd()
    sources = sorted(set(root.glob("*/*.cpp")) | set(root.glob("*/*.hpp")))
    hashes = {str(p.relative_to(root)): digest(p) for p in sources}
    metadata = {
        "base_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": hashes,
        "runner_sha256": digest(__file__),
        "analyzer_sha256": digest(root / "benchmark/analyze_shapes.py"),
        "platform": platform.platform(), "machine": platform.machine(),
        "cpu": subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip(),
        "compiler": subprocess.check_output(["/usr/bin/clang++", "--version"], text=True).strip(),
        "build_profile": "Native Make -std=c++17 -O3 -Wall -Wextra -march=native; Apple SDK; assertions enabled. Work binary separately enables KKT_ENABLE_WORK_STATS.",
        "plan": "Six preselected new families plus hub/random_4 controls; 4096/16384/65536 vertices; graph seeds17/42/999; KKT seeds0/1/7; four repetitions and one checked warmup per algorithm/seed pair. Two complete timing campaigns retained regardless of outcomes. Work measured separately first.",
        "timing_boundary": "Original diverse_benchmark measure() unchanged: tuple conversion and temporary input destruction included; generation/certification/result validation and returned-result destruction excluded.",
        "execution": "Serial work, primary, repeat. No concurrent agent builds/tests/plots. Ordinary desktop, no affinity or controlled power state.",
        "runs": {},
    }
    def save():
        (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    save()
    for tag, binary, args, expected in (
        ("work", work, [], 216),
        ("primary", timing, ["--shapes", "--repetitions", "4", "--warmups", "1"], 3456),
        ("repeat", timing, ["--shapes", "--repetitions", "4", "--warmups", "1"], 3456),
    ):
        command = [str(binary), *args]
        info = {"command": command, "binary_sha256": digest(binary),
                "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
        metadata["runs"][tag] = info
        save()
        start = time.monotonic()
        with (output / (tag + ".csv")).open("w") as stdout, (output / (tag + ".log")).open("w") as stderr:
            result = subprocess.run(["/usr/bin/time", "-l", *command], stdout=stdout, stderr=stderr)
        info.update(exit_status=result.returncode, wall_seconds_including_setup=time.monotonic() - start,
                    finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        info["output_sha256"] = {suffix: digest(output / (tag + suffix)) for suffix in (".csv", ".log")}
        match = re.search(r"(\d+)\s+maximum resident set size", (output / (tag + ".log")).read_text())
        if match: info["peak_resident_set_bytes"] = int(match.group(1))
        save()
        if result.returncode: raise RuntimeError(f"{tag} exited {result.returncode}")
        with (output / (tag + ".csv")).open(newline="") as source:
            rows = list(csv.DictReader(source))
        marker = "pass_certified_oracle_exact_ids" if tag == "work" else "pass"
        if len(rows) != expected or any(row["validation"] != marker for row in rows):
            raise RuntimeError(f"{tag}: incomplete or invalid results")
        # Full strict analyzer validation happens after all timing; this avoids
        # plotting or analysis activity between timed observations.
        info["basic_validated_rows"] = expected
        info["checked_warmup_calls"] = 0 if tag == "work" else 864
        if any(digest(root / path) != value for path, value in hashes.items()):
            raise RuntimeError("source changed while campaign was running")
        save()
        print(f"{tag}: {expected} checked observations", flush=True)


if __name__ == "__main__":
    main()
