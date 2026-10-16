#!/usr/bin/env python3
"""Summarize every completed Google native pair from integer rows; no new fits."""
import argparse
import csv
from fractions import Fraction
import io
import json
from pathlib import Path
import statistics

import analyze_candidate_google as g

a=g.a


def sign_counts(values):
    return dict(comparisons=len(values),wins=sum(q<1 for q in values),ties=sum(q==1 for q in values),
                losses=sum(q>1 for q in values),minimum=float(min(values)),maximum=float(max(values)))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--analysis',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    source=args.analysis.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False);bound={}
    for path in (__file__,g.__file__,a.__file__):a.read(path,bound)
    proof=a.parse(a.read(source/'provenance.json',bound))
    a.require(proof['schema']=='kkt_depth_google_analysis_v1' and proof['validation']=='pass','completed Google analysis')
    g.c.merge(bound,proof['input_sha256']);a.recheck(bound)
    def read(name):return a.read(source/name,bound,proof['output_sha256'][name])
    raw=a.parse(read('all-native-rows.json'));g.validate_rows(raw)
    exported=list(csv.DictReader(io.StringIO(read('native-pairs.csv'))))
    canonical=list(csv.DictReader(io.StringIO(read('native-summary.csv'))))
    native={(r['family'],r['n'],r['policy'],r['invocation'],r['iteration']):r for r in raw if r['phase']=='timed'}
    pairs={};summaries=[];losses=[]
    for family in ('leaf_hierarchy4','leaf_shuffled4','gnm_random'):
        for n in (1024,2048,4096,8192,16384,32768,65536,131072,262144,524288,1048576):
            for clock in ('elapsed_ns','process_cpu_elapsed_ns'):
                values=[];ref=[];depth=[]
                for callback in (0,1,2):
                    for iteration in (0,1):
                        before=native[(family,n,'reference',callback,iteration)][clock]
                        after=native[(family,n,'depth',callback,iteration)][clock]
                        q=Fraction(after,before);values.append(q);ref.append(Fraction(before));depth.append(Fraction(after))
                        key=(family,n,clock,callback,iteration);a.require(key not in pairs,'duplicate native pair');pairs[key]=q
                        if q>=1:losses.append(dict(family=family,n=n,clock=clock,invocation=callback,iteration=iteration,
                            reference_ns=before,depth_ns=after,ratio=float(q),exact_numerator=q.numerator,exact_denominator=q.denominator))
                median=statistics.median(values);separate=statistics.median(depth)/statistics.median(ref)
                summaries.append(dict(family=family,n=n,clock=clock,graph_seed=19000013,sampling_seed=3001,
                    paired_median=float(median),paired_exact_numerator=median.numerator,paired_exact_denominator=median.denominator,
                    separate_median_ratio=float(separate),separate_exact_numerator=separate.numerator,separate_exact_denominator=separate.denominator,
                    reference_median_ns=float(statistics.median(ref)),depth_median_ns=float(statistics.median(depth)),**sign_counts(values)))
    actual={(r['family'],int(r['n']),r['clock'],int(r['invocation']),int(r['iteration'])):
            Fraction(int(r['exact_numerator']),int(r['exact_denominator'])) for r in exported}
    a.require(len(exported)==len(actual)==len(pairs)==396 and actual==pairs,'exported pairs do not match raw')
    indexed={(r['family'],int(r['n']),r['clock']):r for r in canonical};a.require(len(canonical)==len(indexed)==66,'summary identities')
    for r in summaries:
        stored=indexed[(r['family'],r['n'],r['clock'])]
        a.require(float(stored['median_paired_ratio'])==r['paired_median'] and
            Fraction(int(stored['separate_exact_numerator']),int(stored['separate_exact_denominator']))==
            Fraction(r['separate_exact_numerator'],r['separate_exact_denominator']),'summary disagrees with integer raw')
    statistics_by_clock={}
    for clock in ('elapsed_ns','process_cpu_elapsed_ns'):
        values=[q for key,q in pairs.items() if key[2]==clock];cases=[r for r in summaries if r['clock']==clock]
        medians=[Fraction(r['paired_exact_numerator'],r['paired_exact_denominator']) for r in cases]
        separate=[Fraction(r['separate_exact_numerator'],r['separate_exact_denominator']) for r in cases]
        statistics_by_clock[clock]=dict(individual_pairs=sign_counts(values),paired_medians=sign_counts(medians),separate_medians=sign_counts(separate))
    a.write_csv(out/'all-input-medians.csv',summaries)
    if losses:a.write_csv(out/'all-nonwinning-pairs.csv',losses)
    exceptions=[r for r in summaries if r['paired_median']>=1 or r['separate_median_ratio']>=1]
    if exceptions:a.write_csv(out/'all-nonwinning-input-summaries.csv',exceptions)
    endpoints=[r for r in summaries if r['n']==1048576];a.write_csv(out/'largest-inputs.csv',endpoints)
    a.recheck(bound);result=dict(schema='kkt_depth_google_summary_v1',validation='pass',native_execution=False,
        raw_rows=len(raw),clock_statistics=statistics_by_clock,nonwinning_input_clock_rows=len(exceptions),
        input_sha256=bound,output_sha256={p.name:a.sha(p) for p in out.iterdir() if p.is_file()})
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(clock_statistics=statistics_by_clock,nonwinning_inputs=exceptions,largest_inputs=endpoints),indent=2))


if __name__=='__main__':main()
