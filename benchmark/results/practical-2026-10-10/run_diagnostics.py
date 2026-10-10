#!/usr/bin/env python3
"""Run final timing/work diagnostics serially; never build or analyze results.

Example (run from the repository):
  python3 benchmark/results/practical-2026-10-10/run_diagnostics.py \
    --timing-binary /path/to/bazel-bin/benchmark/complexity_benchmark \
    --work-binary /path/to/native/work_sweep \
    --family-binary /path/to/native/family_work

Build profiles are caller declarations, recorded separately for each binary.
Hashes establish the files observed at execution; the runner cannot prove that
an executable was compiled from a particular source snapshot or set of flags.
"""

import argparse
import csv
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import sys
import time


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def interrupted(signum, frame):
    raise KeyboardInterrupt(f"received signal {signum}")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def capture(command, cwd):
    return subprocess.check_output(command, cwd=cwd, text=True).strip()


def save_metadata(path, data):
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def source_paths(repo, family_source):
    result = {}
    for directory in ("common", "kkt", "verifier", "lca", "kruskal", "union_find", "benchmark"):
        for pattern in ("*.cpp", "*.hpp", "BUILD"):
            for path in sorted((repo / directory).glob(pattern)):
                result[str(path.relative_to(repo))] = path
    for name in ("BUILD", "Makefile", "WORKSPACE", "WORKSPACE.bazel", ".bazelrc",
                 "benchmark/analyze_complexity.py"):
        if (repo / name).is_file():
            result[name] = repo / name
    result["scratch/family_work.cpp"] = family_source
    result["scratch/run-diagnostics.py"] = Path(__file__).resolve()
    return result


def source_hashes(paths):
    return {name: sha256(path) for name, path in sorted(paths.items())}


def source_digest(hashes):
    return hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()


def resource_usage(log, system):
    text = log.read_text(errors="replace")
    if system == "Darwin":
        match = re.search(r"^\s*(\d+)\s+maximum resident set size\s*$", text, re.M)
        multiplier = 1
        swaps = re.search(r"^\s*(\d+)\s+swaps\s*$", text, re.M)
    else:
        match = re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)", text)
        multiplier = 1024
        swaps = re.search(r"Swaps:\s*(\d+)", text)
    return {
        "peak_resident_set_bytes": int(match.group(1)) * multiplier if match else None,
        "swaps": int(swaps.group(1)) if swaps else None,
    }


def validate_output(run):
    if run["name"] == "timing":
        payload = json.loads(run["data_path"].read_text())
        records = payload.get("benchmarks", [])
        if not records or any(row.get("error_occurred") for row in records):
            raise RuntimeError("Google Benchmark produced no records or reported an error")
        observations = [row for row in records if row.get("run_type") == "iteration"]
    else:
        with run["data_path"].open(newline="") as stream:
            observations = list(csv.DictReader(stream))
        expected_validation = ("pass" if run["name"] == "work" else
                               "pass_certified_oracle_exact_ids")
        if any(row.get("validation") != expected_validation for row in observations):
            raise RuntimeError(f"{run['name']} has a failed or missing validation marker")
    if len(observations) != run["expected_records"]:
        raise RuntimeError(f"{run['name']} has {len(observations)} records; "
                           f"expected {run['expected_records']}")
    return len(observations)


