#!/usr/bin/env python3
"""Read completed depth-query experiments; independent arithmetic, no native launch."""
import argparse
from collections import defaultdict
from fractions import Fraction
import importlib.util
import json
import math
from pathlib import Path
import statistics
import sys

import analyze_diagnostics as a

MODES=('work','timing','phase','allocation','inline-control','inline-phase')
RUNNER=a.HERE.parent/'candidates/run_candidate.py'


def schedule(mode):
    if mode=='work':return a.matrix('work'),('depth',),1
    if mode=='timing':return [c for c in a.matrix('work') if c['sampling_seed']==3001],('reference','depth'),3
    if mode in ('inline-control','inline-phase'):return a.matrix('calibration'),('reference','depth','depth_noinline'),3
    return a.matrix('allocation'),('reference','depth'),1 if mode=='allocation' else 3


def comparisons(policies):
    result=[(p,'reference') for p in policies if p!='reference']
    if 'depth_noinline' in policies:result.append(('depth_noinline','depth'))
    return tuple(result)


def merge(bound,other):
    for path,digest in other.items():
        a.require(path not in bound or bound[path]==digest,'conflicting candidate input binding')
        bound[path]=digest


def validate_matrix(rows,mode):
    cases,policies,reps=schedule(mode);groups={}
    for row in rows:
        a.require(type(row['repetition']) is int and row['warmup'] is (row['repetition']==0),'candidate repetition/warmup type')
        key=(a.casekey(row),row['policy'],row['repetition'])
        a.require(key not in groups,'duplicate native candidate call');groups[key]=row
    expected={(a.casekey(c),p,r) for c in cases for p in policies for r in range(reps+1)}
    a.require(set(groups)==expected,'independent candidate call matrix')
    for case in cases:
        identities={a.identity(groups[(a.casekey(case),p,r)]) for p in policies for r in range(reps+1)}
        a.require(len(identities)==1,'candidate full fingerprint identity join')


def load(path,mode,bound):
    path=Path(path).resolve();pre=a.parse(a.read(path,bound))
    a.require(pre['schema']=='kkt_depth_candidate_capture_v1' and pre['validation']=='pass' and pre['mode']==mode,'candidate capture mode/status')
    build=a.parse(a.read(pre['build_record'],bound,pre['build_record_sha256']))
    a.require(str(RUNNER) in build['source_sha256'],'missing runner source binding')
    for source,digest in build['source_sha256'].items():
        if source.endswith('.py') or source==str(a.ROOT/'benchmark/work_metrics.hpp'):a.bind(source,bound,digest)
    spec=importlib.util.spec_from_file_location('candidate_provenance_validator',RUNNER)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    # Reuse proof/schema/lifecycle checks only; no collector aggregation or native APIs.
    info,rows,proof=module.load(path);merge(bound,proof)
    a.require(info==pre,'capture changed during strict load')
    validate_matrix(rows,mode)
    a.recheck(bound)
    return info,rows,module


def ratio(numerator,denominator):
    if denominator:return float(Fraction(numerator,denominator)),'defined'
    return '',('both_zero' if numerator==0 else 'zero_denominator')


def pair_summary(values):
    return dict(observations=len(values),median_paired_ratio=float(statistics.median(values)),
                minimum_paired_ratio=float(min(values)),maximum_paired_ratio=float(max(values)),
                numerator_wins=sum(x<1 for x in values),equal=sum(x==1 for x in values),
                numerator_losses=sum(x>1 for x in values))


def measured(rows):
    return [r for r in rows if not r['warmup']]


