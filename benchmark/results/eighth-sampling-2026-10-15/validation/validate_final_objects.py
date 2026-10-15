#!/usr/bin/env python3
"""Verify actual uninstrumented half/eighth timing objects without benchmarking.

Never executes a performance/work driver. Final KKT objects are independently
rebuilt with the exact flags and must be byte-identical to the recorded objects.
Actual final production objects run the unchanged six-solver correctness suite.
The same-flags source-inclusion gate directly checks private/public RNG policy;
it is explicitly not an RNG trace of the separate final linked KKT object.
"""
import argparse
import json
from pathlib import Path
import shlex
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'benchmark'))
import build_eighth_sampling as builder


def checked_records(output):
    parent,sources = builder.check_source_contract(builder.PARENT_PATH)
    records = []; receipts = {}
    for variant in builder.VARIANTS:
        path = output/f'timing-build-{variant}-build-record.json'
        receipts[str(path)] = builder.sha(path)
        record = builder.parent_engine.analysis.read_json(path)
        expected = {'schema':'eighth_sampling_build_v1','profile':'timing-build','variant':variant,
                    'working_directory':str(ROOT),'source_sha256':sources,'common_compile_flags':builder.FLAGS,
                    'build_recipe_sha256':{name:builder.sha(ROOT/name) for name in builder.RECIPES},
                    'build_exit_status':0,'parent_compressed_freeze':str(builder.PARENT_PATH),
                    'parent_compressed_freeze_sha256':builder.PARENT_SHA256,
                    'seven_non_kkt_objects_identical_by_construction':True,'compressed_queries_fixed':True,
                    'public_scalar_sampling_fixed':True,'reference_note':builder.REFERENCE_NOTE,
                    'role':'timing_never_executed','verifier_policy':'compressed','source_overlay_sha256':builder.OVERLAY,
                    'sampling_policy':variant,'private_acceptance_mask':7 if variant == 'eighth' else 1,
                    'sampling_words_per_visited_edge':1}
        for name,value in expected.items():
            builder.require(type(record[name]) is type(value) and record[name] == value,'wrong final build field: '+name)
        original = parent['variants']['compressed']['build']['record']
        for name in ('compiler','compiler_command','sdk'):
            builder.require(record[name] == original[name],'final compiler/SDK changed')
        argv = record['build_command']
        builder.require(type(argv) is list and len(argv) == 9 and Path(argv[0]).name.startswith('python') and
                        argv[1:] == ['-B',str(ROOT/'benchmark/build_eighth_sampling.py'),'--profile','timing-build',
                                     '--output',str(output),'--parent-freeze',str(builder.PARENT_PATH)],'wrong build invocation')
        commands,objects,binaries,main,links = builder.expected_timing_commands(ROOT,record['sdk'])
        for name,value in (('build_commands',commands),('object_paths',objects[variant]),('binary',binaries[variant]),
                           ('main_object',main),('link_command',links[variant])):
            builder.require(record[name] == value,'wrong exact final argv/path: '+name)
        builder.require(set(record['object_sha256']) == set(objects[variant]),'wrong eight-object inventory')
        for name,path in record['object_paths'].items():
            builder.require(builder.sha(path) == record['object_sha256'][name],'stale final production object')
        for path,hashkey in ((record['main_object'],'main_object_sha256'),(record['binary'],'binary_sha256'),
                             (record['build_log'],'build_log_sha256')):
            builder.require(builder.sha(path) == record[hashkey],'stale final build artifact')
        builder.require(builder.profile(record['binary']) == record['binary_profile'],'native executable profile drift')
        descriptor = {name:record[name] for name in ('source','main_object','main_object_sha256','binary','binary_sha256',
                      'binary_profile','link_command','verifier_policy','role','sampling_policy',
                      'private_acceptance_mask','sampling_words_per_visited_edge')}
        builder.require(record['executables'] == [descriptor] and record['source'] == 'benchmark/retention_control.cpp',
                        'unexpected timing descriptor')
        builder.require(all(type(record['executables'][0][name]) is type(descriptor[name]) for name in
                            ('sampling_policy','private_acceptance_mask','sampling_words_per_visited_edge')),
                        'wrong timing descriptor policy type')
        records.append(record)
    first,second = records
    for name in first['object_paths']:
        if name != 'kkt/kkt.o':
            builder.require((first['object_paths'][name],first['object_sha256'][name]) ==
                            (second['object_paths'][name],second['object_sha256'][name]),'shared object changed')
    builder.require(first['object_sha256']['kkt/kkt.o'] != second['object_sha256']['kkt/kkt.o'] and
                    first['binary_sha256'] != second['binary_sha256'],'missing native variant distinction')
    return records,receipts,sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True); args = parser.parse_args()
    output = args.output.resolve(strict=True); records,receipts,sources = checked_records(output)
    script_hash = builder.sha(__file__); build = ROOT/'.build/eighth-sampling/final-object-gate'
    binaries = ROOT/'bin/eighth-sampling/final-object-gate'
    builder.require(not build.exists() and not binaries.exists(),'refusing to overwrite final-object gate')
    build.mkdir(parents=True); binaries.mkdir(parents=True)
    first = records[0]; sdk = first['sdk']
    base = builder.NATIVE+['/usr/bin/clang++','-isysroot',sdk,*builder.FLAGS,'-I.']
    linkflags = [f'-L{sdk}/usr/lib','-Wl,-stack_size,0x20000000']
    guard = builder.SerialGuard(output/'final-object-owned-groups.json')
    logpath = output/'final-object-build.log'; commands = []; tests = []; rebuilds = []; negatives = []
    with logpath.open('x') as log:
        def run(command):
            commands.append(command); log.write('$ '+shlex.join(command)+'\n'); log.flush(); guard.run(command,stdout=log)
        main_object = build/'retention_control_test.o'
        run(base+['-c','test/retention_control_test.cpp','-o',str(main_object)])
        for record in records:
            variant = record['variant']; destination = build/variant; destination.mkdir()
            extra = ['-DKKT_EXPERIMENT_EIGHTH_SAMPLING'] if variant == 'eighth' else []
            rebuilt = destination/'kkt.o'
            run(base+extra+['-c','kkt/kkt.cpp','-o',str(rebuilt)])
            builder.require(builder.sha(rebuilt) == record['object_sha256']['kkt/kkt.o'],
                            'same-source same-flags rebuild differs from actual final KKT object')
            rebuilds.append({'variant':variant,'path':str(rebuilt),'sha256':builder.sha(rebuilt),
                             'matches_actual_object':record['object_paths']['kkt/kkt.o']})
            integration = destination/'eighth_sampling_integration_test.o'
            run(base+extra+['-c','test/eighth_sampling_integration_test.cpp','-o',str(integration)])
            for stem,objects in (
                    ('retention_control_test',list(record['object_paths'].values())+[str(main_object)]),
                    ('eighth_sampling_integration_test',[path for name,path in record['object_paths'].items()
                                                         if name != 'kkt/kkt.o']+[str(integration)])):
                binary = binaries/variant/stem; binary.parent.mkdir(parents=True,exist_ok=True)
                run(base+objects+linkflags+['-o',str(binary)])
                binary_profile = builder.profile(binary); command = builder.NATIVE+[str(binary)]
                if stem == 'eighth_sampling_integration_test': command.append(variant)
                stdout_path,stderr_path = output/f'final-object-{variant}-{stem}.stdout',output/f'final-object-{variant}-{stem}.stderr'
                with stdout_path.open('x') as stdout,stderr_path.open('x') as stderr:
                    status = guard.run(command,stdout=stdout,stderr=stderr,check=False)
                tests.append({'variant':variant,'test':stem,'command':command,'exit_status':status,
                              'binary':str(binary),'binary_sha256':builder.sha(binary),'binary_profile':binary_profile,
                              'stdout':str(stdout_path),'stdout_sha256':builder.sha(stdout_path),
                              'stderr':str(stderr_path),'stderr_sha256':builder.sha(stderr_path),
                              'scope':'actual final production objects' if stem == 'retention_control_test' else
                              'same-flags source-inclusion RNG oracle; separate KKT object is not linked here'})
                builder.save(output/'final-object-tests.json',{'status':'running','tests':tests,'rebuilds':rebuilds})
                builder.require(status == 0,'final-object correctness gate failed')
                builder.check_focused_output(stem,variant,stdout_path.read_text())
                if stem == 'eighth_sampling_integration_test':
                    command = builder.NATIVE+[str(binary),'eighth' if variant == 'half' else 'half']
                    path = output/f'final-object-{variant}-wrong-policy.log'
                    with path.open('x') as stream: status = guard.run(command,stdout=stream,check=False)
                    message = path.read_text()
                    builder.require(status == 1 and 'FAIL: wrong private policy' in message and
                                    not any(token in message for token in ('ERROR: AddressSanitizer','ERROR: LeakSanitizer','runtime error:')),
                                    'wrong final-profile RNG policy accepted')
                    negatives.append({'command':command,'exit_status':status,'log':str(path),'sha256':builder.sha(path)})
    after,after_receipts,after_sources = checked_records(output)
    builder.require(records == after and receipts == after_receipts and sources == after_sources and
                    builder.sha(__file__) == script_hash,'final gate input drift')
    for item in rebuilds: builder.require(builder.sha(item['path']) == item['sha256'],'rebuilt KKT object drift')
    for item in tests: builder.require(builder.sha(item['binary']) == item['binary_sha256'],'gate executable drift')
    builder.require(len(tests) == 4 and len(negatives) == 2 and len(rebuilds) == 2,'incomplete final-object gate')
    builder.save(output/'final-object-tests.json',{'status':'pass','tests':tests,'wrong_policy_gates':negatives,'rebuilds':rebuilds,
        'build_commands':commands,'build_log':str(logpath),'build_log_sha256':builder.sha(logpath),
        'build_record_sha256':receipts,'script_sha256':script_hash,'main_object':str(main_object),
        'main_object_sha256':builder.sha(main_object),'performance_executed':False,'work_driver_executed':False,
        'dispatch_evidence':'Pinned source/macros, byte-identical separate object rebuild, same-flags source-inclusion RNG oracle, actual final-object MST certificates; no direct final-object private RNG trace.'})
    print(json.dumps({'status':'pass','tests':4,'wrong_policy_gates':2,'byte_identical_kkt_rebuilds':2,'performance_executed':False}))


if __name__ == '__main__': main()
