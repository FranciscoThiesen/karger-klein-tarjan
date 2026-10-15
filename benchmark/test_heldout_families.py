#!/usr/bin/env python3
"""Synthetic held-out-family collector gates; no native solver launches.

All native launches and artifact fixtures are mocked. These tests use the
unchanged compressed helper tests to construct independent temporary parents.
"""
import argparse
import contextlib
import copy
import csv
from fractions import Fraction
import json
import math
from pathlib import Path
import statistics
import threading
import unittest
from unittest import mock

import run_heldout_families as heldout
import test_compressed_queries as paired_tests

control = heldout.control
old = paired_tests.old
SIZES = (1024,4096,16384,65536,262144,1048576)
PAIRS = (('leaf_distance4','leaf_shuffled4'),('grid2d_metric','grid2d_random'),('line_metric','line_random'))
ALGORITHMS = ('kkt','compacting_boruvka','multigraph_boruvka','kruskal','prim','boruvka')
# Independently spelled manifest order, not derived from collector constants.
EXPECTED = (
    ('leaf_distance4',1024,32,0),('leaf_shuffled4',1024,32,0),
    ('grid2d_metric',1024,32,0),('grid2d_random',1024,32,0),
    ('line_metric',1024,32,0),('line_random',1024,32,0),
    ('grid2d_metric',4096,32,0),('grid2d_random',4096,32,0),
    ('line_metric',4096,32,0),('line_random',4096,32,0),
    ('leaf_distance4',4096,32,0),('leaf_shuffled4',4096,32,0),
    ('line_metric',16384,32,0),('line_random',16384,32,0),
    ('leaf_distance4',16384,32,0),('leaf_shuffled4',16384,32,0),
    ('grid2d_metric',16384,32,0),('grid2d_random',16384,32,0),
    ('leaf_distance4',65536,32,0),('leaf_shuffled4',65536,32,0),
    ('grid2d_metric',65536,32,0),('grid2d_random',65536,32,0),
    ('line_metric',65536,32,0),('line_random',65536,32,0),
    ('grid2d_metric',262144,32,0),('grid2d_random',262144,32,0),
    ('line_metric',262144,32,0),('line_random',262144,32,0),
    ('leaf_distance4',262144,32,0),('leaf_shuffled4',262144,32,0),
    ('line_metric',1048576,32,0),('line_random',1048576,32,0),
    ('leaf_distance4',1048576,32,0),('leaf_shuffled4',1048576,32,0),
    ('grid2d_metric',1048576,32,0),('grid2d_random',1048576,32,0),
)


