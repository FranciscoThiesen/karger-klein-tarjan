#!/usr/bin/env python3
"""Archive one bounded frontend build and twelve explicitly released small gates."""
import json
from pathlib import Path
import signal
import subprocess
import sys
import time
import build_driver as b


def main():
    b.require(sys.argv[1:] == ['--released-small-gates'], 'explicit small-gate release required')
    prefix = b.HERE / 'build-controller-attempt02'
    paths = {name: Path(str(prefix)+'.'+suffix) for name,suffix in
             (('invocation','invocation.json'),('receipt','json'),('stdout','stdout'),('stderr','stderr'))}
    b.require(not any(path.exists() for path in paths.values()), 'refusing existing attempt')
    command = [sys.executable,'-B',str(b.HERE/'build_driver.py'),'--released-small-gates']
    hashes = {str(path): b.sha(path) for path in (Path(__file__).resolve(),b.HERE/'build_driver.py',b.DRIVER,b.OLD_FREEZE)}
    started = time.monotonic_ns()
    info = dict(schema='heldout_spatial_build_controller_v1',validation='running',command=command,
        working_directory=str(b.ROOT),source_sha256=hashes,started_utc=b.old.native.now(),
        started_monotonic_ns=started,deadline_seconds=180,native_execution_authorized=True,
        performance_execution=False,all_owned_groups_verified_empty=False)
    b.save(paths['invocation'],info,exclusive=True)
    process = None; sampler = None; previous = signal.getsignal(signal.SIGTERM)
    def interrupted(signum,frame): raise KeyboardInterrupt('frontend controller received SIGTERM')
    signal.signal(signal.SIGTERM,interrupted)
    try:
        sampler = b.old.monitor.BoundedSampler(b.old.monitor.LibprocProvider())
        b.require(not sampler.poisoned,'poisoned sampler')
        with paths['stdout'].open('x') as out,paths['stderr'].open('x') as err:
            process = subprocess.Popen(command,cwd=b.ROOT,stdout=out,stderr=err,start_new_session=True)
            info['outer_process_group'] = process.pid
            while process.poll() is None:
                remaining = 180-(time.monotonic_ns()-started)/1e9
                b.require(remaining > 0,'outer build deadline exceeded')
                try: process.wait(timeout=min(2,remaining))
                except subprocess.TimeoutExpired: pass
            info['wrapper_exit_observed_monotonic_ns'] = time.monotonic_ns()
            b.require(info['wrapper_exit_observed_monotonic_ns']-started <= 180*10**9,'late outer exit')
            b.require(type(process.returncode) is int and process.returncode == 0,'frontend build/gate failed')
        info['validation'] = 'command_completed'
    except BaseException as error:
        info.update(validation='failed',error=repr(error))
    finally:
        try:
            signal.signal(signal.SIGTERM,signal.SIG_IGN)
            try: cleanup = b.old.monitor.bounded_terminate(process,sampler,term_seconds=30,kill_seconds=5)
            except BaseException as error:
                cleanup = dict(native_exit_known=False,group_exit_known=False,
                               native_process_may_still_be_running=True,error=repr(error))
            info['outer_cleanup'] = cleanup
            info['exit_status'] = process.poll() if process is not None else None
            b.require(cleanup.get('native_exit_known') is True and cleanup.get('group_exit_known') is True and
                      cleanup.get('native_process_may_still_be_running') is False,'outer exit unknown')
            if info['validation'] == 'command_completed':
                b.check_record()
                for path,digest in hashes.items(): b.old.analysis.hash_check(Path(path),digest)
                info.update(validation='pass',all_owned_groups_verified_empty=True,native_execution=True,
                    checked_build_commands=2,checked_small_inputs=12,checked_solver_outputs=36,
                    checked_replay_chains=24,build_record=str(b.RECORD),build_record_sha256=b.sha(b.RECORD))
        except BaseException as error:
            info.update(validation='failed',cleanup_or_proof_error=repr(error))
        finally:
            signal.signal(signal.SIGTERM,previous)
            info.update(finished_utc=b.old.native.now(),finished_monotonic_ns=time.monotonic_ns())
            info['elapsed_seconds'] = (info['finished_monotonic_ns']-started)/1e9
            info['outer_monitor_events'] = sampler.events if sampler is not None else {}
            for name in ('stdout','stderr'):
                info[name] = str(paths[name])
                if paths[name].exists(): info[name+'_sha256'] = b.sha(paths[name])
            b.save(paths['receipt'],info,exclusive=True)
    print(json.dumps({key:info.get(key) for key in ('validation','exit_status','checked_small_inputs',
                      'all_owned_groups_verified_empty','error','cleanup_or_proof_error')},indent=2))
    raise SystemExit(0 if info['validation'] == 'pass' else 1)


if __name__ == '__main__': main()
