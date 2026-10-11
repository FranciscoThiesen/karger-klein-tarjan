#!/usr/bin/env python3
"""Validate complete graph-shape campaigns and report all wins and losses.

Default: eight families at n=4096,16384,65536, three graph seeds, three KKT
seeds, four repetitions, one warmup. Explicit --sizes still requires every
family at each requested size; --sizes 256 selects the smoke matrix.
Timing uses paired hierarchical medians. Optional untimed work uses balanced
arithmetic seed means and is never pooled into the timing observations.
"""

import argparse
import copy
import csv
import hashlib
import itertools
import json
import math
import re
import statistics
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import analyze_diverse as common
from analyze_complexity import read_registry
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np


FAMILIES = ("preferential_attachment", "small_world", "multi_hub",
            "community_sparse", "balanced_bipartite", "balanced_binary_tree",
            "hub", "random_4")
NAMES = {
    "preferential_attachment": "Preferential attachment",
    "small_world": "Small world",
    "multi_hub": "Sixteen hubs",
    "community_sparse": "Sparse communities",
    "balanced_bipartite": "Balanced bipartite",
    "balanced_binary_tree": "Balanced binary tree",
    "hub": "Hub control",
    "random_4": "Random m=4n control",
}
MAIN_SIZES = (4096, 16384, 65536)
WORK_PREFIX = ("case_id", "family", "n", "m", "graph_seed", "kkt_seed",
               "input_fingerprint", "max_degree", "leaf_vertices", "regime")
WORK_DERIVED_INTS = ("light_edge_incidences", "heavy_edge_incidences",
                     "recursive_vertex_volume", "recursive_edge_volume")
WORK_RATIOS = ("all_kkt_vertices_over_n", "all_kkt_edges_over_m",
               "root_after_two_edges_over_m", "sample_retention_fraction",
               "light_fraction", "heavy_fraction")


def validate_options(sizes, repetitions):
    sizes = tuple(sizes)
    if not sizes or sizes != tuple(sorted(set(sizes))):
        raise ValueError("sizes must be nonempty, distinct, and ascending")
    if sizes != (256,) and any(n not in MAIN_SIZES for n in sizes):
        raise ValueError("sizes must be drawn from 4096,16384,65536, or be exactly 256 for smoke")
    if repetitions <= 0 or repetitions > 1000 or repetitions % 4:
        raise ValueError("repetitions must be a positive multiple of four, at most 1000")
    return sizes


def dimensions(sizes):
    result = {}
    for family in FAMILIES:
        for n in sizes:
            if family == "preferential_attachment":
                m = 4 * n - 10
            elif family == "multi_hub":
                m = 4 * n - 49
            elif family == "balanced_binary_tree":
                m = n - 1
            else:
                m = 4 * n
            result[f"{family}_n{n}"] = {"case_id": f"{family}_n{n}",
                "family": family, "profile": family, "n": n, "m": m}
    return result


def integer(value, context):
    if not isinstance(value, str) or re.fullmatch(r"\d+", value) is None:
        raise ValueError(f"{context}: expected an unsigned decimal integer")
    return int(value)


def read_csv(path, fields):
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != tuple(fields):
            raise ValueError(f"{path}: CSV header differs from the required schema")
        for line, raw in enumerate(reader, 2):
            if None in raw or any(value is None for value in raw.values()):
                raise ValueError(f"{path}:{line}: malformed CSV row")
            yield line, raw


def check_case(row, expected, context):
    case = expected.get(row["case_id"])
    if case is None or any(row[key] != case[key] for key in ("family", "n", "m")):
        raise ValueError(f"{context}: unexpected case, family, or graph dimensions")
    if row["graph_seed"] not in common.GRAPH_SEEDS or row["kkt_seed"] not in common.KKT_SEEDS:
        raise ValueError(f"{context}: unexpected graph or sampling seed")


