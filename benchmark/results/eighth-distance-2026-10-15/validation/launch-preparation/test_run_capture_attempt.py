#!/usr/bin/env python3
"""Outer-controller mocks: no native or collector process may be launched."""
import argparse
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import run_capture_attempt as outer


def args():
    return argparse.Namespace(freeze_sha256='a'*64, attempt='controller-attempt01', released=True)


class Process:
    pid = 12345
    def __init__(self, status=0): self.returncode = status
    def poll(self): return self.returncode
    def wait(self, timeout): return self.returncode


def literal_schedule():
    names = [f'{family}_n{n}_d32_p0' for n in (1024,4096,16384,65536,262144,1048576)
             for family in ('leaf_distance4','leaf_shuffled4')]
    return [dict(case_id=case,graph_seed=graph,kkt_seed=3203)
            for graph, cases in ((21000011,names),(21000041,names[::-1])) for case in cases]


def proof_fixture():
    items = [dict(**spec, process_group=100+index, exit_status=0,
                  group_exit_verification=dict(validation='pass', members=[]))
             for index,spec in enumerate(literal_schedule())]
    captured = dict(validation='pass',checked_rows=1008,checked_timed_rows=864,checked_warmup_rows=144,
                    cleanup=[],native_process_may_still_be_running=False,
                    freeze=str(outer.STUDY/'freeze.json'),freeze_sha256='a'*64,captures=items)
    cases = {f'{family}_n{n}_d32_p0':dict(case_id=f'{family}_n{n}_d32_p0',family=family,n=n,m=32*n,
                density=32,intrusion_per_mille=0) for n in (1024,4096,16384,65536,262144,1048576)
                for family in ('leaf_distance4','leaf_shuffled4')}
    rows = [dict(phase=phase) for phase,count in (('timed',864),('warmup',144)) for _ in range(count)]
    return captured,cases,rows,[{} for _ in range(1008)],[{} for _ in range(24)],{}


