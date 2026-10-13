#!/usr/bin/env python3
"""Synthetic validation for cross-campaign continuation analysis; no timed runs."""
import copy
import csv
import itertools
import json
from pathlib import Path
import tempfile

import analyze_continuation as base
import compare_continuation as comparison


def write_csv(path, fields, rows):
    with path.open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields)
        writer.writeheader();writer.writerows(rows)


def check(condition,message):
    if not condition:raise AssertionError(message)


def fixture(folder):
    specs=[{"family":family,"n":n,"density":2,"intrusion_per_mille":0}
           for family,n in itertools.product(("hierarchical_path","random_path"),(32,64,128))]
    config={"campaigns":[],"confirmation":{"primary":"primary","repeat":"repeat",
        "candidate_groups":[{"family":"hierarchical_path","density":2,"intrusion_per_mille":0}]}}
    documents={}
    for name in ("screen","primary","repeat"):
        gs=(42,17) if name=="screen" else comparison.HOLDOUT_GRAPHS
        ss=(7,0) if name=="screen" else comparison.HOLDOUT_SAMPLING
        reps=2 if name=="screen" else 4
        ordered=specs[::-1] if name=="repeat" else specs
        manifest=folder/(name+"_manifest.csv")
        timing_path=folder/(name+"_timing.csv")
        metadata_path=folder/(name+"_metadata.json")
        write_csv(manifest,base.MANIFEST_FIELDS,ordered)
        cases=base.load_manifest(manifest)
        rows=[]
        for case,spec in cases.items():
            for gi,g in enumerate(gs):
                topology=spec["n"]*1000000+g
                weighted=topology+(1000000000 if spec["family"]=="random_path" else 0)
                for si,s in enumerate(ss):
                    for r,order in itertools.product(range(reps),(0,1)):
                        algorithm=base.ALGORITHMS[(order+r+gi+si)%2]
                        # Lower-size loss must remain visible but not invalidate
                        # the fixed two-largest-size criterion.
                        ratio=1.2 if spec["family"]=="random_path" else {32:1.1,64:.85,128:.90}[spec["n"]]
                        duration=20000 if name=="repeat" else 10000
                        if algorithm=="kkt":duration=round(duration*ratio)
                        rows.append({**spec,"graph_seed":g,"input_fingerprint":weighted,
                            "topology_fingerprint":topology,"kkt_seed":s,"repetition":r,
                            "order":(base.ALGORITHMS.index(algorithm)-r-gi-si)%2,
                            "warmups":1,"algorithm":algorithm,"elapsed_ns":duration,"validation":"pass"})
        write_csv(timing_path,base.TIMING_FIELDS,rows)
        metadata={"mode":"timing","exit_status":0,"interruption":None,
            "output_sha256":comparison.sha256(timing_path),"manifest_sha256":comparison.sha256(manifest),
            "basic_validated_rows":len(rows),"checked_warmup_calls":len(cases)*len(gs)*len(ss)*2,
            "binary_sha256":"a"*64,"runner_sha256":"b"*64,
            "source_sha256":{f:"c"*64 for f in comparison.PRODUCTION_FILES},
            "profile":"synthetic native O3","platform":"synthetic platform","machine":"synthetic architecture"}
        metadata_path.write_text(json.dumps(metadata))
        config["campaigns"].append({"name":name,"role":"screen" if name=="screen" else "confirmation",
            "manifest":manifest.name,"timing_csv":timing_path.name,"timing_metadata":metadata_path.name,
            "graph_seeds":list(gs),"sampling_seeds":list(ss),"repetitions":reps,"warmups":1})
        documents[name]={"rows":rows,"specs":ordered,"metadata":metadata,"manifest":manifest,
                         "timing_csv":timing_path,"timing_metadata":metadata_path}
    return config,documents


def rewrite(document, rows=None, specs=None, update_hashes=True):
    if rows is not None:
        document["rows"]=rows
        write_csv(document["timing_csv"],base.TIMING_FIELDS,rows)
    if specs is not None:
        document["specs"]=specs
        write_csv(document["manifest"],base.MANIFEST_FIELDS,specs)
    if update_hashes:
        document["metadata"]["output_sha256"]=comparison.sha256(document["timing_csv"])
        document["metadata"]["manifest_sha256"]=comparison.sha256(document["manifest"])
    document["timing_metadata"].write_text(json.dumps(document["metadata"]))


