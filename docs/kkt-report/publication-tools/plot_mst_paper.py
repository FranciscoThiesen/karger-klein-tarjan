#!/usr/bin/env python3
"""Re-layout verified MST figures at paper width without changing observations.

Source preparation only; execution requires a separate postcapture release.
This is a presentation adapter, not an independent numerical audit.
"""
import argparse
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import statistics
import sys

WIDTH = 7.1
SCHEMAS = {'extension':'eighth_extension_figures_v1',
           'eighth':'eighth_sampling_figures_v1', 'work':'eighth_work_figures_v1'}


def require(value, message):
    if not value: raise ValueError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bind(inputs, path, expected=None):
    path = Path(path).resolve(strict=True)
    actual = sha(path)
    require(expected is None or actual == expected, 'changed input: '+str(path))
    require(str(path) not in inputs or inputs[str(path)] == actual, 'conflicting input: '+str(path))
    inputs[str(path)] = actual
    return path


def recheck(inputs):
    for path, digest in inputs.items(): bind(inputs, path, digest)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def same(actual, expected, label):
    # JSON spelling distinguishes bool/int/float and preserves row order.
    require(canonical(actual) == canonical(expected), label+' differs')


def write_json(path, value):
    with path.open('x') as stream: json.dump(value, stream, indent=2, allow_nan=False)


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, 'cannot import reviewed source')
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def inherited(args, inputs):
    root = args.standalone.resolve(strict=True)
    provenance = json.loads(bind(inputs, root/'provenance.json').read_text())
    require(provenance.get('schema') == SCHEMAS[args.study] and provenance.get('validation') == 'pass',
            'wrong or incomplete standalone plot provenance')
    require(provenance.get('native_solver_execution', False) is False, 'unexpected native plotting')
    for path, digest in provenance['input_sha256'].items(): bind(inputs, path, digest)
    for name, digest in provenance['output_sha256'].items():
        bind(inputs, root/name, digest)
    values_path = root/'plotted_values.json'
    require('plotted_values.json' in provenance['output_sha256'], 'standalone values not bound')
    require(str(args.source_plot.resolve(strict=True)) in provenance['input_sha256'],
            'standalone did not bind requested plot source')
    values = json.loads(bind(inputs, values_path).read_text())
    if args.study != 'work':
        require(Path(provenance['capture']).resolve(strict=True) == args.capture.resolve(strict=True),
                'standalone used another capture')
    return values, provenance


def timing_audit_fields(value, kind):
    expected = dict(schema='independent_eighth_'+('extension' if kind=='extension' else 'sampling')+'_numerical_audit_v1',
                    validation='pass',collector_imported=False,
                    raw_native_children=28 if kind=='extension' else 48,
                    checked_outputs=1176 if kind=='extension' else 2016,
                    timed_outputs=1008 if kind=='extension' else 1728,
                    warmup_outputs=168 if kind=='extension' else 288)
    for key, wanted in expected.items():
        require(type(value.get(key)) is type(wanted) and value[key]==wanted, 'wrong timing audit '+key)


