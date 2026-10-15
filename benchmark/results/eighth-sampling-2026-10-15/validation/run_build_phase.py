#!/usr/bin/env python3
"""Bound and archive one eighth-study validation/build phase after release.

Native correctness really executes solvers. Each phase is a fixed command;
performance and work drivers cannot be selected. Inner SerialGuard sessions
are distinct from the outer Python group and need their own exit receipts.
"""
import argparse
from collections import Counter
import datetime
import json
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'benchmark'))
import build_eighth_sampling as builder

monitor = builder.inherited.monitor
OUTPUT = ROOT/'benchmark/results/eighth-sampling-2026-10-15/validation'
BUDGETS = {'controller-mocks':180,'build-mocks':180,'collector-mocks':180,'native-correctness':180,
           'sanitizer-correctness':300,'timing-build':120,'final-objects':120}
require = builder.require


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def command_for(phase):
    prefix = [sys.executable,'-B']
    if phase in ('controller-mocks','build-mocks','collector-mocks'):
        test = {'controller-mocks':'test_eighth_controller.py','build-mocks':'test_eighth_build.py',
                'collector-mocks':'test_eighth_sampling.py'}[phase]
        return prefix+['-m','unittest','discover','-s','benchmark','-p',test,'-v']
    if phase == 'final-objects':
        return prefix+[str(OUTPUT/'validate_final_objects.py'),'--output',str(OUTPUT)]
    require(phase in ('native-correctness','sanitizer-correctness','timing-build'),'unknown build phase')
    return prefix+[str(ROOT/'benchmark/build_eighth_sampling.py'),'--profile',phase,
                   '--output',str(OUTPUT),'--parent-freeze',str(builder.PARENT_PATH)]


def source_hashes():
    paths = {Path(__file__).resolve(), OUTPUT/'validate_final_objects.py',
             ROOT/'benchmark/run_eighth_sampling.py',
             ROOT/'benchmark/test_eighth_build.py',ROOT/'benchmark/test_eighth_sampling.py',
             ROOT/'benchmark/test_eighth_controller.py'}
    paths.update(ROOT/name for name in builder.inventory())
    paths.update(ROOT/name for name in builder.RECIPES)
    paths.update(Path(name) for name in builder.parent_engine.helpers())
    return {str(path.resolve(strict=True)):builder.sha(path) for path in sorted(paths)}


