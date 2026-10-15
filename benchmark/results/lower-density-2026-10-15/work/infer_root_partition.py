#!/usr/bin/env python3
"""Infer only root verifier paths forced by cumulative integer bounds; no run."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(ok,message):
    if not ok:raise ValueError(message)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();output=args.output_dir.resolve()
    require(not output.exists(),'refusing existing output')
    proof_path=HERE/'partition-analysis-attempt01/provenance.json'
    inputs={str(Path(__file__).resolve()):sha(__file__),str(proof_path):sha(proof_path)}
    proof=json.loads(proof_path.read_text());require(proof['validation']=='pass','partition proof failed')
    for path,digest in proof['input_sha256'].items():
        require(sha(path)==digest,'partition input changed');inputs[path]=digest
    partition_path=proof_path.parent/'partition.csv'
    require(sha(partition_path)==proof['output_sha256'][partition_path.name],'partition table changed')
    inputs[str(partition_path)]=sha(partition_path)
    with partition_path.open(newline='') as stream:
        partition={(r['case_id'],r['graph_seed']):r for r in csv.DictReader(stream)}
    work_path=HERE/'analysis-attempt01/work.csv'
    with work_path.open(newline='') as stream:
        work=[r for r in csv.DictReader(stream) if r['algorithm']=='kkt']
    require(len(work)==len(partition)==60,'missing full matrix')
    result=[]
    for row in work:
        v=lambda key:int(row[key])
        p=partition[(row['case_id'],row['graph_seed'])]
        root=v('root_after_two_edges');total=v('verifier_edges');forest=v('verifier_forest_edges')
        residual=int(p['disconnected_partition_edge_visits'])
        require(0<root<=total and v('root_after_two_vertices')>0,'nonempty root precondition')
        # Any nonempty disconnected root contributes at least root edge visits.
        # An empty root forest retains all root records, also included in the
        # cumulative filtered_edges. Excluding both leaves the connected path.
        connected=(residual<root and v('filtered_edges')<root)
        # If the root is not partitioned, all partitioned graph volumes sum to
        # at most total-root. Each within-component sum is no greater; all
        # partitioned forest edges are bounded by the whole-solve forest total.
        upper_without_root=2*(total-root)+2*forest
        disconnected=residual>upper_without_root
        require(not (connected and disconnected),'contradictory root inference')
        state='connected' if connected else 'nonempty_disconnected' if disconnected else 'undetermined'
        result.append({key:row[key] for key in ('case_id','family','density','n','m','graph_seed','kkt_seed')} |
                      dict(root_vertices=v('root_after_two_vertices'),root_edges=root,
                           verifier_edges=total,verifier_forest_edges=forest,
                           filtered_edges=v('filtered_edges'),partition_visits=residual,
                           partition_upper_bound_if_root_not_partitioned=upper_without_root,
                           inferred_root_path=state))
    for path,digest in inputs.items():require(sha(path)==digest,'input drift')
    output.mkdir();path=output/'root_inference.csv'
    with path.open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(result[0]));writer.writeheader();writer.writerows(result)
    summary=dict(validation='pass',rows=60,input_sha256=inputs,output_sha256={path.name:sha(path)},
                 classifications={state:sum(r['inferred_root_path']==state for r in result)
                                  for state in ('connected','nonempty_disconnected','undetermined')},
                 scope='Root-path inference only when forced by cumulative integer bounds; no component-count, per-call trace or CPU-time claim.')
    (output/'provenance.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('input_sha256','output_sha256')},indent=2))


if __name__=='__main__':main()
