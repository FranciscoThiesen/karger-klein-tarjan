#!/usr/bin/env python3
"""Bounded schema/provenance regressions; never execute a native solver.

Real-data gates read the 16 archived attachment diagnostic work records and
their complete smoke timing capture. Temporary join manifests are explicitly
synthetic test fixtures, not new native captures or performance evidence.
"""
from __future__ import annotations

from copy import deepcopy
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import Mock

import analyze_attachment_work as work
import attachment_occupancy as occupancy


REPO = Path(__file__).resolve().parents[1]
VALIDATION = REPO / "benchmark/results/search-2026-10-13/validation"
DIAGNOSTICS = VALIDATION / "attachment-diagnostics"
TIMING = VALIDATION / "attachment-smoke-timing.csv"


def registry():
    path = REPO / "benchmark/work_metrics.hpp"
    entries = re.findall(r'\{"([a-z_]+)",\s*&kkt_work::WorkStats::([a-z_]+),\s*(true|false)\}',
                         path.read_text())
    return [a for a, _, _ in entries], {a for a, _, flag in entries if flag == "true"}


FIELDS, PROXY = registry()


def recalculate(record):
    compact = record["algorithms"]["compacting_boruvka"]
    for field, column in (("contraction_vertices", "input_vertices"), ("contraction_edges", "input_edges"),
                          ("contraction_output_vertices", "output_vertices"),
                          ("contraction_output_edges", "output_edges")):
        compact[field] = sum(row[column] for row in record["trace"])
    compact["contraction_calls"] = len(record["trace"])
    for stats in record["algorithms"].values():
        stats["total_work_proxy"] = sum(stats[f] for f in PROXY)


