#!/usr/bin/env python3
"""Read completed readiness artifacts; do not launch builds or native tests."""
import importlib.util
import json
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'benchmark'))
import build_eighth_sampling as builder
import run_eighth_sampling as collector


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


phase = load_module('readiness_build_phase', HERE / 'run_build_phase.py')
require = builder.require
inputs = {}


def pin(path, expected=None):
    path = Path(path).resolve(strict=True)
    digest = builder.sha(path)
    require(expected is None or digest == expected, 'hash differs: ' + str(path))
    inputs[str(path)] = digest
    return digest


def read(path):
    pin(path)
    return collector.analysis.read_json(Path(path))


def arm64(path, executable=False):
    with Path(path).open('rb') as source:
        header = source.read(32)
        magic, cpu, _, kind, commands, size, _, _ = struct.unpack('<8I', header)
        require(magic == 0xfeedfacf and cpu == 0x0100000c, 'non-arm64 artifact')
        if not executable:
            require(kind == 1, 'not an object file')
            return
        require(kind == 2, 'not an executable')
        data = source.read(size)
    offset = 0
    stacks = []
    for _ in range(commands):
        command, length = struct.unpack_from('<II', data, offset)
        require(length >= 8 and offset + length <= len(data), 'bad load command')
        if command == 0x80000028:
            stacks.append(struct.unpack_from('<Q', data, offset + 16)[0])
        offset += length
    require(offset == size and stacks == [536870912], 'wrong executable stack')


def policy(record, variant):
    for key, expected in {'sampling_policy': variant,
                          'private_acceptance_mask': 1 if variant == 'half' else 7,
                          'sampling_words_per_visited_edge': 1}.items():
        require(type(record.get(key)) is type(expected) and record[key] == expected,
                'wrong typed policy: ' + key)
    require(record['verifier_policy'] == 'compressed', 'verifier policy changed')


