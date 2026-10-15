#!/usr/bin/env python3
"""Prepared, unexecuted analysis for the prospective current-candidate study.

This is not evidence that Google Benchmark or this parser has passed a native
schema smoke. A real, fully bound smoke receipt is mandatory at the CLI boundary.
The collector proves native provenance/lifecycle; arithmetic is reread here from
untouched native CSV and Google Benchmark JSON, without collector aggregation.
"""
import argparse
import csv
from fractions import Fraction
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import re
import statistics
import sys

COMMIT = "73d4d5e8d6d449fc8663765a42aa8aeeee844489"
PARENT_SHA = "2be7556d15b58f3f65cc380ac22b67c57fdf8aea747d651b9d648c6a1aa59d2f"
FAMILIES = ("leaf_hierarchy4", "leaf_shuffled4", "gnm_random")
ALGORITHMS = ("kkt", "multigraph_boruvka")
GRAPHS = (19000013, 19000043)
SAMPLERS = (3001, 3011)
SIZES = tuple(1 << exponent for exponent in range(10, 21))
UPPER = SIZES[5:]
CLOCKS = ("native_steady", "native_process_cpu", "library_manual", "library_process_cpu")
MODELS = ("(1)", "lgN", "N", "NlgN", "N^2", "N^3")
FIELDS = tuple("family,algorithm,n,m,N,graph_seed,sampling_seed,input_fingerprint,topology_fingerprint,size_order,invocation,phase,iteration,elapsed_ns,utc_start_ns,utc_end_ns,process_cpu_start_ns,process_cpu_end_ns,process_cpu_elapsed_ns,validation".split(","))
TEXT_FIELDS = {"family", "algorithm", "size_order", "phase", "validation"}
SPEC_FIELDS = ("family", "algorithm", "graph_seed", "sampling_seed", "size_order")
CERT_FIELDS = ("family", "algorithm", "n", "m", "graph_seed", "sampling_seed", "invocation", "input_fingerprint", "topology_fingerprint", "validation")
COMMON = {"name", "run_name", "run_type", "repetitions", "threads"}
COUNTERS = {"vertices", "edges", "graph_seed", "sampling_seed"}
TIMES = {"iterations", "real_time", "cpu_time", "time_unit"}
UNITS_NS = {"ns": 1, "us": 1000, "ms": 1000000, "s": 1000000000}
SCHEMA_CONTRACT = {
    "schema": "current_complexity_json_contract_v1",
    "google_benchmark_commit": COMMIT,
    "root_fields": ["benchmarks", "context"],
    "iteration_fields": sorted(COMMON | TIMES | COUNTERS | {"repetition_index"}),
    "ordinary_aggregate_fields": sorted(COMMON | TIMES | COUNTERS | {"aggregate_name"}),
    "big_o_fields": sorted(COMMON | {"aggregate_name", "cpu_coefficient", "real_coefficient", "big_o", "time_unit"}),
    "rms_fields": sorted(COMMON | {"aggregate_name", "rms"}),
    "ordinary_aggregates": ["mean", "median", "stddev"],
    "iteration_unit": "ms", "coefficient_unit": "ns",
    "name_suffix": "/iterations:2/repeats:3/process_time/manual_time",
    "iterations": 2, "repetitions": 3, "threads": 1,
    "reports_per_curve": 68, "iteration_reports_per_curve": 33,
    "model_order": list(MODELS),
    "selected_model_clock": "library_process_cpu",
    "manual_coefficient_model": "same_as_library_process_cpu",
    "exported_rms": "library_process_cpu_only",
    "coefficient_relative_tolerance": 2e-10,
    "rms_relative_tolerance": 2e-10, "rms_absolute_tolerance": 1e-12,
    "manual_mean_absolute_tolerance_ns": 1.0,
    "manual_mean_relative_tolerance": 5e-12,
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    with Path(path).open("rb") as stream:
        result = hashlib.sha256()
        for block in iter(lambda: stream.read(1048576), b""):
            result.update(block)
    return result.hexdigest()


def pairs_unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON field: " + key)
        result[key] = value
    return result


def finite_tree(value):
    if isinstance(value, float):
        require(math.isfinite(value), "nonfinite JSON number")
    elif isinstance(value, dict):
        for item in value.values():
            finite_tree(item)
    elif isinstance(value, list):
        for item in value:
            finite_tree(item)


def parse_json(text):
    value = json.loads(text, object_pairs_hook=pairs_unique,
                       parse_constant=lambda item: (_ for _ in ()).throw(ValueError("nonfinite JSON: " + item)))
    finite_tree(value)
    return value


def add_bound(bound, path, expected):
    path = str(Path(path).resolve())
    require(isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected), "invalid SHA256")
    require(path not in bound or bound[path] == expected, "conflicting artifact digest: " + path)
    require(digest(path) == expected, "artifact hash mismatch: " + path)
    bound[path] = expected
    return path


