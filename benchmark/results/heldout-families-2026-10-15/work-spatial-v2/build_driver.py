#!/usr/bin/env python3
"""Compile only the spatial diagnostic frontend and validate every declared family."""
import importlib.util
import json
import os
from pathlib import Path
import shlex
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'benchmark'))
import build_compressed_queries as builder

OLD_MODULE = HERE.parent / 'work/collect.py'
OLD_FREEZE = HERE.parent / 'work/freeze.json'
OLD_FREEZE_SHA256 = 'db107c2370735e7bdcec777320ea069374c8247d8d02ba67684528541561bcaf'
OLD_DRIVER = ROOT / builder.WORK_SOURCE
OLD_LINE = '            require(spec.family == "gnm_random", "unsupported diagnostic family");'
NEW_LINE = ('            require(spec.family == "gnm_random" || spec.family == "line_metric" ||\n'
            '                    spec.family == "line_random" || spec.family == "grid2d_metric" ||\n'
            '                    spec.family == "grid2d_random", "unsupported diagnostic family");')
spec = importlib.util.spec_from_file_location('spatial_driver_original_work', OLD_MODULE)
old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
require, sha, save = builder.require, builder.sha, builder.save
BUILD = ROOT / '.build/heldout-spatial-work-attempt02'
BINARY = ROOT / 'bin/heldout-spatial-work-attempt02/retention_work'
DRIVER = HERE / 'driver.cpp'
MAIN = BUILD / 'driver.o'
RECORD = HERE / 'build-record.json'
GATES = HERE / 'frontend-gates.json'
GROUPS = HERE / 'owned-groups-attempt02.json'
LOG = HERE / 'build-attempt02.log'
ENVIRONMENT_POLICY = {'CPATH': None, 'LIBRARY_PATH': None}
FAMILIES = {'leaf_distance4','leaf_shuffled4','line_metric','line_random','grid2d_metric','grid2d_random'}


def parent_proof():
    require(sha(OLD_FREEZE) == OLD_FREEZE_SHA256, 'original work freeze changed')
    frozen = old.check_freeze(OLD_FREEZE)
    artifact = frozen['artifact']
    build_path = Path(artifact['instrumented_build_record'])
    parent = old.analysis.read_json(build_path)
    original = OLD_DRIVER.read_text()
    require(sha(OLD_DRIVER) == builder.WORK_SOURCE_SHA256, 'original driver changed')
    require(original.count(OLD_LINE) == 1 and DRIVER.read_text() == original.replace(OLD_LINE, NEW_LINE),
            'driver differs beyond exact family allowlist expansion')
    gates = [row for row in frozen['schedule'] if row['n'] == 1024 and row['density'] == 32]
    require(len(gates) == 12 and {(r['family'],r['graph_seed']) for r in gates} ==
            {(f,g) for f in FAMILIES for g in (9000011,9000049)} and
            all(r['kkt_seed'] == 2003 for r in gates), 'wrong small family gate matrix')
    return frozen, parent, build_path, gates


def commands(parent):
    base = builder.NATIVE + ['/usr/bin/clang++','-isysroot',parent['sdk'],
                            *parent['common_compile_flags'],'-I.']
    compile_command = base + ['-c',str(DRIVER.relative_to(ROOT)),'-o',str(MAIN)]
    link_command = base + list(parent['object_paths'].values()) + [str(MAIN),
                    '-L'+parent['sdk']+'/usr/lib','-Wl,-stack_size,0x20000000','-o',str(BINARY)]
    return [compile_command,link_command]


def check_groups(groups, expected):
    require(len(groups) == len(expected), 'missing/extra build or gate group')
    for row, command in zip(groups, expected):
        clean = row['cleanup']; proof = clean.get('group_verification',{})
        require(row['command'] == command and type(row['exit_status']) is int and row['exit_status'] == 0,
                'wrong owned command/status')
        require(type(row.get('process_group')) is int and row['process_group'] > 0 and
                clean.get('native_exit_known') is True and clean.get('group_exit_known') is True and
                clean.get('native_process_may_still_be_running') is False and
                type(clean.get('returncode')) is int and clean['returncode'] == 0 and
                proof.get('validation') == 'pass' and proof.get('members') == [] and
                type(proof.get('process_group')) is int and
                proof['process_group'] == row['process_group'], 'owned group exit not proved')


