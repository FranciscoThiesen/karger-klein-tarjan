#!/usr/bin/env python3
"""Validate and compare continuation campaigns without pooling separate runs.

Configuration paths are relative to the JSON configuration. Each campaign has
name, role (screen, confirmation, sensitivity), manifest, timing_csv,
graph_seeds, sampling_seeds, repetitions, warmups, and optional timing_metadata,
work_csv, trace_csv. A confirmation object names primary/repeat campaigns and
candidate_groups [{family, density, intrusion_per_mille}]. Its descriptive rule
is fixed here: ratio <= .90 and every graph ratio < 1, at both largest tested
sizes, separately in both campaigns. The second manifest must reverse the first.
"""
import argparse
import collections
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import sys

import analyze_continuation as base

HOLDOUT_GRAPHS = (2027, 4099, 8191, 104729, 131071)
HOLDOUT_SAMPLING = (11, 29, 97)
THRESHOLD = 0.90
GROUP_FIELDS = ("family", "density", "intrusion_per_mille")
PRODUCTION_FILES = ("kkt/kkt.cpp", "kkt/kkt.hpp", "common/edge.hpp",
                    "verifier/verifier_v2.cpp", "verifier/verifier_v2.hpp",
                    "verifier/median_table.hpp", "lca/lca.cpp", "lca/lca.hpp")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def group(row):
    return tuple(row[f] for f in GROUP_FIELDS)


def json_bank(value, name):
    base.require(isinstance(value, list) and value and all(type(x) is int for x in value),
                 f"{name}: expected a nonempty array of integer seeds")
    return base.seed_bank(",".join(str(x) for x in value))


def load_metadata(path, timing_path, manifest_path, count, warmups):
    data = json.loads(path.read_text())
    base.require(isinstance(data, dict) and data.get("mode") == "timing" and
                 type(data.get("exit_status")) is int and data["exit_status"] == 0 and
                 "interruption" in data and data["interruption"] is None,
                 f"{path}: runner did not complete a successful timed campaign")
    base.require(data.get("output_sha256") == sha256(timing_path) and
                 data.get("manifest_sha256") == sha256(manifest_path),
                 f"{path}: runner raw-data or manifest hash differs")
    base.require(type(data.get("basic_validated_rows")) is int and data["basic_validated_rows"] == count and
                 type(data.get("checked_warmup_calls")) is int and data["checked_warmup_calls"] == warmups,
                 f"{path}: runner row/warmup count differs")
    for name in ("binary_sha256", "runner_sha256"):
        base.require(isinstance(data.get(name), str) and re.fullmatch(r"[0-9a-f]{64}", data[name]),
                     f"{path}: missing {name}")
    base.require(isinstance(data.get("source_sha256"), dict) and
                 all(isinstance(data["source_sha256"].get(f), str) and
                     re.fullmatch(r"[0-9a-f]{64}", data["source_sha256"][f]) for f in PRODUCTION_FILES),
                 f"{path}: missing production source fingerprints")
    base.require(all(isinstance(data.get(f), str) and data[f] for f in ("profile", "platform", "machine")),
                 f"{path}: missing build/machine profile")
    return data