def synthetic(mode="hierarchy"):
    # Explicit n=64,b=4 path+one-shortcut trajectory. This is a schema fixture;
    # its synthetic KKT counters are not presented as native algorithm output.
    n, m, b, q = 64, 64, 4, 16
    sizes = [(64, 64, 16, 16), (16, 16, 8, 8), (8, 8, 4, 4),
             (4, 4, 2, 1), (2, 1, 0, 0)]
    trace = []
    for index, (v, e, out_v, out_m) in enumerate(sizes, 1):
        count = out_v or 1
        trace.append(dict(round=index, input_vertices=v, input_edges=e,
                          selected_edges=v-count, output_vertices=out_v, output_edges=out_m,
                          component_count=count, sum_squared_sizes=n*(n//count), largest_component=n//count))
    compact = {field: 0 for field in FIELDS}
    compact.update(kkt_edge_visits=m, edge_materializations=m, hash_insert_items=n-1)
    kkt = {field: 0 for field in FIELDS}
    kkt.update(kkt_calls=3, kkt_vertices=n+8, kkt_edges=m+8, max_depth=2,
               contraction_calls=4, contraction_vertices=n+q+8, contraction_edges=m+16+8,
               root_after_two_vertices=8, root_after_two_edges=8,
               sampling_calls=1, sampling_edge_visits=8, sampled_edges=4,
               verifier_calls=1, verifier_edges=8, verifier_queries=16, filtered_edges=7,
               edge_materializations=m, hash_insert_items=n-1)
    family = f"leaf_{mode}4"
    result = dict(schema="search_work_v1", case_id=f"{family}_n64_d1_p0", family=family,
                  n=n, m=m, density=1, intrusion_per_mille=0, graph_seed=17, kkt_seed=0,
                  input_fingerprint=123, topology_fingerprint=456,
                  mst_edge_count=n-1, mst_total_weight=n*(n-1)//2, validation="pass",
                  algorithms={"kkt": kkt, "compacting_boruvka": compact}, trace=trace)
    recalculate(result)
    return result


def validate(record):
    _, mode, b, q, local = work.dimensions(record)
    work.check_counters(record, FIELDS, PROXY)
    prediction = occupancy.attachment_expectation(record["n"], record["density"], b) \
        if mode in ("hierarchy", "distance") else None
    work.check_trace(record, mode, b, q, local, prediction)
    return work.derive(record, Path("synthetic-work.json"), mode, b, prediction)


class WorkAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archived_sources = work.read_json(VALIDATION / "attachment-build-validation/provenance.json")["source_sha256"]
        cls.real_records = [work.read_json(path) for path in sorted(DIAGNOSTICS.glob("*-work.json"))]
        if len(cls.real_records) != 16:
            raise AssertionError("expected the 16 archived native attachment diagnostics")

    def test_registry_hash_bound_and_native_schema(self):
        fields, proxy = work.registry(REPO, self.archived_sources, {})
        self.assertEqual((fields, proxy), (FIELDS, PROXY))
        self.assertEqual(len(fields), 65)
        for record in self.real_records:
            with self.subTest(family=record["family"]):
                summary, rounds, counters = validate(record)
                self.assertEqual(len(counters), 2)
                self.assertEqual(summary["compactor_rounds"], len(rounds))
                self.assertEqual(rounds[-1]["component_count"], 1)
                self.assertEqual(rounds[-1]["output_vertices"], 0)

    def test_synthetic_modes_and_indices(self):
        for mode in ("hierarchy", "distance", "shuffled", "random"):
            summary, rounds, _ = validate(synthetic(mode))
            self.assertEqual(summary["occupancy_prediction"], mode in ("hierarchy", "distance"))
            if summary["occupancy_prediction"]:
                self.assertEqual(rounds[0]["model_phase"], "original_star")
                self.assertIsNone(rounds[0]["core_input_block_size"])
                self.assertEqual(rounds[0]["core_output_block_size"], 1)
                self.assertEqual(rounds[1]["core_input_block_size"], 1)
                self.assertEqual(rounds[1]["core_round_index"], 1)
                self.assertEqual(rounds[-1]["core_output_block_size"], 16)
            else:
                self.assertTrue(all(row["expected_input_edges"] is None for row in rounds))
                self.assertIsNone(summary["observed_minus_expected_edges"])

    def test_observed_edges_are_not_forced_to_expectation(self):
        data = synthetic()
        data["trace"][1]["output_edges"] = 7
        data["trace"][2]["input_edges"] = 7
        data["trace"][2]["output_edges"] = 3
        data["trace"][3]["input_edges"] = 3
        data["algorithms"]["kkt"]["root_after_two_edges"] = 7
        recalculate(data)
        summary, rounds, _ = validate(data)
        self.assertNotEqual(summary["observed_minus_expected_edges"], 0)
        self.assertNotEqual(rounds[2]["observed_minus_expected_input_edges"], 0)

    def test_zero_verifier_fraction_is_absent(self):
        data = synthetic()
        data["algorithms"]["kkt"].update(verifier_edges=0, filtered_edges=0)
        summary, _, _ = work.derive(data, Path("synthetic"), "random", 4, None)
        self.assertIsNone(summary["heavy_fraction"])

    def test_dimension_mutations(self):
        mutations = [("family", False), ("family", "leaf_hierarchy8"), ("n", True), ("n", 63),
                     ("m", 63), ("density", 0), ("graph_seed", 2**32), ("kkt_seed", -1),
                     ("input_fingerprint", 2**64), ("intrusion_per_mille", 1),
                     ("mst_edge_count", 62), ("mst_total_weight", 1), ("validation", "fail")]
        for name, value in mutations:
            with self.subTest(name=name):
                record = synthetic(); record[name] = value
                with self.assertRaises(ValueError):
                    validate(record)
        for missing in ("trace", "algorithms"):
            record = synthetic(); del record[missing]
            with self.assertRaises(ValueError):
                validate(record)

    def test_counter_mutations(self):
        for algorithm, field, value in [
            ("kkt", "sampled_edges", True), ("kkt", "max_depth", 0),
            ("kkt", "hash_insert_items", 64), ("kkt", "sampled_edges", 9),
            ("kkt", "filtered_edges", 9), ("kkt", "verifier_queries", 17),
            ("compacting_boruvka", "kkt_edge_visits", 63),
            ("compacting_boruvka", "sampling_calls", 1),
            ("compacting_boruvka", "contraction_edges", 1000)]:
            with self.subTest(algorithm=algorithm, field=field):
                data = synthetic(); data["algorithms"][algorithm][field] = value
                for stats in data["algorithms"].values():
                    stats["total_work_proxy"] = sum(stats[f] for f in PROXY)
                with self.assertRaises(ValueError):
                    validate(data)
        data = synthetic(); data["algorithms"]["kkt"]["total_work_proxy"] += 1
        with self.assertRaises(ValueError):
            validate(data)
        data = synthetic(); data["algorithms"]["kkt"]["unknown"] = 0
        with self.assertRaises(ValueError):
            validate(data)

    def test_trace_mutations(self):
        for row, field, value in [(0,"round",2), (1,"input_edges",17), (0,"selected_edges",47),
                                  (0,"output_vertices",32), (0,"largest_component",5),
                                  (0,"sum_squared_sizes",258), (4,"output_edges",1),
                                  (3,"component_count",3), (2,"input_vertices",True)]:
            with self.subTest(row=row, field=field):
                data = synthetic(); data["trace"][row][field] = value
                with self.assertRaises(ValueError):
                    validate(data)
        data = synthetic(); data["trace"].pop(); recalculate(data)
        with self.assertRaises(ValueError):
            validate(data)
        data = synthetic(); data["algorithms"]["kkt"]["root_after_two_edges"] = 7
        with self.assertRaises(ValueError):
            validate(data)

    def test_json_duplicate_and_nonfinite_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            for text in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    work.read_json(path)

    def test_moment_bounds(self):
        work.check_moments(10, 3, 34, 4)  # Exact partition 4+3+3.
        for args in [(10,3,32,4), (10,3,35,4), (10,3,34,3), (10,3,100,8), (10,0,0,0)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                work.check_moments(*args)

    def temporary_manifest(self, folder):
        # Test-only adapter for existing raw outputs: this intentionally makes
        # no assertion about the historical diagnostics binary hash.
        binary = folder / "synthetic-work-binary"
        binary.write_text("synthetic manifest fixture; never executable\n")
        build_log = VALIDATION / "attachment-build/build.log"
        runs = work.read_json(DIAGNOSTICS / "runs.json")
        records = []
        for run in runs:
            if run["command"][0] != "bin/search_work":
                continue
            family = run["command"][2]
            records.append(dict(command=[str(binary), *run["command"][1:]], exit_status=run["exit_status"],
                                json=str(DIAGNOSTICS / f"{family}-work.json"),
                                log=str(DIAGNOSTICS / f"{family}-work.log"),
                                json_sha256=run["stdout_sha256"], log_sha256=run["stderr_sha256"]))
        return dict(schema="attachment_work_capture_v1", validation="pass", instrumented=True,
                    rows_removed=0, rows_adjusted=0, working_directory=str(REPO),
                    profile="synthetic manifest test only; archived native work records",
                    binary=str(binary), binary_sha256=work.sha(binary),
                    source_sha256=self.archived_sources,
                    build_recipe_sha256={"Makefile": self.archived_sources["Makefile"]},
                    build_log=str(build_log), build_log_sha256=work.sha(build_log),
                    synthetic_manifest_test_only=True, records=records)

    def test_complete_join_and_manifest_failures(self):
        with tempfile.TemporaryDirectory(prefix="attachment-work-test-") as tmp:
            folder = Path(tmp); path = folder / "manifest.json"
            original = self.temporary_manifest(folder)
            def collect(manifest):
                path.write_text(json.dumps(manifest))
                return work.collect(REPO, [TIMING], path)
            tables, provenance, models = collect(original)
            self.assertEqual(provenance["work_records"], 16)
            self.assertEqual(len(tables["counters"]), 32)
            self.assertEqual(len(tables["timing_links"]), 16)
            self.assertEqual(sum(row["prediction"] is not None for row in models), 8)
            self.assertFalse(provenance["timings_pooled"])
            self.assertFalse(provenance["independently_recertifies_mst_from_edges"])
            self.assertIn("n/a", work.report(tables, provenance))
            for mutate in (
                lambda x: x.update(validation="fail"), lambda x: x.update(rows_removed=True),
                lambda x: x.update(binary_sha256="not-a-hash"),
                lambda x: x["records"][0].update(exit_status=1),
                lambda x: x["records"][0].update(error=None),
                lambda x: x["records"][0].update(json_sha256="0"*64),
                lambda x: x["records"][0].pop("log_sha256"),
                lambda x: x["records"][0]["command"].__setitem__(-1,"1"),
                lambda x: x["source_sha256"].__setitem__("kkt/kkt.cpp","0"*64),
                lambda x: x["records"].append(deepcopy(x["records"][0])),
            ):
                changed = deepcopy(original); mutate(changed)
                with self.assertRaises(ValueError):
                    collect(changed)
            # Correctly hashed but absent native certificate is still rejected.
            empty_log = folder / "empty.log"; empty_log.write_text("")
            changed = deepcopy(original)
            changed["records"][0].update(log=str(empty_log), log_sha256=work.sha(empty_log))
            with self.assertRaises(ValueError):
                collect(changed)
            # Change both raw identity and its certificate: the timed join must
            # reject the new fingerprint even when local hashes are consistent.
            changed = deepcopy(original); first = changed["records"][0]
            altered = work.read_json(first["json"]); altered["input_fingerprint"] += 1
            altered_json = folder / "different.json"; altered_json.write_text(json.dumps(altered))
            certificate = {name: altered[name] for name in
                           ("case_id","graph_seed","kkt_seed","n","m","input_fingerprint","topology_fingerprint","validation")}
            altered_log = folder / "different.log"
            altered_log.write_text("reference_certificate_v1 " + json.dumps(certificate) + "\n")
            first.update(json=str(altered_json), json_sha256=work.sha(altered_json),
                         log=str(altered_log), log_sha256=work.sha(altered_log))
            with self.assertRaises(ValueError):
                collect(changed)

    def test_campaign_pairing_preserves_separate_identities(self):
        record = synthetic()
        row = {field: record[field] for field in work.IDENTITY}; row["phase"] = "timed"
        info = dict(revision="synthetic", profile="synthetic", binary_sha256="a"*64,
                    source_sha256={"source":"b"*64}, build_recipe_sha256={"Makefile":"c"*64},
                    checked_timed_rows=1, checked_warmup_rows=0, flagged_calls=0, capture_clock_flags=[])
        with tempfile.TemporaryDirectory() as tmp:
            one, two = Path(tmp)/"one.csv", Path(tmp)/"two.csv"
            one.write_text("synthetic\n"); two.write_text("synthetic\n")
            fake = Mock()
            fake.load.side_effect = [(deepcopy(info),{},[deepcopy(row)],[],[],{}),
                                     (deepcopy(info),{},[deepcopy(row)],[],[],{})]
            index, campaigns = work.load_timings([one,two],fake,{})
            self.assertEqual(len(campaigns),2)
            self.assertEqual(len(index[work.key(record)]),2)
            altered = deepcopy(row); altered["input_fingerprint"] += 1
            fake.load.side_effect = [(deepcopy(info),{},[deepcopy(row)],[],[],{}),
                                     (deepcopy(info),{},[altered],[],[],{})]
            with self.assertRaises(ValueError):
                work.load_timings([one,two],fake,{})


def main():
    output = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(WorkAnalysisTests)
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    if not result.wasSuccessful():
        print(output.getvalue())
        raise SystemExit(1)
    print(json.dumps({"validation":"pass", "test_methods":result.testsRun,
                      "archived_native_work_records":16, "native_binaries_executed":0,
                      "complete_smoke_timing_join":True,
                      "join_manifest_scope":"temporary synthetic test adapter, not new capture evidence"}, indent=2))


if __name__ == "__main__":
    main()
