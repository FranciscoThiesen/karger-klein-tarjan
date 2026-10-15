#!/usr/bin/env python3
"""Build and validate private scalar half/eighth sampling variants.

Install in a separately authorized worktree before execution. Timing builds never
execute a timing or work driver. The two timing variants differ only in kkt.o.
Both variants share the compressed verifier; public half sampling is unchanged.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shlex
import sys

import build_compressed_queries as inherited
import run_compressed_queries as parent_engine

ROOT = Path(__file__).resolve().parents[1]
PARENT_SHA256 = 'bd65da13058d3e9cfa58919a0fe5e02b8a46b1d0b8fe7f05801692d5a0866df9'
PARENT_PATH = Path('/Users/random_person/Desktop/kkt-compressed-queries/benchmark/results/compressed-query-2026-10-15/freeze.json')
PARENT_RECORDS_SHA256 = '47ac8f08a7a3171f5d27431b4304bcdbd8b6a17cccd25f0811e18d2d325b61d4'
OVERLAY = {
    'kkt/kkt.cpp':'f5681b0384fb26ee6af5a23e4f7109b990393d831fc6ceb5385ce43643f5fd9a',
    'kkt/experimental_eighth_sampling.hpp':'dc58872c0f6c8542ce67d8c9f3a1c5c5c4fd9f2b1e5ae9c1bb65b5e6c70293bd',
    'test/eighth_sampling_test.cpp':'f7d4cb33d5359f15b525a8572d76bfde619df7fffd03712dc4bf84e69c7e5fae',
    'test/eighth_sampling_integration_test.cpp':'b323122c31b1a09f31915f4e246f3b57655337e358d06921c5f8c449bb79270a',
}
VARIANTS = ('half','eighth')
SOURCES = ['boruvka/boruvka.cpp','kruskal/kruskal.cpp','prim/prim.cpp','lca/lca.cpp',
           'union_find/union_find.cpp','graph_utils/graph_utils.cpp','verifier/verifier_v2.cpp']
TESTS = [*inherited.TESTS,'test/eighth_sampling_test.cpp','test/eighth_sampling_integration_test.cpp']
WORK_SOURCE = inherited.WORK_SOURCE
REFERENCE_NOTE = 'Fresh predicate-refactored half sampling with compressed verifier queries; not the historical parent timing binary.'
FLAGS = ['-std=c++17','-O3','-Wall','-Wextra','-march=native','-DKKT_EXPERIMENT_RETAIN_PARALLEL','-DKKT_EXPERIMENT_EDGE_VIEW']
NATIVE = inherited.NATIVE
sha, require, save = inherited.sha, inherited.require, inherited.save
inventory, profile, checked_output = inherited.inventory, inherited.profile, inherited.checked_output
SerialGuard = inherited.SerialGuard
RECIPES = (*parent_engine.RECIPES,'benchmark/build_eighth_sampling.py')


def expected_timing_commands(root,sdk):
    base = NATIVE+['/usr/bin/clang++','-isysroot',sdk,*FLAGS,'-I.']
    build = root/'.build/eighth-sampling/timing-build'
    shared = {name.replace('.cpp','.o'):str(build/'shared'/name.replace('.cpp','.o')) for name in SOURCES}
    objects = {variant:{**shared,'kkt/kkt.o':str(build/variant/'kkt/kkt.o')} for variant in VARIANTS}
    binaries = {variant:str(root/'bin/eighth-sampling/timing-build'/variant/'retention_control') for variant in VARIANTS}
    main = str(build/'shared/benchmark/retention_control.o')
    commands = [base+(['-DKKT_EXPERIMENT_COMPRESSED_QUERIES'] if name == 'verifier/verifier_v2.cpp' else [])+
                ['-c',name,'-o',shared[name.replace('.cpp','.o')]] for name in SOURCES]
    commands.extend(base+(['-DKKT_EXPERIMENT_EIGHTH_SAMPLING'] if variant == 'eighth' else [])+
                    ['-c','kkt/kkt.cpp','-o',objects[variant]['kkt/kkt.o']] for variant in VARIANTS)
    commands.append(base+['-c','benchmark/retention_control.cpp','-o',main])
    links = {variant:base+list(objects[variant].values())+[main,f'-L{sdk}/usr/lib','-Wl,-stack_size,0x20000000','-o',binaries[variant]] for variant in VARIANTS}
    commands.extend(links.values())
    return commands,objects,binaries,main,links


def parent_record(path):
    """Use the unchanged parent's complete proof at its original working root."""
    path = Path(path).resolve(strict=True)
    require(sha(path) == PARENT_SHA256,'wrong compressed parent freeze')
    original = parent_engine.analysis.read_json(path)
    expected = original['python_source_sha256']; current = parent_engine.helpers()
    old = {Path(name).name:value for name,value in expected.items()}
    new = {Path(name).name:value for name,value in current.items()}
    require(len(old) == len(expected) and len(new) == len(current) and old == new,
            'immutable parent helper copies changed')
    for name,value in expected.items(): require(sha(name) == value,'original parent helper changed')
    previous = parent_engine.helpers
    try:
        parent_engine.helpers = lambda: expected
        checked,_ = parent_engine.check_freeze(path)
    finally:
        parent_engine.helpers = previous
    return checked


