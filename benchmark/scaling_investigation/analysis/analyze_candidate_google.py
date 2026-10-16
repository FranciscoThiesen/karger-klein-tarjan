#!/usr/bin/env python3
"""Preserve actual Google BigO/RMS; pair fresh native calls without refitting labels."""
import argparse
from collections import defaultdict
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import statistics
import sys

import analyze_diagnostics as a
import analyze_candidate as c

RUNNER=a.HERE.parent/'google/run_google.py'
SIZES=tuple(1<<i for i in range(10,21))
GRAPH,SAMPLER=19000013,3001
CLOCKS=('elapsed_ns','process_cpu_elapsed_ns')


def validate_rows(rows):
    expected={(f,p,n,v,phase,iteration) for f in a.FAMILIES for p in ('reference','depth') for n in SIZES
              for v in range(3) for phase,iteration in (('warmup',0),('timed',0),('timed',1))}
    actual={};fingerprints={}
    for r in rows:
        a.require(all(type(r[k]) is int and r[k]>=0 for k in ('n','m','N','graph_seed','sampling_seed','input_fingerprint','topology_fingerprint','invocation','iteration',*CLOCKS)), 'exact unsigned Google native fields')
        a.require(all(r[k]>0 for k in CLOCKS),'positive native clock durations')
        a.require(r['graph_seed']==GRAPH and r['sampling_seed']==SAMPLER and r['algorithm']=='kkt' and r['size_order']=='ascending','one-graph Google scope')
        a.require(r['m']==r['n']*(16 if r['family']=='gnm_random' else 32) and r['N']==r['n']+r['m'],'Google dimensions')
        key=(r['family'],r['policy'],r['n'],r['invocation'],r['phase'],r['iteration']);a.require(key not in actual,'duplicate Google native call');actual[key]=r
        pair=(r['input_fingerprint'],r['topology_fingerprint']);fpkey=(r['family'],r['n'])
        a.require(fpkey not in fingerprints or fingerprints[fpkey]==pair,'Google cross-policy fingerprint mismatch');fingerprints[fpkey]=pair
    a.require(set(actual)==expected and len(rows)==594,'independent six-curve native matrix')


def native_tables(rows):
    validate_rows(rows);timed={(r['family'],r['n'],r['policy'],r['invocation'],r['iteration']):r for r in rows if r['phase']=='timed'}
    pairs=[];summary=[];means=[];times=[]
    for family in a.FAMILIES:
        for n in SIZES:
            example=timed[(family,n,'reference',0,0)];ident={k:example[k] for k in a.IDENTITY};N=example['N']
            for clock in CLOCKS:
                values=[];absolute={p:[] for p in ('reference','depth')}
                for invocation in range(3):
                    for policy in ('reference','depth'):
                        two=[timed[(family,n,policy,invocation,i)][clock] for i in (0,1)]
                        mean=Fraction(sum(two),2);means.append(dict(ident,N=N,policy=policy,clock=clock,invocation=invocation,mean_ns=float(mean),exact_numerator=mean.numerator,exact_denominator=mean.denominator))
                    for iteration in (0,1):
                        ref=timed[(family,n,'reference',invocation,iteration)][clock];depth=timed[(family,n,'depth',invocation,iteration)][clock]
                        q=Fraction(depth,ref);values.append(q);absolute['reference'].append(Fraction(ref));absolute['depth'].append(Fraction(depth))
                        pairs.append(dict(ident,N=N,clock=clock,invocation=invocation,iteration=iteration,reference_ns=ref,depth_ns=depth,
                            depth_over_reference=float(q),exact_numerator=q.numerator,exact_denominator=q.denominator))
                refmed=statistics.median(absolute['reference']);depmed=statistics.median(absolute['depth']);q=depmed/refmed
                summary.append(dict(ident,N=N,clock=clock,**c.pair_summary(values),reference_median_ns=float(refmed),depth_median_ns=float(depmed),
                    ratio_of_separate_medians=float(q),separate_exact_numerator=q.numerator,separate_exact_denominator=q.denominator))
                for policy,ns in absolute.items():times.append(dict(ident,N=N,clock=clock,policy=policy,observations=6,median_ns=float(statistics.median(ns)),minimum_ns=int(min(ns)),maximum_ns=int(max(ns))))
    a.require((len(pairs),len(summary),len(means),len(times))==(396,66,396,132),'Google native table counts')
    return {'native-pairs':pairs,'native-summary':summary,'native-two-call-means':means,'native-times':times}


