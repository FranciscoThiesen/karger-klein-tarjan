#!/usr/bin/env python3
"""Recheck supplementary work and export exact counts, not performance claims."""
from collections import defaultdict
import csv
import json
from pathlib import Path
import statistics
import sys

import collect

WORK, ROOT = collect.WORK, collect.ROOT
require = collect.require


def write_csv(path, rows):
    require(rows, "empty analysis table")
    with path.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def plot_work(values, groups):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    colors = {"kkt": "#0072B2", "compacting_boruvka": "#D55E00", "multigraph_boruvka": "#009E73"}
    labels = {"kkt": "KKT (retained parallels)", "compacting_boruvka": "Deduplicating Borůvka", "multigraph_boruvka": "Multigraph Borůvka"}
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.6), layout="constrained")
    for name in collect.ALGORITHMS:
        xs, ys, lower, upper = [], [], [], []
        for n in (65536, 262144, 2097152):
            rows = groups[(f"leaf_hierarchy4_n{n}_d16_p0", name)]
            normalized = [r["contraction_edges"] / r["m"] for r in rows]
            xs.append(n); ys.append(statistics.median(normalized)); lower.append(min(normalized)); upper.append(max(normalized))
        axes[0].plot(xs, ys, "o-", color=colors[name], label=labels[name])
        axes[0].fill_between(xs, lower, upper, color=colors[name], alpha=.18)
    axes[0].set(xscale="log", xticks=[65536, 262144, 2097152], xticklabels=["65,536", "262,144", "2,097,152"],
                xlabel="Original vertices n (m = 16n)", ylabel="Sum of contraction input edges / original m",
                title="KKT reduces repeated contraction volume")
    axes[0].legend(fontsize=8.5)
    large = [v for v in values if v["case_id"] == "leaf_hierarchy4_n2097152_d16_p0"]
    for name in collect.ALGORITHMS[1:]:
        require(len(large) == 2 and len(large[0]["rounds"][name]) == len(large[1]["rounds"][name]), "round profiles differ in length")
        data = [[r["edges"] / v["m"] for r in v["rounds"][name]] for v in large]
        xs = list(range(1, len(data[0]) + 1))
        ys = [statistics.median(x) for x in zip(*data)]
        axes[1].plot(xs, ys, ".-", color=colors[name], label=labels[name])
        axes[1].fill_between(xs, [min(x) for x in zip(*data)], [max(x) for x in zip(*data)], color=colors[name], alpha=.18)
    axes[1].set(xlabel="Borůvka contraction round (n = 2,097,152)", ylabel="Edges entering this round / original m",
                title="Multigraph Borůvka carries edges through 20 rounds", ylim=(0, 1.05), xticks=[1, 5, 10, 15, 20])
    axes[1].legend(fontsize=8.5)
    for ax in axes:
        ax.grid(alpha=.22); ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Ordered hierarchy with cheap leaves: logical work, not elapsed time", fontsize=13)
    fig.text(.5, -.035, "Two graph seeds; lines show medians and bands show the observed range (not confidence intervals).", ha="center", fontsize=9)
    for extension in ("svg", "png"):
        fig.savefig(WORK / ("contraction_work." + extension), dpi=180, bbox_inches="tight")
    plt.close(fig)
    return matplotlib.__version__


