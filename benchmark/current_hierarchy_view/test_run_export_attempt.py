#!/usr/bin/env python3
"""Mocked archival lifecycle tests; no build, native export or process launch."""
import argparse
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import run_export_attempt as outer

class Process:
    pid=12345
    def __init__(self,status=0):self.returncode=status
    def poll(self):return self.returncode
    def wait(self,timeout):return self.returncode

class OuterTests(unittest.TestCase):
    def test_fixed_three_command_producer_and_exclusive_attempt(self):
        self.assertEqual(outer.PACKAGE,Path('/Users/random_person/Desktop/kkt-eighth-sampling/benchmark/current_hierarchy_view'))
        self.assertEqual(outer.command_for(Path('/synthetic/inner')),
            ['/usr/bin/arch','-arm64','/usr/bin/python3','-B','-u',str(outer.PACKAGE/'build_native_view.py'),
             '--output','/synthetic/inner','--released'])
        for status,proof_error,expected in ((0,None,'pass'),(0,ValueError('detached proof missing'),'failed'),(1,None,'failed')):
            with self.subTest(status=status,proof_error=proof_error),tempfile.TemporaryDirectory() as directory:
                root=Path(directory).resolve();package=root/'benchmark/current_hierarchy_view';value=argparse.Namespace(output=root/'attempt')
                sampler=mock.Mock(poisoned=False,events={})
                with mock.patch.object(outer,'ROOT',root),mock.patch.object(outer,'PACKAGE',package),mock.patch.object(outer.gate,'HERE',package), \
                     mock.patch.object(outer.Path,'cwd',return_value=root),mock.patch.object(outer,'sources',return_value={}), \
                     mock.patch.object(outer.subprocess,'Popen',return_value=Process(status)) as launched, \
                     mock.patch.object(outer.monitor,'LibprocProvider'),mock.patch.object(outer.monitor,'BoundedSampler',return_value=sampler), \
                     mock.patch.object(outer,'cleanup_outer',return_value=dict(native_exit_known=True,group_exit_known=True,native_process_may_still_be_running=False)), \
                     mock.patch.object(outer,'bounded_proof',side_effect=proof_error,return_value={'validation':'pass'}) as checked:
                    result=outer.run(value);self.assertEqual(result['validation'],expected)
                    self.assertTrue(result['outer_group_verified_empty'])
                    self.assertEqual(result['detached_native_process_may_still_be_running'],expected!='pass')
                    self.assertEqual(result['all_owned_groups_verified_empty'],expected=='pass')
                    self.assertEqual(checked.call_count,int(status==0))
                    with self.assertRaises(FileExistsError):outer.run(value)
                    self.assertEqual(launched.call_count,1)

    def test_late_zero_exit_and_complete_interval_are_retained_failures(self):
        for times in ((0,(outer.BUDGET_SECONDS+1)*10**9,(outer.BUDGET_SECONDS+2)*10**9),
                      (0,1,(outer.BUDGET_SECONDS+1)*10**9)):
            with self.subTest(times=times),tempfile.TemporaryDirectory() as directory:
                root=Path(directory).resolve();package=root/'benchmark/current_hierarchy_view';sampler=mock.Mock(poisoned=False,events={})
                with mock.patch.object(outer,'ROOT',root),mock.patch.object(outer,'PACKAGE',package),mock.patch.object(outer.gate,'HERE',package), \
                     mock.patch.object(outer.Path,'cwd',return_value=root),mock.patch.object(outer,'sources',return_value={}), \
                     mock.patch.object(outer.subprocess,'Popen',return_value=Process()), \
                     mock.patch.object(outer.monitor,'LibprocProvider'),mock.patch.object(outer.monitor,'BoundedSampler',return_value=sampler), \
                     mock.patch.object(outer,'cleanup_outer',return_value=dict(native_exit_known=True,group_exit_known=True,native_process_may_still_be_running=False)), \
                     mock.patch.object(outer,'bounded_proof',return_value={'validation':'pass'}),mock.patch.object(outer.time,'monotonic_ns',side_effect=times):
                    result=outer.run(argparse.Namespace(output=root/'attempt'))
                self.assertEqual(result['validation'],'failed');self.assertTrue(result['complete_interval_deadline_exceeded'])

    def test_unknown_outer_cleanup_cannot_reach_detached_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();package=root/'benchmark/current_hierarchy_view';sampler=mock.Mock(poisoned=False,events={})
            with mock.patch.object(outer,'ROOT',root),mock.patch.object(outer,'PACKAGE',package),mock.patch.object(outer.gate,'HERE',package), \
                 mock.patch.object(outer.Path,'cwd',return_value=root),mock.patch.object(outer,'sources',return_value={}), \
                 mock.patch.object(outer.subprocess,'Popen',return_value=Process()), \
                 mock.patch.object(outer.monitor,'LibprocProvider'),mock.patch.object(outer.monitor,'BoundedSampler',return_value=sampler), \
                 mock.patch.object(outer,'cleanup_outer',return_value=dict(native_exit_known=True,group_exit_known=False,native_process_may_still_be_running=True)), \
                 mock.patch.object(outer,'bounded_proof') as checked:
                result=outer.run(argparse.Namespace(output=root/'attempt'))
            self.assertEqual(result['validation'],'failed');self.assertFalse(result['all_owned_groups_verified_empty'])
            self.assertTrue(result['detached_native_process_may_still_be_running']);checked.assert_not_called()

    def test_cleanup_and_inner_proof_restore_signal_handlers(self):
        prior=object()
        with mock.patch.object(outer.signal,'getsignal',return_value=prior),mock.patch.object(outer.signal,'signal') as handler, \
             mock.patch.object(outer.monitor,'bounded_terminate',side_effect=RuntimeError('cleanup unavailable')):
            result=outer.cleanup_outer(Process(),mock.Mock());self.assertTrue(result['native_process_may_still_be_running'])
            self.assertEqual(handler.call_args_list,[mock.call(outer.signal.SIGTERM,outer.signal.SIG_IGN),mock.call(outer.signal.SIGTERM,prior)])
        with mock.patch.object(outer.time,'monotonic_ns',return_value=1),mock.patch.object(outer.signal,'getitimer',return_value=(0.0,0.0)), \
             mock.patch.object(outer.signal,'getsignal',return_value=prior),mock.patch.object(outer.signal,'signal') as handler, \
             mock.patch.object(outer.signal,'setitimer') as timer,mock.patch.object(outer,'check_inner',side_effect=ValueError('invalid proof')):
            with self.assertRaisesRegex(ValueError,'invalid proof'):outer.bounded_proof(None,None,10**9+1)
            self.assertEqual(timer.call_args_list,[mock.call(outer.signal.ITIMER_REAL,1.0),mock.call(outer.signal.ITIMER_REAL,0)])
            self.assertEqual(handler.call_args_list[-1],mock.call(outer.signal.SIGALRM,prior))

if __name__=='__main__':unittest.main(verbosity=2)
