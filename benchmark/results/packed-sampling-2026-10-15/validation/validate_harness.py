#!/usr/bin/env python3
"""Untimed validation of each final object set with the unchanged harness test."""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "benchmark"))
import build_packed_sampling as builder


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    paths = [HERE / f"timing-build-{variant}-build-record.json" for variant in ("scalar", "packed")]
    records = [json.loads(path.read_text()) for path in paths]
    logpath = HERE / "final-object-harness-build.log"
    if logpath.exists():
        raise RuntimeError("refusing to overwrite existing harness gate evidence")
    for record in records:
        if record["source_sha256"] != builder.inventory():
            raise RuntimeError("native source drift")
        for name, path in record["object_paths"].items():
            if sha(path) != record["object_sha256"][name]:
                raise RuntimeError(f"object drift before correctness: {name}")
    base_command = records[0]["build_commands"][0]
    base = base_command[:base_command.index("-c")]
    main_object = ROOT / ".build/packed-sampling/timing-build/shared/test/retention_control_test.o"
    main_object.parent.mkdir(parents=True, exist_ok=True)
    results = []
    commands = []
    guard = builder.SerialGuard(HERE / "final-object-harness-owned-groups.json")
    with logpath.open("w") as log:
        def build(command):
            commands.append(command)
            log.write("$ " + shlex.join(command) + "\n")
            log.flush()
            guard.run(command, stdout=log)
        build(base + ["-c", "test/retention_control_test.cpp", "-o", str(main_object)])
        for record in records:
            variant = record["variant"]
            binary = ROOT / "bin/packed-sampling/timing-build" / variant / "retention_control_test"
            objects = list(record["object_paths"].values())
            build(base + objects + [str(main_object), f"-L{record['sdk']}/usr/lib",
                                   "-Wl,-stack_size,0x20000000", "-o", str(binary)])
            description = subprocess.check_output(["/usr/bin/file", "-b", str(binary)], text=True).strip()
            if description != "Mach-O 64-bit executable arm64":
                raise RuntimeError(f"rejected translated harness test: {description}")
            load = subprocess.check_output(["/usr/bin/otool", "-l", str(binary)], text=True)
            if "stacksize 536870912" not in load:
                raise RuntimeError("harness correctness test missing 512 MiB stack")
            stdout = HERE / f"final-object-{variant}-harness.stdout"
            stderr = HERE / f"final-object-{variant}-harness.stderr"
            command = ["/usr/bin/arch", "-arm64", str(binary)]
            with stdout.open("w") as out, stderr.open("w") as err:
                status = guard.run(command, stdout=out, stderr=err, check=False)
            results.append({"variant": variant, "command": command, "exit_status": status,
                            "binary": str(binary), "binary_sha256": sha(binary),
                            "file_description": description, "otool_load_commands": load,
                            "stdout": str(stdout), "stdout_sha256": sha(stdout),
                            "stderr": str(stderr), "stderr_sha256": sha(stderr)})
            if status != 0:
                raise RuntimeError(f"untimed harness gate failed: {variant}")
    for record in records:
        if record["source_sha256"] != builder.inventory():
            raise RuntimeError("native source drift")
        for name, path in record["object_paths"].items():
            if sha(path) != record["object_sha256"][name]:
                raise RuntimeError(f"object drift after correctness: {name}")
    evidence = {"status": "pass", "performance_executed": False,
                "build_commands": commands, "build_log": str(logpath), "build_log_sha256": sha(logpath),
                "build_record_sha256": {str(path): sha(path) for path in paths},
                "script_sha256": sha(__file__), "tests": results}
    (HERE / "final-object-harness-tests.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"status": "pass", "tests": len(results), "performance_executed": False}))


if __name__ == "__main__":
    main()