def work_values(source, args, inputs):
    require(args.audit is not None, 'work requires its completed independent audit')
    work = module(bind(inputs, Path(source.__file__).parent/'collect.py'), 'paper_eighth_work_collector')
    audit = json.loads(bind(inputs, args.audit).read_text())
    expected = dict(schema='independent_eighth_work_counter_audit_v1', validation='pass',
                    checked_children=48, solver_rows=144, counter_fields=65, counter_cells=9360,
                    query_rows=48, paired_kkt_counter_rows=1560, engine_words_exact=True,
                    collector_imported=False, aggregation_reused=False)
    for key, value in expected.items():
        require(type(audit.get(key)) is type(value) and audit[key] == value, 'wrong work audit '+key)
    require(audit['input_sha256'].get(str(args.capture.resolve(strict=True))) == sha(args.capture),
            'work audit does not bind this capture')
    for path, digest in audit['input_sha256'].items(): bind(inputs, path, digest)
    info, values = work.load(args.capture)
    require(len(values) == 48, 'work capture incomplete')
    pairs, cases = {}, {}
    for identity, result in values:
        key = (identity['case_id'], identity['graph_seed'], identity['kkt_seed'])
        require(identity['variant'] not in pairs.setdefault(key, {}), 'duplicate work variant')
        pairs[key][identity['variant']] = (identity, result['algorithms']['kkt']['work'])
    require(len(pairs) == 24, 'incomplete work realizations')
    records = []
    for key, variants in pairs.items():
        require(set(variants) == {'half','eighth'}, 'work variant missing')
        identity, half = variants['half']; _, eighth = variants['eighth']
        cases[key[0]] = {name:identity[name] for name in ('case_id','family','n','m')}
        for field, _ in source.FIELDS:
            a, b = half[field], eighth[field]
            ratio = Fraction(b, a) if a else None
            records.append(dict(case_id=key[0], graph_seed=key[1], kkt_seed=key[2], counter=field,
                half=a, eighth=b, ratio_numerator=ratio.numerator if ratio is not None else None,
                ratio_denominator=ratio.denominator if ratio is not None else None,
                ratio=float(ratio) if ratio is not None else None,
                status='defined' if a else 'both_zero' if not b else 'half_zero'))
    require(len(records) == 192 and len(cases) == 6, 'incomplete selected work matrix')
    summaries = []
    for family in source.GROUPS:
        selected = sorted((c for c in cases.values() if c['family'] == family), key=lambda c:c['n'])
        require(len(selected) == 2, 'missing work size')
        for case in selected:
            for field, _ in source.FIELDS:
                data = sorted((r for r in records if r['case_id'] == case['case_id'] and r['counter'] == field),
                              key=lambda r:(r['graph_seed'],r['kkt_seed']))
                require(len(data) == 4, 'missing work realization')
                exact = [Fraction(r['eighth'],r['half']) for r in data if r['half']]
                positive = [float(x) for x in exact if x > 0]
                median = statistics.median(exact) if len(exact) == 4 else None
                summaries.append(dict(case_id=case['case_id'], counter=field,
                    all_four_defined=len(exact) == 4, median_ratio=float(median) if median is not None else None,
                    zero_ratio_count=sum(x == 0 for x in exact),
                    undefined_statuses=[r['status'] for r in data if r['status'] != 'defined'],
                    positive_min=min(positive) if positive else None, positive_max=max(positive) if positive else None))
    return cases, dict(records=records, summaries=summaries), info


def load(args):
    inputs = {}
    bind(inputs, __file__); bind(inputs, args.capture)
    old, provenance = inherited(args, inputs)
    source_path = bind(inputs, args.source_plot)
    old_path = sys.path[:]
    try:
        # One study per process. Only the declared source's existing package is added.
        sys.path.insert(0, str(source_path.parent))
        source = module(source_path, 'mst_paper_original_plot')
        if args.study == 'work':
            cases, tables, info = work_values(source, args, inputs)
            same(tables, old, 'fresh raw work versus original plotted values')
            return source, cases, tables, info, inputs
        audit=json.loads(bind(inputs,args.audit).read_text())
        timing_audit_fields(audit,args.study)
        require(audit['input_sha256'].get(str(args.capture.resolve(strict=True)))==sha(args.capture),
                'timing audit does not bind this capture')
        for path,digest in audit['input_sha256'].items():bind(inputs,path,digest)
        study = source.study
        info, cases, rows, _, _, bound = study.load(args.capture)
        require(len(rows) == (1176 if args.study == 'extension' else 2016), 'wrong timing row count')
        for path, digest in {**bound, **study.helpers()}.items(): bind(inputs, path, digest)
        tables = study.aggregate(rows)
        if args.study == 'extension':
            tables.update(study.crossovers(tables, cases)); source.prepare(cases, tables)
            same(tables, old, 'fresh extension versus original plotted values')
        else:
            source.prepare(cases, tables)
            same({**tables, 'strong_crossover_classifications':study.crossovers(tables, cases)}, old,
                 'fresh eighth versus original plotted values')
        return source, cases, old, info, inputs
    finally:
        sys.path[:] = old_path


def point_key(row):
    return (row['kind'],row['metric'],row['case_id'],row['algorithm'])


def check_points(actual, expected):
    a = {point_key(row):row for row in actual}; e = {point_key(row):row for row in expected}
    require(len(a) == len(actual) and len(e) == len(expected), 'duplicate paper point')
    require(set(a) == set(e), 'missing or extra paper point')
    for key in e: same(a[key], e[key], 'paper point '+str(key))


