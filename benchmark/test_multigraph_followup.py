#!/usr/bin/env python3
"""Follow-up adapter tests with mocked native processes; no solver execution."""
import argparse
import contextlib
import copy
import csv
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import run_multigraph_followup as followup
import test_multigraph_experiment as original_tests

engine = followup.engine


@contextlib.contextmanager
def fixture():
    # First create a completely independent synthetic parent freeze using the
    # unmodified original test fixture and original runner configuration.
    with original_tests.fixture() as (root, parent_args):
        parent = engine.analysis.read_json(parent_args.freeze)
        with mock.patch.object(followup, "parent_freeze", return_value=parent):
            args = copy.copy(parent_args)
            args.manifest = root / "followup-manifest.csv"
            with args.manifest.open("w", newline="") as stream:
                writer = csv.writer(stream); writer.writerow(engine.native.base.MANIFEST_FIELDS)
                writer.writerows(sorted(followup.EXPECTED_CASES))
            args.protocol = root / "FOLLOWUP.md"
            args.protocol.write_text("Synthetic prospective follow-up only.\n")
            args.freeze = root / "followup-freeze.json"
            followup.preflight(args)
            yield root, parent_args, args, parent


def run_capture(root, args):
    factory = original_tests.NativeFactory()
    def provider(group):
        process = next(process for _, process in factory.children if process.pid == group)
        return {"process_group": group, "members": []} if process.returncode is not None else original_tests.provider(group)
    sampler = engine.monitor.BoundedSampler(provider, .1)
    result = followup.capture(argparse.Namespace(freeze=args.freeze, output=root / "followup.csv", released=True),
                              sampler=sampler, popen=factory)
    return result, factory


