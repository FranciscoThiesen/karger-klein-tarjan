#!/usr/bin/env python3
"""Synthetic exact plot-data checks; imports no plotting library and launches no solver."""
import copy
from fractions import Fraction
import statistics
import unittest

import analyze_candidate as c
import plot_candidate as p
from test_analyze_candidate import fixture


def data():
    work=fixture('work');baseline={}
    for row in work:
        N=row['n']+row['m'];before={'kkt_edges':3*N+row['graph_seed']%17,'initialized_slots':5*N,'lca_vertices':row['n'],
                                 **{'counter_'+str(i):N*i for i in range(62)}}
        old=copy.deepcopy(row);old['work']=before;row['work']=dict(before);row['work']['initialized_slots']-=row['n']
        baseline.setdefault(c.a.casekey(row),[]).append(old)
    return c.work_tables(work,baseline)[0],fixture('timing'),fixture('inline-control')


class CandidatePlotData(unittest.TestCase):
    def test_full_cartesian_normalization_from_independent_integers(self):
        work,timing,inline=data();tables=p.prepare(work,timing,inline)
        self.assertEqual({k:len(v) for k,v in tables.items()},
                         {'bending':216,'bending-trials':432,'ratios':216,'ratio-summary':72,'inline-ratios':108,'inline-summary':36})
        raw={(r['family'],r['n'],r['graph_seed'],r['policy'],r['repetition']):r for r in timing if not r['warmup']}
        counts={(r['family'],r['n'],r['graph_seed']):r for r in work if r['sampling_seed']==3001 and r['counter']=='kkt_edges'}
        expected={}
        for f in ('leaf_hierarchy4','leaf_shuffled4','gnm_random'):
            for g in (19000013,19000043):
                for clock in ('wall_ns','cpu_ns'):
                    small=counts[(f,1024,g)];N0=small['n']+small['m'];W0=small['reference']
                    T0=statistics.median(raw[(f,1024,g,'reference',rep)][clock] for rep in (1,2,3))
                    for n in (1024,4096,16384,65536,262144,1048576):
                        row=counts[(f,n,g)];N=row['n']+row['m']
                        expected[(f,n,g,clock,'work')]=Fraction(row['reference']*N0,W0*N)
                        for policy in ('reference','depth'):
                            T=statistics.median(raw[(f,n,g,policy,rep)][clock] for rep in (1,2,3))
                            expected[(f,n,g,clock,policy)]=Fraction(T*N0,T0*N)
        actual={(r['family'],r['n'],r['graph_seed'],r['clock'],r['series']):Fraction(r['exact_median_numerator'],r['exact_median_denominator']) for r in tables['bending']}
        self.assertEqual(actual,expected)
        self.assertTrue(all(r['median']==1 for r in tables['bending'] if r['n']==1024 and r['series'] in ('reference','work')))
        self.assertTrue(all(r['median']<1 for r in tables['bending'] if r['n']==1024 and r['series']=='depth'))
        for r in tables['bending-trials']:
            value=Fraction(r['native_ns']*r['small_N'],r['small_reference_ns']*r['N'])
            self.assertEqual(value,Fraction(r['normalized_time_numerator'],r['normalized_time_denominator']))

    def test_exact_work_joins_and_complete_inputs_fail_closed(self):
        work,timing,_=data()
        for field,value in (('input_fingerprint',0),('depth',0)):
            altered=copy.deepcopy(work);row=next(r for r in altered if r['counter']=='kkt_edges' and r['sampling_seed']==3001);row[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):p.prepare(altered,timing)
        for bad in (work[:-1],work+[work[0]]):
            with self.assertRaises(ValueError):p.prepare(bad,timing)
        with self.assertRaises(ValueError):p.prepare(work,timing[:-1])

    def test_no_inline_mode_and_retained_losses_ranges(self):
        work,timing,_=data();case=c.a.casekey(timing[0])
        for row in timing:
            if c.a.casekey(row)==case and row['policy']=='depth' and row['repetition']==2:row['wall_ns']*=20
        tables=p.prepare(work,timing)
        self.assertNotIn('inline-ratios',tables)
        loss=[r for r in tables['ratios'] if c.a.casekey(r)==case and r['clock']=='wall_ns' and r['repetition']==2][0]
        self.assertGreater(loss['paired_ratio'],1)
        summary=next(r for r in tables['ratio-summary'] if c.a.casekey(r)==case and r['clock']=='wall_ns')
        self.assertEqual(summary['numerator_losses'],1);self.assertEqual(summary['maximum_paired_ratio'],loss['paired_ratio'])
        bend=next(r for r in tables['bending'] if c.a.casekey(r)==case and r['clock']=='wall_ns' and r['series']=='depth')
        self.assertGreater(bend['maximum'],bend['median'])


if __name__=='__main__':unittest.main()
