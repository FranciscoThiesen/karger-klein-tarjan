#!/usr/bin/env python3
"""Focused nonnative gates for the complete lower-density work companion."""
import argparse
import contextlib
import copy
import csv
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import signal
import sys
import tempfile
import threading
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "benchmark"))
_spec = importlib.util.spec_from_file_location("lower_density_work_under_test", HERE / "collect.py")
work = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(work)
import test_eighth_sampling as native_tests
old = native_tests.old
LADDERS = ((16,(512,2048,8192,32768,131072,524288,2097152)),
           (8,(256,1024,4096,16384,65536,262144,1048576,4194304)))


def declared():
    cases = [dict(case_id=f"{family}_n{n}_d{d}_p0",family=family,n=n,m=n*d,density=d,intrusion_per_mille=0)
             for d,sizes in LADDERS for n in sizes for family in ("leaf_distance4","leaf_shuffled4")]
    return [dict(variant="eighth",**case,graph_seed=g,kkt_seed=3407,
                 input_fingerprint=100+case["density"]+case["n"]+(case["family"]=="leaf_shuffled4")+g,
                 topology_fingerprint=case["density"]+case["n"]+g)
            for gi,g in enumerate((23000003,23000029)) for case in (cases if gi==0 else list(reversed(cases)))]


@contextlib.contextmanager
def fixture():
    with tempfile.TemporaryDirectory(prefix="lower-density-work-mock-") as temporary:
        root = Path(temporary).resolve(); bound = root/"bound"; bound.write_text("synthetic")
        frozen = dict(schedule=declared(),variants={"eighth":{"binary":"/never-executed/eighth"}},
                      bound_sha256={str(bound):work.native.sha(bound)})
        freeze=root/"freeze.json";work.write_json(freeze,frozen)
        with mock.patch.object(work,"check_freeze",return_value=frozen):
            yield root,freeze,frozen


def output(spec):
    n,m=spec["n"],spec["m"];q=n//4;r=m-3*n//4;v=n//8;e=m-7*n//8
    rounds=[dict(round=0,vertices=n,edges=m,selected=n-q,output_vertices=q,output_edges=r),
            dict(round=1,vertices=q,edges=r,selected=q-v,output_vertices=v,output_edges=e),
            dict(round=2,vertices=v,edges=e,selected=v-1,output_vertices=0,output_edges=0)]
    algorithms={}
    for name in work.ALGORITHMS:
        counters=dict.fromkeys(work.FIELDS,0)
        counters.update(contraction_calls=3,contraction_vertices=n+q+v,contraction_edges=m+r+e,
            contraction_edge_visits=3*(m+r+e),contraction_output_vertices=q+v,contraction_output_edges=r+e)
        if name=="kkt":
            Q=0 if n==256 else 100+(spec["graph_seed"]==23000029)
            counters.update(kkt_calls=3,root_after_two_vertices=v,root_after_two_edges=e,
                sampling_calls=1,verifier_calls=1,sampling_edge_visits=e,verifier_edges=e,sampled_edges=e//8,
                verifier_queries=Q,path_query_visits=2*Q+Q//2,hash_insert_items=n-1,
                filtered_edges=0 if n==256 else n,initialized_slots=m+spec["graph_seed"]%2)
        else:counters["hash_insert_items"]=None
        algorithms[name]=dict(hash_insert_items_status="measured" if name=="kkt" else "unmeasured",work=counters)
    return dict(schema="retention_control_work_v1",validation="pass",certified_output_items=n-1,
                **{k:v for k,v in spec.items() if k not in ("variant","intrusion_per_mille")},
                algorithms=algorithms,rounds={a:copy.deepcopy(rounds) for a in work.ALGORITHMS[1:]})