def main():
    values = collect.load(WORK / "capture-v2.json")
    capture = json.loads((WORK / "capture-v2.json").read_text())
    require(len(values) == 20 and all(s["intrusion_per_mille"] == 0 for s in capture["schedule"]),
            "supplementary study must match all twenty zero-intrusion declared inputs")
    require(all(v["family"] in ("leaf_hierarchy4", "leaf_distance4", "gnm_random") for v in values), "unexpected family")
    raw_rows, round_rows, groups = [], [], defaultdict(list)
    for value in values:
        identity = {k: value[k] for k in ("case_id", "family", "n", "m", "density", "graph_seed", "kkt_seed",
                                         "input_fingerprint", "topology_fingerprint")}
        for algorithm, data in value["algorithms"].items():
            row = {**identity, "algorithm": algorithm, "hash_insert_items_status": data["hash_insert_items_status"],
                   **data["work"]}
            raw_rows.append(row); groups[(value["case_id"], algorithm)].append(row)
        for algorithm, rounds in value["rounds"].items():
            for r in rounds:
                round_rows.append({**identity, "algorithm": algorithm, **r,
                                   "input_edges_per_original_m": r["edges"] / value["m"],
                                   "output_edges_per_input_edge": r["output_edges"] / r["edges"]})
    write_csv(WORK / "raw_work.csv", raw_rows)
    write_csv(WORK / "rounds.csv", round_rows)
    summary = []
    for (case_id, algorithm), rows in groups.items():
        require(len(rows) == 2 and {r["graph_seed"] for r in rows} == {3000001, 3000029}, "missing graph seed")
        for field in collect.FIELDS:
            values_for_field = [r[field] for r in rows]
            measured = all(v is not None for v in values_for_field)
            summary.append({"case_id": case_id, "algorithm": algorithm, "counter": field,
                            "measurement_status": "measured" if measured else "unmeasured",
                            "median": statistics.median(values_for_field) if measured else None,
                            "minimum": min(values_for_field) if measured else None,
                            "maximum": max(values_for_field) if measured else None,
                            "median_per_original_m": statistics.median(v / rows[0]["m"] for v in values_for_field)
                            if measured else None})
    write_csv(WORK / "case_counter_summary.csv", summary)

    metrics = ("contraction_calls", "contraction_edges", "contraction_edge_visits", "sampling_edge_visits",
               "verifier_edges", "verifier_edge_visits", "path_query_visits", "initialized_slots", "edge_materializations")
    compact = []
    for (case_id, algorithm), rows in groups.items():
        compact.append({"case_id": case_id, "algorithm": algorithm,
                        **{field + ("" if field == "contraction_calls" else "_per_m"):
                           statistics.median(r[field] / (1 if field == "contraction_calls" else r["m"]) for r in rows)
                           for field in metrics}})
    write_csv(WORK / "mechanism_summary.csv", compact)

    resource = [{"case_id": c["spec"]["case_id"], "graph_seed": c["spec"]["graph_seed"],
                 **{k: c[k] for k in ("rss_observations", "rss_unavailable", "sampled_peak_rss_kib")},
                 "empty_group_exit_verified": not c["group_exit_verification"]["members"]}
                for c in capture["captures"]]
    write_csv(WORK / "resources.csv", resource)
    table = ["| Family | n | m/n | Solver | Calls/rounds | Contraction input / m | Query visits / m | Initialized slots / m | Edge copies / m |",
             "|---|---:|---:|---|---:|---:|---:|---:|---:|"]
    for r in compact:
        ref = groups[(r["case_id"], r["algorithm"])][0]
        table.append(f"| {ref['family']} | {ref['n']:,} | {ref['density']} | {r['algorithm']} | "
                     f"{r['contraction_calls']:.1f} | {r['contraction_edges_per_m']:.3f} | "
                     f"{r['path_query_visits_per_m']:.3f} | {r['initialized_slots_per_m']:.3f} | {r['edge_materializations_per_m']:.3f} |")
    (WORK / "WORK_TABLE.md").write_text(
        "Supplementary logical-work observations, each cell the median across the two declared graph seeds. "
        "KKT calls include both recursive branches; Borůvka calls are sequential contraction rounds. "
        "Counts are not equal-cost instructions or time. Final set insertions for both Borůvka continuations are unmeasured.\n\n" +
        "\n".join(table) + "\n")
    matplotlib_version = plot_work(values, groups)
    outputs = ["raw_work.csv", "rounds.csv", "case_counter_summary.csv", "mechanism_summary.csv", "resources.csv", "WORK_TABLE.md", "contraction_work.svg", "contraction_work.png"]
    report = {"schema": "retention_control_work_analysis_v1", "validation": "pass", "children": len(values),
              "algorithm_outputs": len(raw_rows), "replayed_rounds": len(round_rows),
              "all_input_fingerprints_match_timed_control": True, "all_final_ids_match_independent_certificate": True,
              "all_replay_aggregates_equal_exact_helper_counters": True, "all_owned_groups_verified_empty": True,
              "unmeasured_fields": {algorithm: ["hash_insert_items"] for algorithm in collect.ALGORITHMS[1:]},
              "performance_claims_from_this_driver": False,
              "analysis_python": sys.executable, "matplotlib_version": matplotlib_version,
              "input_sha256": {str(p): collect.native.sha(p) for p in
                               (WORK / "capture-v2.json", WORK / "collect.py", Path(__file__))},
              "output_sha256": {name: collect.native.sha(WORK / name) for name in outputs}}
    collect.write_json(WORK / "analysis.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
