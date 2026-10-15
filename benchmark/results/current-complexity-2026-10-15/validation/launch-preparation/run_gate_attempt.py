#!/usr/bin/env python3
"""Archive one released complexity build or real-schema gate, never the study.

Detached SerialGuard children need their own complete receipts. Empty outer
Python process-group evidence alone never proves those children have exited.
"""
import argparse
import json
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT=Path('/Users/random_person/Desktop/kkt-eighth-sampling')
PACKAGE=ROOT/'benchmark/current_complexity'
sys.path.insert(0,str(PACKAGE))
import validate_build as gate

monitor=gate.parent_engine.control.monitor
BUDGETS={'build':2100,'smoke':900}

def save(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')

def source_hashes():
    paths={Path(__file__).resolve(),*(path for path in PACKAGE.iterdir() if path.suffix in ('.py','.cpp','.md'))}
    return {str(path.resolve()):gate.analyzer.digest(path) for path in sorted(paths)}

def command_for(args,inner):
    command=['/usr/bin/arch','-arm64','/usr/bin/python3','-B','-u',str(PACKAGE/'build_library_main.py'),args.phase]
    if args.phase=='build':
        gate.require(args.library_source is not None and args.build_directory is not None and args.build_record is None,'build requires fresh source/build paths only')
        command+=['--parent-freeze',str(ROOT/'benchmark/results/eighth-sampling-2026-10-15/freeze.json'),
                  '--library-source',str(args.library_source.resolve()),'--build-directory',str(args.build_directory.resolve())]
        if args.git_resolve is not None:
            gate.acquisition_command(args.library_source,args.git_resolve)
            command+=['--git-resolve',args.git_resolve]
    else:
        gate.require(args.phase=='smoke' and args.build_record is not None and args.library_source is None and
                     args.build_directory is None and args.git_resolve is None,'smoke requires only the actual build record')
        command+=['--build-record',str(args.build_record.resolve(strict=True))]
    return command+['--output',str(inner),'--released']

def check_inner(args,inner,command):
    path=inner/'attempt.json';initial=gate.analyzer.digest(path);attempt=gate.read(path)
    gate.exact(attempt['schema'],'current_complexity_gate_attempt_v1','wrong producer receipt')
    for key,value in dict(phase=args.phase,validation='pass',performance_capture=False,all_owned_groups_verified_empty=True,
                          native_library_or_solver_execution_authorized=True).items():gate.exact(attempt[key],value,'producer metadata '+key)
    gate.exact(attempt['invocation'],command[5:],'producer invocation differs')
    if args.phase=='build':
        record_path=inner/'build-record.json';record=gate.check_record(record_path)
        expected=[record['acquisition_command'],*record['library_commands'],*record['build_commands']]
        intervals=[record['acquisition_interval'],*record['command_intervals']]
        bound=record['bound_sha256'];groups=6
        gate.exact(attempt['build_record'],str(record_path),'wrong producer build path')
        gate.exact(attempt['build_record_sha256'],gate.analyzer.digest(record_path),'producer build digest differs')
    else:
        record=gate.check_record(args.build_record.resolve(strict=True))
        receipt=inner/'schema-smoke.json';receipt_sha=gate.analyzer.digest(receipt)
        details=gate.check_schema_smoke(receipt,record,gate.analyzer.SCHEMA_CONTRACT)
        expected=[curve['command'] for curve in details['curves']];intervals=details['command_intervals'];groups=2
        bound={**record['bound_sha256'],**gate.read(receipt)['bound_sha256'],str(receipt):receipt_sha}
        gate.exact(attempt['schema_smoke'],str(receipt),'wrong producer smoke path')
        gate.exact(attempt['schema_smoke_sha256'],receipt_sha,'producer smoke digest differs')
    gate.exact(attempt['attempted_commands'],expected,'incomplete actual nested command matrix')
    gate.exact(attempt['command_intervals'],intervals,'producer intervals differ from group proof')
    start,finish=attempt['started_monotonic_ns'],attempt['finished_monotonic_ns']
    gate.require(type(start) is int and type(finish) is int and 0<=start<finish and
                 all(start<=item['started_monotonic_ns']<item['finished_monotonic_ns']<=finish for item in intervals),
                 'nested intervals escape producer lifetime')
    for source,digest in attempt['recipe_sha256'].items():gate.bind(bound,source,digest)
    gate.bind(bound,str(path),initial);gate.analyzer.check_bound(bound)
    return dict(validation='pass',current_phase_groups=groups,bound_sha256=bound,
                native_library_execution=True,native_solver_execution=args.phase=='smoke',
                detached_native_groups_verified_empty=True)

def cleanup_outer(process,sampler):
    previous=signal.getsignal(signal.SIGTERM)
    try:
        signal.signal(signal.SIGTERM,signal.SIG_IGN)
        try:return monitor.bounded_terminate(process,sampler,term_seconds=30,kill_seconds=5)
        except BaseException as error:return dict(native_exit_known=False,group_exit_known=False,
            native_process_may_still_be_running=True,error=repr(error))
    finally:signal.signal(signal.SIGTERM,previous)

def bounded_inner_proof(args,inner,command,deadline):
    remaining=(deadline-time.monotonic_ns())/1e9
    gate.require(remaining>0,'no complete-interval budget remains for inner proof')
    gate.require(signal.getitimer(signal.ITIMER_REAL)==(0.0,0.0),'unexpected existing real-time timer')
    previous=signal.getsignal(signal.SIGALRM)
    def expired(signum,frame):raise TimeoutError('complete-interval deadline during inner proof')
    try:
        signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,remaining)
        return check_inner(args,inner,command)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous)