def timing_tables(rows,mode):
    cases,policies,reps=schedule(mode);a.require(mode in ('timing','inline-control'),'not uninstrumented timing')
    values={(a.casekey(r),r['policy'],r['repetition']):r for r in measured(rows)}
    pairs=[];case_rows=[];times=[];pooled=defaultdict(list);graph_medians=defaultdict(list)
    for case in cases:
        key=a.casekey(case);example=values[(key,policies[0],1)];ident={k:example[k] for k in a.IDENTITY};N=ident['n']+ident['m']
        for clock in ('wall_ns','cpu_ns'):
            for policy in policies:
                durations=[values[(key,policy,r)][clock] for r in range(1,reps+1)]
                times.append(dict(ident,N=N,policy=policy,clock=clock,**a.summary(durations),median_ns_per_N=statistics.median(durations)/N))
            for numerator,denominator in comparisons(policies):
                fractions=[]
                for repetition in range(1,reps+1):
                    num,den=(values[(key,p,repetition)][clock] for p in (numerator,denominator))
                    q=Fraction(num,den);fractions.append(q)
                    pairs.append(dict(ident,N=N,clock=clock,numerator_policy=numerator,denominator_policy=denominator,
                        repetition=repetition,numerator_ns=num,denominator_ns=den,paired_ratio=float(q),
                        exact_numerator=q.numerator,exact_denominator=q.denominator))
                num_median=statistics.median(values[(key,numerator,r)][clock] for r in range(1,reps+1))
                den_median=statistics.median(values[(key,denominator,r)][clock] for r in range(1,reps+1))
                case_rows.append(dict(ident,N=N,clock=clock,numerator_policy=numerator,denominator_policy=denominator,
                    **pair_summary(fractions),ratio_of_medians=num_median/den_median,
                    numerator_median_ns=num_median,denominator_median_ns=den_median))
                pool=(ident['family'],ident['n'],ident['m'],ident['sampling_seed'],clock,numerator,denominator)
                pooled[pool].extend(fractions);graph_medians[pool].append(statistics.median(fractions))
    pool_rows=[]
    for key,fractions in pooled.items():
        family,n,m,s,clock,num,den=key;medians=graph_medians[key]
        pool_rows.append(dict(family=family,n=n,m=m,N=n+m,sampling_seed=s,clock=clock,
            numerator_policy=num,denominator_policy=den,graph_inputs=len(medians),**pair_summary(fractions),
            minimum_graph_median=float(min(medians)),maximum_graph_median=float(max(medians))))
    a.require(len(pairs)==len(cases)*len(comparisons(policies))*2*reps,'paired timing count')
    return dict(pairs=pairs,cases=case_rows,pooled=pool_rows,times=times)


def fit_timing(rows):
    """Google objective on new native calls; not library BigO output."""
    groups=defaultdict(list);fits=[];residuals=[]
    for row in measured(rows):
        for clock in ('wall_ns','cpu_ns'):
            groups[(row['family'],row['graph_seed'],row['sampling_seed'],row['policy'],clock)].append(row)
    for key,group in groups.items():
        family,g,s,policy,clock=key;group.sort(key=lambda r:(r['n'],r['repetition']))
        a.require(len(group)==18 and sorted({r['n'] for r in group})==list(a.SIZES),'six-size native timing fit')
        for aggregate in ('all_calls','size_means'):
            if aggregate=='all_calls':points=[(r['n'],r['n']+r['m'],r['repetition'],Fraction(r[clock])) for r in group]
            else:points=[(n,next(r['n']+r['m'] for r in group if r['n']==n),0,
                          Fraction(sum(r[clock] for r in group if r['n']==n),3)) for n in a.SIZES]
            scores=[];average=float(sum(x[3] for x in points)/len(points))
            for model in ('N','NlgN'):
                xs=[N if model=='N' else N*math.log2(N) for _,N,_,_ in points];scale=max(xs);basis=[x/scale for x in xs]
                ys=[float(x[3]) for x in points];coefficient=math.fsum(x*y for x,y in zip(basis,ys))/math.fsum(x*x for x in basis)
                errors=[y-coefficient*x for x,y in zip(basis,ys)]
                rms=math.sqrt(math.fsum(e*e for e in errors)/len(errors))/average
                entry=dict(family=family,graph_seed=g,sampling_seed=s,policy=policy,clock=clock,
                    aggregation=aggregate,model=model,observations=len(points),distinct_sizes=6,
                    coefficient_ns=coefficient/scale,normalized_rms=rms)
                scores.append(entry)
                for (n,N,rep,value),x,error in zip(points,basis,errors):
                    residuals.append(dict(entry,n=n,N=N,repetition=rep,observed_ns=float(value),
                        observed_exact_numerator=value.numerator,observed_exact_denominator=value.denominator,
                        predicted_ns=coefficient*x,residual_ns=error))
            best=min(scores,key=lambda x:x['normalized_rms'])['model']
            for entry in scores:entry['selected_between_two']=entry['model']==best
            fits.extend(scores)
    a.require(len(fits)==96 and len(residuals)==1152,'timing fit/residual counts')
    return fits,residuals


