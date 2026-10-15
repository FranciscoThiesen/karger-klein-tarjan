#!/usr/bin/env python3
"""Plot the complete eighth distance ladder after a separate root release.

Prepared source-only during native capture. Execution and visual validation
must wait for completed strict and independent numerical audits.
"""
import argparse
import json
import math
from pathlib import Path

import run_eighth_distance as study
import plot_retention_control as style

METRICS = {'wall': 'Steady elapsed time', 'cpu': 'Process CPU time'}
GROUPS = (('leaf_distance4', 'Dyadic-distance core ranks'),
          ('leaf_shuffled4', 'Shuffled core ranks'))
KINDS = ('ratios', 'times')
CROSSOVER_COUNTS = {'crossover_points': 60, 'crossover_brackets': 150, 'crossover_summary': 10}
LABELS = {**style.LABELS, 'kkt': 'KKT (private p=1/8)'}


def prepare(cases, tables):
    require = study.require
    expected_cases = {(family, n, 32, 0) for family, _ in GROUPS
                      for n in (1024,4096,16384,65536,262144,1048576)}
    require(len(cases) == 12 and {(r['family'], r['n'], r['density'], r['intrusion_per_mille'])
            for r in cases.values()} == expected_cases == study.EXPECTED_CASES, 'wrong distance plot matrix')
    require(tuple(study.GRAPH_SEEDS) == (21000011, 21000041) and study.SAMPLING_SEED == 3203 and
            len(study.ALGORITHMS) == 6, 'wrong plot seed/solver inventory')
    require({name: len(rows) for name, rows in tables.items()} == {**study.TABLE_COUNTS, **CROSSOVER_COUNTS},
            'incomplete canonical plot/crossover tables')
    result = {}
    for kind in KINDS:
        times = kind == 'times'; names = study.ALGORITHMS if times else study.ALGORITHMS[1:]
        name_field = 'algorithm' if times else 'competitor'
        table, field = ('summary', 'median_ns') if times else ('comparisons', 'median_paired_ratio')
        pooled = style.indexed(tables[table], ('case_id', name_field, 'metric'))
        graphs = style.indexed(tables['graph_' + table], ('case_id', name_field, 'metric', 'graph_seed'))
        expected = {(case, name, metric) for case in cases for name in names for metric in METRICS}
        require(set(pooled) == expected and set(graphs) == {(*key, seed) for key in expected for seed in study.GRAPH_SEEDS},
                'missing case, solver, graph or clock in plot')
        for key, row in pooled.items():
            values = [row[f] for f in (field, 'trial_min', 'trial_max', 'graph_min', 'graph_max')]
            require(row['trials'] == 12 and all(type(v) in (int, float) and math.isfinite(v) and v > 0 for v in values),
                    'invalid pooled plot value or trial count')
            require(row['trial_min'] <= row[field] <= row['trial_max'], 'pooled median outside trial range')
            medians = []
            for seed in study.GRAPH_SEEDS:
                point = graphs[(*key, seed)]
                require(point['trials'] == 6 and all(type(point[f]) in (int, float) and
                        math.isfinite(point[f]) and point[f] > 0 for f in (field, 'trial_min', 'trial_max')),
                        'invalid graph plot value or trial count')
                require(row['trial_min'] <= point['trial_min'] <= point[field] <= point['trial_max'] <= row['trial_max'],
                        'graph point or range excluded from pooled range')
                medians.append(point[field])
            require(min(medians) == row['graph_min'] and max(medians) == row['graph_max'], 'graph range mismatch')
        result[kind] = pooled, graphs, names, field
    grouped = []
    for family, title in GROUPS:
        selected = sorted((r for r in cases.values() if r['family'] == family), key=lambda r: r['n'])
        require(tuple(r['n'] for r in selected) == study.SIZES, 'unplotted or repeated size')
        grouped.append((family, title, selected))
    require(sum(len(selected) for _, _, selected in grouped) == len(cases), 'unplotted family')
    return result, grouped


