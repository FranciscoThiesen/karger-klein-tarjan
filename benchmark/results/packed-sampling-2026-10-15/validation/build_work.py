#!/usr/bin/env python3
"""Build existing untimed diagnostics against the validated instrumented objects.

Only four small smoke fixtures are run. No large matrix or timing target runs.
"""
import json
from pathlib import Path
import shlex
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "benchmark"))
import build_packed_sampling as builder

SOURCE = "benchmark/results/retention-control-2026-10-15/work/driver.cpp"
CASES = (("leaf_hierarchy4", 512, 16), ("leaf_distance4", 512, 16),
         ("gnm_random", 64, 16), ("gnm_random", 512, 128))


def main():
    output = HERE.parent / "work"
    output.mkdir(exist_ok=True)
    log_path = output / "build.log"
    if log_path.exists():
        raise RuntimeError("refusing to overwrite diagnostic evidence")
    paths = [HERE / f"native-correctness-{v}-build-record.json" for v in builder.VARIANTS]
    records = [json.loads(path.read_text()) for path in paths]
    source_hash = builder.sha(ROOT / SOURCE)

    def validate():
        if source_hash != builder.sha(ROOT / SOURCE):
            raise RuntimeError("supplementary diagnostic source drift")
        for record in records:
            if record["source_sha256"] != builder.inventory():
                raise RuntimeError("production source drift")
            for name, path in record["object_paths"].items():
                if builder.sha(path) != record["object_sha256"][name]:
                    raise RuntimeError("instrumented object drift")

    validate()
    base_command = records[0]["build_commands"][0]
    base = base_command[:base_command.index("-c")]
    main_object = ROOT / ".build/packed-sampling/work/driver.o"
    main_object.parent.mkdir(parents=True, exist_ok=True)
    guard = builder.SerialGuard(output / "owned-groups.json")
    commands, binaries, gates, values = [], [], [], {}
    with log_path.open("w") as log:
        def build(command):
            commands.append(command)
            log.write("$ " + shlex.join(command) + "\n")
            log.flush()
            guard.run(command, stdout=log)
        build(base + ["-c", SOURCE, "-o", str(main_object)])
        for record in records:
            variant = record["variant"]
            binary = ROOT / "bin/packed-sampling/work" / variant / "retention_work"
            binary.parent.mkdir(parents=True, exist_ok=True)
            command = base + list(record["object_paths"].values()) + [str(main_object),
                f"-L{record['sdk']}/usr/lib", "-Wl,-stack_size,0x20000000", "-o", str(binary)]
            build(command)
            binaries.append({"variant": variant, "binary": str(binary),
                "binary_sha256": builder.sha(binary), "binary_profile": builder.profile(binary),
                "link_command": command, "instrumented_build_record": str(paths[len(binaries)]),
                "instrumented_build_record_sha256": builder.sha(paths[len(binaries)]),
                "object_paths": record["object_paths"], "object_sha256": record["object_sha256"]})
            for family, n, density in CASES:
                stem = f"smoke-{variant}-{family}-n{n}-d{density}"
                stdout, stderr = output / (stem + ".json"), output / (stem + ".log")
                command = builder.NATIVE + [str(binary), family, str(n), str(density), "3000001", "809"]
                with stdout.open("w") as out, stderr.open("w") as err:
                    guard.run(command, stdout=out, stderr=err)
                value = json.loads(stdout.read_text())
                if value["validation"] != "pass" or value["certified_output_items"] != n - 1:
                    raise RuntimeError("diagnostic certificate failed")
                values[variant, family, n, density] = value
                gates.append({"variant": variant, "command": command, "exit_status": 0,
                    "stdout": str(stdout), "stdout_sha256": builder.sha(stdout),
                    "stderr": str(stderr), "stderr_sha256": builder.sha(stderr)})
    for family, n, density in CASES:
        a, b = (values[v, family, n, density] for v in builder.VARIANTS)
        for field in ("case_id", "family", "n", "m", "density", "graph_seed", "kkt_seed",
                      "input_fingerprint", "topology_fingerprint", "certified_output_items", "rounds"):
            if a[field] != b[field]:
                raise RuntimeError(f"paired diagnostic {field} differs")
        for algorithm in ("compacting_boruvka", "multigraph_boruvka"):
            if a["algorithms"][algorithm] != b["algorithms"][algorithm]:
                raise RuntimeError("unchanged comparator counters differ")
    validate()
    result = {"schema": "packed_sampling_work_build_v1", "status": "pass",
        "performance_executed": False, "large_matrix_executed": False,
        "source": SOURCE, "source_sha256": source_hash,
        "script_sha256": builder.sha(__file__), "build_commands": commands,
        "main_object": str(main_object), "main_object_sha256": builder.sha(main_object),
        "build_log": str(log_path), "build_log_sha256": builder.sha(log_path),
        "executables": binaries, "smoke_gates": gates,
        "counter_boundary": "Includes tuple-to-Edge input construction, solver, and temporary input destruction; certification and round replay are outside WorkStats."}
    (output / "build-record.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": "pass", "small_smoke_children": len(gates), "large_matrix_executed": False}))


if __name__ == "__main__":
    main()
