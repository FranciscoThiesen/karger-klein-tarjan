#!/usr/bin/env python3
"""Four-campaign attachment summary; run only after native timing has stopped.

Accept complete strict captures or the separately validated interrupted-B
composite. The latter always retains its failed original execution status.
Each campaign retains its own paired medians. Confirmation bars are observed
graph-median ranges, not confidence intervals. Discovery ranges are omitted
uniformly; their complete trial ranges and losses remain in copied data.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import shutil
import sys


SELECTED = ("leaf_hierarchy4", "leaf_distance4")
CONTROLS = ("leaf_shuffled4", "leaf_random4")
CONFIRMATION_SIZES = (65536, 262144, 524288, 1048576, 2097152)
GRAPH_SEEDS = {1000039, 1000081, 1000099}
SAMPLING_SEEDS = {401, 503}
STYLES = {
    "pilot": dict(label="Discovery: original pilot", color="#717780", marker="o", linestyle=":"),
    "large": dict(label="Discovery: larger instances", color="#8662AC", marker="^", linestyle="--"),
    "confirmation_a": dict(label="Confirmation A", color="#0072B2", marker="s", linestyle="-"),
    "confirmation_b": dict(label="Confirmation B", color="#D55E00", marker="D", linestyle="-."),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_plot_helper(repo):
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(repo / "benchmark"))
    helper = importlib.import_module("plot_mst_search")
    require(Path(helper.__file__).resolve() == repo / "benchmark/plot_mst_search.py",
            "plot helper did not resolve to the requested repository")
    return helper


def bound_files(registry, inputs):
    require(type(registry) is dict and registry, "missing bound source registry")
    for name, digest in registry.items():
        path = Path(name).resolve(strict=True)
        require(path.is_file() and sha(path) == digest, "bound source changed: " + str(path))
        inputs[str(path)] = digest


def load_composite(helper, directory, assessment_dir):
    """Explicit composite contract; never present this as a successful capture."""
    directory = directory.resolve(strict=True)
    path = directory / "provenance.json"
    provenance = helper.read_json(path)
    require(provenance.get("schema") == "attachment_confirmation_composite_v1"
            and provenance.get("validation") == "pass", "expected validated interrupted-B composite")
    require(all(provenance.get(field) == 0 for field in ("rows_removed", "rows_adjusted", "native_children_rerun")),
            "composite removed, adjusted or reran observations")
    metadata = provenance.get("composite_metadata", {})
    require(metadata.get("schema") == "attachment_composite_metadata_v1"
            and metadata.get("execution_status") == "interrupted_then_recovered"
            and metadata.get("original_b_capture_validation") == "failed"
            and metadata.get("original_b_controller_validation") == "failed"
            and metadata.get("frozen_execution_completed") is False,
            "composite must retain failed original B execution")
    require(metadata.get("algorithms") == list(helper.ALGORITHMS)
            and metadata.get("checked_rows") == 2160
            and metadata.get("checked_timed_rows") == 1800
            and metadata.get("checked_warmup_rows") == 360,
            "composite protocol or call counts differ")
    require(metadata.get("graph_seeds") == sorted(GRAPH_SEEDS)
            and metadata.get("sampling_seeds") == sorted(SAMPLING_SEEDS)
            and metadata.get("repetitions") == 5 and metadata.get("warmups") == 1,
            "composite confirmation seed/repetition protocol differs")
    order = metadata.get("case_order")
    require(type(order) is list and len(order) == len(set(order)) == 12,
            "composite case menu differs")
    captures = provenance.get("source_capture_metadata", {})
    require(captures.get("interrupted_prefix", {}).get("validation") == "failed"
            and captures.get("recovery_tail", {}).get("validation") == "pass"
            and provenance.get("original_controller_metadata", {}).get("validation") == "failed",
            "composite original/tail status differs")
    registry = provenance.get("source_parts", {})
    for part, positions, calls in (("interrupted_prefix", [1,60], 1800), ("recovery_tail", [61,72], 360)):
        require(registry.get(part, {}).get("original_child_positions") == positions
                and registry[part].get("native_calls") == calls, "composite source split differs")
    inputs = {str(path): sha(path)}
    bound_files(provenance.get("input_sha256"), inputs)
    derived = provenance.get("derived_sha256", {})
    required = {"comparisons.csv", "summary.csv", "graph_comparisons.csv", "graph_summary.csv",
                "paired_ratios.csv", "validated_calls.csv", "call_diagnostics.csv", "source_parts.csv", "README.md"}
    require(required <= set(derived), "composite omitted a complete table")
    for name, digest in derived.items():
        require(Path(name).name == name, "invalid composite derived path")
        current = directory / name
        require(sha(current) == digest, "composite derived table hash mismatch: " + name)
        inputs[str(current)] = digest
    # Bind the independent numerical assessment to this exact composite.
    assessment_dir = assessment_dir.resolve(strict=True)
    ap = assessment_dir / "provenance.json"
    assessment_provenance = helper.read_json(ap)
    require(assessment_provenance.get("schema") == "attachment_recovery_assessor_provenance_v1"
            and assessment_provenance.get("validation") == "pass"
            and assessment_provenance.get("original_frozen_execution_success") is False,
            "expected successful numerical assessment of failed-execution recovery")
    require(assessment_provenance.get("input_sha256", {}).get(str(path)) == sha(path),
            "numerical assessment does not bind this composite")
    bound_files(assessment_provenance["input_sha256"], inputs)
    for name, digest in assessment_provenance.get("derived_sha256", {}).items():
        require(Path(name).name == name and sha(assessment_dir / name) == digest,
                "numerical assessment artifact changed: " + name)
        inputs[str(assessment_dir / name)] = digest
    assessment = helper.read_json(assessment_dir / "assessment.json")
    require(assessment.get("schema") == "attachment_recovery_numerical_assessment_v1"
            and assessment.get("validation") == "pass"
            and assessment.get("original_frozen_execution_success") is False
            and assessment.get("original_b_capture_validation") == "failed"
            and assessment.get("counts") == {"total_calls":4320, "timed_calls":3600, "warmup_calls":720,
                    "a_children":72, "b_prefix_children":60, "recovery_children":12},
            "numerical assessment status/counts differ")
    inputs[str(ap)] = sha(ap)
    identities, comparisons, summaries = {}, {}, {}
    trials = 30
    for raw in helper.read_csv(directory / "comparisons.csv", helper.COMPARISON_FIELDS):
        identity = helper.check_identity(raw, "composite comparison")
        case, metric, algorithm = identity["case_id"], raw["metric"], raw["competitor"]
        key = (case, metric, algorithm)
        require(case in order and identities.get(case, identity) == identity
                and metric in helper.METRICS and algorithm in helper.ALGORITHMS[1:]
                and key not in comparisons, "invalid composite comparison identity")
        identities[case] = identity
        row = {**identity, "metric":metric, "competitor":algorithm,
               **helper.nested_range(raw, ("trial_min_ratio", "graph_min_ratio", "median_paired_ratio",
                                           "graph_max_ratio", "trial_max_ratio"), "composite comparison")}
        for field in ("individual_wins", "individual_losses", "individual_ties", "graph_seeds", "pairs"):
            row[field] = helper.integer(raw[field], field)
        require(row["pairs"] == trials and row["graph_seeds"] == 3
                and sum(row[f] for f in ("individual_wins", "individual_losses", "individual_ties")) == trials,
                "composite comparison omits trials")
        comparisons[key] = row
    require(set(comparisons) == {(c,m,a) for c in order for m in helper.METRICS for a in helper.ALGORITHMS[1:]},
            "composite omits a case/clock/comparator")
    for raw in helper.read_csv(directory / "summary.csv", helper.SUMMARY_FIELDS):
        identity = helper.check_identity(raw, "composite runtime")
        case, metric, algorithm = identity["case_id"], raw["metric"], raw["algorithm"]
        key = (case, metric, algorithm)
        require(identities.get(case) == identity and metric in helper.METRICS
                and algorithm in helper.ALGORITHMS and key not in summaries, "invalid composite runtime identity")
        require(helper.integer(raw["graph_seeds"], "graph count") == 3
                and helper.integer(raw["timed_calls"], "timed calls") == trials, "composite runtime omits trials")
        summaries[key] = {**identity, "metric":metric, "algorithm":algorithm,
                         **helper.nested_range(raw, ("trial_min_ns", "graph_min_ns", "median_ns",
                                                     "graph_max_ns", "trial_max_ns"), "composite runtime")}
    require(set(summaries) == {(c,m,a) for c in order for m in helper.METRICS for a in helper.ALGORITHMS},
            "composite omits a case/clock/solver")
    parts_fields = ("case_id","graph_seed","kkt_seed","phase","repetition","algorithm",
                    "source_part","original_child_index","source_csv","source_csv_sha256")
    parts = list(helper.read_csv(directory / "source_parts.csv", parts_fields))
    require(len(parts) == 2160, "composite source ledger omits calls")
    children, row_keys = {}, set()
    for row in parts:
        index = helper.integer(row["original_child_index"], "child index")
        part = "interrupted_prefix" if index <= 60 else "recovery_tail"
        require(1 <= index <= 72 and row["source_part"] == part, "composite source ledger has invalid part")
        graph, sample = sorted(GRAPH_SEEDS)[((index-1)%6)//2], sorted(SAMPLING_SEEDS)[(index-1)%2]
        require((row["case_id"], int(row["graph_seed"]), int(row["kkt_seed"])) == (order[(index-1)//6], graph, sample),
                "composite source ledger child order differs")
        key = tuple(row[f] for f in parts_fields[:6])
        require(key not in row_keys and row["algorithm"] in helper.ALGORITHMS,
                "composite source ledger has duplicate/unknown call")
        row_keys.add(key)
        rep = helper.integer(row["repetition"], "repetition")
        require((row["phase"] == "warmup" and rep == 0) or (row["phase"] == "timed" and 0 <= rep < 5),
                "composite source ledger has invalid phase/repetition")
        child = (row["source_csv"], row["source_csv_sha256"])
        require(children.get(index, child) == child and inputs.get(child[0]) == child[1],
                "composite source ledger child binding differs")
        children[index] = child
    require(set(children) == set(range(1,73)) and len({v[0] for v in children.values()}) == 72,
            "composite source ledger omits/repeats children")
    groups = defaultdict(list)
    for case in order:
        item = identities[case]; groups[(item["family"],item["density"])].append(item)
    for specs in groups.values():
        specs.sort(key=lambda spec:spec["n"])
        require(len({s["n"] for s in specs}) == len(specs), "composite duplicate family size")
    return {"directory":directory, "label":"B interrupted + recovery", "metadata":metadata,
            "provenance":provenance, "groups":groups, "comparisons":comparisons, "summaries":summaries,
            "input_sha256":inputs, "cases":12, "trials_per_algorithm_case":30,
            "is_composite":True, "source_children":children, "assessment_directory":assessment_dir}


def load_all(helper, directories, composite_b=False, assessment_dir=None):
    campaigns = []
    for role, folder in directories:
        campaign = (load_composite(helper, folder, assessment_dir) if role == "confirmation_b" and composite_b
                    else helper.load_campaign(folder))
        campaign["role"] = role
        provenance = helper.read_json(campaign["directory"] / "provenance.json")
        campaign["provenance"] = provenance
        campaign["is_confirmation"] = role.startswith("confirmation_")
        campaign["display_label"] = "B interrupted + recovery" if campaign.get("is_composite") else STYLES[role]["label"]
        for family in (*SELECTED, *CONTROLS):
            require((family,16) in campaign["groups"], f"{role}: missing required selected/control family {family}")
        if campaign["is_confirmation"]:
            metadata = campaign["metadata"]
            require(set(metadata["graph_seeds"]) == GRAPH_SEEDS
                    and set(metadata["sampling_seeds"]) == SAMPLING_SEEDS
                    and metadata["repetitions"] == 5 and metadata["warmups"] == 1,
                    f"{role}: confirmation seed/repetition protocol differs")
            expected_groups = {(family,16) for family in (*SELECTED,*CONTROLS)}
            require(set(campaign["groups"]) == expected_groups and campaign["cases"] == 12,
                    f"{role}: confirmation case menu differs from the declared 12 cases")
            for family in SELECTED:
                require(tuple(spec["n"] for spec in campaign["groups"][(family,16)]) == CONFIRMATION_SIZES,
                        f"{role}: selected size grid is incomplete or different")
            for family in CONTROLS:
                require([spec["n"] for spec in campaign["groups"][(family,16)]] == [2097152],
                        f"{role}: control size differs")
        else:
            require(campaign["metadata"]["graph_seeds"] == [5009]
                    and campaign["metadata"]["sampling_seeds"] == [149],
                    f"{role}: discovery seed banks differ from the declared campaign")
        campaigns.append(campaign)
    first = campaigns[0]["metadata"]
    for campaign in campaigns[1:]:
        for field in ("binary_sha256","profile","source_sha256","build_recipe_sha256"):
            require(campaign["metadata"][field] == first[field],
                    f"{campaign['role']}: native source/binary/profile differs; do not silently present a fixed-implementation comparison")
    a, b = campaigns[2]["metadata"], campaigns[3]["metadata"]
    require(a["graph_seeds"] == b["graph_seeds"] and a["sampling_seeds"] == b["sampling_seeds"]
            and a["case_order"] == list(reversed(b["case_order"])),
            "A/B do not match the declared repeated-seed, reversed-case-order protocol")
    return campaigns


def points(campaign, family, metric):
    return [campaign["comparisons"][(spec["case_id"],metric,"compacting_boruvka")]
            for spec in campaign["groups"][(family,16)]]


def write_csv(path, rows):
    require(rows, "refusing empty selected data")
    with path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def selected_rows(campaigns, families):
    result = []
    for campaign in campaigns:
        for family in families:
            for metric in ("wall","cpu"):
                for row in points(campaign,family,metric):
                    result.append({"campaign":campaign["role"],
                                   "campaign_label":campaign.get("display_label",STYLES[campaign["role"]]["label"]),
                                   "plotted_range":"observed graph medians" if campaign["is_confirmation"] else "omitted uniformly",
                                   **row})
    return result


def copy_sources(campaigns, output, inputs):
    copied = []
    for campaign in campaigns:
        source = campaign["directory"]
        destination = output / "data" / campaign["role"]
        destination.mkdir(parents=True)
        provenance = campaign["provenance"]
        # Complete unfiltered derived tables retain all competitors, controls,
        # individual losses and diagnostic flags, including off-figure cases.
        names = ["comparisons.csv","summary.csv","graph_comparisons.csv","graph_summary.csv","paired_ratios.csv",
                 "validated_calls.csv","call_diagnostics.csv", "README.md" if campaign.get("is_composite") else "report.md"]
        if campaign.get("is_composite"):
            names.append("source_parts.csv")
        for name in names:
            path = source/name
            expected = provenance["derived_sha256"].get(name)
            require(expected is not None and sha(path) == expected, f"modified derived source: {path}")
            inputs[str(path.resolve())] = expected
            shutil.copyfile(path,destination/name)
            copied.append({"campaign":campaign["role"],"source":str(path),
                           "copy":str((destination/name).relative_to(output)),"sha256":expected})
        shutil.copyfile(source/"provenance.json",destination/"analysis_provenance.json")
        if campaign.get("is_composite"):
            # Original combined B has only 59 children. The prefix validator
            # recovered completed child 60 from its own native CSV; copy all
            # 72 child CSVs rather than imply the failed combined file is full.
            parts = provenance["source_parts"]
            raw_paths = []
            for part, raw_field, label in (("interrupted_prefix","original_failed_csv","original_failed_incomplete"),
                                          ("recovery_tail","raw_csv","recovery_tail")):
                raw = Path(parts[part][raw_field]).resolve(strict=True)
                meta = provenance["source_capture_metadata"][part]
                raw_paths.extend(((raw,label+".csv"), (raw.with_suffix(".json"),label+"_metadata.json"),
                                  (Path(meta["manifest"]).resolve(strict=True),label+"_manifest.csv")))
            (destination/"native_children").mkdir()
            raw_paths.extend((Path(path),f"native_children/{index:02d}.csv")
                             for index,(path,_) in sorted(campaign["source_children"].items()))
            assessment = campaign["assessment_directory"]
            raw_paths.extend((assessment/name,"numerical_assessment_"+name)
                             for name in ("assessment.json","provenance.json","README.md"))
            for path,name in raw_paths:
                expected = campaign["input_sha256"].get(str(path))
                require(expected is not None and sha(path) == expected, "composite raw binding changed: " + str(path))
                inputs[str(path)] = expected
                shutil.copyfile(path,destination/name)
                copied.append({"campaign":campaign["role"],"source":str(path),
                               "copy":str((destination/name).relative_to(output)),"sha256":expected})
            inputs.update(campaign["input_sha256"])
            continue
        # Combined native CSV includes every timed call and warmup. Copy its
        # original metadata and case manifest too; child files remain in the
        # linked full study archive and are bound by the copied provenance.
        metadata = campaign["metadata"]
        raw = Path(metadata["raw_csv"]).resolve(strict=True)
        raw_paths = ((raw,"raw_capture.csv"), (raw.with_suffix(".json"),"raw_capture_metadata.json"),
                     (Path(metadata["manifest"]).resolve(strict=True),"raw_case_manifest.csv"))
        for path,name in raw_paths:
            expected = provenance["input_sha256"].get(str(path))
            require(expected is not None and sha(path) == expected, f"raw source changed after strict analysis: {path}")
            inputs[str(path)] = expected
            shutil.copyfile(path,destination/name)
            copied.append({"campaign":campaign["role"],"source":str(path),
                           "copy":str((destination/name).relative_to(output)),"sha256":expected})
        inputs.update(campaign["input_sha256"])
    return copied


def ratio_limits(campaigns, families):
    """Bounds for every displayed median/range; no outlier cutoff."""
    values = [.9,1.0]
    for campaign in campaigns:
        for family in families:
            for metric in ("wall","cpu"):
                for row in points(campaign,family,metric):
                    values.extend([row["graph_min_ratio"],row["graph_max_ratio"]]
                                  if campaign["is_confirmation"] else [row["median_paired_ratio"]])
    lo,hi = min(values),max(values)
    pad = max(.025,.09*(hi-lo))
    # Every confirmation graph-range endpoint must remain in view, including
    # extremely small ratios caused by a very slow comparator. No positive
    # lower cutoff or wins/losses-based limit is permitted.
    lower_limit, upper_limit = max(0.0,lo-pad), hi+pad
    require(lower_limit <= lo and upper_limit >= hi, "ratio axis would clip an observed graph range")
    return lower_limit, upper_limit


def render(plt, Line2D, FixedLocator, FuncFormatter, campaigns, families, output, name, controls):
    sizes = sorted({row["n"] for campaign in campaigns for family in families
                    for row in points(campaign,family,"wall")})
    lower_limit, upper_limit = ratio_limits(campaigns, families)
    fig,axes = plt.subplots(2,2,figsize=(14,10),sharex=True,sharey=True)
    fig.subplots_adjust(left=.09,right=.985,top=.84,bottom=.22,wspace=.16,hspace=.24)
    title = "Weight controls across four separate campaigns" if controls else "Selected attachment families across four separate campaigns"
    subtitle = "Shuffled core: cheap local stars preserved · global random: all weights permuted" if controls else "Leaf attachments · b = 4, m = 16n · KKT versus compacting Borůvka"
    fig.suptitle(title,x=.09,ha="left",y=.985,fontsize=17)
    fig.text(.09,.94,subtitle,fontsize=11.5,color="#444444")
    fig.text(.09,.897,"Campaign series are kept separate; B includes the interrupted prefix and declared recovery.",fontsize=10.5,color="#444444")
    for column,family in enumerate(families):
        for row_index,metric in enumerate(("wall","cpu")):
            axis = axes[row_index,column]
            for campaign in campaigns:
                series = points(campaign,family,metric)
                style = STYLES[campaign["role"]]
                x,y = [item["n"] for item in series],[item["median_paired_ratio"] for item in series]
                kwargs = dict(color=style["color"],marker=style["marker"],linestyle=style["linestyle"],
                              linewidth=1.7,markersize=6.5,markeredgewidth=1.1,zorder=4,
                              markerfacecolor=style["color"] if campaign["is_confirmation"] else "white")
                if campaign["is_confirmation"]:
                    errors = [[item["median_paired_ratio"]-item["graph_min_ratio"] for item in series],
                              [item["graph_max_ratio"]-item["median_paired_ratio"] for item in series]]
                    axis.errorbar(x,y,yerr=errors,elinewidth=1.1,capsize=3,**kwargs)
                else:
                    axis.plot(x,y,**kwargs)
            axis.axhline(1,color="#333333",linestyle="--",linewidth=1.1,zorder=1)
            axis.axhline(.9,color="#777777",linestyle=":",linewidth=1.1,zorder=1)
            axis.set_xscale("log",base=2)
            axis.xaxis.set_major_locator(FixedLocator(sizes))
            axis.xaxis.set_major_formatter(FuncFormatter(lambda x,_:f"{int(x):,}"))
            axis.tick_params(axis="x",labelrotation=32,labelsize=9)
            axis.set_xlim(sizes[0]/1.18,sizes[-1]*1.18)
            axis.set_ylim(lower_limit,upper_limit)
            axis.grid(True,alpha=.2,linewidth=.6)
            axis.spines["top"].set_visible(False);axis.spines["right"].set_visible(False)
            if row_index == 0:
                axis.set_title(family,loc="left",fontsize=12,pad=10)
            else:
                axis.set_xlabel("Original vertices n (log scale; actual measured sizes)",fontsize=10)
            if column == 0:
                clock = "Wall time (primary)" if metric == "wall" else "Process CPU (secondary)"
                axis.set_ylabel(clock+"\nKKT / compacting Borůvka",fontsize=11)
    handles = [Line2D([0],[0],color=STYLES[c["role"]]["color"],marker=STYLES[c["role"]]["marker"],
                      linestyle=STYLES[c["role"]]["linestyle"],
                      markerfacecolor=STYLES[c["role"]]["color"] if c["is_confirmation"] else "white",
                      label=c["display_label"],linewidth=1.7,markersize=6.5) for c in campaigns]
    handles += [Line2D([0],[0],color="#333333",linestyle="--",label="Parity: 1.0"),
                Line2D([0],[0],color="#777777",linestyle=":",label="10% lower: 0.9")]
    fig.legend(handles=handles,loc="lower center",bbox_to_anchor=(.535,.075),ncol=3,frameon=False,fontsize=10.5)
    fig.text(.09,.044,"A/B bars: min–max of three observed graph medians, not confidence intervals. Discovery spreads omitted here; retained in full data.",fontsize=9)
    fig.text(.09,.022,"A/B reuse the same three graphs and two KKT seeds. Lines connect measured points only; no fitted crossover or extrapolation.",fontsize=9)
    for suffix in ("png","svg","pdf"):
        fig.savefig(output/f"{name}.{suffix}",dpi=180,facecolor="white")
    plt.close(fig)


def render_appendix(plt, Line2D, FixedLocator, FuncFormatter, helper,
                    campaigns, campaign, index, metric, output, ratios):
    """Fixed four-family appendix with room for full legends and x labels.

    Uses the unchanged helper's full-trial bounds and save routine. This local
    layout avoids altering the existing frozen plotting helper or its outputs.
    """
    groups = sorted(campaign["groups"])
    require(len(groups) == 4, "confirmation appendix requires all four families")
    algorithms = helper.ALGORITHMS[1:] if ratios else helper.ALGORITHMS
    fig, axes = plt.subplots(2,2,figsize=(13,10))
    fig.subplots_adjust(left=.085,right=.97,top=.84,bottom=.21,hspace=.55,wspace=.28)
    for axis,group in zip(axes.flat,groups):
        specs = campaign["groups"][group]
        for algorithm in algorithms:
            rows = [campaign["comparisons" if ratios else "summaries"][(s["case_id"],metric,algorithm)] for s in specs]
            factor,mid,suffix = (1,"median_paired_ratio","ratio") if ratios else (1e-9,"median_ns","ns")
            axis.errorbar([r["n"] for r in rows],[r[mid]*factor for r in rows],
                          yerr=[[factor*(r[mid]-r["trial_min_"+suffix]) for r in rows],
                                [factor*(r["trial_max_"+suffix]-r[mid]) for r in rows]],
                          color=helper.COLORS[algorithm],marker=helper.MARKERS[algorithm],
                          markersize=5.5,linewidth=1.4,elinewidth=.85,capsize=2.2,alpha=.93,zorder=3)
        sizes,bounds = helper.limits(campaigns,group,metric,ratios)
        axis.set_xscale("log",base=2);axis.set_yscale("log",base=2 if ratios else 10)
        axis.set_xlim(sizes[0]/1.25,sizes[-1]*1.25);axis.set_ylim(*bounds)
        axis.xaxis.set_major_locator(FixedLocator(sizes))
        axis.xaxis.set_major_formatter(FuncFormatter(lambda x,_:f"$2^{{{int(round(math.log2(x)))}}}$"))
        axis.tick_params(axis="both",labelsize=8)
        axis.set_xlabel("Vertices n (log scale)",fontsize=9)
        axis.set_ylabel("KKT / comparator (log scale)" if ratios else "Seconds (log scale)",fontsize=9)
        axis.set_title(f"{group[0]}\nm = {group[1]}n",fontsize=11)
        axis.grid(True,which="major",alpha=.20,linewidth=.6)
        if ratios:
            axis.axhline(1,color="#303030",linestyle="--",linewidth=1,zorder=2)
            axis.axhline(.9,color="#777777",linestyle=":",linewidth=1,zorder=2)
    handles = [Line2D([],[],color=helper.COLORS[a],marker=helper.MARKERS[a],markersize=5,
                      linewidth=1.4,label=helper.LABELS[a]) for a in algorithms]
    if ratios:
        handles += [Line2D([],[],color="#303030",linestyle="--",label="Parity: 1.0"),
                    Line2D([],[],color="#777777",linestyle=":",label="10% lower: 0.9")]
    fig.legend(handles=handles,loc="lower center",bbox_to_anchor=(.5,.085),
               ncol=3 if ratios else 5,frameon=False,fontsize=9)
    clock = "Steady elapsed time (primary)" if metric == "wall" else "Process CPU time (secondary)"
    kind = "paired_ratios" if ratios else "runtimes"
    fig.suptitle(campaign["display_label"]+"\n"+clock+" — "+
                 ("paired KKT ratios; below 1 favors KKT" if ratios else "separate algorithm runtimes")+
                 "\n3 graph seeds × 2 sampling seeds × 5 timed repetitions; 1 checked warmup per algorithm",y=.98,fontsize=12)
    fig.text(.5,.025,"Markers: hierarchical medians. Bars: full observed individual-trial min–max, not confidence intervals.\n"
             "Lines connect measured sizes only. Campaigns remain separate; all clock flags and control losses are retained.",
             ha="center",va="bottom",fontsize=8.5)
    paths = helper.save_figure(fig,output,f"campaign_{index:02d}_{metric}_{kind}_01")
    plt.close(fig)
    return {"campaign_index":index,"campaign":campaign["display_label"],"metric":metric,"kind":kind,
            "groups":[{"family":f,"density":d} for f,d in groups],"files":paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root",type=Path,required=True)
    parser.add_argument("--pilot-dir",type=Path,required=True)
    parser.add_argument("--large-dir",type=Path,required=True)
    parser.add_argument("--confirmation-a-dir",type=Path,required=True)
    b_choice = parser.add_mutually_exclusive_group(required=True)
    b_choice.add_argument("--confirmation-b-dir",type=Path)
    b_choice.add_argument("--composite-b-dir",type=Path)
    parser.add_argument("--assessment-dir",type=Path,help="required for interrupted-B composite")
    parser.add_argument("--output-dir",type=Path,required=True)
    args = parser.parse_args()
    try:
        require(not args.output_dir.exists(),"refusing to replace existing summary evidence")
        repo = args.repo_root.resolve(strict=True)
        helper = load_plot_helper(repo)
        directories = [("pilot",args.pilot_dir),("large",args.large_dir),
                       ("confirmation_a",args.confirmation_a_dir),("confirmation_b",args.composite_b_dir or args.confirmation_b_dir)]
        require(bool(args.composite_b_dir) == bool(args.assessment_dir), "composite B requires its numerical assessment")
        require(len({path.resolve() for _,path in directories}) == 4,"campaign directories must be distinct")
        campaigns = load_all(helper,directories,bool(args.composite_b_dir),args.assessment_dir)
        # No plotting imports or file copying occur before all four campaigns,
        # including both complete confirmation matrices, have passed validation.
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D
        from matplotlib.ticker import FixedLocator, FuncFormatter
        plt.rcParams.update({"font.family":"sans-serif","font.size":10,"svg.fonttype":"none"})
        output = args.output_dir.resolve()
        output.mkdir(parents=True,exist_ok=False)
        inputs = {str(Path(__file__).resolve()):sha(Path(__file__).resolve()),
                  str(Path(helper.__file__).resolve()):sha(Path(helper.__file__).resolve())}
        copied = copy_sources(campaigns,output,inputs)
        write_csv(output/"selected_paired_data.csv",selected_rows(campaigns,SELECTED))
        write_csv(output/"control_paired_data.csv",selected_rows(campaigns,CONTROLS))
        render(plt,Line2D,FixedLocator,FuncFormatter,campaigns,SELECTED,output,"selected_families",False)
        render(plt,Line2D,FixedLocator,FuncFormatter,campaigns,CONTROLS,output,"weight_controls",True)
        appendix = output/"all-solvers"
        appendix.mkdir()
        appendix_figures = []
        confirmations = campaigns[2:]
        for index,campaign in enumerate(confirmations,1):
            campaign["label"] = campaign["display_label"]
            for metric in helper.METRICS:
                for ratios in (True,False):
                    appendix_figures.append(render_appendix(plt,Line2D,FixedLocator,FuncFormatter,helper,
                                                confirmations,campaign,index,metric,appendix,ratios))
        appendix_report = ["# Complete five-solver confirmation appendices", "",
             "A and interrupted B plus recovery remain separate. Every measured family, size, solver and control is shown. "
             "Bars span full individual-trial min–max ranges, not confidence intervals. The same family has matching axes across captures. "
             "No flagged observation is removed or adjusted. Large wall/CPU discrepancies remain visible. "
             "Original B failed its frozen execution; the composite contains its 60 completed children plus 12 separately declared recovery children.", ""]
        for record in appendix_figures:
            appendix_report += [f"## {record['campaign']}: {record['metric']} / {record['kind']}", "",
                                f"![Complete observed ranges]({record['files'][0]})", "",
                                " · ".join(f"[{Path(p).suffix[1:].upper()}]({p})" for p in record["files"]), ""]
        (appendix/"README.md").write_text("\n".join(appendix_report))
        report = ["# Separate-campaign attachment summary","",
                  "These figures retain each campaign's paired medians separately. Confirmation A/B bars span observed graph medians, not confidence intervals. Discovery ranges are uniformly omitted from these compact figures and retained in the copied complete tables.","",
                  "![Selected ordered families](selected_families.png)","",
                  "![Weight controls, including losses](weight_controls.png)","",
                  "The actual n axis includes only measured sizes. Connecting lines are visual guides, not fitted crossovers. A/B reuse the same graph seeds; their repetitions are not new independent graphs. This script does not declare that the prospective confirmation criterion passed.","",
                  "| Capture | Complete cases | Graph seeds | KKT seeds | Timed calls | Checked warmups | Flagged calls retained | Complete appendix |",
                  "|---|---:|---:|---:|---:|---:|---:|---|"]
        records = []
        for campaign in campaigns:
            meta,provenance = campaign["metadata"],campaign["provenance"]
            link = os.path.relpath(campaign["directory"]/("README.md" if campaign.get("is_composite") else "report.md"),output)
            timed = meta["checked_timed_rows"] if campaign.get("is_composite") else provenance["timed_rows"]
            warmups = meta["checked_warmup_rows"] if campaign.get("is_composite") else provenance["warmup_rows"]
            report.append(f"| {campaign['display_label']} | {campaign['cases']} | {len(meta['graph_seeds'])} | {len(meta['sampling_seeds'])} | {timed} | {warmups} | {meta['flagged_calls']} | [All five solvers and all cases]({link}) |")
            records.append({"role":campaign["role"],"analysis_directory":str(campaign["directory"]),
                            "label":campaign["display_label"],"cases":campaign["cases"],
                            "graph_seeds":meta["graph_seeds"],"sampling_seeds":meta["sampling_seeds"],
                            "flagged_calls_retained":meta.get("flagged_calls"),
                            "capture_clock_flags_retained":meta.get("capture_clock_flags"),
                            "revision":meta.get("revision"),"binary_sha256":meta["binary_sha256"],
                            "execution_status":meta.get("execution_status","complete"),
                            "recovery_declaration_revision":provenance.get("recovery_declaration_revision")})
        report += ["","[Full five-solver A and B-composite figures](all-solvers/README.md) retain individual-trial ranges for both clocks, including control losses.","",
                   "All comparator results and diagnostic flags remain in each appendix and unfiltered `data/<campaign>/` tables. For interrupted B, the copied original combined CSV is explicitly incomplete (59 children); the source ledger and all 72 copied native child CSVs cover its 60 completed prefix children plus 12 recovery children. The original B capture/controller remain failed. A and recovery have their complete combined CSVs. Full child logs/resource archives remain at the original study paths; these copies are not a relocated standalone raw capture.","",
                   "The compact axes include every A/B graph-median range endpoint. Individual trials can have much wider ranges, including very large wall/CPU discrepancies; those are retained in the full all-comparator appendices and copied tables. No flagged observation is removed or adjusted, and no previous campaign's winner is assumed to remain the winner. Clock flags do not by themselves identify the cause of a disturbed call.","",
                   "**Visual QA pending:** generation success is not evidence that labels, graph-range bars or layout were inspected. Open both PNGs after generation; separately render PDF/SVG if those formats will be distributed.",""]
        (output/"README.md").write_text("\n".join(report))
        for path,expected in inputs.items():
            require(sha(Path(path)) == expected,f"input changed while rendering: {path}")
        provenance = {"schema":"attachment_confirmation_figures_v1","validation":"pass",
                      "campaigns":records,"campaigns_pooled":False,"timings_fitted":False,
                      "graph_range_scope":"observed graph-median min/max for A/B, not confidence intervals",
                      "discovery_ranges":"omitted uniformly in compact figures; all values copied",
                      "appendix_figures":appendix_figures,
                      "visual_qa":"pending","matplotlib_version":matplotlib.__version__,
                      "input_sha256":inputs,"raw_and_derived_copies":copied,
                      "artifact_sha256":{str(path.relative_to(output)):sha(path) for path in sorted(output.rglob("*")) if path.is_file()}}
        (output/"provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
        print(json.dumps({"validation":"pass","separate_campaigns":4,"figures":2,"visual_qa":"pending","output_dir":str(output)}))
    except (ValueError,OSError,KeyError,TypeError,ImportError) as error:
        parser.exit(2,f"confirmation summary: {error}\n")


if __name__ == "__main__":
    main()
