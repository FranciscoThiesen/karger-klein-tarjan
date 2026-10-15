#!/usr/bin/env python3
"""Describe a complete strictly validated diagnostic capture; never run a solver."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import re
import statistics

import collect as work


def median_ratio(values):
    return float(statistics.median(values)) if values else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--analysis', type=Path, required=True)
    args = parser.parse_args()
    info, values = work.load(args.capture.resolve(strict=True))
    output = args.analysis.resolve(strict=True)
    provenance = work.analysis.read_json(output/'provenance.json')
    work.require(provenance['capture_sha256'] == work.native.sha(args.capture), 'analysis belongs to another capture')
    names = ('counter_difference_summary.csv', 'case_counter_ratios.csv', 'paired_engine_word_bounds.csv',
             'report.json', 'README.md')
    work.require(all(not (output/name).exists() for name in names), 'refusing to overwrite diagnostic report')
    pairs = {}
    for spec, value in values:
        key = tuple(spec[name] for name in ('case_id', 'graph_seed', 'kkt_seed'))
        pairs.setdefault(key, {})[spec['variant']] = (spec, value['algorithms']['kkt']['work'])
    work.require(len(pairs) == 24 and all(set(pair) == {'scalar', 'packed'} for pair in pairs.values()), 'incomplete work pairs')
    summary, cases, bounds = [], {}, []
    for field in work.FIELDS:
        a = [pair['scalar'][1][field] for pair in pairs.values()]
        b = [pair['packed'][1][field] for pair in pairs.values()]
        ratios = [Fraction(y,x) for x,y in zip(a,b) if x]
        summary.append(dict(counter=field, pairs=24, decreased=sum(y<x for x,y in zip(a,b)),
            unchanged=sum(y==x for x,y in zip(a,b)), increased=sum(y>x for x,y in zip(a,b)),
            zero_denominators=sum(x==0 for x in a), both_zero=sum(x==y==0 for x,y in zip(a,b)),
            delta_min=min(y-x for x,y in zip(a,b)), delta_median=statistics.median(y-x for x,y in zip(a,b)),
            delta_max=max(y-x for x,y in zip(a,b)), ratio_min=float(min(ratios)) if ratios else None,
            ratio_median=median_ratio(ratios), ratio_max=float(max(ratios)) if ratios else None))
    for (case, graph, seed), pair in pairs.items():
        spec, scalar = pair['scalar']; packed = pair['packed'][1]
        groups = cases.setdefault(case, {name: [] for name in work.FIELDS})
        for field in work.FIELDS: groups[field].append((scalar[field], packed[field]))
        lower, upper, method = work.engine_bounds(packed, 'packed')
        words = scalar['sampling_edge_visits']
        bounds.append(dict(case_id=case, graph_seed=graph, kkt_seed=seed,
            scalar_engine_words=words, packed_engine_words_lower=lower, packed_engine_words_upper=upper,
            packed_over_scalar_lower=float(Fraction(lower,words)) if words else None,
            packed_over_scalar_upper=float(Fraction(upper,words)) if words else None,
            ratio_status='defined' if words else 'both_zero' if upper==0 else 'scalar_zero', method=method))
    case_rows = []
    for case, counters in sorted(cases.items()):
        for field, pairs_for_field in counters.items():
            ratios = [Fraction(b,a) for a,b in pairs_for_field if a]
            case_rows.append(dict(case_id=case,counter=field,pairs=len(pairs_for_field),
                ratio_median=median_ratio(ratios),ratio_min=float(min(ratios)) if ratios else None,
                ratio_max=float(max(ratios)) if ratios else None,
                zero_denominators=sum(a==0 for a,b in pairs_for_field)))
    work.require(len(summary)==65 and len(case_rows)==390 and len(bounds)==24, 'incomplete report tables')
    for name, rows in (('counter_difference_summary',summary),('case_counter_ratios',case_rows),
                       ('paired_engine_word_bounds',bounds)):
        work.analysis.write_csv(output/(name+'.csv'),rows)
    fields = ('sampling_edge_visits','verifier_queries','path_query_visits','initialized_slots','edge_materializations')
    indexed = {(row['case_id'],row['counter']): row for row in case_rows}
    lines = ['# Packed-sampling untimed work diagnostics', '',
        'All 48 declared children completed and produced 144 certified solver outputs. Every native result matched '
        'the independently certified MST exactly. All 48 owned groups were observed empty before continuation; '
        'strict reanalysis accepted the complete frozen matrix, fingerprints, resource evidence, raw files and build provenance.', '',
        'The nine mocked collector test groups passed on attempt 01 before capture. No performance timing is reported here. '
        'Diagnostic durations and sampled RSS include generation, certification, all three solvers and replay overhead.', '',
        'All 65 KKT fields are retained in `counter_difference_summary.csv` and every individual difference is in '
        '`paired_kkt_work.csv` (24 pairs × 65 fields = 1,560 rows). Each summary field records decreases, equality, increases, '
        'all difference ranges and all defined count-ratio ranges. Zero denominators remain explicit. '
        'Both comparator implementations have exactly equal counters and replay rounds across variants and sampler seeds '
        'for every fixed case/graph pair.', '',
        'The table below gives medians of the four paired packed/scalar count ratios for each case. These are logical work '
        'counts, not speedups, instructions or bytes. The WorkStats boundary includes tuple-to-Edge input construction, '
        'the solver and temporary input destruction; certification, output checking and round replays are outside it.', '',
        '| Case | Sampling edge visits | Verifier queries | Path-query visits | Initialized slots | Edge materializations |',
        '|---|---:|---:|---:|---:|---:|']
    for case in sorted(cases):
        numbers = [indexed[(case,field)]['ratio_median'] for field in fields]
        lines.append('| '+case+' | '+' | '.join('undefined' if x is None else f'{x:.6f}' for x in numbers)+' |')
    lines += ['', 'The scalar sampler consumes exactly `sampling_edge_visits` engine words. For packed sampling, '
        'the existing aggregate counters only establish `ceil(M/32) <= W <= min(M, floor((M+31*C)/32))`, '
        'where M and C are that packed run’s sampled-input volume and call count. Candidate and reference volumes may differ. '
        'The next table retains the minimum lower bound and maximum upper bound over all four paired realizations in each case. '
        'It does not pretend that aggregate M/32 is an observed exact count.', '',
        '| Case | Packed/scalar engine-word ratio: enclosing bounds |', '|---|---:|']
    for case in sorted(cases):
        points = [row for row in bounds if row['case_id']==case]
        defined = [row for row in points if row['ratio_status']=='defined']
        text = (f"[{min(row['packed_over_scalar_lower'] for row in defined):.8f}, "
                f"{max(row['packed_over_scalar_upper'] for row in defined):.8f}]") if len(defined)==4 else 'see explicit zero-denominator rows'
        lines.append('| '+case+' | '+text+' |')
    lines += ['', 'Packed sampling changes which MT bits supply Bernoulli decisions, so samples and recursive work may change '
        'even with the same seed. These diagnostics measure that changed work for every declared realization; they do not '
        'isolate CPU cost per engine draw or establish asymptotic complexity. Logical materialization counters do not include '
        'implicit vector-growth relocation or allocator costs. Consult the separate paired timing analysis for runtime evidence.', '']
    (output/'README.md').write_text('\n'.join(lines))
    for path,digest in info['bound_sha256'].items(): work.analysis.hash_check(Path(path),digest)
    for item in info['captures']:
        for field,digest in (('raw','raw_sha256'),('log','log_sha256'),('rss_log','rss_sha256')):
            work.analysis.hash_check(Path(item[field]),item[digest])
    result = dict(schema='packed_work_report_v1',status='pass',capture=str(args.capture.resolve()),
        capture_sha256=work.native.sha(args.capture),script_sha256=work.native.sha(__file__),
        certified_solver_outputs=144,known_empty_owned_groups=48,counter_fields=65,individual_counter_pairs=1560,
        per_case_counter_rows=390,paired_engine_bounds=24,comparator_counters_and_rounds_identical=True,
        output_sha256={name:work.native.sha(output/name) for name in names if name!='report.json'})
    work.write_json(output/'report.json',result,exclusive=True)
    print(json.dumps(result,indent=2))


if __name__ == '__main__': main()
