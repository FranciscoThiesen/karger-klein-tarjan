#!/usr/bin/env python3
"""Retain paired-median and separate-absolute-median outcomes independently."""
import argparse
from collections import defaultdict
from fractions import Fraction
import json
from pathlib import Path
import statistics
import analyze_diagnostics as a


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--analysis',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    source=args.analysis.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False);bound={};a.read(__file__,bound)
    p=a.parse(a.read(source/'provenance.json',bound));a.require(p['validation']=='pass' and p['raw_counts']['timing']==288,'complete timing analysis')
    for path,digest in p['input_sha256'].items():a.bind(path,bound,digest)
    raw=a.parse(a.read(source/'all_raw_rows.json',bound,p['output_sha256']['all_raw_rows.json']))['timing'];groups=defaultdict(dict)
    for row in raw:
        if not row['warmup']:groups[a.identity(row)][(row['policy'],row['repetition'])]=row
    a.require(len(groups)==36,'all36input identities');rows=[]
    for identity,group in groups.items():
        a.require(set(group)=={(policy,r) for policy in ('reference','depth') for r in (1,2,3)},'exact36callmatrix')
        for clock in ('wall_ns','cpu_ns'):
            reference=[group[('reference',r)][clock] for r in (1,2,3)];depth=[group[('depth',r)][clock] for r in (1,2,3)]
            refmed=statistics.median(reference);depmed=statistics.median(depth)
            paired=statistics.median(Fraction(x,y) for x,y in zip(depth,reference));separate=Fraction(depmed,refmed)
            rows.append(dict(zip(a.IDENTITY,identity),clock=clock,reference_median_ns=refmed,depth_median_ns=depmed,
                median_paired_ratio=float(paired),ratio_of_separate_medians=float(separate),
                paired_exact_numerator=paired.numerator,paired_exact_denominator=paired.denominator,
                separate_exact_numerator=separate.numerator,separate_exact_denominator=separate.denominator))
    a.write_csv(out/'all-input-medians.csv',rows);a.write_csv(out/'absolute-median-nonwins.csv',[r for r in rows if r['depth_median_ns']>=r['reference_median_ns']])
    summary={clock:{name:{'wins':sum(r[key]<1 for r in rows if r['clock']==clock),'ties':sum(r[key]==1 for r in rows if r['clock']==clock),'losses':sum(r[key]>1 for r in rows if r['clock']==clock)}
        for name,key in (('paired','median_paired_ratio'),('separate_absolute','ratio_of_separate_medians'))} for clock in ('wall_ns','cpu_ns')}
    a.recheck(bound);result=dict(validation='pass',native_execution=False,inputs=36,clock_rows=72,summary=summary,input_sha256=bound,
        output_sha256={p.name:a.sha(p) for p in out.iterdir() if p.is_file()})
    (out/'provenance.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(summary,indent=2))
    for r in rows:
        if r['depth_median_ns']>=r['reference_median_ns']:print(json.dumps(r))


if __name__=='__main__':main()
