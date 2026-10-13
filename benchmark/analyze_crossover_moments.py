#!/usr/bin/env python3
"""Strict analysis of untimed contraction traces and original-component moments.

All manifest graphs are retained. Stage zero is synthesized as n singleton
components; stage r is the output of contraction round r. The final original
component remains size n although production represents its empty quotient with
zero vertices. No elapsed-time predictions or independent-sample claims are made.
Matplotlib is imported only when rendering, never by --validate-only/--self-test.
"""

import argparse
import collections
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys
import tempfile

from analyze_continuation import (
    TRACE_FIELDS, load_manifest, load_traces, require, seed_bank,
)

PREFIX = "component_moments_v1 "
FIELDS = {
    "case_id", "graph_seed", "round", "n", "component_count",
    "sum_squared_sizes", "largest_component", "validation",
}
DESCRIPTION = (
    "Untimed original-vertex component moments reconstructed independently from "
    "selected original edge IDs. Curves retain each graph draw. Summary means "
    "weight graph seeds equally; ranges are observed ranges, not confidence "
    "intervals. Stage zero is the original graph; stage r follows r contractions. "
    "The final original component has size n although the production quotient "
    "is empty. These counters do not predict elapsed time."
)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"nonfinite JSON constant: {value}")


def json_integer(value, context):
    require(type(value) is int and 0 <= value <= 2**64 - 1,
            f"{context}: expected an unsigned integer, not a bool/float/string")
    return value


def balanced_square_sum(total, count):
    require(count >= 1 and total >= count, "invalid positive partition dimensions")
    quotient, remainder = divmod(total, count)
    return (count - remainder) * quotient**2 + remainder * (quotient + 1)**2


def check_partition(row, previous, trace, context):
    n, q, square_sum, largest = (row[name] for name in
        ("n", "component_count", "sum_squared_sizes", "largest_component"))
    require(q == (trace["output_vertices"] or 1), f"{context}: count differs from trace")
    require(1 <= q <= n, f"{context}: invalid component count")
    require((n + q - 1) // q <= largest <= n - q + 1,
            f"{context}: impossible largest component")
    require(balanced_square_sum(n, q) <= square_sum <= (n - q + 1)**2 + q - 1,
            f"{context}: impossible sum of squared component sizes")
    require((square_sum - n) % 2 == 0, f"{context}: square-sum parity mismatch")
    if q == 1:
        require(largest == n and square_sum == n*n, f"{context}: invalid terminal component")
    else:
        remainder = n - largest
        require(square_sum >= largest**2 + balanced_square_sum(remainder, q - 1),
                f"{context}: square sum too small for largest component")
        # Convexity: maximize the remaining squares subject to each size <= L.
        if largest == 1:
            maximum = n
        else:
            full, extra = divmod(remainder - (q - 1), largest - 1)
            maximum = largest**2 + full * largest**2
            maximum += (1 + extra)**2 if extra else 0
            maximum += q - 1 - full - bool(extra)
        require(square_sum <= maximum and square_sum <= n * largest,
                f"{context}: square sum too large for largest component")
    require(q == previous["component_count"] - trace["selected_edges"],
            f"{context}: component reduction differs from selected edges")
    require(largest >= previous["largest_component"], f"{context}: largest component decreased")
    require(square_sum >= previous["sum_squared_sizes"] + 2 * trace["selected_edges"],
            f"{context}: sum of squares did not grow enough for the merges")


def load_moments(path, traces):
    expected = {(case, seed, r["round"]): r
                for (case, seed), rounds in traces.items() for r in rounds}
    records = {}
    with path.open() as stream:
        for line_number, line in enumerate(stream, 1):
            text = line.strip()
            if "component_moments" not in text:
                continue  # Setup diagnostics and unrelated log records are not clock validation.
            context = f"{path}:{line_number}"
            require(text.startswith(PREFIX), f"{context}: malformed/unsupported moment prefix")
            try:
                row = json.loads(text[len(PREFIX):], object_pairs_hook=unique_object,
                                 parse_constant=reject_constant)
            except (ValueError, TypeError) as error:
                raise ValueError(f"{context}: invalid moment JSON: {error}") from error
            require(type(row) is dict and set(row) == FIELDS, f"{context}: unexpected moment fields")
            require(type(row["case_id"]) is str and row["validation"] == "pass",
                    f"{context}: invalid case ID or failed validation")
            for field in FIELDS - {"case_id", "validation"}:
                json_integer(row[field], f"{context} {field}")
            key = row["case_id"], row["graph_seed"], row["round"]
            require(key in expected, f"{context}: unexpected graph/stage")
            require(key not in records, f"{context}: duplicate moment stage")
            require(row["n"] == expected[key]["n"], f"{context}: original n differs from trace")
            records[key] = row
    require(set(records) == set(expected),
            f"incomplete moment matrix: {len(records)}/{len(expected)} stages")
    for (case, seed), rounds in traces.items():
        n = rounds[0]["n"]
        previous = {"component_count": n, "sum_squared_sizes": n, "largest_component": 1}
        for trace in rounds:
            row = records[case, seed, trace["round"]]
            check_partition(row, previous, trace, f"{case}/{seed}/round{trace['round']}")
            previous = row
    return records


