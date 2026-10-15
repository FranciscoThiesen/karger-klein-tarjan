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
import itertools
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
spec = importlib.util.spec_from_file_location("packed_work_under_test", HERE / "collect.py")
work = importlib.util.module_from_spec(spec); spec.loader.exec_module(work)
import test_packed_sampling as timing_tests
old = timing_tests.old


@contextlib.contextmanager
def fixture():
    with tempfile.TemporaryDirectory(prefix="packed-work-mock-") as directory:
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
                            sampled_edges=m//8+(variant == "packed")+(spec["kkt_seed"] == 1613), hash_insert_items=n-1)
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
    def test_complete_48_matrix_and_zero_preserving_summaries(self):
        with fixture() as (root, freeze, frozen):
            factory = capture(root, freeze, frozen)
            info, values = work.load(root/"capture.json")
            self.assertEqual((len(factory.children), len(values), info["checked_solver_outputs"]), (48,48,144))
            self.assertTrue(all(child.returncode == 0 for child in factory.children))
            work.summarize(argparse.Namespace(capture=root/"capture.json", output_dir=root/"analysis"))
            with (root/"analysis/paired_kkt_work.csv").open(newline="") as stream:
                pairs = list(csv.DictReader(stream))
            self.assertEqual(len(pairs), 1560)
            self.assertEqual(sum(row["ratio_status"] == "both_zero" for row in pairs if row["counter"] == "current_depth"), 24)
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

    def test_exact_instrumented_recipe_rejects_later_overwrite(self):
        path = HERE.parent/"validation/native-correctness-packed-build-record.json"
        record = work.analysis.read_json(path)
        work.check_instrumented_recipe(record, ROOT)
        changed = copy.deepcopy(record)
        changed["build_commands"].append([*record["build_commands"][8]])
        changed["build_commands"][-1].insert(3, "-DNDEBUG")
        with self.assertRaisesRegex(ValueError, "compile/link sequence"): work.check_instrumented_recipe(changed, ROOT)
        changed = copy.deepcopy(record); changed["build_commands"][8].remove("-DKKT_EXPERIMENT_PACKED_SAMPLING")
        with self.assertRaises(ValueError): work.check_instrumented_recipe(changed, ROOT)

    def test_engine_bounds_include_partial_and_empty_calls(self):
        for count in range(4):
            for sizes in itertools.product((0,1,31,32,33,64,65), repeat=count):
                counters = dict(sampling_calls=count, sampling_edge_visits=sum(sizes))
                lower, upper, _ = work.engine_bounds(counters, "packed")
                exact = sum((size+31)//32 for size in sizes)
                self.assertLessEqual(lower, exact); self.assertLessEqual(exact, upper)
                self.assertEqual(work.engine_bounds(counters, "scalar")[:2], (sum(sizes),sum(sizes)))


if __name__ == "__main__": unittest.main(verbosity=2)
