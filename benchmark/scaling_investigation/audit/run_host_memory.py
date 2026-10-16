#!/usr/bin/env python3
"""Standalone host calibration; assembly review is required before execution."""
import argparse
import importlib.util
from pathlib import Path
import signal

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('host_memory_proof', HERE.parent/'candidates/run_candidate.py')
proof = importlib.util.module_from_spec(spec); spec.loader.exec_module(proof); base = proof.base
SOURCE, COMPILER = HERE/'host_memory.cpp', Path('/usr/bin/clang++')
SIZES = (16384, 65536, 262144, 1048576, 4194304, 16777216, 67108864)
VISITS, SEED, CAP = 16777224, 0x31415926, 1024**3
FIELDS = set('schema size_order mode chains bytes indices seed fingerprint repetition warmup logical_loads rounds wall_ns process_cpu_start_ns process_cpu_end_ns cpu_ns checksum positions validation'.split())


def bind(bound, path):
    path = str(Path(path).resolve()); digest = base.sha(path)
    base.require(path not in bound or bound[path] == digest, 'conflicting artifact digest')
    bound[path] = digest


def initial():
    bound = {}
    for p in [SOURCE, Path(__file__), Path(proof.__file__), Path(base.__file__), Path(base.monitor.__file__),
              *map(Path, base.monitor.capture.helpers())]: bind(bound, p)
    return bound


def command(argv, output, label, state):
    base.recheck(state['bound_sha256'])
    receipt = base.run_owned(argv, output, label, timeout=300, rss_cap=CAP)
    state['commands'].append(receipt)
    base.require(proof.check_receipt(output/(label+'.json'), argv, state['bound_sha256']) == receipt, 'receipt mismatch')
    for suffix in ('.json', '.stdout', '.stderr'): bind(state['bound_sha256'], output/(label+suffix))
    base.recheck(state['bound_sha256'])
    return (output/(label+'.stdout')).read_text()


def recipe(output, sdk):
    binary = output/'host_memory'
    return [('sdk', ['/usr/bin/xcrun', '--show-sdk-path']),
        ('compiler', ['/usr/bin/arch', '-arm64', str(COMPILER), '--version']),
        ('compile', ['/usr/bin/arch', '-arm64', str(COMPILER), '-std=c++17', '-O3', '-march=native',
             '-Wall', '-Wextra', '-isysroot', str(sdk), '-L'+str(sdk/'usr/lib'), str(SOURCE),
             '-Wl,-stack_size,0x20000000', '-o', str(binary)]),
        ('profile', ['/usr/bin/file', '-b', str(binary)]), ('load-commands', ['/usr/bin/otool', '-l', str(binary)]),
        ('symbols', ['/usr/bin/nm', '-C', str(binary)]), ('assembly', ['/usr/bin/otool', '-tvV', str(binary)])]

def metadata(label, value, sdk):
    if label == 'sdk': base.require(Path(value.strip()).resolve() == sdk, 'selected SDK mismatch')
    if label == 'compiler': base.require('Apple clang' in value and 'arm64' in value, 'non-native Apple compiler')
    if label == 'profile': base.require(value.strip() == 'Mach-O 64-bit executable arm64', 'non-native executable')
    if label == 'load-commands': base.require(base.re.findall(r'\bcmd LC_MAIN\b(?:(?!Load command).)*?\bstacksize (\d+)', value, base.re.S) == ['536870912'], 'wrong stack profile')

def build(args, state):
    output, bound = args.output, state['bound_sha256']; sdk = args.sdk.resolve(); binary = output/'host_memory'
    bind(bound, COMPILER); bind(bound, sdk/'SDKSettings.json'); texts = {}
    for label, argv in recipe(output, sdk):
        texts[label] = command(argv, output, label, state); metadata(label, texts[label], sdk)
        if label == 'compile': bind(bound, binary)
    state.update(binary=str(binary), binary_sha256=base.sha(binary), source_sha256=base.sha(SOURCE),
                 compiler=texts['compiler'], compiler_sha256=base.sha(COMPILER), sdk=str(sdk),
                 sdk_settings_sha256=base.sha(sdk/'SDKSettings.json'), assembly_review_pending=True)