class Factory:
    def __init__(self,schedule,mutation=None,status=0,finishes=True,bad_certificate=False,late=False,raw_transform=None):
        self.schedule=schedule;self.mutation=mutation;self.status=status;self.finishes=finishes
        self.bad_certificate=bad_certificate;self.late=late;self.raw_transform=raw_transform;self.children=[]
    def __call__(self,argv,**kwargs):
        spec=self.schedule[len(self.children)]
        assert argv==work.command("/never-executed/eighth",spec) and kwargs["start_new_session"] is True
        value=output(spec);certificate={key:value[key] for key in work.native.CERTIFICATE_FIELDS}
        if self.bad_certificate:certificate["m"]+=1
        if self.mutation:self.mutation(value)
        raw=json.dumps(value);kwargs["stdout"].write((self.raw_transform(raw) if self.raw_transform else raw)+"\n")
        kwargs["stderr"].write(work.native.CERTIFICATE_PREFIX+json.dumps(certificate)+"\n")
        process=old.FakeProcess(71000+len(self.children),self.status,self.finishes)
        if self.late:
            original=process.wait
            def wait(timeout):
                result=original(timeout);work.DEADLINE_SECONDS=-1;return result
            process.wait=wait
        self.children.append(process);return process


def capture(root,freeze,frozen,factory=None,sampler=None,name="capture.json"):
    factory=factory or Factory(frozen["schedule"])
    def provider(group):
        process=next(p for p in factory.children if p.pid==group)
        return dict(process_group=group,members=[]) if process.returncode is not None else old.provider(group)
    sampler=sampler or work.monitor.BoundedSampler(provider,.1)
    work.capture(argparse.Namespace(freeze=freeze,output=root/name,released=True),sampler=sampler,popen=factory)
    return factory


