#!/usr/bin/env python3
"""Draw the eight-vertex sampling witness after explicit nonperformance release.

Prepared source-only during timing. This script imports no native solver or
collector and reads no captured timing, work count or sampled graph fixture.
Its independent small-graph checks must run before the illustrative rendering.
"""
import argparse
from collections import deque
import csv
import hashlib
import json
import math
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parent.parent
NOTE = ROOT / 'benchmark/results/larger-hierarchy-2026-10-15/SAMPLING_MECHANISM.md'
N = 8


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Sets:
    def __init__(self, n):
        self.parent = list(range(n))

    def find(self, v):
        while self.parent[v] != v:
            v = self.parent[v]
        return v

    def join(self, u, v):
        a, b = self.find(u), self.find(v)
        if a == b:
            return False
        self.parent[b] = a
        return True

    def blocks(self):
        groups = {}
        for v in range(len(self.parent)):
            groups.setdefault(self.find(v), []).append(v)
        return sorted(groups.values())


def witness():
    # The note specifies these ten weights. Give remaining nonpath pairs
    # 11..28 in lexicographic endpoint order to complete its distinct ranks.
    weights = {(v, v + 1): w for v, w in enumerate((1, 5, 2, 7, 3, 6, 4))}
    weights.update({(0, 2): 8, (2, 4): 9, (4, 6): 10})
    next_weight = 11
    for u in range(N):
        for v in range(u + 1, N):
            if (u, v) not in weights:
                weights[u, v] = next_weight
                next_weight += 1
    edges = [dict(id=i, u=u, v=v, weight=weights[u, v])
             for i, (u, v) in enumerate(sorted(weights))]
    chosen = {(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (2, 4), (4, 6)}
    sample = [edge for edge in edges if (edge['u'], edge['v']) in chosen]
    require(len({edge['weight'] for edge in edges}) == len(edges), 'witness weights are not distinct')
    return edges, sample


def kruskal(edges):
    sets = Sets(N)
    forest = []
    for edge in sorted(edges, key=lambda e: e['weight']):
        if sets.join(edge['u'], edge['v']):
            forest.append(edge)
    return forest, sets.blocks()


def forest_path_maxima(forest, edges):
    adjacency = [[] for _ in range(N)]
    acyclic = Sets(N)
    for edge in forest:
        require(acyclic.join(edge['u'], edge['v']), 'query forest contains a cycle')
        for u, v in ((edge['u'], edge['v']), (edge['v'], edge['u'])):
            adjacency[u].append((v, edge['weight']))
    answers = {}
    for edge in edges:
        queue = deque([(edge['u'], None)])
        seen = {edge['u']}
        answer = None
        while queue:
            vertex, maximum = queue.popleft()
            if vertex == edge['v']:
                answer = maximum
                break
            for child, weight in adjacency[vertex]:
                if child not in seen:
                    seen.add(child)
                    queue.append((child, weight if maximum is None else max(maximum, weight)))
        answers[edge['id']] = answer
    return answers


def boruvka(edges):
    """Simultaneous component minima on original records, with no deduplication."""
    sets, trace = Sets(N), []
    while True:
        crossing = [edge for edge in edges if sets.find(edge['u']) != sets.find(edge['v'])]
        if not crossing:
            break
        cheapest = {}
        before = sets.blocks()
        for edge in crossing:
            for vertex in (edge['u'], edge['v']):
                component = sets.find(vertex)
                if component not in cheapest or edge['weight'] < cheapest[component]['weight']:
                    cheapest[component] = edge
        selected = {edge['id']: edge for edge in cheapest.values()}
        accepted = []
        for edge in sorted(selected.values(), key=lambda e: e['weight']):
            if sets.join(edge['u'], edge['v']):
                accepted.append(edge['id'])
        require(accepted, 'Boruvka round makes no progress')
        trace.append({'round': len(trace) + 1, 'input_edges': len(crossing),
                      'components_before': before, 'selected_ids': sorted(selected),
                      'accepted_ids': accepted, 'components_after': sets.blocks()})
    return trace, sets.blocks()


def checked_witness():
    edges, sample = witness()
    mst, components = kruskal(edges)
    forest, sample_components = kruskal(sample)
    require(len(components) == len(sample_components) == 1, 'witness or sample disconnected')
    ids = lambda graph: {edge['id'] for edge in graph}
    require(ids(forest) == ids(sample), 'chosen sample is not its own spanning tree')
    answers = forest_path_maxima(forest, edges)
    light = [edge for edge in edges if answers[edge['id']] is None or edge['weight'] <= answers[edge['id']]]
    heavy = [edge for edge in edges if edge not in light]
    filtered_mst, filtered_components = kruskal(light)
    require(ids(mst) == ids(filtered_mst) and len(filtered_components) == 1,
            'filtering did not preserve the exact MST')
    require(ids(mst) <= ids(light) and not (ids(mst) & ids(heavy)), 'a true MST edge was filtered')
    full_rounds, _ = boruvka(edges)
    sample_rounds, _ = boruvka(sample)
    light_rounds, _ = boruvka(light)
    for graph, rounds in ((edges, full_rounds), (sample, sample_rounds), (light, light_rounds)):
        selected = {edge for row in rounds for edge in row['accepted_ids']}
        optimum, _ = kruskal(graph)
        require(selected == ids(optimum), 'independent Boruvka and Kruskal forests differ')
    non_mst = ids(forest) - ids(mst)
    # Expected witness properties are checked, never substituted for computed labels.
    require((len(edges), len(forest), len(light), len(heavy), len(non_mst)) == (28, 7, 10, 18, 3),
            'constructed witness does not have its declared edge counts')
    require((len(full_rounds), len(sample_rounds), len(light_rounds)) == (3, 2, 3),
            'constructed witness does not have its declared round disruption')
    report = {'validation': 'pass', 'vertices': N, 'full_edges': len(edges),
              'sample_edges': len(sample), 'sample_forest_edges': len(forest),
              'non_mst_sample_forest_edges': len(non_mst), 'light_edges': len(light), 'heavy_edges': len(heavy),
              'true_mst_ids': sorted(ids(mst)), 'sample_forest_ids': sorted(ids(forest)),
              'light_ids': sorted(ids(light)), 'heavy_ids': sorted(ids(heavy)),
              'true_mst_weight': sum(e['weight'] for e in mst),
              'sample_forest_weight': sum(e['weight'] for e in forest),
              'boruvka_rounds': {'full': full_rounds, 'sample': sample_rounds, 'light': light_rounds},
              'path_maxima': answers, 'native_executed': False,
              'scope': 'Independent tiny-graph Kruskal, forest BFS and simultaneous-minimum Boruvka checks; not a C++ correctness or performance result.'}
    return edges, sample, light, report


def render(edges, sample, light, checks, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                         'svg.fonttype': 'none', 'pdf.fonttype': 42})
    figure, axes = plt.subplots(1, 3, figsize=(17, 7.4))
    positions = {v: (math.cos(math.pi / 2 - 2 * math.pi * v / N),
                     math.sin(math.pi / 2 - 2 * math.pi * v / N)) for v in range(N)}
    mst = set(checks['true_mst_ids'])
    forest = set(checks['sample_forest_ids'])
    colors = {'mst': '#1768ac', 'sample_chord': '#d97816', 'other': '#a9afb8'}
    titles = (
        f"Parent graph · {len(edges)} edges\nBorůvka: {len(checks['boruvka_rounds']['full'])} rounds",
        f"Chosen sample H = F · {len(sample)} edges\n{checks['non_mst_sample_forest_edges']} non-MST chords · Borůvka: {len(checks['boruvka_rounds']['sample'])} rounds",
        f"F-light parent · {len(light)} edges\n{checks['heavy_edges']} removed · Borůvka: {len(checks['boruvka_rounds']['light'])} rounds",
    )
    coverage = []
    for panel, (axis, graph, title) in enumerate(zip(axes, (edges, sample, light), titles)):
        drawn = []
        for edge in sorted(graph, key=lambda e: (e['id'] in mst or e['id'] in forest, e['weight'])):
            category = 'mst' if edge['id'] in mst else 'sample_chord' if edge['id'] in forest else 'other'
            a, b = positions[edge['u']], positions[edge['v']]
            important = category != 'other'
            axis.plot((a[0], b[0]), (a[1], b[1]), color=colors[category],
                      linewidth=2.7 if important else .8, alpha=1 if important else .48,
                      linestyle='--' if category == 'sample_chord' else '-', zorder=2 if important else 1)
            if important:
                axis.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, str(edge['weight']),
                          ha='center', va='center', fontsize=10, color=colors[category], zorder=4,
                          bbox=dict(boxstyle='round,pad=.13', fc='white', ec='none', alpha=.95))
            drawn.append(edge['id'])
        for vertex, (x, y) in positions.items():
            axis.scatter([x], [y], s=330, facecolor='white', edgecolor='#303640', linewidth=1.5, zorder=5)
            axis.text(x, y, str(vertex), ha='center', va='center', zorder=6, fontsize=11)
        axis.set_aspect('equal')
        axis.set_xlim(-1.18, 1.18); axis.set_ylim(-1.18, 1.18); axis.axis('off')
        axis.set_title(title, fontsize=12, pad=16)
        require(set(drawn) == {edge['id'] for edge in graph} and len(drawn) == len(graph), 'unplotted/duplicated witness edge')
        coverage.append({'panel': panel, 'vertices_drawn': N, 'edge_ids_drawn': drawn,
                         'weight_labels': [edge['weight'] for edge in graph if edge['id'] in (mst | forest)]})
    handles = [Line2D([], [], color=colors['mst'], linewidth=2.7, label='Edges of the original unique MST'),
               Line2D([], [], color=colors['sample_chord'], linewidth=2.7, linestyle='--', label='Sampled forest chords outside that MST'),
               Line2D([], [], color=colors['other'], linewidth=1, label='Other high chords')]
    figure.legend(handles=handles, loc='lower center', bbox_to_anchor=(.5, .14), ncol=3, frameon=False)
    figure.suptitle('ILLUSTRATIVE WITNESS · a sampled tree can differ from the true MST and still filter safely', fontsize=16, y=.98)
    heavy_weights = [edge['weight'] for edge in edges if edge['id'] in set(checks['heavy_ids'])]
    figure.text(.5, .025,
        f'All edges are drawn. Important edges carry their distinct weights; other chord weights are {min(heavy_weights)}–{max(heavy_weights)}. Vertex positions are illustrative.\n'
        'An edge is removed only when its sampled-forest path has a strictly smaller maximum weight. Every original MST edge survives.\n'
        'This is a chosen eight-vertex sample, not a timing input, typical random draw or performance prediction. Counts and round traces are independently checked.',
        ha='center', fontsize=9, linespacing=1.6)
    figure.tight_layout(rect=(0, .25, 1, .91), w_pad=2)
    paths = []
    for extension in ('png', 'svg', 'pdf'):
        path = output / ('sampling_witness.' + extension)
        figure.savefig(path, dpi=180, bbox_inches='tight'); paths.append(path)
    plt.close(figure)
    return paths, positions, coverage, matplotlib.__version__


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--released', action='store_true')
    args = parser.parse_args()
    require(args.released, 'tiny-graph checks and rendering require root nonperformance release')
    output = args.output.resolve(); require(not output.exists(), 'refusing to overwrite witness attempt')
    sources = {str(path): sha(path) for path in (Path(__file__).resolve(), NOTE)}
    edges, sample, light, checks = checked_witness()
    output.mkdir(parents=True)
    records = [{**edge, 'in_original_mst': edge['id'] in checks['true_mst_ids'],
                'sampled': edge['id'] in checks['sample_forest_ids'],
                'forest_path_maximum': checks['path_maxima'][edge['id']],
                'f_light': edge['id'] in checks['light_ids']} for edge in edges]
    edge_path = output / 'witness_edges.csv'
    with edge_path.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0])); writer.writeheader(); writer.writerows(records)
    check_path = output / 'independent_checks.json'
    with check_path.open('x') as stream:
        json.dump(checks, stream, indent=2); stream.write('\n')
    paths, positions, coverage, version = render(edges, sample, light, checks, output)
    for path, digest in sources.items(): require(sha(path) == digest, 'witness source changed while rendering')
    paths.extend((edge_path, check_path))
    with (output / 'provenance.json').open('x') as stream:
        json.dump({'schema': 'illustrative_sampling_witness_figure_v1', 'validation': 'pass',
                   'source_sha256': sources, 'output_sha256': {p.name: sha(p) for p in paths},
                   'measured_input_files': [], 'native_executed': False, 'positions': positions,
                   'coverage': coverage, 'python_executable': sys.executable, 'python_version': platform.python_version(),
                   'matplotlib_version': version, 'argv': sys.argv,
                   'visual_review': 'pending: inspect all three panels before publication'}, stream, indent=2)
        stream.write('\n')
    (output / 'README.md').write_text('# Illustrative sampling witness\n\n'
        f"The independent tiny-graph checks found {len(edges)} parent edges, {len(sample)} sample-tree edges "
        f"({checks['non_mst_sample_forest_edges']} outside the original MST), {len(light)} light survivors "
        f"and {checks['heavy_edges']} heavy removals. Full/sample/filtered Borůvka round counts are "
        f"{len(checks['boruvka_rounds']['full'])}/{len(checks['boruvka_rounds']['sample'])}/{len(checks['boruvka_rounds']['light'])}. "
        'The exact original MST is preserved. Complete edge weights, memberships, forest-path maxima and round partitions are archived. '
        'This selected illustration is neither a measured benchmark nor a typicality claim. Visual QA is pending; PNG has SVG/PDF counterparts.\n')
    print(json.dumps({'validation': 'pass', 'panels': len(coverage), 'output': str(output), 'visual_review': 'pending'}))


if __name__ == '__main__':
    main()
