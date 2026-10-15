#!/usr/bin/env python3
"""Render an analytic hierarchy-retention expectation after explicit release.

No timing capture, work-counter file, native binary or collector is read.
The source and the deferred enumeration checks were prepared during timing;
imports, checks and rendering must wait for root's nonperformance release.
"""
import argparse
import csv
from fractions import Fraction
import hashlib
from itertools import combinations
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parent.parent
STUDY = ROOT / 'benchmark/results/larger-hierarchy-2026-10-15'
SIZES = (65536, 1048576, 4194304)
DENSITY = 32
SOURCE_PATHS = (
    Path(__file__).resolve(),
    STUDY / 'PROTOCOL.md', STUDY / 'manifest.csv', STUDY / 'HIERARCHY_EXPECTATION.md',
    ROOT / 'benchmark/results/density-search-2026-10-15/HIERARCHY_RETENTION.md',
    ROOT / 'benchmark/results/edge-view-2026-10-15/THEORY.md',
    ROOT / 'benchmark/core_attachment_fixtures.hpp',
    ROOT / 'benchmark/continuation_fixtures.hpp',
    ROOT / 'kkt/experimental_multigraph_contraction.hpp',
    ROOT / 'benchmark/retention_boruvka.hpp',
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parameters(q, chords):
    require(type(q) is int and q >= 4 and q & (q - 1) == 0, 'q must be a power of two at least four')
    population = (q - 1) * (q - 2) // 2
    require(type(chords) is int and 0 <= chords <= population, 'invalid nonpath chord count')
    return q.bit_length() - 1, population


def internal_pairs(q, block_size):
    require(type(block_size) is int and 1 <= block_size <= q and block_size & (block_size - 1) == 0
            and q % block_size == 0, 'invalid aligned block size')
    # All internal pairs, minus the internal path pairs excluded from the population.
    return (q // block_size) * (block_size * (block_size - 1) // 2) - (q - q // block_size)


def expected_core_input(q, chords, block_size):
    _, population = parameters(q, chords)
    internal = internal_pairs(q, block_size)
    require(0 <= internal <= population, 'invalid internal-pair count')
    return Fraction(q // block_size - 1) + Fraction(chords * (population - internal), population)


def expected_total_input(q, chords):
    levels, _ = parameters(q, chords)
    original_m = 4 * q - 1 + chords
    correction = Fraction(3 * q * (levels - 2) + 6, (q - 1) * (q - 2))
    return Fraction(original_m + 2 * q - 2 - levels) + chords * (levels - 1 + correction)


def enumeration_checks():
    """Independent small-domain counts, not a second spelling of the formula.

    Enumerate actual eligible unordered vertex pairs. For q=4 and q=8,
    enumerate every subset at several fixed chord counts and directly count
    crossing pairs in every aligned partition, then average those integer
    volumes. This is a finite combinatorial check, not a generator or solver run.
    """
    pair_cases = 0
    for q in (4, 8, 16, 32):
        path = [(u, u + 1) for u in range(q - 1)]
        eligible = [(u, v) for u in range(q) for v in range(u + 1, q) if v != u + 1]
        levels, population = parameters(q, 0)
        require(len(eligible) == population, 'enumerated chord population differs')
        for k in range(levels + 1):
            b = 1 << k
            observed = sum(u // b == v // b for u, v in eligible)
            require(observed == internal_pairs(q, b), 'enumerated internal nonpath pairs differ')
            require(sum(u // b != v // b for u, v in path) == q // b - 1,
                    'enumerated retained path count differs')
            pair_cases += 1
        require(internal_pairs(q, 1) == internal_pairs(q, 2) == 0 and
                internal_pairs(q, q) == population, 'boundary pair counts differ')

    subset_cases = subsets = 0
    for q in (4, 8):
        path = [(u, u + 1) for u in range(q - 1)]
        eligible = [(u, v) for u in range(q) for v in range(u + 1, q) if v != u + 1]
        levels, population = parameters(q, 0)
        for chord_count in sorted({0, 1, 2, 3, population - 1, population}):
            volume_sum = 0
            per_round_sum = [0] * levels
            count = 0
            for selected in combinations(eligible, chord_count):
                core_edges = path + list(selected)
                original_m = 3 * q + len(core_edges)
                round_inputs = [sum(u // (1 << k) != v // (1 << k) for u, v in core_edges)
                                for k in range(levels)]
                volume_sum += original_m + sum(round_inputs)
                per_round_sum = [a + b for a, b in zip(per_round_sum, round_inputs)]
                count += 1
            require(count > 0, 'empty subset enumeration')
            require(Fraction(volume_sum, count) == expected_total_input(q, chord_count),
                    'exhaustive subset mean total volume differs')
            for k, total in enumerate(per_round_sum):
                require(Fraction(total, count) == expected_core_input(q, chord_count, 1 << k),
                        'exhaustive subset mean round volume differs')
            subset_cases += 1
            subsets += count
    return {'validation': 'pass', 'enumerated_pair_partitions': pair_cases,
            'fixed_chord_count_ensembles': subset_cases, 'enumerated_chord_subsets': subsets,
            'native_solver_or_generator_executed': False}


def declared_manifest():
    with (STUDY / 'manifest.csv').open(newline='') as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == ['family', 'n', 'density', 'intrusion_per_mille'], 'wrong manifest header')
        rows = list(reader)
    expected = [{'family': family, 'n': str(n), 'density': '32', 'intrusion_per_mille': '0'}
                for n in SIZES for family in ('leaf_hierarchy4', 'leaf_shuffled4')]
    require(rows == expected, 'manifest differs from the six declared cases')
    return rows


def theoretical_rows():
    rows = []
    for n in SIZES:
        m, q = DENSITY * n, n // 4
        chords = m - n + 1
        levels, population = parameters(q, chords)
        require(n <= 1 << 22 and m <= 134217728, 'outside the existing generator domain')
        cumulative = Fraction(0)
        for full_round in range(1, levels + 2):
            star = full_round == 1
            b = None if star else 1 << (full_round - 2)
            local = 3 * q if star else 0
            path = q - 1 if star else q // b - 1
            retained_chords = Fraction(chords) if star else Fraction(chords * (population - internal_pairs(q, b)), population)
            edges = local + path + retained_chords
            cumulative += edges
            rows.append({'n': n, 'm': m, 'q': q, 'core_rounds': levels,
                         'full_contraction_round': full_round, 'stage': 'star' if star else 'core',
                         'core_block_size': b, 'local_edges': local, 'path_edges': path,
                         'eligible_nonpath_pairs': population, 'chord_count': chords,
                         'expected_chord_edges': retained_chords, 'expected_input_edges': edges,
                         'expected_input_over_m': edges / m,
                         'expected_cumulative_input_edges': cumulative,
                         'expected_cumulative_input_over_m': cumulative / m})
        require(cumulative == expected_total_input(q, chords), 'round sum differs from closed total')
        require(expected_core_input(q, chords, q) == 0, 'final quotient is not empty')
    require(len(rows) == 55, 'missing declared input round')
    return rows


def exported(rows):
    result = []
    for row in rows:
        item = {}
        for key, value in row.items():
            if isinstance(value, Fraction):
                item[key] = float(value)
                item[key + '_numerator'] = value.numerator
                item[key + '_denominator'] = value.denominator
            else:
                item[key] = value
        result.append(item)
    return result


def render(rows, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'svg.fonttype': 'none', 'pdf.fonttype': 42})
    figure, axes = plt.subplots(1, 2, figsize=(15.5, 7.5))
    colors, markers = ('#1768ac', '#d97816', '#25854b'), ('o', 's', '^')
    fields = ('expected_input_over_m', 'expected_cumulative_input_over_m')
    coverage = []
    for index, n in enumerate(SIZES):
        selected = [row for row in rows if row['n'] == n]
        rounds = [row['full_contraction_round'] for row in selected]
        require(rounds == list(range(1, selected[0]['core_rounds'] + 2)), 'nonconsecutive theoretical rounds')
        for axis, field in zip(axes, fields):
            axis.plot(rounds, [float(row[field]) for row in selected], color=colors[index],
                      marker=markers[index], markersize=4.7, linewidth=1.8, alpha=.85,
                      label=f'n = {n:,} ({len(rounds)} full rounds)')
            coverage.append({'panel': field, 'n': n, 'rounds': rounds,
                             'points': len(rounds), 'extrapolated_rounds': 0})
    titles = ('Expected input edges in each contraction', 'Expected accumulated contraction input')
    labels = ('Expected input edges / original m', 'Expected cumulative input edges / original m')
    for axis, title, label in zip(axes, titles, labels):
        axis.set_title(title, loc='left', fontsize=13)
        axis.set_xlabel('Full contraction round (round 1 collapses the stars)')
        axis.set_ylabel(label)
        axis.set_xticks(range(1, 22, 2))
        axis.set_xlim(.5, 21.5)
        axis.grid(alpha=.18)
    axes[0].set_ylim(0, 1.05)
    axes[1].set_ylim(0, 1.07 * max(float(row[fields[1]]) for row in rows))
    for axis, field in zip(axes, fields):
        lo, hi = axis.get_ylim()
        require(all(lo <= float(row[field]) <= hi for row in rows), 'theoretical point outside plot bounds')
    figure.suptitle('THEORETICAL EXPECTATION · hierarchy-ordered leaf cores\n'
                    'Uniform nonpath chords; m/n = 32; no measured timing or work data', fontsize=16, y=.98)
    handles, labels = axes[0].get_legend_handles_labels()
    require(len(handles) == len(labels) == 3, 'missing size legend')
    figure.legend(handles, labels, loc='lower center', bbox_to_anchor=(.5, .14), ncol=3, frameon=False)
    figure.text(.5, .025,
        'Round 1 reads m edges. Core-round inputs use aligned blocks b = 1, 2, 4, …, q/2; the final contraction leaves an empty quotient.\n'
        'Markers include every defined input round; lines only connect that discrete expectation. Curves stop at their own final contraction.\n'
        'These are ensemble expectations of one input-edge count per call, not measured scans, CPU work, memory or runtime predictions.',
        ha='center', fontsize=9, linespacing=1.6)
    figure.tight_layout(rect=(0, .27, 1, .89), w_pad=3)
    paths = []
    for extension in ('png', 'svg', 'pdf'):
        path = output / ('hierarchy_expectation.' + extension)
        figure.savefig(path, dpi=180, bbox_inches='tight')
        paths.append(path)
    plt.close(figure)
    return paths, coverage, matplotlib.__version__


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--released', action='store_true')
    args = parser.parse_args()
    require(args.released, 'theory checks and rendering require root nonperformance release')
    output = args.output.resolve()
    require(not output.exists(), 'refusing to overwrite a theory-figure attempt')
    sources = {str(path): sha(path) for path in SOURCE_PATHS}
    manifest = declared_manifest()
    checks = enumeration_checks()
    rows = theoretical_rows()
    output.mkdir(parents=True)
    values_path = output / 'theoretical_values.csv'
    values = exported(rows)
    with values_path.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)
    with (output / 'enumeration_checks.json').open('x') as stream:
        json.dump(checks, stream, indent=2)
        stream.write('\n')
    paths, coverage, version = render(rows, output)
    require(len(coverage) == 6 and sum(point['points'] for point in coverage) == 110, 'missing theory plot coverage')
    for path, digest in sources.items():
        require(sha(path) == digest, 'source changed during theory rendering')
    paths.extend((values_path, output / 'enumeration_checks.json'))
    with (output / 'provenance.json').open('x') as stream:
        json.dump({'schema': 'analytic_hierarchy_retention_figure_v1', 'validation': 'pass',
                   'theoretical_expectation_only': True, 'measured_input_files': [],
                   'manifest': manifest, 'modeled_family': 'leaf_hierarchy4',
                   'unmodeled_weight_twin': 'leaf_shuffled4', 'rows': len(rows),
                   'source_sha256': sources, 'output_sha256': {p.name: sha(p) for p in paths},
                   'python_version': platform.python_version(), 'python_executable': sys.executable,
                   'matplotlib_version': version, 'argv': sys.argv, 'coverage': coverage,
                   'uniform_model': 'Uniform fixed-C subset of eligible distinct nonpath core pairs.',
                   'finite_generator_domain_only': True,
                   'visual_review': 'pending: inspect the two-panel PNG before publication'}, stream, indent=2)
        stream.write('\n')
    lines = ['# Analytic hierarchy retention', '',
             '**Theoretical expectation, not observed work or timing.** All three declared hierarchy sizes at d=32 are included; '
             'the shuffled twin has no fixed-partition prediction here. Every defined input round is plotted.', '',
             '| n | q | Core rounds | Full calls | Exact-model expected total input / m |',
             '|---:|---:|---:|---:|---:|']
    for n in SIZES:
        selected = [row for row in rows if row['n'] == n]
        last = selected[-1]
        lines.append(f"| {n:,} | {last['q']:,} | {last['core_rounds']} | {len(selected)} | {float(last['expected_cumulative_input_over_m']):.8f} |")
    lines.extend(['', 'The CSV retains exact rational numerators and denominators for every expectation. '
                  'Independent finite-pair and exhaustive small-subset enumeration checks passed before rendering. '
                  'This checks the formula on small domains, not the native solver, generator RNG, measured memory or hardware. '
                  'Visual review is pending; PNG has SVG/PDF counterparts.', ''])
    (output / 'README.md').write_text('\n'.join(lines))
    print(json.dumps({'validation': 'pass', 'theoretical_rows': len(rows), 'panels': 2,
                      'enumeration_checks': checks, 'output': str(output), 'visual_review': 'pending'}))


if __name__ == '__main__':
    main()
