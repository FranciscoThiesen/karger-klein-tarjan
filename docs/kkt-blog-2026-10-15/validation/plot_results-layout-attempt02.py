#!/usr/bin/env python3
"""Make editorial charts from completed, independently audited evidence only.

No collector import, native solver, model fit, trimming, or historical pooling.
Recompute every lower-density timing summary from integer calls and the plotted
native CPU summaries from the Google campaign's raw integer records.
"""
import argparse
import csv
from collections import defaultdict
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import statistics
import textwrap

ROOT = Path(__file__).resolve().parents[3]
LOW = ROOT/'benchmark/results/lower-density-2026-10-15'
GB = ROOT/'benchmark/results/current-complexity-2026-10-15'
ALGS = ('kkt','compacting_boruvka','multigraph_boruvka','kruskal','prim','boruvka')
LABEL = dict(zip(ALGS, ('KKT','Dedup. B','Retained B','Kruskal','Prim','Original B')))
GRAPHS = (23000003,23000029)
FIELDS = {'wall':'elapsed_ns','cpu':'process_cpu_elapsed_ns'}
BG,INK,TEAL,ORANGE,SLATE,FAINT = '#fbfaf7','#172c38','#007f82','#bd571e','#657782','#dce2e2'

def require(ok, why):
    if not ok: raise ValueError(why)

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class Evidence:
    def __init__(self): self.inputs = {str(Path(__file__).resolve()):sha(__file__)}
    def read(self, path, expected=None):
        path=Path(path).resolve(strict=True); value=sha(path)
        require(expected is None or value==expected, 'audit-bound file changed: '+str(path))
        require(str(path) not in self.inputs or self.inputs[str(path)]==value, 'input changed during read')
        self.inputs[str(path)]=value; data=path.read_text(); require(sha(path)==value,'read drift'); return data
    def audit(self,path,schema):
        data=json.loads(self.read(path)); require(data['schema']==schema and data['validation']=='pass','audit failed'); return data
    def csv(self,path,audit=None):
        expected=None
        if audit is not None:
            expected=audit['input_sha256'].get(str(Path(path).resolve()))
            require(expected is not None,'file absent from independent audit')
        return list(csv.DictReader(self.read(path,expected).splitlines()))
    def recheck(self):
        for path,value in self.inputs.items(): require(sha(path)==value,'input drift: '+path)

def near(value,expected):
    require(math.isclose(float(value),float(expected),rel_tol=3e-15,abs_tol=1e-12),
            'canonical arithmetic differs: '+str((value,expected)))

def median(values): return statistics.median(values)
def ident(row): return row['case_id']
def point(values):
    flat=[x for v in values.values() for x in v]; meds=[median(values[g]) for g in GRAPHS]
    return dict(value=float(median(flat)),minimum=float(min(flat)),maximum=float(max(flat)),
                g1=float(meds[0]),g2=float(meds[1]),exact_median=str(median(flat)),
                exact_g1=str(meds[0]),exact_g2=str(meds[1]))