def checked_text(path, expected, bound):
    path = add_bound(bound, path, expected)
    value = Path(path).read_text(encoding="utf-8")
    require(digest(path) == expected, "artifact changed while reading: " + path)
    return value


def check_bound(bound):
    for path, expected in bound.items():
        require(digest(path) == expected, "artifact changed after analysis: " + path)


def schedule():
    result = []
    for family in FAMILIES:
        for graph_slot, graph in enumerate(GRAPHS):
            for sample_slot, sample in enumerate(SAMPLERS):
                algorithms = ALGORITHMS if (graph_slot + sample_slot) % 2 == 0 else ALGORITHMS[::-1]
                for algorithm in algorithms:
                    result.append(dict(family=family, algorithm=algorithm, graph_seed=graph,
                                       sampling_seed=sample, size_order="descending" if graph_slot else "ascending"))
    return result


def sizes_for(spec):
    return SIZES if spec["size_order"] == "ascending" else SIZES[::-1]


def integer(value, name, maximum=(1 << 64) - 1):
    require(type(value) is int and 0 <= value <= maximum, "invalid integer: " + name)
    return value


def number(value, name, positive=False):
    require(type(value) in (int, float) and math.isfinite(value), "invalid numeric value: " + name)
    require(value > 0 if positive else value >= 0, "invalid numeric sign: " + name)
    return float(value)


def clock_flags(row, previous):
    wall, cpu = row["elapsed_ns"], row["process_cpu_elapsed_ns"]
    utc = row["utc_end_ns"] - row["utc_start_ns"]
    threshold = max(2_000_000_000, cpu)
    flags = []
    if utc < 0:
        flags.append("realtime_reversed_within_call")
    if previous is not None and row["utc_start_ns"] < previous["utc_end_ns"]:
        flags.append("realtime_reversed_between_calls")
    if 4 * (wall - cpu) > threshold:
        flags.append("steady_exceeds_process_cpu")
    if 4 * (cpu - wall) > threshold:
        flags.append("process_cpu_exceeds_steady")
    if 4 * abs(utc - wall) > threshold:
        flags.append("utc_steady_duration_disagreement")
    return flags


