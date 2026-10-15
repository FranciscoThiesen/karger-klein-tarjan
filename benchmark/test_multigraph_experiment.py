#!/usr/bin/env python3
"""Synthetic paired-screen tests. Never builds or executes a native MST solver."""
import argparse
import contextlib
import copy
import csv
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest import mock

import run_multigraph_experiment as experiment


def fake_rows(command):
    argv = dict(zip(command[3::2], command[4::2]))
    spec = {"family": argv["--family"], "n": int(argv["--n"]),
            "density": int(argv["--density"]), "intrusion_per_mille": 0}
    spec.update(m=spec["n"] * spec["density"], case_id=experiment.native.base.case_id(spec))
    candidate = "multigraph" in Path(command[2]).name
    rows = []; cpu = 0; utc = 946684800_000000000
    for phase, count in (("warmup", 1), ("timed", 5)):
        for rep in range(count):
            for order in range(5):
                algorithm = experiment.native.ALGORITHMS[(order + rep) % 5]
                elapsed = 1000 * (1 + experiment.native.ALGORITHMS.index(algorithm))
                if algorithm == "kkt" and candidate:
                    elapsed = 800
                rows.append({**spec, "graph_seed": int(argv["--graph-seed"]), "kkt_seed": int(argv["--kkt-seed"]),
                             "input_fingerprint": 9, "topology_fingerprint": 8, "phase": phase, "repetition": rep,
                             "order": order, "warmups": 1, "algorithm": algorithm, "elapsed_ns": elapsed,
                             "utc_start_ns": utc, "utc_end_ns": utc + elapsed, "process_cpu_start_ns": cpu,
                             "process_cpu_end_ns": cpu + elapsed, "process_cpu_elapsed_ns": elapsed, "validation": "pass"})
                cpu += elapsed + 10; utc += elapsed + 10
    return rows


class FakeProcess:
    def __init__(self, pid, status=0, finishes=True):
        self.pid = pid; self.returncode = None; self.status = status; self.finishes = finishes
    def wait(self, timeout):
        if not self.finishes:
            raise subprocess.TimeoutExpired("synthetic-only", timeout)
        self.returncode = self.status
        return self.status
    def poll(self):
        return self.returncode


class NativeFactory:
    def __init__(self, status=0, finishes=True, row_mutator=None):
        self.children = []; self.status = status; self.finishes = finishes; self.row_mutator = row_mutator
    def __call__(self, command, **kwargs):
        assert command[:2] == ["/usr/bin/time", "-l"] and kwargs["start_new_session"] is True
        rows = fake_rows(command)
        certificate = {field: rows[0][field] for field in experiment.native.CERTIFICATE_FIELDS}
        kwargs["stderr"].write(experiment.native.CERTIFICATE_PREFIX + json.dumps(certificate) + "\n")
        if self.row_mutator:
            self.row_mutator(rows)
        writer = csv.DictWriter(kwargs["stdout"], fieldnames=experiment.native.FIELDS)
        writer.writeheader(); writer.writerows(rows)
        process = FakeProcess(42000 + len(self.children), self.status, self.finishes)
        self.children.append((command, process))
        return process


def provider(group):
    return {"process_group": group, "members": [{"pid": group, "rss_kib": 1024, "command": "synthetic-only"}]}


