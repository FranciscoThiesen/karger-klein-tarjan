#!/usr/bin/env python3
"""Synthetic paper-input rejection gates; no native proof or rendering.

The original strict evidence loader is the sole mocked proof boundary. The real
standalone prepare(), paper load(), exact-value checks and hash checks run. Test
artifacts are temporary synthetic bytes, never a claimed completed capture.
"""
import argparse
import copy
import csv
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
COMPLEXITY_PACKAGE = None


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {name: value}):
        spec.loader.exec_module(value)
    return value


def csv_text(rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    return stream.getvalue()


class PaperInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if COMPLEXITY_PACKAGE is None:
            raise RuntimeError('explicit --complexity-package is required')
        cls.paper = module(HERE/'plot_complexity_paper_v2.py', 'paper_v2_under_test')
        cls.original_path = COMPLEXITY_PACKAGE/'plot_complexity.py'
        cls.original = module(cls.original_path, 'paper_test_standalone')
        analysis = module(COMPLEXITY_PACKAGE/'analyze_complexity.py', 'paper_test_analysis')
        with mock.patch.dict(sys.modules, {'analyze_complexity': analysis}):
            helpers = module(COMPLEXITY_PACKAGE/'test_analyze_complexity.py', 'paper_test_fixture_helpers')
        # Reuse the existing complete varied-clock fixture, rather than invent
        # native receipts or a second synthetic fit implementation here.
        curves = [helpers.make_curve(spec)[0] for spec in helpers.declared_specs()]
        cls.base_tables = analysis.aggregate(curves)
        cls.base_values = cls.paper.expected_values(cls.original, cls.base_tables, {'clock_flag_count': 0})

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='complexity-paper-synthetic-')
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.directory = root/'standalone'; self.directory.mkdir()
        canonical = root/'canonical'; canonical.mkdir()
        (self.directory/'analysis_tables').mkdir()
        self.tables = copy.deepcopy(self.base_tables)
        self.copies = {name+'.csv': csv_text(rows) for name, rows in self.tables.items()}
        self.inherited = {}
        for name, text in self.copies.items():
            path = canonical/name; path.write_text(text)
            self.inherited[str(path.resolve())] = self.paper.digest(path)
            (self.directory/'analysis_tables'/name).write_text(text)
        (self.directory/'plotted_values.json').write_text(json.dumps(self.base_values, allow_nan=False))
        for name in [*('normalized_'+clock for clock in self.original.CLOCKS), 'google_cpu_models']:
            for suffix in ('png', 'svg', 'pdf'):
                (self.directory/(name+'.'+suffix)).write_bytes(b'SYNTHETIC UNRENDERED TEST BYTES\n')
        self.source = root/'standalone_source.py'
        self.source.write_bytes(self.original_path.read_bytes())
        self.args = types.SimpleNamespace(standalone_source=self.source,
            standalone_source_sha256=self.paper.digest(self.source), standalone_dir=self.directory)
        self.proof = dict(schema='current_complexity_figures_v1', validation='rendered_pending_visual_qa',
            source_sha256=self.args.standalone_source_sha256, figures=5, formats=['png', 'svg', 'pdf'],
            normalized_points=1056, model_cells=288, google_curves=24, rows_removed=0, rows_adjusted=0,
            native_solver_execution=False, independent_numerical_audit=False, clock_flag_count=0,
            table_counts=self.original.COUNTS, input_sha256=self.inherited,
            output_sha256={str(path.relative_to(self.directory)): self.paper.digest(path)
                           for path in self.directory.rglob('*') if path.is_file()})
        self.write_proof()

    def write_proof(self):
        (self.directory/'provenance.json').write_text(json.dumps(self.proof, allow_nan=False))

    def update_output_hash(self, name):
        self.proof['output_sha256'][name] = self.paper.digest(self.directory/name)
        self.write_proof()

    def load(self):
        real_spec = importlib.util.spec_from_file_location
        fixture = self
        def intercepted_spec(name, path, *args, **kwargs):
            spec = real_spec(name, path, *args, **kwargs)
            if name == 'reviewed_complexity_standalone_layout':
                delegate = spec.loader
                class Loader:
                    def create_module(self, current):
                        return delegate.create_module(current)
                    def exec_module(self, value):
                        delegate.exec_module(value)
                        # Only native/capture reconstruction is mocked. Keep
                        # the actual source's complete prepare() validation.
                        value.load_evidence = lambda unused: (fixture.tables, fixture.copies,
                            fixture.inherited, {'clock_flag_count': 0})
                spec.loader = Loader()
            return spec
        with mock.patch.dict(sys.modules), mock.patch.object(
                self.paper.importlib.util, 'spec_from_file_location', side_effect=intercepted_spec):
            return self.paper.load(self.args)

    def test_complete_realization_clock_window_model_matrix(self):
        original, values, copies, bound = self.load()
        self.assertEqual(len(values['normalized_points']), 1056)
        self.assertEqual(len(values['model_cells']), 288)
        self.assertEqual(len(values['google_choices']), 24)
        self.assertEqual(set(copies), {name+'.csv' for name in original.COUNTS})
        self.assertEqual({row['display_clock'] for row in values['normalized_points']}, set(original.CLOCKS))
        self.assertEqual({row['model'] for row in values['model_cells']}, set(original.MODELS))
        self.assertIn(str((self.directory/'provenance.json').resolve()), bound)

    def test_changed_values_and_canonical_copy_rejected_even_after_rehash(self):
        path = self.directory/'plotted_values.json'
        values = copy.deepcopy(self.base_values)
        values['normalized_points'][0]['median_ns_per_N'] *= 1.01
        path.write_text(json.dumps(values, allow_nan=False)); self.update_output_hash(path.name)
        with self.assertRaisesRegex(ValueError, 'plotted data differs'):
            self.load()
        path.write_text(json.dumps(self.base_values, allow_nan=False)); self.update_output_hash(path.name)
        name = 'analysis_tables/model_fits.csv'
        path = self.directory/name
        rows = list(csv.DictReader(io.StringIO(path.read_text())))
        rows[0]['coefficient_ns'] = str(float(rows[0]['coefficient_ns']) + 1)
        path.write_text(csv_text(rows)); self.update_output_hash(name)
        with self.assertRaisesRegex(ValueError, 'copied canonical table differs'):
            self.load()

    def test_omitted_fit_clock_model_or_point_coverage_rejected(self):
        mutations = (
            lambda t: t['model_fits'].pop(),
            lambda t: t.__setitem__('model_fits', [r for r in t['model_fits'] if r['clock'] != 'native_steady']),
            lambda t: t.__setitem__('model_fits', [r for r in t['model_fits'] if r['model'] != 'N^3']),
            lambda t: t.__setitem__('size_summaries', [r for r in t['size_summaries'] if r['clock'] != 'library_manual']),
            lambda t: t['google_selection'].pop(),
        )
        for index, mutation in enumerate(mutations):
            self.tables = copy.deepcopy(self.base_tables); mutation(self.tables)
            with self.subTest(index=index), self.assertRaisesRegex(ValueError, 'incomplete'):
                self.load()

    def test_source_output_and_input_hash_drift_or_missing_inventory_rejected(self):
        for path in (self.source, self.directory/'google_cpu_models.pdf', Path(next(iter(self.inherited)))):
            original = path.read_bytes(); path.write_bytes(original+b'changed\n')
            try:
                with self.subTest(path=path.name), self.assertRaisesRegex(ValueError, 'changed input'):
                    self.load()
            finally:
                path.write_bytes(original)
        self.proof['output_sha256'].pop('google_cpu_models.svg'); self.write_proof()
        with self.assertRaisesRegex(ValueError, 'incomplete standalone output inventory'):
            self.load()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--complexity-package', type=Path, required=True)
    options, remaining = parser.parse_known_args()
    COMPLEXITY_PACKAGE = options.complexity_package.resolve(strict=True)
    unittest.main(argv=[sys.argv[0], *remaining])
