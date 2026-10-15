#!/usr/bin/env python3
"""Prepared untimed harness gate for the actual final compressed-query object sets.

Copy beside the prospective study's validation records after authorization.
This compiles/runs only retention_control_test, never the timing/work driver.
"""
import argparse
import json
from pathlib import Path
import shlex
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--validation',type=Path,required=True)
    args = parser.parse_args(); root = args.root.resolve(strict=True); output = args.validation.resolve(strict=True)
    sys.path.insert(0,str(root/'benchmark'))
    import build_compressed_queries as builder
    builder.require(builder.ROOT == root,'builder imported from the wrong worktree')
    paths = [output/f'timing-build-{variant}-build-record.json' for variant in builder.VARIANTS]
    records = [json.loads(path.read_text()) for path in paths]
    receipts = {str(path):builder.sha(path) for path in paths}
    initial_sources = builder.inventory(); script_hash = builder.sha(__file__)
    for variant,record in zip(builder.VARIANTS,records):
        builder.require(record['schema'] == 'compressed_query_build_v1' and record['profile'] == 'timing-build' and
                        record['variant'] == variant and record['source_sha256'] == initial_sources,'wrong/stale final build record')
        builder.check_source_contract(Path(record['parent_edge_freeze']))
        builder.require(record['build_exit_status'] == 0 and record['reference_source_textually_unchanged'] is True and
                        record['scalar_sampling_fixed'] is True,'missing declared source gates')
        for name,path in record['object_paths'].items(): builder.require(builder.sha(path) == record['object_sha256'][name],'stale production object')
        builder.require(builder.sha(record['main_object']) == record['main_object_sha256'] and
                        builder.sha(record['binary']) == record['binary_sha256'],'stale timing harness/binary')
        builder.require(not any('WORK_STATS' in flag or 'NDEBUG' in flag or 'PACKED_SAMPLING' in flag
                                for flag in record['common_compile_flags']),'wrong final instrumentation/assertion/sampling flags')
    first,second = records
    for name in first['object_paths']:
        if name != 'verifier/verifier_v2.o':
            builder.require((first['object_paths'][name],first['object_sha256'][name]) ==
                            (second['object_paths'][name],second['object_sha256'][name]),'non-verifier object differs')
    builder.require(first['object_sha256']['verifier/verifier_v2.o'] != second['object_sha256']['verifier/verifier_v2.o'],
                    'verifier objects unexpectedly identical')
    base_command = first['build_commands'][0]; base = base_command[:base_command.index('-c')]
    main_object = root/'.build/compressed-query/final-object-gate/retention_control_test.o'
    builder.require(not main_object.parent.exists(),'refusing to overwrite final-object gate')
    main_object.parent.mkdir(parents=True)
    logpath = output/'final-object-harness-build.log'; commands = []; tests = []
    guard = builder.SerialGuard(output/'final-object-harness-owned-groups.json')
    with logpath.open('x') as log:
        def build(command):
            commands.append(command); log.write('$ '+shlex.join(command)+'\n'); log.flush(); guard.run(command,stdout=log)
        build(base+['-c','test/retention_control_test.cpp','-o',str(main_object)])
        for record in records:
            variant = record['variant']; binary = root/'bin/compressed-query/final-object-gate'/variant/'retention_control_test'
            binary.parent.mkdir(parents=True,exist_ok=True)
            build(base+list(record['object_paths'].values())+[str(main_object),f"-L{record['sdk']}/usr/lib",'-Wl,-stack_size,0x20000000','-o',str(binary)])
            profile = builder.profile(binary); stdout_path = output/f'final-object-{variant}-harness.stdout'
            stderr_path = output/f'final-object-{variant}-harness.stderr'; command = builder.NATIVE+[str(binary)]
            with stdout_path.open('x') as stdout,stderr_path.open('x') as stderr:
                status = guard.run(command,stdout=stdout,stderr=stderr,check=False)
            tests.append({'variant':variant,'command':command,'exit_status':status,'binary':str(binary),
                          'binary_sha256':builder.sha(binary),'binary_profile':profile,
                          'stdout':str(stdout_path),'stdout_sha256':builder.sha(stdout_path),
                          'stderr':str(stderr_path),'stderr_sha256':builder.sha(stderr_path)})
            builder.save(output/'final-object-harness-tests.json',{'status':'running','tests':tests})
            builder.require(status == 0,'actual final-object harness gate failed: '+variant)
    builder.require(initial_sources == builder.inventory() and builder.sha(__file__) == script_hash,'source/script changed during gates')
    for path,value in receipts.items(): builder.require(builder.sha(path) == value,'final build receipt changed')
    for record in records:
        for name,path in record['object_paths'].items(): builder.require(builder.sha(path) == record['object_sha256'][name],'final object changed during gate')
        builder.require(builder.sha(record['binary']) == record['binary_sha256'],'timing binary changed during gate')
    builder.save(output/'final-object-harness-tests.json',{'status':'pass','performance_executed':False,'work_driver_executed':False,
        'build_commands':commands,'build_log':str(logpath),'build_log_sha256':builder.sha(logpath),
        'build_record_sha256':receipts,'script_sha256':script_hash,'main_object':str(main_object),
        'main_object_sha256':builder.sha(main_object),'tests':tests})
    print(json.dumps({'status':'pass','tests':len(tests),'performance_executed':False}))


if __name__ == '__main__': main()
