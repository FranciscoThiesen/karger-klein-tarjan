#!/usr/bin/env python3
"""Build isolated Edge-query variants; run correctness only, never benchmarks.

Each profile compiles seven shared production objects once. Only kkt.cpp is
compiled twice, with KKT_EXPERIMENT_EDGE_VIEW as the sole flag difference.
The timing-build profile links the unchanged six-solver harness but never runs
it. Both variants use retained-parallel contraction and the refactored verifier.
"""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ["/usr/bin/arch", "-arm64"]
SOURCES = ["boruvka/boruvka.cpp", "kruskal/kruskal.cpp", "prim/prim.cpp",
           "lca/lca.cpp", "union_find/union_find.cpp", "graph_utils/graph_utils.cpp",
           "verifier/verifier_v2.cpp"]
TESTS = ["test/edge_verifier_view_test.cpp", "test/multigraph_contraction_test.cpp",
         "test/regression_test.cpp", "test/contraction_test.cpp", "test/simple_test.cpp",
         "benchmark/core_attachment_test.cpp"]
VARIANTS = ("tuple", "edge")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory():
    return {str(p.relative_to(ROOT)): sha(p) for p in
            sorted(set(ROOT.glob("*/*.cpp")) | set(ROOT.glob("*/*.hpp")))}


def checked_output(command):
    return subprocess.check_output(command, cwd=ROOT, text=True, timeout=60)


def profile(binary):
    description = checked_output(["/usr/bin/file", "-b", str(binary)]).strip()
    if description != "Mach-O 64-bit executable arm64":
        raise RuntimeError(f"rejected nonnative executable: {description}")
    load = checked_output(["/usr/bin/otool", "-l", str(binary)])
    match = re.search(r"\bcmd LC_MAIN\b(?:(?!Load command).)*?\bstacksize (\d+)", load, re.S)
    if not match or int(match.group(1)) != 536870912:
        raise RuntimeError("missing 512 MiB main stack")
    return {"file_description": description, "otool_load_commands": load,
            "main_stack_bytes": int(match.group(1))}


