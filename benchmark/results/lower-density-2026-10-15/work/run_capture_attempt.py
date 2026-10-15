#!/usr/bin/env python3
"""Bounded truthful outer controller for the separately released untimed matrix."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location("lower_density_work_outer",HERE/"collect.py")
work=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(work)
BUDGET_SECONDS=108600  # 60*1800+600; a safety ceiling, never a finish-time prediction.


def identities():
    cases=[f"{family}_n{n}_d{density}_p0"
           for density,sizes in ((16,(512,2048,8192,32768,131072,524288,2097152)),
                                  (8,(256,1024,4096,16384,65536,262144,1048576,4194304)))
           for n in sizes for family in ("leaf_distance4","leaf_shuffled4")]
    return [("eighth",case,graph,3407) for graph,order in
            ((23000003,cases),(23000029,cases[::-1])) for case in order]


def recheck(hashes):
    for path,digest in hashes.items():work.analysis.hash_check(Path(path),digest)


def check_completion(capture,freeze_sha,hashes):
    captured,values=work.load(capture)
    work.require(captured["freeze"]==str(HERE/"freeze.json") and captured["freeze_sha256"]==freeze_sha,
                 "completed capture differs from supplied freeze")
    work.require(captured["validation"]=="pass" and captured["cleanup"]==[] and
                 captured["native_process_may_still_be_running"] is False and
                 type(captured["checked_children"]) is int and captured["checked_children"]==60 and
                 type(captured["checked_solver_outputs"]) is int and captured["checked_solver_outputs"]==180,
                 "incomplete native matrix")
    work.require(len(values)==len(captured["captures"])==60,"incomplete strict values")
    actual=[tuple(spec[k] for k in ("variant","case_id","graph_seed","kkt_seed")) for spec,value in values]
    work.require(actual==identities(),"wrong complete native schedule")
    groups=[]
    for item,(spec,value) in zip(captured["captures"],values):
        group=item["process_group"]
        work.require(type(group) is int and group>0 and group not in groups,"invalid/reused native group")
        work.require(type(item["exit_status"]) is int and item["exit_status"]==0 and
                     item["spec"]==spec and item["group_exit_verification"]["validation"]=="pass" and
                     item["group_exit_verification"]["members"]==[],"native exit/group proof missing")
        groups.append(group)
    work.require(sum(len(value["algorithms"]) for _,value in values)==180 and
                 sum(len(value["rounds"]) for _,value in values)==120,"wrong solver/replay count")
    recheck(hashes)
    return dict(checked_children=60,checked_solver_outputs=180,checked_replay_chains=120,
                native_process_groups=groups,detached_native_groups_verified_empty=True,
                capture=str(capture),capture_sha256=work.native.sha(capture))


def bounded_completion(capture,freeze_sha,hashes,deadline_ns):
    remaining=(deadline_ns-time.monotonic_ns())/1e9
    work.require(remaining>0,"no time left for strict completion proof")
    work.require(signal.getitimer(signal.ITIMER_REAL)==(0.0,0.0),"existing process timer must not be replaced")
    previous=signal.getsignal(signal.SIGALRM)
    def expired(signum,frame):raise TimeoutError("whole-interval completion proof deadline")
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,remaining)
    try:return check_completion(capture,freeze_sha,hashes)
    finally:signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous)


def cleanup_outer(process,sampler):
    previous=signal.getsignal(signal.SIGTERM)
    try:
        signal.signal(signal.SIGTERM,signal.SIG_IGN)
        try:return work.monitor.bounded_terminate(process,sampler,term_seconds=30,kill_seconds=5)
        except BaseException as error:
            return dict(native_exit_known=False,group_exit_known=False,native_process_may_still_be_running=True,error=repr(error))
    finally:signal.signal(signal.SIGTERM,previous)


def run(args):
    work.require(args.released,"explicit separate root diagnostic release required")
    work.digest_text(args.freeze_sha256)
    work.require(re.fullmatch(r"attempt[0-9]{2}",args.attempt) is not None,"invalid attempt identity")
    freeze=HERE/"freeze.json";capture=HERE/("capture-"+args.attempt+".json")
    folder=capture.with_name(capture.stem+"_cases");prefix=HERE/("capture-controller-"+args.attempt)
    paths={name:Path(str(prefix)+"."+suffix) for name,suffix in
           (("invocation","invocation.json"),("receipt","json"),("stdout","stdout"),("stderr","stderr"))}
    work.require(not capture.exists() and not folder.exists() and not any(p.exists() for p in paths.values()),"refusing existing evidence")
    work.analysis.hash_check(freeze,args.freeze_sha256);frozen=work.check_freeze(freeze)
    work.require([(s["variant"],s["case_id"],s["graph_seed"],s["kkt_seed"]) for s in frozen["schedule"]]==identities(),"wrong frozen schedule")
    hashes={str(path):work.native.sha(path) for path in (Path(__file__).resolve(),HERE/"collect.py",freeze)}
    command=["/usr/bin/arch","-arm64","/usr/bin/python3","-B","-u",str(HERE/"collect.py"),
             "capture","--freeze",str(freeze),"--output",str(capture),"--released"]
    started=time.monotonic_ns();deadline=started+BUDGET_SECONDS*10**9
    info=dict(schema="lower_density_work_controller_v1",validation="running",command=command,
        working_directory=str(work.ROOT),started_utc=work.native.now(),started_monotonic_ns=started,
        source_sha256=hashes,deadline_seconds=BUDGET_SECONDS,per_child_native_exit_deadline_seconds=1800,
        native_solver_execution_authorized=True,native_solver_execution=True,performance_execution=False,
        all_owned_groups_verified_empty=False,detached_native_process_may_still_be_running=False)
    work.write_json(paths["invocation"],info,exclusive=True)
    process=sampler=None;previous=signal.getsignal(signal.SIGTERM)
    def interrupted(signum,frame):raise KeyboardInterrupt("work outer received SIGTERM")
    signal.signal(signal.SIGTERM,interrupted)
    try:
        sampler=work.monitor.BoundedSampler(work.monitor.LibprocProvider())
        work.require(not sampler.poisoned,"poisoned outer sampler")
        with paths["stdout"].open("x") as stdout,paths["stderr"].open("x") as stderr:
            # Popen or the following metadata read may be interrupted after a
            # child has spawned. Conservatively mark detached state unknown
            # before either operation; only complete strict proof clears it.
            info["detached_native_process_may_still_be_running"]=True
            process=subprocess.Popen(command,cwd=work.ROOT,stdout=stdout,stderr=stderr,start_new_session=True)
            info.update(outer_process_group=process.pid)
            # Native children have their own sessions and existing RSS/deadline
            # guards. This outer watcher bounds the collector, not their RSS.
            while process.poll() is None:
                remaining=(deadline-time.monotonic_ns())/1e9
                work.require(remaining>0,"outer diagnostic deadline exceeded")
                try:process.wait(timeout=min(30,remaining))
                except subprocess.TimeoutExpired:pass
            info["wrapper_exit_observed_monotonic_ns"]=time.monotonic_ns()
            work.require(info["wrapper_exit_observed_monotonic_ns"]<=deadline,"observed outer exit exceeded deadline")
            work.require(type(process.returncode) is int and process.returncode==0,"collector actual exit failed")
        info["validation"]="command_completed"
    except BaseException as error:info.update(validation="failed",error=repr(error))
    finally:
        try:
            cleanup=cleanup_outer(process,sampler);info["outer_cleanup"]=cleanup
            info["exit_status"]=process.poll() if process is not None else None
            work.require(cleanup.get("native_exit_known") is True and cleanup.get("group_exit_known") is True and
                         cleanup.get("native_process_may_still_be_running") is False,"outer group exit unknown")
            if info["validation"]=="command_completed":
                proof=bounded_completion(capture,args.freeze_sha256,hashes,deadline)
                info.update(proof,validation="pass",all_owned_groups_verified_empty=True,
                            detached_native_process_may_still_be_running=False)
        except BaseException as error:info.update(validation="failed",cleanup_or_proof_error=repr(error))
        finally:
            # Ignore repeated termination only during this final bounded receipt
            # write. Unknown detached exits remain unknown on every failure.
            signal.signal(signal.SIGTERM,signal.SIG_IGN)
            try:
                info["outer_monitor_events"]=sampler.events if sampler is not None else {}
                for name in ("stdout","stderr"):
                    info[name]=str(paths[name])
                    if paths[name].exists():info[name+"_sha256"]=work.native.sha(paths[name])
                info.update(finished_utc=work.native.now(),finished_monotonic_ns=time.monotonic_ns())
                info["elapsed_seconds"]=(info["finished_monotonic_ns"]-started)/1e9
                info["complete_interval_deadline_exceeded"]=info["finished_monotonic_ns"]>deadline
                if info["complete_interval_deadline_exceeded"]:
                    info.update(validation="failed",error="complete diagnostic interval exceeded deadline")
                work.write_json(paths["receipt"],info,exclusive=True)
            finally:signal.signal(signal.SIGTERM,previous)
    return info


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--released",action="store_true");parser.add_argument("--freeze-sha256",required=True)
    parser.add_argument("--attempt",default="attempt01")
    info=run(parser.parse_args())
    print(json.dumps({k:info.get(k) for k in ("validation","exit_status","checked_children","all_owned_groups_verified_empty",
                                            "error","cleanup_or_proof_error")},indent=2))
    raise SystemExit(0 if info["validation"]=="pass" else 1)


if __name__=="__main__":main()