def load_measurements(path, sizes=MAIN_SIZES, repetitions=4):
    sizes = validate_options(sizes, repetitions)
    expected = dimensions(sizes)
    rows = {}
    for line, raw in read_csv(path, common.FIELDS):
        context = f"timing line {line}"
        row = dict(raw)
        for field in common.INTEGER_FIELDS:
            row[field] = integer(raw[field], f"{context} {field}")
        check_case(row, expected, context)
        if row["validation"] != "pass" or row["elapsed_ns"] <= 0:
            raise ValueError(f"{context}: failed validation or nonpositive elapsed time")
        if row["algorithm"] not in common.ALGORITHMS or row["repetition"] not in range(repetitions):
            raise ValueError(f"{context}: unexpected algorithm or repetition")
        if row["warmups"] != 1:
            raise ValueError(f"{context}: the shapes protocol requires exactly one warmup")
        g = common.GRAPH_SEEDS.index(row["graph_seed"])
        s = common.KKT_SEEDS.index(row["kkt_seed"])
        order = (common.ALGORITHMS.index(row["algorithm"]) - row["repetition"] - g - s) % 4
        if row["order"] != order:
            raise ValueError(f"{context}: execution order differs from the rotating harness schedule")
        key = (row["case_id"], row["graph_seed"], row["kkt_seed"], row["repetition"], row["algorithm"])
        if key in rows:
            raise ValueError(f"{context}: duplicate observation {key}")
        rows[key] = row
    required = set(itertools.product(expected, common.GRAPH_SEEDS, common.KKT_SEEDS,
                                     range(repetitions), common.ALGORITHMS))
    if set(rows) != required:
        raise ValueError(f"incomplete timing matrix: expected {len(required)} rows, got {len(rows)}; "
                         f"missing {len(required - set(rows))}")
    # Exact per-row schedule plus full repetitions implies unique blocks and
    # balanced positions; check the latter explicitly as a protocol invariant.
    for case, g, s in itertools.product(expected, common.GRAPH_SEEDS, common.KKT_SEEDS):
        for algorithm in common.ALGORITHMS:
            positions = Counter(rows[case, g, s, rep, algorithm]["order"] for rep in range(repetitions))
            if positions != Counter({position: repetitions // 4 for position in range(4)}):
                raise ValueError(f"unbalanced positions for {case}/{g}/{s}/{algorithm}")
    return rows, list(expected.values())


def load_work(path, sizes):
    expected = dimensions(sizes)
    counter_fields, proxy_fields, _ = read_registry()
    fields = (*WORK_PREFIX, *counter_fields, *WORK_DERIVED_INTS, *WORK_RATIOS,
              "total_work_proxy", "validation")
    numeric = ("n", "m", "graph_seed", "kkt_seed", "input_fingerprint", "max_degree",
               "leaf_vertices", *counter_fields, *WORK_DERIVED_INTS, "total_work_proxy")
    rows = {}
    for line, raw in read_csv(path, fields):
        context = f"work line {line}"
        row = dict(raw)
        for field in numeric:
            row[field] = integer(raw[field], f"{context} {field}")
        for field in WORK_RATIOS:
            try:
                row[field] = float(raw[field])
            except ValueError as error:
                raise ValueError(f"{context}: invalid {field}") from error
            if not math.isfinite(row[field]) or row[field] < 0:
                raise ValueError(f"{context}: nonfinite or negative {field}")
        check_case(row, expected, context)
        if row["validation"] != "pass_certified_oracle_exact_ids":
            raise ValueError(f"{context}: missing certified exact-ID validation")
        if not 1 <= row["max_degree"] < row["n"] or row["leaf_vertices"] > row["n"]:
            raise ValueError(f"{context}: invalid degree or leaf count")
        if row["family"] == "balanced_binary_tree" and (row["max_degree"], row["leaf_vertices"]) != (3, row["n"] // 2):
            raise ValueError(f"{context}: binary-tree degree metrics differ from the fixture")
        if row["family"] == "balanced_bipartite" and row["max_degree"] > row["n"] // 2:
            raise ValueError(f"{context}: degree exceeds the opposite partition size")
        identities = {
            "current_depth": 0,
            "verifier_calls": row["sampling_calls"],
            "verifier_edges": row["sampling_edge_visits"],
            "light_edge_incidences": row["filtered_edges"],
            "heavy_edge_incidences": row["verifier_edges"] - row["filtered_edges"],
            "recursive_vertex_volume": row["kkt_vertices"] - row["n"],
            "recursive_edge_volume": row["kkt_edges"] - row["m"],
            "total_work_proxy": sum(row[field] for field in proxy_fields),
        }
        if any(row[key] != value or value < 0 for key, value in identities.items()):
            raise ValueError(f"{context}: inconsistent counter or derived volume")
        if row["kkt_calls"] < 1 or row["contraction_calls"] < 1 or row["sampled_edges"] > row["sampling_edge_visits"]:
            raise ValueError(f"{context}: missing instrumentation or impossible sample volume")
        ratios = {
            "all_kkt_vertices_over_n": (row["kkt_vertices"], row["n"]),
            "all_kkt_edges_over_m": (row["kkt_edges"], row["m"]),
            "root_after_two_edges_over_m": (row["root_after_two_edges"], row["m"]),
            "sample_retention_fraction": (row["sampled_edges"], row["sampling_edge_visits"]),
            "light_fraction": (row["filtered_edges"], row["verifier_edges"]),
            "heavy_fraction": (row["heavy_edge_incidences"], row["verifier_edges"]),
        }
        for field, (numerator, denominator) in ratios.items():
            target = numerator / denominator if denominator else 0.0
            if not math.isclose(row[field], target, rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError(f"{context}: inconsistent {field}")
        if row["root_after_two_edges"] > row["m"] or row["root_after_two_vertices"] > row["n"]:
            raise ValueError(f"{context}: contraction output exceeds root input")
        if row["sampling_calls"]:
            regime = "sampling_with_heavy_removal" if row["heavy_edge_incidences"] else "sampling_without_heavy_removal"
            if row["root_after_two_edges"] == 0 or row["root_after_two_vertices"] == 0:
                raise ValueError(f"{context}: sampled after empty root contraction")
        else:
            regime = {1: "one_boruvka_round", 2: "two_boruvka_rounds"}.get(row["contraction_calls"])
            if row["kkt_calls"] != 1 or row["root_after_two_edges"] != 0:
                raise ValueError(f"{context}: no-sampling regime unexpectedly recursed")
        if row["regime"] != regime:
            raise ValueError(f"{context}: inconsistent execution regime")
        key = (row["case_id"], row["graph_seed"], row["kkt_seed"])
        if key in rows:
            raise ValueError(f"{context}: duplicate observation {key}")
        rows[key] = row
    required = set(itertools.product(expected, common.GRAPH_SEEDS, common.KKT_SEEDS))
    if set(rows) != required:
        raise ValueError(f"incomplete work matrix: expected {len(required)} rows, got {len(rows)}")
    for case, graph_seed in itertools.product(expected, common.GRAPH_SEEDS):
        records = [rows[case, graph_seed, seed] for seed in common.KKT_SEEDS]
        for field in ("input_fingerprint", "max_degree", "leaf_vertices"):
            if len({row[field] for row in records}) != 1:
                raise ValueError(f"work fixture {case}/{graph_seed}: inconsistent {field}")
    return rows


def summarize_work(rows, cases):
    summaries, graphs = [], []
    metrics = (*WORK_RATIOS, "max_degree", "leaf_vertices", "total_work_proxy")
    for case in cases:
        selected = [rows[case["case_id"], g, s] for g in common.GRAPH_SEEDS for s in common.KKT_SEEDS]
        by_graph = []
        for g in common.GRAPH_SEEDS:
            records = [row for row in selected if row["graph_seed"] == g]
            item = {**case, "graph_seed": g,
                    **{field: statistics.mean(row[field] for row in records) for field in metrics}}
            graphs.append(item)
            by_graph.append(item)
        summary = {**case, "observations": len(selected),
                   "sampling_calls_min": min(row["sampling_calls"] for row in selected),
                   "sampling_calls_max": max(row["sampling_calls"] for row in selected),
                   "one_round_observations": sum(row["regime"] == "one_boruvka_round" for row in selected),
                   "two_round_observations": sum(row["regime"] == "two_boruvka_rounds" for row in selected),
                   "sampling_observations": sum(row["sampling_calls"] > 0 for row in selected)}
        for field in metrics:
            values = [row[field] for row in by_graph]
            summary[field + "_mean"] = statistics.mean(values)
            summary[field + "_graph_min"] = min(values)
            summary[field + "_graph_max"] = max(values)
        summaries.append(summary)
    return summaries, graphs


def errorbars(records, value, lower, upper):
    return np.array([[row[value] - row[lower] for row in records],
                     [row[upper] - row[value] for row in records]])


def plot_ratios(cases, comparisons, output):
    lookup = {(row["case_id"], row["reference"]): row for row in comparisons if row["algorithm"] == "kkt"}
    records = [lookup[case["case_id"], ref] for case in cases for ref in common.ALGORITHMS[1:]]
    lower = min(1.0, min(row["graph_min_ratio"] for row in records)) / 1.25
    upper = max(1.0, max(row["graph_max_ratio"] for row in records)) * 1.25
    figure, axes = plt.subplots(4, 2, figsize=(14, 14), squeeze=False)
    handles = []
    for index, family in enumerate(FAMILIES):
        axis = axes.flat[index]
        selected = [case for case in cases if case["family"] == family]
        x = [case["n"] for case in selected]
        for reference in common.ALGORITHMS[1:]:
            rows = [lookup[case["case_id"], reference] for case in selected]
            line = axis.errorbar(x, [row["paired_runtime_ratio"] for row in rows],
                yerr=errorbars(rows, "paired_runtime_ratio", "graph_min_ratio", "graph_max_ratio"),
                color=common.COLORS[reference], marker=common.MARKERS[reference], capsize=3, linewidth=1.8)
            if index == 0:
                handles.append(line)
        axis.axhline(1, color="#263442", linestyle="--", linewidth=1)
        axis.set_xscale("log", base=2)
        axis.set_yscale("log", base=2)
        axis.set_ylim(lower, upper)
        axis.set_xticks(x, [f"{n:,}" for n in x])
        axis.set_title(NAMES[family], loc="left", fontsize=12, fontweight="bold")
        axis.set_xlabel("Vertices")
        axis.set_ylabel("KKT / competitor runtime")
        axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: common.ratio_label(value)))
        common.style_axis(axis)
    figure.suptitle("Graph shapes: KKT versus every competitor", x=0.07, ha="left", fontsize=20, fontweight="bold")
    figure.legend(handles, [f"KKT / {common.ALGORITHM_NAMES[a]}" for a in common.ALGORITHMS[1:]],
                  loc="upper left", bbox_to_anchor=(0.063, 0.962), ncol=3, frameon=False)
    figure.text(0.07, 0.012, "Below 1× favors KKT. Shared logarithmic ratio scale. Bars span three graph-level medians, not confidence intervals.\n"
                "All requested shapes and sizes are retained; lines connect measured points only.", fontsize=10)
    figure.tight_layout(rect=(0.025, 0.05, 1, 0.94), h_pad=2.1, w_pad=2.3)
    common.save_figure(figure, output, "shape_ratios")


def plot_work(cases, summaries, output):
    lookup = {row["case_id"]: row for row in summaries}
    figure, axes = plt.subplots(1, 2, figsize=(13.5, max(7.0, 0.28 * len(cases) + 2)), sharey=True)
    positions = np.arange(len(cases))
    for index, case in enumerate(cases):
        row = lookup[case["case_id"]]
        for axis, metric, color in zip(axes, ("root_after_two_edges_over_m", "all_kkt_edges_over_m"), ("#087F75", "#7437A5")):
            mean = row[metric + "_mean"]
            axis.errorbar(mean, index, xerr=[[mean - row[metric + "_graph_min"]],
                                             [row[metric + "_graph_max"] - mean]],
                          fmt="o", color=color, capsize=3, markersize=4)
    axes[0].set_yticks(positions, [f"{NAMES[case['family']]} · {case['n']:,}" for case in cases])
    axes[0].invert_yaxis()
    axes[0].set_xlim(-0.025, 1.025)
    axes[0].set_xticks([0, 0.25, 0.5, 0.75, 1])
    axes[0].xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{100 * value:.0f}%"))
    axes[0].set_title("Root edges remaining after contraction", loc="left", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("Remaining root edges / original m")
    axes[1].axvline(1, color="#52616D", linestyle="--", linewidth=1)
    axes[1].set_title("Total recursive KKT edge-input volume", loc="left", fontsize=13, fontweight="bold")
    axes[1].set_xlabel("Σ subproblem edges / original m (root included)")
    upper = max(row["all_kkt_edges_over_m_graph_max"] for row in summaries)
    tick_step = 0.1 if upper <= 1.6 else 0.25
    tick_end = max(1.1, math.ceil((upper - 1) / tick_step) * tick_step + 1)
    axes[1].set_xlim(0.98, tick_end + 0.02)
    axes[1].set_xticks(np.arange(1, tick_end + tick_step / 2, tick_step))
    for axis in axes:
        common.style_axis(axis)
    figure.suptitle("Separate untimed diagnosis of contraction and recursion", x=0.025, ha="left", fontsize=18, fontweight="bold")
    figure.text(0.025, 0.014, "Arithmetic seed means; bars span graph-level means. Zero remaining edges includes an earlier one-round finish.\n"
                "Edge-input volume excludes repeated internal passes. These counters do not isolate a causal sampling speedup.", fontsize=9)
    figure.tight_layout(rect=(0.015, 0.055, 1, 0.96), w_pad=2.6)
    common.save_figure(figure, output, "shape_work")


def write_report(output, input_path, rows, cases, repetitions, summaries, comparisons, work_summaries):
    lookup = {(row["case_id"], row["algorithm"]): row for row in summaries}
    paired = {(row["case_id"], row["reference"]): row for row in comparisons if row["algorithm"] == "kkt"}
    leaders, graph_leaders = [], []
    for case in cases:
        records = [paired[case["case_id"], reference] for reference in common.ALGORITHMS[1:]]
        if all(row["paired_runtime_ratio"] < 1 for row in records): leaders.append(case["case_id"])
        if all(row["graph_max_ratio"] < 1 for row in records): graph_leaders.append(case["case_id"])
    text = ["# Graph-shape experiment", "",
        f"Validated **{len(cases)} cases and {len(rows):,} timed observations**, with three graph seeds, "
        f"three sampling-seed labels, {repetitions} repetitions, and one warmup per algorithm/seed pair. "
        f"The complete requested matrix retains all eight families at sizes {', '.join(str(n) for n in sorted({c['n'] for c in cases}))}. "
        "Six added shapes and the hub/random-4 controls were selected before these measurements; no family is dropped according to its result.", "",
        common.AGGREGATION, "", "Lower ratios favor KKT. Displayed runtime medians and paired ratios are aggregated separately; "
        "dividing displayed times need not reproduce the paired ratios.", "",
        "| Case | KKT ms | Kruskal ms | Prim ms | Borůvka ms | KKT/Kruskal | KKT/Prim | KKT/Borůvka |",
        "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for case in cases:
        cid = case["case_id"]
        times = [f"{lookup[cid, a]['median_ms']:.3f}" for a in common.ALGORITHMS]
        ratios = [f"{paired[cid, a]['paired_runtime_ratio']:.3f}×" for a in common.ALGORITHMS[1:]]
        text.append("| " + " | ".join([cid, *times, *ratios]) + " |")
    listing = lambda values: ", ".join(f"`{value}`" for value in values) or "none"
    text += ["", "KKT leads all competitors by paired case medians in: " + listing(leaders) + ".",
             "The stricter descriptive check, a lead on every graph-level median against every competitor, holds in: " + listing(graph_leaders) + ".", "",
             "![KKT against all competitors on every measured shape](shape_ratios.png)", "",
             "All individual loss counts, ties, and graph-level ratio ranges remain in [comparisons.csv](comparisons.csv). "
             "[summary.csv](summary.csv) retains every algorithm's runtime, and [graph_summary.csv](graph_summary.csv) retains every graph seed."]
    if work_summaries:
        largest = max(case["n"] for case in cases)
        text += ["", "## Separate logical-work diagnosis", "",
            "The untimed probe certifies its reference MST independently and checks exact KKT IDs. "
            "Work summaries use arithmetic means across sampling seeds within each graph and then across the three graphs. "
            "They are separate from timing medians and cannot establish that sampling caused a runtime advantage.", "",
            f"At n={largest:,}, root reduction and recursion are:", "",
            "| Family | Mean maximum degree | Mean leaves | Root edges retained | Sampling calls, range | Σm/m, mean | Heavy fraction, mean |",
            "|---|---:|---:|---:|---:|---:|---:|"]
        for row in work_summaries:
            if row["n"] != largest: continue
            root_fraction = row["root_after_two_edges_over_m_mean"]
            retained = "<0.01%" if 0 < root_fraction < 0.0001 else f"{100 * root_fraction:.2f}%"
            text.append(f"| {NAMES[row['family']]} | {row['max_degree_mean']:.1f} | {row['leaf_vertices_mean']:.1f} | "
                f"{retained} | {row['sampling_calls_min']}–{row['sampling_calls_max']} | "
                f"{row['all_kkt_edges_over_m_mean']:.4f} | {100 * row['heavy_fraction_mean']:.2f}% |")
        text += ["", "![Contraction and recursive edge volume](shape_work.png)", "",
            "Zero root-retained edges includes a finish after the first contraction. Heavy fractions divide summed heavy-edge "
            "incidences by verifier input incidences within each observation before averaging; they are not fractions of distinct "
            "original edges. Σm includes every recursive KKT input, including the root, but omits repeated internal passes. "
            "[work_summary.csv](work_summary.csv) retains all sizes and execution regimes; [graph_work_summary.csv](graph_work_summary.csv) retains graph-level means."]
    text += ["", "## Limits", "",
        "These are synthetic models, not representative application datasets or a workload-weighted ranking. "
        "Three graph seeds are the independent graph samples; sampling labels and repetitions are not extra graphs. "
        "Graph ranges are descriptive, not confidence intervals, and no statistical significance or asymptotic crossover is claimed. "
        "Lines connect measured sizes only. Family weights are distinct and randomized; topology labels alone do not describe every real graph with a similar name.", "",
        "All four algorithms use the common tuple-edge-list boundary. KKT conversion and temporary input destruction are included; "
        "fixture generation, reference certification, result checks, and returned-result destruction are excluded. "
        "The rotating order is balanced within each graph/sampling pair. Ordinary desktop scheduling, cache/allocator state, and "
        "power/thermal variation can still affect measurements. Consult campaign metadata for binary, source, and build provenance.", ""]
    (output / "report.md").write_text("\n".join(text))
    return {"input_csv": str(input_path), "case_count": len(cases), "observation_count": len(rows),
            "sizes": sorted({case["n"] for case in cases}), "families": list(FAMILIES),
            "graph_seeds": list(common.GRAPH_SEEDS), "kkt_seeds": list(common.KKT_SEEDS),
            "repetitions": repetitions, "warmups": 1, "aggregation": common.AGGREGATION,
            "kkt_below_all_competitors_by_paired_medians": leaders,
            "kkt_below_all_competitors_on_every_graph": graph_leaders}


def synthetic_rows(sizes=(256,), repetitions=4):
    rows = []
    for case, g, s, rep, algorithm in itertools.product(dimensions(sizes).values(), common.GRAPH_SEEDS,
                                                        common.KKT_SEEDS, range(repetitions), common.ALGORITHMS):
        a = common.ALGORITHMS.index(algorithm)
        rows.append({"case_id": case["case_id"], "family": case["family"], "n": case["n"], "m": case["m"],
            "graph_seed": g, "kkt_seed": s, "repetition": rep,
            "order": (a - rep - common.GRAPH_SEEDS.index(g) - common.KKT_SEEDS.index(s)) % 4,
            "warmups": 1, "algorithm": algorithm, "elapsed_ns": (a + 1) * (1000 + g + s + rep), "validation": "pass"})
    return rows


def synthetic_work(sizes):
    counters, proxy_fields, _ = read_registry()
    fields = (*WORK_PREFIX, *counters, *WORK_DERIVED_INTS, *WORK_RATIOS,
              "total_work_proxy", "validation")
    rows = []
    for case, g, s in itertools.product(dimensions(sizes).values(), common.GRAPH_SEEDS, common.KKT_SEEDS):
        n, m = case["n"], case["m"]
        row = {field: 0 for field in fields}
        row.update({key: case[key] for key in ("case_id", "family", "n", "m")})
        row.update(graph_seed=g, kkt_seed=s, input_fingerprint=n + g,
                   max_degree=3 if case["family"] == "balanced_binary_tree" else 8,
                   leaf_vertices=n // 2 if case["family"] == "balanced_binary_tree" else 0,
                   regime="one_boruvka_round", validation="pass_certified_oracle_exact_ids",
                   kkt_calls=1, kkt_vertices=n, kkt_edges=m, max_depth=1,
                   contraction_calls=1, contraction_vertices=n, contraction_edges=m,
                   contraction_edge_visits=m, initialized_slots=2 * n,
                   edge_materializations=m, kkt_edge_visits=m, hash_insert_items=n - 1,
                   all_kkt_vertices_over_n=1.0, all_kkt_edges_over_m=1.0)
        row["total_work_proxy"] = sum(row[field] for field in proxy_fields)
        rows.append(row)
    return fields, rows


def self_test():
    checks = []
    with tempfile.TemporaryDirectory(prefix="kkt-shape-analyzer-") as temporary:
        path = Path(temporary) / "input.csv"
        base = synthetic_rows()
        def write(rows):
            with path.open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=common.FIELDS, lineterminator="\n")
                writer.writeheader(); writer.writerows(rows)
        write(base)
        loaded, cases = load_measurements(path, (256,), 4)
        _, _, comparisons = common.aggregate(loaded, cases, 4)
        for row in comparisons:
            expected = (common.ALGORITHMS.index(row["algorithm"]) + 1) / (common.ALGORITHMS.index(row["reference"]) + 1)
            if not math.isclose(row["paired_runtime_ratio"], expected, rel_tol=1e-12):
                raise AssertionError("synthetic paired aggregation mismatch")
        checks.append({"case": "complete synthetic smoke and exact ratios", "status": "pass"})
        mutations = {
            "missing row": lambda rows: rows.pop(),
            "duplicate row": lambda rows: rows.append(dict(rows[0])),
            "invalid dimension": lambda rows: rows[0].update(m=1),
            "failed result": lambda rows: rows[0].update(validation="fail"),
            "zero duration": lambda rows: rows[0].update(elapsed_ns=0),
            "wrong order": lambda rows: rows[0].update(order=(rows[0]["order"] + 1) % 4),
            "wrong warmups": lambda rows: rows[0].update(warmups=0),
            "unexpected seed": lambda rows: rows[0].update(kkt_seed=999),
            "missing family": lambda rows: rows.__setitem__(slice(None), [r for r in rows if r["family"] != FAMILIES[0]]),
            "mismatched family": lambda rows: rows[0].update(family="star"),
        }
        for name, mutate in mutations.items():
            changed = copy.deepcopy(base); mutate(changed); write(changed)
            try:
                load_measurements(path, (256,), 4)
            except ValueError as error:
                checks.append({"case": name, "status": "rejected", "message": str(error)})
            else:
                raise AssertionError("accepted malformed synthetic input: " + name)
        write(synthetic_rows(MAIN_SIZES))
        loaded, cases = load_measurements(path, MAIN_SIZES, 4)
        checks.append({"case": "complete 24-case 3456-row matrix", "status": "pass", "rows": len(loaded), "cases": len(cases)})
        fields, base_work = synthetic_work(MAIN_SIZES)
        def write_work(records):
            with path.open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
                writer.writeheader(); writer.writerows(records)
        write_work(base_work)
        work = load_work(path, MAIN_SIZES)
        summaries, graphs = summarize_work(work, cases)
        if len(work) != 216 or len(summaries) != 24 or len(graphs) != 72:
            raise AssertionError("synthetic work matrix or grouping mismatch")
        checks.append({"case": "complete 216-row work matrix and graph aggregation", "status": "pass"})
        work_mutations = {
            "work missing row": lambda rows: rows.pop(),
            "work duplicate": lambda rows: rows.append(dict(rows[0])),
            "work dimensions": lambda rows: rows[0].update(m=1),
            "work fingerprint": lambda rows: rows[0].update(input_fingerprint=0),
            "work degree": lambda rows: rows[0].update(max_degree=rows[0]["n"]),
            "work leaf consistency": lambda rows: rows[0].update(leaf_vertices=1),
            "work counter identity": lambda rows: rows[0].update(heavy_edge_incidences=1),
            "work proxy": lambda rows: rows[0].update(total_work_proxy=1),
            "work NaN ratio": lambda rows: rows[0].update(heavy_fraction="nan"),
            "work wrong regime": lambda rows: rows[0].update(regime="two_boruvka_rounds"),
        }
        for name, mutate in work_mutations.items():
            changed = copy.deepcopy(base_work); mutate(changed); write_work(changed)
            try:
                load_work(path, MAIN_SIZES)
            except ValueError as error:
                checks.append({"case": name, "status": "rejected", "message": str(error)})
            else:
                raise AssertionError("accepted malformed synthetic input: " + name)
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", type=Path)
    parser.add_argument("--work-csv", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--sizes", type=int, nargs="+", default=list(MAIN_SIZES))
    parser.add_argument("--repetitions", type=int, default=4)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps({"checks": self_test()}, indent=2)); return
    sizes = validate_options(args.sizes, args.repetitions)
    if args.input_csv is None or (not args.validate_only and args.output_dir is None):
        parser.error("--input-csv is required, and plotting also requires --output-dir")
    rows, cases = load_measurements(args.input_csv, sizes, args.repetitions)
    work = load_work(args.work_csv, sizes) if args.work_csv else None
    if args.validate_only:
        print(json.dumps({"status": "pass", "cases": len(cases), "timing_observations": len(rows),
                          "work_observations": len(work) if work is not None else 0})); return
    summaries, graphs, comparisons = common.aggregate(rows, cases, args.repetitions)
    work_summaries, work_graphs = summarize_work(work, cases) if work is not None else ([], [])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, records in (("summary.csv", summaries), ("graph_summary.csv", graphs),
                           ("comparisons.csv", comparisons), ("work_summary.csv", work_summaries),
                           ("graph_work_summary.csv", work_graphs)):
        if records: common.write_csv(args.output_dir / name, records)
    analysis = write_report(args.output_dir, args.input_csv, rows, cases, args.repetitions, summaries, comparisons, work_summaries)
    analysis["input_sha256"] = hashlib.sha256(args.input_csv.read_bytes()).hexdigest()
    if args.work_csv:
        analysis.update(work_csv=str(args.work_csv), work_sha256=hashlib.sha256(args.work_csv.read_bytes()).hexdigest(),
                        work_observation_count=len(work), work_aggregation="Arithmetic sampling-seed means within each graph, then arithmetic graph-seed means.")
    (args.output_dir / "analysis.json").write_text(json.dumps(analysis, indent=2) + "\n")
    plot_ratios(cases, comparisons, args.output_dir)
    if work_summaries: plot_work(cases, work_summaries, args.output_dir)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, AssertionError) as error:
        print("shapes analysis: " + str(error), file=sys.stderr)
        sys.exit(1)
