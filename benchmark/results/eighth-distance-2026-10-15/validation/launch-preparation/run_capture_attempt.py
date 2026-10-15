#!/usr/bin/env python3
"""Archive an explicitly released, fixed 24-child eighth-distance capture.

The 21,600-second complete-interval ceiling is not an expected runtime or a
per-child deadline. Actual collector exit and strict reload are both required.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

ROOT = Path('/Users/random_person/Desktop/kkt-eighth-sampling')
STUDY = ROOT/'benchmark/results/eighth-distance-2026-10-15'
COLLECTOR = ROOT/'benchmark/run_eighth_distance.py'
_saved_path = sys.path[:]
try:
    sys.path.insert(0, str(ROOT/'benchmark'))
    _spec = importlib.util.spec_from_file_location('_eighth_distance_outer_collector', COLLECTOR)
    engine = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(engine)
finally:
    sys.path[:] = _saved_path

monitor = engine.monitor
BUDGET_SECONDS = 21600
SIZES = (1024, 4096, 16384, 65536, 262144, 1048576)
FAMILIES = ('leaf_distance4', 'leaf_shuffled4')
MACHINE_COMMANDS = [['/usr/bin/arch'], ['/usr/sbin/sysctl', '-n', 'machdep.cpu.brand_string'],
                    ['/usr/sbin/sysctl', '-n', 'hw.memsize'], ['/usr/bin/sw_vers'],
                    ['/usr/sbin/sysctl', 'vm.swapusage'], ['/usr/bin/pmset', '-g', 'assertions']]


def exact(actual, expected, message):
    engine.require(type(actual) is type(expected) and actual == expected, message)


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def expected_cases():
    return {f'{family}_n{n}_d32_p0': dict(case_id=f'{family}_n{n}_d32_p0', family=family,
            n=n, m=n*32, density=32, intrusion_per_mille=0) for n in SIZES for family in FAMILIES}


def expected_schedule():
    cases = list(expected_cases())
    return [dict(case_id=case, graph_seed=graph, kkt_seed=3203)
            for index, graph in enumerate((21000011, 21000041))
            for case in (cases if index == 0 else cases[::-1])]


def recheck(hashes):
    for path, digest in hashes.items(): engine.analysis.hash_check(Path(path), digest)


def merge(bound, additions):
    for path, digest in additions.items():
        engine.require(path not in bound or bound[path] == digest, 'conflicting evidence hash')
        bound[path] = digest


def command():
    return ['/usr/bin/arch', '-arm64', '/usr/bin/python3', '-B', '-u', str(COLLECTOR),
            'capture', '--freeze', str(STUDY/'freeze.json'), '--output', str(STUDY/'distance.csv'), '--released']


def preflight(args):
    engine.require(args.released, 'explicit root quiet performance release required')
    engine.require(Path.cwd().resolve() == ROOT, 'run from the fixed eighth worktree')
    engine.require(type(args.freeze_sha256) is str and re.fullmatch(r'[0-9a-f]{64}', args.freeze_sha256),
                   'invalid explicit future freeze hash')
    engine.require(type(args.attempt) is str and re.fullmatch(r'[a-z][a-z0-9_-]*', args.attempt),
                   'invalid exclusive attempt name')
    freeze = STUDY/'freeze.json'; engine.analysis.hash_check(freeze, args.freeze_sha256)
    frozen, cases = engine.check_freeze(freeze)
    exact(frozen['working_directory'], str(ROOT), 'wrong frozen working directory')
    exact(cases, expected_cases(), 'wrong twelve-case distance declaration')
    exact(frozen['schedule'], expected_schedule(), 'wrong 24-child distance schedule')
    exact(frozen['resource_rule']['rss_limit_kib'], 40*1024*1024, 'different native RSS cap')
    before = STUDY/'machine-before.json'; metadata = engine.analysis.read_json(before)
    exact(metadata['validation'], 'pass', 'missing successful machine preflight')
    exact(metadata['phase'], 'before', 'wrong machine metadata phase')
    exact(metadata['sleep_inhibition_verified'], False, 'unexpected sleep-inhibition claim')
    exact([item['command'] for item in metadata['commands']], MACHINE_COMMANDS, 'wrong machine queries')
    engine.require(all(type(item['exit_status']) is int and item['exit_status'] == 0
                       for item in metadata['commands']), 'failed machine query')
    hashes = {str(path): engine.native.sha(path) for path in
              (Path(__file__).resolve(), COLLECTOR, freeze, before)}
    exact(hashes[str(freeze)], args.freeze_sha256, 'freeze changed during preflight')
    recheck(hashes)
    return hashes


def check_completion(capture, freeze_sha256, hashes):
    captured, cases, rows, diagnostics, resources, inherited = engine.load(capture)
    for key, expected in dict(validation='pass', checked_rows=1008, checked_timed_rows=864,
                              checked_warmup_rows=144, cleanup=[], native_process_may_still_be_running=False,
                              freeze=str(STUDY/'freeze.json'), freeze_sha256=freeze_sha256).items():
        exact(captured[key], expected, 'incomplete strict completion: '+key)
    exact(cases, expected_cases(), 'completed cases differ from fixed declaration')
    items = captured['captures']
    exact([{field:item[field] for field in ('case_id','graph_seed','kkt_seed')} for item in items],
          expected_schedule(), 'wrong completed native identities')
    exact(len(rows), 1008, 'wrong solver output count')
    exact(sum(row['phase'] == 'timed' for row in rows), 864, 'wrong timed output count')
    exact(sum(row['phase'] == 'warmup' for row in rows), 144, 'wrong warmup output count')
    exact(len(diagnostics), 1008, 'incomplete clock diagnostic coverage')
    exact(len(resources), 24, 'incomplete child resource coverage')
    groups = [item['process_group'] for item in items]
    engine.require(all(type(group) is int and group > 0 for group in groups) and len(set(groups)) == 24,
                   'incomplete or reused native process groups')
    engine.require(all(type(item['exit_status']) is int and item['exit_status'] == 0 and
                       item['group_exit_verification']['validation'] == 'pass' and
                       item['group_exit_verification']['members'] == [] for item in items),
                   'native groups are not verified empty')
    bound = dict(hashes); merge(bound, inherited); recheck(bound)
    return dict(validation='pass', checked_children=24, checked_solver_outputs=1008,
                checked_timed_outputs=864, checked_warmup_outputs=144, native_process_groups=groups,
                capture=str(capture), capture_sha256=engine.native.sha(capture), bound_sha256=bound,
                detached_native_groups_verified_empty=True)


def bounded_proof(capture, freeze_sha256, hashes, deadline):
    remaining = (deadline-time.monotonic_ns())/1e9
    engine.require(remaining > 0, 'no complete-interval budget remains for strict reload')
    engine.require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'unexpected existing real-time timer')
    previous = signal.getsignal(signal.SIGALRM)
    def expired(signum, frame): raise TimeoutError('complete-interval deadline during strict reload')
    try:
        signal.signal(signal.SIGALRM, expired); signal.setitimer(signal.ITIMER_REAL, remaining)
        return check_completion(capture, freeze_sha256, hashes)
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
    hashes = preflight(args)
    capture = STUDY/'distance.json'
    engine.require(not any(path.exists() for path in (capture, STUDY/'distance.csv', STUDY/'distance_cases')),
                   'refusing existing raw evidence, including failed captures')
    output = STUDY/'validation'/args.attempt; output.mkdir(parents=True, exist_ok=False)
    argv = command(); started = time.monotonic_ns(); deadline = started+BUDGET_SECONDS*10**9
    info = dict(schema='eighth_distance_outer_capture_v1', validation='running', command=argv,
                working_directory=str(ROOT), freeze=str(STUDY/'freeze.json'), freeze_sha256=args.freeze_sha256,
                source_sha256=hashes, started_utc=engine.native.now(), started_monotonic_ns=started,
                complete_interval_budget_seconds=BUDGET_SECONDS,
                deadline_scope='launch through cleanup, strict reload and log hashing; ceiling, not expected runtime',
                per_child_total_wall_deadline=None, native_child_sampled_rss_limit_kib=40*1024*1024,
                cleanup_term_seconds=30, cleanup_kill_seconds=5,
                native_solver_execution_authorized=True, performance_execution_authorized=True,
                native_solver_execution=None, performance_execution=None, sleep_inhibition_verified=False,
                outer_observations=[], outer_group_verified_empty=False,
                detached_native_groups_verified_empty=False, detached_native_process_may_still_be_running=False,
                all_owned_groups_verified_empty=False)
    save(output/'invocation.json', info)
    process = None; sampler = None; previous = signal.getsignal(signal.SIGTERM)
    def interrupted(signum, frame): raise KeyboardInterrupt('distance capture launcher received SIGTERM')
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
                engine.require(remaining > 0, 'overall distance capture deadline exceeded')
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
                info['strict_completion'] = bounded_proof(capture, args.freeze_sha256, hashes, deadline)
                info.update(validation='pass', detached_native_groups_verified_empty=True,
                            detached_native_process_may_still_be_running=False, all_owned_groups_verified_empty=True,
                            native_solver_execution=True, performance_execution=True)
        except BaseException as error: info.update(validation='failed', cleanup_or_proof_error=repr(error))
        finally:
            signal.signal(signal.SIGTERM, previous)
            info['outer_monitor_events'] = sampler.events if sampler is not None else {}
            for name in ('stdout', 'stderr'):
                path = output/name; info[name] = str(path)
                if path.exists(): info[name+'_sha256'] = engine.native.sha(path)
            info.update(finished_utc=engine.native.now(), finished_monotonic_ns=time.monotonic_ns())
            info['elapsed_seconds'] = (info['finished_monotonic_ns']-started)/1e9
            if info['finished_monotonic_ns'] > deadline:
                info.update(validation='failed', complete_interval_deadline_exceeded=True)
            save(output/'receipt.json', info)
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze-sha256', required=True)
    parser.add_argument('--attempt', required=True, help='fresh directory name under fixed study validation/')
    parser.add_argument('--released', action='store_true'); args = parser.parse_args()
    result = run(args)
    print(json.dumps({key: result.get(key) for key in ('validation', 'exit_status', 'elapsed_seconds',
        'outer_group_verified_empty', 'detached_native_groups_verified_empty', 'all_owned_groups_verified_empty',
        'error', 'cleanup_or_proof_error')}))
    raise SystemExit(0 if result['validation'] == 'pass' else 1)


if __name__ == '__main__': main()