def validate_native(text, log, spec):
    require(spec in schedule() and set(spec) == set(SPEC_FIELDS), "undeclared curve specification")
    require(all(type(spec[key]) is (int if key.endswith("_seed") else str) for key in SPEC_FIELDS), "curve specification type mismatch")
    reader = csv.DictReader(io.StringIO(text))
    require(tuple(reader.fieldnames or ()) == FIELDS, "native CSV header mismatch")
    raw = list(reader)
    require(len(raw) == 99, "native curve must contain 99 rows")
    expected = [(n, invocation, phase, iteration) for n in sizes_for(spec)
                for invocation in range(3) for phase, iteration in (("warmup", 0), ("timed", 0), ("timed", 1))]
    rows, flags, fingerprints = [], [], {}
    previous = None
    for index, (source, identity) in enumerate(zip(raw, expected)):
        require(set(source) == set(FIELDS) and None not in source.values(), "malformed CSV row")
        row = {}
        for key, value in source.items():
            if key in TEXT_FIELDS:
                row[key] = value
            else:
                require(isinstance(value, str) and re.fullmatch(r"0|[1-9][0-9]*", value), "noncanonical integer: " + key)
                row[key] = integer(int(value), key, (1 << 63) - 1 if key.endswith("_ns") else (1 << 64) - 1)
        require(all(row[key] == value for key, value in spec.items()), "native curve identity mismatch")
        require((row["n"], row["invocation"], row["phase"], row["iteration"]) == identity, "native ordered call identity mismatch")
        n = row["n"]
        require(row["m"] == n * (16 if spec["family"] == "gnm_random" else 32), "native edge count mismatch")
        require(row["N"] == n + row["m"], "complexity N must be n+m")
        require(row["validation"] == "pass", "native validation failed")
        require(row["elapsed_ns"] > 0 and row["process_cpu_elapsed_ns"] > 0, "nonpositive native duration")
        require(row["utc_start_ns"] > 0 and row["utc_end_ns"] > 0, "invalid UTC endpoint")
        require(row["process_cpu_end_ns"] - row["process_cpu_start_ns"] == row["process_cpu_elapsed_ns"], "CPU endpoint mismatch")
        require(previous is None or row["process_cpu_start_ns"] >= previous["process_cpu_end_ns"], "overlapping/reversed process CPU calls")
        fingerprint = (row["input_fingerprint"], row["topology_fingerprint"])
        require(n not in fingerprints or fingerprints[n] == fingerprint, "fingerprint changed within curve")
        fingerprints[n] = fingerprint
        for flag in clock_flags(row, previous):
            flags.append(dict(spec, row_index=index, n=n, invocation=row["invocation"], phase=row["phase"], iteration=row["iteration"], flag=flag))
        previous = row
        rows.append(row)
    certificates = []
    prefix = "complexity_certificate_v1 "
    for line in log.splitlines():
        if "complexity_certificate" in line:
            require(line.startswith(prefix), "malformed certificate marker")
            certificates.append(parse_json(line[len(prefix):]))
    require(len(certificates) == 33, "certificate count mismatch")
    for cert, row in zip(certificates, rows[::3]):
        require(type(cert) is dict and set(cert) == set(CERT_FIELDS), "certificate field mismatch")
        for key in CERT_FIELDS:
            require(type(cert[key]) is type(row[key]) and cert[key] == row[key], "certificate identity/value mismatch: " + key)
    return rows, flags


def check_graphs(curves):
    require(len(curves) == 24 and [item["spec"] for item in curves] == schedule(), "complete ordered 24-curve matrix required")
    fingerprints = {}
    for curve in curves:
        for row in curve["native_rows"]:
            key = (row["family"], row["n"], row["graph_seed"])
            value = (row["input_fingerprint"], row["topology_fingerprint"])
            require(key not in fingerprints or fingerprints[key] == value, "graph changed across algorithm/sampler curves")
            fingerprints[key] = value
    require(len(fingerprints) == 66, "graph identity count mismatch")
    for n in SIZES:
        for graph in GRAPHS:
            hierarchy = fingerprints[("leaf_hierarchy4", n, graph)]
            shuffled = fingerprints[("leaf_shuffled4", n, graph)]
            require(hierarchy[1] == shuffled[1] and hierarchy[0] != shuffled[0], "hierarchy/shuffled topology twin mismatch")
    return fingerprints


def base_name(spec, n=None):
    name = f'{spec["algorithm"]}/{spec["family"]}/graph_{spec["graph_seed"]}/sampler_{spec["sampling_seed"]}'
    if n is not None:
        name += "/" + str(n)
    return name + SCHEMA_CONTRACT["name_suffix"]


def model_value(model, N):
    require(N > 0 and model in MODELS, "invalid model input")
    if model == "(1)":
        return 1.0
    if model == "lgN":
        return 1.44269504088896340736 * math.log(float(N))
    if model == "N":
        return float(N)
    if model == "NlgN":
        return 1.44269504088896340736 * N * math.log(float(N))
    return math.pow(N, 2 if model == "N^2" else 3)


def fit_model(points, model):
    require(len(points) >= 2, "fit requires at least two observations")
    values = [(model_value(model, N), number(time, "fit duration", True)) for N, time in points]
    # Deliberately preserve ordinary sequential sum and source model order.
    coefficient = sum(time * g for g, time in values) / sum(g * g for g, time in values)
    residual = sum(math.pow(time - coefficient * g, 2) for g, time in values)
    mean = sum(time for _, time in values) / len(values)
    return dict(model=model, coefficient_ns=coefficient,
                normalized_rms=math.sqrt(residual / len(values)) / mean)