def load_campaign(raw, folder):
    required = {"name", "role", "manifest", "timing_csv", "graph_seeds", "sampling_seeds", "repetitions", "warmups"}
    allowed = required | {"timing_metadata", "work_csv", "trace_csv"}
    base.require(isinstance(raw, dict) and required <= set(raw) <= allowed, "unexpected campaign configuration fields")
    base.require(isinstance(raw["name"], str) and re.fullmatch(r"[A-Za-z0-9_-]+", raw["name"]), "invalid campaign name")
    base.require(raw["role"] in ("screen", "confirmation", "sensitivity"), "invalid campaign role")
    paths = {}
    for field in ("manifest", "timing_csv", "timing_metadata", "work_csv", "trace_csv"):
        if field in raw:
            base.require(isinstance(raw[field], str) and raw[field], f"invalid path: {field}")
            paths[field] = (folder / raw[field]).resolve()
    gs, ss = json_bank(raw["graph_seeds"], "graph_seeds"), json_bank(raw["sampling_seeds"], "sampling_seeds")
    base.require(type(raw["repetitions"]) is int and type(raw["warmups"]) is int, "protocol counts must be integers")
    cases = base.load_manifest(paths["manifest"])
    timing = base.load_timing(paths["timing_csv"], cases, gs, ss, raw["repetitions"], raw["warmups"])
    expected_order = [(case,g,s,r,base.ALGORITHMS[(order+r+gi+si)%2])
                      for case in cases for gi,g in enumerate(gs) for si,s in enumerate(ss)
                      for r in range(raw["repetitions"]) for order in (0,1)]
    base.require(list(timing) == expected_order,
                 f'{raw["name"]}: CSV record order differs from the manifest and balanced execution schedule')
    work = base.load_work(paths["work_csv"], cases, gs, ss) if "work_csv" in paths else {}
    traces = base.load_traces(paths["trace_csv"], cases, gs) if "trace_csv" in paths else {}
    base.crosscheck(timing, work, traces, ss)
    checked_warmups = len(cases)*len(gs)*len(ss)*2*raw["warmups"]
    provenance = load_metadata(paths["timing_metadata"], paths["timing_csv"], paths["manifest"], len(timing), checked_warmups) if "timing_metadata" in paths else None
    return {"name":raw["name"], "role":raw["role"], "cases":cases, "timing":timing,
            "work":work, "traces":traces, "graph_seeds":gs, "sampling_seeds":ss,
            "repetitions":raw["repetitions"], "warmups":raw["warmups"], "provenance":provenance,
            "checked_warmups":checked_warmups, "paths":paths,
            "tables":base.aggregate_timing(timing, cases, gs, ss, raw["repetitions"]),
            "work_tables":base.aggregate_work(work, traces, cases, gs, ss)}


def validate_confirmation(spec, campaigns):
    base.require(isinstance(spec, dict) and set(spec) == {"primary", "repeat", "candidate_groups"},
                 "confirmation must name primary, repeat and candidate_groups")
    by_name = {c["name"]:c for c in campaigns}
    base.require(isinstance(spec["primary"], str) and isinstance(spec["repeat"], str) and
                 spec["primary"] != spec["repeat"] and spec["primary"] in by_name and spec["repeat"] in by_name,
                 "confirmation requires two distinct configured campaigns")
    a,b = by_name[spec["primary"]], by_name[spec["repeat"]]
    base.require({c["name"] for c in campaigns if c["role"] == "confirmation"} == {a["name"], b["name"]},
                 "confirmation roles must identify exactly the two named campaigns")
    base.require(a["cases"] == b["cases"] and list(b["cases"]) == list(reversed(a["cases"])),
                 "confirmation must use the same case set in exactly reversed manifest order")
    for c in (a,b):
        base.require(c["graph_seeds"] == HOLDOUT_GRAPHS and c["sampling_seeds"] == HOLDOUT_SAMPLING and
                     c["repetitions"] == 4 and c["warmups"] == 1,
                     "confirmation differs from the predeclared fresh-seed protocol")
        base.require(c["provenance"] is not None, "confirmation requires runner metadata")
    for c in campaigns:
        if c["role"] == "screen":
            base.require(not set(c["graph_seeds"]) & set(HOLDOUT_GRAPHS) and
                         not set(c["sampling_seeds"]) & set(HOLDOUT_SAMPLING),
                         "screen used held-out graph or sampling seeds")
    pa,pb = a["provenance"],b["provenance"]
    for field in ("binary_sha256", "profile", "platform", "machine"):
        base.require(pa[field] == pb[field], f"confirmation {field} differs across runs")
    base.require(pa["source_sha256"] == pb["source_sha256"], "confirmation source inventory changed across runs")
    base.require(set(a["timing"]) == set(b["timing"]), "confirmation timing keys differ")
    base.check_fingerprints([*a["timing"].values(), *b["timing"].values()])
    for field in ("work", "traces"):
        if a[field] and b[field]:
            base.require(a[field] == b[field], f"identical confirmation graphs have different {field} observations")
    raw_groups = spec["candidate_groups"]
    base.require(isinstance(raw_groups, list) and raw_groups, "confirmation needs preselected candidate groups")
    candidates = []
    for raw in raw_groups:
        base.require(isinstance(raw, dict) and set(raw) == set(GROUP_FIELDS), "invalid candidate group fields")
        base.require(isinstance(raw["family"], str) and type(raw["density"]) is int and
                     type(raw["intrusion_per_mille"]) is int, "invalid candidate group types")
        key = group(raw)
        base.require(key in {group(r) for r in a["cases"].values()} and key[2] == 0,
                     "candidate must be an unperturbed group in the frozen confirmation manifest")
        base.require(key not in candidates, "duplicate candidate group")
        candidates.append(key)
    return a,b,set(candidates)


