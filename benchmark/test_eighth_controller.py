#!/usr/bin/env python3
"""Synthetic outer eighth-controller gates; no subprocess or native execution."""
import copy
import importlib.util
import json
from pathlib import Path
import signal
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('eighth_outer_controller_test',
    HERE/'results/eighth-sampling-2026-10-15/validation/run_build_phase.py')
controller = importlib.util.module_from_spec(spec); spec.loader.exec_module(controller)


def inner_fixture(root,phase):
    builds,positive,negative = {'native-correctness':(43,20,4),'sanitizer-correctness':(40,20,4),
                              'timing-build':(12,0,0),'final-objects':(9,4,2)}[phase]
    commands = [['compile',str(index)] for index in range(builds)]
    tests = [dict(command=['test',str(i)],exit_status=0) for i in range(positive)]
    negatives = [dict(command=['negative',str(i)],exit_status=1) for i in range(negative)]
    def write(name,data):
        path = root/name; path.write_text(json.dumps(data)); return path
    if phase == 'final-objects':
        write('final-object-tests.json',dict(status='pass',build_commands=commands,tests=tests,
              wrong_policy_gates=negatives,rebuilds=[{},{}]))
        group_name = 'final-object-owned-groups.json'
    else:
        for variant in ('half','eighth'):
            write(f'{phase}-{variant}-build-record.json',dict(build_commands=commands,build_exit_status=0))
        if positive: write(f'{phase}-tests.json',dict(status='pass',tests=tests,wrong_policy_gates=negatives))
        group_name = f'{phase}-owned-groups.json'
    groups = []
    for index,item in enumerate([*[dict(command=c,exit_status=0) for c in commands],*tests,*negatives]):
        pid = 700+index
        groups.append(dict(**item,process_group=pid,cleanup=dict(native_exit_known=True,group_exit_known=True,
            native_process_may_still_be_running=False,returncode=item['exit_status'],process_group=pid,
            group_verification=dict(validation='pass',process_group=pid,members=[]))))
    return write(group_name,dict(groups=groups)),groups


