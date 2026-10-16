#!/usr/bin/env python3
"""Strict, manifest-driven analysis of KKT versus continued production compaction.

Timing ratios use matched calls, then medians of repetitions, sampling seeds,
and graph seeds. Logical-work means remain separate from elapsed times. This
whole-strategy comparison includes recursion, RNG and storage lifetimes.
"""
import argparse
import collections
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import statistics
import sys

ALGORITHMS = ("kkt", "compacting_boruvka")
FAMILIES = ("hierarchical_path", "hierarchical_tree", "low_path", "random_path",
            "random_tree", "distance_path", "distance_tree", "legacy_random",
            "line_metric", "line_random", "grid2d_metric", "grid2d_random", "gnm_random", "line_wide_metric")
MANIFEST_FIELDS = ("family", "n", "density", "intrusion_per_mille")
PREFIX = ("case_id", "family", "n", "m", "density", "intrusion_per_mille",
          "graph_seed", "input_fingerprint", "topology_fingerprint")
TIMING_FIELDS = (*PREFIX, "kkt_seed", "repetition", "order", "warmups",
                 "algorithm", "elapsed_ns", "validation")
TRACE_FIELDS = (*PREFIX, "round", "input_vertices", "input_edges", "selected_edges",
                "output_vertices", "output_edges", "total_rounds", "total_selected_edges", "validation")
UINT64_MAX = 2**64 - 1


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, context, maximum=UINT64_MAX):
    require(isinstance(value, str) and re.fullmatch(r"[0-9]+", value) is not None,
            f"{context}: expected an unsigned decimal integer")
    result = int(value)
    require(result <= maximum, f"{context}: integer exceeds {maximum}")
    return result


def seed_bank(value):
    result = tuple(integer(part, "seed", 2**32 - 1) for part in value.split(","))
    require(result and len(result) == len(set(result)), "seed bank must be nonempty and distinct")
    return result


def read_csv(path, fields):
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        require(tuple(reader.fieldnames or ()) == tuple(fields), f"{path}: unexpected CSV header")
        for line, row in enumerate(reader, 2):
            require(None not in row and all(value is not None for value in row.values()),
                    f"{path}:{line}: malformed CSV row")
            yield f"{path}:{line}", row


def case_id(spec):
    return f'{spec["family"]}_n{spec["n"]}_d{spec["density"]}_p{spec["intrusion_per_mille"]}'


