#!/usr/bin/env python3
"""Recheck actual library/main/schema evidence without executing a solver."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path('/Users/random_person/Desktop/kkt-eighth-sampling')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'benchmark/current_complexity'))
import validate_build as gate


def main():
    build_path = HERE/'build-attempt04/inner/build-record.json'
    smoke_path = HERE/'smoke-attempt01/inner/schema-smoke.json'
    build = gate.check_record(build_path)
    details = gate.check_schema_smoke(smoke_path, build, gate.analyzer.SCHEMA_CONTRACT)
    bound = dict(build['bound_sha256'])
    for path in (smoke_path, HERE/'build-attempt04/receipt.json', HERE/'smoke-attempt01/receipt.json'):
        bound[str(path)] = gate.analyzer.digest(path)
    for name in ('build-attempt04', 'smoke-attempt01'):
        value = gate.read(HERE/name/'receipt.json')
        for key, expected in dict(validation='pass', exit_status=0, outer_group_verified_empty=True,
                                  detached_native_groups_verified_empty=True,
                                  all_owned_groups_verified_empty=True).items():
            gate.exact(value[key], expected, 'outer proof '+key)
    affected = {}
    for name, count in (('validator-tests', 6), ('producer-tests', 3), ('outer-tests', 4)):
        path = HERE/'archive-index-repair-attempt01'/(name+'.json')
        value = gate.read(path)
        gate.exact(value['validation'], 'pass', 'affected mocks')
        gate.exact(value['exit_status'], 0, 'affected mock exit')
        gate.exact(value['owned_groups_verified_empty'], True, 'affected mock group')
        gate.analyzer.check_bound(value['source_sha256_after'])
        bound[str(path)] = gate.analyzer.digest(path)
        affected[name] = count
    failed = {}
    for number in range(1, 4):
        path = HERE/f'build-attempt{number:02d}'/'receipt.json'
        audit = path.parent/'independent-exit-audit.json'
        gate.exact(gate.read(path)['validation'], 'failed', 'preserve failed attempt')
        gate.exact(gate.read(audit)['all_owned_groups_verified_empty'], True, 'failed group audit')
        failed[str(path)] = gate.analyzer.digest(path)
        bound[str(path)] = failed[str(path)]
        bound[str(audit)] = gate.analyzer.digest(audit)
    gate.analyzer.check_bound(bound)
    result = dict(schema='current_complexity_readiness_v1', validation='pass',
                  readiness_scope='actual build/schema gates ready for declaration commit; no study capture',
                  build_record=str(build_path), schema_smoke=str(smoke_path),
                  binary=build['binary'], binary_sha256=build['binary_sha256'],
                  library_sha256=build['library_sha256'], google_benchmark_commit=gate.COMMIT,
                  checked_library_objects=len(build['library_object_sha256']),
                  checked_production_objects=len(build['object_paths']),
                  checked_curves=details['checked_curves'], checked_raw_rows=details['checked_raw_rows'],
                  checked_certificates=details['checked_certificates'],
                  schema_smoke_used_in_study_analysis=False, performance_capture_executed=False,
                  affected_mock_groups=affected, failed_attempts_preserved=failed, bound_sha256=bound)
    output=HERE/'readiness-attempt01.json'
    with output.open('x') as stream:
        json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({key: result[key] for key in ('validation','checked_library_objects',
        'checked_production_objects','checked_curves','checked_raw_rows','checked_certificates')}))


if __name__ == '__main__':
    main()
