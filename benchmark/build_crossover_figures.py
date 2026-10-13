#!/usr/bin/env python3
"""Build standalone crossover figures from a strictly validated comparison.

Input is a compare_crossover.py output directory. Before plotting, raw captures
are revalidated using its recorded configuration, input hashes are checked, and
all plotted CSV tables are compared with freshly derived values. Campaigns are
never pooled. Matplotlib imports occur only after validation and are skipped by
--validate-only. No asymptotic model is fitted or extrapolated.
"""

import argparse
import collections
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import sys

import compare_crossover as comparison

MAIN_FAMILIES = ("line_metric", "line_wide_metric", "line_random",
                 "grid2d_metric", "grid2d_random", "gnm_random")
NAMES = {
    "line_metric": "Line · distance ranks · gaps 1…1,024",
    "line_wide_metric": "Line · distance ranks · gaps 1…2³²",
    "line_random": "Line · random ranks · gaps 1…1,024",
    "grid2d_metric": "2D grid + shortcuts · distance ranks",
    "grid2d_random": "2D grid + shortcuts · random ranks",
    "gnm_random": "Connected G(n,m) · random ranks",
    "hierarchical_path": "Hierarchy path anchor",
    "random_tree": "Random-weight tree + shortcuts anchor",
}
COLORS = {"line_metric":"#7946A5", "line_wide_metric":"#C26B20", "grid2d_metric":"#7946A5",
          "line_random":"#277BA8", "grid2d_random":"#277BA8", "gnm_random":"#138478"}
ALGORITHM_COLORS = {"kkt":"#7946A5", "compacting_boruvka":"#277BA8"}
ALGORITHM_NAMES = {"kkt":"KKT", "compacting_boruvka":"Compacting Borůvka"}
STYLES = (("-","o"),("--","^"),("-.","s"),(":","D"),("-","P"),("--","X"))
METRICS = {"wall":"Steady elapsed time", "cpu":"Process CPU diagnostic"}
AGGREGATION = (
    "Ratios pair algorithm times within each trial, then take medians over "
    "repetitions, sampling seeds, and graph seeds. Algorithm costs use the same "
    "hierarchy separately, divided by the original input edge count m. A ratio "
    "of the displayed algorithm medians need not equal the paired-ratio median. "
    "Thick capped ranges span graph-level medians; thin ranges span all individual "
    "paired trials. Neither range is a confidence interval. Repeated timing and "
    "sampling seeds are not additional graph draws. Campaigns remain separate."
)
PRECISION_NOTE = (
    "The wide-gap line is a precision ablation: its gaps are uniform integers "
    "from 1 to 2³², versus 1 to 1,024 for the original line. At matched size, "
    "density and graph seed, topology, edge IDs, labels and input order agree, "
    "but coordinates and distance ranks differ. The random-rank line uses the "
    "original narrow-gap geometry. Both gap alphabets are fixed and finite; "
    "these finite-size curves do not establish an asymptotic crossover."
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_file(record, context):
    require(type(record) is dict and set(record) == {"path","sha256"},
            f"{context}: invalid file provenance")
    require(type(record["path"]) is str and type(record["sha256"]) is str,
            f"{context}: invalid path/hash types")
    path = Path(record["path"])
    require(path.is_file() and sha256(path) == record["sha256"],
            f"{context}: missing or hash-mismatched input {path}")
    return path.resolve()


def check_table(path, expected):
    require(expected, f"{path}: expected a nonempty table")
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == list(expected[0]), f"{path}: unexpected header")
        rows = list(reader)
    require(len(rows) == len(expected), f"{path}: row count differs from validated raw data")
    for line, (actual, wanted) in enumerate(zip(rows, expected), 2):
        require(None not in actual and all(v is not None for v in actual.values()),
                f"{path}:{line}: malformed CSV")
        for field, value in wanted.items():
            text = actual[field]
            if type(value) is float:
                try:
                    parsed = float(text)
                except ValueError as error:
                    raise ValueError(f"{path}:{line}: nonnumeric {field}") from error
                require(math.isfinite(parsed) and parsed == value,
                        f"{path}:{line}: {field} differs from raw-data aggregation")
            else:
                require(text == str(value), f"{path}:{line}: {field} differs from raw data")
    return sha256(path)