def derive(cases, graph_seeds, traces, moments):
    stages, graphs = [], []
    for case, spec in cases.items():
        n, m = spec["n"], spec["m"]
        for seed in graph_seeds:
            rounds = traces[case, seed]
            common = {**spec, "graph_seed": seed,
                      "input_fingerprint": rounds[0]["input_fingerprint"],
                      "topology_fingerprint": rounds[0]["topology_fingerprint"]}
            state = {"component_count": n, "sum_squared_sizes": n, "largest_component": 1}
            cumulative = 0
            graph_stages = []
            for stage in range(len(rounds) + 1):
                if stage:
                    trace = rounds[stage - 1]
                    state = moments[case, seed, stage]
                    vertices, edges = trace["output_vertices"], trace["output_edges"]
                    cumulative += trace["input_edges"]
                else:
                    vertices, edges = n, m
                q = state["component_count"]
                q_eff = n*n / state["sum_squared_sizes"]
                graph_stages.append({**common, "stage": stage,
                    "remaining_vertices": vertices, "remaining_edges": edges,
                    "component_count": q, "sum_squared_sizes": state["sum_squared_sizes"],
                    "largest_component": state["largest_component"],
                    "effective_component_count": q_eff,
                    "component_count_over_n": q/n, "effective_count_over_n": q_eff/n,
                    "effective_over_actual_count": q_eff/q,
                    "largest_component_fraction": state["largest_component"]/n,
                    "remaining_edge_fraction": edges/m,
                    "cumulative_contraction_input_edges": cumulative,
                    "cumulative_contraction_input_over_m": cumulative/m,
                    "validation": "pass"})
            stages.extend(graph_stages)
            root = graph_stages[min(2, len(rounds))]
            graphs.append({**common, "rounds": len(rounds),
                "contraction_input_edges": cumulative, "contraction_input_over_m": cumulative/m,
                "contraction_input_vertices_over_n": sum(r["input_vertices"] for r in rounds)/n,
                "after_two_edge_fraction": root["remaining_edge_fraction"],
                "after_two_component_count": root["component_count"],
                "after_two_effective_count": root["effective_component_count"],
                "after_two_effective_over_actual": root["effective_over_actual_count"],
                "after_two_largest_fraction": root["largest_component_fraction"], "validation": "pass"})
    summaries = []
    for case, spec in cases.items():
        selected = [r for r in graphs if r["case_id"] == case]
        row = {**spec, "graphs": len(selected)}
        for field in ("rounds", "contraction_input_over_m", "after_two_edge_fraction",
                      "after_two_effective_over_actual", "after_two_largest_fraction"):
            values = [r[field] for r in selected]
            row.update({"mean_"+field: statistics.mean(values), "min_"+field: min(values),
                        "max_"+field: max(values)})
        summaries.append(row)
    return stages, graphs, summaries