def choose_best(fits):
    require([item["model"] for item in fits] == list(MODELS), "model order mismatch")
    best = fits[0]
    for candidate in fits[1:]:
        if candidate["normalized_rms"] < best["normalized_rms"]:
            best = candidate
    return best


def close(actual, expected, label, relative=2e-10, absolute=0.0):
    require(math.isclose(actual, expected, rel_tol=relative, abs_tol=absolute), "numerical mismatch: " + label)


def validate_curve_library(document, spec, native_rows):
    """Validate the source-declared v1.5.2 schema; real smoke is a caller gate.

    Metadata includes independently reconstructed library means and the CPU
    selection. Native rows must already have passed validate_native.
    """
    finite_tree(document)
    require(type(document) is dict and set(document) == {"context", "benchmarks"}, "unsupported library JSON root")
    context, reports = document["context"], document["benchmarks"]
    required_context = {"date", "host_name", "num_cpus", "mhz_per_cpu", "caches", "load_avg", "library_build_type"}
    require(type(context) is dict and required_context <= set(context) <= required_context | {"executable", "cpu_scaling_enabled"}, "unsupported library context")
    require(context["library_build_type"] in ("debug", "release"), "invalid library build type")
    require(type(reports) is list and len(reports) == 68, "library report count mismatch")
    require(len(native_rows) == 99, "complete native curve required")
    native = {(row["n"], row["invocation"], row["iteration"]): row for row in native_rows if row["phase"] == "timed"}
    expected = []
    for n in sizes_for(spec):
        expected += [("iteration", n, index) for index in range(3)]
        expected += [("aggregate", n, name) for name in ("mean", "median", "stddev")]
    expected += [("aggregate", None, "BigO"), ("aggregate", None, "RMS")]
    means = []
    big_o = rms = None
    for report, (kind, n, item) in zip(reports, expected):
        require(type(report) is dict, "invalid library report")
        if kind == "iteration":
            keys = SCHEMA_CONTRACT["iteration_fields"]
        elif item == "BigO":
            keys = SCHEMA_CONTRACT["big_o_fields"]
        elif item == "RMS":
            keys = SCHEMA_CONTRACT["rms_fields"]
        else:
            keys = SCHEMA_CONTRACT["ordinary_aggregate_fields"]
        require(set(report) == set(keys), "unsupported library report fields or error row")
        run_name = base_name(spec, n)
        require(report["run_name"] == run_name and report["name"] == run_name + ("_" + str(item) if kind == "aggregate" else ""), "library run name/order mismatch")
        require(report["run_type"] == kind, "library run type mismatch")
        require(type(report["threads"]) is int and report["threads"] == 1, "library thread count mismatch")
        require(type(report["repetitions"]) is int and report["repetitions"] == 3, "library repetition count mismatch")
        if kind == "aggregate":
            require(report["aggregate_name"] == item, "library aggregate identity mismatch")
        if item == "RMS":
            number(report["rms"], "CPU RMS")
            rms = report
            continue
        expected_unit = "ns" if item == "BigO" else "ms"
        require(report["time_unit"] == expected_unit, "unsupported per-row library time unit")
        scale = UNITS_NS[report["time_unit"]]
        if item == "BigO":
            require(report["big_o"] in MODELS, "unsupported Google model")
            number(report["cpu_coefficient"], "CPU coefficient", True)
            number(report["real_coefficient"], "manual coefficient", True)
            big_o = report
            continue
        require(type(report["iterations"]) is int and report["iterations"] == (2 if kind == "iteration" else 3), "library iterations mismatch")
        for field in ("real_time", "cpu_time"):
            number(report[field], field, kind == "iteration")
        for field in COUNTERS:
            number(report[field], field)
        counters = dict(vertices=n, edges=n * (16 if spec["family"] == "gnm_random" else 32), graph_seed=spec["graph_seed"], sampling_seed=spec["sampling_seed"])
        if kind == "iteration" or item != "stddev":
            require(all(report[key] == value for key, value in counters.items()), "library graph counter mismatch")
        # The ordinary aggregate rows are retained and schema-checked, not used
        # as fit inputs or independently claimed as recomputed statistics.
        if kind != "iteration":
            continue
        require(type(report["repetition_index"]) is int and report["repetition_index"] == item, "library repetition identity mismatch")
        calls = [native[(n, item, iteration)] for iteration in (0, 1)]
        native_mean = Fraction(sum(row["elapsed_ns"] for row in calls), 2)
        manual = report["real_time"] * scale
        close(manual, float(native_mean), "manual mean versus native steady", relative=5e-12, absolute=1.0)
        means.append(dict(n=n, N=n + counters["edges"], invocation=item,
                          library_manual=manual, library_process_cpu=report["cpu_time"] * scale,
                          manual_seconds=report["real_time"] * (scale / 1e9),
                          cpu_seconds=report["cpu_time"] * (scale / 1e9)))
    require(len(means) == 33 and big_o is not None and rms is not None, "incomplete library fit inputs")
    # Google fits seconds internally; preserve that scale for its selected model
    # (scale changes can affect the last bit of near-tie floating-point scores).
    cpu_fits = [fit_model([(row["N"], row["cpu_seconds"]) for row in means], model) for model in MODELS]
    selected = choose_best(cpu_fits)
    require(big_o["big_o"] == selected["model"], "Google CPU-selected model mismatch")
    manual_fit = fit_model([(row["N"], row["manual_seconds"]) for row in means], selected["model"])
    coefficient_scale = UNITS_NS[big_o["time_unit"]]
    close(big_o["cpu_coefficient"] * coefficient_scale, selected["coefficient_ns"] * 1e9, "Google CPU coefficient")
    close(big_o["real_coefficient"] * coefficient_scale, manual_fit["coefficient_ns"] * 1e9, "Google manual coefficient uses CPU-selected model")
    close(rms["rms"], selected["normalized_rms"], "Google exported CPU RMS", absolute=1e-12)
    return dict(means=means, context=context, reports=reports,
                selection=dict(selected_model=selected["model"], cpu_coefficient_ns=selected["coefficient_ns"] * 1e9,
                               manual_coefficient_ns=manual_fit["coefficient_ns"] * 1e9,
                               cpu_normalized_rms=selected["normalized_rms"],
                               manual_reconstructed_normalized_rms=manual_fit["normalized_rms"],
                               manual_rms_exported=False))


