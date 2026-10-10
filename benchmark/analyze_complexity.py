#!/usr/bin/env python3
"""Validate the complete complexity experiment and plot finite-size evidence.

Logical counters and uninstrumented manual timings are separate measurements.
Balanced arithmetic seed means estimate expected cost on these fixtures. Fits
describe the measured window; they are not asymptotic-complexity certificates.
Only plotting needs matplotlib/numpy; validation and fitting use the stdlib.
"""

import argparse
import csv
import json
import math
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path


GRAPH_SEEDS = (17, 42, 999)
KKT_SEEDS = (0, 1, 7)
WORK_FAMILIES = ("random_4", "random_32", "star", "hierarchical_path")
TIMING_FAMILIES = WORK_FAMILIES[:3]
WORK_SIZES = (1024, 4096, 16384, 65536, 262144)
TIMING_SIZES = tuple(1024 * 2**i for i in range(7))
ALGORITHMS = ("KKT", "Kruskal")
REPETITIONS = 3
ITERATIONS = 3
FAMILY_LABELS = {
    "random_4": "Random, m = 4n", "random_32": "Random, m = 32n",
    "star": "Star", "hierarchical_path": "Hierarchical path",
}
FAMILY_COLORS = {
    "random_4": "#7437A5", "random_32": "#087F75",
    "star": "#D07916", "hierarchical_path": "#2774AE",
}
COMPONENTS = {
    "contraction": "Contraction visits",
    "filtering": "Sampling / filtering / isolation",
    "verification": "Verifier / FBT / paths / median",
    "lca": "LCA operations / tables",
    "storage": "Initialization / edge records",
    "hash_api": "Hash API items",
}
COMPONENT_COLORS = ("#2774AE", "#7437A5", "#087F75", "#68A691", "#D07916", "#A95555")
NAME_PATTERN = re.compile(
    r"(KKT|Kruskal)/(random_4|random_32|star)/graph_(\d+)/(\d+)"
    r"/iterations:3/repeats:3/manual_time"
)


def edge_count(family, n):
    return int(family.split("_")[1]) * n if family.startswith("random_") else n - 1


def integral(value, description):
    if isinstance(value, bool):
        raise ValueError(f"{description}: expected an integer")
    try:
        number = int(value)
        # CSV counters are decimal integers; avoid rounding uint64 values
        # through a float. JSON user counters may legitimately be 4096.0.
        if isinstance(value, str):
            exact = re.fullmatch(r"[+-]?\d+", value) is not None
        else:
            exact = value == number
        if not exact:
            raise ValueError()
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{description}: expected an integer") from error
    return number


def positive(value, description):
    if isinstance(value, bool):
        raise ValueError(f"{description}: expected a positive finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{description}: expected a positive finite number") from error
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{description}: expected a positive finite number")
    return number


def read_registry():
    source = Path(__file__).with_name("work_metrics.hpp").read_text()
    matches = re.findall(r'\{"(\w+)",\s*&kkt_work::WorkStats::(\w+),\s*(true|false)\}', source)
    if not matches or any(name != member for name, member, _ in matches):
        raise ValueError("cannot read the work-counter registry")
    fields = [name for name, _, _ in matches]
    if len(fields) != len(set(fields)):
        raise ValueError("duplicate work-counter registry entry")
    proxy_fields = [name for name, _, contributes in matches if contributes == "true"]
    groups = defaultdict(list)
    for name in proxy_fields:
        if name.startswith("contraction_"):
            group = "contraction"
        elif name.startswith(("isolation_", "sampling_", "kkt_")):
            group = "filtering"
        elif name.startswith(("verifier_", "fbt_", "path_")) or name == "median_entries":
            group = "verification"
        elif name.startswith("lca_"):
            group = "lca"
        elif name in ("initialized_slots", "edge_materializations"):
            group = "storage"
        elif name in ("hash_lookup_calls", "hash_insert_items"):
            group = "hash_api"
        else:
            raise ValueError(f"assign the new proxy field to a plotting component: {name}")
        groups[group].append(name)
    return fields, proxy_fields, groups


