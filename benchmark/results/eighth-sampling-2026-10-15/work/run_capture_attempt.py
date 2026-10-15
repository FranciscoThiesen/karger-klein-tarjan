#!/usr/bin/env python3
"""Archive the separately released 48-child eighth-sampling work capture.

Install beside the eighth study's collect.py before use. This is an untimed
native diagnostic controller; its elapsed time is not an algorithm benchmark.
"""
import importlib.util
import json
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('eighth_work_capture_controller',HERE/'collect.py')
work = importlib.util.module_from_spec(spec); spec.loader.exec_module(work)


def main():
    work.require(sys.argv[1:] == ['--released'],'explicit root diagnostic release required')
    freeze = HERE/'freeze.json'; capture = HERE/'capture-attempt01.json'
    prefix = HERE/'capture-controller-attempt01'
    paths = {name:Path(str(prefix)+'.'+suffix) for name,suffix in
             (('invocation','invocation.json'),('receipt','json'),('stdout','stdout'),('stderr','stderr'))}
    work.require(not capture.exists() and not any(p.exists() for p in paths.values()),'refusing existing evidence')
    work.check_freeze(freeze)
    hashes = {str(path):work.native.sha(path) for path in (Path(__file__).resolve(),HERE/'collect.py',freeze)}
    command = [sys.executable,'-B',str(HERE/'collect.py'),'capture','--freeze',str(freeze),
               '--output',str(capture),'--released']
    started = time.monotonic_ns(); budget_seconds = 7200
    info = dict(schema='eighth_sampling_work_controller_v1',validation='running',command=command,
        working_directory=str(work.ROOT),started_utc=work.native.now(),started_monotonic_ns=started,
        source_sha256=hashes,deadline_seconds=budget_seconds,native_solver_execution_authorized=True,
        native_solver_execution=True,
        performance_execution=False,all_owned_groups_verified_empty=False)
    work.write_json(paths['invocation'],info,exclusive=True)
    process = None; sampler = None; old = signal.getsignal(signal.SIGTERM)
    def interrupted(signum,frame): raise KeyboardInterrupt('diagnostic controller received SIGTERM')
    signal.signal(signal.SIGTERM,interrupted)
    try:
        sampler = work.monitor.BoundedSampler(work.monitor.LibprocProvider())
        work.require(not sampler.poisoned,'poisoned outer sampler')
        with paths['stdout'].open('x') as stdout,paths['stderr'].open('x') as stderr:
            process = subprocess.Popen(command,cwd=work.ROOT,stdout=stdout,stderr=stderr,start_new_session=True)
            info['outer_process_group'] = process.pid
            # Each native child belongs to another session, guarded by the
            # unchanged collector. This timeout governs the Python controller.
            while process.poll() is None:
                remaining = budget_seconds-(time.monotonic_ns()-started)/1e9
                work.require(remaining > 0,'outer diagnostic deadline exceeded')
                try: process.wait(timeout=min(30,remaining))
                except subprocess.TimeoutExpired: pass
            info['wrapper_exit_observed_monotonic_ns'] = time.monotonic_ns()
            work.require(info['wrapper_exit_observed_monotonic_ns']-started <= budget_seconds*10**9,
                         'outer observed exit exceeded deadline')
            work.require(type(process.returncode) is int and process.returncode == 0,'collector failed')
        info['validation'] = 'command_completed'
    except BaseException as error:
        info.update(validation='failed',error=repr(error))
    finally:
        try:
            signal.signal(signal.SIGTERM,signal.SIG_IGN)
            try: cleanup = work.monitor.bounded_terminate(process,sampler,term_seconds=30,kill_seconds=5)
            except BaseException as error:
                cleanup = dict(native_exit_known=False,group_exit_known=False,
                               native_process_may_still_be_running=True,error=repr(error))
            info['outer_cleanup'] = cleanup
            info['exit_status'] = process.poll() if process is not None else None
            work.require(cleanup.get('native_exit_known') is True and cleanup.get('group_exit_known') is True
                         and cleanup.get('native_process_may_still_be_running') is False,'outer group exit unknown')
            if info['validation'] == 'command_completed':
                captured,values = work.load(capture)
                work.require(len(values) == 48,'incomplete diagnostic inputs')
                for path,digest in hashes.items(): work.analysis.hash_check(Path(path),digest)
                info.update(validation='pass',all_owned_groups_verified_empty=True,native_solver_execution=True,
                            checked_children=48,checked_solver_outputs=144,checked_replay_chains=96,
                            capture=str(capture),capture_sha256=work.native.sha(capture))
        except BaseException as error:
            info.update(validation='failed',cleanup_or_proof_error=repr(error))
        finally:
            signal.signal(signal.SIGTERM,old)
            info.update(finished_utc=work.native.now(),finished_monotonic_ns=time.monotonic_ns())
            info['elapsed_seconds'] = (info['finished_monotonic_ns']-started)/1e9
            info['outer_monitor_events'] = sampler.events if sampler is not None else {}
            for name in ('stdout','stderr'):
                info[name] = str(paths[name])
                if paths[name].exists(): info[name+'_sha256'] = work.native.sha(paths[name])
            work.write_json(paths['receipt'],info,exclusive=True)
    print(json.dumps({name:info.get(name) for name in ('validation','exit_status','checked_children',
          'all_owned_groups_verified_empty','error','cleanup_or_proof_error')},indent=2))
    raise SystemExit(0 if info['validation'] == 'pass' else 1)


if __name__ == '__main__': main()