def log_slope(points):
    xs = [math.log(N) for N, _ in points]
    ys = [math.log(number(time, "log-fit time", True)) for _, time in points]
    xmean, ymean = statistics.mean(xs), statistics.mean(ys)
    denominator = sum((x - xmean) ** 2 for x in xs)
    require(denominator > 0, "log-fit sizes must vary")
    exponent = sum((x - xmean) * (y - ymean) for x, y in zip(xs, ys)) / denominator
    intercept = ymean - exponent * xmean
    residual = sum((y - intercept - exponent * x) ** 2 for x, y in zip(xs, ys))
    return dict(log_log_exponent=exponent, log_intercept=intercept, log_rms=math.sqrt(residual / len(xs)))


def aggregate(curves):
    check_graphs(curves)
    means, models, summaries, slopes, adjacent, selections = [], [], [], [], [], []
    for curve in curves:
        spec, native, library = curve["spec"], curve["native_rows"], curve["library"]
        selection = dict(spec, **library["selection"])
        selections.append(selection)
        for item in library["means"]:
            calls = [row for row in native if row["phase"] == "timed" and row["n"] == item["n"] and row["invocation"] == item["invocation"]]
            require(len(calls) == 2, "mean requires two native calls")
            for clock in CLOCKS:
                exact = None
                if clock.startswith("native_"):
                    field = "elapsed_ns" if clock == "native_steady" else "process_cpu_elapsed_ns"
                    exact = Fraction(sum(row[field] for row in calls), 2)
                    value = float(exact)
                else:
                    value = item[clock]
                means.append(dict(spec, clock=clock, n=item["n"], N=item["N"], invocation=item["invocation"],
                                  mean_ns=value, exact_numerator=exact.numerator if exact is not None else "",
                                  exact_denominator=exact.denominator if exact is not None else ""))
        for clock in CLOCKS:
            current = [row for row in means if all(row[key] == value for key, value in spec.items()) and row["clock"] == clock]
            require(len(current) == 33, "curve/clock mean count mismatch")
            for window, sizes in (("full11", SIZES), ("upper6", UPPER)):
                points = [(row["N"], row["mean_ns"]) for row in current if row["n"] in sizes]
                fits = [fit_model(points, model) for model in MODELS]
                best = choose_best(fits)
                for fit in fits:
                    models.append(dict(spec, clock=clock, window=window, observations=len(points), sizes=len(sizes),
                                       **fit, selected_for_this_clock=fit["model"] == best["model"],
                                       google_exported_selection=(window == "full11" and clock == "library_process_cpu" and fit["model"] == selection["selected_model"])))
                slopes.append(dict(spec, clock=clock, window=window, observations=len(points), **log_slope(points)))
            previous = None
            for n in SIZES:
                subset = [row for row in current if row["n"] == n]
                N = subset[0]["N"]
                if clock.startswith("native_"):
                    field = "elapsed_ns" if clock == "native_steady" else "process_cpu_elapsed_ns"
                    values = [row[field] for row in native if row["n"] == n and row["phase"] == "timed"]
                    scope = "six_native_calls"
                else:
                    values = [row["mean_ns"] for row in subset]
                    scope = "three_library_two_call_means"
                median = statistics.median(values)
                summary = dict(spec, clock=clock, n=n, N=N, observation_scope=scope, observations=len(values),
                               minimum_ns=min(values), median_ns=median, maximum_ns=max(values), median_ns_per_N=median / N)
                summaries.append(summary)
                if previous is not None:
                    adjacent.append(dict(spec, clock=clock, lower_n=previous["n"], upper_n=n,
                                         lower_N=previous["N"], upper_N=N,
                                         adjacent_log_log_exponent=math.log(median / previous["median_ns"]) / math.log(N / previous["N"])))
                previous = summary
    result = dict(means=means, model_fits=models, size_summaries=summaries, log_log_slopes=slopes,
                  adjacent_slopes=adjacent, google_selection=selections)
    counts = {"means": 3168, "model_fits": 1152, "size_summaries": 1056,
              "log_log_slopes": 192, "adjacent_slopes": 960, "google_selection": 24}
    require({key: len(value) for key, value in result.items()} == counts, "analysis table cardinality mismatch")
    return result