def render(cases, tables, info, output):
    prepared, grouped = prepare(cases, tables)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FuncFormatter, NullFormatter
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'svg.fonttype': 'none', 'pdf.fonttype': 42})
    generated, coverage, legends = [], [], {}
    for kind, (pooled, graphs, names, field) in prepared.items():
        scale = 1e9 if kind == 'times' else 1
        bounds = {family: style.limits([pooled[(case['case_id'], name, clock)][endpoint] / scale
                  for case in selected for name in names for clock in METRICS for endpoint in ('trial_min', 'trial_max')],
                  () if kind == 'times' else (.9, 1.0)) for family, _, selected in grouped}
        for metric, clock_label in METRICS.items():
            figure, axes = plt.subplots(1, 2, figsize=(15.5, 7.4))
            for axis, (family, title, selected) in zip(axes.flat, grouped):
                sizes = [r['n'] for r in selected]; plotted = []
                for name in names:
                    color = style.COLORS[name]
                    points = [pooled[(r['case_id'], name, metric)] for r in selected]
                    values, low, high = ([p[f] / scale for p in points] for f in (field, 'trial_min', 'trial_max'))
                    axis.vlines(sizes, low, high, color=color, linewidth=1.3, alpha=.25, zorder=1)
                    for gi, seed in enumerate(study.GRAPH_SEEDS):
                        medians = [graphs[(r['case_id'], name, metric, seed)][field] / scale for r in selected]
                        axis.scatter(sizes, medians, marker=('^', 'v')[gi], color=color, s=27, alpha=.42, zorder=2)
                        plotted.extend(medians)
                    axis.plot(sizes, values, color=color, marker='o', markersize=4.5,
                              linewidth=2.3 if name in ('kkt', 'multigraph_boruvka') else 1.6, zorder=3)
                    plotted.extend([*values, *low, *high])
                if kind == 'ratios':
                    axis.axhline(1, color='#555555', linestyle='--', linewidth=1)
                    axis.axhline(.9, color='#888888', linestyle=':', linewidth=1)
                axis.set_xscale('log', base=2); axis.set_yscale('log', base=2 if kind == 'ratios' else 10)
                axis.set_xticks(sizes, [f'{n:,}' for n in sizes]); axis.tick_params(axis='x', labelsize=8, rotation=25)
                axis.set_xlim(min(sizes)/1.18, max(sizes)*1.18); axis.set_ylim(*bounds[family])
                axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f'{value:g}'))
                axis.yaxis.set_minor_formatter(NullFormatter())
                axis.set_title(title + ' · m/n = 32', loc='left', fontsize=11)
                axis.set_xlabel('Vertices n · logarithmic scale')
                axis.set_ylabel('Seconds · logarithmic scale' if kind == 'times' else 'KKT / comparator time · logarithmic scale')
                axis.grid(which='major', alpha=.16)
                lo, hi = axis.get_ylim(); study.require(all(lo <= v <= hi for v in plotted), 'clipped trial endpoint or graph median')
                coverage.append({'figure': kind+'_'+metric, 'family': family, 'case_ids': [r['case_id'] for r in selected],
                    'algorithms': list(names), 'pooled_points': 6*len(names), 'graph_median_points': 12*len(names),
                    'trial_range_endpoints': 12*len(names), 'all_points_in_bounds': True, 'y_limits': [lo, hi]})
            title = 'KKT against all five MST comparators' if kind == 'ratios' else 'Absolute runtime of all six MST implementations'
            figure.suptitle(title+'\n'+clock_label, fontsize=16, y=.99)
            handles = [Line2D([], [], color=style.COLORS[name], marker='o', label=LABELS[name]) for name in names]
            handles += [Line2D([], [], color='#666666', marker='^', linestyle='none', alpha=.42, label='Two graph medians'),
                        Line2D([], [], color='#777777', linewidth=2, alpha=.3, label='Full trial range')]
            legend = figure.legend(handles=handles, loc='lower center', bbox_to_anchor=(.5,.13), ncol=4, frameon=False, fontsize=10)
            labels = [text.get_text() for text in legend.get_texts()]
            study.require(labels == [LABELS[name] for name in names] + ['Two graph medians', 'Full trial range'], 'missing or mislabeled legend')
            legends[kind+'_'+metric] = labels
            statistic = 'durations' if kind == 'times' else 'paired ratios'
            caption = (f'Solid points: medians of twelve {statistic}. Faint triangles: two six-trial graph medians. Vertical spans: every trial-range endpoint.\n'
                       'Two graph seeds × one fixed scalar sampling seed; repetitions reuse each realization. Ranges are descriptive, not confidence intervals.\n'
                       f'Lines connect measured sizes, not inferred thresholds. All {info["flagged_calls"]} flagged calls retained. No normalization or historical pooling.')
            if kind == 'ratios':
                caption += '\nDashed: parity (1.00). Dotted: strong lead (0.90). A crossover needs both graphs/clocks, an earlier loss and strong leads at every larger size.'
            figure.text(.5, .015, caption, ha='center', fontsize=9, linespacing=1.5)
            figure.tight_layout(rect=(0,.27,1,.91), h_pad=2.5, w_pad=2.4)
            for extension in ('png', 'svg', 'pdf'):
                path = output / f'{kind}_{metric}.{extension}'; figure.savefig(path, dpi=180, bbox_inches='tight'); generated.append(path)
            plt.close(figure)
    return generated, coverage, legends, matplotlib.__version__


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--released', action='store_true'); args = parser.parse_args()
    study.require(args.released, 'plotting requires root release after timing')
    output = args.output.resolve(); study.require(not output.exists(), 'refusing to overwrite plots')
    info, cases, rows, _, _, inputs = study.load(args.capture)
    study.require(len(rows) == 1008 and len(info['captures']) == 24, 'incomplete capture')
    tables = study.aggregate(rows); tables.update(study.crossovers(tables, cases)); prepare(cases, tables)
    inputs = {**inputs, **study.helpers(), str(Path(__file__).resolve()): study.native.sha(__file__),
              str(Path(style.__file__).resolve()): study.native.sha(style.__file__)}
    output.mkdir(parents=True); study.write_json(output/'plotted_values.json', tables, exclusive=True)
    generated, coverage, legends, version = render(cases, tables, info, output)
    study.require(len(coverage) == 8 and all(r['all_points_in_bounds'] for r in coverage), 'missing panel coverage')
    bounds = {(r['figure'], r['family']): r['y_limits'] for r in coverage}
    for kind in KINDS:
        for family, _ in GROUPS:
            study.require(bounds[(kind+'_wall',family)] == bounds[(kind+'_cpu',family)], 'clock axes differ')
    for path, digest in inputs.items(): study.analysis.hash_check(Path(path), digest)
    generated.append(output/'plotted_values.json')
    study.write_json(output/'provenance.json', {'schema': 'eighth_distance_figures_v1', 'validation': 'pass',
        'capture': str(args.capture.resolve()), 'input_sha256': inputs, 'matplotlib_version': version,
        'checked_outputs': 1008, 'timed_outputs': 864, 'warmup_outputs': 144, 'rows_removed': 0, 'rows_adjusted': 0,
        'graph_realizations': 2, 'sampling_seeds': [study.SAMPLING_SEED], 'trials_per_case': 12,
        'flagged_calls_retained': info['flagged_calls'], 'coverage': coverage, 'legends': legends,
        'control_normalization': False, 'confidence_intervals': False, 'interpolated_crossover': False,
        'matched_clock_axes': True, 'output_sha256': {p.name: study.native.sha(p) for p in generated},
        'visual_review': 'pending: inspect all four PNGs before publication'}, exclusive=True)
    (output/'README.md').write_text('# Eighth distance/shuffled ladder figures\n\n'
        'All 1,008 checked outputs are strictly revalidated before plotting. Four figures show both clocks for all '
        'five KKT/comparator ratios and all six absolute solver times across two families and six sizes. Each PNG '
        'has SVG/PDF counterparts. Solid points pool twelve trials; faint markers retain both six-trial graph medians '
        'and spans retain every trial-range endpoint. Repetitions reuse two graph realizations with one fixed sampler seed. '
        'Both clocks have matching panel axes. KKT labels identify its private sampling rate. No normalization, historical pooling, '
        'confidence intervals or interpolated crossover is claimed. All 60 exact point classifications, 150 endpoint '
        'pairs and 10 crossover summaries are preserved with the canonical tables in plotted_values.json. Visual review is pending.\n')
    print(json.dumps({'validation': 'pass', 'figures': 4, 'panels': 8, 'output': str(output), 'visual_review': 'pending'}))


if __name__ == '__main__': main()