def work_tables(rows,baseline):
    result=[];summaries=[];selected=measured(rows)
    a.require(len(selected)==72,'candidate work size')
    for row in selected:
        old=baseline[a.casekey(row)][1];a.require(a.identity(old)==a.identity(row),'baseline/candidate work fingerprints')
        ident={k:row[k] for k in a.IDENTITY};N=row['n']+row['m'];before=old['work'];after=row['work']
        a.require(set(before)==set(after) and len(before)==65,'counter inventory')
        for field,value in before.items():
            expected=before['lca_vertices'] if field=='initialized_slots' else 0
            a.require(value-after[field]==expected,'unexpected independent work delta: '+field)
            q,status=ratio(after[field],value)
            result.append(dict(ident,N=N,counter=field,reference=value,depth=after[field],depth_minus_reference=after[field]-value,
                reference_per_N=value/N,depth_per_N=after[field]/N,depth_over_reference=q,ratio_status=status))
        a.require(before['lca_vertices']>0,'missing depth dispatch witness')
        summaries.append(dict(ident,N=N,equal_counters=64,decreased_counter='initialized_slots',
            initialized_slots_saved=before['lca_vertices'],saved_per_N=before['lca_vertices']/N))
    a.require(len(result)==4680,'work field count')
    return result,summaries


def phase_tables(rows,mode):
    cases,policies,reps=schedule(mode);a.require(reps==3,'phase repetitions')
    by={(a.casekey(r),r['policy'],r['repetition']):r for r in measured(rows)};times=[];deltas=[]
    for case in cases:
        key=a.casekey(case);example=by[(key,policies[0],1)];ident={k:example[k] for k in a.IDENTITY};N=ident['n']+ident['m']
        values={}
        for policy in policies:
            for phase in (*a.PHASES,'outside_collector','total'):
                ns=[]
                for rep in (1,2,3):
                    row=by[(key,policy,rep)]
                    ns.append(row['wall_ns'] if phase=='total' else row['wall_ns']-row['phase_total_ns'] if phase=='outside_collector' else row['phases'][phase]['wall_ns'])
                values[(policy,phase)]=ns
                times.append(dict(ident,N=N,policy=policy,phase=phase,**a.summary(ns),median_ns_per_N=statistics.median(ns)/N))
        for numerator,denominator in comparisons(policies):
            sums={}
            for phase in (*a.PHASES,'outside_collector','total'):
                num,den=(values[(p,phase)] for p in (numerator,denominator))
                delta=Fraction(sum(num)-sum(den),3*N);sums[phase]=delta
                q,status=ratio(sum(num),sum(den))
                deltas.append(dict(ident,N=N,numerator_policy=numerator,denominator_policy=denominator,phase=phase,
                    numerator_mean_ns_per_N=float(Fraction(sum(num),3*N)),denominator_mean_ns_per_N=float(Fraction(sum(den),3*N)),
                    mean_delta_ns_per_N=float(delta),delta_exact_numerator=delta.numerator,delta_exact_denominator=delta.denominator,
                    ratio_of_means=q,ratio_status=status))
            a.require(sum(v for k,v in sums.items() if k!='total')==sums['total'],'phase difference exact additivity')
    return times,deltas


