#!/usr/bin/env python3
"""Bounded native and sanitizer correctness gates for the depth-query candidate."""
import argparse
from contextlib import contextmanager
import importlib.util
import os
from pathlib import Path
import re
import signal
import time

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('depth_correctness_candidate', HERE/'run_candidate.py')
candidate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(candidate)
base, ROOT = candidate.base, candidate.ROOT
require, sha, write = base.require, base.sha, base.write
ARCH = ['/usr/bin/arch', '-arm64']
NATIVE = '/usr/bin/clang++'
SANITIZER = '/opt/homebrew/opt/llvm/bin/clang++'
RENAMES = ['-D'+name+'=depth_'+name for name in
           ('heavy_edge_marks', 'verify_mst', 'verify_general_graph', 'fbt_reduction')]
DEPTH = ['-DKKT_EXPERIMENT_DEPTH_QUERIES']
WORK = ['-DKKT_ENABLE_WORK_STATS']
SAN_FLAGS = ['-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-fno-omit-frame-pointer']
SAN_ENV = {'ASAN_OPTIONS': 'detect_leaks=0:halt_on_error=1:abort_on_error=1',
           'UBSAN_OPTIONS': 'halt_on_error=1:print_stacktrace=1'}
SUITES = ('edge_verifier_view_test', 'retention_control_test')
# The two explicit gnm_random fixtures report their deterministic topology attempts.
RETENTION_STDERR = 'crossover_topology_attempts=1\ncrossover_topology_attempts=1\n'
WRONG_MESSAGE = 'depth dispatch / exact removed-height initialization mismatch\n'
GUARDS = ('guard-add-negative', 'guard-add-equal', 'guard-add-deeper', 'guard-lookup-absent')


@contextmanager
def sanitizer_environment(enabled):
    previous = {name: os.environ.get(name) for name in SAN_ENV}
    try:
        for name, value in SAN_ENV.items():
            if enabled: os.environ[name] = value
            else: os.environ.pop(name, None)
        yield previous
    finally:
        for name, value in previous.items():
            if value is None: os.environ.pop(name, None)
            else: os.environ[name] = value


def validate_child(receipt, command, expected_exit, timeout, rss_cap):
    require(receipt['command'] == command and receipt['cwd'] == str(ROOT), 'child command/cwd mismatch')
    require(type(receipt['exit_code']) is int and receipt['exit_code'] == expected_exit, 'unexpected exact child exit')
    require(receipt['validation'] == ('pass' if expected_exit == 0 else 'failed'), 'unexpected child status')
    if expected_exit:
        require(receipt.get('error') == "RuntimeError('nonzero native exit')", 'unrelated failure in expected-negative child')
    require(receipt['group_empty'] is True and receipt['native_process_may_still_be_running'] is False,
            'child group exit unknown')
    require(type(receipt['pgid']) is int and receipt['pgid'] > 0, 'invalid owned group')
    require(receipt['deadline_seconds'] == timeout and receipt['rss_limit_bytes'] == rss_cap, 'child limits changed')
    start, exited, finished = [receipt[k] for k in ('started_monotonic_ns', 'exit_monotonic_ns', 'finished_monotonic_ns')]
    require(all(base.uint(x) for x in (start, exited, finished)) and start <= exited <= finished
            and exited-start <= timeout*10**9, 'child deadline/interval failure')
    cleanup = receipt['cleanup']
    require(cleanup['native_exit_known'] is True and cleanup['group_exit_known'] is True
            and cleanup['native_process_may_still_be_running'] is False
            and type(cleanup['returncode']) is int and cleanup['returncode'] == expected_exit
            and cleanup['process_group'] == receipt['pgid'], 'child cleanup identity failure')
    require(cleanup['group_verification']['validation'] == 'pass'
            and cleanup['group_verification']['members'] == [], 'nonempty final child group')
    unavailable = 0
    for observation in receipt['observations']:
        require(observation['validation'] in ('pass', 'unavailable'), 'poisoned child resources')
        unavailable = unavailable+1 if observation['validation'] == 'unavailable' else 0
        require(unavailable < 3, 'unavailable child resources')
        if observation['validation'] == 'pass':
            require(base.uint(observation['rss_kib']) and observation['rss_kib']*1024 <= rss_cap,
                    'child resource ceiling')