def load_manifest(path):
    cases = {}
    for context, raw in read_csv(path, MANIFEST_FIELDS):
        spec = dict(raw)
        for field in MANIFEST_FIELDS[1:]:
            spec[field] = integer(raw[field], context + " " + field, 2**32 - 1)
        n, d, p, family = spec["n"], spec["density"], spec["intrusion_per_mille"], spec["family"]
        require(family in FAMILIES, f"{context}: unsupported family")
        maximum_n = 2**23 if family in ("line_metric", "line_random", "grid2d_metric", "grid2d_random", "gnm_random", "line_wide_metric") else 2**22
        require(32 <= n <= maximum_n and n & (n - 1) == 0 and 1 <= d <= 512 and p <= 1000,
                f"{context}: invalid dimensions or intrusion parameter")
        m = n * d
        require(m <= n * (n - 1) // 2 and m < 0x3f3f3f3f,
                f"{context}: exceeds simple-graph or weight capacity")
        require(n * p // 1000 <= m - n + 1, f"{context}: too many intrusions")
        if family in ("random_path", "random_tree", "distance_path", "distance_tree"):
            require(p == 0, f"{context}: random/distance weight modes require p=0")
        if family == "legacy_random":
            require(p == 0 and d in (4, 32, 128), f"{context}: invalid legacy control")
        if family in ("line_metric", "line_random", "grid2d_metric", "grid2d_random", "line_wide_metric"):
            require(p == 0, f"{context}: crossover geometric models require p=0")
        if family in ("grid2d_metric", "grid2d_random"):
            require(d >= 2, f"{context}: grid backbone requires density at least two")
        if family == "gnm_random":
            require(p == 0 and d >= 16, f"{context}: connected G(n,m) requires d>=16,p=0")
        spec.update(m=m, case_id=case_id(spec))
        require(spec["case_id"] not in cases, f"{context}: duplicate manifest case")
        cases[spec["case_id"]] = spec
    require(cases, "empty manifest")
    return cases


def registry():
    path = Path(__file__).with_name("work_metrics.hpp")
    entries = re.findall(r'\{"(\w+)",\s*&kkt_work::WorkStats::(\w+),\s*(true|false)\}', path.read_text())
    require(entries and all(name == member for name, member, _ in entries), "invalid work registry")
    names = tuple(name for name, _, _ in entries)
    require(len(set(names)) == len(names), "duplicate work counter")
    return names, tuple(name for name, _, enabled in entries if enabled == "true")


def parse_prefix(raw, cases, graph_seeds, context):
    row = dict(raw)
    for field in PREFIX[2:]:
        row[field] = integer(raw[field], context + " " + field)
    expected = cases.get(row["case_id"])
    require(expected is not None and all(row[field] == expected[field] for field in
            ("family", "n", "m", "density", "intrusion_per_mille")), f"{context}: case differs from manifest")
    require(row["graph_seed"] in graph_seeds, f"{context}: unexpected graph seed")
    require(row["validation"] == "pass", f"{context}: failed exact-MST validation")
    return row


def check_fingerprints(records):
    weighted, topology = {}, {}
    for row in records:
        key = row["case_id"], row["graph_seed"]
        value = row["input_fingerprint"], row["topology_fingerprint"]
        require(key not in weighted or weighted[key] == value, f"{key}: inconsistent fingerprints")
        weighted[key] = value
        # Different weight modes/noise levels share a topology. Legacy fixtures
        # use a different generator and must not be folded into these controls.
        if row["family"] not in ("legacy_random", "gnm_random"):
            if row["family"] in ("line_metric", "line_random", "line_wide_metric"):
                kind = "crossover_line"
            elif row["family"] in ("grid2d_metric", "grid2d_random"):
                kind = "crossover_grid2d"
            else:
                kind = "tree" if row["family"] in ("hierarchical_tree", "random_tree", "distance_tree") else "path"
            pair = kind, row["n"], row["density"], row["graph_seed"]
            require(pair not in topology or topology[pair] == row["topology_fingerprint"],
                    f"{pair}: paired weight controls have different topology/order fingerprints")
            topology[pair] = row["topology_fingerprint"]
    return weighted


def load_timing(path, cases, graph_seeds, sampling_seeds, repetitions, warmups):
    require(2 <= repetitions <= 100 and repetitions % 2 == 0, "repetitions must be even, in [2,100]")
    require(1 <= warmups <= 100, "warmups must be in [1,100]")
    rows = {}
    for context, raw in read_csv(path, TIMING_FIELDS):
        row = parse_prefix(raw, cases, graph_seeds, context)
        for field in ("kkt_seed", "repetition", "order", "warmups", "elapsed_ns"):
            row[field] = integer(raw[field], context + " " + field)
        require(row["algorithm"] in ALGORITHMS and row["kkt_seed"] in sampling_seeds,
                f"{context}: unexpected algorithm or sampling seed")
        require(row["repetition"] in range(repetitions) and row["warmups"] == warmups,
                f"{context}: repetition or warmup protocol differs")
        require(0 < row["elapsed_ns"] <= 2**63 - 1, f"{context}: invalid duration")
        g, s = graph_seeds.index(row["graph_seed"]), sampling_seeds.index(row["kkt_seed"])
        order = (ALGORITHMS.index(row["algorithm"]) - row["repetition"] - g - s) % 2
        require(row["order"] == order, f"{context}: unbalanced or incorrect execution order")
        key = row["case_id"], row["graph_seed"], row["kkt_seed"], row["repetition"], row["algorithm"]
        require(key not in rows, f"{context}: duplicate timing row")
        rows[key] = row
    expected = set(itertools.product(cases, graph_seeds, sampling_seeds, range(repetitions), ALGORITHMS))
    require(set(rows) == expected, f"incomplete timing matrix: {len(rows)}/{len(expected)} rows")
    check_fingerprints(rows.values())
    return rows


def load_work(path, cases, graph_seeds, sampling_seeds):
    counters, proxy = registry()
    fields = (*PREFIX, "kkt_seed", "algorithm", *counters, "total_work_proxy", "validation")
    rows = {}
    for context, raw in read_csv(path, fields):
        row = parse_prefix(raw, cases, graph_seeds, context)
        require(row["algorithm"] in ALGORITHMS, f"{context}: unexpected algorithm")
        if row["algorithm"] == "kkt":
            row["kkt_seed"] = integer(raw["kkt_seed"], context + " sampling seed", 2**32 - 1)
            require(row["kkt_seed"] in sampling_seeds, f"{context}: unexpected sampling seed")
        else:
            require(raw["kkt_seed"] == "na", f"{context}: deterministic compactor seed must be na")
        for field in (*counters, "total_work_proxy"):
            row[field] = integer(raw[field], context + " " + field)
        require(row["total_work_proxy"] == sum(row[field] for field in proxy), f"{context}: proxy mismatch")
        require(row["current_depth"] == 0 and row["contraction_calls"] > 0 and
                row["contraction_edges"] >= row["m"] and row["contraction_vertices"] >= row["n"],
                f"{context}: missing or unbalanced instrumentation")
        require(row["contraction_edges"] <= row["contraction_edge_visits"] <= 4 * row["contraction_edges"] and
                row["edge_materializations"] >= row["m"] and row["hash_insert_items"] == row["n"] - 1,
                f"{context}: contraction/copy/output counter bounds violated")
        require(row["contraction_output_edges"] <= row["contraction_edges"] and
                row["contraction_output_vertices"] <= row["contraction_vertices"] // 2,
                f"{context}: contraction aggregate outputs exceed inputs")
        if row["algorithm"] == "kkt":
            require(row["kkt_calls"] == 1 + 2 * row["sampling_calls"] and row["max_depth"] > 0 and
                    row["max_depth"] <= row["kkt_calls"] and
                    row["kkt_edges"] >= row["m"] and row["kkt_vertices"] >= row["n"],
                    f"{context}: invalid KKT recursion counters")
            require(row["sampling_calls"] == row["verifier_calls"] and
                    row["sampling_edge_visits"] == row["verifier_edges"] and
                    row["sampled_edges"] <= row["sampling_edge_visits"] and
                    row["filtered_edges"] <= row["verifier_edges"] and
                    row["verifier_forest_edges"] <= row["sampled_edges"] and
                    row["kkt_edge_visits"] == row["m"] + 2 * row["verifier_edges"] + row["verifier_forest_edges"] and
                    row["path_query_visits"] == 4 * row["verifier_queries"],
                    f"{context}: inconsistent sampling/verifier counters")
            require(row["root_after_two_vertices"] <= row["n"] // 4 and
                    row["root_after_two_edges"] <= row["m"] and
                    (row["root_after_two_vertices"] == 0) == (row["root_after_two_edges"] == 0),
                    f"{context}: impossible root contraction sizes")
            if row["sampling_calls"]:
                require(row["root_after_two_vertices"] >= 2, f"{context}: sampled an empty residual")
            else:
                require(row["contraction_calls"] in (1, 2) and row["root_after_two_edges"] == 0,
                        f"{context}: invalid contraction-only KKT work")
        else:
            zero_fields = [f for f in counters if f.startswith(("sampling_", "sampled_", "filtered_",
                "verifier_", "fbt_", "path_", "lca_", "isolation_", "root_after_"))]
            zero_fields += ["kkt_calls", "kkt_vertices", "kkt_edges", "max_depth", "median_entries", "hash_lookup_calls"]
            require(all(row[f] == 0 for f in zero_fields) and row["kkt_edge_visits"] == row["m"],
                    f"{context}: compactor has unexpected KKT/sampling/verifier work")
        key = row["case_id"], row["graph_seed"], row["kkt_seed"], row["algorithm"]
        require(key not in rows, f"{context}: duplicate work row")
        rows[key] = row
    expected = {(c,g,s,"kkt") for c,g,s in itertools.product(cases,graph_seeds,sampling_seeds)}
    expected |= {(c,g,"na","compacting_boruvka") for c,g in itertools.product(cases,graph_seeds)}
    require(set(rows) == expected, f"incomplete work matrix: {len(rows)}/{len(expected)} rows")
    check_fingerprints(rows.values())
    return rows


def load_traces(path, cases, graph_seeds):
    groups = collections.defaultdict(dict)
    for context, raw in read_csv(path, TRACE_FIELDS):
        row = parse_prefix(raw, cases, graph_seeds, context)
        for field in TRACE_FIELDS[len(PREFIX):-1]:
            row[field] = integer(raw[field], context + " " + field)
        require(1 <= row["round"] <= row["total_rounds"] <= row["n"].bit_length() - 1,
                f"{context}: invalid contraction round")
        key = row["case_id"], row["graph_seed"]
        require(row["round"] not in groups[key], f"{context}: duplicate contraction round")
        groups[key][row["round"]] = row
    require(set(groups) == set(itertools.product(cases,graph_seeds)), "incomplete trace graph matrix")
    result = {}
    for key, records in groups.items():
        rounds = [records[r] for r in sorted(records)]
        first = rounds[0]
        require(set(records) == set(range(1, first["total_rounds"] + 1)), f"{key}: missing trace round")
        previous = first["n"], first["m"]
        selected = 0
        for row in rounds:
            require(row["total_rounds"] == len(rounds) and row["total_selected_edges"] == first["n"] - 1,
                    f"{key}: inconsistent total round/selected count")
            n,m,nr,mr = (row[f] for f in ("input_vertices","input_edges","output_vertices","output_edges"))
            require((n,m) == previous and n >= 2 and n - 1 <= m <= n * (n - 1) // 2,
                    f"{key}: broken trace chain or invalid connected input")
            require(nr <= n // 2 and nr != 1 and (nr == 0) == (mr == 0) and mr < m and
                    mr <= nr * (nr - 1) // 2 and (nr == 0 or mr >= nr - 1),
                    f"{key}: invalid contraction progress or output dimensions")
            require(row["selected_edges"] == n - (nr or 1) and mr <= m - row["selected_edges"],
                    f"{key}: selected-edge accounting mismatch")
            if row["family"] in ("hierarchical_path", "hierarchical_tree", "distance_path", "distance_tree") and row["intrusion_per_mille"] == 0:
                target = first["n"] >> row["round"]
                require(nr == (0 if target == 1 else target), f"{key}: exact hierarchy did not halve")
            selected += row["selected_edges"]
            previous = nr,mr
        require(previous == (0,0) and selected == first["n"] - 1, f"{key}: incomplete contraction")
        result[key] = rounds
    check_fingerprints(row for rounds in result.values() for row in rounds)
    return result


def crosscheck(timing, work, traces, sampling_seeds):
    records = list(timing.values()) + list(work.values())
    records.extend(row for rounds in traces.values() for row in rounds)
    check_fingerprints(records)
    if not work or not traces:
        return
    for (case,g), rounds in traces.items():
        comp = work[case,g,"na","compacting_boruvka"]
        expected = {"contraction_calls":len(rounds),
                    "contraction_edges":sum(r["input_edges"] for r in rounds),
                    "contraction_vertices":sum(r["input_vertices"] for r in rounds),
                    "contraction_output_edges":sum(r["output_edges"] for r in rounds),
                    "contraction_output_vertices":sum(r["output_vertices"] for r in rounds)}
        require(all(comp[k] == v for k,v in expected.items()), f"{case}/{g}: work/trace contraction volume mismatch")
        root = rounds[min(1,len(rounds)-1)]
        for s in sampling_seeds:
            kkt = work[case,g,s,"kkt"]
            require((kkt["root_after_two_vertices"],kkt["root_after_two_edges"]) ==
                    (root["output_vertices"],root["output_edges"]), f"{case}/{g}/{s}: KKT root/trace mismatch")


def hierarchy(values, graph_seeds, sampling_seeds):
    graph_values = {g:statistics.median(statistics.median(values[g,s]) for s in sampling_seeds)
                    for g in graph_seeds}
    return statistics.median(graph_values.values()), graph_values


def aggregate_timing(rows, cases, graph_seeds, sampling_seeds, repetitions):
    summaries, graphs, pairs, orders = [], [], [], []
    for case,spec in cases.items():
        ratios = collections.defaultdict(list)
        elapsed = {a:collections.defaultdict(list) for a in ALGORITHMS}
        order_ratios = {position:collections.defaultdict(list) for position in (0,1)}
        case_pairs = []
        for g,s,r in itertools.product(graph_seeds,sampling_seeds,range(repetitions)):
            a,b = (rows[case,g,s,r,algorithm] for algorithm in ALGORITHMS)
            ratio = a["elapsed_ns"] / b["elapsed_ns"]
            ratios[g,s].append(ratio)
            for algorithm,row in zip(ALGORITHMS,(a,b)):
                elapsed[algorithm][g,s].append(row["elapsed_ns"])
            order_ratios[a["order"]][g,s].append(ratio)
            case_pairs.append({**spec,"graph_seed":g,"kkt_seed":s,"repetition":r,
                "input_fingerprint":a["input_fingerprint"],"topology_fingerprint":a["topology_fingerprint"],
                "kkt_order":a["order"],"kkt_elapsed_ns":a["elapsed_ns"],
                "compacting_boruvka_elapsed_ns":b["elapsed_ns"],"paired_runtime_ratio":ratio})
        center, by_graph = hierarchy(ratios,graph_seeds,sampling_seeds)
        times = {a:hierarchy(elapsed[a],graph_seeds,sampling_seeds) for a in ALGORITHMS}
        summaries.append({**spec,"paired_runtime_ratio":center,"graph_min_ratio":min(by_graph.values()),
            "graph_max_ratio":max(by_graph.values()),"kkt_median_ns":times["kkt"][0],
            "compacting_boruvka_median_ns":times["compacting_boruvka"][0],
            "kkt_slower_observations":sum(p["paired_runtime_ratio"] > 1 for p in case_pairs),
            "equal_observations":sum(p["paired_runtime_ratio"] == 1 for p in case_pairs),
            "paired_observations":len(case_pairs),"all_graph_medians_below_one":max(by_graph.values()) < 1})
        for g in graph_seeds:
            selected = [p for p in case_pairs if p["graph_seed"] == g]
            graphs.append({**spec,"graph_seed":g,"input_fingerprint":selected[0]["input_fingerprint"],
                "topology_fingerprint":selected[0]["topology_fingerprint"],"paired_runtime_ratio":by_graph[g],
                "kkt_median_ns":times["kkt"][1][g],"compacting_boruvka_median_ns":times["compacting_boruvka"][1][g],
                "kkt_slower_observations":sum(p["paired_runtime_ratio"] > 1 for p in selected),
                "equal_observations":sum(p["paired_runtime_ratio"] == 1 for p in selected),"paired_observations":len(selected)})
        for position in (0,1):
            ratio, graph_ratios = hierarchy(order_ratios[position],graph_seeds,sampling_seeds)
            selected = [p for p in case_pairs if p["kkt_order"] == position]
            orders.append({**spec,"kkt_order":position,"paired_runtime_ratio":ratio,
                "graph_min_ratio":min(graph_ratios.values()),"graph_max_ratio":max(graph_ratios.values()),
                "kkt_slower_observations":sum(p["paired_runtime_ratio"] > 1 for p in selected),
                "equal_observations":sum(p["paired_runtime_ratio"] == 1 for p in selected),"paired_observations":len(selected)})
        pairs.extend(case_pairs)
    return summaries,graphs,pairs,orders


def aggregate_work(work, traces, cases, graph_seeds, sampling_seeds):
    summaries, graphs, trace_summaries, rounds_output = [], [], [], []
    metrics = ("contraction_calls","contraction_edges","contraction_edge_visits","contraction_vertices",
               "verifier_edges","sampling_calls","filtered_edges","initialized_slots","edge_materializations",
               "total_work_proxy")
    if work:
        for case,spec in cases.items():
            for algorithm in ALGORITHMS:
                per_graph = []
                for g in graph_seeds:
                    seeds = sampling_seeds if algorithm == "kkt" else ("na",)
                    rows = [work[case,g,s,algorithm] for s in seeds]
                    record = {**spec,"algorithm":algorithm,"graph_seed":g,
                        **{"mean_"+f:statistics.fmean(r[f] for r in rows) for f in metrics}}
                    record["contraction_edges_over_m"] = record["mean_contraction_edges"] / spec["m"]
                    record["mean_heavy_fraction"] = statistics.fmean(
                        (r["verifier_edges"]-r["filtered_edges"])/r["verifier_edges"] if r["verifier_edges"] else 0 for r in rows)
                    if traces:
                        shared = sum(r["input_edges"] for r in traces[case,g][:2])
                        record["mean_contraction_edges_after_shared_prefix"] = record["mean_contraction_edges"] - shared
                    graphs.append(record);per_graph.append(record)
                fields = [f for f in per_graph[0] if f.startswith("mean_") or f == "contraction_edges_over_m"]
                summaries.append({**spec,"algorithm":algorithm,
                                  **{f:statistics.fmean(r[f] for r in per_graph) for f in fields}})
    for (case,g), rounds in traces.items():
        spec = cases[case]
        trace_summaries.append({**spec,"graph_seed":g,"rounds":len(rounds),
            "contraction_edges":sum(r["input_edges"] for r in rounds),
            "contraction_edges_over_m":sum(r["input_edges"] for r in rounds)/spec["m"],
            "root_after_two_vertices":rounds[min(1,len(rounds)-1)]["output_vertices"],
            "root_after_two_edges":rounds[min(1,len(rounds)-1)]["output_edges"]})
        rounds_output.extend({**r,"input_edges_over_m":r["input_edges"]/r["m"],
                              "output_edges_over_m":r["output_edges"]/r["m"]} for r in rounds)
    return summaries,graphs,trace_summaries,rounds_output


def write_csv(path, rows):
    if not rows:
        # An analysis directory may be refreshed without optional work/trace
        # inputs. Remove only this analyzer's named derived file in that case.
        if path.exists():
            path.unlink()
        return
    with path.open("w",newline="") as stream:
        writer = csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)


