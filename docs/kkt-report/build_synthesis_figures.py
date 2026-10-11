#!/usr/bin/env python3
"""Print-sized report figures; full-resolution exploratory plots remain archived."""
from pathlib import Path
import csv
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
BASE=ROOT/'benchmark/results/common-2026-10-11'
NAMES={'unbalanced_bipartite_16':'Bipartite k=16','unbalanced_bipartite_256':'Bipartite k=256','unbalanced_bipartite_sqrt':'Bipartite k=floor(sqrt(n))',
'leaf_core_50':'50% attached leaves','leaf_core_90':'90% attached leaves','ring_cliques_16':'Ring of cliques (16)',
'grid2d_random':'2D grid, random weights','grid2d_distance':'2D grid, distance weights','grid3d_random':'3D grid, random weights','grid3d_distance':'3D grid, distance weights','regular_8':'Degree-eight regular','hub':'Hub control','random_4':'Random4 control','small_world':'Small-world variant'}
FAMILIES=list(NAMES)[:-1];SIZES=[4096,16384,65536,262144]

def read(path):return list(csv.DictReader(path.open()))
def save(fig,name):
 for ext in ('png','svg'):
  fig.savefig(HERE/'figures'/(name+'.'+ext),dpi=240,bbox_inches='tight',facecolor='white')
 plt.close(fig)

