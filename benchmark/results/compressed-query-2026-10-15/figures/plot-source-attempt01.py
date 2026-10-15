#!/usr/bin/env python3
"""Prepared compressed-query plots; install in benchmark/ after root release.

Source only: not imported, tested, or rendered during the active packed capture.
"""
import argparse
import json
import math
from pathlib import Path

import run_compressed_queries as study
import plot_retention_control as style

METRICS = {'wall': 'Steady elapsed time', 'cpu': 'Process CPU time'}
GROUPS = (('leaf_hierarchy4', 32, 'Ordered core ranks · m/n = 32'),
          ('leaf_shuffled4', 32, 'Shuffled core ranks · m/n = 32'),
          ('gnm_random', 16, 'Random G(n,m) · m/n = 16'))
KINDS = ('variant_gains', 'reference_ratios', 'compressed_ratios', 'reference_times', 'compressed_times')
REALIZATIONS = tuple((graph, seed) for graph in study.GRAPH_SEEDS for seed in study.SAMPLING_SEEDS)


def prepare(cases, tables):
    require = study.require
    require(study.VARIANTS == ('reference', 'compressed') and len(study.GRAPH_SEEDS) == 2
            and len(study.SAMPLING_SEEDS) == 1 and len(REALIZATIONS) == 2, 'wrong plot seed/variant design')
    require(len(cases) == 6 and {(r['family'], r['n'], r['density'], r['intrusion_per_mille'])
            for r in cases.values()} == study.EXPECTED_CASES, 'wrong plot matrix')
    require({key: len(value) for key, value in tables.items()} == study.TABLE_COUNTS, 'incomplete plot tables')
    result = {}
    for kind in KINDS:
        times = kind.endswith('_times')
        name_field = 'algorithm' if times or kind == 'variant_gains' else 'competitor'
        names = study.ALGORITHMS if name_field == 'algorithm' else study.ALGORITHMS[1:]
        table = 'variant_comparisons' if kind == 'variant_gains' else ('summary' if times else 'comparisons')
        selected = {name: [row for row in tables[name] if kind == 'variant_gains' or row['variant'] == kind.split('_')[0]]
                    for name in (table, 'realization_' + table)}
        pooled = style.indexed(selected[table], ('case_id', name_field, 'metric'))
        realizations = style.indexed(selected['realization_' + table], ('case_id', name_field, 'metric', 'graph_seed', 'kkt_seed'))
        expected = {(case, name, metric) for case in cases for name in names for metric in METRICS}
        require(set(pooled) == expected and set(realizations) == {(*key, *identity) for key in expected for identity in REALIZATIONS},
                'missing plot identity')
        value_field = 'median_ns' if times else 'median_paired_ratio'
        for key, row in pooled.items():
            require(row['trials'] == 12, 'pooled plot point must include twelve trials')
            values = [row[field] for field in (value_field, 'trial_min', 'trial_max', 'realization_min', 'realization_max')]
            require(all(type(value) in (int, float) and math.isfinite(value) and value > 0 for value in values), 'invalid plot value')
            medians = []
            for identity in REALIZATIONS:
                point = realizations[(*key, *identity)]
                require(point['trials'] == 6 and row['trial_min'] <= point['trial_min'] <= point[value_field]
                        <= point['trial_max'] <= row['trial_max'], 'graph realization outside full range')
                medians.append(point[value_field])
            require(min(medians) == row['realization_min'] and max(medians) == row['realization_max'] and
                    row['trial_min'] <= row[value_field] <= row['trial_max'], 'range mismatch')
        result[kind] = pooled, realizations, names, value_field
    groups = []
    for family, density, title in GROUPS:
        selected = sorted((r for r in cases.values() if r['family'] == family and r['density'] == density), key=lambda r: r['n'])
        require(len(selected) == 2, 'unplotted endpoint')
        groups.append((title, selected))
    return result, groups


