#!/usr/bin/env python3
"""Compact paired-candidate plots with raw-derived, hash-checked plot tables."""
import argparse
import csv
from fractions import Fraction
import io
import json
from pathlib import Path
import statistics
import sys

import analyze_candidate as c

a=c.a
CLOCKS=('wall_ns','cpu_ns')
LABELS={'leaf_hierarchy4':'Ordered hierarchy + leaves','leaf_shuffled4':'Shuffled weights + leaves','gnm_random':'Connected G(n, m)'}
COLORS={'reference':'#bd571e','depth':'#007f82','work':'#687785'}


def canonical(table):
    stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=list(table[0]));writer.writeheader();writer.writerows(table)
    return list(csv.DictReader(io.StringIO(stream.getvalue())))


def load_analysis(directory,mode,bound):
    directory=directory.resolve();p=a.parse(a.read(directory/'provenance.json',bound))
    a.require(p['schema']=='kkt_depth_candidate_analysis_v1' and p['validation']=='pass' and mode in p['modes'],'analysis mode/status')
    a.require(p['native_execution'] is False and p['rows_removed']==p['rows_adjusted']==0,'analysis scope')
    c.merge(bound,p['input_sha256']);a.recheck(bound)
    actual={x.name for x in directory.iterdir() if x.is_file() and x.name!='provenance.json'}
    a.require(actual==set(p['output_sha256']),'analysis output inventory')
    for name,digest in p['output_sha256'].items():a.bind(directory/name,bound,digest)
    argv=p['invocation'];flag='--'+mode;a.require(argv.count(flag)==1,'analysis capture argument')
    capture=Path(argv[argv.index(flag)+1]);capture=capture if capture.is_absolute() else a.ROOT/capture
    info,rows,module=c.load(capture,mode,bound)
    saved=a.parse(a.read(directory/'all_raw_rows.json',bound))[mode]
    a.require(saved==rows,'canonical raw export drift')
    if mode=='work':
        build,_=module.read(info['build_record']);baseline,proof=module.baseline_work(Path(info['baseline_work']),Path(build['snapshot']));c.merge(bound,proof)
        counters,summary=c.work_tables(rows,baseline);tables={'work-counters':counters,'work-summary':summary}
    else:tables={mode+'-'+k:v for k,v in c.timing_tables(rows,mode).items()}
    for name,table in tables.items():
        stored=list(csv.DictReader(io.StringIO(a.read(directory/(name+'.csv'),bound))))
        a.require(stored==canonical(table),'canonical plot input differs from raw: '+name)
    return rows,tables,info['build_record_sha256']


def exact_fields(value,prefix):
    return {prefix:float(value),prefix+'_numerator':value.numerator,prefix+'_denominator':value.denominator}