def main():
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
 rows=read(BASE/'primary_analysis/comparisons.csv')
 lookup={(r['family'],int(r['n']),r['reference']):float(r['paired_runtime_ratio']) for r in rows if r['algorithm']=='kkt'}
 values=np.array([[[lookup[f,n,a] for n in SIZES] for f in FAMILIES] for a in ('kruskal','prim','boruvka')])
 low=min(-1,float(np.floor(np.log2(values.min()))));high=max(1,float(np.ceil(np.log2(values.max()))))
 norm=TwoSlopeNorm(vmin=low,vcenter=0,vmax=high);cmap=plt.get_cmap('RdBu_r')
 fig,axs=plt.subplots(1,3,figsize=(7.2,4.55),sharey=True)
 for i,(ax,name) in enumerate(zip(axs,['Kruskal','Prim','Borůvka'])):
  ax.imshow(np.log2(values[i]),cmap=cmap,norm=norm,aspect='auto')
  for y in range(len(FAMILIES)):
   for x in range(4):
    z=float(np.log2(values[i,y,x]));color='white' if norm(z)<.18 or norm(z)>.83 else '#142d3f'
    ax.text(x,y,f'{values[i,y,x]:.2f}',ha='center',va='center',fontsize=7.4,color=color)
  ax.set_title('KKT / '+name,fontsize=9,pad=10);ax.set_xticks(range(4),['4k','16k','65k','262k']);ax.set_xlabel('Vertices (rounded)',fontsize=7.5)
  ax.tick_params(axis='both',length=0,labelsize=7.3);ax.spines[['left','bottom']].set_visible(False)
 axs[0].set_yticks(range(len(FAMILIES)),[NAMES[f] for f in FAMILIES],fontsize=7.6)
 fig.subplots_adjust(left=.26,right=.99,top=.9,bottom=.13,wspace=.13)
 fig.text(.26,.99,'All 52 new cases · primary matched ratios',va='top',fontsize=10,weight='bold')
 fig.text(.26,.015,'Blue < 1: KKT faster. Red > 1: competitor faster. No uncertainty encoded here;\ngraph ranges and repeat results remain in the full tables.',fontsize=7.1)
 save(fig,'all_family_heatmap')

 rows=read(ROOT/'benchmark/results/practical-2026-10-10/overall_analysis/before_after.csv')
 cases=[('random_4_n65536','Random4 · 65,536'),('random_32_n65536','Random32 · 65,536'),('hub_n16384','Hub · 16,384'),('star_n16384','Star · 16,384'),('geometric_grid_n16384','Geometric grid · 16,384'),('complete_n1024','Complete · 1,024')]
 lookup={r['case_id']:r for r in rows if r['suite']=='diverse' and r['algorithm']=='kkt'}
 fig,ax=plt.subplots(figsize=(6.6,2.4))
 vals=[float(lookup[c]['paired_final_over_baseline']) for c,_ in cases]
 ax.barh(range(len(cases)),vals,color='#007e88',height=.62);ax.set_yticks(range(len(cases)),[n for _,n in cases]);ax.invert_yaxis()
 for i,v in enumerate(vals):ax.text(v+.015,i,f'{v:.3f}×',va='center',fontsize=8)
 ax.axvline(1,color='#536571',ls='--',lw=1);ax.set_xlim(0,1.12);ax.set_xlabel('Final KKT / already structurally repaired baseline');ax.grid(axis='x',alpha=.15)
 ax.set_title('Six examples from the 39-case practical optimization study',loc='left',fontsize=10);fig.tight_layout();save(fig,'practical_changes')

 rows=read(BASE/'diagnostics/complexity_analysis/timing_summary.csv')
 families=['unbalanced_bipartite_16','ring_cliques_16','grid3d_distance','leaf_core_90','regular_8']
 fig,axs=plt.subplots(3,2,figsize=(7.2,6.1),constrained_layout=True)
 for ax,f in zip(axs.flat,families):
  for a,color in [('KKT','#007e88'),('Kruskal','#bd693d')]:
   selected=sorted([r for r in rows if r['family']==f and r['algorithm']==a],key=lambda r:int(r['n']))
   x=[int(r['n']) for r in selected];y=[float(r['ns_per_input']) for r in selected]
   ax.plot(x,y,'-o',ms=2.4,lw=1.1,label=a,color=color)
   ax.fill_between(x,[float(r['graph_min_time_ns'])/float(r['input_size']) for r in selected],[float(r['graph_max_time_ns'])/float(r['input_size']) for r in selected],color=color,alpha=.15,linewidth=0)
  ax.set_xscale('log',base=2);ax.set_xticks([1024,16384,262144],['1,024','16,384','262,144']);ax.set_title(NAMES[f],loc='left',fontsize=9)
  ax.set_xlabel('Vertices n',fontsize=7.8);ax.set_ylabel('ns / (n + m)',fontsize=7.8);ax.tick_params(labelsize=7.4);ax.grid(alpha=.16)
 axs.flat[0].legend(frameon=False,fontsize=7.5);axs.flat[-1].axis('off');axs.flat[-1].text(0,.88,'Manual time; Google Benchmark build.\n\nA flat line supports linear timing\nwithin the measured window.\n\nShading spans three graph means,\nnot a confidence interval.',va='top',fontsize=8,linespacing=1.6)
 save(fig,'complexity_normalized')

 rows=read(BASE/'diagnostics/ablation_analysis/paired_summary.csv')
 fams=['unbalanced_bipartite_16','leaf_core_90','ring_cliques_16','grid3d_distance','regular_8','random_4','small_world']
 fig,ax=plt.subplots(figsize=(7.1,3.4))
 for run,offset,color,marker in [('primary',-.13,'#86559b','o'),('confirmation',.13,'#007e88','s')]:
  selected=[next(r for r in rows if r['family']==f and int(r['n'])==(65536 if f=='small_world' else 262144) and r['run']==run) for f in fams]
  x=[float(r['paired_runtime_ratio']) for r in selected]
  ax.errorbar(x,np.arange(7)+offset,xerr=[[v-float(r['graph_min_ratio']) for v,r in zip(x,selected)],[float(r['graph_max_ratio'])-v for v,r in zip(x,selected)]],fmt=marker,color=color,ms=4,capsize=2,label='Repeat' if run=='confirmation' else 'Primary')
 ax.axvline(1,color='#536571',ls='--',lw=1);ax.set_xscale('log',base=2);ax.set_yticks(range(7),[NAMES[f]+(' · 65,536' if f=='small_world' else ' · 262,144') for f in fams],fontsize=8);ax.invert_yaxis();ax.legend(frameon=False,fontsize=8)
 ax.set_xlabel('KKT / repeated production contraction (below 1 favors KKT)',fontsize=8);ax.grid(axis='x',alpha=.15)
 from matplotlib.ticker import FuncFormatter, NullLocator
 ax.set_xticks([.95,1,1.1,1.2,1.3,1.4]);ax.xaxis.set_minor_locator(NullLocator())
 ax.xaxis.set_major_formatter(FuncFormatter(lambda x,pos:f'{x:g}×'))
 ax.set_title('Largest available case of each ablation family',loc='left',fontsize=10);fig.tight_layout();save(fig,'ablation_largest')
 print('Built four compact, print-sized synthesis figures.')

if __name__=='__main__':main()
