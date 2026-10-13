import sys,csv,tempfile,copy,json,statistics,hashlib
from pathlib import Path
root=Path('/Users/random_person/Desktop/karger-klein-tarjan');sys.path.insert(0,str(root/'benchmark'))
import analyze_mst_search as a
c=a.capture
spec={'family':'hierarchical_path','n':128,'m':512,'density':4,'intrusion_per_mille':0};spec['case_id']=a.base.case_id(spec)
rows=[];cpu=0;utc=10_000_000_000
ratios={17:(1,2,4),42:(.01,20,30),999:(.02,6,9)}
for g,rs in ratios.items():
 for sample,r in enumerate(rs):
  for phase,count in [('warmup',1),('timed',5)]:
   for rep in range(count):
    if g==17 and sample==0:
     k=[1,8,9,10,11][rep]*1000; comp=[1,2,3,100,100][rep]*1000
    else:k=round(r*100_000);comp=100_000
    for order in range(5):
     alg=c.ALGORITHMS[(rep+order)%5];ix=c.ALGORITHMS.index(alg)
     ns=k if ix==0 else comp*ix; cpuns=ns*9//10 if ix==0 else ns*8//10
     rows.append({**spec,'graph_seed':g,'kkt_seed':sample,'input_fingerprint':g,'topology_fingerprint':g,'phase':phase,'repetition':rep,'order':order,'warmups':1,'algorithm':alg,'elapsed_ns':ns,'utc_start_ns':utc,'utc_end_ns':utc+ns,'process_cpu_start_ns':cpu,'process_cpu_end_ns':cpu+cpuns,'process_cpu_elapsed_ns':cpuns,'validation':'pass'})
     cpu+=cpuns+10;utc+=ns+10
out=a.aggregate(rows)
case={(r['metric'],r['competitor']):r for r in out['comparisons']}
for ix,alg in enumerate(c.ALGORITHMS[1:],1):
 assert case['wall',alg]['median_paired_ratio']==6/ix
 assert case['cpu',alg]['median_paired_ratio']==6.75/ix
 assert case['wall',alg]['pairs']==45
 assert sum(case['wall',alg][f] for f in ['individual_wins','individual_losses','individual_ties'])==45
raw=[r['kkt_over_competitor'] for r in out['paired_ratios'] if r['metric']=='wall' and r['competitor']=='compacting_boruvka']
assert statistics.median(raw)==4 and case['wall','compacting_boruvka']['median_paired_ratio']==6
assert len(out['paired_ratios'])==360
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'clock.csv';child=[r for r in rows if r['graph_seed']==17 and r['kkt_seed']==0]
 def save(rs):
  with p.open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=c.FIELDS);w.writeheader();w.writerows(rs)
 save(child);parsed,diag=c.check_rows(p,spec,17,0,5,1)
 assert len(parsed)==30 and not any(d['diagnostic_flags'] for d in diag)
 changed=copy.deepcopy(child);changed[9]['elapsed_ns']+=2_000_000_000;changed[9]['utc_end_ns']+=2_000_000_000
 save(changed);parsed,diag=c.check_rows(p,spec,17,0,5,1)
 assert len(parsed)==30 and 'steady_exceeds_process_cpu' in diag[9]['diagnostic_flags'] and all(not d['excluded'] for d in diag)
 changed=copy.deepcopy(child);changed[9]['utc_end_ns']=changed[9]['utc_start_ns']-1
 save(changed);parsed,diag=c.check_rows(p,spec,17,0,5,1)
 assert len(parsed)==30 and 'realtime_reversed_within_call' in diag[9]['diagnostic_flags'] and all(not d['excluded'] for d in diag)
result={'validation':'pass','native_calls':0,'checks':['270-row 3graph x3sampling full five-algorithm synthetic data','paired nested median6 differs from pooled4','independent CPU paired median6.75','45pairs per competitor per metric;360total; wins+losses+ties complete','single-child full30-call balanced schedule','sleep-affected call retained and flagged','reversed UTC call retained and flagged'],'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/'benchmark/run_mst_search.py',root/'benchmark/analyze_mst_search.py']}}
print(json.dumps(result,indent=2))
