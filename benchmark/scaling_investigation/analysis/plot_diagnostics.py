#!/usr/bin/env python3
"""Diagnostic figures from strict canonical tables; never benchmarks solvers."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PHASES='api input recursion contraction minimum_scan sampling isolation forest_recovery partition tree_setup fbt lca_build queries query_gather mark_scatter path_solve median_table path_walk filtering output'.split()
FAMILIES=('leaf_hierarchy4','leaf_shuffled4','gnm_random')
GRAPHS=(19000013,19000043)
SEEDS=(3001,3011)
COLORS=('#087f8c','#bd622e','#405ca1','#87609c')
LABELS=('G1/S3001','G1/S3011','G2/S3001','G2/S3011')
COUNTS=('kkt_edges','contraction_edge_visits','sampling_edge_visits','verifier_edge_visits',
        'verifier_queries','path_query_visits','path_binary_search_steps','lca_queries',
        'lca_sparse_cells','initialized_slots','edge_materializations','median_entries')
EVENTS=('input','minimum_scan','sampling','forest_recovery','fbt','lca_build',
        'query_gather','mark_scatter','median_table','path_walk','filtering','output')
FIT_COUNTS=('kkt_edges','contraction_edge_visits','verifier_queries','path_binary_search_steps',
            'lca_sparse_cells','initialized_slots','edge_materializations')
GROUPS={'API/input/output/outside':('api','input','output','outside_collector'),
        'Contraction':('contraction','minimum_scan'),
        'Sampling/recovery/filter':('sampling','isolation','forest_recovery','filtering'),
        'Recursion exclusive':('recursion',),'Partition/tree setup':('partition','tree_setup'),
        'FBT/LCA build':('fbt','lca_build'),'Query gather/scatter':('queries','query_gather','mark_scatter'),
        'Compressed path':('path_solve','median_table','path_walk')}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();source=args.analysis.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    bound={str(Path(__file__).resolve()):sha(__file__)}
    p=source/'provenance.json';bound[str(p)]=sha(p);info=json.loads(p.read_text())
    assert info['validation']=='pass' and info['exact_google_joins']==72
    assert info['raw_counts']==dict(phase=288,work=144,allocation=36,calibration=48)
    for path,digest in info['input_sha256'].items():
        assert sha(path)==digest, 'Analysis input drift: '+path
        assert path not in bound or bound[path]==digest
        bound[path]=digest
    tables={}
    for name in ('phase_summary','phase_per_event','work','historical_cpu_work','allocation_summary',
                 'calibration_pairs','calibration_summary','endpoint_contributions'):
        path=source/(name+'.csv');digest=sha(path);assert digest==info['output_sha256'][path.name]
        tables[name]=list(csv.DictReader(path.open()));assert len(tables[name])==info['table_counts'][name]
        bound[str(path)]=digest
    plt.rcParams.update({'font.size':10,'axes.titlesize':11,'axes.labelsize':10,'axes.spines.top':False,
                         'axes.spines.right':False,'figure.facecolor':'white','savefig.facecolor':'white'})
    outputs=[]

    def save(fig,name):
        for ext in ('png','svg'):
            path=out/(name+'.'+ext);fig.savefig(path,dpi=160);outputs.append(path)
        plt.close(fig)

    def grid(family,table,field,metrics,yfield,title,ylabel,filename,low=None,high=None,range_per_N=True):
        fig,axes=plt.subplots(math.ceil(len(metrics)/4),4,figsize=(16,3.15*math.ceil(len(metrics)/4)+1.2),squeeze=False)
        panel_rows=[r for r in tables[table] if r['family']==family]
        for ax,metric in zip(axes.flat,metrics):
            undefined=0
            for k,(g,s) in enumerate((g,s) for g in GRAPHS for s in SEEDS):
                rows=sorted((r for r in panel_rows if r[field]==metric and int(r['graph_seed'])==g and int(r['sampling_seed'])==s),key=lambda r:int(r['n']))
                assert len(rows)==6, 'Incomplete plotted metric/curve: '+metric
                undefined+=sum(r[yfield]=='' for r in rows);rows=[r for r in rows if r[yfield]!='']
                if not rows:continue
                xs=[int(r['n']) for r in rows];ys=[float(r[yfield]) for r in rows]
                ax.plot(xs,ys,color=COLORS[k],marker='o',markersize=3,label=LABELS[k],linestyle='-' if k%2==0 else '--',linewidth=1.2)
                if low is not None:
                    ax.fill_between(xs,[float(r[low])/((int(r['n'])+int(r['m'])) if range_per_N else 1) for r in rows],
                                    [float(r[high])/((int(r['n'])+int(r['m'])) if range_per_N else 1) for r in rows],color=COLORS[k],alpha=.10)
            ax.set_title(metric.replace('_',' '));ax.set_xscale('log',base=4)
            ax.set_xticks([1024,16384,262144,1048576],['1K','16K','256K','1M']);ax.set_xlabel('Vertices n')
            ax.set_ylabel(ylabel);ax.grid(alpha=.16);ax.set_ylim(0,ax.get_ylim()[1]*1.06)
            if undefined:ax.text(.02,.95,f'{undefined} undefined zero-denominator points',transform=ax.transAxes,va='top',fontsize=8)
        for ax in list(axes.flat)[len(metrics):]:ax.set_visible(False)
        handles,labels=axes.flat[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=4,bbox_to_anchor=(.5,.035))
        fig.suptitle(title+' — '+family,fontsize=15,y=.99)
        fig.text(.5,.012,'Diagnostic data; no uninstrumented performance claim. G1 ascends, G2 descends. All seeds retained; full tables accompany figures.',ha='center',fontsize=9)
        fig.tight_layout(rect=(0,.09,1,.96));save(fig,filename)

    for family in FAMILIES:
        grid(family,'phase_summary','phase',PHASES,'median_ns_per_N','Exclusive phase wall time / N','ns / (n+m)',
             'phase-'+family,low='minimum',high='maximum')
        grid(family,'work','counter',COUNTS,'per_N','Exact logical counts / N','Logical events / (n+m)','counts-'+family)
        grid(family,'phase_per_event','phase',EVENTS,'ns_per_event','Phase wall time / declared logical event','Median phase ns / event','phase-cost-'+family,
             low='minimum_ns_per_event',high='maximum_ns_per_event',range_per_N=False)
        grid(family,'historical_cpu_work','counter',FIT_COUNTS,'historical_cpu_ns_per_counter',
             'Historical total CPU / matching new count (not phase cost)','Old total CPU ns / named event','historical-cost-'+family,
             low='historical_minimum_cpu_ns_per_counter',high='historical_maximum_cpu_ns_per_counter',range_per_N=False)

    metrics=('peak_live_usable_bytes','returned_live_usable_bytes','cumulative_requested_bytes','cumulative_usable_bytes','cumulative_allocations')
    fig,axes=plt.subplots(3,5,figsize=(18,10),squeeze=False)
    for i,family in enumerate(FAMILIES):
        for j,metric in enumerate(metrics):
            ax=axes[i,j]
            for k,g in enumerate(GRAPHS):
                rows=sorted((r for r in tables['allocation_summary'] if r['family']==family and r['metric']==metric and int(r['graph_seed'])==g),key=lambda r:int(r['n']))
                assert len(rows)==3 and all(int(r['sampling_seed'])==3001 for r in rows)
                ax.plot([int(r['n']) for r in rows],[float(r['median_per_N']) for r in rows],color=COLORS[k*2],marker='o',label=f'G{k+1}/S3001')
            ax.set_title(metric.replace('_',' '));ax.set_xscale('log',base=4);ax.set_xticks([16384,262144,1048576],['16K','256K','1M'])
            ax.set_ylabel(family+'\n'+('Allocations / N' if metric=='cumulative_allocations' else 'Bytes / N'));ax.set_ylim(0,ax.get_ylim()[1]*1.06);ax.grid(alpha=.16)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=2,bbox_to_anchor=(.5,.035))
    fig.suptitle('Allocator diagnostics: live usable bytes are not cumulative allocated bytes',fontsize=15)
    fig.text(.5,.015,'One measured call per input; warmup retained separately. C++ new/delete within solver scope, not RSS or all libc allocation.',ha='center',fontsize=10)
    fig.tight_layout(rect=(0,.09,1,.95));save(fig,'allocation')

    assert set(p for ps in GROUPS.values() for p in ps)==set(PHASES)|{'outside_collector'}
    assert sum(len(ps) for ps in GROUPS.values())==21
    fig,axes=plt.subplots(1,3,figsize=(17,6),squeeze=False)
    group_colors=plt.get_cmap('tab10').colors
    for ax,family in zip(axes.flat,FAMILIES):
        bottom_pos=[0.]*4;bottom_neg=[0.]*4
        for i,(group,names) in enumerate(GROUPS.items()):
            values=[]
            for g,s in ((g,s) for g in GRAPHS for s in SEEDS):
                rows=[r for r in tables['endpoint_contributions'] if r['family']==family and int(r['graph_seed'])==g and int(r['sampling_seed'])==s and r['phase'] in names]
                assert len(rows)==len(names);values.append(sum(float(r['mean_delta_ns_per_N']) for r in rows))
            bottom=[bottom_pos[k] if y>=0 else bottom_neg[k] for k,y in enumerate(values)]
            ax.bar(range(4),values,bottom=bottom,color=group_colors[i],label=group,width=.7)
            for k,y in enumerate(values):
                if y>=0:bottom_pos[k]+=y
                else:bottom_neg[k]+=y
        total=[float(next(r['mean_delta_ns_per_N'] for r in tables['endpoint_contributions'] if r['family']==family and int(r['graph_seed'])==g and int(r['sampling_seed'])==s and r['phase']=='total')) for g in GRAPHS for s in SEEDS]
        ax.scatter(range(4),total,color='black',marker='_',s=130,zorder=5,label='Total mean change');ax.axhline(0,color='black',lw=.6)
        ax.set_xticks(range(4),LABELS,rotation=20,ha='right');ax.set_title(family);ax.set_ylabel('Change in mean wall ns / N');ax.grid(axis='y',alpha=.15)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=3,bbox_to_anchor=(.5,.03),fontsize=9)
    fig.suptitle('Where the diagnostic extra ns/N occurs: 1K → 1M',fontsize=15)
    fig.text(.5,.012,'Untrimmed arithmetic means preserve additivity. Grouped phases partition all exclusive clocks plus outside-collector time; this is not CPU attribution.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.24,1,.93));save(fig,'endpoint-contributions')

    fig,axes=plt.subplots(1,2,figsize=(13,5.5),squeeze=False)
    for ax,clock in zip(axes.flat,('wall_ns','cpu_ns')):
        labels=[]
        for i,(family,n) in enumerate((f,n) for f in FAMILIES for n in (1024,1048576)):
            rows=[r for r in tables['calibration_pairs'] if r['family']==family and int(r['n'])==n and r['clock']==clock]
            assert len(rows)==3
            for offset,r in zip((-.09,0,.09),rows):ax.scatter(i+offset,float(r['phase_over_reference']),color=COLORS[0],s=23,alpha=.65)
            r=next(r for r in tables['calibration_summary'] if r['family']==family and int(r['n'])==n and r['clock']==clock)
            ax.scatter(i,float(r['median_paired_ratio']),color='black',marker='_',s=150)
            ax.scatter(i,float(r['ratio_of_medians']),color=COLORS[1],marker='x',s=40)
            labels.append(family.replace('leaf_','')+'\n'+('1K' if n==1024 else '1M'))
        ax.axhline(1,color='gray',lw=1);ax.set_xticks(range(6),labels,rotation=20,ha='right');ax.set_ylabel('Phase-instrumented / reference');ax.set_title('Wall' if clock=='wall_ns' else 'Process CPU');ax.grid(axis='y',alpha=.15)
    fig.suptitle('Calibration of phase instrumentation, not a solver speedup test',fontsize=14)
    fig.text(.5,.02,'G1/S3001 only. Teal: matched-repetition ratios; black: their median; orange ×: ratio of medians. Order alternates by case; no correction applied.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.13,1,.92));save(fig,'calibration')
    for path,digest in bound.items():assert sha(path)==digest
    (out/'provenance.json').write_text(json.dumps(dict(validation='pass',native_execution=False,input_sha256=bound,
        matplotlib=matplotlib.__version__,figures=len(outputs)//2,output_sha256={p.name:sha(p) for p in outputs},
        status='Rendering complete; visual inspection is a separate gate.'),indent=2)+'\n')


if __name__=='__main__':main()
