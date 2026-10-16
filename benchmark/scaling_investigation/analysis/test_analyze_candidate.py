#!/usr/bin/env python3
"""Prepared synthetic arithmetic checks; no native process or captured timing."""
import copy
from fractions import Fraction
import statistics
import unittest

import analyze_candidate as c


def fixture(mode):
    cases,policies,reps=c.schedule(mode);rows=[]
    for case in cases:
        n=case['n'];m=n*(16 if case['family']=='gnm_random' else 32);N=n+m
        for policy in policies:
            factor={'reference':100,'depth':80,'depth_noinline':93}[policy]
            for rep in range(reps+1):
                phases={name:dict(wall_ns=N*(i+1)*factor+rep*rep,calls=1,allocations=3,
                    requested_bytes=N*2,usable_bytes=N*3,deallocations=2,freed_usable_bytes=N)
                    for i,name in enumerate(c.a.PHASES)}
                phases['query_gather']['wall_ns']+=N*(case['graph_seed']%7)+rep*factor
                phase_total=sum(v['wall_ns'] for v in phases.values())
                rows.append(dict(case,m=m,input_fingerprint=n+case['graph_seed'],topology_fingerprint=n+case['graph_seed']+1,
                    policy=policy,repetition=rep,warmup=rep==0,wall_ns=phase_total+N+rep*3,
                    cpu_ns=phase_total//2+N*factor+rep*11,phase_total_ns=phase_total,phases=phases,
                    peak_live_usable_bytes=N*4,returned_live_usable_bytes=N))
    return rows


