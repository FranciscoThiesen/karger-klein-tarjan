#!/usr/bin/env python3
"""All65 baseline fields: exact per-N changes, zeros and semantic categories; no fits."""
import argparse
from collections import defaultdict,Counter
import csv
from fractions import Fraction
import io
import json
from pathlib import Path
import re
import statistics
import analyze_diagnostics as a


def category(field,proxy):
    if field=='current_depth':return 'final_state'
    if field in ('max_depth','path_max_height'):return 'maximum_not_additive_work'
    if field.startswith('root_after_two_'):return 'root_volume'
    if field=='fbt_rounds':return 'cumulative_round_count'
    if field.endswith('_calls') and field!='hash_lookup_calls':return 'call_count'
    return 'logical_event_in_heterogeneous_proxy' if proxy else 'cumulative_volume_or_structure_count'


def main():
    p=argparse.ArgumentParser();p.add_argument('--work-analysis',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    source=args.work_analysis.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False);bound={};a.read(__file__,bound)
    proof=a.parse(a.read(source/'provenance.json',bound));a.require(proof['validation']=='pass' and proof['raw_counts']['work']==144,'complete work proof')
    for path,digest in proof['input_sha256'].items():a.bind(path,bound,digest)
    metrics=a.read(a.ROOT/'benchmark/work_metrics.hpp',bound)
    registry=re.findall(r'\{"([a-z_]+)", &kkt_work::WorkStats::([a-z_]+), (true|false)\}',metrics)
    a.require(len(registry)==65 and all(x==y for x,y,_ in registry),'exact65member-bound schema')
    flags={x:flag=='true' for x,_,flag in registry};path=source/'work-counters.csv'
    rows=list(csv.DictReader(io.StringIO(a.read(path,bound,proof['output_sha256'][path.name]))))
    a.require(len(rows)==4680 and {r['counter'] for r in rows}==set(flags),'complete65x72matrix')
    groups=defaultdict(list);points=[];seen=set()
    for r in rows:
        f=r['counter'];key=(r['family'],int(r['graph_seed']),int(r['sampling_seed']),f);n=int(r['n']);N=int(r['N']);value=int(r['reference']);q=Fraction(value,N)
        a.require((key,n) not in seen,'duplicate work point');seen.add((key,n))
        row={k:r[k] for k in a.IDENTITY};row.update(n=n,graph_seed=key[1],sampling_seed=key[2],m=int(r['m']),N=N,counter=f,category=category(f,flags[f]),contributes_to_proxy=flags[f],value=value,per_N=float(q),exact_numerator=q.numerator,exact_denominator=q.denominator)
        points.append(row);groups[key].append((n,q,value,N))
    expected={(f,g,s,counter) for f in a.FAMILIES for g in a.GRAPHS for s in a.SEEDS for counter in flags};a.require(set(groups)==expected,'all780countercurves')
    curves=[]
    for (family,g,s,field),values in groups.items():
        values.sort();a.require(tuple(v[0] for v in values)==a.SIZES,'all6sizes');first,last=values[0],values[-1];peak=max(values,key=lambda v:v[1]);trough=min(values,key=lambda v:v[1]);delta=last[1]-first[1]
        status='defined' if first[2]>0 else 'all_zero' if all(v[2]==0 for v in values) else 'zero_at_small_input'
        ratio=last[1]/first[1] if first[2] else None
        curves.append(dict(family=family,graph_seed=g,sampling_seed=s,counter=field,category=category(field,flags[field]),contributes_to_proxy=flags[field],small_value=first[2],large_value=last[2],small_per_N=float(first[1]),large_per_N=float(last[1]),large_minus_small_per_N=float(delta),delta_numerator=delta.numerator,delta_denominator=delta.denominator,
            ratio_status=status,large_over_small_per_N=float(ratio) if ratio is not None else '',zero_points=sum(v[2]==0 for v in values),peak_n=peak[0],peak_per_N=float(peak[1]),peak_minus_small_per_N=float(peak[1]-first[1]),trough_n=trough[0],trough_per_N=float(trough[1])))
    summary=[]
    for family in a.FAMILIES:
        for field in flags:
            v=[r for r in curves if r['family']==family and r['counter']==field];a.require(len(v)==4,'fourcounterrealizations');defined=[r['large_over_small_per_N'] for r in v if r['ratio_status']=='defined']
            summary.append(dict(family=family,counter=field,category=category(field,flags[field]),contributes_to_proxy=flags[field],curves=4,
                endpoint_increases=sum(Fraction(r['delta_numerator'],r['delta_denominator'])>0 for r in v),endpoint_equal=sum(r['delta_numerator']==0 for r in v),endpoint_decreases=sum(r['delta_numerator']<0 for r in v),
                minimum_delta_per_N=min(r['large_minus_small_per_N'] for r in v),maximum_delta_per_N=max(r['large_minus_small_per_N'] for r in v),median_delta_per_N=statistics.median(r['large_minus_small_per_N'] for r in v),
                minimum_defined_ratio=min(defined) if defined else '',maximum_defined_ratio=max(defined) if defined else '',zero_denominator_curves=4-len(defined),maximum_peak_delta_per_N=max(r['peak_minus_small_per_N'] for r in v)))
    a.write_csv(out/'all-points.csv',points);a.write_csv(out/'all-curves.csv',curves);a.write_csv(out/'all-family-fields.csv',summary)
    ranking=sorted(summary,key=lambda r:r['maximum_delta_per_N'],reverse=True);a.write_csv(out/'ranked-normalized-changes.csv',ranking)
    a.recheck(bound);info=dict(validation='pass',native_execution=False,fields=65,points=len(points),curves=len(curves),family_field_summaries=len(summary),
        zero_points=sum(r['value']==0 for r in points),curve_ratio_status=dict(Counter(r['ratio_status'] for r in curves)),
        endpoint_direction=dict(Counter('increase' if r['delta_numerator']>0 else 'decrease' if r['delta_numerator']<0 else 'equal' for r in curves)),
        interpretation='Heterogeneous counts; ranking is not CPU cost. No automatic complexity fits on call counts, maxima or any other field.',input_sha256=bound,
        output_sha256={p.name:a.sha(p) for p in out.iterdir() if p.is_file()})
    (out/'provenance.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps({k:v for k,v in info.items() if k not in ('input_sha256','output_sha256')},indent=2))
    print('Largest absolute positive endpoint changes per N; heterogeneous fields:')
    for r in ranking[:24]:print(r['family'],r['counter'],r['category'],'delta',r['minimum_delta_per_N'],r['maximum_delta_per_N'],'ratio',r['minimum_defined_ratio'],r['maximum_defined_ratio'],'rising',r['endpoint_increases'])
    print('Largest positive finite ratio by field/family, including small-base effects:')
    for r in sorted((r for r in summary if r['maximum_defined_ratio']!=''),key=lambda r:r['maximum_defined_ratio'],reverse=True)[:16]:print(r['family'],r['counter'],'ratio',r['minimum_defined_ratio'],r['maximum_defined_ratio'],'delta',r['minimum_delta_per_N'],r['maximum_delta_per_N'])


if __name__=='__main__':main()