@contextlib.contextmanager
def fixture():
    with paired_tests.fixture() as (root,parent_args,_):
        manifest=root/'heldout-manifest.csv'
        with manifest.open('w',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(control.native.base.MANIFEST_FIELDS);writer.writerows(EXPECTED)
        protocol=root/'HELDOUT.md';protocol.write_text('Synthetic prospective held-out matrix.\n')
        args=argparse.Namespace(parent_freeze=parent_args.freeze,manifest=manifest,protocol=protocol,freeze=root/'heldout-freeze.json')
        with mock.patch.object(heldout,'PARENT_SHA256',control.native.sha(parent_args.freeze)):
            heldout.preflight(args)
            yield root,args,parent_args


class Factory(paired_tests.control_tests.Factory):
    def __call__(self,argv,**kwargs):
        assert argv[:2]==['/usr/bin/time','-l'] and kwargs['start_new_session'] is True
        rows=paired_tests.control_tests.rows_for(argv)
        fingerprints={family:(7+i,20+2*i+j) for i,pair in enumerate(PAIRS) for j,family in enumerate(pair)}
        for row in rows:row['topology_fingerprint'],row['input_fingerprint']=fingerprints[row['family']]
        certificate={name:rows[0][name] for name in control.native.CERTIFICATE_FIELDS}
        if getattr(self,'false_certificate',False):certificate['validation']='failed'
        if not getattr(self,'omit_certificate',False):
            kwargs['stderr'].write(control.native.CERTIFICATE_PREFIX+json.dumps(certificate)+'\n')
        if self.mutation:self.mutation(rows)
        writer=csv.DictWriter(kwargs['stdout'],fieldnames=getattr(self,'fields',control.FIELDS),extrasaction='ignore')
        writer.writeheader();writer.writerows(rows)
        process=old.FakeProcess(75000+len(self.children),self.status,self.finishes)
        self.children.append((argv,process));return process


def capture(root,args,factory=None,sampler=None,output='heldout.csv'):
    factory=factory or Factory()
    def provider(group):
        process=next(p for _,p in factory.children if p.pid==group)
        return {'process_group':group,'members':[]} if process.returncode is not None else old.provider(group)
    sampler=sampler or control.monitor.BoundedSampler(provider,.1)
    info=heldout.capture(argparse.Namespace(freeze=args.freeze,output=root/output,released=True),sampler=sampler,popen=factory)
    return info,factory


def prepared_rows():
    rows=[]
    for ci,(family,n,d,p) in enumerate(EXPECTED):
        for gi,graph in enumerate((9000011,9000049)):
            for rep in range(6):
                for ai,algorithm in enumerate(ALGORITHMS):
                    rows.append(dict(case_id=f'{family}_n{n}_d{d}_p{p}',family=family,n=n,m=n*d,density=d,
                        intrusion_per_mille=p,graph_seed=graph,kkt_seed=2003,phase='timed',repetition=rep,algorithm=algorithm,
                        elapsed_ns=1009+ci*31+gi*101+rep*43+ai*71+rep*ai*13,
                        process_cpu_elapsed_ns=1217+ci*47+gi*79+rep*29+ai*61+rep*ai*17))
    return rows


def declared_cases():
    return {f'{f}_n{n}_d{d}_p{p}':dict(family=f,n=n,density=d,intrusion_per_mille=p) for f,n,d,p in EXPECTED}


class HeldoutFamilyTests(unittest.TestCase):
    def test_scope_restoration_and_unscoped_full_parent_proof(self):
        before=control.GRAPH_SEEDS,control.SAMPLING_SEED
        with self.assertRaises(RuntimeError):
            with heldout.configured():
                self.assertEqual((control.GRAPH_SEEDS,control.SAMPLING_SEED),((9000011,9000049),2003))
                with heldout.configured():raise RuntimeError('synthetic')
        self.assertEqual((control.GRAPH_SEEDS,control.SAMPLING_SEED),before)
        with fixture() as (root,args,parent_args):
            actual=heldout.parent_engine.check_freeze
            def check(path):
                self.assertEqual((control.GRAPH_SEEDS,control.SAMPLING_SEED),before);return actual(path)
            with mock.patch.object(heldout.parent_engine,'check_freeze',side_effect=check) as proof:
                heldout.check_freeze(args.freeze);self.assertEqual(proof.call_count,1)
            with mock.patch.object(heldout.parent_engine,'check_freeze',side_effect=ValueError('synthetic parent')):
                with self.assertRaisesRegex(ValueError,'synthetic parent'):heldout.check_freeze(args.freeze)
            self.assertEqual((control.GRAPH_SEEDS,control.SAMPLING_SEED),before)

    def test_full_matrix_schedule_analysis_twins_and_power(self):
        with fixture() as (root,args,parent_args):
            info,factory=capture(root,args)
            self.assertEqual((len(factory.children),info['checked_rows'],info['checked_timed_rows'],info['checked_warmup_rows']),(72,3024,2592,432))
            cases=[f'{f}_n{n}_d{d}_p{p}' for f,n,d,p in EXPECTED]
            expected=[dict(case_id=c,graph_seed=g,kkt_seed=2003) for g,order in ((9000011,cases),(9000049,list(reversed(cases)))) for c in order]
            self.assertEqual([{k:item[k] for k in ('case_id','graph_seed','kkt_seed')} for item in info['captures']],expected)
            self.assertTrue(all(item['command'][0]==str(parent_args.compressed_binary) for item in info['captures']))
            loaded=heldout.load(root/'heldout.json');tables=heldout.aggregate(loaded[2])
            self.assertEqual({k:len(v) for k,v in tables.items()},{'paired_ratios':4320,'comparisons':360,'graph_comparisons':720,'summary':432,'graph_summary':864})
            self.assertTrue(all(r['trials']==12 for r in tables['comparisons']))
            self.assertTrue(all(r['trials']==6 for r in tables['graph_comparisons']))
            self.assertEqual({k:len(v) for k,v in heldout.crossovers(tables,loaded[1]).items()},{'crossover_points':180,'crossover_brackets':450,'crossover_summary':30})
            power=root/'power.log';power.write_text('2000-01-01 00:00:00 +0000 Sleep Entering Sleep state\n2000-01-01 00:00:00 +0000 Wake Requests request=Maintenance\n2000-01-01 00:00:01 +0000 Wake Wake from Deep Idle\n')
            heldout.analyze(argparse.Namespace(capture=root/'heldout.json',output_dir=root/'analysis',power_log=power))
            self.assertEqual(control.analysis.read_json(root/'analysis/provenance.json')['power_audit']['logged_overlap_calls'],3024)
            with self.assertRaisesRegex(ValueError,'overwrite'):capture(root,args)

    def test_parent_binary_build_objects_sources_helpers_and_manifest_bound(self):
        with fixture() as (root,args,parent_args):
            parent=control.analysis.read_json(parent_args.freeze);record=parent['variants']['compressed']['build']['record']
            self.assertEqual(heldout.DECLARED_CASES,EXPECTED)
            for path in (args.parent_freeze,args.protocol,args.manifest,parent_args.compressed_binary,parent_args.compressed_build_record,
                         root/'benchmark/retention_control.cpp',root/'verifier/verifier_v2.cpp',
                         Path(record['object_paths']['kkt/kkt.o']),Path(record['object_paths']['verifier/verifier_v2.o']),Path(record['main_object'])):
                before=path.read_bytes();factory=Factory()
                try:
                    path.write_bytes(before+b'drift')
                    with self.subTest(path=path),self.assertRaises(ValueError):capture(root,args,factory=factory)
                    self.assertFalse(factory.children)
                finally:path.write_bytes(before)
            helpers=heldout.helpers();changed=dict(helpers);changed[str(heldout.HERE)]='0'*64
            with mock.patch.object(heldout,'helpers',return_value=changed),self.assertRaises(ValueError):heldout.check_freeze(args.freeze)
            with self.assertRaisesRegex(ValueError,'released'):heldout.capture(argparse.Namespace(freeze=args.freeze,output=root/'unreleased.csv',released=False))
            frozen=control.analysis.read_json(args.freeze);frozen['binary']=str(parent_args.reference_binary);control.write_json(args.freeze,frozen)
            with self.assertRaisesRegex(ValueError,'inherited'):heldout.check_freeze(args.freeze)
            for name,values in (('reordered',list(reversed(EXPECTED))),('missing',EXPECTED[:-1]),
                                ('duplicate',EXPECTED[:-1]+(EXPECTED[0],)),('unknown',(('leaf_hierarchy4',1024,32,0),)+EXPECTED[1:])):
                path=root/(name+'.csv')
                with path.open('w',newline='') as stream:
                    writer=csv.writer(stream);writer.writerow(control.native.base.MANIFEST_FIELDS);writer.writerows(values)
                with self.subTest(name=name),self.assertRaises(ValueError):heldout.cases_from_manifest(path)

    def test_bad_metadata_raw_certificate_and_combined_concat_rejected(self):
        with fixture() as (root,args,parent_args):
            good,_=capture(root,args)
            for mutation in (lambda x:x['captures'].pop(),lambda x:x['captures'][0].update(graph_seed=8000009),
                             lambda x:x.update(checked_rows=1008),lambda x:x['captures'][0].update(exit_status=None),
                             lambda x:x['captures'][0].update(group_exit_verification={}),
                             lambda x:x['captures'][0]['certificate'].update(m=1),lambda x:x.update(rows_removed=1)):
                changed=copy.deepcopy(good);mutation(changed);control.write_json(root/'heldout.json',changed)
                with self.assertRaises((ValueError,KeyError)):heldout.load(root/'heldout.json')
            raw=Path(good['captures'][0]['csv']);original=raw.read_bytes()
            raw.write_text(raw.read_text().replace(',2003,',',1801,'))
            changed=copy.deepcopy(good);changed['captures'][0]['output_sha256']=control.native.sha(raw);control.write_json(root/'heldout.json',changed)
            with self.assertRaises(ValueError):heldout.load(root/'heldout.json')
            raw.write_bytes(original)
            combined=root/'heldout.csv';rows=[r for _,r in control.native.base.read_csv(combined,control.FIELDS)]
            rows[0]['elapsed_ns']=str(int(rows[0]['elapsed_ns'])+1);control.analysis.write_csv(combined,rows)
            changed=copy.deepcopy(good);changed['output_sha256']=control.native.sha(combined);control.write_json(root/'heldout.json',changed)
            with self.assertRaisesRegex(ValueError,'concatenation'):heldout.load(root/'heldout.json')

    def test_all_three_twins_topology_and_nonvacuous_weights(self):
        rows=[]
        for graph in (9000011,9000049):
            for family,n,d,p in EXPECTED:
                i,j=next((i,j) for i,pair in enumerate(PAIRS) for j,f in enumerate(pair) if f==family)
                rows.append(dict(case_id=f'{family}_n{n}_d{d}_p{p}',family=family,n=n,density=d,graph_seed=graph,
                                 input_fingerprint=20+2*i+j,topology_fingerprint=7+i))
        heldout.check_fingerprints(rows,complete=True)
        for pair in PAIRS:
            index=next(i for i,r in enumerate(rows) if r['family']==pair[1])
            bad=copy.deepcopy(rows);bad[index]['topology_fingerprint']+=100
            with self.subTest(pair=pair),self.assertRaisesRegex(ValueError,'different topology'):heldout.check_fingerprints(bad,complete=True)
            bad=copy.deepcopy(rows);bad[index]['input_fingerprint']-=1
            with self.subTest(pair=pair),self.assertRaisesRegex(ValueError,'identical weighted'):heldout.check_fingerprints(bad,complete=True)
        with self.assertRaisesRegex(ValueError,'incomplete'):heldout.check_fingerprints(rows[:-1],complete=True)

    def test_native_row_and_certificate_failure_stops_after_one_child(self):
        mutations=(('missing timed',lambda rows:rows.pop()),('missing warmup',lambda rows:rows.pop(0)),
                   ('duplicate',lambda rows:rows.__setitem__(-1,dict(rows[-2]))),
                   ('reordered',lambda rows:rows.reverse()),
                   ('wrong solver',lambda rows:rows[-1].update(algorithm='kkt')),
                   ('invalid clock',lambda rows:rows[-1].update(process_cpu_end_ns=0)),
                   ('invalid validation',lambda rows:rows[-1].update(validation='failed')),
                   ('missing column',None),('absent certificate',None),('false certificate',None))
        for name,mutation in mutations:
            with self.subTest(name=name),fixture() as (root,args,parent_args):
                factory=Factory(mutation=mutation)
                if name=='missing column':factory.fields=[f for f in control.FIELDS if f!='validation']
                if name=='absent certificate':factory.omit_certificate=True
                if name=='false certificate':factory.false_certificate=True
                with self.assertRaises(ValueError):capture(root,args,factory=factory)
                self.assertEqual(len(factory.children),1)
                failed=control.analysis.read_json(root/'heldout.json')
                self.assertEqual(failed['validation'],'failed');self.assertEqual(len(failed['captures']),1)
                self.assertIn('error',failed);self.assertFalse(failed['native_process_may_still_be_running'])
                verified=failed['captures'][0]['group_exit_verification']
                self.assertEqual((verified['validation'],verified['members']),('pass',[]))
                self.assertTrue(Path(failed['captures'][0]['csv']).exists())
                self.assertTrue(Path(failed['captures'][0]['log']).exists())
        # Hashes and combined concatenation are updated consistently. Rejection
        # must come from the raw 42-call schema, not an earlier stale-hash gate.
        with fixture() as (root,args,parent_args):
            good,_=capture(root,args);item=good['captures'][0];raw=Path(item['csv'])
            rows=[r for _,r in control.native.base.read_csv(raw,control.FIELDS)];rows.pop()
            control.analysis.write_csv(raw,rows);item['output_sha256']=control.native.sha(raw)
            combined=root/'heldout.csv';rows=[r for _,r in control.native.base.read_csv(combined,control.FIELDS)];rows.pop(41)
            control.analysis.write_csv(combined,rows);good['output_sha256']=control.native.sha(combined)
            control.write_json(root/'heldout.json',good)
            with self.assertRaisesRegex(ValueError,'incomplete six-solver matrix'):heldout.load(root/'heldout.json')

    def test_independent_fraction_pairs_and_all_summary_medians(self):
        rows=prepared_rows();tables=heldout.aggregate(rows)
        raw={(r['case_id'],r['graph_seed'],r['repetition'],r['algorithm']):r for r in rows}
        pairs={};groups={name:{} for name in ('comparisons','graph_comparisons','summary','graph_summary')}
        for family,n,d,p in EXPECTED:
            case=f'{family}_n{n}_d{d}_p{p}'
            for graph in (9000011,9000049):
                for rep in range(6):
                    for metric,field in (('wall','elapsed_ns'),('cpu','process_cpu_elapsed_ns')):
                        for algorithm in ALGORITHMS:
                            duration=raw[(case,graph,rep,algorithm)][field]
                            groups['summary'].setdefault((case,metric,algorithm),[]).append(duration)
                            groups['graph_summary'].setdefault((case,graph,metric,algorithm),[]).append(duration)
                            if algorithm=='kkt':continue
                            numerator=raw[(case,graph,rep,'kkt')][field];value=Fraction(numerator,duration)
                            pairs[(case,graph,rep,metric,algorithm)]=(numerator,duration,value)
                            groups['comparisons'].setdefault((case,metric,algorithm),[]).append(value)
                            groups['graph_comparisons'].setdefault((case,graph,metric,algorithm),[]).append(value)
        actual={tuple(r[k] for k in ('case_id','graph_seed','repetition','metric','competitor')):r for r in tables['paired_ratios']}
        self.assertEqual(len(actual),len(tables['paired_ratios']));self.assertEqual(set(actual),set(pairs));self.assertEqual(len(actual),4320)
        def close(actual,expected):
            expected=float(expected);self.assertLessEqual(abs(actual-expected),2*math.ulp(expected))
        for key,(num,den,value) in pairs.items():
            self.assertEqual((actual[key]['kkt_ns'],actual[key]['competitor_ns'],actual[key]['kkt_seed']),(num,den,2003))
            close(actual[key]['kkt_over_competitor'],value)
        for name,expected in groups.items():
            ratio='comparisons' in name;identity=('case_id',)+(('graph_seed',) if name.startswith('graph_') else ())+('metric','competitor' if ratio else 'algorithm')
            actual={tuple(r[k] for k in identity):r for r in tables[name]}
            self.assertEqual(len(actual),len(tables[name]));self.assertEqual(set(actual),set(expected))
            for key,values in expected.items():
                close(actual[key]['median_paired_ratio' if ratio else 'median_ns'],statistics.median(values))
                close(actual[key]['trial_min'],min(values));close(actual[key]['trial_max'],max(values))
                self.assertEqual(actual[key]['trials'],len(values))

    def test_exact_crossover_thresholds_reversals_all_pairs_and_missing_trials(self):
        base=heldout.aggregate(prepared_rows());target=('leaf_distance4','multigraph_boruvka')
        def evaluate(values,change=None):
            tables=copy.deepcopy(base)
            for row in tables['paired_ratios']:
                if (row['family'],row['competitor'])==target:
                    value=values[SIZES.index(row['n'])]
                    if change:value=change(row,value)
                    row['kkt_ns'],row['competitor_ns']=value.numerator,value.denominator
            result=heldout.crossovers(tables,declared_cases())
            summary=next(r for r in result['crossover_summary'] if (r['family'],r['competitor'])==target)
            brackets=[r for r in result['crossover_brackets'] if (r['family'],r['competitor'])==target]
            self.assertEqual(len(result['crossover_points']),180);self.assertEqual(len(brackets),15);self.assertEqual(len(result['crossover_brackets']),450)
            return summary,brackets
        loss,strong,tie=Fraction(11,10),Fraction(9,10),Fraction(1)
        summary,_=evaluate([loss,loss,strong,strong,strong,strong])
        self.assertEqual((summary['strong_crossover'],summary['primary_lower_n'],summary['primary_upper_n'],summary['qualifying_brackets']),(True,4096,16384,8))
        summary,brackets=evaluate([loss,strong,loss,strong,strong,strong])
        self.assertEqual((summary['primary_lower_n'],summary['primary_upper_n']),(16384,65536))
        self.assertFalse(next(r for r in brackets if r['lower_n']==1024 and r['upper_n']==4096)['strong_crossover'])
        summary,_=evaluate([tie,strong,strong,strong,strong,strong]);self.assertFalse(summary['strong_crossover'])
        summary,_=evaluate([strong]*6);self.assertTrue(summary['strong_lead_at_every_measured_size']);self.assertFalse(summary['strong_crossover'])
        summary,_=evaluate([loss]*6);self.assertTrue(summary['loss_at_every_measured_size']);self.assertFalse(summary['strong_crossover'])
        for change in (lambda r,v:Fraction(900_000_000_000_000_001,10**18) if r['metric']=='cpu' and r['n']==1048576 else v,
                       lambda r,v:Fraction(91,100) if r['graph_seed']==9000049 and r['n']==1048576 else v):
            summary,_=evaluate([loss,strong,strong,strong,strong,strong],change);self.assertFalse(summary['strong_crossover'])
        bad=copy.deepcopy(base);bad['paired_ratios'].pop()
        with self.assertRaisesRegex(ValueError,'incomplete'):heldout.crossovers(bad,declared_cases())
        bad=copy.deepcopy(base);bad['paired_ratios'].append(bad['paired_ratios'][0])
        with self.assertRaisesRegex(ValueError,'duplicate'):heldout.crossovers(bad,declared_cases())

    def test_clock_flags_monitor_failures_and_poison(self):
        with fixture() as (root,args,parent_args):
            info,_=capture(root,args,factory=Factory(mutation=lambda rows:rows[0].update(elapsed_ns=2_000_000_000)))
            self.assertEqual(info['flagged_calls'],72);self.assertEqual(len(heldout.load(root/'heldout.json')[2]),3024)
        for failure in ('ceiling','unavailable','nonempty exit','unavailable exit','crash'):
            with self.subTest(failure=failure),fixture() as (root,args,parent_args):
                factory=Factory(status=-11 if failure=='crash' else 0,finishes=failure!='unavailable')
                def provider(group):
                    exited=factory.children[-1][1].returncode is not None
                    if failure=='unavailable' or (failure=='unavailable exit' and exited):raise OSError('synthetic')
                    result=old.provider(group)
                    if failure=='ceiling':result['members'][0]['rss_kib']=control.RULE['rss_limit_kib']+1
                    return result
                with mock.patch.object(control.monitor,'bounded_terminate',return_value={'native_process_may_still_be_running':True}),self.assertRaises(ValueError):
                    capture(root,args,factory=factory,sampler=control.monitor.BoundedSampler(provider,.1))
                self.assertEqual(len(factory.children),1)
        with fixture() as (root,args,parent_args):
            gate=threading.Event();factory=Factory();sampler=control.monitor.BoundedSampler(lambda group:(gate.wait(),old.provider(group))[1],.01)
            try:
                with mock.patch.object(control.monitor,'bounded_terminate',return_value={'native_process_may_still_be_running':True}),self.assertRaisesRegex(ValueError,'timed out'):
                    capture(root,args,factory=factory,sampler=sampler)
                second=Factory()
                with self.assertRaisesRegex(ValueError,'forbids launching'):capture(root,args,factory=second,sampler=sampler,output='second.csv')
                self.assertEqual((len(factory.children),len(second.children),sampler.workers_started),(1,0,1))
            finally:gate.set()


if __name__=='__main__':unittest.main(verbosity=2)