class FollowupTests(unittest.TestCase):
    def test_complete_new_matrix_and_original_analyzer_remain_independent(self):
        with fixture() as (root, parent_args, args, parent):
            parent_capture, _, _ = original_tests.run_capture(root, parent_args)
            info, factory = run_capture(root, args)
            self.assertEqual(len(factory.children), 40)
            self.assertEqual(info["checked_rows"], 1200)
            self.assertEqual((info["checked_timed_rows"], info["checked_warmup_rows"]), (1000, 200))
            self.assertEqual({child["graph_seed"] for child in info["captures"]}, {3000001, 3000029})
            self.assertEqual({child["kkt_seed"] for child in info["captures"]}, {809})
            self.assertEqual([child["case_id"] for child in info["captures"][:20]],
                             list(reversed([child["case_id"] for child in info["captures"][20:]])))
            self.assertEqual([child["variant"] for child in info["captures"][:20]], ["reference", "multigraph"] * 10)
            self.assertEqual([child["variant"] for child in info["captures"][20:]], ["multigraph", "reference"] * 10)
            self.assertEqual(info["frozen_protocol"]["variants"], parent["variants"])
            self.assertEqual(info["frozen_protocol"]["source_sha256"], parent["source_sha256"])
            self.assertEqual(set(info["frozen_protocol"]["python_source_sha256"]),
                             {*parent["python_source_sha256"], str(followup.HERE)})
            loaded = followup.load(root / "followup.json")
            self.assertEqual(len(loaded[2]), 1200)
            self.assertEqual(len(engine.paired_variants(loaded[2])["variant_pairs"]), 1000)
            followup.analyze(argparse.Namespace(capture=root / "followup.json", output_dir=root / "followup-analysis", power_log=None))
            provenance = engine.analysis.read_json(root / "followup-analysis/provenance.json")
            self.assertEqual(provenance["followup_identity"], followup.IDENTITY)
            self.assertEqual(provenance["power_audit"]["status"], "not_audited")
            self.assertTrue((root / "followup-analysis/README.md").read_text().startswith("# Fresh-seed"))
            self.assertEqual(engine.load(root / "capture.json")[0], parent_capture)
            with self.assertRaises(ValueError):
                engine.load(root / "followup.json")
            with self.assertRaises(ValueError):
                followup.load(root / "capture.json")

    def test_configuration_restores_after_success_nested_scope_and_error(self):
        original = {key: getattr(engine, key) for key in ("GRAPH_SEEDS", "SAMPLING_SEED", "EXPECTED_CASES", "SEMANTICS", "helpers", "preflight", "check_freeze", "analyze")}
        self.assertEqual(engine.GRAPH_SEEDS, (2000003, 2000029))
        with self.assertRaisesRegex(RuntimeError, "synthetic"):
            with followup.configured():
                self.assertEqual(engine.GRAPH_SEEDS, (3000001, 3000029))
                with followup.configured():
                    self.assertEqual(engine.SAMPLING_SEED, 809)
                self.assertEqual(engine.GRAPH_SEEDS, (3000001, 3000029))
                raise RuntimeError("synthetic interruption")
        for key, value in original.items():
            self.assertIs(getattr(engine, key), value)

    def test_adapter_source_drift_is_rejected_without_affecting_parent(self):
        with fixture() as (root, parent_args, args, parent):
            run_capture(root, args)
            original_sha = engine.native.sha
            def changed_sha(path):
                return "0" * 64 if Path(path).resolve() == followup.HERE else original_sha(path)
            with mock.patch.object(engine.native, "sha", side_effect=changed_sha):
                with self.assertRaisesRegex(ValueError, "helper inventory"):
                    followup.load(root / "followup.json")
                self.assertEqual(engine.check_freeze(parent_args.freeze)[0], parent)

    def test_parent_helper_drift_fails_preflight_and_capture_before_native_launch(self):
        with fixture() as (root, parent_args, args, parent):
            changed = dict(parent["python_source_sha256"])
            changed[next(iter(changed))] = "0" * 64
            alternate = copy.copy(args)
            alternate.freeze = root / "never-frozen.json"
            native = mock.Mock(side_effect=AssertionError("native launch forbidden"))
            with mock.patch.object(followup, "BASE_HELPERS", return_value=changed):
                with self.assertRaisesRegex(ValueError, "unchanged parent helper inventory"):
                    followup.preflight(alternate)
                self.assertFalse(alternate.freeze.exists())
                with self.assertRaisesRegex(ValueError, "unchanged parent helper inventory"):
                    followup.capture(argparse.Namespace(freeze=args.freeze, output=root / "never.csv", released=True),
                                     popen=native)
                native.assert_not_called()
            self.assertEqual(engine.check_freeze(parent_args.freeze)[0], parent)

    def test_followup_requires_exact_cases_counts_seeds_and_certified_rows(self):
        with fixture() as (root, parent_args, args, parent):
            info, _ = run_capture(root, args)
            for mutation in (lambda value: value["captures"].pop(),
                             lambda value: value.update(checked_timed_rows=999),
                             lambda value: value["captures"][0].update(graph_seed=2000003),
                             lambda value: value["captures"][0].update(kkt_seed=607)):
                changed = copy.deepcopy(info); mutation(changed)
                engine.write_json(root / "followup.json", changed)
                with self.assertRaises(ValueError):
                    followup.load(root / "followup.json")
            engine.write_json(root / "followup.json", info)
            raw = Path(info["captures"][0]["csv"])
            rows = [row for _, row in engine.native.base.read_csv(raw, engine.native.FIELDS)]
            rows[0]["graph_seed"] = "2000003"
            engine.analysis.write_csv(raw, rows)
            changed = copy.deepcopy(info); changed["captures"][0]["output_sha256"] = engine.native.sha(raw)
            engine.write_json(root / "followup.json", changed)
            with self.assertRaisesRegex(ValueError, "seed or validation mismatch"):
                followup.load(root / "followup.json")
            with followup.configured(), self.assertRaisesRegex(ValueError, "ten declared"):
                engine.cases_from_manifest(parent_args.manifest)

    def test_native_source_binary_build_and_parent_identity_are_bound(self):
        with fixture() as (root, parent_args, args, parent):
            for field in ("variants", "source_sha256", "build_recipe_sha256"):
                changed = copy.deepcopy(parent)
                if field == "variants":
                    changed[field]["multigraph"]["binary_sha256"] = "0" * 64
                else:
                    first = next(iter(changed[field])); changed[field][first] = "0" * 64
                with self.subTest(field=field), self.assertRaisesRegex(ValueError, "unchanged follow-up"):
                    followup.check_shared(changed)
            for path in (args.multigraph_binary, args.multigraph_build_record, root / "kkt/kkt.cpp"):
                before = path.read_bytes(); path.write_bytes(before + b"drift")
                with self.subTest(path=path), self.assertRaises(ValueError):
                    followup.capture(argparse.Namespace(freeze=args.freeze, output=root / "never.csv", released=True),
                                     popen=mock.Mock(side_effect=AssertionError("native launch forbidden")))
                path.write_bytes(before)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "parent.json"
            engine.write_json(path, {"schema": "multigraph_experiment_freeze_v1"})
            digest = engine.native.sha(path)
            with mock.patch.object(followup, "PARENT_FREEZE", path), mock.patch.object(followup, "PARENT_SHA256", digest):
                followup.parent_freeze()
                path.write_text(path.read_text() + " ")
                with self.assertRaisesRegex(ValueError, "hash mismatch"):
                    followup.parent_freeze()

    def test_parent_manifest_protocol_and_unreleased_capture_rejected(self):
        with fixture() as (root, parent_args, args, parent):
            for field in ("manifest", "protocol"):
                wrong = copy.copy(args); setattr(wrong, field, getattr(parent_args, field))
                with self.subTest(field=field), self.assertRaisesRegex(ValueError, "needs its own"):
                    followup.preflight(wrong)
            with self.assertRaisesRegex(ValueError, "released"):
                followup.capture(argparse.Namespace(freeze=args.freeze, output=root / "unreleased.csv", released=False))


if __name__ == "__main__":
    unittest.main(verbosity=2)
