#!/usr/bin/env python3
"""Fresh frontend binding and mocked full-schedule gates; no native launches."""
import argparse
import copy
import csv
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import importlib.util
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('spatial_work_under_test',HERE/'collect.py')
work = importlib.util.module_from_spec(spec); spec.loader.exec_module(work)
old_tests = work.module('spatial_inherited_work_test_helpers',work.PARENT/'test_collect.py')


def mock_capture(root,frozen,freeze,mutation=None,bad_certificate=False):
    factory = old_tests.prior_tests.Factory(frozen['schedule'],mutation=mutation,bad_certificate=bad_certificate)
    def provider(group):
        process = next(p for p in factory.children if p.pid == group)
        return {'process_group':group,'members':[]} if process.returncode is not None else old_tests.old.provider(group)
    sampler = work.engine.monitor.BoundedSampler(provider,.1)
    args = argparse.Namespace(freeze=freeze,output=root/'capture.json',released=True)
    with mock.patch.object(work,'check_freeze',return_value=frozen):
        work.capture(args,sampler=sampler,popen=factory)
    return factory


class SpatialWorkTests(unittest.TestCase):
    def test_scopes_restore_and_parent_proof_never_uses_replacement(self):
        original = work.engine.check_freeze
        with mock.patch.object(work,'ORIGINAL_CHECK_FREEZE',return_value={'original':True}) as parent, \
             mock.patch.object(work.analysis,'hash_check'):
            with work.configured():
                self.assertIs(work.engine.check_freeze,work.check_freeze)
                self.assertEqual(work.parent(),{'original':True})
                with self.assertRaisesRegex(RuntimeError,'nested'):
                    with work.configured(): raise RuntimeError('nested')
                self.assertIs(work.engine.check_freeze,work.check_freeze)
            parent.assert_called_once_with(work.PARENT_FREEZE)
        self.assertIs(work.engine.check_freeze,original)
        with mock.patch.object(work,'ORIGINAL_CHECK_FREEZE',side_effect=ValueError('original proof drift')), \
             mock.patch.object(work.analysis,'hash_check'),self.assertRaisesRegex(ValueError,'original proof'):
            work.parent()

    def test_full72_fresh_capture_all216_counters_and144_chains(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); cases,schedule = old_tests.inputs()
            bound = root/'source'; bound.write_text('synthetic source')
            # The inherited fake launcher requires this sentinel; actual new
            # binary/path identity is checked against the real build below.
            frozen = dict(schedule=schedule,artifact={'binary':'/never-executed/compressed'},
                          bound_sha256={str(bound):work.native.sha(bound)})
            freeze = root/'freeze.json'; work.engine.write_json(freeze,frozen)
            factory = mock_capture(root,frozen,freeze)
            with mock.patch.object(work,'check_freeze',return_value=frozen):
                info,values = work.load(root/'capture.json')
                work.summarize(argparse.Namespace(capture=root/'capture.json',output_dir=root/'analysis'))
            self.assertEqual((len(factory.children),len(values),info['checked_solver_outputs'],info['checked_replay_chains']),
                             (72,72,216,144))
            self.assertEqual([spec for spec,value in values],schedule)
            for algorithm in work.engine.ALGORITHMS:
                for declaration,value in values:
                    expected = old_tests.prior_tests.output_for(declaration,'compressed')['algorithms'][algorithm]['work']
                    self.assertEqual(value['algorithms'][algorithm]['work'],expected)
            expected_counts = dict(work=216,rounds=432,round_chains=144,query_work=72)
            for name,count in expected_counts.items():
                with (root/'analysis'/f'{name}.csv').open(newline='') as stream:
                    self.assertEqual(len(list(csv.DictReader(stream))),count)
            with self.assertRaisesRegex(ValueError,'overwrite'): mock_capture(root,frozen,freeze)
            self.assertIs(work.engine.check_freeze,work.ORIGINAL_CHECK_FREEZE)

    def test_real_full_parent_newmain_and_twelve_frontend_gates(self):
        original = work.parent(); record = work.builder.check_record()
        self.assertEqual(record['object_paths'],original['artifact']['object_paths'])
        self.assertEqual(record['object_sha256'],original['artifact']['object_sha256'])
        self.assertEqual(len(record['build_commands']),2)
        proof = work.analysis.read_json(Path(record['gate_receipt']))
        self.assertEqual({(r['spec']['family'],r['spec']['graph_seed']) for r in proof['tests']},
            {(f,g) for f in ('leaf_distance4','leaf_shuffled4','grid2d_metric','grid2d_random','line_metric','line_random')
                   for g in (9000011,9000049)})
        self.assertEqual(len(proof['tests']),12)
        actual_read = work.analysis.read_json
        for mode in ('object','flags','extra','main','driver','build_status'):
            changed = copy.deepcopy(record)
            if mode == 'object': changed['object_paths']['kkt/kkt.o'] = '/other/object.o'
            elif mode == 'flags': changed['build_commands'][0].append('-DNDEBUG')
            elif mode == 'extra': changed['build_commands'].append(['unexpected'])
            elif mode == 'main': changed['main_object_sha256'] = '0'*64
            elif mode == 'driver': changed['source_delta']['new'] += '\n'
            else: changed['build_exit_status'] = True
            def read(path): return changed if Path(path).resolve() == work.builder.RECORD.resolve() else actual_read(path)
            with self.subTest(mode=mode),mock.patch.object(work.analysis,'read_json',side_effect=read),self.assertRaises(RuntimeError):
                work.builder.check_record()

    def test_gate_metadata_matrix_and_command_mutations_rejected(self):
        proof = work.analysis.read_json(work.builder.GATES); actual_read = work.analysis.read_json
        for mode in ('family','missing','command','counter_count','schema','status_bool'):
            changed = copy.deepcopy(proof)
            if mode == 'family': changed['schedule'][0]['family'] = 'leaf_hierarchy4'
            elif mode == 'missing': changed['tests'].pop()
            elif mode == 'command': changed['tests'][0]['command'][-1] = 'foreign'
            elif mode == 'counter_count': changed['checked_counter_fields'] = 64
            elif mode == 'schema': changed['schema'] = 'foreign'
            else: changed['tests'][0]['exit_status'] = False
            def read(path): return changed if Path(path).resolve() == work.builder.GATES.resolve() else actual_read(path)
            with self.subTest(mode=mode),mock.patch.object(work.analysis,'read_json',side_effect=read),self.assertRaises(RuntimeError):
                work.builder.check_record()

    def test_new_freeze_full_matrix_and_parent_binding(self):
        declared = work.declaration()
        self.assertEqual(declared['schema'],'heldout_spatial_work_freeze_v1')
        self.assertEqual((len(declared['schedule']),declared['prior_successes_reused']), (72,0))
        self.assertEqual(declared['schedule'],work.parent()['schedule'])
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary).resolve()/'freeze.json'
            work.engine.write_json(target,declared)
            with mock.patch.object(work,'declaration',return_value=declared):
                work.check_freeze(target)
                for mode in ('missing','reuse','artifact','parent','schema'):
                    changed = copy.deepcopy(declared)
                    if mode == 'missing': changed['schedule'].pop()
                    elif mode == 'reuse': changed['prior_successes_reused'] = 2
                    elif mode == 'artifact': changed['artifact']['binary'] = '/old/binary'
                    elif mode == 'parent': changed['parent_work_freeze_sha256'] = '0'*64
                    else: changed['schema'] = 'heldout_work_freeze_v1'
                    work.engine.write_json(target,changed)
                    with self.subTest(mode=mode),self.assertRaises(ValueError): work.check_freeze(target)

    def test_inherited_invalid_counter_and_certificate_stop_after_one_child(self):
        for mode in ('counter','certificate'):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve(); _,schedule = old_tests.inputs()
                frozen = dict(schedule=schedule,artifact={'binary':'/never-executed/compressed'},bound_sha256={})
                freeze = root/'freeze.json'; work.engine.write_json(freeze,frozen)
                with self.assertRaises(ValueError):
                    mock_capture(root,frozen,freeze,
                        mutation=(lambda value:value['algorithms']['kkt']['work'].update(sampled_edges=True)) if mode == 'counter' else None,
                        bad_certificate=mode == 'certificate')
                failed = work.analysis.read_json(root/'capture.json')
                self.assertEqual((failed['validation'],len(failed['captures'])),('failed',1))
                self.assertFalse(failed['native_process_may_still_be_running'])
                self.assertEqual(failed['captures'][0]['group_exit_verification']['members'],[])
                self.assertIs(work.engine.check_freeze,work.ORIGINAL_CHECK_FREEZE)


if __name__ == '__main__': unittest.main(verbosity=2)