def render(cases, tables, info, output):
    prepared, groups = prepare(cases, tables)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FuncFormatter
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'svg.fonttype': 'none', 'pdf.fonttype': 42})
    generated, coverage = [], []
    for kind, (pooled, realizations, names, field) in prepared.items():
        times = kind.endswith('_times'); scale = 1e9 if times else 1
        bounds = {title: style.limits([pooled[(case['case_id'], name, clock)][endpoint] / scale
                  for case in selected for name in names for clock in METRICS for endpoint in ('trial_min', 'trial_max')],
                  () if times else (.9, 1.0)) for title, selected in groups}
        for metric, clock_label in METRICS.items():
            figure, axes = plt.subplots(1, 3, figsize=(17.5, 6.7))
            for axis, (title, selected) in zip(axes, groups):
                sizes = [case['n'] for case in selected]; all_values = []
                for name in names:
                    color = style.COLORS[name]
                    points = [pooled[(case['case_id'], name, metric)] for case in selected]
                    values, lower, upper = ([point[value] / scale for point in points]
                                             for value in (field, 'trial_min', 'trial_max'))
                    axis.vlines(sizes, lower, upper, color=color, linewidth=1.2, alpha=.28)
                    for ri, identity in enumerate(REALIZATIONS):
                        medians = [realizations[(case['case_id'], name, metric, *identity)][field] / scale for case in selected]
                        axis.scatter(sizes, medians, marker=('^', 'v')[ri], color=color, s=27, alpha=.42, zorder=2)
                        all_values.extend(medians)
                    axis.plot(sizes, values, color=color, marker='o', markersize=4.5,
                              linewidth=2.3 if name in ('kkt', 'multigraph_boruvka') else 1.6, zorder=3)
                    all_values.extend([*values, *lower, *upper])
                if not times:
                    axis.axhline(1, color='#555555', linestyle='--', linewidth=1)
                    axis.axhline(.9, color='#888888', linestyle=':', linewidth=1)
                axis.set_xscale('log', base=2)
                if kind != 'variant_gains': axis.set_yscale('log', base=2)
                axis.set_xticks(sizes, [f'{n:,}' for n in sizes]); axis.set_xlim(min(sizes)/1.18, max(sizes)*1.18)
                axis.set_ylim(*bounds[title]); axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f'{value:g}'))
                axis.set_title(title, loc='left', fontsize=11); axis.set_xlabel('Vertices n · logarithmic scale')
                axis.set_ylabel('Seconds · logarithmic scale' if times else ('Compressed / reference time' if kind == 'variant_gains' else 'KKT / comparator time · logarithmic scale'))
                axis.grid(which='major', alpha=.16)
                low, high = axis.get_ylim(); study.require(all(low <= value <= high for value in all_values), 'clipped trial endpoint')
                coverage.append({'figure': kind+'_'+metric, 'group': title, 'case_ids': [r['case_id'] for r in selected],
                    'algorithms': list(names), 'pooled_points': 2*len(names), 'realization_points': 4*len(names),
                    'trial_range_endpoints': 4*len(names), 'all_points_in_bounds': True, 'y_limits': [low, high]})
            title = ('Compressed / reference: all six solvers' if kind == 'variant_gains' else
                     kind.split('_')[0].title() + (' absolute solver times' if times else ' KKT against all five MST comparators'))
            figure.suptitle(title+'\n'+clock_label, fontsize=16, y=.99)
            handles = [Line2D([], [], color=style.COLORS[name], marker='o', label=style.LABELS.get(name, 'KKT')) for name in names]
            handles += [Line2D([], [], color='#666666', marker='^', linestyle='none', alpha=.42, label='Two graph medians · one fixed sampler seed'),
                        Line2D([], [], color='#777777', linewidth=2, alpha=.3, label='Full trial range')]
            statistic = 'twelve individual durations' if times else 'twelve individual paired ratios'
            caption = (f'Solid points are medians of {statistic}; faint markers show two six-trial graph medians. Repetitions reuse each graph.\n'
                       'Two graph seeds × one fixed scalar sampling seed. All cases, controls, losses and ranges remain; ranges are descriptive, not confidence intervals.\n'
                       f'Lines connect tested endpoints without threshold interpolation. All {info["flagged_calls"]} flagged calls retained. No control normalization or historical pooling.')
            figure.text(.5, .015, caption, ha='center', fontsize=8.4, linespacing=1.5)
            figure.tight_layout(rect=(0,.25,1,.9), w_pad=2.5)
            for extension in ('png','svg','pdf'):
                path = output / f'{kind}_{metric}.{extension}'; figure.savefig(path, dpi=180, bbox_inches='tight'); generated.append(path)
            plt.close(figure)
    return generated, coverage, matplotlib.__version__


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--released', action='store_true'); args = parser.parse_args()
    study.require(args.released, 'plotting requires root release after timing')
    output = args.output.resolve(); study.require(not output.exists(), 'refusing to overwrite plots')
    info, cases, rows, _, _, inputs = study.load(args.capture)
    study.require(len(rows) == 1008 and len(info['captures']) == 24, 'incomplete capture')
    tables = study.aggregate(rows); prepare(cases, tables)
    inputs = {**inputs, **study.helpers(), str(Path(__file__).resolve()): study.native.sha(__file__),
              str(Path(style.__file__).resolve()): study.native.sha(style.__file__)}
    output.mkdir(parents=True); study.write_json(output/'plotted_values.json', tables, exclusive=True)
    generated, coverage, version = render(cases, tables, info, output)
    study.require(len(coverage) == 30 and all(row['all_points_in_bounds'] for row in coverage), 'missing plot coverage')
    limits = {(row['figure'],row['group']): row['y_limits'] for row in coverage}
    for kind in KINDS:
        for _,_,title in GROUPS: study.require(limits[(kind+'_wall',title)] == limits[(kind+'_cpu',title)], 'clock axes differ')
    for path, digest in inputs.items(): study.analysis.hash_check(Path(path), digest)
    generated.append(output/'plotted_values.json')
    study.write_json(output/'provenance.json', {'schema':'compressed_query_figures_v1','validation':'pass',
        'capture':str(args.capture.resolve()),'input_sha256':inputs,'matplotlib_version':version,
        'checked_outputs':1008,'timed_outputs':864,'warmup_outputs':144,'rows_removed':0,'rows_adjusted':0,
        'graph_realizations':2,'sampling_seeds':list(study.SAMPLING_SEEDS),'trials_per_case':12,
        'flagged_calls_retained':info['flagged_calls'],'coverage':coverage,'control_normalization':False,
        'confidence_intervals':False,'interpolated_crossover':False,'matched_clock_axes':True,
        'output_sha256':{path.name:study.native.sha(path) for path in generated},
        'visual_review':'pending: inspect all ten PNGs before publication'},exclusive=True)
    (output/'README.md').write_text('# Compressed-query figures\n\n'
        'All 1,008 checked outputs are strictly revalidated before plotting. Ten figures show both clocks for all-six '
        'compressed/reference drift, both variants against all five comparators, and both variants’ absolute solver times. '
        'Each PNG has SVG/PDF counterparts. Solid points are pooled medians of twelve individual paired ratios or durations; '
        'two faint markers show six-trial graph medians, and spans retain every trial-range endpoint. '
        'Two graph seeds use one fixed scalar sampling seed; repeated runs are not additional independent graphs or samplers. '
        'Clock figures use matching axes. No normalization, historical pooling, confidence intervals or interpolated crossover. '
        'Canonical graph and single-sampler marginal summaries remain in plotted_values.json; the single-sampler marginal '
        'equals the pooled case summary and supplies no extra independent realization. Visual review is pending.\n')
    print(json.dumps({'validation':'pass','figures':10,'output':str(output),'visual_review':'pending'}))


if __name__ == '__main__': main()
