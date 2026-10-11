#!/usr/bin/env python3
"""Populate the report from retained, validated analysis tables.

This does not measure algorithms or infer ratios from rounded figure labels.
Run the strict common/complexity/ablation analyzers before this script.
"""
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / 'benchmark/results/common-2026-10-11'
NAMES = {
    'unbalanced_bipartite_16': 'Bipartite k=16',
    'unbalanced_bipartite_256': 'Bipartite k=256',
    'unbalanced_bipartite_sqrt': 'Bipartite k=⌊√n⌋',
    'leaf_core_50': '50% attached leaves', 'leaf_core_90': '90% attached leaves',
    'ring_cliques_16': 'Ring of cliques (16)',
    'grid2d_random': '2D grid, random', 'grid2d_distance': '2D grid, distance',
    'grid3d_random': '3D grid, random', 'grid3d_distance': '3D grid, distance',
    'regular_8': 'Degree-eight regular', 'hub': 'Hub control', 'random_4': 'Random4 control',
    'small_world': 'Small-world variant',
}
FAMILIES = list(NAMES)[:-1]
SIZES = [4096, 16384, 65536, 262144]
ALGORITHMS = {'kruskal': 'Kruskal', 'prim': 'Prim', 'boruvka': 'Borůvka'}


def read(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |',
                      '| ' + ' | '.join('---' for _ in headers) + ' |'] +
                     ['| ' + ' | '.join(str(x) for x in row) + ' |' for row in rows])


