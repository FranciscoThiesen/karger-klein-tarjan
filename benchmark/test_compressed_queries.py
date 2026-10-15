#!/usr/bin/env python3
"""SOURCE PREPARATION ONLY: mocked compressed-query collector gates.

Not imported, syntax-checked or executed. Run only after the root releases
nonperformance work and installs the draft in the isolated worktree.
No native binary is launched by these tests.
"""
import argparse
import contextlib
import copy
import csv
import json
import math
from fractions import Fraction
import statistics
from pathlib import Path
import threading
import os
import shutil
import unittest
from unittest import mock

import run_compressed_queries as experiment
import test_edge_view_experiment as parent_tests
import test_retention_control as control_tests

control = experiment.control
old = control_tests.old_tests


@contextlib.contextmanager
def fixture():
    with parent_tests.fixture() as (parent_root, parent_args, _):
        parent = control.analysis.read_json(parent_args.freeze)
        root = parent_root / 'compressed-checkout'; root.mkdir()
        for name in (*parent['source_sha256'], *control.RECIPES):
            path = root / name; path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(parent_root / name, path)
        for name in experiment.CHANGED_NATIVE:
            path = root / name; path.write_text(path.read_text() + 'synthetic compressed optimization\n')
        for name in experiment.NEW_NATIVE:
            path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('synthetic new source\n')
        (root / 'benchmark/build_compressed_queries.py').write_text('synthetic build recipe; never executed\n')
        inherited = parent['variants']['edge']['build']['record']
        commands, objects, binaries, main, links = experiment.expected_commands(root, inherited['sdk'])
        for variant in experiment.VARIANTS:
            for name, value in objects[variant].items():
                path = Path(value); path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('synthetic ' + name + (variant if name == 'verifier/verifier_v2.o' else 'shared'))
        Path(main).parent.mkdir(parents=True, exist_ok=True); Path(main).write_text('synthetic shared main')
        manifest = root / 'compressed-manifest.csv'
        with manifest.open('w', newline='') as stream:
            writer = csv.writer(stream); writer.writerow(control.native.base.MANIFEST_FIELDS)
            writer.writerows(sorted(experiment.EXPECTED_CASES))
        protocol = root / 'COMPRESSED.md'; protocol.write_text('Synthetic prospective compressed experiment.\n')
        args = argparse.Namespace(parent_freeze=parent_args.freeze, manifest=manifest, protocol=protocol, freeze=root / 'compressed-freeze.json')
        for variant in experiment.VARIANTS:
            binary = Path(binaries[variant]); binary.parent.mkdir(parents=True, exist_ok=True); binary.write_text('synthetic binary ' + variant)
            log = root / (variant + '.build.log'); log.write_text('synthetic build log')
            record = dict(schema='compressed_query_build_v1', profile='timing-build', variant=variant,
                          base_commit='30728a3dedb9f6fc9b52289053e05d78a47ceffd',
                          seven_non_verifier_objects_identical_by_construction=True,
                          reference_source_textually_unchanged=True, scalar_sampling_fixed=True,
                          role='timing_never_executed',
                          working_directory=str(root), source_sha256=control.native.source_inventory(root),
                          build_recipe_sha256={name: control.native.sha(root / name) for name in experiment.RECIPES},
                          binary=str(binary), binary_sha256=control.native.sha(binary), binary_profile=parent['variants']['edge']['binary_profile'],
                          compiler=inherited['compiler'], compiler_command=inherited['compiler_command'],
                          sdk=inherited['sdk'], common_compile_flags=experiment.FLAGS,
                          build_command=['python3', '-B', str(root / 'benchmark/build_compressed_queries.py'), '--profile', 'timing-build', '--output', str(root), '--parent-freeze', str(parent_args.freeze)],
                          build_commands=commands, object_paths=objects[variant], object_sha256={name: control.native.sha(Path(value)) for name, value in objects[variant].items()},
                          main_object=main, main_object_sha256=control.native.sha(Path(main)), link_command=links[variant],
                          build_exit_status=0, build_log=str(log), build_log_sha256=control.native.sha(log),
                          parent_edge_freeze=str(parent_args.freeze), parent_edge_freeze_sha256=control.native.sha(parent_args.freeze))
            path = root / (variant + '-build.json'); control.write_json(path, record)
            setattr(args, variant + '_binary', binary); setattr(args, variant + '_build_record', path)
        os.chdir(root)
        try:
            with mock.patch.object(experiment, 'PARENT_SHA256', control.native.sha(parent_args.freeze)):
                experiment.preflight(args)
                yield root, args, parent
        finally:
            os.chdir(parent_root)


