#!/usr/bin/env python3
"""Descriptive report tables from the completed, independently audited work CSVs.

No native launch and no collector aggregation. Counts are logical events, not
CPU costs. Every case, graph, solver and declared field remains in the outputs.
"""
import argparse
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SELECTED = ('sampled_edges', 'filtered_edges', 'contraction_edge_visits',
            'sampling_edge_visits', 'verifier_edge_visits', 'path_query_visits',
            'initialized_slots', 'edge_materializations')
ALGORITHMS = ('kkt', 'compacting_boruvka', 'multigraph_boruvka')


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(ok, message):
    if not ok: raise ValueError(message)
def rows(path):
    with Path(path).open(newline='') as stream: return list(csv.DictReader(stream))
def write_csv(path, values):
    with path.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(values[0]))
        writer.writeheader(); writer.writerows(values)
def bounds(values):
    defined = [v for v in values if v is not None]
    return (min(defined), max(defined)) if defined else (None, None)
def text(value): return '' if value is None else str(float(value))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve(); require(not output.exists(), 'output already exists')
    audit_path = HERE/'independent-counter-audit-attempt01/audit.json'
    inputs = {str(Path(__file__).resolve()): sha(__file__), str(audit_path): sha(audit_path)}
    audit = json.loads(audit_path.read_text())
    for name, value in dict(validation='pass', counter_cells=11700, solver_rows=180,
                           counter_fields=65, unmeasured_hash_counter_cells=120,
                           replay_chains=120, replay_round_rows=1236,
                           cumulative_query_rows=60, topology_twins=30,
                           exact_normalizations=11700, engine_words_exact=True).items():
        require(type(audit[name]) is type(value) and audit[name] == value, 'audit gate: '+name)
    def read_bound(path, csv_file=False):
        path = path.resolve(); digest = sha(path)
        require(audit['input_sha256'].get(str(path)) == digest, 'not bound by passed audit: '+str(path))
        inputs[str(path)] = digest
        return rows(path) if csv_file else json.loads(path.read_text())
    capture = read_bound(HERE/'capture-attempt01.json')
    work = read_bound(HERE/'analysis-attempt01/work.csv', True)
    chains = read_bound(HERE/'analysis-attempt01/round_chains.csv', True)
    query = read_bound(HERE/'analysis-attempt01/query_work.csv', True)
    require(len(work) == 180 and len(chains) == 120 and len(query) == 60, 'matrix counts')
    fields = list(work[0])[13:]; require(len(fields) == 65, 'counter inventory')
    index = {(r['case_id'], int(r['graph_seed']), r['algorithm']): r for r in work}
    require(len(index) == 180, 'duplicate work identity')
    for item in capture['captures']:
        raw = read_bound(Path(item['raw']))
        spec = item['spec']; key = (spec['case_id'], spec['graph_seed'])
        for alg in ALGORITHMS:
            row = index[key + (alg,)]
            for field in fields:
                count = raw['algorithms'][alg]['work'][field]
                require(row[field] == ('' if count is None else str(count)), 'raw/table counter mismatch')
    groups = {}
    for row in work:
        key = (row['family'], int(row['density']), int(row['n']))
        groups.setdefault(key, []).append(row)
    require(len(groups) == 30 and all(len(v) == 6 for v in groups.values()), 'case coverage')
    per_case, statuses, continuation = [], [], []
    chain_index = {(r['case_id'], int(r['graph_seed']), r['algorithm']): r for r in chains}
    query_index = {(r['case_id'], int(r['graph_seed'])): r for r in query}
    for (family, density, n), group in sorted(groups.items()):
        case = group[0]['case_id']; m = n*density
        identity = dict(case_id=case, family=family, density=density, n=n, m=m)
        record = dict(identity)
        for alg in ALGORITHMS:
            chosen = [r for r in group if r['algorithm'] == alg]
            require(len(chosen) == 2, 'graph/algorithm coverage')
            for field in fields:
                counts = [int(r[field]) if r[field] else None for r in chosen]
                lo, hi = bounds(counts)
                per_case.append(dict(identity, algorithm=alg, counter=field,
                    count_min=lo, count_max=hi, per_m_min=text(Fraction(lo,m) if lo is not None else None),
                    per_m_max=text(Fraction(hi,m) if hi is not None else None),
                    zero_count=sum(v == 0 for v in counts), unmeasured_count=sum(v is None for v in counts)))
            lo, hi = bounds([Fraction(int(r['contraction_edge_visits']),m) for r in chosen])
            record[alg+'_visits_per_m_min'],record[alg+'_visits_per_m_max'] = text(lo),text(hi)
            if alg != 'kkt':
                replay = [chain_index[(case, int(r['graph_seed']), alg)] for r in chosen]
                for field in ('rounds','edges_sum'):
                    vs = [Fraction(int(r[field]), m if field == 'edges_sum' else 1) for r in replay]
                    lo,hi = bounds(vs)
                    record[alg+'_'+field+'_min'], record[alg+'_'+field+'_max'] = text(lo),text(hi)
            else:
                for field in ('sampling_edge_visits','verifier_edge_visits','initialized_slots','edge_materializations','filtered_edges','verifier_edges'):
                    lo,hi = bounds([Fraction(int(r[field]),m) for r in chosen])
                    record[field+'_per_m_min'],record[field+'_per_m_max'] = text(lo),text(hi)
                for name, numerator, denominator in (('U_over_Q','U','Q'),):
                    vs = [query_index[(case,int(r['graph_seed']))] for r in chosen]
                    lo,hi = bounds([Fraction(int(v[numerator]),int(v[denominator])) if int(v[denominator]) else None for v in vs])
                    record[name+'_min'],record[name+'_max'] = text(lo),text(hi)
                lo,hi = bounds([Fraction(int(r['filtered_edges']),int(r['verifier_edges'])) if int(r['verifier_edges']) else None for r in chosen])
                record['light_retention_min'],record['light_retention_max'] = text(lo),text(hi)
        continuation.append(record)
        for graph in (23000003,23000029):
            kkt = index[(case,graph,'kkt')]
            for alg in ALGORITHMS[1:]:
                comp = index[(case,graph,alg)]
                for field in fields:
                    a,b = kkt[field],comp[field]
                    if not a or not b: state='unmeasured'; delta=None; ratio=None
                    else:
                        a,b=int(a),int(b); delta=a-b
                        state='lower' if a<b else 'higher' if a>b else 'equal'
                        ratio=Fraction(a,b) if b else None
                    statuses.append(dict(identity,graph_seed=graph,competitor=alg,counter=field,
                        kkt_count=kkt[field],competitor_count=comp[field],state=state,delta=delta,
                        ratio_status=('unmeasured' if state=='unmeasured' else 'defined' if ratio is not None else 'both_zero' if a==0 else 'zero_denominator'),
                        ratio_numerator=ratio.numerator if ratio is not None else None,
                        ratio_denominator=ratio.denominator if ratio is not None else None))
    require(len(per_case)==5850 and len(statuses)==7800 and len(continuation)==30, 'output matrix')
    for r in query:
        k = index[(r['case_id'],int(r['graph_seed']),'kkt')]
        require(int(r['engine_words']) == int(r['sampling_edge_visits']) == int(k['sampling_edge_visits']), 'engine count')
    summary = dict(validation='pass',scope='Descriptive logical counts only; no runtime or CPU attribution.',
        input_sha256=inputs,case_counter_ranges=len(per_case),paired_counter_statuses=len(statuses),
        continuation_cases=len(continuation),state_counts={s:sum(r['state']==s for r in statuses) for s in ('lower','higher','equal','unmeasured')},
        ratio_status_counts={s:sum(r['ratio_status']==s for r in statuses) for s in ('defined','both_zero','zero_denominator','unmeasured')},
        query_zero_denominators=sum(int(r['Q'])==0 for r in query))
    for path,digest in inputs.items(): require(sha(path)==digest, 'input changed')
    output.mkdir()
    write_csv(output/'all_counter_ranges.csv',per_case)
    write_csv(output/'selected_counter_ranges.csv',[r for r in per_case if r['counter'] in SELECTED])
    write_csv(output/'counter_comparisons.csv',statuses)
    write_csv(output/'continuation_summary.csv',continuation)
    summary['output_sha256']={p.name:sha(p) for p in output.iterdir()}
    (output/'provenance.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('input_sha256','output_sha256')},indent=2))


if __name__ == '__main__': main()
