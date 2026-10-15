#!/usr/bin/env python3
"""Descriptive work-count tables from a complete strict-validated capture."""
import argparse
from collections import defaultdict
from fractions import Fraction
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('spatial_mechanism_capture',HERE/'collect.py')
work = importlib.util.module_from_spec(spec); spec.loader.exec_module(work)


def summarize(capture,output):
    capture = capture.resolve(strict=True); digest = work.native.sha(capture)
    source = Path(__file__).resolve(); source_digest = work.native.sha(source)
    info,values = work.load(capture)
    work.require(not output.exists(),'refusing mechanism table overwrite')
    rows = []
    for identity,value in values:
        k = value['algorithms']['kkt']['work']
        b = value['algorithms']['multigraph_boruvka']['work']
        c = value['algorithms']['compacting_boruvka']['work']
        q = k['verifier_queries']; u = k['path_query_visits']-2*q
        original_m = identity['m']
        row = {key:identity[key] for key in ('case_id','family','n','m','graph_seed','kkt_seed')}
        row.update(retained_rounds=len(value['rounds']['multigraph_boruvka']),
                   dedup_rounds=len(value['rounds']['compacting_boruvka']),
                   kkt_cumulative_contraction_calls=k['contraction_calls'])
        ratios = dict(
            retained_contraction_visits_per_input_edge=Fraction(b['contraction_edge_visits'],original_m),
            dedup_contraction_visits_per_input_edge=Fraction(c['contraction_edge_visits'],original_m),
            kkt_contraction_visits_per_input_edge=Fraction(k['contraction_edge_visits'],original_m),
            kkt_sampling_visits_per_input_edge=Fraction(k['sampling_edge_visits'],original_m),
            kkt_verifier_visits_per_input_edge=Fraction(k['verifier_edge_visits'],original_m),
            cumulative_filter_retained_fraction=Fraction(k['filtered_edges'],k['verifier_edges']) if k['verifier_edges'] else None,
            cumulative_U_over_Q=Fraction(u,q) if q else None)
        for name,ratio in ratios.items():
            row[name] = float(ratio) if ratio is not None else None
            row[name+'_numerator'] = ratio.numerator if ratio is not None else None
            row[name+'_denominator'] = ratio.denominator if ratio is not None else None
        rows.append(row)
    work.require(len(rows) == 72,'incomplete mechanism matrix')
    groups = defaultdict(list)
    for row in rows: groups[row['family'],row['n']].append(row)
    ranges = []
    metrics = [name for name in rows[0] if name not in ('case_id','family','n','m','graph_seed','kkt_seed')
               and not name.endswith(('_numerator','_denominator'))]
    for (family,n),pair in sorted(groups.items()):
        work.require(len(pair) == 2 and {row['graph_seed'] for row in pair} == {9000011,9000049},'missing graph realization')
        row = dict(family=family,n=n,m=pair[0]['m'],graph_realizations=2)
        for name in metrics:
            present = [value[name] for value in pair if value[name] is not None]
            row[name+'_defined_count'] = len(present)
            row[name+'_minimum'] = min(present) if present else None
            row[name+'_maximum'] = max(present) if present else None
        ranges.append(row)
    work.require(len(ranges) == 36,'incomplete family/size table')
    output.mkdir(parents=True)
    work.analysis.write_csv(output/'per_input.csv',rows)
    work.analysis.write_csv(output/'family_size_ranges.csv',ranges)
    work.analysis.hash_check(capture,digest)
    work.analysis.hash_check(source,source_digest)
    raw_hashes = {item[field]:item[field+'_sha256'] for item in info['captures'] for field in ('raw','log')}
    raw_hashes.update({item['rss_log']:item['rss_sha256'] for item in info['captures']})
    for path,expected in {**info['bound_sha256'],**raw_hashes}.items():
        work.analysis.hash_check(Path(path),expected)
    work.write_json(output/'provenance.json',dict(schema='heldout_work_mechanism_tables_v1',validation='pass',
        capture=str(capture),capture_sha256=digest,source=str(source),source_sha256=source_digest,
        bound_sha256=info['bound_sha256'],raw_sha256=raw_hashes,
        input_rows=72,family_size_rows=36,graph_realizations_per_case=2,performance_claim=False,
        interval_meaning='Minimum and maximum across two graph seeds; descriptive, not confidence intervals.',
        filter_fraction_scope='Cumulative filtered_edges/verifier_edges across all recursive verifier calls; not a root-only removal fraction.',
        query_fraction_scope='Sum of per-call distinct requests U divided by cumulative endpoint requests Q; not global uniqueness.',
        contraction_scope='Comparator rounds are one full contraction chain; KKT calls are cumulative across recursion and not directly comparable round counts.',
        output_sha256={name:work.native.sha(output/name) for name in ('per_input.csv','family_size_ranges.csv')}),exclusive=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args = parser.parse_args(); summarize(args.capture,args.output_dir.resolve())