def plots(summary, work_summary, traces_summary, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter, MaxNLocator, NullFormatter
    plt.rcParams.update({"font.size":10,"svg.fonttype":"none","pdf.fonttype":42})
    groups = sorted({(r["family"],r["intrusion_per_mille"]) for r in summary})
    cols = min(3,len(groups));rows = math.ceil(len(groups)/cols)
    colors = plt.get_cmap("tab10")
    def canvas():
        fig,axes = plt.subplots(rows,cols,figsize=(4.7*cols,3.65*rows+0.6),squeeze=False)
        for axis in axes.flat[len(groups):]:axis.set_visible(False)
        return fig,axes
    def finish(fig, stem, caption):
        fig.text(.02,.012,caption,fontsize=9,va="bottom")
        fig.tight_layout(rect=(0,.09 if rows==1 else .065,1,.98))
        for extension in ("png","svg","pdf"):
            fig.savefig(output/(stem+"."+extension),dpi=180,bbox_inches="tight")
        plt.close(fig)
    fig,axes=canvas()
    lower=min(1,min(r["graph_min_ratio"] for r in summary))*.9
    upper=max(1,max(r["graph_max_ratio"] for r in summary))*1.1
    for axis,(family,p) in zip(axes.flat,groups):
        selected=[r for r in summary if r["family"]==family and r["intrusion_per_mille"]==p]
        for i,d in enumerate(sorted({r["density"] for r in selected})):
            points=sorted((r for r in selected if r["density"]==d),key=lambda r:r["n"])
            x=[r["n"] for r in points];center=[r["paired_runtime_ratio"] for r in points]
            axis.plot(x,center,"-o",label=f"m/n={d}",color=colors(i%10),ms=4)
            axis.fill_between(x,[r["graph_min_ratio"] for r in points],[r["graph_max_ratio"] for r in points],color=colors(i%10),alpha=.12)
            axis.vlines(x,[r["graph_min_ratio"] for r in points],[r["graph_max_ratio"] for r in points],color=colors(i%10),alpha=.5)
        axis.axhline(1,color="#555",ls="--",lw=1)
        axis.set_xscale("log",base=2);axis.set_yscale("log");axis.set_ylim(lower,upper)
        ticks=[v for v in MaxNLocator(nbins=5).tick_values(lower,upper) if lower<=v<=upper and v>0]
        axis.set_yticks(sorted(set([1.0,*ticks])))
        axis.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f"{v:g}×"))
        axis.yaxis.set_minor_formatter(NullFormatter())
        ns=sorted({r["n"] for r in selected})
        axis.set_xticks(ns,[f"{n:,}" for n in ns]);axis.xaxis.set_minor_formatter(NullFormatter())
        axis.set_title(f"{family} · intrusion {p}‰ of n",fontsize=10);axis.set_xlabel("Vertices n")
        axis.set_ylabel("KKT / compacting Borůvka time");axis.grid(alpha=.18);axis.legend(frameon=False,fontsize=8)
    finish(fig,"runtime_ratios","Below 1× favors KKT. Ratios are paired before hierarchical medians; graph ranges are descriptive, not confidence intervals.\nAll manifest cases retained. Same production algorithms and common input/output boundary.")
    if not work_summary and not traces_summary:
        for extension in ("png","svg","pdf"):
            path=output/("contraction_edge_volume."+extension)
            if path.exists():path.unlink()
        return
    fig,axes=canvas()
    for axis,(family,p) in zip(axes.flat,groups):
        densities=sorted({r["density"] for r in summary if r["family"]==family and r["intrusion_per_mille"]==p})
        for i,d in enumerate(densities):
            if work_summary:
                for algorithm,style in (("kkt","-"),("compacting_boruvka","--")):
                    points=sorted((r for r in work_summary if (r["family"],r["intrusion_per_mille"],r["density"],r["algorithm"])==(family,p,d,algorithm)),key=lambda r:r["n"])
                    axis.plot([r["n"] for r in points],[r["contraction_edges_over_m"] for r in points],style+"o",color=colors(i%10),ms=3,label=f"d={d} {algorithm}")
            else:
                by_n=collections.defaultdict(list)
                for r in traces_summary:
                    if (r["family"],r["intrusion_per_mille"],r["density"])==(family,p,d):by_n[r["n"]].append(r["contraction_edges_over_m"])
                axis.plot(sorted(by_n),[statistics.fmean(by_n[n]) for n in sorted(by_n)],"--o",color=colors(i%10),label=f"d={d} compaction")
        axis.set_xscale("log",base=2);axis.set_ylim(bottom=0)
        ns=sorted({r["n"] for r in summary if r["family"]==family and r["intrusion_per_mille"]==p})
        axis.set_xticks(ns,[f"{n:,}" for n in ns]);axis.xaxis.set_minor_formatter(NullFormatter())
        axis.set_title(f"{family} · intrusion {p}‰ of n",fontsize=10);axis.set_xlabel("Vertices n")
        axis.set_ylabel("Sum of contraction input edges / m");axis.grid(alpha=.18);axis.legend(frameon=False,fontsize=7)
    finish(fig,"contraction_edge_volume","Both strategies use the SAME contraction_edges counter: one input-edge incidence per production contraction call.\nArithmetic seed means; not elapsed time or individual loop visits. Verification and other work are reported separately.")