def collect(config, folder):
    base.require(isinstance(config, dict) and {"campaigns"} <= set(config) <= {"campaigns", "confirmation", "selection_file"},
                 "unexpected top-level comparison configuration fields")
    base.require(isinstance(config["campaigns"], list) and config["campaigns"], "empty campaign list")
    campaigns = [load_campaign(c,folder) for c in config["campaigns"]]
    base.require(len({c["name"] for c in campaigns}) == len(campaigns), "duplicate campaign name")
    # Shared graph labels must mean the same input, including screens that extend
    # earlier manifests. New seeds are different realizations, not mismatches.
    base.check_fingerprints(r for c in campaigns for r in c["timing"].values())
    reference = next((c["provenance"] for c in campaigns if c["provenance"]), None)
    if reference:
        for c in campaigns:
            if c["provenance"]:
                base.require(all(c["provenance"]["source_sha256"][f] == reference["source_sha256"][f]
                                 for f in PRODUCTION_FILES), "listed production-library sources changed across campaigns")
                base.require(all(c["provenance"][f] == reference[f] for f in ("profile","platform","machine")),
                             "build or machine profile changed across campaigns")
    confirmation = validate_confirmation(config["confirmation"], campaigns) if "confirmation" in config else None
    base.require(confirmation is not None or all(c["role"] != "confirmation" for c in campaigns),
                 "confirmation campaign lacks a declared comparison")
    if "selection_file" in config:
        base.require(confirmation is not None and isinstance(config["selection_file"],str) and config["selection_file"],
                     "selection_file requires a declared confirmation pair and a path")
        validate_selection(folder/config["selection_file"],campaigns,confirmation)
    return campaigns, confirmation


def timestamp(value, context):
    base.require(isinstance(value,str), context+": missing timestamp")
    result=datetime.fromisoformat(value.replace("Z","+00:00"))
    base.require(result.tzinfo is not None, context+": timestamp must specify timezone")
    return result


def validate_selection(path, campaigns, confirmation):
    """Bind the declared comparison to the archived pre-timing selection record.

    The record and runner timestamps are evidence from the harness, not an
    independent clock or an authenticated history; the git freeze remains part
    of the provenance audit.
    """
    selection=json.loads(path.read_text())
    a,b,candidates=confirmation
    base.require(isinstance(selection,dict), "selection record must be an object")
    raw_groups=selection.get("selected_groups")
    base.require(isinstance(raw_groups,list) and all(isinstance(r,dict) and set(r)==set(GROUP_FIELDS)
                 and isinstance(r["family"],str) and type(r["density"]) is int
                 and type(r["intrusion_per_mille"]) is int for r in raw_groups),
                 "invalid frozen candidate groups")
    groups=[group(r) for r in raw_groups]
    base.require(len(groups)==len(set(groups)) and set(groups)==candidates, "candidate groups differ from frozen selection")
    sizes=selection.get("selected_sizes")
    base.require(isinstance(sizes,list) and len(sizes)==2 and all(type(n) is int for n in sizes)
                 and sizes==sorted(set(sizes)), "frozen selection must name two distinct ascending sizes")
    for key in candidates:
        base.require(sorted(r["n"] for r in a["cases"].values() if group(r)==key)==sizes,
                     "candidate sizes differ from frozen selection")
    for field,expected in (("graph_seeds",list(HOLDOUT_GRAPHS)),("sampling_seeds",list(HOLDOUT_SAMPLING)),
                           ("repetitions",4),("warmups",1),("campaigns",2)):
        actual=selection.get(field)
        base.require(actual==expected and (type(actual) is list if isinstance(expected,list) else type(actual) is int),
                     f"frozen {field} differs from confirmation protocol")
        if isinstance(expected,list):base.require(all(type(x) is int for x in actual),f"frozen {field} requires integers")
    screens={c["paths"]["timing_csv"].name:sha256(c["paths"]["timing_csv"])
             for c in campaigns if c["role"]=="screen"}
    base.require(len(screens)==sum(c["role"]=="screen" for c in campaigns) and
                 selection.get("selection_evidence_sha256")==screens,
                 "selection evidence differs from the complete declared screening set")
    manifests={c["paths"]["manifest"].name:sha256(c["paths"]["manifest"])
               for c in campaigns if c["role"] in ("confirmation","sensitivity")}
    base.require(len(manifests)==sum(c["role"] in ("confirmation","sensitivity") for c in campaigns) and
                 selection.get("manifest_sha256")==manifests, "frozen confirmation/sensitivity manifests differ")
    frozen=timestamp(selection.get("frozen_utc"), "selection freeze")
    for c in (a,b):
        base.require(c["provenance"]["binary_sha256"]==selection.get("binary_sha256"),
                     "confirmation binary differs from frozen selection")
        started=timestamp(c["provenance"].get("started_utc"), c["name"]+" runner start")
        base.require(started>frozen, "confirmation started before the recorded selection freeze")


