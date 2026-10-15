#!/usr/bin/env python3
"""Synthetic outer-controller checks; no native or collector process launches."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import signal
import tempfile
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location("lower_density_work_outer_under_test",HERE/"run_capture_attempt.py")
outer=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(outer)


def args():return argparse.Namespace(released=True,freeze_sha256="a"*64,attempt="attempt01")


class Process:
    pid=76543
    def __init__(self,status=0):self.returncode=status
    def poll(self):return self.returncode
    def wait(self,timeout):return self.returncode


def expected():
    cases=[f"{f}_n{n}_d{d}_p0" for d,sizes in
           ((16,(512,2048,8192,32768,131072,524288,2097152)),
            (8,(256,1024,4096,16384,65536,262144,1048576,4194304)))
           for n in sizes for f in ("leaf_distance4","leaf_shuffled4")]
    return [("eighth",c,g,3407) for g,order in ((23000003,cases),(23000029,cases[::-1])) for c in order]


def proof():
    specs=[dict(zip(("variant","case_id","graph_seed","kkt_seed"),identity)) for identity in expected()]
    values=[(s,dict(algorithms={a:{} for a in ("kkt","compacting_boruvka","multigraph_boruvka")},
                    rounds={a:[] for a in ("compacting_boruvka","multigraph_boruvka")})) for s in specs]
    items=[dict(spec=s,process_group=100+i,exit_status=0,group_exit_verification=dict(validation="pass",members=[]))
           for i,s in enumerate(specs)]
    info=dict(validation="pass",cleanup=[],native_process_may_still_be_running=False,
              freeze=str(outer.HERE/"freeze.json"),freeze_sha256="a"*64,
              checked_children=60,checked_solver_outputs=180,captures=items)
    return info,values


class WorkOuterTests(unittest.TestCase):
    def test_fixed_schedule_ceiling_and_explicit_release(self):
        self.assertEqual(outer.BUDGET_SECONDS,60*1800+600)
        self.assertEqual(outer.identities(),expected())
        with tempfile.TemporaryDirectory() as directory,mock.patch.object(outer,"HERE",Path(directory)),\
             mock.patch.object(outer.work.subprocess,"Popen") as launched:
            for field,value in (("released",False),("freeze_sha256","wrong"),("attempt","../escape")):
                changed=args();setattr(changed,field,value)
                with self.assertRaises(ValueError):outer.run(changed)
            launched.assert_not_called()

    def test_strict_completion_exact_all_groups_and_counts(self):
        with mock.patch.object(outer.work,"load",return_value=proof()),mock.patch.object(outer,"recheck") as checked,\
             mock.patch.object(outer.work.native,"sha",return_value="b"*64):
            result=outer.check_completion(Path("/synthetic/capture.json"),"a"*64,{})
            self.assertEqual((result["checked_children"],result["checked_solver_outputs"],result["checked_replay_chains"]),(60,180,120))
            self.assertEqual(len(result["native_process_groups"]),60);checked.assert_called_once()
        for change in (lambda p:p[0].update(checked_children=59),lambda p:p[0].update(freeze_sha256="c"*64),
            lambda p:p[0]["captures"][0].update(exit_status=False),
            lambda p:p[0]["captures"][0].update(process_group=p[0]["captures"][1]["process_group"]),
            lambda p:p[0]["captures"][0]["group_exit_verification"].update(members=[1]),
            lambda p:p[1][0][0].update(kkt_seed=2609),lambda p:p[1].pop(),
            lambda p:p[1][0][1]["rounds"].pop("compacting_boruvka")):
            value=copy.deepcopy(proof());change(value)
            with mock.patch.object(outer.work,"load",return_value=value),self.assertRaises(ValueError):
                outer.check_completion(Path("/synthetic/capture.json"),"a"*64,{})

    def test_actual_exit_and_full_proof_both_required_with_exclusive_receipts(self):
        for status,proof_error,validation in ((0,None,"pass"),(2,None,"failed"),(0,ValueError("strict reject"),"failed")):
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);(root/"collect.py").write_text("synthetic");(root/"freeze.json").write_text("synthetic")
                sampler=mock.Mock(poisoned=False,events={})
                with mock.patch.object(outer,"HERE",root),mock.patch.object(outer.work.analysis,"hash_check"),\
                     mock.patch.object(outer.work.native,"sha",return_value="a"*64),\
                     mock.patch.object(outer.work,"check_freeze",return_value=dict(schedule=[dict(zip(("variant","case_id","graph_seed","kkt_seed"),v)) for v in expected()])),\
                     mock.patch.object(outer.subprocess,"Popen",return_value=Process(status)) as launched,\
                     mock.patch.object(outer.work.monitor,"LibprocProvider"),\
                     mock.patch.object(outer.work.monitor,"BoundedSampler",return_value=sampler),\
                     mock.patch.object(outer,"cleanup_outer",return_value=dict(native_exit_known=True,group_exit_known=True,native_process_may_still_be_running=False)),\
                     mock.patch.object(outer,"bounded_completion",side_effect=proof_error,return_value=dict(checked_children=60)) as completed:
                    result=outer.run(args())
                    self.assertEqual((result["validation"],result["exit_status"]),(validation,status))
                    self.assertEqual(result["all_owned_groups_verified_empty"],validation=="pass")
                    self.assertEqual(result["detached_native_process_may_still_be_running"],validation!="pass")
                    self.assertEqual(completed.call_count,1 if status==0 else 0)
                    self.assertTrue(result["native_solver_execution"]);self.assertFalse(result["performance_execution"])
                    argv=launched.call_args.args[0]
                    self.assertEqual(argv,["/usr/bin/arch","-arm64","/usr/bin/python3","-B","-u",str(root/"collect.py"),
                        "capture","--freeze",str(root/"freeze.json"),"--output",str(root/"capture-attempt01.json"),"--released"])
                    with self.assertRaisesRegex(ValueError,"existing evidence"):outer.run(args())
                    self.assertEqual(launched.call_count,1)
                receipt=json.loads((root/"capture-controller-attempt01.json").read_text())
                self.assertEqual(receipt["validation"],validation)

    def test_late_observed_exit_and_late_complete_interval_preserve_actual_status(self):
        for clocks in ((0,(outer.BUDGET_SECONDS+1)*10**9,(outer.BUDGET_SECONDS+2)*10**9),
                       (0,1,(outer.BUDGET_SECONDS+1)*10**9)):
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);sampler=mock.Mock(poisoned=False,events={})
                with mock.patch.object(outer,"HERE",root),mock.patch.object(outer.work.analysis,"hash_check"),\
                     mock.patch.object(outer.work.native,"sha",return_value="a"*64),\
                     mock.patch.object(outer.work,"check_freeze",return_value=dict(schedule=[dict(zip(("variant","case_id","graph_seed","kkt_seed"),v)) for v in expected()])),\
                     mock.patch.object(outer.subprocess,"Popen",return_value=Process()),\
                     mock.patch.object(outer.work.monitor,"LibprocProvider"),\
                     mock.patch.object(outer.work.monitor,"BoundedSampler",return_value=sampler),\
                     mock.patch.object(outer,"cleanup_outer",return_value=dict(native_exit_known=True,group_exit_known=True,native_process_may_still_be_running=False)),\
                     mock.patch.object(outer,"bounded_completion",return_value=dict(checked_children=60)),\
                     mock.patch.object(outer.time,"monotonic_ns",side_effect=clocks):
                    result=outer.run(args())
                self.assertEqual((result["validation"],result["exit_status"]),("failed",0))
                self.assertTrue(result["complete_interval_deadline_exceeded"])

    def test_unknown_outer_exit_and_spawn_metadata_interruptions_remain_unknown(self):
        class MetadataInterrupted(Process):
            @property
            def pid(self):raise KeyboardInterrupt("metadata interrupted after spawn")
        for mode in ("unknown_cleanup","popen_interrupted","metadata_interrupted"):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);sampler=mock.Mock(poisoned=False,events={})
                process=MetadataInterrupted() if mode=="metadata_interrupted" else Process()
                interrupted=KeyboardInterrupt("Popen interrupted after possible spawn") if mode=="popen_interrupted" else None
                cleanup=dict(native_exit_known=mode!="unknown_cleanup",group_exit_known=mode!="unknown_cleanup",
                             native_process_may_still_be_running=mode=="unknown_cleanup")
                with mock.patch.object(outer,"HERE",root),mock.patch.object(outer.work.analysis,"hash_check"),\
                     mock.patch.object(outer.work.native,"sha",return_value="a"*64),\
                     mock.patch.object(outer.work,"check_freeze",return_value=dict(schedule=[dict(zip(("variant","case_id","graph_seed","kkt_seed"),v)) for v in expected()])),\
                     mock.patch.object(outer.subprocess,"Popen",side_effect=interrupted,return_value=process) as launched,\
                     mock.patch.object(outer.work.monitor,"LibprocProvider"),\
                     mock.patch.object(outer.work.monitor,"BoundedSampler",return_value=sampler),\
                     mock.patch.object(outer,"cleanup_outer",return_value=cleanup),\
                     mock.patch.object(outer,"bounded_completion") as completed:
                    result=outer.run(args())
                self.assertEqual(result["validation"],"failed");self.assertFalse(result["all_owned_groups_verified_empty"])
                self.assertTrue(result["detached_native_process_may_still_be_running"]);completed.assert_not_called()
                self.assertEqual(launched.call_count,1)
                receipt=json.loads((root/"capture-controller-attempt01.json").read_text())
                self.assertTrue(receipt["detached_native_process_may_still_be_running"])
                self.assertEqual(receipt["exit_status"],None if mode=="popen_interrupted" else 0)

    def test_cleanup_signal_and_proof_timer_restore_even_on_failure(self):
        previous=object()
        with mock.patch.object(outer.signal,"getsignal",return_value=previous),mock.patch.object(outer.signal,"signal") as handler,\
             mock.patch.object(outer.work.monitor,"bounded_terminate",side_effect=KeyboardInterrupt("synthetic")):
            result=outer.cleanup_outer(Process(),mock.Mock())
            self.assertTrue(result["native_process_may_still_be_running"])
            self.assertEqual(handler.call_args_list,[mock.call(signal.SIGTERM,signal.SIG_IGN),mock.call(signal.SIGTERM,previous)])
        with mock.patch.object(outer.time,"monotonic_ns",return_value=1),\
             mock.patch.object(outer.signal,"getitimer",return_value=(0.0,0.0)),\
             mock.patch.object(outer.signal,"getsignal",return_value=previous),mock.patch.object(outer.signal,"signal") as handler,\
             mock.patch.object(outer.signal,"setitimer") as timer,\
             mock.patch.object(outer,"check_completion",side_effect=ValueError("strict rejected")):
            with self.assertRaisesRegex(ValueError,"strict rejected"):outer.bounded_completion(None,None,None,10**9+1)
            self.assertEqual(timer.call_args_list,[mock.call(signal.ITIMER_REAL,1.0),mock.call(signal.ITIMER_REAL,0)])
            self.assertEqual(handler.call_args_list[-1],mock.call(signal.SIGALRM,previous))


if __name__=="__main__":unittest.main(verbosity=2)
