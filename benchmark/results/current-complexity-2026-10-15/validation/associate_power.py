#!/usr/bin/env python3
"""Correlate an already completed complexity capture with an archived power log.

Source prepared during capture; execute only after all owned groups are empty.
This adds diagnostics only and never filters or adjusts measured observations.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path('/Users/random_person/Desktop/kkt-eighth-sampling')
STUDY = ROOT / 'benchmark/results/current-complexity-2026-10-15'
COLLECTOR_SHA = '69c34734e478c43d158ecb01d2e77cdff4d1ad0274424be647723fc7e6bdc393'


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--released', action='store_true')
    args = parser.parse_args()
    require(args.released and Path.cwd().resolve() == ROOT, 'explicit postcapture release and fixed worktree required')
    collector_path = ROOT / 'benchmark/current_complexity/collect.py'
    require(sha(collector_path) == COLLECTOR_SHA, 'collector changed')
    sys.path.insert(0, str(collector_path.parent))
    import collect as collector
    sys.path.insert(0, str(ROOT / 'benchmark'))
    import audit_attachment_recovery_power as power

    capture = STUDY / 'capture-attempt01/capture.json'
    info, records, inherited = collector.load(capture)
    require(info['validation'] == 'pass' and len(records) == 24, 'incomplete capture')
    rows = []
    for record in records:
        current, _ = collector.check_rows(record['raw_csv'], record['spec'])
        rows.extend(current)
    require(len(rows) == 2376, 'incomplete native call matrix')

    query_path = STUDY / 'complexity-power-audit/query.json'
    log_path = STUDY / 'complexity-power-audit/pmset.log'
    query_digest = sha(query_path)
    query = collector.read_json(query_path)
    require(sha(query_path) == query_digest, 'power query receipt changed while reading')
    require(query['validation'] == 'pass' and type(query['exit_status']) is int and query['exit_status'] == 0,
            'power query did not succeed')
    require(query['command'] == ['/usr/bin/pmset', '-g', 'log'] and
            query['log_sha256'] == sha(log_path) and query['full_log_private_ignored'] is True,
            'power query/log identity mismatch')
    sources = [Path(__file__).resolve(), collector_path, query_path, log_path,
               Path(power.__file__).resolve(), Path(power.original.__file__).resolve()]
    bound = dict(inherited)
    require(str(query_path) not in bound or bound[str(query_path)] == query_digest,
            'conflicting query receipt provenance')
    bound[str(query_path)] = query_digest
    require(str(log_path) not in bound or bound[str(log_path)] == query['log_sha256'],
            'conflicting power log provenance')
    bound[str(log_path)] = query['log_sha256']
    for path in sources:
        digest = sha(path)
        require(str(path) not in bound or bound[str(path)] == digest, 'conflicting provenance')
        bound[str(path)] = digest

    events, malformed, reversals = power.parse_events(log_path.read_text(errors='replace'))
    # The established correlator consumes only the two UTC endpoints and copies
    # identity fields. Supply aliases locally, then publish native identities.
    aliases = [dict(case_id=f"{r['family']}/{r['n']}", graph_seed=r['graph_seed'],
                    kkt_seed=r['sampling_seed'], phase=r['phase'], repetition=r['invocation'],
                    order=r['iteration'], algorithm=r['algorithm'], elapsed_ns=r['elapsed_ns'],
                    process_cpu_elapsed_ns=r['process_cpu_elapsed_ns'],
                    utc_start_ns=r['utc_start_ns'], utc_end_ns=r['utc_end_ns']) for r in rows]
    associated = power.original.correlate(aliases, events, power.original.sleep_intervals(events))
    require(len(associated) == len(rows), 'association count mismatch')
    fields = ('utc_alignable', 'nominal_logged_sleep_overlap_ns', 'sleep_interval_indices',
              'overlap_has_unclosed_sleep', 'nearby_power_event_lines', 'excluded')
    output_rows = [{**row, **{key: association[key] for key in fields}}
                   for row, association in zip(rows, associated)]
    require(all(row['excluded'] is False for row in output_rows), 'unexpected excluded observation')
    collector.recheck(bound)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    with (output / 'call_power_associations.csv').open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]) + list(fields))
        writer.writeheader(); writer.writerows(output_rows)
    result = dict(schema='current_complexity_power_associations_v1', validation='pass',
                  checked_calls=len(rows), parser=power.PARSER, input_sha256=bound,
                  associations_sha256=sha(output / 'call_power_associations.csv'),
                  logged_overlap_calls=sum(bool(row['nominal_logged_sleep_overlap_ns']) for row in output_rows),
                  unalignable_calls=sum(not row['utc_alignable'] for row in output_rows),
                  malformed_event_lines=len(malformed), source_order_reversals=len(reversals),
                  rows_removed=0, rows_adjusted=0, sleep_inhibition_verified=False,
                  limitation='Successful archived query is not proof of complete log retention, continuous wakefulness, stable thermals or host idleness. No raw private events are published.')
    with (output / 'audit.json').open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'input_sha256'}))


if __name__ == '__main__':
    main()
