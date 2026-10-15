#!/usr/bin/env python3
"""Plot complete untimed lower-density work; never interpret process durations."""
import argparse
import csv
import importlib.util
import json
from pathlib import Path
import statistics

HERE=Path(__file__).resolve()
_spec=importlib.util.spec_from_file_location("lower_density_work_for_plot",HERE.with_name("collect.py"))
work=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(work)
COLORS={"kkt":"#075f9b","compacting_boruvka":"#b94c1f","multigraph_boruvka":"#21845a"}
LABELS={"kkt":"KKT (eighth)","compacting_boruvka":"Deduplicating Boruvka","multigraph_boruvka":"Retained-edge Boruvka"}
TITLES={"sampled_edges":"Sampled edges","filtered_edges":"Surviving filtered edges",
        "contraction_edge_visits":"Contraction edge visits","sampling_edge_visits":"Sampling visits / MT words",
        "verifier_edge_visits":"Verifier edge visits","path_query_visits":"Path-query visits",
        "initialized_slots":"Explicit initialized slots","edge_materializations":"Edge materializations"}


def csv_rows(path):
    with path.open(newline="") as stream:
        reader=csv.DictReader(stream);rows=list(reader)
        work.require(reader.fieldnames and len(reader.fieldnames)==len(set(reader.fieldnames)) and
                     all(None not in r and None not in r.values() for r in rows),"malformed canonical CSV")
    return rows


def prepare(capture,analysis_dir):
    initial=work.native.sha(capture);info,values=work.load(capture)
    expected=work.tables(values);inputs={str(HERE):work.native.sha(HERE),str(capture):initial}
    provenance=analysis_dir/"provenance.json";provenance_sha=work.native.sha(provenance)
    record=work.analysis.read_json(provenance)
    work.require(record["schema"]=="lower_density_work_analysis_v1" and record["validation"]=="pass" and
                 record["capture"]==str(capture) and record["capture_sha256"]==initial and
                 record["bound_sha256"]==info["bound_sha256"] and record["performance_claim"] is False,
                 "wrong strict work analysis provenance")
    work.analysis.equal(record,"table_counts",{name:len(rows) for name,rows in expected.items()},"analysis counts")
    inputs[str(provenance)]=provenance_sha
    for name,rows in expected.items():
        path=analysis_dir/(name+".csv");inputs[str(path)]=work.native.sha(path)
        actual=csv_rows(path)
        work.require(actual==[{k:"" if v is None else str(v) for k,v in row.items()} for row in rows],
                     "canonical table differs from strict raw reconstruction: "+name)
    plotted=[r for r in expected["normalized_work"] if r["counter"] in work.SELECTED_FIELDS]
    work.require((len(plotted),len(expected["round_chains"]),len(expected["query_work"]))==(1440,120,60),
                 "incomplete plotted work/round/query points")
    work.recheck(info,capture,initial)
    for path,digest in inputs.items():work.analysis.hash_check(Path(path),digest)
    return info,inputs,plotted,expected["round_chains"],expected["query_work"]