def main():
    results=[]
    with tempfile.TemporaryDirectory(prefix="continuation-compare-test-") as temporary:
        folder=Path(temporary)
        config,docs=fixture(folder)
        campaigns,confirmation=comparison.collect(config,folder)
        cases,groups,graphs=comparison.confirmation_tables(confirmation)
        selected=next(r for r in groups if r["selected_candidate"])
        check(selected["confirmed_preselected_group"] and selected["criterion_sizes"]=="64,128",
              "largest-two rule or inclusive .90 threshold failed")
        check(len(cases)==6 and len(graphs)==30 and all(r["repeat_over_primary_kkt_median"]==2 for r in cases),
              "run drift or complete matched matrix lost")
        check(sum(r["both_case_medians_below_one"] for r in cases)==2 and
              any(r["n"]==32 and r["primary_kkt_slower_observations"]==60 for r in cases),"losses omitted")
        results.append({"case":"complete screen and reversed held-out pair; inclusive .90; lower-size losses retained; drift preserved","status":"pass"})
        tables=comparison.tagged_tables(campaigns)
        check(len(tables["paired_pairs"])==768 and len(tables["case_summary"])==18 and
              len(tables["order_summary"])==36,"tagged campaign records were pooled or dropped")
        results.append({"case":"every campaign, pair and order stratum retained separately","status":"pass"})

        # A single graph at parity prevents confirmation even when the case
        # median remains .85; the failure is a valid result, not malformed data.
        config,docs=fixture(folder)
        rows=copy.deepcopy(docs["repeat"]["rows"])
        for row in rows:
            if (row["family"],row["n"],row["graph_seed"],row["algorithm"])==("hierarchical_path",64,comparison.HOLDOUT_GRAPHS[0],"kkt"):
                row["elapsed_ns"]=20000
        rewrite(docs["repeat"],rows=rows)
        _,conf=comparison.collect(config,folder)
        cc,gg,_=comparison.confirmation_tables(conf)
        check(not next(r for r in gg if r["selected_candidate"])["confirmed_preselected_group"],"one graph at parity passed")
        check(next(r for r in cc if r["family"]=="hierarchical_path" and r["n"]==64)["repeat_paired_runtime_ratio"]==.85,
              "single-graph failure incorrectly changed median")
        results.append({"case":"one graph exactly at parity blocks confirmation despite .85 case median","status":"pass"})

        config,docs=fixture(folder)
        rows=copy.deepcopy(docs["repeat"]["rows"])
        for row in rows:
            if (row["family"],row["n"],row["algorithm"])==("hierarchical_path",128,"kkt"):
                row["elapsed_ns"]=18001
        rewrite(docs["repeat"],rows=rows)
        _,conf=comparison.collect(config,folder)
        check(not next(r for r in comparison.confirmation_tables(conf)[1] if r["selected_candidate"])["confirmed_preselected_group"],
              "ratio just above .90 passed")
        results.append({"case":"one campaign just above .90 blocks confirmation without rounding into a pass","status":"pass"})

        config,docs=fixture(folder)
        for name in ("primary","repeat"):
            doc=docs[name]
            keep=lambda r:r["family"]!="hierarchical_path" or r["n"]==128
            rows=[r for r in doc["rows"] if keep(r)]
            specs=[r for r in doc["specs"] if keep(r)]
            doc["metadata"]["basic_validated_rows"]=len(rows)
            doc["metadata"]["checked_warmup_calls"]=len(specs)*len(comparison.HOLDOUT_GRAPHS)*len(comparison.HOLDOUT_SAMPLING)*2
            rewrite(doc,rows=rows,specs=specs)
        _,conf=comparison.collect(config,folder)
        selected=next(r for r in comparison.confirmation_tables(conf)[1] if r["selected_candidate"])
        check(not selected["two_sizes_available"] and not selected["confirmed_preselected_group"],
              "one successful size cannot satisfy the two-size rule")
        results.append({"case":"a single successful tested size remains insufficient for confirmation","status":"pass"})

        def reject(name,mutation):
            cfg,documents=fixture(folder)
            mutation(cfg,documents)
            try:comparison.collect(cfg,folder)
            except ValueError as error:results.append({"case":name,"status":"rejected","message":str(error)})
            else:raise AssertionError(name+" was accepted")
        def change_metadata(d,name,field,value):
            d[name]["metadata"][field]=value
            rewrite(d[name])
        reject("repeat manifest not reversed",lambda c,d:rewrite(d["repeat"],specs=d["primary"]["specs"]))
        reject("duplicate campaign name",lambda c,d:c["campaigns"][2].update(name="primary"))
        reject("confirmation pair uses same run",lambda c,d:c["confirmation"].update(repeat="primary"))
        reject("missing declared confirmation",lambda c,d:c.pop("confirmation"))
        reject("unknown campaign option",lambda c,d:c["campaigns"][0].update(typo=True))
        reject("missing runner metadata",lambda c,d:c["campaigns"][2].pop("timing_metadata"))
        reject("repeat binary differs",lambda c,d:change_metadata(d,"repeat","binary_sha256","d"*64))
        reject("repeat compiler profile differs",lambda c,d:change_metadata(d,"repeat","profile","other"))
        reject("repeat platform differs",lambda c,d:change_metadata(d,"repeat","platform","other"))
        reject("screen production code differs",lambda c,d:change_metadata(d,"screen","source_sha256",
            {f:("d" if f=="kkt/kkt.cpp" else "c")*64 for f in comparison.PRODUCTION_FILES}))
        reject("runner failed",lambda c,d:change_metadata(d,"repeat","exit_status",1))
        reject("runner interrupted",lambda c,d:change_metadata(d,"repeat","interruption","SIGINT"))
        reject("runner wrong mode",lambda c,d:change_metadata(d,"repeat","mode","work"))
        reject("runner row count differs",lambda c,d:change_metadata(d,"repeat","basic_validated_rows",1))
        reject("runner warmup count differs",lambda c,d:change_metadata(d,"repeat","checked_warmup_calls",1))
        reject("boolean runner count",lambda c,d:change_metadata(d,"repeat","basic_validated_rows",True))
        reject("missing source inventory",lambda c,d:change_metadata(d,"repeat","source_sha256",{}))
        reject("empty candidate group list",lambda c,d:c["confirmation"].update(candidate_groups=[]))
        reject("candidate not in manifest",lambda c,d:c["confirmation"]["candidate_groups"][0].update(density=64))
        reject("duplicate candidate group",lambda c,d:c["confirmation"]["candidate_groups"].append(copy.deepcopy(c["confirmation"]["candidate_groups"][0])))
        reject("candidate boolean density",lambda c,d:c["confirmation"]["candidate_groups"][0].update(density=True))
        reject("boolean protocol count",lambda c,d:c["campaigns"][0].update(repetitions=True))
        reject("duplicate seed bank",lambda c,d:c["campaigns"][0].update(graph_seeds=[17,17]))
        reject("missing holdout sampling seed",lambda c,d:c["campaigns"][2].update(sampling_seeds=[11,29]))
        reject("unbalanced seed bank order",lambda c,d:c["campaigns"][2].update(graph_seeds=list(reversed(comparison.HOLDOUT_GRAPHS))))
        reject("missing timing row",lambda c,d:rewrite(d["repeat"],rows=d["repeat"]["rows"][:-1]))
        reject("CSV records reordered despite correct order labels",lambda c,d:rewrite(d["repeat"],rows=d["repeat"]["rows"][::-1]))
        def mutate_rows(doc,predicate,field,value):
            rows=copy.deepcopy(doc["rows"])
            for row in rows:
                if predicate(row):row[field]=value(row) if callable(value) else value
            rewrite(doc,rows=rows)
        reject("cross-run weighted fingerprint mismatch",lambda c,d:mutate_rows(d["repeat"],lambda r:True,
            "input_fingerprint",lambda r:r["input_fingerprint"]+1))
        reject("cross-run topology fingerprint mismatch",lambda c,d:mutate_rows(d["repeat"],lambda r:True,
            "topology_fingerprint",lambda r:r["topology_fingerprint"]+1))
        reject("wrong execution order",lambda c,d:mutate_rows(d["repeat"],lambda r:True,"order",lambda r:1-r["order"]))
        reject("failed exact MST validation",lambda c,d:mutate_rows(d["repeat"],lambda r:True,"validation","fail"))
        def stale_hash(c,d):
            d["repeat"]["metadata"]["output_sha256"]="0"*64
            rewrite(d["repeat"],update_hashes=False)
        reject("raw timing hash differs from metadata",stale_hash)
    print(json.dumps({"validation":"pass","positive_checks":sum(r["status"]=="pass" for r in results),
                      "negative_checks":sum(r["status"]=="rejected" for r in results),"checks":results},indent=2))


if __name__=="__main__":main()
