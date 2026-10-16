#!/usr/bin/env python3
"""Synthetic Google-export arithmetic checks; never launches a benchmark."""
import copy
from fractions import Fraction
import statistics
import unittest

import analyze_candidate_google as g


def fixture():
    rows=[]
    for fi,family in enumerate(('leaf_hierarchy4','leaf_shuffled4','gnm_random')):
        for policy in ('reference','depth'):
            for size in range(10,21):
                n=1<<size;m=n*(16 if family=='gnm_random' else 32)
                for invocation in range(3):
                    for phase,iteration in (('warmup',0),('timed',0),('timed',1)):
                        position=invocation*2+iteration
                        # Different clocks and trial order, retaining wins and losses.
                        wall=(n+m)*(71+fi*7)+(position+1)**2*101
                        cpu=(n+m)*(59+fi*11)+(6-position)**2*233
                        if policy=='depth':
                            wall=wall*(81+position*5)//100+17
                            cpu=cpu*(109-position*5)//100+31
                        rows.append(dict(family=family,algorithm='kkt',policy=policy,n=n,m=m,N=n+m,
                            graph_seed=19000013,sampling_seed=3001,input_fingerprint=n+fi+100,
                            topology_fingerprint=n+fi+200,size_order='ascending',invocation=invocation,
                            phase=phase,iteration=iteration,elapsed_ns=wall,process_cpu_elapsed_ns=cpu))
    return rows


def captures():
    values=[]
    for fi,family in enumerate(('leaf_hierarchy4','leaf_shuffled4','gnm_random')):
        for pi,policy in enumerate(('reference','depth')):
            values.append(dict(policy=policy,spec=dict(family=family,algorithm='kkt',graph_seed=19000013,
                sampling_seed=3001,size_order='ascending'),
                library_big_o=dict(aggregate_name='BigO',time_unit='ns',big_o='NlgN',
                    cpu_coefficient=3.25+fi+pi/4,real_coefficient=4.75+fi+pi/8),
                library_rms=dict(aggregate_name='RMS',rms=.0125+fi/100+pi/1000)))
    return values


class GoogleCandidateAnalysis(unittest.TestCase):
    def test_full_native_identity_ratios_means_and_medians(self):
        raw=fixture();saved=copy.deepcopy(raw);tables=g.native_tables(raw)
        self.assertEqual(raw,saved)
        self.assertEqual({k:len(v) for k,v in tables.items()},
            {'native-pairs':396,'native-summary':66,'native-two-call-means':396,'native-times':132})
        index={(r['family'],r['policy'],r['n'],r['invocation'],r['iteration']):r
               for r in raw if r['phase']=='timed'}
        expected={}
        for family in ('leaf_hierarchy4','leaf_shuffled4','gnm_random'):
            for n in (1024,2048,4096,8192,16384,32768,65536,131072,262144,524288,1048576):
                for invocation in (0,1,2):
                    for iteration in (0,1):
                        for clock in ('elapsed_ns','process_cpu_elapsed_ns'):
                            key=(family,n,invocation,iteration,clock)
                            expected[key]=Fraction(index[(family,'depth',n,invocation,iteration)][clock],
                                                   index[(family,'reference',n,invocation,iteration)][clock])
        actual={(r['family'],r['n'],r['invocation'],r['iteration'],r['clock']):
                Fraction(r['exact_numerator'],r['exact_denominator']) for r in tables['native-pairs']}
        self.assertEqual(actual,expected)
        for r in tables['native-two-call-means']:
            values=[index[(r['family'],r['policy'],r['n'],r['invocation'],i)][r['clock']] for i in (0,1)]
            self.assertEqual(Fraction(r['exact_numerator'],r['exact_denominator']),Fraction(sum(values),2))
        for r in tables['native-summary']:
            values=[expected[(r['family'],r['n'],v,i,r['clock'])] for v in (0,1,2) for i in (0,1)]
            self.assertEqual(r['median_paired_ratio'],float(statistics.median(values)))
            self.assertEqual(r['observations'],6)
            self.assertEqual(r['numerator_wins'],sum(q<1 for q in values))
            self.assertEqual(r['numerator_losses'],sum(q>1 for q in values))
        for r in tables['native-times']:
            values=[index[(r['family'],r['policy'],r['n'],v,i)][r['clock']] for v in (0,1,2) for i in (0,1)]
            self.assertEqual((r['median_ns'],r['minimum_ns'],r['maximum_ns']),
                             (float(statistics.median(values)),min(values),max(values)))

    def test_matrix_fingerprints_scope_and_exact_types_reject(self):
        raw=fixture()
        for changed in (raw[:-1],raw+[raw[0]]):
            with self.assertRaises(ValueError):g.validate_rows(changed)
        for field,value in (('graph_seed',19000043),('sampling_seed',3011),('size_order','descending'),
                ('input_fingerprint',0),('topology_fingerprint',0),('N',1),('invocation',False),
                ('elapsed_ns',0),('process_cpu_elapsed_ns',-1),('iteration',0.0)):
            changed=copy.deepcopy(raw);changed[0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):g.validate_rows(changed)

    def test_actual_library_records_are_retained_without_refit(self):
        original=captures();before=copy.deepcopy(original);choices,comparison,exported=g.actual_library_tables(original)
        self.assertEqual(original,before);self.assertEqual(exported,before)
        self.assertEqual((len(choices),len(comparison)),(6,3))
        for item,row in zip(original,choices):
            self.assertEqual(row['selected_model'],item['library_big_o']['big_o'])
            self.assertEqual(row['cpu_coefficient_ns'],item['library_big_o']['cpu_coefficient'])
            self.assertEqual(row['manual_coefficient_ns'],item['library_big_o']['real_coefficient'])
            self.assertEqual(row['exported_cpu_normalized_rms'],item['library_rms']['rms'])
            self.assertIs(row['manual_rms_exported'],False)
        for fi,row in enumerate(comparison):
            self.assertEqual(row['cpu_coefficient_depth_over_reference'],(3.5+fi)/(3.25+fi))
        changed=copy.deepcopy(original);changed[1]['library_big_o']['big_o']='N'
        _,different,_=g.actual_library_tables(changed)
        self.assertEqual(different[0]['coefficient_ratio_status'],'different_models_not_comparable')
        self.assertEqual(different[0]['cpu_coefficient_depth_over_reference'],'')
        self.assertEqual(different[0]['manual_coefficient_depth_over_reference'],'')
        for bad in (original[:-1],original+[original[0]]):
            with self.assertRaises(ValueError):g.actual_library_tables(bad)
        changed=copy.deepcopy(original);changed[0]['library_big_o']['time_unit']='ms'
        with self.assertRaises(ValueError):g.actual_library_tables(changed)

    def test_paired_ratio_and_separate_medians_can_disagree(self):
        raw=fixture();family='gnm_random';n=1024
        for r in raw:
            if r['family']==family and r['n']==n and r['phase']=='timed':
                i=r['invocation']*2+r['iteration']
                r['elapsed_ns']=((5,110,900,5,110,900) if r['policy']=='depth' else (10,100,1000,10,100,1000))[i]
        row=next(r for r in g.native_tables(raw)['native-summary'] if r['family']==family and r['n']==n and r['clock']=='elapsed_ns')
        self.assertEqual(row['median_paired_ratio'],.9)
        self.assertEqual(row['ratio_of_separate_medians'],1.1)
        self.assertEqual((row['numerator_wins'],row['numerator_losses']),(4,2))
        self.assertEqual(Fraction(row['separate_exact_numerator'],row['separate_exact_denominator']),Fraction(11,10))


if __name__=='__main__':unittest.main()
