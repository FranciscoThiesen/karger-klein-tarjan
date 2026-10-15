#!/usr/bin/env python3
"""Re-layout the complete audited eighth-distance ladder at paper width.

This presentation adapter rereads the strict capture and requires exact equality
with the standalone plotted tables. It does not perform an independent audit.
Execution requires a separate release after the complete native study/audit.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

WIDTH = 7.1
SIZES = (1024, 4096, 16384, 65536, 262144, 1048576)
FAMILIES = ('leaf_distance4', 'leaf_shuffled4')
GRAPHS = (21000011, 21000041)
TABLE_COUNTS = {'paired_ratios': 1440, 'comparisons': 120, 'graph_comparisons': 240,
                'summary': 144, 'graph_summary': 288,
                'crossover_points': 60, 'crossover_brackets': 150, 'crossover_summary': 10}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bind(bound, path, expected=None):
    path = Path(path).resolve(strict=True)
    actual = sha(path)
    require(expected is None or actual == expected, 'Changed input: ' + str(path))
    require(str(path) not in bound or bound[str(path)] == actual, 'Conflicting input: ' + str(path))
    bound[str(path)] = actual
    return path


def recheck(bound):
    for path, value in bound.items():
        bind(bound, path, value)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def same(actual, expected, message):
    require(canonical(actual) == canonical(expected), message)


def write_json(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def checked_load(args):
    bound = {}
    bind(bound, __file__)
    capture = bind(bound, args.capture)
    standalone = args.standalone.resolve(strict=True)
    provenance = json.loads(bind(bound, standalone / 'provenance.json').read_text())
    same(provenance.get('schema'), 'eighth_distance_figures_v1', 'Wrong standalone figure schema')
    same(provenance.get('validation'), 'pass', 'Standalone figures incomplete')
    require(Path(provenance['capture']).resolve(strict=True) == capture, 'Standalone capture differs')
    for path, value in provenance['input_sha256'].items():
        bind(bound, path, value)
    for name, value in provenance['output_sha256'].items():
        target = (standalone / name).resolve(strict=True)
        require(target.is_relative_to(standalone), 'Standalone output path escapes its directory')
        bind(bound, target, value)
    require('plotted_values.json' in provenance['output_sha256'], 'Standalone plotted tables not bound')
    previous = json.loads(bind(bound, standalone / 'plotted_values.json').read_text())
    source_path = bind(bound, args.source_plot)
    require(str(source_path) in provenance['input_sha256'], 'Standalone did not bind this plot source')
    audit = json.loads(bind(bound, args.audit).read_text())
    expected = dict(schema='independent_eighth_distance_numerical_audit_v1', validation='pass',
                    collector_imported=False, raw_native_children=24, checked_outputs=1008,
                    timed_outputs=864, warmup_outputs=144)
    for key, value in expected.items():
        require(type(audit.get(key)) is type(value) and audit[key] == value, 'Wrong independent audit ' + key)
    require(audit['input_sha256'].get(str(capture)) == sha(capture), 'Audit does not bind this capture')
    for path, value in audit['input_sha256'].items():
        bind(bound, path, value)
    saved_path = sys.path[:]
    try:
        sys.path.insert(0, str(source_path.parent))
        spec = importlib.util.spec_from_file_location('_distance_paper_standalone', source_path)
        require(spec is not None and spec.loader is not None, 'Cannot load reviewed standalone source')
        source = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = source
        spec.loader.exec_module(source)
        study = source.study
        require(tuple(study.GRAPH_SEEDS) == GRAPHS and study.SAMPLING_SEED == 3203 and
                tuple(study.SIZES) == SIZES, 'Distance declaration changed')
        info, cases, rows, _, _, inherited = study.load(capture)
        require(len(rows) == 1008 and len(info['captures']) == 24, 'Incomplete distance capture')
        for inventory in (inherited, study.helpers()):
            for path, value in inventory.items():
                bind(bound, path, value)
        tables = study.aggregate(rows)
        tables.update(study.crossovers(tables, cases))
        source.prepare(cases, tables)
        same({name: len(values) for name, values in tables.items()}, TABLE_COUNTS, 'Wrong table cardinalities')
        same(tables, previous, 'Raw-derived tables differ from the standalone plotted values')
        recheck(bound)
        return source, cases, tables, info, bound
    finally:
        sys.path[:] = saved_path


def point_key(row):
    return row['kind'], row['metric'], row['case_id'], row['algorithm']


def paper_data(source, cases, tables):
    prepared, grouped = source.prepare(cases, tables)
    require(tuple(family for family, _, _ in grouped) == FAMILIES, 'Wrong family order')
    require(len(cases) == 12 and all(tuple(c['n'] for c in selected) == SIZES
            for _, _, selected in grouped), 'Wrong six-size plot matrix')
    points = []
    for kind in ('ratios', 'times'):
        pooled, graphs, algorithms, field = prepared[kind]
        require(tuple(algorithms) == tuple(source.study.ALGORITHMS if kind == 'times' else
                                           source.study.ALGORITHMS[1:]), 'Missing solver series')
        scale = 1e9 if kind == 'times' else 1
        for metric in ('wall', 'cpu'):
            for _, _, selected in grouped:
                for case in selected:
                    for algorithm in algorithms:
                        row = pooled[(case['case_id'], algorithm, metric)]
                        points.append(dict(kind=kind, metric=metric, case_id=case['case_id'],
                            algorithm=algorithm, n=case['n'], median=row[field] / scale,
                            minimum=row['trial_min'] / scale, maximum=row['trial_max'] / scale,
                            graph_medians=[graphs[(case['case_id'], algorithm, metric, seed)][field] / scale
                                           for seed in GRAPHS]))
    require(len(points) == 264 and len({point_key(row) for row in points}) == 264,
            'Missing or duplicate publication point')
    return grouped, points


def render(source, cases, tables, info, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FuncFormatter, NullFormatter
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9.5,
        'axes.spines.top': False, 'axes.spines.right': False, 'svg.fonttype': 'none', 'pdf.fonttype': 42})
    grouped, expected = paper_data(source, cases, tables)
    indexed = {point_key(row): row for row in expected}
    emitted, coverage, legends = [], [], {}
    style = source.style
    for kind in ('ratios', 'times'):
        algorithms = source.study.ALGORITHMS if kind == 'times' else source.study.ALGORITHMS[1:]
        limits = {family: style.limits([indexed[(kind, clock, case['case_id'], algorithm)][endpoint]
                  for case in selected for algorithm in algorithms for clock in ('wall', 'cpu')
                  for endpoint in ('minimum', 'maximum')], () if kind == 'times' else (.9, 1))
                  for family, _, selected in grouped}
        for metric, clock_title in source.METRICS.items():
            figure, axes = plt.subplots(2, 1, figsize=(WIDTH, 8.8))
            # The explicit right margin preserves the complete final-size label.
            # Additional lower space separates the three-line caption and legend.
            figure.subplots_adjust(left=.17, right=.94, bottom=.22, top=.91, hspace=.53)
            for axis, (family, title, selected) in zip(axes, grouped):
                sizes = [case['n'] for case in selected]
                plotted = []
                for algorithm in algorithms:
                    rows = [indexed[(kind, metric, case['case_id'], algorithm)] for case in selected]
                    middle = [row['median'] for row in rows]
                    low = [row['minimum'] for row in rows]
                    high = [row['maximum'] for row in rows]
                    color = style.COLORS[algorithm]
                    axis.vlines(sizes, low, high, color=color, alpha=.3, linewidth=1.2)
                    for index in range(2):
                        medians = [row['graph_medians'][index] for row in rows]
                        axis.scatter(sizes, medians, marker=('^', 'v')[index], color=color, alpha=.5, s=20)
                        plotted.extend(medians)
                    axis.plot(sizes, middle, color=color, marker='o', markersize=3.7, linewidth=1.5)
                    plotted.extend([*middle, *low, *high])
                    emitted.extend(rows)
                if kind == 'ratios':
                    axis.axhline(1, color='#555555', linestyle='--', linewidth=.9)
                    axis.axhline(.9, color='#888888', linestyle=':', linewidth=.9)
                axis.set_xscale('log', base=2)
                axis.set_yscale('log', base=10 if kind == 'times' else 2)
                axis.set_xlim(min(sizes) / 1.18, max(sizes) * 1.18)
                axis.set_ylim(*limits[family])
                axis.set_xticks(sizes, [f'{n:,}' for n in sizes])
                axis.tick_params(axis='x', labelsize=8.5)
                axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f'{value:g}'))
                axis.yaxis.set_minor_formatter(NullFormatter())
                axis.grid(which='major', alpha=.16)
                axis.set_title(title + ' (m/n = 32)', loc='left', fontsize=10)
                axis.set_xlabel('Vertices n (log scale)', fontsize=9.5)
                axis.set_ylabel('Seconds (log scale)' if kind == 'times' else 'KKT / comparator time', fontsize=9.5)
                lo, hi = axis.get_ylim()
                require(all(lo <= value <= hi for value in plotted), 'A paper trial endpoint or graph median is clipped')
                coverage.append(dict(figure=kind + '_' + metric, family=family,
                    case_ids=[case['case_id'] for case in selected], algorithms=list(algorithms),
                    pooled_points=6 * len(algorithms), graph_medians=12 * len(algorithms),
                    trial_range_endpoints=12 * len(algorithms), limits=[lo, hi]))
            title = 'Eighth KKT against all five comparators' if kind == 'ratios' else 'All six solver times'
            figure.suptitle(title + '\n' + clock_title, fontsize=12, y=.985)
            labels = [source.LABELS[algorithm] for algorithm in algorithms]
            handles = [Line2D([], [], color=style.COLORS[algorithm], marker='o', label=label)
                       for algorithm, label in zip(algorithms, labels)]
            handles += [Line2D([], [], color='#666666', marker='^', linestyle='none', label='Two graph medians'),
                        Line2D([], [], color='#777777', alpha=.4, linewidth=2, label='Full trial range')]
            legend = figure.legend(handles=handles, loc='lower center', bbox_to_anchor=(.5, .075),
                                   ncol=3, frameon=False, fontsize=8.5)
            actual_labels = [item.get_text() for item in legend.get_texts()]
            same(actual_labels, labels + ['Two graph medians', 'Full trial range'], 'Missing paper legend')
            legends[kind + '_' + metric] = actual_labels
            thresholds = 'Ratios: dashed 1.00 = parity; dotted 0.90 = strong-lead threshold.' if kind == 'ratios' else 'No normalization or historical pooling.'
            caption = ('Twelve trials per point; two graphs, one fixed sampler. All ranges are descriptive.\n'
                       f'Lines connect measured sizes only. All {info["flagged_calls"]} flagged calls retained.\n' + thresholds)
            figure.text(.5, .012, caption, ha='center', fontsize=8.5, linespacing=1.4)
            require(float(figure.get_size_inches()[0]) == WIDTH, 'Paper canvas width changed')
            for suffix in ('png', 'svg', 'pdf'):
                figure.savefig(output / ('paper_' + kind + '_' + metric + '.' + suffix), dpi=220, facecolor='white')
            plt.close(figure)
    actual = {point_key(row): row for row in emitted}
    require(len(emitted) == len(actual) == 264, 'Publication omitted or repeated an observation')
    require(set(actual) == set(indexed), 'Publication point identities differ')
    same([actual[key] for key in sorted(actual)], [indexed[key] for key in sorted(indexed)],
         'Publication data differ from checked standalone summaries')
    require(len(coverage) == 8, 'Publication panel missing')
    for kind in ('ratios', 'times'):
        for family in FAMILIES:
            bounds = [item['limits'] for item in coverage if item['family'] == family and
                      item['figure'] in (kind + '_wall', kind + '_cpu')]
            require(len(bounds) == 2 and bounds[0] == bounds[1], 'Clock panel axes differ')
    return dict(points=emitted, coverage=coverage, legends=legends, figures=4,
                matplotlib_version=matplotlib.__version__)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('capture', 'source-plot', 'standalone', 'audit', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--released', action='store_true')
    args = parser.parse_args()
    require(args.released, 'Explicit postcapture publication release required')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    metadata = dict(schema='eighth_distance_publication_figures_v1', validation='running', invocation=sys.argv,
                    native_solver_execution=False, independent_numerical_audit=False, visual_review='pending')
    try:
        source, cases, tables, info, bound = checked_load(args)
        metadata['input_sha256'] = bound
        result = render(source, cases, tables, info, output)
        write_json(output / 'plotted_values.json', tables)
        write_json(output / 'paper_points.json', result)
        recheck(bound)
        metadata.update(validation='rendered_pending_visual_qa', figures=4, figure_width_inches=WIDTH,
            checked_outputs=1008, timed_outputs=864, warmup_outputs=144, pooled_summaries=264,
            graph_medians=528, trial_range_endpoints=528, minimum_label_points=8.5,
            standalone_plotted_values_equal=True, all_observations_drawn=True,
            original_artifacts_modified=False, matched_clock_axes=True, rows_removed=0, rows_adjusted=0,
            confidence_intervals=False, interpolated_crossovers=False, historical_pooling=False)
    except BaseException as error:
        metadata.update(validation='failed', error=repr(error))
        raise
    finally:
        metadata['output_sha256'] = {str(path.relative_to(output)): sha(path)
                                     for path in output.rglob('*') if path.is_file()}
        write_json(output / 'provenance.json', metadata)
    print(json.dumps({key: metadata[key] for key in ('validation', 'figures', 'pooled_summaries')}))


if __name__ == '__main__':
    main()
