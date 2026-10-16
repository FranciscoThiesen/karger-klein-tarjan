#!/usr/bin/env python3
"""Independent completed host arithmetic, without importing the producer."""
import csv
import hashlib
import io
import json
import math
from fractions import Fraction
from pathlib import Path
from statistics import median

ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'benchmark/results/scaling-investigation-2026-10-15'
OUT=STUDY/'host-memory-analysis01'
BOUND={}

def read(path):
    path=Path(path);data=path.read_bytes();digest=hashlib.sha256(data).hexdigest()
    assert str(path) not in BOUND or BOUND[str(path)]==digest
    BOUND[str(path)]=digest
    return data.decode()

def main():
    read(__file__);doc=read(ROOT/'docs/scaling-investigation/HOST_MEMORY.md')
    proof=json.loads(read(OUT/'analysis.json'));assert proof['validation']=='pass'
    raw=[]
    for order in ('ascending','descending'):
        path=STUDY/'host-memory01'/(order+'.stdout')
        rows=[json.loads(line) for line in read(path).splitlines()]
        assert BOUND[str(path)]==proof['input_sha256'][str(path)]
        assert len(rows)==112 and all(r['size_order']==order for r in rows)
        raw+=rows
    sizes=tuple(16*1024*4**i for i in range(7));visits=16777224
    actual={(r['size_order'],r['bytes'],r['chains'],r['repetition']):r for r in raw}
    assert len(actual)==224 and set(actual)=={(o,b,c,r) for o in ('ascending','descending') for b in sizes for c in (1,4,8,0) for r in range(4)}
    assert sum(r['warmup'] for r in raw)==56
    for r in raw:
        assert r['warmup']==(r['repetition']==0) and r['logical_loads']==visits
        assert r['cpu_ns']==r['process_cpu_end_ns']-r['process_cpu_start_ns']>0 and r['wall_ns']>0
    summaries=list(csv.DictReader(io.StringIO(read(OUT/'summary.csv'))));assert len(summaries)==112
    assert BOUND[str(OUT/'summary.csv')]==proof['output_sha256'][str(OUT/'summary.csv')]
    derived={}
    for r in summaries:
        o,b,c,clock=r['size_order'],int(r['bytes']),int(r['chains']),r['clock']
        k=o,b,c,clock;assert k not in derived
        nums=[actual[o,b,c,i][clock+'_ns'] for i in (1,2,3)]
        assert [int(r[f'repetition_{i}_ns']) for i in (1,2,3)]==nums
        for label,value in (('min',min(nums)),('median',median(nums)),('max',max(nums))):
            assert int(r[label+'_ns'])==value
            assert math.isclose(float(r[label+'_ns_per_indexed_load']),float(Fraction(value,visits)),rel_tol=1e-12,abs_tol=1e-12)
        derived[k]=dict(minimum=float(Fraction(min(nums),visits)),median=float(Fraction(median(nums),visits)),maximum=float(Fraction(max(nums),visits)))
    calls=list(csv.DictReader(io.StringIO(read(OUT/'all-calls.csv'))));assert len(calls)==224
    assert BOUND[str(OUT/'all-calls.csv')]==proof['output_sha256'][str(OUT/'all-calls.csv')]
    for source,record in zip(raw,calls):
        for name,value in source.items():assert record[name]==(';'.join(map(str,value)) if name=='positions' else str(value))
        for clock in ('wall','cpu'):assert math.isclose(float(record[clock+'_ns_per_indexed_load']),source[clock+'_ns']/visits,rel_tol=1e-12)
    endpoints=[]
    for chains in (1,4,8,0):
        for order in ('ascending','descending'):
            for clock in ('cpu','wall'):
                first,last=derived[order,sizes[0],chains,clock],derived[order,sizes[-1],chains,clock]
                endpoints.append(dict(chains=chains,order=order,clock=clock,small=first,large=last,large_over_small_median=last['median']/first['median']))
    # Exact published CPU table strings, independently formatted from raw integers.
    precision={1:(3,3,3),4:(4,3,3),8:(4,3,3),0:(4,5,5)}
    for chains,label in ((1,'One dependent chain'),(4,'Four independent chains'),(8,'Eight independent chains'),(0,'Contiguous scan')):
        smallp,largep,rangep=precision[chains]
        aa,dd=(derived[o,sizes[0],chains,'cpu'] for o in ('ascending','descending'))
        a,b=(derived[o,sizes[-1],chains,'cpu'] for o in ('ascending','descending'))
        line=f"| {label} | {aa['median']:.{smallp}f} / {dd['median']:.{smallp}f} | {a['median']:.{largep}f} / {b['median']:.{largep}f} | {a['minimum']:.{rangep}f}–{a['maximum']:.{rangep}f} | {b['minimum']:.{rangep}f}–{b['maximum']:.{rangep}f} |"
        assert line in doc,line
    for path,digest in BOUND.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
    result=dict(validation='pass',native_execution=False,producer_imported=False,raw_rows=224,timed_rows=168,warmup_rows=56,checked_summaries=112,exact_published_cpu_rows=4,endpoints=endpoints,input_sha256=BOUND)
    target=Path(__file__).with_name('INDEPENDENT_HOST_ARITHMETIC_REVIEW.json')
    with target.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))

if __name__=='__main__':main()