class CaptureTests(unittest.TestCase):
    def test_fixed_command_schedule_and_supplied_freeze_preflight(self):
        self.assertEqual(outer.BUDGET_SECONDS,21600)
        self.assertEqual(outer.COLLECTOR,Path('/Users/random_person/Desktop/kkt-eighth-sampling/benchmark/run_eighth_distance.py'))
        self.assertEqual(outer.command(),['/usr/bin/arch','-arm64','/usr/bin/python3','-B','-u',str(outer.COLLECTOR),
            'capture','--freeze',str(outer.STUDY/'freeze.json'),'--output',str(outer.STUDY/'distance.csv'),'--released'])
        self.assertEqual(outer.expected_schedule(),literal_schedule())
        self.assertEqual(len(outer.expected_cases()),12)
        captured,cases,*_ = proof_fixture()
        frozen=dict(working_directory=str(outer.ROOT),schedule=literal_schedule(),resource_rule=dict(rss_limit_kib=40*1024*1024))
        metadata=dict(validation='pass',phase='before',sleep_inhibition_verified=False,
            commands=[dict(command=command,exit_status=0) for command in outer.MACHINE_COMMANDS])
        with mock.patch.object(outer.Path,'cwd',return_value=outer.ROOT), \
             mock.patch.object(outer.engine.analysis,'hash_check') as checked, \
             mock.patch.object(outer.engine,'check_freeze',return_value=(frozen,cases)), \
             mock.patch.object(outer.engine.analysis,'read_json',return_value=metadata), \
             mock.patch.object(outer.engine.native,'sha',return_value='a'*64):
            outer.preflight(args())
            self.assertEqual(checked.call_args_list[0],mock.call(outer.STUDY/'freeze.json','a'*64))
            for field,value in (('released',False),('freeze_sha256','invalid'),('attempt','../escape')):
                changed=args();setattr(changed,field,value)
                with self.assertRaises(ValueError):outer.preflight(changed)
            metadata['commands'][0]['exit_status']=False
            with self.assertRaisesRegex(ValueError,'machine query'):outer.preflight(args())
            metadata['commands'][0]['exit_status']=0
            frozen['schedule'][0]['graph_seed']=17000011
            with self.assertRaisesRegex(ValueError,'schedule'):outer.preflight(args())
            frozen['schedule']=literal_schedule()
            checked.side_effect=ValueError('wrong supplied freeze')
            with self.assertRaisesRegex(ValueError,'wrong supplied freeze'):outer.preflight(args())

    def test_complete_strict_reload_counts_groups_identities_and_hashes(self):
        fixture=proof_fixture()
        with mock.patch.object(outer.engine,'load',return_value=fixture), \
             mock.patch.object(outer.engine.native,'sha',return_value='b'*64),mock.patch.object(outer,'recheck') as checked:
            result=outer.check_completion(Path('/synthetic/distance.json'),'a'*64,{})
            self.assertEqual(result['checked_solver_outputs'],1008)
            self.assertEqual(len(result['native_process_groups']),24)
            self.assertTrue(result['detached_native_groups_verified_empty']);checked.assert_called_once()
        changes=[('count',lambda f:f[0].update(checked_rows=1007)),
                 ('freeze',lambda f:f[0].update(freeze_sha256='c'*64)),
                 ('identity',lambda f:f[0]['captures'][0].update(case_id=f[0]['captures'][1]['case_id'])),
                 ('pid',lambda f:f[0]['captures'][0].update(process_group=f[0]['captures'][1]['process_group'])),
                 ('exit',lambda f:f[0]['captures'][0].update(exit_status=False)),
                 ('members',lambda f:f[0]['captures'][0]['group_exit_verification'].update(members=[123])),
                 ('raw_count',lambda f:f[2].pop()),
                 ('phase',lambda f:f[2][0].update(phase='warmup')),
                 ('resources',lambda f:f[4].pop())]
        for name,change in changes:
            with self.subTest(name=name):
                fixture=copy.deepcopy(proof_fixture());change(fixture)
                with mock.patch.object(outer.engine,'load',return_value=fixture):
                    with self.assertRaises(ValueError):outer.check_completion(Path('/synthetic/distance.json'),'a'*64,{})
        with self.assertRaisesRegex(ValueError,'conflicting'):outer.merge({'/x':'a'*64},{'/x':'b'*64})

    def test_actual_exit_and_strict_proof_are_both_required_and_attempts_exclusive(self):
        for status,proof_error,expected in ((0,None,'pass'),(1,None,'failed'),(0,ValueError('bad strict load'),'failed')):
            with self.subTest(status=status,proof_error=proof_error),tempfile.TemporaryDirectory() as directory:
                study=Path(directory).resolve();sampler=mock.Mock(poisoned=False,events={})
                cleanup=dict(native_exit_known=True,group_exit_known=True,native_process_may_still_be_running=False)
                with mock.patch.object(outer,'STUDY',study),mock.patch.object(outer,'preflight',return_value={}), \
                     mock.patch.object(outer.subprocess,'Popen',return_value=Process(status)) as launched, \
                     mock.patch.object(outer.monitor,'LibprocProvider'),mock.patch.object(outer.monitor,'BoundedSampler',return_value=sampler), \
                     mock.patch.object(outer,'cleanup_outer',return_value=cleanup), \
                     mock.patch.object(outer,'bounded_proof',side_effect=proof_error,return_value={'validation':'pass'}) as proof:
                    result=outer.run(args());self.assertEqual(result['validation'],expected)
                    self.assertEqual(proof.call_count,1 if status==0 else 0)
                    self.assertEqual(result['all_owned_groups_verified_empty'],expected=='pass')
                    self.assertEqual(result['detached_native_process_may_still_be_running'],expected!='pass')
                    self.assertEqual(result['exit_status'],status)
                    self.assertIsNone(result['per_child_total_wall_deadline'])
                    with self.assertRaises(FileExistsError):outer.run(args())
                    self.assertEqual(launched.call_count,1)
                receipt=json.loads((study/'validation/controller-attempt01/receipt.json').read_text())
                self.assertEqual(receipt['validation'],expected)
        with tempfile.TemporaryDirectory() as directory:
            study=Path(directory);(study/'distance.json').write_text('{"validation":"failed"}')
            with mock.patch.object(outer,'STUDY',study),mock.patch.object(outer,'preflight',return_value={}), \
                 mock.patch.object(outer.subprocess,'Popen') as launched:
                with self.assertRaisesRegex(ValueError,'existing raw evidence'):outer.run(args())
                launched.assert_not_called()

    def test_late_observed_exit_and_late_complete_interval_keep_actual_status(self):
        for times in ((0,(outer.BUDGET_SECONDS+1)*10**9,(outer.BUDGET_SECONDS+2)*10**9),
                      (0,1,(outer.BUDGET_SECONDS+1)*10**9)):
            with self.subTest(times=times),tempfile.TemporaryDirectory() as directory:
                sampler=mock.Mock(poisoned=False,events={})
                with mock.patch.object(outer,'STUDY',Path(directory)),mock.patch.object(outer,'preflight',return_value={}), \
                     mock.patch.object(outer.subprocess,'Popen',return_value=Process()), \
                     mock.patch.object(outer.monitor,'LibprocProvider'),mock.patch.object(outer.monitor,'BoundedSampler',return_value=sampler), \
                     mock.patch.object(outer,'cleanup_outer',return_value=dict(native_exit_known=True,group_exit_known=True,native_process_may_still_be_running=False)), \
                     mock.patch.object(outer,'bounded_proof',return_value={'validation':'pass'}), \
                     mock.patch.object(outer.time,'monotonic_ns',side_effect=times):
                    result=outer.run(args())
                self.assertEqual(result['validation'],'failed');self.assertEqual(result['exit_status'],0)
                self.assertTrue(result['complete_interval_deadline_exceeded'])

    def test_resource_failure_no_successful_proof_and_cleanup_uncertainty(self):
        class Running(Process):
            def __init__(self):super().__init__(None)
            def wait(self,timeout):raise outer.subprocess.TimeoutExpired('synthetic',timeout)
        for observation in (dict(validation='pass',rss_kib=40*1024*1024+1),dict(validation='unavailable')):
            with self.subTest(observation=observation),tempfile.TemporaryDirectory() as directory:
                sampler=mock.Mock(poisoned=False,events={});sampler.sample.return_value=observation
                with mock.patch.object(outer,'STUDY',Path(directory)),mock.patch.object(outer,'preflight',return_value={}), \
                     mock.patch.object(outer.subprocess,'Popen',return_value=Running()), \
                     mock.patch.object(outer.monitor,'LibprocProvider'),mock.patch.object(outer.monitor,'BoundedSampler',return_value=sampler), \
                     mock.patch.object(outer,'cleanup_outer',return_value=dict(native_exit_known=False,group_exit_known=False,native_process_may_still_be_running=True)), \
                     mock.patch.object(outer,'bounded_proof') as proof:
                    result=outer.run(args())
                self.assertEqual(result['validation'],'failed');self.assertIsNone(result['exit_status'])
                self.assertTrue(result['detached_native_process_may_still_be_running'])
                self.assertFalse(result['all_owned_groups_verified_empty']);proof.assert_not_called()
                self.assertEqual(sampler.sample.call_count,1 if observation['validation']=='pass' else 3)

    def test_cleanup_exception_and_proof_timer_restore_handlers(self):
        previous=object()
        with mock.patch.object(outer.signal,'getsignal',return_value=previous),mock.patch.object(outer.signal,'signal') as handler, \
             mock.patch.object(outer.monitor,'bounded_terminate',side_effect=KeyboardInterrupt('cleanup interrupted')):
            result=outer.cleanup_outer(Process(),mock.Mock())
            self.assertTrue(result['native_process_may_still_be_running'])
            self.assertEqual(handler.call_args_list,[mock.call(outer.signal.SIGTERM,outer.signal.SIG_IGN),mock.call(outer.signal.SIGTERM,previous)])
        with mock.patch.object(outer.time,'monotonic_ns',return_value=1),mock.patch.object(outer.signal,'getitimer',return_value=(0.0,0.0)), \
             mock.patch.object(outer.signal,'getsignal',return_value=previous),mock.patch.object(outer.signal,'signal') as handler, \
             mock.patch.object(outer.signal,'setitimer') as timer,mock.patch.object(outer,'check_completion',side_effect=ValueError('strict proof failed')):
            with self.assertRaisesRegex(ValueError,'strict proof failed'):outer.bounded_proof(None,None,None,10**9+1)
            self.assertEqual(timer.call_args_list,[mock.call(outer.signal.ITIMER_REAL,1.0),mock.call(outer.signal.ITIMER_REAL,0)])
            self.assertEqual(handler.call_args_list[-1],mock.call(outer.signal.SIGALRM,previous))


if __name__=='__main__':unittest.main(verbosity=2)
