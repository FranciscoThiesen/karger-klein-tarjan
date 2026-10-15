#!/usr/bin/env python3
"""Plot preselected work counters only after the complete audited capture.

Prepared before reading any diagnostic counter output. Work is not CPU cost.
Install beside the study's collect.py before invoking it.
"""
import argparse
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
FIELDS = (
    ('sampled_edges', 'Edges accepted into samples'),
    ('filtered_edges', 'Edges surviving filtering'),
    ('contraction_edge_visits', 'Contraction edge visits'),
    ('sampling_edge_visits', 'Sampling visits / RNG words'),
    ('verifier_edge_visits', 'Verifier edge visits'),
    ('path_query_visits', 'Path-query visits'),
    ('initialized_slots', 'Explicit initialized slots'),
    ('edge_materializations', 'Explicit edge materializations'),
)
GROUPS = ('leaf_hierarchy4', 'leaf_shuffled4', 'gnm_random')
LABELS = ('Ordered hierarchy', 'Shuffled twin', 'Random G(n,m)')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--released', action='store_true')
    args = parser.parse_args()
    def digest(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    inputs = {str(p.resolve(strict=True)): digest(p) for p in
              (args.capture, args.audit, Path(__file__), HERE/'collect.py')}
    spec = importlib.util.spec_from_file_location('eighth_work_plot_collector', HERE/'collect.py')
    work = importlib.util.module_from_spec(spec); spec.loader.exec_module(work)
    require = work.require
    require(args.released, 'postcapture plot release required')
    output = args.output.resolve()
    require(not output.exists(), 'refusing to overwrite output')
    audit = json.loads(args.audit.read_text())
    for key,value in dict(schema='independent_eighth_work_counter_audit_v1',validation='pass',
                         checked_children=48,solver_rows=144,counter_fields=65,counter_cells=9360,
                         query_rows=48,paired_kkt_counter_rows=1560,engine_words_exact=True,
                         collector_imported=False,aggregation_reused=False).items():
        require(type(audit.get(key)) is type(value) and audit[key]==value, 'wrong audit '+key)
    require(audit['input_sha256'].get(str(args.capture.resolve(strict=True))) == work.native.sha(args.capture),
            'audit does not bind this capture')
    for path,digest in audit['input_sha256'].items():
        work.analysis.hash_check(Path(path),digest)
        require(path not in inputs or inputs[path] == digest, 'conflicting input digest '+path)
    inputs.update(audit['input_sha256'])
    info, values = work.load(args.capture)
    pairs = {}
    for identity, result in values:
        key = (identity['case_id'], identity['graph_seed'], identity['kkt_seed'])
        pairs.setdefault(key, {})[identity['variant']] = (identity, result['algorithms']['kkt']['work'])
    require(len(pairs) == 24, 'incomplete realization pairs')
    records = []; cases = {}
    for key, variants in pairs.items():
        require(set(variants) == {'half', 'eighth'}, 'missing variant')
        identity, half = variants['half']; _, eighth = variants['eighth']
        cases[key[0]] = {k: identity[k] for k in ('case_id', 'family', 'n', 'm')}
        for field, label in FIELDS:
            a, b = half[field], eighth[field]
            ratio = Fraction(b,a) if a else None
            records.append(dict(case_id=key[0],graph_seed=key[1],kkt_seed=key[2],counter=field,
                half=a,eighth=b,ratio_numerator=ratio.numerator if ratio is not None else None,
                ratio_denominator=ratio.denominator if ratio is not None else None,
                ratio=float(ratio) if ratio is not None else None,
                status='defined' if a else 'both_zero' if not b else 'half_zero'))
    require(len(records) == 192 and len(cases) == 6, 'incomplete selected counter matrix')
    positive = [r['ratio'] for r in records if r['ratio'] is not None and r['ratio'] > 0]
    require(positive and all(math.isfinite(x) for x in positive), 'nonfinite plotted ratio')
    lo, hi = min(*positive,1)/1.30, max(*positive,1)*1.30
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FuncFormatter
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                         'axes.spines.right':False,'svg.fonttype':'none','pdf.fonttype':42})
    fig, axes = plt.subplots(2,3,figsize=(18,10.5),sharex=True)
    summaries=[]
    for column, (family,title) in enumerate(zip(GROUPS,LABELS)):
        selected=sorted((c for c in cases.values() if c['family']==family),key=lambda c:c['n'])
        require(len(selected)==2, 'missing family size')
        for row,case in enumerate(selected):
            ax=axes[row,column]
            for y,(field,label) in enumerate(FIELDS):
                data=sorted((r for r in records if r['case_id']==case['case_id'] and r['counter']==field),
                            key=lambda r:(r['graph_seed'],r['kkt_seed']))
                require(len(data)==4,'missing realization')
                exact=[Fraction(r['eighth'],r['half']) for r in data if r['half']]
                points=[float(x) for x in exact if x>0]
                undefined=[r['status'] for r in data if r['status']!='defined']
                zero=sum(x==0 for x in exact)
                if points: ax.hlines(y,min(points),max(points),color='#226b8a',alpha=.4,lw=3)
                for i,r in enumerate(data):
                    if r['ratio'] is not None and r['ratio']>0:
                        ax.scatter(r['ratio'],y+(i-1.5)*.065,marker=('^','v','<','>')[i],s=31,
                                   color='#226b8a',alpha=.6,zorder=3)
                med=statistics.median(exact) if len(exact)==4 else None
                if med is not None and med>0: ax.scatter(float(med),y,color='#173c50',s=29,zorder=4)
                if undefined or zero:
                    ax.text(hi/1.02,y,'; '.join([*undefined,*(['zero ratio']*zero)]),ha='right',va='center',fontsize=8)
                summaries.append(dict(case_id=case['case_id'],counter=field,
                    all_four_defined=len(exact)==4,median_ratio=float(med) if med is not None else None,
                    zero_ratio_count=zero,undefined_statuses=undefined,
                    positive_min=min(points) if points else None,positive_max=max(points) if points else None))
            ax.axvline(1,color='#777777',ls='--',lw=1)
            ax.set_xscale('log',base=2); ax.set_xlim(lo,hi); ax.set_ylim(7.7,-.7)
            ax.set_yticks(range(8),[label for _,label in FIELDS],fontsize=9)
            ax.xaxis.set_major_formatter(FuncFormatter(lambda value,_:f'{value:g}'))
            ax.set_title(f'{title} · n = {case["n"]:,}',loc='left',fontsize=11)
            ax.grid(axis='x',alpha=.15)
            ax.set_xlabel('Eighth / half logical count · log scale')
    fig.suptitle('Lower sampling: which recursive work shrinks, and which grows?',fontsize=17,y=.99)
    handles=[Line2D([],[],color='#173c50',marker='o',ls='none',label='Median of four graph/sampler ratios'),
             Line2D([],[],color='#226b8a',marker='^',ls='none',alpha=.6,label='All four realization ratios'),
             Line2D([],[],color='#226b8a',lw=3,alpha=.4,label='Full positive-ratio range')]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.072),ncol=3,frameon=False)
    fig.text(.5,.012,'Two graphs × two sampler seeds per case; the four realizations share graphs. Counts include all recursive calls.\n'
             'Eight fields selected before diagnostic results; all 65 remain in the tables. Zero ratios and undefined denominators are annotated, not plotted on the log axis.\n'
             'These are different logical events, not CPU instructions or additive time costs. Instrumented durations are excluded.',
             ha='center',fontsize=9,linespacing=1.5)
    fig.tight_layout(rect=(0,.13,1,.95),w_pad=2,h_pad=2)
    output.mkdir(parents=True)
    exports=[]
    for extension in ('png','svg','pdf'):
        path=output/f'work_ratios.{extension}'; fig.savefig(path,dpi=180,bbox_inches='tight'); exports.append(path)
    plt.close(fig)
    work.write_json(output/'plotted_values.json',dict(records=records,summaries=summaries),exclusive=True)
    exports.append(output/'plotted_values.json')
    for path,digest in inputs.items(): work.analysis.hash_check(Path(path),digest)
    work.write_json(output/'provenance.json',dict(schema='eighth_work_figures_v1',validation='pass',
        input_sha256=inputs,capture_sha256=work.native.sha(args.capture),checked_native_inputs=48,
        selected_fields=[f for f,_ in FIELDS],selected_paired_records=192,case_counter_summaries=48,
        matched_axes=True,x_limits=[lo,hi],undefined_ratios_retained=True,
        logical_counts_are_time=False,performance_claim=False,matplotlib_version=matplotlib.__version__,
        output_sha256={p.name:work.native.sha(p) for p in exports},visual_review='pending'),exclusive=True)
    print(json.dumps(dict(validation='pass',figures=1,selected_records=192,visual_review='pending')))

if __name__=='__main__': main()