def load_work(path, fields, proxy_fields):
    expected_keys = {(family, n, graph, sample) for family in WORK_FAMILIES
                     for n in WORK_SIZES for graph in GRAPH_SEEDS for sample in KKT_SEEDS}
    header = ["case_id", "family", "n", "m", "graph_seed", "kkt_seed", *fields,
              "total_work_proxy", "validation"]
    rows = {}
    with path.open(newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != header:
            raise ValueError("work CSV header differs from the current work-metric registry")
        for line, raw in enumerate(reader, 2):
            if None in raw or any(value is None for value in raw.values()):
                raise ValueError(f"work line {line}: malformed record")
            if raw["validation"] != "pass":
                raise ValueError(f"work line {line}: failed MST validation")
            row = dict(raw)
            for field in ["n", "m", "graph_seed", "kkt_seed", *fields, "total_work_proxy"]:
                row[field] = integral(raw[field], f"work line {line}, {field}")
                if row[field] < 0:
                    raise ValueError(f"work line {line}: negative {field}")
            key = (row["family"], row["n"], row["graph_seed"], row["kkt_seed"])
            if key not in expected_keys or key in rows:
                raise ValueError(f"work line {line}: unexpected or duplicate sample {key}")
            if row["case_id"] != f'{row["family"]}_n{row["n"]}' or row["m"] != edge_count(row["family"], row["n"]):
                raise ValueError(f"work line {line}: inconsistent graph metadata")
            if row["total_work_proxy"] != sum(row[field] for field in proxy_fields):
                raise ValueError(f"work line {line}: proxy disagrees with its registered components")
            if row["current_depth"] != 0 or row["kkt_calls"] == 0 or row["contraction_edge_visits"] == 0:
                raise ValueError(f"work line {line}: missing or unbalanced instrumentation")
            rows[key] = row
    missing = expected_keys - rows.keys()
    if missing:
        raise ValueError(f"work CSV incomplete: {len(rows)}/180 observations; first missing {sorted(missing)[0]}")
    return rows


def load_timing(path):
    document = json.loads(path.read_text())
    if not isinstance(document, dict) or not isinstance(document.get("benchmarks"), list):
        raise ValueError("timing JSON must contain a benchmarks array")
    expected = {(algorithm, family, n, seed) for algorithm in ALGORITHMS
                for family in TIMING_FAMILIES for n in TIMING_SIZES for seed in GRAPH_SEEDS}
    groups = defaultdict(list)
    builtin_fits = []
    for index, raw in enumerate(document["benchmarks"]):
        if not isinstance(raw, dict):
            raise ValueError(f"timing record {index}: expected an object")
        if raw.get("error_occurred") or raw.get("error_message"):
            raise ValueError(f'timing record {index}: benchmark error: {raw.get("error_message", "unspecified")}')
        name = raw.get("name", "")
        if "big_o" in raw or "rms" in raw:
            builtin_fits.append(raw)
            continue
        run_type = raw.get("run_type")
        if run_type == "aggregate" or "aggregate_name" in raw:
            continue
        if run_type not in (None, "iteration"):
            raise ValueError(f"timing record {index}: unknown run_type {run_type!r}")
        # Older reporters omit run_type and identify statistics by suffix.
        if run_type is None and re.search(r"_(mean|median|stddev|cv|BigO|RMS)$", name):
            continue
        match = NAME_PATTERN.fullmatch(name)
        if not match or raw.get("run_name", name) != name:
            raise ValueError(f"timing record {index}: unexpected raw benchmark name {name!r}")
        algorithm, family, graph_seed, vertices = match.groups()
        n, graph_seed = int(vertices), int(graph_seed)
        key = (algorithm, family, n, graph_seed)
        if key not in expected:
            raise ValueError(f"timing record {index}: unexpected fixture {key}")
        expected_counters = {"iterations": ITERATIONS, "repetitions": REPETITIONS, "threads": 1,
                             "vertices": n, "edges": edge_count(family, n),
                             "graph_seed": graph_seed, "sampling_seeds": len(KKT_SEEDS)}
        for field, value in expected_counters.items():
            if integral(raw.get(field), f"timing record {index}, {field}") != value:
                raise ValueError(f"timing record {index}: unexpected {field}")
        multiplier = {"ns": 1, "us": 1000, "ms": 1_000_000, "s": 1_000_000_000}.get(raw.get("time_unit"))
        if multiplier is None:
            raise ValueError(f"timing record {index}: unknown time unit")
        row = {"algorithm": algorithm, "family": family, "n": n, "m": edge_count(family, n),
               "graph_seed": graph_seed, "repetition": raw.get("repetition_index"),
               "mean_time_ns": positive(positive(raw.get("real_time"), f"timing record {index}, real_time") * multiplier,
                                        f"timing record {index}, converted real_time"),
               "mean_cpu_ns": positive(positive(raw.get("cpu_time"), f"timing record {index}, cpu_time") * multiplier,
                                       f"timing record {index}, converted cpu_time")}
        groups[key].append(row)
    if groups.keys() != expected:
        missing = sorted(expected - groups.keys())
        raise ValueError(f"timing JSON incomplete: {len(groups)}/126 instances; first missing {missing[0] if missing else 'none'}")
    result = []
    for key in sorted(groups):
        rows = groups[key]
        if len(rows) != REPETITIONS:
            raise ValueError(f"timing instance {key}: expected exactly 3 raw repetitions, got {len(rows)}")
        indices = [row["repetition"] for row in rows]
        if all(index is None for index in indices):
            for index, row in enumerate(rows):
                row["repetition"] = index
        elif any(index is None for index in indices):
            raise ValueError(f"timing instance {key}: mixed explicit/implicit repetition indices")
        else:
            for row in rows:
                row["repetition"] = integral(row["repetition"], f"timing instance {key}, repetition_index")
            if sorted(row["repetition"] for row in rows) != list(range(REPETITIONS)):
                raise ValueError(f"timing instance {key}: duplicate or missing repetition indices")
        result.extend(sorted(rows, key=lambda row: row["repetition"]))
    return result, builtin_fits


def aggregate_work(rows, fields, components):
    metrics = [*fields, "total_work_proxy"]
    graph_rows, summaries = [], []
    for family in WORK_FAMILIES:
        for n in WORK_SIZES:
            m = edge_count(family, n)
            common = {"case_id": f"{family}_n{n}", "family": family, "n": n, "m": m, "input_size": n + m}
            graph_records = []
            for seed in GRAPH_SEEDS:
                selected = [rows[(family, n, seed, sample)] for sample in KKT_SEEDS]
                record = {**common, "graph_seed": seed, "sampling_seeds": len(KKT_SEEDS)}
                record.update({f"mean_{field}": statistics.fmean(row[field] for row in selected) for field in metrics})
                graph_rows.append(record)
                graph_records.append(record)
            result = {**common, "observations": len(GRAPH_SEEDS) * len(KKT_SEEDS)}
            result.update({f"mean_{field}": statistics.fmean(row[f"mean_{field}"] for row in graph_records) for field in metrics})
            result["graph_min_work_proxy"] = min(row["mean_total_work_proxy"] for row in graph_records)
            result["graph_max_work_proxy"] = max(row["mean_total_work_proxy"] for row in graph_records)
            result["work_per_input"] = result["mean_total_work_proxy"] / (n + m)
            result["recursive_vertices_per_n"] = result["mean_kkt_vertices"] / n
            result["recursive_edges_per_m"] = result["mean_kkt_edges"] / m
            result["recursive_input_per_input"] = (result["mean_kkt_vertices"] + result["mean_kkt_edges"]) / (n + m)
            for component in COMPONENTS:
                result[f"{component}_per_input"] = sum(result[f"mean_{field}"] for field in components[component]) / (n + m)
            summaries.append(result)
    return summaries, graph_rows


def aggregate_timing(rows, work):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["algorithm"], row["family"], row["n"], row["graph_seed"])].append(row)
    work_lookup = {(row["family"], row["n"]): row for row in work}
    summaries, graph_rows = [], []
    for family in TIMING_FAMILIES:
        for n in TIMING_SIZES:
            m = edge_count(family, n)
            for algorithm in ALGORITHMS:
                common = {"case_id": f"{family}_n{n}", "algorithm": algorithm, "family": family,
                          "n": n, "m": m, "input_size": n + m}
                graph_records = []
                for seed in GRAPH_SEEDS:
                    selected = grouped[(algorithm, family, n, seed)]
                    record = {**common, "graph_seed": seed, "repetitions": REPETITIONS,
                              "calls": REPETITIONS * ITERATIONS,
                              "mean_time_ns": statistics.fmean(row["mean_time_ns"] for row in selected),
                              "mean_cpu_ns": statistics.fmean(row["mean_cpu_ns"] for row in selected)}
                    graph_records.append(record)
                    graph_rows.append(record)
                result = {**common, "raw_records": len(GRAPH_SEEDS) * REPETITIONS,
                          "calls": len(GRAPH_SEEDS) * REPETITIONS * ITERATIONS,
                          "mean_time_ns": statistics.fmean(row["mean_time_ns"] for row in graph_records),
                          "mean_cpu_ns": statistics.fmean(row["mean_cpu_ns"] for row in graph_records),
                          "graph_min_time_ns": min(row["mean_time_ns"] for row in graph_records),
                          "graph_max_time_ns": max(row["mean_time_ns"] for row in graph_records)}
                result["ns_per_input"] = result["mean_time_ns"] / (n + m)
                match = work_lookup.get((family, n))
                result["ns_per_work_proxy"] = result["mean_time_ns"] / match["mean_total_work_proxy"] if match and algorithm == "KKT" else ""
                summaries.append(result)
    lookup = {(row["family"], row["n"], row["algorithm"]): row for row in summaries}
    for row in summaries:
        reference = lookup[(row["family"], row["n"], "Kruskal")]
        row["ratio_of_mean_times_to_kruskal"] = row["mean_time_ns"] / reference["mean_time_ns"]
    return summaries, graph_rows


