#!/usr/bin/env python3
"""Re-layout validated current complexity figures at readable paper width.

No new fits, pooled curves or thresholds. Requires the complete standalone
figure provenance and exact equality of every plotted value before and after.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys


def require(value, message):
    if not value: raise ValueError(message)


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key'); result[key] = value
        return result
    def invalid(value): raise ValueError('nonfinite JSON: '+value)
    result = json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)
    def finite(value):
        if type(value) is float: require(math.isfinite(value), 'nonfinite numeric overflow')
        elif type(value) is dict:
            for nested in value.values(): finite(nested)
        elif type(value) is list:
            for nested in value: finite(nested)
    finite(result); return result


def exact(actual, expected, message):
    require(type(actual) is type(expected) and actual == expected, message)
    if type(expected) is dict:
        for key in expected: exact(actual[key], expected[key], message+': '+key)
    elif type(expected) is list:
        for current, wanted in zip(actual, expected): exact(current, wanted, message)


def bind(bound, path, expected):
    path = Path(path).resolve(strict=True)
    require(type(expected) is str and len(expected) == 64, 'invalid expected hash')
    require(str(path) not in bound or bound[str(path)] == expected, 'conflicting input hash')
    require(digest(path) == expected, 'changed input: '+str(path)); bound[str(path)] = expected
    return path


def read_bound(bound, path, expected):
    path = bind(bound, path, expected); result = path.read_text(); bind(bound, path, expected)
    return result


def recheck(bound):
    for path, expected in bound.items(): bind(bound, path, expected)


def expected_values(original, tables, provenance):
    """Exact standalone value contract; reuse checked preparation, not fitting."""
    summaries, fits, selections, limits = original.prepare(tables)
    result = dict(normalized_points=[], model_cells=[], google_choices=tables['google_selection'],
                  common_normalized_y_limits=list(limits), clock_flag_count=provenance['clock_flag_count'])
    for clock in original.CLOCKS:
        for family in original.FAMILIES:
            for algorithm in original.ALGORITHMS:
                for graph in original.GRAPHS:
                    for sample in original.SAMPLERS:
                        for n in original.SIZES:
                            result['normalized_points'].append(dict(summaries[(family,algorithm,graph,sample,clock,n)], display_clock=clock))
    for window in ('full11', 'upper6'):
        for curve in original.curve_order():
            selected = selections[curve]['selected_model'] if window == 'full11' else next(
                model for model in original.MODELS if fits[(*curve,'library_process_cpu',window,model)]['selected_for_this_clock'])
            for model in original.MODELS:
                row = fits[(*curve,'library_process_cpu',window,model)]
                result['model_cells'].append(dict(row, plotted_rms_percent=row['normalized_rms']*100,
                    outlined=model==selected, outline_scope='google_exported_cpu_selection' if window=='full11' else 'custom_upper6_library_cpu'))
    require(len(result['normalized_points']) == 1056 and len(result['model_cells']) == 288, 'incomplete paper value matrix')
    return result


def load(args):
    bound = {str(Path(__file__).resolve()): digest(__file__)}
    source = bind(bound, args.standalone_source, args.standalone_source_sha256)
    directory = args.standalone_dir.resolve(strict=True)
    provenance_path = directory/'provenance.json'
    standalone = strict_json(read_bound(bound, provenance_path, digest(provenance_path)))
    for key, expected in dict(schema='current_complexity_figures_v1', validation='rendered_pending_visual_qa',
                              source_sha256=args.standalone_source_sha256, figures=5, formats=['png','svg','pdf'],
                              normalized_points=1056, model_cells=288, google_curves=24,
                              rows_removed=0, rows_adjusted=0, native_solver_execution=False,
                              independent_numerical_audit=False).items():
        exact(standalone[key], expected, 'standalone proof differs: '+key)
    spec = importlib.util.spec_from_file_location('reviewed_complexity_standalone_layout', source)
    require(spec is not None and spec.loader is not None, 'cannot load reviewed standalone plotter')
    original = importlib.util.module_from_spec(spec); sys.modules[spec.name] = original; spec.loader.exec_module(original)
    tables, copies, inherited, analysis = original.load_evidence(args)
    exact(standalone['input_sha256'], inherited, 'standalone input inventory differs from fresh strict reconstruction')
    exact(standalone['table_counts'], original.COUNTS, 'standalone analysis cardinality differs')
    exact(standalone['clock_flag_count'], analysis['clock_flag_count'], 'standalone clock flags differ')
    for path, expected in inherited.items(): bind(bound, path, expected)
    names = {'plotted_values.json', *(f'analysis_tables/{name}.csv' for name in original.COUNTS)}
    figures = [*('normalized_'+clock for clock in original.CLOCKS), 'google_cpu_models']
    names |= {name+'.'+suffix for name in figures for suffix in ('png','svg','pdf')}
    exact(set(standalone['output_sha256']), names, 'incomplete standalone output inventory')
    for name, expected in standalone['output_sha256'].items(): bind(bound, directory/name, expected)
    values = strict_json(read_bound(bound, directory/'plotted_values.json', standalone['output_sha256']['plotted_values.json']))
    for name, text in copies.items():
        exact(read_bound(bound, directory/'analysis_tables'/name, standalone['output_sha256']['analysis_tables/'+name]), text,
              'standalone copied canonical table differs')
    exact(values, expected_values(original, tables, analysis), 'standalone plotted data differs from checked analysis')
    recheck(bound)
    return original, values, copies, bound


def render(original, values, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Rectangle
    from matplotlib.colors import Normalize
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9.5,'svg.fonttype':'none','pdf.fonttype':42})
    plotted = dict(normalized_points=[], model_cells=[], google_choices=values['google_choices'],
                   common_normalized_y_limits=values['common_normalized_y_limits'], clock_flag_count=values['clock_flag_count'])
    points = {(*original.identity(row),row['clock'],row['n']):row for row in values['normalized_points']}
    cells = {(*original.identity(row),row['window'],row['model']):row for row in values['model_cells']}
    require(len(points)==1056 and len(cells)==288, 'duplicate plotted identity')
    limits = values['common_normalized_y_limits']; realizations = [(g,s) for g in original.GRAPHS for s in original.SAMPLERS]
    markers = ('o','s','^','D')
    def save(fig, name):
        for suffix in ('png','svg','pdf'): fig.savefig(output/(name+'.'+suffix), dpi=200, facecolor='white')
        plt.close(fig)
    def compact(value): return f'{value/1e6:.2g}M' if value>=1e6 else f'{value/1e3:.3g}K'
    for clock in original.CLOCKS:
        fig, axes = plt.subplots(3,1,figsize=(7.05,9.0),sharey=True)
        fig.subplots_adjust(left=.145,right=.975,bottom=.235,top=.89,hspace=.55)
        fig.suptitle('Current KKT: time per input item',fontsize=14,y=.985)
        fig.text(.5,.949,original.CLOCK_NAMES[clock]+' · T / (n + m)',ha='center',fontsize=10)
        for axis, family in zip(axes,original.FAMILIES):
            axis.set_title(original.NAMES[family],fontsize=10.5,pad=9)
            for algorithm in original.ALGORITHMS:
                for index,(graph,sample) in enumerate(realizations):
                    rows = [points[(family,algorithm,graph,sample,clock,n)] for n in original.SIZES]
                    x=[row['N'] for row in rows]; y=[row['median_ns_per_N'] for row in rows]
                    low=[row['minimum_ns_per_N'] for row in rows]; high=[row['maximum_ns_per_N'] for row in rows]
                    require(all(limits[0]<a<=b<=c<limits[1] for a,b,c in zip(low,y,high)), 'paper range would be clipped')
                    axis.errorbar(x,y,yerr=([b-a for a,b in zip(low,y)],[c-b for b,c in zip(y,high)]),
                        color=original.COLORS[algorithm],marker=markers[index],markersize=3.3,
                        linestyle='-' if graph==original.GRAPHS[0] else '--',linewidth=.8,
                        elinewidth=.55,capsize=1.4,alpha=.75)
                    plotted['normalized_points'].extend(rows)
            axis.set_xscale('log',base=2);axis.set_yscale('log');axis.set_ylim(*limits)
            factor=17 if family=='gnm_random' else 33
            ticks=[factor*original.SIZES[i] for i in (0,3,6,10)]
            axis.set_xticks(ticks,[compact(value) for value in ticks]);axis.tick_params(labelsize=8.5)
            axis.set_xlim(factor*original.SIZES[0]*.8,factor*original.SIZES[-1]*1.25)
            axis.set_xlabel('Represented input N = n + m',fontsize=9)
            axis.set_ylabel('ns / input item',fontsize=9)
            axis.grid(True,which='major',alpha=.22);axis.spines[['top','right']].set_visible(False)
        handles=[Line2D([],[],color=original.COLORS[a],linewidth=2,label=original.ALGORITHM_NAMES[a]) for a in original.ALGORITHMS]
        handles += [Line2D([],[],color='#52616c',marker=markers[i],linestyle='-' if g==original.GRAPHS[0] else '--',
                    label=f'G{original.GRAPHS.index(g)+1}/S{original.SAMPLERS.index(s)+1}') for i,(g,s) in enumerate(realizations)]
        fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.125),ncol=3,frameon=False,fontsize=8.5)
        scope='six native calls' if clock.startswith('native_') else 'three library two-call means'
        fig.text(.5,.088,'Median and complete min-max of '+scope+' per size/realization.',ha='center',fontsize=8.5)
        fig.text(.5,.064,'G1 ascending, G2 descending: graph/order confounded. Ranges are not CIs.',ha='center',fontsize=8.5)
        fig.text(.5,.040,'Lines connect observations. All four clocks share y limits; all flags retained.',ha='center',fontsize=8.5)
        fig.text(.5,.018,'Library CPU uses a different timer envelope. No pooled fit or extrapolation.',ha='center',fontsize=8.5)
        save(fig,'paper_normalized_'+clock)
    color_max=max(max(row['plotted_rms_percent'] for row in cells.values()),1e-12)
    labels=[f'{("Ordered" if f==original.FAMILIES[0] else "Shuffled" if f==original.FAMILIES[1] else "G(n,m)")} / '
            f'{("KKT" if a=="kkt" else "retained B")} / G{original.GRAPHS.index(g)+1} S{original.SAMPLERS.index(s)+1}'
            for f,a,g,s in original.curve_order()]
    for window in ('full11','upper6'):
        fig,axis=plt.subplots(figsize=(7.05,9.0));fig.subplots_adjust(left=.32,right=.87,bottom=.17,top=.88)
        grid=[[cells[(*curve,window,model)]['plotted_rms_percent'] for model in original.MODELS] for curve in original.curve_order()]
        image=axis.imshow(grid,aspect='auto',cmap='YlGnBu',norm=Normalize(0,color_max),interpolation='nearest')
        axis.set_xticks(range(6),['1','log N','N','N log N','N²','N³'],fontsize=8.5)
        axis.set_yticks(range(24),labels,fontsize=8.5)
        for index,curve in enumerate(original.curve_order()):
            row_cells=[cells[(*curve,window,model)] for model in original.MODELS]
            require(sum(row['outlined'] is True for row in row_cells)==1,'wrong selected model count')
            for column,row in enumerate(row_cells):
                value=row['plotted_rms_percent']
                axis.text(column,index,format(value,'.2g'),ha='center',va='center',fontsize=8.5,
                          color='white' if value>.60*color_max else '#173044')
                if row['outlined']:axis.add_patch(Rectangle((column-.46,index-.46),.92,.92,fill=False,edgecolor='#d62728',linewidth=1.5))
                plotted['model_cells'].append(row)
        for boundary in (7.5,15.5):axis.axhline(boundary,color='white',linewidth=2)
        color_axis=fig.add_axes((.895,.24,.020,.56));fig.colorbar(image,cax=color_axis,label='Normalized RMS residual (%)')
        fig.suptitle('All 24 curves: six-model residuals',fontsize=14,y=.985)
        subtitle='Full 11 sizes: actual Google oAuto CPU selection' if window=='full11' else 'Upper 6 sizes: separately selected custom CPU fit'
        fig.text(.5,.948,subtitle,ha='center',fontsize=10)
        count=33 if window=='full11' else 18
        fig.text(.5,.920,f'{count} two-call library CPU means per curve; each realization remains separate.',ha='center',fontsize=8.8)
        fig.text(.5,.108,'Red outline: '+('reported Google CPU choice.' if window=='full11' else 'custom upper-window minimum, not a built-in result.'),ha='center',fontsize=8.5)
        fig.text(.5,.080,'Google shares its CPU-selected model with the manual coefficient; CPU RMS only.',ha='center',fontsize=8.5)
        fig.text(.5,.052,'Both pages share color limits. Exact four-clock/all-model values remain in CSV.',ha='center',fontsize=8.5)
        fig.text(.5,.024,'Residual labels are rounded for display. Fit labels do not prove asymptotic complexity.',ha='center',fontsize=8.5)
        save(fig,'paper_google_cpu_models_'+window)
    exact(plotted,values,'paper plotting dropped or changed a standalone value')
    return plotted,matplotlib.__version__


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('analysis','analyzer','collector','standalone-dir','standalone-source','output-dir'):
        parser.add_argument('--'+name,type=Path,required=True)
    for name in ('analyzer-sha256','collector-sha256','standalone-source-sha256'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--released',action='store_true');args=parser.parse_args()
    require(args.released,'explicit nonperformance paper-figure release required')
    output=args.output_dir.resolve();output.mkdir(parents=True,exist_ok=False)
    metadata=dict(schema='current_complexity_paper_figures_v1',validation='running',invocation=sys.argv,
                  source_sha256=digest(__file__),native_solver_execution=False,independent_numerical_audit=False,
                  visual_qa='pending',page_scale_qa='pending')
    try:
        original,values,copies,bound=load(args);metadata['input_sha256']=bound
        plotted,version=render(original,values,output)
        exact(plotted,values,'paper data changed after rendering');recheck(bound)
        (output/'analysis_tables').mkdir()
        for name,text in copies.items():
            with (output/'analysis_tables'/name).open('x') as stream:stream.write(text)
        with (output/'plotted_values.json').open('x') as stream:json.dump(plotted,stream,indent=2,allow_nan=False)
        exact(strict_json((output/'plotted_values.json').read_text()),values,'saved paper values differ')
        recheck(bound)
        metadata.update(validation='rendered_pending_visual_qa',figures=6,formats=['png','svg','pdf'],
                        normalized_points=1056,model_cells=288,google_curves=24,table_counts=original.COUNTS,
                        rows_removed=0,rows_adjusted=0,matplotlib_version=version,
                        figure_inches=[7.05,9.0],plotted_data_equal_to_standalone=True,
                        clock_flag_count=values['clock_flag_count'])
    except BaseException as error:metadata.update(validation='failed',error=repr(error));raise
    finally:
        metadata['output_sha256']={str(path.relative_to(output)):digest(path) for path in output.rglob('*') if path.is_file()}
        with (output/'provenance.json').open('x') as stream:json.dump(metadata,stream,indent=2,allow_nan=False)
    print(json.dumps({key:metadata[key] for key in ('validation','figures','normalized_points','model_cells')}))


if __name__=='__main__':main()