def data(e):
    audit=e.audit(LOW/'independent-audit-attempt01/audit.json','independent_lower_density_numerical_audit_v1')
    require(audit['checked_outputs']==2520 and audit['clock_flagged_calls']==0,'timing scope differs')
    calls=e.csv(LOW/'analysis-attempt01/validated_calls.csv',audit)
    require(len(calls)==2520 and all(r['validation']=='pass' for r in calls),'incomplete validated calls')
    blocks=defaultdict(dict); times=defaultdict(lambda:defaultdict(list)); cases={}
    for r in calls:
        cases[r['case_id']]={k:r[k] for k in ('case_id','family','n','m','density')}
        if r['phase']!='timed': continue
        key=(r['case_id'],int(r['graph_seed']),int(r['repetition']))
        require(r['algorithm'] not in blocks[key],'duplicate timed solver'); blocks[key][r['algorithm']]=r
        for clock,field in FIELDS.items(): times[(r['case_id'],r['algorithm'],clock)][int(r['graph_seed'])].append(int(r[field]))
    require(len(blocks)==360 and len(cases)==30,'timed matrix differs')
    ratios=defaultdict(lambda:defaultdict(list))
    for (case,g,rep),block in blocks.items():
        require(set(block)==set(ALGS),'missing six-solver comparison')
        for alg in ALGS[1:]:
            for clock,field in FIELDS.items(): ratios[(case,alg,clock)][g].append(Fraction(int(block['kkt'][field]),int(block[alg][field])))
    checked=0
    for collection,name,keyfield,valuefield,count in ((ratios,'comparisons','competitor','median_paired_ratio',300),
                                                       (times,'summary','algorithm','median_ns',360)):
        require(len(collection)==count,'summary scope differs')
        for graph_table in (False,True):
            rows=e.csv(LOW/'analysis-attempt01'/((('graph_' if graph_table else '')+name)+'.csv'),audit)
            require(len(rows)==count*(2 if graph_table else 1),'canonical table count differs')
            seen=set()
            for r in rows:
                key=(r['case_id'],r[keyfield],r['metric']); values=collection[key]
                identity=key+(int(r['graph_seed']),) if graph_table else key
                require(identity not in seen,'duplicate canonical identity'); seen.add(identity)
                require(set(values)==set(GRAPHS) and all(len(v)==6 for v in values.values()),'graph/repetition mismatch')
                flat=values[int(r['graph_seed'])] if graph_table else [x for v in values.values() for x in v]
                for field,v in ((valuefield,median(flat)),('trial_min',min(flat)),('trial_max',max(flat))):near(r[field],v)
                if not graph_table:
                    near(r['graph_min'],min(map(median,values.values())));near(r['graph_max'],max(map(median,values.values())))
                if keyfield=='competitor': require(int(r['individual_wins'])==sum(v<1 for v in flat),'win count differs')
                checked+=1
    def ratio_rows(selected):
        return [dict(cases[case],clock=clock,competitor='multigraph_boruvka',**point(ratios[(case,'multigraph_boruvka',clock)]))
                for case in selected for clock in FIELDS]
    ordered_cases=sorted(cases,key=lambda c:(int(cases[c]['density']),cases[c]['family'],int(cases[c]['n'])))
    cross=ratio_rows([c for c in ordered_cases if int(cases[c]['density'])==16])
    endpoints=[c for c in ordered_cases if int(cases[c]['n'])*int(cases[c]['density'])==33554432]
    endpoint=[dict(cases[c],algorithm=a,clock=clock,**point(times[(c,a,clock)])) for c in endpoints for a in ALGS for clock in FIELDS]
    endpoint_ratios=[dict(cases[c],competitor=a,clock=clock,**point(ratios[(c,a,clock)])) for c in endpoints for a in ALGS[1:] for clock in FIELDS]
    reversal=ratio_rows([c for c in ordered_cases if cases[c]['family']=='leaf_distance4' and int(cases[c]['density'])==8 and int(cases[c]['n'])>=262144])

    wa=e.audit(LOW/'work/independent-counter-audit-attempt01/audit.json','independent_lower_density_work_counter_audit_v1')
    require(wa['counter_cells']==11700 and wa['engine_words_exact'] is True,'work audit scope differs')
    work=e.csv(LOW/'work/analysis-attempt01/work.csv',wa); require(len(work)==180,'work rows differ')
    volume=[]; partition=[]
    pc=e.csv(LOW/'work/partition-analysis-attempt01/partition.csv'); pi={(r['case_id'],int(r['graph_seed'])):r for r in pc}
    for r in work:
        if r['algorithm'] in ('kkt','multigraph_boruvka'):
            volume.append({k:r[k] for k in ('case_id','family','n','m','density','graph_seed','algorithm')} |
                          dict(count=int(r['contraction_edges']),per_m=float(Fraction(int(r['contraction_edges']),int(r['m'])))))
        if r['algorithm']=='kkt':
            base=2*int(r['verifier_tree_edges'])+2*(int(r['fbt_output_vertices'])-int(r['fbt_calls']))
            part=int(r['verifier_edge_visits'])-base; require(part>=0,'negative partition residual')
            q=pi[(r['case_id'],int(r['graph_seed']))]
            require(int(q['disconnected_partition_edge_visits'])==part and
                    int(q['connected_query_scan_visits'])+int(q['fbt_edge_scan_visits'])==base,'partition identity differs')
            if r['family']=='leaf_distance4' and int(r['density'])==8 and int(r['n'])==4194304:
                partition.append(dict(graph_seed=int(r['graph_seed']),m=int(r['m']),base=base,partition=part,total=base+part,
                                      base_per_m=base/int(r['m']),partition_per_m=part/int(r['m'])))
    require(len(volume)==120 and len(partition)==2,'work plot scope differs')

    ga=e.audit(GB/'arithmetic-audit-attempt01/audit.json','current_complexity_independent_arithmetic_audit_v1')
    gs=e.csv(GB/'analysis-attempt01/size_summaries.csv',ga)
    choices=e.csv(GB/'analysis-attempt01/google_selection.csv',ga)
    require(len(choices)==24 and {r['selected_model'] for r in choices}=={'NlgN'},'Google result differs')
    capture=json.loads(e.read(GB/'capture-attempt01/capture.json',ga['input_sha256'][str(GB/'capture-attempt01/capture.json')]))
    cpu=defaultdict(list)
    for child in capture['captures']:
        raw=e.csv(child['raw_csv'],ga)
        for r in raw:
            if r['phase']=='timed':
                key=tuple(r[k] for k in ('family','algorithm','graph_seed','sampling_seed','n'))
                cpu[key].append(int(r['process_cpu_elapsed_ns']))
    complexity=[]
    for r in gs:
        if r['clock']!='native_process_cpu':continue
        key=tuple(r[k] for k in ('family','algorithm','graph_seed','sampling_seed','n')); values=cpu[key]
        multiplier=17 if r['family']=='gnm_random' else 33
        require(len(values)==6 and int(r['N'])==multiplier*int(r['n']),'complexity observation domain differs')
        for field,v in (('minimum_ns',min(values)),('median_ns',median(values)),('maximum_ns',max(values))):near(r[field],v)
        near(r['median_ns_per_N'],median(values)/int(r['N']))
        complexity.append(dict(r,minimum_ns_per_N=min(values)/int(r['N']),maximum_ns_per_N=max(values)/int(r['N'])))
    require(len(complexity)==264,'native CPU plot matrix differs')
    return dict(crossover=cross,endpoints=endpoint,endpoint_ratios=endpoint_ratios,volume=volume,complexity=complexity,reversal=reversal,partition=partition,
                google_choices=choices),dict(lower_timing_summaries_recomputed=checked,lower_timed_calls=2160,
                exact_pair_groups=300,work_rows=180,partition_identities_checked=60,native_cpu_summaries_recomputed=264,
                google_exported_choices=24)