def report(output, summaries, work_summary, metadata):
    leads=sum(r["paired_runtime_ratio"] < 1 for r in summaries)
    robust=sum(r["all_graph_medians_below_one"] for r in summaries)
    lines=["# Unchanged KKT versus continued production contraction","",
        f'Validated {metadata["timing_rows"]:,} timed calls across {len(summaries)} manifest cases; '
        f'{metadata["checked_warmup_calls"]:,} additional checked warmup calls are not timing rows.',"",
        f"KKT has a lower paired case median in **{leads}/{len(summaries)}** cases; "
        f"all graph medians favor KKT in **{robust}/{len(summaries)}**. These are this run's descriptive results, not automatic confirmation of a selected hypothesis.","",
        "Every ratio divides matched call times first, then takes medians across repetitions, sampling seeds and graph seeds. Independent timing medians need not divide to the paired ratio. Graph ranges are not confidence intervals. Order-stratified summaries and every individual loss/tie are retained.","",
        "| Case | KKT / compaction [graph range] | KKT ms | Compaction ms | KKT losses / pairs |",
        "|---|---:|---:|---:|---:|"]
    for r in summaries:
        lines.append(f'| {r["case_id"]} | {r["paired_runtime_ratio"]:.4f} [{r["graph_min_ratio"]:.4f}, {r["graph_max_ratio"]:.4f}] | {r["kkt_median_ns"]/1e6:.3f} | {r["compacting_boruvka_median_ns"]/1e6:.3f} | {r["kkt_slower_observations"]}/{r["paired_observations"]} |')
    lines += ["","![Every runtime case](runtime_ratios.png)","",
        "The comparison uses identical production contraction code and reserved ID-set output. It measures whole continuation strategies, including recursive/iterative storage lifetimes, RNG, sampling and verification. Engineered hierarchy, cheap-backbone and hierarchical-distance cases are stress tests, not representative application graphs. Globally randomized weight controls share topology/IDs/order only; their full weighted fingerprints are not required to match.","",
        "Timing and instrumented work are separate runs. Work means average sampling seeds within graphs, then graph seeds. The logical proxy sums mixed loop/table/storage/hash-API events, omitting allocator internals, collisions, deallocation and cache behavior; it is not CPU instructions."]
    if work_summary or metadata["trace_graphs"]:
        lines += ["","![Contraction edge volume](contraction_edge_volume.png)","",
            "Contraction volumes compare `contraction_edges` for both algorithms, not KKT recursive input volume. Verification input edges, copies, initialized slots and the full proxy remain separate columns. Traces validate complete contraction chains, selected-edge accounting and exact dyadic halving for unperturbed hierarchy cases. Crosschecks compare fingerprints and root-after-two dimensions; full intermediate edge lists are not exported."]
    lines += ["","Input hashes, exact manifest and ordered seed banks are recorded in analysis_inputs.json. Build/machine provenance comes from the accompanying runner metadata, not from timing CSV alone."]
    (output/"report.md").write_text("\n".join(lines)+"\n")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ("timing-csv","manifest","output-dir"):
        parser.add_argument("--"+flag,required=True,type=Path)
    parser.add_argument("--graph-seeds",required=True,type=seed_bank)
    parser.add_argument("--sampling-seeds",required=True,type=seed_bank)
    parser.add_argument("--repetitions",required=True,type=int)
    parser.add_argument("--warmups",required=True,type=int)
    parser.add_argument("--trace-csv",type=Path)
    parser.add_argument("--work-csv",type=Path)
    parser.add_argument("--validate-only",action="store_true")
    args=parser.parse_args()
    cases=load_manifest(args.manifest)
    timing=load_timing(args.timing_csv,cases,args.graph_seeds,args.sampling_seeds,args.repetitions,args.warmups)
    work=load_work(args.work_csv,cases,args.graph_seeds,args.sampling_seeds) if args.work_csv else {}
    traces=load_traces(args.trace_csv,cases,args.graph_seeds) if args.trace_csv else {}
    crosscheck(timing,work,traces,args.sampling_seeds)
    metadata={"cases":len(cases),"timing_rows":len(timing),"work_rows":len(work),"trace_graphs":len(traces),
        "labeled_graph_realizations":len(cases)*len(args.graph_seeds),
        "distinct_input_fingerprints":len({r["input_fingerprint"] for r in timing.values()}),
        "distinct_topology_order_fingerprints":len({r["topology_fingerprint"] for r in timing.values()}),
        "trace_rows":sum(len(r) for r in traces.values()),"graph_seeds":args.graph_seeds,
        "sampling_seeds":args.sampling_seeds,"repetitions":args.repetitions,"warmups":args.warmups,
        "checked_warmup_calls":len(cases)*len(args.graph_seeds)*len(args.sampling_seeds)*len(ALGORITHMS)*args.warmups,
        "validation":"pass","inputs":{},"analysis_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "work_registry_sha256":hashlib.sha256(Path(__file__).with_name("work_metrics.hpp").read_bytes()).hexdigest()}
    for name in ("timing_csv","manifest","trace_csv","work_csv"):
        path=getattr(args,name)
        if path:metadata["inputs"][name]={"path":str(path.resolve()),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    if args.validate_only:
        print(json.dumps(metadata,indent=2));return
    args.output_dir.mkdir(parents=True,exist_ok=True)
    summaries,graphs,pairs,orders=aggregate_timing(timing,cases,args.graph_seeds,args.sampling_seeds,args.repetitions)
    work_summary,work_graphs,trace_summary,rounds=aggregate_work(work,traces,cases,args.graph_seeds,args.sampling_seeds)
    for name,rows in (("paired_summary",summaries),("graph_summary",graphs),("paired_pairs",pairs),
        ("order_summary",orders),("work_summary",work_summary),("graph_work_summary",work_graphs),
        ("trace_summary",trace_summary),("round_edge_volumes",rounds)):
        write_csv(args.output_dir/(name+".csv"),rows)
    (args.output_dir/"analysis_inputs.json").write_text(json.dumps(metadata,indent=2)+"\n")
    plots(summaries,work_summary,trace_summary,args.output_dir)
    report(args.output_dir,summaries,work_summary,metadata)
    print(f"Validated {len(timing)} timing, {len(work)} work, and {metadata['trace_rows']} trace rows; wrote {args.output_dir}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError,OSError) as error:
        print("continuation analysis: "+str(error),file=sys.stderr)
        sys.exit(1)
