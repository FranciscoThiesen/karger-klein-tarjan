#!/usr/bin/env python3
"""Outer-controller mocks only; no acquisition, compiler or native execution."""
import argparse
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import run_gate_attempt as outer

def args(output,phase='build'):
    return argparse.Namespace(phase=phase,output=output,library_source=Path('/synthetic/source'),
        build_directory=Path('/synthetic/build'),build_record=None,git_resolve=None)

class Process:
    pid=12345
    def __init__(self,status=0):self.returncode=status
    def poll(self):return self.returncode
    def wait(self,timeout):return self.returncode

class OuterTests(unittest.TestCase):
    def test_literal_commands_cannot_launch_study(self):
        self.assertEqual(outer.PACKAGE,Path('/Users/random_person/Desktop/kkt-eighth-sampling/benchmark/current_complexity'))
        value=args(Path('/synthetic/output'));command=outer.command_for(value,Path('/synthetic/inner'))
        self.assertEqual(command[:6],['/usr/bin/arch','-arm64','/usr/bin/python3','-B','-u',str(outer.PACKAGE/'build_library_main.py')])
        self.assertEqual(command[6],'build');self.assertNotIn('capture',command)
        value.phase='capture'
        with self.assertRaises(ValueError):outer.command_for(value,Path('/synthetic/inner'))
        with tempfile.TemporaryDirectory() as directory:
            record=Path(directory)/'record.json';record.write_text('{}')
            value=argparse.Namespace(phase='smoke',build_record=record,library_source=None,build_directory=None,git_resolve=None)
            command=outer.command_for(value,Path('/synthetic/inner'))
            self.assertEqual(command[6:9],['smoke','--build-record',str(record.resolve())])
            value.library_source=Path('/forbidden')
            with self.assertRaises(ValueError):outer.command_for(value,Path('/synthetic/inner'))

    def test_success_requires_inner_proof_and_keeps_exclusive_receipts(self):
        for proof_error,status,expected in ((None,0,'pass'),(ValueError('missing detached proof'),0,'failed'),(None,1,'failed')):
            with self.subTest(proof_error=proof_error,status=status),tempfile.TemporaryDirectory() as directory:
                root=Path(directory).resolve();value=args(root/'attempt');sampler=mock.Mock(poisoned=False,events={})
                cleanup=dict(native_exit_known=True,group_exit_known=True,native_process_may_still_be_running=False)
                with mock.patch.object(outer,'ROOT',root),mock.patch.object(outer.gate,'ROOT',root),mock.patch.object(outer.Path,'cwd',return_value=root), \
                     mock.patch.object(outer,'source_hashes',return_value={}),mock.patch.object(outer.subprocess,'Popen',return_value=Process(status)) as launched, \
                     mock.patch.object(outer.monitor,'LibprocProvider'),mock.patch.object(outer.monitor,'BoundedSampler',return_value=sampler), \
                     mock.patch.object(outer,'cleanup_outer',return_value=cleanup),mock.patch.object(outer,'bounded_inner_proof',side_effect=proof_error,return_value={'validation':'pass'}) as checked:
                    result=outer.run_phase(value)
                    self.assertEqual(result['validation'],expected);self.assertTrue(result['outer_group_verified_empty'])
                    self.assertEqual(result['all_owned_groups_verified_empty'],expected=='pass')
                    self.assertEqual(result['detached_native_process_may_still_be_running'],expected!='pass')
                    self.assertEqual(checked.call_count,1 if status==0 else 0)
                    with self.assertRaises(FileExistsError):outer.run_phase(value)
                    self.assertEqual(launched.call_count,1)
                self.assertEqual(json.loads((value.output/'receipt.json').read_text())['validation'],expected)

    def test_late_observed_zero_exit_and_late_complete_interval_are_failures(self):
        for times in ((0,(outer.BUDGETS['build']+1)*10**9,(outer.BUDGETS['build']+2)*10**9),
                      (0,1,(outer.BUDGETS['build']+1)*10**9)):
            with self.subTest(times=times),tempfile.TemporaryDirectory() as directory:
                root=Path(directory).resolve();sampler=mock.Mock(poisoned=False,events={})
                with mock.patch.object(outer,'ROOT',root),mock.patch.object(outer.gate,'ROOT',root),mock.patch.object(outer.Path,'cwd',return_value=root), \
                     mock.patch.object(outer,'source_hashes',return_value={}),mock.patch.object(outer.subprocess,'Popen',return_value=Process()), \
                     mock.patch.object(outer.monitor,'LibprocProvider'),mock.patch.object(outer.monitor,'BoundedSampler',return_value=sampler), \
                     mock.patch.object(outer,'cleanup_outer',return_value=dict(native_exit_known=True,group_exit_known=True,native_process_may_still_be_running=False)), \
                     mock.patch.object(outer,'bounded_inner_proof',return_value={'validation':'pass'}),mock.patch.object(outer.time,'monotonic_ns',side_effect=times):
                    result=outer.run_phase(args(root/'attempt'))
                self.assertEqual(result['validation'],'failed');self.assertTrue(result['complete_interval_deadline_exceeded'])

    def test_cleanup_interrupt_and_proof_timer_restore_handlers(self):
        prior=object()
        with mock.patch.object(outer.signal,'getsignal',return_value=prior),mock.patch.object(outer.signal,'signal') as handler, \
             mock.patch.object(outer.monitor,'bounded_terminate',side_effect=RuntimeError('cleanup unavailable')):
            result=outer.cleanup_outer(Process(),mock.Mock())
            self.assertTrue(result['native_process_may_still_be_running'])
            self.assertEqual(handler.call_args_list,[mock.call(outer.signal.SIGTERM,outer.signal.SIG_IGN),mock.call(outer.signal.SIGTERM,prior)])
        with mock.patch.object(outer.time,'monotonic_ns',return_value=1),mock.patch.object(outer.signal,'getitimer',return_value=(0.0,0.0)), \
             mock.patch.object(outer.signal,'getsignal',return_value=prior),mock.patch.object(outer.signal,'signal') as handler, \
             mock.patch.object(outer.signal,'setitimer') as timer,mock.patch.object(outer,'check_inner',side_effect=ValueError('invalid complete proof')):
            with self.assertRaisesRegex(ValueError,'invalid complete proof'):outer.bounded_inner_proof(None,None,None,10**9+1)
            self.assertEqual(timer.call_args_list,[mock.call(outer.signal.ITIMER_REAL,1.0),mock.call(outer.signal.ITIMER_REAL,0)])
            self.assertEqual(handler.call_args_list[-1],mock.call(outer.signal.SIGALRM,prior))

if __name__=='__main__':unittest.main(verbosity=2)
