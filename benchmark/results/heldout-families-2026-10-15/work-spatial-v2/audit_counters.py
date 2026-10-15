#!/usr/bin/env python3
"""Independently reconstruct raw diagnostic counters and tables after strict loading."""
import argparse
import csv
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ALGORITHMS = ('kkt','compacting_boruvka','multigraph_boruvka')
FAMILIES = ('leaf_distance4','leaf_shuffled4','grid2d_metric','grid2d_random','line_metric','line_random')
SIZES = (1024,4096,16384,65536,262144,1048576)
GRAPHS = (9000011,9000049)
CHAIN_FIELDS = ('contraction_calls','contraction_vertices','contraction_edges',
                'contraction_edge_visits','contraction_output_vertices','contraction_output_edges')


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
    return json.loads(Path(path).read_text(),object_pairs_hook=unique,parse_constant=nonfinite)


def field_names():
    pairs = re.findall(r'\{\s*"([a-z_0-9]+)"\s*,\s*&kkt_work::WorkStats::([a-z_0-9]+)\s*,\s*(?:true|false)\s*\}',
                       (ROOT/'benchmark/work_metrics.hpp').read_text())
    require(len(pairs) == len({name for name,member in pairs}) == 65 and all(name == member for name,member in pairs),
            'counter declarations are not 65 distinct member-bound fields')
    return [name for name,member in pairs]


