#!/usr/bin/env python3
"""Plot the complete lower-density ladders after a separate root release.

Prepared source-only during native capture. Execution and visual validation
must wait for completed strict and independent numerical audits.
"""
import argparse
import json
import math
from pathlib import Path

import run_lower_density as study
import plot_retention_control as style

METRICS = {'wall': 'Steady elapsed time', 'cpu': 'Process CPU time'}
GROUPS = (('leaf_distance4', 16, 'Dyadic-distance core ranks'),
          ('leaf_shuffled4', 16, 'Shuffled core ranks'),
          ('leaf_distance4', 8, 'Dyadic-distance core ranks'),
          ('leaf_shuffled4', 8, 'Shuffled core ranks'))
SIZE_LADDERS = {16: (512, 2048, 8192, 32768, 131072, 524288, 2097152),
                8: (256, 1024, 4096, 16384, 65536, 262144, 1048576, 4194304)}
KINDS = ('ratios', 'times')
CROSSOVER_COUNTS = {'crossover_points': 150, 'crossover_brackets': 490, 'crossover_summary': 20}
LABELS = {**style.LABELS, 'kkt': 'KKT (private p=1/8)'}


def prepare(cases, tables):
    require = study.require
    expected_cases = {(family, n, density, 0) for family, density, _ in GROUPS
                      for n in SIZE_LADDERS[density]}
    require(len(cases) == 30 and {(r['family'], r['n'], r['density'], r['intrusion_per_mille'])
            for r in cases.values()} == expected_cases == study.EXPECTED_CASES, 'wrong lower-density plot matrix')
    require(study.SIZE_LADDERS == SIZE_LADDERS, 'wrong per-density size ladders')
    require(tuple(study.GRAPH_SEEDS) == (23000003, 23000029) and study.SAMPLING_SEED == 3407 and
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
    for family, density, title in GROUPS:
        selected = sorted((r for r in cases.values() if r['family'] == family and r['density'] == density), key=lambda r: r['n'])
        require(tuple(r['n'] for r in selected) == SIZE_LADDERS[density], 'unplotted or repeated size')
        grouped.append((family, density, title, selected))
    require(sum(len(selected) for _, _, _, selected in grouped) == len(cases), 'unplotted family/density')
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
        bounds = {(family, density): style.limits([pooled[(case['case_id'], name, clock)][endpoint] / scale
                  for case in selected for name in names for clock in METRICS for endpoint in ('trial_min', 'trial_max')],
                  () if kind == 'times' else (.9, 1.0)) for family, density, _, selected in grouped}
        for metric, clock_label in METRICS.items():
            figure, axes = plt.subplots(2, 2, figsize=(15.5, 11.8))
            for axis, (family, density, title, selected) in zip(axes.flat, grouped):
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
                axis.set_xticks(sizes, [f'{n:,}' for n in sizes]); axis.tick_params(axis='x', labelsize=8.5, rotation=25)
                axis.set_xlim(min(sizes)/1.18, max(sizes)*1.18); axis.set_ylim(*bounds[(family,density)])
                axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f'{value:g}'))
                axis.yaxis.set_minor_formatter(NullFormatter())
                axis.set_title(title + f' · m/n = {density}', loc='left', fontsize=11)
                axis.set_xlabel('Vertices n · logarithmic scale')
                axis.set_ylabel('Seconds · logarithmic scale' if kind == 'times' else 'KKT / comparator time · logarithmic scale')
                axis.grid(which='major', alpha=.16)
                lo, hi = axis.get_ylim(); study.require(all(lo <= v <= hi for v in plotted), 'clipped trial endpoint or graph median')
                coverage.append({'figure': kind+'_'+metric, 'family': family, 'density': density,
                    'case_ids': [r['case_id'] for r in selected], 'algorithms': list(names),
                    'pooled_points': len(selected)*len(names), 'graph_median_points': 2*len(selected)*len(names),
                    'trial_range_endpoints': 2*len(selected)*len(names), 'all_points_in_bounds': True, 'y_limits': [lo, hi]})
            title = 'KKT against all five MST comparators' if kind == 'ratios' else 'Absolute runtime of all six MST implementations'
            figure.suptitle(title+'\n'+clock_label, fontsize=16, y=.99)
            handles = [Line2D([], [], color=style.COLORS[name], marker='o', label=LABELS[name]) for name in names]
            handles += [Line2D([], [], color='#666666', marker='^', linestyle='none', alpha=.42, label='Two graph medians'),
                        Line2D([], [], color='#777777', linewidth=2, alpha=.3, label='Full trial range')]
            legend = figure.legend(handles=handles, loc='lower center', bbox_to_anchor=(.5,.092), ncol=4, frameon=False, fontsize=10)
            labels = [text.get_text() for text in legend.get_texts()]
            study.require(labels == [LABELS[name] for name in names] + ['Two graph medians', 'Full trial range'], 'missing or mislabeled legend')
            legends[kind+'_'+metric] = labels
            statistic = 'durations' if kind == 'times' else 'paired ratios'
            caption = (f'Solid points: medians of twelve {statistic}. Faint triangles: two six-trial graph medians. Vertical spans: every trial-range endpoint.\n'
                       'Two graph seeds × one fixed sampler; graph two reverses the full schedule. Repetitions reuse each realization; ranges are not confidence intervals.\n'
                       f'Lines connect measured sizes, not inferred thresholds. All {info["flagged_calls"]} flagged calls retained. No normalization or historical pooling.')
            if kind == 'ratios':
                caption += '\nDashed: parity (1.00). Dotted: strong lead (0.90). Within each density, crossover needs both graphs/clocks, an earlier loss and all larger sizes strong.'
            figure.text(.5, .015, caption, ha='center', fontsize=9, linespacing=1.5)
            figure.tight_layout(rect=(0,.18,1,.94), h_pad=2.8, w_pad=2.4)
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
    study.require(len(rows) == 2520 and len(info['captures']) == 60, 'incomplete capture')
    tables = study.aggregate(rows); tables.update(study.crossovers(tables, cases)); prepare(cases, tables)
    inputs = {**inputs, **study.helpers(), str(Path(__file__).resolve()): study.native.sha(__file__),
              str(Path(style.__file__).resolve()): study.native.sha(style.__file__)}
    output.mkdir(parents=True); study.write_json(output/'plotted_values.json', tables, exclusive=True)
    generated, coverage, legends, version = render(cases, tables, info, output)
    study.require(len(coverage) == 16 and all(r['all_points_in_bounds'] for r in coverage), 'missing panel coverage')
    bounds = {(r['figure'], r['family'], r['density']): r['y_limits'] for r in coverage}
    for kind in KINDS:
        for family, density, _ in GROUPS:
            study.require(bounds[(kind+'_wall',family,density)] == bounds[(kind+'_cpu',family,density)], 'clock axes differ')
    for path, digest in inputs.items(): study.analysis.hash_check(Path(path), digest)
    generated.append(output/'plotted_values.json')
    study.write_json(output/'provenance.json', {'schema': 'lower_density_figures_v1', 'validation': 'pass',
        'capture': str(args.capture.resolve()), 'input_sha256': inputs, 'matplotlib_version': version,
        'checked_outputs': 2520, 'timed_outputs': 2160, 'warmup_outputs': 360, 'rows_removed': 0, 'rows_adjusted': 0,
        'graph_realizations': 2, 'sampling_seeds': [study.SAMPLING_SEED], 'trials_per_case': 12,
        'flagged_calls_retained': info['flagged_calls'], 'coverage': coverage, 'legends': legends,
        'control_normalization': False, 'confidence_intervals': False, 'interpolated_crossover': False,
        'matched_clock_axes': True, 'output_sha256': {p.name: study.native.sha(p) for p in generated},
        'visual_review': 'pending: inspect all four PNGs before publication'}, exclusive=True)
    (output/'README.md').write_text('# Lower-density distance/shuffled ladder figures\n\n'
        'All 2,520 checked outputs are strictly revalidated before plotting. Four figures show both clocks for all '
        'five KKT/comparator ratios and all six absolute solver times across two families at each of two densities. '
        'The m/n=16 ladder has seven sizes and the m/n=8 ladder has eight; all points are retained. Each PNG '
        'has SVG/PDF counterparts. Solid points pool twelve trials; faint markers retain both six-trial graph medians '
        'and spans retain every trial-range endpoint. Repetitions reuse two graph realizations with one fixed sampler seed. '
        'Both clocks have matching panel axes. KKT labels identify its private sampling rate. No normalization, historical pooling, '
        'confidence intervals or interpolated crossover is claimed. All 150 exact point classifications, 490 endpoint '
        'pairs and 20 crossover summaries are preserved with the canonical tables in plotted_values.json. Densities are never pooled. Visual review is pending.\n')
    print(json.dumps({'validation': 'pass', 'figures': 4, 'panels': 16, 'output': str(output), 'visual_review': 'pending'}))


if __name__ == '__main__': main()