def validate_smoke(info, bound, own_path):
    frozen = info["frozen_protocol"]
    require(frozen["parent_freeze_sha256"] == PARENT_SHA, "wrong parent freeze")
    text = checked_text(frozen["schema_smoke"], frozen["schema_smoke_sha256"], bound)
    smoke = parse_json(text)
    required = {"schema", "validation", "google_benchmark_commit", "driver_sha256", "binary_sha256", "library_sha256",
                "source_sha256", "bound_sha256", "schema_contract", "native_execution", "owned_groups_verified_empty"}
    require(type(smoke) is dict and set(smoke) == required, "unsupported real schema-smoke receipt")
    require(smoke["schema"] == "current_complexity_schema_smoke_v1" and smoke["validation"] == "pass", "schema smoke has not passed")
    require(smoke["google_benchmark_commit"] == COMMIT and
            json.dumps(smoke["schema_contract"], sort_keys=True) == json.dumps(SCHEMA_CONTRACT, sort_keys=True),
            "schema smoke contract mismatch")
    require(smoke["native_execution"] is True and smoke["owned_groups_verified_empty"] is True, "schema smoke lacks native/empty-group proof")
    for key in ("driver_sha256", "binary_sha256", "library_sha256"):
        require(smoke[key] == frozen[key], "schema smoke artifact mismatch: " + key)
    for key in ("source_sha256", "bound_sha256"):
        require(type(smoke[key]) is dict and smoke[key], "empty smoke hash inventory")
        for path, expected in smoke[key].items():
            add_bound(bound, path, expected)
    require(smoke["source_sha256"].get(str(own_path)) == digest(own_path), "smoke did not bind this analyzer source")
    return smoke


