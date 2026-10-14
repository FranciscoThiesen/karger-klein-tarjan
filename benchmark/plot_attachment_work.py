#!/usr/bin/env python3
"""Scientific figures for the selected 16-record attachment work capture.

Consumes a hash-verified analyze_attachment_work output directory. These are
untimed logical-work figures, never fitted or extrapolated running times.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_table(path, integer_fields, float_fields):
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    require(rows, f"empty table: {path}")
    for row in rows:
        for field in integer_fields:
            row[field] = int(row[field])
        for field in float_fields:
            row[field] = None if row[field] == "" else float(row[field])
            require(row[field] is None or math.isfinite(row[field]), f"nonfinite {field}")
    return rows


def load(folder):
    provenance_path = folder / "provenance.json"
    provenance = json.loads(provenance_path.read_text())
    require(provenance["schema"] == "attachment_work_analysis_v1"
            and provenance["validation"] == "pass" and provenance["work_records"] == 16
            and provenance["rows_removed"] == provenance["rows_adjusted"] == 0,
            "expected the complete, successful selected 16-record work analysis")
    inputs = {str(provenance_path.resolve()): sha(provenance_path)}
    for name, expected in provenance["derived_sha256"].items():
        path = folder / name
        require(sha(path) == expected, f"modified derived input: {path}")
        inputs[str(path.resolve())] = expected
    summary = read_table(folder/"summary.csv", ("n","m","density","block_size","graph_seed","kkt_seed","compactor_rounds"),
                         ("compactor_contraction_edges_per_m","kkt_contraction_edges_per_m","expected_compactor_edges_per_m"))
    rounds = read_table(folder/"rounds.csv", ("n","m","density","graph_seed","kkt_seed","round","input_vertices","input_edges"),
                        ("expected_input_edges","observed_minus_expected_input_edges"))
    require(len(summary) == 16 and len(rounds) == provenance["trace_rounds"], "work table size changed")
    seeds = {(row["graph_seed"],row["kkt_seed"]) for row in summary}
    require(len(seeds) == 1, "selected plots require one graph/KKT seed pair; do not silently pool graphs")
    index = {(row["family"],row["n"],row["density"]):row for row in summary}
    require(len(index) == 16, "duplicate selected case")
    for row in summary:
        require(row["compactor_contraction_edges_per_m"] >= 1
                and row["kkt_contraction_edges_per_m"] >= 1, "invalid normalized edge volume")
    grouped = {key: sorted((row for row in rounds if (row["family"],row["n"],row["density"]) == key),
                           key=lambda row:row["round"]) for key in index}
    for key, trace in grouped.items():
        require([row["round"] for row in trace] == list(range(1,index[key]["compactor_rounds"]+1)),
                "incomplete or duplicate per-round input table")
    return summary, index, grouped, next(iter(seeds)), inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        require(not args.output_dir.exists(), "refusing to replace an existing figure directory")
        summary, index, traces, seeds, inputs = load(args.analysis_dir)
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.ticker import FixedLocator, FuncFormatter, MaxNLocator
        plt.rcParams.update({"font.size":10,"axes.titlesize":12,"axes.labelsize":10,
                             "figure.dpi":140,"savefig.dpi":180,"axes.spines.top":False,
                             "axes.spines.right":False,"axes.grid":True,"grid.alpha":.2,
                             "grid.linewidth":.6,"svg.fonttype":"none"})
        args.output_dir.mkdir(parents=True, exist_ok=False)
        files = []
        footer = f"Untimed logical counters · graph seed {seeds[0]}, KKT seed {seeds[1]} · no time fit or extrapolation"
        def save(fig, name, caption):
            fig.text(.02,.015,footer,fontsize=9,color="#555555")
            for suffix in ("png","svg"):
                path = args.output_dir / f"{name}.{suffix}"
                fig.savefig(path, facecolor="white")
                files.append(path)
            plt.close(fig)
            return {"file":name+".png","caption":caption}
        captions = []
        modes = [("hierarchy","#0072B2","o"),("distance","#D55E00","s")]
        sizes = (16384,65536,262144,1048576)
        fig, axes = plt.subplots(1,2,figsize=(12.5,4.9))
        fig.subplots_adjust(left=.075,right=.98,top=.81,bottom=.17,wspace=.24)
        fig.suptitle("More repeated compactor edge input as the ordered core grows",x=.075,ha="left",y=.97,fontsize=16)
        fig.text(.075,.89,"Leaf attachments · b = 4, d = 16 · two weight modes on the same topology",fontsize=11,color="#555555")
        for mode,color,marker in modes:
            rows = [index[("leaf_"+mode+"4",n,16)] for n in sizes]
            axes[0].plot(sizes,[row["kkt_contraction_edges_per_m"] for row in rows],color=color,
                         marker=marker,markerfacecolor="white",label="KKT: "+mode,linewidth=1.7)
            axes[1].plot(sizes,[row["kkt_contraction_edges_per_m"]/row["compactor_contraction_edges_per_m"] for row in rows],
                         color=color,marker=marker,markerfacecolor="white",label=mode,linewidth=1.7)
        comp = [index[("leaf_hierarchy4",n,16)] for n in sizes]
        require(all(index[("leaf_distance4",n,16)]["compactor_contraction_edges_per_m"] == row["compactor_contraction_edges_per_m"]
                    for n,row in zip(sizes,comp)),"ordered compactor equality changed; use separate lines")
        axes[0].plot(sizes,[row["compactor_contraction_edges_per_m"] for row in comp],color="#333333",marker="D",label="Compactor: both modes",linewidth=1.8)
        axes[0].plot(sizes,[row["expected_compactor_edges_per_m"] for row in comp],color="#009E73",linestyle="--",linewidth=1.5,label="Compactor: ideal expectation")
        for axis in axes:
            axis.set_xscale("log",base=2)
            axis.xaxis.set_major_locator(FixedLocator(sizes))
            axis.xaxis.set_major_formatter(FuncFormatter(lambda x,_:f"{int(x):,}"))
            axis.tick_params(axis="x",labelrotation=20)
            axis.set_xlabel("Original vertices n")
        axes[0].set_ylabel("Total contraction edge inputs / original m")
        axes[0].set_ylim(0,8); axes[0].legend(frameon=False,fontsize=9,loc="upper left")
        axes[1].set_ylabel("KKT / compactor contraction edge volume")
        axes[1].set_ylim(0,1.05); axes[1].axhline(1,color="#777777",linestyle=":",linewidth=1)
        axes[1].legend(frameon=False,fontsize=9); axes[1].text(.04,.07,"A work ratio, not a runtime ratio.",transform=axes[1].transAxes,fontsize=10,color="#555555")
        captions.append(save(fig,"volume_scaling","All eight ordered leaf b=4,d=16 size records. Compactor hierarchy/distance volumes are identical; overlapping KKT curves are retained. The ideal model predicts edge counts only."))

        fig, axes = plt.subplots(2,2,figsize=(12.5,7.4),gridspec_kw={"height_ratios":[2.2,1]})
        fig.subplots_adjust(left=.075,right=.98,top=.84,bottom=.12,hspace=.34,wspace=.24)
        fig.suptitle("Actual compactor rounds follow the quotient-occupancy model",x=.075,ha="left",y=.97,fontsize=16)
        fig.text(.075,.915,"n = 1,048,576, d = 16 · hierarchy and distance traces coincide for each block size",fontsize=11,color="#555555")
        for column,b in enumerate((4,16)):
            actual = traces[(f"leaf_hierarchy{b}",1048576,16)]
            twin = traces[(f"leaf_distance{b}",1048576,16)]
            require([(row["input_vertices"],row["input_edges"]) for row in actual] == [(row["input_vertices"],row["input_edges"]) for row in twin],"ordered round trajectories differ")
            x = [row["round"] for row in actual]
            axes[0,column].plot(x,[row["input_edges"]/row["m"] for row in actual],"o",markersize=4,color="#0072B2",label="Observed: both modes")
            axes[0,column].plot(x,[row["expected_input_edges"]/row["m"] for row in actual],color="#009E73",linestyle="--",label="Ideal subset expectation")
            axes[0,column].set_title(f"b = {b} · {len(actual)} compactor rounds",loc="left")
            axes[0,column].set_ylim(-.02,1.07); axes[0,column].set_ylabel("Input edges / original m")
            axes[0,column].legend(frameon=False,fontsize=9)
            axes[1,column].axhline(0,color="#777777",linewidth=1)
            axes[1,column].plot(x,[row["observed_minus_expected_input_edges"] for row in actual],"o-",markersize=3,color="#6A3D9A")
            axes[1,column].set_ylabel("Observed − expected\nedge count")
            axes[1,column].set_xlabel("Compactor round (round 1 consumes original graph)")
            for axis in axes[:,column]:
                axis.xaxis.set_major_locator(MaxNLocator(integer=True))
                axis.set_xlim(.5,max(x)+.5)
        captions.append(save(fig,"round_occupancy","The original-input and terminal counts are exact. Intermediate signed deviations are retained; they are ordinary single-graph variation, not significance scores. Model truncation bounds do not cover floating-point roundoff or random-graph variation."))

        fig, axes = plt.subplots(1,2,figsize=(12.5,5.2))
        fig.subplots_adjust(left=.075,right=.98,top=.8,bottom=.16,wspace=.25)
        fig.suptitle("Removing the core weight order changes the contraction path",x=.075,ha="left",y=.97,fontsize=16)
        fig.text(.075,.89,"Same leaf-attachment topology · n = 1,048,576, b = 4, d = 16 · actual observed rounds",fontsize=11,color="#555555")
        for mode,color,label in (("hierarchy","#0072B2","Hierarchy / distance"),
                                 ("shuffled","#009E73","Core-only shuffled; local stars cheap"),
                                 ("random","#D55E00","Global-random weights")):
            rows = traces[("leaf_"+mode+"4",1048576,16)]
            x = [row["round"] for row in rows]
            axes[0].plot(x,[row["input_vertices"]/row["n"] for row in rows],"o-",markersize=3,color=color,label=label)
            axes[1].plot(x,[row["input_edges"]/row["m"] for row in rows],"o-",markersize=3,color=color,label=label)
        for axis in axes:
            axis.set_yscale("log")
            axis.xaxis.set_major_locator(MaxNLocator(integer=True))
            axis.set_xlabel("Compactor round")
            axis.set_xlim(.5,19.5)
        axes[0].set_ylabel("Input vertices / original n");axes[1].set_ylabel("Input edges / original m")
        axes[0].legend(frameon=False,fontsize=9,loc="upper right")
        captions.append(save(fig,"weight_controls","Hierarchy and distance share the ordered compactor trajectory. Core-only shuffle preserves the first star contraction; global shuffle may change it. No occupancy-model curve is assigned to the controls. The logarithmic axis shows all positive input counts through completion."))

        fig, axis = plt.subplots(figsize=(12.5,9))
        fig.subplots_adjust(left=.32,right=.97,top=.88,bottom=.1)
        fig.suptitle("All 16 selected work records remain visible",x=.035,ha="left",y=.98,fontsize=16)
        fig.text(.035,.93,"Total contraction edge-input volume, normalized by original m · one recorded graph and sampling seed per case",fontsize=10.5,color="#555555")
        y = list(range(len(summary)))
        axis.barh([v-.18 for v in y],[row["compactor_contraction_edges_per_m"] for row in summary],height=.33,color="#555555",label="Compacting Borůvka")
        axis.barh([v+.18 for v in y],[row["kkt_contraction_edges_per_m"] for row in summary],height=.33,color="#0072B2",label="KKT")
        axis.set_yticks(y,[f"{row['family']}  ·  n={row['n']:,}, d={row['density']}" for row in summary],fontsize=9)
        axis.invert_yaxis();axis.set_xlabel("Total contraction edge inputs / original m")
        axis.legend(frameon=False,loc="lower right");axis.set_xlim(0,8);axis.grid(axis="y",visible=False)
        captions.append(save(fig,"all_selected_records","All 16 selected records, including community endpoint twins, b=16, d=2 and both shuffled controls. These are operation counts, not performance measurements; every record also remains in data.csv and the analysis report table."))

        shutil.copyfile(args.analysis_dir/"summary.csv",args.output_dir/"data.csv")
        shutil.copyfile(args.analysis_dir/"rounds.csv",args.output_dir/"round_data.csv")
        readme = ["# Attachment logical-work figures","",footer+".","",
                  "All 16 selected records are retained in [data.csv](data.csv), with every observed round in [round_data.csv](round_data.csv).",
                  "The complete case table and checked provenance are in [the analysis report](../attachment-work-analysis/report.md).",
                  "This figure set does not estimate wall-clock speed, fit asymptotic time complexity, or pool repeated graph seeds.",""]
        for item in captions:
            readme += [f"![{item['caption']}]({item['file']})","",item["caption"],""]
        (args.output_dir/"README.md").write_text("\n".join(readme))
        inputs[str(Path(__file__).resolve())] = sha(Path(__file__).resolve())
        record = {"schema":"attachment_work_figures_v1","validation":"pass","work_records":len(summary),
                  "trace_rounds":sum(len(value) for value in traces.values()),"graph_seed":seeds[0],"kkt_seed":seeds[1],
                  "matplotlib_version":matplotlib.__version__,"input_sha256":inputs,
                  "figure_captions":captions,"timings_fitted":False,"rows_removed":0,"rows_adjusted":0,
                  "artifact_sha256":{path.name:sha(path) for path in sorted(args.output_dir.iterdir())}}
        (args.output_dir/"provenance.json").write_text(json.dumps(record,indent=2)+"\n")
        print(json.dumps({"validation":"pass","figures":len(captions),"work_records":len(summary),"output_dir":str(args.output_dir)}))
    except (ValueError,OSError,KeyError,TypeError,ImportError) as error:
        parser.exit(2,f"attachment work plots: {error}\n")


if __name__ == "__main__":
    main()
