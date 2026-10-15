#!/usr/bin/env python3
"""Synthetic six-solver collector tests; no native solver builds or execution."""
import argparse
import contextlib
import copy
import csv
import json
from pathlib import Path
import threading
import unittest
from unittest import mock

import run_retention_control as control
import test_multigraph_experiment as old_tests


@contextlib.contextmanager
def fixture():
    with old_tests.fixture() as (root, parent_args):
        parent = control.analysis.read_json(parent_args.freeze)
        # Actual disposable object files make the new object's on-disk hash
        # check meaningful without compiling or claiming native performance.
        object_hashes = {}
        for name in control.previous.OBJECTS:
            path = root / ".build/retention-control" / name
            path.parent.mkdir(parents=True, exist_ok=True); path.write_text("synthetic object " + name)
            object_hashes[name] = control.native.sha(path)
        for variant in control.previous.VARIANTS:
            record_path = Path(parent["variants"][variant]["build"]["path"])
            record = control.analysis.read_json(record_path); record["object_sha256"] = object_hashes
            control.write_json(record_path, record)
            parent["variants"][variant]["build"] = {"path": str(record_path), "sha256": control.native.sha(record_path), "record": record}
        control.write_json(parent_args.freeze, parent)
        for name in control.NEW_NATIVE_FILES:
            path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text("synthetic control source\n")
        (root / "benchmark/retention_control.mk").write_text("synthetic additional Make recipe\n")
        binary = root / "bin/retention-control/retention_control"
        binary.parent.mkdir(parents=True); binary.write_text("synthetic six-solver binary; never executed\n")
        build = copy.deepcopy(parent["variants"]["multigraph"]["build"]["record"])
        build.update(schema="retention_control_build_v1", working_directory=str(root), binary=str(binary), binary_sha256=control.native.sha(binary),
                     source_sha256=control.native.source_inventory(root),
                     build_recipe_sha256={name: control.native.sha(root / name) for name in control.RECIPES},
                     binary_profile=parent["variants"]["multigraph"]["binary_profile"],
                     build_command=["/usr/bin/arch", "-arm64", "/usr/bin/make", "-f", "benchmark/retention_control.mk", "-B", "-j4",
                                    "CXX=/usr/bin/clang++", "BUILD_DIR=.build/retention-control", "BIN_DIR=bin/retention-control",
                                    "CXXFLAGS=" + " ".join(control.previous.BASE_FLAGS + ["-DKKT_EXPERIMENT_RETAIN_PARALLEL"]),
                                    "retention-control", "retention-control-test"],
                     parent_candidate_build_record=parent["variants"]["multigraph"]["build"]["path"],
                     parent_candidate_build_record_sha256=parent["variants"]["multigraph"]["build"]["sha256"],
                     all_eight_production_objects_equal_parent_candidate=True)
        build_path = root / "control-build.json"; control.write_json(build_path, build)
        manifest = root / "control-manifest.csv"
        with manifest.open("w", newline="") as stream:
            writer = csv.writer(stream); writer.writerow(control.native.base.MANIFEST_FIELDS); writer.writerows(sorted(control.EXPECTED_CASES))
        protocol = root / "CONTROL.md"; protocol.write_text("Synthetic prospective control.\n")
        args = argparse.Namespace(binary=binary, build_record=build_path, parent_freeze=parent_args.freeze,
                                  manifest=manifest, protocol=protocol, freeze=root / "control-freeze.json")
        with mock.patch.object(control, "PARENT_SHA256", control.native.sha(parent_args.freeze)):
            control.preflight(args)
            yield root, args, parent