def write_csv(path, rows):
    require(rows, f"refusing to write empty table: {path}")
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plots(stages, graphs, cases, graph_seeds, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    plt.rcParams.update({"font.size": 10, "svg.fonttype": "none", "pdf.fonttype": 42})
    colors = plt.get_cmap("tab10")
    by_graph = collections.defaultdict(list)
    graph_summary = {(r["case_id"], r["graph_seed"]): r for r in graphs}
    for row in stages:
        by_graph[row["case_id"], row["graph_seed"]].append(row)
    groups = collections.defaultdict(list)
    for case, spec in cases.items():
        groups[spec["n"], spec["density"], spec["intrusion_per_mille"]].append(case)
    files = []

    def save(fig, stem):
        for extension in ("png", "svg", "pdf"):
            path = output / f"{stem}.{extension}"
            fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
            if extension == "svg":
                path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines())+"\n")
            files.append(path.name)
        plt.close(fig)

    for (n, d, p), case_ids in sorted(groups.items()):
        case_ids.sort(key=lambda case: cases[case]["family"])
        suffix = f"n{n}_d{d}_p{p}"
        for kind in ("edge_retention", "effective_components", "component_balance"):
            columns = min(3, len(case_ids))
            rows = math.ceil(len(case_ids)/columns)
            fig, axes = plt.subplots(rows, columns, squeeze=False,
                                     figsize=(4.8*columns, 3.35*rows+1.1))
            for axis in axes.flat[len(case_ids):]:
                axis.set_visible(False)
            for axis, case in zip(axes.flat, case_ids):
                for index, seed in enumerate(graph_seeds):
                    records = by_graph[case, seed]
                    x = [r["stage"] for r in records]
                    color = colors(index % 10)
                    kwargs = {"color": color, "linewidth": 1.5, "markersize": 3}
                    if kind == "edge_retention":
                        axis.plot(x, [r["remaining_edge_fraction"] for r in records],
                                  marker="o", label=f"g={seed}", **kwargs)
                        axis.set_ylabel("Remaining edges / original m")
                    elif kind == "effective_components":
                        axis.plot(x, [r["effective_count_over_n"] for r in records],
                                  marker="o", label=f"g={seed}: effective", **kwargs)
                        axis.plot(x, [r["component_count_over_n"] for r in records],
                                  linestyle="--", label=f"g={seed}: actual", **kwargs)
                        axis.set_yscale("log")
                        axis.set_ylabel("Component count / original n (log)")
                    else:
                        axis.plot(x, [r["largest_component_fraction"] for r in records],
                                  marker="o", label=f"g={seed}: largest / n", **kwargs)
                        axis.plot(x, [r["effective_over_actual_count"] for r in records],
                                  linestyle="--", label=f"g={seed}: effective / actual", **kwargs)
                        axis.set_ylabel("Fraction")
                axis.set_title(cases[case]["family"].replace("_", " "), fontsize=11)
                axis.set_xlabel("Completed contraction rounds")
                axis.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))
                axis.grid(alpha=.22)
                axis.spines[["top", "right"]].set_visible(False)
                if kind != "effective_components":
                    axis.set_ylim(-.025, 1.04)
                if kind == "edge_retention":
                    values = [graph_summary[case, seed]["contraction_input_over_m"] for seed in graph_seeds]
                    axis.text(.97, .93, f"mean V/m = {statistics.mean(values):.3f}",
                              transform=axis.transAxes, ha="right", va="top", fontsize=9,
                              bbox={"facecolor":"white", "edgecolor":"none", "alpha":.85})
            title = {"edge_retention":"Edge retention", "effective_components":"Effective versus actual components",
                     "component_balance":"Largest component and size balance"}[kind]
            fig.suptitle(f"{title} · n={n:,}, m/n={d}, intrusion={p}‰", y=.995, fontsize=14)
            handles, labels = axes.flat[0].get_legend_handles_labels()
            fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(.5,.048),
                       ncol=min(4, len(labels)), fontsize=8, frameon=False)
            fig.text(.02,.008, "Untimed traces; each line is one graph. Final original component remains size n; quotient is empty.",
                     fontsize=8)
            fig.tight_layout(rect=(0,.11,1,.965))
            save(fig, f"{kind}_{suffix}")
        fig, axis = plt.subplots(figsize=(max(7, 1.35*len(case_ids)), 4.6))
        for index, case in enumerate(case_ids):
            values = [graph_summary[case, seed]["contraction_input_over_m"] for seed in graph_seeds]
            axis.bar(index, statistics.mean(values), width=.65, color="#CAD8E5")
            for seed_index, value in enumerate(values):
                offset = 0 if len(values) == 1 else .3*(seed_index/(len(values)-1)-.5)
                axis.scatter(index+offset, value, color=colors(seed_index%10), s=35,
                             label=f"g={graph_seeds[seed_index]}" if index == 0 else None, zorder=3)
        axis.set_xticks(range(len(case_ids)), [cases[c]["family"].replace("_", "\n") for c in case_ids], fontsize=9)
        axis.set_ylabel("Sum of contraction input edges / original m")
        axis.set_title(f"Normalized contraction volume · n={n:,}, m/n={d}, intrusion={p}‰")
        axis.set_ylim(bottom=0)
        axis.grid(axis="y", alpha=.2)
        axis.set_axisbelow(True)
        axis.legend(fontsize=8, frameon=False)
        fig.text(.02,.01,"Bars: arithmetic means over graph seeds. Dots: all graph draws. This is work volume, not elapsed time.", fontsize=8)
        fig.tight_layout(rect=(0,.06,1,1))
        save(fig, f"edge_volume_{suffix}")
    return files