def main():
    pin(__file__)
    parent, sources = builder.check_source_contract(builder.PARENT_PATH)
    require(parent == collector.parent_record(builder.PARENT_PATH), 'parent proofs differ')
    variants = {}
    for variant in builder.VARIANTS:
        path = HERE / f'timing-build-{variant}-build-record.json'
        record = read(path)
        checked = collector.build_record(path, Path(record['binary']), ROOT,
                                         parent, builder.PARENT_PATH, variant)
        variants[variant] = {'build': checked}
        arm64(record['binary'], True)
    collector.check_pair(variants)
    phases = {'controller-mocks': ('controller-mocks', 4),
              'build-mocks': ('build-mocks', 7), 'collector-mocks': ('collector-mocks', 14),
              'native-correctness': ('native-controller', 0),
              'sanitizer-correctness': ('sanitizer-controller', 0),
              'timing-build': ('timing-controller', 0), 'final-objects': ('final-controller', 0)}
    phase_summary = {}
    for name, (prefix, mocks) in phases.items():
        receipt = read(HERE / f'{prefix}-attempt01.json')
        require(receipt['validation'] == 'pass' and type(receipt['exit_status']) is int
                and receipt['exit_status'] == 0 and receipt['phase'] == name, 'phase did not pass')
        require(receipt['all_owned_groups_verified_empty'] is True, 'groups not proved empty')
        require(receipt['source_sha256_before'] == receipt['source_sha256_after'], 'phase source drift')
        for path, digest in receipt['source_sha256_after'].items(): pin(path, digest)
        for key in ('stdout', 'stderr'): pin(receipt[key], receipt[key + '_sha256'])
        require(receipt['performance_execution_authorized'] is False
                and receipt['work_driver_execution_authorized'] is False, 'forbidden execution authorized')
        require(receipt['outer_wrapper_exit_observed_monotonic_ns'] - receipt['started_monotonic_ns']
                <= receipt['command_deadline_seconds'] * 10**9, 'late phase exit')
        require(phase.check_inner(name) == receipt['inner_proof'], 'inner proof changed')
        if mocks:
            text = Path(receipt['stderr']).read_text()
            require(f'Ran {mocks} tests in ' in text and text.rstrip().endswith('OK'), 'mock count missing')
        phase_summary[name] = {'mock_groups': mocks, **receipt['inner_proof']}
    coverage = {}
    for profile in ('native-correctness', 'sanitizer-correctness', 'timing-build'):
        records = {}
        for variant in builder.VARIANTS:
            record = read(HERE / f'{profile}-{variant}-build-record.json')
            require(record['source_sha256'] == sources, 'current source inventory differs')
            require(record['build_exit_status'] == 0, 'failed build')
            for key, expected in {'sampling_policy': variant,
                                  'private_acceptance_mask': 1 if variant == 'half' else 7,
                                  'sampling_words_per_visited_edge': 1}.items():
                require(type(record[key]) is type(expected) and record[key] == expected, 'build policy differs')
            pin(record['build_log'], record['build_log_sha256'])
            for path, digest in record['build_recipe_sha256'].items(): pin(ROOT / path, digest)
            for name, path in record['object_paths'].items():
                pin(path, record['object_sha256'][name]); arm64(path)
            for executable in record['executables']:
                policy(executable, variant)
                pin(executable['binary'], executable['binary_sha256'])
                pin(executable['main_object'], executable['main_object_sha256'])
                arm64(executable['binary'], True); arm64(executable['main_object'])
            records[variant] = record
        for name in records['half']['object_paths']:
            if name != 'kkt/kkt.o':
                require(records['half']['object_paths'][name] == records['eighth']['object_paths'][name]
                        and records['half']['object_sha256'][name] == records['eighth']['object_sha256'][name],
                        'non-KKT object differs')
        require(records['half']['object_sha256']['kkt/kkt.o'] != records['eighth']['object_sha256']['kkt/kkt.o'],
                'KKT policy object missing')
        if profile == 'timing-build': continue
        proof = read(HERE / f'{profile}-tests.json')
        expected = {(variant, Path(source).stem) for variant in builder.VARIANTS for source in builder.TESTS}
        require(len(proof['tests']) == 20 and {(x['variant'], x['test']) for x in proof['tests']} == expected,
                'missing correctness suite')
        require(proof['performance_executed'] is False and proof['work_driver_executed'] is False, 'forbidden native execution')
        for test in proof['tests']:
            require(type(test['exit_status']) is int and test['exit_status'] == 0, 'positive failed')
            pin(test['command'][2], test['binary_sha256'])
            for key in ('stdout', 'stderr'): pin(test[key], test[key + '_sha256'])
            builder.check_focused_output(test['test'], test['variant'], Path(test['stdout']).read_text())
        require(len(proof['wrong_policy_gates']) == 4, 'missing negative gates')
        for test in proof['wrong_policy_gates']:
            require(type(test['exit_status']) is int and test['exit_status'] == 1, 'negative did not reject')
            pin(test['log'], test['sha256'])
        pair = proof['sampling_pair']
        computed = builder.compare_sampling(pair['half_records'], pair['eighth_records'])
        computed['wrong_sampling_record_substitution'] = builder.reject_substitution(builder.compare_sampling, pair['half_records'])
        require(computed == pair, 'sampling pair differs')
        replay = proof['parent_half_replay']
        require(builder.compare_half_parent(replay['parent_records'], replay['fresh_records']) == replay, 'parent replay differs')
        coverage[profile] = {'positive': 20, 'negative': 4, 'records': 1344, 'counter_fields': 65,
                             'changed_recursive_work_pairs': computed['different_recursive_work_pairs'],
                             'half_parent_replay': 'exact'}
    final = read(HERE / 'final-object-tests.json')
    require(final['status'] == 'pass' and len(final['tests']) == 4 and len(final['wrong_policy_gates']) == 2
            and len(final['rebuilds']) == 2, 'final-object coverage differs')
    pin(HERE / 'validate_final_objects.py', final['script_sha256'])
    pin(final['build_log'], final['build_log_sha256']); pin(final['main_object'], final['main_object_sha256'])
    for path, digest in final['build_record_sha256'].items(): pin(path, digest)
    for test in final['tests']:
        for key in ('binary', 'stdout', 'stderr'): pin(test[key], test[key + '_sha256'])
        arm64(test['binary'], True)
    require(sum(t['scope'] == 'actual final production objects' for t in final['tests']) == 2,
            'actual-object certificate suite missing')
    for test in final['wrong_policy_gates']: pin(test['log'], test['sha256'])
    for rebuilt in final['rebuilds']:
        pin(rebuilt['path'], rebuilt['sha256']); pin(rebuilt['matches_actual_object'], rebuilt['sha256'])
    require(final['performance_executed'] is False and final['work_driver_executed'] is False, 'forbidden final execution')
    for path, digest in list(inputs.items()): pin(path, digest)
    print(json.dumps({'schema': 'eighth_independent_readiness_v1', 'validation': 'pass',
        'review_native_execution': False, 'parent_freeze_sha256': builder.PARENT_SHA256,
        'timing_binary_sha256': {v: variants[v]['build']['record']['binary_sha256'] for v in builder.VARIANTS},
        'seven_non_kkt_objects_and_timing_main_shared': True, 'coverage': coverage,
        'final_object_coverage': {'positive': 4, 'negative': 2, 'byte_identical_rebuilds': 2},
        'phases': phase_summary, 'input_sha256': inputs,
        'scope': 'Read-only proof/hash/receipt reload; no native tests, builds, performance, freeze or commit.'}, indent=2))


if __name__ == '__main__': main()