def check_record(path=RECORD):
    frozen, parent, parent_path, gates = parent_proof()
    record = old.analysis.read_json(Path(path))
    expected = dict(schema='heldout_spatial_work_build_v1',validation='pass',working_directory=str(ROOT),
        parent_work_freeze=str(OLD_FREEZE),parent_work_freeze_sha256=OLD_FREEZE_SHA256,
        parent_build_record=str(parent_path),parent_build_record_sha256=sha(parent_path),
        parent_driver=str(OLD_DRIVER),parent_driver_sha256=builder.WORK_SOURCE_SHA256,
        source=str(DRIVER.relative_to(ROOT)),source_sha256=sha(DRIVER),source_delta={'old':OLD_LINE,'new':NEW_LINE},
        builder=str(Path(__file__).resolve()),builder_sha256=sha(__file__),
        compiler=parent['compiler'],compiler_command=parent['compiler_command'],sdk=parent['sdk'],
        common_compile_flags=parent['common_compile_flags'],production_source_sha256=parent['source_sha256'],
        object_paths=parent['object_paths'],object_sha256=parent['object_sha256'],
        main_object=str(MAIN),main_object_sha256=sha(MAIN),binary=str(BINARY),binary_sha256=sha(BINARY),
        build_commands=commands(parent),compile_command=commands(parent)[0],link_command=commands(parent)[1],
        build_exit_status=0,role='untimed_work_frontend',production_objects_rebuilt=False,
        build_environment_policy=ENVIRONMENT_POLICY,
        performance_executed=False,gate_receipt=str(GATES),gate_receipt_sha256=sha(GATES),
        owned_groups=str(GROUPS),owned_groups_sha256=sha(GROUPS))
    for key, value in expected.items():
        require(type(record.get(key)) is type(value) and record[key] == value, 'build binding differs: '+key)
    require(record['binary_profile']['file_description'] == 'Mach-O 64-bit executable arm64' and
            record['binary_profile']['main_stack_bytes'] == 536870912, 'wrong native binary profile')
    for name, value in record['object_paths'].items():
        require(sha(value) == record['object_sha256'][name], 'original production object changed')
    proof = old.analysis.read_json(GATES)
    require(proof['validation'] == 'pass' and len(proof['tests']) == 12 and proof['schedule'] == gates,
            'frontend gates incomplete')
    for key, value in dict(schema='heldout_spatial_frontend_gates_v1',expected_solver_outputs=36,
                          expected_counter_fields=65,expected_replay_chains=24,checked_solver_outputs=36,
                          checked_counter_fields=65,checked_replay_chains=24,native_execution=True,
                          performance_executed=False).items():
        require(type(proof.get(key)) is type(value) and proof[key] == value, 'wrong gate metadata: '+key)
    for gate, declaration in zip(proof['tests'], gates):
        require(gate['spec'] == declaration and type(gate['exit_status']) is int and gate['exit_status'] == 0
                and gate['command'] == old.command(str(BINARY),declaration), 'wrong gate identity/status')
        value = old.check_output(Path(gate['stdout']), declaration)
        old.native.check_certificate(Path(gate['stderr']), [value])
        for key in ('stdout','stderr'): old.analysis.hash_check(Path(gate[key]), gate[key+'_sha256'])
    expected_commands = commands(parent) + [old.command(str(BINARY), declaration) for declaration in gates]
    check_groups(old.analysis.read_json(GROUPS)['groups'], expected_commands)
    bound = dict(frozen['bound_sha256'])
    for dependency in (OLD_FREEZE,OLD_MODULE,DRIVER,Path(__file__).resolve(),parent_path,
                       LOG,MAIN,BINARY,GATES,GROUPS,
                       *[Path(test[key]) for test in proof['tests'] for key in ('stdout','stderr')]):
        bound[str(dependency)] = sha(dependency)
    require(record['bound_sha256'] == bound, 'incomplete or changed complete build binding')
    require(record['build_log'] == str(LOG) and record['build_log_sha256'] == sha(LOG), 'build log changed')
    require(type(record.get('removed_environment')) is dict and set(record['removed_environment']) == set(ENVIRONMENT_POLICY)
            and all(value is None or type(value) is str for value in record['removed_environment'].values()),
            'missing original ambient search-path record')
    for dependency, digest in record['bound_sha256'].items():
        old.analysis.hash_check(Path(dependency), digest)
    return record