class Gate:
    def __init__(self, output, build_path):
        self.output, self.build_path = output, build_path
        self.build, self.bound = candidate.check_build(build_path)
        for source in (Path(__file__), *(ROOT/'test'/(name+'.cpp') for name in SUITES)):
            candidate.add(self.bound, source)
        # The included harness source is not a top-level production source.
        candidate.add(self.bound, ROOT/'benchmark/retention_control.cpp')
        for compiler in (NATIVE, SANITIZER):
            require(Path(compiler).is_file(), 'missing required compiler: '+compiler)
            candidate.add(self.bound, compiler)
        self.commands = []
        self.started = time.monotonic_ns()

    def child(self, directory, label, command, *, expected_exit=0, timeout=300, rss_cap=12*1024**3):
        base.recheck(self.bound)
        require(time.monotonic_ns()-self.started < 3600*10**9, 'correctness campaign ceiling')
        caught = None
        try:
            base.run_owned(command, directory, label, timeout=timeout, rss_cap=rss_cap)
        except RuntimeError as error:
            caught = error
            if expected_exit == 0: raise
        # Interruptions, missing receipts, poison and unrelated errors never qualify.
        require(not base._launch_blocked and not base.sampler().poisoned, 'unsafe continuation after child')
        require((caught is not None) == (expected_exit != 0), 'expected-negative execution contract')
        receipt_path = directory/(label+'.json')
        receipt, digest = candidate.read(receipt_path)
        validate_child(receipt, command, expected_exit, timeout, rss_cap)
        candidate.add(self.bound, receipt_path, digest)
        values = []
        for suffix, key in (('.stdout', 'stdout_sha256'), ('.stderr', 'stderr_sha256')):
            path = directory/(label+suffix)
            candidate.add(self.bound, path, receipt[key])
            values.append(path.read_text())
        base.recheck(self.bound)
        self.commands.append(dict(receipt=str(receipt_path), command=command, expected_exit=expected_exit,
                                  validation='pass', timeout=timeout, rss_cap=rss_cap))
        return tuple(values)

    def compile(self, folder, compiler, flags, label, source, macros=()):
        obj = folder/(label+'.o')
        self.child(folder, 'compile-'+label, ARCH+[compiler]+flags+list(macros)+['-c', str(source), '-o', str(obj)],
                   timeout=180, rss_cap=4*1024**3)
        candidate.add(self.bound, obj)
        return obj

    def link(self, folder, compiler, label, objects, sanitizer=False):
        binary = folder/label
        sdk = self.build['sdk']
        command = ARCH+[compiler, '-isysroot', sdk, '-L'+sdk+'/usr/lib']
        command += (SAN_FLAGS if sanitizer else [])+list(map(str, objects))
        command += ['-Wl,-stack_size,0x20000000', '-o', str(binary)]
        self.child(folder, 'link-'+label, command, timeout=60)
        candidate.add(self.bound, binary)
        description, _ = self.child(folder, 'file-'+label, ['/usr/bin/file', '-b', str(binary)], timeout=30)
        require(description.strip() == 'Mach-O 64-bit executable arm64', 'non-native correctness binary')
        loads, _ = self.child(folder, 'loads-'+label, ['/usr/bin/otool', '-l', str(binary)], timeout=30)
        stacks = re.findall(r'\bcmd LC_MAIN\b(?:(?!Load command).)*?\bstacksize (\d+)', loads, re.S)
        require(stacks == ['536870912'], 'missing/duplicate 512 MiB stack')
        return binary

    def symbols(self, folder, label, obj, renamed):
        output, _ = self.child(folder, 'symbols-'+label, ['/usr/bin/nm', '-gU', '-C', str(obj)], timeout=30)
        for name in ('heavy_edge_marks', 'verify_mst', 'verify_general_graph', 'fbt_reduction'):
            require(bool(re.search(r'(?<![\w])'+('depth_' if renamed else '')+name+r'\(', output)),
                    'missing defined verifier symbol: '+name)
            require(not re.search(r'(?<![\w])'+('' if renamed else 'depth_')+name+r'\(', output),
                    'unisolated verifier symbol: '+name)


def check_focused(stdout, stderr):
    match = re.fullmatch(r'depth_queries_test pass trees=(\d+) query_pairs=(\d+) marks=(\d+) dispatch_cases=(\d+)\n', stdout)
    require(match is not None and stderr == '', 'focused positive output mismatch')
    trees, queries, marks, dispatch = map(int, match.groups())
    sizes = (1,2,3,4,7,8,9,15,16,17,31,32,33,63,64,65,127,128,129,257,513)
    require(trees == 164 and queries == sum(n*n*(8 if n <= 129 else 6) for n in sizes)
            and marks == 317 and dispatch > 0, 'focused coverage mismatch')