def check_inner(phase):
    """Bind every actual guard command/outcome to completed inner receipts."""
    if phase in ('controller-mocks','build-mocks','collector-mocks'):
        return {'validation':'pass','groups':0,'native_test_executions':0,'receipt_sha256':{},
                'scope':'Mock-only command; outer process group is checked separately.'}
    paths = []
    if phase == 'final-objects':
        proof_path = OUTPUT/'final-object-tests.json'; paths.append(proof_path)
        proof = builder.parent_engine.analysis.read_json(proof_path)
        require(proof['status'] == 'pass' and len(proof['tests']) == 4 and
                len(proof['wrong_policy_gates']) == len(proof['rebuilds']) == 2,
                'incomplete final-object result')
        commands = proof['build_commands']; expected_compiles = 9
        tests,negatives = proof['tests'],proof['wrong_policy_gates']
        group_path = OUTPUT/'final-object-owned-groups.json'
    else:
        paths += [OUTPUT/f'{phase}-{variant}-build-record.json' for variant in builder.VARIANTS]
        records = [builder.parent_engine.analysis.read_json(path) for path in paths]
        require(all(type(r['build_exit_status']) is int and r['build_exit_status'] == 0 for r in records),
                'inner build did not finish successfully')
        require(records[0]['build_commands'] == records[1]['build_commands'],'inner build command records differ')
        commands = records[0]['build_commands']; expected_compiles = {
            'native-correctness':43,'sanitizer-correctness':40,'timing-build':12}[phase]
        tests,negatives = [],[]
        if phase != 'timing-build':
            proof_path = OUTPUT/f'{phase}-tests.json'; paths.append(proof_path)
            proof = builder.parent_engine.analysis.read_json(proof_path)
            require(proof['status'] == 'pass' and len(proof['tests']) == 20 and len(proof['wrong_policy_gates']) == 4,
                    'incomplete inner correctness result')
            tests,negatives = proof['tests'],proof['wrong_policy_gates']
        group_path = OUTPUT/f'{phase}-owned-groups.json'
    require(len(commands) == expected_compiles,'unexpected inner compile/link count')
    require(all(type(t['exit_status']) is int and t['exit_status'] == 0 for t in tests) and
            all(type(t['exit_status']) is int and t['exit_status'] == 1 for t in negatives),
            'incorrect positive/negative inner outcome')
    wanted = Counter((tuple(command),0) for command in commands)
    wanted.update((tuple(t['command']),t['exit_status']) for t in [*tests,*negatives])
    paths.append(group_path)
    groups = builder.parent_engine.analysis.read_json(group_path)['groups']
    require(len(groups) == sum(wanted.values()),'missing or extra nested owned group')
    observed = Counter()
    for group in groups:
        pid = group['process_group']; cleanup = group['cleanup']; verification = cleanup.get('group_verification',{})
        require(type(pid) is int and pid > 0 and type(group['exit_status']) is int,
                'unknown nested child identity/exit')
        require(cleanup.get('native_exit_known') is True and cleanup.get('group_exit_known') is True and
                cleanup.get('native_process_may_still_be_running') is False and
                cleanup.get('process_group') == pid and type(cleanup.get('returncode')) is int and
                cleanup['returncode'] == group['exit_status'] and verification.get('validation') == 'pass' and
                verification.get('process_group') == pid and verification.get('members') == [],
                'nested owned-group exit not proved')
        observed[tuple(group['command']),group['exit_status']] += 1
    require(observed == wanted,'nested commands/outcomes do not match complete build/test receipts')
    return {'validation':'pass','groups':len(groups),'native_test_executions':len(tests)+len(negatives),
            'receipt_sha256':{str(path):builder.sha(path) for path in paths}}


def cleanup_outer(process,sampler):
    # Inner SerialGuard may need 10s TERM +5s KILL +5s bounded observation.
    # Give it 30s to handle our TERM and save its own-session cleanup receipt.
    previous = signal.getsignal(signal.SIGTERM)
    try:
        signal.signal(signal.SIGTERM,signal.SIG_IGN)
        try:
            return monitor.bounded_terminate(process,sampler,term_seconds=30,kill_seconds=5)
        except BaseException as error:
            return {'native_exit_known':False,'group_exit_known':False,
                    'native_process_may_still_be_running':True,'error':repr(error)}
    finally:
        signal.signal(signal.SIGTERM,previous)