class CandidateAnalysis(unittest.TestCase):
    def test_complete_timing_identity_and_exact_ratios_both_clocks(self):
        rows=fixture('timing');c.validate_matrix(rows,'timing');tables=c.timing_tables(rows,'timing')
        self.assertEqual({k:len(v) for k,v in tables.items()},dict(pairs=216,cases=72,pooled=36,times=144))
        raw={(c.a.casekey(r),r['policy'],r['repetition']):r for r in rows}
        expected={}
        for family in ('leaf_hierarchy4','leaf_shuffled4','gnm_random'):
            for n in (1024,4096,16384,65536,262144,1048576):
                for g in (19000013,19000043):
                    case=(family,n,g,3001)
                    for rep in (1,2,3):
                        for clock in ('wall_ns','cpu_ns'):
                            expected[(case,rep,clock)]=Fraction(raw[(case,'depth',rep)][clock],raw[(case,'reference',rep)][clock])
        actual={(c.a.casekey(r),r['repetition'],r['clock']):Fraction(r['exact_numerator'],r['exact_denominator']) for r in tables['pairs']}
        self.assertEqual(actual,expected)
        for r in tables['cases']:
            ratios=[expected[(c.a.casekey(r),rep,r['clock'])] for rep in (1,2,3)]
            self.assertEqual(r['median_paired_ratio'],float(statistics.median(ratios)))
        for r in tables['pooled']:
            ratios=[expected[((r['family'],r['n'],g,3001),rep,r['clock'])] for g in (19000013,19000043) for rep in (1,2,3)]
            self.assertEqual(r['median_paired_ratio'],float(statistics.median(ratios)))

    def test_three_policy_inline_controls_have_all_pair_directions(self):
        rows=fixture('inline-control');c.validate_matrix(rows,'inline-control');t=c.timing_tables(rows,'inline-control')
        self.assertEqual({k:len(v) for k,v in t.items()},dict(pairs=108,cases=36,pooled=36,times=36))
        self.assertEqual({(r['numerator_policy'],r['denominator_policy']) for r in t['pairs']},
                         {('depth','reference'),('depth_noinline','reference'),('depth_noinline','depth')})
        self.assertTrue(all(r['graph_inputs']==1 for r in t['pooled']))

    def test_missing_duplicate_fingerprint_and_warmup_fail_closed(self):
        rows=fixture('timing')
        for changed in (rows[:-1],rows+[rows[0]]):
            with self.assertRaises(ValueError):c.validate_matrix(changed,'timing')
        for key,value in (('input_fingerprint',0),('warmup',1),('repetition',False),('sampling_seed',3011)):
            changed=copy.deepcopy(rows);changed[0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):c.validate_matrix(changed,'timing')

    def test_native_call_fits_linear_oracle_and_all_residuals(self):
        rows=fixture('timing')
        for r in rows:
            N=r['n']+r['m'];r['wall_ns']=N*17;r['cpu_ns']=N*11
        fits,residuals=c.fit_timing(rows)
        self.assertEqual((len(fits),len(residuals)),(96,1152))
        self.assertEqual({r['observations'] for r in fits},{6,18})
        self.assertTrue(all(r['selected_between_two']==(r['model']=='N') for r in fits))
        for r in fits:
            if r['model']=='N':self.assertAlmostEqual(r['coefficient_ns'],17 if r['clock']=='wall_ns' else 11,places=10)
        self.assertTrue(all(abs(r['residual_ns'])<1e-5 for r in residuals if r['model']=='N'))
        with self.assertRaises(ValueError):c.fit_timing(rows[:-1])

    def test_work_only_initialized_slots_changes_and_zero_is_explicit(self):
        rows=fixture('work');baseline={}
        for row in rows:
            n=row['n'];before={'initialized_slots':5*n,'lca_vertices':n,**{'counter_'+str(i):n*i for i in range(63)}}
            old=copy.deepcopy(row);old['work']=before;after=dict(before);after['initialized_slots']-=n;row['work']=after
            baseline.setdefault(c.a.casekey(row),[]).append(old)
        counters,summary=c.work_tables(rows,baseline)
        self.assertEqual((len(counters),len(summary)),(4680,72))
        self.assertEqual(sum(r['depth_minus_reference']<0 for r in counters),72)
        self.assertEqual(sum(r['ratio_status']=='both_zero' for r in counters),72)
        changed=copy.deepcopy(rows);changed[1]['work']['counter_2']+=1
        with self.assertRaises(ValueError):c.work_tables(changed,baseline)

    def test_phase_difference_is_exact_and_includes_outside_for_three_policies(self):
        for mode,counts in (('phase',(792,396)),('inline-phase',(396,396))):
            rows=fixture(mode);c.validate_matrix(rows,mode);times,deltas=c.phase_tables(rows,mode)
            self.assertEqual((len(times),len(deltas)),counts)
            groups={}
            for r in deltas:
                key=(c.a.casekey(r),r['numerator_policy'],r['denominator_policy'])
                groups.setdefault(key,{})[r['phase']]=Fraction(r['delta_exact_numerator'],r['delta_exact_denominator'])
            for phases in groups.values():self.assertEqual(sum(x for p,x in phases.items() if p!='total'),phases['total'])

    def test_allocation_cumulative_and_live_labels_are_separate(self):
        rows=fixture('allocation');c.validate_matrix(rows,'allocation');table=c.allocation_tables(rows)
        self.assertEqual(len(table),1566)
        self.assertNotIn('live_requested_bytes',{r['metric'] for r in table})
        row=next(r for r in table if r['metric']=='cumulative_requested_bytes')
        self.assertEqual(row['reference'],row['N']*2*20)
        self.assertTrue(all(r['depth_over_reference']==1 for r in table))

    def test_zeros_losses_and_pair_median_not_separate_medians(self):
        self.assertEqual(c.ratio(0,4),(0.0,'defined'));self.assertEqual(c.ratio(0,0),('','both_zero'));self.assertEqual(c.ratio(4,0),('','zero_denominator'))
        rows=fixture('timing');case=c.a.casekey(rows[0])
        for row in rows:
            if c.a.casekey(row)==case and not row['warmup']:
                row['wall_ns']=((100,50,6) if row['policy']=='depth' else (10,100,2))[row['repetition']-1]
        table=c.timing_tables(rows,'timing')['cases'];r=next(x for x in table if c.a.casekey(x)==case and x['clock']=='wall_ns')
        self.assertEqual(r['median_paired_ratio'],3);self.assertEqual(r['ratio_of_medians'],5)
        self.assertEqual((r['numerator_wins'],r['numerator_losses']),(1,2))


if __name__=='__main__':unittest.main()