def load(comparison_dir):
    metadata_path = comparison_dir / "comparison_inputs.json"
    metadata = comparison.read_json(metadata_path)
    require(type(metadata) is dict and metadata.get("schema") == "crossover_comparison_result_v1"
            and metadata.get("validation") == "pass", "not a validated crossover comparison")
    require(type(metadata.get("rows_removed")) is int and metadata["rows_removed"] == 0 and
            type(metadata.get("rows_adjusted")) is int and metadata["rows_adjusted"] == 0,
            "comparison reports removed or adjusted observations")
    config_path = check_file(metadata.get("config"), "comparison configuration")
    if metadata.get("selection") is not None:
        check_file(metadata["selection"], "frozen selection")
    require(type(metadata.get("campaigns")) is list and metadata["campaigns"], "missing campaign provenance")
    for campaign in metadata["campaigns"]:
        require(type(campaign) is dict and type(campaign.get("inputs")) is dict,
                "invalid campaign input provenance")
        for name, record in campaign["inputs"].items():
            check_file(record, f"{campaign.get('name')}/{name}")
    campaigns, confirmation, selection_path = comparison.collect(
        comparison.read_json(config_path), config_path.parent)
    require((str(selection_path) if selection_path else None) ==
            (str(Path(metadata["selection"]["path"]).resolve()) if metadata.get("selection") else None),
            "recorded selection differs from comparison configuration")
    require(len(campaigns) == len(metadata["campaigns"]), "campaign provenance length mismatch")
    for campaign, recorded in zip(campaigns, metadata["campaigns"]):
        expected = {"name":campaign["name"], "role":campaign["role"], "cases":list(campaign["cases"]),
            "graph_seeds":list(campaign["graph_seeds"]), "sampling_seeds":list(campaign["sampling_seeds"]),
            "repetitions":campaign["repetitions"], "warmups":campaign["warmups"],
            "timed_calls":len(campaign["timing"]), "checked_warmups":campaign["checked_warmups"],
            "flagged_calls":campaign["clock_audit"]["flagged_calls"]}
        require(all(recorded.get(field) == value and type(recorded.get(field)) is type(value)
                    for field,value in expected.items()), f"{campaign['name']}: protocol metadata differs")
        require(set(recorded["inputs"]) == set(campaign["paths"]), "input path registry differs")
        require(all(Path(recorded["inputs"][key]["path"]).resolve() == path.resolve()
                    for key,path in campaign["paths"].items()), "recorded raw input paths differ")
    derived = comparison.tables(campaigns, confirmation)
    hashes = {}
    for metric in METRICS:
        for table in ("case_summary", "graph_summary", "paired_pairs"):
            name = metric + "_" + table
            hashes[name+".csv"] = check_table(comparison_dir/(name+".csv"), derived[name])
    hashes["call_clocks.csv"] = check_table(comparison_dir/"call_clocks.csv", derived["call_clocks"])
    return campaigns, derived, {"comparison_metadata":str(metadata_path.resolve()),
        "comparison_metadata_sha256":sha256(metadata_path), "config":metadata["config"],
        "selection":metadata.get("selection"), "verified_table_sha256":hashes,
        "recorded_comparison_source_sha256":metadata.get("comparison_sha256"),
        "current_validator_source_sha256":{
            Path(module.__file__).name:sha256(Path(module.__file__))
            for module in (comparison, comparison.base, comparison.prior, comparison.clocks)}}


def is_main(row):
    return row["family"] in MAIN_FAMILIES and row["density"] == 16 and row["intrusion_per_mille"] == 0


