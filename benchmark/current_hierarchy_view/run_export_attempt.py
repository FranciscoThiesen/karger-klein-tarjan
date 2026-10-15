#!/usr/bin/env python3
"""Archive one released untimed viewer build/export, including detached proof."""
import argparse
import json
from pathlib import Path
import signal
import subprocess
import sys
import time

import build_native_view as gate

ROOT=gate.ROOT
PACKAGE=ROOT/'benchmark/current_hierarchy_view'
monitor=gate.parent_engine.control.monitor
BUDGET_SECONDS=1200

def save(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')

def sources():
    return {str(path.resolve()):gate.sha(path) for path in PACKAGE.iterdir() if path.suffix in ('.py','.cpp','.html','.md')}

def command_for(inner):
    return ['/usr/bin/arch','-arm64','/usr/bin/python3','-B','-u',str(PACKAGE/'build_native_view.py'),
            '--output',str(inner),'--released']

def check_inner(inner,command):
    path=inner/'attempt.json';initial=gate.sha(path);attempt=gate.read(path)
    for key,value in dict(schema='current_hierarchy_export_attempt_v1',validation='pass',
                          native_execution_authorized=True,performance_execution=False,
                          owned_groups_verified_empty=True,native_process_may_still_be_running=False).items():
        gate.exact(attempt[key],value,'inner attempt '+key)
    gate.exact(attempt['invocation'],command[5:],'inner invocation differs')
    receipt=inner/'build-record.json';record=gate.check_record(receipt)
    gate.exact(attempt['build_record'],str(receipt),'wrong inner build record')
    gate.exact(attempt['build_record_sha256'],gate.sha(receipt),'inner record changed')
    gate.exact(attempt['command_intervals'],record['command_intervals'],'inner command intervals differ')
    gate.exact(attempt['source_sha256'],record['source_sha256'],'inner source inventory differs')
    gate.exact(attempt['environment_policy'],record['environment_policy'],'inner environment differs')
    start,finish=attempt['started_monotonic_ns'],attempt['finished_monotonic_ns']
    gate.require(type(start) is int and type(finish) is int and 0<=start<finish and
                 all(start<=item['started_monotonic_ns']<item['finished_monotonic_ns']<=finish
                     for item in record['command_intervals']),'native intervals outside producer lifetime')
    bound={**record['bound_sha256'],str(path):initial};gate.check_bound(bound)
    return dict(validation='pass',native_command_groups=3,native_execution=True,performance_execution=False,
                detached_native_groups_verified_empty=True,bound_sha256=bound)

def cleanup_outer(process,sampler):
    previous=signal.getsignal(signal.SIGTERM)
    try:
        signal.signal(signal.SIGTERM,signal.SIG_IGN)
        try:return monitor.bounded_terminate(process,sampler,term_seconds=30,kill_seconds=5)
        except BaseException as error:return dict(native_exit_known=False,group_exit_known=False,
            native_process_may_still_be_running=True,error=repr(error))
    finally:signal.signal(signal.SIGTERM,previous)

def bounded_proof(inner,command,deadline):
    remaining=(deadline-time.monotonic_ns())/1e9;gate.require(remaining>0,'no full-proof budget remains')
    gate.require(signal.getitimer(signal.ITIMER_REAL)==(0.0,0.0),'unexpected existing timer')
    previous=signal.getsignal(signal.SIGALRM)
    def expired(signum,frame):raise TimeoutError('complete export interval exceeded during proof')
    try:
        signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,remaining)
        return check_inner(inner,command)
    finally:signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous)