def timing_data(source, cases, tables, kind):
    base = {k:v for k,v in tables.items() if k != 'strong_crossover_classifications'}
    prepared, groups = source.prepare(cases, base)
    kinds = ('ratios','times') if kind == 'extension' else ('variant_gains','eighth_ratios')
    groups = ([(title,selected) for _,title,selected in groups] if kind == 'extension' else groups)
    identities = [(g,) for g in source.study.GRAPH_SEEDS] if kind == 'extension' else source.REALIZATIONS
    expected = []
    for name in kinds:
        pooled, realized, algorithms, field = prepared[name]
        scale = 1e9 if name == 'times' else 1
        for metric in source.METRICS:
            for _, selected in groups:
                for case in selected:
                    for algorithm in algorithms:
                        row = pooled[(case['case_id'],algorithm,metric)]
                        expected.append(dict(kind=name, metric=metric, case_id=case['case_id'], algorithm=algorithm,
                            n=case['n'], median=row[field]/scale, minimum=row['trial_min']/scale,
                            maximum=row['trial_max']/scale,
                            realization_medians=[realized[(case['case_id'],algorithm,metric,*identity)][field]/scale
                                                 for identity in identities]))
    require(len(expected) == (308 if kind == 'extension' else 132), 'wrong paper timing count')
    return groups, kinds, expected


def save(plt, figure, output, name):
    require(tuple(figure.get_size_inches())[0] == WIDTH, 'paper width changed')
    for suffix in ('png','svg','pdf'):
        # No tight-bbox resize: physical canvas width and font sizes stay explicit.
        figure.savefig(output/(name+'.'+suffix), dpi=220, facecolor='white')
    plt.close(figure)


def timing_render(source, cases, tables, info, output, kind):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FuncFormatter, NullFormatter
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9.5,
        'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','pdf.fonttype':42})
    groups, kinds, expected = timing_data(source, cases, tables, kind)
    points = {point_key(row):row for row in expected}; emitted=[]; coverage=[]
    style = source.style
    for name in kinds:
        algorithms = source.study.ALGORITHMS if name in ('variant_gains','times') else source.study.ALGORITHMS[1:]
        limits = {title:style.limits([points[(name,clock,c['case_id'],a)][endpoint]
                   for c in selected for a in algorithms for clock in source.METRICS
                   for endpoint in ('minimum','maximum')], () if name == 'times' else (.9,1))
                  for title,selected in groups}
        for metric, clock_title in source.METRICS.items():
            fig, axes = plt.subplots(len(groups),1,figsize=(WIDTH,8.8),squeeze=False)
            fig.subplots_adjust(left=.17,right=.98,bottom=.16,top=.91,hspace=.53)
            for ax,(title,selected) in zip(axes.flat,groups):
                sizes = [case['n'] for case in selected]
                plotted=[]
                for algorithm in algorithms:
                    rows = [points[(name,metric,c['case_id'],algorithm)] for c in selected]
                    middle=[r['median'] for r in rows]; lo=[r['minimum'] for r in rows]; hi=[r['maximum'] for r in rows]
                    color=style.COLORS[algorithm]
                    ax.vlines(sizes,lo,hi,color=color,alpha=.3,lw=1.2)
                    for index in range(len(rows[0]['realization_medians'])):
                        medians=[r['realization_medians'][index] for r in rows]
                        ax.scatter(sizes,medians,marker=('^','v','<','>')[index],color=color,alpha=.5,s=20)
                        plotted.extend(medians)
                    ax.plot(sizes,middle,color=color,marker='o',ms=3.7,lw=1.5)
                    plotted.extend([*middle,*lo,*hi]); emitted.extend(rows)
                if name != 'times':
                    ax.axhline(1,color='#555555',ls='--',lw=.9);ax.axhline(.9,color='#888888',ls=':',lw=.9)
                ax.set_xscale('log',base=2)
                if name != 'variant_gains':ax.set_yscale('log',base=10 if name=='times' else 2)
                ax.set_xlim(min(sizes)/1.18,max(sizes)*1.18);ax.set_ylim(*limits[title])
                ax.set_xticks(sizes,[f'{n:,}' for n in sizes]);ax.tick_params(axis='x',labelsize=8.5)
                ax.yaxis.set_major_formatter(FuncFormatter(lambda value,_:f'{value:g}'))
                ax.yaxis.set_minor_formatter(NullFormatter());ax.grid(which='major',alpha=.16)
                ax.set_title(title.replace('–','-').replace('—','-'),loc='left',fontsize=10)
                ax.set_xlabel('Vertices n (log scale)',fontsize=9.5)
                ax.set_ylabel('Seconds (log scale)' if name=='times' else
                              'Eighth / half time' if name=='variant_gains' else 'KKT / comparator time',fontsize=9.5)
                low,high=ax.get_ylim();require(all(low<=v<=high for v in plotted),'paper timing clips a value')
                coverage.append(dict(figure=name+'_'+metric,family=selected[0]['family'],
                    cases=[c['case_id'] for c in selected],algorithms=list(algorithms),limits=[low,high]))
            title={'ratios':'Eighth KKT against all five comparators','times':'All six solver times',
                   'variant_gains':'Eighth / half: all six implementations',
                   'eighth_ratios':'Eighth KKT against all five comparators'}[name]
            fig.suptitle(title+'\n'+clock_title,fontsize=12,y=.985)
            names = source.LABELS if kind=='extension' else {**style.LABELS,'kkt':'KKT'}
            handles=[Line2D([],[],color=style.COLORS[a],marker='o',label=names[a]) for a in algorithms]
            handles += [Line2D([],[],color='#666666',marker='^',ls='none',label='Realization medians'),
                        Line2D([],[],color='#777777',alpha=.4,lw=2,label='Full trial range')]
            legend=fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.045),ncol=3,frameon=False,fontsize=8.5)
            same([t.get_text() for t in legend.get_texts()],[names[a] for a in algorithms]+['Realization medians','Full trial range'],
                 'paper legend')
            statistic=('12 trials per point; two graph medians.' if kind=='extension' else
                       '24 trials per point; four graph/sampler medians.')
            fig.text(.5,.012,statistic+' Complete ranges, not confidence intervals.\n'
                     'No normalization; lines connect observations only; every clock flag retained.',
                     ha='center',fontsize=8.5,linespacing=1.4)
            save(plt,fig,output,'paper_'+name+'_'+metric)
    check_points(emitted,expected)
    for name in kinds:
        for _,selected in groups:
            family=selected[0]['family']
            matched=[r['limits'] for r in coverage if r['figure'] in (name+'_wall',name+'_cpu') and r['family']==family]
            require(len(matched)==2 and matched[0]==matched[1],'paper clock limits differ')
    return dict(points=emitted,coverage=coverage,figures=2*len(kinds),matplotlib_version=matplotlib.__version__)


