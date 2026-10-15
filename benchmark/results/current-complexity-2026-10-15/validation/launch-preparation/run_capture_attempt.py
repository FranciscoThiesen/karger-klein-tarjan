#!/usr/bin/env python3
"""Archive one explicitly released, fixed 24-curve complexity capture.

The complete-interval ceiling is not an expected run time. Actual collector
exit and complete strict reload are required for success.
"""
import argparse
import json
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

ROOT = Path('/Users/random_person/Desktop/kkt-eighth-sampling')
PACKAGE = ROOT/'benchmark/current_complexity'
STUDY = ROOT/'benchmark/results/current-complexity-2026-10-15'
sys.path.insert(0, str(PACKAGE))
import collect as engine

monitor = engine.monitor
CURVE_SECONDS = 3600
BUDGET_SECONDS = 24*CURVE_SECONDS+600


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def expected_schedule():
    algorithms = ('kkt', 'multigraph_boruvka')
    return [dict(family=family, algorithm=algorithm, graph_seed=graph, sampling_seed=sampler,
                 size_order='ascending' if gi == 0 else 'descending')
            for family in ('leaf_hierarchy4', 'leaf_shuffled4', 'gnm_random')
            for gi, graph in enumerate((19000013, 19000043))
            for si, sampler in enumerate((3001, 3011))
            for algorithm in (algorithms if (gi+si)%2 == 0 else algorithms[::-1])]


def merge(bound, additions):
    for path, digest in additions.items():
        engine.require(path not in bound or bound[path] == digest, 'conflicting evidence hash')
        bound[path] = digest


def sources():
    paths = {Path(__file__).resolve(), *(path for path in PACKAGE.iterdir() if path.suffix in ('.py', '.cpp', '.md'))}
    return {str(path.resolve()): engine.digest(path) for path in sorted(paths)}


def command(capture):
    return ['/usr/bin/arch', '-arm64', '/usr/bin/python3', '-B', '-u', str(PACKAGE/'collect.py'),
            'capture', '--freeze', str(STUDY/'freeze.json'), '--output', str(capture), '--released']


def preflight(args):
    engine.require(args.released, 'explicit root quiet performance release required')
    engine.require(Path.cwd().resolve() == ROOT and engine.ROOT == ROOT, 'run from the fixed eighth worktree')
    engine.require(type(args.freeze_sha256) is str and re.fullmatch(r'[0-9a-f]{64}', args.freeze_sha256), 'invalid explicit freeze hash')
    engine.require(re.fullmatch(r'[a-z][a-z0-9_-]*', args.attempt), 'invalid exclusive attempt name')
    freeze = STUDY/'freeze.json'
    engine.digest(freeze, args.freeze_sha256)
    frozen = engine.check_freeze(freeze)
    engine.exact(frozen['schedule'], expected_schedule(), 'different 24-curve declaration')
    engine.exact(frozen['sizes'], [1 << exponent for exponent in range(10, 21)], 'different eleven-size ladder')
    engine.exact(frozen['deadline_seconds'], CURVE_SECONDS, 'different per-curve deadline')
    engine.require(frozen['resource_rule']['rss_limit_kib'] == 40*1024*1024, 'different per-curve RSS cap')
    before = sources(); bound = dict(before)
    for inventory in ('source_sha256', 'parent_helpers', 'bound_sha256'): merge(bound, frozen[inventory])
    merge(bound, {str(freeze): args.freeze_sha256})
    engine.recheck(bound)
    return before, bound


def check_completion(capture, freeze_sha256, before, bound):
    captured, records, inherited = engine.load(capture)
    for key, expected in dict(validation='pass', checked_curves=24, checked_raw_rows=2376,
                              checked_timed_rows=1584, checked_warmup_rows=792,
                              cleanup=[], native_process_may_still_be_running=False,
                              freeze=str(STUDY/'freeze.json'), freeze_sha256=freeze_sha256).items():
        engine.exact(captured[key], expected, 'incomplete strict completion: '+key)
    engine.exact([record['spec'] for record in records], expected_schedule(), 'wrong completed curve identities')
    groups = [record['process_group'] for record in records]
    engine.require(all(type(group) is int and group > 0 for group in groups) and len(set(groups)) == 24,
                   'incomplete or reused native process groups')
    engine.require(all(type(record['exit_status']) is int and record['exit_status'] == 0 and
                       record['group_exit_verification']['validation'] == 'pass' and
                       record['group_exit_verification']['members'] == [] for record in records),
                   'native group exit is not verified')
    merge(bound, inherited); engine.exact(sources(), before, 'launcher/package source changed')
    engine.recheck(bound)
    return dict(validation='pass', checked_curves=24, checked_solver_calls=2376,
                checked_timed_calls=1584, checked_warmup_calls=792, native_process_groups=groups,
                capture=str(capture), capture_sha256=engine.digest(capture), bound_sha256=bound,
                detached_native_groups_verified_empty=True)


def bounded_proof(capture, freeze_sha256, before, bound, deadline):
    remaining = (deadline-time.monotonic_ns())/1e9
    engine.require(remaining > 0, 'no complete-interval budget remains for strict reload')
    engine.require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'unexpected existing real-time timer')
    previous = signal.getsignal(signal.SIGALRM)
    def expired(signum, frame): raise TimeoutError('complete-interval deadline during strict reload')
    try:
        signal.signal(signal.SIGALRM, expired); signal.setitimer(signal.ITIMER_REAL, remaining)
        return check_completion(capture, freeze_sha256, before, bound)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0); signal.signal(signal.SIGALRM, previous)