def main():
    summaries = {run: {(r['case_id'], r['algorithm']): r for r in
                      read(BASE / (run + '_analysis') / 'summary.csv')}
                 for run in ('primary', 'repeat')}
    comparisons = {run: {(r['case_id'], r['reference']): r for r in
                        read(BASE / (run + '_analysis') / 'comparisons.csv')
                        if r['algorithm'] == 'kkt'} for run in summaries}
    work = {r['case_id']: r for r in read(BASE / 'primary_analysis/work_summary.csv')}
    ablation = {(r['run'], r['case_id']): r for r in
                read(BASE / 'diagnostics/ablation_analysis/paired_summary.csv')}
    fits = read(BASE / 'diagnostics/complexity_analysis/model_fits.csv')

    def ratio(run, family, n, reference='kruskal'):
        return float(comparisons[run][f'{family}_n{n}', reference]['paired_runtime_ratio'])

    def fastest(run, family, n):
        case = f'{family}_n{n}'
        return min(ALGORITHMS, key=lambda a: float(summaries[run][case, a]['median_ms']))

    def ratio_cell(family, n):
        a, b = (fastest(run, family, n) for run in summaries)
        label = ALGORITHMS[a] if a == b else f'{ALGORITHMS[a]} / {ALGORITHMS[b]}'
        return f'{ratio("primary", family, n, a):.3f} / {ratio("repeat", family, n, b):.3f} ({label})'

    def appendix(families):
        return table(['Family', '4,096', '16,384', '65,536', '262,144'],
                     [[NAMES[f]] + [ratio_cell(f, n) for n in SIZES] for f in families])

    leaders = {}
    for run in summaries:
        leaders[run] = {f'{f}_n{n}' for f in FAMILIES for n in SIZES
                        if all(ratio(run, f, n, a) < 1 for a in ALGORITHMS)}
    robust = {case for case in leaders['primary'] & leaders['repeat']
              if all(float(comparisons[run][case, a]['graph_max_ratio']) < 1
                     for run in summaries for a in ALGORITHMS)}
    assert (len(leaders['primary']), len(leaders['repeat']), len(robust)) == (22, 21, 21)

    values = {}
    values['EXECUTIVE_RESULTS'] = '''**The answer in three parts.** The old implementation had two genuine superlinear bookkeeping/preprocessing defects, plus a recursive RNG-reset problem. Repairing them and reducing allocation/hash costs made KKT useful on several structured inputs. But the current wall-clock curves do **not** measure as uniformly linear, and larger random graphs still do not show general-purpose dominance.

In the new study, KKT leads Kruskal, Prim and the repository's ordinary Borůvka on **21 of 52 cases in both campaigns, on all three graph medians**. The strongest new family has a small bipartite side: at 262,144 vertices, k=16 takes 0.463 / 0.475 times Kruskal's time. Leaf-rich cores produce smaller gains; all tested meshes lose to Kruskal.

The decisive qualification is the continuation experiment: simply repeating KKT's own compacting Borůvka step beats KKT in **18 of 20 cases in both runs**. The only repeated KKT median lead is about 1% and does not hold across every graph. These experiments establish practical wins for the current implementation against the original baselines; they do not establish that randomized sampling is the source of those wins.'''

    values['HISTORICAL_TABLES'] = table(
        ['Original repair example', 'Original KKT', 'Repaired KKT', 'Matched speedup'],
        [['n=1,000; m=400,000', '16.52 ms', '5.07 ms', '3.28×'],
         ['n=4,096; m=16,384', '3.38 ms', '1.35 ms', '2.48×'],
         ['n=4,096; m=131,072', '17.58 ms', '5.18 ms', '3.32×'],
         ['n=4,096; m=524,288', '62.66 ms', '13.99 ms', '4.54×'],
         ['n=16,384; m=524,288', '131.36 ms', '42.34 ms', '3.12×']])

    fit_families = ['unbalanced_bipartite_16', 'ring_cliques_16', 'grid3d_distance',
                    'leaf_core_90', 'regular_8']
    fit_rows = []
    for f in fit_families:
        powers = [next(float(r['power_exponent']) for r in fits
                       if r['dataset'] == 'manual_time_ns' and r['algorithm'] == 'KKT'
                       and r['family'] == f and r['window'] == w and r['model'] == 'N_power_p')
                  for w in ('full', 'upper_half')]
        first, last = (work[f'{f}_n{n}'] for n in (4096, 262144))
        work_n = lambda r: float(r['total_work_proxy_mean']) / (int(r['n']) + int(r['m']))
        fit_rows.append([NAMES[f], f'{powers[0]:.3f}', f'{powers[1]:.3f}',
                         f'{work_n(first):.2f} → {work_n(last):.2f}',
                         'N² (3/3)' if f == 'ring_cliques_16' else 'N log N (3/3)'])
    values['NEW_COMPLEXITY_TABLE'] = '**New final-source diagnostics:**\n\n' + table(
        ['Family', 'KKT full p', 'Upper p', 'Work/N, first → last', 'Built-in KKT label'], fit_rows)
    values['COMPLEXITY_INTERPRETATION'] = '''All five new KKT timing curves rise overall in time per represented input. Full-window exponents range from **1.113 to 1.185**; none receives the built-in N label. The clique case receives N² despite a free-power exponent of only 1.185. That is a particularly clear warning against reading the selected label as a mathematical classification.

The fixed-cover and clique work proxies are nearly flat per N (7.31→7.20 and 9.19→9.15) while their timings rise. Changing counted algorithmic work alone cannot explain those curves. Memory/allocator effects and uncounted operations are plausible contributors, but these runs do not profile them. The regular and leaf-core proxies also increase, showing that finite-size work mix matters.

This diagnostic is less controlled than a dedicated benchmark machine: the startup log records load averages 18.42, 16.06 and 14.13. Those are system-load measures, not CPU-utilization percentages. Treat small fit differences and near-crossovers cautiously; retain the raw records instead of smoothing them away.'''

    values['NEW_OVERVIEW'] = '''KKT leads all three original comparators by case medians in **22/52 primary cases and 21/52 repeat cases**. The same 21 cases lead on every graph median in both campaigns: all 12 bipartite parameter/size cases, all four hub controls, the three smaller clique cases, and the two larger 90%-leaf cases.

KKT beats Prim and ordinary Borůvka by paired case medians in all 52 cases in both runs. Individual observations still lose: primary has 0/1 losses to Prim/Borůvka; repeat has 18/35, out of 1,872 matched pairs per comparator. Against Kruskal, there are 1,085 / 1,091 individual losses. The result is strong structural selectivity, not universal dominance.'''

    largest = []
    for f in FAMILIES:
        case = f'{f}_n262144'
        ms = [f'{float(summaries["primary"][case, a]["median_ms"]):.2f}'
              for a in ('kkt', 'kruskal', 'prim', 'boruvka')]
        largest.append([NAMES[f]] + ms + [ratio_cell(f, 262144)])
    values['LARGEST_TABLE'] = table(['Family', 'KKT ms', 'Kruskal', 'Prim', 'Borůvka',
                                     'Matched ratio: primary / repeat'], largest)
    values['LARGEST_INTERPRETATION'] = '''The fixed k=16 bipartite family is about **2.16× / 2.10× faster than Kruskal** by the reciprocal matched ratio. Growing the cover reduces the advantage. The 90%-leaf gain is only about 5–6%; the clique family has crossed from a smaller-size lead to a largest-size near-tie/loss. None of the four spatial variants beats Kruskal at this size.'''

    core_rows = []
    for f in FAMILIES[:3]:
        w = work[f'{f}_n262144']
        core_rows.append([NAMES[f], f'{ratio("primary", f, 262144):.3f} / {ratio("repeat", f, 262144):.3f}',
                          f'{100*float(w["root_after_two_edges_over_m_mean"]):.6f}%'])
    values['CORE_RESULTS'] = table(['At n=262,144', 'KKT/Kruskal: primary / repeat',
                                   'Root edges remaining after two rounds'], core_rows) + '''

The residual fractions are arithmetic means over the separate work runs. They make the mechanism concrete: the fixed 16-vertex cover almost eliminates the recursive problem, while the growing cover leaves a larger tail. They are not a measured timing decomposition.'''

    values['LEAF_RESULTS'] = '''At 262,144 vertices the 90%-attachment model takes **0.943 / 0.953× Kruskal**, while the 50% model takes **1.469 / 1.373×**. The smaller core is enough to change the practical ranking. At 16,384 vertices, however, the 90% case is only 0.987 / 1.005×: that apparent first-run crossover does not repeat.

After two root rounds, the 90% model retains about 23.59% of its original edges; the 50% model retains 60.24%. Neither resembles the star's immediate termination. This is why “many leaves” can help without guaranteeing that KKT wins.'''
    values['CLIQUE_RESULTS'] = '''KKT beats all original comparators on every graph median at 4,096, 16,384 and 65,536 vertices in both campaigns. At 262,144 it takes **1.006 / 1.051× Kruskal**, losing that lead. Root contraction is still excellent: only **0.975%** of original edges remain after two rounds at the largest size.

The counted work stays near 9.15 events per N, while time per N rises. Moreover, among verifier-input edges the mean retained-light fraction is about **99.69%** in the largest work case: filtering removes little from the already sparse tails. Excellent initial contraction therefore need not imply a benefit from the randomized continuation.'''
    values['SPATIAL_RESULTS'] = '''All four mesh variants lose to Kruskal at all four main sizes in both campaigns. At 262,144 vertices, paired KKT/Kruskal ratios range from **1.242 to 1.505** across variants and runs.

Distance ranking does not rescue KKT here. Matched distance/random KKT times are **1.100 / 1.140×** for the 2D meshes and **1.076 / 1.038×** for the 3D meshes at the largest size. KKT's relative ratio against Kruskal also worsens: 1.085 / 1.135× and 1.063 / 1.037×, respectively. These weight effects are specific to this paired mesh construction.

The work traces agree in direction: distance-weighted meshes leave more edges after two rounds—13.62% versus 10.75% in 2D, and 18.31% versus 15.72% in 3D. This provides a mechanism consistent with the timing; it does not separately measure the causal contribution of every later phase.'''
    values['NEGATIVE_RESULTS'] = '''At 262,144 vertices, degree-eight regular graphs take **1.712 / 1.815× Kruskal**, and random4 takes **1.647 / 1.681×**. Their two-round root residuals retain 75.88% and 75.42% of original edges. KKT then performs substantial verification and recursion after paying for the contractions.

Neither loss disappears because many edges are eventually classified as heavy. The retained-light fractions across verifier inputs are only about 3.65% and 3.31%, respectively: filtering is active and powerful, but its total cost still exceeds Kruskal's on these tests. Activity is not the same as net benefit.'''
    values['ABLATION_RESULTS'] = '''Compacting Borůvka has the lower paired case median in **19/20 primary cases and 18/20 repeat cases**, with the same 18 losses for KKT in both. KKT's only repeated lead is bipartite16 at 65,536 vertices: **0.989 / 0.991×**, with all three graph ratios below 1 in primary but a range crossing 1 in repeat. No case gives KKT a lead on every graph in both runs. Bipartite16 at 262,144 reverses from 1.017× to 0.988×; that is another near-tie, not a stable win.

At the largest common size, KKT costs **1.289 / 1.260×** repeated contraction on the distance 3D mesh, **1.214 / 1.207×** on random4, and **1.239 / 1.174×** on regular8. Even ring cliques favor continued contraction, 1.042 / 1.064×. Their 10–11 rounds process only about **1.083m total contraction-input edges**. Many rounds can be cheap when the edge volume vanishes quickly.'''
    values['SYNTHESIS'] = '''**The original implementation was not a faithful constant-factor realization of the intended local bounds.** Two audited defects could introduce superlinear work; the private RNG stream restored the intended recursive sampling discipline. The retained storage and lookup changes then reduced practical constants substantially.

**The current implementation is not empirically linear across these timing windows.** Stars behave nearly linearly, several structural work proxies are flat, and the source audit supports the expected O(n+m) design under its assumptions. But the new measured time exponents exceed one, and prior large random cases become less competitive. Those statements can all be true together.

**KKT is useful relative to these original baselines on particular structures, but its randomized continuation has not earned the credit.** Fixed small covers provide the strongest mechanism and gains. Leaf-rich cores and small dense communities help under specific parameters. The continuation experiment shows that much of this practical advantage is available to a simpler compacting Borůvka implementation.'''
    values['VALIDATION_RESULTS'] = '''The new study passed **222 fixture checks** and **all ten Bazel test targets**. Both full comparison campaigns validated all **14,976 timed outputs and 3,744 warmups**. The separate continuation campaigns validated **2,880 timed outputs and 720 warmups**. Work campaigns and traces remain untimed evidence; the new Google Benchmark sweep checked the outputs of its 2,430 timed calls.

The common analyzer's synthetic checks include six valid scenarios and 25 malformed-data rejections; the ablation analyzer has 43 malformed/math checks. Seven full graph exports pass independent contraction and heavy-edge oracles. The 18 overlapping control case/graph realizations match every common work field in the earlier archive. Counts and hashes are reconciled in [VALIDATION.md](../../benchmark/results/common-2026-10-11/VALIDATION.md).'''
    values['APPENDIX_CORE_TABLE'] = appendix(FAMILIES[:6])
    values['APPENDIX_SPATIAL_TABLE'] = appendix(FAMILIES[6:])

    ablation_rows = []
    for f in ['unbalanced_bipartite_16', 'leaf_core_90', 'ring_cliques_16',
              'grid3d_distance', 'regular_8', 'random_4', 'small_world']:
        for n in ([4096, 65536] if f == 'small_world' else [4096, 65536, 262144]):
            pair = [ablation[run, f'{f}_n{n}'] for run in ('primary', 'confirmation')]
            ablation_rows.append([NAMES[f], f'{n:,}'] +
                                 [f'{float(r["paired_runtime_ratio"]):.3f} [{float(r["graph_min_ratio"]):.3f}, {float(r["graph_max_ratio"]):.3f}]' for r in pair])
    values['ABLATION_APPENDIX'] = table(['Family', 'n', 'Primary ratio [graph range]',
                                       'Repeat ratio [graph range]'], ablation_rows)

    source = (HERE / 'REPORT.template.md').read_text()
    for key, value in values.items():
        marker = '{{' + key + '}}'
        assert source.count(marker) == 1, (key, source.count(marker))
        source = source.replace(marker, value)
    assert '{{' not in source
    (HERE / 'REPORT.md').write_text(source)
    print(f'Populated {len(values)} sections; {len(source.split()):,} approximate words.')


if __name__ == '__main__':
    main()
