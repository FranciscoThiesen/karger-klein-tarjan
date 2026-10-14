#!/usr/bin/env python3
"""SOURCE-ONLY DRAFT: four-campaign attachment summary; do not run during timing.

Run only after BOTH complete confirmation captures have been strictly analyzed.
Each campaign retains its own paired medians. Confirmation bars are observed
graph-median ranges, not confidence intervals. Discovery ranges are omitted
uniformly; their complete trial ranges and losses remain in copied data.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
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


def load_all(helper, directories):
    campaigns = []
    for role, folder in directories:
        campaign = helper.load_campaign(folder)
        campaign["role"] = role
        provenance = helper.read_json(campaign["directory"] / "provenance.json")
        campaign["provenance"] = provenance
        campaign["is_confirmation"] = role.startswith("confirmation_")
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
                                   "campaign_label":STYLES[campaign["role"]]["label"],
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
        for name in ("comparisons.csv","summary.csv","graph_comparisons.csv","paired_ratios.csv",
                     "validated_calls.csv","call_diagnostics.csv","report.md"):
            path = source/name
            expected = provenance["derived_sha256"].get(name)
            require(expected is not None and sha(path) == expected, f"modified derived source: {path}")
            inputs[str(path.resolve())] = expected
            shutil.copyfile(path,destination/name)
            copied.append({"campaign":campaign["role"],"source":str(path),
                           "copy":str((destination/name).relative_to(output)),"sha256":expected})
        shutil.copyfile(source/"provenance.json",destination/"analysis_provenance.json")
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
    fig.text(.09,.897,"Lower ratios favor KKT. Every line belongs to a separate capture; no observations are pooled.",fontsize=10.5,color="#444444")
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
    handles = [Line2D([0],[0],color=style["color"],marker=style["marker"],linestyle=style["linestyle"],
                      markerfacecolor=style["color"] if role.startswith("confirmation_") else "white",
                      label=style["label"],linewidth=1.7,markersize=6.5)
               for role,style in STYLES.items()]
    handles += [Line2D([0],[0],color="#333333",linestyle="--",label="Parity: 1.0"),
                Line2D([0],[0],color="#777777",linestyle=":",label="10% lower: 0.9")]
    fig.legend(handles=handles,loc="lower center",bbox_to_anchor=(.535,.075),ncol=3,frameon=False,fontsize=10.5)
    fig.text(.09,.044,"A/B bars: min–max of three observed graph medians, not confidence intervals. Discovery spreads omitted here; retained in full data.",fontsize=9)
    fig.text(.09,.022,"A/B reuse the same three graphs and two KKT seeds. Lines connect measured points only; no fitted crossover or extrapolation.",fontsize=9)
    for suffix in ("png","svg","pdf"):
        fig.savefig(output/f"{name}.{suffix}",dpi=180,facecolor="white")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root",type=Path,required=True)
    parser.add_argument("--pilot-dir",type=Path,required=True)
    parser.add_argument("--large-dir",type=Path,required=True)
    parser.add_argument("--confirmation-a-dir",type=Path,required=True)
    parser.add_argument("--confirmation-b-dir",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    args = parser.parse_args()
    try:
        require(not args.output_dir.exists(),"refusing to replace existing summary evidence")
        repo = args.repo_root.resolve(strict=True)
        helper = load_plot_helper(repo)
        directories = [("pilot",args.pilot_dir),("large",args.large_dir),
                       ("confirmation_a",args.confirmation_a_dir),("confirmation_b",args.confirmation_b_dir)]
        require(len({path.resolve() for _,path in directories}) == 4,"campaign directories must be distinct")
        campaigns = load_all(helper,directories)
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
            link = os.path.relpath(campaign["directory"]/"report.md",output)
            report.append(f"| {STYLES[campaign['role']]['label']} | {campaign['cases']} | {len(meta['graph_seeds'])} | {len(meta['sampling_seeds'])} | {provenance['timed_rows']} | {provenance['warmup_rows']} | {meta['flagged_calls']} | [All five solvers and all cases]({link}) |")
            records.append({"role":campaign["role"],"analysis_directory":str(campaign["directory"]),
                            "label":STYLES[campaign["role"]]["label"],"cases":campaign["cases"],
                            "graph_seeds":meta["graph_seeds"],"sampling_seeds":meta["sampling_seeds"],
                            "flagged_calls_retained":meta.get("flagged_calls"),
                            "capture_clock_flags_retained":meta.get("capture_clock_flags"),
                            "revision":meta["revision"],"binary_sha256":meta["binary_sha256"]})
        report += ["","All comparator results, control losses and diagnostic flags remain in each appendix and unfiltered `data/<campaign>/` tables. The copied combined native CSVs contain timed calls and warmups. The copied metadata retains original child-file paths; the full child CSV/log/resource archive remains at those original study paths. These copies are not a relocated standalone raw capture.","",
                   "The compact axes include every A/B graph-median range endpoint. Individual trials can have much wider ranges, including very large wall/CPU discrepancies; those are retained in the full all-comparator appendices and copied tables. No flagged observation is removed or adjusted, and no previous campaign's winner is assumed to remain the winner. Clock flags do not by themselves identify the cause of a disturbed call.","",
                   "**Visual QA pending:** generation success is not evidence that labels, graph-range bars or layout were inspected. Open both PNGs after generation; separately render PDF/SVG if those formats will be distributed.",""]
        (output/"README.md").write_text("\n".join(report))
        for path,expected in inputs.items():
            require(sha(Path(path)) == expected,f"input changed while rendering: {path}")
        provenance = {"schema":"attachment_confirmation_figures_v1","validation":"pass",
                      "campaigns":records,"campaigns_pooled":False,"timings_fitted":False,
                      "graph_range_scope":"observed graph-median min/max for A/B, not confidence intervals",
                      "discovery_ranges":"omitted uniformly in compact figures; all values copied",
                      "visual_qa":"pending","matplotlib_version":matplotlib.__version__,
                      "input_sha256":inputs,"raw_and_derived_copies":copied,
                      "artifact_sha256":{str(path.relative_to(output)):sha(path) for path in sorted(output.rglob("*")) if path.is_file()}}
        (output/"provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
        print(json.dumps({"validation":"pass","separate_campaigns":4,"figures":2,"visual_qa":"pending","output_dir":str(output)}))
    except (ValueError,OSError,KeyError,TypeError,ImportError) as error:
        parser.exit(2,f"confirmation summary: {error}\n")


if __name__ == "__main__":
    main()