def actual_library_tables(captures):
    rows=[];raw=[];indexed={}
    for item in captures:
        spec=item['spec'];policy=item['policy'];family=spec['family'];key=(family,policy)
        a.require(key not in indexed and family in a.FAMILIES and policy in ('reference','depth'),'library curve identity')
        a.require(spec==dict(family=family,algorithm='kkt',graph_seed=GRAPH,sampling_seed=SAMPLER,size_order='ascending'),'library curve scope')
        big=item['library_big_o'];rms=item['library_rms']
        a.require(big['aggregate_name']=='BigO' and rms['aggregate_name']=='RMS' and big['time_unit']=='ns','actual library aggregate units/types')
        row=dict(family=family,policy=policy,graph_seed=GRAPH,sampling_seed=SAMPLER,sizes=11,callbacks=33,
            selected_model=big['big_o'],cpu_coefficient_ns=big['cpu_coefficient'],manual_coefficient_ns=big['real_coefficient'],
            exported_cpu_normalized_rms=rms['rms'],manual_rms_exported=False,model_selected_using='library_process_cpu',
            manual_coefficient_uses='same_CPU_selected_model')
        indexed[key]=row;rows.append(row);raw.append(dict(policy=policy,spec=spec,library_big_o=big,library_rms=rms))
    a.require(set(indexed)=={(f,p) for f in a.FAMILIES for p in ('reference','depth')},'six actual library curves')
    comparisons=[]
    for family in a.FAMILIES:
        ref,dep=(indexed[(family,p)] for p in ('reference','depth'));same=ref['selected_model']==dep['selected_model']
        comparisons.append(dict(family=family,graph_seed=GRAPH,sampling_seed=SAMPLER,reference_model=ref['selected_model'],depth_model=dep['selected_model'],
            coefficient_ratio_status='same_model' if same else 'different_models_not_comparable',
            cpu_coefficient_depth_over_reference=dep['cpu_coefficient_ns']/ref['cpu_coefficient_ns'] if same else '',
            manual_coefficient_depth_over_reference=dep['manual_coefficient_ns']/ref['manual_coefficient_ns'] if same else '',
            reference_exported_cpu_rms=ref['exported_cpu_normalized_rms'],depth_exported_cpu_rms=dep['exported_cpu_normalized_rms']))
    return rows,comparisons,raw


def load(path,bound):
    path=path.resolve();pre=a.parse(a.read(path,bound));a.require(pre['schema']=='kkt_depth_google_capture_v1' and pre['validation']=='pass','complete actual Google capture required')
    build=a.parse(a.read(pre['build_record'],bound,pre['build_record_sha256']))
    candidate=a.parse(a.read(build['candidate_build'],bound,build['candidate_build_sha256']))
    for inventory in (build['source_sha256'],candidate['source_sha256']):
        for source,digest in inventory.items():
            if source.endswith('.py') or source==str(a.ROOT/'benchmark/work_metrics.hpp'):a.bind(source,bound,digest)
    a.require(str(RUNNER) in build['source_sha256'],'Google runner binding')
    spec=importlib.util.spec_from_file_location('candidate_google_provenance',RUNNER);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    info,rows,proof=module.load(path);c.merge(bound,proof);a.require(info==pre,'Google capture changed during load');validate_rows(rows);a.recheck(bound)
    return info,rows


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--capture',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False);bound={};status=dict(schema='kkt_depth_google_analysis_v1',validation='running',native_execution=False,input_sha256=bound,invocation=sys.argv,
        graph_seeds=[GRAPH],sampling_seeds=[SAMPLER],rows_removed=0,rows_adjusted=0,library_choices='Actual BigO/RMS records, not substituted custom fits',
        scope='One graph/sampler, all11sizes ascending; separate process curves, paired by callback/iteration labels; no pooling with primary native study.')
    try:
        for source in (__file__,a.__file__,c.__file__):a.read(source,bound)
        info,rows=load(args.capture,bound);tables=native_tables(rows);choices,comparisons,raw=actual_library_tables(info['captures'])
        tables.update({'actual-library-choices':choices,'library-coefficient-comparison':comparisons})
        for name,table in tables.items():a.write_csv(out/(name+'.csv'),table)
        (out/'actual-library-BigO-RMS.json').write_text(json.dumps(raw,indent=2)+'\n')
        (out/'all-native-rows.json').write_text(json.dumps(rows,indent=2)+'\n')
        for i,item in enumerate(info['captures']):
            source=Path(item['benchmark_json']);a.read(source,bound)
            destination=out/f'original-library-{i:02d}.json';destination.write_bytes(source.read_bytes())
            a.require(a.sha(destination)==bound[str(source.resolve())],'original Google JSON copy differs')
        diagnostics=[dict(policy=r['policy'],spec=r['spec'],diagnostics=r['diagnostics']) for r in info['captures']]
        (out/'native-clock-diagnostics.json').write_text(json.dumps(diagnostics,indent=2)+'\n')
        a.recheck(bound);status.update(validation='pass',raw_rows=len(rows),warmup_rows=sum(r['phase']=='warmup' for r in rows),table_counts={k:len(v) for k,v in tables.items()})
    except BaseException as error:status.update(validation='failed',error=repr(error));raise
    finally:
        status['output_sha256']={p.name:a.sha(p) for p in out.iterdir() if p.is_file()};(out/'provenance.json').write_text(json.dumps(status,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:status[k] for k in ('validation','raw_rows','warmup_rows','table_counts')}))


if __name__=='__main__':main()
