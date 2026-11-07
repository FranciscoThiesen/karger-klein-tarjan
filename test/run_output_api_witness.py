#!/usr/bin/env python3
"""Count actual libc++ unique-insertion bucket visits; no timing measurement.

The installed SDK header is copied into a temporary include directory. Only
the two explicitly matched unique-insertion loop bodies receive an increment.
The installed SDK and the production algorithm files are never modified.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True, exist_ok=False)
    sdk = Path(subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip())
    # A Python installed under /usr/local may itself run under Rosetta. Target
    # the host ISA explicitly so it cannot silently select translated code.
    arm64 = subprocess.run(["/usr/sbin/sysctl", "-n", "hw.optional.arm64"],
                           capture_output=True, text=True)
    target_arch = "arm64" if arm64.returncode == 0 and arm64.stdout.strip() == "1" else "x86_64"
    header = sdk / "usr/include/c++/v1/__hash_table"
    original = header.read_text()
    modified = original
    targets = [
        """            {\n                if ((__ndptr->__hash() == __hash) &&\n                    key_eq()(__ndptr->__upcast()->__value_, __value))""",
        """            {\n                if ((__nd->__hash() == __hash) &&\n                    key_eq()(__nd->__upcast()->__value_, __k))""",
    ]
    for target in targets:
        if modified.count(target) != 1:
            raise RuntimeError("SDK unique-insertion loop differs; review instrumentation before proceeding")
        modified = modified.replace(target, target.replace(
            "            {\n", "            {\n                ++::kkt_hash_probe::unique_insert_visits;\n", 1))
    sources = ["test/output_api_witness.cpp", "kkt/kkt.cpp",
               "verifier/verifier_v2.cpp", "lca/lca.cpp", "union_find/union_find.cpp"]
    bound_sources = set(sources + ["test/run_output_api_witness.py"])
    for directory in ("common", "kkt", "verifier", "lca", "union_find"):
        bound_sources.update(str(p.relative_to(root)) for p in (root / directory).glob("*.hpp"))
    configurations = {"default": []}
    metadata = {"purpose": "Untimed comparison of both KKT output APIs and exact unique-insertion bucket-node visits",
                "not_measured": ["wall time", "cache misses", "TLB misses"],
                "sdk": str(sdk), "original_header": str(header),
                "target_arch": target_arch,
                "original_header_sha256": sha(header),
                "modified_header_sha256": hashlib.sha256(modified.encode()).hexdigest(),
                "instrumentation": "One increment in each of two unique-insertion bucket traversal loops",
                "source_sha256": {p: sha(root / p) for p in sorted(bound_sources)},
                "configurations": configurations, "commands": [], "executions": {},
                "records": [], "status": "incomplete"}
    metadata["compiler"] = subprocess.check_output(["/usr/bin/clang++", "--version"], text=True)
    def save_metadata():
        (args.output / "RESULTS.json").write_text(json.dumps(metadata, indent=2) + "\n")
    save_metadata()
    with tempfile.TemporaryDirectory(prefix="kkt-output-api-witness-") as temporary:
        temp = Path(temporary)
        include = temp / "include"; include.mkdir()
        (include / "__hash_table").write_text(modified)
        counter = temp / "counter.hpp"
        counter.write_text("#pragma once\nnamespace kkt_hash_probe { inline unsigned long long unique_insert_visits = 0; }\n")
        for name, flags in configurations.items():
            binary = temp / name
            command = ["/usr/bin/clang++", "-arch", target_arch, "-std=c++17", "-O2", "-Wall", "-Wextra",
                       "-isysroot", str(sdk), "-I" + str(include), "-I" + str(root),
                       "-include", str(counter), "-DKKT_ENABLE_WORK_STATS",
                       '-DKKT_HASH_WITNESS_CONFIG="' + name + '"']
            command += ["-D" + flag for flag in flags]
            command += [str(root / p) for p in sources] + ["-o", str(binary)]
            metadata["commands"].append(command)
            build = subprocess.run(command, capture_output=True, text=True)
            (args.output / (name + ".build.stdout")).write_text(build.stdout)
            (args.output / (name + ".build.stderr")).write_text(build.stderr)
            metadata["executions"][name] = {"build_exit_code": build.returncode}
            if build.returncode:
                metadata["status"] = "build_failed"
            save_metadata()
            build.check_returncode()
            metadata["executions"][name]["binary_sha256"] = sha(binary)
            metadata["executions"][name]["binary_format"] = subprocess.check_output(
                ["/usr/bin/file", str(binary)], text=True).strip()
            run = subprocess.run([str(binary)], capture_output=True, text=True)
            (args.output / (name + ".stdout.jsonl")).write_text(run.stdout)
            (args.output / (name + ".stderr")).write_text(run.stderr)
            metadata["executions"][name]["run_exit_code"] = run.returncode
            if run.returncode:
                metadata["status"] = "run_failed"
            save_metadata()
            run.check_returncode()
            records = [json.loads(line) for line in run.stdout.splitlines()]
            assert len(records) == 16
            metadata["records"].extend(records)
    metadata["status"] = "pass"
    save_metadata()
    print(json.dumps({"status": "pass", "cases": len(metadata["records"]),
                      "output": str(args.output)}))


if __name__ == "__main__":
    main()
