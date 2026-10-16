#!/usr/bin/env python3
"""Independent completed-data arithmetic check; stdlib only, no solver/imported analyzer."""
import csv
import hashlib
import io
import json
import math
from collections import Counter, defaultdict
from fractions import Fraction as F
from pathlib import Path
from statistics import median

ROOT=Path(__file__).resolve().parents[4]
A=ROOT/'benchmark/scaling_investigation/analysis'
FAMILIES=('leaf_hierarchy4','leaf_shuffled4','gnm_random')
GRAPHS=(19000013,19000043)
SIZES=(1024,4096,16384,65536,262144,1048576)
PHASES='api input recursion contraction minimum_scan sampling isolation forest_recovery partition tree_setup fbt lca_build queries query_gather mark_scatter path_solve median_table path_walk filtering output'.split()
BOUND={}

def read(path):
    path=Path(path);data=path.read_bytes();digest=hashlib.sha256(data).hexdigest()
    assert str(path) not in BOUND or BOUND[str(path)]==digest
    BOUND[str(path)]=digest
    return data.decode()

def js(path):return json.loads(read(path))
def table(path):return list(csv.DictReader(io.StringIO(read(path))))
def key(r):return r['family'],int(r['n']),int(r['graph_seed']),int(r['sampling_seed'])
def same(x,y):assert math.isclose(float(x),float(y),rel_tol=1e-12,abs_tol=1e-12),(x,y)
def canonical(folder,name):
    p=js(folder/'provenance.json');assert p['validation']=='pass'
    rows=table(folder/name);assert BOUND[str(folder/name)]==p['output_sha256'][name]
    return rows
def raw(folder,mode):
    p=js(folder/'provenance.json');assert p['validation']=='pass'
    r=js(folder/'all_raw_rows.json')[mode]
    assert BOUND[str(folder/'all_raw_rows.json')]==p['output_sha256']['all_raw_rows.json']
    return r

def phases():
    folder=A/'depth-phase-analysis-attempt01';rows=raw(folder,'phase');assert len(rows)==144
    by={(key(r),r['policy'],r['repetition']):r for r in rows};assert len(by)==144
    cases={(f,n,g,3001) for f in FAMILIES for n in (16384,262144,1048576) for g in GRAPHS}
    assert set(by)=={(k,p,r) for k in cases for p in ('reference','depth') for r in range(4)}
    for r in rows:
        assert set(r['phases'])==set(PHASES)
        assert sum(p['wall_ns'] for p in r['phases'].values())==r['phase_total_ns']<=r['wall_ns']
    values={};deltas={};ratios={}
    for k in cases:
        N=by[k,'reference',1]['n']+by[k,'reference',1]['m']
        for p in ('reference','depth'):
            for phase in (*PHASES,'outside_collector','total'):
                vals=[]
                for rep in (1,2,3):
                    r=by[k,p,rep]
                    vals.append(r['wall_ns'] if phase=='total' else r['wall_ns']-r['phase_total_ns'] if phase=='outside_collector' else r['phases'][phase]['wall_ns'])
                values[k,p,phase]=vals
        for phase in (*PHASES,'outside_collector','total'):
            old,new=(sum(values[k,p,phase]) for p in ('reference','depth'))
            deltas[k,phase]=F(new-old,3*N);ratios[k,phase]=F(new,old) if old else None
        assert sum(deltas[k,p] for p in (*PHASES,'outside_collector'))==deltas[k,'total']
    times=canonical(folder,'phase-times.csv');assert len(times)==792
    for r in times:
        k=key(r);v=values[k,r['policy'],r['phase']];N=int(r['N'])
        for name,want in [('minimum',min(v)),('median',median(v)),('maximum',max(v)),('mean',F(sum(v),3)),('median_ns_per_N',F(median(v),N))]:same(r[name],want)
    ds=canonical(folder,'phase-deltas.csv');assert len(ds)==396
    for r in ds:
        k=key(r);p=r['phase'];N=int(r['N'])
        assert F(int(r['delta_exact_numerator']),int(r['delta_exact_denominator']))==deltas[k,p]
        same(r['mean_delta_ns_per_N'],deltas[k,p]);same(r['ratio_of_means'],ratios[k,p])
        for policy,col in [('depth','numerator_mean_ns_per_N'),('reference','denominator_mean_ns_per_N')]:same(r[col],F(sum(values[k,policy,p]),3*N))
    summaries=canonical(A/'depth-phase-summary-attempt01','all-input-additive-summary.csv');assert len(summaries)==18
    for r in summaries:
        k=key(r);other=deltas[k,'total']-deltas[k,'query_gather']
        assert F(int(r['other_exact_numerator']),int(r['other_exact_denominator']))==other
        same(r['all_other_phases_delta_ns_per_N'],other)
        for p in ('total','query_gather','minimum_scan','mark_scatter','lca_build','outside_collector'):
            same(r[p+'_delta_ns_per_N'],deltas[k,p]);same(r[p+'_depth_over_reference_mean'],ratios[k,p])
    return {p:dict(lower=sum(deltas[k,p]<0 for k in cases),higher=sum(deltas[k,p]>0 for k in cases),ratio_min=float(min(ratios[k,p] for k in cases)),ratio_max=float(max(ratios[k,p] for k in cases)),maximum_absolute_delta_ns_per_N=float(max(abs(deltas[k,p]) for k in cases))) for p in ('total','query_gather','minimum_scan','outside_collector')}

