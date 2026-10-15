#!/usr/bin/env python3
"""Independent descriptive counter review; no collector import or native call."""
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import statistics

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
FIELDS=re.findall(r'\{"(\w+)", &kkt_work::WorkStats::\w+, (?:true|false)\}',
                  (ROOT/'benchmark/work_metrics.hpp').read_text())
SELECTED=('sampled_edges','filtered_edges','contraction_edge_visits','sampling_edge_visits',
          'verifier_edge_visits','path_query_visits','initialized_slots','edge_materializations')


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def read_csv(path):
    with path.open(newline='') as f:return list(csv.DictReader(f))
def identity(row):return tuple(str(row[k]) for k in ('variant','case_id','graph_seed','kkt_seed'))
def write_csv(path,rows):
    with path.open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def ratio(a,b):return Fraction(b,a) if a else None
def stats(values):
    defined=[v for v in values if v is not None]
    return {'defined':len(defined),'minimum':str(min(defined)) if defined else None,
            'median':str(statistics.median(defined)) if defined else None,
            'maximum':str(max(defined)) if defined else None,
            'median_float':float(statistics.median(defined)) if defined else None}


def main():
    out=HERE/'mechanism-review-attempt01';assert not out.exists()
    audit_path=HERE/'independent-counter-audit-attempt01/audit.json'
    capture_path=HERE/'capture-attempt01.json';analysis=HERE/'analysis-attempt01'
    own=Path(__file__).resolve()
    audit=json.loads(audit_path.read_text());capture=json.loads(capture_path.read_text())
    assert audit['validation']==capture['validation']=='pass'
    expected={'checked_children':48,'solver_rows':144,'counter_fields':65,'counter_cells':9360,
              'unmeasured_hash_counter_cells':96,'replay_chains':96,'replay_round_rows':1000,
              'query_rows':48,'paired_kkt_counter_rows':1560}
    for k,v in expected.items():assert type(audit[k]) is int and audit[k]==v
    inputs=dict(audit['input_sha256'])
    for p in [own,audit_path,capture_path,ROOT/'benchmark/work_metrics.hpp',ROOT/'kkt/kkt.cpp',
              ROOT/'kkt/experimental_eighth_sampling.hpp',ROOT/'verifier/experimental_compressed_queries.hpp',
              ROOT/'verifier/verifier_v2.cpp',HERE/'plot_work.py']:
        h=sha(p);assert str(p) not in inputs or inputs[str(p)]==h;inputs[str(p)]=h
    for p,h in inputs.items():assert sha(Path(p))==h,p
    assert len(FIELDS)==len(set(FIELDS))==65
    records={};pairs={};controls={};nulls=0;chains=0;round_count=0;root_rows=[]
    for item in capture['captures']:
        p=Path(item['raw']);assert sha(p)==item['raw_sha256'];raw=json.loads(p.read_text());spec=item['spec']
        key=identity(spec);assert key not in records;records[key]=raw
        assert raw['validation']=='pass' and raw['certified_output_items']==spec['n']-1
        for k in ('case_id','graph_seed','kkt_seed','family','n','m','density','input_fingerprint','topology_fingerprint'):
            assert type(raw[k]) is type(spec[k]) and raw[k]==spec[k]
        kkt=raw['algorithms']['kkt']['work'];assert set(kkt)==set(FIELDS)
        pairs.setdefault(key[1:],{})[spec['variant']]=(spec,kkt)
        sig={name:(raw['algorithms'][name],raw['rounds'][name]) for name in ('compacting_boruvka','multigraph_boruvka')}
        control_key=(spec['case_id'],spec['graph_seed'])
        assert control_key not in controls or controls[control_key]==sig;controls[control_key]=sig
        retained=raw['rounds']['multigraph_boruvka'][1]
        assert (kkt['root_after_two_vertices'],kkt['root_after_two_edges'])==(retained['output_vertices'],retained['output_edges'])
        root_rows.append({**spec,'root_vertices':kkt['root_after_two_vertices'],'root_edges':kkt['root_after_two_edges']})
        for algorithm,record in raw['algorithms'].items():
            assert set(record['work'])==set(FIELDS)
            for field,value in record['work'].items():
                if algorithm!='kkt' and field=='hash_insert_items':assert value is None;nulls+=1
                else:assert type(value) is int and 0<=value<2**64
        for name,chain in raw['rounds'].items():
            chains+=1;round_count+=len(chain)
            assert sum(r['selected'] for r in chain)==spec['n']-1
            assert len(chain)==raw['algorithms'][name]['work']['contraction_calls']
    assert (len(records),len(pairs),len(controls),nulls,chains,round_count)==(48,24,12,96,96,1000)
    tables={name:read_csv(analysis/(name+'.csv')) for name in ('work','paired_kkt_work','query_work','round_chains','rounds')}
    assert [len(tables[k]) for k in tables]==[144,1560,48,96,1000]
    seen=set();cells=0
    for row in tables['work']:
        key=(*identity(row),row['algorithm']);assert key not in seen;seen.add(key)
        record=records[key[:4]]['algorithms'][key[4]]
        assert row['hash_insert_items_status']==record['hash_insert_items_status']
        for field,value in record['work'].items():assert row[field]==('' if value is None else str(value));cells+=1
    assert cells==9360
    seen=set()
    for row in tables['paired_kkt_work']:
        key=tuple(row[k] for k in ('case_id','graph_seed','kkt_seed'));field=row['counter']
        assert (*key,field) not in seen;seen.add((*key,field))
        a=pairs[key]['half'][1][field];b=pairs[key]['eighth'][1][field];r=ratio(a,b)
        assert (int(row['half']),int(row['eighth']),int(row['eighth_minus_half']))==(a,b,b-a)
        assert row['ratio_status']==('defined' if a else 'both_zero' if b==0 else 'half_zero')
        assert row['eighth_over_half']=='' if r is None else float(row['eighth_over_half'])==float(r)
    query_rows=[]
    for row in tables['query_work']:
        raw=records[identity(row)];w=raw['algorithms']['kkt']['work'];q=w['verifier_queries'];u=w['path_query_visits']-2*q
        assert 0<=u<=q and q==2*w['verifier_tree_edges'] and w['sampling_edge_visits']==w['verifier_edges']
        for field,value in dict(Q=q,U=u,M=w['verifier_tree_edges'],T=w['verifier_tree_calls'],Nsum=w['fbt_output_vertices'],
                                collapsed_requests=q-u,engine_words=w['sampling_edge_visits'],sampling_edge_visits=w['sampling_edge_visits'],sampling_calls=w['sampling_calls']).items():
            assert int(row[field])==value
        assert row['query_fraction_status']==('defined' if q else 'both_zero')
        assert float(row['U_over_Q'])==float(Fraction(u,q)) if q else row['U_over_Q']==''
        query_rows.append({**{k:row[k] for k in ('variant','case_id','graph_seed','kkt_seed')},'Q':q,'U':u,
            'U_over_Q':str(Fraction(u,q)) if q else None,'engine_words':w['sampling_edge_visits']})
    for row in tables['round_chains']:
        chain=records[identity(row)]['rounds'][row['algorithm']];assert int(row['rounds'])==len(chain)
        for field in ('vertices','edges','selected','output_vertices','output_edges'):
            assert int(row[field+'_sum'])==sum(r[field] for r in chain)
    for row in tables['rounds']:
        actual=records[identity(row)]['rounds'][row['algorithm']][int(row['round'])]
        for field,value in actual.items():assert int(row[field])==value
    case_order=list(dict.fromkeys(item['spec']['case_id'] for item in capture['captures']))
    summaries=[];global_status=[]
    for case in case_order:
        group=[v for k,v in pairs.items() if k[0]==case];assert len(group)==4
        for field in FIELDS:
            values=[(v['half'][1][field],v['eighth'][1][field]) for v in group]
            summaries.append({'case_id':case,'counter':field,**stats([ratio(a,b) for a,b in values]),
                'decrease':sum(b<a for a,b in values),'increase':sum(b>a for a,b in values),
                'equal_positive':sum(a==b and a>0 for a,b in values),'both_zero':sum(a==b==0 for a,b in values),
                'half_zero':sum(a==0 and b>0 for a,b in values),'eighth_zero_half_positive':sum(a>0 and b==0 for a,b in values)})
    for field in FIELDS:
        group=[r for r in summaries if r['counter']==field]
        global_status.append({'counter':field,**{name:sum(r[name] for r in group) for name in
            ('defined','decrease','increase','equal_positive','both_zero','half_zero','eighth_zero_half_positive')}})
    roots={}
    for row in root_rows:
        key=row['case_id'],row['graph_seed'];value=row['root_vertices'],row['root_edges']
        assert key not in roots or roots[key]==value;roots[key]=value
    query_summary=[]
    for case in case_order:
        for variant in ('half','eighth'):
            group=[r for r in query_rows if r['case_id']==case and r['variant']==variant];assert len(group)==4
            query_summary.append({'case_id':case,'variant':variant,
                **{name+'_min':min(r[name] for r in group) for name in ('Q','U','engine_words')},
                **{name+'_max':max(r[name] for r in group) for name in ('Q','U','engine_words')},
                **{'U_over_Q_'+k:v for k,v in stats([Fraction(r['U'],r['Q']) if r['Q'] else None for r in group]).items()}})
    for p,h in inputs.items():assert sha(Path(p))==h,p
    out.mkdir()
    for name,rows in [('all_case_field_statuses',summaries),('all_field_statuses',global_status),
                     ('selected_case_ratios',[r for r in summaries if r['counter'] in SELECTED]),
                     ('query_realizations',query_rows),('query_case_summaries',query_summary),('root_dimensions',root_rows)]:
        write_csv(out/(name+'.csv'),rows)
    result={'validation':'pass','collector_imported':False,'native_execution':False,'performance_claim':False,
        **expected,'verified_cells':cells,'comparator_graph_identities_equal_across_rate_and_sampler':12,
        'root_dimension_identities_equal':12,'selected_fields':SELECTED,'input_sha256':inputs,
        'output_sha256':{p.name:sha(p) for p in out.glob('*.csv')}}
    write=out/'review.json'
    with write.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('input_sha256','output_sha256')},indent=2))
    print('SELECTED')
    for case in case_order:print(case,{r['counter']:round(r['median_float'],5) if r['median_float'] is not None else None for r in summaries if r['case_id']==case and r['counter'] in SELECTED})
    print('GLOBAL_STATUS',global_status)
    print('QUERY',query_summary)


if __name__=='__main__':main()