def compare_records(first, second):
    a = [json.loads(line) for line in Path(first).read_text().splitlines()]
    b = [json.loads(line) for line in Path(second).read_text().splitlines()]
    if len(a) != 1344 or len(b) != len(a):
        raise RuntimeError(f"incomplete paired records: {len(a)}, {len(b)}")
    verifier_positive = 0
    savings = 0
    seen = set()
    for old, new in zip(a, b):
        identity = (old["fixture"], old["order"], old["seed"])
        if identity in seen:
            raise RuntimeError("duplicate paired identity")
        seen.add(identity)
        for field in ("fixture", "order", "seed", "fingerprint", "ids"):
            if old[field] != new[field]:
                raise RuntimeError(f"paired {field} mismatch at {identity}")
        expected = old["stats"]["verifier_edges"]
        if expected != old["stats"]["sampling_edge_visits"]:
            raise RuntimeError("sampling/verifier volume differs")
        if set(old["stats"]) != set(new["stats"]) or len(old["stats"]) != 65:
            raise RuntimeError("counter schema differs")
        for field in old["stats"]:
            delta = expected if field in ("kkt_edge_visits", "edge_materializations") else 0
            if old["stats"][field] - new["stats"][field] != delta:
                raise RuntimeError(f"unexpected {field} delta at {identity}")
        verifier_positive += expected > 0
        savings += expected
    if verifier_positive == 0:
        raise RuntimeError("vacuous dispatch comparison")
    return {"status": "pass", "pairs": len(a), "fields_per_pair": 65,
            "verifier_positive_pairs": verifier_positive,
            "saved_kkt_edge_visits": savings, "saved_edge_materializations": savings,
            "identical_input_fingerprints_and_sorted_mst_ids": True,
            "all_other_fields_identical": True,
            "tuple_records": str(first), "tuple_records_sha256": sha(first),
            "edge_records": str(second), "edge_records_sha256": sha(second)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True,
                        choices=("native-correctness", "sanitizer-correctness", "timing-build"))
    parser.add_argument("--output", type=Path,
                        default=ROOT / "benchmark/results/edge-view-2026-10-15/validation")
    parser.add_argument("--parent-freeze", type=Path, default=Path(
        "/Users/random_person/Desktop/kkt-retention-control/benchmark/results/retention-control-2026-10-15/freeze.json"))
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    tag = args.profile
    build = ROOT / ".build/edge-verifier" / tag
    binaries = ROOT / "bin/edge-verifier" / tag
    build.mkdir(parents=True, exist_ok=True)
    binaries.mkdir(parents=True, exist_ok=True)
    log_path = output / f"{tag}-build.log"
    if log_path.exists():
        raise RuntimeError(f"refusing to overwrite existing build evidence: {log_path}")
    sources = inventory()
    compiler = "/opt/homebrew/opt/llvm/bin/clang++" if tag == "sanitizer-correctness" else "/usr/bin/clang++"
    compiler_command = NATIVE + [compiler, "--version"]
    compiler_version = checked_output(compiler_command)
    expected_compiler = "clang version 22." if tag == "sanitizer-correctness" else "Apple clang version 15."
    if "Target: arm64-" not in compiler_version or expected_compiler not in compiler_version:
        raise RuntimeError(f"unexpected compiler profile: {compiler_version}")
    sdk = checked_output(NATIVE + ["/usr/bin/xcrun", "--show-sdk-path"]).strip()
    flags = ["-std=c++17", "-O3", "-Wall", "-Wextra", "-march=native",
             "-DKKT_EXPERIMENT_RETAIN_PARALLEL"]
    if tag == "sanitizer-correctness":
        flags = ["-std=c++17", "-O1", "-g", "-Wall", "-Wextra", "-march=native",
                 "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                 "-DKKT_EXPERIMENT_RETAIN_PARALLEL"]
    if tag != "timing-build":
        flags.append("-DKKT_ENABLE_WORK_STATS")
    base = NATIVE + [compiler, "-isysroot", sdk] + flags + ["-I."]
    linkflags = [f"-L{sdk}/usr/lib", "-Wl,-stack_size,0x20000000"]
    commands = []
    with log_path.open("w") as log:
        log.write(compiler_version + f"SDK: {sdk}\n")

        def run(command):
            commands.append(command)
            log.write("\n$ " + shlex.join(command) + "\n")
            log.flush()
            subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=300)

        def compile_source(source, destination, extra=()):
            destination.parent.mkdir(parents=True, exist_ok=True)
            run(base + list(extra) + ["-c", source, "-o", str(destination)])
            if "arm64" not in checked_output(["/usr/bin/file", "-b", str(destination)]):
                raise RuntimeError(f"translated object: {destination}")
            return destination

        shared = {s.replace(".cpp", ".o"): compile_source(s, build / "shared" / s.replace(".cpp", ".o"))
                  for s in SOURCES}
        kkt_objects = {}
        for variant in VARIANTS:
            extra = ["-DKKT_EXPERIMENT_EDGE_VIEW"] if variant == "edge" else []
            kkt_objects[variant] = compile_source("kkt/kkt.cpp", build / variant / "kkt/kkt.o", extra)
        targets = ["benchmark/retention_control.cpp"] if tag == "timing-build" else TESTS
        records = {variant: [] for variant in VARIANTS}
        for source in targets:
            main_object = compile_source(source, build / "shared" / source.replace(".cpp", ".o"))
            for variant in VARIANTS:
                binary = binaries / variant / Path(source).stem
                binary.parent.mkdir(parents=True, exist_ok=True)
                objects = [str(path) for path in shared.values()] + [str(kkt_objects[variant]), str(main_object)]
                command = base + objects + linkflags + ["-o", str(binary)]
                run(command)
                records[variant].append({"source": source, "main_object": str(main_object),
                                         "main_object_sha256": sha(main_object),
                                         "binary": str(binary), "binary_sha256": sha(binary),
                                         "binary_profile": profile(binary), "link_command": command})
    if sources != inventory():
        raise RuntimeError("native source inventory changed during build")
    common = {"schema": "edge_verifier_build_v1", "profile": tag,
              "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "working_directory": str(ROOT),
              "revision": checked_output(["git", "rev-parse", "HEAD"]).strip(),
              "source_sha256": sources,
              "build_recipe_sha256": {"Makefile": sha(ROOT / "Makefile"),
                                      "benchmark/retention_control.mk": sha(ROOT / "benchmark/retention_control.mk"),
                                      "benchmark/build_edge_verifier.py": sha(__file__)},
              "compiler_command": compiler_command, "compiler": compiler_version, "sdk": sdk,
              "common_compile_flags": flags, "build_commands": commands,
              "build_command": [sys.executable, "-B", str(Path(__file__).resolve()),
                                "--profile", tag, "--output", str(output),
                                "--parent-freeze", str(args.parent_freeze.resolve())],
              "build_log": str(log_path), "build_log_sha256": sha(log_path), "build_exit_status": 0,
              "shared_object_paths": {name: str(path) for name, path in shared.items()},
              "seven_non_kkt_objects_identical_by_construction": True,
              "reference_note": "Fresh refactored tuple path; original frozen timings are not reused."}
    common["parent_control_freeze"] = str(args.parent_freeze.resolve())
    common["parent_control_freeze_sha256"] = sha(args.parent_freeze)
    for variant in VARIANTS:
        objects = {name: sha(path) for name, path in shared.items()}
        objects["kkt/kkt.o"] = sha(kkt_objects[variant])
        paths = {name: str(path) for name, path in shared.items()}
        paths["kkt/kkt.o"] = str(kkt_objects[variant])
        data = dict(common, variant=variant, object_sha256=objects, object_paths=paths,
                    kkt_object=str(kkt_objects[variant]), executables=records[variant])
        if tag == "timing-build":
            data.update(records[variant][0])
        path = output / f"{tag}-{variant}-build-record.json"
        path.write_text(json.dumps(data, indent=2) + "\n")
    if tag == "timing-build":
        print("Built both native timing executables; neither was executed.", flush=True)
        return

    environment = os.environ.copy()
    if tag == "sanitizer-correctness":
        environment["ASAN_OPTIONS"] = "detect_leaks=1:abort_on_error=1"
        environment["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
    tests = []
    for variant in VARIANTS:
        for record in records[variant]:
            stem = Path(record["binary"]).name
            stdout_path = output / f"{tag}-{variant}-{stem}.stdout"
            stderr_path = output / f"{tag}-{variant}-{stem}.stderr"
            command = NATIVE + [record["binary"]]
            print(f"Correctness: {tag} {variant} {stem}", flush=True)
            with stdout_path.open("w") as stdout, stderr_path.open("w") as stderr:
                outcome = subprocess.run(command, cwd=ROOT, env=environment, stdout=stdout,
                                         stderr=stderr, timeout=300)
            item = {"variant": variant, "test": stem, "command": command,
                    "exit_status": outcome.returncode, "binary_sha256": record["binary_sha256"],
                    "stdout": str(stdout_path), "stdout_sha256": sha(stdout_path),
                    "stderr": str(stderr_path), "stderr_sha256": sha(stderr_path)}
            tests.append(item)
            (output / f"{tag}-tests.json").write_text(json.dumps(
                {"status": "running", "tests": tests,
                 "sanitizer_options": {key: environment[key] for key in ("ASAN_OPTIONS", "UBSAN_OPTIONS")
                                       if key in environment}}, indent=2) + "\n")
            if outcome.returncode != 0:
                raise RuntimeError(f"correctness failed: {tag}/{variant}/{stem}; see {stderr_path}")
    pair = compare_records(output / f"{tag}-tuple-edge_verifier_view_test.stdout",
                           output / f"{tag}-edge-edge_verifier_view_test.stdout")
    # Demonstrate that an accidentally tuple-linked candidate is rejected.
    try:
        compare_records(pair["tuple_records"], pair["tuple_records"])
    except RuntimeError:
        pair["wrong_dispatch_negative_gate"] = "rejected"
    else:
        raise RuntimeError("paired gate accepted a wrongly linked tuple candidate")
    if sources != inventory():
        raise RuntimeError("native source inventory changed during correctness tests")
    (output / f"{tag}-tests.json").write_text(json.dumps(
        {"status": "pass", "tests": tests, "paired_work": pair,
         "sanitizer_options": {key: environment[key] for key in ("ASAN_OPTIONS", "UBSAN_OPTIONS")
                               if key in environment}}, indent=2) + "\n")
    print(json.dumps(pair, indent=2), flush=True)


if __name__ == "__main__":
    main()
