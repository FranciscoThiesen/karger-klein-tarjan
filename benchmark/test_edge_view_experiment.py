#!/usr/bin/env python3
"""Disposable mocked paired-six capture; no native build or execution."""
import argparse
import contextlib
import copy
import csv
import json
from pathlib import Path
import threading
import unittest
from unittest import mock

import run_edge_view_experiment as experiment
import test_retention_control as control_tests

control = experiment.control
old = control_tests.old_tests


@contextlib.contextmanager
def fixture():
    with control_tests.fixture() as (root, control_args, _):
        parent = control.analysis.read_json(control_args.freeze)
        for name in experiment.CHANGED_NATIVE:
            path = root / name; path.write_text(path.read_text() + 'synthetic verifier optimization\n')
        for name in experiment.NEW_NATIVE:
            path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('synthetic new test\n')
        (root / 'benchmark/build_edge_verifier.py').write_text('synthetic build recipe; never executed\n')
        commands, objects, binaries, main, links = experiment.expected_commands(root, parent['build']['record']['sdk'])
        for variant in experiment.VARIANTS:
            for name, value in objects[variant].items():
                path = Path(value); path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('synthetic ' + name + (variant if name == 'kkt/kkt.o' else 'shared'))
        Path(main).parent.mkdir(parents=True, exist_ok=True); Path(main).write_text('synthetic shared main')
        manifest = root / 'edge-manifest.csv'; manifest.write_bytes(control_args.manifest.read_bytes())
        protocol = root / 'EDGE.md'; protocol.write_text('Synthetic prospective paired experiment.\n')
        args = argparse.Namespace(parent_freeze=control_args.freeze, manifest=manifest, protocol=protocol, freeze=root / 'edge-freeze.json')
        for variant in experiment.VARIANTS:
            binary = Path(binaries[variant]); binary.parent.mkdir(parents=True, exist_ok=True); binary.write_text('synthetic binary ' + variant)
            log = root / (variant + '.build.log'); log.write_text('synthetic build log')
            record = dict(schema='edge_verifier_build_v1', profile='timing-build', variant=variant,
                          working_directory=str(root), source_sha256=control.native.source_inventory(root),
                          build_recipe_sha256={name: control.native.sha(root / name) for name in experiment.RECIPES},
                          binary=str(binary), binary_sha256=control.native.sha(binary), binary_profile=parent['binary_profile'],
                          compiler=parent['build']['record']['compiler'], compiler_command=parent['build']['record']['compiler_command'],
                          sdk=parent['build']['record']['sdk'], common_compile_flags=experiment.FLAGS,
                          build_command=['python3', '-B', str(root / 'benchmark/build_edge_verifier.py'), '--profile', 'timing-build', '--output', str(root), '--parent-freeze', str(control_args.freeze)],
                          build_commands=commands, object_paths=objects[variant], object_sha256={name: control.native.sha(Path(value)) for name, value in objects[variant].items()},
                          main_object=main, main_object_sha256=control.native.sha(Path(main)), link_command=links[variant],
                          build_exit_status=0, build_log=str(log), build_log_sha256=control.native.sha(log),
                          parent_control_freeze=str(control_args.freeze), parent_control_freeze_sha256=control.native.sha(control_args.freeze))
            path = root / (variant + '-build.json'); control.write_json(path, record)
            setattr(args, variant + '_binary', binary); setattr(args, variant + '_build_record', path)
        with mock.patch.object(experiment, 'PARENT_SHA256', control.native.sha(control_args.freeze)):
            experiment.preflight(args)
            yield root, args, parent


class Factory(control_tests.Factory):
    def __call__(self, argv, **kwargs):
        rows = control_tests.rows_for(argv)
        if '/edge/' in argv[2]:
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