def group_series(axis,rows,sizes,key,value,algorithms):
    for algorithm in algorithms:
        medians=[]
        for n in sizes:
            points=[r for r in rows if r["n"]==n and r[key]==algorithm]
            work.require(len(points)==2 and {r["graph_seed"] for r in points}=={23000003,23000029},"missing graph point")
            values=[value(r) for r in points]
            work.require(all(v is not None for v in values),"undefined plotted count")
            medians.append(statistics.median(values));axis.vlines(n,min(values),max(values),color=COLORS[algorithm],alpha=.35)
            for r,v in zip(points,values):axis.scatter([n],[v],s=23,marker="v" if r["graph_seed"]==23000003 else "^",color=COLORS[algorithm],alpha=.8)
        axis.plot(sizes,medians,color=COLORS[algorithm],linewidth=1.2,label=LABELS[algorithm])
    axis.set_xscale("log",base=2);axis.set_xticks(sizes,[f"{n:,}" for n in sizes],rotation=35,ha="right")
    axis.set_ylim(bottom=0);axis.grid(axis="y",alpha=.2)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture",type=Path,required=True);parser.add_argument("--analysis-dir",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True);parser.add_argument("--released",action="store_true")
    args=parser.parse_args();work.require(args.released,"plotting awaits explicit nonperformance release")
    capture=args.capture.resolve(strict=True);analysis_dir=args.analysis_dir.resolve(strict=True);output=args.output_dir.resolve()
    work.require(not output.exists(),"refusing to overwrite figures")
    info,inputs,points,chains,queries=prepare(capture,analysis_dir)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size":10,"axes.titlesize":11,"axes.labelsize":10,"xtick.labelsize":9,"ytick.labelsize":9})
    output.mkdir(parents=True);artifacts=[]
    groups=[(family,d,sizes) for d,sizes in work.timing.SIZE_LADDERS.items() for family in ("leaf_distance4","leaf_shuffled4")]
    def save(fig,name):
        for suffix in ("png","pdf"):
            path=output/(name+"."+suffix);fig.savefig(path,dpi=160);artifacts.append(path)
        plt.close(fig)
    for family,density,sizes in groups:
        fig,axes=plt.subplots(4,2,figsize=(12.2,16.0))
        for axis,field in zip(axes.flat,work.SELECTED_FIELDS):
            selected=[r for r in points if (r["family"],r["density"],r["counter"])==(family,density,field)]
            group_series(axis,selected,sizes,"algorithm",lambda r:r["per_original_edge"],work.ALGORITHMS)
            axis.set_title(TITLES[field]);axis.set_ylabel("Count / original input m");axis.set_xlabel("Vertices n")
        handles,labels=axes.flat[0].get_legend_handles_labels();fig.legend(handles,labels,loc="upper center",ncol=3,bbox_to_anchor=(.5,.955))
        fig.suptitle(f"{family}, m/n={density}: complete cumulative logical work",y=.985)
        fig.text(.5,.018,"Triangles: the two graphs; segments: their full range; line: their median. No runtime or CPU decomposition.\n"
                 "Measured sizes only; connecting lines guide the eye. Counts include all recursive calls. All zero control counts remain.",ha="center",fontsize=9)
        fig.tight_layout(rect=(0,.055,1,.93));save(fig,f"counts_{family}_d{density}")
    fig,axes=plt.subplots(2,2,figsize=(12.2,9.5))
    for axis,(family,density,sizes) in zip(axes.flat,groups):
        selected=[r for r in chains if (r["family"],r["density"])==(family,density)]
        group_series(axis,selected,sizes,"algorithm",lambda r:r["rounds"],work.ALGORITHMS[1:])
        axis.set_title(f"{family}, m/n={density}");axis.set_ylabel("Full continuation rounds");axis.set_xlabel("Vertices n")
    handles,labels=axes.flat[0].get_legend_handles_labels();fig.legend(handles,labels,loc="upper center",ncol=2)
    fig.text(.5,.02,"Both complete deterministic replays, all sizes and both graph observations. These are not KKT recursion depths.",ha="center",fontsize=9)
    fig.tight_layout(rect=(0,.055,1,.94));save(fig,"comparator_rounds")
    fig,axes=plt.subplots(2,2,figsize=(12.2,9.5))
    for axis,(family,density,sizes) in zip(axes.flat,groups):
        for graph,marker in ((23000003,"v"),(23000029,"^")):
            selected=[r for r in queries if (r["family"],r["density"],r["graph_seed"])==(family,density,graph)]
            work.require(len(selected)==len(sizes),"incomplete query series")
            selected.sort(key=lambda r:r["n"])
            axis.plot([r["n"] for r in selected],[float("nan") if r["U_over_Q"] is None else r["U_over_Q"] for r in selected],marker=marker,label=f"Graph {graph}")
            for r in selected:
                if r["U_over_Q"] is None:axis.annotate("Q=0: undefined",(r["n"],0),xytext=(0,7),textcoords="offset points",rotation=90,fontsize=9)
        axis.set_xscale("log",base=2);axis.set_xticks(sizes,[f"{n:,}" for n in sizes],rotation=35,ha="right")
        axis.set_title(f"{family}, m/n={density}");axis.set_ylabel("Per-solve cumulative U / Q");axis.set_xlabel("Vertices n");axis.set_ylim(bottom=0);axis.grid(axis="y",alpha=.2)
    handles,labels=axes.flat[0].get_legend_handles_labels();fig.legend(handles,labels,loc="upper center",ncol=2)
    fig.text(.5,.02,"U sums unique requests within individual verifier-tree calls. Q=0 remains undefined; no global-uniqueness or CPU claim.",ha="center",fontsize=9)
    fig.tight_layout(rect=(0,.055,1,.94));save(fig,"query_compression")
    for name,rows in (("plotted_counts",points),("plotted_rounds",chains),("plotted_queries",queries)):
        path=output/(name+".csv");work.analysis.write_csv(path,rows);artifacts.append(path)
    # Reconstruct every plotted input again after rendering; no dropped series
    # or normalization change can pass as a presentation-only transformation.
    _,again,points2,chains2,queries2=prepare(capture,analysis_dir)
    work.require((inputs,points,chains,queries)==(again,points2,chains2,queries2),"plot inputs changed")
    for path,digest in inputs.items():work.analysis.hash_check(Path(path),digest)
    work.write_json(output/"provenance.json",dict(schema="lower_density_work_figures_v1",validation="pass",
        input_sha256=inputs,output_sha256={str(p):work.native.sha(p) for p in artifacts},figures=6,
        plotted_counter_points=1440,plotted_round_points=120,plotted_query_points=60,
        rows_removed=0,performance_claim=False,visual_review="pending"),exclusive=True)


if __name__=="__main__":main()
