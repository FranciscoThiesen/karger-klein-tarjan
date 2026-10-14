#!/usr/bin/env python3
"""Serial untimed diagnostics for completed attachment discovery inputs."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    repo = Path(__file__).resolve().parents[3]
    study = Path(__file__).resolve().parent
    output = study / "attachment-work"
    output.mkdir(exist_ok=False)
    binary = repo / "bin/search_work"
    build_log = study / "validation/attachment-build/build.log"
    sources = {str(p.relative_to(repo)): sha(p) for pattern in ("*/*.cpp", "*/*.hpp")
               for p in sorted(repo.glob(pattern)) if p.is_file()}
    manifest = {
        "schema": "attachment_work_capture_v1", "validation": "running",
        "instrumented": True, "rows_removed": 0, "rows_adjusted": 0,
        "working_directory": str(repo),
        "profile": "Native Make WORK_OBJS; /usr/bin/clang++ 15; C++17 -O3 -march=native -DKKT_ENABLE_WORK_STATS; assertions enabled",
        "binary": str(binary), "binary_sha256": sha(binary),
        "source_sha256": sources, "build_recipe_sha256": {"Makefile": sha(repo / "Makefile")},
        "build_log": str(build_log), "build_log_sha256": sha(build_log),
        "capture_script_sha256": sha(Path(__file__)), "records": [],
        "started_utc": now(), "purpose": "Untimed structural counters; no durations used as performance evidence",
    }
    cases = [(family, n, 16) for family in ("leaf_hierarchy4", "leaf_distance4")
             for n in (16384, 65536, 262144, 1048576)]
    cases += [(family, 1048576, 16) for family in (
        "leaf_shuffled4", "leaf_random4", "community_hierarchy4", "community_distance4",
        "leaf_hierarchy16", "leaf_distance16")]
    cases += [(family, 1048576, 2) for family in ("leaf_hierarchy4", "leaf_distance4")]
    for family, n, density in cases:
        stem = f"{family}_n{n}_d{density}_g5009_s149"
        raw, log = output / (stem + ".json"), output / (stem + ".log")
        command = [str(binary), "--family", family, "--n", str(n), "--density", str(density),
                   "--graph-seed", "5009", "--kkt-seed", "149"]
        record = {"command": command, "started_utc": now(), "json": raw.name, "log": log.name}
        with raw.open("xb") as stdout, log.open("xb") as stderr:
            result = subprocess.run(command, cwd=repo, stdout=stdout, stderr=stderr)
        record.update(exit_status=result.returncode, finished_utc=now(),
                      json_sha256=sha(raw), log_sha256=sha(log))
        manifest["records"].append(record)
        (output / "capture.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"{len(manifest['records'])}/{len(cases)} {stem}: exit {result.returncode}", flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)
    if sources != {name: sha(repo / name) for name in sources} or manifest["binary_sha256"] != sha(binary):
        raise SystemExit("native source or work binary changed during capture")
    manifest.update(validation="pass", finished_utc=now())
    (output / "capture.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