def self_test():
    """Small independently constructed trace, plus fail-closed log mutations."""
    with tempfile.TemporaryDirectory(prefix="kkt-moments-test-") as directory:
        root = Path(directory)
        manifest, trace, log = root/"manifest.csv", root/"trace.csv", root/"trace.log"
        manifest.write_text("family,n,density,intrusion_per_mille\nline_random,32,1,0\n")
        cases = load_manifest(manifest)
        case, spec = next(iter(cases.items()))
        records, moment_rows = [], []
        vertices, edges = 32, 32
        for r in range(1,6):
            q = 32 >> r
            out_v, out_m = (q, q-1) if q > 1 else (0,0)
            records.append({**spec,"graph_seed":17,"input_fingerprint":123,"topology_fingerprint":456,
                "round":r,"input_vertices":vertices,"input_edges":edges,
                "selected_edges":vertices-q,"output_vertices":out_v,"output_edges":out_m,
                "total_rounds":5,"total_selected_edges":31,"validation":"pass"})
            moment_rows.append({"case_id":case,"graph_seed":17,"round":r,"n":32,
                "component_count":q,"sum_squared_sizes":32*(1<<r),
                "largest_component":1<<r,"validation":"pass"})
            vertices, edges = out_v, out_m
        with trace.open("w",newline="") as stream:
            writer=csv.DictWriter(stream, fieldnames=TRACE_FIELDS)
            writer.writeheader();writer.writerows(records)
        def encode(rows):
            return "setup_generation_ms=0\n"+"".join(PREFIX+json.dumps(row)+"\n" for row in rows)
        valid = encode(moment_rows)
        log.write_text(valid)
        traces = load_traces(trace, cases, (17,))
        loaded = load_moments(log, traces)
        stages, graphs, summaries = derive(cases, (17,), traces, loaded)
        require(len(stages)==6 and stages[-1]["effective_component_count"]==1 and
                stages[-1]["remaining_vertices"]==0 and graphs[0]["contraction_input_edges"]==58,
                "self-test derivation mismatch")
        mutations = {"missing":encode(moment_rows[:-1]), "duplicate":valid+PREFIX+json.dumps(moment_rows[0])+"\n",
            "malformed_json":valid+PREFIX+"{bad}\n", "unsupported_prefix":valid.replace(PREFIX,"component_moments_v2 ",1),
            "duplicate_json_key":valid.replace('"n": 32','"n": 32, "n": 32',1),
            "nonfinite":valid.replace('"n": 32','"n": NaN',1),
            "not_an_object":valid+PREFIX+"[]\n"}
        replacements = {"bool":("sum_squared_sizes",True),"float":("component_count",16.0),
            "negative":("largest_component",-1),"wrong_n":("n",64),"wrong_seed":("graph_seed",19),
            "wrong_case":("case_id","missing_case"),
            "wrong_round":("round",0),"wrong_count":("component_count",15),"parity":("sum_squared_sizes",65),
            "too_small":("sum_squared_sizes",62),"too_large":("sum_squared_sizes",1024),
            "max_too_small":("largest_component",1),"max_too_large":("largest_component",18),
            "incompatible_max":("largest_component",3),"failed":("validation","fail"),"string":("n","32")}
        for label,(field,value) in replacements.items():
            changed=[dict(row) for row in moment_rows];changed[0][field]=value
            mutations[label]=encode(changed)
        changed=[dict(row) for row in moment_rows];changed[-1]["sum_squared_sizes"]=1022
        mutations["bad_terminal"]=encode(changed)
        changed=[dict(row) for row in moment_rows];changed[0]["extra"]=1
        mutations["extra_field"]=encode(changed)
        for label, content in mutations.items():
            log.write_text(content)
            try:load_moments(log,traces)
            except ValueError:pass
            else:raise ValueError(f"self-test accepted malformed case: {label}")
        return {"validation":"pass","valid_graphs":1,"valid_stages":5,"derived_stages_including_zero":6,
                "malformed_cases_rejected":len(mutations),"malformed_case_names":sorted(mutations),
                "scope":"Moment/trace validation only; clock records belong to crossover_clocks.py."}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-csv",type=Path)
    parser.add_argument("--log",type=Path)
    parser.add_argument("--manifest",type=Path)
    parser.add_argument("--graph-seeds",type=seed_bank)
    parser.add_argument("--output-dir",type=Path)
    parser.add_argument("--validate-only",action="store_true")
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(),indent=2));return
    require(all(getattr(args,name) is not None for name in ("trace_csv","log","manifest","graph_seeds")),
            "--trace-csv, --log, --manifest and --graph-seeds are required")
    require(args.validate_only or args.output_dir is not None,"--output-dir is required unless --validate-only")
    cases=load_manifest(args.manifest)
    traces=load_traces(args.trace_csv,cases,args.graph_seeds)
    moments=load_moments(args.log,traces)
    stages,graphs,summaries=derive(cases,args.graph_seeds,traces,moments)
    metadata={"validation":"pass","case_count":len(cases),"graph_count":len(traces),
        "graph_seeds":args.graph_seeds,"trace_stages":len(moments),"derived_stages_including_zero":len(stages),
        "description":DESCRIPTION,"clock_validation":"Not performed; use crossover_clocks.py for timing logs.",
        "inputs":{},"source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "trace_loader_sha256":hashlib.sha256(Path(__file__).with_name("analyze_continuation.py").read_bytes()).hexdigest()}
    for name in ("trace_csv","log","manifest"):
        path=getattr(args,name)
        metadata["inputs"][name]={"path":str(path.resolve()),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    if args.validate_only:
        print(json.dumps(metadata,indent=2));return
    args.output_dir.mkdir(parents=True,exist_ok=True)
    for name,rows in (("component_stages",stages),("graph_summary",graphs),("case_summary",summaries)):
        write_csv(args.output_dir/(name+".csv"),rows)
    metadata["figures"]=plots(stages,graphs,cases,args.graph_seeds,args.output_dir)
    (args.output_dir/"provenance.json").write_text(json.dumps(metadata,indent=2)+"\n")
    report=["# Untimed contraction components", "", DESCRIPTION, "",
        f"Validated {len(cases)} cases, {len(traces)} graphs and {len(moments)} moment/trace stages; all retained.","",
        "`q_eff = n² / sum(size²)` measures effective component count; `q_eff/q` is one for equal sizes and falls as sizes become uneven. The largest fraction is max(size)/n. These are descriptive statistics, not an independent-background occupancy theorem for random-weight graphs.","",
        "| Case | Graphs | Mean V/m [graph range] | Mean balance after two rounds | Mean largest fraction after two rounds |",
        "|---|---:|---:|---:|---:|"]
    for row in summaries:
        report.append(f"| {row['case_id']} | {row['graphs']} | {row['mean_contraction_input_over_m']:.4f} [{row['min_contraction_input_over_m']:.4f}, {row['max_contraction_input_over_m']:.4f}] | {row['mean_after_two_effective_over_actual']:.4f} | {row['mean_after_two_largest_fraction']:.6f} |")
    report.extend(["","Raw inputs:",""])
    for name in ("trace_csv","log","manifest"):
        report.append(f"- [{name}]({os.path.relpath(getattr(args,name).resolve(),args.output_dir.resolve())})")
    report.extend(["","[Per-stage data](component_stages.csv), [per-graph volumes](graph_summary.csv), [case summaries](case_summary.csv), [provenance](provenance.json).",""])
    for name in metadata["figures"]:
        if name.endswith(".png"):report.extend([f"![{Path(name).stem.replace('_',' ')}]({name})",""])
    (args.output_dir/"report.md").write_text("\n".join(report).rstrip()+"\n")
    print(f"Validated {len(traces)} graphs and {len(moments)} stages; wrote {args.output_dir}")


if __name__=="__main__":
    try:main()
    except (ValueError,OSError) as error:
        print("crossover moments: "+str(error),file=sys.stderr)
        sys.exit(1)
