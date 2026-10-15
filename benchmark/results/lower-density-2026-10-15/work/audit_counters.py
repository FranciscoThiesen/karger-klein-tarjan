#!/usr/bin/env python3
"""Reconstruct lower-density raw counters independently after strict loading.

The installed work collector supplies provenance/lifecycle only. This module
never calls its tables(), summarize() or query arithmetic. It runs no solver.
"""
import argparse
import csv
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ALGORITHMS = ('kkt','compacting_boruvka','multigraph_boruvka')
FAMILIES = ('leaf_distance4','leaf_shuffled4')
LADDERS = ((16,(512,2048,8192,32768,131072,524288,2097152)),
           (8,(256,1024,4096,16384,65536,262144,1048576,4194304)))
GRAPHS = (23000003,23000029)
SEED = 3407
SELECTED = ('sampled_edges','filtered_edges','contraction_edge_visits','sampling_edge_visits',
            'verifier_edge_visits','path_query_visits','initialized_slots','edge_materializations')


def require(condition,message):
    if not condition: raise ValueError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    def unique(pairs):
        result = {}
        for key,value in pairs:
            require(key not in result,'duplicate JSON key'); result[key] = value
        return result
    def nonfinite(value): raise ValueError('nonfinite JSON: '+value)
    def finite(value):
        parsed = float(value)
        require(math.isfinite(parsed),'nonfinite numeric overflow')
        return parsed
    return json.loads(Path(path).read_text(),object_pairs_hook=unique,parse_constant=nonfinite,parse_float=finite)


def bind(inputs,path,expected=None):
    path = Path(path).resolve(strict=True); actual = sha(path)
    require(expected is None or actual == expected,'changed audit input: '+str(path))
    require(str(path) not in inputs or inputs[str(path)] == actual,'conflicting audit input: '+str(path))
    inputs[str(path)] = actual
    return path


def provenance_load(capture):
    """Restore the temporary package path and named module after strict reload."""
    name = '_lower_density_counter_audit_provenance'
    previous_path, previous_module = sys.path[:], sys.modules.get(name)
    try:
        sys.path.insert(0,str(HERE))
        spec = importlib.util.spec_from_file_location(name,HERE/'collect.py')
        require(spec is not None and spec.loader is not None,'missing installed work collector')
        collector = importlib.util.module_from_spec(spec); sys.modules[name] = collector
        spec.loader.exec_module(collector)
        return collector.load(capture)[0]
    finally:
        sys.path[:] = previous_path
        if previous_module is None: sys.modules.pop(name,None)
        else: sys.modules[name] = previous_module


def declared():
    cases = [dict(variant='eighth',case_id=f'{family}_n{n}_d{density}_p0',family=family,n=n,m=n*density,
                  density=density,intrusion_per_mille=0)
             for density,sizes in LADDERS for n in sizes for family in FAMILIES]
    return [dict(case,graph_seed=graph,kkt_seed=SEED) for index,graph in enumerate(GRAPHS)
            for case in (cases if index == 0 else list(reversed(cases)))]


def validate_matrix(specs,values):
    expected = declared()
    require(len(specs) == len(values) == len(expected) == 60,'incomplete literal matrix')
    for spec,(identity,raw),wanted in zip(specs,values,expected):
        require(spec == identity and set(spec) == set(wanted) | {'input_fingerprint','topology_fingerprint'},
                'wrong schedule field set')
        for key,value in wanted.items():
            require(type(spec[key]) is type(value) and spec[key] == value,'declared input/order differs')
        for key in ('input_fingerprint','topology_fingerprint'):
            require(type(spec[key]) is int and 0 <= spec[key] < 2**64,'fingerprint domain')
        expected_raw = {key:value for key,value in spec.items() if key not in ('variant','intrusion_per_mille')}
        expected_raw.update(schema='retention_control_work_v1',validation='pass',certified_output_items=spec['n']-1)
        require(set(raw) == set(expected_raw) | {'algorithms','rounds'},'raw output schema differs')
        for key,value in expected_raw.items():
            require(type(raw[key]) is type(value) and raw[key] == value,'raw input/fingerprint differs')
    indexed = {(s['family'],s['density'],s['n'],s['graph_seed']):r for s,r in values}
    require(len(indexed) == 60,'duplicate raw input')
    count = 0
    for density,sizes in LADDERS:
        for n in sizes:
            for graph in GRAPHS:
                a,b = (indexed[family,density,n,graph] for family in FAMILIES)
                require(a['topology_fingerprint'] == b['topology_fingerprint'] and
                        a['input_fingerprint'] != b['input_fingerprint'],'topology twin/weight control differs')
                count += 1
    require(count == 30,'incomplete twin matrix')
    return count