def cleanup_outer(process, sampler):
    previous = signal.getsignal(signal.SIGTERM)
    try:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        try: return monitor.bounded_terminate(process, sampler, term_seconds=30, kill_seconds=5)
        except BaseException as error:
            return dict(native_exit_known=False, group_exit_known=False,
                        native_process_may_still_be_running=True, error=repr(error))
    finally: signal.signal(signal.SIGTERM, previous)


def run(args):
    before, bound = preflight(args)
    output = STUDY/args.attempt; output.mkdir(parents=True, exist_ok=False)
    capture = output/'capture.json'; argv = command(capture)
    started = time.monotonic_ns(); deadline = started+BUDGET_SECONDS*10**9
    info = dict(schema='current_complexity_outer_capture_v1', validation='running', command=argv,
                working_directory=str(ROOT), package=str(PACKAGE), freeze=str(STUDY/'freeze.json'),
                freeze_sha256=args.freeze_sha256, source_sha256=before, initial_bound_sha256=bound.copy(),
                started_utc=engine.native.now(), started_monotonic_ns=started,
                complete_interval_budget_seconds=BUDGET_SECONDS,
                deadline_scope='launch through cleanup, strict reload and log hashing; ceiling, not expected runtime',
                per_curve_native_exit_seconds=CURVE_SECONDS, cleanup_term_seconds=30, cleanup_kill_seconds=5,
                native_solver_execution_authorized=True, performance_execution_authorized=True,
                native_solver_execution=None, performance_execution=None,
                outer_observations=[], outer_group_verified_empty=False,
                detached_native_groups_verified_empty=False, detached_native_process_may_still_be_running=False,
                all_owned_groups_verified_empty=False)
    save(output/'invocation.json', info)
    process = None; sampler = None; previous = signal.getsignal(signal.SIGTERM)
    def interrupted(signum, frame): raise KeyboardInterrupt('complexity capture launcher received SIGTERM')
    signal.signal(signal.SIGTERM, interrupted)
    try:
        sampler = monitor.BoundedSampler(monitor.LibprocProvider())
        engine.require(not sampler.poisoned, 'poisoned outer sampler')
        with (output/'stdout').open('x') as stdout, (output/'stderr').open('x') as stderr:
            info['detached_native_process_may_still_be_running'] = True
            process = subprocess.Popen(argv, cwd=ROOT, stdout=stdout, stderr=stderr, start_new_session=True)
            info['outer_process_group'] = process.pid; unavailable = 0
            while process.poll() is None:
                remaining = (deadline-time.monotonic_ns())/1e9
                engine.require(remaining > 0, 'overall complexity capture deadline exceeded')
                try: process.wait(timeout=min(2, remaining))
                except subprocess.TimeoutExpired: pass
                observation = sampler.sample(process.pid); info['outer_observations'].append(observation)
                unavailable = unavailable+1 if observation['validation'] != 'pass' else 0
                engine.require(not sampler.poisoned and unavailable < 3, 'outer resource observations unavailable')
                engine.require(observation['validation'] != 'pass' or observation['rss_kib'] <= 40*1024*1024,
                               'outer collector group exceeded 40 GiB')
            info['wrapper_exit_observed_monotonic_ns'] = time.monotonic_ns()
            engine.require(info['wrapper_exit_observed_monotonic_ns'] <= deadline, 'collector exit observed beyond deadline')
            engine.require(type(process.returncode) is int and process.returncode == 0, 'collector exited unsuccessfully')
        info['validation'] = 'command_completed'
    except BaseException as error: info.update(validation='failed', error=repr(error))
    finally:
        try:
            cleanup = cleanup_outer(process, sampler); info['outer_cleanup'] = cleanup
            info['exit_status'] = process.poll() if process is not None else None
            engine.require(cleanup.get('native_exit_known') is True and cleanup.get('group_exit_known') is True and
                           cleanup.get('native_process_may_still_be_running') is False, 'outer group exit unknown')
            info['outer_group_verified_empty'] = True
            if info['validation'] == 'command_completed':
                info['strict_completion'] = bounded_proof(capture, args.freeze_sha256, before, bound, deadline)
                info.update(validation='pass', detached_native_groups_verified_empty=True,
                            detached_native_process_may_still_be_running=False, all_owned_groups_verified_empty=True,
                            native_solver_execution=True, performance_execution=True)
        except BaseException as error: info.update(validation='failed', cleanup_or_proof_error=repr(error))
        finally:
            signal.signal(signal.SIGTERM, previous)
            info['outer_monitor_events'] = sampler.events if sampler is not None else {}
            for name in ('stdout', 'stderr'):
                path = output/name; info[name] = str(path)
                if path.exists(): info[name+'_sha256'] = engine.digest(path)
            info.update(finished_utc=engine.native.now(), finished_monotonic_ns=time.monotonic_ns())
            info['elapsed_seconds'] = (info['finished_monotonic_ns']-started)/1e9
            if info['finished_monotonic_ns'] > deadline:
                info.update(validation='failed', complete_interval_deadline_exceeded=True)
            save(output/'receipt.json', info)
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze-sha256', required=True)
    parser.add_argument('--attempt', required=True, help='fresh directory name under the fixed study')
    parser.add_argument('--released', action='store_true'); args = parser.parse_args()
    result = run(args)
    print(json.dumps({key: result.get(key) for key in ('validation', 'exit_status', 'elapsed_seconds',
        'outer_group_verified_empty', 'detached_native_groups_verified_empty', 'all_owned_groups_verified_empty',
        'error', 'cleanup_or_proof_error')}))
    raise SystemExit(0 if result['validation'] == 'pass' else 1)


if __name__ == '__main__': main()