class LowerDensityWorkTests(unittest.TestCase):
    def test_full_parent_entrypoints_audited_timing_binding_and_typed_policy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();workdir=root/"benchmark/results/lower-density-2026-10-15/work"
            workdir.mkdir(parents=True);(workdir/"PROTOCOL.md").write_text("synthetic work protocol")
            parentdir=root/"benchmark/results/eighth-sampling-2026-10-15/work";parentdir.mkdir(parents=True)
            parentfreeze=parentdir/"freeze.json";parentfreeze.write_text("synthetic parent freeze")
            oldcapture=parentdir/"old.json";oldcapture.write_text("synthetic completed parent capture")
            binary=root/"existing-instrumented";binary.write_text("synthetic bytes; never run")
            artifact=dict(binary=str(binary),sampling_policy="eighth",private_acceptance_mask=7,
                          sampling_words_per_visited_edge=1,verifier_policy="compressed")
            inherited=dict(timing_capture=str(oldcapture),variants={"eighth":artifact},
                           bound_sha256={str(binary):work.native.sha(binary)})
            schedule=declared();cases={s["case_id"]:{k:s[k] for k in
                ("case_id","family","n","m","density","intrusion_per_mille")} for s in schedule[:30]}
            rows=[{**s,"phase":phase,"repetition":rep,"order":order,"algorithm":algorithm}
                  for s in schedule for phase,count in (("warmup",1),("timed",6))
                  for rep in range(count) for order,algorithm in enumerate(work.timing.ALGORITHMS)]
            timingfreeze=root/"future-timing-freeze.json";timingfreeze.write_text("synthetic prospective freeze")
            info=dict(captures=[{} for _ in schedule],freeze=str(timingfreeze),freeze_sha256=work.native.sha(timingfreeze),
                      frozen_protocol=dict(parent_freeze_sha256=work.timing.PARENT_SHA256))
            capturepath=workdir.parent/"lower-density.json";work.write_json(capturepath,info)
            auditdir=workdir.parent/"independent-audit-attempt01";auditdir.mkdir(parents=True)
            auditsource=workdir.parent/"validation/independent_numerical_audit.py";auditsource.parent.mkdir()
            auditsource.write_text("synthetic audit")
            auditpath=auditdir/"audit.json"
            report=dict(schema="independent_lower_density_numerical_audit_v1",validation="pass",collector_imported=False,
                raw_native_children=60,checked_outputs=2520,timed_outputs=2160,warmup_outputs=360,
                matched_topology_twins=30,certificates=60,owned_groups_verified_empty=60,
                strict_analyzer_pairs_medians_ranges_counts_agree=True,
                table_counts={**work.timing.TABLE_COUNTS,"crossover_points":150,"crossover_brackets":490,"crossover_summary":20},
                supplied_freeze=str(timingfreeze),supplied_freeze_sha256=info["freeze_sha256"],
                input_sha256={str(capturepath):work.native.sha(capturepath),str(auditsource):work.native.sha(auditsource)})
            work.write_json(auditpath,report)
            before=(work.parent.timing.GRAPH_SEEDS,work.parent.timing.SAMPLING_SEEDS,work.timing.GRAPH_SEEDS)
            with mock.patch.multiple(work,ROOT=root,WORK=workdir,PARENT_WORK=parentdir),\
                 mock.patch.object(work.parent,"check_freeze",return_value=inherited) as proof,\
                 mock.patch.object(work.parent.timing,"load",return_value=({"freeze_sha256":work.timing.PARENT_SHA256},None,None,None,None,None)) as oldload,\
                 mock.patch.object(work.timing,"load",return_value=(info,cases,rows,[],[],{})) as newload,\
                 mock.patch.object(work.timing,"helpers",return_value={}):
                args=(capturepath,auditpath,parentfreeze,work.native.sha(parentfreeze))
                got,actual,paths=work.provenance(*args)
                self.assertEqual(got,artifact);self.assertEqual(actual,schedule)
                proof.assert_called_once_with(parentfreeze);oldload.assert_called_once_with(oldcapture);newload.assert_called_once_with(capturepath)
                self.assertEqual(before,(work.parent.timing.GRAPH_SEEDS,work.parent.timing.SAMPLING_SEEDS,work.timing.GRAPH_SEEDS))
                for field,value in (("private_acceptance_mask",1),("sampling_words_per_visited_edge",True),("verifier_policy","original")):
                    changed=copy.deepcopy(inherited);changed["variants"]["eighth"][field]=value
                    with mock.patch.object(work.parent,"check_freeze",return_value=changed),self.assertRaisesRegex(ValueError,"policy"):
                        work.provenance(*args)
                for field,value in (("checked_outputs",2521),("validation","failed"),("supplied_freeze_sha256","0"*64)):
                    changed=copy.deepcopy(report);changed[field]=value;work.write_json(auditpath,changed)
                    with self.assertRaises(ValueError):work.provenance(*args)
                changed=copy.deepcopy(report);changed["input_sha256"].pop(str(capturepath));work.write_json(auditpath,changed)
                with self.assertRaisesRegex(ValueError,"bind timing"):work.provenance(*args)
                work.write_json(auditpath,report)
                with mock.patch.object(work.parent,"check_freeze",side_effect=ValueError("full parent rejected")),self.assertRaisesRegex(ValueError,"full parent"):
                    work.provenance(*args)
                original_read=work.analysis.read_json
                def drifting_audit(path):
                    result=original_read(path)
                    if Path(path)==auditpath:Path(path).write_text(Path(path).read_text()+" ")
                    return result
                with mock.patch.object(work.analysis,"read_json",side_effect=drifting_audit),self.assertRaises(ValueError):
                    work.provenance(*args)
                work.write_json(auditpath,report)
                binary.write_text("drift")
                with self.assertRaises(ValueError):work.provenance(*args)

    def test_full_60_matrix_exact_11700_normalizations_and_zero_queries(self):
        with fixture() as (root,freeze,frozen):
            factory=capture(root,freeze,frozen);info,values=work.load(root/"capture.json")
            self.assertEqual((len(factory.children),len(values),info["checked_solver_outputs"]),(60,60,180))
            self.assertEqual([s for s,v in values],declared())
            tables=work.tables(values)
            self.assertEqual({k:len(v) for k,v in tables.items()},
                             dict(work=180,rounds=360,round_chains=120,query_work=60,normalized_work=11700))
            raw={(s["case_id"],s["graph_seed"],a):v["algorithms"][a]["work"] for s,v in values for a in work.ALGORITHMS}
            seen=set();null=0
            for row in tables["normalized_work"]:
                key=row["case_id"],row["graph_seed"],row["algorithm"],row["counter"]
                self.assertNotIn(key,seen);seen.add(key)
                count=raw[key[:3]][key[3]];self.assertEqual(row["count"],count)
                if count is None:
                    null+=1;self.assertEqual((row["status"],row["numerator"],row["denominator"],row["per_original_edge"]),
                                             ("unmeasured",None,None,None))
                else:
                    exact=Fraction(count,row["m"])
                    self.assertEqual((row["status"],row["numerator"],row["denominator"],row["per_original_edge"]),
                                     ("defined",exact.numerator,exact.denominator,float(exact)))
            self.assertEqual((len(seen),null),(11700,120))
            self.assertTrue(any(r["query_fraction_status"]=="both_zero" for r in tables["query_work"]))
            self.assertTrue(all(r["engine_words"]==r["sampling_edge_visits"] for r in tables["query_work"]))
            work.summarize(argparse.Namespace(capture=root/"capture.json",output_dir=root/"analysis"))
            with self.assertRaisesRegex(ValueError,"overwrite"):capture(root,freeze,frozen)

    def test_schema_counter_certificate_root_and_replay_failures_stop_one(self):
        mutations=(lambda v:v.update(schema="wrong"),lambda v:v.update(n=True),lambda v:v.update(input_fingerprint=0),
            lambda v:v["algorithms"]["kkt"]["work"].pop("sampled_edges"),
            lambda v:v["algorithms"]["kkt"]["work"].update(sampled_edges=True),
            lambda v:v["algorithms"]["kkt"]["work"].update(path_query_visits=0),
            lambda v:v["algorithms"]["kkt"]["work"].update(initialized_slots=2**64),
            lambda v:v["rounds"]["multigraph_boruvka"][0].update(selected=0),
            lambda v:v.update(certified_output_items=1))
        for mutation in mutations:
            with fixture() as (root,freeze,frozen):
                factory=Factory(frozen["schedule"],mutation=mutation)
                with self.assertRaises(ValueError):capture(root,freeze,frozen,factory)
                self.assertEqual(len(factory.children),1)
                self.assertEqual(work.analysis.read_json(root/"capture.json")["validation"],"failed")
        for options in (dict(bad_certificate=True),dict(raw_transform=lambda raw:raw[:-1]),
                        dict(raw_transform=lambda raw:raw[:-1]+',"validation":"pass"}')):
            with fixture() as (root,freeze,frozen):
                factory=Factory(frozen["schedule"],**options)
                with self.assertRaises(ValueError):capture(root,freeze,frozen,factory)
                self.assertEqual(len(factory.children),1)
        # Consistently change both root counters and retained replay: the new
        # distance-only dimensions must still reject an inherited-valid shape.
        spec=declared()[0];value=output(spec);value["algorithms"]["kkt"]["work"]["root_after_two_edges"]-=1
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/"raw.json";work.write_json(path,value)
            with mock.patch.object(work.parent,"check_output",return_value=value),self.assertRaisesRegex(ValueError,"exact two-step"):
                work.check_output(path,spec)

    def test_all_twins_duplicate_density_and_positive_witness(self):
        values=[(s,output(s)) for s in declared()];work.complete(values)
        for changed in (values[:-1],values[:-1]+[values[0]]):
            with self.assertRaisesRegex(ValueError,"matrix"):work.complete(changed)
        for key in ("topology_fingerprint","input_fingerprint"):
            changed=copy.deepcopy(values);changed[1][1][key]=changed[0][1][key]+(1 if key.startswith("topology") else 0)
            with self.assertRaises(ValueError):work.complete(changed)
        zero=copy.deepcopy(values)
        for spec,value in zero:value["algorithms"]["kkt"]["work"].update(verifier_queries=0,path_query_visits=0)
        with self.assertRaisesRegex(ValueError,"positive query"):work.complete(zero)
        with fixture() as (root,freeze,frozen):
            factory=Factory(frozen["schedule"],mutation=lambda v:v["algorithms"]["kkt"]["work"].update(verifier_queries=0,path_query_visits=0))
            with self.assertRaisesRegex(ValueError,"positive query"):capture(root,freeze,frozen,factory)
            failed=work.analysis.read_json(root/"capture.json")
            self.assertEqual((len(factory.children),failed["validation"]),(60,"failed"))

    def test_deadline_postwait_and_strict_reload(self):
        with fixture() as (root,freeze,frozen):
            factory=Factory(frozen["schedule"],late=True)
            with mock.patch.object(work,"DEADLINE_SECONDS",1800),self.assertRaisesRegex(ValueError,"exit exceeded deadline"):
                capture(root,freeze,frozen,factory)
            self.assertEqual(len(factory.children),1)
        with fixture() as (root,freeze,frozen):
            clock=work.time.monotonic_ns
            with mock.patch.object(work.time,"monotonic_ns",side_effect=lambda:clock()+3600*10**9):capture(root,freeze,frozen)
            path=root/"capture.json";info=work.analysis.read_json(path);child=info["captures"][0]
            child["started_monotonic_ns"]=child["wrapper_exit_monotonic_ns"]-1800*10**9-1
            child["monotonic_elapsed_seconds"]=(child["finished_monotonic_ns"]-child["started_monotonic_ns"])/1e9
            info["started_monotonic_ns"]=child["started_monotonic_ns"]-1;work.write_json(path,info)
            with self.assertRaisesRegex(ValueError,"exit exceeded deadline"):work.load(path)

    def test_resource_unknown_exit_poison_and_bound_source_stop(self):
        for mode in ("ceiling","unavailable","unknown","crash"):
            with fixture() as (root,freeze,frozen):
                factory=Factory(frozen["schedule"],status=-11 if mode=="crash" else 0,finishes=mode!="unavailable")
                def provider(group):
                    if mode=="unavailable":raise OSError("synthetic")
                    result=old.provider(group)
                    if mode=="ceiling":result["members"][0]["rss_kib"]=work.RULE["rss_limit_kib"]+1
                    return result
                with mock.patch.object(work.monitor,"bounded_terminate",return_value=dict(native_process_may_still_be_running=True)),self.assertRaises(ValueError):
                    capture(root,freeze,frozen,factory,work.monitor.BoundedSampler(provider,.1))
                self.assertEqual(len(factory.children),1)
                self.assertTrue(work.analysis.read_json(root/"capture.json")["native_process_may_still_be_running"])
        with fixture() as (root,freeze,frozen):
            gate=threading.Event();factory=Factory(frozen["schedule"])
            sampler=work.monitor.BoundedSampler(lambda group:(gate.wait(),old.provider(group))[1],.01)
            try:
                with mock.patch.object(work.monitor,"bounded_terminate",return_value=dict(native_process_may_still_be_running=True)),self.assertRaises(ValueError):
                    capture(root,freeze,frozen,factory,sampler)
                second=Factory(frozen["schedule"])
                with self.assertRaisesRegex(ValueError,"poisoned"):capture(root,freeze,frozen,second,sampler,"second.json")
                self.assertEqual((len(factory.children),len(second.children),sampler.workers_started),(1,0,1))
            finally:gate.set()
        with fixture() as (root,freeze,frozen):
            Path(next(iter(frozen["bound_sha256"]))).write_text("drift")
            factory=Factory(frozen["schedule"])
            with self.assertRaises(ValueError):capture(root,freeze,frozen,factory)
            self.assertFalse(factory.children)

    def test_cleanup_interrupt_and_terminal_load_failure_are_retained(self):
        prior=signal.getsignal(signal.SIGTERM)
        with fixture() as (root,freeze,frozen):
            def cleanup(*args):
                self.assertEqual(signal.getsignal(signal.SIGTERM),signal.SIG_IGN)
                raise KeyboardInterrupt("synthetic cleanup interruption")
            factory=Factory(frozen["schedule"],status=-11)
            with mock.patch.object(work.monitor,"bounded_terminate",side_effect=cleanup),self.assertRaises(ValueError):
                capture(root,freeze,frozen,factory)
            info=work.analysis.read_json(root/"capture.json")
            self.assertTrue(info["native_process_may_still_be_running"])
            self.assertEqual(len(info["cleanup"]),1);self.assertEqual(signal.getsignal(signal.SIGTERM),prior)
        with fixture() as (root,freeze,frozen):
            with mock.patch.object(work,"load",side_effect=ValueError("final load rejected")),self.assertRaisesRegex(ValueError,"final load"):
                capture(root,freeze,frozen)
            self.assertEqual(work.analysis.read_json(root/"capture.json")["validation"],"failed")

    def test_analysis_rechecks_capture_and_raw_hashes(self):
        with fixture() as (root,freeze,frozen):
            capture(root,freeze,frozen);original=work.load
            def changing(path):
                result=original(path);path.write_text(path.read_text()+" ");return result
            with mock.patch.object(work,"load",side_effect=changing),self.assertRaises(ValueError):
                work.summarize(argparse.Namespace(capture=root/"capture.json",output_dir=root/"analysis"))
        with fixture() as (root,freeze,frozen):
            capture(root,freeze,frozen);info=work.analysis.read_json(root/"capture.json")
            raw=Path(info["captures"][0]["raw"]);raw.write_text(raw.read_text()+" ")
            with self.assertRaises(ValueError):work.load(root/"capture.json")

    def test_plot_canonical_full_matrix_and_mutations_without_rendering(self):
        spec=importlib.util.spec_from_file_location("lower_density_work_plot_under_test",HERE/"plot_work.py")
        plot=importlib.util.module_from_spec(spec);spec.loader.exec_module(plot)
        with fixture() as (root,freeze,frozen),mock.patch.object(plot,"work",work):
            capture(root,freeze,frozen);directory=root/"analysis"
            work.summarize(argparse.Namespace(capture=root/"capture.json",output_dir=directory))
            _,_,counts,rounds,queries=plot.prepare(root/"capture.json",directory)
            self.assertEqual((len(counts),len(rounds),len(queries)),(1440,120,60))
            self.assertEqual({r["counter"] for r in counts},set(work.SELECTED_FIELDS))
            self.assertEqual({(r["family"],r["density"]) for r in counts},
                             {(f,d) for f in ("leaf_distance4","leaf_shuffled4") for d in (8,16)})
            path=directory/"normalized_work.csv";original=path.read_bytes()
            for mode in ("value","missing"):
                path.write_bytes(original)
                with path.open(newline="") as stream:rows=list(csv.DictReader(stream))
                if mode=="missing":rows.pop()
                else:rows[0]["count"]=str(int(rows[0]["count"])+1)
                work.analysis.write_csv(path,rows)
                with self.subTest(mode=mode),self.assertRaisesRegex(ValueError,"canonical table"):
                    plot.prepare(root/"capture.json",directory)
            path.write_bytes(original)
            original_read=work.analysis.read_json
            def drifting_analysis(path):
                result=original_read(path)
                if Path(path)==directory/"provenance.json":Path(path).write_text(Path(path).read_text()+" ")
                return result
            with mock.patch.object(work.analysis,"read_json",side_effect=drifting_analysis),self.assertRaises(ValueError):
                plot.prepare(root/"capture.json",directory)


if __name__=="__main__":unittest.main(verbosity=2)
