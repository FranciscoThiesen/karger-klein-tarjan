#!/usr/bin/env python3
"""Strict analysis of two complete production-contraction ablation runs.

This compares whole continuation strategies, including their storage lifetimes;
it does not isolate only sampling or verifier instructions. Repeated compacting
Boruvka is deterministic. Its KKT-seed labels are matching keys, not new inputs.
"""

import argparse
import csv
import hashlib
import itertools
import json
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path


ALGORITHMS = ("kkt", "compacting_boruvka")
RUNS = ("primary", "confirmation")
GRAPH_SEEDS = (17, 42, 999)
KKT_SEEDS = (0, 1, 7)
REPETITIONS = 4
FAMILIES = ("unbalanced_bipartite_16", "ring_cliques_16", "grid3d_distance",
            "leaf_core_90", "regular_8", "random_4", "small_world")
NAMES = {
    "unbalanced_bipartite_16": "Bipartite: 16-vertex side",
    "ring_cliques_16": "Ring of 16-vertex cliques",
    "grid3d_distance": "3D grid: distance weights",
    "leaf_core_90": "Core with at least 90% leaves",
    "regular_8": "8-regular graph",
    "random_4": "Random m=4n control",
    "small_world": "Protected-cycle small world",
}
TIMING_FIELDS = ("case_id", "family", "n", "m", "graph_seed", "kkt_seed",
                 "repetition", "order", "warmups", "algorithm", "elapsed_ns", "validation")
TRACE_FIELDS = ("case_id", "family", "n", "m", "graph_seed", "algorithm", "round",
                "input_vertices", "input_edges", "selected_edges", "output_vertices",
                "output_edges", "total_rounds", "total_selected_edges", "input_fingerprint",
                "validation")


