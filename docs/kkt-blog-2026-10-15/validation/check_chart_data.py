import csv,json,hashlib,math,sys
from pathlib import Path
from collections import defaultdict
from fractions import Fraction
from statistics import median
root=Path(__file__).resolve().parents[3]
blog=root/'docs/kkt-blog-2026-10-15'; tables=blog/'chart-data'/sys.argv[1]
bound={}
def read(path):
 d=hashlib.sha256(path.read_bytes()).hexdigest();rows=list(csv.DictReader(path.open()));assert hashlib.sha256(path.read_bytes()).hexdigest()==d;bound[str(path.relative_to(root))]=d;return rows
def equal(a,b):assert math.isclose(float(a),float(b),rel_tol=1e-14,abs_tol=1e-12),(a,b)
low=root/'benchmark/results/lower-density-2026-10-15'
rows=read(low/'analysis-attempt01/validated_calls.csv'); lookup={}; by_case={}
for r in rows:
 if r['phase']=='timed':lookup[(r['case_id'],r['graph_seed'],r['repetition'],r['algorithm'])]=r
 by_case[r['case_id']]=r
assert len(lookup)==2160
checked={}; graphs=['23000003','23000029']; fields={'wall':'elapsed_ns','cpu':'process_cpu_elapsed_ns'}
for name,count in [('crossover',28),('reversal',6),('endpoints',48),('endpoint_ratios',40)]:
 out=read(tables/(name+'.csv'));assert len(out)==count
 seen=set()
 for r in out:
  case=r['case_id'];field=fields[r['clock']]; alg=r.get('algorithm',r.get('competitor'));k=(case,alg,r['clock']);assert k not in seen;seen.add(k)
  for f in ['family','n','m','density']:assert r[f]==by_case[case][f]
  allvalues=[];gv=[]
  for g in graphs:
   v=[]
   for rep in range(6):
    if name=='endpoints':x=Fraction(int(lookup[(case,g,str(rep),alg)][field]))
    else:x=Fraction(int(lookup[(case,g,str(rep),'kkt')][field]),int(lookup[(case,g,str(rep),alg)][field]))
    v.append(x)
   allvalues+=v;gv.append(median(v))
  for f,x in [('value',median(allvalues)),('minimum',min(allvalues)),('maximum',max(allvalues)),('g1',gv[0]),('g2',gv[1])]:equal(r[f],x)
  for f,x in [('exact_median',median(allvalues)),('exact_g1',gv[0]),('exact_g2',gv[1])]:assert Fraction(r[f])==x
 expected_cases={c for c,r in by_case.items() if (name=='crossover' and r['density']=='16') or (name=='reversal' and r['family']=='leaf_distance4' and r['density']=='8' and int(r['n'])>=262144) or (name in ['endpoints','endpoint_ratios'] and int(r['m'])==33554432)}
 assert {r['case_id'] for r in out}==expected_cases;checked[name]=len(out)
work=read(low/'work/analysis-attempt01/work.csv');assert len(work)==180
index={(r['case_id'],r['graph_seed'],r['algorithm']):r for r in work}
out=read(tables/'volume.csv');assert len(out)==120
for r in out:
 w=index[(r['case_id'],r['graph_seed'],r['algorithm'])];assert int(r['count'])==int(w['contraction_edges']);equal(r['per_m'],Fraction(int(w['contraction_edges']),int(w['m'])))
assert {(r['case_id'],r['graph_seed'],r['algorithm']) for r in out}=={k for k in index if k[2] in ['kkt','multigraph_boruvka']};checked['volume']=len(out)
p=read(low/'work/partition-analysis-attempt01/partition.csv');assert len(p)==60
for r in p:
 w=index[(r['case_id'],r['graph_seed'],'kkt')];base=2*int(w['verifier_tree_edges'])+2*(int(w['fbt_output_vertices'])-int(w['fbt_calls']));part=int(w['verifier_edge_visits'])-base
 assert int(r['disconnected_partition_edge_visits'])==part and part>=0
out=read(tables/'partition.csv');assert {r['graph_seed'] for r in out}==set(graphs)
for r in out:
 w=index[('leaf_distance4_n4194304_d8_p0',r['graph_seed'],'kkt')];base=2*int(w['verifier_tree_edges'])+2*(int(w['fbt_output_vertices'])-int(w['fbt_calls']));part=int(w['verifier_edge_visits'])-base
 for f,v in [('base',base),('partition',part),('total',base+part)]:assert int(r[f])==v
 equal(r['base_per_m'],Fraction(base,int(w['m'])));equal(r['partition_per_m'],Fraction(part,int(w['m'])))
checked['partition_identities']=60;checked['partition_plot_rows']=2
gb=root/'benchmark/results/current-complexity-2026-10-15'; cp=gb/'capture-attempt01/capture.json';capture=json.loads(cp.read_text());bound[str(cp.relative_to(root))]=hashlib.sha256(cp.read_bytes()).hexdigest()
cpu=defaultdict(list)
for child in capture['captures']:
 for r in read(Path(child['raw_csv'])):
  if r['phase']=='timed':cpu[tuple(r[f] for f in ['family','algorithm','graph_seed','sampling_seed','n'])].append(int(r['process_cpu_elapsed_ns']))
out=read(tables/'complexity.csv');assert len(out)==len(cpu)==264
seen=set()
for r in out:
 k=tuple(r[f] for f in ['family','algorithm','graph_seed','sampling_seed','n']);assert k not in seen;seen.add(k);v=cpu[k];assert len(v)==6
 n=int(r['N']);assert n==int(r['n'])*(17 if r['family']=='gnm_random' else 33)
 for f,z in [('minimum_ns',min(v)),('median_ns',median(v)),('maximum_ns',max(v)),('minimum_ns_per_N',Fraction(min(v),n)),('median_ns_per_N',median([Fraction(t,n) for t in v])),('maximum_ns_per_N',Fraction(max(v),n))]:equal(r[f],z)
checked['native_cpu_summaries']=264
assert read(tables/'google_choices.csv')==read(gb/'analysis-attempt01/google_selection.csv');checked['google_choices']=24
for f,d in bound.items():assert hashlib.sha256((root/f).read_bytes()).hexdigest()==d
result={'schema':'independent_kkt_blog_chart_arithmetic_v1','validation':'pass','attempt':sys.argv[1],'native_execution':False,'collector_or_plotter_imported':False,'checks':checked,'scope':'Numeric CSV review only; independent rational reconstruction from archived calls/counters. No visual or rendered-element check. Model choice inventory is compared, not independently refitted. Prior independent audits remain source/provenance authority.','input_sha256':bound}
output=Path(sys.argv[2]);output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'validation':'pass','checks':checked}))
