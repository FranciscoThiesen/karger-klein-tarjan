#!/usr/bin/env python3
"""Light completed-phase-only inspection while other diagnostics are running."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import statistics
from collections import defaultdict
import analyze_diagnostics as a


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True);p.add_argument('--phase',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--source-snapshot',type=Path);args=p.parse_args()
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False);bound={}
    result=dict(validation='running',scope='Completed phase capture only; not the joint four-mode analysis.',
                native_execution=False,input_sha256=bound)
    try:
        a.read(__file__,bound);a.read(Path(a.__file__),bound)
        snapshot=a.source_snapshot(args.source_snapshot,bound);result['source_snapshot']=snapshot
        build=args.build.resolve();a.load_build(build,bound,snapshot)
        old=a.historical(bound);validator,fields=a.row_validator(bound)
        raw=a.load_capture(args.phase,'phase',build,bound,old,validator,fields,snapshot)
        groups=defaultdict(list)
        for row in raw:
            if not row['warmup']:groups[a.identity(row)].append(row)
        summaries=[];endpoints=[];values={}
        for key,rows in groups.items():
            identity=dict(zip(a.IDENTITY,key));N=identity['n']+identity['m']
            for name in (*a.PHASES,'outside_collector','total'):
                times=[r['wall_ns'] if name=='total' else r['wall_ns']-r['phase_total_ns'] if name=='outside_collector' else r['phases'][name]['wall_ns'] for r in rows]
                value=dict(identity,N=N,phase=name,**a.summary(times),median_ns_per_N=statistics.median(times)/N,
                           mean_ns_per_N=statistics.mean(times)/N,minimum_ns_per_N=min(times)/N,maximum_ns_per_N=max(times)/N)
                summaries.append(value);values[(identity['family'],identity['graph_seed'],identity['sampling_seed'],identity['n'],name)]=times
        for family in a.FAMILIES:
            for graph in a.GRAPHS:
                for sampler in a.SEEDS:
                    deltas={}
                    for name in (*a.PHASES,'outside_collector','total'):
                        rates=[]
                        for n in (min(a.SIZES),max(a.SIZES)):
                            times=values[(family,graph,sampler,n,name)];N=n*(17 if family=='gnm_random' else 33)
                            rates.append(Fraction(sum(times),len(times)*N))
                        delta=rates[1]-rates[0];deltas[name]=delta
                        endpoints.append(dict(family=family,graph_seed=graph,sampling_seed=sampler,phase=name,
                            small_mean_ns_per_N=float(rates[0]),large_mean_ns_per_N=float(rates[1]),mean_delta_ns_per_N=float(delta),
                            exact_numerator=delta.numerator,exact_denominator=delta.denominator))
                    a.require(sum(v for k,v in deltas.items() if k!='total')==deltas['total'],'endpoint exact additivity')
        a.require(len(summaries)==1584 and len(endpoints)==264,'phase table counts')
        a.write_csv(output/'phase_summary.csv',summaries);a.write_csv(output/'endpoint_contributions.csv',endpoints)
        large=[]
        for family in a.FAMILIES:
            for name in (*a.PHASES,'outside_collector','total'):
                rows=[r for r in summaries if r['family']==family and r['phase']==name and r['n']==max(a.SIZES)]
                mean_rates=[r['mean_ns_per_N'] for r in rows];median_rates=[r['median_ns_per_N'] for r in rows]
                large.append(dict(family=family,phase=name,curve_count=len(rows),mean_ns_per_N_min=min(mean_rates),
                    mean_ns_per_N_max=max(mean_rates),median_ns_per_N_min=min(median_rates),median_ns_per_N_max=max(median_rates)))
        a.write_csv(output/'largest_size_ranges.csv',large);a.recheck(bound)
        result.update(validation='pass',phase_inputs=72,raw_rows=288,timed_rows=216,warmup_rows=72,
                      phase_summary_rows=1584,endpoint_rows=264,all_seeds_retained=True)
    except BaseException as error:result.update(validation='failed',error=repr(error));raise
    finally:
        result['output_sha256']={p.name:a.sha(p) for p in output.iterdir() if p.is_file()}
        (output/'provenance.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('input_sha256','output_sha256')}))


if __name__=='__main__':main()