def check_suite(name, stdout, stderr):
    if name == 'retention_control_test':
        match = re.fullmatch(r'PASS simple_cases=(\d+) solver_outputs=(\d+) raw_cases=(\d+) exhaustive_cases=(\d+) rejected_trees=(\d+) rejected_options=(\d+)\n', stdout)
        require(match is not None and stderr == RETENTION_STDERR
                and tuple(map(int,match.groups())) == (28,819,35,35,140,10),
                'retention suite did not complete')
    else:
        match = re.fullmatch(r'PASS (\d+) positional oracle cases; (\d+) independently checked full KKT records\n', stderr)
        require(match is not None and tuple(map(int,match.groups())) == (1248,1344), 'edge/full-KKT suite did not complete')
        rows = [base.strict_json(line) for line in stdout.splitlines()]
        require(len(rows) == int(match[2]), 'missing full-KKT records')
        expected = [(fixture,order,seed) for fixture in range(56) for order in range(3)
                    for seed in (0,1,2,17,401,809,65537,2**32-1)]
        for row, key in zip(rows, expected):
            require(set(row) == {'fixture','order','seed','fingerprint','ids','stats'}, 'full-KKT row schema')
            require(all(type(row[k]) is int for k in ('fixture','order','seed'))
                    and tuple(row[k] for k in ('fixture','order','seed')) == key, 'full-KKT identity/order mismatch')
            require(base.uint(row['fingerprint']) and type(row['ids']) is list
                    and all(type(x) is int and -2**31 <= x < 2**31 for x in row['ids'])
                    and row['ids'] == sorted(set(row['ids'])), 'full-KKT fingerprint/IDs invalid')
            require(set(row['stats']) == set(base.work_fields()) and all(base.uint(x) for x in row['stats'].values()),
                    'full-KKT counter schema')


