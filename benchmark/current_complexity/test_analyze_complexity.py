#!/usr/bin/env python3
"""Prepared synthetic gates, not executed or evidence of native API validity."""
import copy
import csv
from fractions import Fraction
import io
import json
import math
from pathlib import Path
import statistics
import tempfile
import unittest

import analyze_complexity as analysis

# Spell the declaration independently of the analyzer's schedule implementation.
DECLARED_SIZES = (1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 1048576)
DECLARED_UPPER = (32768, 65536, 131072, 262144, 524288, 1048576)
DECLARED_CLOCKS = ("native_steady", "native_process_cpu", "library_manual", "library_process_cpu")
DECLARED_MODELS = ("(1)", "lgN", "N", "NlgN", "N^2", "N^3")
DECLARED_FAMILIES = ("leaf_hierarchy4", "leaf_shuffled4", "gnm_random")
DECLARED_GRAPHS = (19000013, 19000043)
DECLARED_SAMPLERS = (3001, 3011)


def declared_specs():
    result = []
    orders = (("kkt", "multigraph_boruvka"), ("multigraph_boruvka", "kkt"),
              ("multigraph_boruvka", "kkt"), ("kkt", "multigraph_boruvka"))
    for family in DECLARED_FAMILIES:
        for cell, (graph, sample) in enumerate(((19000013, 3001), (19000013, 3011), (19000043, 3001), (19000043, 3011))):
            for algorithm in orders[cell]:
                result.append(dict(family=family, algorithm=algorithm, graph_seed=graph,
                                   sampling_seed=sample, size_order="ascending" if cell < 2 else "descending"))
    return result