def confirmation_tables(confirmation):
    if confirmation is None:
        return [],[],[]
    a,b,candidates = confirmation
    rows_a = {r["case_id"]:r for r in a["tables"][0]}
    rows_b = {r["case_id"]:r for r in b["tables"][0]}
    cases,groups,graphs = [],[],[]
    for case,ar in rows_a.items():
        br = rows_b[case]
        spec = a["cases"][case]
        row = {**spec, "selected_candidate":group(spec) in candidates}
        for name,r in (("primary",ar),("repeat",br)):
            for field in ("paired_runtime_ratio","graph_min_ratio","graph_max_ratio","kkt_median_ns",
                          "compacting_boruvka_median_ns","kkt_slower_observations","equal_observations","paired_observations"):
                row[name+"_"+field] = r[field]
        row.update(both_case_medians_below_one=all(r["paired_runtime_ratio"] < 1 for r in (ar,br)),
                   both_all_graph_medians_below_one=all(r["graph_max_ratio"] < 1 for r in (ar,br)),
                   passes_case_threshold=all(r["paired_runtime_ratio"] <= THRESHOLD and r["graph_max_ratio"] < 1 for r in (ar,br)),
                   repeat_over_primary_kkt_median=br["kkt_median_ns"]/ar["kkt_median_ns"],
                   repeat_over_primary_compaction_median=br["compacting_boruvka_median_ns"]/ar["compacting_boruvka_median_ns"])
        cases.append(row)
    for key in sorted({group(r) for r in cases}):
        selected = sorted((r for r in cases if group(r)==key),key=lambda r:r["n"])
        largest = selected[-2:]
        sufficient = len(largest)==2
        passed = sufficient and all(r["passes_case_threshold"] for r in largest)
        groups.append({**dict(zip(GROUP_FIELDS,key)), "selected_candidate":key in candidates,
                       "tested_sizes":",".join(str(r["n"]) for r in selected),
                       "criterion_sizes":",".join(str(r["n"]) for r in largest),
                       "two_sizes_available":sufficient, "threshold":THRESHOLD,
                       "passes_numeric_rule":passed, "confirmed_preselected_group":key in candidates and passed})
    ga = {(r["case_id"],r["graph_seed"]):r for r in a["tables"][1]}
    gb = {(r["case_id"],r["graph_seed"]):r for r in b["tables"][1]}
    for key,ar in ga.items():
        br = gb[key]
        graphs.append({**a["cases"][key[0]], "graph_seed":key[1], "input_fingerprint":ar["input_fingerprint"],
            "topology_fingerprint":ar["topology_fingerprint"], "primary_ratio":ar["paired_runtime_ratio"],
            "repeat_ratio":br["paired_runtime_ratio"],
            "both_runs_below_one":ar["paired_runtime_ratio"] < 1 and br["paired_runtime_ratio"] < 1})
    return cases,groups,graphs


def tagged_tables(campaigns):
    names = ("case_summary", "graph_summary", "paired_pairs", "order_summary",
             "work_summary", "graph_work_summary", "trace_summary", "round_edge_volumes")
    result = {name:[] for name in names}
    for c in campaigns:
        for name,rows in zip(names,(*c["tables"], *c["work_tables"])):
            result[name].extend({"campaign":c["name"], "role":c["role"], **r} for r in rows)
    return result


