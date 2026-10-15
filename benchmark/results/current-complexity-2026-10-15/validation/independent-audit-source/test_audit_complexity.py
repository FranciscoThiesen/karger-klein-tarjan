#!/usr/bin/env python3
"""Synthetic gates for the independent arithmetic audit; no native execution."""
import copy
import csv
from fractions import Fraction
import importlib.util
import io
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('independent_complexity_tested',HERE/'audit_complexity.py')
audit=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(audit)


def csv_text(rows,fields):
    stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=fields)
    writer.writeheader();writer.writerows(rows);return stream.getvalue()


def literal_specs():
    # Independent declaration: literal curve order, with two algorithms swapped
    # at graph/sampler parity, and graph2 visiting sizes in reverse.
    return [dict(family=family,algorithm=algorithm,graph_seed=graph,sampling_seed=sampler,size_order=order)
            for family in ('leaf_hierarchy4','leaf_shuffled4','gnm_random')
            for graph,order in ((19000013,'ascending'),(19000043,'descending'))
            for sampler,algorithms in ((3001,('kkt','multigraph_boruvka') if graph==19000013 else ('multigraph_boruvka','kkt')),
                                       (3011,('multigraph_boruvka','kkt') if graph==19000013 else ('kkt','multigraph_boruvka')))
            for algorithm in algorithms]


def curve_fixture(spec):
    sizes=[2**power for power in range(10,21)]
    if spec['size_order']=='descending':sizes.reverse()
    family_index=('leaf_hierarchy4','leaf_shuffled4','gnm_random').index(spec['family'])
    offset=11*family_index+7*(spec['graph_seed']==19000043)+3*(spec['sampling_seed']==3011)+(spec['algorithm']=='kkt')
    cpu_coefficient=3+offset
    rows=[];reports=[];manual_points=[];cursor=100000000000000000
    stem=f"{spec['algorithm']}/{spec['family']}/graph_{spec['graph_seed']}/sampler_{spec['sampling_seed']}"
    suffix='/iterations:2/repeats:3/process_time/manual_time'
    for n in sizes:
        m=n*(16 if spec['family']=='gnm_random' else 32);N=n+m
        topology=10000000+spec['graph_seed']+n+(100000000 if family_index==2 else 0)
        weighted=topology+1000*(family_index+1)
        run=f'{stem}/{n}{suffix}'
        for repetition in range(3):
            elapsed=[]
            for phase,iteration in (('warmup',0),('timed',0),('timed',1)):
                wall=5*N+offset+2*repetition+iteration+10
                cpu=7*N+2*offset+3*repetition+2*iteration+9
                rows.append(dict(spec,n=n,m=m,N=N,input_fingerprint=weighted,topology_fingerprint=topology,
                    invocation=repetition,phase=phase,iteration=iteration,elapsed_ns=wall,
                    utc_start_ns=cursor,utc_end_ns=cursor+wall,process_cpu_start_ns=cursor,
                    process_cpu_end_ns=cursor+cpu,process_cpu_elapsed_ns=cpu,validation='pass'))
                cursor+=max(wall,cpu)+100
                if phase=='timed':elapsed.append(wall)
            manual=Fraction(sum(elapsed),2);manual_points.append((N,manual))
            reports.append(dict(name=run,run_name=run,run_type='iteration',repetitions=3,threads=1,
                repetition_index=repetition,iterations=2,real_time=float(manual)/1000000,
                cpu_time=cpu_coefficient*N*N/1000000,time_unit='ms',vertices=n,edges=m,
                graph_seed=spec['graph_seed'],sampling_seed=spec['sampling_seed']))
        for kind in ('mean','median','stddev'):
            reports.append(dict(name=run+'_'+kind,run_name=run,run_type='aggregate',repetitions=3,threads=1,
                aggregate_name=kind,iterations=3,real_time=0,cpu_time=0,time_unit='ms',
                vertices=0 if kind=='stddev' else n,edges=0 if kind=='stddev' else m,
                graph_seed=0 if kind=='stddev' else spec['graph_seed'],sampling_seed=0 if kind=='stddev' else spec['sampling_seed']))
    # Independent rational zero-intercept projection of manual linear-ish
    # durations onto the deliberately quadratic library CPU model.
    coefficient=sum(time*N*N for N,time in manual_points)/sum(N**4 for N,_ in manual_points)
    run=stem+suffix
    reports.append(dict(name=run+'_BigO',run_name=run,run_type='aggregate',repetitions=3,threads=1,
        aggregate_name='BigO',cpu_coefficient=cpu_coefficient,real_coefficient=float(coefficient),big_o='N^2',time_unit='ns'))
    reports.append(dict(name=run+'_RMS',run_name=run,run_type='aggregate',repetitions=3,threads=1,
        aggregate_name='RMS',rms=0.0))
    document=dict(context=dict(date='synthetic',host_name='synthetic',num_cpus=1,mhz_per_cpu=1.0,
        caches=[],load_avg=[],library_build_type='release'),benchmarks=reports)
    return dict(spec=spec,raw=csv_text(rows,audit.NATIVE_FIELDS),document=document)


