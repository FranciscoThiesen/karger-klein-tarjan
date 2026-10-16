#!/usr/bin/env python3
"""Plot all native-CPU curves and fixed blocked predictions; no new fitting."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import statistics

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

FAMILIES=('leaf_hierarchy4','leaf_shuffled4','gnm_random')
ALGORITHMS=('kkt','multigraph_boruvka')
GRAPHS=(19000013,19000043)
SAMPLERS=(3001,3011)
COLORS=('#087f8c','#c25e2d','#455c9b','#826089')
LABELS=('G1/S3001','G1/S3011','G2/S3001','G2/S3011')

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    source=args.analysis.resolve(); output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    provenance=source/'provenance.json'; inputs={str(provenance):digest(provenance),str(Path(__file__).resolve()):digest(Path(__file__))}
    info=json.loads(provenance.read_text()); assert info['validation']=='pass'
    tables={}
    for name in ('means','holdouts'):
        path=source/(name+'.csv');assert digest(path)==info['output_sha256'][path.name]
        inputs[str(path)]=digest(path)
        tables[name]=list(csv.DictReader(path.open()))
    plt.rcParams.update({'font.size':11,'axes.labelsize':11,'axes.titlesize':12,'figure.facecolor':'white','axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(3,2,figsize=(11,10),squeeze=False)
    for i,family in enumerate(FAMILIES):
        for j,algorithm in enumerate(ALGORITHMS):
            ax=axes[i,j]
            rows=[r for r in tables['means'] if r['family']==family and r['algorithm']==algorithm and r['clock']=='native_process_cpu']
            for k,(g,s) in enumerate((g,s) for g in GRAPHS for s in SAMPLERS):
                selected=[r for r in rows if int(r['graph_seed'])==g and int(r['sampling_seed'])==s]
                sizes=sorted({int(r['n']) for r in selected})
                xs=[int(r['n']) for r in selected];ys=[float(r['mean_ns'])/int(r['N']) for r in selected]
                ax.scatter(xs,ys,c=COLORS[k],s=11,alpha=.4)
                ax.plot(sizes,[statistics.median(float(r['mean_ns'])/int(r['N']) for r in selected if int(r['n'])==n) for n in sizes],
                        color=COLORS[k],label=LABELS[k],linewidth=1.4,linestyle='-' if k%2==0 else '--')
            ax.set_xscale('log',base=2);ax.set_xticks([1024,16384,262144,1048576],['1K','16K','256K','1M'])
            ax.set_title(f"{family.replace('leaf_','')} / {'KKT' if algorithm=='kkt' else 'retained Boruvka'}")
            ax.set_ylabel('Native process CPU / (n+m) [ns]');ax.grid(alpha=.18)
            if i==2:ax.set_xlabel('Vertices n')
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=4,bbox_to_anchor=(.5,.035))
    fig.suptitle('The measured cost per input unit rises, but not at one fixed rate',fontsize=15,y=.98)
    fig.text(.5,.012,'Dots: every two-call mean. Lines: median of three means. G1 sizes ascend; G2 descend. Retained B ignores S.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.08,1,.95))
    for ext in ('svg','png'):fig.savefig(output/f'normalization.{ext}',dpi=180)
    plt.close(fig)
    models=('N','NlgN','affine_N','affine_NlgN','hinge_16384','hinge_65536')
    labels=('N','N log N','a+bN','a+bN log N','hinge16K','hinge64K')
    fig,axes=plt.subplots(3,2,figsize=(11,10),squeeze=False)
    for i,family in enumerate(FAMILIES):
        for j,algorithm in enumerate(ALGORITHMS):
            ax=axes[i,j]
            rows=[r for r in tables['holdouts'] if r['family']==family and r['algorithm']==algorithm and r['clock']=='native_process_cpu' and r['fold']=='first8_last3']
            for k,(g,s) in enumerate((g,s) for g in GRAPHS for s in SAMPLERS):
                selected={r['model']:r for r in rows if int(r['graph_seed'])==g and int(r['sampling_seed'])==s}
                assert all(selected[m]['status']=='identified' for m in models)
                ax.plot(range(len(models)),[float(selected[m]['normalized_rms'])*100 for m in models],
                        color=COLORS[k],marker='o',markersize=4,linewidth=1.1,label=LABELS[k],linestyle='-' if k%2==0 else '--')
            ax.set_xticks(range(len(models)),labels,rotation=25,ha='right');ax.set_ylim(bottom=0)
            ax.set_ylabel('Held-out normalized RMS [%]');ax.grid(axis='y',alpha=.18)
            ax.set_title(f"{family.replace('leaf_','')} / {'KKT' if algorithm=='kkt' else 'retained Boruvka'}")
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=4,bbox_to_anchor=(.5,.035))
    fig.suptitle('Predicting 256K, 512K and 1M from 1K through 128K',fontsize=15,y=.98)
    fig.text(.5,.012,'All nine held-out means retained per curve. Hinge256K is unidentified in training and is explicitly absent, not zero.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.08,1,.95))
    for ext in ('svg','png'):fig.savefig(output/f'blocked-prediction.{ext}',dpi=180)
    plt.close(fig)
    for path,expected in inputs.items():assert digest(Path(path))==expected
    record=dict(validation='pass',native_execution=False,matplotlib=matplotlib.__version__,input_sha256=inputs,
                output_sha256={p.name:digest(p) for p in output.iterdir() if p.is_file()},
                included_curves=24,normalization_means=792,holdout_points=144,other_clocks_and_folds='complete CSV tables linked from model note')
    (output/'provenance.json').write_text(json.dumps(record,indent=2)+'\n')

if __name__=='__main__':main()