@contextlib.contextmanager
def fixture():
    with tempfile.TemporaryDirectory(prefix="kkt-paired-synthetic-") as folder:
        root = Path(folder).resolve()
        for name in experiment.analysis.NATIVE_FILES:
            path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text("synthetic source\n")
        (root / "Makefile").write_text("synthetic Make recipe\n")
        manifest = root / "manifest.csv"
        with manifest.open("w", newline="") as stream:
            writer = csv.writer(stream); writer.writerow(experiment.native.base.MANIFEST_FIELDS)
            writer.writerows(sorted(experiment.EXPECTED_CASES))
        protocol = root / "PROTOCOL.md"; protocol.write_text("Synthetic test declaration only.\n")
        args = argparse.Namespace(manifest=manifest, protocol=protocol, freeze=root / "freeze.json")
        sources = experiment.native.source_inventory(root)
        for variant in experiment.VARIANTS:
            binary = root / (variant + "-not-executable"); binary.write_text(variant + " never executed\n")
            log = root / (variant + ".build.log"); log.write_text("synthetic build log, no compiler executed\n")
            record = {"variant": variant, "binary": str(binary), "binary_sha256": experiment.native.sha(binary),
                      "source_sha256": sources, "build_recipe_sha256": {"Makefile": experiment.native.sha(root / "Makefile")},
                      "compiler": "Apple clang synthetic-only\nTarget: arm64-apple-darwin\n",
                      "build_command": ["/usr/bin/arch", "-arm64", "/usr/bin/make", "-B", "-j4", "CXX=/usr/bin/clang++",
                                        "BUILD_DIR=.build/" + variant, "BIN_DIR=bin/" + variant,
                                        "CXXFLAGS=" + " ".join(experiment.BASE_FLAGS + (["-DKKT_EXPERIMENT_RETAIN_PARALLEL"] if variant == "multigraph" else [])),
                                        "mst-search-large-stack"],
                      "compiler_command": ["/usr/bin/arch", "-arm64", "/usr/bin/clang++", "--version"],
                      "sdk": "synthetic-sdk", "build_exit_status": 0,
                      "object_sha256": {name: "1" * 64 for name in experiment.OBJECTS}, "build_log": str(log),
                      "build_log_sha256": experiment.native.sha(log)}
            record_path = root / (variant + "-build.json"); experiment.write_json(record_path, record)
            setattr(args, variant + "_binary", binary)
            setattr(args, variant + "_build_record", record_path)
        previous = Path.cwd()
        os.chdir(root)
        try:
            profile = {"file_description": "Mach-O 64-bit executable arm64", "main_stack_bytes": 536870912,
                       "otool_load_commands": "cmd LC_MAIN\ncmdsize 24\nentryoff 12\nstacksize 536870912\n"}
            with mock.patch.object(experiment.native, "binary_profile", return_value=profile), \
                 mock.patch.object(experiment.subprocess, "check_output", return_value="synthetic-revision\n"), \
                 mock.patch.object(experiment.platform, "platform", return_value="synthetic-platform"), \
                 contextlib.redirect_stdout(io.StringIO()):
                experiment.preflight(args)
                yield root, args
        finally:
            os.chdir(previous)


def run_capture(root, prepared, factory=None, sampler=None, output="capture.csv"):
    factory = factory or NativeFactory()
    def scoped_provider(group):
        process = next(process for _, process in factory.children if process.pid == group)
        return {"process_group": group, "members": []} if process.returncode is not None else provider(group)
    sampler = sampler or experiment.monitor.BoundedSampler(scoped_provider, .1)
    args = argparse.Namespace(freeze=prepared.freeze, output=root / output, released=True)
    info = experiment.capture(args, sampler=sampler, popen=factory)
    return info, factory, sampler