def allocation_tables(rows):
    cases,policies,reps=schedule('allocation');a.require(reps==1,'allocation repetitions')
    by={(a.casekey(r),r['policy']):r for r in measured(rows)};table=[]
    for case in cases:
        key=a.casekey(case);old,new=(by[(key,p)] for p in policies);a.require(a.identity(old)==a.identity(new),'allocation identity')
        def metrics(row):
            result={k:row[k] for k in ('peak_live_usable_bytes','returned_live_usable_bytes')}
            for metric in ('allocations','requested_bytes','usable_bytes','deallocations','freed_usable_bytes'):
                result['cumulative_'+metric]=sum(p[metric] for p in row['phases'].values())
            for phase,values in row['phases'].items():
                for metric in ('allocations','requested_bytes','usable_bytes','freed_usable_bytes'):result[phase+'__cumulative_'+metric]=values[metric]
            return result
        before,after=metrics(old),metrics(new);N=old['n']+old['m'];ident={k:old[k] for k in a.IDENTITY}
        for metric,value in before.items():
            q,status=ratio(after[metric],value)
            table.append(dict(ident,N=N,metric=metric,reference=value,depth=after[metric],depth_minus_reference=after[metric]-value,
                              reference_per_N=value/N,depth_per_N=after[metric]/N,depth_over_reference=q,ratio_status=status))
    a.require(len(table)==1566,'allocation metric count')
    return table


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for mode in MODES:parser.add_argument('--'+mode,type=Path)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    requested={mode:getattr(args,mode.replace('-','_')) for mode in MODES if getattr(args,mode.replace('-','_')) is not None}
    a.require(requested,'provide at least one completed capture')
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False);bound={};artifacts={};raw={};records={}
    status=dict(schema='kkt_depth_candidate_analysis_v1',validation='running',native_execution=False,input_sha256=bound,
        modes=list(requested),invocation=sys.argv,rows_removed=0,rows_adjusted=0,
        fit_scope='Numerical reanalysis of native calls, not a Google Benchmark run. All-call and size-mean fits explicitly separate.',
        instrumentation_scope='Only timing and inline-control are uninstrumented comparisons; other clocks are diagnostic.')
    try:
        a.read(__file__,bound);a.read(a.__file__,bound)
        for mode,path in requested.items():
            info,rows,module=load(path,mode,bound);raw[mode]=rows;records[mode]=info
            if mode in ('timing','inline-control'):
                for name,table in timing_tables(rows,mode).items():artifacts[mode+'-'+name]=table
                if mode=='timing':artifacts['timing-fits'],artifacts['timing-residuals']=fit_timing(rows)
            elif mode=='work':
                build,_=module.read(info['build_record']);baseline,proof=module.baseline_work(Path(info['baseline_work']),Path(build['snapshot']));merge(bound,proof)
                artifacts['work-counters'],artifacts['work-summary']=work_tables(rows,baseline)
            elif mode in ('phase','inline-phase'):artifacts[mode+'-times'],artifacts[mode+'-deltas']=phase_tables(rows,mode)
            else:artifacts['allocation-counters']=allocation_tables(rows)
        a.require(len({r['build_record_sha256'] for r in records.values()})==1,'mixed candidate builds')
        for name,table in artifacts.items():a.write_csv(output/(name+'.csv'),table)
        (output/'all_raw_rows.json').write_text(json.dumps(raw,indent=2)+'\n')
        a.recheck(bound);status.update(validation='pass',table_counts={k:len(v) for k,v in artifacts.items()},
            raw_counts={k:len(v) for k,v in raw.items()},warmups_retained={k:sum(r['warmup'] for r in v) for k,v in raw.items()},
            utc_reversals={k:sum(r['utc_end_ns']<r['utc_start_ns'] for r in v) for k,v in raw.items()})
    except BaseException as error:status.update(validation='failed',error=repr(error));raise
    finally:
        status['output_sha256']={p.name:a.sha(p) for p in output.iterdir() if p.is_file()}
        (output/'provenance.json').write_text(json.dumps(status,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:status[k] for k in ('validation','modes','raw_counts','table_counts')}))


if __name__=='__main__':main()