def compact(n):
    n=int(n)
    return (f'{n//1048576}M' if n>=1048576 else f'{n//1024}K' if n>=1024 else str(n))

def render(d, output, mobile):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Rectangle
    from matplotlib.ticker import FuncFormatter
    width=3.6 if mobile else 7.2; fs=9.6 if mobile else 11.2
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':fs,'text.color':INK,'axes.labelcolor':INK,
        'xtick.color':SLATE,'ytick.color':SLATE,'axes.edgecolor':FAINT,'axes.facecolor':BG,
        'figure.facecolor':BG,'savefig.facecolor':BG,'svg.fonttype':'none','svg.hashsalt':'kkt-blog-2026-10-15',
        'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.spines.bottom':False})
    generated=[]
    def figure(height,title,subtitle=None):
        fig=plt.figure(figsize=(width,height),dpi=100)
        title='\n'.join(textwrap.wrap(title,32)) if mobile else title
        fig.text(.07,.975,title,fontsize=14 if mobile else 19,fontweight='bold',va='top')
        if subtitle:fig.text(.07,.975-((.72 if '\n' in title else .42)/height),
                            '\n'.join(textwrap.wrap(subtitle,43)) if mobile else subtitle,
                            fontsize=fs-0.2,color=SLATE,va='top')
        return fig
    def save(fig,name):
        stem='quant-'+name+('-mobile' if mobile else '')
        for ext in ('svg','png'):
            path=output/(stem+'.'+ext); require(not path.exists(),'refusing figure overwrite')
            fig.savefig(path,dpi=200,metadata={'Creator':'KKT evidence charts'} if ext=='svg' else None)
            generated.append(path)
        plt.close(fig)
    def axes(fig,rect):
        ax=fig.add_axes(rect);ax.grid(axis='y',color=FAINT,lw=.7,zorder=0);ax.tick_params(length=0,pad=5);return ax
    def xaxis(ax,ns):
        ax.set_xscale('log',base=2);ax.set_xticks(ns,[compact(n) for n in ns],rotation=35 if mobile else 0)
        ax.set_xlim(min(ns)/1.4,max(ns)*1.4)
    def foot(fig,text,y=.025):
        fig.text(.07,y,'\n'.join(textwrap.wrap(text,43 if mobile else 92)),fontsize=9.6 if mobile else 10.3,
                 color=SLATE,va='bottom',linespacing=1.45)
    def ratios(ax,rows,color,label,style='-'):
        rows=sorted(rows,key=lambda r:int(r['n']));ns=[int(r['n']) for r in rows]
        ax.vlines(ns,[r['minimum'] for r in rows],[r['maximum'] for r in rows],color=color,alpha=.3,lw=2.5)
        for key,mark in (('g1','^'),('g2','v')):ax.scatter(ns,[r[key] for r in rows],marker=mark,s=24,color=color,alpha=.5,zorder=3)
        ax.plot(ns,[r['value'] for r in rows],style,color=color,lw=2.2,marker='o',ms=4.5,label=label,zorder=4)
        return ns

    fig=figure(5.4 if mobile else 4.8,'A crossover that survives','KKT / retained Borůvka · wall time · m/n = 16')
    ax=axes(fig,[.16 if mobile else .12,.30,.79 if mobile else .83,.48 if mobile else .49])
    for family,color,label in [('leaf_distance4',TEAL,'Ordered weights'),('leaf_shuffled4',SLATE,'Shuffled twin')]:
        ns=ratios(ax,[r for r in d['crossover'] if r['family']==family and r['clock']=='wall'],color,label)
    xaxis(ax,ns);ax.axhline(1,color=INK,lw=.8,ls='--');ax.axhline(.9,color=TEAL,lw=.8,ls=':')
    ax.set_ylim(.55,max(r['maximum'] for r in d['crossover'] if r['clock']=='wall')*1.08)
    ax.set_ylabel('Time ratio · lower favors KKT');ax.set_xlabel('Vertices · K = 1,024; M = 1,048,576',fontsize=fs-1)
    ax.legend(loc='lower left',bbox_to_anchor=(0,1.015),frameon=False,fontsize=fs-.2,
              ncol=1 if mobile else 2,borderaxespad=0)
    foot(fig,'Dots: median of 12 paired calls. Triangles: two graph medians. Stems: full trial range. Parity = 1; strong lead = 0.90. Both clocks qualify the measured bracket (512, 8,192].')
    save(fig,'crossover')

    cases=sorted({(int(r['density']),r['family'],int(r['n']),r['case_id']) for r in d['endpoints']},reverse=True)
    # Fixed intuitive order; every largest endpoint has exactly 33,554,432 edges.
    cases=sorted(cases,key=lambda c:(-c[0],c[1]!='leaf_distance4'))
    ep={(r['case_id'],r['algorithm'],r['clock']):r for r in d['endpoints']}
    if mobile:
        fig=figure(13.2,'KKT is not the fastest solver','Largest endpoints · seconds · wall / CPU')
        for j,(density,family,n,case) in enumerate(cases):
            top=.88-j*.19;ax=fig.add_axes([.07,top-.167,.88,.167]);ax.axis('off')
            ax.text(0,1.14,('Ordered' if family=='leaf_distance4' else 'Shuffled')+f' · d={density} · {compact(n)} vertices',fontweight='bold',fontsize=11)
            best=min(ALGS,key=lambda a:ep[(case,a,'wall')]['value'])
            for i,a in enumerate(ALGS):
                y=.94-i*.172;color=TEAL if a=='kkt' else INK
                if a=='kkt':ax.add_patch(Rectangle((-.02,y-.095),1.04,.15,facecolor='#e5f1ef',edgecolor='none'))
                ax.text(0,y,LABEL[a],va='center',color=color,fontweight='bold' if a in ('kkt',best) else 'normal')
                ax.text(1,y,f"{ep[(case,a,'wall')]['value']/1e9:.3f} / {ep[(case,a,'cpu')]['value']/1e9:.3f}",ha='right',va='center',fontweight='bold' if a==best else 'normal')
        foot(fig,'Median of 12 calls per cell; wall and CPU remain separate. Bold competitor = smallest wall median in that row. Every graph has 33,554,432 edges. Paired ratios, graph medians and all ranges remain in chart data.',.02)
    else:
        fig=figure(4.85,'A crossover is not a six-way victory','Largest endpoints · seconds · wall / CPU')
        ax=fig.add_axes([.06,.28,.91,.47]);ax.axis('off');ax.set_xlim(-1.45,6);ax.set_ylim(-.45,4.45)
        desktop_labels={**LABEL,'compacting_boruvka':'Dedup.\nBorůvka','multigraph_boruvka':'Retained\nBorůvka','boruvka':'Original\nBorůvka'}
        for i,a in enumerate(ALGS):ax.text(i+.5,4.1,desktop_labels[a],ha='center',fontweight='bold',fontsize=11,va='bottom')
        for j,(density,family,n,case) in enumerate(cases):
            y=3.5-j;ax.text(-1.4,y,('Ordered' if family=='leaf_distance4' else 'Shuffled')+f'\nd={density} · {compact(n)}',va='center',fontsize=11)
            best=min(ALGS,key=lambda a:ep[(case,a,'wall')]['value'])
            for i,a in enumerate(ALGS):
                ax.add_patch(Rectangle((i,y-.43),.97,.86,facecolor='#e5f1ef' if a=='kkt' else '#efefea',edgecolor='none'))
                for delta,clock,color in ((.13,'wall',TEAL if a=='kkt' else INK),(-.16,'cpu',SLATE)):
                    ax.text(i+.485,y+delta,f"{ep[(case,a,clock)]['value']/1e9:.3f}",ha='center',va='center',fontsize=11,
                            color=color,fontweight='bold' if a==best else 'normal')
        foot(fig,'Each cell: wall seconds above CPU seconds. Medians of 12 calls. Bold competitor has the smallest wall median. All four graphs have 33,554,432 edges; paired ratios and full ranges are retained in chart data.')
    save(fig,'alternatives')

    fig=figure(7.7 if mobile else 6.7,'Repeated scans accumulate','Cumulative contraction input / original edges')
    for j,density in enumerate((16,8)):
        ax=axes(fig,[.17 if mobile else .12,.56-j*.30,.78 if mobile else .83,.23]);ns=[]
        for algorithm,color in [('kkt',TEAL),('multigraph_boruvka',ORANGE)]:
            for family,style in [('leaf_distance4','-'),('leaf_shuffled4','--')]:
                rows=[r for r in d['volume'] if r['algorithm']==algorithm and r['family']==family and int(r['density'])==density]
                ns=sorted({int(r['n']) for r in rows}); by={n:[r['per_m'] for r in rows if int(r['n'])==n] for n in ns}
                ax.plot(ns,[median(by[n]) for n in ns],style,color=color,lw=2,label=LABEL[algorithm]+(' · ordered' if style=='-' else ' · shuffled'))
                ax.fill_between(ns,[min(by[n]) for n in ns],[max(by[n]) for n in ns],color=color,alpha=.1)
                for r in rows:ax.plot(int(r['n']),r['per_m'],marker='o' if int(r['graph_seed'])==GRAPHS[0] else 'x',color=color,ms=3,alpha=.55)
        xaxis(ax,ns);ax.set_ylim(0,20);ax.set_yticks([0,5,10,15,20]);ax.set_ylabel(f'd = {density}',fontweight='bold')
    handles=[Line2D([],[],color=c,ls=ls,lw=2,label=l) for c,ls,l in [(TEAL,'-','KKT · ordered'),(TEAL,'--','KKT · shuffled'),(ORANGE,'-','Retained B · ordered'),(ORANGE,'--','Retained B · shuffled')]]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.14),ncol=2,frameon=False,fontsize=9.4 if mobile else 10.6)
    foot(fig,'Both graph realizations are shown. KKT totals span recursion; retained B totals span its full chain. These are logical input counts, not CPU cost. K/M denote powers of 1,024.',.018)
    save(fig,'work')

    fig=figure(9.0 if mobile else 8.0,'The finite fit is still N log N','Native CPU nanoseconds / N · N = n + m')
    families=('leaf_hierarchy4','leaf_shuffled4','gnm_random');titles=('Hierarchy weights','Shuffled weights','Uniform random graph')
    for j,(family,title) in enumerate(zip(families,titles)):
        ax=axes(fig,[.17 if mobile else .12,.65-j*.235,.78 if mobile else .83,.175])
        values=[]
        for a,color in [('kkt',TEAL),('multigraph_boruvka',ORANGE)]:
            for gi,g in enumerate((19000013,19000043)):
                for si,s in enumerate((3001,3011)):
                    rows=sorted((r for r in d['complexity'] if r['family']==family and r['algorithm']==a and int(r['graph_seed'])==g and int(r['sampling_seed'])==s),key=lambda r:int(r['N']))
                    require(len(rows)==11,'missing plotted complexity realization')
                    x=[int(r['N']) for r in rows];y=[float(r['median_ns_per_N']) for r in rows]
                    ax.vlines(x,[float(r['minimum_ns_per_N']) for r in rows],[float(r['maximum_ns_per_N']) for r in rows],color=color,alpha=.11,lw=.8)
                    ax.plot(x,y,color=color,lw=1.5,alpha=.68,ls='-' if si==0 else '--',marker='o' if gi==0 else 'x',ms=2.8)
                    values.extend(float(r['maximum_ns_per_N']) for r in rows)
        multiplier=17 if family=='gnm_random' else 33
        ticks=[1024*multiplier,32768*multiplier,1048576*multiplier]
        ax.set_xscale('log',base=2);ax.set_yscale('log');ax.set_xticks(ticks,[f'{n:,}' for n in ticks],fontsize=9.6 if mobile else 10.5)
        if mobile:
            ax.get_xticklabels()[0].set_ha('left');ax.get_xticklabels()[-1].set_ha('right')
        ax.set_xlim(min(ticks)/1.4,max(ticks)*1.4);ax.set_ylim(5,max(values)*1.18)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda y,_:f'{y:g}'));ax.set_title(title,loc='left',fontweight='bold',fontsize=fs,pad=9)
    fig.legend(handles=[Line2D([],[],color=c,lw=2,label=l) for c,l in ((TEAL,'KKT'),(ORANGE,'Retained B'))],loc='lower center',bbox_to_anchor=(.5,.11),ncol=2,frameon=False)
    foot(fig,'Four realizations per solver; no pooling. Lines: six-call medians; faint stems: full ranges. Log axes. Google selected N log N on all 24 library-CPU curves. A finite fit does not prove an asymptotic bound.',.018)
    save(fig,'complexity')

    fig=figure(8.5 if mobile else 6.7,'The lead can reverse','Ordered weights · m/n = 8')
    ax=axes(fig,[.17 if mobile else .12,.56,.78 if mobile else .83,.23])
    rows=sorted([r for r in d['reversal'] if r['clock']=='wall'],key=lambda r:int(r['n']));ns=[int(r['n']) for r in rows]
    ratios(ax,rows,TEAL,'Pooled median')
    ax.axhline(1,color=INK,ls='--',lw=.8);ax.set_ylim(min(r['minimum'] for r in rows)*.9,max(r['maximum'] for r in rows)*1.08)
    xaxis(ax,ns);ax.set_ylabel('KKT / retained B');ax.set_title('Wall-time ratio',loc='left',fontsize=fs,fontweight='bold')
    ax=axes(fig,[.20 if mobile else .16,.32 if mobile else .28,.75 if mobile else .79,.16]);parts=sorted(d['partition'],key=lambda r:r['graph_seed'])
    for i,r in enumerate(parts):
        ax.barh(i,r['base_per_m'],color='#bcc9cc',height=.47)
        ax.barh(i,r['partition_per_m'],left=r['base_per_m'],color=ORANGE,height=.47)
        ax.text(r['base_per_m']+r['partition_per_m']+.04,i,f"{r['total']/r['m']:.2f}×",va='center',fontsize=fs)
    ax.set_yticks([0,1],['Graph 1','Graph 2']);ax.invert_yaxis();ax.set_xlim(0,5.35);ax.set_xlabel('Verifier-edge visits / original m',fontsize=fs-.5)
    ax.set_title('At 4M: different verifier work',loc='left',fontweight='bold',fontsize=fs)
    fig.legend(handles=[Line2D([],[],color=c,lw=7,label=l) for c,l in (('#bcc9cc','Tree-query + FBT scans'),(ORANGE,'Forest partition'))],loc='lower center',bbox_to_anchor=(.5,.17 if mobile else .13),ncol=1 if mobile else 2,frameon=False,fontsize=9.6 if mobile else 10.2)
    foot(fig,'Top: 12 paired calls, both graph medians and full ranges. Bottom: cumulative logical counters on the same inputs. Exact counter bounds identify a disconnected root for graph 2; this is not a CPU-time decomposition.',.018)
    save(fig,'reversal')
    return generated,matplotlib.__version__

