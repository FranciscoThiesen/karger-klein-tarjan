#!/usr/bin/env python3
"""Prepared correctness/build recipe; copy to an authorized worktree's benchmark/.

Only verifier_v2.o differs. Both variants retain scalar sampling, parallel-edge
contraction and direct-Edge verifier input. No timing/work driver is executed.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
import time

import recover_mst_search as monitor

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = '30728a3dedb9f6fc9b52289053e05d78a47ceffd'
PARENT_SHA256 = 'f976a7d61650f5aaf8e7221c7684461e36bcb51492347f45a56497b6b1cee306'
REFERENCE_VERIFIER_SHA256 = 'e7b61d0ebc24c2c04f3e3012b94d88b550f020c2ae7415ceb908352057ae7f7e'
NATIVE = ['/usr/bin/arch', '-arm64']
VARIANTS = ('reference', 'compressed')
SOURCES = ['boruvka/boruvka.cpp', 'kruskal/kruskal.cpp', 'prim/prim.cpp', 'lca/lca.cpp',
           'union_find/union_find.cpp', 'graph_utils/graph_utils.cpp', 'kkt/kkt.cpp']
TESTS = ['test/compressed_query_test.cpp', 'test/edge_verifier_view_test.cpp',
         'test/multigraph_contraction_test.cpp', 'test/regression_test.cpp',
         'test/contraction_test.cpp', 'test/simple_test.cpp',
         'benchmark/core_attachment_test.cpp', 'benchmark/certificate_test.cpp']
WORK_SOURCE = 'benchmark/results/retention-control-2026-10-15/work/driver.cpp'
WORK_SOURCE_SHA256 = 'ae08c5d199d83668d81f41a573452fea099c7e7cd5bd9bb4807c4a8ba9120e25'
CHANGED_COUNTERS = {'verifier_vertex_visits', 'verifier_edge_visits', 'path_query_visits', 'initialized_slots'}
ADDED_NATIVE = {'verifier/experimental_compressed_queries.hpp', 'test/compressed_query_test.cpp'}


def require(condition, message):
    if not condition: raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory():
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(set(ROOT.glob('*/*.cpp')) | set(ROOT.glob('*/*.hpp')))}


def save(path, data, exclusive=False):
    with Path(path).open('x' if exclusive else 'w') as stream:
        json.dump(data, stream, indent=2, allow_nan=False); stream.write('\n')


def checked_output(command):
    return subprocess.check_output(command, cwd=ROOT, text=True, timeout=60)


def profile(binary):
    description = checked_output(['/usr/bin/file','-b',str(binary)]).strip()
    require(description == 'Mach-O 64-bit executable arm64', 'rejected translated executable')
    load = checked_output(['/usr/bin/otool','-l',str(binary)])
    matches = re.findall(r'\bcmd LC_MAIN\b(?:(?!Load command).)*?\bstacksize (\d+)',load,re.S)
    require(matches == ['536870912'], 'missing/duplicate 512 MiB main-stack record')
    return {'file_description':description,'otool_load_commands':load,'main_stack_bytes':536870912}


def check_source_contract(parent_path):
    require(sha(parent_path) == PARENT_SHA256, 'wrong original Edge freeze')
    parent = json.loads(parent_path.read_text())
    require(parent['schema'] == 'edge_view_experiment_freeze_v1', 'wrong parent schema')
    current = inventory(); original = parent['source_sha256']
    require(set(current) == set(original) | ADDED_NATIVE, 'unexpected native additions/removals')
    require({name for name,value in original.items() if current[name] != value} == {'verifier/verifier_v2.cpp'},
            'only verifier_v2.cpp may change; scalar sampling must remain fixed')
    require(checked_output(['git','merge-base',BASE_COMMIT,'HEAD']).strip() == BASE_COMMIT, 'worktree does not descend from declared base')
    parent_root = Path(parent['working_directory'])
    baseline_path = parent_root/'verifier/verifier_v2.cpp'
    require(sha(baseline_path) == original['verifier/verifier_v2.cpp'] == REFERENCE_VERIFIER_SHA256, 'reference verifier drift')
    baseline = baseline_path.read_text(); proposed = (ROOT/'verifier/verifier_v2.cpp').read_text()
    include = '#ifdef KKT_EXPERIMENT_COMPRESSED_QUERIES\n#include "experimental_compressed_queries.hpp"\n#endif\n'
    require(proposed.count(include) == 1, 'unexpected macro include')
    restored = proposed.replace(include, '', 1)
    marker = '\tvector<unsigned char> compute_heavy_marks()\n\t{\n'
    require(restored.count(marker) == 1, 'ambiguous verifier dispatch body')
    start = restored.index(marker)+len(marker)
    require(restored.startswith('#ifdef KKT_EXPERIMENT_COMPRESSED_QUERIES\n',start), 'missing opt-in dispatch')
    alternate = restored.index('#else\n',start)
    tail = restored.index('#endif\n\t}\n};',alternate)
    restored = restored[:start]+restored[alternate+len('#else\n'):tail]+restored[tail+len('#endif\n'):]
    require(restored == baseline, 'unselected reference source was changed textually')
    for name in ('Makefile','benchmark/retention_control.mk'):
        require(sha(ROOT/name) == parent['build_recipe_sha256'][name], 'parent Make recipe changed')
    # Bound the reused monitor implementation, including its original source.
    monitor_path = Path(monitor.__file__).resolve()
    matching = [(Path(name),value) for name,value in parent['python_source_sha256'].items() if Path(name).name == monitor_path.name]
    require(len(matching) == 1 and sha(monitor_path) == matching[0][1] == sha(matching[0][0]), 'bounded monitor changed')
    require(sha(ROOT/WORK_SOURCE) == WORK_SOURCE_SHA256, 'untimed work driver changed')
    return parent,current


def compare_records(first, second):
    def unique(pairs):
        result = {}
        for key,value in pairs:
            require(key not in result, 'duplicate JSON key'); result[key] = value
        return result
    def nonfinite(value): raise RuntimeError('nonfinite record value: '+value)
    def load(path):
        return [json.loads(line,object_pairs_hook=unique,parse_constant=nonfinite) for line in Path(path).read_text().splitlines()]
    a,b = load(first),load(second)
    identities = [(fixture,order,seed) for fixture in range(56) for order in range(3)
                  for seed in (0,1,2,17,401,809,65537,4294967295)]
    require(len(a) == len(b) == len(identities) == 1344, 'incomplete full-KKT paired matrix')
    declarations = re.findall(r'\{\s*"([a-z_0-9]+)"\s*,\s*&kkt_work::WorkStats::([a-z_0-9]+)\s*,\s*(?:true|false)\s*\}',
                              (ROOT/'benchmark/work_metrics.hpp').read_text())
    fields = {name for name,member in declarations}
    require(len(declarations) == len(fields) == 65 and all(name == member for name,member in declarations)
            and CHANGED_COUNTERS <= fields, 'wrong canonical 65-field member-bound work schema')
    unchanged = fields-CHANGED_COUNTERS; require(len(unchanged) == 61, 'wrong unchanged counter set')
    witnesses = 0; derived = []
    for identity,reference,candidate in zip(identities,a,b):
        for record in (reference,candidate):
            require(set(record) == {'fixture','order','seed','fingerprint','ids','stats'}, 'wrong full-KKT record fields')
            require(all(type(record[name]) is int for name in ('fixture','order','seed')), 'fixture/order/seed must be exact integers')
            require(tuple(record[name] for name in ('fixture','order','seed')) == identity, 'missing/reordered full-KKT record')
            require(type(record['fingerprint']) is int and record['fingerprint'] >= 0, 'invalid input fingerprint')
            require(type(record['ids']) is list and all(type(value) is int for value in record['ids']) and
                    record['ids'] == sorted(set(record['ids'])), 'invalid sorted unique MST IDs')
            require(set(record['stats']) == fields and all(type(value) is int and value >= 0 for value in record['stats'].values()),
                    'invalid work-counter schema/domain')
        for name in ('fixture','order','seed','fingerprint','ids'):
            require(reference[name] == candidate[name], f'input/MST identity mismatch at {identity}/{name}')
        old,new = reference['stats'],candidate['stats']
        require(all(old[name] == new[name] for name in unchanged), f'one of 61 invariant counters differs at {identity}')
        q,m,t,n = (old[name] for name in ('verifier_queries','verifier_tree_edges','verifier_tree_calls','fbt_output_vertices'))
        u = new['path_query_visits']-2*q
        require(0 <= u <= q, f'invalid derived unique request count at {identity}')
        require(old['path_query_visits'] == 4*q, f'reference path visits differ from 4Q at {identity}')
        require(old['initialized_slots']-new['initialized_slots'] == m+q-u+t, f'initialization identity failed at {identity}')
        require(old['verifier_edge_visits']-new['verifier_edge_visits'] == m, f'edge-visit identity failed at {identity}')
        require(new['verifier_vertex_visits']-old['verifier_vertex_visits'] == n, f'vertex-visit identity failed at {identity}')
        witnesses += q > 0 and new['path_query_visits'] < old['path_query_visits']
        derived.append({'fixture':identity[0],'order':identity[1],'seed':identity[2],
                        'Q':q,'U':u,'M':m,'T':t,'Nsum':n})
    require(witnesses > 0, 'no positive linked compressed-query witness')
    return {'status':'pass','pairs':1344,'fields_per_pair':65,'identical_counter_fields':sorted(unchanged),
            'changed_fields_with_exact_identities':sorted(CHANGED_COUNTERS),'positive_work_witnesses':witnesses,
            'identical_input_fingerprints_and_sorted_mst_ids':True,'derived_unique_request_counts':derived,
            'reference_records':str(first),'reference_records_sha256':sha(first),
            'compressed_records':str(second),'compressed_records_sha256':sha(second),
            'scope':'Exact input/result IDs and work invariants; no intermediate sample/forest trace is claimed.'}


class SerialGuard:
    """Same bounded monitor and owned-group cleanup as prior native correctness."""
    def __init__(self,evidence):
        self.evidence = evidence; self.groups = []; self.sampler = monitor.BoundedSampler(monitor.LibprocProvider())
    def run(self,command,stdout,stderr=subprocess.STDOUT,env=None,check=True):
        require(not self.sampler.poisoned,'poisoned sampler forbids another child')
        process = None
        entry = {'command':command,'process_group':None,'observations':[]}; self.groups.append(entry)
        deadline = time.monotonic()+300; unavailable = 0
        previous_handler = signal.getsignal(signal.SIGTERM)
        def terminated(signum,frame):
            raise KeyboardInterrupt('owned build/test received SIGTERM')
        signal.signal(signal.SIGTERM,terminated)
        try:
            process = subprocess.Popen(command,cwd=ROOT,stdout=stdout,stderr=stderr,env=env,start_new_session=True)
            entry['process_group'] = process.pid
            while process.poll() is None:
                try: process.wait(timeout=2)
                except subprocess.TimeoutExpired: pass
                observation = self.sampler.sample(process.pid); entry['observations'].append(observation)
                unavailable = unavailable+1 if observation['validation'] != 'pass' else 0
                require(not self.sampler.poisoned and unavailable < 3,'bounded resource observations unavailable')
                require(observation['validation'] != 'pass' or observation['rss_kib'] <= 40*1024*1024,'owned group exceeded 40 GiB sampled RSS')
                require(time.monotonic() <= deadline,'owned build/test exceeded 300 seconds')
            entry['exit_status'] = process.returncode
        except BaseException as error:
            entry['error'] = repr(error); raise
        finally:
            try:
                # A second SIGTERM cannot interrupt the bounded cleanup proof.
                signal.signal(signal.SIGTERM,signal.SIG_IGN)
                entry['cleanup'] = monitor.bounded_terminate(process,self.sampler)
                save(self.evidence,{'groups':self.groups})
                require(not entry['cleanup']['native_process_may_still_be_running'],'owned group exit unknown; no further launch')
            finally:
                signal.signal(signal.SIGTERM,previous_handler)
        require(not check or process.returncode == 0,f'command failed: {process.returncode}: {command}')
        return process.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',required=True,choices=('native-correctness','sanitizer-correctness','timing-build'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--parent-freeze',type=Path,default=Path('/Users/random_person/Desktop/kkt-edge-verifier-view/benchmark/results/edge-view-2026-10-15/freeze.json'))
    args = parser.parse_args(); parent_path = args.parent_freeze.resolve(strict=True)
    require(Path(__file__).resolve().parent == ROOT/'benchmark','copy this preparation into the authorized benchmark directory first')
    parent,sources = check_source_contract(parent_path)
    output = args.output.resolve(); output.mkdir(parents=True,exist_ok=True); tag = args.profile
    build = ROOT/'.build/compressed-query'/tag; binaries = ROOT/'bin/compressed-query'/tag
    require(not build.exists() and not binaries.exists(),'refusing to overwrite existing profile objects/binaries')
    log_path = output/f'{tag}-build.log'; require(not log_path.exists(),'refusing to overwrite build evidence')
    build.mkdir(parents=True); binaries.mkdir(parents=True)
    compiler = '/opt/homebrew/opt/llvm/bin/clang++' if tag == 'sanitizer-correctness' else '/usr/bin/clang++'
    compiler_command = NATIVE+[compiler,'--version']; compiler_version = checked_output(compiler_command)
    expected_compiler = 'clang version 22.' if tag == 'sanitizer-correctness' else 'Apple clang version 15.'
    require('Target: arm64-' in compiler_version and expected_compiler in compiler_version,'wrong native compiler profile')
    sdk = checked_output(NATIVE+['/usr/bin/xcrun','--show-sdk-path']).strip()
    if tag != 'sanitizer-correctness':
        inherited = parent['variants']['edge']['build']['record']
        require((compiler_command,compiler_version,sdk) ==
                (inherited['compiler_command'],inherited['compiler'],inherited['sdk']),
                'native compiler/SDK differs from frozen Edge parent')
    flags = ['-std=c++17','-O3','-Wall','-Wextra','-march=native','-DKKT_EXPERIMENT_RETAIN_PARALLEL','-DKKT_EXPERIMENT_EDGE_VIEW']
    if tag == 'sanitizer-correctness':
        flags = ['-std=c++17','-O1','-g','-Wall','-Wextra','-march=native','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                 '-DKKT_EXPERIMENT_RETAIN_PARALLEL','-DKKT_EXPERIMENT_EDGE_VIEW']
    if tag != 'timing-build': flags.append('-DKKT_ENABLE_WORK_STATS')
    require(not any('PACKED_SAMPLING' in flag or 'NDEBUG' in flag for flag in flags),'sampler/assertion policy changed')
    base = NATIVE+[compiler,'-isysroot',sdk,*flags,'-I.']; linkflags = [f'-L{sdk}/usr/lib','-Wl,-stack_size,0x20000000']
    commands = []; guard = SerialGuard(output/f'{tag}-owned-groups.json'); recipe_hash = sha(__file__)
    records = {variant:[] for variant in VARIANTS}
    with log_path.open('x') as log:
        log.write(compiler_version+f'SDK: {sdk}\n')
        def run(command):
            commands.append(command); log.write('\n$ '+shlex.join(command)+'\n'); log.flush(); guard.run(command,stdout=log)
        def compile_source(source,destination,extra=()):
            destination.parent.mkdir(parents=True,exist_ok=True)
            run(base+list(extra)+['-c',source,'-o',str(destination)])
            require('arm64' in checked_output(['/usr/bin/file','-b',str(destination)]),'translated object')
            return destination
        shared = {source.replace('.cpp','.o'):compile_source(source,build/'shared'/source.replace('.cpp','.o')) for source in SOURCES}
        verifier_objects = {variant:compile_source('verifier/verifier_v2.cpp',build/variant/'verifier/verifier_v2.o',
            ['-DKKT_EXPERIMENT_COMPRESSED_QUERIES'] if variant == 'compressed' else []) for variant in VARIANTS}
        targets = ['benchmark/retention_control.cpp'] if tag == 'timing-build' else [*TESTS,*([WORK_SOURCE] if tag == 'native-correctness' else [])]
        for source in targets:
            main_object = compile_source(source,build/'shared'/source.replace('.cpp','.o'))
            for variant in VARIANTS:
                binary = binaries/variant/('retention_work' if source == WORK_SOURCE else Path(source).stem)
                binary.parent.mkdir(parents=True,exist_ok=True)
                command = base+[str(path) for path in shared.values()]+[str(verifier_objects[variant]),str(main_object)]+linkflags+['-o',str(binary)]
                run(command)
                records[variant].append({'source':source,'main_object':str(main_object),'main_object_sha256':sha(main_object),
                    'binary':str(binary),'binary_sha256':sha(binary),'binary_profile':profile(binary),'link_command':command,
                    'role':'untimed_work_never_executed' if source == WORK_SOURCE else 'timing_never_executed' if tag == 'timing-build' else 'correctness'})
    require(sources == check_source_contract(parent_path)[1] and sha(__file__) == recipe_hash,'source/recipe changed during build')
    common = {'schema':'compressed_query_build_v1','profile':tag,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'working_directory':str(ROOT),'revision':checked_output(['git','rev-parse','HEAD']).strip(),'base_commit':BASE_COMMIT,
        'source_sha256':sources,'build_recipe_sha256':{'Makefile':sha(ROOT/'Makefile'),'benchmark/retention_control.mk':sha(ROOT/'benchmark/retention_control.mk'),
            'benchmark/build_compressed_queries.py':recipe_hash},'compiler_command':compiler_command,'compiler':compiler_version,'sdk':sdk,
        'common_compile_flags':flags,'build_commands':commands,'build_command':[sys.executable,'-B',str(Path(__file__).resolve()),'--profile',tag,'--output',str(output),'--parent-freeze',str(parent_path)],
        'build_log':str(log_path),'build_log_sha256':sha(log_path),'build_exit_status':0,'parent_edge_freeze':str(parent_path),'parent_edge_freeze_sha256':PARENT_SHA256,
        'seven_non_verifier_objects_identical_by_construction':True,'reference_source_textually_unchanged':True,'scalar_sampling_fixed':True,
        'work_driver':str(ROOT/WORK_SOURCE),'work_driver_sha256':WORK_SOURCE_SHA256}
    for variant in VARIANTS:
        objects = {**shared,'verifier/verifier_v2.o':verifier_objects[variant]}
        record = {**common,'variant':variant,'object_paths':{name:str(path) for name,path in objects.items()},
            'object_sha256':{name:sha(path) for name,path in objects.items()},'executables':records[variant]}
        if tag == 'timing-build': record.update(records[variant][0])
        save(output/f'{tag}-{variant}-build-record.json',record,exclusive=True)
    if tag == 'timing-build':
        require(len(commands) == 12,'unexpected timing compile/link sequence')
        print('Built both timing executables without executing either.'); return
    environment = os.environ.copy()
    if tag == 'sanitizer-correctness':
        environment['ASAN_OPTIONS'] = 'detect_leaks=1:abort_on_error=1'
        environment['UBSAN_OPTIONS'] = 'halt_on_error=1:print_stacktrace=1'
    tests = []; negatives = []
    for variant in VARIANTS:
        for record in records[variant]:
            if record['role'] != 'correctness': continue
            stem = Path(record['binary']).name
            command = NATIVE+[record['binary']]+([variant] if stem == 'compressed_query_test' else [])
            stdout_path,stderr_path = output/f'{tag}-{variant}-{stem}.stdout',output/f'{tag}-{variant}-{stem}.stderr'
            with stdout_path.open('x') as stdout,stderr_path.open('x') as stderr:
                status = guard.run(command,stdout=stdout,stderr=stderr,env=environment,check=False)
            tests.append({'variant':variant,'test':stem,'command':command,'exit_status':status,'binary_sha256':record['binary_sha256'],
                'stdout':str(stdout_path),'stdout_sha256':sha(stdout_path),'stderr':str(stderr_path),'stderr_sha256':sha(stderr_path)})
            save(output/f'{tag}-tests.json',{'status':'running','tests':tests})
            require(status == 0,f'correctness failed: {tag}/{variant}/{stem}')
            if stem == 'compressed_query_test':
                require(stdout_path.read_text().strip() == f'PASS 252 positional cases, 7 malformed lookups; actual linked policy={variant}',
                        'focused oracle/guard/dispatch count mismatch')
    require(len(tests) == 16,'incomplete correctness suite')
    for variant in VARIANTS:
        record = next(item for item in records[variant] if Path(item['binary']).name == 'compressed_query_test')
        wrong = 'compressed' if variant == 'reference' else 'reference'; command = NATIVE+[record['binary'],wrong]
        path = output/f'{tag}-{variant}-wrong-policy.log'
        with path.open('x') as log: status = guard.run(command,stdout=log,env=environment,check=False)
        message = path.read_text()
        require(status == 1 and 'FAIL: wrong linked query representation' in message and
                not any(token in message for token in ('ERROR: AddressSanitizer','ERROR: LeakSanitizer','runtime error:')),
                'wrong linked query policy not cleanly rejected')
        negatives.append({'command':command,'exit_status':status,'log':str(path),'sha256':sha(path)})
    pair = compare_records(output/f'{tag}-reference-edge_verifier_view_test.stdout',output/f'{tag}-compressed-edge_verifier_view_test.stdout')
    try: compare_records(pair['reference_records'],pair['reference_records'])
    except RuntimeError: pair['reference_linked_candidate_negative'] = 'rejected'
    else: raise RuntimeError('paired gate accepted reference-linked candidate')
    require(sources == check_source_contract(parent_path)[1] and sha(__file__) == recipe_hash,'source/recipe drift after correctness')
    for variant in VARIANTS:
        record = json.loads((output/f'{tag}-{variant}-build-record.json').read_text())
        for name,path in record['object_paths'].items(): require(sha(path) == record['object_sha256'][name],'object changed during correctness')
        for executable in records[variant]: require(sha(executable['binary']) == executable['binary_sha256'],'test/work binary changed')
    save(output/f'{tag}-tests.json',{'status':'pass','tests':tests,'paired_mst':pair,'wrong_policy_gates':negatives,
        'sanitizer_options':{key:environment[key] for key in ('ASAN_OPTIONS','UBSAN_OPTIONS') if key in environment},
        'performance_executed':False,'work_driver_executed':False})
    print(json.dumps({'status':'pass','tests':len(tests),'paired_records':pair['pairs'],
                      'invariant_counter_fields':61,'positive_work_witnesses':pair['positive_work_witnesses']},indent=2))


if __name__ == '__main__': main()
