#!/usr/bin/env python3
"""Create one self-contained HTML view from a complete, certified untimed export.

Run only after root release. Does not build or launch native code. A completed,
strictly validated extension combined CSV is required for exact fixture joins.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
FAMILIES=("leaf_hierarchy4","leaf_shuffled4")
ROOT=Path('/Users/random_person/Desktop/kkt-eighth-sampling')
PARENT_SHA='2be7556d15b58f3f65cc380ac22b67c57fdf8aea747d651b9d648c6a1aa59d2f'
ALGORITHMS=('kkt','compacting_boruvka','multigraph_boruvka','kruskal','prim','boruvka')

def require(ok,message):
    if not ok: raise ValueError(message)

def enforce_proofs(args,bound):
    # The native checker must be independently reviewed with the future build
    # receipt; preparation does not synthesize one or accept a pass boolean.
    checker=args.native_proof_checker.resolve(strict=True)
    require(hashlib.sha256(checker.read_bytes()).hexdigest()==args.native_proof_checker_sha256,'unreviewed native proof checker')
    bound[str(checker)]=args.native_proof_checker_sha256
    spec=importlib.util.spec_from_file_location('checked_root_view_export',checker)
    require(spec is not None and spec.loader is not None,'cannot load native proof checker')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    proof=module.check_record(args.native_receipt.resolve(strict=True))
    require(proof['validation']=='pass' and proof['native_execution'] is True and proof['owned_groups_verified_empty'] is True and
            proof['only_new_main'] is True and proof['parent_freeze_sha256']==PARENT_SHA and len(proof['object_paths'])==8,
            'incomplete native export proof')
    require(Path(proof['export_json']).resolve()==args.data.resolve() and proof['export_sha256']==bound[str(args.data.resolve())],
            'native proof did not validate this export')
    require(proof['bound_sha256'].get(str(args.native_receipt.resolve()))==bound[str(args.native_receipt.resolve())],
            'native receipt not bound by checker')
    for path,digest in proof['bound_sha256'].items():
        require(path not in bound or bound[path]==digest,'conflicting native proof hash');bound[path]=digest
    # The unchanged original collector validates the entire completed extension,
    # all child lifecycles, raw concatenation, certificates and parent freeze.
    helper=ROOT/'benchmark/run_eighth_extension.py';bound[str(helper)]=hashlib.sha256(helper.read_bytes()).hexdigest()
    sys.path.insert(0,str(ROOT/'benchmark'))
    import run_eighth_extension as timing
    info,_,_,_,_,inputs=timing.load(args.timing_capture.resolve(strict=True))
    require(Path(info['output']).resolve()==args.timing_csv.resolve(),'different strict-loaded timing CSV')
    for path,digest in inputs.items():
        require(path not in bound or bound[path]==digest,'conflicting timing proof hash');bound[path]=digest
    for path,digest in bound.items():require(hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,'proof input drift')

def fingerprint(edges,n,weights):
    value=14695981039346656037
    for number in [n,*[item for u,v,w,i in edges for item in ([u,v,w,i] if weights else [u,v,i])]]:
        for shift in (0,8,16,24): value=((value^((number>>shift)&255))*1099511628211)&((1<<64)-1)
    return str(value)

def check_timing_join(rows,graph):
    joined=[row for row in rows if row['family']==graph['family'] and int(row['n'])==1024 and int(row['graph_seed'])==17000011]
    require(len(joined)==42,'completed timing fixture needs all 42 solver calls')
    expected={(algorithm,phase,repetition) for algorithm in ALGORITHMS for phase,repetition in
              [('warmup',0),*[('timed',rep) for rep in range(6)]]}
    require({(row['algorithm'],row['phase'],int(row['repetition'])) for row in joined}==expected,'incomplete/duplicate 42-call identity matrix')
    require(all(row['validation']=='pass' and int(row['kkt_seed'])==2801 and int(row['m'])==32768 and
                int(row['density'])==32 and int(row['intrusion_per_mille'])==0 and int(row['warmups'])==1 and
                int(row['order'])==(ALGORITHMS.index(row['algorithm'])-int(row['repetition']))%6 and
                row['input_fingerprint']==graph['input_fingerprint'] and row['topology_fingerprint']==graph['topology_fingerprint']
                for row in joined),'timing input/certificate join differs')

def enrich(graph):
    require(graph["validation"]=="pass" and (graph["n"],graph["m"],graph["density"],graph["graph_seed"],graph["sampling_seed"])==
            (1024,32768,32,17000011,2801),"wrong explanatory fixture")
    labels=graph["original_to_label"];require(sorted(labels)==list(range(1024)),"invalid original labels")
    stages=graph["stages"];require(len(stages)==3 and len(graph["maps"])==2,"incomplete root stages")
    for stage in stages:
        require(stage["m"]==len(stage["edges"]),"incomplete full edge export")
        require(len({edge[3] for edge in stage["edges"]})==stage["m"],"duplicate ID")
        require(all(len(edge)==4 and all(type(item) is int for item in edge) and 0<=edge[0]<stage["n"] and
                    0<=edge[1]<stage["n"] and edge[0]!=edge[1] for edge in stage["edges"]),"invalid edge schema")
    for weighted,key in ((True,"input_fingerprint"),(False,"topology_fingerprint")):
        require(fingerprint(stages[0]["edges"],1024,weighted)==graph[key],"export fingerprint mismatch")
    # Morton-style dyadic boxes: explanatory geometry, never a benchmark input.
    xyz=[None]*1024
    for original,label in enumerate(labels):
        core,clone=divmod(original,4)
        x=sum(((core>>bit)&1)*(1<<j) for j,bit in enumerate((0,3,6)))
        y=sum(((core>>bit)&1)*(1<<j) for j,bit in enumerate((1,4,7)))
        z=sum(((core>>bit)&1)*(1<<j) for j,bit in enumerate((2,5)))
        offset=((0,0,0),(.23,0,0),(0,.23,0),(0,0,.23))[clone]
        xyz[label]=[(x+offset[0]-3.5)/4,(y+offset[1]-3.5)/4,(z+offset[2]-1.5)/4]
    members=[[[v] for v in range(1024)]];layouts=[xyz]
    for index,mapping in enumerate(graph["maps"]):
        require(len(mapping)==stages[index]["n"] and all(type(v) is int and 0<=v<stages[index+1]["n"] for v in mapping),"invalid quotient map")
        next_members=[[] for _ in range(stages[index+1]["n"])]
        for vertex,target in enumerate(mapping):next_members[target].extend(members[-1][vertex])
        require(all(next_members),"unexpected isolated quotient")
        members.append(next_members)
        layouts.append([[sum(xyz[v][axis] for v in values)/len(values) for axis in range(3)] for values in next_members])
    root=stages[2];by_id={edge[3]:i for i,edge in enumerate(root["edges"])}
    require([sample["policy"] for sample in graph["samples"]]==["half","eighth"],"missing scalar policies")
    for sample,mask in zip(graph["samples"],(1,7)):
        require(sample["mask"]==mask and sample["engine_words"]==root["m"],"wrong root word count")
        selected=sample["selected_parent_positions"]
        require(selected==sorted(set(selected)) and all(type(v) is int and 0<=v<root["m"] for v in selected),"sample order/positions")
        require(sample["sampled_ids"]==[root["edges"][v][3] for v in selected],"sample IDs are not parent positions restored")
        require(sample["sample_edges"]==len(selected) and sample["forest_edges"]==len(sample["forest_ids"]) and
                sample["heavy_edges"]==len(sample["heavy_ids"]) and sample["light_edges"]+sample["heavy_edges"]==root["m"] and
                sample["forest_components"]+sample["forest_edges"]==root["n"],"incomplete sample/filter counts")
        require(set(sample["forest_ids"])<=set(sample["sampled_ids"]) and set(sample["heavy_ids"])<=set(by_id),"invalid forest/heavy IDs")
    require(set(graph["samples"][1]["sampled_ids"])<=set(graph["samples"][0]["sampled_ids"]),"eighth root sample is not nested within half")
    graph.update(layouts=layouts,members=members)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data",type=Path,required=True);parser.add_argument("--timing-csv",type=Path,required=True)
    parser.add_argument("--timing-capture",type=Path,required=True);parser.add_argument("--native-receipt",type=Path,required=True)
    parser.add_argument("--native-proof-checker",type=Path,required=True);parser.add_argument("--native-proof-checker-sha256",required=True)
    parser.add_argument("--output",type=Path,required=True);args=parser.parse_args()
    paths=(args.data,args.timing_csv,args.timing_capture,args.native_receipt,HERE/"viewer.html",Path(__file__))
    before={str(path.resolve()):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    enforce_proofs(args,before)
    data=json.loads(args.data.read_text());require(data["schema"]=="current_hierarchy_root_view_v1" and
        data["trace_scope"]=="reconstructed_root_only","wrong export scope")
    require([graph["family"] for graph in data["graphs"]]==list(FAMILIES),"wrong fixture matrix")
    for graph in data["graphs"]:enrich(graph)
    ordered,shuffled=data["graphs"]
    require(ordered["original_to_label"]==shuffled["original_to_label"] and
        [(e[0],e[1],e[3]) for e in ordered["stages"][0]["edges"]]==[(e[0],e[1],e[3]) for e in shuffled["stages"][0]["edges"]],"topology twin differs")
    require(sorted(e[2] for e in ordered["stages"][0]["edges"])==sorted(e[2] for e in shuffled["stages"][0]["edges"]),"weight multiset differs")
    with args.timing_csv.open(newline="") as stream:rows=list(csv.DictReader(stream))
    for graph in data['graphs']:check_timing_join(rows,graph)
    template=(HERE/"viewer.html").read_text();require(template.count("__GRAPH_JSON__")==1,"invalid offline template")
    rendered=template.replace("__GRAPH_JSON__",json.dumps(data,separators=(",",":")))
    require(all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest for path,digest in before.items()),"view input drift")
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/"index.html").write_text(rendered)
    (args.output/"provenance.json").write_text(json.dumps(dict(schema="current_hierarchy_view_v1",input_sha256=before,
        html_sha256=hashlib.sha256(rendered.encode()).hexdigest(),timing_claim=False,context_edge_limit=512,
        scope="reconstructed root only; all complete edges/counts embedded; bounded displayed context"),indent=2)+"\n")
    print("Built one offline root-stage viewer; no native execution or timing analysis.")

if __name__=="__main__":main()
