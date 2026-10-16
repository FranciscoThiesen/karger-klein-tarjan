#!/usr/bin/env python3
"""Independent raw Google/native arithmetic and final-report checks, stdlib only."""
import csv
import hashlib
import io
import json
import math
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
from statistics import median

ROOT=Path(__file__).resolve().parents[4]
A=ROOT/'benchmark/scaling_investigation/analysis'
RAW=ROOT/'benchmark/results/scaling-investigation-2026-10-15/depth-google01'
OUT=A/'depth-google-analysis-attempt01'
FAMILIES=('leaf_hierarchy4','leaf_shuffled4','gnm_random')
LABELS=dict(zip(FAMILIES,('Ordered hierarchy','Shuffled weights','Connected G(n,m)')))
SIZES=tuple(2**i for i in range(10,21))
BOUND={}

def read(path):
    path=Path(path);data=path.read_bytes();digest=hashlib.sha256(data).hexdigest()
    assert str(path) not in BOUND or BOUND[str(path)]==digest
    BOUND[str(path)]=digest
    return data.decode()
def js(path):return json.loads(read(path))
def csvrows(path):return list(csv.DictReader(io.StringIO(read(path))))
def close(x,y):assert math.isclose(float(x),float(y),rel_tol=1e-11,abs_tol=1e-10),(x,y)
def stats(v):return dict(count=len(v),wins=sum(q<1 for q in v),ties=sum(q==1 for q in v),losses=sum(q>1 for q in v),minimum=float(min(v)),maximum=float(max(v)))
def table(name,proof):
    value=csvrows(OUT/name);assert BOUND[str(OUT/name)]==proof['output_sha256'][name]
    return value