def run_phase(phase,prefix):
    require(phase in BUDGETS,'unknown phase')
    prefix = Path(prefix).resolve(); require(prefix.parent == OUTPUT.resolve(),'attempt must be in this study validation directory')
    OUTPUT.mkdir(parents=True,exist_ok=True)
    paths = {name:Path(str(prefix)+'.'+suffix) for name,suffix in
             (('invocation','invocation.json'),('receipt','json'),('stdout','stdout'),('stderr','stderr'))}
    require(not any(path.exists() for path in paths.values()),'refusing existing attempt artifacts')
    before = source_hashes(); command = command_for(phase); started = time.monotonic_ns()
    info = {'schema':'eighth_build_controller_v1','validation':'running','phase':phase,'command':command,
            'working_directory':str(ROOT),'started_utc':now(),'started_monotonic_ns':started,
            'command_deadline_seconds':BUDGETS[phase],'cleanup_term_seconds':30,'cleanup_kill_seconds':5,
            'source_sha256_before':before,'outer_observations':[],
            'native_solver_execution_authorized':phase in ('native-correctness','sanitizer-correctness','final-objects'),
            'performance_execution_authorized':False,'work_driver_execution_authorized':False,
            'all_owned_groups_verified_empty':False,'native_solver_execution':None}
    builder.save(paths['invocation'],info,exclusive=True)
    process = None; sampler = None
    previous = signal.getsignal(signal.SIGTERM)
    def interrupted(signum,frame):
        raise KeyboardInterrupt('outer phase received SIGTERM')
    signal.signal(signal.SIGTERM,interrupted)
    try:
        sampler = monitor.BoundedSampler(monitor.LibprocProvider())
        require(not sampler.poisoned,'poisoned outer sampler')
        with paths['stdout'].open('x') as stdout,paths['stderr'].open('x') as stderr:
            process = subprocess.Popen(command,cwd=ROOT,stdout=stdout,stderr=stderr,start_new_session=True)
            info['outer_process_group'] = process.pid; unavailable = 0
            deadline = started/1e9+BUDGETS[phase]
            while process.poll() is None:
                remaining = deadline-time.monotonic(); require(remaining > 0,'outer phase deadline exceeded')
                try: process.wait(timeout=min(2,remaining))
                except subprocess.TimeoutExpired: pass
                sample = sampler.sample(process.pid); info['outer_observations'].append(sample)
                unavailable = unavailable+1 if sample['validation'] != 'pass' else 0
                require(not sampler.poisoned and unavailable < 3,'outer RSS observations unavailable')
                require(sample['validation'] != 'pass' or sample['rss_kib'] <= 40*1024*1024,'outer group exceeded40GiB')
                require(time.monotonic() <= deadline,'outer phase completion exceeded deadline')
            info['outer_wrapper_exit_observed_monotonic_ns'] = time.monotonic_ns()
            require(info['outer_wrapper_exit_observed_monotonic_ns'] <= started+BUDGETS[phase]*1_000_000_000,
                    'outer wrapper exit observed beyond phase deadline')
            info['exit_status'] = process.returncode
            require(type(process.returncode) is int and process.returncode == 0,'outer command exited unsuccessfully')
        info['validation'] = 'command_completed'
    except BaseException as error:
        info.update(validation='failed',error=repr(error))
    finally:
        try:
            info['outer_cleanup'] = cleanup_outer(process,sampler)
            info['exit_status'] = process.poll() if process is not None else None
            outer = info['outer_cleanup']
            require(outer.get('native_exit_known') is True and outer.get('group_exit_known') is True and
                    outer.get('native_process_may_still_be_running') is False,'outer group exit unknown')
            if info['validation'] == 'command_completed':
                info['inner_proof'] = check_inner(phase)
                info['source_sha256_after'] = source_hashes()
                require(before == info['source_sha256_after'],'phase source changed')
                info['all_owned_groups_verified_empty'] = True
                info['native_solver_execution'] = info['native_solver_execution_authorized']
                info['validation'] = 'pass'
        except BaseException as error:
            info.update(validation='failed',cleanup_or_proof_error=repr(error))
        finally:
            signal.signal(signal.SIGTERM,previous)
            info.update(finished_utc=now(),finished_monotonic_ns=time.monotonic_ns())
            info['elapsed_seconds'] = (info['finished_monotonic_ns']-started)/1e9
            info['outer_monitor_events'] = sampler.events if sampler is not None else {}
            for name in ('stdout','stderr'):
                info[name] = str(paths[name])
                if paths[name].exists(): info[name+'_sha256'] = builder.sha(paths[name])
            # Abnormal outer completion deliberately does not infer that every
            # detached inner session is gone, even if the outer group is empty.
            builder.save(paths['receipt'],info,exclusive=True)
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=tuple(BUDGETS),required=True)
    parser.add_argument('--prefix',type=Path,required=True)
    parser.add_argument('--released',action='store_true')
    args = parser.parse_args(); require(args.released,'root nonperformance release required')
    result = run_phase(args.phase,args.prefix)
    print(json.dumps({name:result.get(name) for name in
        ('validation','phase','exit_status','elapsed_seconds','all_owned_groups_verified_empty',
         'native_solver_execution','error','cleanup_or_proof_error')},indent=2))
    raise SystemExit(0 if result['validation'] == 'pass' else 1)


if __name__ == '__main__': main()
