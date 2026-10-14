#!/usr/bin/env python3
"""Validate already-built attachment dispatch binaries; never run a valid case.

Run only after integration and after all timing captures have stopped. This
script does not build anything. It checks native arm64 Mach-O code identity,
normal/512 MiB stack records, help, and invalid CLI rejection before generation.
Every command's stdout/stderr and failures are retained in a fresh directory.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import struct
import subprocess
import time

ATTACHMENT_FAMILIES = tuple(f"{endpoint}_{mode}{b}" for endpoint in ("leaf", "community")
                            for mode in ("hierarchy", "distance", "shuffled", "random") for b in (4, 16))
PYTHON_HELPERS = ("run_mst_search.py", "analyze_mst_search.py", "run_crossover.py",
                  "analyze_continuation.py", "crossover_clocks.py", "run_crossover_baselines.py")
OBJECT_NAMES = ("boruvka/boruvka", "kruskal/kruskal", "prim/prim", "lca/lca", "union_find/union_find",
                "graph_utils/graph_utils", "verifier/verifier_v2", "kkt/kkt")


def require(value, message):
    if not value: raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def inventory(root):
    paths = {path for pattern in ("*/*.cpp", "*/*.hpp") for path in root.glob(pattern)}
    paths.add(root/"Makefile")
    return {str(path.relative_to(root)): sha(path) for path in sorted(paths)}


def macho(path):
    data = path.read_bytes()
    require(len(data) >= 32, "truncated Mach-O header")
    magic, cpu, subtype, file_type, commands, command_bytes, flags, reserved = struct.unpack_from("<IiiIIIII", data)
    require(magic == 0xfeedfacf and cpu == 0x0100000c and file_type == 2,
            "expected a thin little-endian native arm64 Mach-O executable")
    require(commands > 0 and 32+command_bytes <= len(data), "truncated Mach-O load commands")
    result = {"path": str(path), "sha256": sha(path), "binary_bytes": len(data), "cpu_type": cpu,
              "cpu_subtype": subtype, "file_type": file_type, "flags": flags, "reserved": reserved}
    position = 32; body = None; main_count = text_count = 0
    for _ in range(commands):
        require(position+8 <= 32+command_bytes, "truncated load-command header")
        command, size = struct.unpack_from("<II", data, position)
        require(size >= 8 and size % 8 == 0 and position+size <= 32+command_bytes, "invalid load-command extent")
        if command == 0x80000028:  # LC_MAIN: entry_point_command
            require(size >= 24, "truncated LC_MAIN")
            entry, stack = struct.unpack_from("<QQ", data, position+8)
            result.update(entry_file_offset=entry, main_stack_bytes=stack); main_count += 1
        elif command == 0x19:  # LC_SEGMENT_64
            require(size >= 72, "truncated segment_command_64")
            section_count = struct.unpack_from("<I", data, position+64)[0]
            require(72+80*section_count <= size, "truncated section_64 table")
            for index in range(section_count):
                section = struct.unpack_from("<16s16sQQIIIIIIII", data, position+72+index*80)
                name, segment = section[0].rstrip(b"\0"), section[1].rstrip(b"\0")
                if (segment, name) != (b"__TEXT", b"__text"): continue
                address, length, offset = section[2:5]
                require(length > 0 and offset+length <= len(data), "invalid executable text section extent")
                body = data[offset:offset+length]; text_count += 1
                result.update(text_address=address, text_file_offset=offset, text_bytes=length,
                              text_sha256=hashlib.sha256(body).hexdigest())
        position += size
    require(position == 32+command_bytes and main_count == 1 and text_count == 1 and body is not None,
            "expected exactly one complete LC_MAIN and executable __TEXT,__text section")
    return result, body


def invalid_cases():
    base = ["--family", "leaf_hierarchy4", "--n", "1024", "--density", "2"]
    cases = [("missing_required", []), ("missing_value", ["--family"]),
        ("unknown_family", ["--family", "attachment_unknown", "--n", "1024", "--density", "2"])]
    for family in ATTACHMENT_FAMILIES:
        b = 16 if family.endswith("16") else 4
        # These targets fit the expanded simple graph but overfill the core:
        # b4,n32,d2: E40>C(8,2)28; b16,n512,d2: E544>C(32,2)496.
        cases.append((family+"_core_capacity", ["--family", family, "--n", str(512 if b == 16 else 32), "--density", "2"]))
    for label, family, n, density in (
        ("unknown_block", "leaf_hierarchy8", 1024, 2),
        ("unknown_mode", "community_shuffle4", 1024, 2),
        ("two_vertex_core", "leaf_shuffled16", 32, 1),
        ("zero_vertices", "community_random4", 0, 2),
        ("non_dyadic", "community_distance4", 1023, 2),
        ("too_few_vertices", "leaf_distance4", 16, 1),
        ("vertex_cap", "community_hierarchy16", 1 << 23, 1),
        ("edge_cap", "leaf_random4", 1 << 22, 33),
        ("density_zero", "leaf_hierarchy4", 1024, 0),
        ("density_cap", "community_shuffled16", 1024, 513),
        ("old_lift_domain", "lifted_hierarchy4", 32, 4),
        ("old_grid_domain", "grid2d_metric", 128, 1),
        ("old_gnm_domain", "gnm_random", 128, 4)):
        cases.append((label, ["--family", family, "--n", str(n), "--density", str(density)]))
    for label, tail in (
        ("repetitions_not_rotated", ["--repetitions", "4"]),
        ("repetitions_zero", ["--repetitions", "0"]),
        ("repetitions_cap", ["--repetitions", "105"]),
        ("warmups_zero", ["--warmups", "0"]), ("warmups_cap", ["--warmups", "101"]),
        ("duplicate_n", ["--n", "1024"]), ("negative_seed", ["--graph-seed", "-1"]),
        ("seed_overflow", ["--graph-seed", "4294967296"]),
        ("sampling_overflow", ["--kkt-seed", "4294967296"]),
        ("intrusion_unsupported", ["--intrusion-per-mille", "1"]),
        ("unknown_option", ["--not-a-flag", "1"])):
        cases.append((label, base+tail))
    require(len({name for name, _ in cases}) == len(cases), "duplicate validation case label")
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--normal-binary", type=Path)
    parser.add_argument("--large-binary", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--build-log", action="append", type=Path, default=[],
                        help="archive/hash existing build logs; this validator does not build")
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    normal = (args.normal_binary or root/"bin/mst_search").resolve(strict=True)
    large = (args.large_binary or root/"bin/large_stack/mst_search").resolve(strict=True)
    output = args.output_dir.resolve()
    require(not output.exists(), "refusing to overwrite build/CLI validation evidence")
    require(normal != large, "normal and enlarged-stack binaries must differ")
    require((root/"benchmark/core_attachment_fixtures.hpp").is_file(), "integrate the attachment header before validation")
    sources = inventory(root)
    helpers = {str(Path("benchmark")/name): sha(root/"benchmark"/name) for name in PYTHON_HELPERS}
    objects = {str(Path(".build")/(name+".o")): sha(root/".build"/(name+".o")) for name in OBJECT_NAMES}
    frozen = {normal: sha(normal), large: sha(large), Path(__file__).resolve(): sha(__file__)}
    output.mkdir(parents=True)
    (output/"validate_attachment_build.py").write_bytes(Path(__file__).read_bytes())
    (output/"Makefile.at_validation").write_bytes((root/"Makefile").read_bytes())
    record = {"schema": "attachment_build_validation_v1", "validation": "running", "started_utc": now(),
        "working_directory": str(root), "machine": platform.machine(), "platform": platform.platform(),
        "source_sha256": sources, "python_source_sha256": helpers, "object_sha256": objects,
        "validator_sha256": sha(__file__), "normal_binary": str(normal), "normal_binary_sha256": frozen[normal],
        "large_binary": str(large), "large_binary_sha256": frozen[large], "requested_stack_bytes": 1 << 29,
        "timing_runs_requested": 0, "valid_fixture_runs_requested": 0, "commands": [], "build_logs": [],
        "scope": "Already-built code/stack identity and rejection-before-generation checks only. No valid fixture "
                 "is executed; correctness and wrapper smoke remain separate gates. Source/object hashes are observed "
                 "provenance, not a replacement for the original build command/log."}
    def save():
        (output/"provenance.json").write_text(json.dumps(record, indent=2, allow_nan=False)+"\n")
    def unchanged():
        require(inventory(root) == sources, "C++/Make source inventory changed during validation")
        require(all(sha(root/path) == value for path, value in {**helpers, **objects}.items()), "helper or production object changed")
        require(all(sha(path) == value for path, value in frozen.items()), "binary or validator changed")
    def run(command, name):
        stdout_path, stderr_path = output/(name+".stdout"), output/(name+".stderr")
        item = {"command": command, "working_directory": str(root), "started_utc": now(),
                "stdout": stdout_path.name, "stderr": stderr_path.name}
        record["commands"].append(item); save()
        process = None; error = None; begin = time.monotonic()
        try:
            with stdout_path.open("x") as stdout, stderr_path.open("x") as stderr:
                process = subprocess.Popen(command, cwd=root, stdout=stdout, stderr=stderr, start_new_session=True)
                status = process.wait(timeout=10)
        except BaseException as caught:
            error = caught
            if process is not None and process.poll() is None:
                try: os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                process.wait()
            status = process.returncode if process is not None else None
        item.update(exit_status=status, finished_utc=now(), operational_elapsed_seconds=time.monotonic()-begin,
                    error=repr(error) if error else None,
                    stdout_sha256=sha(stdout_path) if stdout_path.exists() else None,
                    stderr_sha256=sha(stderr_path) if stderr_path.exists() else None)
        if stdout_path.exists(): item["stdout_nonempty"] = bool(stdout_path.stat().st_size)
        if stderr_path.exists(): item["fixture_generation_started"] = "Running " in stderr_path.read_text()
        save()
        if error: raise error
        return item, stdout_path.read_text(), stderr_path.read_text()
    save()
    try:
        for index, path in enumerate(args.build_log, 1):
            path = path.resolve(strict=True); target = output/f"build_log_{index:02d}_{path.name}"
            target.write_bytes(path.read_bytes())
            record["build_logs"].append({"original_path": str(path), "file": target.name, "sha256": sha(target)})
        normal_info, normal_text = macho(normal); large_info, large_text = macho(large)
        record.update(normal_macho=normal_info, large_macho=large_info)
        save()
        require(normal_info["main_stack_bytes"] == 0, "normal binary has an unexpected requested stack")
        require(large_info["main_stack_bytes"] == 1 << 29, "large binary is not the 512 MiB profile")
        require(normal_text == large_text, "normal/large executable __TEXT,__text bytes differ")
        record["entire_text_byte_identical"] = True
        record["text_identity_scope"] = "Entire executable __TEXT,__text only; no claim that all data sections or binaries are identical."
        cases = invalid_cases()
        for profile, binary in (("normal", normal), ("large", large)):
            item, stdout, stderr = run([str(binary), "--help"], profile+"_help")
            require(item["exit_status"] == 0 and "multiple of five" in stdout and "attachment" in stdout.lower()
                    and "Running " not in stderr, "integrated help check failed")
            item["expected_outcome"] = "successful_help"; item["validation"] = "pass"; save()
            for index, (name, arguments) in enumerate(cases, 1):
                item, stdout, stderr = run([str(binary), *arguments], f"{profile}_{index:02d}_{name}")
                item["expected_outcome"] = "reject_before_generation"
                item["fixture_generation_started"] = "Running " in stderr
                require(item["exit_status"] != 0 and not stdout and not item["fixture_generation_started"]
                        and "mst search:" in stderr, "invalid CLI accepted or generation started: " + name)
                item["validation"] = "pass"; save()
        unchanged()
        record.update(validation="pass", negative_cli_checks_per_binary=len(cases),
                      negative_cli_checks=2*len(cases), help_checks=2,
                      sources_helpers_objects_and_binaries_preserved=True)
    except BaseException as error:
        record.update(validation="failed", error=repr(error)); raise
    finally:
        record["finished_utc"] = now()
        record["observed_generation_start_commands"] = sum(bool(item.get("fixture_generation_started")) for item in record["commands"])
        record["artifact_sha256"] = {p.name: sha(p) for p in sorted(output.iterdir())
                                      if p.is_file() and p.name != "provenance.json"}
        save()
    print(json.dumps({"validation": record["validation"], "negative_cli_checks": record["negative_cli_checks"],
                      "stack_bytes": large_info["main_stack_bytes"], "text_sha256": large_info["text_sha256"],
                      "output_directory": str(output)}, indent=2))


if __name__ == "__main__":
    main()
