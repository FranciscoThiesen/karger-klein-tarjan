#!/usr/bin/env python3
"""SOURCE ONLY until timing release: focused mocked work-capture gates.

No native binary is launched. Capture/lifecycle fixtures replace only the
already separately validated provenance entry point and use real raw parsers,
resource checks, command/row checks and aggregation. Recipe negatives test the
actual exact-command checker using the existing instrumented build receipt.
"""
import argparse
import contextlib
import copy
import csv
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "benchmark"))
spec = importlib.util.spec_from_file_location("compressed_work_under_test", HERE / "collect.py")
work = importlib.util.module_from_spec(spec); spec.loader.exec_module(work)
import test_compressed_queries as timing_tests
old = timing_tests.old


@contextlib.contextmanager
def fixture():
    with tempfile.TemporaryDirectory(prefix="compressed-work-mock-") as directory:
        root = Path(directory)
        cases = {}
        for family, n, density in (("leaf_hierarchy4", 65536, 32), ("leaf_shuffled4", 65536, 32),
                                   ("leaf_hierarchy4", 1048576, 32), ("leaf_shuffled4", 1048576, 32),
                                   ("gnm_random", 4096, 16), ("gnm_random", 1048576, 16)):
            case = f"{family}_n{n}_d{density}_p0"
            cases[case] = dict(case_id=case, family=family, n=n, density=density, intrusion_per_mille=0, m=n*density)
        schedule = [{**identity, **cases[identity["case_id"]],
                     "input_fingerprint": 10 if cases[identity["case_id"]]["family"] == "leaf_shuffled4" else 9,
                     "topology_fingerprint": 7} for identity in work.timing.schedule(cases)]
        bound = root / "bound.txt"; bound.write_text("synthetic bound source")
        frozen = dict(schedule=schedule, variants={variant: {"binary": "/never-executed/" + variant}
                      for variant in work.timing.VARIANTS}, bound_sha256={str(bound): work.native.sha(bound)})
        freeze = root / "freeze.json"; work.write_json(freeze, frozen)
        with mock.patch.object(work, "check_freeze", return_value=frozen):
            yield root, freeze, frozen


