#!/usr/bin/env python3
"""Small complete-case summary of canonical paired timing; no native or plotting."""
import argparse
from collections import defaultdict
import csv
from fractions import Fraction
import json
import math
from pathlib import Path
import statistics
import analyze_diagnostics as a


def main():
    p=argparse.ArgumentParser();p.add_argument('--analysis',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    source=args.analysis.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False);bound={};a.read(__file__,bound)
    info=a.parse(a.read(source/'provenance.json',bound));a.require(info['validation']=='pass' and info['schema']=='kkt_depth_candidate_analysis_v1','timing analysis status')
    for path,digest in info['input_sha256'].items():a.bind(path,bound,digest)
    tables={}
    for name in ('pairs','cases','pooled','times','fits'):
        path=source/('timing-'+name+'.csv');tables[name]=list(csv.DictReader(__import__('io').StringIO(a.read(path,bound,info['output_sha256'][path.name]))))
    pairs=tables['pairs'];a.require(len(pairs)==216,'paired count');grouped=defaultdict(list)
    for r in pairs:
        key=(r['family'],int(r['n']),r['clock']);q=Fraction(int(r['numerator_ns']),int(r['denominator_ns']))
        a.require(q==Fraction(int(r['exact_numerator']),int(r['exact_denominator'])),'exact ratio mismatch');grouped[key].append((r,q))
    sizes=[]
    for r in tables['pooled']:
        key=(r['family'],int(r['n']),r['clock']);v=grouped[key];q=[x[1] for x in v]
        a.require(len(q)==6 and float(statistics.median(q))==float(r['median_paired_ratio']),'pooled paired median mismatch')
        row=dict(r);row['all_ratios_below_one']=all(x<1 for x in q)
        for gi,g in enumerate(a.GRAPHS,1):
            graph=[value for raw,value in v if int(raw['graph_seed'])==g];a.require(len(graph)==3,'graph repetition count')
            row[f'graph{gi}_median']=float(statistics.median(graph))
        sizes.append(row)
    a.write_csv(out/'all-size-ratios.csv',sizes)
    losses=[r for r in pairs if int(r['numerator_ns'])>=int(r['denominator_ns'])]
    if losses:a.write_csv(out/'all-nonwinning-pairs.csv',losses)
    summary={}
    for clock in ('wall_ns','cpu_ns'):
        values=[Fraction(int(r['numerator_ns']),int(r['denominator_ns'])) for r in pairs if r['clock']==clock]
        summary[clock]=dict(observations=len(values),wins=sum(q<1 for q in values),ties=sum(q==1 for q in values),losses=sum(q>1 for q in values),minimum=float(min(values)),maximum=float(max(values)))
    fit_summary=[]
    for aggregation in ('all_calls','size_means'):
        for clock in ('wall_ns','cpu_ns'):
            for policy in ('reference','depth'):
                rows=[r for r in tables['fits'] if r['aggregation']==aggregation and r['clock']==clock and r['policy']==policy]
                selected=[r for r in rows if r['selected_between_two']=='True'];a.require(len(selected)==6,'six curve fits')
                fit_summary.append(dict(aggregation=aggregation,clock=clock,policy=policy,selected_N=sum(r['model']=='N' for r in selected),selected_NlgN=sum(r['model']=='NlgN' for r in selected)))
    growth=[]
    for family in a.FAMILIES:
        for graph in a.GRAPHS:
            for clock in ('wall_ns','cpu_ns'):
                for policy in ('reference','depth'):
                    rows=[r for r in tables['times'] if r['family']==family and int(r['graph_seed'])==graph and r['clock']==clock and r['policy']==policy]
                    a.require(len(rows)==6,'six growth values');rows.sort(key=lambda r:int(r['n']));lo,hi=rows[0],rows[-1]
                    q=Fraction(int(hi['median'])*int(lo['N']),int(lo['median'])*int(hi['N']))
                    growth.append(dict(family=family,graph_seed=graph,clock=clock,policy=policy,large_over_small_time_per_N=float(q)))
    a.write_csv(out/'normalization-growth.csv',growth)
    a.recheck(bound);result=dict(validation='pass',native_execution=False,clock_totals=summary,fit_choices=fit_summary,nonwinning_rows=len(losses),input_sha256=bound)
    result['output_sha256']={p.name:a.sha(p) for p in out.iterdir() if p.is_file()}
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(clock_totals=summary,fit_choices=fit_summary,nonwinning_rows=len(losses)),indent=2))
    for family in a.FAMILIES:
        print(family)
        for n in a.SIZES:
            selected=[r for r in sizes if r['family']==family and int(r['n'])==n]
            print(n,'; '.join(f"{r['clock']} median={float(r['median_paired_ratio']):.6f}, graph={r['graph1_median']:.6f}/{r['graph2_median']:.6f}, range={float(r['minimum_paired_ratio']):.6f}..{float(r['maximum_paired_ratio']):.6f}, wins={r['numerator_wins']}/6" for r in selected))


if __name__=='__main__':main()