def points(campaigns, derived):
    protocol = {c["name"]:c for c in campaigns}
    result = []
    for metric in METRICS:
        raw = collections.defaultdict(list)
        graphs = collections.defaultdict(list)
        for row in derived[metric+"_paired_pairs"]:
            raw[row["campaign"],row["case_id"]].append(row)
        for row in derived[metric+"_graph_summary"]:
            graphs[row["campaign"],row["case_id"]].append(row)
        for row in derived[metric+"_case_summary"]:
            key = row["campaign"], row["case_id"]
            pairs, graph_rows, campaign = raw[key], graphs[key], protocol[row["campaign"]]
            record = {"metric":metric, **row, "figure_group":"d16_main" if is_main(row) else "controls_anchors",
                "graph_count":len(campaign["graph_seeds"]), "sampling_seed_count":len(campaign["sampling_seeds"]),
                "repetitions":campaign["repetitions"], "warmups":campaign["warmups"],
                "individual_min_ratio":min(r["paired_runtime_ratio"] for r in pairs),
                "individual_max_ratio":max(r["paired_runtime_ratio"] for r in pairs)}
            for algorithm in ALGORITHM_NAMES:
                field = algorithm+"_median_ns"
                record[algorithm+"_ns_per_edge"] = row[field]/row["m"]
                record[algorithm+"_graph_min_ns_per_edge"] = min(r[field] for r in graph_rows)/row["m"]
                record[algorithm+"_graph_max_ns_per_edge"] = max(r[field] for r in graph_rows)/row["m"]
                elapsed = algorithm+"_elapsed_ns"
                record[algorithm+"_individual_min_ns_per_edge"] = min(r[elapsed] for r in pairs)/row["m"]
                record[algorithm+"_individual_max_ns_per_edge"] = max(r[elapsed] for r in pairs)/row["m"]
            require(record["individual_min_ratio"] <= row["graph_min_ratio"] <= row["paired_runtime_ratio"] <=
                    row["graph_max_ratio"] <= record["individual_max_ratio"], "ratio range inconsistency")
            result.append(record)
    require(len(result) == 2*sum(len(c["cases"]) for c in campaigns), "figure coverage dropped cases")
    return result


def write_csv(path, rows):
    with path.open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator="\n")
        writer.writeheader();writer.writerows(rows)


