#!/usr/bin/env python3
"""Validate and fit the added Google Benchmark families, preserving every model.

Uses the existing arithmetic-mean, finite-window fitting routines in an isolated
process. This is a timing diagnostic, never an asymptotic proof. Work counters
come from the separately executed fixed common-family matrix (four sizes).
"""
import argparse
import collections
import json
import math
from pathlib import Path
import re
import statistics

import analyze_complexity as fit
import analyze_common as common

FAMILIES = ('unbalanced_bipartite_16', 'ring_cliques_16', 'grid3d_distance',
            'leaf_core_90', 'regular_8')
SIZES = tuple(1024 * 2**i for i in range(9))


def configure():
    # This adapter runs in its own process; original analyzer defaults/files
    # remain unchanged, including the original benchmark's three-family mode.
    fit.TIMING_FAMILIES = FAMILIES
    fit.TIMING_SIZES = SIZES
    fit.NAME_PATTERN = re.compile(
        r'(KKT|Kruskal)/(' + '|'.join(FAMILIES) +
        r')/graph_(\d+)/(\d+)/iterations:3/repeats:3/manual_time')
    dimensions = common.dimensions(SIZES)
    fit.edge_count = lambda family, n: dimensions[f'{family}_n{n}']['m']


def validate_builtins(rows):
    expected = {(a, f, str(g), kind) for a in fit.ALGORITHMS for f in FAMILIES
                for g in fit.GRAPH_SEEDS for kind in ('BigO', 'RMS')}
    seen = set()
    for row in rows:
        match = re.fullmatch(r'(KKT|Kruskal)/(' + '|'.join(FAMILIES) +
            r')/graph_(\d+)/iterations:3/repeats:3/manual_time_(BigO|RMS)', row['name'])
        if not match or match.groups() not in expected or match.groups() in seen:
            raise ValueError('missing, duplicate, or unexpected built-in fit')
        seen.add(match.groups())
        for key in ('real_coefficient', 'cpu_coefficient', 'rms'):
            if key in row and (not math.isfinite(row[key]) or row[key] < 0):
                raise ValueError('invalid built-in fit value')
    if seen != expected:
        raise ValueError('incomplete built-in fit matrix')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timing-json', required=True, type=Path)
    parser.add_argument('--work-csv', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    configure()
    raw, builtin = fit.load_timing(args.timing_json)
    validate_builtins(builtin)
    # Full 52-case work matrix is required even though timing fits cover five
    # preselected mechanisms, so a favorable subset cannot silently replace it.
    work_rows = common.load_work(args.work_csv, common.MAIN_SIZES)
    work = []
    for family in FAMILIES:
        for n in common.MAIN_SIZES:
            rows = [r for r in work_rows.values() if r['family'] == family and r['n'] == n]
            assert len(rows) == 9
            m = fit.edge_count(family, n)
            work.append({'case_id': f'{family}_n{n}', 'family': family, 'n': n, 'm': m,
                         'input_size': n + m,
                         'mean_total_work_proxy': statistics.fmean(r['total_work_proxy'] for r in rows)})
    timing, graphs = fit.aggregate_timing(raw, work)
    exponents, models = fit.analyze_models(fit.series_from_summaries(work, timing))
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    for name, rows in [('timing_repetitions', raw), ('timing_summary', timing),
                       ('graph_timing_summary', graphs), ('work_summary', work),
                       ('effective_exponents', exponents), ('model_fits', models)]:
        fit.write_csv(out / (name + '.csv'), rows)
    (out / 'builtin_complexity.json').write_text(json.dumps(builtin, indent=2) + '\n')

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 10, 'svg.fonttype': 'none', 'pdf.fonttype': 42})
    fig, axes = plt.subplots(2, 3, figsize=(12, 7.2), constrained_layout=True)
    for ax, family in zip(axes.flat, FAMILIES):
        for algo, color in [('KKT', '#137c83'), ('Kruskal', '#d26a28')]:
            selected = [r for r in timing if r['family'] == family and r['algorithm'] == algo]
            x = [r['n'] for r in selected]
            y = [r['ns_per_input'] for r in selected]
            ax.plot(x, y, '-o', color=color, label=algo, ms=3)
            ax.fill_between(x, [r['graph_min_time_ns']/r['input_size'] for r in selected],
                            [r['graph_max_time_ns']/r['input_size'] for r in selected],
                            color=color, alpha=.14, linewidth=0)
        ax.set_xscale('log', base=2)
        ax.set_title(common.NAMES[family])
        ax.set_xlabel('Vertices n')
        ax.set_ylabel('Manual time / (n + m), ns')
        ax.grid(alpha=.18)
    axes.flat[0].legend(frameon=False)
    axes.flat[-1].axis('off')
    axes.flat[-1].text(0, .88, 'A flat line supports linear timing\nover this finite range.\n\nShading: range of three graph means.\nNot a confidence interval.\n\nGoogle Benchmark profile;\nseparate from paired Make timings.',
                       va='top', linespacing=1.7)
    for ext in ('png', 'svg', 'pdf'):
        fig.savefig(out / ('common_normalized_timing.'+ext), dpi=180, bbox_inches='tight')
    plt.close(fig)
    lines = ['# Added Google Benchmark complexity diagnostics', '',
             f'Validated {len(raw)} raw records, {len(raw)*3} timed calls, and {len(builtin)} built-in fit rows. '
             'All five families, nine powers of two from 1,024 to 262,144 vertices, two algorithms, '
             'three graph seeds and three repetition batches are present. Each batch cycles KKT seeds 0, 1, 7.', '',
             'Input size is N=n+m. Fits use balanced arithmetic means; the paired comparison campaigns use '
             'a different aggregation and native build profile. Neither type of fit proves Big-O complexity.', '',
             '| Family | Algorithm | Full p | Upper-half p | ns/N first | ns/N last | Built-in models across graph seeds |',
             '|---|---|---:|---:|---:|---:|---|']
    for family in FAMILIES:
        for algo in fit.ALGORITHMS:
            def power(window):
                return next(r['power_exponent'] for r in models if r['family']==family and r['algorithm']==algo
                    and r['dataset']=='manual_time_ns' and r['window']==window and r['model']=='N_power_p')
            selected = [r for r in timing if r['family']==family and r['algorithm']==algo]
            labels = [r['big_o'] for r in builtin if r.get('big_o') and r['name'].startswith(f'{algo}/{family}/')]
            lines.append(f'| {common.NAMES[family]} | {algo} | {power("full"):.3f} | {power("upper_half"):.3f} | '
                         f'{selected[0]["ns_per_input"]:.3f} | {selected[-1]["ns_per_input"]:.3f} | {", ".join(labels)} |')
    lines += ['', '![Normalized manual time](common_normalized_timing.png)', '',
              'The built-in model is chosen from CPU time in Google Benchmark 1.5.2, then manual time is fitted '
              'to that same model. All model coefficients and RMS records remain in builtin_complexity.json. '
              'Independent fits retain N, N log N, N (log N)^2, N^2 and a free power, full and upper-half windows, '
              'with original-unit and relative residuals. The exponent p is from log-space regression.', '',
              'Upper-half timing fits use the largest five of nine sizes. Work fits use the four fixed main sizes '
              'and the largest two for their upper half: the latter are only a two-point slope. Work counters omit '
              'allocator internals, hash collisions, deallocation and cache behavior. Registration order is fixed; '
              'there is no paired/randomized algorithm schedule in this separate diagnostic.']
    (out/'report.md').write_text('\n'.join(lines)+'\n')
    print(f'Validated {len(raw)} timing records and {len(work_rows)} work observations')

if __name__ == '__main__':
    main()