def rows(text, order):
    values = [base.strict_json(line) for line in text.splitlines()]
    sizes = SIZES if order == 'ascending' else tuple(reversed(SIZES))
    expected = [(size, rep, (slot+rep)%4) for size in sizes for rep in range(4) for slot in range(4)]
    base.require(len(values) == 112, 'incomplete native matrix')
    previous_cpu = 0
    for row, (size, rep, mode) in zip(values, expected):
        chains = (1, 4, 8, 0)[mode]; n = size//4
        base.require(type(row) is dict and set(row) == FIELDS, 'unexpected row schema')
        fixed = dict(schema='host_memory_calibration_v1', size_order=order, mode='scan' if mode == 3 else 'chase',
                     chains=chains, bytes=size, indices=n, seed=SEED, repetition=rep, warmup=rep == 0,
                     logical_loads=VISITS, rounds=VISITS//chains if chains else VISITS, validation='pass')
        base.require(all(type(row[k]) is type(v) and row[k] == v for k, v in fixed.items()), 'identity/count mismatch')
        for key in ('fingerprint', 'wall_ns', 'process_cpu_start_ns', 'process_cpu_end_ns', 'cpu_ns', 'checksum'):
            base.require(base.uint(row[key]), 'invalid numeric domain')
        base.require(row['wall_ns'] > 0 and row['cpu_ns'] > 0 and row['process_cpu_start_ns'] >= previous_cpu
                     and row['cpu_ns'] == row['process_cpu_end_ns']-row['process_cpu_start_ns'], 'invalid clocks')
        previous_cpu = row['process_cpu_end_ns']
        p = row['positions']
        base.require(type(p) is list and len(p) == 8 and all(base.uint(v) and v < n for v in p), 'invalid positions')
        base.require(all(v == 0 for v in p[chains:]), 'unused position changed')
        base.require(mode == 3 or row['checksum'] == 0, 'unexpected chase checksum')
    return values


def run(args, state):
    base.require(args.assembly_reviewed, 'root must inspect the archived assembly first')
    bind(state['bound_sha256'], args.build)
    record = base.strict_json(args.build.read_text())
    sdk = Path(record['sdk']); binary = args.build.parent/'host_memory'; required = set(initial())
    required.update(str(p.resolve()) for p in (COMPILER, sdk/'SDKSettings.json', binary))
    base.require(sdk.is_absolute() and sdk == sdk.resolve() and record['binary'] == str(binary), 'noncanonical build paths')
    base.require(record['schema'] == 'host_memory_build_v1' and record['validation'] == 'pass'
                 and record['native_process_may_still_be_running'] is False
                 and len(record['commands']) == 7 and all(type(c['deadline_seconds']) is int and c['deadline_seconds'] == 300
                     and type(c['rss_limit_bytes']) is int and c['rss_limit_bytes'] == CAP for c in record['commands']), 'invalid build')
    for (label, argv), receipt in zip(recipe(args.build.parent, sdk), record['commands']):
        path = args.build.parent/(label+'.json')
        required.update(str(args.build.parent/(label+s)) for s in ('.json', '.stdout', '.stderr'))
        base.require(proof.check_receipt(path, argv, state['bound_sha256']) == receipt, 'receipt mismatch')
        for suffix, field in (('.stdout', 'stdout_sha256'), ('.stderr', 'stderr_sha256')):
            base.require(base.sha(args.build.parent/(label+suffix)) == receipt[field], 'receipt log drift')
        metadata(label, (args.build.parent/(label+'.stdout')).read_text(), sdk)
    base.require(required <= set(record['bound_sha256']), 'omitted build binding'); base.recheck(record['bound_sha256'])
    for p in record['bound_sha256']: bind(state['bound_sha256'], p)
    for key, path in (('binary_sha256', binary), ('source_sha256', SOURCE), ('compiler_sha256', COMPILER), ('sdk_settings_sha256', sdk/'SDKSettings.json')):
        base.require(base.sha(path) == record[key], 'build metadata drift')
    base.require(record['compiler'] == (args.build.parent/'compiler.stdout').read_text(), 'compiler version drift')
    values = []
    for order in ('ascending', 'descending'):
        text = command(['/usr/bin/arch', '-arm64', str(binary), order], args.output, order, state)
        values.extend(rows(text, order))
    for size in SIZES:
        group = [row for row in values if row['bytes'] == size]
        base.require(len({row['fingerprint'] for row in group}) == 1, 'input fingerprints differ')
        for chains in (1, 4, 8, 0): base.require(len({(tuple(r['positions']), r['checksum']) for r in group if r['chains'] == chains}) == 1, 'replay result differs')
    state.update(build_record=str(args.build), assembly_review_acknowledged=True,
                 checked_rows=len(values), measured_rows=sum(not r['warmup'] for r in values), warmup_rows=56)


def main():
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('build'); p.add_argument('output', type=Path); p.add_argument('--sdk', type=Path, required=True)
    p = sub.add_parser('run'); p.add_argument('output', type=Path); p.add_argument('--build', type=Path, required=True)
    p.add_argument('--assembly-reviewed', action='store_true')
    args = parser.parse_args(); args.output = args.output.resolve(); args.output.mkdir(parents=True, exist_ok=False)
    if args.action == 'run': args.build = args.build.resolve()
    state = dict(schema='host_memory_'+args.action+'_v1', validation='running', commands=[], bound_sha256={})
    try:
        state['bound_sha256'] = initial()
        (build if args.action == 'build' else run)(args, state)
        base.recheck(state['bound_sha256']); state['validation'] = 'pass'
    except BaseException as error:
        state.update(validation='failed', error=repr(error)); raise
    finally:
        state['native_process_may_still_be_running'] = base._launch_blocked
        base.write(args.output/'attempt.json', state)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda signum, frame: (_ for _ in ()).throw(KeyboardInterrupt('host calibration terminated')))
    main()