def reconstruct(values,fields):
    tables = {name:[] for name in ('work','rounds','round_chains','query_work')}
    exact = []
    for spec,raw in values:
        n,m = spec['n'],spec['m']
        require(raw['certified_output_items'] == n-1 and set(raw['algorithms']) == set(ALGORITHMS),
                'wrong solver output coverage')
        for algorithm in ALGORITHMS:
            data = raw['algorithms'][algorithm]; stats = data['work']
            require(set(stats) == set(fields),'missing/extra counter')
            for name,value in stats.items():
                if algorithm != 'kkt' and name == 'hash_insert_items':
                    require(value is None,'unmeasured comparator hash count invented')
                else:
                    require(type(value) is int and 0 <= value < 2**64,'counter integer domain')
            require(data['hash_insert_items_status'] == ('measured' if algorithm == 'kkt' else 'unmeasured'),
                    'hash-count measurement status')
            tables['work'].append(dict(spec,algorithm=algorithm,hash_insert_items_status=data['hash_insert_items_status'],**stats))
            if algorithm == 'kkt': continue
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
            tables['round_chains'].append(dict(spec,algorithm=algorithm,round_count=len(replay),selected_edges=selected,
                                              **{field:stats[field] for field in CHAIN_FIELDS}))
        stats = raw['algorithms']['kkt']['work']
        q = stats['verifier_queries']; u = stats['path_query_visits']-q-q
        require(0 <= u <= q,'compressed request count outside logical range')
        quantities = {'Q':q,'U':u,'M':stats['verifier_tree_edges'],'T':stats['verifier_tree_calls'],
                      'Nsum':stats['fbt_output_vertices'],'collapsed_requests':q-u}
        row = dict(spec,**quantities,U_over_Q=float(Fraction(u,q)) if q else None,
                   query_fraction_status='defined' if q else 'both_zero')
        for name,value in quantities.items():
            fraction = Fraction(value,m)
            row[name+'_per_original_edge'] = float(fraction)
            exact.append(dict(spec,quantity=name,numerator=fraction.numerator,denominator=fraction.denominator))
        tables['query_work'].append(row)
    return tables,exact


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
    module_spec = importlib.util.spec_from_file_location('spatial_counter_audit_provenance',HERE/'collect.py')
    collector = importlib.util.module_from_spec(module_spec); module_spec.loader.exec_module(collector)
    capture = args.capture.resolve(strict=True); initial = sha(capture)
    info,_ = collector.load(capture)  # Provenance/lifecycle only; no aggregation helper is called.
    frozen = read_json(info['freeze']); specs = frozen['schedule']
    require(len(specs) == 72 and {(r['family'],r['n'],r['graph_seed']) for r in specs} ==
            {(family,n,graph) for family in FAMILIES for n in SIZES for graph in GRAPHS},'incomplete literal matrix')
    require(all(r['variant'] == 'compressed' and r['density'] == 32 and r['intrusion_per_mille'] == 0
                and r['kkt_seed'] == 2003 and r['m'] == 32*r['n'] for r in specs),'matrix parameters drift')
    values = []; input_hashes = {str(capture):initial,str(Path(__file__).resolve()):sha(__file__)}
    for spec,item in zip(specs,info['captures']):
        require(item['spec'] == spec,'capture order differs from frozen schedule')
        raw = read_json(item['raw'])
        for key in ('case_id','family','n','m','density','graph_seed','kkt_seed','input_fingerprint','topology_fingerprint'):
            require(type(raw[key]) is type(spec[key]) and raw[key] == spec[key],'raw timing fingerprint/input mismatch')
        require(sha(item['raw']) == item['raw_sha256'],'raw changed')
        input_hashes[item['raw']] = item['raw_sha256']; values.append((spec,raw))
    indexed = {(s['family'],s['n'],s['graph_seed']):r for s,r in values}
    twin_count = 0
    for first,second in (('leaf_distance4','leaf_shuffled4'),('grid2d_metric','grid2d_random'),('line_metric','line_random')):
        for n in SIZES:
            for graph in GRAPHS:
                a,b = indexed[first,n,graph],indexed[second,n,graph]
                require(a['topology_fingerprint'] == b['topology_fingerprint'] and
                        a['input_fingerprint'] != b['input_fingerprint'],'topology twin/weight control differs')
                twin_count += 1
    fields = field_names(); tables,exact = reconstruct(values,fields)
    require(len(tables['work']) == 216 and len(tables['round_chains']) == 144 and len(tables['query_work']) == 72,
            'incomplete reconstructed tables')
    nulls = sum(row['hash_insert_items'] is None for row in tables['work'])
    require(nulls == 144,'incorrect null counter coverage')
    for name,rows in tables.items():
        path = args.analysis_dir/(name+'.csv')
        digest = sha(path)
        check_table(path,rows)
        require(sha(path) == digest,'table changed during read')
        input_hashes[str(path.resolve())] = digest
    metadata_path = args.analysis_dir/'provenance.json'
    metadata_digest = sha(metadata_path)
    metadata = read_json(metadata_path)
    require(sha(metadata_path) == metadata_digest,'metadata changed during read')
    input_hashes[str(metadata_path.resolve())] = metadata_digest
    for key,value in dict(validation='pass',capture=str(capture),capture_sha256=initial,solver_rows=216,counter_fields=65,
                          counter_cells=14040,unmeasured_hash_counter_cells=144,replay_chains=144,
                          replay_round_rows=len(tables['rounds']),cumulative_query_rows=72,reference_compression_pairs=0,
                          performance_claim=False,memory_peak_claim=False,bound_sha256=info['bound_sha256']).items():
        require(type(metadata.get(key)) is type(value) and metadata[key] == value,'analysis provenance differs: '+key)
    for path,digest in {**info['bound_sha256'],**input_hashes}.items(): require(sha(path) == digest,'audit input drift')
    output.mkdir()
    with (output/'exact_query_normalizations.csv').open('x',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=list(exact[0])); writer.writeheader(); writer.writerows(exact)
    result = dict(validation='pass',counter_cells=14040,solver_rows=216,unmeasured_hash_counter_cells=nulls,
                  replay_chains=144,replay_round_rows=len(tables['rounds']),cumulative_query_rows=72,topology_twins=twin_count,
                  exact_normalizations=len(exact),aggregation_reused=False,native_execution=False,
                  input_sha256=input_hashes,bound_sha256=info['bound_sha256'])
    (output/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:value for key,value in result.items() if key not in ('input_sha256','bound_sha256')},indent=2))


if __name__ == '__main__': main()
