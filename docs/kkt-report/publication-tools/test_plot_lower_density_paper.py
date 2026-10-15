#!/usr/bin/env python3
"""Synthetic publication gates, never a native/capture proof or render test.

Use the actual standalone prepare() and paper loader. Only the native evidence
collector and the style index helper are substituted with declared test doubles.
All temporary receipts and rows are synthetic. Rendering/page QA is separate.
"""
import argparse
import copy
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
STANDALONE_SOURCE = None
ALGORITHMS = ('kkt', 'compacting_boruvka', 'multigraph_boruvka', 'kruskal', 'prim', 'boruvka')


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {name: result}):
        spec.loader.exec_module(result)
    return result


def indexed(rows, fields):
    values = {tuple(row[key] for key in fields): row for row in rows}
    if len(values) != len(rows):
        raise ValueError('duplicate synthetic index')
    return values


class PaperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if STANDALONE_SOURCE is None:
            raise RuntimeError('explicit --standalone-source is required')
        cls.paper = module(HERE / 'plot_lower_density_paper.py', '_lower_paper_tests')

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='lower-density-paper-synthetic-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.capture = self.root / 'capture.json'
        self.capture.write_text('SYNTHETIC, NOT A NATIVE CAPTURE\n')
        self.source_path = self.root / 'plot_lower_density.py'
        self.source_path.write_bytes(STANDALONE_SOURCE.read_bytes())
        self.standalone = self.root / 'standalone'; self.standalone.mkdir()
        self.audit_path = self.root / 'audit.json'
        self.args = types.SimpleNamespace(capture=self.capture, source_plot=self.source_path,
                                         standalone=self.standalone, audit=self.audit_path)
        self.cases = {}
        for density, sizes in self.paper.SIZE_LADDERS.items():
            for n in sizes:
                for family in self.paper.FAMILIES:
                    case_id = f'{family}_d{density}_n{n}'
                    self.cases[case_id] = dict(case_id=case_id, family=family, n=n, m=n*density,
                                               density=density, intrusion_per_mille=0)
        self.tables = {name: [] for name in self.paper.TABLE_COUNTS}
        for ci, case in enumerate(self.cases.values()):
            for metric_index, metric in enumerate(('wall', 'cpu')):
                for name, names, field in (('comparisons', ALGORITHMS[1:], 'median_paired_ratio'),
                                            ('summary', ALGORITHMS, 'median_ns')):
                    for ai, algorithm in enumerate(names):
                        value = (.45 + ((ci+ai+metric_index) % 8) / 4) * (1e6 if name == 'summary' else 1)
                        identity = {**case, 'metric': metric,
                                    'algorithm' if name == 'summary' else 'competitor': algorithm}
                        self.tables[name].append({**identity, field: value, 'trial_min': value*.5,
                            'trial_max': value*1.5, 'graph_min': value*.9, 'graph_max': value*1.1, 'trials': 12})
                        for seed, factor in zip(self.paper.GRAPHS, (.9, 1.1)):
                            self.tables['graph_' + name].append({**identity, 'graph_seed': seed,
                                field: value*factor, 'trial_min': value*.7, 'trial_max': value*1.3, 'trials': 6})
        # Classification data are preserved, not calculated by this presentation test.
        for density, sizes in self.paper.SIZE_LADDERS.items():
            for family in self.paper.FAMILIES:
                for competitor in ALGORITHMS[1:]:
                    identity = dict(family=family, density=density, competitor=competitor)
                    self.tables['crossover_points'].extend({**identity, 'n': n, 'state': 'synthetic'} for n in sizes)
                    self.tables['crossover_brackets'].extend({**identity, 'lower_n': a, 'upper_n': b,
                        'strong_crossover': False} for a, b in itertools.combinations(sizes, 2))
                    self.tables['crossover_summary'].append({**identity, 'strong_crossover': False})
        self.tables['paired_ratios'] = [{'synthetic_index': i} for i in range(3600)]
        self.study = types.ModuleType('run_lower_density')
        self.study.require = self.paper.require
        self.study.GRAPH_SEEDS = self.paper.GRAPHS
        self.study.SAMPLING_SEED = 3407
        self.study.ALGORITHMS = ALGORITHMS
        self.study.SIZE_LADDERS = self.paper.SIZE_LADDERS
        self.study.EXPECTED_CASES = {(c['family'], c['n'], c['density'], 0) for c in self.cases.values()}
        self.study.TABLE_COUNTS = {key: count for key, count in self.paper.TABLE_COUNTS.items()
                                   if not key.startswith('crossover_')}
        self.study.load = lambda path: ({'captures': [{}]*60, 'flagged_calls': 3}, self.cases,
                                       [None]*2520, [], [], {})
        self.study.helpers = lambda: {}
        self.study.aggregate = lambda rows: copy.deepcopy({k: v for k, v in self.tables.items()
                                                          if not k.startswith('crossover_')})
        self.study.crossovers = lambda tables, cases: copy.deepcopy({k: v for k, v in self.tables.items()
                                                                   if k.startswith('crossover_')})
        self.style = types.ModuleType('plot_retention_control')
        self.style.LABELS = {name: name for name in ALGORITHMS}
        self.style.indexed = indexed
        self.proof = dict(schema='lower_density_figures_v1', validation='pass', capture=str(self.capture),
            input_sha256={str(self.capture): self.paper.sha(self.capture), str(self.source_path): self.paper.sha(self.source_path)},
            output_sha256={})
        self.audit = dict(schema='independent_lower_density_numerical_audit_v1', validation='pass',
            collector_imported=False, raw_native_children=60, checked_outputs=2520, timed_outputs=2160,
            warmup_outputs=360, matched_topology_twins=30, certificates=60, owned_groups_verified_empty=60,
            strict_analyzer_pairs_medians_ranges_counts_agree=True, table_counts=self.paper.TABLE_COUNTS,
            input_sha256={str(self.capture): self.paper.sha(self.capture)})
        self.audit_path.write_text(json.dumps(self.audit))
        self.write_values(self.tables)

    def write_values(self, value):
        path = self.standalone / 'plotted_values.json'
        path.write_text(json.dumps(value, allow_nan=False))
        self.proof['output_sha256'][path.name] = self.paper.sha(path)
        (self.standalone / 'provenance.json').write_text(json.dumps(self.proof))

    def load(self):
        with mock.patch.dict(sys.modules, {'run_lower_density': self.study, 'plot_retention_control': self.style}):
            return self.paper.checked_load(self.args)

    def test_complete_two_density_matrix_and_all_values(self):
        source, cases, tables, _, bound = self.load()
        groups, points = self.paper.paper_data(source, cases, tables)
        self.assertEqual(len(groups), 4)
        self.assertEqual(len(points), 660)
        self.assertEqual(sum(len(row['graph_medians']) for row in points), 1320)
        self.assertEqual(sum(2 for row in points), 1320)
        self.assertEqual({d: sum(p['density'] == d for p in points) for d in (16, 8)}, {16: 308, 8: 352})
        for row in points:
            names, field = ('summary', 'median_ns') if row['kind'] == 'times' else ('comparisons', 'median_paired_ratio')
            name_field = 'algorithm' if row['kind'] == 'times' else 'competitor'
            expected = next(r for r in tables[names] if (r['case_id'], r[name_field], r['metric']) ==
                            (row['case_id'], row['algorithm'], row['metric']))
            self.assertEqual(row['median'], expected[field] / (1e9 if names == 'summary' else 1))
        self.assertTrue(any(row['median'] > 1 for row in points if row['kind'] == 'ratios'))
        self.assertTrue(any(row['median'] < .9 for row in points if row['kind'] == 'ratios'))
        self.assertEqual({key: len(value) for key, value in tables.items()}, self.paper.TABLE_COUNTS)
        self.assertIn(str(self.audit_path), bound)

    def test_changed_canonical_values_or_classification_rejected_after_rehash(self):
        for name, key in (('comparisons', 'median_paired_ratio'), ('crossover_points', 'state'),
                          ('crossover_brackets', 'strong_crossover'), ('crossover_summary', 'density')):
            with self.subTest(name=name):
                values = copy.deepcopy(self.tables)
                values[name][0][key] = {'median_paired_ratio': 9.5, 'state': 'changed',
                                       'strong_crossover': True, 'density': 99}[key]
                self.write_values(values)
                with self.assertRaisesRegex(ValueError, 'Raw-derived tables differ'):
                    self.load()
        self.write_values(self.tables)

    def test_missing_clock_solver_density_and_duplicate_point_rejected(self):
        original = copy.deepcopy(self.tables)
        for change in ('clock', 'solver', 'density', 'duplicate', 'classification'):
            with self.subTest(change=change):
                self.tables = copy.deepcopy(original)
                if change == 'clock': self.tables['comparisons'][0]['metric'] = 'wrong_clock'
                elif change == 'solver': self.tables['summary'][0]['algorithm'] = 'unknown'
                elif change == 'density': self.cases[next(iter(self.cases))]['density'] = 8
                elif change == 'duplicate': self.tables['graph_comparisons'][1] = self.tables['graph_comparisons'][0]
                else: self.tables['crossover_brackets'].pop()
                self.write_values(self.tables)
                with self.assertRaises(ValueError): self.load()
                self.cases[next(iter(self.cases))]['density'] = 16
        self.tables = original

    def test_hash_receipt_and_import_restoration_guards(self):
        before = sys.path[:]
        sentinel = object()
        with mock.patch.dict(sys.modules, {'_lower_density_paper_standalone': sentinel}):
            self.load()
            self.assertIs(sys.modules['_lower_density_paper_standalone'], sentinel)
            self.assertEqual(sys.path, before)
            self.study.load = mock.Mock(side_effect=ValueError('synthetic load failure'))
            with self.assertRaisesRegex(ValueError, 'synthetic load failure'): self.load()
            self.assertIs(sys.modules['_lower_density_paper_standalone'], sentinel)
            self.assertEqual(sys.path, before)
        for path in (self.capture, self.source_path, self.standalone / 'plotted_values.json'):
            original = path.read_bytes(); path.write_bytes(original + b'\n')
            with self.assertRaisesRegex(ValueError, 'Changed input'): self.load()
            path.write_bytes(original)
        self.audit['checked_outputs'] = 2520.0
        self.audit_path.write_text(json.dumps(self.audit))
        with self.assertRaisesRegex(ValueError, 'Wrong independent audit checked_outputs'): self.load()
        malformed = self.root / 'malformed.json'
        for text in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}'):
            malformed.write_text(text)
            with self.assertRaises(ValueError): self.paper.read_json(malformed)


def main():
    global STANDALONE_SOURCE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--standalone-source', type=Path, required=True)
    args, remaining = parser.parse_known_args()
    STANDALONE_SOURCE = args.standalone_source.resolve(strict=True)
    unittest.main(argv=[sys.argv[0], *remaining])


if __name__ == '__main__':
    main()