class PairedScreenTests(unittest.TestCase):
    def test_full_mock_capture_analysis_and_balanced_schedule(self):
        with fixture() as (root, prepared):
            info, factory, sampler = run_capture(root, prepared)
            self.assertEqual(len(factory.children), 40)
            self.assertEqual((info["checked_rows"], info["checked_timed_rows"], info["checked_warmup_rows"]), (1200, 1000, 200))
            first, second = info["captures"][:20], info["captures"][20:]
            self.assertEqual([r["variant"] for r in first], ["reference", "multigraph"] * 10)
            self.assertEqual([r["variant"] for r in second], ["multigraph", "reference"] * 10)
            self.assertEqual([r["case_id"] for r in second], list(reversed([r["case_id"] for r in first])))
            loaded = experiment.load(root / "capture.json")
            self.assertEqual(len(loaded[2]), 1200)
            comparisons = experiment.paired_variants(loaded[2])
            self.assertEqual(len(comparisons["variant_pairs"]), 1000)
            self.assertEqual(len(comparisons["variant_comparisons"]), 100)
            for row in comparisons["variant_comparisons"]:
                self.assertEqual(row["median_paired_ratio"], .8 if row["algorithm"] == "kkt" else 1)
                self.assertEqual(row["pairs"], 10)
            power_log = root / "private-power.log"
            power_log.write_text("2000-01-01 00:00:00 +0000 Sleep Entering Sleep state\n"
                                 "2000-01-01 00:00:00 +0000 Wake Requests request=Maintenance\n"
                                 "2000-01-01 00:00:01 +0000 Wake Wake from Deep Idle\n")
            experiment.analyze(argparse.Namespace(capture=root / "capture.json", output_dir=root / "analysis", power_log=power_log))
            provenance = experiment.analysis.read_json(root / "analysis/provenance.json")
            self.assertEqual(provenance["power_audit"]["logged_overlap_calls"], 1200)
            self.assertFalse(provenance["power_audit"]["sleep_inhibition_verified"])
            self.assertTrue((root / "analysis/reference/comparisons.csv").is_file())
            self.assertTrue((root / "analysis/multigraph/comparisons.csv").is_file())
            with self.assertRaisesRegex(ValueError, "overwrite"):
                run_capture(root, prepared)

    def test_case_median_is_all_ten_ratios_not_median_of_graph_medians(self):
        rows = []
        for graph, values in zip(experiment.GRAPH_SEEDS, ([1, 2, 10, 20, 30], [3, 4, 5, 6, 7])):
            for rep, value in enumerate(values):
                base = {"case_id": "synthetic", "family": "synthetic", "n": 1, "m": 2, "density": 2,
                        "intrusion_per_mille": 0, "graph_seed": graph, "kkt_seed": 607, "repetition": rep,
                        "algorithm": "kkt", "input_fingerprint": 9, "topology_fingerprint": 8,
                        "phase": "timed", "elapsed_ns": 100, "process_cpu_elapsed_ns": 100}
                rows.extend(({**base, "variant": "reference"},
                             {**base, "variant": "multigraph", "elapsed_ns": 100 * value, "process_cpu_elapsed_ns": 100 * value}))
        table = experiment.paired_variants(rows)
        self.assertEqual(table["variant_comparisons"][0]["median_paired_ratio"], 5.5)
        self.assertNotEqual(table["variant_comparisons"][0]["median_paired_ratio"], 7.5)
        rows[-1]["input_fingerprint"] = 100
        with self.assertRaisesRegex(ValueError, "input_fingerprint"):
            experiment.paired_variants(rows)

    def test_metadata_semantic_corruption_is_rejected(self):
        with fixture() as (root, prepared):
            good, _, _ = run_capture(root, prepared)
            mutations = {
                "failed": lambda x: x.update(validation="failed"),
                "missing child": lambda x: x["captures"].pop(),
                "wrong variant": lambda x: x["captures"][0].update(variant="multigraph"),
                "unknown native exit": lambda x: x["captures"][0].update(exit_status=None),
                "native process uncertain": lambda x: x.update(native_process_may_still_be_running=True),
                "cleanup present": lambda x: x.update(cleanup=[{}]),
                "native command": lambda x: x["captures"][0]["command"].append("--fake"),
                "group mismatch": lambda x: x["captures"][0].update(process_group=99),
                "unverified empty group": lambda x: x["captures"][0].update(group_exit_verification={}),
                "verification before exit": lambda x: x["captures"][0].update(wrapper_exit_monotonic_ns=x["captures"][0]["finished_monotonic_ns"] + 1),
                "wrong certificate": lambda x: x["captures"][0]["certificate"].update(m=1),
                "resource summary": lambda x: x["captures"][0].update(sampled_peak_rss_kib=1),
                "monitor summary": lambda x: x["captures"][0]["recovery_monitor"].update(max_sampler_duration_ns=0),
                "omitted diagnostic": lambda x: x["call_diagnostics"].pop(),
                "wrong count": lambda x: x.update(checked_timed_rows=999),
                "row adjustment": lambda x: x.update(rows_adjusted=1),
                "overlap": lambda x: x["captures"][1].update(started_monotonic_ns=x["captures"][0]["started_monotonic_ns"]),
            }
            for name, mutate in mutations.items():
                with self.subTest(mutation=name):
                    changed = copy.deepcopy(good); mutate(changed)
                    experiment.write_json(root / "capture.json", changed)
                    with self.assertRaises((ValueError, KeyError)):
                        experiment.load(root / "capture.json")
            experiment.write_json(root / "capture.json", good)
            self.assertEqual(len(experiment.load(root / "capture.json")[2]), 1200)

    def test_raw_csv_corruption_fails_even_with_updated_hashes(self):
        with fixture() as (root, prepared):
            good, _, _ = run_capture(root, prepared)
            raw = Path(good["captures"][0]["csv"])
            original = raw.read_bytes()
            rows = [row for _, row in experiment.native.base.read_csv(raw, experiment.native.FIELDS)]
            for field, value in (("validation", "failed"), ("algorithm", "prim"), ("graph_seed", "1"), ("input_fingerprint", "7")):
                with self.subTest(field=field):
                    changed = copy.deepcopy(rows); changed[0][field] = value
                    experiment.analysis.write_csv(raw, changed)
                    metadata = copy.deepcopy(good); metadata["captures"][0]["output_sha256"] = experiment.native.sha(raw)
                    experiment.write_json(root / "capture.json", metadata)
                    with self.assertRaises(ValueError):
                        experiment.load(root / "capture.json")
            raw.write_bytes(original)
            experiment.write_json(root / "capture.json", good)
            combined = root / "capture.csv"
            data = list(experiment.native.base.read_csv(combined, experiment.FIELDS))
            changed = [row for _, row in data]; changed[0]["variant"] = "multigraph"
            experiment.analysis.write_csv(combined, changed)
            good["output_sha256"] = experiment.native.sha(combined)
            experiment.write_json(root / "capture.json", good)
            with self.assertRaisesRegex(ValueError, "concatenation"):
                experiment.load(root / "capture.json")

    def test_freeze_protocol_binary_and_source_drift_fail_before_launch(self):
        with fixture() as (root, prepared):
            for path in (prepared.protocol, prepared.reference_binary, root / "kkt/kkt.cpp"):
                old = path.read_bytes(); path.write_bytes(old + b"drift")
                factory = NativeFactory()
                with self.assertRaises(ValueError):
                    run_capture(root, prepared, factory=factory)
                self.assertFalse(factory.children)
                path.write_bytes(old)
            args = argparse.Namespace(freeze=prepared.freeze, output=root / "unreleased.csv", released=False)
            with self.assertRaisesRegex(ValueError, "released"):
                experiment.capture(args, popen=NativeFactory())

    def test_monitor_failures_stop_without_a_second_child(self):
        unknown = {"native_exit_known": False, "group_exit_known": False,
                   "native_process_may_still_be_running": True, "signals": []}
        failure_providers = {
            "ceiling": lambda group: {"process_group": group, "members": [{"pid": group,
                "rss_kib": experiment.RULE["rss_limit_kib"] + 1, "command": "synthetic-only"}]},
            "three unavailable": mock.Mock(side_effect=OSError("synthetic unavailable")),
        }
        for name, source in failure_providers.items():
            with self.subTest(name=name), fixture() as (root, prepared):
                factory = NativeFactory(finishes=False)
                sampler = experiment.monitor.BoundedSampler(source, .1)
                with mock.patch.object(experiment.monitor, "bounded_terminate", return_value=unknown), self.assertRaises(ValueError):
                    run_capture(root, prepared, factory=factory, sampler=sampler)
                self.assertEqual(len(factory.children), 1)
                info = experiment.analysis.read_json(root / "capture.json")
                self.assertEqual(info["validation"], "failed")
                self.assertTrue(info["native_process_may_still_be_running"])
                self.assertEqual(info["captures"][0]["rss_observations"], 3 if name == "three unavailable" else 1)
                self.assertTrue(Path(info["captures"][0]["csv"]).exists())

    def test_sampler_timeout_and_poisoned_start_fail_closed(self):
        with fixture() as (root, prepared):
            gate = threading.Event()
            sampler = experiment.monitor.BoundedSampler(lambda group: (gate.wait(), provider(group))[1], .01)
            factory = NativeFactory()
            unknown = {"native_process_may_still_be_running": True}
            try:
                with mock.patch.object(experiment.monitor, "bounded_terminate", return_value=unknown), self.assertRaisesRegex(ValueError, "timed out"):
                    run_capture(root, prepared, factory=factory, sampler=sampler)
                self.assertEqual(len(factory.children), 1)
                self.assertEqual(sampler.workers_started, 1)
                factory2 = NativeFactory()
                with self.assertRaisesRegex(ValueError, "forbids launching"):
                    run_capture(root, prepared, factory=factory2, sampler=sampler, output="second.csv")
                self.assertFalse(factory2.children)
                self.assertEqual(sampler.workers_started, 1)
            finally:
                gate.set()

    def test_zero_exit_requires_an_available_empty_owned_group(self):
        for failure in ("nonempty", "unavailable"):
            with self.subTest(failure=failure), fixture() as (root, prepared):
                factory = NativeFactory()
                def source(group):
                    if factory.children[-1][1].returncode is not None and failure == "unavailable":
                        raise OSError("post-exit observation unavailable")
                    return provider(group)
                sampler = experiment.monitor.BoundedSampler(source, .1)
                with self.assertRaisesRegex(ValueError, "group exit is not verified"):
                    run_capture(root, prepared, factory=factory, sampler=sampler)
                self.assertEqual(len(factory.children), 1)
                info = experiment.analysis.read_json(root / "capture.json")
                self.assertEqual(info["validation"], "failed")
                self.assertTrue(info["native_process_may_still_be_running"])
                self.assertEqual(info["captures"][0]["exit_status"], 0)
                self.assertEqual(info["captures"][0]["rss_observations"], 2)

    def test_build_flags_macro_directories_and_toolchain_are_bound(self):
        with fixture() as (root, prepared):
            frozen = experiment.analysis.read_json(prepared.freeze)
            variants = frozen["variants"]
            experiment.check_build_pair(variants)
            good = variants["reference"]["build"]["record"]["build_command"]
            mutations = []
            for extra in (" -DNDEBUG", " -DKKT_ENABLE_WORK_STATS", " -fsanitize=address", " -DKKT_EXPERIMENT_RETAIN_PARALLEL", " -O0"):
                changed = list(good); changed[8] += extra; mutations.append(changed)
            changed = list(good); changed[1] = "-x86_64"; mutations.append(changed)
            changed = list(good); changed[5] = "CXX=clang++"; mutations.append(changed)
            changed = list(good); changed[8] = "CPPFLAGS=-DNDEBUG"; mutations.append(changed)
            changed = list(good); changed[-1] = "mst-search"; mutations.append(changed)
            for argv in mutations:
                with self.subTest(argv=argv), self.assertRaises(ValueError):
                    experiment.normalized_build_command(argv, "reference")
            for field, value in (("compiler", "different Apple clang"), ("sdk", "different-sdk")):
                changed = copy.deepcopy(variants); changed["multigraph"]["build"]["record"][field] = value
                with self.subTest(field=field), self.assertRaises(ValueError):
                    experiment.check_build_pair(changed)
            changed = copy.deepcopy(variants)
            changed["multigraph"]["build"]["record"]["object_sha256"]["prim/prim.o"] = "2" * 64
            with self.assertRaisesRegex(ValueError, "unchanged production object"):
                experiment.check_build_pair(changed)
            changed = copy.deepcopy(variants)
            changed["multigraph"]["build"]["record"]["build_command"][6] = good[6]
            with self.assertRaisesRegex(ValueError, "distinct build/bin directories"):
                experiment.check_build_pair(changed)

    def test_nonzero_native_exit_stops_and_records_bounded_cleanup(self):
        with fixture() as (root, prepared):
            factory = NativeFactory(status=-11)
            cleanup = {"native_exit_known": True, "group_exit_known": True,
                       "native_process_may_still_be_running": False, "signals": []}
            with mock.patch.object(experiment.monitor, "bounded_terminate", return_value=cleanup), self.assertRaisesRegex(ValueError, "native child failed"):
                run_capture(root, prepared, factory=factory)
            self.assertEqual(len(factory.children), 1)
            info = experiment.analysis.read_json(root / "capture.json")
            self.assertEqual(info["captures"][0]["exit_status"], -11)
            self.assertEqual(info["cleanup"], [cleanup])
            self.assertEqual(info["validation"], "failed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
