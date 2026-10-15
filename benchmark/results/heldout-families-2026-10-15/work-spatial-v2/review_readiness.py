#!/usr/bin/env python3
"""Read-only completed adapter, native artifact and prospective freeze review."""
import json
from pathlib import Path
import collect


def main():
    work = Path(__file__).resolve().parent
    freeze = work/'freeze.json'
    expected = 'cd6e7a349f689879af04b6b458bfd9a6db16ecfdf10e8fd93b134310e8e09663'
    collect.analysis.hash_check(freeze,expected)
    original = collect.engine.check_freeze
    checked = collect.check_freeze(freeze)
    with collect.configured():
        collect.require(collect.engine.check_freeze is collect.check_freeze, 'adapter not installed in scope')
        collect.require(collect.check_freeze(freeze) == checked, 'scoped full parent proof differs')
    collect.require(collect.engine.check_freeze is original, 'parent checker was not restored')
    record = collect.builder.check_record()
    parent = collect.parent()
    for field in ('object_paths','object_sha256'):
        collect.require(record[field] == parent['artifact'][field], 'original production objects changed')
    collect.require(len(record['build_commands']) == 2 and len(record['object_paths']) == 8, 'build scope differs')
    collect.require(record['build_environment_policy'] == {'CPATH':None,'LIBRARY_PATH':None}, 'recovery differs')
    collect.require(record['removed_environment'] == {'CPATH':'/usr/local/include','LIBRARY_PATH':'/usr/local/lib'},
                    'original ambient search paths differ')
    collect.require(checked['schedule'] == parent['schedule'] and checked['prior_successes_reused'] == 0
                    and len(checked['schedule']) == 72, 'fresh full matrix differs')
    receipts = {}
    for name in ('mocks-attempt02.json','prepare-attempt01.json','check-freeze-attempt01.json',
                 'build-controller-attempt02.json'):
        path = work/name; data = collect.analysis.read_json(path)
        collect.require(data['validation'] == 'pass' and type(data['exit_status']) is int and data['exit_status'] == 0,
                        'completed readiness phase failed')
        empty = data.get('all_owned_groups_verified_empty',data.get('owned_groups_verified_empty'))
        collect.require(empty is True, 'readiness phase groups not proved empty')
        for field in ('stdout','stderr'): collect.analysis.hash_check(Path(data[field]),data[field+'_sha256'])
        if 'source_sha256_after' in data:
            collect.require(data['source_sha256_after'] == data['source_sha256_before'], 'phase source changed')
            for dependency,digest in data['source_sha256_after'].items():
                collect.analysis.hash_check(Path(dependency),digest)
        receipts[str(path)] = collect.native.sha(path)
    failure = collect.analysis.read_json(work/'build-failure-audit-attempt01.json')
    collect.require(failure['validation'] == 'pass' and failure['all_owned_groups_verified_empty'] is True
                    and failure['native_small_gates_executed'] == 0, 'failed attempt cleanup not preserved')
    for dependency,digest in failure['artifacts_sha256'].items():
        collect.analysis.hash_check(Path(dependency),digest)
    print(json.dumps(dict(validation='pass',scope='Read-only artifact and full parent proof reload; no native execution',
        freeze_sha256=expected,bound_files=len(checked['bound_sha256']),fresh_children=72,solver_outputs=216,
        replay_chains=144,prior_successes_reused=0,original_production_objects=8,new_build_commands=2,
        small_family_inputs=12,small_solver_outputs=36,small_replay_chains=24,
        binary_sha256=record['binary_sha256'],build_record_sha256=collect.native.sha(work/'build-record.json'),
        recorded_environment_only_recovery=True,parent_checker_restored=True,readiness_receipt_sha256=receipts),indent=2))


if __name__ == '__main__': main()
