#!/usr/bin/env python3
"""One held-out diagnostic profile; never a benchmark or an unattended campaign."""
import argparse
import contextlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "benchmark"))
import run_edge_view_experiment as paired

native, analysis, monitor = paired.native, paired.analysis, paired.monitor
require, write_json = paired.require, paired.write_json
FIXTURE = {"family": "leaf_hierarchy4", "n": 2097152, "m": 33554432,
           "density": 16, "intrusion_per_mille": 0, "graph_seed": 6000011,
           "kkt_seed": 1423, "calls": 4}


def preparation():
    path = HERE.with_name("prepared-commands.json")
    prepared = analysis.read_json(path)
    freeze = Path(prepared["edge_view_freeze"])
    analysis.hash_check(freeze, prepared["edge_view_freeze_sha256"])
    frozen, _ = paired.check_freeze(freeze)
    edge = frozen["variants"]["edge"]["build"]
    record = edge["record"]
    source, obj, binary = (HERE.with_name(name) for name in ("kkt_profile.cpp", "kkt_profile.o", "kkt_profile"))
    link = list(record["link_command"])
    link[link.index(record["main_object"])] = str(obj)
    link[-1] = str(binary)
    first_object = next(i for i, arg in enumerate(link) if arg.endswith(".o"))
    compile_argv = link[:first_object] + ["-DKKT_EXPERIMENT_EDGE_VIEW", "-c", str(source), "-o", str(obj)]
    for field, expected in (("schema", "kkt_profile_preparation_v1"), ("working_directory", str(ROOT)),
                            ("parent_build_record", edge["path"]), ("parent_build_record_sha256", edge["sha256"]),
                            ("driver_source", str(source)), ("object_paths", record["object_paths"]),
                            ("object_sha256", record["object_sha256"]), ("compiler", record["compiler"]),
                            ("sdk", record["sdk"]), ("compile_command", compile_argv), ("link_command", link),
                            ("binary", str(binary)), ("fixture", FIXTURE)):
        analysis.equal(prepared, field, expected, "profile preparation")
    analysis.hash_check(source, prepared["driver_source_sha256"])
    return prepared, path


def build_record(path, prepared, prepared_path):
    record = analysis.read_json(path)
    for field, expected in (("schema", "kkt_profile_build_v1"),
                            ("prepared_commands_sha256", native.sha(prepared_path)),
                            ("driver_source_sha256", prepared["driver_source_sha256"]),
                            ("edge_view_freeze_sha256", prepared["edge_view_freeze_sha256"]),
                            ("commands", [prepared["compile_command"], prepared["link_command"]]),
                            ("exit_statuses", [0, 0]), ("production_object_sha256", prepared["object_sha256"]),
                            ("compiler", prepared["compiler"]), ("sdk", prepared["sdk"]),
                            ("binary", prepared["binary"])):
        analysis.equal(record, field, expected, "profile build")
    analysis.hash_check(Path(record["binary"]), record["binary_sha256"])
    analysis.hash_check(HERE.with_name("kkt_profile.o"), record["driver_object_sha256"])
    analysis.hash_check(Path(record["build_log"]), record["build_log_sha256"])
    require(record["binary_profile"]["file_description"] == "Mach-O 64-bit executable arm64" and
            record["binary_profile"]["main_stack_bytes"] == 536870912, "wrong profile binary architecture/stack")
    return record


def completed_markers(markers, pid):
    expected = [("GENERATION_BEGIN", -1), ("CERTIFICATE_BEGIN", -1), ("READY", None)]
    expected += [(event, rep) for rep in range(4) for event in ("KKT_BEGIN", "KKT_END", "VALIDATED")]
    expected += [("DONE", -1)]
    require([(row.get("event"), row.get("repetition")) for row in markers] == expected,
            "missing, duplicate, reordered or unexpected profiling markers")
    ready = markers[2]
    for field, value in FIXTURE.items():
        if field != "intrusion_per_mille": analysis.equal(ready, field, value, "READY")
    require(ready["pid"] == pid and ready["validation"] == "pass", "wrong READY PID/certificate")
    for field in ("input_fingerprint", "topology_fingerprint"):
        require(type(ready[field]) is int and 0 <= ready[field] < 2**64, "invalid READY fingerprint")


