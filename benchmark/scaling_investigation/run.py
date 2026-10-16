#!/usr/bin/env python3
"""Sequential diagnostics with bounded owned groups and exact output validation."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
_saved_path = list(sys.path)
try:
    sys.path.insert(0, str(ROOT/'benchmark'))
    import recover_mst_search as monitor
finally:
    sys.path[:] = _saved_path
SOURCES = ['boruvka/boruvka.cpp', 'kruskal/kruskal.cpp', 'prim/prim.cpp', 'lca/lca.cpp',
           'union_find/union_find.cpp', 'graph_utils/graph_utils.cpp', 'verifier/verifier_v2.cpp', 'kkt/kkt.cpp']
BASE_FLAGS = ['-std=c++17', '-O3', '-march=native', '-Wall', '-Wextra', '-I'+str(ROOT),
              '-DKKT_EXPERIMENT_RETAIN_PARALLEL', '-DKKT_EXPERIMENT_EDGE_VIEW',
              '-DKKT_EXPERIMENT_COMPRESSED_QUERIES', '-DKKT_EXPERIMENT_EIGHTH_SAMPLING']
VARIANTS = {'reference': [], 'phase': ['-DKKT_ENABLE_PHASE_STATS'],
            'allocation': ['-DKKT_ENABLE_PHASE_STATS', '-DKKT_SCALING_ALLOCATIONS'],
            'work': ['-DKKT_ENABLE_WORK_STATS']}
PHASES = 'api input recursion contraction minimum_scan sampling isolation forest_recovery partition tree_setup fbt lca_build queries query_gather mark_scatter path_solve median_table path_walk filtering output'.split()
PHASE_FIELDS = 'wall_ns calls allocations requested_bytes usable_bytes deallocations freed_usable_bytes'.split()
ROW_FIELDS = set('schema family n m graph_seed sampling_seed input_fingerprint topology_fingerprint repetition warmup wall_ns cpu_ns utc_start_ns utc_end_ns phase_total_ns peak_live_usable_bytes returned_live_usable_bytes phases work work_proxy validation'.split())
GOOGLE_CAPTURE = ROOT/'benchmark/results/current-complexity-2026-10-15/capture-attempt01/capture.json'
GOOGLE_SHA = '2d2d95769fe6c7cd6e7608450ba891fcbf5dacd97938fe700ff8058577db6206'
_sampler = None
_launch_blocked = False
EMPTY_ENVIRONMENT = ('CPLUS_INCLUDE_PATH', 'C_INCLUDE_PATH', 'CFLAGS', 'CXXFLAGS', 'CPPFLAGS', 'LDFLAGS',
                     'CC', 'CXX', 'CMAKE_GENERATOR', 'CMAKE_TOOLCHAIN_FILE', 'CMAKE_POLICY_VERSION_MINIMUM',
                     'CMAKE_OSX_ARCHITECTURES', 'MACOSX_DEPLOYMENT_TARGET', 'APPVEYOR')


def require(ok, why):
    if not ok: raise RuntimeError(why)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')


def strict_json(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate JSON key'); result[key] = value
        return result
    def finite(value):
        if isinstance(value, float): require(math.isfinite(value), 'nonfinite JSON number')
        elif isinstance(value, dict):
            for item in value.values(): finite(item)
        elif isinstance(value, list):
            for item in value: finite(item)
    value = json.loads(text, object_pairs_hook=unique,
                       parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite '+value)))
    finite(value)
    return value


def uint(value): return type(value) is int and 0 <= value <= 2**64-1


def recheck(inventory):
    for path, digest in inventory.items(): require(sha(path) == digest, 'artifact drift: '+str(path))


def sampler():
    global _sampler
    if _sampler is None: _sampler = monitor.BoundedSampler(monitor.LibprocProvider())
    return _sampler


def clean_environment():
    environment = dict(os.environ)
    checked = sorted(set(EMPTY_ENVIRONMENT) | {key for key in environment if key.startswith('DYLD_')})
    policy = {'removed': {key: environment.pop(key, None) for key in ('CPATH', 'LIBRARY_PATH')},
              'required_empty': {key: environment.get(key) for key in checked},
              'retained': {key: environment.get(key) for key in ('SDKROOT', 'DEVELOPER_DIR')}}
    require(all(value in (None, '') for value in policy['required_empty'].values()),
            'unreviewed nonempty toolchain override')
    return environment, policy


def run_owned(command, directory, label, timeout=300, rss_cap=12*1024**3):
    """Reuse the reviewed bounded provider/cleanup; unknown exit forbids continuation."""
    global _launch_blocked
    require(not _launch_blocked, 'prior unknown exit/poison forbids another child')
    environment, policy = clean_environment()
    guard = sampler(); require(not guard.poisoned, 'poisoned sampler')
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    out, err, receipt = [directory/(label+suffix) for suffix in ('.stdout', '.stderr', '.json')]
    require(not any(path.exists() for path in (out, err, receipt)), 'output collision')
    start = time.monotonic_ns(); process = None; error = None; unavailable = 0; launch_attempted = False
    record = {'command': command, 'cwd': str(ROOT), 'pgid': None, 'exit_code': None,
              'validation': 'running', 'group_empty': False, 'native_process_may_still_be_running': True,
              'start_utc_ns': time.time_ns(), 'started_monotonic_ns': start, 'exit_monotonic_ns': None,
              'deadline_seconds': timeout, 'rss_limit_bytes': rss_cap, 'observations': [],
              'peak_sampled_group_rss_bytes': 0, 'environment_policy': policy}
    previous = signal.getsignal(signal.SIGTERM)
    def terminated(signum, frame): raise KeyboardInterrupt('owned diagnostic received SIGTERM')
    signal.signal(signal.SIGTERM, terminated)
    try:
        with out.open('xb') as stdout, err.open('xb') as stderr:
            try:
                launch_attempted = True
                process = subprocess.Popen(command, cwd=ROOT, stdout=stdout, stderr=stderr, start_new_session=True, env=environment)
                record['pgid'] = process.pid
                while process.poll() is None:
                    remaining = timeout-(time.monotonic_ns()-start)/1e9
                    require(remaining > 0, 'native deadline')
                    try: process.wait(timeout=min(2.0, remaining))
                    except subprocess.TimeoutExpired: pass
                    observation = guard.sample(process.pid); record['observations'].append(observation)
                    unavailable = unavailable+1 if observation['validation'] != 'pass' else 0
                    require(not guard.poisoned and unavailable < 3, 'resource observations unavailable')
                    if observation['validation'] == 'pass':
                        rss = observation['rss_kib']*1024
                        record['peak_sampled_group_rss_bytes'] = max(record['peak_sampled_group_rss_bytes'], rss)
                        require(rss <= rss_cap, 'sampled RSS limit')
                record['exit_monotonic_ns'] = time.monotonic_ns()
                record['exit_code'] = process.returncode
                require(record['exit_monotonic_ns']-start <= timeout*1e9, 'native exit observed after deadline')
                require(type(process.returncode) is int and process.returncode == 0, 'nonzero native exit')
            except BaseException as caught:
                error = caught; record['error'] = repr(caught)
            finally:
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
                try:
                    cleanup = monitor.bounded_terminate(process, guard)
                    record['cleanup'] = cleanup
                    # Require all three affirmative facts; a direct wrapper exit alone is insufficient.
                    known = ((process is not None or not launch_attempted)
                             and cleanup.get('native_exit_known') is True and cleanup.get('group_exit_known') is True
                             and cleanup.get('native_process_may_still_be_running') is False)
                    record['native_process_may_still_be_running'] = not known
                    record['group_empty'] = known
                    if process is not None: record['exit_code'] = process.poll()
                    if not known or guard.poisoned:
                        _launch_blocked = True
                        if error is None: error = RuntimeError('owned group exit unknown or sampler poisoned')
                except BaseException as caught:
                    _launch_blocked = True; record['cleanup_error'] = repr(caught)
                    if error is None: error = caught
    finally:
        record['finished_monotonic_ns'] = time.monotonic_ns(); record['end_utc_ns'] = time.time_ns()
        record['duration_s'] = (record['finished_monotonic_ns']-start)/1e9
        record['rss_samples'] = len(record['observations'])
        record['stdout_sha256'] = sha(out) if out.exists() else None
        record['stderr_sha256'] = sha(err) if err.exists() else None
        if error is not None: record['error'] = repr(error)
        record['validation'] = 'pass' if error is None and record['group_empty'] else 'failed'
        try: write(receipt, record)
        finally: signal.signal(signal.SIGTERM, previous)
    if error is not None: raise error
    require(record['validation'] == 'pass', 'owned command did not pass')
    return record


def source_inventory():
    paths = set(ROOT.glob('*/*.hpp')) | {ROOT/p for p in SOURCES}
    paths |= {HERE/'diagnostic.cpp', HERE/'run.py', ROOT/'docs/scaling-investigation/PROTOCOL.md'}
    paths |= {Path(name) for name in monitor.capture.helpers()} | {Path(monitor.__file__)}
    return {str(path.resolve()): sha(path) for path in sorted(paths)}


def bounded_output(command):
    environment, policy = clean_environment()
    return subprocess.check_output(command, cwd=ROOT, text=True, timeout=30, env=environment)


def binary_profile(binary):
    description = bounded_output(['/usr/bin/file', '-b', str(binary)]).strip()
    require(description == 'Mach-O 64-bit executable arm64', 'rejected non-native binary')
    loads = bounded_output(['/usr/bin/otool', '-l', str(binary)])
    stacks = re.findall(r'\bcmd LC_MAIN\b(?:(?!Load command).)*?\bstacksize (\d+)', loads, re.S)
    require(stacks == ['536870912'], 'missing/duplicate 512 MiB stack')
    return {'description': description, 'load_commands': loads, 'stack_bytes': 536870912}


def build(out, variant_names):
    out.mkdir(parents=True, exist_ok=False)
    require(len(set(variant_names)) == len(variant_names), 'duplicate build variant')
    sdk = bounded_output(['/usr/bin/arch', '-arm64', '/usr/bin/xcrun', '--show-sdk-path']).strip()
    compiler = bounded_output(['/usr/bin/arch', '-arm64', '/usr/bin/clang++', '--version'])
    require('Apple clang' in compiler and 'Target: arm64-' in compiler, 'wrong compiler profile')
    flags = BASE_FLAGS+['-isysroot', sdk]; inputs = source_inventory(); results = {}; records = []
    status = {'validation': 'running', 'source_sha256': inputs, 'flags': flags,
              'variant_defines': VARIANTS, 'compiler': compiler, 'sdk': sdk, 'variants': results, 'commands': records}
    try:
        for variant in variant_names:
            folder = out/variant; folder.mkdir(); objects = []
            for i, source in enumerate(SOURCES+['benchmark/scaling_investigation/diagnostic.cpp']):
                recheck(inputs); obj = folder/(Path(source).stem+'.o'); objects.append(str(obj))
                command = ['/usr/bin/arch', '-arm64', '/usr/bin/clang++']+flags+VARIANTS[variant]+['-c', str(ROOT/source), '-o', str(obj)]
                records.append(run_owned(command, folder, 'compile-'+str(i), timeout=180, rss_cap=4*1024**3))
            binary = folder/'diagnostic'; recheck(inputs)
            command = ['/usr/bin/arch', '-arm64', '/usr/bin/clang++', '-isysroot', sdk,
                       '-L'+sdk+'/usr/lib']+objects+['-Wl,-stack_size,0x20000000', '-o', str(binary)]
            records.append(run_owned(command, folder, 'link', timeout=60))
            results[variant] = {'binary': str(binary), 'sha256': sha(binary), 'profile': binary_profile(binary),
                                'objects': {str(Path(o).relative_to(out)): sha(o) for o in objects}}
        recheck(inputs); status['validation'] = 'pass'
    except BaseException as error:
        status['validation'] = 'failed'; status['error'] = repr(error); raise
    finally: write(out/'build.json', status)
    print(json.dumps({'build': 'pass', 'variants': list(results), 'directory': str(out)}), flush=True)


def matrix(mode):
    sizes = [1024, 4096, 16384, 65536, 262144, 1048576]
    graphs = [19000013, 19000043]; seeds = [3001, 3011]
    if mode == 'smoke': sizes = [1024]; graphs = graphs[:1]; seeds = seeds[:1]
    if mode == 'allocation': sizes = [16384, 262144, 1048576]; seeds = seeds[:1]
    if mode == 'calibration': sizes = [1024, 1048576]; seeds = seeds[:1]; graphs = graphs[:1]
    return [{'family': f, 'n': n, 'graph_seed': g, 'sampling_seed': s}
            for gi, g in enumerate(graphs) for n in (sizes if gi == 0 else list(reversed(sizes)))
            for f in ['leaf_hierarchy4', 'leaf_shuffled4', 'gnm_random'] for s in seeds]


def work_fields():
    fields = re.findall(r'\{"([a-z_0-9]+)",\s*&kkt_work::WorkStats::([a-z_0-9]+),\s*(true|false)\}',
                        (ROOT/'benchmark/work_metrics.hpp').read_text())
    require(len(fields) == len({x[0] for x in fields}) == 65 and all(x[0] == x[1] for x in fields), 'work schema drift')
    return {name: proxy == 'true' for name, member, proxy in fields}


def historical_inputs():
    require(sha(GOOGLE_CAPTURE) == GOOGLE_SHA, 'completed Google capture changed')
    info = strict_json(GOOGLE_CAPTURE.read_text()); result = {}
    require(info['validation'] == 'pass' and len(info['captures']) == 24, 'incomplete historical capture')
    for child in info['captures']:
        for item in child['certificates']:
            if item['algorithm'] != 'kkt': continue
            key = tuple(item[k] for k in ('family', 'n', 'graph_seed', 'sampling_seed'))
            value = tuple(item[k] for k in ('m', 'input_fingerprint', 'topology_fingerprint'))
            require(key not in result or result[key] == value, 'historical fingerprint disagreement'); result[key] = value
    require(len(result) == 132 and sha(GOOGLE_CAPTURE) == GOOGLE_SHA, 'historical input matrix drift')
    return result


def validate_rows(rows, case, variant, repetitions, fields, expected):
    require(len(rows) == repetitions+1, 'missing/extra diagnostic rows')
    for rep, row in enumerate(rows):
        require(type(row) is dict and set(row) == ROW_FIELDS, 'diagnostic row schema')
        require(row['schema'] == 'kkt_scaling_diagnostic_v1' and row['validation'] == 'pass', 'invalid row status')
        require(type(row['family']) is str and row['family'] == case['family'], 'wrong family')
        for key in ('n', 'graph_seed', 'sampling_seed'):
            require(type(row[key]) is int and row[key] == case[key], 'wrong typed input identity')
        for key in ROW_FIELDS-{'schema', 'family', 'warmup', 'phases', 'work', 'validation'}:
            require(uint(row[key]), 'invalid integer field: '+key)
        require(row['repetition'] == rep and type(row['warmup']) is bool and row['warmup'] == (rep == 0), 'wrong repetition/warmup')
        require(tuple(row[k] for k in ('m', 'input_fingerprint', 'topology_fingerprint')) == expected, 'Google fixture mismatch')
        require(row['wall_ns'] > 0 and row['cpu_ns'] > 0, 'nonpositive clock')
        # UTC reversal is retained as a descriptive flag; it never alters native intervals.
        require(type(row['work']) is dict and set(row['work']) == set(fields) and all(uint(x) for x in row['work'].values()), 'work field schema')
        require(row['work_proxy'] == sum(row['work'][name] for name, contributes in fields.items() if contributes), 'work proxy mismatch')
        require(type(row['phases']) is dict and set(row['phases']) == set(PHASES), 'phase name schema')
        for entry in row['phases'].values():
            require(type(entry) is dict and set(entry) == set(PHASE_FIELDS) and all(uint(x) for x in entry.values()), 'phase field schema')
        require(sum(x['wall_ns'] for x in row['phases'].values()) == row['phase_total_ns'] <= row['wall_ns'], 'exclusive phase mismatch')
        require(row['returned_live_usable_bytes'] <= row['peak_live_usable_bytes'], 'invalid live-byte bounds')
        if variant in ('reference', 'work'):
            require(not any(value for entry in row['phases'].values() for value in entry.values()) and row['peak_live_usable_bytes'] == row['returned_live_usable_bytes'] == 0, 'unexpected phase instrumentation')
        else: require(row['phase_total_ns'] > 0 and row['phases']['contraction']['calls'] > 0, 'missing linked phase instrumentation')
        if variant != 'allocation':
            require(not any(entry[name] for entry in row['phases'].values() for name in PHASE_FIELDS[2:]), 'unexpected allocation instrumentation')
        else:
            allocated = sum(x['usable_bytes'] for x in row['phases'].values())
            freed = sum(x['freed_usable_bytes'] for x in row['phases'].values())
            require(allocated > 0 and allocated-freed == row['returned_live_usable_bytes'] > 0, 'allocation conservation failed')
        w = row['work']
        if variant != 'work': require(not any(w.values()), 'unexpected work instrumentation')
        else:
            require(w == rows[0]['work'], 'nonreproducible counters')
            require(w['kkt_calls'] > 0 and w['hash_insert_items'] == row['n']-1 and w['hash_lookup_calls'] == 0, 'wrong linked KKT counters')
            require(w['sampled_edges']+w['filtered_edges'] <= w['sampling_edge_visits']+w['verifier_forest_edges'], 'sample/filter bound')
            require(w['kkt_vertices'] <= 2*row['n'] and w['current_depth'] == 0, 'vertex/depth bound')
            require(w['path_binary_search_steps'] <= 4*w['fbt_input_vertices']+3*w['verifier_queries'], 'path search bound')
            require(w['contraction_edge_visits'] <= 3*w['contraction_edges'], 'retained contraction bound')
            require(0 <= w['path_query_visits']-2*w['verifier_queries'] <= w['verifier_queries'], 'compressed-query bound')
    return rows


def capture(out, build_dir, mode):
    out.mkdir(parents=True, exist_ok=False)
    build_path = build_dir/'build.json'; build_digest = sha(build_path); record = strict_json(build_path.read_text())
    require(record['validation'] == 'pass' and sha(build_path) == build_digest, 'invalid build record')
    bound = {build_path: build_digest, **record['source_sha256'], GOOGLE_CAPTURE: GOOGLE_SHA}
    for value in record['variants'].values():
        bound[Path(value['binary'])] = value['sha256']
        for name, digest in value['objects'].items(): bound[build_dir/name] = digest
    recheck(bound); historical = historical_inputs(); fields = work_fields()
    variants = list(VARIANTS) if mode == 'smoke' else ['reference', 'phase'] if mode == 'calibration' else [mode]
    cases = matrix(mode); repetitions = 1 if mode in ('smoke', 'allocation', 'work') else 3
    declaration = {'schema': 'kkt_scaling_capture_v1', 'mode': mode, 'cases': cases, 'variants': variants,
                   'repetitions': repetitions, 'warmups': 1, 'build_sha256': build_digest,
                   'global_limit_seconds': 7200, 'child_limit_seconds': 300, 'rss_limit_bytes': 12*1024**3,
                   'timing_claim': 'phase/allocation/work builds are diagnostic; only reference is uninstrumented'}
    write(out/'declaration.json', declaration); bound[out/'declaration.json'] = sha(out/'declaration.json')
    started = time.monotonic_ns(); captures = []
    status = {'validation': 'running', 'captures': captures, 'bound_sha256': {str(p): h for p, h in bound.items()}}
    try:
        for index, case in enumerate(cases):
            expected = historical[tuple(case[k] for k in ('family', 'n', 'graph_seed', 'sampling_seed'))]
            for variant in (variants if index % 2 == 0 else list(reversed(variants))):
                remaining = 7200-(time.monotonic_ns()-started)/1e9
                require(remaining > 0, 'global capture deadline'); recheck(bound)
                binary = Path(record['variants'][variant]['binary']); label = f'{index:03d}-{variant}'
                receipt = run_owned(['/usr/bin/arch', '-arm64', str(binary), case['family'], str(case['n']), str(case['graph_seed']), str(case['sampling_seed']), str(repetitions)], out, label, timeout=min(300, remaining))
                require(time.monotonic_ns()-started <= 7200*1e9, 'global capture deadline')
                raw = out/(label+'.stdout'); digest = sha(raw)
                rows = validate_rows([strict_json(line) for line in raw.read_text().splitlines()], case, variant, repetitions, fields, expected)
                require(sha(raw) == digest, 'raw changed during validation')
                for suffix in ('.stdout', '.stderr', '.json'):
                    path = out/(label+suffix); bound[path] = sha(path)
                captures.append({'case': case, 'variant': variant, 'label': label, 'rows': len(rows),
                                 'stdout_sha256': digest, 'receipt_sha256': bound[out/(label+'.json')],
                                 'utc_reversals': sum(row['utc_end_ns'] < row['utc_start_ns'] for row in rows)})
                write(out/'progress.json', {'completed': captures, 'validation': 'in_progress'})
                print(json.dumps({'completed': len(captures), 'total': len(cases)*len(variants), 'case': case, 'variant': variant}), flush=True)
        require(len(captures) == len(cases)*len(variants), 'incomplete capture')
        recheck(bound); require(time.monotonic_ns()-started <= 7200*1e9, 'global capture deadline')
        status['validation'] = 'pass'
    except BaseException as error:
        status.update(validation='failed', error=repr(error)); raise
    finally:
        status.update(duration_s=(time.monotonic_ns()-started)/1e9, bound_sha256={str(p): h for p, h in bound.items()},
                      native_process_may_still_be_running=_launch_blocked)
        write(out/'capture.json', status)


def main():
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest='action', required=True)
    b = sub.add_parser('build'); b.add_argument('output', type=Path); b.add_argument('--variants', nargs='+', choices=list(VARIANTS), default=list(VARIANTS))
    c = sub.add_parser('capture'); c.add_argument('output', type=Path); c.add_argument('--build', required=True, type=Path); c.add_argument('--mode', choices=['smoke', 'phase', 'work', 'allocation', 'calibration'], required=True)
    args = parser.parse_args()
    previous = signal.getsignal(signal.SIGTERM)
    def terminated(signum, frame): raise KeyboardInterrupt('diagnostic controller received SIGTERM')
    signal.signal(signal.SIGTERM, terminated)
    try:
        if args.action == 'build': build(args.output.resolve(), args.variants)
        else: capture(args.output.resolve(), args.build.resolve(), args.mode)
    finally: signal.signal(signal.SIGTERM, previous)

if __name__ == '__main__': main()
