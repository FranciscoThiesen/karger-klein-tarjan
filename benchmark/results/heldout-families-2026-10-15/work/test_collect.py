#!/usr/bin/env python3
"""Mocked held-out diagnostic capture gates. Never launches a native solver."""
import argparse
import contextlib
import copy
import csv
import importlib.util
import json
from pathlib import Path
import signal
import sys
import tempfile
import threading
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[3]
sys.path.insert(0,str(ROOT/'benchmark'))
spec = importlib.util.spec_from_file_location('heldout_work_under_test',HERE/'collect.py')
work = importlib.util.module_from_spec(spec); spec.loader.exec_module(work)
prior_spec = importlib.util.spec_from_file_location('heldout_prior_work_test_helpers',work.PREVIOUS_PATH.parent/'test_collect.py')
prior_tests = importlib.util.module_from_spec(prior_spec); prior_spec.loader.exec_module(prior_tests)
old = prior_tests.old
GRAPHS,SAMPLER = (9000011,9000049),2003
FAMILY_PAIRS = (('leaf_distance4','leaf_shuffled4'),('grid2d_metric','grid2d_random'),('line_metric','line_random'))


def inputs():
    cases = {}
    for size_index,n in enumerate((1024,4096,16384,65536,262144,1048576)):
        pair_order = ((0,1,2),(1,2,0),(2,0,1),(0,1,2),(1,2,0),(2,0,1))[size_index]
        for pair_index in pair_order:
            for family in FAMILY_PAIRS[pair_index]:
                case = f'{family}_n{n}_d32_p0'
                cases[case] = dict(case_id=case,family=family,n=n,density=32,intrusion_per_mille=0,m=32*n)
    schedule = []
    for gi,g in enumerate(GRAPHS):
        for case in (list(cases) if gi == 0 else list(reversed(cases))):
            row = cases[case]; pi,fi = next((pi,fi) for pi,pair in enumerate(FAMILY_PAIRS) for fi,f in enumerate(pair) if f == row['family'])
            topology = 100000+row['n']+100*pi+gi
            schedule.append(dict(variant='compressed',**row,graph_seed=g,kkt_seed=SAMPLER,
                                 topology_fingerprint=topology,input_fingerprint=2*topology+fi))
    return cases,schedule


@contextlib.contextmanager
def fixture():
    with tempfile.TemporaryDirectory(prefix='heldout-work-mock-') as directory:
        root = Path(directory); _,schedule = inputs(); bound = root/'bound.txt'; bound.write_text('synthetic bound source')
        frozen = dict(schedule=schedule,artifact={'binary':'/never-executed/compressed'},bound_sha256={str(bound):work.native.sha(bound)})
        freeze = root/'freeze.json'; work.write_json(freeze,frozen)
        with mock.patch.object(work,'check_freeze',return_value=frozen): yield root,freeze,frozen


def capture(root,freeze,frozen,factory=None,sampler=None,name='capture.json'):
    factory = factory if factory is not None else prior_tests.Factory(frozen['schedule'])
    def provider(group):
        process = next(p for p in factory.children if p.pid == group)
        return {'process_group':group,'members':[]} if process.returncode is not None else old.provider(group)
    sampler = sampler if sampler is not None else work.monitor.BoundedSampler(provider,.1)
    work.capture(argparse.Namespace(freeze=freeze,output=root/name,released=True),sampler=sampler,popen=factory)
    return factory