def check_source_contract(parent_path):
    require(inherited.ROOT == ROOT,'inherited builder must be the local unchanged copy')
    parent = parent_record(parent_path); sources = inventory(); original = parent['source_sha256']
    require(set(sources) == set(original) | (set(OVERLAY)-{'kkt/kkt.cpp'}),
            'unexpected eighth-study native source additions/removals')
    require({name for name,value in original.items() if sources[name] != value} == {'kkt/kkt.cpp'},
            'only existing kkt.cpp may change from compressed parent')
    for name,value in OVERLAY.items(): require(sources[name] == value,'declared eighth overlay changed: '+name)
    for name,value in parent['build_recipe_sha256'].items():
        require(sha(ROOT/name) == value,'parent build recipe changed: '+name)
    require(sha(ROOT/WORK_SOURCE) == inherited.WORK_SOURCE_SHA256,'untimed work driver changed')
    return parent,sources


def load_records(path):
    def unique(pairs):
        result = {}
        for key,value in pairs:
            require(key not in result,'duplicate JSON key'); result[key] = value
        return result
    def nonfinite(value): raise RuntimeError('nonfinite record value: '+value)
    rows = [json.loads(line,object_pairs_hook=unique,parse_constant=nonfinite)
            for line in Path(path).read_text().splitlines()]
    declarations = re.findall(r'\{\s*"([a-z_0-9]+)"\s*,\s*&kkt_work::WorkStats::([a-z_0-9]+)\s*,\s*(?:true|false)\s*\}',
                              (ROOT/'benchmark/work_metrics.hpp').read_text())
    fields = {name for name,member in declarations}
    require(len(declarations) == len(fields) == 65 and all(name == member for name,member in declarations),
            'wrong canonical member-bound work schema')
    identities = [(fixture,order,seed) for fixture in range(56) for order in range(3)
                  for seed in (0,1,2,17,401,809,65537,4294967295)]
    require(len(rows) == len(identities) == 1344,'incomplete full-KKT record matrix')
    for identity,row in zip(identities,rows):
        require(set(row) == {'fixture','order','seed','fingerprint','ids','stats'},'wrong record fields')
        require(all(type(row[name]) is int for name in ('fixture','order','seed')) and
                tuple(row[name] for name in ('fixture','order','seed')) == identity,'wrong record identity')
        require(type(row['fingerprint']) is int and 0 <= row['fingerprint'] <= 2**64-1,'invalid fingerprint')
        require(type(row['ids']) is list and all(type(value) is int for value in row['ids']) and
                row['ids'] == sorted(set(row['ids'])),'invalid sorted unique MST IDs')
        require(type(row['stats']) is dict and set(row['stats']) == fields and
                all(type(value) is int and 0 <= value <= 2**64-1 for value in row['stats'].values()),'invalid work counters')
    return rows


def compare_sampling(first,second):
    half,eighth = load_records(first),load_records(second); different = 0
    for a,b in zip(half,eighth):
        require(all(a[name] == b[name] for name in ('fixture','order','seed','fingerprint','ids')),
                'sampling policies changed certified input/MST identity')
        require(all(a['stats'][name] == b['stats'][name] for name in ('root_after_two_vertices','root_after_two_edges')),
                'sampling policies changed deterministic root contractions')
        different += a['stats'] != b['stats']
    require(different > 0,'no linked eighth sampling witness; half substitution rejected')
    return {'status':'pass','pairs':1344,'fields_per_pair':65,'different_recursive_work_pairs':different,
            'half_records':str(first),'half_records_sha256':sha(first),
            'eighth_records':str(second),'eighth_records_sha256':sha(second),
            'identical_root_after_two_dimensions':True,
            'scope':'Exact input/MST IDs and initial contractions; recursive inputs and work intentionally differ.'}