class ArithmeticAuditTests(unittest.TestCase):
    def test_closed_form_models_and_independent_fraction_projection(self):
        for model in ('(1)','lgN','N','NlgN','N^2','N^3'):
            points=[(n,7*audit.basis(model,n)) for n in (2,4,8,16,32)]
            fit=audit.independent_fit(points,model)
            self.assertTrue(math.isclose(fit['coefficient_ns'],7,rel_tol=2e-15))
            self.assertLess(fit['normalized_rms'],2e-15)
            self.assertEqual(audit.selected_model(points),model)
        points=[(2,11),(3,14),(7,32),(11,51)]
        expected=Fraction(sum(n*t for n,t in points),sum(n*n for n,_ in points))
        rms_squared=sum((Fraction(t)-expected*n)**2 for n,t in points)/len(points)/(Fraction(sum(t for _,t in points),len(points))**2)
        fit=audit.independent_fit(points,'N')
        self.assertTrue(math.isclose(fit['coefficient_ns'],float(expected),rel_tol=2e-15))
        self.assertTrue(math.isclose(fit['normalized_rms'],math.sqrt(float(rms_squared)),rel_tol=2e-14))
        with self.assertRaisesRegex(ValueError,'fit time'):audit.independent_fit([(2,1),(4,0)],'N')

    def test_literal_complete_matrix_and_all_clock_model_identities(self):
        specs=literal_specs();self.assertEqual(len(specs),24);self.assertEqual(audit.schedule(),specs)
        curves=[curve_fixture(spec) for spec in specs];tables=audit.reconstruct(curves)
        self.assertEqual({key:len(value) for key,value in tables.items()},dict(means=3168,model_fits=1152,google_selection=24))
        expected={(tuple(spec.values()),clock,n,repetition) for spec in specs
                  for clock in ('native_steady','native_process_cpu','library_manual','library_process_cpu')
                  for n in (1024,2048,4096,8192,16384,32768,65536,131072,262144,524288,1048576) for repetition in range(3)}
        found={(tuple(row[key] for key in audit.SPEC),row['clock'],row['n'],row['invocation']) for row in tables['means']}
        self.assertEqual(found,expected)
        for row in tables['model_fits']:
            self.assertEqual((row['observations'],row['sizes']),(33,11) if row['window']=='full11' else (18,6))
        for row in tables['google_selection']:
            self.assertEqual(row['selected_model'],'N^2');self.assertIs(row['manual_rms_exported'],False)
            self.assertGreater(row['manual_reconstructed_normalized_rms'],.1)
        for name,rows in tables.items():audit.compare_csv(csv_text(rows,audit.HEADERS[name]),rows,name)
        with self.assertRaisesRegex(ValueError,'fixed24'):audit.reconstruct(curves[:-1])
        changed=copy.deepcopy(curves);changed[-1]=copy.deepcopy(changed[-2])
        with self.assertRaisesRegex(ValueError,'fixed24'):audit.reconstruct(changed)

    def test_raw_and_google_schema_policy_and_mean_join_negatives(self):
        spec=literal_specs()[0];curve=curve_fixture(spec);native=audit.native_rows(curve['raw'],spec)
        audit.library_means(curve['document'],spec,native)
        for mutation,message in (
            (lambda reports:reports[0].update(name='wrong'),'library identity'),
            (lambda reports:reports[0].update(time_unit='ns'),'per-report unit'),
            (lambda reports:reports[0].update(real_time=reports[0]['real_time']+1),'manual mean'),
            (lambda reports:reports[-2].update(big_o='N'),'CPU model'),
            (lambda reports:reports[-2].update(time_unit='ms'),'per-report unit'),
            (lambda reports:reports[-1].update(real_rms=0),'library fields'),
            (lambda reports:reports[-1].update(rms=.02),'CPU RMS'),
            (lambda reports:reports[0].update(iterations=True),'iteration count')):
            broken=copy.deepcopy(curve['document']);mutation(broken['benchmarks'])
            with self.subTest(message=message),self.assertRaisesRegex(ValueError,message):audit.library_means(broken,spec,native)
        rows=list(csv.DictReader(io.StringIO(curve['raw'])));rows[2]['phase']='warmup'
        with self.assertRaisesRegex(ValueError,'identity'):audit.native_rows(csv_text(rows,audit.NATIVE_FIELDS),spec)
        for value in ('{"a":1,"a":2}','{"a":NaN}','{"a":[1e999]}'):
            with self.assertRaises(ValueError):audit.parse_json(value)

    def test_canonical_same_identity_numeric_and_identity_mutations(self):
        tables=audit.reconstruct([curve_fixture(spec) for spec in literal_specs()])
        for name,key in (('means','mean_ns'),('model_fits','coefficient_ns'),('model_fits','normalized_rms'),
                         ('google_selection','manual_coefficient_ns'),('google_selection','cpu_normalized_rms')):
            changed=copy.deepcopy(tables[name]);changed[0][key]=changed[0][key]*1.01+.0001
            with self.subTest(name=name,key=key),self.assertRaisesRegex(ValueError,'mismatch'):
                audit.compare_csv(csv_text(changed,audit.HEADERS[name]),tables[name],name)
        for key,value in (('clock','native_process_cpu'),('invocation',2),('exact_denominator',3)):
            changed=copy.deepcopy(tables['means']);changed[0][key]=value
            with self.assertRaisesRegex(ValueError,'exact canonical'):
                audit.compare_csv(csv_text(changed,audit.HEADERS['means']),tables['means'],'means')
        rows=copy.deepcopy(tables['model_fits']);rows[0]['selected_for_this_clock']=not rows[0]['selected_for_this_clock']
        with self.assertRaisesRegex(ValueError,'exact canonical'):audit.compare_csv(csv_text(rows,audit.HEADERS['model_fits']),tables['model_fits'],'model_fits')
        rows=copy.deepcopy(tables['means']);rows[1]=copy.deepcopy(rows[0])
        with self.assertRaises(ValueError):audit.compare_csv(csv_text(rows,audit.HEADERS['means']),tables['means'],'means')
        with self.assertRaisesRegex(ValueError,'row count'):audit.compare_csv(csv_text(rows[:-1],audit.HEADERS['means']),tables['means'],'means')

    def test_hash_conflicts_and_mutation_between_read_and_final_proof(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=(Path(temporary)/'raw.json').resolve();path.write_text('original');expected=audit.digest(path);bound={}
            self.assertEqual(audit.read_bound(bound,path,expected),'original')
            with self.assertRaisesRegex(ValueError,'conflicting'):audit.bind(bound,path,'0'*64)
            path.write_text('changed')
            with self.assertRaisesRegex(ValueError,'artifact changed'):audit.recheck(bound)
            path.write_text('original');original=Path.read_text
            def mutate(source,*args,**kwargs):
                text=original(source,*args,**kwargs)
                if source==path:source.write_text('changed during read')
                return text
            with mock.patch.object(Path,'read_text',mutate),self.assertRaisesRegex(ValueError,'artifact changed'):
                audit.read_bound({},path,expected)

    def test_separate_deep_package_sibling_import_and_path_restoration(self):
        previous=list(sys.path);old_module=sys.modules.get('complexity_audit_checked_collector')
        with tempfile.TemporaryDirectory() as temporary:
            package=Path(temporary)/'deep'/'package';package.mkdir(parents=True)
            (package/'independent_audit_fixture_sibling.py').write_text('value = 79\n')
            collector=package/'collect.py'
            collector.write_text('import independent_audit_fixture_sibling\n'
                'def load(path):\n    return independent_audit_fixture_sibling.value, str(path), {}\n')
            try:
                self.assertEqual(audit.provenance_load(collector,Path('capture')), (79,'capture',{}))
                self.assertEqual(sys.path,previous)
                self.assertIs(sys.modules.get('complexity_audit_checked_collector'),old_module)
                collector.write_text('import sys\n'
                    'def load(path):\n    sys.path.append("fixture-must-not-leak")\n    raise ValueError("fixture failure")\n')
                with self.assertRaisesRegex(ValueError,'fixture failure'):audit.provenance_load(collector,Path('capture'))
                self.assertEqual(sys.path,previous)
                self.assertIs(sys.modules.get('complexity_audit_checked_collector'),old_module)
                collector.write_text('raise ValueError("fixture import failure")\n')
                with self.assertRaisesRegex(ValueError,'fixture import failure'):audit.provenance_load(collector,Path('capture'))
                self.assertEqual(sys.path,previous)
            finally:sys.modules.pop('independent_audit_fixture_sibling',None)


if __name__=='__main__':unittest.main()