def field_names():
    pairs = re.findall(r'\{\s*"([a-z_0-9]+)"\s*,\s*&kkt_work::WorkStats::([a-z_0-9]+)\s*,\s*(?:true|false)\s*\}',
                       (ROOT/'benchmark/work_metrics.hpp').read_text())
    require(len(pairs) == len({name for name,member in pairs}) == 65 and all(name == member for name,member in pairs),
            'counter declarations are not 65 distinct member-bound fields')
    return [name for name,member in pairs]


def reconstruct(values,fields):
    tables = {name:[] for name in ('work','rounds','round_chains','query_work','normalized_work')}
    for spec,raw in values:
        n,m = spec['n'],spec['m']
        require(type(raw['certified_output_items']) is int and raw['certified_output_items'] == n-1 and
                set(raw['algorithms']) == set(ALGORITHMS) and set(raw['rounds']) == set(ALGORITHMS[1:]),
                'wrong solver output coverage')
        for algorithm in ALGORITHMS:
            data = raw['algorithms'][algorithm]; stats = data['work']
            require(set(data) == {'work','hash_insert_items_status'},'wrong solver record schema')
            require(set(stats) == set(fields),'missing/extra counter')
            for name,value in stats.items():
                if algorithm != 'kkt' and name == 'hash_insert_items':
                    require(value is None,'unmeasured comparator hash count invented')
                else:
                    require(type(value) is int and 0 <= value < 2**64,'counter integer domain')
            require(data['hash_insert_items_status'] == ('measured' if algorithm == 'kkt' else 'unmeasured'),
                    'hash-count measurement status')
            tables['work'].append(dict(spec,algorithm=algorithm,hash_insert_items_status=data['hash_insert_items_status'],**stats))
            require(stats['current_depth'] == 0,'unwound recursion differs')
            require(stats['contraction_edge_visits'] <= (4 if algorithm == 'compacting_boruvka' else 3) *
                    stats['contraction_edges'],'contraction scan bound')
            for field in fields:
                value = stats[field]; fraction = Fraction(value,m) if value is not None else None
                tables['normalized_work'].append(dict(spec,algorithm=algorithm,counter=field,count=value,
                    per_original_edge=float(fraction) if fraction is not None else None,
                    numerator=fraction.numerator if fraction is not None else None,
                    denominator=fraction.denominator if fraction is not None else None,
                    status='defined' if fraction is not None else 'unmeasured'))
            if algorithm == 'kkt':
                require(stats['hash_insert_items'] == n-1,'KKT unique certified output differs')
                require(stats['sampling_calls'] == stats['verifier_calls'] and
                        stats['sampling_edge_visits'] == stats['verifier_edges'] and
                        stats['sampled_edges'] <= stats['sampling_edge_visits'] and
                        (stats['sampling_calls'] > 0 or stats['sampling_edge_visits'] == 0),
                        'sample/verifier accounting differs')
                continue
            require(all(stats[key] == 0 for key in ('kkt_calls','sampling_calls','verifier_calls')),
                    'comparator invokes recursive sampler')
            replay = raw['rounds'][algorithm]
            vertices,edges,selected = n,m,0
            totals = {'vertices':0,'edges':0,'output_vertices':0,'output_edges':0}
            for index,row in enumerate(replay):
                require(set(row) == {'round','vertices','edges','selected','output_vertices','output_edges'}
                        and all(type(value) is int and 0 <= value < 2**64 for value in row.values()),'round schema/domain')
                require((row['round'],row['vertices'],row['edges']) == (index,vertices,edges),'broken round chain')
                require(row['output_vertices'] <= vertices//2 and row['output_edges'] <= edges,'round failed to shrink')
                require((row['output_vertices'] == 0) == (row['output_edges'] == 0),'terminal graph mismatch')
                remaining = row['output_vertices'] if row['output_edges'] else 1
                require(row['selected'] == vertices-remaining,'connected selected-edge count')
                selected += row['selected']
                for key in totals: totals[key] += row[key]
                vertices,edges = row['output_vertices'],row['output_edges']
                tables['rounds'].append(dict(spec,algorithm=algorithm,**row))
            require(vertices == edges == 0 and selected == n-1 and stats['contraction_calls'] == len(replay),
                    'incomplete replay')
            for field,total in totals.items():
                require(stats['contraction_'+field] == total,'round sum differs from actual helper counters')
            tables['round_chains'].append(dict(spec,algorithm=algorithm,rounds=len(replay),
                **{field+'_sum':sum(row[field] for row in replay)
                   for field in ('vertices','edges','selected','output_vertices','output_edges')}))
        stats = raw['algorithms']['kkt']['work']
        retained = raw['rounds']['multigraph_boruvka']
        after = retained[1] if len(retained) >= 2 else {'output_vertices':0,'output_edges':0}
        require((stats['root_after_two_vertices'],stats['root_after_two_edges']) ==
                (after['output_vertices'],after['output_edges']),'root differs from retained replay')
        if spec['family'] == 'leaf_distance4':
            require((stats['root_after_two_vertices'],stats['root_after_two_edges']) == (n//8,m-7*n//8),
                    'ordered exact root dimensions differ')
        q = stats['verifier_queries']; u = stats['path_query_visits']-q-q
        require(0 <= u <= q,'compressed request count outside logical range')
        quantities = {'Q':q,'U':u,'M':stats['verifier_tree_edges'],'T':stats['verifier_tree_calls'],
                      'Nsum':stats['fbt_output_vertices'],'collapsed_requests':q-u}
        row = dict(spec,**quantities,U_over_Q=float(Fraction(u,q)) if q else None,
                   query_fraction_status='defined' if q else 'both_zero',
                   sampling_calls=stats['sampling_calls'],sampling_edge_visits=stats['sampling_edge_visits'],
                   engine_words=stats['sampling_edge_visits'],engine_word_method='exact_scalar_one_draw_per_visited_edge')
        tables['query_work'].append(row)
    return tables


def check_table(path,expected):
    with Path(path).open(newline='') as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames is not None and len(reader.fieldnames) == len(set(reader.fieldnames)), 'duplicate CSV header')
        rows = list(reader)
    require(len(rows) == len(expected),'table row count: '+str(path))
    for actual,wanted in zip(rows,expected):
        require(set(actual) == set(wanted),'table field identity: '+str(path))
        for key,value in wanted.items():
            require(actual[key] == ('' if value is None else str(value)), 'table value differs: '+str(path)+' '+key)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',type=Path,required=True)
    parser.add_argument('--analysis-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args = parser.parse_args(); output = args.output_dir.resolve()
    require(not output.exists(),'refusing audit overwrite')
    capture = args.capture.resolve(strict=True); initial = sha(capture)
    input_hashes = {str(capture):initial,str(Path(__file__).resolve()):sha(__file__)}
    bind(input_hashes,HERE/'collect.py')
    info = provenance_load(capture)  # Provenance/lifecycle only; no aggregation helper is called.
    for path,digest in info['bound_sha256'].items(): bind(input_hashes,path,digest)
    frozen = read_json(bind(input_hashes,info['freeze'],info['freeze_sha256'])); specs = frozen['schedule']
    require(frozen['schema'] == 'lower_density_work_freeze_v1','wrong freeze schema')
    require(len(specs) == len(info['captures']) == 60,'incomplete capture children')
    values = []
    for spec,item in zip(specs,info['captures']):
        require(item['spec'] == spec,'capture order differs from frozen schedule')
        raw = read_json(bind(input_hashes,item['raw'],item['raw_sha256']))
        for key,digest in (('log','log_sha256'),('rss_log','rss_sha256')):
            bind(input_hashes,item[key],item[digest])
        values.append((spec,raw))
    twin_count = validate_matrix(specs,values)
    bind(input_hashes,ROOT/'benchmark/work_metrics.hpp')
    fields = field_names(); tables = reconstruct(values,fields)
    require(len(tables['work']) == 180 and len(tables['round_chains']) == 120 and len(tables['query_work']) == 60 and
            len(tables['normalized_work']) == 11700,
            'incomplete reconstructed tables')
    require(any(row['Q'] > 0 for row in tables['query_work']),'no positive query witness')
    nulls = sum(row['hash_insert_items'] is None for row in tables['work'])
    require(nulls == 120 and sum(row['status'] == 'unmeasured' for row in tables['normalized_work']) == 120,
            'incorrect null counter coverage')
    for name,rows in tables.items():
        path = bind(input_hashes,args.analysis_dir/(name+'.csv'))
        digest = input_hashes[str(path)]
        check_table(path,rows)
        require(sha(path) == digest,'table changed during read')
    metadata_path = bind(input_hashes,args.analysis_dir/'provenance.json')
    metadata_digest = input_hashes[str(metadata_path)]
    metadata = read_json(metadata_path)
    require(sha(metadata_path) == metadata_digest,'metadata changed during read')
    for key,value in dict(schema='lower_density_work_analysis_v1',validation='pass',capture=str(capture),
                          capture_sha256=initial,expected_children=60,expected_solver_outputs=180,counter_cells=11700,
                          unmeasured_hash_cells=120,replay_chains=120,query_rows=60,topology_twins=30,
                          table_counts={name:len(rows) for name,rows in tables.items()},selected_fields=list(SELECTED),
                          counter_boundary=info['counter_boundary'],engine_words_exact=True,
                          performance_claim=False,bound_sha256=info['bound_sha256']).items():
        require(type(metadata.get(key)) is type(value) and metadata[key] == value,'analysis provenance differs: '+key)
    for path,digest in input_hashes.items(): require(sha(path) == digest,'audit input drift')
    output.mkdir()
    with (output/'exact_counter_normalizations.csv').open('x',newline='') as stream:
        rows = tables['normalized_work']
        writer = csv.DictWriter(stream,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    for path,digest in input_hashes.items(): require(sha(path) == digest,'audit input drift after export')
    result = dict(schema='independent_lower_density_work_counter_audit_v1',validation='pass',counter_cells=11700,
                  solver_rows=180,counter_fields=65,unmeasured_hash_counter_cells=nulls,
                  replay_chains=120,replay_round_rows=len(tables['rounds']),cumulative_query_rows=60,topology_twins=twin_count,
                  exact_normalizations=11700,engine_words_exact=True,aggregation_reused=False,native_execution=False,
                  strict_collector_imported_for_provenance=True,
                  scope='Independent raw numeric/schema/schedule/twin/table reconstruction. Certificates, lifecycle and native build proof are supplied by the unchanged strict collector; no runtime inference.',
                  input_sha256=input_hashes,output_sha256={'exact_counter_normalizations.csv':sha(output/'exact_counter_normalizations.csv')})
    (output/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:value for key,value in result.items() if key not in ('input_sha256','output_sha256')},indent=2))


if __name__ == '__main__': main()