class HeldoutWorkTests(unittest.TestCase):
    def test_complete_72_inputs_all_counters_chains_and_query_summaries(self):
        with fixture() as (root,freeze,frozen):
            cases,schedule = inputs()
            self.assertEqual(len(cases),36); self.assertEqual(len(schedule),72)
            self.assertEqual([s['case_id'] for s in schedule[36:]],list(reversed([s['case_id'] for s in schedule[:36]])))
            factory = capture(root,freeze,frozen); info,values = work.load(root/'capture.json')
            self.assertEqual((len(factory.children),len(values),info['checked_solver_outputs'],info['checked_replay_chains']),(72,72,216,144))
            self.assertEqual([spec for spec,value in values],schedule)
            work.summarize(argparse.Namespace(capture=root/'capture.json',output_dir=root/'analysis'))
            tables = {}
            for name in ('work','rounds','round_chains','query_work'):
                with (root/'analysis'/f'{name}.csv').open(newline='') as stream: tables[name] = list(csv.DictReader(stream))
            self.assertEqual({name:len(rows) for name,rows in tables.items()},dict(work=216,rounds=432,round_chains=144,query_work=72))
            indexed = {(r['case_id'],int(r['graph_seed']),r['algorithm']):r for r in tables['work']}
            self.assertEqual(set(indexed),{(c,g,a) for c in cases for g in GRAPHS for a in ('kkt','compacting_boruvka','multigraph_boruvka')})
            for spec in schedule:
                expected = prior_tests.output_for(spec,'compressed')
                for name,record in expected['algorithms'].items():
                    row = indexed[spec['case_id'],spec['graph_seed'],name]
                    self.assertEqual(row['hash_insert_items_status'],record['hash_insert_items_status'])
                    for field,value in record['work'].items(): self.assertEqual(row[field],'' if value is None else str(value))
            self.assertEqual(sum(row['hash_insert_items'] == '' for row in tables['work']),144)
            for row in tables['query_work']:
                n,m = int(row['n']),int(row['m'])
                self.assertEqual(tuple(int(row[k]) for k in ('Q','U','M','T','Nsum')),(m//2,n//4,m//4,2,n))
                self.assertEqual(float(row['U_over_Q']),(n//4)/(m//2))
            for row in tables['round_chains']:
                self.assertEqual((int(row['round_count']),int(row['selected_edges'])),(3,int(row['n'])-1))
            provenance = work.analysis.read_json(root/'analysis/provenance.json')
            self.assertEqual((provenance['counter_cells'],provenance['unmeasured_hash_counter_cells']),(14040,144))
            self.assertFalse(provenance['performance_claim']); self.assertFalse(provenance['memory_peak_claim'])
            self.assertEqual(provenance['reference_compression_pairs'],0)
            with self.assertRaisesRegex(ValueError,'overwrite'): capture(root,freeze,frozen)

    def test_real_original_artifact_proof_with_mocked_completed_timing_join(self):
        # No active/partial timing file is read. Only the already frozen timing
        # declaration and completed original compressed proof are real inputs.
        cases,schedule = inputs(); heldout_freeze = HERE.parent/'freeze.json'
        frozen = work.analysis.read_json(heldout_freeze)
        rows = [{key:s[key] for key in ('case_id','graph_seed','kkt_seed','input_fingerprint','topology_fingerprint')}
                for s in schedule for _ in range(42)]
        info = {'freeze':str(heldout_freeze),'frozen_protocol':frozen}
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)/'synthetic-timing.json'; source.write_text('synthetic completed timing join')
            result = (info,cases,rows,[],[],{str(source):work.native.sha(source)})
            with mock.patch.object(work.timing,'load',return_value=result):
                artifact,actual,paths = work.provenance(source)
                self.assertEqual(actual,schedule); self.assertIn('/compressed/retention_work',artifact['binary'])
                self.assertEqual(paths[str(work.PARENT_WORK_FREEZE)],work.PARENT_WORK_FREEZE_SHA256)
                self.assertEqual(len(work.FIELDS),65)
                with mock.patch.object(work.previous,'check_freeze',side_effect=ValueError('original artifact drift')):
                    with self.assertRaisesRegex(ValueError,'original artifact'): work.provenance(source)
            for changed in (rows[:-1],[{**rows[0],'input_fingerprint':-1},*rows[1:]]):
                with mock.patch.object(work.timing,'load',return_value=(info,cases,changed,[],[],{})),self.assertRaises(ValueError):
                    work.provenance(source)
            changed = copy.deepcopy(info); changed['frozen_protocol']['build']['record']['sdk'] = 'foreign-sdk'
            with mock.patch.object(work.timing,'load',return_value=(changed,cases,rows,[],[],{})),self.assertRaisesRegex(ValueError,'toolchain|production'):
                work.provenance(source)

    def test_full_instrumented_recipe_rejects_macro_object_main_and_extra_commands(self):
        path = ROOT/'benchmark/results/compressed-query-2026-10-15/validation/native-correctness-compressed-build-record.json'
        record = work.analysis.read_json(path); work.previous.check_instrumented_recipe(record,ROOT)
        for mode in ('macro','object','main','role','extra'):
            changed = copy.deepcopy(record)
            if mode == 'macro': changed['build_commands'][8].remove('-DKKT_EXPERIMENT_COMPRESSED_QUERIES')
            elif mode == 'object': changed['object_paths']['kkt/kkt.o'] = 'foreign'
            elif mode == 'main': changed['executables'][-1]['main_object'] = 'foreign'
            elif mode == 'role': changed['executables'][-1]['role'] = 'correctness'
            else: changed['build_commands'].append(['unexpected'])
            with self.subTest(mode=mode),self.assertRaises(ValueError): work.previous.check_instrumented_recipe(changed,ROOT)

    def test_schema_counter_fingerprint_certificate_and_raw_json_fail_closed(self):
        mutations = (lambda x:x.update(schema='wrong'),lambda x:x['algorithms']['kkt']['work'].pop('sampled_edges'),
            lambda x:x['algorithms']['kkt']['work'].update(sampled_edges=True),lambda x:x.update(input_fingerprint=999),
            lambda x:x.update(certified_output_items=1),lambda x:x['algorithms']['compacting_boruvka']['work'].update(hash_insert_items=0))
        for mutation in mutations:
            with fixture() as (root,freeze,frozen):
                factory = prior_tests.Factory(frozen['schedule'],mutation=mutation)
                with self.assertRaises(ValueError): capture(root,freeze,frozen,factory)
                self.assertEqual(len(factory.children),1)
                failed = work.analysis.read_json(root/'capture.json'); self.assertEqual(failed['validation'],'failed')
                self.assertFalse(failed['native_process_may_still_be_running'])
        for transform in (lambda raw:raw[:-1],lambda raw:raw[:-1]+',"validation":"pass"}',lambda raw:raw[:-1]+',"bad":NaN}'):
            with fixture() as (root,freeze,frozen):
                factory = prior_tests.Factory(frozen['schedule'],raw_transform=transform)
                with self.assertRaises(ValueError): capture(root,freeze,frozen,factory)
                self.assertEqual(len(factory.children),1)
        with fixture() as (root,freeze,frozen):
            factory = prior_tests.Factory(frozen['schedule'],bad_certificate=True)
            with self.assertRaisesRegex(ValueError,'certificate'): capture(root,freeze,frozen,factory)
            self.assertEqual(len(factory.children),1)

    def test_query_zero_bounds_round_chain_and_selected_edge_checks(self):
        zero = dict.fromkeys(work.FIELDS,0); result = work.query_diagnostics(zero)
        self.assertEqual((result['Q'],result['U'],result['U_over_Q'],result['query_fraction_status']),(0,0,None,'both_zero'))
        for q,u in ((5,0),(5,5)):
            result = work.query_diagnostics({**zero,'verifier_queries':q,'path_query_visits':2*q+u})
            self.assertEqual(result['U'],u)
        for value in (-1,16):
            with self.assertRaisesRegex(ValueError,'U outside'): work.query_diagnostics({**zero,'verifier_queries':5,'path_query_visits':value})
        with fixture() as (root,freeze,frozen):
            spec = frozen['schedule'][0]; original = prior_tests.output_for(spec,'compressed'); raw = root/'raw.json'
            for label in ('round identity','selected redistribution','replay aggregate','root dimensions','query U'):
                changed = copy.deepcopy(original)
                if label == 'round identity': changed['rounds']['multigraph_boruvka'][0]['round'] = 1
                elif label == 'selected redistribution':
                    changed['rounds']['compacting_boruvka'][0]['selected'] -= 1
                    changed['rounds']['compacting_boruvka'][1]['selected'] += 1
                elif label == 'replay aggregate': changed['algorithms']['multigraph_boruvka']['work']['contraction_edges'] += 1
                elif label == 'root dimensions': changed['algorithms']['kkt']['work']['root_after_two_edges'] += 1
                else: changed['algorithms']['kkt']['work']['path_query_visits'] = 0
                work.write_json(raw,changed)
                with self.subTest(label=label),self.assertRaises(ValueError): work.check_output(raw,spec)

    def test_strict_reload_hashes_schedule_raw_resource_and_complete_twins(self):
        with fixture() as (root,freeze,frozen):
            capture(root,freeze,frozen); path = root/'capture.json'; original = work.analysis.read_json(path)
            for label,change in (
                ('missing',lambda x:x['captures'].pop()),('exit',lambda x:x['captures'][0].update(exit_status=None)),
                ('spec',lambda x:x['captures'][0]['spec'].update(kkt_seed=2005)),
                ('group',lambda x:x['captures'][0]['group_exit_verification'].update(members=[{'pid':1}])),
                ('count',lambda x:x.update(checked_solver_outputs=215))):
                changed = copy.deepcopy(original); change(changed); work.write_json(path,changed)
                with self.subTest(label=label),self.assertRaises(ValueError): work.load(path)
            work.write_json(path,original); item = original['captures'][0]; raw = Path(item['raw']); before = raw.read_bytes()
            changed_value = work.analysis.read_json(raw); changed_value['algorithms']['kkt']['work']['sampled_edges'] = True
            work.write_json(raw,changed_value); changed = copy.deepcopy(original); changed['captures'][0]['raw_sha256'] = work.native.sha(raw); work.write_json(path,changed)
            with self.assertRaisesRegex(ValueError,'counter'): work.load(path)
            raw.write_bytes(before); work.write_json(path,original)
            _,values = work.load(path); altered = copy.deepcopy(values)
            altered[1][1]['topology_fingerprint'] += 1
            with self.assertRaisesRegex(ValueError,'topology'): work.complete(altered)
            bound = next(iter(frozen['bound_sha256'])); Path(bound).write_text('drift')
            with self.assertRaises(ValueError): work.load(path)

    def test_rss_unavailable_poison_crash_and_unknown_exit_never_advance(self):
        for mode in ('ceiling','unavailable','nonempty','crash'):
            with self.subTest(mode=mode),fixture() as (root,freeze,frozen):
                factory = prior_tests.Factory(frozen['schedule'],status=-11 if mode == 'crash' else 0,finishes=mode != 'unavailable')
                def provider(group):
                    if mode == 'unavailable': raise OSError('synthetic')
                    result = old.provider(group)
                    if mode == 'ceiling': result['members'][0]['rss_kib'] = work.RULE['rss_limit_kib']+1
                    return result
                sampler = work.monitor.BoundedSampler(provider,.1)
                with mock.patch.object(work.monitor,'bounded_terminate',return_value={'native_process_may_still_be_running':True}),self.assertRaises(ValueError):
                    capture(root,freeze,frozen,factory,sampler)
                self.assertEqual(len(factory.children),1)
                self.assertTrue(work.analysis.read_json(root/'capture.json')['native_process_may_still_be_running'])
        with fixture() as (root,freeze,frozen):
            gate = threading.Event(); factory = prior_tests.Factory(frozen['schedule'])
            sampler = work.monitor.BoundedSampler(lambda group:(gate.wait(),old.provider(group))[1],.01)
            try:
                with mock.patch.object(work.monitor,'bounded_terminate',return_value={'native_process_may_still_be_running':True}),self.assertRaisesRegex(ValueError,'timed out'):
                    capture(root,freeze,frozen,factory,sampler)
                second = prior_tests.Factory(frozen['schedule'])
                with self.assertRaisesRegex(ValueError,'poisoned'): capture(root,freeze,frozen,second,sampler,name='second.json')
                self.assertFalse(second.children); self.assertEqual(sampler.workers_started,1)
            finally: gate.set()

    def test_deadline_and_cleanup_exception_signal_guard_fail_closed(self):
        with fixture() as (root,freeze,frozen),mock.patch.object(work,'DEADLINE_SECONDS',-1):
            factory = prior_tests.Factory(frozen['schedule'])
            with mock.patch.object(work.monitor,'bounded_terminate',return_value={'native_process_may_still_be_running':True}),self.assertRaisesRegex(ValueError,'deadline'):
                capture(root,freeze,frozen,factory)
            self.assertEqual(len(factory.children),1)
        original_handler = signal.getsignal(signal.SIGTERM)
        with fixture() as (root,freeze,frozen):
            factory = prior_tests.Factory(frozen['schedule'],status=-11)
            def interrupted_cleanup(process,sampler):
                self.assertEqual(signal.getsignal(signal.SIGTERM),signal.SIG_IGN)
                raise KeyboardInterrupt('synthetic cleanup interruption')
            with mock.patch.object(work.monitor,'bounded_terminate',side_effect=interrupted_cleanup),self.assertRaises(ValueError):
                capture(root,freeze,frozen,factory)
            failed = work.analysis.read_json(root/'capture.json')
            self.assertTrue(failed['native_process_may_still_be_running']); self.assertIn('cleanup interruption',failed['cleanup'][0]['error'])
            self.assertEqual(signal.getsignal(signal.SIGTERM),original_handler); self.assertEqual(len(factory.children),1)
        info = dict(cleanup=[],native_process_may_still_be_running=True)
        with mock.patch.object(work.monitor,'bounded_terminate',return_value=dict(native_exit_known=True,group_exit_known=True,native_process_may_still_be_running=False)):
            work.cleanup_owned_group(None,None,info)
        self.assertTrue(info['native_process_may_still_be_running'])

    def test_merge_path_conflicts_and_freeze_matrix_metadata(self):
        self.assertEqual(work.merge_paths({'a':'one'},{'a':'one','b':'two'}),{'a':'one','b':'two'})
        with self.assertRaisesRegex(ValueError,'conflicting'): work.merge_paths({'a':'one'},{'a':'two'})
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root/'timing.json'; source.write_text('synthetic'); cases,schedule = inputs()
            proof = ({'binary':'/never-executed/compressed'},schedule,{str(source):work.native.sha(source)})
            path = root/'freeze.json'
            with mock.patch.object(work,'provenance',return_value=proof):
                work.prepare(argparse.Namespace(timing_capture=source,freeze=path)); good = work.check_freeze(path)
                self.assertEqual((good['expected_children'],good['expected_solver_outputs'],good['expected_replay_chains']),(72,216,144))
                for field in ('expected_children','expected_solver_outputs','expected_replay_chains','child_deadline_seconds'):
                    changed = copy.deepcopy(good); changed[field] += 1; work.write_json(path,changed)
                    with self.subTest(field=field),self.assertRaises(ValueError): work.check_freeze(path)


if __name__ == '__main__': unittest.main(verbosity=2)
