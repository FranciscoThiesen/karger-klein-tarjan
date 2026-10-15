from pathlib import Path
from fractions import Fraction
from statistics import median
from collections import defaultdict
import csv, json, hashlib, math
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
RESULTS=ROOT/'benchmark/results'
inputs={}
def read(p):
 p=Path(p); before=hashlib.sha256(p.read_bytes()).hexdigest(); rows=list(csv.DictReader(p.open())); assert hashlib.sha256(p.read_bytes()).hexdigest()==before; inputs[str(p.relative_to(ROOT))]=before; return rows
def close(x,y): assert math.isclose(float(x),float(y),rel_tol=1e-14,abs_tol=1e-14),(x,y)
checks={}; selected=[]
for study,folder,count in [('lower-density-2026-10-15','analysis-attempt01',2520),('eighth-extension-2026-10-15','analysis',1176),('eighth-distance-2026-10-15','analysis',1008)]:
 a=RESULTS/study/folder; raw=read(a/'validated_calls.csv'); assert len(raw)==count
 lookup={}; sets=defaultdict(set)
 for r in raw:
  assert r['validation']=='pass'
  key=(r['case_id'],r['graph_seed'],r['kkt_seed'],r['phase'],r['repetition'],r['algorithm']); assert key not in lookup; lookup[key]=r
  sets[key[:-1]].add(r['algorithm'])
 assert all(s=={'kkt','compacting_boruvka','multigraph_boruvka','kruskal','prim','boruvka'} for s in sets.values())
 pairs=defaultdict(list); graphs=defaultdict(lambda:defaultdict(list)); simultaneous=defaultdict(int)
 for key,r in lookup.items():
  if r['phase']!='timed' or r['algorithm']!='kkt':continue
  for clock,field in [('wall','elapsed_ns'),('cpu','process_cpu_elapsed_ns')]:
   wins=[]
   for alg in ['compacting_boruvka','multigraph_boruvka','kruskal','prim','boruvka']:
    c=lookup[key[:-1]+(alg,)]; ratio=Fraction(int(r[field]),int(c[field])); k=(r['case_id'],alg,clock)
    pairs[k].append(ratio); graphs[k][r['graph_seed']].append(ratio);wins.append(ratio<1)
   simultaneous[clock]+=all(wins)
 comparisons=read(a/'comparisons.csv');assert len(comparisons)==len(pairs)
 for r in comparisons:
  k=(r['case_id'],r['competitor'],r['metric']); v=pairs[k]; g=[median(x) for x in graphs[k].values()]
  for name,value in [('median_paired_ratio',median(v)),('trial_min',min(v)),('trial_max',max(v)),('graph_min',min(g)),('graph_max',max(g))]:close(r[name],value)
  assert int(r['trials'])==len(v) and int(r['individual_wins'])==sum(x<1 for x in v)
  keep=(study.startswith('lower') and int(r['n']) in ([512,2048,8192,2097152] if r['density']=='16' else [262144,1048576,4194304])) or (not study.startswith('lower') and int(r['n']) in [1024,1048576,4194304])
  if keep:selected.append({'study':study,**r})
 checks[study]={'outputs':len(raw),'timed_outputs':sum(r['phase']=='timed' for r in raw),'comparison_rows_recomputed':len(comparisons),'exact_pairs':sum(map(len,pairs.values())),'simultaneous_all_five_wins':dict(simultaneous)}
 if study.startswith('lower'):
  states={}
  for k,g in graphs.items():
   c,alg,clock=k
   states.setdefault((c,alg),[]).extend(median(v) for v in g.values())
  state={k:('strong_lead' if all(x<=Fraction(9,10) for x in v) else 'narrow_lead' if all(x<1 for x in v) else 'loss' if all(x>1 for x in v) else 'mixed_or_tied') for k,v in states.items()}
  points=read(a/'crossover_points.csv');assert len(points)==150
  for r in points:assert r['state']==state[(r['case_id'],r['competitor'])]
  outcomes=read(a/'crossover_summary.csv'); brackets=read(a/'crossover_brackets.csv');assert len(outcomes)==20 and len(brackets)==490
  checks[study].update(strong_outcomes=sum(r['strong_crossover']=='True' for r in outcomes),qualifying_endpoint_pairs=sum(r['strong_crossover']=='True' for r in brackets),pooled_all_five_cases=sum(all(median(pairs[(case,alg,metric)])<1 for alg in ['compacting_boruvka','multigraph_boruvka','kruskal','prim','boruvka'] for metric in ['wall','cpu']) for case in {k[0] for k in pairs}))
# Paired probability change: fresh half/eighth timing rows, exact same identifiers.
a=RESULTS/'eighth-sampling-2026-10-15/analysis'; raw=read(a/'validated_calls.csv'); index={}
for r in raw:
 k=tuple(r[x] for x in ['variant','case_id','graph_seed','kkt_seed','phase','repetition','algorithm']);assert k not in index;index[k]=r
vp=defaultdict(list)
for k,r in index.items():
 if r['variant']!='eighth' or r['phase']!='timed':continue
 other=index[('half',)+k[1:]]
 for metric,field in [('wall','elapsed_ns'),('cpu','process_cpu_elapsed_ns')]:vp[(r['case_id'],r['algorithm'],metric)].append(Fraction(int(r[field]),int(other[field])))
variants=read(a/'variant_comparisons.csv');assert len(vp)==len(variants)==72
for r in variants:
 v=vp[(r['case_id'],r['algorithm'],r['metric'])];close(median(v),r['median_paired_ratio']);assert len(v)==int(r['trials']);assert sum(x<1 for x in v)==int(r['individual_wins'])
 if r['algorithm']=='kkt':selected.append({'study':'eighth-sampling-2026-10-15',**r})
checks['eighth-sampling-2026-10-15']={'variant_comparison_rows_recomputed':72,'kkt_wins_by_clock':{c:sum(x<1 for k,v in vp.items() if k[1:] == ('kkt',c) for x in v) for c in ['wall','cpu']},'kkt_trials_per_clock':144}
# The independent fit audit is already complete; verify the reported choice inventories directly.
a=RESULTS/'current-complexity-2026-10-15/analysis-attempt01'; g=read(a/'google_selection.csv');f=read(a/'model_fits.csv');m=read(a/'means.csv');assert len(g)==24 and len(f)==1152 and len(m)==3168
assert {r['selected_model'] for r in g}=={'NlgN'}; choices=[r for r in f if r['selected_for_this_clock']=='True'];assert len(choices)==192 and {r['model'] for r in choices}=={'NlgN'}
checks['current-complexity-2026-10-15']={'google_choices':24,'kkt_google_choices':sum(r['algorithm']=='kkt' for r in g),'custom_choices':192,'all_selected_model':'NlgN','means':3168,'fits':1152,'scope':'Choice inventory independently reread; prior independent arithmetic audit supplies fit reconstruction.'}
report=ROOT/'docs/kkt-report/current-2026-10-15/html-attempt03/REPORT.md';inputs[str(report.relative_to(ROOT))]=hashlib.sha256(report.read_bytes()).hexdigest()
for p,d in inputs.items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==d
out={'schema':'kkt_blog_fact_audit_v1','validation':'pass','scope':'No new measurements. Independently recomputed paired ratios, ranges, graph medians and point states from already independently audited validated calls; retained prior independent source/provenance audit as upstream authority. Fit menu inventory only, no duplicate fitting.','checks':checks,'selected_claim_rows':selected,'source_sha256':inputs}
(HERE/'verified-claims.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'validation':'pass','checks':checks,'report_sha256':inputs[str(report.relative_to(ROOT))]},indent=2))
