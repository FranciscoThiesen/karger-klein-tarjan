#!/usr/bin/env python3
"""Serial, fail-closed capture of five unchanged MST solvers.

One native child per case/graph/sampling seed. Raw child CSVs, logs, periodic
process-group RSS observations, warmups and partial failures are never trimmed.
The native binary must certify the reference independently and emit the exact
reference_certificate_v1 JSON marker before its solver outputs are accepted.
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
import time

import analyze_continuation as base
import crossover_clocks as clocks
from run_crossover import source_inventory
from run_crossover_baselines import FIELDS, TEXT_FIELDS, MAX_NS

ALGORITHMS = ("kkt", "compacting_boruvka", "kruskal", "prim", "boruvka")
CERTIFICATE_PREFIX = "reference_certificate_v1 "
CERTIFICATE_FIELDS = {"case_id", "graph_seed", "kkt_seed", "n", "m", "input_fingerprint", "topology_fingerprint", "validation"}
LIFTED_FAMILIES = tuple(f"lifted_{mode}{factor}" for mode in ("hierarchy", "distance", "random") for factor in (2, 4))
ATTACHMENT_FAMILIES = tuple(f"{endpoint}_{mode}{factor}" for endpoint in ("leaf", "community")
                            for mode in ("hierarchy", "distance", "shuffled", "random") for factor in (4, 16))
FAMILIES = (*(family for family in base.FAMILIES if family != "legacy_random"), *LIFTED_FAMILIES, *ATTACHMENT_FAMILIES)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def helpers():
    names = ("run_mst_search.py", "analyze_mst_search.py", "run_crossover.py", "analyze_continuation.py",
             "crossover_clocks.py", "run_crossover_baselines.py")
    return {str(Path(__file__).with_name(name).resolve()): sha(Path(__file__).with_name(name)) for name in names}


def binary_profile(binary):
    """Inspect the frozen Mach-O before any measured child is started."""
    description = subprocess.check_output(["/usr/bin/file", "-b", str(binary)], text=True).strip()
    commands = subprocess.check_output(["/usr/bin/otool", "-l", str(binary)], text=True)
    stacks = re.findall(r"cmd LC_MAIN\s+cmdsize \d+\s+entryoff \d+\s+stacksize (\d+)", commands)
    base.require("Mach-O 64-bit executable arm64" in description and stacks == ["536870912"],
                 "search requires the native arm64 Make large-stack binary (512 MiB)")
    return {"file_description": description, "main_stack_bytes": int(stacks[0]), "otool_load_commands": commands}


def load_manifest(path):
    cases = {}
    for context, raw in base.read_csv(path, base.MANIFEST_FIELDS):
        base.require(re.fullmatch(r"[a-z][a-z0-9_]{0,63}", raw["family"]), context + ": invalid family identifier")
        spec = {"family": raw["family"], **{f: base.integer(raw[f], context + " " + f, 2**32-1)
                                           for f in base.MANIFEST_FIELDS[1:]}}
        n, d, p = spec["n"], spec["density"], spec["intrusion_per_mille"]
        family = spec["family"]
        m = n*d
        base.require(family in FAMILIES, context + ": unsupported family")
        base.require(32 <= n <= 2**22 and n & (n-1) == 0 and 1 <= d <= 512 and p == 0 and
                     m <= min(2**27, n*(n-1)//2) and m < 0x3f3f3f3f,
                     context + ": outside frozen size/density/edge limits")
        if family in LIFTED_FAMILIES:
            b = int(family[-1]); q = n//b; numerator = m-q*(b-1)
            base.require(q >= b*b and numerator >= 0 and numerator % (b*b) == 0 and
                         q-1 <= numerator//(b*b) <= q*(q-1)//2,
                         context + ": invalid lifted core size, integrality or simple-graph capacity")
        if family in ATTACHMENT_FAMILIES:
            b = 16 if family.endswith("16") else 4
            q = n//b
            # Each of q stars contributes b-1 edges; every external core pair
            # contributes ONE edge. There is no b-squared bundle division.
            external_edges = m-n+q
            base.require(n % b == 0 and q-1 <= external_edges <= q*(q-1)//2,
                         context + ": attachment core cannot be a connected simple graph")
        if family == "legacy_random":
            base.require(d in (4, 32, 128), context + ": invalid legacy density")
        if family in ("grid2d_metric", "grid2d_random"):
            base.require(d >= 2, context + ": grid scaffold requires density at least two")
        if family == "gnm_random":
            base.require(d >= 16, context + ": connected G(n,m) requires density at least sixteen")
        spec.update(m=m, case_id=base.case_id(spec))
        base.require(spec["case_id"] not in cases, context + ": duplicate case")
        cases[spec["case_id"]] = spec
    base.require(cases, "empty manifest")
    return cases


def check_fingerprints(rows):
    """Bind repeated inputs and only genuinely paired topology variants."""
    weighted, topologies = {}, {}
    for row in rows:
        key = row["case_id"], row["graph_seed"]
        value = row["input_fingerprint"], row["topology_fingerprint"]
        base.require(key not in weighted or weighted[key] == value, f"{key}: inconsistent graph fingerprints")
        weighted[key] = value
        family = row["family"]
        if family in LIFTED_FAMILIES: group = "lift"+family[-1]
        elif family in ATTACHMENT_FAMILIES:
            endpoint = family.split("_", 1)[0]
            b = 16 if family.endswith("16") else 4
            group = f"attachment_{endpoint}{b}"
        elif family in ("line_metric", "line_random", "line_wide_metric"): group = "line"
        elif family in ("grid2d_metric", "grid2d_random"): group = "grid"
        elif family in ("hierarchical_tree", "random_tree", "distance_tree"): group = "tree"
        elif family in ("hierarchical_path", "low_path", "random_path", "distance_path"): group = "path"
        else: group = family
        pair = group, row["n"], row["density"], row["graph_seed"]
        base.require(pair not in topologies or topologies[pair] == row["topology_fingerprint"],
                     f"{pair}: paired weight controls have different topology/order fingerprints")
        topologies[pair] = row["topology_fingerprint"]
    return weighted


def protocol(repetitions, warmups):
    base.require(type(repetitions) is int and 5 <= repetitions <= 100 and repetitions % 5 == 0,
                 "repetitions must be a positive multiple of five in [5,100]")
    base.require(type(warmups) is int and 1 <= warmups <= 100, "warmups must be in [1,100]")


def check_rows(path, spec, graph_seed, kkt_seed, repetitions, warmups):
    protocol(repetitions, warmups)
    rows = []
    for context, raw in base.read_csv(path, FIELDS):
        row = dict(raw)
        for field in FIELDS:
            if field not in TEXT_FIELDS:
                row[field] = base.integer(raw[field], context + " " + field,
                                          MAX_NS if field.endswith("_ns") else base.UINT64_MAX)
        base.require(all(row[field] == value for field, value in spec.items()), context + ": fixture differs from manifest")
        base.require(row["graph_seed"] == graph_seed and row["kkt_seed"] == kkt_seed and
                     row["warmups"] == warmups and row["validation"] == "pass", context + ": seed or validation mismatch")
        base.require(row["elapsed_ns"] > 0 and row["utc_start_ns"] > 0 and row["utc_end_ns"] > 0 and
                     row["process_cpu_end_ns"] - row["process_cpu_start_ns"] == row["process_cpu_elapsed_ns"] > 0,
                     context + ": invalid steady/CPU duration or clock endpoint")
        rows.append(row)
    expected = [(phase, repetition, order, ALGORITHMS[(order+repetition) % 5])
                for phase, count in (("warmup", warmups), ("timed", repetitions))
                for repetition in range(count) for order in range(5)]
    base.require(len(rows) == len(expected), "incomplete five-solver matrix")
    diagnostics = []
    previous_cpu = previous_utc = None
    for row, identity in zip(rows, expected):
        base.require(tuple(row[f] for f in ("phase", "repetition", "order", "algorithm")) == identity,
                     "duplicate, missing or incorrectly ordered five-solver call")
        base.require(previous_cpu is None or row["process_cpu_start_ns"] >= previous_cpu,
                     "process CPU clock reversed or overlapped between calls")
        previous_cpu = row["process_cpu_end_ns"]
        cpu, steady = row["process_cpu_elapsed_ns"], row["elapsed_ns"]
        utc = row["utc_end_ns"] - row["utc_start_ns"]
        threshold_times_four = max(2_000_000_000, cpu)
        flags = []
        if utc < 0: flags.append("realtime_reversed_within_call")
        if previous_utc is not None and row["utc_start_ns"] < previous_utc: flags.append("realtime_reversed_between_calls")
        if 4*(steady-cpu) > threshold_times_four: flags.append("steady_exceeds_process_cpu")
        if 4*(cpu-steady) > threshold_times_four: flags.append("process_cpu_exceeds_steady")
        if 4*abs(utc-steady) > threshold_times_four: flags.append("utc_steady_duration_disagreement")
        previous_utc = row["utc_end_ns"]
        diagnostics.append({"case_id": spec["case_id"], "graph_seed": graph_seed, "kkt_seed": kkt_seed,
            **dict(zip(("phase", "repetition", "order", "algorithm"), identity)),
            "elapsed_ns": steady, "process_cpu_elapsed_ns": cpu, "utc_elapsed_ns": utc,
            "steady_minus_cpu_ns": steady-cpu, "utc_minus_steady_ns": utc-steady,
            "diagnostic_flags": flags, "excluded": False})
    base.require(len({(r["input_fingerprint"],r["topology_fingerprint"]) for r in rows}) == 1,
                 "algorithms/phases received different input fingerprints")
    return rows, diagnostics


def check_certificate(log, rows):
    certificates = []
    for number, line in enumerate(log.read_text().splitlines(), 1):
        if not line.startswith("reference_certificate"): continue
        base.require(line.startswith(CERTIFICATE_PREFIX), f"{log}:{number}: invalid certificate marker")
        certificate = clocks.parse_json(line[len(CERTIFICATE_PREFIX):])
        base.require(type(certificate) is dict and set(certificate) == CERTIFICATE_FIELDS,
                     "unexpected certificate marker fields")
        certificates.append(certificate)
    base.require(len(certificates) == 1, "expected exactly one successful independent reference certificate")
    expected = {f: rows[0][f] for f in CERTIFICATE_FIELDS}
    base.require(all(type(certificates[0][f]) is type(value) and certificates[0][f] == value
                     for f,value in expected.items()), "certificate marker differs from captured graph")
    return certificates[0]


def capture_clock_flags(info):
    """UTC is descriptive; process ordering is checked using monotonic endpoints."""
    flags = []
    start = datetime.datetime.fromisoformat(info["started_utc"])
    finish = datetime.datetime.fromisoformat(info["finished_utc"])
    if finish < start: flags.append({"scope": "capture", "flag": "utc_reversed_interval"})
    previous = start
    for index, item in enumerate(info["captures"], 1):
        if "finished_utc" not in item: continue
        child_start = datetime.datetime.fromisoformat(item["started_utc"])
        child_finish = datetime.datetime.fromisoformat(item["finished_utc"])
        scope = f"child {index}"
        if child_finish < child_start: flags.append({"scope": scope, "flag": "utc_reversed_interval"})
        if child_start < previous: flags.append({"scope": scope, "flag": "utc_reversed_between_children"})
        if child_start < start or child_finish > finish:
            flags.append({"scope": scope, "flag": "utc_interval_outside_capture"})
        previous = child_finish
    return flags


def sample_rss(group):
    """RSS is a sampled process-group sum in KiB, not a continuous peak/footprint."""
    observation = {"utc": now(), "monotonic_ns": time.monotonic_ns(), "process_group": group}
    try:
        result = subprocess.run(["/bin/ps", "-axo", "pid=,pgid=,rss=,comm="], check=True,
                                capture_output=True, text=True, timeout=5)
        members = []
        for line in result.stdout.splitlines():
            fields = line.split(None, 3)
            if len(fields) == 4 and fields[1] == str(group):
                pid, pgid, rss = map(int, fields[:3])
                if rss < 0: raise ValueError("negative ps RSS")
                members.append({"pid": pid, "rss_kib": rss, "command": fields[3]})
        observation.update(validation="pass", members=members, rss_kib=sum(m["rss_kib"] for m in members))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        observation.update(validation="unavailable", error=repr(error))
    return observation


def terminate(process):
    if process is None or process.poll() is not None: return
    try: os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError: return
    try: process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try: os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("binary", "manifest", "output"):
        parser.add_argument("--"+name, required=True, type=Path)
    parser.add_argument("--graph-seeds", type=base.seed_bank, required=True)
    parser.add_argument("--sampling-seeds", type=base.seed_bank, required=True)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--rss-limit-gib", type=int, default=40)
    parser.add_argument("--rss-poll-seconds", type=float, default=2)
    args = parser.parse_args()
    protocol(args.repetitions,args.warmups)
    base.require(1 <= args.rss_limit_gib <= 40 and .25 <= args.rss_poll_seconds <= 60,
                 "RSS limit must be 1–40 GiB; poll interval must be 0.25–60 seconds")
    root=Path.cwd().resolve();binary=args.binary.resolve(strict=True);manifest=args.manifest.resolve(strict=True)
    output=args.output.resolve();sidecar=output.with_suffix(".json")
    folder=output.with_name(output.stem+"_cases")
    base.require(output.suffix==".csv" and not any(p.exists() for p in (output,sidecar,folder)),
                 "output must be a new .csv path; refusing to overwrite evidence")
    cases=load_manifest(manifest);sources=source_inventory(root);python_sources=helpers()
    build_recipe = root/"Makefile"
    immutable={str(binary):sha(binary),str(manifest):sha(manifest),str(build_recipe):sha(build_recipe),**python_sources}
    inspected_binary = binary_profile(binary)
    def unchanged():
        base.require(source_inventory(root)==sources,"C++ source inventory changed during capture")
        base.require(all(Path(p).exists() and sha(p)==digest for p,digest in immutable.items()),
                     "binary, manifest or Python capture/analysis helper changed")
    output.parent.mkdir(parents=True,exist_ok=True);folder.mkdir()
    info={"schema":"mst_search_capture_v1","validation":"running","working_directory":str(root),
          "revision":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
          "platform":platform.platform(),"machine":platform.machine(),
          "profile":"Native Make Apple clang C++17 -O3 -march=native; assertions enabled; no work counters; 512MiB stack",
          "binary":str(binary),"binary_sha256":sha(binary),"manifest":str(manifest),"manifest_sha256":sha(manifest),
          "binary_profile":inspected_binary,"build_recipe_sha256":{"Makefile":sha(build_recipe)},
          "source_sha256":sources,"python_source_sha256":python_sources,
          "case_order":list(cases),"graph_seeds":args.graph_seeds,"sampling_seeds":args.sampling_seeds,
          "algorithms":ALGORITHMS,"repetitions":args.repetitions,"warmups":args.warmups,
          "schedule":"case,graph seed,sampling seed; warmup then timed; repetition then order0..4; algorithm=(order+repetition)%5",
          "timing_boundary":"Common native tuple input; public native result types. KKT/compactor conversion and temporary input destruction timed; returned result destruction and exact validation excluded. UTC/CPU clocks enclose steady interval.",
          "certificate_scope":"Exactly one independent native reference certificate per child, followed by exact unique-MST ID/tuple validation for every row.",
          "resource_rule":{"rss_limit_kib":args.rss_limit_gib*1024**2,"poll_seconds":args.rss_poll_seconds,
                           "measure":"Sum of ps RSS KiB over child process group; sampled, not a continuous peak; shared pages may be counted more than once.",
                           "failure":"Terminate above ceiling or after three consecutive ps failures; retain every partial artifact."},
          "rows_removed":0,"rows_adjusted":0,"started_utc":now(),"started_monotonic_ns":time.monotonic_ns(),"captures":[]}
    write_json(sidecar,info);begin=time.monotonic();all_rows=[];all_diagnostics=[]
    def interrupted(signum,frame): raise KeyboardInterrupt(f"capture received signal {signum}")
    signal.signal(signal.SIGTERM,interrupted)
    try:
        with output.open("x",newline="") as combined:
            writer=csv.DictWriter(combined,fieldnames=FIELDS);writer.writeheader();combined.flush()
            for spec in cases.values():
                for graph_seed in args.graph_seeds:
                    for kkt_seed in args.sampling_seeds:
                        unchanged();index=len(info["captures"])+1
                        raw=folder/f"{index:04d}_{spec['case_id']}_g{graph_seed}_s{kkt_seed}.csv"
                        log=raw.with_suffix(".log");rss=raw.with_suffix(".rss.jsonl")
                        command=[str(binary),"--family",spec["family"],"--n",str(spec["n"]),"--density",str(spec["density"]),
                                 "--graph-seed",str(graph_seed),"--kkt-seed",str(kkt_seed),"--repetitions",str(args.repetitions),"--warmups",str(args.warmups)]
                        item={"case_id":spec["case_id"],"graph_seed":graph_seed,"kkt_seed":kkt_seed,"command":command,
                              "csv":str(raw),"log":str(log),"rss_log":str(rss),"started_utc":now(),
                              "started_monotonic_ns":time.monotonic_ns()}
                        info["captures"].append(item);write_json(sidecar,info)
                        process=None;failure=None;case_begin=time.monotonic();observations=[];unavailable=0
                        try:
                            with raw.open("x") as stdout,log.open("x") as stderr,rss.open("x") as resource:
                                process=subprocess.Popen(["/usr/bin/time","-l",*command],cwd=root,stdout=stdout,stderr=stderr,start_new_session=True)
                                while True:
                                    observation=sample_rss(process.pid);observations.append(observation)
                                    resource.write(json.dumps(observation,allow_nan=False)+"\n");resource.flush()
                                    if observation["validation"]=="pass":
                                        unavailable=0
                                        base.require(observation["rss_kib"]<=info["resource_rule"]["rss_limit_kib"],"sampled process-group RSS exceeded the ceiling")
                                    else:
                                        unavailable+=1
                                        base.require(unavailable<3,"three consecutive RSS observations failed")
                                    try:exit_status=process.wait(timeout=args.rss_poll_seconds);break
                                    except subprocess.TimeoutExpired:pass
                        except BaseException as error:
                            failure=error;terminate(process);exit_status=process.returncode if process else -1
                        item.update(exit_status=exit_status,interruption=repr(failure) if failure else None,
                                    finished_utc=now(),finished_monotonic_ns=time.monotonic_ns(),
                                    monotonic_elapsed_seconds=time.monotonic()-case_begin,
                                    output_sha256=sha(raw),log_sha256=sha(log),rss_sha256=sha(rss),rss_observations=len(observations),
                                    rss_unavailable=sum(r["validation"]!="pass" for r in observations),
                                    rss_nonempty_observations=sum(r["validation"]=="pass" and bool(r["members"]) for r in observations),
                                    sampled_peak_rss_kib=max((r["rss_kib"] for r in observations if r["validation"]=="pass"),default=None))
                        write_json(sidecar,info)
                        if failure:raise failure
                        base.require(exit_status==0,"native child failed; partial raw evidence retained")
                        unchanged();rows,diagnostics=check_rows(raw,spec,graph_seed,kkt_seed,args.repetitions,args.warmups)
                        certificate=check_certificate(log,rows)
                        check_fingerprints([*all_rows,*rows])
                        item.update(validation="pass",rows=len(rows),certificate=certificate,
                                    flagged_calls=sum(bool(r["diagnostic_flags"]) for r in diagnostics))
                        writer.writerows(rows);combined.flush();all_rows.extend(rows);all_diagnostics.extend(diagnostics)
                        write_json(sidecar,info)
        unchanged();info.update(validation="pass",checked_rows=len(all_rows),
            checked_timed_rows=len(cases)*len(args.graph_seeds)*len(args.sampling_seeds)*args.repetitions*5,
            checked_warmup_rows=len(cases)*len(args.graph_seeds)*len(args.sampling_seeds)*args.warmups*5,
            flagged_calls=sum(bool(r["diagnostic_flags"]) for r in all_diagnostics))
    except BaseException as error:
        info.update(validation="failed",error=repr(error));raise
    finally:
        info.update(finished_utc=now(),finished_monotonic_ns=time.monotonic_ns(),
                    monotonic_elapsed_seconds=time.monotonic()-begin,call_diagnostics=all_diagnostics)
        info["capture_clock_flags"] = capture_clock_flags(info)
        if output.exists():info["output_sha256"]=sha(output)
        write_json(sidecar,info)
    print(f"Validated {len(cases)} cases: {info['checked_timed_rows']} timed + {info['checked_warmup_rows']} warmup calls")


if __name__=="__main__":
    main()