def main():
    require(sys.argv[1:] == ['--released-small-gates'], 'explicit small-gate release required')
    require(not RECORD.exists() and not GATES.exists() and not GROUPS.exists() and
            not BUILD.exists() and not BINARY.parent.exists(), 'refusing prior build/gate artifacts')
    frozen,parent,parent_path,gates = parent_proof()
    initial = dict(frozen['bound_sha256'])
    initial.update({str(OLD_FREEZE):sha(OLD_FREEZE),str(OLD_MODULE):sha(OLD_MODULE),
                    str(DRIVER):sha(DRIVER),str(Path(__file__).resolve()):sha(__file__),
                    str(parent_path):sha(parent_path)})
    require(builder.checked_output(parent['compiler_command']) == parent['compiler'], 'current compiler differs')
    require(builder.checked_output(['/usr/bin/xcrun','--show-sdk-path']).strip() == parent['sdk'], 'current SDK differs')
    environment = os.environ.copy()
    removed = {name:environment.pop(name,None) for name in ENVIRONMENT_POLICY}
    BUILD.mkdir(); BINARY.parent.mkdir(parents=True)
    guard = builder.SerialGuard(GROUPS)
    log = LOG
    with log.open('x') as stream:
        for command in commands(parent):
            stream.write('$ '+shlex.join(command)+'\n'); stream.flush()
            guard.run(command,stdout=stream,env=environment)
    native_profile = builder.profile(BINARY)
    require('arm64' in builder.checked_output(['/usr/bin/file','-b',str(MAIN)]), 'translated new main')
    proof = dict(schema='heldout_spatial_frontend_gates_v1',validation='running',schedule=gates,tests=[],
                 expected_solver_outputs=36,expected_counter_fields=65,expected_replay_chains=24,
                 native_execution=True,performance_executed=False)
    save(GATES,proof,exclusive=True)
    for index,declaration in enumerate(gates):
        stdout = HERE / f'gate-{index:02d}.json'
        stderr = HERE / f'gate-{index:02d}.stderr'
        command = old.command(str(BINARY),declaration)
        with stdout.open('x') as out, stderr.open('x') as err:
            status = guard.run(command,stdout=out,stderr=err)
        value = old.check_output(stdout,declaration)
        old.native.check_certificate(stderr,[value])
        proof['tests'].append(dict(spec=declaration,command=command,exit_status=status,
            stdout=str(stdout),stdout_sha256=sha(stdout),stderr=str(stderr),stderr_sha256=sha(stderr)))
        save(GATES,proof)
    proof.update(validation='pass',checked_solver_outputs=36,checked_counter_fields=65,checked_replay_chains=24)
    save(GATES,proof)
    require(parent_proof()[0] == frozen, 'original full proof changed during build/gates')
    for path,digest in initial.items(): old.analysis.hash_check(Path(path),digest)
    bound = dict(initial)
    for path in (log,MAIN,BINARY,GATES,GROUPS,*[Path(test[key]) for test in proof['tests'] for key in ('stdout','stderr')]):
        bound[str(path)] = sha(path)
    record = dict(schema='heldout_spatial_work_build_v1',validation='pass',working_directory=str(ROOT),
        parent_work_freeze=str(OLD_FREEZE),parent_work_freeze_sha256=OLD_FREEZE_SHA256,
        parent_build_record=str(parent_path),parent_build_record_sha256=sha(parent_path),
        parent_driver=str(OLD_DRIVER),parent_driver_sha256=builder.WORK_SOURCE_SHA256,
        source=str(DRIVER.relative_to(ROOT)),source_sha256=sha(DRIVER),source_delta={'old':OLD_LINE,'new':NEW_LINE},
        builder=str(Path(__file__).resolve()),builder_sha256=sha(__file__),
        compiler=parent['compiler'],compiler_command=parent['compiler_command'],sdk=parent['sdk'],
        common_compile_flags=parent['common_compile_flags'],production_source_sha256=parent['source_sha256'],
        object_paths=parent['object_paths'],object_sha256=parent['object_sha256'],
        main_object=str(MAIN),main_object_sha256=sha(MAIN),binary=str(BINARY),binary_sha256=sha(BINARY),
        binary_profile=native_profile,build_commands=commands(parent),compile_command=commands(parent)[0],link_command=commands(parent)[1],
        build_command=[sys.executable,'-B',str(Path(__file__).resolve()),'--released-small-gates'],
        build_log=str(log),build_log_sha256=sha(log),build_exit_status=0,role='untimed_work_frontend',
        production_objects_rebuilt=False,performance_executed=False,gate_receipt=str(GATES),gate_receipt_sha256=sha(GATES),
        build_environment_policy=ENVIRONMENT_POLICY,removed_environment=removed,
        owned_groups=str(GROUPS),owned_groups_sha256=sha(GROUPS),bound_sha256=bound)
    save(RECORD,record,exclusive=True)
    check_record(RECORD)
    print(json.dumps({'validation':'pass','build_commands':2,'native_small_inputs':12,
                     'solver_outputs':36,'replay_chains':24,'all_groups_verified_empty':True,
                     'record':str(RECORD),'record_sha256':sha(RECORD)}))


if __name__ == '__main__': main()
