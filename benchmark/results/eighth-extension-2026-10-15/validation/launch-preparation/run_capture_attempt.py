#!/usr/bin/env python3
"""Archive the separately released frozen 28-child eighth extension.

Source preparation only until root schedules release. This outer controller
has one 51,000-second deadline; it does not add a per-child deadline to the
unchanged frozen performance collector.
"""
import json
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path('/Users/random_person/Desktop/kkt-eighth-sampling')
STUDY = ROOT/'benchmark/results/eighth-extension-2026-10-15'
sys.path.insert(0, str(ROOT/'benchmark'))
import run_eighth_extension as experiment

FREEZE_SHA = 'aa2f9ae7385105eb7185b864a1f46387f8a02ebe8b967f041d3d0cef5ffa7bc5'
BUDGET_SECONDS = 28*1800+600


def main():
    require = experiment.require
    require(sys.argv[1:] == ['--released'], 'explicit root quiet performance release required')
    require(Path.cwd().resolve() == ROOT, 'run from the fixed eighth worktree')
    freeze = STUDY/'freeze.json'; capture = STUDY/'extension.json'
    output = STUDY/'extension.csv'; folder = STUDY/'extension_cases'
    prefix = STUDY/'controller-attempt01'
    paths = {name:Path(str(prefix)+'.'+suffix) for name,suffix in
             (('invocation','invocation.json'),('receipt','json'),('stdout','stdout'),('stderr','stderr'))}
    require(not any(p.exists() for p in (capture,output,folder,*paths.values())), 'refusing existing evidence')
    experiment.analysis.hash_check(freeze, FREEZE_SHA)
    frozen,cases = experiment.check_freeze(freeze)
    require(len(cases) == 14 and len(frozen['schedule']) == 28, 'wrong extension matrix')
    before = STUDY/'machine-before.json'
    metadata = experiment.analysis.read_json(before)
    require(metadata['validation'] == 'pass' and metadata['phase'] == 'before'
            and metadata['sleep_inhibition_verified'] is False, 'missing successful machine preflight')
    hashes = {str(p):experiment.native.sha(p) for p in
              (Path(__file__).resolve(),ROOT/'benchmark/run_eighth_extension.py',freeze,before)}
    command = ['/usr/bin/python3','-B','-u',str(ROOT/'benchmark/run_eighth_extension.py'),
               'capture','--freeze',str(freeze),'--output',str(output),'--released']
    started = time.monotonic_ns()
    info = dict(schema='eighth_extension_controller_v1',validation='running',command=command,
        working_directory=str(ROOT),started_utc=experiment.native.now(),started_monotonic_ns=started,
        source_sha256=hashes,deadline_seconds=BUDGET_SECONDS,
        deadline_scope='overall collector only; no per-child wall deadline is asserted',
        native_solver_execution_authorized=True,native_solver_execution=True,performance_execution=True,
        sleep_inhibition_verified=False,all_owned_groups_verified_empty=False)
    experiment.write_json(paths['invocation'],info,exclusive=True)
    process = None; sampler = None; old = signal.getsignal(signal.SIGTERM)
    def interrupted(signum,frame): raise KeyboardInterrupt('extension controller received SIGTERM')
    signal.signal(signal.SIGTERM,interrupted)
    try:
        sampler = experiment.monitor.BoundedSampler(experiment.monitor.LibprocProvider())
        require(not sampler.poisoned,'poisoned outer sampler')
        with paths['stdout'].open('x') as stdout,paths['stderr'].open('x') as stderr:
            process = subprocess.Popen(command,cwd=ROOT,stdout=stdout,stderr=stderr,start_new_session=True)
            info['outer_process_group'] = process.pid
            # Native children have separate owned sessions and unchanged inner
            # RSS/cleanup guards. Only the Python collector is in this group.
            while process.poll() is None:
                remaining = BUDGET_SECONDS-(time.monotonic_ns()-started)/1e9
                require(remaining > 0,'overall extension deadline exceeded')
                try: process.wait(timeout=min(30,remaining))
                except subprocess.TimeoutExpired: pass
            info['wrapper_exit_observed_monotonic_ns'] = time.monotonic_ns()
            require(info['wrapper_exit_observed_monotonic_ns']-started <= BUDGET_SECONDS*10**9,
                    'observed collector exit exceeded deadline')
            require(type(process.returncode) is int and process.returncode == 0,'collector failed')
        info['validation'] = 'command_completed'
    except BaseException as error:
        info.update(validation='failed',error=repr(error))
    finally:
        try:
            # Inner cleanup is bounded; allow 30 seconds before outer SIGKILL.
            # Repeated SIGTERM must not interrupt this cleanup proof.
            signal.signal(signal.SIGTERM,signal.SIG_IGN)
            try: cleanup = experiment.monitor.bounded_terminate(process,sampler,term_seconds=30,kill_seconds=5)
            except BaseException as error:
                cleanup = dict(native_exit_known=False,group_exit_known=False,
                               native_process_may_still_be_running=True,error=repr(error))
            info['outer_cleanup'] = cleanup
            info['exit_status'] = process.poll() if process is not None else None
            require(cleanup.get('native_exit_known') is True and cleanup.get('group_exit_known') is True
                    and cleanup.get('native_process_may_still_be_running') is False,'outer group exit unknown')
            if info['validation'] == 'command_completed':
                captured,cases,rows,diagnostics,resources,inputs = experiment.load(capture)
                require(len(captured['captures']) == 28 and len(rows) == 1176
                        and sum(row['phase']=='timed' for row in rows) == 1008
                        and sum(row['phase']=='warmup' for row in rows) == 168,'incomplete extension')
                for path,digest in hashes.items(): experiment.analysis.hash_check(Path(path),digest)
                for path,digest in inputs.items(): experiment.analysis.hash_check(Path(path),digest)
                info.update(validation='pass',all_owned_groups_verified_empty=True,
                            checked_children=28,checked_solver_outputs=1176,checked_timed_outputs=1008,
                            checked_warmup_outputs=168,capture=str(capture),
                            capture_sha256=experiment.native.sha(capture))
        except BaseException as error:
            info.update(validation='failed',cleanup_or_proof_error=repr(error))
        finally:
            signal.signal(signal.SIGTERM,old)
            info.update(finished_utc=experiment.native.now(),finished_monotonic_ns=time.monotonic_ns())
            info['elapsed_seconds'] = (info['finished_monotonic_ns']-started)/1e9
            info['outer_monitor_events'] = sampler.events if sampler is not None else {}
            for name in ('stdout','stderr'):
                info[name] = str(paths[name])
                if paths[name].exists(): info[name+'_sha256'] = experiment.native.sha(paths[name])
            experiment.write_json(paths['receipt'],info,exclusive=True)
    print(json.dumps({name:info.get(name) for name in ('validation','exit_status','checked_children',
          'checked_solver_outputs','all_owned_groups_verified_empty','error','cleanup_or_proof_error')},indent=2))
    raise SystemExit(0 if info['validation'] == 'pass' else 1)


if __name__ == '__main__': main()