def run(args):
    gate.require(Path.cwd().resolve()==ROOT and gate.HERE==PACKAGE,'run the installed package from the frozen eighth worktree')
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False);inner=output/'inner'
    command=command_for(inner);before=sources();started=time.monotonic_ns();deadline=started+BUDGET_SECONDS*10**9
    info=dict(schema='current_hierarchy_export_outer_v1',validation='running',command=command,working_directory=str(ROOT),
        package=str(PACKAGE),source_sha256=before,started_monotonic_ns=started,complete_interval_budget_seconds=BUDGET_SECONDS,
        deadline_scope='launch through cleanup, full inner proof and final artifact hashing; receipt serialization excluded',
        native_execution_authorized=True,native_execution=None,performance_execution=False,outer_observations=[],
        outer_group_verified_empty=False,detached_native_groups_verified_empty=False,
        detached_native_process_may_still_be_running=False,all_owned_groups_verified_empty=False)
    save(output/'invocation.json',info);process=None;sampler=None;previous=signal.getsignal(signal.SIGTERM)
    def interrupted(signum,frame):raise KeyboardInterrupt('viewer outer received SIGTERM')
    signal.signal(signal.SIGTERM,interrupted)
    try:
        sampler=monitor.BoundedSampler(monitor.LibprocProvider());gate.require(not sampler.poisoned,'poisoned outer sampler')
        with (output/'stdout').open('x') as stdout,(output/'stderr').open('x') as stderr:
            info['detached_native_process_may_still_be_running']=True
            process=subprocess.Popen(command,cwd=ROOT,stdout=stdout,stderr=stderr,start_new_session=True)
            info['outer_process_group']=process.pid;unavailable=0
            while process.poll() is None:
                remaining=(deadline-time.monotonic_ns())/1e9;gate.require(remaining>0,'outer export deadline')
                try:process.wait(timeout=min(2,remaining))
                except subprocess.TimeoutExpired:pass
                observation=sampler.sample(process.pid);info['outer_observations'].append(observation)
                unavailable=unavailable+1 if observation['validation']!='pass' else 0
                gate.require(not sampler.poisoned and unavailable<3,'outer resource observation unavailable')
                gate.require(observation['validation']!='pass' or observation['rss_kib']<=40*1024*1024,'outer sampled RSS over 40GiB')
            info['exit_observed_monotonic_ns']=time.monotonic_ns()
            gate.require(info['exit_observed_monotonic_ns']<=deadline,'outer exit observed past deadline')
            gate.exact(process.returncode,0,'export producer exited unsuccessfully')
        info['validation']='command_completed'
    except BaseException as error:info.update(validation='failed',error=repr(error))
    finally:
        try:
            cleanup=cleanup_outer(process,sampler);info['outer_cleanup']=cleanup
            info['exit_status']=process.poll() if process is not None else None
            gate.require(cleanup.get('native_exit_known') is True and cleanup.get('group_exit_known') is True and
                         cleanup.get('native_process_may_still_be_running') is False,'outer group exit unknown')
            info['outer_group_verified_empty']=True
            if info['validation']=='command_completed':
                info['inner_proof']=bounded_proof(inner,command,deadline)
                gate.exact(sources(),before,'source changed during export attempt')
                info.update(validation='pass',detached_native_groups_verified_empty=True,
                    detached_native_process_may_still_be_running=False,all_owned_groups_verified_empty=True,native_execution=True)
        except BaseException as error:info.update(validation='failed',cleanup_or_proof_error=repr(error))
        finally:
            signal.signal(signal.SIGTERM,previous);info['outer_monitor_events']=sampler.events if sampler is not None else {}
            for name in ('stdout','stderr'):
                path=output/name;info[name]=str(path)
                if path.exists():info[name+'_sha256']=gate.sha(path)
            info['finished_monotonic_ns']=time.monotonic_ns();info['elapsed_seconds']=(info['finished_monotonic_ns']-started)/1e9
            if info['finished_monotonic_ns']>deadline:info.update(validation='failed',complete_interval_deadline_exceeded=True)
            save(output/'receipt.json',info)
    return info

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--released',action='store_true');args=parser.parse_args()
    gate.require(args.released,'explicit root untimed export release required');result=run(args)
    print(json.dumps({key:result.get(key) for key in ('validation','exit_status','elapsed_seconds',
        'outer_group_verified_empty','detached_native_groups_verified_empty','all_owned_groups_verified_empty','error','cleanup_or_proof_error')}))
    raise SystemExit(0 if result['validation']=='pass' else 1)

if __name__=='__main__':main()