def series_from_summaries(work, timing):
    groups = defaultdict(list)
    for row in work:
        groups[("logical_work", row["family"], "KKT")].append({**row, "value": row["mean_total_work_proxy"]})
    for row in timing:
        groups[("manual_time_ns", row["family"], row["algorithm"])].append({**row, "value": row["mean_time_ns"]})
    return {key: sorted(rows, key=lambda row: row["input_size"]) for key, rows in groups.items()}


def analyze_models(series):
    exponents, fits = [], []
    for (dataset, family, algorithm), rows in series.items():
        common = {"dataset": dataset, "family": family, "algorithm": algorithm}
        for first, last in zip(rows, rows[1:]):
            growth = last["value"] / first["value"]
            input_growth = last["input_size"] / first["input_size"]
            exponents.append({**common, "n_start": first["n"], "n_end": last["n"],
                              "input_start": first["input_size"], "input_end": last["input_size"],
                              "value_start": first["value"], "value_end": last["value"],
                              "input_growth": input_growth, "observed_growth": growth,
                              "effective_exponent": math.log(growth) / math.log(input_growth)})
        for window, selected in (("full", rows), ("upper_half", rows[len(rows) // 2:])):
            x = [float(row["input_size"]) for row in selected]
            y = [row["value"] for row in selected]
            base = {**common, "window": window, "points": len(selected),
                    "n_min": selected[0]["n"], "n_max": selected[-1]["n"],
                    "input_min": x[0], "input_max": x[-1]}
            functions = {
                "N": x,
                "N_log_N": [value * math.log(value) for value in x],
                "N_log_squared_N": [value * math.log(value)**2 for value in x],
                "N_squared": [value**2 for value in x],
            }
            for model, values in functions.items():
                coefficient = sum(a * b for a, b in zip(values, y)) / sum(value**2 for value in values)
                predicted = [coefficient * value for value in values]
                fits.append({**base, "model": model, "fit_objective": "least_squares_original_units_zero_intercept",
                             "coefficient": coefficient, "power_exponent": "", **fit_errors(y, predicted)})
            log_x, log_y = [math.log(value) for value in x], [math.log(value) for value in y]
            mx, my = statistics.fmean(log_x), statistics.fmean(log_y)
            power = sum((a - mx) * (b - my) for a, b in zip(log_x, log_y)) / sum((a - mx)**2 for a in log_x)
            coefficient = math.exp(my - power * mx)
            predicted = [coefficient * value**power for value in x]
            fits.append({**base, "model": "N_power_p", "fit_objective": "least_squares_log_units",
                         "coefficient": coefficient, "power_exponent": power, **fit_errors(y, predicted)})
    return exponents, fits


def fit_errors(observed, predicted):
    rmse = math.sqrt(statistics.fmean((a - b)**2 for a, b in zip(observed, predicted)))
    return {"rmse": rmse, "rmse_over_mean_observed": rmse / statistics.fmean(observed),
            "pointwise_relative_rmse": math.sqrt(statistics.fmean(((a - b) / a)**2 for a, b in zip(observed, predicted)))}


def write_csv(path, rows):
    if not rows:
        raise ValueError(f"refusing to write empty table {path}")
    with path.open("w", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plot_results(work, timing, exponents, output_dir):
    # Import only after all input validation has succeeded.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.labelcolor": "#263541", "text.color": "#17232E",
                         "svg.fonttype": "none", "pdf.fonttype": 42})

    def save(figure, name):
        for extension in ("png", "svg", "pdf"):
            path = output_dir / f"{name}.{extension}"
            figure.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
            if extension == "svg":
                path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
        plt.close(figure)

    def style(axis, ylabel):
        axis.set_xscale("log", base=2)
        axis.set_xlabel("Input size N = n + m")
        axis.set_ylabel(ylabel)
        axis.grid(True, alpha=0.18)
        axis.set_axisbelow(True)
        axis.spines[["top", "right"]].set_visible(False)
        axis.ticklabel_format(axis="y", style="plain")

    figure, axes = plt.subplots(2, 2, figsize=(13.4, 8.3))
    for family, axis in zip(WORK_FAMILIES, axes.flat):
        selected = [row for row in work if row["family"] == family]
        x = [row["input_size"] for row in selected]
        values = [[row[f"{component}_per_input"] for row in selected] for component in COMPONENTS]
        axis.stackplot(x, values, labels=list(COMPONENTS.values()), colors=COMPONENT_COLORS, alpha=0.9)
        axis.plot(x, [row["work_per_input"] for row in selected], color="#17232E", marker="o", markersize=4, linewidth=1.3)
        axis.set_title(FAMILY_LABELS[family], loc="left", fontweight="bold")
        style(axis, "Counted logical events / N")
        axis.set_ylim(bottom=0)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.95), ncol=3, frameon=False)
    figure.suptitle("Does counted work per input stay flat?", x=0.055, ha="left", fontsize=18, fontweight="bold")
    figure.text(0.055, 0.012, "Arithmetic means over 3 graph seeds × 3 KKT seeds. Components count different logical events; these are not CPU instructions.", fontsize=9)
    figure.tight_layout(rect=(0.02, 0.04, 1, 0.89), h_pad=2)
    save(figure, "work_per_input")

    figure, axes = plt.subplots(1, 3, figsize=(17.0, 5.6))
    for family in WORK_FAMILIES:
        selected = [row for row in work if row["family"] == family]
        axes[0].plot([row["input_size"] for row in selected], [row["recursive_input_per_input"] for row in selected],
                     marker="o", color=FAMILY_COLORS[family], label=FAMILY_LABELS[family])
    for family in TIMING_FAMILIES:
        for algorithm in ALGORITHMS:
            selected = [row for row in timing if row["family"] == family and row["algorithm"] == algorithm]
            x = np.array([row["input_size"] for row in selected])
            y = np.array([row["ns_per_input"] for row in selected])
            low = np.array([row["graph_min_time_ns"] / row["input_size"] for row in selected])
            high = np.array([row["graph_max_time_ns"] / row["input_size"] for row in selected])
            axes[1].fill_between(x, low, high, color=FAMILY_COLORS[family], alpha=0.10)
            axes[1].plot(x, y, marker="o" if algorithm == "KKT" else "s", markersize=3.5,
                         linestyle="-" if algorithm == "KKT" else "--", color=FAMILY_COLORS[family],
                         label=f'{FAMILY_LABELS[family]} · {algorithm}')
        selected = [row for row in timing if row["family"] == family and row["algorithm"] == "KKT" and row["ns_per_work_proxy"] != ""]
        axes[2].plot([row["input_size"] for row in selected], [row["ns_per_work_proxy"] for row in selected],
                     marker="o", color=FAMILY_COLORS[family], label=FAMILY_LABELS[family])
    for axis, title, ylabel in zip(axes, ("Recursive input volume", "Uninstrumented runtime", "Time / counted work"),
                                  ("Σ recursive (vertices + edges) / N", "Runtime / N (ns)", "KKT runtime / logical event (ns)")):
        style(axis, ylabel)
        axis.set_title(title, loc="left", fontweight="bold")
        axis.legend(fontsize=8, frameon=False, loc="best")
    axes[1].set_yscale("log")
    axes[2].set_yscale("log")
    figure.suptitle("Separate work growth from the cost of executing it", x=0.055, ha="left", fontsize=18, fontweight="bold")
    figure.text(0.055, 0.012, "Means across balanced seeds. Shading: min/max graph means, not confidence intervals. Time/work uses matched sizes and is a diagnostic, not primitive latency.", fontsize=9)
    figure.tight_layout(rect=(0.015, 0.045, 1, 0.93), w_pad=2)
    save(figure, "normalized_costs")

    figure, axes = plt.subplots(2, 2, figsize=(13.4, 8.0), sharey=True)
    for family, axis in zip(WORK_FAMILIES, axes.flat):
        for dataset, algorithm, label, color, marker in (
            ("logical_work", "KKT", "KKT counted work", "#087F75", "o"),
            ("manual_time_ns", "KKT", "KKT runtime", "#7437A5", "s"),
            ("manual_time_ns", "Kruskal", "Kruskal runtime", "#2774AE", "^"),
        ):
            selected = [row for row in exponents if row["family"] == family and row["dataset"] == dataset and row["algorithm"] == algorithm]
            if selected:
                axis.plot([math.sqrt(row["input_start"] * row["input_end"]) for row in selected],
                          [row["effective_exponent"] for row in selected], marker=marker, label=label, color=color)
        axis.axhline(1, color="#17232E", linestyle="--", alpha=0.65, linewidth=1)
        style(axis, "Local effective exponent p")
        axis.set_title(FAMILY_LABELS[family], loc="left", fontweight="bold")
        axis.legend(fontsize=9, frameon=False)
    figure.suptitle("Finite-size slopes are not asymptotic orders", x=0.055, ha="left", fontsize=18, fontweight="bold")
    figure.text(0.055, 0.012, "p = log(cost₂ / cost₁) / log(N₂ / N₁); x is the geometric midpoint. Work intervals grow 4×; runtime intervals grow 2×. Dashed p = 1 is linear growth.", fontsize=9)
    figure.tight_layout(rect=(0.02, 0.04, 1, 0.94), h_pad=2)
    save(figure, "effective_exponents")