def rows_for(command):
    argv = dict(zip(command[3::2], command[4::2]))
    spec = {"family": argv["--family"], "n": int(argv["--n"]), "density": int(argv["--density"]), "intrusion_per_mille": 0}
    spec.update(m=spec["n"] * spec["density"], case_id=control.native.base.case_id(spec))
    rows = []; cpu = 0; utc = 946684800_000000000
    for phase, count in (("warmup", 1), ("timed", 6)):
        for rep in range(count):
            for order in range(6):
                algorithm = control.ALGORITHMS[(order + rep) % 6]
                duration = 1000 * (1 + control.ALGORITHMS.index(algorithm))
                rows.append({**spec, "graph_seed": int(argv["--graph-seed"]), "kkt_seed": int(argv["--kkt-seed"]),
                             "input_fingerprint": 9, "topology_fingerprint": 8, "phase": phase, "repetition": rep,
                             "order": order, "warmups": 1, "algorithm": algorithm, "elapsed_ns": duration,
                             "utc_start_ns": utc, "utc_end_ns": utc + duration, "process_cpu_start_ns": cpu,
                             "process_cpu_end_ns": cpu + duration, "process_cpu_elapsed_ns": duration, "validation": "pass"})
                utc += duration + 10; cpu += duration + 10
    return rows


class Factory:
    def __init__(self, status=0, finishes=True, mutation=None):
        self.children = []; self.status = status; self.finishes = finishes; self.mutation = mutation
    def __call__(self, argv, **kwargs):
        assert argv[:2] == ["/usr/bin/time", "-l"] and kwargs["start_new_session"] is True
        rows = rows_for(argv)
        certificate = {field: rows[0][field] for field in control.native.CERTIFICATE_FIELDS}
        kwargs["stderr"].write(control.native.CERTIFICATE_PREFIX + json.dumps(certificate) + "\n")
        if self.mutation: self.mutation(rows)
        writer = csv.DictWriter(kwargs["stdout"], fieldnames=control.FIELDS); writer.writeheader(); writer.writerows(rows)
        process = old_tests.FakeProcess(55000 + len(self.children), self.status, self.finishes)
        self.children.append((argv, process)); return process


def capture(root, args, factory=None, sampler=None, output="control.csv"):
    factory = factory or Factory()
    def provider(group):
        process = next(process for _, process in factory.children if process.pid == group)
        return {"process_group": group, "members": []} if process.returncode is not None else old_tests.provider(group)
    sampler = sampler or control.monitor.BoundedSampler(provider, .1)
    info = control.capture(argparse.Namespace(freeze=args.freeze, output=root / output, released=True), sampler=sampler, popen=factory)
    return info, factory