def render(data, campaigns, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FuncFormatter, FixedLocator, NullFormatter
    plt.rcParams.update({"font.size":10,"svg.fonttype":"none","pdf.fonttype":42})
    campaign_order = [c["name"] for c in campaigns]
    styles = {name:STYLES[i%len(STYLES)] for i,name in enumerate(campaign_order)}
    campaign_colors = {name:plt.get_cmap("tab10")(i%10) for i,name in enumerate(campaign_order)}
    files=[]

    def label(campaign):
        count=len(campaign["graph_seeds"])
        detail="single-graph screen" if campaign["role"]=="screen" and count==1 else f"{count} graphs; {campaign['role']}"
        return campaign["name"]+" ("+detail+")"

    def save(fig,stem):
        for extension in ("png","svg","pdf"):
            path=output/(stem+"."+extension)
            fig.savefig(path,dpi=190,bbox_inches="tight",facecolor="white")
            if extension=="svg":
                path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines())+"\n")
            files.append(path.name)
        plt.close(fig)

    def format_n(value,_):
        return f"{value/1048576:g}M" if value>=1048576 else f"{value/1024:g}K"

    def style(axis, size_axis=False):
        axis.spines[["top","right"]].set_visible(False)
        axis.grid(which="major",alpha=.2)
        axis.set_axisbelow(True)
        if size_axis:
            axis.set_xscale("log",base=2)
            axis.xaxis.set_major_formatter(FuncFormatter(format_n))
            axis.xaxis.set_minor_formatter(NullFormatter())
            axis.set_xlabel("Vertices n (K=2¹⁰, M=2²⁰)")

    def thresholds(axis, horizontal=True):
        draw=axis.axhline if horizontal else axis.axvline
        draw(1,color="#555F68",linewidth=1.1,linestyle="--",zorder=1)
        draw(.9,color="#25806D",linewidth=1.1,linestyle=":",zorder=1)

    def ratio_ticks(axis, low, high, horizontal=False):
        target=axis.xaxis if horizontal else axis.yaxis
        target.set_major_formatter(FuncFormatter(lambda value,_: f"{value:g}"))
        target.set_minor_formatter(NullFormatter())
        if high/low <= 3:
            candidates=(.25,.3,.4,.5,.6,.7,.75,.8,.85,.9,.95,1,1.05,1.1,1.2,1.3,1.4,1.5,1.75,2,2.5,3)
            ticks=[value for value in candidates if low <= value <= high]
            if len(ticks)>10:
                ticks=sorted(set(ticks[::2]+[value for value in (.9,1) if low<=value<=high]))
            target.set_major_locator(FixedLocator(ticks))

    def footer(fig, extra=""):
        fig.text(.015,.014,"Thin ranges: every paired trial. Thick caps: graph medians. Neither is a confidence interval. "+extra,fontsize=8)

    def legend_handles(algorithms=False):
        if algorithms:
            handles=[Line2D([0],[0],color=ALGORITHM_COLORS[a],lw=2,label=ALGORITHM_NAMES[a]) for a in ALGORITHM_NAMES]
        else:
            handles=[Line2D([0],[0],color="#7946A5",lw=2,label="Distance ranks"),
                     Line2D([0],[0],color="#277BA8",lw=2,label="Random ranks"),
                     Line2D([0],[0],color="#138478",lw=2,label="Connected G(n,m)")]
            if any(r["family"]=="line_wide_metric" for r in data):
                handles.insert(1,Line2D([0],[0],color=COLORS["line_wide_metric"],lw=2,
                                       label="Wide-gap line distance ranks (precision ablation)"))
        handles.extend(Line2D([0],[0],color="#35414D",linestyle=styles[c["name"]][0],
                             marker=styles[c["name"]][1],label=label(c)) for c in campaigns)
        return handles

    def vertical_ranges(axis, x, center, low, high, graph_low, graph_high, color):
        axis.vlines(x,low,high,color=color,alpha=.28,linewidth=1,zorder=2)
        axis.errorbar(x,center,yerr=[[center-graph_low],[graph_high-center]],fmt="none",
                      ecolor=color,elinewidth=2,capsize=3,capthick=1.5,zorder=3)

    for metric,title in METRICS.items():
        measured=[r for r in data if r["metric"]==metric]
        main=[r for r in measured if is_main(r)]
        if main:
            fig,axes=plt.subplots(1,3,figsize=(14.6,5.0),sharey=True)
            panels=(("Line + uniform shortcuts",("line_metric","line_wide_metric","line_random")),
                    ("Open 2D grid + uniform shortcuts",("grid2d_metric","grid2d_random")),
                    ("Connected G(n,m)",("gnm_random",)))
            for axis,(panel_title,families) in zip(axes,panels):
                selected=[r for r in main if r["family"] in families]
                for family in families:
                    for campaign in campaign_order:
                        curve=sorted((r for r in selected if r["campaign"]==campaign and r["family"]==family),key=lambda r:r["n"])
                        if not curve:continue
                        color=COLORS[family];linestyle,marker=styles[campaign]
                        axis.plot([r["n"] for r in curve],[r["paired_runtime_ratio"] for r in curve],
                                  color=color,linestyle=linestyle,marker=marker,markersize=6,linewidth=1.65,zorder=4)
                        for r in curve:
                            vertical_ranges(axis,r["n"],r["paired_runtime_ratio"],r["individual_min_ratio"],
                                            r["individual_max_ratio"],r["graph_min_ratio"],r["graph_max_ratio"],color)
                axis.set_title(panel_title,fontsize=11)
                style(axis,True);thresholds(axis)
                axis.set_yscale("log")
                axis.xaxis.set_major_locator(FixedLocator(sorted({r["n"] for r in selected})))
                if not selected:axis.text(.5,.5,"No declared cases",transform=axis.transAxes,ha="center")
                if "line_wide_metric" in families and any(r["family"]=="line_wide_metric" for r in selected):
                    axis.text(.02,.98,"Line gaps: 1…1,024; orange: 1…2³²\nMatched seed: same topology, new coordinates",
                              transform=axis.transAxes,va="top",fontsize=8,
                              bbox={"facecolor":"white","edgecolor":"none","alpha":.85})
            lower=min(.9,min(r["individual_min_ratio"] for r in main))
            upper=max(1,max(r["individual_max_ratio"] for r in main))
            axes[0].set_ylim(lower*.92,upper*1.08)
            ratio_ticks(axes[0],lower*.92,upper*1.08)
            axes[0].set_ylabel("Paired KKT / compacting Borůvka (log; lower is better)")
            fig.suptitle(f"{title}: fixed density m=16n",fontsize=15,y=.99)
            fig.legend(handles=legend_handles(),loc="lower center",bbox_to_anchor=(.5,.075),ncol=3,fontsize=8,frameon=False)
            footer(fig,"Lines at 1.00 (tie) and 0.90 (reference threshold); no fitted/extrapolated curve.")
            fig.tight_layout(rect=(0,.24,1,.94))
            save(fig,f"crossover_ratios_{metric}")

            fig,axes=plt.subplots(2,3,figsize=(14.6,8.5),squeeze=False)
            present_families=[family for family in MAIN_FAMILIES if any(r["family"]==family for r in main)]
            for axis,family in zip(axes.flat,present_families):
                selected=[r for r in main if r["family"]==family]
                for campaign in campaign_order:
                    curve=sorted((r for r in selected if r["campaign"]==campaign),key=lambda r:r["n"])
                    if not curve:continue
                    linestyle,marker=styles[campaign]
                    for algorithm,color in ALGORITHM_COLORS.items():
                        axis.plot([r["n"] for r in curve],[r[algorithm+"_ns_per_edge"] for r in curve],
                                  color=color,linestyle=linestyle,marker=marker,markersize=5,linewidth=1.6,zorder=4)
                        for r in curve:
                            vertical_ranges(axis,r["n"],r[algorithm+"_ns_per_edge"],
                                r[algorithm+"_individual_min_ns_per_edge"],r[algorithm+"_individual_max_ns_per_edge"],
                                r[algorithm+"_graph_min_ns_per_edge"],r[algorithm+"_graph_max_ns_per_edge"],color)
                style(axis,True);axis.set_yscale("log")
                axis.xaxis.set_major_locator(FixedLocator(sorted({r["n"] for r in selected})))
                axis.set_title(NAMES[family],fontsize=10)
                axis.set_ylabel("Nanoseconds / original edge m (log)")
                if not selected:axis.text(.5,.5,"No declared cases",transform=axis.transAxes,ha="center")
            for axis in list(axes.flat)[len(present_families):]:
                axis.set_visible(False)
            fig.suptitle(f"{title}: separate solver cost per input edge · m=16n",fontsize=14,y=.99)
            fig.legend(handles=legend_handles(True),loc="lower center",bbox_to_anchor=(.5,.065),ncol=3,fontsize=8,frameon=False)
            footer(fig,"Each algorithm is aggregated separately; dividing the two displayed medians is not the paired-ratio statistic.")
            fig.tight_layout(rect=(0,.20,1,.95))
            save(fig,f"crossover_cost_per_edge_{metric}")

        def case_plot(rows,stem,title_prefix):
            unique={r["case_id"]:r for r in rows}
            keys=sorted(unique,key=lambda key:(unique[key]["density"],unique[key]["family"],unique[key]["n"],unique[key]["intrusion_per_mille"]))
            for page,start in enumerate(range(0,len(keys),24),1):
                included=keys[start:start+24]
                fig,axis=plt.subplots(figsize=(11.8,max(4.7,.39*len(included)+2.0)))
                for index,key in enumerate(included):
                    for ci,campaign in enumerate(campaign_order):
                        matches=[r for r in rows if r["case_id"]==key and r["campaign"]==campaign]
                        if not matches:continue
                        require(len(matches)==1,"duplicate figure case/campaign")
                        r=matches[0];color=campaign_colors[campaign]
                        offset=0 if len(campaign_order)==1 else .55*(ci/(len(campaign_order)-1)-.5)
                        y=index+offset
                        axis.hlines(y,r["individual_min_ratio"],r["individual_max_ratio"],color=color,alpha=.3,lw=1)
                        axis.errorbar(r["paired_runtime_ratio"],y,
                            xerr=[[r["paired_runtime_ratio"]-r["graph_min_ratio"]],[r["graph_max_ratio"]-r["paired_runtime_ratio"]]],
                            fmt=styles[campaign][1],color=color,capsize=3,elinewidth=2,markersize=5)
                labels=[]
                for key in included:
                    r=unique[key]
                    name=NAMES.get(r["family"],r["family"].replace("_"," "))
                    labels.append(f"{name}\nn={r['n']:,}; m/n={r['density']}; p={r['intrusion_per_mille']}‰")
                axis.set_yticks(range(len(included)),labels,fontsize=8)
                axis.invert_yaxis();axis.set_xscale("log");thresholds(axis,False);style(axis)
                selected=[r for r in rows if r["case_id"] in included]
                lower=min(.9,min(r["individual_min_ratio"] for r in selected))*.92
                upper=max(1,max(r["individual_max_ratio"] for r in selected))*1.08
                axis.set_xlim(lower,upper)
                ratio_ticks(axis,lower,upper,True)
                axis.set_xlabel("Paired KKT / compacting Borůvka (log; lower is better)")
                axis.set_title(f"{title}: {title_prefix}"+(f" · page{page}" if len(keys)>24 else ""))
                handles=[Line2D([0],[0],color=campaign_colors[c["name"]],marker=styles[c["name"]][1],
                                linestyle="none",label=label(c)) for c in campaigns]
                fig.legend(handles=handles,loc="lower center",bbox_to_anchor=(.5,.065),ncol=2,fontsize=8,frameon=False)
                footer(fig,"All declared observations retained. 0.90 is a reference, not an automatic confirmation verdict.")
                fig.tight_layout(rect=(0,.17,1,.96))
                save(fig,stem+(f"_{page}" if len(keys)>24 else ""))
        controls=[r for r in measured if not is_main(r)]
        if controls:case_plot(controls,f"crossover_controls_{metric}","density controls and anchors")
        case_plot(measured,f"crossover_all_cases_{metric}","every declared case")
    return files


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison-dir",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path)
    parser.add_argument("--validate-only",action="store_true")
    args=parser.parse_args()
    require(args.validate_only or args.output_dir is not None,"--output-dir is required unless --validate-only")
    campaigns,derived,inputs=load(args.comparison_dir.resolve())
    data=points(campaigns,derived)
    metadata={"schema":"crossover_figures_v1","validation":"pass","aggregation":AGGREGATION,
        "inputs":inputs,"figure_script_sha256":sha256(Path(__file__)),"rows_removed":0,"rows_adjusted":0,
        "plotted_case_campaigns_per_metric":len(data)//2,"point_rows":len(data),
        "main_definition":"Five initial families and the separately labeled wide-gap line precision ablation at m/n16,p0; every other case appears in controls/anchors. All cases also appear in the appendix.",
        "precision_ablation":PRECISION_NOTE,
        "campaigns":[{"name":c["name"],"role":c["role"],"case_count":len(c["cases"]),
                      "graph_seeds":c["graph_seeds"],"sampling_seeds":c["sampling_seeds"],
                      "repetitions":c["repetitions"],"warmups":c["warmups"],
                      "flagged_calls":c["clock_audit"]["flagged_calls"]} for c in campaigns]}
    if args.validate_only:
        print(json.dumps(metadata,indent=2,allow_nan=False));return
    args.output_dir.mkdir(parents=True,exist_ok=True)
    write_csv(args.output_dir/"figure_points.csv",data)
    metadata["figures"]=render(data,campaigns,args.output_dir)
    (args.output_dir/"provenance.json").write_text(json.dumps(metadata,indent=2,allow_nan=False)+"\n")
    lines=["# Crossover figure guide","",AGGREGATION,"",
        "Steady elapsed time is primary. Process CPU is a separately plotted diagnostic envelope; its clock reads surround the solver interval. No flagged calls are removed. Connecting segments join only measured sizes within the same campaign and family; no extrapolation or asymptotic fit is drawn.","",
        "A single-graph screen has no measured graph-to-graph spread. Its thin trial range reflects repeated timings of that one graph. The 0.90 line is a visual reference: the frozen criterion additionally requires both selected sizes, every graph median below1, both wall/CPU metrics and both confirmation campaigns.","",
        PRECISION_NOTE,"",
        "| Campaign | Role | Cases | Graphs | Sampling seeds | Repeats | Warmups | Flagged calls |",
        "|---|---|---:|---:|---:|---:|---:|---:|"]
    for c in metadata["campaigns"]:
        lines.append(f"| {c['name']} | {c['role']} | {c['case_count']} | {len(c['graph_seeds'])} | {len(c['sampling_seeds'])} | {c['repetitions']} | {c['warmups']} | {c['flagged_calls']} |")
    comparison_link=os.path.relpath(args.comparison_dir.resolve()/"report.md",args.output_dir.resolve())
    lines.extend(["",f"[Strict comparison report]({comparison_link}), [all plotted numeric values](figure_points.csv), [input and script provenance](provenance.json).",""])
    for name in metadata["figures"]:
        if name.endswith(".png"):lines.extend([f"![{Path(name).stem.replace('_',' ')}]({name})",""])
    (args.output_dir/"README.md").write_text("\n".join(lines).rstrip()+"\n")
    print(f"Validated {len(campaigns)} campaigns and {len(data)//2} case/campaign observations; wrote {args.output_dir}")


if __name__=="__main__":
    try:main()
    except (ValueError,OSError,KeyError) as error:
        print("crossover figures: "+str(error),file=sys.stderr)
        sys.exit(1)
