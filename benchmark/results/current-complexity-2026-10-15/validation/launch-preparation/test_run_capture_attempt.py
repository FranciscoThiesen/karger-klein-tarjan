#!/usr/bin/env python3
"""Prepared outer-controller mocks; never launch a native or collector process."""
import argparse
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import run_capture_attempt as outer


def args():
    return argparse.Namespace(freeze_sha256='a'*64, attempt='attempt01', released=True)


class Process:
    pid = 12345
    def __init__(self, status=0): self.returncode = status
    def poll(self): return self.returncode
    def wait(self, timeout): return self.returncode


def proof_fixture():
    records = [dict(spec=spec, process_group=100+index, exit_status=0,
                    group_exit_verification=dict(validation='pass', members=[]))
               for index, spec in enumerate(outer.expected_schedule())]
    captured = dict(validation='pass', checked_curves=24, checked_raw_rows=2376,
                    checked_timed_rows=1584, checked_warmup_rows=792, cleanup=[],
                    native_process_may_still_be_running=False,
                    freeze=str(outer.STUDY/'freeze.json'), freeze_sha256='a'*64)
    return captured, records, {}


class CaptureTests(unittest.TestCase):
    def test_fixed_persistent_command_schedule_and_explicit_freeze(self):
        self.assertEqual(outer.PACKAGE, Path('/Users/random_person/Desktop/kkt-eighth-sampling/benchmark/current_complexity'))
        self.assertEqual(outer.BUDGET_SECONDS, 87000)
        self.assertEqual(outer.command(Path('/synthetic/capture.json')),
            ['/usr/bin/arch', '-arm64', '/usr/bin/python3', '-B', '-u',
             str(outer.PACKAGE/'collect.py'), 'capture', '--freeze', str(outer.STUDY/'freeze.json'),
             '--output', '/synthetic/capture.json', '--released'])
        schedule = outer.expected_schedule()
        self.assertEqual(len(schedule), 24)
        self.assertEqual({tuple(row.values()) for row in schedule},
            {(family, algorithm, graph, sample, direction)
             for family in ('leaf_hierarchy4', 'leaf_shuffled4', 'gnm_random')
             for algorithm in ('kkt', 'multigraph_boruvka')
             for graph, direction in ((19000013, 'ascending'), (19000043, 'descending'))
             for sample in (3001, 3011)})
        frozen = dict(schedule=schedule, sizes=[2**exponent for exponent in range(10,21)], deadline_seconds=3600,
                      resource_rule=dict(rss_limit_kib=40*1024*1024), source_sha256={}, parent_helpers={}, bound_sha256={})
        with mock.patch.object(outer.Path, 'cwd', return_value=outer.ROOT), mock.patch.object(outer.engine, 'ROOT', outer.ROOT), \
             mock.patch.object(outer.engine, 'digest', return_value='a'*64) as hashed, \
             mock.patch.object(outer.engine, 'check_freeze', return_value=frozen), \
             mock.patch.object(outer, 'sources', return_value={}), mock.patch.object(outer.engine, 'recheck'):
            outer.preflight(args())
            self.assertEqual(hashed.call_args_list[0], mock.call(outer.STUDY/'freeze.json', 'a'*64))
            for field, value in (('released', False), ('freeze_sha256', 'not-a-sha'), ('attempt', '../escape')):
                changed = args(); setattr(changed, field, value)
                with self.assertRaises(ValueError): outer.preflight(changed)
            hashed.side_effect = ValueError('wrong supplied freeze')
            with self.assertRaisesRegex(ValueError, 'wrong supplied freeze'): outer.preflight(args())

    def test_complete_reload_counts_groups_identities_and_hashes(self):
        captured, records, bound = proof_fixture()
        with mock.patch.object(outer.engine, 'load', return_value=(captured, records, bound)), \
             mock.patch.object(outer.engine, 'digest', return_value='b'*64), \
             mock.patch.object(outer.engine, 'recheck') as rechecked, mock.patch.object(outer, 'sources', return_value={}):
            result = outer.check_completion(Path('/synthetic/capture.json'), 'a'*64, {}, {})
            self.assertEqual(result['checked_solver_calls'], 2376)
            self.assertEqual(len(result['native_process_groups']), 24)
            self.assertTrue(result['detached_native_groups_verified_empty']); rechecked.assert_called_once()
        changes = [('count', lambda info, rows: info.update(checked_raw_rows=2375)),
                   ('freeze', lambda info, rows: info.update(freeze_sha256='c'*64)),
                   ('identity', lambda info, rows: rows[0].update(spec=rows[1]['spec'])),
                   ('pid', lambda info, rows: rows[0].update(process_group=rows[1]['process_group'])),
                   ('exit', lambda info, rows: rows[0].update(exit_status=False)),
                   ('members', lambda info, rows: rows[0]['group_exit_verification'].update(members=[123]))]
        for name, change in changes:
            with self.subTest(name=name):
                info, rows, bound = copy.deepcopy(proof_fixture()); change(info, rows)
                with mock.patch.object(outer.engine, 'load', return_value=(info, rows, bound)):
                    with self.assertRaises(ValueError): outer.check_completion(Path('/synthetic/capture.json'), 'a'*64, {}, {})
        with self.assertRaisesRegex(ValueError, 'conflicting'): outer.merge({'/x':'a'*64}, {'/x':'b'*64})

    def test_actual_outer_status_and_strict_proof_both_required_exclusive(self):
        for status, proof_error, expected in ((0,None,'pass'), (1,None,'failed'), (0,ValueError('bad strict load'),'failed')):
            with self.subTest(status=status, proof_error=proof_error), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve(); sampler = mock.Mock(poisoned=False, events={})
                cleanup = dict(native_exit_known=True, group_exit_known=True, native_process_may_still_be_running=False)
                with mock.patch.object(outer, 'STUDY', root), mock.patch.object(outer, 'preflight', return_value=({},{})), \
                     mock.patch.object(outer.subprocess, 'Popen', return_value=Process(status)) as launched, \
                     mock.patch.object(outer.monitor, 'LibprocProvider'), mock.patch.object(outer.monitor, 'BoundedSampler', return_value=sampler), \
                     mock.patch.object(outer, 'cleanup_outer', return_value=cleanup), \
                     mock.patch.object(outer, 'bounded_proof', side_effect=proof_error, return_value={'validation':'pass'}) as proof:
                    result = outer.run(args()); self.assertEqual(result['validation'], expected)
                    self.assertEqual(proof.call_count, 1 if status==0 else 0)
                    self.assertEqual(result['all_owned_groups_verified_empty'], expected=='pass')
                    self.assertEqual(result['detached_native_process_may_still_be_running'], expected!='pass')
                    self.assertEqual(result['exit_status'], status)
                    with self.assertRaises(FileExistsError): outer.run(args())
                    self.assertEqual(launched.call_count, 1)
                receipt = json.loads((root/'attempt01/receipt.json').read_text())
                self.assertEqual(receipt['validation'], expected)

    def test_deadline_failures_keep_actual_status_and_do_not_claim_success(self):
        for times in ((0, (outer.BUDGET_SECONDS+1)*10**9, (outer.BUDGET_SECONDS+2)*10**9),
                      (0, 1, (outer.BUDGET_SECONDS+1)*10**9)):
            with self.subTest(times=times), tempfile.TemporaryDirectory() as directory:
                sampler = mock.Mock(poisoned=False, events={})
                with mock.patch.object(outer, 'STUDY', Path(directory)), mock.patch.object(outer, 'preflight', return_value=({},{})), \
                     mock.patch.object(outer.subprocess, 'Popen', return_value=Process()), \
                     mock.patch.object(outer.monitor, 'LibprocProvider'), mock.patch.object(outer.monitor, 'BoundedSampler', return_value=sampler), \
                     mock.patch.object(outer, 'cleanup_outer', return_value=dict(native_exit_known=True,group_exit_known=True,native_process_may_still_be_running=False)), \
                     mock.patch.object(outer, 'bounded_proof', return_value={'validation':'pass'}), \
                     mock.patch.object(outer.time, 'monotonic_ns', side_effect=times):
                    result = outer.run(args())
                self.assertEqual(result['validation'], 'failed'); self.assertEqual(result['exit_status'], 0)
                self.assertTrue(result['complete_interval_deadline_exceeded'])

    def test_cleanup_uncertainty_and_proof_timer_restore_handlers(self):
        previous = object()
        with mock.patch.object(outer.signal, 'getsignal', return_value=previous), mock.patch.object(outer.signal, 'signal') as handler, \
             mock.patch.object(outer.monitor, 'bounded_terminate', side_effect=KeyboardInterrupt('cleanup interrupted')):
            result = outer.cleanup_outer(Process(), mock.Mock())
            self.assertTrue(result['native_process_may_still_be_running'])
            self.assertEqual(handler.call_args_list, [mock.call(outer.signal.SIGTERM,outer.signal.SIG_IGN),mock.call(outer.signal.SIGTERM,previous)])
        with mock.patch.object(outer.time, 'monotonic_ns', return_value=1), mock.patch.object(outer.signal,'getitimer',return_value=(0.0,0.0)), \
             mock.patch.object(outer.signal,'getsignal',return_value=previous), mock.patch.object(outer.signal,'signal') as handler, \
             mock.patch.object(outer.signal,'setitimer') as timer, mock.patch.object(outer,'check_completion',side_effect=ValueError('strict proof failed')):
            with self.assertRaisesRegex(ValueError, 'strict proof failed'): outer.bounded_proof(None,None,None,None,10**9+1)
            self.assertEqual(timer.call_args_list,[mock.call(outer.signal.ITIMER_REAL,1.0),mock.call(outer.signal.ITIMER_REAL,0)])
            self.assertEqual(handler.call_args_list[-1],mock.call(outer.signal.SIGALRM,previous))


if __name__ == '__main__': unittest.main(verbosity=2)