def work_render(source,cases,tables,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FuncFormatter, NullFormatter
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9.5,
        'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','pdf.fonttype':42})
    records=tables['records'];summary={(r['case_id'],r['counter']):r for r in tables['summaries']}
    positive=[r['ratio'] for r in records if r['ratio'] is not None and r['ratio']>0]
    require(positive and all(math.isfinite(v) for v in positive),'no finite positive work ratios')
    lo,hi=min(*positive,1)/1.30,max(*positive,1)*1.30
    emitted=[];emitted_summary=[];coverage=[]
    for endpoint in (0,1):
        fig,axes=plt.subplots(3,1,figsize=(WIDTH,9.0))
        fig.subplots_adjust(left=.37,right=.98,bottom=.13,top=.92,hspace=.43)
        for ax,family,title in zip(axes,source.GROUPS,source.LABELS):
            selected=sorted((c for c in cases.values() if c['family']==family),key=lambda c:c['n'])
            require(len(selected)==2,'work endpoint missing');case=selected[endpoint]
            for y,(field,label) in enumerate(source.FIELDS):
                data=sorted((r for r in records if r['case_id']==case['case_id'] and r['counter']==field),
                            key=lambda r:(r['graph_seed'],r['kkt_seed']))
                point=summary[(case['case_id'],field)]
                values=[r['ratio'] for r in data if r['ratio'] is not None and r['ratio']>0]
                require(len(data)==4 and all(lo<=v<=hi for v in values),'work observation lost')
                if values:ax.hlines(y,min(values),max(values),color='#226b8a',alpha=.4,lw=3)
                for index,row in enumerate(data):
                    if row['ratio'] is not None and row['ratio']>0:
                        ax.scatter(row['ratio'],y+(index-1.5)*.065,marker=('^','v','<','>')[index],s=23,color='#226b8a',alpha=.6)
                if point['median_ratio'] is not None and point['median_ratio']>0:
                    ax.scatter(point['median_ratio'],y,color='#173c50',s=25,zorder=4)
                notes=[*point['undefined_statuses'],*(['zero ratio']*point['zero_ratio_count'])]
                if notes:ax.text(hi/1.02,y,'; '.join(notes),ha='right',va='center',fontsize=8.5)
                emitted.extend(data);emitted_summary.append(point)
            ax.axvline(1,color='#777777',ls='--',lw=.9);ax.set_xscale('log',base=2)
            ax.set_xlim(lo,hi);ax.set_ylim(7.7,-.7);ax.grid(axis='x',alpha=.15)
            ax.set_yticks(range(8),[label for _,label in source.FIELDS],fontsize=9)
            ax.xaxis.set_major_formatter(FuncFormatter(lambda value,_:f'{value:g}'))
            ax.xaxis.set_minor_formatter(NullFormatter())
            ax.set_title(f'{title}: n={case["n"]:,}',loc='left',fontsize=10)
            ax.set_xlabel('Eighth / half logical count (log scale)',fontsize=9.5)
            coverage.append(dict(case_id=case['case_id'],counter_fields=[f for f,_ in source.FIELDS],
                                 records=32,limits=[lo,hi]))
        fig.suptitle('Recursive work: '+('smaller' if endpoint==0 else 'larger')+' endpoints',fontsize=12,y=.98)
        handles=[Line2D([],[],color='#173c50',marker='o',ls='none',label='Four-ratio median'),
                 Line2D([],[],color='#226b8a',marker='^',ls='none',alpha=.6,label='Every realization'),
                 Line2D([],[],color='#226b8a',lw=3,alpha=.4,label='Full positive range')]
        fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.052),ncol=3,frameon=False,fontsize=8.5)
        fig.text(.5,.022,'All recursive calls; two graphs x two sampler seeds. Logical counts are not CPU costs.',ha='center',fontsize=8.5)
        save(plt,fig,output,'paper_work_'+('small' if endpoint==0 else 'large'))
    record_key=lambda r:(r['case_id'],r['counter'],r['graph_seed'],r['kkt_seed'])
    summary_key=lambda r:(r['case_id'],r['counter'])
    same(sorted(emitted,key=record_key),sorted(records,key=record_key),'all paper work observations')
    same(sorted(emitted_summary,key=summary_key),sorted(tables['summaries'],key=summary_key),'all paper work summaries')
    require(len(coverage)==6 and len({r['case_id'] for r in coverage})==6,'work case omitted')
    return dict(records=emitted,summaries=emitted_summary,coverage=coverage,figures=2,
                matplotlib_version=matplotlib.__version__)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study',choices=tuple(SCHEMAS),required=True)
    for name in ('capture','source-plot','standalone','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--audit',type=Path,required=True)
    parser.add_argument('--released',action='store_true')
    args=parser.parse_args();require(args.released,'explicit postcapture publication release required')
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    metadata=dict(schema='mst_publication_figures_v1',validation='running',invocation=sys.argv,
                  native_solver_execution=False,independent_numerical_audit=False,visual_review='pending')
    try:
        source,cases,tables,info,inputs=load(args);metadata['input_sha256']=inputs
        result=(work_render(source,cases,tables,output) if args.study=='work' else
                timing_render(source,cases,tables,info,output,args.study))
        write_json(output/'plotted_values.json',tables)
        write_json(output/'paper_points.json',result)
        recheck(inputs)
        metadata.update(validation='rendered_pending_visual_qa',study=args.study,figures=result['figures'],
            figure_width_inches=WIDTH,label_points=9.5,minimum_tick_legend_points=8.5,
            standalone_plotted_values_equal=True,all_selected_observations_drawn=True,
            original_artifacts_modified=False,matched_clock_axes=True,rows_removed=0,rows_adjusted=0,
            note='Paired paper panels select variant gains and eighth direct ratios; full original tables and gallery remain.')
    except BaseException as error:
        metadata.update(validation='failed',error=repr(error));raise
    finally:
        metadata['output_sha256']={str(p.relative_to(output)):sha(p) for p in output.rglob('*') if p.is_file()}
        write_json(output/'provenance.json',metadata)
    print(json.dumps({key:metadata[key] for key in ('validation','study','figures')}))


if __name__=='__main__':main()