def output_for(spec, variant):
    n, m = spec["n"], spec["m"]
    rounds = [dict(round=0, vertices=n, edges=m, selected=n//2, output_vertices=n//2, output_edges=m//2),
              dict(round=1, vertices=n//2, edges=m//2, selected=n//4, output_vertices=n//4, output_edges=m//4),
              dict(round=2, vertices=n//4, edges=m//4, selected=n//4-1, output_vertices=0, output_edges=0)]
    algorithms = {}
    for name in work.ALGORITHMS:
        counters = dict.fromkeys(work.FIELDS, 0)
        counters.update(contraction_calls=3, contraction_vertices=n+n//2+n//4,
                        contraction_edges=m+m//2+m//4, contraction_edge_visits=3*(m+m//2+m//4),
                        contraction_output_vertices=n//2+n//4, contraction_output_edges=m//2+m//4)
        if name == "kkt":
            counters.update(kkt_calls=3, root_after_two_vertices=n//4, root_after_two_edges=m//4,
                            sampling_calls=1, verifier_calls=1, sampling_edge_visits=m//4, verifier_edges=m//4,
                            sampled_edges=m//8, hash_insert_items=n-1)
            q, u, tree_edges, tree_calls, tree_vertices = m//2, n//4, m//4, 2, n
            counters.update(verifier_queries=q, verifier_tree_edges=tree_edges, verifier_tree_calls=tree_calls,
                            fbt_output_vertices=tree_vertices, path_query_visits=4*q,
                            initialized_slots=10*m, verifier_edge_visits=5*m, verifier_vertex_visits=3*n)
            if variant == "compressed":
                counters.update(path_query_visits=2*q+u, initialized_slots=10*m-tree_edges-q+u-tree_calls,
                                verifier_edge_visits=5*m-tree_edges, verifier_vertex_visits=3*n+tree_vertices)
        else: counters["hash_insert_items"] = None
        algorithms[name] = dict(hash_insert_items_status="measured" if name == "kkt" else "unmeasured", work=counters)
    return {"schema": "retention_control_work_v1", "validation": "pass",
            **{k: v for k, v in spec.items() if k not in ("variant", "intrusion_per_mille")},
            "certified_output_items": n-1, "algorithms": algorithms,
            "rounds": {name: copy.deepcopy(rounds) for name in work.ALGORITHMS[1:]}}


class Factory:
    def __init__(self, schedule, mutation=None, bad_certificate=False, status=0, finishes=True, late=False,
                 raw_transform=None):
        self.schedule, self.mutation, self.bad_certificate = schedule, mutation, bad_certificate
        self.status, self.finishes, self.late = status, finishes, late
        self.raw_transform = raw_transform
        self.children = []

    def __call__(self, argv, **kwargs):
        spec = self.schedule[len(self.children)]
        assert argv == work.command("/never-executed/" + spec["variant"], spec)
        value = output_for(spec, spec["variant"])
        certificate = {k: value[k] for k in work.native.CERTIFICATE_FIELDS}
        if self.bad_certificate: certificate["m"] += 1
        if self.mutation: self.mutation(value)
        raw = json.dumps(value)
        kwargs["stdout"].write((self.raw_transform(raw) if self.raw_transform else raw) + "\n")
        kwargs["stderr"].write(work.native.CERTIFICATE_PREFIX + json.dumps(certificate) + "\n")
        process = old.FakeProcess(67000 + len(self.children), self.status, self.finishes)
        if self.late:
            original_wait = process.wait
            def wait(timeout):
                result = original_wait(timeout)
                # Make the elapsed native-exit budget negative immediately after
                # wait returns, without sleeping or touching the host clock.
                work.DEADLINE_SECONDS = -1
                return result
            process.wait = wait
        self.children.append(process)
        return process


def capture(root, freeze, frozen, factory=None, sampler=None, name="capture.json"):
    factory = factory if factory is not None else Factory(frozen["schedule"])
    def provider(group):
        process = next(p for p in factory.children if p.pid == group)
        return {"process_group": group, "members": []} if process.returncode is not None else old.provider(group)
    sampler = sampler if sampler is not None else work.monitor.BoundedSampler(provider, .1)
    work.capture(argparse.Namespace(freeze=freeze, output=root/name, released=True), sampler=sampler, popen=factory)
    return factory


class WorkCollectorTests(unittest.TestCase):
    def test_complete_24_matrix_and_zero_preserving_summaries(self):
        with fixture() as (root, freeze, frozen):
            cases = list(dict.fromkeys(spec["case_id"] for spec in frozen["schedule"]))
            expected_schedule = [(variant, case, graph, 1801)
                for index, graph in enumerate((8000009,8000023))
                for case in (cases if index == 0 else list(reversed(cases)))
                for variant in (("reference","compressed") if index == 0 else ("compressed","reference"))]
            self.assertEqual([tuple(spec[key] for key in ("variant","case_id","graph_seed","kkt_seed"))
                              for spec in frozen["schedule"]], expected_schedule)
            factory = capture(root, freeze, frozen)
            info, values = work.load(root/"capture.json")
            self.assertEqual((len(factory.children), len(values), info["checked_solver_outputs"]), (24,24,72))
            self.assertTrue(all(child.returncode == 0 for child in factory.children))
            work.summarize(argparse.Namespace(capture=root/"capture.json", output_dir=root/"analysis"))
            with (root/"analysis/paired_kkt_work.csv").open(newline="") as stream:
                pairs = list(csv.DictReader(stream))
            self.assertEqual(len(pairs), 780)
            self.assertEqual(sum(row["ratio_status"] == "both_zero" for row in pairs if row["counter"] == "current_depth"), 12)
            indexed = {(row["case_id"],int(row["graph_seed"]),int(row["kkt_seed"]),row["counter"]):row for row in pairs}
            expected_ids = {(case,graph,1801,field) for case in cases for graph in (8000009,8000023) for field in work.FIELDS}
            self.assertEqual(len(indexed),len(pairs)); self.assertEqual(set(indexed),expected_ids)
            for spec in frozen["schedule"]:
                if spec["variant"] != "reference": continue
                first = output_for(spec,"reference")["algorithms"]["kkt"]["work"]
                second = output_for(spec,"compressed")["algorithms"]["kkt"]["work"]
                for field in work.FIELDS:
                    row = indexed[(spec["case_id"],spec["graph_seed"],1801,field)]
                    a,b = first[field],second[field]
                    self.assertEqual((int(row["reference"]),int(row["compressed"]),int(row["compressed_minus_reference"])),(a,b,b-a))
                    self.assertEqual(float(row["delta_per_original_edge"]),(b-a)/spec["m"])
                    self.assertEqual(float(row["reference_per_original_edge"]),a/spec["m"])
                    self.assertEqual(float(row["compressed_per_original_edge"]),b/spec["m"])
                    if a: self.assertEqual(float(row["compressed_over_reference"]),b/a)
                    else: self.assertEqual(row["compressed_over_reference"],"")
            with (root/"analysis/query_compression.csv").open(newline="") as stream:
                queries = list(csv.DictReader(stream))
            self.assertEqual(len(queries),12)
            query_ids = {(row["case_id"],int(row["graph_seed"]),int(row["kkt_seed"])) for row in queries}
            self.assertEqual(query_ids,{(case,graph,1801) for case in cases for graph in (8000009,8000023)})
            for row in queries:
                n,m = int(row["n"]),int(row["m"])
                self.assertEqual(tuple(int(row[k]) for k in ("Q","U","M","T","Nsum")),(m//2,n//4,m//4,2,n))
                self.assertEqual(int(row["initialized_slots_saved"]),3*m//4-n//4+2)
                self.assertEqual(int(row["path_query_visits_saved"]),m-n//4)
                self.assertEqual(float(row["U_over_Q"]),(n//4)/(m//2))
                self.assertEqual(float(row["initialized_slots_saved_per_original_edge"]),(3*m//4-n//4+2)/m)
            with self.assertRaisesRegex(ValueError, "overwrite"): capture(root, freeze, frozen)

    def test_output_schema_counters_certificate_and_fingerprint_fail_closed(self):
        mutations = (lambda x: x.update(schema="wrong"),
                     lambda x: x["algorithms"]["kkt"]["work"].pop("sampled_edges"),
                     lambda x: x["algorithms"]["kkt"]["work"].update(sampled_edges=True),
                     lambda x: x.update(input_fingerprint=999),
                     lambda x: x.update(certified_output_items=1))
        for mutation in mutations:
            with fixture() as (root, freeze, frozen):
                factory = Factory(frozen["schedule"], mutation=mutation)
                with self.assertRaises(ValueError): capture(root, freeze, frozen, factory)
                self.assertEqual(len(factory.children), 1)
                self.assertEqual(work.analysis.read_json(root/"capture.json")["validation"], "failed")
        with fixture() as (root, freeze, frozen):
            factory = Factory(frozen["schedule"], bad_certificate=True)
            with self.assertRaisesRegex(ValueError, "certificate"): capture(root, freeze, frozen, factory)
            self.assertEqual(len(factory.children), 1)
        for transform in (lambda raw: raw[:-1],
                          lambda raw: raw[:-1] + ', "validation": "pass"}',
                          lambda raw: raw[:-1] + ', "not_finite": NaN}'):
            with fixture() as (root, freeze, frozen):
                factory = Factory(frozen["schedule"], raw_transform=transform)
                with self.assertRaises(ValueError): capture(root, freeze, frozen, factory)
                self.assertEqual(len(factory.children), 1)

    def test_comparator_change_stops_before_next_child(self):
        with fixture() as (root, freeze, frozen):
            calls = [0]
            def mutate(value):
                calls[0] += 1
                if calls[0] == 2: value["algorithms"]["compacting_boruvka"]["work"]["initialized_slots"] = 1
            factory = Factory(frozen["schedule"], mutation=mutate)
            with self.assertRaisesRegex(ValueError, "comparator"): capture(root, freeze, frozen, factory)
            self.assertEqual(len(factory.children), 2)

    def test_late_native_exit_and_consistent_reload_rejected(self):
        with fixture() as (root, freeze, frozen):
            factory = Factory(frozen["schedule"], late=True)
            with mock.patch.object(work, "DEADLINE_SECONDS", 1800):
                with self.assertRaisesRegex(ValueError, "exit exceeded deadline"): capture(root, freeze, frozen, factory)
            self.assertEqual(len(factory.children), 1)
        with fixture() as (root, freeze, frozen):
            # Keep this independent of machine uptime. Every recorded monotonic
            # source (including the monitor thread) receives the same offset.
            original_clock = work.time.monotonic_ns
            with mock.patch.object(work.time, "monotonic_ns", side_effect=lambda: original_clock()+3600*10**9):
                capture(root, freeze, frozen)
            # Alter the first start consistently, preserving child/resource order,
            # durations and all raw hashes. Only the native-exit deadline is false.
            path = root/"capture.json"; info = work.analysis.read_json(path)
            child = info["captures"][0]
            child["started_monotonic_ns"] = child["wrapper_exit_monotonic_ns"] - (1800*10**9 + 1)
            child["monotonic_elapsed_seconds"] = (child["finished_monotonic_ns"]-child["started_monotonic_ns"])/1e9
            info["started_monotonic_ns"] = child["started_monotonic_ns"] - 1
            work.write_json(path, info)
            with self.assertRaisesRegex(ValueError, "exit exceeded deadline"): work.load(path)

    def test_reload_rejects_malformed_resource_evidence(self):
        with fixture() as (root, freeze, frozen):
            capture(root, freeze, frozen)
            path = root/"capture.json"; original = work.analysis.read_json(path)
            child = original["captures"][0]; rss = Path(child["rss_log"])
            lines = [json.loads(line) for line in rss.read_text().splitlines()]
            for mutate in (lambda rows: rows[0].update(rss_kib=True),
                           lambda rows: rows[-1].update(process_group=child["process_group"]+1),
                           lambda rows: rows[-1].update(members=[{"pid": child["process_group"],
                                                                 "rss_kib": 0, "command": "synthetic-only"}])):
                changed = copy.deepcopy(lines); mutate(changed)
                rss.write_text("".join(json.dumps(row)+"\n" for row in changed))
                info = copy.deepcopy(original)
                info["captures"][0]["rss_sha256"] = work.native.sha(rss)
                work.write_json(path, info)
                with self.assertRaises(ValueError): work.load(path)

    def test_resource_and_unknown_exit_never_launch_second_child(self):
        for failure in ("ceiling", "unavailable", "unknown exit", "crash"):
            with fixture() as (root, freeze, frozen):
                factory = Factory(frozen["schedule"], status=-11 if failure == "crash" else 0,
                                  finishes=failure != "unavailable")
                def provider(group):
                    if failure == "unavailable": raise OSError("mock unavailable")
                    result = old.provider(group)
                    if failure == "ceiling": result["members"][0]["rss_kib"] = work.RULE["rss_limit_kib"]+1
                    return result
                sampler = work.monitor.BoundedSampler(provider, .1)
                with mock.patch.object(work.monitor, "bounded_terminate", return_value={"native_process_may_still_be_running": True}):
                    with self.assertRaises(ValueError): capture(root, freeze, frozen, factory, sampler)
                self.assertEqual(len(factory.children), 1)
                self.assertTrue(work.analysis.read_json(root/"capture.json")["native_process_may_still_be_running"])

    def test_poison_and_bound_hash_forbid_launch(self):
        with fixture() as (root, freeze, frozen):
            gate = threading.Event(); factory = Factory(frozen["schedule"])
            sampler = work.monitor.BoundedSampler(lambda group: (gate.wait(), old.provider(group))[1], .01)
            try:
                with mock.patch.object(work.monitor, "bounded_terminate", return_value={"native_process_may_still_be_running": True}):
                    with self.assertRaisesRegex(ValueError, "timed out"): capture(root, freeze, frozen, factory, sampler)
                second = Factory(frozen["schedule"])
                with self.assertRaisesRegex(ValueError, "poisoned"): capture(root, freeze, frozen, second, sampler, "second.json")
                self.assertFalse(second.children)
            finally: gate.set()
        with fixture() as (root, freeze, frozen):
            (root/"bound.txt").write_text("drift")
            factory = Factory(frozen["schedule"])
            with self.assertRaisesRegex(ValueError, "hash mismatch"): capture(root, freeze, frozen, factory)
            self.assertFalse(factory.children)
            with self.assertRaisesRegex(ValueError, "released"):
                work.capture(argparse.Namespace(freeze=freeze, output=root/"unreleased.json", released=False))

    def test_all_four_identities_and_unchanged_fields_fail_closed(self):
        for field in ("initialized_slots","path_query_visits","verifier_edge_visits","verifier_vertex_visits",
                      "sampled_edges","verifier_queries","sampling_calls","path_init_vertices"):
            with self.subTest(field=field), fixture() as (root, freeze, frozen):
                calls = [0]
                def mutate(value):
                    calls[0] += 1
                    if calls[0] == 2: value["algorithms"]["kkt"]["work"][field] += 1
                factory = Factory(frozen["schedule"], mutation=mutate)
                with self.assertRaises(ValueError): capture(root,freeze,frozen,factory)
                self.assertEqual(len(factory.children),2)
                self.assertEqual(work.analysis.read_json(root/"capture.json")["validation"],"failed")

    def test_query_algebra_boundaries_and_wrong_dispatch(self):
        for q,u,m,t,n in ((0,0,0,0,0),(0,0,4,2,8),(1,1,1,1,3),(17,0,11,3,20),(17,17,11,3,20),(24,4,12,1,7)):
            first = dict.fromkeys(work.FIELDS,0)
            first.update(verifier_queries=q,verifier_tree_edges=m,verifier_tree_calls=t,fbt_output_vertices=n,
                         initialized_slots=1000,path_query_visits=4*q,verifier_edge_visits=100,verifier_vertex_visits=100)
            second = {**first,"initialized_slots":1000-m-q+u-t,"path_query_visits":2*q+u,
                      "verifier_edge_visits":100-m,"verifier_vertex_visits":100+n}
            result = work.query_diagnostics(first,second)
            self.assertEqual((result["Q"],result["U"],result["M"],result["T"],result["Nsum"]),(q,u,m,t,n))
            self.assertEqual(result["U_over_Q"],u/q if q else None)
            for bad_u in (-1,q+1):
                changed = {**second,"path_query_visits":2*q+bad_u}
                with self.assertRaisesRegex(ValueError,"derived U"): work.query_diagnostics(first,changed)
            if q:
                with self.assertRaisesRegex(ValueError,"derived U"): work.query_diagnostics(first,first)
                changed = {**first,"path_query_visits":4*q+1}
                with self.assertRaisesRegex(ValueError,"4Q"): work.query_diagnostics(changed,second)

    def test_exact_instrumented_recipe_rejects_later_overwrite(self):
        path = HERE.parent/"validation/native-correctness-compressed-build-record.json"
        record = work.analysis.read_json(path)
        work.check_instrumented_recipe(record, ROOT)
        self.assertEqual(len(record["build_commands"]),36)
        self.assertEqual(len(record["executables"]),9)
        commands=record["build_commands"]
        flagged=[index for index,command in enumerate(commands) if "-DKKT_EXPERIMENT_COMPRESSED_QUERIES" in command]
        self.assertEqual(flagged,[8])
        self.assertIn("kkt/kkt.cpp",commands[6]); self.assertNotIn("-DKKT_EXPERIMENT_COMPRESSED_QUERIES",commands[6])
        for mutation in (lambda x:x["build_commands"].append(list(x["build_commands"][8])),
                         lambda x:x["build_commands"][8].remove("-DKKT_EXPERIMENT_COMPRESSED_QUERIES"),
                         lambda x:x["build_commands"][6].insert(3,"-DKKT_EXPERIMENT_PACKED_SAMPLING"),
                         lambda x:x["executables"][-1].update(role="correctness"),
                         lambda x:x["executables"][-1]["link_command"].insert(3,"-DNDEBUG")):
            changed=copy.deepcopy(record); mutation(changed)
            with self.assertRaises(ValueError): work.check_instrumented_recipe(changed,ROOT)

    def test_actual_build_provenance_and_mutation_rejection(self):
        # Bind real existing build artifacts without executing binaries. Only
        # the not-yet-existing completed timing capture is substituted here.
        with fixture() as (_,freeze,frozen):
            read=work.analysis.read_json
            builds={variant:read(HERE.parent/"validation"/("timing-build-"+variant+"-build-record.json"))
                    for variant in ("reference","compressed")}
            sources=builds["reference"]["source_sha256"]
            info={"frozen_protocol":{"source_sha256":sources,"variants":{
                variant:{"build":{"record":record}} for variant,record in builds.items()}}}
            cases={spec["case_id"]:{k:spec[k] for k in ("case_id","family","n","m","density","intrusion_per_mille")}
                   for spec in frozen["schedule"]}
            timing_rows=list(frozen["schedule"])
            loaded=(info,cases,timing_rows,[],[],{})
            with mock.patch.object(work.timing,"load",return_value=loaded):
                variants,schedule,paths=work.provenance(Path("synthetic-timing-capture.json"))
                self.assertEqual((set(variants),len(schedule)),({"reference","compressed"},24))
                self.assertEqual(paths[str(ROOT/work.SOURCE)],"ae08c5d199d83668d81f41a573452fea099c7e7cd5bd9bb4807c4a8ba9120e25")
                record_path=HERE.parent/"validation/native-correctness-compressed-build-record.json"
                original=read(record_path)
                for mutation in (lambda x:x.update(scalar_sampling_fixed=False),
                                 lambda x:x.update(reference_source_textually_unchanged=False),
                                 lambda x:x.update(seven_non_verifier_objects_identical_by_construction=False),
                                 lambda x:x.update(work_driver_sha256="0"*64),
                                 lambda x:x.update(base_commit="0"*40),
                                 lambda x:x["object_sha256"].update({"kkt/kkt.o":"0"*64}),
                                 lambda x:x["executables"][-1].update(binary_sha256="0"*64),
                                 lambda x:x["build_command"].append("--unrecorded-override")):
                    changed=copy.deepcopy(original); mutation(changed)
                    def substitute(path): return changed if Path(path)==record_path else read(path)
                    with mock.patch.object(work.analysis,"read_json",side_effect=substitute),self.assertRaises(ValueError):
                        work.provenance(Path("synthetic-timing-capture.json"))


if __name__ == "__main__": unittest.main(verbosity=2)