def run_phase(args):
    gate.require(Path.cwd().resolve()==ROOT and gate.ROOT==ROOT,'run from the frozen eighth worktree')
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False);inner=output/'inner'
    command=command_for(args,inner);before=source_hashes();input_bound={}
    if args.phase=='smoke':
        path=args.build_record.resolve(strict=True);input_bound[str(path)]=gate.analyzer.digest(path)
    started=time.monotonic_ns();deadline=started+BUDGETS[args.phase]*10**9
    info=dict(schema='current_complexity_outer_gate_v1',validation='running',phase=args.phase,command=command,
        working_directory=str(ROOT),package=str(PACKAGE),started_monotonic_ns=started,started_utc=gate.native.now(),
        complete_interval_budget_seconds=BUDGETS[args.phase],deadline_scope='launch through cleanup and full inner proof',
        cleanup_term_seconds=30,cleanup_kill_seconds=5,source_sha256=before,input_sha256=input_bound,
        performance_execution_authorized=False,native_library_execution_authorized=True,
        native_solver_execution_authorized=args.phase=='smoke',native_library_execution=None,native_solver_execution=None,
        outer_observations=[],outer_group_verified_empty=False,detached_native_groups_verified_empty=False,
        detached_native_process_may_still_be_running=False,all_owned_groups_verified_empty=False)
    save(output/'invocation.json',info);process=None;sampler=None;previous=signal.getsignal(signal.SIGTERM)
    def interrupted(signum,frame):raise KeyboardInterrupt('complexity outer gate received SIGTERM')
    signal.signal(signal.SIGTERM,interrupted)
    try:
        sampler=monitor.BoundedSampler(monitor.LibprocProvider());gate.require(not sampler.poisoned,'poisoned outer sampler')
        with (output/'stdout').open('x') as stdout,(output/'stderr').open('x') as stderr:
            # Mark uncertainty before Popen: a signal immediately after a
            # successful spawn must not leave a false no-native-process flag.
            info['detached_native_process_may_still_be_running']=True
            process=subprocess.Popen(command,cwd=ROOT,stdout=stdout,stderr=stderr,start_new_session=True)
            info.update(outer_process_group=process.pid,detached_native_process_may_still_be_running=True)
            unavailable=0
            while process.poll() is None:
                remaining=(deadline-time.monotonic_ns())/1e9;gate.require(remaining>0,'outer phase deadline exceeded')
                try:process.wait(timeout=min(2,remaining))
                except subprocess.TimeoutExpired:pass
                observation=sampler.sample(process.pid);info['outer_observations'].append(observation)
                unavailable=unavailable+1 if observation['validation']!='pass' else 0
                gate.require(not sampler.poisoned and unavailable<3,'outer resource observations unavailable')
                gate.require(observation['validation']!='pass' or observation['rss_kib']<=40*1024*1024,'outer group exceeded 40GiB')
            info['wrapper_exit_observed_monotonic_ns']=time.monotonic_ns()
            gate.require(info['wrapper_exit_observed_monotonic_ns']<=deadline,'outer exit observed beyond phase deadline')
            gate.require(type(process.returncode) is int and process.returncode==0,'producer exited unsuccessfully')
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
                info['inner_proof']=bounded_inner_proof(args,inner,command,deadline)
                gate.exact(source_hashes(),before,'source changed during outer gate')
                gate.analyzer.check_bound(input_bound)
                info.update(validation='pass',detached_native_groups_verified_empty=True,
                            detached_native_process_may_still_be_running=False,all_owned_groups_verified_empty=True,
                            native_library_execution=True,native_solver_execution=args.phase=='smoke')
        except BaseException as error:info.update(validation='failed',cleanup_or_proof_error=repr(error))
        finally:
            signal.signal(signal.SIGTERM,previous)
            info['outer_monitor_events']=sampler.events if sampler is not None else {}
            for name in ('stdout','stderr'):
                path=output/name;info[name]=str(path)
                if path.exists():info[name+'_sha256']=gate.analyzer.digest(path)
            info.update(finished_monotonic_ns=time.monotonic_ns(),finished_utc=gate.native.now())
            info['elapsed_seconds']=(info['finished_monotonic_ns']-started)/1e9
            if info['finished_monotonic_ns']>deadline:
                info.update(validation='failed',complete_interval_deadline_exceeded=True)
            # A failed/aborted producer is never treated as a complete native
            # proof merely because the outer Python session is now empty.
            save(output/'receipt.json',info)
    return info

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=tuple(BUDGETS),required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--library-source',type=Path);parser.add_argument('--build-directory',type=Path)
    parser.add_argument('--build-record',type=Path);parser.add_argument('--git-resolve')
    parser.add_argument('--released',action='store_true');args=parser.parse_args()
    gate.require(args.released,'explicit root nonperformance build/schema release required')
    result=run_phase(args);print(json.dumps({key:result.get(key) for key in ('validation','phase','exit_status','elapsed_seconds',
        'outer_group_verified_empty','detached_native_groups_verified_empty','all_owned_groups_verified_empty','error','cleanup_or_proof_error')}))
    raise SystemExit(0 if result['validation']=='pass' else 1)

if __name__=='__main__':main()