def execute(command, stdout_path, stderr_path, cwd):
    # A separate process group lets interruption stop both /usr/bin/time and
    # its child, so an aborted diagnostic cannot overlap a later manual run.
    with stdout_path.open("x") as output, stderr_path.open("x") as error:
        process = subprocess.Popen(command, cwd=cwd, stdout=output, stderr=error,
                                   start_new_session=True)
        try:
            return process.wait()
        except BaseException:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--results", type=Path,
                        default=Path("benchmark/results/practical-2026-10-10"))
    parser.add_argument("--timing-binary", type=Path, required=True)
    parser.add_argument("--work-binary", type=Path, required=True)
    parser.add_argument("--family-binary", type=Path, required=True)
    parser.add_argument("--family-source", type=Path,
                        default=Path(__file__).with_name("family_work.cpp"))
    parser.add_argument("--timing-build-profile", default=
                        "Bazel -c opt --copt=-O3; arm64/macOS SDK; no -march=native; "
                        "NDEBUG enabled; KKT_ENABLE_WORK_STATS disabled")
    parser.add_argument("--work-build-profile", default=
                        "Native Make -std=c++17 -O3 -Wall -Wextra -march=native; "
                        "macOS SDK; assertions enabled; KKT_ENABLE_WORK_STATS enabled; untimed")
    parser.add_argument("--family-build-profile", default=
                        "Native compiler using Make work-stats objects; -std=c++17 -O3 "
                        "-march=native; assertions enabled; KKT_ENABLE_WORK_STATS enabled; untimed")
    args = parser.parse_args()
    repo = args.repo.resolve()
    results = (args.results if args.results.is_absolute() else repo / args.results).resolve()
    complexity = results / "complexity"
    metadata_path = complexity / "metadata.json"
    system = platform.system()
    if system not in ("Darwin", "Linux"):
        raise RuntimeError("RSS capture supports Darwin and Linux only")
    timer = Path("/usr/bin/time")
    if not timer.is_file():
        raise RuntimeError("/usr/bin/time is required for per-process RSS")

    binaries = {"timing": args.timing_binary.resolve(), "work": args.work_binary.resolve(),
                "family_work": args.family_binary.resolve()}
    for name, path in binaries.items():
        if not path.is_file() or not os.access(path, os.X_OK):
            raise RuntimeError(f"{name} executable is missing or not executable: {path}")
    runs = [
        {"name": "timing", "command": [str(binaries["timing"]),
            f"--benchmark_out={complexity / 'timing.json'}", "--benchmark_out_format=json",
            "--benchmark_color=false"],
         "stdout_path": complexity / "timing.stdout.txt", "stderr_path": complexity / "timing.log",
         "data_path": complexity / "timing.json", "expected_records": 378,
         "profile": args.timing_build_profile, "measurement": "manual steady_clock timing"},
        {"name": "work", "command": [str(binaries["work"]), "--large"],
         "stdout_path": complexity / "work.csv", "stderr_path": complexity / "work.log",
         "data_path": complexity / "work.csv", "expected_records": 180,
         "profile": args.work_build_profile, "measurement": "logical counters; no algorithm timer"},
        {"name": "family_work", "command": [str(binaries["family_work"])],
         "stdout_path": results / "family_work.csv", "stderr_path": results / "family_work.log",
         "data_path": results / "family_work.csv", "expected_records": 162,
         "profile": args.family_build_profile, "measurement": "family logical counters; no algorithm timer"},
    ]
    outputs = {metadata_path, metadata_path.with_suffix(".json.tmp")}
    for run in runs:
        outputs.update(run[key] for key in ("stdout_path", "stderr_path", "data_path"))
    existing = sorted(str(path) for path in outputs if path.exists())
    if existing:
        raise RuntimeError("refusing to overwrite diagnostic evidence: " + ", ".join(existing))
    paths = source_paths(repo, args.family_source.resolve())
    hashes = source_hashes(paths)
    source_revision = capture(["git", "rev-parse", "HEAD"], repo)
    tracked_paths = [name for name in paths if not name.startswith("scratch/")]
    metadata = {
        "status": "running", "started_utc": utc_now(), "repository": str(repo),
        "source_revision": source_revision, "source_sha256": hashes,
        "source_snapshot_sha256": source_digest(hashes),
        "source_paths": {name: str(path) for name, path in paths.items()},
        "source_working_tree_status": capture(["git", "status", "--porcelain", "--", *tracked_paths], repo),
        "runner_sha256": sha256(Path(__file__).resolve()),
        "host": {"system": system, "platform": platform.platform(), "architecture": platform.machine()},
        "build_profile_provenance": "Caller declarations; executable hashes and source snapshots recorded, "
                                    "but the runner does not verify their build relationship.",
        "execution": "Timing, work sweep, and family probe execute serially. Stop after first failed "
                     "command or basic output check. External builds/plots/background activity are not controlled.",
        "wall_time_scope": "Whole process including fixture generation, certification, and output; "
                           "this orchestration duration is not an MST timing observation.",
        "clock_metadata_caveat": "Google Benchmark CPU-frequency metadata is not used; use exported real_time.",
        "graph_seeds": [17, 42, 999], "sampling_seeds": [0, 1, 7],
        "validation_scope": "Runner checks exit status, error markers, and record counts. "
                            "The existing analyzer must separately validate complete matrices and timing values.",
        "runs": {},
    }
    for run in runs:
        name = run["name"]
        metadata["runs"][name] = {
            "status": "not_started", "exit_status": None,
            "command": run["command"], "cwd": str(repo),
            "wrapper_command": [str(timer), "-l" if system == "Darwin" else "-v", *run["command"]],
            "binary_path": str(binaries[name]), "binary_sha256": sha256(binaries[name]),
            "source_revision": source_revision, "source_snapshot_sha256": source_digest(hashes),
            "build_profile": run["profile"], "measurement": run["measurement"],
            "expected_records": run["expected_records"],
            "stdout": str(run["stdout_path"]), "stderr": str(run["stderr_path"]),
            "data": str(run["data_path"]),
        }
    complexity.mkdir(parents=True, exist_ok=True)
    # Claim this campaign before launching any process.
    with metadata_path.open("x") as output:
        output.write(json.dumps(metadata, indent=2, sort_keys=True) + "\n")

    try:
        for run in runs:
            info = metadata["runs"][run["name"]]
            if source_hashes(paths) != hashes or sha256(binaries[run["name"]]) != info["binary_sha256"]:
                raise RuntimeError("source or binary changed before " + run["name"])
            print("Starting " + run["name"], flush=True)
            info.update(status="running", started_utc=utc_now())
            save_metadata(metadata_path, metadata)
            started = time.monotonic()
            try:
                info["exit_status"] = execute(info["wrapper_command"], run["stdout_path"],
                                              run["stderr_path"], repo)
                info.update(finished_utc=utc_now(), wall_seconds_including_setup=time.monotonic() - started)
                if info["exit_status"] != 0:
                    raise RuntimeError(f"{run['name']} exited with status {info['exit_status']}")
                if sha256(binaries[run["name"]]) != info["binary_sha256"] or source_hashes(paths) != hashes:
                    raise RuntimeError("source or binary changed during " + run["name"])
                info["validated_records"] = validate_output(run)
                info.update(resource_usage(run["stderr_path"], system))
                if info["peak_resident_set_bytes"] is None:
                    raise RuntimeError("missing per-process RSS for " + run["name"])
                info["status"] = "passed"
            except BaseException as error:
                info.update(status="failed", error=str(error) or type(error).__name__)
                raise
            finally:
                info.setdefault("finished_utc", utc_now())
                info.setdefault("wall_seconds_including_setup", time.monotonic() - started)
                if run["stderr_path"].is_file():
                    info.update(resource_usage(run["stderr_path"], system))
                info["output_sha256"] = {str(path): sha256(path) for path in
                    {run["stdout_path"], run["stderr_path"], run["data_path"]} if path.is_file()}
                save_metadata(metadata_path, metadata)
            print(f"Completed {run['name']}: {info['validated_records']} records, exit 0", flush=True)
        metadata["status"] = "passed"
    except BaseException as error:
        metadata.update(status="failed", error=str(error) or type(error).__name__)
        raise
    finally:
        metadata["finished_utc"] = utc_now()
        save_metadata(metadata_path, metadata)


if __name__ == "__main__":
    # Preserve failure metadata and stop an active child group on SIGTERM too.
    signal.signal(signal.SIGTERM, interrupted)
    try:
        main()
    except (Exception, KeyboardInterrupt) as error:
        print("diagnostics: " + (str(error) or type(error).__name__), file=sys.stderr)
        sys.exit(1)
