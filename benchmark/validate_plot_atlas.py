#!/usr/bin/env python3
"""Bounded post-capture checks, without Matplotlib rendering.

Requires both completed, strictly analyzed confirmations and explicit timing
release. Does not execute native binaries, generate fixtures, or edit inputs.
Temporary mutations are synthetic negative tests, not benchmark observations.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "module has no source loader")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def rejected(function, fragment):
    try:
        function()
    except ValueError as error:
        require(fragment in str(error), f"wrong rejection: {error}; expected {fragment}")
    else:
        raise AssertionError("accepted invalid input: " + fragment)


def contained(bounds, values, context):
    low, high = bounds
    require(math.isfinite(low) and math.isfinite(high) and low < high, "invalid bounds: "+context)
    require(all(low <= value <= high for value in values), "clipped endpoint: "+context)


class Snapshot:
    def __init__(self, values, directories):
        self.values = {str(Path(folder).resolve()):data for (_,folder),data in zip(directories,values)}
    def load_campaign(self, folder):
        return copy.deepcopy(self.values[str(Path(folder).resolve())])
    def read_json(self, _path):
        return {}


def check_plots(plot, helper, campaigns, directories):
    checks = []
    for families in (plot.SELECTED, plot.CONTROLS):
        expected = {(c["role"],family,metric,row["case_id"]) for c in campaigns
                    for family in families for metric in ("wall","cpu") for row in plot.points(c,family,metric)}
        actual = plot.selected_rows(campaigns, families)
        keys = {(r["campaign"],r["family"],r["metric"],r["case_id"]) for r in actual}
        require(keys == expected and len(actual) == len(keys), "selected/control rows dropped or duplicated")
        values = [.9,1.]
        for c in campaigns:
            for family in families:
                for metric in ("wall","cpu"):
                    for row in plot.points(c,family,metric):
                        values += ([row["graph_min_ratio"],row["graph_max_ratio"]] if c["is_confirmation"]
                                   else [row["median_paired_ratio"]])
        contained(plot.ratio_limits(campaigns,families), values, "real compact ranges")
        # Exercise tiny positive ratios and enormous ranges in BOTH selected
        # families and controls, without editing any actual artifact.
        changed = copy.deepcopy(campaigns)
        for c in changed[2:]:
            for family in families:
                for metric in ("wall","cpu"):
                    point = plot.points(c,family,metric)[-1]
                    point["graph_min_ratio"] = 1e-12
                    point["graph_max_ratio"] = 1e9
        contained(plot.ratio_limits(changed,families), [1e-12,1e9,.9,1.], "extreme compact ranges")
    checks.append("selected/control coverage and real/extreme graph-range containment")
    # Check the actual complete-appendix limit function against EVERY solver,
    # clock, group and campaign. The compact figure intentionally has fewer
    # visible comparisons and cannot substitute for this check.
    groups = set().union(*(set(c["groups"]) for c in campaigns))
    for group in groups:
        for metric in ("wall","cpu"):
            for ratios in (False,True):
                _, bounds = helper.limits(campaigns,group,metric,ratios)
                values = []
                for c in campaigns:
                    for spec in c["groups"].get(group,[]):
                        for algorithm in helper.ALGORITHMS[1:] if ratios else helper.ALGORITHMS:
                            row = c["comparisons" if ratios else "summaries"][(spec["case_id"],metric,algorithm)]
                            suffix,factor = ("ratio",1.) if ratios else ("ns",1e-9)
                            values.extend([row["trial_min_"+suffix]*factor,row["trial_max_"+suffix]*factor])
                contained(bounds,values,"full appendix real trial ranges")
    changed = copy.deepcopy(campaigns)
    spec = changed[-1]["groups"][("leaf_hierarchy4",16)][-1]
    for metric in ("wall","cpu"):
        for algorithm in helper.ALGORITHMS[1:]:
            row = changed[-1]["comparisons"][(spec["case_id"],metric,algorithm)]
            row["trial_min_ratio"],row["trial_max_ratio"] = 1e-12,1e9
        for algorithm in helper.ALGORITHMS:
            row = changed[-1]["summaries"][(spec["case_id"],metric,algorithm)]
            row["trial_min_ns"],row["trial_max_ns"] = 1,10**18
        contained(helper.limits(changed,("leaf_hierarchy4",16),metric,True)[1],[1e-12,1e9],"extreme all-comparator ratios")
        contained(helper.limits(changed,("leaf_hierarchy4",16),metric,False)[1],[1e-9,1e9],"extreme all-solver runtimes")
    checks.append("full appendix real/extreme individual-trial ranges for all competitors and clocks")
    mutations = [
        (lambda c:c[-1]["groups"].pop(("leaf_random4",16)), "missing required selected/control family"),
        (lambda c:c[-1]["groups"][("leaf_hierarchy4",16)].pop(), "selected size grid"),
        (lambda c:c[-1]["metadata"].update(case_order=list(c[-2]["metadata"]["case_order"])), "reversed-case-order protocol"),
        (lambda c:c[-1]["metadata"].update(binary_sha256="0"*64), "native source/binary/profile differs"),
        (lambda c:c[-1]["metadata"].update(graph_seeds=[5009]), "confirmation seed/repetition protocol"),
    ]
    for mutate,fragment in mutations:
        changed = copy.deepcopy(campaigns); mutate(changed)
        rejected(lambda:plot.load_all(Snapshot(changed,directories),directories),fragment)
    checks.append("five compact-figure protocol rejection gates")
    return checks


def check_atlas(atlas, repo, folder):
    datasets, certificates, _ = atlas.load_inputs(repo,folder)
    require(len(certificates) == 4 and all(r["validation"] == "pass" for r in certificates), "certificate gate failed")
    context = atlas.context_ids(datasets[0])
    first_positions = atlas.coordinates(datasets[0])
    require(len(first_positions[0]) == len(first_positions[1]) == 1024, "coordinate count differs")
    require(all(math.isfinite(v) for points in first_positions for point in points for v in point), "nonfinite coordinates")
    for data in datasets:
        require(atlas.coordinates(data) == first_positions, "weight changes altered shared coordinates")
        require(atlas.context_ids(data) == context, "weight/MST changes altered context selection")
        partition = atlas.visible_partition(data,context)
        all_ids,mst = {edge["id"] for edge in data["edges"]},set(data["certified_mst_ids"])
        require(partition["mst"] == mst and len(mst) == 1023, "complete MST is not visible")
        require(len(partition["local_mst"]) == 768 and len(partition["core_mst"]) == 255, "local/core MST counts differ")
        require(partition["visible"] <= all_ids and partition["visible"] == mst | context, "invented/missing visible ID")
        require(partition["hidden"] == all_ids - partition["visible"], "hidden ledger differs")
        require(len(partition["visible"])+len(partition["hidden"]) == 16384, "edge accounting differs")
        require(len(partition["extra"]) == len(context)-len(context & mst), "context overlap double counted")
    rejected(lambda:atlas.visible_partition(datasets[0],context | {16384}),"invented edge ID")
    rejected(lambda:atlas.visible_partition(datasets[0],context | {0}),"local edge")
    # All following mutations live in a disposable directory. The authentic
    # graph exports and their provenance are never rewritten.
    files = [f+".json" for f in atlas.FAMILIES]+["exports.json","render_validation.json"]
    def save(path,data):
        path.write_text(json.dumps(data,indent=2)+"\n")
    def refresh_manifest_link(target):
        path = target/"render_validation.json"; prior = atlas.strict_json(path)
        prior["native_exports_provenance_sha256"] = sha(target/"exports.json"); save(path,prior)
    def mutate_manifest(target):
        path = target/"exports.json"; data = atlas.strict_json(path)
        data["validation"] = "failed"; save(path,data)
    def mutate_exit(target):
        path = target/"exports.json"; data = atlas.strict_json(path)
        data["records"][0]["exit_status"] = 1; save(path,data); refresh_manifest_link(target)
    def mutate_binding(target):
        path = target/"render_validation.json"; data = atlas.strict_json(path)
        data["records"][0]["input_sha256"] = "0"*64; save(path,data)
    def mutate_mst(target):
        path = target/(atlas.FAMILIES[0]+".json"); data = atlas.strict_json(path)
        data["certified_mst_ids"].pop(); save(path,data)
    def mutate_labels(target):
        # A consistently relabelled, still valid certified graph must fail the
        # paired topology/label gate even with synthetic hash bindings updated.
        validator = sys.modules["render_attachment_view"]
        family = atlas.FAMILIES[-1]; path = target/(family+".json")
        old = sha(path); data = atlas.strict_json(path)
        change = lambda label:1-label if label in (0,1) else label
        data["original_to_label"] = [change(label) for label in data["original_to_label"]]
        for edge in data["edges"]:
            edge["from"],edge["to"] = change(edge["from"]),change(edge["to"])
        for name,weighted in (("input_fingerprint",True),("topology_fingerprint",False)):
            data[name] = validator.fingerprint(data["edges"],data["n"],weighted)
        validator.validate_export(data); save(path,data); new = sha(path)
        manifest_path = target/"exports.json"; manifest = atlas.strict_json(manifest_path)
        for row in manifest["records"]:
            if row["stdout_sha256"] == old:
                row["stdout_sha256"] = new
        save(manifest_path,manifest)
        prior_path = target/"render_validation.json"; prior = atlas.strict_json(prior_path)
        for row in prior["records"]:
            if row["family"] == family:
                row["input_sha256"] = new
        save(prior_path,prior); refresh_manifest_link(target)
    negatives = [(mutate_manifest,"native export provenance is not successful"),
                 (mutate_exit,"one successful native export"),
                 (mutate_binding,"export changed after prior validation"),
                 (mutate_mst,"MST does not contain n-1 IDs"),
                 (mutate_labels,"paired labels, topology or edge order differ")]
    for mutate,fragment in negatives:
        with tempfile.TemporaryDirectory(prefix="attachment-atlas-smoke-") as directory:
            target = Path(directory)
            for name in files:
                shutil.copyfile(folder/name,target/name)
            mutate(target)
            rejected(lambda:atlas.load_inputs(repo,target),fragment)
    return ["four real independent Python cycle certificates and shared coordinates/context",
            "exact visible/hidden/MST/context ID partitions and two invented/local ID rejections",
            "five synthetic provenance/certificate/paired-topology rejection gates"]


def check_composite(plot, helper, study, campaign):
    folder = campaign["directory"]
    assessment = study/"attachment-confirmation-recovery-assessment"
    require(campaign["display_label"] == "B interrupted + recovery"
            and len(campaign["source_children"]) == 72, "composite status/child coverage differs")
    # The unchanged generic loader must continue to reject this new evidence
    # type, and the failed original B must never become a successful capture.
    rejected(lambda:helper.load_campaign(folder), "expected complete validated")
    with tempfile.TemporaryDirectory(prefix="composite-plot-checks-") as temporary:
        target = Path(temporary).resolve()/"composite"; target.mkdir()
        audit = Path(temporary).resolve()/"assessment"; audit.mkdir()
        for source in folder.iterdir():
            if source.is_file(): shutil.copyfile(source,target/source.name)
        for source in assessment.iterdir():
            if source.is_file(): shutil.copyfile(source,audit/source.name)
        original = helper.read_json(target/"provenance.json")
        audit_original = helper.read_json(audit/"provenance.json")
        def save(path,data): path.write_text(json.dumps(data,indent=2)+"\n")
        def bind(provenance):
            save(target/"provenance.json",provenance)
            record = copy.deepcopy(audit_original)
            record["input_sha256"].pop(str(folder/"provenance.json"),None)
            record["input_sha256"][str(target/"provenance.json")] = sha(target/"provenance.json")
            save(audit/"provenance.json",record)
        bind(original)
        loaded = plot.load_composite(helper,target,audit)
        require(loaded["comparisons"] == campaign["comparisons"]
                and loaded["summaries"] == campaign["summaries"], "bounded copy changed actual derived values")
        negatives = [
            (lambda p:p.update(schema="mst_search_analysis_v1"), "expected validated interrupted-B composite"),
            (lambda p:p["composite_metadata"].update(frozen_execution_completed=True), "retain failed original B"),
            (lambda p:p["source_capture_metadata"]["interrupted_prefix"].update(validation="pass"), "original/tail status"),
            (lambda p:p.update(native_children_rerun=1), "reran observations"),
            (lambda p:p["source_parts"]["interrupted_prefix"].update(native_calls=1770), "source split differs"),
        ]
        for mutate,fragment in negatives:
            changed = copy.deepcopy(original); mutate(changed); bind(changed)
            rejected(lambda:plot.load_composite(helper,target,audit),fragment)
        # Refresh all synthetic hashes, so this reaches semantic row coverage
        # instead of merely detecting changed bytes.
        import csv
        path = target/"comparisons.csv"
        with path.open(newline="") as stream:
            reader=csv.DictReader(stream); fields=reader.fieldnames; rows=list(reader)
        with path.open("w",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
            writer.writerows([r for r in rows if r["competitor"] != "prim"])
        changed=copy.deepcopy(original); changed["derived_sha256"][path.name]=sha(path); bind(changed)
        rejected(lambda:plot.load_composite(helper,target,audit), "omits a case/clock/comparator")
        shutil.copyfile(folder/path.name,path)
        path=target/"source_parts.csv"
        with path.open(newline="") as stream:
            reader=csv.DictReader(stream);fields=reader.fieldnames;rows=list(reader)
        rows[0]["source_part"]="recovery_tail"
        with path.open("w",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
        changed=copy.deepcopy(original);changed["derived_sha256"][path.name]=sha(path);bind(changed)
        rejected(lambda:plot.load_composite(helper,target,audit), "invalid part")
    return ["actual composite/assessment source bindings and all 72 children; generic loader rejects composite",
            "seven synthetic composite status/provenance/comparator/child-ledger rejection gates"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root",type=Path,required=True)
    parser.add_argument("--draft-dir",type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--phase",choices=("all","atlas","plot-logic","composite"),default="all",
                        help="plot-logic uses an explicitly synthetic A-copy only to test code; never renders or reports B outcomes")
    args = parser.parse_args()
    try:
        sys.dont_write_bytecode = True
        require(not args.output.exists(), "refusing to overwrite validation evidence")
        repo = args.repo_root.resolve(strict=True)
        study = repo/"benchmark/results/search-2026-10-13"
        plot_path,atlas_path = (args.draft_dir/name for name in ("plot_confirmation_summary.py","render_attachment_atlas.py"))
        plot,atlas = module("summary_under_test",plot_path),module("atlas_under_test",atlas_path)
        helper = plot.load_plot_helper(repo)
        directories = [("pilot",study/"attachment-analysis"),("large",study/"attachment-large-analysis"),
                       ("confirmation_a",study/"attachment-confirmation-a-analysis"),
                       ("confirmation_b",study/"attachment-confirmation-b-analysis")]
        checks, provenance_directories = [], []
        if args.phase != "atlas":
            if args.phase == "composite":
                directories[-1] = ("confirmation_b",study/"attachment-confirmation-b-composite-analysis")
                campaigns = plot.load_all(helper,directories,True,study/"attachment-confirmation-recovery-assessment")
                checks += check_composite(plot,helper,study,campaigns[-1])
                provenance_directories = directories
            elif args.phase == "plot-logic":
                # The interrupted original B remains failed. This synthetic
                # in-memory B is test scaffolding, never a successful capture.
                real = [helper.load_campaign(folder) for _,folder in directories[:3]]
                synthetic = copy.deepcopy(real[-1])
                synthetic["metadata"]["case_order"] = list(reversed(synthetic["metadata"]["case_order"]))
                campaigns = plot.load_all(Snapshot([*real,synthetic],directories),directories)
                provenance_directories = directories[:3]
            else:
                campaigns = plot.load_all(helper,directories)
                provenance_directories = directories
            checks += check_plots(plot,helper,campaigns,directories)
        if args.phase not in ("plot-logic","composite"):
            checks += check_atlas(atlas,repo,study/"attachment-views-d16")
        source_paths = (Path(__file__),plot_path,atlas_path,Path(helper.__file__),repo/"benchmark/render_attachment_view.py")
        result = {"schema":"attachment_plot_atlas_checks_v1","validation":"pass","checks":checks,
                  "source_sha256":{str(p.resolve()):sha(p) for p in source_paths},
                  "phase":args.phase,"synthetic_B_for_figure_logic":args.phase == "plot-logic",
                  "campaign_analysis_provenance_sha256":{str((folder/"provenance.json").resolve()):sha(folder/"provenance.json") for _,folder in provenance_directories},
                  "native_execution":False,"matplotlib_imported":"matplotlib" in sys.modules,
                  "figures_rendered":False,"visual_qa":"not performed by this script",
                  "synthetic_mutations":"temporary negative tests only; not measurement observations"}
        require(not result["matplotlib_imported"], "validation unexpectedly imported Matplotlib")
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open("x") as stream:
            stream.write(json.dumps(result,indent=2)+"\n")
        print(json.dumps({"validation":"pass","check_groups":len(checks),"visual_qa":"pending"}))
    except (AssertionError,ValueError,OSError,KeyError,TypeError,ImportError) as error:
        parser.exit(2,"plot/atlas validation: "+str(error)+"\n")


if __name__ == "__main__":
    main()
