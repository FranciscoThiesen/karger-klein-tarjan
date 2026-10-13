#!/usr/bin/env python3
"""Replay presentation guards on copied, completed comparison tables.

This checks the report figure's input guards, not the raw timing validator or
MST implementation. No plots are rendered and source evidence is never edited.
"""
import argparse
import csv
import json
from pathlib import Path
import shutil
import tempfile

import plot_continuation_report as report


def rewrite_table(folder, name, mutate):
    path=folder/name
    with path.open(newline="") as stream:
        reader=csv.DictReader(stream)
        fields=reader.fieldnames
        rows=list(reader)
    mutate(rows)
    with path.open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields)
        writer.writeheader();writer.writerows(rows)


def rewrite_metadata(folder, mutate):
    path=folder/"comparison_inputs.json"
    data=json.loads(path.read_text())
    mutate(data)
    path.write_text(json.dumps(data))


def rewrite_config(folder, mutate, update_digest=True):
    path=folder/"comparison_inputs.json"
    metadata=json.loads(path.read_text())
    config=json.loads(Path(metadata["config"]["path"]).read_text())
    mutate(config)
    copied=folder/"copied_config.json"
    copied.write_text(json.dumps(config))
    metadata["config"]["path"]=str(copied)
    if update_digest:metadata["config"]["sha256"]=report.digest(copied)
    path.write_text(json.dumps(metadata))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison-dir",type=Path,required=True)
    args=parser.parse_args()
    source=args.comparison_dir.resolve()
    names=("comparison_inputs.json","confirmation_cases.csv","case_summary.csv")
    results=[]
    report.load_inputs(source,"million","sensitivity")
    results.append({"case":"complete real comparison tables","status":"accepted"})

    def reject(name, mutate, expected):
        with tempfile.TemporaryDirectory(prefix="continuation-figure-guard-") as temporary:
            folder=Path(temporary)
            for filename in names:shutil.copyfile(source/filename,folder/filename)
            mutate(folder)
            try:report.load_inputs(folder,"million","sensitivity")
            except (ValueError,KeyError,TypeError,OSError) as error:
                if expected not in str(error):
                    raise AssertionError(f"{name}: wrong rejection: {error}") from error
                results.append({"case":name,"status":"rejected","reason":str(error)})
            else:raise AssertionError(f"{name}: malformed presentation input accepted")

    confirmation=lambda f,m:rewrite_table(f,"confirmation_cases.csv",m)
    summary=lambda f,m:rewrite_table(f,"case_summary.csv",m)
    reject("missing candidate",lambda f:confirmation(f,lambda rows:rows.pop(0)),"all four candidate")
    reject("missing control",lambda f:confirmation(f,lambda rows:rows.remove(next(r for r in rows if r["selected_candidate"]=="False"))),"all four candidate")
    reject("duplicate confirmation case",lambda f:confirmation(f,lambda rows:rows.append(dict(rows[0]))),"all four candidate")
    reject("wrong candidate label",lambda f:confirmation(f,lambda rows:rows[0].update(selected_candidate="False")),"candidate label")
    reject("wrong pair count",lambda f:confirmation(f,lambda rows:rows[0].update(primary_paired_observations="59")),"pair/loss count")
    reject("loss count out of range",lambda f:confirmation(f,lambda rows:rows[0].update(repeat_kkt_slower_observations="61")),"pair/loss count")
    reject("non-finite ratio",lambda f:confirmation(f,lambda rows:rows[0].update(primary_paired_runtime_ratio="nan")),"invalid ratio")
    reject("nonpositive ratio",lambda f:confirmation(f,lambda rows:rows[0].update(primary_paired_runtime_ratio="0")),"invalid ratio")
    reject("range excludes median",lambda f:confirmation(f,lambda rows:rows[0].update(primary_graph_max_ratio="0.01")),"invalid ratio")
    reject("changed campaign summary",lambda f:summary(f,lambda rows:next(r for r in rows if r["campaign"]=="confirmation").update(paired_runtime_ratio="0.999",graph_max_ratio="1.001")),"summaries differ")
    reject("duplicate campaign case",lambda f:summary(f,lambda rows:rows.append(dict(rows[0]))),"duplicate campaign/case")
    reject("missing sensitivity case",lambda f:summary(f,lambda rows:rows.remove(next(r for r in rows if r["campaign"]=="sensitivity"))),"all six perturbation")
    reject("unexpected sensitivity setting",lambda f:summary(f,lambda rows:next(r for r in rows if r["campaign"]=="sensitivity").update(intrusion_per_mille="2")),"all six perturbation")
    reject("sensitivity wrong pair count",lambda f:summary(f,lambda rows:next(r for r in rows if r["campaign"]=="sensitivity").update(paired_observations="7")),"wrong pair count")
    reject("failed comparison validation",lambda f:rewrite_metadata(f,lambda m:m.update(validation="fail")),"did not pass")
    reject("wrong held-out graph bank",lambda f:rewrite_metadata(f,lambda m:next(c for c in m["campaigns"] if c["name"]=="confirmation").update(graph_seeds=[17,42])),"protocol differs")
    reject("mismatched sensitivity bank",lambda f:rewrite_metadata(f,lambda m:next(c for c in m["campaigns"] if c["name"]=="sensitivity").update(sampling_seeds=[11,29])),"same screen protocol")
    reject("no frozen selection",lambda f:rewrite_config(f,lambda c:c.pop("selection_file")),"declared, frozen")
    reject("config changed after analysis",lambda f:rewrite_config(f,lambda c:c.update(extra="changed"),False),"configuration changed")
    print(json.dumps({"accepted":1,"rejected":len(results)-1,"source_sha256":report.digest(Path(report.__file__)),
        "comparison_inputs_sha256":report.digest(source/"comparison_inputs.json"),
        "scope":"presentation guards only; no plots or raw/MST revalidation","checks":results},indent=2))


if __name__=="__main__":main()