class Factory(control_tests.Factory):
    def __call__(self, argv, **kwargs):
        rows = control_tests.rows_for(argv)
        for row in rows:
            row['input_fingerprint'] = 10 if row['family'] == 'leaf_shuffled4' else 9
        if '/compressed/' in argv[2]:
            cpu = 0; utc = 946684800_000000000
            for row in rows:
                duration = 800 if row['algorithm'] == 'kkt' else row['elapsed_ns']
                row.update(elapsed_ns=duration, process_cpu_start_ns=cpu, process_cpu_end_ns=cpu + duration,
                           process_cpu_elapsed_ns=duration, utc_start_ns=utc, utc_end_ns=utc + duration)
                cpu += duration + 10; utc += duration + 10
        certificate = {field: rows[0][field] for field in control.native.CERTIFICATE_FIELDS}
        kwargs['stderr'].write(control.native.CERTIFICATE_PREFIX + json.dumps(certificate) + '\n')
        if self.mutation: self.mutation(rows)
        writer = csv.DictWriter(kwargs['stdout'], fieldnames=control.FIELDS); writer.writeheader(); writer.writerows(rows)
        process = old.FakeProcess(65000 + len(self.children), self.status, self.finishes)
        self.children.append((argv, process)); return process


def capture(root, args, factory=None, sampler=None, output='paired.csv'):
    factory = factory or Factory()
    def provider(group):
        process = next(process for _, process in factory.children if process.pid == group)
        return {'process_group': group, 'members': []} if process.returncode is not None else old.provider(group)
    sampler = sampler or control.monitor.BoundedSampler(provider, .1)
    info = experiment.capture(argparse.Namespace(freeze=args.freeze, output=root / output, released=True), sampler=sampler, popen=factory)
    return info, factory