def encode_rows(rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=analysis.FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def make_native(spec):
    family_slot = DECLARED_FAMILIES.index(spec["family"])
    graph_slot = DECLARED_GRAPHS.index(spec["graph_seed"])
    sample_slot = DECLARED_SAMPLERS.index(spec["sampling_seed"])
    algorithm_slot = 0 if spec["algorithm"] == "kkt" else 1
    sizes = DECLARED_SIZES if spec["size_order"] == "ascending" else DECLARED_SIZES[::-1]
    rows, certificates = [], []
    cpu, utc = 1000, 10**18
    for n in sizes:
        m = n * (16 if family_slot == 2 else 32)
        # Fingerprints depend on G/family/n, never algorithm or sampler seed.
        weighted = (family_slot + 1) * 10**12 + n * 10 + graph_slot
        topology = (2 if family_slot == 2 else 1) * 10**12 + n * 10 + graph_slot
        for invocation in range(3):
            for phase, iteration in (("warmup", 0), ("timed", 0), ("timed", 1)):
                wall = 17 * (n + m) + family_slot * 31 + graph_slot * 29 + sample_slot * 23 + algorithm_slot * 19 + invocation * 11 + iteration * 3 + 101
                cpu_duration = wall * 4 // 5 + 7
                row = dict(spec, n=n, m=m, N=n + m, input_fingerprint=weighted, topology_fingerprint=topology,
                           invocation=invocation, phase=phase, iteration=iteration, elapsed_ns=wall,
                           utc_start_ns=utc, utc_end_ns=utc + wall, process_cpu_start_ns=cpu,
                           process_cpu_end_ns=cpu + cpu_duration, process_cpu_elapsed_ns=cpu_duration,
                           validation="pass")
                rows.append(row)
                if phase == "warmup":
                    certificates.append("complexity_certificate_v1 " + json.dumps({key: row[key] for key in analysis.CERT_FIELDS}))
                cpu += cpu_duration + 31
                utc += wall + 43
    return rows, "\n".join(certificates) + "\n"


def independent_name(spec, n=None):
    head = f'{spec["algorithm"]}/{spec["family"]}/graph_{spec["graph_seed"]}/sampler_{spec["sampling_seed"]}'
    return head + ("/" + str(n) if n is not None else "") + "/iterations:2/repeats:3/process_time/manual_time"


def make_library(spec, native):
    # CPU is exactly quadratic as a rational construction; wall is near-linear.
    # The exported manual coefficient is fitted to CPU's N², not its own best N.
    reports, observations = [], []
    sizes = DECLARED_SIZES if spec["size_order"] == "ascending" else DECLARED_SIZES[::-1]
    for n in sizes:
        base = independent_name(spec, n)
        ordinary = []
        for invocation in range(3):
            calls = [row for row in native if row["n"] == n and row["invocation"] == invocation and row["phase"] == "timed"]
            N, m = calls[0]["N"], calls[0]["m"]
            manual_ns = Fraction(sum(row["elapsed_ns"] for row in calls), 2)
            cpu_ns = Fraction(N * N, 1000)
            row = dict(name=base, run_name=base, run_type="iteration", repetitions=3,
                       repetition_index=invocation, threads=1, iterations=2,
                       real_time=float(manual_ns / 10**6), cpu_time=float(cpu_ns / 10**6), time_unit="ms",
                       vertices=n, edges=m, graph_seed=spec["graph_seed"], sampling_seed=spec["sampling_seed"])
            reports.append(row)
            ordinary.append(row)
            observations.append((N, manual_ns))
        for aggregate in ("mean", "median", "stddev"):
            row = {key: value for key, value in ordinary[0].items() if key != "repetition_index"}
            row.update(name=base + "_" + aggregate, run_type="aggregate", aggregate_name=aggregate, iterations=3)
            function = {"mean": statistics.mean, "median": statistics.median, "stddev": statistics.stdev}[aggregate]
            for key in ("real_time", "cpu_time", "vertices", "edges", "graph_seed", "sampling_seed"):
                row[key] = function([item[key] for item in ordinary])
            reports.append(row)
    denominator = sum(N**4 for N, _ in observations)
    coefficient = sum(time * N**2 for N, time in observations) / denominator
    base = independent_name(spec)
    reports.append(dict(name=base + "_BigO", run_name=base, run_type="aggregate", repetitions=3,
                        threads=1, aggregate_name="BigO", cpu_coefficient=0.001,
                        real_coefficient=float(coefficient), big_o="N^2", time_unit="ns"))
    reports.append(dict(name=base + "_RMS", run_name=base, run_type="aggregate", repetitions=3,
                        threads=1, aggregate_name="RMS", rms=0.0))
    context = dict(date="synthetic", host_name="not-native", num_cpus=1, mhz_per_cpu=1,
                   caches=[], load_avg=[], library_build_type="release")
    return dict(context=context, benchmarks=reports)


def make_curve(spec):
    rows, log = make_native(spec)
    native, flags = analysis.validate_native(encode_rows(rows), log, spec)
    library = analysis.validate_curve_library(make_library(spec, rows), spec, native)
    return dict(spec=spec, native_rows=native, library=library), flags


class AnalysisTests(unittest.TestCase):
    def test_literal_schedule_native_certificates_fingerprints_and_twins(self):
        self.assertEqual(analysis.schedule(), declared_specs())
        curves, flags = [], []
        for spec in declared_specs():
            curve, current_flags = make_curve(spec)
            curves.append(curve)
            flags.extend(current_flags)
        self.assertEqual(sum(len(curve["native_rows"]) for curve in curves), 2376)
        self.assertEqual(len(analysis.check_graphs(curves)), 66)
        self.assertEqual(flags, [])
        changed = copy.deepcopy(curves)
        changed[-1]["native_rows"][0]["input_fingerprint"] += 1
        with self.assertRaisesRegex(ValueError, "graph changed"):
            analysis.check_graphs(changed)
        with self.assertRaisesRegex(ValueError, "24-curve"):
            analysis.check_graphs(curves[::-1])
        changed = copy.deepcopy(curves)
        for curve in changed:
            if curve["spec"]["family"] == "leaf_shuffled4":
                for row in curve["native_rows"]:
                    row["topology_fingerprint"] += 1
        with self.assertRaisesRegex(ValueError, "topology twin"):
            analysis.check_graphs(changed)

    def test_native_negative_identities_types_clocks_and_retained_flags(self):
        spec = declared_specs()[0]
        rows, log = make_native(spec)
        mutations = [lambda x: x.pop(), lambda x: x.__setitem__(1, copy.deepcopy(x[0])),
                     lambda x: x[0].__setitem__("N", x[0]["N"] + 1),
                     lambda x: x[0].__setitem__("m", x[0]["m"] + 1),
                     lambda x: x[1].__setitem__("phase", "warmup"),
                     lambda x: x[0].__setitem__("elapsed_ns", 0),
                     lambda x: x[0].__setitem__("process_cpu_end_ns", x[0]["process_cpu_end_ns"] + 1),
                     lambda x: x[1].__setitem__("process_cpu_start_ns", 0),
                     lambda x: x[0].__setitem__("validation", "fail"),
                     lambda x: x[0].__setitem__("elapsed_ns", "01"),
                     lambda x: x[0].__setitem__("elapsed_ns", 1 << 63)]
        for mutation in mutations:
            changed = copy.deepcopy(rows)
            mutation(changed)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                analysis.validate_native(encode_rows(changed), log, spec)
        for bad_log in (log + log.splitlines()[0] + "\n", log.replace("\"validation\": \"pass\"", "\"validation\": false", 1),
                        log + "complexity_certificate_v2 {}\n", log + "prefix complexity_certificate_v1 {}\n",
                        "\n".join(log.splitlines()[1:])):
            with self.assertRaises(ValueError):
                analysis.validate_native(encode_rows(rows), bad_log, spec)
        changed = copy.deepcopy(rows)
        changed[1]["utc_end_ns"] = changed[1]["utc_start_ns"] - 1
        unchanged_calls, flags = analysis.validate_native(encode_rows(changed), log, spec)
        self.assertEqual(len(unchanged_calls), 99)
        self.assertIn("realtime_reversed_within_call", [item["flag"] for item in flags])
        self.assertEqual(unchanged_calls[1]["elapsed_ns"], rows[1]["elapsed_ns"])

    def test_library_schema_units_cpu_selection_and_failure_cases(self):
        spec = declared_specs()[0]
        rows, _ = make_native(spec)
        document = make_library(spec, rows)
        result = analysis.validate_curve_library(document, spec, rows)
        self.assertEqual(len(result["means"]), 33)
        self.assertEqual(result["selection"]["selected_model"], "N^2")
        self.assertFalse(result["selection"]["manual_rms_exported"])
        self.assertGreater(result["selection"]["manual_reconstructed_normalized_rms"], 0.1)
        self.assertAlmostEqual(result["selection"]["cpu_coefficient_ns"], 0.001, places=12)
        mutations = [lambda x: x["benchmarks"].pop(),
                     lambda x: x["benchmarks"].__setitem__(1, copy.deepcopy(x["benchmarks"][0])),
                     lambda x: x["benchmarks"][0].__setitem__("repetition_index", True),
                     lambda x: x["benchmarks"][0].__setitem__("vertices", 4096),
                     lambda x: x["benchmarks"][0].__setitem__("time_unit", "us"),
                     lambda x: x["benchmarks"][-2].__setitem__("time_unit", "ms"),
                     lambda x: x["benchmarks"][-2].__setitem__("big_o", "N"),
                     lambda x: x["benchmarks"][-2].__setitem__("real_coefficient", 17.0),
                     lambda x: x["benchmarks"][-1].__setitem__("rms", 0.1),
                     lambda x: x["benchmarks"][0].__setitem__("real_time", x["benchmarks"][0]["real_time"] + 1),
                     lambda x: x["benchmarks"][0].__setitem__("error_occurred", False),
                     lambda x: x["benchmarks"][0].__setitem__("cpu_time", float("nan"))]
        for mutation in mutations:
            changed = copy.deepcopy(document)
            mutation(changed)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                analysis.validate_curve_library(changed, spec, rows)
        for malformed in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}'):
            with self.assertRaises(ValueError):
                analysis.parse_json(malformed)

    def test_independent_rational_ols_all_model_ties_and_power_slopes(self):
        points = [(3, 5.0), (7, 17.0), (11, 29.0)]
        rational = Fraction(3 * 5 + 7 * 17 + 11 * 29, 3**2 + 7**2 + 11**2)
        fit = analysis.fit_model(points, "N")
        self.assertEqual(fit["coefficient_ns"], float(rational))
        residual = sum((Fraction(time) - rational * N)**2 for N, time in points)
        expected_rms = math.sqrt(float(residual / 3)) / 17
        self.assertAlmostEqual(fit["normalized_rms"], expected_rms, places=15)
        ties = [dict(model=model, coefficient_ns=1.0, normalized_rms=0.5) for model in DECLARED_MODELS]
        self.assertEqual(analysis.choose_best(ties)["model"], "(1)")
        ties[2]["normalized_rms"] = 0.499
        ties[3]["normalized_rms"] = 0.499
        self.assertEqual(analysis.choose_best(ties)["model"], "N")
        for model, exponent in (("N", 1), ("N^2", 2), ("N^3", 3)):
            power = [(n, float(7 * n**exponent)) for n in (16, 32, 64, 128)]
            fits = [analysis.fit_model(power, candidate) for candidate in DECLARED_MODELS]
            self.assertEqual(analysis.choose_best(fits)["model"], model)
            self.assertAlmostEqual(analysis.log_slope(power)["log_log_exponent"], exponent, places=12)
        for model, function in (("(1)", lambda n: 13.0), ("lgN", lambda n: 7 * math.log2(n)),
                                ("NlgN", lambda n: 7 * n * math.log2(n))):
            points = [(n, function(n)) for n in (16, 32, 64, 128)]
            fits = [analysis.fit_model(points, candidate) for candidate in DECLARED_MODELS]
            self.assertEqual(analysis.choose_best(fits)["model"], model)
        with self.assertRaises(ValueError):
            analysis.log_slope([(1, 1), (1, 2)])

    def test_complete_mean_fit_summary_identities_and_independent_means(self):
        curves = [make_curve(spec)[0] for spec in declared_specs()]
        tables = analysis.aggregate(curves)
        def spec_key(row):
            return tuple(row[key] for key in ("family", "algorithm", "graph_seed", "sampling_seed", "size_order"))
        expected_mean = {}
        expected_models = set()
        for spec in declared_specs():
            raw, _ = make_native(spec)
            for n in DECLARED_SIZES:
                for invocation in range(3):
                    calls = [row for row in raw if row["n"] == n and row["invocation"] == invocation and row["phase"] == "timed"]
                    for clock in DECLARED_CLOCKS:
                        if clock in ("native_steady", "library_manual"):
                            value = Fraction(sum(row["elapsed_ns"] for row in calls), 2)
                        elif clock == "native_process_cpu":
                            value = Fraction(sum(row["process_cpu_elapsed_ns"] for row in calls), 2)
                        else:
                            value = Fraction(calls[0]["N"]**2, 1000)
                        expected_mean[(spec_key(spec), clock, n, invocation)] = value
            for clock in DECLARED_CLOCKS:
                for window in ("full11", "upper6"):
                    for model in DECLARED_MODELS:
                        expected_models.add((spec_key(spec), clock, window, model))
        actual_mean = {(spec_key(row), row["clock"], row["n"], row["invocation"]): row for row in tables["means"]}
        self.assertEqual(len(actual_mean), len(tables["means"]))
        self.assertEqual(set(actual_mean), set(expected_mean))
        self.assertEqual(len(actual_mean), 3168)
        for identity, expected in expected_mean.items():
            actual = actual_mean[identity]
            self.assertTrue(math.isclose(actual["mean_ns"], float(expected), rel_tol=2e-15, abs_tol=1e-7))
            if identity[1].startswith("native_"):
                self.assertEqual(Fraction(actual["exact_numerator"], actual["exact_denominator"]), expected)
        actual_models = {(spec_key(row), row["clock"], row["window"], row["model"]) for row in tables["model_fits"]}
        self.assertEqual(len(tables["model_fits"]), 1152)
        self.assertEqual(actual_models, expected_models)
        for row in tables["model_fits"]:
            self.assertEqual(row["observations"], 33 if row["window"] == "full11" else 18)
            self.assertEqual(row["sizes"], 11 if row["window"] == "full11" else 6)
        self.assertEqual(analysis.UPPER, DECLARED_UPPER)
        for row in tables["size_summaries"]:
            self.assertEqual(row["observations"], 6 if row["clock"].startswith("native_") else 3)
            self.assertLessEqual(row["minimum_ns"], row["median_ns"])
            self.assertLessEqual(row["median_ns"], row["maximum_ns"])
        self.assertEqual(len(tables["log_log_slopes"]), 192)
        self.assertEqual(len(tables["adjacent_slopes"]), 960)
        self.assertEqual(len(tables["google_selection"]), 24)

    def test_bound_hash_conflicts_drift_and_real_smoke_contract_requirement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            own = Path(analysis.__file__).resolve()
            source = root / "gate.py"
            source.write_text("# synthetic gate fixture, not native proof\n", encoding="utf-8")
            artifact = root / "smoke.log"
            artifact.write_text("synthetic\n", encoding="utf-8")
            smoke_path = root / "smoke.json"
            frozen = dict(parent_freeze_sha256=analysis.PARENT_SHA, driver_sha256="a" * 64,
                          binary_sha256="b" * 64, library_sha256="c" * 64, schema_smoke=str(smoke_path))
            smoke = dict(schema="current_complexity_schema_smoke_v1", validation="pass",
                         google_benchmark_commit=analysis.COMMIT,
                         driver_sha256=frozen["driver_sha256"], binary_sha256=frozen["binary_sha256"], library_sha256=frozen["library_sha256"],
                         source_sha256={str(own): analysis.digest(own), str(source): analysis.digest(source)},
                         bound_sha256={str(artifact): analysis.digest(artifact)}, schema_contract=analysis.SCHEMA_CONTRACT,
                         native_execution=True, owned_groups_verified_empty=True)
            def validate(value):
                smoke_path.write_text(json.dumps(value), encoding="utf-8")
                frozen["schema_smoke_sha256"] = analysis.digest(smoke_path)
                return analysis.validate_smoke(dict(frozen_protocol=frozen), {}, own)
            self.assertEqual(validate(smoke)["validation"], "pass")
            for key, value in (("native_execution", False), ("owned_groups_verified_empty", False),
                               ("google_benchmark_commit", "wrong"), ("binary_sha256", "d" * 64),
                               ("source_sha256", {}), ("bound_sha256", {})):
                changed = copy.deepcopy(smoke)
                changed[key] = value
                with self.subTest(key=key), self.assertRaises(ValueError):
                    validate(changed)
            changed = copy.deepcopy(smoke)
            changed["schema_contract"]["threads"] = True
            with self.assertRaisesRegex(ValueError, "contract"):
                validate(changed)
            bound = {}
            analysis.add_bound(bound, artifact, analysis.digest(artifact))
            with self.assertRaisesRegex(ValueError, "conflicting"):
                analysis.add_bound(bound, artifact, "f" * 64)
            artifact.write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "changed after"):
                analysis.check_bound(bound)


if __name__ == "__main__":
    unittest.main(verbosity=2)