def work():
    # Read original baseline stdout, not the producer's normalized table.
    old={}
    for path in sorted((ROOT/'benchmark/results/scaling-investigation-2026-10-15/work01').glob('*-work.stdout')):
        rr=[json.loads(line) for line in read(path).splitlines()];assert len(rr)==2 and rr[0]['warmup'] and not rr[1]['warmup']
        r=rr[1];assert key(r) not in old;old[key(r)]=r
    expected={(f,n,g,s) for f in FAMILIES for n in SIZES for g in GRAPHS for s in (3001,3011)}
    assert set(old)==expected
    fields=set(next(iter(old.values()))['work']);assert len(fields)==65
    candidate=raw(A/'depth-work-analysis-attempt01','work');new={key(r):r for r in candidate if not r['warmup']};assert set(new)==expected
    rows=canonical(A/'depth-work-analysis-attempt01','work-counters.csv');assert len(rows)==4680
    for r in rows:
        k=key(r);field=r['counter'];before,after=old[k]['work'][field],new[k]['work'][field]
        assert int(r['reference'])==before and int(r['depth'])==after
        assert before-after==(old[k]['work']['lca_vertices'] if field=='initialized_slots' else 0)
        for name in ('input_fingerprint','topology_fingerprint'):assert old[k][name]==new[k][name]==int(r[name])
    folder=A/'all-work-fields-attempt01';points=canonical(folder,'all-points.csv');assert len(points)==4680
    for r in points:
        v=old[key(r)]['work'][r['counter']];N=old[key(r)]['n']+old[key(r)]['m'];assert int(r['value'])==v and int(r['N'])==N
        assert F(int(r['exact_numerator']),int(r['exact_denominator']))==F(v,N);same(r['per_N'],F(v,N))
    curves=canonical(folder,'all-curves.csv');assert len(curves)==780;computed={};statuses=Counter();directions=Counter()
    for r in curves:
        f,g,s,c=r['family'],int(r['graph_seed']),int(r['sampling_seed']),r['counter']
        vals=[(n,F(old[f,n,g,s]['work'][c],old[f,n,g,s]['n']+old[f,n,g,s]['m'])) for n in SIZES]
        lo,hi=vals[0][1],vals[-1][1];delta=hi-lo;status='defined' if lo else 'all_zero' if all(v==0 for _,v in vals) else 'zero_at_small_input'
        assert r['ratio_status']==status;assert F(int(r['delta_numerator']),int(r['delta_denominator']))==delta
        same(r['small_per_N'],lo);same(r['large_per_N'],hi);same(r['large_minus_small_per_N'],delta)
        assert int(r['zero_points'])==sum(v==0 for _,v in vals)
        peak=max(vals,key=lambda t:t[1]);trough=min(vals,key=lambda t:t[1])
        assert int(r['peak_n'])==peak[0] and int(r['trough_n'])==trough[0]
        same(r['peak_per_N'],peak[1]);same(r['peak_minus_small_per_N'],peak[1]-lo);same(r['trough_per_N'],trough[1])
        if lo:same(r['large_over_small_per_N'],hi/lo)
        else:assert r['large_over_small_per_N']==''
        statuses[status]+=1;directions['increase' if delta>0 else 'decrease' if delta<0 else 'equal']+=1
        computed[f,g,s,c]=(delta,hi/lo if lo else None,peak[1]-lo)
    summaries=canonical(folder,'all-family-fields.csv');assert len(summaries)==195
    for r in summaries:
        vals=[v for (f,g,s,c),v in computed.items() if (f,c)==(r['family'],r['counter'])];assert len(vals)==4
        ds=[v[0] for v in vals];rat=[v[1] for v in vals if v[1] is not None]
        for col,v in [('minimum_delta_per_N',min(ds)),('maximum_delta_per_N',max(ds)),('median_delta_per_N',median(ds)),('maximum_peak_delta_per_N',max(v[2] for v in vals))]:same(r[col],v)
        for col,v in [('endpoint_increases',sum(x>0 for x in ds)),('endpoint_decreases',sum(x<0 for x in ds)),('endpoint_equal',sum(x==0 for x in ds)),('zero_denominator_curves',4-len(rat))]:assert int(r[col])==v
        if rat:same(r['minimum_defined_ratio'],min(rat));same(r['maximum_defined_ratio'],max(rat))
        else:assert r['minimum_defined_ratio']==r['maximum_defined_ratio']==''
    selected={}
    for f in FAMILIES:
        for c in ('path_query_visits','verifier_queries','initialized_slots','path_binary_search_steps'):
            vals=[v for (ff,g,s,cc),v in computed.items() if (ff,cc)==(f,c)];rr=[v[1] for v in vals if v[1] is not None]
            selected[f+'/'+c]=dict(minimum_defined_ratio=float(min(rr)) if rr else None,maximum_defined_ratio=float(max(rr)) if rr else None,maximum_endpoint_delta=float(max(v[0] for v in vals)),maximum_peak_delta=float(max(v[2] for v in vals)))
    return dict(points=4680,curves=780,summaries=195,zero_points=sum(v==0 for r in old.values() for v in r['work'].values()),ratio_status=dict(statuses),endpoint_direction=dict(directions),selected=selected)