def main():
    read(__file__);report=read(ROOT/'docs/scaling-investigation/RESULTS.md')
    read(ROOT/'docs/scaling-investigation/HOST_MEMORY.md');read(ROOT/'benchmark/current_complexity/current_complexity.cpp')
    proof=js(OUT/'provenance.json');assert proof['validation']=='pass'
    capture=js(RAW/'capture.json');assert capture['validation']=='pass' and len(capture['captures'])==6
    assert BOUND[str(RAW/'capture.json')]==proof['input_sha256'][str(RAW/'capture.json')]
    native={};library={};selected_fits=[]
    for index,item in enumerate(capture['captures']):
        family,policy=item['spec']['family'],item['policy'];assert (family,policy) not in library
        path=Path(item['raw_csv']);rows=csvrows(path);assert len(rows)==99
        assert BOUND[str(path)]==proof['input_sha256'][str(path)]
        for r in rows:
            assert r['family']==family and r['graph_seed']=='19000013' and r['sampling_seed']=='3001' and r['size_order']=='ascending' and r['validation']=='pass'
            n,v,i=int(r['n']),int(r['invocation']),int(r['iteration']);k=family,policy,n,v,r['phase'],i
            assert k not in native;native[k]=r
            assert int(r['m'])==n*(16 if family=='gnm_random' else 32) and int(r['N'])==n+int(r['m'])
        path=Path(item['benchmark_json']);document=js(path)
        assert BOUND[str(path)]==proof['input_sha256'][str(path)]
        copied=OUT/f'original-library-{index:02d}.json';read(copied);assert BOUND[str(path)]==BOUND[str(copied)]
        big,= [r for r in document['benchmarks'] if r.get('aggregate_name')=='BigO']
        rms,= [r for r in document['benchmarks'] if r.get('aggregate_name')=='RMS']
        assert big==item['library_big_o'] and rms==item['library_rms'] and big['big_o']=='NlgN' and big['time_unit']=='ns'
        iters=[r for r in document['benchmarks'] if r['run_type']=='iteration'];assert len(iters)==33
        assert {(int(r['vertices']),r['repetition_index']) for r in iters}=={(n,v) for n in SIZES for v in range(3)}
        # Recompute the selected zero-intercept fit from the library's own CPU/manual intervals.
        x=[];cpu=[];manual=[]
        for r in iters:
            n=int(r['vertices']);v=r['repetition_index'];N=n+int(r['edges']);assert r['iterations']==2 and r['time_unit']=='ms'
            x.append(N*math.log2(N));cpu.append(r['cpu_time']*1e6);manual.append(r['real_time']*1e6)
            two=[int(native[family,policy,n,v,'timed',i]['elapsed_ns']) for i in (0,1)]
            close(manual[-1],F(sum(two),2))
        coeff=lambda y:sum(xx*yy for xx,yy in zip(x,y))/sum(xx*xx for xx in x)
        cp,ma=coeff(cpu),coeff(manual);rms_value=math.sqrt(sum((y-cp*xx)**2 for xx,y in zip(x,cpu))/len(x))/(sum(cpu)/len(cpu))
        close(cp,big['cpu_coefficient']);close(ma,big['real_coefficient']);close(rms_value,rms['rms'])
        library[family,policy]=(big,rms)
        selected_fits.append(dict(family=family,policy=policy,model=big['big_o'],cpu_coefficient=big['cpu_coefficient'],manual_coefficient=big['real_coefficient'],cpu_rms=rms['rms']))
        line=f"| {LABELS[family]} | {policy.title()} | {big['cpu_coefficient']:.6f} | {big['real_coefficient']:.6f} | {rms['rms']:.6f} |"
        assert line in report,line
    assert set(native)=={(f,p,n,v,phase,i) for f in FAMILIES for p in ('reference','depth') for n in SIZES for v in range(3) for phase,i in (('warmup',0),('timed',0),('timed',1))}
    assert set(library)=={(f,p) for f in FAMILIES for p in ('reference','depth')}
    summaries={};pairs={};means={};times={}
    for f in FAMILIES:
        for n in SIZES:
            for clock in ('elapsed_ns','process_cpu_elapsed_ns'):
                duration={p:[int(native[f,p,n,v,'timed',i][clock]) for v in range(3) for i in (0,1)] for p in ('reference','depth')}
                for v in range(3):
                    for i in (0,1):
                        k=f,n,clock,v,i;pairs[k]=F(duration['depth'][2*v+i],duration['reference'][2*v+i])
                        for name in ('input_fingerprint','topology_fingerprint'):assert native[f,'depth',n,v,'timed',i][name]==native[f,'reference',n,v,'timed',i][name]
                    for p in ('reference','depth'):means[f,n,clock,v,p]=F(sum(duration[p][2*v:2*v+2]),2)
                qs=[pairs[f,n,clock,v,i] for v in range(3) for i in (0,1)]
                separate=F(median(duration['depth']),median(duration['reference']))
                summaries[f,n,clock]=(median(qs),separate,qs,duration)
                for p in ('reference','depth'):times[f,n,clock,p]=(median(duration[p]),min(duration[p]),max(duration[p]))
    canonical=table('native-pairs.csv',proof);assert len(canonical)==396
    for r in canonical:assert F(int(r['exact_numerator']),int(r['exact_denominator']))==pairs[r['family'],int(r['n']),r['clock'],int(r['invocation']),int(r['iteration'])]
    canonical=table('native-summary.csv',proof);assert len(canonical)==66
    for r in canonical:
        pm,sm,qs,d=summaries[r['family'],int(r['n']),r['clock']]
        close(r['median_paired_ratio'],pm);assert F(int(r['separate_exact_numerator']),int(r['separate_exact_denominator']))==sm
        close(r['minimum_paired_ratio'],min(qs));close(r['maximum_paired_ratio'],max(qs))
        assert int(r['numerator_wins'])==sum(q<1 for q in qs) and int(r['numerator_losses'])==sum(q>1 for q in qs) and int(r['equal'])==sum(q==1 for q in qs)
    canonical=table('native-two-call-means.csv',proof);assert len(canonical)==396
    for r in canonical:assert F(int(r['exact_numerator']),int(r['exact_denominator']))==means[r['family'],int(r['n']),r['clock'],int(r['invocation']),r['policy']]
    canonical=table('native-times.csv',proof);assert len(canonical)==132
    for r in canonical:
        values=times[r['family'],int(r['n']),r['clock'],r['policy']]
        for name,want in zip(('median_ns','minimum_ns','maximum_ns'),values):close(r[name],want)
    coeff_ratios=[]
    for r in table('library-coefficient-comparison.csv',proof):
        f=r['family'];rb,rr=library[f,'reference'];db,dr=library[f,'depth'];cp=db['cpu_coefficient']/rb['cpu_coefficient'];ma=db['real_coefficient']/rb['real_coefficient']
        close(r['cpu_coefficient_depth_over_reference'],cp);close(r['manual_coefficient_depth_over_reference'],ma)
        coeff_ratios.append(dict(family=f,cpu=cp,manual=ma))
    clocks={}
    for clock in ('elapsed_ns','process_cpu_elapsed_ns'):
        clocks[clock]=dict(individual_pairs=stats([q for k,q in pairs.items() if k[2]==clock]),paired_medians=stats([v[0] for k,v in summaries.items() if k[2]==clock]),separate_medians=stats([v[1] for k,v in summaries.items() if k[2]==clock]))
    endpoints=[]
    for f in FAMILIES:
        wall,cpu=(summaries[f,1048576,c] for c in ('elapsed_ns','process_cpu_elapsed_ns'))
        line=f"| {LABELS[f]} | {float(wall[0]):.6f} / {float(cpu[0]):.6f} | {float(wall[1]):.6f} / {float(cpu[1]):.6f} |";assert line in report,line
        endpoints.append(dict(family=f,wall_paired=float(wall[0]),cpu_paired=float(cpu[0]),wall_separate=float(wall[1]),cpu_separate=float(cpu[1])))
    # Check the newly qualified largest-input separate-median claim against primary raw calls.
    primary=js(A/'depth-timing-analysis-attempt01/all_raw_rows.json')['timing'];assert len(primary)==288
    grouped=defaultdict(dict)
    for r in primary:
        if not r['warmup']:grouped[r['family'],r['n'],r['graph_seed']][r['policy'],r['repetition']]=r
    primary_summary={}
    for clock in ('wall_ns','cpu_ns'):
        pp=[];mm=[];ss=[];large=[]
        for (f,n,g),v in grouped.items():
            rr=[v['reference',i][clock] for i in (1,2,3)];dd=[v['depth',i][clock] for i in (1,2,3)]
            qq=[F(d,r) for d,r in zip(dd,rr)];pp+=qq;mm.append(median(qq));separate=F(median(dd),median(rr));ss.append(separate)
            if n==1048576:large.append(separate)
        primary_summary[clock]=dict(individual_pairs=stats(pp),paired_medians=stats(mm),separate_medians=stats(ss),largest_separate_median_ratios=stats(large))
    for path,digest in BOUND.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
    result=dict(validation='pass',native_execution=False,repository_analyzers_imported=False,raw_google_rows=594,actual_library_rows=selected_fits,coefficient_ratios=coeff_ratios,clock_statistics=clocks,largest_google_inputs=endpoints,primary_campaign_crosscheck=primary_summary,input_sha256=BOUND)
    with Path(__file__).with_name('independent-actual-google-review-attempt01.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))

if __name__=='__main__':main()