def analyze(capture_path, collector_path, collector_sha, output_dir):
    own = Path(__file__).resolve()
    bound = {}
    add_bound(bound, own, digest(own))
    capture_path = Path(capture_path).resolve()
    capture_sha = digest(capture_path)
    checked_text(capture_path, capture_sha, bound)
    collector_path = Path(add_bound(bound, collector_path, collector_sha))
    module_spec = importlib.util.spec_from_file_location("current_complexity_checked_collector", collector_path)
    require(module_spec is not None and module_spec.loader is not None, "cannot load declared collector")
    collector = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = collector
    module_spec.loader.exec_module(collector)
    info, records, inherited_bound = collector.load(capture_path)
    require(info["schema"] == "current_complexity_capture_v1" and info["validation"] == "pass", "capture has not passed strict reload")
    require(info["native_process_may_still_be_running"] is False, "capture contains unknown native exit")
    for key, expected in (("rows_removed", 0), ("rows_adjusted", 0), ("checked_curves", 24), ("checked_raw_rows", 2376)):
        require(type(info[key]) is int and info[key] == expected, "capture count/adjustment mismatch: " + key)
    for path, expected in inherited_bound.items():
        add_bound(bound, path, expected)
    validate_smoke(info, bound, own)
    require(len(records) == 24 and [row["spec"] for row in records] == schedule(), "capture curve schedule mismatch")
    curves, flags, library_documents = [], [], []
    for record in records:
        raw = checked_text(record["raw_csv"], record["raw_sha256"], bound)
        log = checked_text(record["log"], record["log_sha256"], bound)
        document = parse_json(checked_text(record["benchmark_json"], record["benchmark_sha256"], bound))
        rows, current_flags = validate_native(raw, log, record["spec"])
        library = validate_curve_library(document, record["spec"], rows)
        curves.append(dict(spec=record["spec"], native_rows=rows, library=library))
        flags += current_flags
        library_documents.append(dict(spec=record["spec"], context=library["context"], reports=library["reports"]))
    tables = aggregate(curves)
    diagnostic_keys = (*SPEC_FIELDS, "n", "invocation", "phase", "iteration")
    independently_flagged = [{**{key: row[key] for key in diagnostic_keys}, "flag": row["flag"]} for row in flags]
    recorded_flags = [{**{key: row[key] for key in diagnostic_keys}, "flag": flag}
                      for row in info["call_diagnostics"] for flag in row["diagnostic_flags"]]
    require(independently_flagged == recorded_flags, "independent clock flags differ from collector")
    flagged_calls = len({tuple(row[key] for key in diagnostic_keys) for row in flags})
    require(type(info["flagged_calls"]) is int and info["flagged_calls"] == flagged_calls, "independent flagged-call count differs")
    check_bound(bound)
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=False)
    written = {}
    for name, rows in tables.items():
        path = output / (name + ".csv")
        with path.open("x", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        written[str(path.resolve())] = digest(path)
    for name, value in (("clock_flags.json", flags), ("library_reports.json", library_documents)):
        path = output / name
        with path.open("x", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.write("\n")
        written[str(path.resolve())] = digest(path)
    check_bound(bound)
    check_bound(written)
    provenance = dict(schema="current_complexity_analysis_v1", validation="pass", capture=str(capture_path),
                      capture_sha256=capture_sha, rows_removed=0, rows_adjusted=0, checked_curves=24,
                      checked_raw_rows=2376, clock_flag_count=len(flags), flagged_call_count=flagged_calls, schema_contract=SCHEMA_CONTRACT,
                      table_counts={key: len(value) for key, value in tables.items()},
                      input_sha256=bound, output_sha256=written,
                      limitations=["finite-range descriptive fits; no asymptotic proof", "CPU selects Google's model; manual coefficient uses that same model",
                                   "library CPU has a different timer envelope from native CPU", "two graphs and two repeated sampler seeds do not establish a universal expectation",
                                   "ordinary aggregate rows are preserved/schema-checked, not inputs to model reconstruction"])
    with (output / "provenance.json").open("x", encoding="utf-8") as stream:
        json.dump(provenance, stream, indent=2, allow_nan=False)
        stream.write("\n")
    return provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", required=True)
    parser.add_argument("--collector", required=True)
    parser.add_argument("--collector-sha256", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = analyze(args.capture, args.collector, args.collector_sha256, args.output_dir)
    print(json.dumps({key: result[key] for key in ("validation", "checked_curves", "checked_raw_rows", "table_counts", "clock_flag_count")}, sort_keys=True))


if __name__ == "__main__":
    main()