class CompressedQueryTests(unittest.TestCase):
    def test_scoped_helpers_restore_after_nesting_and_failure(self):
        original = control.GRAPH_SEEDS, control.SAMPLING_SEED
        with self.assertRaisesRegex(RuntimeError, 'synthetic'):
            with experiment.configured(1801):
                self.assertEqual(control.SAMPLING_SEED, 1801)
                with experiment.configured(1801):
                    self.assertEqual(control.GRAPH_SEEDS, experiment.GRAPH_SEEDS)
                    self.assertEqual(control.SAMPLING_SEED, 1801)
                self.assertEqual(control.SAMPLING_SEED, 1801)
                raise RuntimeError('synthetic')
        self.assertEqual((control.GRAPH_SEEDS, control.SAMPLING_SEED), original)
        with self.assertRaisesRegex(ValueError, 'unknown sampling seed'):
            with experiment.configured(1803):
                self.fail('undeclared sampling seed entered scope')
        self.assertEqual((control.GRAPH_SEEDS, control.SAMPLING_SEED), original)

    def test_full_schedule_all_ratios_and_power(self):
        with fixture() as (root, args, parent):
            info, factory = capture(root, args)
            self.assertEqual((len(factory.children), info['checked_rows'], info['checked_timed_rows'], info['checked_warmup_rows']), (24, 1008, 864, 144))
            expected_schedule = experiment.schedule(experiment.cases_from_manifest(args.manifest))
            self.assertEqual([{key: item[key] for key in ('variant','case_id','graph_seed','kkt_seed')}
                              for item in info['captures']], expected_schedule)
            cases = list(experiment.cases_from_manifest(args.manifest))
            self.assertEqual(experiment.GRAPH_SEEDS, (8000009, 8000023))
            self.assertEqual(experiment.SAMPLING_SEEDS, (1801,))
            for gi, graph_seed in enumerate((8000009, 8000023)):
                block = info['captures'][gi*12:gi*12+12]
                variants = ['reference','compressed'] if gi == 0 else ['compressed','reference']
                case_order = cases if gi == 0 else list(reversed(cases))
                self.assertEqual([item['variant'] for item in block], variants*6)
                self.assertEqual([item['case_id'] for item in block], [case for case in case_order for _ in range(2)])
                self.assertTrue(all(item['graph_seed'] == graph_seed and item['kkt_seed'] == 1801 for item in block))
            loaded = experiment.load(root / 'paired.json'); tables = experiment.aggregate(loaded[2])
            self.assertEqual({key: len(value) for key, value in tables.items()}, experiment.TABLE_COUNTS)
            self.assertEqual(experiment.TABLE_COUNTS, {
                'paired_ratios': 1440, 'comparisons': 120, 'realization_comparisons': 240,
                'graph_comparisons': 240, 'sampling_comparisons': 120,
                'summary': 144, 'realization_summary': 288, 'graph_summary': 288,
                'sampling_summary': 144, 'variant_pairs': 864, 'variant_comparisons': 72,
                'realization_variant_comparisons': 144, 'graph_variant_comparisons': 144,
                'sampling_variant_comparisons': 72})
            self.assertEqual({row['algorithm'] for row in tables['variant_comparisons']}, set(control.ALGORITHMS))
            for row in tables['variant_pairs']:
                self.assertEqual(row['compressed_over_reference'], row['compressed_ns'] / row['reference_ns'])
            self.assertTrue(all(row['median_paired_ratio'] == (.8 if row['algorithm'] == 'kkt' else 1) and row['trials'] == 12 for row in tables['variant_comparisons']))
            for row in tables['comparisons']:
                scale = 1 if row['variant'] == 'reference' else .8
                self.assertAlmostEqual(row['median_paired_ratio'], scale / (1 + control.ALGORITHMS.index(row['competitor'])))
            power = root / 'power.log'
            power.write_text('2000-01-01 00:00:00 +0000 Sleep Entering Sleep state\n2000-01-01 00:00:00 +0000 Wake Requests request=Maintenance\n2000-01-01 00:00:01 +0000 Wake Wake from Deep Idle\n')
            experiment.analyze(argparse.Namespace(capture=root / 'paired.json', output_dir=root / 'analysis', power_log=power))
            self.assertEqual(control.analysis.read_json(root / 'analysis/provenance.json')['power_audit']['logged_overlap_calls'], 1008)
            with self.assertRaisesRegex(ValueError, 'overwrite'): capture(root, args)

    def test_schedule_metadata_native_exit_and_identity_fail_closed(self):
        with fixture() as (root, args, parent):
            good, _ = capture(root, args)
            mutations = {
                'missing child': lambda x: x['captures'].pop(),
                'wrong variant': lambda x: x['captures'][0].update(variant='compressed'),
                'wrong seed': lambda x: x['captures'][0].update(graph_seed=3000001),
                'wrong count': lambda x: x.update(checked_rows=840),
                'unknown exit': lambda x: x['captures'][0].update(exit_status=None),
                'wrong command': lambda x: x['captures'][0]['command'].append('extra'),
                'certificate': lambda x: x['captures'][0]['certificate'].update(m=1),
                'RSS identity': lambda x: x['captures'][0].update(process_group=1),
                'unverified group': lambda x: x['captures'][0].update(group_exit_verification={}),
                'early group': lambda x: x['captures'][0].update(wrapper_exit_monotonic_ns=x['captures'][0]['finished_monotonic_ns']+1),
                'missing flags': lambda x: x['call_diagnostics'].pop(),
                'trimmed': lambda x: x.update(rows_removed=1),
                'failed': lambda x: x.update(validation='failed'),
                'unknown group': lambda x: x.update(native_process_may_still_be_running=True),
            }
            for name, mutate in mutations.items():
                changed = copy.deepcopy(good); mutate(changed); control.write_json(root / 'paired.json', changed)
                with self.subTest(name=name), self.assertRaises((ValueError, KeyError)): experiment.load(root / 'paired.json')

    def test_native_rows_certificate_pair_fingerprints_and_combined_reread(self):
        with fixture() as (root, args, parent):
            good, _ = capture(root, args)
            item = good['captures'][1]; raw = Path(item['csv']); original = raw.read_bytes()
            values = [row for _, row in control.native.base.read_csv(raw, control.FIELDS)]
            for field, value in (('algorithm', 'kruskal'), ('kkt_seed', '809'), ('input_fingerprint', '12'), ('validation', 'failed')):
                rows = copy.deepcopy(values); rows[0][field] = value; control.analysis.write_csv(raw, rows)
                changed = copy.deepcopy(good); changed['captures'][1]['output_sha256'] = control.native.sha(raw)
                control.write_json(root / 'paired.json', changed)
                with self.subTest(field=field), self.assertRaises(ValueError): experiment.load(root / 'paired.json')
            for name, mutate in (
                    ('missing warmup', lambda rows: rows.pop(0)),
                    ('missing timed call', lambda rows: rows.pop()),
                    ('duplicate timed row', lambda rows: rows.__setitem__(-1, dict(rows[-2])))):
                rows = copy.deepcopy(values); mutate(rows); control.analysis.write_csv(raw, rows)
                changed = copy.deepcopy(good); changed['captures'][1]['output_sha256'] = control.native.sha(raw)
                control.write_json(root / 'paired.json', changed)
                with self.subTest(name=name), self.assertRaises(ValueError): experiment.load(root / 'paired.json')
            raw.write_bytes(original); control.write_json(root / 'paired.json', good)
            # Change every fingerprint and certificate in one variant: per-child
            # consistency passes, but cross-variant same-input validation must fail.
            rows = copy.deepcopy(values)
            for row in rows: row['input_fingerprint'] = '12'
            control.analysis.write_csv(raw, rows)
            log = Path(item['log']); original_log = log.read_bytes()
            cert = copy.deepcopy(item['certificate']); cert['input_fingerprint'] = 12
            log.write_text(control.native.CERTIFICATE_PREFIX + json.dumps(cert) + '\n')
            changed = copy.deepcopy(good); changed['captures'][1].update(output_sha256=control.native.sha(raw), log_sha256=control.native.sha(log), certificate=cert)
            control.write_json(root / 'paired.json', changed)
            with self.assertRaisesRegex(ValueError, 'fingerprints'): experiment.load(root / 'paired.json')
            raw.write_bytes(original); log.write_bytes(original_log)
            combined = root / 'paired.csv'; rows = [row for _, row in control.native.base.read_csv(combined, experiment.FIELDS)]
            rows[0]['variant'] = 'compressed'; control.analysis.write_csv(combined, rows)
            good['output_sha256'] = control.native.sha(combined); control.write_json(root / 'paired.json', good)
            with self.assertRaisesRegex(ValueError, 'concatenation'): experiment.load(root / 'paired.json')

    def test_provenance_source_helpers_objects_flags_and_parent_drift(self):
        with fixture() as (root, args, parent):
            record = control.analysis.read_json(args.compressed_build_record)
            for path in (args.compressed_binary, args.protocol, args.manifest, args.parent_freeze,
                         root / 'benchmark/retention_control.cpp', root / 'verifier/verifier_v2.cpp',
                         root / 'benchmark/build_compressed_queries.py', Path(record['object_paths']['verifier/verifier_v2.o']), Path(record['object_paths']['kkt/kkt.o']),
                         Path(record['main_object'])):
                before = path.read_bytes(); path.write_bytes(before + b'drift'); factory = Factory()
                with self.subTest(path=path), self.assertRaises(ValueError): capture(root, args, factory=factory)
                self.assertFalse(factory.children); path.write_bytes(before)
            helpers = control.helpers(); changed = dict(helpers); changed[next(iter(changed))] = '0' * 64
            with mock.patch.object(control, 'helpers', return_value=changed), self.assertRaisesRegex(ValueError, 'Edge helper copies changed'):
                experiment.check_freeze(args.freeze)
            mutations = {
                'NDEBUG': lambda x: x['build_commands'][0].insert(3, '-DNDEBUG'),
                'stats': lambda x: x['common_compile_flags'].append('-DKKT_ENABLE_WORK_STATS'),
                'wrong dispatch': lambda x: x['build_commands'][8].remove('-DKKT_EXPERIMENT_COMPRESSED_QUERIES'),
                'wrong link': lambda x: x['link_command'].insert(-2, 'foreign.o'),
                'wrong shared object': lambda x: x['object_sha256'].update({'kkt/kkt.o': '0'*64}),
                'wrong base': lambda x: x.update(base_commit='0'*40),
                'wrong role': lambda x: x.update(role='timing_executed'),
                'changed sampler': lambda x: x.update(scalar_sampling_fixed=False),
                'changed default': lambda x: x.update(reference_source_textually_unchanged=False),
                'unshared controls': lambda x: x.update(seven_non_verifier_objects_identical_by_construction=False),
                'packed macro': lambda x: x['build_commands'][6].insert(3, '-DKKT_EXPERIMENT_PACKED_SAMPLING'),
                'wrong sdk': lambda x: x.update(sdk='other'),
                'wrong parent': lambda x: x.update(parent_edge_freeze_sha256='0'*64),
            }
            for name, mutate in mutations.items():
                changed = copy.deepcopy(record); mutate(changed); control.write_json(args.compressed_build_record, changed)
                with self.subTest(name=name), self.assertRaises(ValueError):
                    experiment.build_record(args.compressed_build_record, args.compressed_binary, root, parent, args.parent_freeze, 'compressed')
            control.write_json(args.compressed_build_record, record)
            with self.assertRaisesRegex(ValueError, 'released'):
                experiment.capture(argparse.Namespace(freeze=args.freeze, output=root/'unreleased.csv', released=False))

    def test_clock_flags_preserved_and_pair_median_pools_twelve_trials(self):
        with fixture() as (root, args, parent):
            info, _ = capture(root, args, factory=Factory(mutation=lambda rows: rows[0].update(elapsed_ns=2_000_000_000)))
            self.assertEqual(info['flagged_calls'], 24)
            rows = experiment.load(root/'paired.json')[2]
            self.assertEqual(len(rows), 1008)
            self.assertTrue(all(not row['excluded'] for row in info['call_diagnostics']))
            case = rows[0]['case_id']
            values = dict(zip(experiment.GRAPH_SEEDS, ([1,2,10,20,30,40], [3,4,5,6,7,8])))
            for row in rows:
                if row['case_id'] == case and row['phase'] == 'timed' and row['algorithm'] == 'kkt':
                    value = values[row['graph_seed']][row['repetition']] if row['variant'] == 'compressed' else 1
                    row.update(elapsed_ns=value*100, process_cpu_elapsed_ns=value*100)
            compared = experiment.aggregate(rows)['variant_comparisons']
            self.assertTrue(all(row['median_paired_ratio'] == 6.5 for row in compared if row['case_id'] == case and row['algorithm'] == 'kkt'))
            rows = [row for row in rows if not (row['case_id'] == case and row['phase'] == 'timed' and row['algorithm'] == 'kkt' and row['variant'] == 'compressed' and row['repetition'] == 0)]
            with self.assertRaises(ValueError): experiment.aggregate(rows)

    def test_twins_sampler_marginals_manifest_and_parent_scope(self):
        with fixture() as (root, args, parent):
            info, _ = capture(root, args)
            rows = experiment.load(root / 'paired.json')[2]
            tables = experiment.aggregate(rows)
            for prefix, trials in (('realization_', 6), ('graph_', 6), ('sampling_', 12)):
                for name in ('comparisons', 'summary', 'variant_comparisons'):
                    self.assertTrue(all(row['trials'] == trials for row in tables[prefix + name]))
            for field, message in (('topology_fingerprint', 'different topology'), ('input_fingerprint', 'identical weighted')):
                changed = copy.deepcopy(rows)
                for row in changed:
                    if row['family'] == 'leaf_shuffled4':
                        row[field] = 999 if field == 'topology_fingerprint' else 9
                with self.subTest(field=field), self.assertRaisesRegex(ValueError, message):
                    experiment.check_fingerprints(changed, complete=True)
            # There is only one sampler realization; an extra sampler is not
            # silently pooled into the case or treated as another graph.
            changed = copy.deepcopy(rows)
            next(row for row in changed if row['phase'] == 'timed')['kkt_seed'] = 1803
            with self.assertRaisesRegex(ValueError, 'unknown realization'):
                experiment.aggregate(changed)
            for name, value_field in (('comparisons', 'median_paired_ratio'),
                                      ('summary', 'median_ns'),
                                      ('variant_comparisons', 'median_paired_ratio')):
                def identity(row):
                    return tuple((key, row[key]) for key in
                                 ('variant','case_id','algorithm','competitor','metric') if key in row)
                pooled = {identity(row): row[value_field] for row in tables[name]}
                self.assertEqual(len(tables['sampling_' + name]), len(pooled))
                for row in tables['sampling_' + name]:
                    self.assertEqual(row['kkt_seed'], 1801)
                    self.assertEqual(row[value_field], pooled[identity(row)])
                    self.assertEqual(row['trials'], 12)
            before = args.manifest.read_bytes(); args.manifest.write_bytes(before.replace(b'65536', b'131072', 1))
            with self.assertRaisesRegex(ValueError, 'six compressed'): experiment.cases_from_manifest(args.manifest)
            args.manifest.write_bytes(before)
            original = experiment.parent_engine.helpers
            with mock.patch.object(experiment.parent_engine, 'check_freeze', side_effect=RuntimeError('parent failure')):
                with self.assertRaisesRegex(RuntimeError, 'parent failure'): experiment.parent_record(args.parent_freeze)
            self.assertIs(experiment.parent_engine.helpers, original)
            self.assertEqual(len(experiment.crossovers(tables, experiment.cases_from_manifest(args.manifest))), 30)

    def test_exact_build_commands_change_only_verifier_and_share_scalar_kkt(self):
        with fixture() as (root, args, parent):
            record = control.analysis.read_json(args.compressed_build_record)
            commands = record['build_commands']
            self.assertEqual(len(commands), 12)
            shared = ('boruvka/boruvka.cpp', 'kruskal/kruskal.cpp', 'prim/prim.cpp',
                      'lca/lca.cpp', 'union_find/union_find.cpp', 'graph_utils/graph_utils.cpp',
                      'kkt/kkt.cpp')
            expected_flags = ['-std=c++17', '-O3', '-Wall', '-Wextra', '-march=native',
                              '-DKKT_EXPERIMENT_RETAIN_PARALLEL', '-DKKT_EXPERIMENT_EDGE_VIEW']
            self.assertEqual(experiment.FLAGS, expected_flags)
            base = ['/usr/bin/arch', '-arm64', '/usr/bin/clang++', '-isysroot', record['sdk'],
                    *expected_flags, '-I.']
            build = root / '.build/compressed-query/timing-build'
            for index, source in enumerate(shared):
                self.assertEqual(commands[index], base + ['-c', source, '-o',
                    str(build / 'shared' / source.replace('.cpp', '.o'))])
            for index, variant in ((7, 'reference'), (8, 'compressed')):
                macro = ['-DKKT_EXPERIMENT_COMPRESSED_QUERIES'] if variant == 'compressed' else []
                self.assertEqual(commands[index], base + macro + ['-c', 'verifier/verifier_v2.cpp', '-o',
                    str(build / variant / 'verifier/verifier_v2.o')])
            self.assertEqual(commands[9], base + ['-c', 'benchmark/retention_control.cpp', '-o',
                str(build / 'shared/benchmark/retention_control.o')])
            records = [control.analysis.read_json(getattr(args, variant + '_build_record'))
                       for variant in ('reference', 'compressed')]
            for source in shared:
                name = source.replace('.cpp', '.o')
                self.assertEqual(records[0]['object_paths'][name], records[1]['object_paths'][name])
                self.assertEqual(records[0]['object_sha256'][name], records[1]['object_sha256'][name])
            self.assertNotEqual(records[0]['object_paths']['verifier/verifier_v2.o'],
                                records[1]['object_paths']['verifier/verifier_v2.o'])
            for index, variant in ((10, 'reference'), (11, 'compressed')):
                # Spell the link inputs independently of expected_commands and
                # of both record fields populated from that same helper.
                expected_link = base + [
                    str(build / 'shared/boruvka/boruvka.o'),
                    str(build / 'shared/kruskal/kruskal.o'),
                    str(build / 'shared/prim/prim.o'),
                    str(build / 'shared/lca/lca.o'),
                    str(build / 'shared/union_find/union_find.o'),
                    str(build / 'shared/graph_utils/graph_utils.o'),
                    str(build / 'shared/kkt/kkt.o'),
                    str(build / variant / 'verifier/verifier_v2.o'),
                    str(build / 'shared/benchmark/retention_control.o'),
                    '-L' + record['sdk'] + '/usr/lib',
                    '-Wl,-stack_size,0x20000000', '-o',
                    str(root / 'bin/compressed-query/timing-build' / variant / 'retention_control')]
                self.assertEqual(commands[index], expected_link)
                self.assertEqual(records[index - 10]['link_command'], expected_link)
                self.assertNotIn('-DKKT_EXPERIMENT_COMPRESSED_QUERIES', commands[index])
                self.assertNotIn('-DKKT_EXPERIMENT_PACKED_SAMPLING', commands[index])

    def test_every_ratio_and_graph_median_against_rational_raw_values(self):
        with fixture() as (root, args, parent):
            capture(root, args)
            # The strict loader first validates the captured clock/certificate
            # data. Change only an in-memory copy for this arithmetic oracle;
            # these synthetic durations are never claimed to be a capture.
            rows = copy.deepcopy(experiment.load(root / 'paired.json')[2])
            algorithms = ('kkt', 'compacting_boruvka', 'multigraph_boruvka',
                          'kruskal', 'prim', 'boruvka')
            variants, graphs = ('reference', 'compressed'), (8000009, 8000023)
            expected_cases = {('leaf_hierarchy4', 65536, 32, 0),
                              ('leaf_shuffled4', 65536, 32, 0),
                              ('leaf_hierarchy4', 1048576, 32, 0),
                              ('leaf_shuffled4', 1048576, 32, 0),
                              ('gnm_random', 4096, 16, 0),
                              ('gnm_random', 1048576, 16, 0)}
            case_specs = {}
            for row in rows:
                spec = tuple(row[key] for key in ('family', 'n', 'density', 'intrusion_per_mille'))
                if row['case_id'] in case_specs:
                    self.assertEqual(case_specs[row['case_id']], spec)
                case_specs[row['case_id']] = spec
            self.assertEqual(len(case_specs), 6)
            self.assertEqual(set(case_specs.values()), expected_cases)
            cases = sorted(case_specs)
            for row in rows:
                if row['phase'] != 'timed': continue
                c, g = cases.index(row['case_id']), graphs.index(row['graph_seed'])
                r, a = row['repetition'], algorithms.index(row['algorithm'])
                v = variants.index(row['variant'])
                # Different coefficients and variant effects in the two clocks
                # prevent swapped clocks, graph groups, or repetitions from
                # passing merely because every synthetic ratio is constant.
                row['elapsed_ns'] = (1000003 + 10007*c + 2113*g + 421*r + 113*a
                    + v*(4001 + 73*c + 41*g + 17*r + 13*a + 7*r*a))
                row['process_cpu_elapsed_ns'] = (600001 + 7013*c + 1747*g + 307*r + 89*a
                    + v*(2039 + 47*c + 37*g + 19*r + 11*a + 5*r*a))
                self.assertGreater(row['process_cpu_elapsed_ns'], 0)
                self.assertGreater(row['elapsed_ns'], row['process_cpu_elapsed_ns'])
            raw = {(row['variant'], row['case_id'], row['graph_seed'], row['kkt_seed'],
                    row['repetition'], row['algorithm']): row for row in rows if row['phase'] == 'timed'}
            expected_raw = {(variant, case, graph, 1801, rep, algorithm)
                            for variant in variants for case in cases for graph in graphs
                            for rep in range(6) for algorithm in algorithms}
            self.assertEqual(sum(row['phase'] == 'timed' for row in rows), len(raw))
            self.assertEqual(len(raw), 864)
            self.assertEqual(set(raw), expected_raw)
            clock_fields = {'wall': 'elapsed_ns', 'cpu': 'process_cpu_elapsed_ns'}
            expected_variant, expected_within, variant_groups, within_groups = {}, {}, {}, {}
            # Derive the complete Cartesian identities and groups from raw
            # six-solver rows, never from collector-produced pairs or summaries.
            for case in cases:
                for graph in graphs:
                    for rep in range(6):
                        for algorithm in algorithms:
                            for metric, field in clock_fields.items():
                                first = raw[('reference', case, graph, 1801, rep, algorithm)][field]
                                second = raw[('compressed', case, graph, 1801, rep, algorithm)][field]
                                ratio = Fraction(second, first)
                                expected_variant[(case, graph, 1801, rep, algorithm, metric)] = first, second, ratio
                                key = case, algorithm, metric
                                variant_groups.setdefault(key, {}).setdefault(graph, []).append(ratio)
                        for variant in variants:
                            for competitor in algorithms[1:]:
                                for metric, field in clock_fields.items():
                                    first = raw[(variant, case, graph, 1801, rep, 'kkt')][field]
                                    second = raw[(variant, case, graph, 1801, rep, competitor)][field]
                                    ratio = Fraction(first, second)
                                    expected_within[(variant, case, graph, 1801, rep, competitor, metric)] = first, second, ratio
                                    key = variant, case, competitor, metric
                                    within_groups.setdefault(key, {}).setdefault(graph, []).append(ratio)
            self.assertEqual((len(expected_variant), len(expected_within)), (864, 1440))
            tables = experiment.aggregate(rows)

            def check_pairs(actual, expected, fields, first_field, second_field, ratio_field):
                indexed = {tuple(row[key] for key in fields): row for row in actual}
                self.assertEqual(len(actual), len(indexed), 'duplicate pair identity')
                self.assertEqual(set(indexed), set(expected), 'missing or extra pair identity')
                for identity, (first, second, ratio) in expected.items():
                    row = indexed[identity]
                    self.assertEqual((row[first_field], row[second_field]), (first, second))
                    self.assertEqual(row[ratio_field], float(ratio))

            for name, expected, fields, first_field, second_field, ratio_field in (
                    ('variant_pairs', expected_variant,
                     ('case_id','graph_seed','kkt_seed','repetition','algorithm','metric'),
                     'reference_ns', 'compressed_ns', 'compressed_over_reference'),
                    ('paired_ratios', expected_within,
                     ('variant','case_id','graph_seed','kkt_seed','repetition','competitor','metric'),
                     'kkt_ns', 'competitor_ns', 'kkt_over_competitor')):
                actual = tables[name]
                check_pairs(actual, expected, fields, first_field, second_field, ratio_field)
                # Exercise the oracle itself: equal row counts cannot conceal a
                # duplicate identity, and retaining metric labels cannot conceal
                # data taken from the opposite clock.
                for corruption in ('duplicate', 'missing', 'opposite clock'):
                    damaged = copy.deepcopy(actual)
                    if corruption == 'duplicate': damaged[-1] = copy.deepcopy(damaged[0])
                    elif corruption == 'missing': damaged.pop()
                    else:
                        identity = tuple(damaged[0][key] for key in fields)
                        other = expected[(*identity[:-1], 'cpu' if identity[-1] == 'wall' else 'wall')]
                        damaged[0][first_field], damaged[0][second_field] = other[:2]
                        damaged[0][ratio_field] = float(other[2])
                    with self.subTest(table=name, corruption=corruption), self.assertRaises(AssertionError):
                        check_pairs(damaged, expected, fields, first_field, second_field, ratio_field)

            for name, groups, key_fields in (
                    ('variant_comparisons', variant_groups, ('case_id','algorithm','metric')),
                    ('comparisons', within_groups, ('variant','case_id','competitor','metric'))):
                for by_graph in groups.values():
                    self.assertEqual(set(by_graph), {8000009, 8000023})
                    self.assertTrue(all(len(values) == 6 for values in by_graph.values()))
                expected_summaries = {
                    name: {key: [value for graph in graphs for value in by_graph[graph]]
                           for key, by_graph in groups.items()},
                    'graph_' + name: {(*key, graph): by_graph[graph]
                                     for key, by_graph in groups.items() for graph in graphs},
                    'realization_' + name: {(*key, graph, 1801): by_graph[graph]
                                           for key, by_graph in groups.items() for graph in graphs},
                    'sampling_' + name: {(*key, 1801): [value for graph in graphs for value in by_graph[graph]]
                                        for key, by_graph in groups.items()}}
                for table_name, extra_fields in ((name, ()), ('graph_' + name, ('graph_seed',)),
                        ('realization_' + name, ('graph_seed','kkt_seed')), ('sampling_' + name, ('kkt_seed',))):
                    actual = tables[table_name]
                    indexed = {tuple(row[key] for key in (*key_fields, *extra_fields)): row for row in actual}
                    expected = expected_summaries[table_name]
                    self.assertEqual(len(actual), len(indexed), 'duplicate summary identity')
                    self.assertEqual(set(indexed), set(expected), 'missing or extra summary identity')
                    for identity, values in expected.items():
                        row = indexed[identity]
                        median = float(statistics.median(values))
                        # The implementation takes a median of rounded binary
                        # ratios; allow only final floating-point rounding.
                        self.assertAlmostEqual(row['median_paired_ratio'], median, delta=2*math.ulp(median))
                        self.assertEqual(row['trial_min'], float(min(values)))
                        self.assertEqual(row['trial_max'], float(max(values)))
                        self.assertEqual(row['individual_wins'], sum(value < 1 for value in values))
                        self.assertEqual(row['trials'], len(values))

    def test_crossover_requires_both_graphs_both_clocks_and_exact_thresholds(self):
        with fixture() as (root, args, parent):
            capture(root, args)
            loaded = experiment.load(root / 'paired.json')
            original = experiment.aggregate(loaded[2])
            def target(row):
                return (row['variant'], row['family'], row['density'], row['competitor']) == (
                    'compressed', 'leaf_hierarchy4', 32, 'multigraph_boruvka')
            for kind, expected, large_state in (
                    ('strong', True, 'strong_lead'), ('one_graph', False, 'mixed_or_tied'),
                    ('one_clock', False, 'narrow_lead'), ('small_tie', False, 'strong_lead'),
                    ('already_leads', False, 'strong_lead'), ('narrow', False, 'narrow_lead')):
                tables = copy.deepcopy(original)
                affected = [row for row in tables['realization_comparisons'] if target(row)]
                self.assertEqual(len(affected), 8)
                for row in affected:
                    small = row['n'] == 65536
                    value = 1.1 if small else .9
                    if kind == 'one_graph' and not small and row['graph_seed'] == 8000023: value = 1.1
                    if kind == 'one_clock' and not small and row['metric'] == 'cpu': value = .95
                    if kind == 'small_tie' and small and row['graph_seed'] == 8000023: value = 1
                    if kind == 'already_leads' and small: value = .8
                    if kind == 'narrow' and not small: value = .95
                    row['median_paired_ratio'] = value
                classifications = experiment.crossovers(tables, loaded[1])
                selected = [row for row in classifications if target(row)]
                self.assertEqual(len(classifications), 30)
                self.assertEqual(len(selected), 1)
                self.assertEqual(selected[0]['strong_crossover'], expected, kind)
                self.assertEqual(selected[0]['large_state'], large_state, kind)
                self.assertFalse(any(row['strong_crossover'] for row in classifications if not target(row)))
            missing = copy.deepcopy(original)
            missing['realization_comparisons'].pop()
            with self.assertRaisesRegex(ValueError, 'both graph medians on both clocks'):
                experiment.crossovers(missing, loaded[1])

    def test_parent_checker_runs_unscoped_and_restores_helper_binding(self):
        with fixture() as (root, args, parent):
            original_state = control.GRAPH_SEEDS, control.SAMPLING_SEED
            original_checker = experiment.parent_engine.check_freeze
            original_helpers = experiment.parent_engine.helpers
            observations = []
            def check(path):
                observations.append((control.GRAPH_SEEDS, control.SAMPLING_SEED))
                self.assertEqual(observations[-1], original_state)
                return original_checker(path)
            with mock.patch.object(experiment.parent_engine, 'check_freeze', side_effect=check):
                experiment.check_freeze(args.freeze)
            self.assertTrue(observations)
            self.assertIs(experiment.parent_engine.helpers, original_helpers)
            self.assertEqual((control.GRAPH_SEEDS, control.SAMPLING_SEED), original_state)
            # The parent still validates normally after the temporary binding.
            original_checker(args.parent_freeze)

    def test_monitor_and_native_failure_never_advance_to_second_variant(self):
        for failure in ('ceiling', 'unavailable', 'nonempty group', 'unavailable exit', 'native crash'):
            with self.subTest(failure=failure), fixture() as (root, args, parent):
                factory = Factory(status=-11 if failure == 'native crash' else 0, finishes=failure != 'unavailable')
                def provider(group):
                    exited = factory.children[-1][1].returncode is not None
                    if failure == 'unavailable' or (failure == 'unavailable exit' and exited): raise OSError('synthetic')
                    result = old.provider(group)
                    if failure == 'ceiling': result['members'][0]['rss_kib'] = control.RULE['rss_limit_kib'] + 1
                    return result
                sampler = control.monitor.BoundedSampler(provider, .1)
                with mock.patch.object(control.monitor, 'bounded_terminate', return_value={'native_process_may_still_be_running': True}), self.assertRaises(ValueError):
                    capture(root, args, factory=factory, sampler=sampler)
                self.assertEqual(len(factory.children), 1)
                self.assertEqual(control.analysis.read_json(root/'paired.json')['validation'], 'failed')

    def test_stuck_sampler_poison_blocks_new_capture(self):
        with fixture() as (root, args, parent):
            gate = threading.Event(); factory = Factory()
            sampler = control.monitor.BoundedSampler(lambda group: (gate.wait(), old.provider(group))[1], .01)
            try:
                with mock.patch.object(control.monitor, 'bounded_terminate', return_value={'native_process_may_still_be_running': True}), self.assertRaisesRegex(ValueError, 'timed out'):
                    capture(root, args, factory=factory, sampler=sampler)
                self.assertEqual((len(factory.children), sampler.workers_started), (1, 1))
                second = Factory()
                with self.assertRaisesRegex(ValueError, 'forbids launching'):
                    capture(root, args, factory=second, sampler=sampler, output='second.csv')
                self.assertFalse(second.children); self.assertEqual(sampler.workers_started, 1)
            finally: gate.set()


if __name__ == '__main__': unittest.main(verbosity=2)