def write_report(output_dir, work, timing, fits, builtin_fits):
    powers = {(row["dataset"], row["family"], row["algorithm"], row["window"]): row["power_exponent"]
              for row in fits if row["model"] == "N_power_p"}
    lines = [
        "# Measured complexity diagnostics", "",
        "Validated 180 logical-work observations (20 graph cases × 3 graph seeds × 3 KKT seeds) "
        "and 378 raw timing records (126 benchmark instances × 3 repetitions). Each timing record "
        "averages exactly three invocations, cycling KKT seeds 0, 1, 7: 1,134 timed calls total. "
        "All measured MST outputs passed the harness's checks; the work CSV records `pass` and "
        "the timing JSON contains no benchmark errors.", "",
        "Work and timing summaries use arithmetic means: mean across sampling seeds or repetition "
        "batches within each graph, then mean across graph seeds 17, 42, 999. Every graph receives "
        "equal weight. The three seeds are a small empirical sample, not an exact expectation. "
        "Graph ranges are descriptive min/max values, not confidence intervals. Repeated timings "
        "are not additional independent graphs.", "",
        "## Counted work", "",
        "| Family | Events/N at n=1,024 | Events/N at n=262,144 | Change | Power p, full / upper half |",
        "|---|---:|---:|---:|---:|",
    ]
    for family in WORK_FAMILIES:
        selected = [row for row in work if row["family"] == family]
        first, last = selected[0], selected[-1]
        full = powers[("logical_work", family, "KKT", "full")]
        upper = powers[("logical_work", family, "KKT", "upper_half")]
        lines.append(f'| {FAMILY_LABELS[family]} | {first["work_per_input"]:.3f} | {last["work_per_input"]:.3f} | '
                     f'{last["work_per_input"] / first["work_per_input"]:.3f}× | {full:.3f} / {upper:.3f} |')
    lines += ["", "## Uninstrumented manual time", "",
              "| Family | Algorithm | ns/N at n=1,024 | ns/N at n=65,536 | Power p, full / upper half |",
              "|---|---|---:|---:|---:|"]
    for family in TIMING_FAMILIES:
        for algorithm in ALGORITHMS:
            selected = [row for row in timing if row["family"] == family and row["algorithm"] == algorithm]
            full = powers[("manual_time_ns", family, algorithm, "full")]
            upper = powers[("manual_time_ns", family, algorithm, "upper_half")]
            lines.append(f'| {FAMILY_LABELS[family]} | {algorithm} | {selected[0]["ns_per_input"]:.3f} | '
                         f'{selected[-1]["ns_per_input"]:.3f} | {full:.3f} / {upper:.3f} |')
    lines += ["", "KKT / Kruskal ratios below divide the arithmetic mean times; they are not means of paired ratios. "
              "Values below 1 favor KKT. Losses are retained.", "",
              "| Family | Smallest-size ratio | Largest-size ratio | Range over all seven sizes |",
              "|---|---:|---:|---:|"]
    for family in TIMING_FAMILIES:
        ratios = [row["ratio_of_mean_times_to_kruskal"] for row in timing if row["family"] == family and row["algorithm"] == "KKT"]
        lines.append(f'| {FAMILY_LABELS[family]} | {ratios[0]:.3f} | {ratios[-1]:.3f} | {min(ratios):.3f}–{max(ratios):.3f} |')
    lines += [
        "", "## Interpretation and limits", "",
        "- Input size is `N = n + m`. Each family has fixed density, and fits never pool families. "
        "The counter window spans n=1,024…262,144 (five points); timing spans n=1,024…65,536 (seven points). "
        "Upper-half fits use the largest three and four points respectively.",
        "- The four fixed models are `cN`, `cN ln N`, `cN (ln N)^2`, and `cN²`, each fitted by "
        "least squares in original units with zero intercept. `rmse_over_mean_observed` divides "
        "the original-unit RMSE by the mean observed cost; `pointwise_relative_rmse` is the RMS "
        "of each point's relative residual. The free-power model fits `ln cost = ln c + p ln N`. "
        "Both fitting objectives and all model errors are retained; no best fit is declared to be an actual Big-O bound.",
        "- Local slopes compare adjacent arithmetic means. Curvature, short windows, cache and memory "
        "effects, allocation, and timing noise can change effective exponents. Flat work/N is evidence "
        "about the counted work on these fixtures, not a proof of expected linear time on all graphs.",
        "- The work proxy adds distinct logical events: loop visits, table writes, explicit initialization "
        "slots, edge materializations, and hash API items. It can count a visit and a copy separately. "
        "It excludes hash probes/collisions/rehashing, allocator internals, implicit growth copies, "
        "deallocation work, cache misses, and CPU instructions. Recursive input volume is a separate "
        "diagnostic and is not added again to the proxy.",
        "- Star and hierarchical-path fixtures are structural controls. The star finishes on its first "
        "contraction, so KKT seed labels do not create different execution paths there. The hierarchical "
        "path probes repeated recursive contraction; it has logical counters only in this protocol.",
        "- Runtime measures the common edge-list boundary, including KKT input conversion and temporary "
        "input destruction. Fixture generation, oracle/certificate work, result checks, and returned-result "
        "destruction are outside manual timing. Counter collection runs separately; time/work combines "
        "matched fixture sizes and is a diagnostic ratio, not the latency of a single operation.",
        "- Google Benchmark 1.5.2 chooses its automatic Big-O model from CPU time, then fits manual "
        "time to that same model. Builtin rows are preserved in `builtin_complexity.json`, separately "
        "from the independent manual-time fits. The library's CPU-frequency metadata is not used. "
        "These timings are not automatically combined with earlier benchmark protocols.",
        "- Benchmark instances run in registration order, without randomized algorithm order or "
        "a paired timing schedule. Order, warm-cache behavior, thermal drift, and clock noise can "
        "affect comparisons. Three repetition batches provide repeated measurements, not "
        "statistical certainty. The build and host protocol must be taken from the accompanying "
        "experiment metadata, not inferred from older Make-based measurements.",
        "", "## Artifacts", "",
        "- `work_summary.csv` and `graph_work_summary.csv`: overall and per-graph arithmetic counter means.",
        "- `timing_summary.csv`, `graph_timing_summary.csv`, and `timing_repetitions.csv`: means and normalized raw timing records.",
        "- `effective_exponents.csv` and `model_fits.csv`: adjacent slopes and every finite-window fit.",
        "- `work_per_input.{png,svg,pdf}`: counted work components divided by input size.",
        "- `normalized_costs.{png,svg,pdf}`: recursive volume, runtime/input, and runtime/work proxy.",
        "- `effective_exponents.{png,svg,pdf}`: local work and runtime slopes.",
        f"- `builtin_complexity.json`: {len(builtin_fits)} builtin Big-O/RMS records, retained without using their selected models.",
    ]
    (output_dir / "report.md").write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-csv", type=Path, required=True)
    parser.add_argument("--timing-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        fields, proxy_fields, components = read_registry()
        raw_work = load_work(args.work_csv, fields, proxy_fields)
        raw_timing, builtin_fits = load_timing(args.timing_json)
        work, graph_work = aggregate_work(raw_work, fields, components)
        timing, graph_timing = aggregate_timing(raw_timing, work)
        exponents, fits = analyze_models(series_from_summaries(work, timing))
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for filename, rows in (("work_summary.csv", work), ("graph_work_summary.csv", graph_work),
                               ("timing_summary.csv", timing), ("graph_timing_summary.csv", graph_timing),
                               ("timing_repetitions.csv", raw_timing), ("effective_exponents.csv", exponents),
                               ("model_fits.csv", fits)):
            write_csv(args.output_dir / filename, rows)
        (args.output_dir / "builtin_complexity.json").write_text(json.dumps(builtin_fits, indent=2, allow_nan=False) + "\n")
        write_report(args.output_dir, work, timing, fits, builtin_fits)
        plot_results(work, timing, exponents, args.output_dir)
        print(f"Validated {len(raw_work)} work observations and {len(raw_timing)} timing records; wrote {args.output_dir}")
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"complexity analysis failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