def compare_half_parent(first,second):
    require(sha(first) == PARENT_RECORDS_SHA256,'historical compressed-scalar correctness records changed')
    require(load_records(first) == load_records(second),'predicate-refactored half changed exact parent replay')
    return {'status':'pass','pairs':1344,'identical_counter_fields':65,'parent_records':str(first),
            'parent_records_sha256':sha(first),'fresh_records':str(second),'fresh_records_sha256':sha(second),
            'scope':'Logical fixture replay; not timing or assembly equivalence.'}


def reject_substitution(function,first):
    try: function(first,first)
    except RuntimeError: return 'rejected'
    raise RuntimeError('paired gate accepted a wrong linked-policy record substitution')


def check_focused_output(stem,variant,text):
    if stem == 'compressed_query_test':
        require(text.strip() == 'PASS 252 positional cases, 7 malformed lookups; actual linked policy=compressed',
                'focused verifier count/policy mismatch')
    elif stem == 'eighth_sampling_test':
        require(text.strip() == 'PASS: three deterministic eighth-sampling predicate groups',
                'focused predicate group count mismatch')
    elif stem == 'eighth_sampling_integration_test':
        match = re.fullmatch(r'PASS 132 private/public sampling cases, each replayed; ([0-9]+) half/eighth witnesses; policy='+
                             re.escape(variant),text.strip())
        require(match is not None and 0 < int(match.group(1)) <= 66,
                'private/public integration count/policy/witness mismatch')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',required=True,choices=('native-correctness','sanitizer-correctness','timing-build'))
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--parent-freeze',type=Path,default=PARENT_PATH)
    args = parser.parse_args(); parent_path = args.parent_freeze.resolve(strict=True)
    require(Path(__file__).resolve().parent == ROOT/'benchmark','install into authorized worktree first')
    parent,sources = check_source_contract(parent_path); tag = args.profile
    output = args.output.resolve(); output.mkdir(parents=True,exist_ok=True)
    build,binaries = ROOT/'.build/eighth-sampling'/tag,ROOT/'bin/eighth-sampling'/tag
    require(not build.exists() and not binaries.exists(),'refusing to overwrite existing build profile')
    log_path = output/f'{tag}-build.log'; require(not log_path.exists(),'refusing to overwrite build evidence')
    build.mkdir(parents=True); binaries.mkdir(parents=True)
    compiler = '/opt/homebrew/opt/llvm/bin/clang++' if tag == 'sanitizer-correctness' else '/usr/bin/clang++'
    compiler_command = NATIVE+[compiler,'--version']; compiler_version = checked_output(compiler_command)
    expected = 'clang version 22.' if tag == 'sanitizer-correctness' else 'Apple clang version 15.'
    require('Target: arm64-' in compiler_version and expected in compiler_version,'wrong compiler profile')
    sdk = checked_output(NATIVE+['/usr/bin/xcrun','--show-sdk-path']).strip()
    if tag != 'sanitizer-correctness':
        prior = parent['variants']['compressed']['build']['record']
        require((compiler_command,compiler_version,sdk) == (prior['compiler_command'],prior['compiler'],prior['sdk']),
                'native compiler/SDK differs from parent')
    flags = list(FLAGS)
    if tag == 'sanitizer-correctness':
        flags = ['-std=c++17','-O1','-g','-Wall','-Wextra','-march=native','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                 '-DKKT_EXPERIMENT_RETAIN_PARALLEL','-DKKT_EXPERIMENT_EDGE_VIEW']
    if tag != 'timing-build': flags.append('-DKKT_ENABLE_WORK_STATS')
    base = NATIVE+[compiler,'-isysroot',sdk,*flags,'-I.']; linkflags = [f'-L{sdk}/usr/lib','-Wl,-stack_size,0x20000000']
    commands = []; guard = SerialGuard(output/f'{tag}-owned-groups.json')
    recipes = {name:sha(ROOT/name) for name in RECIPES}; records = {variant:[] for variant in VARIANTS}
    with log_path.open('x') as log:
        log.write(compiler_version+f'SDK: {sdk}\n')
        def run(command):
            commands.append(command); log.write('\n$ '+shlex.join(command)+'\n'); log.flush(); guard.run(command,stdout=log)
        def compile_source(source,destination,extra=()):
            destination.parent.mkdir(parents=True,exist_ok=True)
            run(base+list(extra)+['-c',source,'-o',str(destination)])
            require('arm64' in checked_output(['/usr/bin/file','-b',str(destination)]),'translated object')
            return destination
        shared = {source.replace('.cpp','.o'):compile_source(source,build/'shared'/source.replace('.cpp','.o'),
                  ['-DKKT_EXPERIMENT_COMPRESSED_QUERIES'] if source == 'verifier/verifier_v2.cpp' else []) for source in SOURCES}
        kkt_objects = {variant:compile_source('kkt/kkt.cpp',build/variant/'kkt/kkt.o',
                       ['-DKKT_EXPERIMENT_EIGHTH_SAMPLING'] if variant == 'eighth' else []) for variant in VARIANTS}
        require(sha(kkt_objects['half']) != sha(kkt_objects['eighth']),'KKT dispatch objects unexpectedly identical')
        targets = ['benchmark/retention_control.cpp'] if tag == 'timing-build' else [*TESTS,*([WORK_SOURCE] if tag == 'native-correctness' else [])]
        for source in targets:
            integration = source == 'test/eighth_sampling_integration_test.cpp'
            common_main = None if integration else compile_source(source,build/'shared'/source.replace('.cpp','.o'))
            for variant in VARIANTS:
                main_object = compile_source(source,build/variant/source.replace('.cpp','.o'),
                    ['-DKKT_EXPERIMENT_EIGHTH_SAMPLING'] if variant == 'eighth' else []) if integration else common_main
                selected = dict(shared)
                if not integration: selected['kkt/kkt.o'] = kkt_objects[variant]
                binary = binaries/variant/('retention_work' if source == WORK_SOURCE else Path(source).stem)
                binary.parent.mkdir(parents=True,exist_ok=True)
                command = base+[str(path) for path in selected.values()]+[str(main_object)]+linkflags+['-o',str(binary)]
                run(command)
                records[variant].append({'source':source,'main_object':str(main_object),'main_object_sha256':sha(main_object),
                    'binary':str(binary),'binary_sha256':sha(binary),'binary_profile':profile(binary),'link_command':command,
                    'sampling_policy':variant,'private_acceptance_mask':7 if variant == 'eighth' else 1,
                    'sampling_words_per_visited_edge':1,
                    'verifier_policy':'compressed','role':'untimed_work_never_executed' if source == WORK_SOURCE else
                    'timing_never_executed' if tag == 'timing-build' else 'correctness'})
    require(sources == check_source_contract(parent_path)[1] and recipes == {name:sha(ROOT/name) for name in RECIPES},
            'source/recipe changed during build')
    common = {'schema':'eighth_sampling_build_v1','profile':tag,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'working_directory':str(ROOT),'revision':checked_output(['git','rev-parse','HEAD']).strip(),'source_sha256':sources,
        'build_recipe_sha256':recipes,'compiler_command':compiler_command,'compiler':compiler_version,'sdk':sdk,
        'common_compile_flags':flags,'build_commands':commands,'build_command':[sys.executable,'-B',str(Path(__file__).resolve()),
        '--profile',tag,'--output',str(output),'--parent-freeze',str(parent_path)],'build_log':str(log_path),
        'build_log_sha256':sha(log_path),'build_exit_status':0,'parent_compressed_freeze':str(parent_path),
        'parent_compressed_freeze_sha256':PARENT_SHA256,'seven_non_kkt_objects_identical_by_construction':True,
        'compressed_queries_fixed':True,'public_scalar_sampling_fixed':True,'reference_note':REFERENCE_NOTE,
        'source_overlay_sha256':OVERLAY,'work_driver':str(ROOT/WORK_SOURCE),'work_driver_sha256':inherited.WORK_SOURCE_SHA256}
    for variant in VARIANTS:
        objects = {**shared,'kkt/kkt.o':kkt_objects[variant]}
        record = {**common,'variant':variant,'object_paths':{name:str(path) for name,path in objects.items()},
                  'object_sha256':{name:sha(path) for name,path in objects.items()},'executables':records[variant],
                  'sampling_policy':variant,'private_acceptance_mask':7 if variant == 'eighth' else 1,
                  'sampling_words_per_visited_edge':1}
        if tag == 'timing-build': record.update(records[variant][0])
        save(output/f'{tag}-{variant}-build-record.json',record,exclusive=True)
    if tag == 'timing-build':
        require(commands == expected_timing_commands(ROOT,sdk)[0] and len(commands) == 12,
                'unexpected timing compile/link sequence')
        print('Built both half/eighth timing executables; neither was executed.'); return

    environment = os.environ.copy()
    if tag == 'sanitizer-correctness':
        environment['ASAN_OPTIONS'] = 'detect_leaks=1:abort_on_error=1'
        environment['UBSAN_OPTIONS'] = 'halt_on_error=1:print_stacktrace=1'
    tests = []; negatives = []; record_paths = {}
    for variant in VARIANTS:
        for record in records[variant]:
            if record['role'] != 'correctness': continue
            stem,policy = Path(record['binary']).name,record['verifier_policy']
            extra = [variant] if stem == 'eighth_sampling_integration_test' else [policy] if stem == 'compressed_query_test' else []
            command = NATIVE+[record['binary']]+extra
            stdout_path = output/f'{tag}-{variant}-{policy}-{stem}.stdout'
            stderr_path = output/f'{tag}-{variant}-{policy}-{stem}.stderr'
            with stdout_path.open('x') as stdout,stderr_path.open('x') as stderr:
                status = guard.run(command,stdout=stdout,stderr=stderr,env=environment,check=False)
            tests.append({'variant':variant,'verifier_policy':policy,'test':stem,'command':command,'exit_status':status,
                          'binary_sha256':record['binary_sha256'],'stdout':str(stdout_path),'stdout_sha256':sha(stdout_path),
                          'stderr':str(stderr_path),'stderr_sha256':sha(stderr_path)})
            save(output/f'{tag}-tests.json',{'status':'running','tests':tests})
            require(status == 0,'correctness failed: '+str(command))
            check_focused_output(stem,variant,stdout_path.read_text())
            if stem == 'edge_verifier_view_test': record_paths[variant,policy] = stdout_path
            if stem in ('compressed_query_test','eighth_sampling_integration_test'):
                wrong = ('reference' if policy == 'compressed' else 'compressed') if stem == 'compressed_query_test' else ('eighth' if variant == 'half' else 'half')
                command = NATIVE+[record['binary'],wrong]; path = output/f'{tag}-{variant}-{policy}-{stem}-wrong-policy.log'
                with path.open('x') as log: status = guard.run(command,stdout=log,env=environment,check=False)
                message = path.read_text(); marker = 'FAIL: wrong linked query representation' if stem == 'compressed_query_test' else 'FAIL: wrong private policy'
                require(status == 1 and marker in message and not any(token in message for token in
                        ('ERROR: AddressSanitizer','ERROR: LeakSanitizer','runtime error:')),'wrong policy not cleanly rejected')
                negatives.append({'command':command,'exit_status':status,'log':str(path),'sha256':sha(path)})
    require(len(tests) == 20 and len(negatives) == 4,'incomplete correctness/negative matrix')
    sampling = compare_sampling(record_paths['half','compressed'],record_paths['eighth','compressed'])
    sampling['wrong_sampling_record_substitution'] = reject_substitution(compare_sampling,record_paths['half','compressed'])
    original_records = Path(parent['working_directory'])/'benchmark/results/compressed-query-2026-10-15/validation/native-correctness-compressed-edge_verifier_view_test.stdout'
    replay = compare_half_parent(original_records,record_paths['half','compressed'])
    require(sources == check_source_contract(parent_path)[1] and recipes == {name:sha(ROOT/name) for name in RECIPES},
            'source/recipe drift after correctness')
    for variant in VARIANTS:
        record = json.loads((output/f'{tag}-{variant}-build-record.json').read_text())
        for name,path in record['object_paths'].items(): require(sha(path) == record['object_sha256'][name],'production object changed')
        for executable in records[variant]:
            require(sha(executable['binary']) == executable['binary_sha256'] and
                    sha(executable['main_object']) == executable['main_object_sha256'],'test/work artifact changed')
    save(output/f'{tag}-tests.json',{'status':'pass','tests':tests,
        'sampling_pair':sampling,'parent_half_replay':replay,'wrong_policy_gates':negatives,
        'sanitizer_options':{key:environment[key] for key in ('ASAN_OPTIONS','UBSAN_OPTIONS') if key in environment},
        'performance_executed':False,'work_driver_executed':False})
    print(json.dumps({'status':'pass','tests':len(tests),'wrong_policy_gates':len(negatives),
                      'sampling_pairs':1344,'half_parent_replay_fields':65}))


if __name__ == '__main__': main()