class EighthControllerTests(unittest.TestCase):
    def test_fixed_commands_and_finite_budgets(self):
        self.assertEqual(controller.BUDGETS,{'controller-mocks':180,'build-mocks':180,'collector-mocks':180,'native-correctness':180,
                         'sanitizer-correctness':300,'timing-build':120,'final-objects':120})
        for phase in controller.BUDGETS:
            command = controller.command_for(phase)
            self.assertEqual(command[:2],[controller.sys.executable,'-B'])
            if phase in ('native-correctness','sanitizer-correctness','timing-build'):
                self.assertEqual(command[2:],[str(controller.ROOT/'benchmark/build_eighth_sampling.py'),
                    '--profile',phase,'--output',str(controller.OUTPUT),'--parent-freeze',str(controller.builder.PARENT_PATH)])
        with self.assertRaises(RuntimeError): controller.command_for('capture')

    def test_nested_receipts_complete_commands_outcomes_and_empty_groups(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            with mock.patch.object(controller,'OUTPUT',root):
                for phase,count in (('native-correctness',67),('sanitizer-correctness',64),('timing-build',12),('final-objects',15)):
                    path,groups = inner_fixture(root,phase)
                    proof = controller.check_inner(phase)
                    self.assertEqual(proof['groups'],count)
                    self.assertEqual(proof['native_test_executions'],0 if phase == 'timing-build' else 6 if phase == 'final-objects' else 24)
                    for mutate in (lambda values:values.pop(),
                                   lambda values:values[0]['cleanup'].__setitem__('group_exit_known',False),
                                   lambda values:values[0]['cleanup']['group_verification'].__setitem__('members',[123]),
                                   lambda values:values[0].__setitem__('exit_status',1),
                                   lambda values:values[0].__setitem__('command',['unexpected'])):
                        changed = copy.deepcopy(groups); mutate(changed); path.write_text(json.dumps(dict(groups=changed)))
                        with self.assertRaises(RuntimeError): controller.check_inner(phase)
                    path.write_text(json.dumps(dict(groups=groups)))

    def test_outer_success_timeout_signal_and_cleanup_failure_archive(self):
        class FakeProcess:
            pid = 987654
            def __init__(self,mode): self.returncode = 0 if mode == 'late_exit' else None; self.mode = mode
            def poll(self): return self.returncode
            def wait(self,timeout):
                if self.mode == 'signal': signal.getsignal(signal.SIGTERM)(signal.SIGTERM,None)
                self.returncode = 0; return 0
        class Sampler:
            poisoned = False
            def __init__(self): self.events = {}
            def sample(self,pid): return dict(validation='pass',rss_kib=0,members=[],process_group=pid)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            for mode in ('success','timeout','late_exit','signal','cleanup_error'):
                process = FakeProcess(mode); original_handler = signal.getsignal(signal.SIGTERM)
                actual_ns = controller.time.monotonic_ns
                late_timeline = iter((1_000_000_000,182_000_000_000,183_000_000_000))
                def cleanup(process,sampler,term_seconds,kill_seconds):
                    self.assertEqual((term_seconds,kill_seconds),(30,5))
                    self.assertIs(signal.getsignal(signal.SIGTERM),signal.SIG_IGN)
                    if mode == 'cleanup_error': raise KeyboardInterrupt('mock cleanup interrupted')
                    if process.returncode is None: process.returncode = -15
                    return dict(native_exit_known=True,group_exit_known=True,native_process_may_still_be_running=False)
                with mock.patch.object(controller,'OUTPUT',root), \
                     mock.patch.object(controller,'source_hashes',return_value={'source':'hash'}), \
                     mock.patch.object(controller,'check_inner',return_value=dict(validation='pass',groups=67,native_test_executions=24)), \
                     mock.patch.object(controller.monitor,'LibprocProvider',return_value=None), \
                     mock.patch.object(controller.monitor,'BoundedSampler',return_value=Sampler()), \
                     mock.patch.object(controller.monitor,'bounded_terminate',side_effect=cleanup), \
                     mock.patch.object(controller.subprocess,'Popen',return_value=process) as launch, \
                     mock.patch.object(controller.time,'monotonic_ns',side_effect=
                         (lambda: next(late_timeline)) if mode == 'late_exit' else actual_ns), \
                     mock.patch.dict(controller.BUDGETS,{'native-correctness':-1 if mode == 'timeout' else 180}):
                    result = controller.run_phase('native-correctness',root/mode)
                    launch.assert_called_once()
                    self.assertEqual(result['validation'],'pass' if mode == 'success' else 'failed')
                    self.assertEqual(result['all_owned_groups_verified_empty'],mode == 'success')
                    self.assertEqual(result['native_solver_execution'],True if mode == 'success' else None)
                    self.assertEqual(result['exit_status'],process.returncode)
                    if mode == 'late_exit':
                        self.assertEqual(result['exit_status'],0)
                        self.assertIn('exit observed beyond phase deadline',result['error'])
                    self.assertTrue((root/(mode+'.invocation.json')).exists())
                    self.assertEqual(json.loads((root/(mode+'.json')).read_text())['validation'],result['validation'])
                    with self.assertRaises(RuntimeError): controller.run_phase('native-correctness',root/mode)
                    launch.assert_called_once()
                self.assertIs(signal.getsignal(signal.SIGTERM),original_handler)

    def test_sampler_constructor_failure_is_archived_without_launch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            with mock.patch.object(controller,'OUTPUT',root), \
                 mock.patch.object(controller,'source_hashes',return_value={}), \
                 mock.patch.object(controller.monitor,'LibprocProvider',side_effect=RuntimeError('provider unavailable')), \
                 mock.patch.object(controller.subprocess,'Popen') as launch:
                result = controller.run_phase('build-mocks',root/'provider-failure')
                self.assertEqual(result['validation'],'failed'); launch.assert_not_called()
                self.assertIn('provider unavailable',result['error'])
                self.assertFalse(result['all_owned_groups_verified_empty'])
                self.assertTrue((root/'provider-failure.json').exists())


if __name__ == '__main__': unittest.main(verbosity=2)
