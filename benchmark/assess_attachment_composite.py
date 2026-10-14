#!/usr/bin/env python3
"""Assess A versus interrupted-B-plus-declared-recovery, never relabel failed B.

This NEW postprocessor accepts only an independently validated 60-child prefix
and the exact remaining 12 successful recovery children. It rereads all native
evidence, retains source-part identities, and recomputes the declared medians.
No solvers are launched, observations replaced, or original captures rewritten.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
import statistics
import subprocess

import analyze_mst_search as analysis
import assess_attachment_confirmation as rule
import assess_attachment_recovery as prefix
import run_mst_search as capture

require, same, track = rule.require, rule.same, rule.track


def records(rows, diagnostics, campaign, order, expected):
    """Independent explicit grid loops: pair first, never flatten repetitions."""
    lookup = {}
    for row in rows:
        key = tuple(row[k] for k in prefix.ROW_KEY)
        require(key not in lookup and row["validation"] == "pass", "duplicate or failed composite call")
        same({key: row[key] for key in rule.IDENTITY}, expected[row["case_id"]], "composite case identity")
        lookup[key] = row
    wanted = {(case,g,s,phase,rep,algorithm) for case,g,s in itertools.product(order,rule.GRAPHS,rule.SAMPLES)
              for phase,count in (("warmup",1),("timed",5)) for rep,algorithm in itertools.product(range(count),rule.ALGORITHMS)}
    same(set(lookup), wanted, "full composite call grid")
    pairs, graphs, cases = [], [], []
    for case,metric,competitor in itertools.product(order,rule.METRICS,rule.COMPETITORS):
        graph_medians, all_values = [], []
        for g in rule.GRAPHS:
            sample_medians, graph_values = [], []
            for s in rule.SAMPLES:
                values = []
                for rep in range(5):
                    numerator = lookup[(case,g,s,"timed",rep,"kkt")][rule.METRICS[metric]]
                    denominator = lookup[(case,g,s,"timed",rep,competitor)][rule.METRICS[metric]]
                    require(type(numerator) is int and type(denominator) is int and numerator > 0 and denominator > 0,
                            "invalid paired duration")
                    ratio = numerator/denominator; values.append(ratio)
                    pairs.append({"campaign":campaign,**expected[case],"metric":metric,"competitor":competitor,
                                  "graph_seed":g,"kkt_seed":s,"repetition":rep,"kkt_ns":numerator,
                                  "competitor_ns":denominator,"kkt_over_competitor":ratio})
                sample_medians.append(statistics.median(values)); graph_values.extend(values)
            median = statistics.median(sample_medians); graph_medians.append(median); all_values.extend(graph_values)
            graphs.append({"campaign":campaign,**expected[case],"metric":metric,"competitor":competitor,
                           "graph_seed":g,"median_paired_ratio":median,"trial_min_ratio":min(graph_values),
                           "trial_max_ratio":max(graph_values),"individual_wins":sum(v<1 for v in graph_values),
                           "individual_losses":sum(v>1 for v in graph_values),"individual_ties":sum(v==1 for v in graph_values),
                           "pairs":len(graph_values)})
        cases.append({"campaign":campaign,**expected[case],"metric":metric,"competitor":competitor,
                      "median_paired_ratio":statistics.median(graph_medians),"graph_min_ratio":min(graph_medians),
                      "graph_max_ratio":max(graph_medians),"trial_min_ratio":min(all_values),"trial_max_ratio":max(all_values),
                      "individual_wins":sum(v<1 for v in all_values),"individual_losses":sum(v>1 for v in all_values),
                      "individual_ties":sum(v==1 for v in all_values),"graph_seeds":3,"pairs":len(all_values)})
    same(len(diagnostics),len(rows),"all clock diagnostics retained")
    same({tuple(row[k] for k in prefix.ROW_KEY) for row in diagnostics},wanted,"diagnostic grid")
    require(all(row["excluded"] is False for row in diagnostics), "excluded clock observation")
    return {"campaign":campaign,"cases":cases,"graphs":graphs,"pairs":pairs,
            "diagnostics":[{"campaign":campaign,**row} for row in prefix.diagnostic_rows(diagnostics)],
            "fingerprints":capture.check_fingerprints(rows)}


def check_tables(independent, tables):
    for kind, name, keys in (("cases","comparisons",("case_id","metric","competitor")),
                             ("graphs","graph_comparisons",("case_id","metric","competitor","graph_seed")),
                             ("pairs","paired_ratios",("case_id","metric","competitor","graph_seed","kkt_seed","repetition"))):
        actual = {tuple(row[k] for k in keys):row for row in tables[name]}
        expected = {tuple(row[k] for k in keys):{k:v for k,v in row.items() if k!="campaign"} for row in independent[kind]}
        same(actual,expected,"independent paired aggregation "+kind)


def check_parts(parts, rows):
    same(len(parts),2160,"source-part count")
    for index,(part,row) in enumerate(zip(parts,rows)):
        same({k:part[k] for k in prefix.ROW_KEY},{k:row[k] for k in prefix.ROW_KEY},"source-part row identity")
        same(part["original_child_index"],index//30+1,"source-part original child position")
        same(part["source_part"],"interrupted_prefix" if index<1800 else "recovery_tail","source-part partition")
    same(len({tuple(row[k] for k in prefix.ROW_KEY) for row in parts}),2160,"disjoint source-part identities")


def bind_power(path, inputs, checked_calls, schema, raw_metadata=None):
    record = analysis.read_json(track(path,inputs))
    for field,value in (("schema",schema),("validation","pass"),("checked_calls",checked_calls),
                        ("rows_removed",0),("rows_adjusted",0)):
        analysis.equal(record,field,value,"source-part power audit")
    if raw_metadata is not None:
        same(record["input_sha256"].get(str(raw_metadata)),rule.sha(raw_metadata),"power/metadata binding")
    if schema=="mst_search_power_audit_v1":
        same(record.get("power_event_parser"),"wake_requests_excluded_v1","corrected power-event parser")
        corrected=Path(__file__).with_name("audit_attachment_recovery_power.py").resolve()
        underlying=Path(__file__).with_name("audit_mst_search_power.py").resolve()
        track(corrected,inputs,record.get("script_sha256"))
        track(underlying,inputs,record.get("underlying_auditor_sha256"))
    # Full machine logs remain unpublished. Bind the published scoped audit and
    # associations; its historical complete-log hashes are retained verbatim.
    associations=path.parent/"call_power_associations.csv"
    track(associations,inputs,record["output_sha256"]["call_power_associations.csv"])
    same(len(rule.read_csv(associations)),checked_calls,"power association count")
    return record


def compose(root,folder,prefix_dir,tail_csv,tail_power,output,composite_dir):
    require(not output.exists() and not composite_dir.exists(),"refusing to overwrite assessment outputs")
    data=prefix.load_prefix(root,folder,prefix_dir);inputs=data["inputs"]
    track(__file__,inputs);track(folder/"ATTACHMENT_RECOVERY.md",inputs)
    recovery_manifest=track(folder/"attachment-confirmation-b-recovery.csv",inputs)
    expected,plans=data["expected"],data["plans"]
    # A stays on its original, successful, frozen analysis path.
    a=rule.load_campaign(root,folder,"a",expected,plans["a"],inputs)
    a_supplement=bind_power(folder/"attachment-confirmation-a-transition-power-audit/audit.json",inputs,2160,
                           "mst_search_power_audit_v1",folder/"attachment-confirmation-a-timing.json")
    a["power_audit"]={"original":a["power_audit"],"corrected_transition_supplement":a_supplement}
    a_info,a_specs,a_rows,a_diagnostics,_,a_inputs=analysis.load(folder/"attachment-confirmation-a-timing.csv")
    rule.bind(a_inputs,inputs)
    a_independent=records(a_rows,a_diagnostics,"a",plans["a"],expected)
    check_tables(a_independent,analysis.aggregate(a_rows))
    for kind in ("cases","graphs","pairs"):
        key=lambda row:tuple(str(row.get(k,"")) for k in (*rule.IDENTITY,"metric","competitor","graph_seed","kkt_seed","repetition"))
        same(sorted(a[kind],key=key),sorted(a_independent[kind],key=key),"A strict/independent "+kind)
    prefix_power=bind_power(folder/"attachment-confirmation-b-prefix-power-audit/audit.json",inputs,1800,
                            "interrupted_prefix_power_audit_v1",folder/"attachment-confirmation-b-timing.json")
    import recover_mst_search as recovery
    recovery.install_analysis()
    tail_info,tail_specs,tail_rows,tail_diagnostics,tail_resources,tail_inputs=analysis.load(tail_csv)
    rule.bind(tail_inputs,inputs)
    track(recovery.__file__,inputs,tail_info["python_source_sha256"][str(Path(recovery.__file__).resolve())])
    recovery_revision=tail_info["revision"]
    # Bind the declaration/remaining manifest to the repository revision recorded
    # BEFORE native recovery, rather than accepting a post-outcome edited plan.
    for path in (folder/"ATTACHMENT_RECOVERY.md",recovery_manifest,Path(recovery.__file__).resolve()):
        original=subprocess.check_output(["git","show",recovery_revision+":"+path.relative_to(root).as_posix()],cwd=root)
        import hashlib
        track(path,inputs,hashlib.sha256(original).hexdigest())
    for field in prefix.SOURCE_FIELDS:
        same(a_info[field],data["info"][field],"A/prefix "+field)
        same(tail_info[field],data["info"][field],"tail/prefix "+field)
    same(data["info"]["python_source_sha256"],a_info["python_source_sha256"],"A/prefix frozen helper inventory")
    for path,digest in data["info"]["python_source_sha256"].items():
        same(tail_info["python_source_sha256"].get(path),digest,"tail frozen helper "+path)
    same(list(tail_specs),plans["b"][10:],"exact remaining case order")
    same(tail_info["manifest"],str(recovery_manifest),"recovery manifest path")
    same(tail_info["manifest_sha256"],rule.sha(recovery_manifest),"recovery manifest hash")
    for field,value in (("graph_seeds",list(rule.GRAPHS)),("sampling_seeds",list(rule.SAMPLES)),
                        ("algorithms",list(rule.ALGORITHMS)),("repetitions",5),("warmups",1),("checked_rows",360)):
        analysis.equal(tail_info,field,value,"tail protocol")
    require(len(tail_info["captures"])==12,"tail is not exactly 12 children")
    require(analysis.timestamp(tail_info["started_utc"])>analysis.timestamp(data["info"]["finished_utc"]),
            "recovery did not follow finalized interruption")
    tail_power_record=bind_power(tail_power,inputs,360,"mst_search_power_audit_v1",tail_csv.with_suffix(".json"))
    parts=list(data["source_parts"])
    for index,item in enumerate(tail_info["captures"],61):
        child_rows,_=capture.check_rows(Path(item["csv"]),tail_specs[item["case_id"]],item["graph_seed"],item["kkt_seed"],5,1)
        parts.extend({**{k:row[k] for k in prefix.ROW_KEY},"source_part":"recovery_tail","original_child_index":index,
                      "source_csv":item["csv"],"source_csv_sha256":item["output_sha256"]} for row in child_rows)
    rows=data["rows"]+tail_rows;diagnostics=data["diagnostics"]+tail_diagnostics
    check_parts(parts,rows)
    b=records(rows,diagnostics,"b",plans["b"],expected)
    same(a["fingerprints"],b["fingerprints"],"A/composite captured input fingerprints")
    b_metadata={"schema":"attachment_composite_metadata_v1","execution_status":"interrupted_then_recovered",
                "original_b_capture_validation":"failed","original_b_controller_validation":"failed",
                "frozen_execution_completed":False,"case_order":plans["b"],"graph_seeds":list(rule.GRAPHS),
                "sampling_seeds":list(rule.SAMPLES),"algorithms":list(rule.ALGORITHMS),"repetitions":5,"warmups":1,
                "checked_rows":2160,"checked_timed_rows":1800,"checked_warmup_rows":360,
                "flagged_calls":sum(bool(row["diagnostic_flags"]) for row in diagnostics),
                "capture_clock_flags":{"interrupted_prefix":data["info"]["capture_clock_flags"],
                                       "recovery_tail":tail_info["capture_clock_flags"]},
                **{field:data["info"][field] for field in prefix.SOURCE_FIELDS}}
    b.update(metadata=b_metadata,power_audit={"interrupted_prefix":prefix_power,"recovery_tail":tail_power_record})
    results=rule.assess([a,b]);coupling=rule.topology_coupling([a,b]);tables=analysis.aggregate(rows);check_tables(b,tables)
    prefix.check_inputs(inputs)
    composite_dir.mkdir(parents=True);output.mkdir(parents=True)
    for name,values in tables.items():analysis.write_csv(composite_dir/(name+".csv"),values)
    for name,values in (("validated_calls",rows),("call_diagnostics",prefix.diagnostic_rows(diagnostics)),("source_parts",parts)):
        analysis.write_csv(composite_dir/(name+".csv"),values)
    (composite_dir/"README.md").write_text("# Interrupted B plus separately declared recovery\n\n"
        "This is a complete numerical data set assembled from 60 completed native children in failed campaign B "
        "and exactly 12 previously unstarted children in the declared monitor recovery. Original B remains failed; "
        "this is not a successful frozen execution. All 2,160 calls, including 360 warmups, are retained in original "
        "case/seed order. source_parts.csv identifies every raw child and its hash. No observation was rerun, "
        "replaced, corrected, or removed. Timing medians use native call clocks, never stalled wrapper durations. "
        "Monitoring changed between the two parts; CPU agreement and numerical thresholds do not establish a quiet host.\n")
    composite_provenance={"schema":"attachment_confirmation_composite_v1","validation":"pass",
                          "validation_scope":"complete native numerical evidence; failed original execution is retained",
                          "recovery_declaration_revision":recovery_revision,
                          "composite_metadata":b_metadata,"source_capture_metadata":{"interrupted_prefix":data["info"],"recovery_tail":tail_info},
                          "source_parts":{"interrupted_prefix":{"validated_prefix_dir":str(prefix_dir),
                              "original_failed_csv":str(folder/"attachment-confirmation-b-timing.csv"),
                              "original_child_positions":[1,60],"native_calls":1800},
                              "recovery_tail":{"raw_csv":str(tail_csv),"original_child_positions":[61,72],"native_calls":360}},
                          "original_controller_metadata":data["controller"],"input_sha256":inputs,
                          "rows_removed":0,"rows_adjusted":0,"native_children_rerun":0,
                          "derived_sha256":{p.name:rule.sha(p) for p in composite_dir.iterdir()}}
    prefix.save(composite_dir/"provenance.json",composite_provenance)
    track(composite_dir/"provenance.json",inputs)
    for kind in ("cases","graphs","pairs","diagnostics"):
        analysis.write_csv(output/(kind+".csv"),[row for c in (a,b) for row in c[kind]])
    record={"schema":"attachment_recovery_numerical_assessment_v1","validation":"pass",
            "original_frozen_execution_success":False,"original_b_capture_validation":"failed",
            "criterion_scope":"Declared numerical rule on complete A and interrupted-B-plus-recovery, separately; not protocol success",
            "criterion_results":results,"shared_control_size_topology_coupling":coupling,
            "all_four_competitors_pass_by_family":{family:all(r["declared_upper_size_advantage_pass"] for r in results if r["family"]==family) for family in rule.FAMILIES},
            "counts":{"total_calls":4320,"timed_calls":3600,"warmup_calls":720,"a_children":72,"b_prefix_children":60,"recovery_children":12},
            "campaigns":[{"campaign":c["campaign"],"flagged_calls":c["metadata"]["flagged_calls"],
                          "capture_clock_flags":c["metadata"]["capture_clock_flags"],"power_audit":c["power_audit"]} for c in (a,b)],
            "rows_removed":0,"rows_adjusted":0,"campaigns_pooled":False,"infer_beyond_tested_range":False}
    prefix.save(output/"assessment.json",record)
    text=rule.markdown(results,[a,b],coupling)
    text=text.replace("# Frozen attachment confirmation assessment","# Numerical assessment after the declared recovery")
    text=text.replace("Both complete campaigns are retained separately.","A completed its frozen execution. Original B failed; its 60 completed native children are combined only with the separately declared remaining 12 recovery children. The original B capture and controller remain failed. This assessment concerns the numerical rule, not successful execution of the original protocol. Monitoring changed for the recovery and broad B disturbance remains a limitation. A and composite B are retained separately.")
    text=text.replace("## Campaign B","## Interrupted B plus recovery")
    text=text.replace("This assessor binds existing successful capture/analysis artifacts and independently recomputes the paired aggregation; the underlying strict analyzer remains responsible for native certificate, schedule and clock-schema validation.","This assessor rereads the completed A capture, independently validates all 60 interrupted-prefix children, validates the 12-child recovery through its separate strict adapter, and independently recomputes the paired aggregation. The original strict assessor continues to reject failed B.")
    text=text.replace("Power-audit outputs are retained as previously computed, not rerun here.","Scoped power audits for A, the interrupted prefix, and the recovery tail are retained separately, with no row corrections or exclusions.")
    (output/"README.md").write_text(text)
    prefix.save(output/"provenance.json",{"schema":"attachment_recovery_assessor_provenance_v1","validation":"pass",
                 "original_frozen_execution_success":False,"input_sha256":inputs,
                 "derived_sha256":{p.name:rule.sha(p) for p in output.iterdir()},"counts":record["counts"]})
    print(json.dumps({"validation":"pass","original_b_validation":"failed","calls":4320,"criteria":8}))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("repo-root","prefix-dir","tail-csv","tail-power-audit","output-dir","composite-dir"):
        parser.add_argument("--"+name,type=Path,required=True)
    args=parser.parse_args()
    try:
        root=args.repo_root.resolve(strict=True);folder=root/"benchmark/results/search-2026-10-13"
        compose(root,folder,args.prefix_dir.resolve(strict=True),args.tail_csv.resolve(strict=True),
                args.tail_power_audit.resolve(strict=True),args.output_dir.resolve(),args.composite_dir.resolve())
    except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as error:parser.exit(2,"attachment composite assessment: "+str(error)+"\n")


if __name__=="__main__":main()