def write_tables(output, tables):
    # Optional trace-derived work fields can differ by campaign; explicitly fill
    # those unavailable values with empty cells, never with misleading zeros.
    for name,rows in tables.items():
        fields = list(dict.fromkeys(f for row in rows for f in row))
        base.write_csv(output/(name+".csv"), [{f:r.get(f,"") for f in fields} for r in rows])


def plots(output, campaigns, tables):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter
    plt.rcParams.update({"font.size":9, "svg.fonttype":"none", "pdf.fonttype":42})
    groups = sorted({group(r) for r in tables["case_summary"]})
    colors = {c["name"]:plt.get_cmap("tab10")(i%10) for i,c in enumerate(campaigns)}
    def pages(kind, label):
        plotted_groups = groups if kind != "work" else sorted({group(r) for r in
            [*tables["work_summary"], *tables["trace_summary"]]})
        for page in range(math.ceil(len(plotted_groups)/6)):
            shown = plotted_groups[page*6:(page+1)*6]
            ncols=min(3,len(shown));nrows=math.ceil(len(shown)/ncols)
            fig,axes=plt.subplots(nrows,ncols,figsize=(5*ncols,3.7*nrows+1),squeeze=False)
            for axis in axes.flat[len(shown):]:axis.set_visible(False)
            for axis,key in zip(axes.flat,shown):
                relevant=[r for r in tables["case_summary"] if group(r)==key]
                for c in campaigns:
                    rows=sorted((r for r in relevant if r["campaign"]==c["name"]),key=lambda r:r["n"])
                    if not rows:continue
                    color=colors[c["name"]]
                    x=[r["n"] for r in rows]
                    if kind=="ratios":
                        y=[r["paired_runtime_ratio"] for r in rows]
                        axis.plot(x,y,"-o",color=color,ms=4,label=c["name"])
                        axis.vlines(x,[r["graph_min_ratio"] for r in rows],[r["graph_max_ratio"] for r in rows],color=color,alpha=.65)
                        axis.fill_between(x,[r["graph_min_ratio"] for r in rows],[r["graph_max_ratio"] for r in rows],color=color,alpha=.08)
                    elif kind=="times":
                        for algorithm,field,style in (("KKT","kkt_median_ns","-"),("compaction","compacting_boruvka_median_ns","--")):
                            axis.plot(x,[r[field]/1e6 for r in rows],style+"o",color=color,ms=3,label=f'{c["name"]} {algorithm}')
                    else:
                        for algorithm,style in (("kkt","-"),("compacting_boruvka","--")):
                            wr=sorted((r for r in tables["work_summary"] if r["campaign"]==c["name"] and group(r)==key and r["algorithm"]==algorithm),key=lambda r:r["n"])
                            if wr:axis.plot([r["n"] for r in wr],[r["contraction_edges_over_m"] for r in wr],style+"o",color=color,ms=3,label=f'{c["name"]} {algorithm}')
                        if not c["work"]:
                            tr=collections.defaultdict(list)
                            for r in tables["trace_summary"]:
                                if r["campaign"]==c["name"] and group(r)==key:tr[r["n"]].append(r["contraction_edges_over_m"])
                            if tr:axis.plot(sorted(tr),[statistics.fmean(tr[n]) for n in sorted(tr)],"--o",color=color,ms=3,label=f'{c["name"]} compaction trace')
                if kind=="ratios":
                    axis.axhline(1,color="#555",ls="--",lw=1)
                    axis.axhline(THRESHOLD,color="#999",ls=":",lw=1)
                    # Include 1 and .90 in every panel; changes in tiny ranges
                    # therefore cannot masquerade as a large practical gain.
                    axis.set_ylim(min(THRESHOLD,min(r["graph_min_ratio"] for r in relevant))*.95,
                                  max(1,max(r["graph_max_ratio"] for r in relevant))*1.05)
                    axis.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f"{v:g}×"))
                elif kind=="times":
                    axis.set_yscale("log")
                    axis.yaxis.set_major_locator(LogLocator(base=10,subs=(1,2,5)))
                    axis.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f"{v:g}"))
                else:axis.set_ylim(bottom=0)
                axis.set_xscale("log",base=2)
                ns=sorted({r["n"] for r in relevant})
                axis.set_xticks(ns,[f"{n:,}" for n in ns],rotation=25 if len(ns)>3 else 0)
                axis.xaxis.set_minor_formatter(NullFormatter());axis.yaxis.set_minor_formatter(NullFormatter())
                axis.set_title(f"{key[0]} · m/n={key[1]} · intrusion {key[2]}‰ of n")
                axis.set_xlabel("Vertices n");axis.set_ylabel(label);axis.grid(alpha=.18)
                handles,labels=axis.get_legend_handles_labels()
                if handles:axis.legend(frameon=False,fontsize=7,handlelength=3.5)
                elif kind=="work":axis.text(.5,.5,"No work/trace input supplied",ha="center",transform=axis.transAxes)
            caption={"ratios":"Ratios are paired before medians over repetitions, sampling seeds and graphs; bars are graph ranges, not confidence intervals.\nCampaigns are kept separate. Dashed line: parity; dotted line: predeclared .90 case threshold.",
                     "times":"Independent time medians use the same hierarchy as ratios, but their quotient need not equal the median paired ratio.\nInput conversion and output hash construction included; generation, certification and output destruction excluded.",
                     "work":"Same contraction_edges counter for both strategies, divided by original m. Arithmetic seed means, collected outside timing.\nVerifier edge volume and the mixed logical-work proxy are separate CSV columns; neither is CPU instructions."}[kind]
            fig.text(.02,.015,caption,fontsize=8,va="bottom")
            fig.tight_layout(rect=(0,.12 if nrows==1 else .075,1,.98))
            stem=f"{kind}_{page+1}"
            for extension in ("png","svg","pdf"):fig.savefig(output/(stem+"."+extension),dpi=180,bbox_inches="tight")
            plt.close(fig)
    pages("ratios","KKT / compacting Borůvka time")
    pages("times","Elapsed time (ms; log scale)")
    if tables["work_summary"] or tables["trace_summary"]:pages("work","Contraction input edges / original m")


