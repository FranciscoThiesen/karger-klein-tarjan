#!/usr/bin/env python3
"""Render compact figures from a completed, strictly validated comparison.

This is presentation code, not an alternative raw-data validator. Run
compare_continuation.py first. It preserves both runs and every declared
candidate/control; sensitivity remains a separate exploratory figure.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import textwrap

GROUPS = ("hierarchical_path", "hierarchical_tree")
SIZES = (524288, 1048576)
CONTROLS = (("random_path",1048576,16), ("random_tree",1048576,16),
            ("low_path",1048576,16), ("legacy_random",65536,32),
            ("legacy_random",65536,128))
NAMES = {"hierarchical_path":"Hierarchical path", "hierarchical_tree":"Hierarchical tree",
         "random_path":"Randomized path weights", "random_tree":"Randomized tree weights",
         "low_path":"Cheap path, shuffled priorities", "legacy_random":"Legacy random"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_table(path):
    with path.open(newline="") as stream:
        reader=csv.DictReader(stream)
        require(reader.fieldnames and len(reader.fieldnames)==len(set(reader.fieldnames)),
                f"{path}: missing or duplicated column names")
        rows=list(reader)
    require(rows and all(None not in r and all(v is not None for v in r.values()) for r in rows),
            f"{path}: empty or malformed table")
    return rows


def key(row):
    values=tuple(int(row[f]) for f in ("n","density","intrusion_per_mille"))
    require(all(str(n)==row[f] for n,f in zip(values,("n","density","intrusion_per_mille"))),
            "noncanonical integer in case dimensions")
    return row["family"],*values


def ratios(row, prefix=""):
    values=tuple(float(row[prefix+f]) for f in ("paired_runtime_ratio","graph_min_ratio","graph_max_ratio"))
    center,low,high=values
    require(all(math.isfinite(x) and x>0 for x in values) and low<=center<=high,
            "invalid ratio or graph range")
    return center,low,high


def load_inputs(folder, baseline, sensitivity):
    metadata_path=folder/"comparison_inputs.json"
    metadata=json.loads(metadata_path.read_text())
    require(metadata.get("validation")=="pass", "comparison did not pass strict validation")
    config_path=Path(metadata["config"]["path"])
    require(digest(config_path)==metadata["config"]["sha256"], "comparison configuration changed after analysis")
    config=json.loads(config_path.read_text())
    require("confirmation" in config and "selection_file" in config,
            "headline figure requires a declared, frozen confirmation")
    selected={(r["family"],r["density"],r["intrusion_per_mille"])
              for r in config["confirmation"]["candidate_groups"]}
    require(selected=={(f,16,0) for f in GROUPS}, "report figure does not match the frozen selected families")
    campaigns={c["name"]:c for c in metadata["campaigns"]}
    primary,repeat=(config["confirmation"][f] for f in ("primary","repeat"))
    require(primary!=repeat and all(campaigns[n]["role"]=="confirmation" for n in (primary,repeat)),
            "missing separate confirmation campaigns")
    for name in (primary,repeat):
        c=campaigns[name]
        require(c["graph_seeds"]==[2027,4099,8191,104729,131071] and
                c["sampling_seeds"]==[11,29,97] and c["repetitions"]==4 and c["warmups"]==1,
                "headline protocol differs from frozen confirmation")
    confirmation_path=folder/"confirmation_cases.csv"
    confirmation=read_table(confirmation_path)
    by_case={key(r):r for r in confirmation}
    candidates=[(f,n,16,0) for f in GROUPS for n in SIZES]
    controls=[(*r,0) for r in CONTROLS]
    require(len(by_case)==len(confirmation)==9 and set(by_case)==set(candidates+controls),
            "headline requires all four candidate cases and all five controls")
    for k,row in by_case.items():
        require(row["selected_candidate"]==str(k in candidates), "candidate label differs from frozen selection")
        for prefix in ("primary_","repeat_"):
            ratios(row,prefix)
            require(int(row[prefix+"paired_observations"])==60 and
                    0<=int(row[prefix+"kkt_slower_observations"])<=60, "wrong matched-pair/loss count")
    summary_path=folder/"case_summary.csv"
    summary=read_table(summary_path)
    all_rows={(r["campaign"],*key(r)):r for r in summary}
    require(len(all_rows)==len(summary), "duplicate campaign/case summary")
    # Crosscheck the specialized confirmation table against the unabridged
    # campaign table, so the figure cannot silently use a different run.
    for k,row in by_case.items():
        for prefix,name in (("primary_",primary),("repeat_",repeat)):
            require(ratios(row,prefix)==ratios(all_rows[(name,*k)]), "confirmation and campaign summaries differ")
    require(baseline in campaigns and sensitivity in campaigns and
            campaigns[baseline]["role"]=="screen" and campaigns[sensitivity]["role"]=="sensitivity",
            "sensitivity requires a separately labeled screen baseline and sensitivity campaign")
    for name in (baseline,sensitivity):
        c=campaigns[name]
        require(c["graph_seeds"]==[17,42] and c["sampling_seeds"]==[0,1] and
                c["repetitions"]==2 and c["warmups"]==1,
                "zero-intrusion baseline and sensitivity do not use the same screen protocol")
    sensitivity_rows={}
    expected={(f,1048576,16,p) for f in GROUPS for p in (1,10,100)}
    actual={key(r) for r in summary if r["campaign"]==sensitivity}
    require(actual==expected, "sensitivity figure must retain all six perturbation cases")
    for family in GROUPS:
        for p in (0,1,10,100):
            row=all_rows[(baseline if p==0 else sensitivity,family,1048576,16,p)]
            ratios(row)
            require(int(row["paired_observations"])==8, "sensitivity row has the wrong pair count")
            sensitivity_rows[family,p]=row
    inputs={str(p.resolve()):digest(p) for p in (metadata_path,config_path,confirmation_path,summary_path)}
    return by_case,candidates,controls,sensitivity_rows,inputs


def save(fig, output, stem, caption):
    import matplotlib.pyplot as plt
    wrapped="\n".join(textwrap.fill(line,width=135) for line in caption.split("\n"))
    fig.text(.02,.015,wrapped,ha="left",va="bottom",fontsize=9)
    for extension in ("png","svg","pdf"):
        fig.savefig(output/(stem+"."+extension),dpi=200,bbox_inches="tight")
    plt.close(fig)


def headline(output, rows, candidates, controls):
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter, MaxNLocator
    fig,axes=plt.subplots(2,1,figsize=(11.8,9),sharex=True,
                          gridspec_kw={"height_ratios":[4,5]})
    fig.subplots_adjust(left=.34,right=.97,top=.9,bottom=.14,hspace=.27)
    colors=("#1261a0","#d77816")
    values=[ratios(r,p) for r in rows.values() for p in ("primary_","repeat_")]
    low=min(.9,min(v[1] for v in values));high=max(1,max(v[2] for v in values))
    span=max(.2,high-low)
    for axis,keys,title in zip(axes,(candidates,controls),
                              ("Frozen candidates · m/n=16", "All five controls")):
        for i,k in enumerate(keys):
            for run,(prefix,color,offset) in enumerate(zip(("primary_","repeat_"),colors,(-.12,.12)),1):
                center,minimum,maximum=ratios(rows[k],prefix)
                axis.errorbar(center,i+offset,xerr=[[center-minimum],[maximum-center]],fmt="o",
                              color=color,capsize=3,ms=5,lw=1.6,label=f"Run {run}" if i==0 else None)
                axis.text(maximum+.025*span,i+offset,f"{center:.3f}",color=color,fontsize=9,va="center")
        labels=[f'{NAMES[f]}\nn={n:,}'+(f" · m/n={d}" if keys is controls else "") for f,n,d,p in keys]
        axis.set_yticks(range(len(keys)),labels)
        axis.set_ylim(len(keys)-.55,-.55)
        axis.set_xlim(low-.06*span,high+.2*span)
        axis.axvline(1,color="#555555",ls="--",lw=1)
        axis.axvline(.9,color="#999999",ls=":",lw=1)
        axis.grid(axis="x",alpha=.18)
        axis.set_title(title,loc="left",fontweight="bold",fontsize=11)
        axis.tick_params(axis="y",length=0,labelsize=10)
        axis.xaxis.set_major_locator(MaxNLocator(nbins=7))
        axis.xaxis.set_major_formatter(FuncFormatter(lambda x,_:f"{x:g}×"))
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,frameon=False,ncol=2,loc="upper center",bbox_to_anchor=(.66,.945))
    axes[-1].set_xlabel("KKT / compacting Borůvka elapsed time · below 1× favors KKT")
    fig.suptitle("Held-out continuation comparison",fontsize=16,fontweight="bold",y=.975)
    save(fig,output,"heldout_headline",
         "Points are paired time ratios, summarized by medians over repetitions, sampling seeds, then graphs. Whiskers span the five graph medians; they are not confidence intervals.\n"
         "Dashed: parity. Dotted: predeclared .90 case threshold; every graph ratio must also be <1 at both candidate sizes in both runs.\n"
         "All calls retained, including 922.6 s KKT and 312.6 s compactor control observations. Desktop power transitions limit inference.")


def sensitivity_figure(output, rows):
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter, MaxNLocator
    fig,axes=plt.subplots(1,2,figsize=(11.8,5.3),sharey=True)
    fig.subplots_adjust(left=.08,right=.98,top=.79,bottom=.32,wspace=.14)
    all_values=[ratios(r) for r in rows.values()]
    low=min(1,min(v[1] for v in all_values));high=max(1,max(v[2] for v in all_values));span=max(.15,high-low)
    for axis,family in zip(axes,GROUPS):
        values=[ratios(rows[family,p]) for p in (0,1,10,100)]
        axis.plot(range(4),[v[0] for v in values],color="#aaaaaa",lw=1,zorder=1)
        for i,(center,minimum,maximum) in enumerate(values):
            color="#1261a0" if i==0 else "#d77816"
            axis.errorbar(i,center,yerr=[[center-minimum],[maximum-center]],fmt="o",color=color,
                          markerfacecolor="white" if i==0 else color,ms=6,capsize=4,lw=1.7,zorder=2,
                          label="Zero: million screen" if i==0 else "Sensitivity run" if i==1 else None)
            axis.annotate(f"{center:.3f}",(i,maximum),xytext=(0,7),textcoords="offset points",
                          ha="center",fontsize=9,color=color)
        axis.axhline(1,color="#555555",ls="--",lw=1)
        axis.set_ylim(low-.08*span,high+.2*span)
        axis.set_xticks(range(4),["0","1","10","100"])
        axis.set_xlim(-.25,3.25)
        axis.set_xlabel("Promoted shortcuts per 1,000 vertices\n(discrete settings)")
        axis.set_title(NAMES[family],fontsize=12)
        axis.grid(alpha=.18)
        axis.yaxis.set_major_locator(MaxNLocator(nbins=5))
        axis.yaxis.set_major_formatter(FuncFormatter(lambda x,_:f"{x:g}×"))
    axes[0].set_ylabel("KKT / compacting Borůvka time")
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc="upper center",bbox_to_anchor=(.5,.91),ncol=2,frameon=False)
    fig.suptitle("Exploratory sensitivity · n=1,048,576, m/n=16",fontsize=15,fontweight="bold",y=.995)
    save(fig,output,"sensitivity_exploration",
         "Each point uses matched KKT/compaction calls with graph seeds 17,42, sampling seeds 0,1 and two repetitions; whiskers span two graph medians, not confidence intervals. Zero uses the same seeds and topology from the separate million screen.\n"
         "That baseline capture includes a logged 1,030 s clamshell sleep, without a long recorded solver call; its suspension phase is unknown.\n"
         "Promotions equal floor(n × setting / 1000), not a fraction of all edges. The campaign is exploratory; it cannot rescue a failed held-out confirmation. Separate runs may have different desktop conditions.")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison-dir",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--baseline-campaign",default="million")
    parser.add_argument("--sensitivity-campaign",default="sensitivity")
    args=parser.parse_args()
    rows,candidates,controls,sensitivity,inputs=load_inputs(args.comparison_dir,args.baseline_campaign,args.sensitivity_campaign)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size":10,"svg.fonttype":"none","pdf.fonttype":42})
    args.output_dir.mkdir(parents=True,exist_ok=True)
    headline(args.output_dir,rows,candidates,controls)
    sensitivity_figure(args.output_dir,sensitivity)
    metadata={"validation":"pass","source_sha256":digest(Path(__file__)),"inputs_sha256":inputs,
              "headline_cases":len(rows),"sensitivity_points":len(sensitivity),
              "validation_scope":"presentation checks on previously strict-validated comparison tables; no new raw-data or MST validation"}
    (args.output_dir/"report_figures_inputs.json").write_text(json.dumps(metadata,indent=2)+"\n")
    print(f"Wrote held-out and exploratory-sensitivity figures to {args.output_dir}")


if __name__=="__main__":
    try:main()
    except (ValueError,OSError,KeyError,TypeError) as error:
        print("continuation report figures: "+str(error),file=sys.stderr)
        sys.exit(1)
