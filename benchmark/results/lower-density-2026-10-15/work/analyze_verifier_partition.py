#!/usr/bin/env python3
"""Derive the exact cumulative forest-partition edge-visit bucket; no native run."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(ok, message):
    if not ok: raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args(); output = args.output_dir.resolve()
    require(not output.exists(), 'refusing existing output')
    audit_path = HERE/'independent-counter-audit-attempt01/audit.json'
    inputs = {str(Path(__file__).resolve()):sha(__file__), str(audit_path):sha(audit_path)}
    audit = json.loads(audit_path.read_text()); require(audit['validation']=='pass','audit not passed')
    for path in (HERE/'analysis-attempt01/work.csv', ROOT/'verifier/verifier_v2.cpp',
                 ROOT/'kkt/kkt.cpp', ROOT/'common/work_stats.hpp'):
        digest = sha(path)
        require(audit['input_sha256'].get(str(path)) == digest, 'source/table differs from audited artifact')
        inputs[str(path)] = digest
    with (HERE/'analysis-attempt01/work.csv').open(newline='') as stream:
        work = [r for r in csv.DictReader(stream) if r['algorithm']=='kkt']
    require(len(work)==60, 'missing complete KKT matrix')
    rows=[]
    for row in work:
        v=lambda name:int(row[name])
        # Every connected-tree reduction emits one FBT, with vertices minus one
        # edges. Its two query scans and two FBT-edge scans account for the first
        # two terms. Only the nonempty disconnected-forest path adds the residual.
        require(v('fbt_calls')==v('verifier_tree_calls'),'FBT/tree-call identity')
        base_queries=2*v('verifier_tree_edges')
        base_fbt=2*(v('fbt_output_vertices')-v('fbt_calls'))
        partition=v('verifier_edge_visits')-base_queries-base_fbt
        require(partition>=0 and v('verifier_arc_visits')%2==0,'invalid partition accounting')
        # Iterative DFS consumes each forest adjacency exactly once. Its 2F
        # increments are disjoint from edge visits and reveal the two forest scans.
        forest_twice=v('verifier_arc_visits')
        query_partition=partition-forest_twice
        require(query_partition>=0, 'negative partition query scans')
        rows.append({key:row[key] for key in ('case_id','family','density','n','m','graph_seed','kkt_seed')} |
                    dict(verifier_edge_visits=v('verifier_edge_visits'),
                         connected_query_scan_visits=base_queries, fbt_edge_scan_visits=base_fbt,
                         disconnected_partition_edge_visits=partition,
                         disconnected_forest_scan_visits=forest_twice,
                         disconnected_graph_plus_component_scan_visits=query_partition,
                         partition_per_m=partition/v('m'),verifier_calls=v('verifier_calls'),
                         verifier_components=v('verifier_components'),tree_calls=v('verifier_tree_calls'),
                         initialized_slots=v('initialized_slots'),edge_materializations=v('edge_materializations')))
    for path,digest in inputs.items():require(sha(path)==digest,'input changed')
    output.mkdir()
    path=output/'partition.csv'
    with path.open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    result=dict(validation='pass',rows=len(rows),all_nonnegative=True,input_sha256=inputs,
                output_sha256={path.name:sha(path)},
                scope='Exact cumulative logical edge visits of nonempty disconnected-forest partitioning; not root-call identification or CPU attribution.')
    (output/'provenance.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('input_sha256','output_sha256')},indent=2))


if __name__=='__main__':main()