def prepare(work,timing,inline=None):
    """No plotting dependency. Times share reference-small normalization; work has its own."""
    c.validate_matrix(timing,'timing')
    fields={}
    for row in work:
        key=(a.casekey(row),row['counter']);a.require(key not in fields,'duplicate work metric');fields[key]=row
    a.require(len(fields)==4680,'complete work inventory')
    raw={(a.casekey(r),r['policy'],r['repetition']):r for r in c.measured(timing)}
    bends=[];trials=[]
    for family in a.FAMILIES:
        for graph in a.GRAPHS:
            small=(family,a.SIZES[0],graph,3001)
            small_work=fields[(small,'kkt_edges')];small_N=small_work['N'];small_count=small_work['reference']
            a.require(small_count>0,'positive small work denominator')
            for clock in CLOCKS:
                small_ns=statistics.median(raw[(small,'reference',rep)][clock] for rep in (1,2,3))
                a.require(type(small_ns) is int and small_ns>0,'positive exact small timing denominator')
                for n in a.SIZES:
                    case=(family,n,graph,3001);workrow=fields[(case,'kkt_edges')];example=raw[(case,'reference',1)]
                    a.require(a.identity(workrow)==a.identity(example),'work/timing exact input join')
                    a.require(workrow['reference']==workrow['depth'],'kkt_edges must be equal across policies')
                    ident={k:example[k] for k in a.IDENTITY};N=example['n']+example['m']
                    q=Fraction(workrow['reference']*small_N,small_count*N)
                    bends.append(dict(ident,N=N,clock=clock,series='work',normalization='Own small-input kkt_edges/N',
                        median=float(q),minimum=float(q),maximum=float(q),small_N=small_N,small_reference=small_count,
                        **exact_fields(q,'exact_median')))
                    for policy in ('reference','depth'):
                        times=[raw[(case,policy,rep)][clock] for rep in (1,2,3)]
                        values=[Fraction(value*small_N,small_ns*N) for value in times];q=statistics.median(values)
                        bends.append(dict(ident,N=N,clock=clock,series=policy,normalization='Reference small-input time/N shared by both policies',
                            median=float(q),minimum=float(min(values)),maximum=float(max(values)),small_N=small_N,small_reference=small_ns,
                            **exact_fields(q,'exact_median')))
                        for repetition,value,ns in zip((1,2,3),values,times):
                            trials.append(dict(ident,N=N,clock=clock,policy=policy,repetition=repetition,native_ns=ns,
                                small_reference_ns=small_ns,small_N=small_N,**exact_fields(value,'normalized_time')))
    a.require(len(bends)==216 and len(trials)==432,'compact curve table counts')
    tables={'bending':bends,'bending-trials':trials}
    t=c.timing_tables(timing,'timing');tables.update({'ratios':t['pairs'],'ratio-summary':t['cases']})
    if inline is not None:
        c.validate_matrix(inline,'inline-control');t=c.timing_tables(inline,'inline-control')
        tables.update({'inline-ratios':t['pairs'],'inline-summary':t['cases']})
    return tables