def write_report(output, campaigns, tables, confirmed):
    lines=["# Continuation campaigns: all outcomes","",
        "Campaigns retain their own seed banks and timing medians. Screening selected candidates; it does not confirm them. "
        "Ratios divide matched call times before medians across repetitions, sampling seeds and graphs. "
        "Individual pairs, order strata, graph ranges and separate algorithm times remain in CSVs.","",
        "| Campaign | Role | Cases | Timed calls | Checked warmups | Case leads | Every graph leads |",
        "|---|---|---:|---:|---:|---:|---:|"]
    for c in campaigns:
        ss=c["tables"][0]
        lines.append(f'| {c["name"]} | {c["role"]} | {len(ss)} | {len(c["timing"])} | {c["checked_warmups"]} | '
                     f'{sum(r["paired_runtime_ratio"]<1 for r in ss)} | {sum(r["graph_max_ratio"]<1 for r in ss)} |')
    lines += ["","The comparison measures the whole continuation strategy: repeated production contraction versus unchanged KKT, "
        "including iterative/recursive storage lifetimes, RNG, sampling and verification. Engineered hierarchy and hierarchical-distance "
        "cases are stress tests, not representative application graphs. Counters cannot identify an unmeasured cache or allocator bottleneck.",""]
    if confirmed[1]:
        lines += ["## Predeclared confirmation","",
            "A selected group passes only when its case ratio is ≤0.90 and every graph ratio is <1 at each of its two largest "
            "tested sizes, separately in both runs. Adjacent means adjacent entries in the frozen size menu. "
            "Runs use fresh seeds and reverse manifest order; they are not pooled. This descriptive criterion is not a significance test. "
            "When a frozen selection record is supplied, its candidates, sizes, screen/manifest hashes and binary must match, and "
            "runner start timestamps must follow its freeze timestamp. These recorded timestamps complement the pre-timing git commit; "
            "they are not an independent authentication of historical order.","",
            "| Family | m/n | Intrusion ‰ of n | Selected | Two largest sizes | Numeric rule | Confirmed selected group |",
            "|---|---:|---:|---|---|---|---|"]
        for r in confirmed[1]:
            lines.append(f'| {r["family"]} | {r["density"]} | {r["intrusion_per_mille"]} | {r["selected_candidate"]} | '
                         f'{r["criterion_sizes"]} | {r["passes_numeric_rule"]} | {r["confirmed_preselected_group"]} |')
    else:lines += ["No held-out confirmation pair was supplied; all results below remain descriptive."]
    lines += ["","## Every case","",
        "| Campaign | Case | KKT / compaction [graph range] | KKT ms | Compaction ms | Individual KKT losses / pairs |",
        "|---|---|---:|---:|---:|---:|"]
    for r in tables["case_summary"]:
        lines.append(f'| {r["campaign"]} | {r["case_id"]} | {r["paired_runtime_ratio"]:.4f} '
            f'[{r["graph_min_ratio"]:.4f}, {r["graph_max_ratio"]:.4f}] | {r["kkt_median_ns"]/1e6:.3f} | '
            f'{r["compacting_boruvka_median_ns"]/1e6:.3f} | {r["kkt_slower_observations"]}/{r["paired_observations"]} |')
    for image in sorted(output.glob("*.png")):
        if re.fullmatch(r"(?:ratios|times|work)_[0-9]+\.png",image.name):
            lines += ["",f"![{image.stem}]({image.name})"]
    lines += ["","`comparison_inputs.json` records source/config/raw hashes and each runner metadata file. "
        "Across screening phases, automatic source checks cover the listed production-library files, not changed harness function bodies: "
        "the compaction wrapper and timing boundary live in `continuation_search.cpp`, whose setup/logging code may change. "
        "Their cross-screen equivalence requires the separately recorded source audit. The held-out pair requires identical full source "
        "inventories and binary hashes. "
        "FNV64 input fingerprints crosscheck labels and paired controls; they are not collision-proof equality certificates. "
        "Exact-MST pass fields are validated for every row. Build assertions and independent certificates belong to the recorded harness, "
        "and graph generation/validation are outside the timed region."]
    (output/"report.md").write_text("\n".join(lines)+"\n")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--validate-only",action="store_true")
    args=parser.parse_args()
    config=json.loads(args.config.read_text())
    campaigns,confirmation=collect(config,args.config.resolve().parent)
    tables=tagged_tables(campaigns)
    confirmed=confirmation_tables(confirmation)
    for name,rows in zip(("confirmation_cases","confirmation_groups","confirmation_graphs"),confirmed):tables[name]=rows
    metadata={"validation":"pass", "config":{"path":str(args.config.resolve()),"sha256":sha256(args.config)},
              "comparison_source_sha256":sha256(Path(__file__)), "base_analysis_source_sha256":sha256(Path(base.__file__)),
              "cross_screen_checked_library_files":PRODUCTION_FILES,
              "cross_screen_harness_body_equivalence":"requires separate source audit when harness hashes differ",
              "criterion":{"maximum_case_ratio":THRESHOLD,"every_graph_ratio_strictly_below":1,
                           "sizes":"two largest tested sizes per group", "both_runs_required":True},"campaigns":[]}
    if "selection_file" in config:
        selection_path=(args.config.resolve().parent/config["selection_file"]).resolve()
        metadata["frozen_selection"]={"path":str(selection_path),"sha256":sha256(selection_path)}
    for c in campaigns:
        metadata["campaigns"].append({"name":c["name"],"role":c["role"],"graph_seeds":c["graph_seeds"],
            "sampling_seeds":c["sampling_seeds"],"repetitions":c["repetitions"],"warmups":c["warmups"],
            "timing_rows":len(c["timing"]),"checked_warmups":c["checked_warmups"],"work_rows":len(c["work"]),
            "trace_graphs":len(c["traces"]),"cases":list(c["cases"]),
            "inputs":{key:{"path":str(path),"sha256":sha256(path)} for key,path in c["paths"].items()}})
    if args.validate_only:
        print(json.dumps(metadata,indent=2));return
    args.output_dir.mkdir(parents=True,exist_ok=True)
    # Only remove named plot pages owned by this tool, so reruns with fewer
    # groups or absent work do not retain pictures from a previous campaign.
    for path in args.output_dir.iterdir():
        if re.fullmatch(r"(?:ratios|times|work)_[0-9]+\.(?:png|svg|pdf)",path.name):path.unlink()
    write_tables(args.output_dir,tables)
    plots(args.output_dir,campaigns,tables)
    write_report(args.output_dir,campaigns,tables,confirmed)
    (args.output_dir/"comparison_inputs.json").write_text(json.dumps(metadata,indent=2)+"\n")
    print(f"Validated {len(campaigns)} campaigns; wrote {args.output_dir}")


if __name__ == "__main__":
    try:main()
    except (ValueError,OSError,KeyError,TypeError) as error:
        print("continuation comparison: "+str(error),file=sys.stderr)
        sys.exit(1)