def inline_control():
    folder=A/'depth-inline-analysis-attempt01';rows=raw(folder,'inline-control');assert len(rows)==72
    by={(key(r),r['policy'],r['repetition']):r for r in rows if not r['warmup']};assert len(by)==54
    result=[];cases=canonical(folder,'inline-control-cases.csv');assert len(cases)==36
    for r in cases:
        k=key(r);p,q=r['numerator_policy'],r['denominator_policy'];clock=r['clock']
        num=[by[k,p,i][clock] for i in (1,2,3)];den=[by[k,q,i][clock] for i in (1,2,3)];rat=[F(x,y) for x,y in zip(num,den)]
        for col,want in [('median_paired_ratio',median(rat)),('minimum_paired_ratio',min(rat)),('maximum_paired_ratio',max(rat)),('ratio_of_medians',F(median(num),median(den)))]:same(r[col],want)
        for col,want in [('numerator_wins',sum(x<1 for x in rat)),('equal',sum(x==1 for x in rat)),('numerator_losses',sum(x>1 for x in rat))]:assert int(r[col])==want
        if k[:2]==('gnm_random',1048576) and (p,q)==('depth','reference'):result.append(dict(clock=clock,median_paired_ratio=float(median(rat)),ratio_of_separate_medians=float(F(median(num),median(den)))))
    return dict(cases=36,raw_rows=72,gnm_large_exception=result)

def main():
    read(__file__)
    result=dict(validation='pass',native_execution=False,repository_analyzers_imported=False,scope='Independent arithmetic of completed raw/canonical data; existing strict collectors retain build/lifecycle responsibility.',phase=phases(),work=work(),inline=inline_control())
    for path,digest in BOUND.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
    result['input_sha256']=BOUND
    output=Path(__file__).with_name('independent-phase-all65-review-attempt01.json')
    with output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))

if __name__=='__main__':main()