def render(tables,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.titlesize':13,'axes.labelsize':11,
        'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#fbfaf7','axes.facecolor':'#fbfaf7',
        'savefig.facecolor':'#fbfaf7','text.color':'#172c38','axes.labelcolor':'#172c38',
        'xtick.color':'#172c38','ytick.color':'#172c38','svg.hashsalt':'kkt-depth-query-candidate'})
    outputs=[]
    def save(fig,name):
        for ext in ('png','svg'):
            path=out/(name+'.'+ext);fig.savefig(path,dpi=170);outputs.append(path)
        plt.close(fig)
    def size_axis(ax):
        ax.set_xscale('log',base=4);ax.set_xticks(a.SIZES,['1K','4K','16K','64K','256K','1M']);ax.set_xlabel('Vertices n; normalization uses N = n + m')
        ax.grid(alpha=.16);lo,hi=ax.get_ylim();span=max(hi-lo,.05);ax.set_ylim(max(0,lo-.05*span),hi+.08*span)
    graph_handles=[Line2D([0],[0],color='#172c38',marker=marker,linestyle=line,label=label)
        for marker,line,label in (('o','-','Graph 1; sizes ascend'),('s','--','Graph 2; sizes descend'))]
    for clock in CLOCKS:
        title_clock='Wall time' if clock=='wall_ns' else 'Process CPU time'
        fig,axes=plt.subplots(3,1,figsize=(8.8,11.3))
        for ax,family in zip(axes,a.FAMILIES):
            for graph,marker,line in zip(a.GRAPHS,('o','s'),('-','--')):
                for series in ('reference','depth','work'):
                    rows=sorted((r for r in tables['bending'] if r['family']==family and r['graph_seed']==graph and r['clock']==clock and r['series']==series),key=lambda r:r['n'])
                    a.require(len(rows)==6,'six compact curve points');x=[r['n'] for r in rows];y=[r['median'] for r in rows]
                    ax.plot(x,y,color=COLORS[series],marker=marker,linestyle=line,markersize=4,linewidth=1.8 if series!='work' else 1.3,zorder=3)
                    if series!='work':ax.fill_between(x,[r['minimum'] for r in rows],[r['maximum'] for r in rows],color=COLORS[series],alpha=.11)
            ax.axhline(1,color='#a7aeb2',linewidth=.7);ax.set_title(LABELS[family],loc='left');ax.set_ylabel('Relative per-N value');size_axis(ax)
        series_handles=[Line2D([0],[0],color=COLORS[s],linewidth=2,label=l) for s,l in
            (('reference','Reference time/N'),('depth','Depth-query time/N'),('work','Logical kkt_edges/N'))]
        fig.suptitle('Counted work and fresh paired time scale differently\n'+title_clock,fontsize=17,y=.985)
        fig.legend(handles=series_handles,loc='lower center',ncol=3,bbox_to_anchor=(.5,.103),fontsize=10)
        fig.legend(handles=graph_handles,loc='lower center',ncol=2,bbox_to_anchor=(.5,.073),fontsize=10)
        fig.text(.5,.018,'Time curves share each graph’s reference 1K time/N denominator. Work uses its own 1K count/N.\n'
            'Different normalizations: this is not time per counted event. Separate absolute timing medians + full three-call ranges.\n'
            'One sampler (3001); exact graph fingerprints match diagnostic work. Counts do not enumerate all instructions.',ha='center',fontsize=9.2,linespacing=1.45)
        fig.subplots_adjust(left=.105,right=.97,top=.9,bottom=.18,hspace=.58);save(fig,'curve-bending-'+clock)

        fig,axes=plt.subplots(3,1,figsize=(8.8,10.8))
        for ax,family in zip(axes,a.FAMILIES):
            for graph,marker,line in zip(a.GRAPHS,('o','s'),('-','--')):
                summaries=sorted((r for r in tables['ratio-summary'] if r['family']==family and r['graph_seed']==graph and r['clock']==clock),key=lambda r:r['n'])
                a.require(len(summaries)==6,'six ratio summaries')
                x=[r['n'] for r in summaries];y=[r['median_paired_ratio'] for r in summaries]
                ax.plot(x,y,color=COLORS['depth'],marker=marker,linestyle=line,markersize=5,linewidth=1.7)
                ax.fill_between(x,[r['minimum_paired_ratio'] for r in summaries],[r['maximum_paired_ratio'] for r in summaries],color=COLORS['depth'],alpha=.10)
                ax.scatter(x,[r['ratio_of_medians'] for r in summaries],marker='x',color=COLORS['reference'],s=35,zorder=5)
                raw=[r for r in tables['ratios'] if r['family']==family and r['graph_seed']==graph and r['clock']==clock]
                for r in raw:ax.scatter(r['n']*(1.025 if graph==a.GRAPHS[1] else .975),r['paired_ratio'],color=COLORS['depth'],s=12,alpha=.38,marker=marker)
            ax.axhline(1,color=COLORS['reference'],linewidth=1);ax.set_title(LABELS[family],loc='left');ax.set_ylabel('Depth / reference');size_axis(ax)
        fig.suptitle('Fresh paired candidate ratios\n'+title_clock+'; lower is faster',fontsize=17,y=.985)
        fig.legend(handles=graph_handles,loc='lower center',ncol=2,bbox_to_anchor=(.5,.088),fontsize=10)
        fig.text(.5,.072,'Orange ×: ratio of separate absolute-duration medians (a different statistic).',ha='center',fontsize=9.5)
        fig.text(.5,.02,'Lines: median of three matched-repetition ratios for each graph. Dots and bands retain every trial.\n'
            'One sampler (3001); no trimming or historical timing pooling. Graph and size order remain confounded.',ha='center',fontsize=9.4,linespacing=1.5)
        fig.subplots_adjust(left=.105,right=.97,top=.9,bottom=.16,hspace=.58);save(fig,'paired-ratios-'+clock)

    if 'inline-ratios' in tables:
        for clock in CLOCKS:
            fig,axes=plt.subplots(3,1,figsize=(9.2,10.8));cases=[(f,n) for f in a.FAMILIES for n in (1024,1048576)]
            pairs=(('depth','reference'),('depth_noinline','reference'),('depth_noinline','depth'))
            labels=[LABELS[f].replace(' + leaves','')+'\n'+('1K' if n==1024 else '1M') for f,n in cases]
            for ax,(num,den) in zip(axes,pairs):
                for i,(family,n) in enumerate(cases):
                    values=[r['paired_ratio'] for r in tables['inline-ratios'] if r['family']==family and r['n']==n and r['clock']==clock and r['numerator_policy']==num and r['denominator_policy']==den]
                    a.require(len(values)==3,'three inline-control trials')
                    ax.vlines(i,min(values),max(values),color=COLORS['depth'],linewidth=2,alpha=.45)
                    ax.scatter([i-.08,i,i+.08],values,color=COLORS['depth'],s=25,alpha=.6)
                    ax.scatter(i,statistics.median(values),marker='_',color='#172c38',s=140,zorder=4)
                ax.axhline(1,color=COLORS['reference'],linewidth=1);ax.set_title(num.replace('_',' ')+' / '+den.replace('_',' '),loc='left')
                ax.set_xticks(range(6),labels,fontsize=9);ax.set_ylabel('Paired time ratio');ax.grid(axis='y',alpha=.16)
                lo,hi=ax.get_ylim();span=max(hi-lo,.05);ax.set_ylim(max(0,lo-.05*span),hi+.08*span)
            fig.suptitle('Query-method noinline control: all six endpoint inputs\n'+('Wall time' if clock=='wall_ns' else 'Process CPU time'),fontsize=16,y=.985)
            fig.text(.5,.016,'Three trials + median per input; G1/S3001 only. Launch positions rotate among three policies.\n'
                'Noinline applies only to query_depth. The helper API/inlining changes remain shared by both depth variants;\n'
                'this control does not isolate representation from all compiler effects.',ha='center',fontsize=9.3,linespacing=1.45)
            fig.subplots_adjust(left=.105,right=.97,top=.9,bottom=.13,hspace=.6);save(fig,'inline-controls-'+clock)
    return outputs,matplotlib.__version__


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work-analysis',type=Path,required=True)
    parser.add_argument('--timing-analysis',type=Path,required=True);parser.add_argument('--inline-analysis',type=Path)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    bound={};status=dict(schema='kkt_depth_candidate_figures_v1',validation='running',native_execution=False,
        input_sha256=bound,invocation=sys.argv,visual_qa='pending',rows_removed=0)
    try:
        for source in (__file__,c.__file__,a.__file__):a.read(source,bound)
        _,wt,wb=load_analysis(args.work_analysis,'work',bound);timing,_,tb=load_analysis(args.timing_analysis,'timing',bound)
        a.require(wb==tb,'work/timing builds differ');inline=None
        if args.inline_analysis:
            inline,_,ib=load_analysis(args.inline_analysis,'inline-control',bound);a.require(ib==tb,'inline build differs')
        tables=prepare(wt['work-counters'],timing,inline)
        for name,rows in tables.items():a.write_csv(out/(name+'.csv'),rows)
        a.recheck(bound);outputs,version=render(tables,out);a.recheck(bound)
        status.update(validation='pass',table_counts={k:len(v) for k,v in tables.items()},matplotlib=version,
            figures=len(outputs)//2,scope='Presentation only; full exact work/timing input joins and raw-derived canonical equality.')
    except BaseException as error:status.update(validation='failed',error=repr(error));raise
    finally:
        status['output_sha256']={p.name:a.sha(p) for p in out.iterdir() if p.is_file()}
        (out/'provenance.json').write_text(json.dumps(status,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:status[k] for k in ('validation','table_counts','figures')}))


if __name__=='__main__':main()