def write_csv(path,rows):
    with path.open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--attempt',required=True)
    args=parser.parse_args();require(args.attempt.isalnum() or all(c.isalnum() or c=='-' for c in args.attempt),'unsafe attempt')
    blog=Path(__file__).resolve().parents[1];output=blog/'assets'/args.attempt;tables=blog/'chart-data'/args.attempt
    require(not output.exists() and not tables.exists(),'refusing existing publication attempt')
    e=Evidence();values,checks=data(e);e.recheck();output.mkdir(parents=True);tables.mkdir(parents=True)
    for name,rows in values.items():write_csv(tables/(name+'.csv'),rows)
    generated=[]
    for mobile in (False,True):files,version=render(values,output,mobile);generated+=files
    e.recheck();metadata=dict(schema='kkt_blog_quantitative_figures_v1',validation='rendered_pending_visual_qa',
        independent_arithmetic_checks=checks,source_sha256=sha(__file__),input_sha256=e.inputs,
        chart_table_counts={k:len(v) for k,v in values.items()},matplotlib_version=version,
        native_solver_execution=False,new_model_fits=False,historical_pooling=False,
        plots=['crossover','alternatives','work','complexity','reversal'],responsive_variants=['desktop','mobile'],
        formats=['svg','png'],desktop_logical_width_px=720,mobile_logical_width_px=360,png_density=2,
        units='Timing clocks kept separate. Diagnostic counts are not CPU cost. K/M size ticks are powers of 1024.',
        output_sha256={str(p.relative_to(blog)):sha(p) for p in [*generated,*tables.glob('*.csv')]})
    with (tables/'provenance.json').open('x') as stream:json.dump(metadata,stream,indent=2);stream.write('\n')
    print(json.dumps({'validation':metadata['validation'],'assets':len(generated),'checks':checks,'output':str(output)}))

if __name__=='__main__':main()
