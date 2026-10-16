#!/usr/bin/env python3
"""Exact additive summary of all18 paired phase inputs; diagnostic wall clock only."""
import argparse,csv,io,json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
import analyze_diagnostics as a


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--analysis',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    source=args.analysis.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False);bound={};a.read(__file__,bound)
    p=a.parse(a.read(source/'provenance.json',bound));a.require(p['validation']=='pass' and p['raw_counts']['phase']==144,'complete paired phases')
    for path,digest in p['input_sha256'].items():a.bind(path,bound,digest)
    path=source/'phase-deltas.csv';data=list(csv.DictReader(io.StringIO(a.read(path,bound,p['output_sha256'][path.name]))));groups=defaultdict(dict)
    for r in data:
        a.require(r['phase'] not in groups[a.identity(r)],'duplicate phase');groups[a.identity(r)][r['phase']]=r
    a.require(len(groups)==18,'all18inputs');rows=[];headlines={}
    for identity,phases in groups.items():
        a.require(set(phases)==set(a.PHASES)|{'total','outside_collector'},'all22phases')
        values={k:Fraction(int(v['delta_exact_numerator']),int(v['delta_exact_denominator'])) for k,v in phases.items()}
        a.require(sum(v for k,v in values.items() if k!='total')==values['total'],'exact difference additivity')
        row=dict(zip(a.IDENTITY,identity))
        for name in ('total','query_gather','minimum_scan','mark_scatter','lca_build','outside_collector'):
            row[name+'_delta_ns_per_N']=float(values[name]);row[name+'_depth_over_reference_mean']=phases[name]['ratio_of_means']
        other=sum(v for k,v in values.items() if k not in ('total','query_gather'));row.update(all_other_phases_delta_ns_per_N=float(other),other_exact_numerator=other.numerator,other_exact_denominator=other.denominator)
        rows.append(row)
    a.write_csv(out/'all-input-additive-summary.csv',rows)
    a.write_csv(out/'largest-input-additive-summary.csv',[r for r in rows if int(r['n'])==1048576])
    for phase in ('total','query_gather','minimum_scan','mark_scatter','lca_build','outside_collector'):
        deltas=[float(r[phase+'_delta_ns_per_N']) for r in rows];ratios=[float(r[phase+'_depth_over_reference_mean']) for r in rows]
        headlines[phase]=dict(inputs=18,lower=sum(v<0 for v in deltas),equal=sum(v==0 for v in deltas),higher=sum(v>0 for v in deltas),minimum_delta=min(deltas),maximum_delta=max(deltas),minimum_ratio=min(ratios),maximum_ratio=max(ratios))
    a.recheck(bound);info=dict(validation='pass',native_execution=False,scope='Arithmetic means of three diagnostic wall calls, exact additive differences; no CPU attribution',headlines=headlines,input_sha256=bound,output_sha256={p.name:a.sha(p) for p in out.iterdir() if p.is_file()})
    (out/'provenance.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(headlines,indent=2))
    for r in rows:
        if int(r['n'])==1048576:print(r['family'],r['graph_seed'],'total/gather/other',r['total_delta_ns_per_N'],r['query_gather_delta_ns_per_N'],r['all_other_phases_delta_ns_per_N'])


if __name__=='__main__':main()