class EdgeViewExperimentTests(unittest.TestCase):
    def test_scoped_helpers_restore_after_nesting_and_failure(self):
        original = control.GRAPH_SEEDS, control.SAMPLING_SEED
        with self.assertRaisesRegex(RuntimeError, 'synthetic'):
            with experiment.configured():
                self.assertEqual(control.SAMPLING_SEED, 1013)
                with experiment.configured(): self.assertEqual(control.GRAPH_SEEDS, experiment.GRAPH_SEEDS)
                self.assertEqual(control.SAMPLING_SEED, 1013)
                raise RuntimeError('synthetic')
        self.assertEqual((control.GRAPH_SEEDS, control.SAMPLING_SEED), original)

    def test_full_schedule_all_ratios_and_power(self):
        with fixture() as (root, args, parent):
            info, factory = capture(root, args)
            self.assertEqual((len(factory.children), info['checked_rows'], info['checked_timed_rows'], info['checked_warmup_rows']), (40, 1680, 1440, 240))
            first = [(item['case_id'], item['variant']) for item in info['captures'][:20]]
            second = [(item['case_id'], item['variant']) for item in info['captures'][20:]]
            self.assertEqual(first, list(reversed(second)))
            self.assertEqual([item[1] for item in first], ['tuple', 'edge'] * 10)
            loaded = experiment.load(root / 'paired.json'); tables = experiment.aggregate(loaded[2])
            expected = {'paired_ratios': 2400, 'comparisons': 200, 'graph_comparisons': 400, 'summary': 240,
                        'graph_summary': 480, 'variant_pairs': 1440, 'variant_comparisons': 120, 'graph_variant_comparisons': 240}
            self.assertEqual({key: len(value) for key, value in tables.items()}, expected)
            self.assertEqual({row['algorithm'] for row in tables['variant_comparisons']}, set(control.ALGORITHMS))
            for row in tables['variant_pairs']:
                self.assertEqual(row['edge_over_tuple'], row['edge_ns'] / row['tuple_ns'])
            self.assertTrue(all(row['median_paired_ratio'] == (.8 if row['algorithm'] == 'kkt' else 1) and row['trials'] == 12 for row in tables['variant_comparisons']))
            for row in tables['comparisons']:
                scale = 1 if row['variant'] == 'tuple' else .8
                self.assertAlmostEqual(row['median_paired_ratio'], scale / (1 + control.ALGORITHMS.index(row['competitor'])))
            power = root / 'power.log'
            power.write_text('2000-01-01 00:00:00 +0000 Sleep Entering Sleep state\n2000-01-01 00:00:00 +0000 Wake Requests request=Maintenance\n2000-01-01 00:00:01 +0000 Wake Wake from Deep Idle\n')
            experiment.analyze(argparse.Namespace(capture=root / 'paired.json', output_dir=root / 'analysis', power_log=power))
            self.assertEqual(control.analysis.read_json(root / 'analysis/provenance.json')['power_audit']['logged_overlap_calls'], 1680)
            with self.assertRaisesRegex(ValueError, 'overwrite'): capture(root, args)

    def test_schedule_metadata_native_exit_and_identity_fail_closed(self):
        with fixture() as (root, args, parent):
            good, _ = capture(root, args)
            mutations = {
                'missing child': lambda x: x['captures'].pop(),
                'wrong variant': lambda x: x['captures'][0].update(variant='edge'),
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
            rows[0]['variant'] = 'edge'; control.analysis.write_csv(combined, rows)
            good['output_sha256'] = control.native.sha(combined); control.write_json(root / 'paired.json', good)
            with self.assertRaisesRegex(ValueError, 'concatenation'): experiment.load(root / 'paired.json')

    def test_provenance_source_helpers_objects_flags_and_parent_drift(self):
        with fixture() as (root, args, parent):
            record = control.analysis.read_json(args.edge_build_record)
            for path in (args.edge_binary, args.protocol, args.manifest, args.parent_freeze,
                         root / 'benchmark/retention_control.cpp', root / 'verifier/verifier_v2.cpp',
                         root / 'benchmark/build_edge_verifier.py', Path(record['object_paths']['verifier/verifier_v2.o']),
                         Path(record['main_object'])):
                before = path.read_bytes(); path.write_bytes(before + b'drift'); factory = Factory()
                with self.subTest(path=path), self.assertRaises(ValueError): capture(root, args, factory=factory)
                self.assertFalse(factory.children); path.write_bytes(before)
            helpers = control.helpers(); changed = dict(helpers); changed[next(iter(changed))] = '0' * 64
            with mock.patch.object(control, 'helpers', return_value=changed), self.assertRaisesRegex(ValueError, 'control helpers changed'):
                experiment.check_freeze(args.freeze)
            mutations = {
                'NDEBUG': lambda x: x['build_commands'][0].insert(3, '-DNDEBUG'),
                'stats': lambda x: x['common_compile_flags'].append('-DKKT_ENABLE_WORK_STATS'),
                'wrong dispatch': lambda x: x['build_commands'][8].remove('-DKKT_EXPERIMENT_EDGE_VIEW'),
                'wrong link': lambda x: x['link_command'].insert(-2, 'foreign.o'),
                'wrong shared object': lambda x: x['object_sha256'].update({'verifier/verifier_v2.o': '0'*64}),
                'wrong sdk': lambda x: x.update(sdk='other'),
                'wrong parent': lambda x: x.update(parent_control_freeze_sha256='0'*64),
            }
            for name, mutate in mutations.items():
                changed = copy.deepcopy(record); mutate(changed); control.write_json(args.edge_build_record, changed)
                with self.subTest(name=name), self.assertRaises(ValueError):
                    experiment.build_record(args.edge_build_record, args.edge_binary, root, parent, args.parent_freeze, 'edge')
            control.write_json(args.edge_build_record, record)
            with self.assertRaisesRegex(ValueError, 'released'):
                experiment.capture(argparse.Namespace(freeze=args.freeze, output=root/'unreleased.csv', released=False))

    def test_clock_flags_preserved_and_pair_median_pools_twelve_trials(self):
        with fixture() as (root, args, parent):
            info, _ = capture(root, args, factory=Factory(mutation=lambda rows: rows[0].update(elapsed_ns=2_000_000_000)))
            self.assertEqual(info['flagged_calls'], 40)
            rows = experiment.load(root/'paired.json')[2]
            self.assertEqual(len(rows), 1680)
            self.assertTrue(all(not row['excluded'] for row in info['call_diagnostics']))
            case = rows[0]['case_id']
            values = dict(zip(experiment.GRAPH_SEEDS, ([1,2,10,20,30,40], [3,4,5,6,7,8])))
            for row in rows:
                if row['case_id'] == case and row['phase'] == 'timed' and row['algorithm'] == 'kkt':
                    value = values[row['graph_seed']][row['repetition']] if row['variant'] == 'edge' else 1
                    row.update(elapsed_ns=value*100, process_cpu_elapsed_ns=value*100)
            compared = experiment.aggregate(rows)['variant_comparisons']
            self.assertTrue(all(row['median_paired_ratio'] == 6.5 for row in compared if row['case_id'] == case and row['algorithm'] == 'kkt'))
            rows = [row for row in rows if not (row['case_id'] == case and row['phase'] == 'timed' and row['algorithm'] == 'kkt' and row['variant'] == 'edge' and row['repetition'] == 0)]
            with self.assertRaises(ValueError): experiment.aggregate(rows)

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