def dimensions():
    result = {}
    for family in FAMILIES:
        sizes = (4096, 65536) if family == "small_world" else (4096, 65536, 262144)
        for n in sizes:
            if family == "unbalanced_bipartite_16":
                m = 4 * (n - 16)
            elif family == "ring_cliques_16":
                m = 121 * (n // 16)
            elif family == "leaf_core_90":
                m = n + 3 * (n // 10)
            elif family == "grid3d_distance":
                exponent = n.bit_length() - 1
                sides = [1 << (exponent // 3 + (axis < exponent % 3)) for axis in range(3)]
                m = sum((side - 1) * (n // side) for side in sides)
            else:
                m = 4 * n
            case_id = f"{family}_n{n}"
            result[case_id] = {"case_id": case_id, "family": family, "n": n, "m": m}
    return result


def integer(value, context):
    if not isinstance(value, str) or re.fullmatch(r"[0-9]+", value) is None:
        raise ValueError(f"{context}: expected an unsigned decimal integer")
    return int(value)


def read_csv(path, fields):
    with path.open(newline="") as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != fields:
            raise ValueError(f"{path}: unexpected CSV schema")
        for line, raw in enumerate(reader, 2):
            if None in raw or any(value is None for value in raw.values()):
                raise ValueError(f"{path}:{line}: malformed CSV record")
            yield f"{path}:{line}", raw


def check_case(row, context):
    expected = dimensions().get(row["case_id"])
    if expected is None or any(row[field] != expected[field] for field in ("family", "n", "m")):
        raise ValueError(f"{context}: unexpected case, family, or dimensions")
    if row["graph_seed"] not in GRAPH_SEEDS:
        raise ValueError(f"{context}: unsupported graph seed")


def load_timing(path):
    result = {}
    numeric = ("n", "m", "graph_seed", "kkt_seed", "repetition", "order", "warmups", "elapsed_ns")
    for context, raw in read_csv(path, TIMING_FIELDS):
        row = dict(raw)
        for field in numeric:
            row[field] = integer(raw[field], f"{context} {field}")
        check_case(row, context)
        if row["validation"] != "pass" or not 0 < row["elapsed_ns"] <= 2**63 - 1:
            raise ValueError(f"{context}: failed validation or invalid duration")
        if row["algorithm"] not in ALGORITHMS or row["kkt_seed"] not in KKT_SEEDS:
            raise ValueError(f"{context}: unexpected algorithm or sampling seed")
        if row["repetition"] not in range(REPETITIONS) or row["warmups"] != 1:
            raise ValueError(f"{context}: requires four repetitions and one warmup")
        g, s = GRAPH_SEEDS.index(row["graph_seed"]), KKT_SEEDS.index(row["kkt_seed"])
        expected_order = (ALGORITHMS.index(row["algorithm"]) - row["repetition"] - g - s) % 2
        if row["order"] != expected_order:
            raise ValueError(f"{context}: wrong balanced execution order")
        key = (row["case_id"], row["graph_seed"], row["kkt_seed"], row["repetition"], row["algorithm"])
        if key in result:
            raise ValueError(f"{context}: duplicate timing {key}")
        result[key] = row
    expected = set(itertools.product(dimensions(), GRAPH_SEEDS, KKT_SEEDS, range(REPETITIONS), ALGORITHMS))
    if set(result) != expected:
        raise ValueError(f"{path}: incomplete timing matrix: expected 1440 rows, got {len(result)}")
    return result


def load_traces(path):
    grouped = defaultdict(dict)
    numeric = tuple(field for field in TRACE_FIELDS
                    if field not in ("case_id", "family", "algorithm", "validation"))
    for context, raw in read_csv(path, TRACE_FIELDS):
        row = dict(raw)
        for field in numeric:
            row[field] = integer(raw[field], f"{context} {field}")
        check_case(row, context)
        if row["algorithm"] != "compacting_boruvka" or row["validation"] != "pass":
            raise ValueError(f"{context}: trace algorithm or validation differs")
        if not 1 <= row["total_rounds"] <= row["n"].bit_length() or not 1 <= row["round"] <= row["total_rounds"]:
            raise ValueError(f"{context}: invalid round count")
        if row["input_fingerprint"] >= 2**64:
            raise ValueError(f"{context}: fingerprint is not a uint64")
        group = grouped[row["case_id"], row["graph_seed"]]
        if row["round"] in group:
            raise ValueError(f"{context}: duplicate contraction round")
        group[row["round"]] = row
    expected = set(itertools.product(dimensions(), GRAPH_SEEDS))
    if set(grouped) != expected:
        raise ValueError(f"{path}: contraction traces must cover exactly 60 graphs")
    result = {}
    for key, records in grouped.items():
        rounds = [records[index] for index in sorted(records)]
        first = rounds[0]
        if set(records) != set(range(1, first["total_rounds"] + 1)):
            raise ValueError(f"{key}: missing contraction round")
        previous = (first["n"], first["m"])
        selected = 0
        for row in rounds:
            if any(row[field] != first[field] for field in
                   ("total_rounds", "total_selected_edges", "input_fingerprint")):
                raise ValueError(f"{key}: inconsistent per-graph trace metadata")
            n, m = row["input_vertices"], row["input_edges"]
            nr, mr = row["output_vertices"], row["output_edges"]
            if (n, m) != previous or n < 2 or m < n - 1:
                raise ValueError(f"{key}: trace is not a connected chain from the original input")
            if nr > n // 2 or nr == 1 or (nr == 0) != (mr == 0):
                raise ValueError(f"{key}: invalid contracted vertex count")
            if mr >= m or mr > nr * (nr - 1) // 2 or (nr and mr < nr - 1):
                raise ValueError(f"{key}: contracted graph is not smaller, simple, and connected")
            if row["selected_edges"] != n - (nr or 1) or mr > m - row["selected_edges"]:
                raise ValueError(f"{key}: selected-edge accounting disagrees with contraction")
            selected += row["selected_edges"]
            previous = (nr, mr)
        if previous != (0, 0) or selected != first["n"] - 1 or selected != first["total_selected_edges"]:
            raise ValueError(f"{key}: unfinished trace or wrong total selected edge count")
        result[key] = rounds
    return result


def load_provenance(common_path, shapes_path, traces):
    # Reuse complete work-matrix validators without changing any module globals.
    # Each also validates the counter schema, correctness marks, and derived data.
    import analyze_common
    import analyze_shapes
    common = analyze_common.load_work(common_path, analyze_common.MAIN_SIZES)
    shapes = analyze_shapes.load_work(shapes_path, analyze_shapes.MAIN_SIZES)
    for key in set(common).intersection(shapes):
        if common[key]["input_fingerprint"] != shapes[key]["input_fingerprint"]:
            raise ValueError(f"shared control input differs between work campaigns: {key}")
    records = []
    for (case, g), rounds in traces.items():
        source = shapes if rounds[0]["family"] == "small_world" else common
        expected_root = rounds[min(1, len(rounds) - 1)]
        for s in KKT_SEEDS:
            row = source[case, g, s]
            if row["input_fingerprint"] != rounds[0]["input_fingerprint"]:
                raise ValueError(f"{case}/{g}: trace input differs from independently collected work")
            if (row["root_after_two_vertices"], row["root_after_two_edges"]) != (
                    expected_root["output_vertices"], expected_root["output_edges"]):
                raise ValueError(f"{case}/{g}/{s}: KKT root contractions disagree with ablation trace")
        records.append({**dimensions()[case], "graph_seed": g,
                        "input_fingerprint": rounds[0]["input_fingerprint"],
                        "source_work": "shapes" if source is shapes else "common",
                        "sampling_seeds_matched": len(KKT_SEEDS), "validation": "pass"})
    return records


def median_hierarchy(values):
    """Input keys (graph seed, sampling seed, repetition); equal graph weights."""
    graphs = {}
    for g in GRAPH_SEEDS:
        graphs[g] = statistics.median(
            statistics.median(values[g, s, r] for r in range(REPETITIONS)) for s in KKT_SEEDS)
    return statistics.median(graphs.values()), graphs


def summarize(runs):
    times, paired, graphs, observations, drift, confirmation = [], [], [], [], [], []
    cases = dimensions()
    for run, rows in runs.items():
        for case, metadata in cases.items():
            for algorithm in ALGORITHMS:
                values = {(g, s, r): rows[case, g, s, r, algorithm]["elapsed_ns"] / 1e6
                          for g, s, r in itertools.product(GRAPH_SEEDS, KKT_SEEDS, range(REPETITIONS))}
                median, per_graph = median_hierarchy(values)
                times.append({"run": run, **metadata, "algorithm": algorithm,
                              "median_ms": median, "graph_min_ms": min(per_graph.values()),
                              "graph_max_ms": max(per_graph.values()), "observations": len(values)})
            ratios = {}
            for g, s, r in itertools.product(GRAPH_SEEDS, KKT_SEEDS, range(REPETITIONS)):
                kkt = rows[case, g, s, r, "kkt"]["elapsed_ns"]
                compacting = rows[case, g, s, r, "compacting_boruvka"]["elapsed_ns"]
                ratios[g, s, r] = kkt / compacting
                observations.append({"run": run, **metadata, "graph_seed": g, "kkt_seed": s,
                                     "repetition": r, "kkt_ns": kkt, "compacting_boruvka_ns": compacting,
                                     "paired_runtime_ratio": kkt / compacting})
            median, per_graph = median_hierarchy(ratios)
            paired.append({"run": run, **metadata, "paired_runtime_ratio": median,
                           "graph_min_ratio": min(per_graph.values()), "graph_max_ratio": max(per_graph.values()),
                           "kkt_slower_observations": sum(value > 1 for value in ratios.values()),
                           "equal_observations": sum(value == 1 for value in ratios.values()),
                           "paired_observations": len(ratios)})
            for g, ratio in per_graph.items():
                graphs.append({"run": run, **metadata, "graph_seed": g, "paired_runtime_ratio": ratio})
    lookup = {(row["run"], row["case_id"]): row for row in paired}
    for case, metadata in cases.items():
        a, b = (lookup[run, case] for run in RUNS)
        confirmation.append({**metadata,
            "primary_paired_ratio": a["paired_runtime_ratio"], "confirmation_paired_ratio": b["paired_runtime_ratio"],
            "primary_graph_min": a["graph_min_ratio"], "primary_graph_max": a["graph_max_ratio"],
            "confirmation_graph_min": b["graph_min_ratio"], "confirmation_graph_max": b["graph_max_ratio"],
            "kkt_case_median_lead_both_runs": a["paired_runtime_ratio"] < 1 and b["paired_runtime_ratio"] < 1,
            "kkt_every_graph_lead_both_runs": a["graph_max_ratio"] < 1 and b["graph_max_ratio"] < 1})
        for algorithm in ALGORITHMS:
            ratios = {(g, s, r): runs["confirmation"][case, g, s, r, algorithm]["elapsed_ns"] /
                      runs["primary"][case, g, s, r, algorithm]["elapsed_ns"]
                      for g, s, r in itertools.product(GRAPH_SEEDS, KKT_SEEDS, range(REPETITIONS))}
            median, per_graph = median_hierarchy(ratios)
            drift.append({**metadata, "algorithm": algorithm, "confirmation_over_primary": median,
                          "graph_min_ratio": min(per_graph.values()), "graph_max_ratio": max(per_graph.values()),
                          "slower_observations": sum(value > 1 for value in ratios.values()),
                          "equal_observations": sum(value == 1 for value in ratios.values()), "paired_observations": len(ratios)})
    return {"timing_summary": times, "paired_summary": paired, "graph_paired_summary": graphs,
            "matched_pairs": observations, "run_drift": drift, "confirmation_summary": confirmation}


def summarize_traces(traces):
    graph_rows, summary, volumes = [], [], []
    for case, metadata in dimensions().items():
        case_rows = []
        for g in GRAPH_SEEDS:
            rounds = traces[case, g]
            row = {**metadata, "graph_seed": g, "rounds": len(rounds),
                   "input_edge_volume": sum(r["input_edges"] for r in rounds),
                   "input_vertex_volume": sum(r["input_vertices"] for r in rounds),
                   "after_two_edges": rounds[min(1, len(rounds) - 1)]["output_edges"]}
            row["input_edge_volume_over_m"] = row["input_edge_volume"] / metadata["m"]
            row["after_two_edges_over_m"] = row["after_two_edges"] / metadata["m"]
            graph_rows.append(row)
            case_rows.append(row)
        row = dict(metadata)
        for field in ("rounds", "input_edge_volume_over_m", "after_two_edges_over_m"):
            values = [r[field] for r in case_rows]
            row.update({field + "_mean": statistics.fmean(values), field + "_min": min(values), field + "_max": max(values)})
        summary.append(row)
        for step in range(max(r["rounds"] for r in case_rows) + 1):
            edges = [metadata["m"] if step == 0 else traces[case, g][step - 1]["output_edges"]
                     if step <= len(traces[case, g]) else 0 for g in GRAPH_SEEDS]
            volumes.append({**metadata, "completed_rounds": step, "remaining_edges_mean": statistics.fmean(edges),
                            "remaining_edges_min": min(edges), "remaining_edges_max": max(edges),
                            "remaining_fraction_mean": statistics.fmean(edges) / metadata["m"],
                            "remaining_fraction_min": min(edges) / metadata["m"],
                            "remaining_fraction_max": max(edges) / metadata["m"]})
    return {"graph_contraction_summary": graph_rows, "contraction_summary": summary, "round_edge_volumes": volumes}


def write_csv(path, rows):
    with path.open("w", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot(tables, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter, MaxNLocator

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "svg.fonttype": "none", "pdf.fonttype": 42})

    def save(figure, name):
        for extension in ("png", "svg", "pdf"):
            path = output / f"{name}.{extension}"
            figure.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
            if extension == "svg":
                path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
        plt.close(figure)

    cases = list(dimensions().values())
    lookup = {(row["run"], row["case_id"]): row for row in tables["paired_summary"]}
    figure, axis = plt.subplots(figsize=(12.0, 10.8))
    for run, offset, color, marker in (("primary", -0.13, "#7437A5", "o"), ("confirmation", 0.13, "#087F75", "s")):
        rows = [lookup[run, case["case_id"]] for case in cases]
        values = [row["paired_runtime_ratio"] for row in rows]
        axis.errorbar(values, [i + offset for i in range(len(cases))],
                      xerr=[[v - r["graph_min_ratio"] for v, r in zip(values, rows)],
                            [r["graph_max_ratio"] - v for v, r in zip(values, rows)]],
                      fmt=marker, color=color, capsize=3, markersize=5, label=run.title())
    axis.axvline(1, color="#263442", linestyle="--", linewidth=1)
    axis.set_xscale("log", base=2)
    # Ratios often occupy less than one doubling; powers-of-two ticks alone
    # would leave only 1x labeled and make the effect sizes hard to read.
    low, high = axis.get_xlim()
    ticks = MaxNLocator(nbins=8).tick_values(low, high)
    axis.set_xticks(sorted({1.0, *(value for value in ticks if low <= value <= high)}))
    axis.set_xlim(low, high)
    axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}×"))
    axis.set_yticks(range(len(cases)), [f"{NAMES[c['family']]} · n={c['n']:,}" for c in cases], fontsize=9)
    axis.invert_yaxis()
    axis.set_xlabel("KKT / repeated compacting Borůvka runtime (below 1× favors KKT)")
    axis.set_title("Does sampling beat continued production contraction?", loc="left", fontsize=17, fontweight="bold", pad=15)
    axis.legend(frameon=False, loc="best")
    axis.grid(axis="x", alpha=0.2)
    axis.spines[["top", "right"]].set_visible(False)
    figure.text(0.02, 0.012, "All 20 cases. Paired medians: repetitions → sampling-seed labels → graph seeds. Bars span three graph medians, not confidence intervals.\nWhole-strategy comparison, including storage lifetimes and RNG; not an isolated verifier instruction cost.", fontsize=9)
    figure.tight_layout(rect=(0, 0.07, 1, 1))
    save(figure, "ablation_runtime_ratios")

    figure, axes = plt.subplots(4, 2, figsize=(13.5, 13), sharey=True)
    colors = {4096: "#2774AE", 65536: "#087F75", 262144: "#D07916"}
    for family, axis in zip(FAMILIES, axes.flat):
        for n in (4096, 65536, 262144):
            rows = [row for row in tables["round_edge_volumes"] if row["family"] == family and row["n"] == n]
            if not rows:
                continue
            x = [row["completed_rounds"] for row in rows]
            axis.plot(x, [row["remaining_fraction_mean"] for row in rows], marker="o", markersize=3,
                      color=colors[n], label=f"n={n:,}")
            axis.fill_between(x, [row["remaining_fraction_min"] for row in rows],
                              [row["remaining_fraction_max"] for row in rows], color=colors[n], alpha=0.15)
        axis.set_title(NAMES[family], loc="left", fontweight="bold")
        axis.set_xlabel("Completed production contraction rounds")
        axis.set_ylabel("Remaining edges / original edges")
        axis.set_ylim(-0.025, 1.025)
        axis.xaxis.set_major_locator(MaxNLocator(integer=True))
        axis.grid(alpha=0.2)
        axis.spines[["top", "right"]].set_visible(False)
        axis.legend(frameon=False, fontsize=9)
    axes.flat[-1].axis("off")
    axes.flat[-1].text(0, 0.8, "Untimed traces: one per graph.\nMeans and ranges over 3 graph seeds.\nTerminated traces remain at zero.\nNo sampling-seed replication.\n\nThis is repeated compacting Borůvka,\nnot KKT's recursive subproblem volume.", va="top", fontsize=11)
    figure.suptitle("How quickly does plain compacting contraction discard edges?", x=0.05, ha="left", fontsize=17, fontweight="bold")
    figure.tight_layout(rect=(0, 0.01, 1, 0.965), h_pad=2)
    save(figure, "contraction_round_edges")


def write_report(tables, output):
    rows = tables["confirmation_summary"]
    both = sum(row["kkt_case_median_lead_both_runs"] for row in rows)
    every = sum(row["kkt_every_graph_lead_both_runs"] for row in rows)
    lines = ["# KKT versus continued production contraction", "",
             "Both full runs passed strict validation: 1,440 timings each, 20 cases, three graph seeds, three sampling-seed labels, four repeats, one checked warmup per algorithm. The separate trace covers all 60 graphs. Its original input fingerprints and graph sizes after two contractions (or earlier termination) match the independently collected common/shape work evidence. Intermediate edge contents are not compared.", "",
             f"KKT's case-level paired median is below repeated compacting Borůvka in **{both}/20 cases in both runs**. In **{every}/20 cases**, all three graph-level paired medians are below one in both runs. Every case and loss is retained below.", "",
             "This is a whole-strategy ablation using the exact production boruvka_step: continue deterministic compaction versus KKT's sampling, verifier, recursion, RNG, and storage lifetimes. It does not isolate only verifier instructions, compare against a best possible Borůvka, or establish an asymptotic crossover. Compaction releases prior input storage each round; KKT has recursive lifetimes.", "",
             "Both timings include tuple conversion, temporary input destruction, and the same reserved public ID-set construction. Validation and returned-result destruction are outside. The independently certified reference is outside timing. Fingerprints link the untimed trace to the other work campaigns; the timing CSV itself contains no per-call fingerprint, so binary/fixture provenance must accompany the data.", "",
             "Paired ratios divide matched KKT/compaction elapsed times, take the median over repetitions, then sampling-seed labels, then graph seeds. Ranges span the three graph medians, not confidence intervals. Only three graph seeds represent graph draws; deterministic compaction's seed labels are repeated trials. Confirmation is a second execution, not a new graph sample. run_drift.csv retains each algorithm's matched confirmation/primary movement.", "",
             "| Case | Primary ratio [graph range] | Confirmation ratio [graph range] |", "|---|---:|---:|"]
    for row in rows:
        lines.append(f"| {row['case_id']} | {row['primary_paired_ratio']:.4f} [{row['primary_graph_min']:.4f}, {row['primary_graph_max']:.4f}] | {row['confirmation_paired_ratio']:.4f} [{row['confirmation_graph_min']:.4f}, {row['confirmation_graph_max']:.4f}] |")
    lines += ["", "![All paired runtime ratios](ablation_runtime_ratios.png)", "",
              "## Untimed contraction volumes", "",
              "Volumes are arithmetic means over three graphs. A round's input is counted once; these are edge visits to whole contraction calls, not the number of individual loop passes or KKT recursive edge volume. The round plot shows remaining edges and pads completed traces with zero, preserving every size.", "",
              "| Case | Rounds mean [range] | Sum of round input edges / m, mean | After two rounds / m, mean |", "|---|---:|---:|---:|"]
    for row in tables["contraction_summary"]:
        lines.append(f"| {row['case_id']} | {row['rounds_mean']:.2f} [{row['rounds_min']}, {row['rounds_max']}] | {row['input_edge_volume_over_m_mean']:.4f} | {row['after_two_edges_over_m_mean']:.4f} |")
    lines += ["", "![Every contraction trace family](contraction_round_edges.png)", "",
              "Raw matched pairs, graph-level ratios, slower/equal observation counts, both runtime summaries, confirmation summary, run drift, contraction summaries, round volumes, and provenance matches are retained as CSVs. analysis_inputs.json records input hashes. No cases are selected after observing which algorithm wins."]
    (output / "report.md").write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("timing-csv", "confirmation-csv", "trace-csv", "common-work-csv", "shapes-work-csv", "output-dir"):
        parser.add_argument("--" + flag, required=True, type=Path)
    args = parser.parse_args()
    if args.timing_csv.resolve() == args.confirmation_csv.resolve():
        raise ValueError("primary and confirmation must be distinct files from separate executions")
    runs = {"primary": load_timing(args.timing_csv), "confirmation": load_timing(args.confirmation_csv)}
    traces = load_traces(args.trace_csv)
    provenance = load_provenance(args.common_work_csv, args.shapes_work_csv, traces)
    tables = {**summarize(runs), **summarize_traces(traces), "provenance_matches": provenance}
    # Validate every input before creating the output directory or any artifact.
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    for name, rows in tables.items():
        write_csv(output / f"{name}.csv", rows)
    files = {name: path for name, path in vars(args).items() if name != "output_dir"}
    metadata = {"inputs": {name: {"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                            for name, path in files.items()},
                "cases": 20, "timing_rows_per_run": 1440, "trace_graphs": len(traces),
                "trace_rows": sum(len(rows) for rows in traces.values()),
                "build_machine_provenance": "Use the accompanying experiment metadata; it is not inferable from this CSV."}
    (output / "analysis_inputs.json").write_text(json.dumps(metadata, indent=2) + "\n")
    plot(tables, output)
    write_report(tables, output)
    print(f"Validated both 1440-row timing matrices and all 60 graph traces; wrote {output}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        raise SystemExit(f"ablation analysis: {error}") from error