class RetentionControlTests(unittest.TestCase):
    def test_full_matrix_strict_analysis_all_comparators_and_power(self):
        with fixture() as (root, args, parent):
            info, factory = capture(root, args)
            self.assertEqual((len(factory.children), info["checked_rows"], info["checked_timed_rows"], info["checked_warmup_rows"]), (20, 840, 720, 120))
            self.assertEqual([item["case_id"] for item in info["captures"][:10]], list(reversed([item["case_id"] for item in info["captures"][10:]])))
            loaded = control.load(root / "control.json")
            tables = control.aggregate(loaded[2])
            self.assertEqual(len(tables["paired_ratios"]), 1200)
            self.assertEqual(len(tables["comparisons"]), 100)
            self.assertEqual(len(tables["summary"]), 120)
            for row in tables["comparisons"]:
                self.assertEqual(row["trials"], 12)
                self.assertEqual(row["median_paired_ratio"], 1 / (1 + control.ALGORITHMS.index(row["competitor"])))
            for item in info["captures"]:
                raw = [row for _, row in control.native.base.read_csv(Path(item["csv"]), control.FIELDS)]
                for solver in control.ALGORITHMS:
                    positions = [int(row["order"]) for row in raw if row["phase"] == "timed" and row["algorithm"] == solver]
                    self.assertEqual(sorted(positions), list(range(6)))
            log = root / "private-power.log"
            log.write_text("2000-01-01 00:00:00 +0000 Sleep Entering Sleep state\n2000-01-01 00:00:00 +0000 Wake Requests request=Maintenance\n2000-01-01 00:00:01 +0000 Wake Wake from Deep Idle\n")
            control.analyze(argparse.Namespace(capture=root / "control.json", output_dir=root / "analysis", power_log=log))
            self.assertEqual(control.analysis.read_json(root / "analysis/provenance.json")["power_audit"]["logged_overlap_calls"], 840)
            with self.assertRaisesRegex(ValueError, "overwrite"):
                capture(root, args)

    def test_semantic_metadata_corruption_fails(self):
        with fixture() as (root, args, parent):
            good, _ = capture(root, args)
            mutations = {
                "failed": lambda x: x.update(validation="failed"),
                "missing child": lambda x: x["captures"].pop(),
                "wrong seed": lambda x: x["captures"][0].update(graph_seed=2000003),
                "wrong count": lambda x: x.update(checked_rows=1200),
                "five-solver count": lambda x: x["captures"][0].update(rows=30),
                "unknown exit": lambda x: x["captures"][0].update(exit_status=None),
                "uncertain group": lambda x: x.update(native_process_may_still_be_running=True),
                "wrong argv": lambda x: x["captures"][0]["command"].append("extra"),
                "wrong certificate": lambda x: x["captures"][0]["certificate"].update(m=1),
                "RSS identity": lambda x: x["captures"][0].update(process_group=3),
                "RSS peak": lambda x: x["captures"][0].update(sampled_peak_rss_kib=1),
                "group unverified": lambda x: x["captures"][0].update(group_exit_verification={}),
                "group early": lambda x: x["captures"][0].update(wrapper_exit_monotonic_ns=x["captures"][0]["finished_monotonic_ns"] + 1),
                "missing flags": lambda x: x["call_diagnostics"].pop(),
                "row trimmed": lambda x: x.update(rows_removed=1),
            }
            for name, mutation in mutations.items():
                changed = copy.deepcopy(good); mutation(changed); control.write_json(root / "control.json", changed)
                with self.subTest(name=name), self.assertRaises((ValueError, KeyError)):
                    control.load(root / "control.json")

    def test_six_order_rows_certificates_and_combined_csv_reread(self):
        with fixture() as (root, args, parent):
            good, _ = capture(root, args)
            raw = Path(good["captures"][0]["csv"]); original = raw.read_bytes()
            rows = [row for _, row in control.native.base.read_csv(raw, control.FIELDS)]
            for field, value in (("algorithm", "kruskal"), ("graph_seed", "1"), ("kkt_seed", "607"), ("validation", "failed"), ("input_fingerprint", "123")):
                changed = copy.deepcopy(rows); changed[0][field] = value; control.analysis.write_csv(raw, changed)
                info = copy.deepcopy(good); info["captures"][0]["output_sha256"] = control.native.sha(raw)
                control.write_json(root / "control.json", info)
                with self.subTest(field=field), self.assertRaises(ValueError): control.load(root / "control.json")
            raw.write_bytes(original); control.write_json(root / "control.json", good)
            combined = root / "control.csv"
            values = [row for _, row in control.native.base.read_csv(combined, control.FIELDS)]
            values[0]["elapsed_ns"] = "9999"; control.analysis.write_csv(combined, values)
            good["output_sha256"] = control.native.sha(combined); control.write_json(root / "control.json", good)
            with self.assertRaisesRegex(ValueError, "concatenation"): control.load(root / "control.json")

    def test_clock_flags_preserved_and_six_pair_aggregation_is_pooled(self):
        with fixture() as (root, args, parent):
            info, _ = capture(root, args, factory=Factory(mutation=lambda rows: rows[0].update(elapsed_ns=2_000_000_000)))
            self.assertEqual(info["flagged_calls"], 20)
            self.assertEqual(len(control.load(root / "control.json")[2]), 840)
            self.assertTrue(all(not row["excluded"] for row in info["call_diagnostics"]))
        rows = []
        for graph, values in zip(control.GRAPH_SEEDS, ([1, 2, 10, 20, 30, 40], [3, 4, 5, 6, 7, 8])):
            for rep, value in enumerate(values):
                for solver in control.ALGORITHMS:
                    rows.append({"case_id": "synthetic", "family": "synthetic", "n": 1, "m": 1, "density": 1,
                                 "intrusion_per_mille": 0, "graph_seed": graph, "kkt_seed": 809, "repetition": rep,
                                 "algorithm": solver, "phase": "timed", "elapsed_ns": value * 100 if solver == "kkt" else 100,
                                 "process_cpu_elapsed_ns": value * 100 if solver == "kkt" else 100})
        self.assertEqual(control.aggregate(rows)["comparisons"][0]["median_paired_ratio"], 6.5)
        rows.pop()
        with self.assertRaisesRegex(ValueError, "incomplete six-algorithm"): control.aggregate(rows)

    def test_provenance_drift_prevents_launch_and_build_flags_are_checked(self):
        with fixture() as (root, args, parent):
            for path in (args.binary, args.protocol, root / "kkt/kkt.cpp", root / ".build/retention-control/kkt/kkt.o"):
                before = path.read_bytes(); path.write_bytes(before + b"drift")
                factory = Factory()
                with self.subTest(path=path), self.assertRaises(ValueError): capture(root, args, factory=factory)
                self.assertFalse(factory.children); path.write_bytes(before)
            record = control.analysis.read_json(args.build_record)
            for mutation in (lambda x: x["build_command"].__setitem__(10, x["build_command"][10] + " -DNDEBUG"),
                             lambda x: x["object_sha256"].update({"kkt/kkt.o": "0" * 64}),
                             lambda x: x.update(sdk="different SDK")):
                changed = copy.deepcopy(record); mutation(changed); control.write_json(args.build_record, changed)
                with self.assertRaises(ValueError): control.build_record(args.build_record, args.binary, root, parent)
            control.write_json(args.build_record, record)
            original_helpers = control.previous.helpers()
            changed = dict(original_helpers); changed[next(iter(changed))] = "0" * 64
            with mock.patch.object(control.previous, "helpers", return_value=changed), self.assertRaisesRegex(ValueError, "parent helpers changed"):
                control.check_freeze(args.freeze)
            with self.assertRaisesRegex(ValueError, "released"):
                control.capture(argparse.Namespace(freeze=args.freeze, output=root / "unreleased.csv", released=False))

    def test_monitor_failures_nonzero_exit_and_unverified_group_stop(self):
        for failure in ("ceiling", "unavailable", "nonempty group", "unavailable exit", "native crash"):
            with self.subTest(failure=failure), fixture() as (root, args, parent):
                factory = Factory(status=-11 if failure == "native crash" else 0, finishes=failure != "unavailable")
                def provider(group):
                    exited = factory.children[-1][1].returncode is not None
                    if failure == "unavailable" or (failure == "unavailable exit" and exited): raise OSError("synthetic unavailable")
                    result = old_tests.provider(group)
                    if failure == "ceiling": result["members"][0]["rss_kib"] = control.RULE["rss_limit_kib"] + 1
                    return result
                sampler = control.monitor.BoundedSampler(provider, .1)
                with mock.patch.object(control.monitor, "bounded_terminate", return_value={"native_process_may_still_be_running": True}), self.assertRaises(ValueError):
                    capture(root, args, factory=factory, sampler=sampler)
                self.assertEqual(len(factory.children), 1)
                info = control.analysis.read_json(root / "control.json")
                self.assertEqual(info["validation"], "failed")
                self.assertTrue(info["native_process_may_still_be_running"])
                with self.assertRaises(ValueError): control.load(root / "control.json")

    def test_stuck_sampler_never_launches_next_child_or_more_threads(self):
        with fixture() as (root, args, parent):
            gate = threading.Event(); factory = Factory()
            sampler = control.monitor.BoundedSampler(lambda group: (gate.wait(), old_tests.provider(group))[1], .01)
            try:
                with mock.patch.object(control.monitor, "bounded_terminate", return_value={"native_process_may_still_be_running": True}), self.assertRaisesRegex(ValueError, "timed out"):
                    capture(root, args, factory=factory, sampler=sampler)
                self.assertEqual((len(factory.children), sampler.workers_started), (1, 1))
                other = Factory()
                with self.assertRaisesRegex(ValueError, "forbids launching"):
                    capture(root, args, factory=other, sampler=sampler, output="second.csv")
                self.assertFalse(other.children); self.assertEqual(sampler.workers_started, 1)
            finally: gate.set()


if __name__ == "__main__": unittest.main(verbosity=2)