def capture(args):
    require(args.released, "profiling requires explicit root quiet-period --released")
    prepared, prepared_path = preparation()
    build_path = args.build_record.resolve(strict=True)
    build = build_record(build_path, prepared, prepared_path)
    output = args.output.resolve()
    require(not output.exists(), "refusing to overwrite profiling evidence")
    output.mkdir(parents=True)
    info = {"schema": "kkt_sample_profile_v1", "validation": "running",
            "diagnostic_only": True, "profiling_overhead_present": True, "benchmark_timing": False,
            "fixture": FIXTURE, "prepared_commands": prepared, "prepared_commands_sha256": native.sha(prepared_path),
            "build_record": str(build_path), "build_record_sha256": native.sha(build_path),
            "binary_sha256": build["binary_sha256"], "driver_object_sha256": build["driver_object_sha256"],
            "controller_sha256": native.sha(HERE), "started_utc": native.now(),
            "groups": {}, "markers": [], "cleanup": [], "native_process_may_still_be_running": False,
            "resource_rule": {**paired.RULE, "measure": "Sequential bounded RSS observations summed across both owned groups"},
            "deadlines_seconds": {"ready": 600, "attach_after_ready": 45, "driver": 900, "sampler": 90}}
    sidecar = output / "profile.json"
    write_json(sidecar, info)
    sampler = monitor.BoundedSampler(monitor.LibprocProvider())
    processes, unavailable, empty = {}, {}, set()
    start = time.monotonic(); ready_at = None; released = False; attach_banner = None
    lines_seen = 0; failure = None; incomplete_observations = 0
    old_term = signal.getsignal(signal.SIGTERM)
    def interrupted(signum, frame): raise KeyboardInterrupt(f"profile controller received signal {signum}")
    signal.signal(signal.SIGTERM, interrupted)
    try:
        with contextlib.ExitStack() as stack:
            logs = {name: stack.enter_context((output / name).open("xb"))
                    for name in ("driver.stdout", "driver.stderr", "sample.stdout", "sample.stderr")}
            resources = stack.enter_context((output / "resources.jsonl").open("x"))
            def launch(name, argv):
                require(not sampler.poisoned, "poisoned monitor prohibits a new child")
                child = subprocess.Popen(argv, cwd=ROOT, stdin=subprocess.PIPE if name == "driver" else subprocess.DEVNULL,
                                         stdout=logs[name + ".stdout"], stderr=logs[name + ".stderr"], start_new_session=True)
                processes[name] = child; unavailable[name] = 0
                info["groups"][name] = {"command": argv, "process_group": child.pid, "started_monotonic": time.monotonic()}
                write_json(sidecar, info)
            def read_markers():
                nonlocal lines_seen, ready_at
                data = (output / "driver.stdout").read_bytes()
                require(len(data) <= 65536, "unexpectedly large profiling marker stream")
                lines = data.split(b"\n")[:-1]
                for line in lines[lines_seen:]:
                    require(line.startswith(b"profile_v1 "), "unexpected driver stdout")
                    marker = json.loads(line[len(b"profile_v1 "):])
                    info["markers"].append(marker)
                    if marker.get("event") == "READY":
                        require(ready_at is None, "duplicate READY")
                        require([(r.get("event"), r.get("repetition")) for r in info["markers"]] ==
                                [("GENERATION_BEGIN", -1), ("CERTIFICATE_BEGIN", -1), ("READY", None)], "unexpected pre-READY phases")
                        for field, value in FIXTURE.items():
                            if field != "intrusion_per_mille": analysis.equal(marker, field, value, "READY")
                        require(marker["pid"] == processes["driver"].pid and marker["validation"] == "pass", "READY identity/certificate mismatch")
                        require(processes["driver"].poll() is None, "driver exited before sampler launch")
                        ready_at = time.monotonic()
                        launch("sample", ["/usr/bin/sample", str(marker["pid"]), "60", "1", "-mayDie", "-file", str(output / "sample.txt")])
                lines_seen = len(lines)
            launch("driver", ["/usr/bin/arch", "-arm64", prepared["binary"]])
            while True:
                tick = time.monotonic()
                require(tick - start <= 900, "whole-driver wall deadline exceeded")
                observations = {}
                # Check both groups even while waiting for READY or attachment.
                for name, child in processes.items():
                    if name in empty: continue
                    exited = child.poll()
                    row = sampler.sample(child.pid)
                    observations[name] = row
                    resources.write(json.dumps({"kind": "group_observation", "name": name, "observation": row}) + "\n")
                    resources.flush()
                    require(not sampler.poisoned, "RSS sampler timed out; stop both groups")
                    if row["validation"] == "pass":
                        unavailable[name] = 0
                        if exited is not None and not row["members"]:
                            empty.add(name)
                            info["groups"][name]["exit_status"] = exited
                            info["groups"][name]["group_exit_verification"] = row
                    else:
                        unavailable[name] += 1
                        require(unavailable[name] < 3, name + ": three unavailable RSS observations")
                known_sum = sum(row["rss_kib"] for row in observations.values() if row["validation"] == "pass")
                complete = all(row["validation"] == "pass" for row in observations.values())
                incomplete_observations = 0 if complete else incomplete_observations + 1
                resources.write(json.dumps({"kind": "combined_observation", "monotonic_ns": time.monotonic_ns(), "groups": observations,
                                            "known_rss_sum_kib": known_sum,
                                            "complete": complete}) + "\n")
                resources.flush()
                require(known_sum <= paired.RULE["rss_limit_kib"], "combined sampled RSS exceeded 40 GiB")
                require(incomplete_observations < 3, "three incomplete combined RSS observations")

                read_markers()
                if ready_at is None: require(time.monotonic() - start <= 600, "READY deadline exceeded")
                if "sample" in processes:
                    sampling = processes["sample"]
                    require(time.monotonic() - info["groups"]["sample"]["started_monotonic"] <= 90, "sampler/report deadline exceeded")
                    sample_log = (output / "sample.stdout").read_text(errors="replace") + (output / "sample.stderr").read_text(errors="replace")
                    if not released:
                        require(sampling.poll() is None, "sampler exited before confirmed attachment")
                        require(time.monotonic() - ready_at <= 45, "no confirmed sampler attachment within deadline")
                        banner = re.search(r"Sampling process\s+" + str(processes["driver"].pid) + r"\b", sample_log)
                        if banner:
                            attach_banner = banner.group(0)
                            require(processes["driver"].poll() is None, "driver exited before release")
                            processes["driver"].stdin.write(b"G"); processes["driver"].stdin.flush()
                            processes["driver"].stdin.close(); released = True
                            info.update(attachment_banner=attach_banner, release_monotonic_ns=time.monotonic_ns())
                    if sampling.poll() is not None:
                        require(sampling.returncode == 0, "sample failed; no permission workaround")
                        require(processes["driver"].poll() is not None, "sample ended before driver completed; partial profile")
                if processes["driver"].poll() is not None:
                    require(processes["driver"].returncode == 0, "driver failed")
                    # The driver may have finished after the earlier stdout read.
                    read_markers()
                    completed_markers(info["markers"], processes["driver"].pid)
                write_json(sidecar, info)
                if released and set(processes) == empty == {"driver", "sample"}: break
                time.sleep(max(0, paired.RULE["poll_seconds"] - (time.monotonic() - tick)))
            require((output / "sample.txt").is_file() and (output / "sample.txt").stat().st_size > 0, "missing sample report")
            # Parent/helper/source/binary drift after profiling invalidates success.
            analysis.hash_check(prepared_path, info["prepared_commands_sha256"])
            analysis.hash_check(build_path, info["build_record_sha256"])
            analysis.hash_check(Path(prepared["binary"]), build["binary_sha256"])
            analysis.hash_check(HERE.with_name("kkt_profile.o"), build["driver_object_sha256"])
            preparation(); build_record(build_path, prepared, prepared_path)
            require(native.sha(HERE) == info["controller_sha256"], "profile controller changed during capture")
            info["validation"] = "pass"
    except BaseException as error:
        failure = error; info.update(validation="failed", error=repr(error))
    finally:
        for name in ("sample", "driver"):
            child = processes.get(name)
            if child is not None and child.stdin is not None and not child.stdin.closed:
                try: child.stdin.close()
                except Exception as error:
                    info.setdefault("stdin_close_errors", []).append({"name": name, "error": repr(error)})
            if child is not None and name not in empty:
                cleanup = monitor.bounded_terminate(child, sampler)
                info["cleanup"].append({"name": name, **cleanup})
                info["native_process_may_still_be_running"] |= cleanup["native_process_may_still_be_running"]
        signal.signal(signal.SIGTERM, old_term)
        info.update(finished_utc=native.now(), monitor_events=sampler.events,
                    artifacts_sha256={path.name: native.sha(path) for path in output.iterdir() if path.is_file() and path != sidecar})
        if info["native_process_may_still_be_running"]: info["validation"] = "failed"
        write_json(sidecar, info)
    if failure: raise failure
    require(info["validation"] == "pass", "profile cleanup did not establish both groups empty")
    print("Diagnostic profile completed; four exact-ID checks, both groups empty. Not benchmark timing.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-record", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--released", action="store_true")
    capture(parser.parse_args())
