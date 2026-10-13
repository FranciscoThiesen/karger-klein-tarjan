#!/usr/bin/env python3
"""Small synthetic correctness tests; never builds or runs a timed executable."""
import copy
import csv
import itertools
import json
from pathlib import Path
import tempfile

import analyze_continuation as analysis

GRAPH_SEEDS = (42, 17)  # Deliberately nonnumeric order: schedule uses bank positions.
SAMPLING_SEEDS = (7, 0)
REPETITIONS = 2


def write(path, fields, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader();writer.writerows(rows)


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def synthetic(cases):
    timing, work, trace = [], [], []
    counters, proxy = analysis.registry()
    for index,(case,spec) in enumerate(cases.items()):
        for gi,g in enumerate(GRAPH_SEEDS):
            prefix = {**spec,"graph_seed":g,"input_fingerprint":100000+index*1000+g,
                      "topology_fingerprint":spec["n"]*100+spec["density"]*10000+g}
            n,m=spec["n"],spec["m"]
            rounds=[]
            while m:
                nr=n//2
                if nr==1:nr=0
                mr=min(m//2,nr*(nr-1)//2)
                rounds.append({**prefix,"round":len(rounds)+1,"input_vertices":n,"input_edges":m,
                    "selected_edges":n-(nr or 1),"output_vertices":nr,"output_edges":mr,
                    "total_selected_edges":spec["n"]-1,"validation":"pass"})
                n,m=nr,mr
            for r in rounds:r["total_rounds"]=len(rounds)
            trace.extend(rounds)
            comp={f:0 for f in counters}
            comp.update(contraction_calls=len(rounds),contraction_edges=sum(r["input_edges"] for r in rounds),
                contraction_vertices=sum(r["input_vertices"] for r in rounds),
                contraction_output_vertices=sum(r["output_vertices"] for r in rounds),
                contraction_output_edges=sum(r["output_edges"] for r in rounds),
                kkt_edge_visits=spec["m"],initialized_slots=2*spec["n"],
                edge_materializations=spec["m"],hash_insert_items=spec["n"]-1)
            comp["contraction_edge_visits"]=3*comp["contraction_edges"]
            work.append({**prefix,"algorithm":"compacting_boruvka","kkt_seed":"na",**comp,
                         "total_work_proxy":sum(comp[f] for f in proxy),"validation":"pass"})
            for si,s in enumerate(SAMPLING_SEEDS):
                root=rounds[1]
                stats={f:0 for f in counters}
                stats.update(kkt_calls=3,kkt_vertices=spec["n"]+2*root["output_vertices"],
                    kkt_edges=spec["m"]+root["output_edges"],max_depth=2,
                    root_after_two_vertices=root["output_vertices"],root_after_two_edges=root["output_edges"],
                    contraction_calls=4,contraction_edges=spec["m"]+rounds[1]["input_edges"]+root["output_edges"],
                    contraction_vertices=spec["n"]+rounds[1]["input_vertices"]+2*root["output_vertices"],
                    sampling_calls=1,verifier_calls=1,sampling_edge_visits=root["output_edges"],
                    verifier_edges=root["output_edges"],sampled_edges=root["output_edges"]//2,
                    filtered_edges=root["output_edges"]//2,kkt_edge_visits=spec["m"]+2*root["output_edges"],
                    initialized_slots=2*spec["n"],edge_materializations=spec["m"],hash_insert_items=spec["n"]-1)
                stats["contraction_edge_visits"]=3*stats["contraction_edges"]
                work.append({**prefix,"algorithm":"kkt","kkt_seed":s,**stats,
                             "total_work_proxy":sum(stats[f] for f in proxy),"validation":"pass"})
                for repetition,algorithm in itertools.product(range(REPETITIONS),analysis.ALGORITHMS):
                    # Median of per-pair ratios is 1.0, whereas independently
                    # summarized time medians divide to 7525/5050, not 1.0.
                    base=100 if repetition==0 else 10000
                    scale=(gi+1)*(1 if si==0 else 3)
                    elapsed=base*scale
                    if algorithm=="kkt":elapsed=elapsed//2 if repetition==0 else elapsed*3//2
                    timing.append({**prefix,"kkt_seed":s,"repetition":repetition,
                        "order":(analysis.ALGORITHMS.index(algorithm)-repetition-gi-si)%2,
                        "warmups":1,"algorithm":algorithm,"elapsed_ns":elapsed,"validation":"pass"})
    return timing,work,trace


def main():
    checks=[]
    with tempfile.TemporaryDirectory(prefix="continuation-analysis-test-") as temporary:
        folder=Path(temporary)
        manifest=folder/"manifest.csv"
        specs=[{"family":f,"n":n,"density":2,"intrusion_per_mille":0}
               for f,n in itertools.product(("hierarchical_path","random_path"),(32,64))]
        write(manifest,analysis.MANIFEST_FIELDS,specs)
        cases=analysis.load_manifest(manifest)
        timing,work,trace=synthetic(cases)
        counters,proxy=analysis.registry()
        work_fields=(*analysis.PREFIX,"kkt_seed","algorithm",*counters,"total_work_proxy","validation")
        tp,wp,rp=folder/"timing.csv",folder/"work.csv",folder/"trace.csv"
        def load_timing(rows):
            write(tp,analysis.TIMING_FIELDS,rows)
            return analysis.load_timing(tp,cases,GRAPH_SEEDS,SAMPLING_SEEDS,REPETITIONS,1)
        def load_work(rows):
            write(wp,work_fields,rows)
            return analysis.load_work(wp,cases,GRAPH_SEEDS,SAMPLING_SEEDS)
        def load_trace(rows):
            write(rp,analysis.TRACE_FIELDS,rows)
            return analysis.load_traces(rp,cases,GRAPH_SEEDS)
        t,w,r=load_timing(timing),load_work(work),load_trace(trace)
        analysis.crosscheck(t,w,r,SAMPLING_SEEDS)
        checks.append({"case":"complete arbitrary manifest and all timing/work/trace matrices","status":"pass"})
        summaries,graphs,pairs,orders=analysis.aggregate_timing(t,cases,GRAPH_SEEDS,SAMPLING_SEEDS,REPETITIONS)
        check(len(summaries)==4 and len(graphs)==8 and len(pairs)==32 and len(orders)==8,"wrong output matrix sizes")
        for row in summaries:
            check(row["paired_runtime_ratio"]==1.0 and row["graph_min_ratio"]==row["graph_max_ratio"]==1.0,"wrong paired median")
            check(row["kkt_median_ns"]==22575 and row["compacting_boruvka_median_ns"]==15150,"wrong independent time medians")
            check(row["kkt_slower_observations"]==4 and row["paired_observations"]==8,"wrong individual losses")
        checks.append({"case":"paired ratios differ from ratio of independent medians; nested medians and losses exact","status":"pass"})
        order_timing=copy.deepcopy(timing)
        comp_times={(x["case_id"],x["graph_seed"],x["kkt_seed"],x["repetition"]):x["elapsed_ns"]
                    for x in order_timing if x["algorithm"]=="compacting_boruvka"}
        for row in order_timing:
            if row["algorithm"]=="kkt":
                duration=comp_times[row["case_id"],row["graph_seed"],row["kkt_seed"],row["repetition"]]
                row["elapsed_ns"]=duration//2 if row["order"]==0 else duration*3//2
        _,_,_,strata=analysis.aggregate_timing(load_timing(order_timing),cases,GRAPH_SEEDS,SAMPLING_SEEDS,REPETITIONS)
        check(all(x["paired_runtime_ratio"]==(.5 if x["kkt_order"]==0 else 1.5) for x in strata),"order strata mixed")
        checks.append({"case":"order-stratified paired medians preserve directional order effect","status":"pass"})
        ws,wg,ts,rs=analysis.aggregate_work(w,r,cases,GRAPH_SEEDS,SAMPLING_SEEDS)
        check(len(ws)==8 and len(wg)==16 and len(ts)==8 and len(rs)==len(trace),"wrong work summaries")
        for row in ws:
            check(row["contraction_edges_over_m"]==row["mean_contraction_edges"]/row["m"],"wrong contraction denominator")
        checks.append({"case":"same contraction_edges metric and trace volumes retained for both algorithms","status":"pass"})

        def reject(name, action):
            try:action()
            except ValueError as error:
                checks.append({"case":name,"status":"rejected","message":str(error)})
            else:raise AssertionError(name+" was accepted")
        def mutate(loader,rows,index,field,value,recompute=False):
            changed=copy.deepcopy(rows);changed[index][field]=value
            if recompute:changed[index]["total_work_proxy"]=sum(changed[index][f] for f in proxy)
            return loader(changed)

        reject("timing missing row",lambda:load_timing(timing[:-1]))
        reject("timing duplicate row",lambda:load_timing(timing+[timing[0]]))
        reject("timing missing sampling seed",lambda:load_timing([x for x in timing if x["kkt_seed"]!=0]))
        reject("timing missing graph seed",lambda:load_timing([x for x in timing if x["graph_seed"]!=17]))
        for field,value in [("family","random_tree"),("n",128),("m",65),("density",3),
            ("intrusion_per_mille",1),("graph_seed",999),("kkt_seed",11),("algorithm","kruskal"),
            ("repetition",2),("warmups",0),("order",1-timing[0]["order"]),
            ("elapsed_ns",0),("elapsed_ns",-1),("elapsed_ns","nan"),("elapsed_ns","1.5"),
            ("elapsed_ns",2**63),("validation","fail"),("input_fingerprint",2**64),
            ("input_fingerprint",123),("topology_fingerprint",123)]:
            reject(f"timing {field}={value}",lambda f=field,v=value:mutate(load_timing,timing,0,f,v))
        changed=copy.deepcopy(timing)
        for row in changed:
            if row["family"]=="random_path":row["topology_fingerprint"]+=1
        reject("paired weight controls have different topology",lambda:load_timing(changed))
        reject("odd repetition protocol",lambda:analysis.load_timing(tp,cases,GRAPH_SEEDS,SAMPLING_SEEDS,3,1))
        reject("wrong ordered seed bank",lambda:analysis.load_timing(tp,cases,GRAPH_SEEDS[::-1],SAMPLING_SEEDS,2,1))
        reject("duplicate seed bank",lambda:analysis.seed_bank("7,7"))
        reject("empty seed bank",lambda:analysis.seed_bank(""))
        reject("overflow seed",lambda:analysis.seed_bank(str(2**32)))

        ki=next(i for i,row in enumerate(work) if row["algorithm"]=="kkt")
        ci=next(i for i,row in enumerate(work) if row["algorithm"]=="compacting_boruvka")
        reject("work missing row",lambda:load_work(work[:-1]))
        reject("work duplicate row",lambda:load_work(work+[work[0]]))
        for index,field,value,recompute in [(ki,"kkt_seed",999,False),(ci,"kkt_seed",7,False),
            (ki,"initialized_slots",-1,False),(ki,"total_work_proxy",1,False),
            (ki,"verifier_calls",2,True),(ki,"path_query_visits",1,True),
            (ki,"kkt_calls",4,True),(ki,"current_depth",1,True),
            (ki,"hash_insert_items",1,True),(ki,"root_after_two_vertices",32,True),
            (ci,"verifier_calls",1,True),(ci,"kkt_edge_visits",1,True),
            (ci,"contraction_edge_visits",1,True)]:
            reject(f"work {index} {field}={value}",lambda i=index,f=field,v=value,z=recompute:mutate(load_work,work,i,f,v,z))

        reject("trace missing graph",lambda:load_trace([x for x in trace if (x["case_id"],x["graph_seed"])!=(trace[0]["case_id"],trace[0]["graph_seed"])]))
        reject("trace missing round",lambda:load_trace(trace[1:]))
        reject("trace duplicate round",lambda:load_trace(trace+[trace[0]]))
        for field,value in [("input_edges",63),("selected_edges",0),("output_vertices",17),
            ("output_edges",64),("total_rounds",99),("total_selected_edges",30),("validation","fail")]:
            reject(f"trace {field}={value}",lambda f=field,v=value:mutate(load_trace,trace,0,f,v))
        changed=copy.deepcopy(trace)
        for row in changed:
            if row["case_id"]==trace[0]["case_id"] and row["graph_seed"]==trace[0]["graph_seed"]:
                row["input_fingerprint"]+=1
        changed_trace=load_trace(changed)
        reject("trace input fingerprint differs from timing/work",lambda:analysis.crosscheck(t,w,changed_trace,SAMPLING_SEEDS))
        changed=copy.deepcopy(work);changed[ci]["contraction_edges"]+=1
        changed_work=load_work(changed)
        reject("compactor trace/work volume differs",lambda:analysis.crosscheck(t,changed_work,r,SAMPLING_SEEDS))
        changed=copy.deepcopy(work);changed[ki]["root_after_two_edges"]-=1
        changed_work=load_work(changed)
        reject("KKT root/trace residual differs",lambda:analysis.crosscheck(t,changed_work,r,SAMPLING_SEEDS))

        def manifest_rows(rows):
            write(manifest,analysis.MANIFEST_FIELDS,rows)
            return analysis.load_manifest(manifest)
        reject("empty manifest",lambda:manifest_rows([]))
        reject("duplicate manifest case",lambda:manifest_rows(specs+[specs[0]]))
        for field,value in [("family","unknown"),("n",33),("density",512),("intrusion_per_mille",1001)]:
            reject(f"manifest {field}={value}",lambda f=field,v=value:mutate(manifest_rows,specs,0,f,v))
        reject("random control with intrusions",lambda:manifest_rows([{"family":"random_path","n":32,"density":2,"intrusion_per_mille":1}]))
        reject("invalid legacy density",lambda:manifest_rows([{"family":"legacy_random","n":32,"density":2,"intrusion_per_mille":0}]))
        crossover_families=("line_metric","line_random","grid2d_metric","grid2d_random","gnm_random")
        for family in crossover_families:
            for n in (2**22,2**23):
                accepted=manifest_rows([{"family":family,"n":n,"density":16,"intrusion_per_mille":0}])
                check(next(iter(accepted.values()))["m"]==n*16,"new-family boundary edge count differs")
            accepted=manifest_rows([{"family":family,"n":2**23,"density":126,"intrusion_per_mille":0}])
            check(next(iter(accepted.values()))["m"]==1056964608,"valid high-density edge count differs")
            checks.append({"case":f"{family} accepts old4M/new8M dimensions and unchanged weight boundary","status":"pass"})
            reject(f"{family} rejects16M",lambda f=family:manifest_rows(
                [{"family":f,"n":2**24,"density":16,"intrusion_per_mille":0}]))
            reject(f"{family} rejects8M above weight sentinel",lambda f=family:manifest_rows(
                [{"family":f,"n":2**23,"density":127,"intrusion_per_mille":0}]))
        for family in analysis.FAMILIES:
            if family not in crossover_families:
                reject(f"old {family} retains4M vertex cap",lambda f=family:manifest_rows(
                    [{"family":f,"n":2**23,"density":32 if f=="legacy_random" else 16,"intrusion_per_mille":0}]))
        distance_specs=[{"family":f,"n":32,"density":2,"intrusion_per_mille":0}
                        for f in ("distance_path","distance_tree")]
        distance_cases=manifest_rows(distance_specs)
        dt,dw,dr=synthetic(distance_cases)
        write(tp,analysis.TIMING_FIELDS,dt);write(wp,work_fields,dw);write(rp,analysis.TRACE_FIELDS,dr)
        distance_timing=analysis.load_timing(tp,distance_cases,GRAPH_SEEDS,SAMPLING_SEEDS,2,1)
        distance_work=analysis.load_work(wp,distance_cases,GRAPH_SEEDS,SAMPLING_SEEDS)
        distance_trace=analysis.load_traces(rp,distance_cases,GRAPH_SEEDS)
        analysis.crosscheck(distance_timing,distance_work,distance_trace,SAMPLING_SEEDS)
        checks.append({"case":"both engineered distance families accept complete p=0 data and exact-halving traces","status":"pass"})
        for family in ("distance_path","distance_tree"):
            reject(f"{family} rejects intrusions",lambda f=family:manifest_rows(
                [{"family":f,"n":32,"density":2,"intrusion_per_mille":1}]))
            changed=copy.deepcopy(dr)
            index=next(i for i,row in enumerate(changed) if row["family"]==family and row["round"]==1)
            changed[index]["output_vertices"]=15;changed[index]["selected_edges"]=17
            write(rp,analysis.TRACE_FIELDS,changed)
            reject(f"{family} requires exact dyadic halving",lambda:analysis.load_traces(rp,distance_cases,GRAPH_SEEDS))
        def missing_counter():
            write(wp,tuple(f for f in work_fields if f!="median_entries"),
                  [{k:v for k,v in row.items() if k!="median_entries"} for row in work])
            return analysis.load_work(wp,cases,GRAPH_SEEDS,SAMPLING_SEEDS)
        reject("missing registered counter column",missing_counter)
    print(json.dumps({"checks":checks,"accepted":sum(x["status"]=="pass" for x in checks),
                      "rejected":sum(x["status"]=="rejected" for x in checks)},indent=2))


if __name__=="__main__":
    main()