def run(output, build_path):
    output.mkdir(parents=True, exist_ok=False)
    status = dict(schema='kkt_depth_correctness_gate_v1', validation='running', native_pass=False,
                  sanitizers_pass=False, owned_groups_empty=False, native_process_may_still_be_running=True)
    gate = None
    try:
        gate = Gate(output, build_path)
        status.update(source_sha256=gate.build['source_sha256'], build_record=str(build_path),
                      build_record_sha256=sha(build_path), compiler_paths={'native':NATIVE,'sanitizer':SANITIZER},
                      sdk=gate.build['sdk'], sanitizer_options=SAN_ENV,
                      coverage={'focused_profiles':['native','sanitizer'], 'full_solver_suites':list(SUITES),
                                'native_assertion_modes':list(GUARDS), 'wrong_dispatch':'native',
                                'noinline_attribute_tested':False, 'leak_detection':False,
                                'suite_instrumentation':{'edge_verifier_view_test':'work',
                                                         'retention_control_test':'none'}}, commands=gate.commands)
        baseline_outputs = {}
        for profile, compiler in (('native',NATIVE), ('sanitizer',SANITIZER)):
            folder = output/profile; folder.mkdir()
            sanitized = profile == 'sanitizer'
            with sanitizer_environment(sanitized) as previous:
                status.setdefault('previous_sanitizer_environment', {})[profile] = previous
                version, _ = gate.child(folder, 'compiler-version', ARCH+[compiler, '--version'], timeout=30)
                if sanitized:
                    require('clang version' in version and 'Target: arm64-' in version and 'Apple clang' not in version,
                            'unexpected sanitizer toolchain')
                else:
                    require(version == gate.build['compiler'], 'native compiler differs from candidate build')
                    sdk, _ = gate.child(folder, 'sdk', ARCH+['/usr/bin/xcrun','--show-sdk-path'], timeout=30)
                    require(sdk.strip() == gate.build['sdk'], 'SDK drift')
                status.setdefault('compiler_versions', {})[profile] = version
                flags = list(base.BASE_FLAGS)
                if sanitized:
                    flags[flags.index('-O3')] = '-O1'
                    flags += ['-g']+SAN_FLAGS
                flags += ['-isysroot',gate.build['sdk']]+WORK
                lca = gate.compile(folder,compiler,flags,'lca',ROOT/'lca/lca.cpp')
                reference = gate.compile(folder,compiler,flags,'reference-verifier',ROOT/'verifier/verifier_v2.cpp')
                depth = gate.compile(folder,compiler,flags,'depth-renamed-verifier',ROOT/'verifier/verifier_v2.cpp',DEPTH+RENAMES)
                focused_main = gate.compile(folder,compiler,flags,'depth-test',HERE/'depth_queries_test.cpp',DEPTH)
                gate.symbols(folder,'reference',reference,False); gate.symbols(folder,'depth',depth,True)
                focused = gate.link(folder,compiler,'depth-test',[lca,reference,depth,focused_main],sanitized)
                focused_output = gate.child(folder,'positive-depth',ARCH+[str(focused)])
                check_focused(*focused_output)
                if not sanitized:
                    for mode in GUARDS:
                        stdout, stderr = gate.child(folder,mode,ARCH+[str(focused),mode],expected_exit=-signal.SIGABRT)
                        expression, function = (('(mask & requested_bit) != 0','rank') if mode=='guard-lookup-absent'
                                                else ('upper_depth >= 0 && upper_depth < depth_[lower]','add_request_depth'))
                        require(stdout == '' and 'Assertion failed:' in stderr and expression in stderr
                                and function in stderr and 'experimental_compressed_queries.hpp' in stderr,
                                'wrong assertion diagnostic')
                    wrong_obj = gate.compile(folder,compiler,flags,'wrong-reference-verifier',ROOT/'verifier/verifier_v2.cpp',RENAMES)
                    gate.symbols(folder,'wrong-reference',wrong_obj,True)
                    wrong = gate.link(folder,compiler,'wrong-dispatch',[lca,reference,wrong_obj,focused_main])
                    stdout, stderr = gate.child(folder,'negative-dispatch',ARCH+[str(wrong)],expected_exit=1)
                    require(stdout == '' and stderr == WRONG_MESSAGE, 'wrong dispatch failed for unrelated reason')
                    production = [build_path.parent/'depth-work'/(Path(source).stem+'.o') for source in base.SOURCES]
                    declared = gate.build['variants']['depth-work']['objects']
                    for obj in production:
                        require(declared[str(obj.relative_to(build_path.parent))] == sha(obj), 'production object drift')
                else:
                    production = []
                    for source in base.SOURCES:
                        production.append(lca if source=='lca/lca.cpp' else
                            gate.compile(folder,compiler,flags,'production-'+Path(source).stem,ROOT/source,DEPTH))
                for name in SUITES:
                    suite_flags, suite_objects = flags, production
                    if name == 'retention_control_test':
                        # This suite includes the timing-only harness. Its whole
                        # link, not just its main, must have work counters off.
                        suite_flags = [flag for flag in flags if flag not in WORK]
                        if sanitized:
                            suite_objects = [gate.compile(folder,compiler,suite_flags,
                                'timing-production-'+Path(source).stem,ROOT/source,DEPTH)
                                for source in base.SOURCES]
                        else:
                            suite_objects = [build_path.parent/'depth-reference'/(Path(source).stem+'.o')
                                             for source in base.SOURCES]
                            declared = gate.build['variants']['depth-reference']['objects']
                            for obj in suite_objects:
                                require(declared[str(obj.relative_to(build_path.parent))] == sha(obj),
                                        'uninstrumented production object drift')
                    main = gate.compile(folder,compiler,suite_flags,name+'-main',ROOT/'test'/(name+'.cpp'),DEPTH)
                    binary = gate.link(folder,compiler,name,[*suite_objects,main],sanitized)
                    result = gate.child(folder,'positive-'+name,ARCH+[str(binary)])
                    check_suite(name,*result)
                    if sanitized: require(result == baseline_outputs[name], 'native/sanitizer suite records differ')
                    else: baseline_outputs[name] = result
                if sanitized: require(focused_output == baseline_outputs['focused'], 'focused native/sanitizer coverage differs')
                else: baseline_outputs['focused'] = focused_output
                status[profile+'_pass' if not sanitized else 'sanitizers_pass'] = True
        base.recheck(gate.bound)
        require(time.monotonic_ns()-gate.started <= 3600*10**9, 'correctness campaign ceiling')
        require(not base._launch_blocked and not base.sampler().poisoned, 'unknown process state')
        status.update(validation='pass', owned_groups_empty=True, native_process_may_still_be_running=False)
    except BaseException as error:
        status.update(validation='failed', error=repr(error))
        raise
    finally:
        if gate is not None:
            status.update(bound_sha256=gate.bound, commands=gate.commands,
                          duration_s=(time.monotonic_ns()-gate.started)/1e9)
        write(output/'gate.json',status)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('output',type=Path)
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--released',action='store_true')
    args=parser.parse_args()
    require(args.released, 'correctness requires explicit root release')
    previous=signal.getsignal(signal.SIGTERM)
    def stopped(signum, frame): raise KeyboardInterrupt('correctness controller received SIGTERM')
    signal.signal(signal.SIGTERM,stopped)
    try: run(args.output.resolve(),args.build.resolve())
    finally: signal.signal(signal.SIGTERM,previous)


if __name__=='__main__': main()
