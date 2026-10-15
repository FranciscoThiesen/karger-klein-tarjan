#!/usr/bin/env python3
"""Disposable mocked paired-six capture; no native build or execution."""
import argparse
import contextlib
import copy
import csv
from fractions import Fraction
import json
import math
from pathlib import Path
import threading
import os
import shutil
import signal
import statistics
import unittest
from unittest import mock

import run_eighth_sampling as experiment
import test_compressed_queries as parent_tests
import test_retention_control as control_tests

control = experiment.control
old = control_tests.old_tests
EXPECTED = (('leaf_hierarchy4',65536,32,0),('leaf_shuffled4',65536,32,0),
            ('leaf_hierarchy4',1048576,32,0),('leaf_shuffled4',1048576,32,0),
            ('gnm_random',4096,16,0),('gnm_random',1048576,16,0))
GRAPHS, SAMPLERS = (15000011,15000031),(2609,2617)
ALGORITHMS = ('kkt','compacting_boruvka','multigraph_boruvka','kruskal','prim','boruvka')


@contextlib.contextmanager
def fixture():
    with parent_tests.fixture() as (parent_root, parent_args, _):
        parent = control.analysis.read_json(parent_args.freeze)
        root = parent_root / 'eighth-checkout'; root.mkdir()
        for name in (*parent['source_sha256'], *experiment.parent_engine.RECIPES):
            path = root / name; path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(parent_root / name, path)
        for name in experiment.CHANGED_NATIVE:
            path = root / name; path.write_text(path.read_text() + 'synthetic eighth optimization\n')
        for name in experiment.NEW_NATIVE:
            path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('synthetic new source\n')
        overlay={name:control.native.sha(root/name) for name in experiment.OVERLAY}
        (root / 'benchmark/build_eighth_sampling.py').write_text('synthetic build recipe; never executed\n')
        inherited = parent['variants']['compressed']['build']['record']
        commands, objects, binaries, main, links = experiment.expected_commands(root, inherited['sdk'])
        for variant in experiment.VARIANTS:
            for name, value in objects[variant].items():
                path = Path(value); path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('synthetic ' + name + (variant if name == 'kkt/kkt.o' else 'shared'))
        Path(main).parent.mkdir(parents=True, exist_ok=True); Path(main).write_text('synthetic shared main')
        manifest = root / 'eighth-manifest.csv'
        with manifest.open('w', newline='') as stream:
            writer = csv.writer(stream); writer.writerow(control.native.base.MANIFEST_FIELDS)
            writer.writerows(EXPECTED)
        protocol = root / 'EIGHTH.md'; protocol.write_text('Synthetic prospective eighth experiment.\n')
        args = argparse.Namespace(parent_freeze=parent_args.freeze, manifest=manifest, protocol=protocol, freeze=root / 'eighth-freeze.json')
        for variant in experiment.VARIANTS:
            binary = Path(binaries[variant]); binary.parent.mkdir(parents=True, exist_ok=True); binary.write_text('synthetic binary ' + variant)
            log = root / (variant + '.build.log'); log.write_text('synthetic build log')
            record = dict(schema='eighth_sampling_build_v1', profile='timing-build', variant=variant,
                          working_directory=str(root), source_sha256=control.native.source_inventory(root),
                          build_recipe_sha256={name: control.native.sha(root / name) for name in experiment.RECIPES},
                          binary=str(binary), binary_sha256=control.native.sha(binary), binary_profile=parent['variants']['compressed']['binary_profile'],
                          compiler=inherited['compiler'], compiler_command=inherited['compiler_command'],
                          sdk=inherited['sdk'], common_compile_flags=experiment.FLAGS,
                          build_command=['python3', '-B', str(root / 'benchmark/build_eighth_sampling.py'), '--profile', 'timing-build', '--output', str(root), '--parent-freeze', str(parent_args.freeze)],
                          build_commands=commands, object_paths=objects[variant], object_sha256={name: control.native.sha(Path(value)) for name, value in objects[variant].items()},
                          main_object=main, main_object_sha256=control.native.sha(Path(main)), link_command=links[variant],
                          build_exit_status=0, build_log=str(log), build_log_sha256=control.native.sha(log),
                          parent_compressed_freeze=str(parent_args.freeze), parent_compressed_freeze_sha256=control.native.sha(parent_args.freeze),
                          role='timing_never_executed',source='benchmark/retention_control.cpp',
                          seven_non_kkt_objects_identical_by_construction=True,compressed_queries_fixed=True,
                          public_scalar_sampling_fixed=True,reference_note=experiment.REFERENCE_NOTE,
                          verifier_policy='compressed',source_overlay_sha256=overlay,
                          sampling_policy=variant,private_acceptance_mask=1 if variant=='half' else 7,
                          sampling_words_per_visited_edge=1)
            record['executables']=[{name:record[name] for name in ('source','main_object','main_object_sha256',
                'binary','binary_sha256','binary_profile','link_command','role','verifier_policy',
                'sampling_policy','private_acceptance_mask','sampling_words_per_visited_edge')}]
            path = root / (variant + '-build.json'); control.write_json(path, record)
            setattr(args, variant + '_binary', binary); setattr(args, variant + '_build_record', path)
        os.chdir(root)
        try:
            with mock.patch.object(experiment,'PARENT_SHA256',control.native.sha(parent_args.freeze)), \
                 mock.patch.object(experiment,'OVERLAY',overlay):
                experiment.preflight(args)
                yield root, args, parent
        finally:
            os.chdir(parent_root)


class Factory(control_tests.Factory):
    def __call__(self, argv, **kwargs):
        rows = control_tests.rows_for(argv)
        for row in rows:
            row['input_fingerprint'] = 10 if row['family'] == 'leaf_shuffled4' else 9
        if '/eighth/' in argv[2]:
            cpu = 0; utc = 946684800_000000000
            for row in rows:
                duration = 800 if row['algorithm'] == 'kkt' else row['elapsed_ns']
                row.update(elapsed_ns=duration, process_cpu_start_ns=cpu, process_cpu_end_ns=cpu + duration,
                           process_cpu_elapsed_ns=duration, utc_start_ns=utc, utc_end_ns=utc + duration)
                cpu += duration + 10; utc += duration + 10
        certificate = {field: rows[0][field] for field in control.native.CERTIFICATE_FIELDS}
        if getattr(self,'false_certificate',False):certificate['validation']='failed'
        if not getattr(self,'omit_certificate',False):
            kwargs['stderr'].write(control.native.CERTIFICATE_PREFIX + json.dumps(certificate) + '\n')
        if self.mutation: self.mutation(rows)
        writer = csv.DictWriter(kwargs['stdout'],fieldnames=getattr(self,'fields',control.FIELDS),extrasaction='ignore')
        writer.writeheader();writer.writerows(rows)
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


class EighthSamplingTests(unittest.TestCase):
    def test_cleanup_exception_second_signal_and_prior_unknown_fail_closed(self):
        prior=signal.getsignal(signal.SIGTERM)
        for mode in ('raises','second SIGTERM ignored'):
            with self.subTest(mode=mode),fixture() as (root,args,parent):
                factory=Factory(status=-11)
                observed=[]
                def cleanup(process,sampler):
                    handler=signal.getsignal(signal.SIGTERM);observed.append(handler)
                    self.assertEqual(handler,signal.SIG_IGN)
                    # Emulate signal delivery at the Python handler boundary;
                    # never send a real signal or launch a real native process.
                    if callable(handler):handler(signal.SIGTERM,None)
                    if mode=='raises':raise KeyboardInterrupt('synthetic cleanup interruption')
                    return dict(native_exit_known=True,group_exit_known=True,
                                native_process_may_still_be_running=False)
                with mock.patch.object(control.monitor,'bounded_terminate',side_effect=cleanup),self.assertRaises(ValueError):
                    capture(root,args,factory=factory)
                failed=control.analysis.read_json(root/'paired.json')
                self.assertEqual(len(factory.children),1);self.assertEqual(len(observed),1)
                self.assertEqual(failed['validation'],'failed');self.assertEqual(len(failed['cleanup']),1)
                self.assertEqual(failed['native_process_may_still_be_running'],mode=='raises')
                if mode=='raises':self.assertIn('synthetic cleanup interruption',failed['cleanup'][0]['error'])
                self.assertEqual(signal.getsignal(signal.SIGTERM),prior)
        info=dict(cleanup=[],native_process_may_still_be_running=True)
        with mock.patch.object(control.monitor,'bounded_terminate',return_value=dict(
                native_exit_known=True,group_exit_known=True,native_process_may_still_be_running=False)):
            experiment.cleanup_owned_group(None,None,info)
        self.assertTrue(info['native_process_may_still_be_running'])
        self.assertEqual(signal.getsignal(signal.SIGTERM),prior)

    def test_independent_twelve_command_recipe_and_shared_compressed_verifier(self):
        with fixture() as (root,args,parent):
            records=[control.analysis.read_json(getattr(args,v+'_build_record')) for v in ('half','eighth')]
            sdk=records[0]['sdk'];commands=records[0]['build_commands']
            flags=['-std=c++17','-O3','-Wall','-Wextra','-march=native',
                   '-DKKT_EXPERIMENT_RETAIN_PARALLEL','-DKKT_EXPERIMENT_EDGE_VIEW']
            base=['/usr/bin/arch','-arm64','/usr/bin/clang++','-isysroot',sdk,*flags,'-I.']
            self.assertEqual(experiment.FLAGS,flags);self.assertEqual(len(commands),12)
            build=root/'.build/eighth-sampling/timing-build'
            shared=('boruvka/boruvka.cpp','kruskal/kruskal.cpp','prim/prim.cpp','lca/lca.cpp',
                    'union_find/union_find.cpp','graph_utils/graph_utils.cpp','verifier/verifier_v2.cpp')
            for i,source in enumerate(shared):
                extra=['-DKKT_EXPERIMENT_COMPRESSED_QUERIES'] if i==6 else []
                self.assertEqual(commands[i],base+extra+['-c',source,'-o',str(build/'shared'/source.replace('.cpp','.o'))])
                name=source.replace('.cpp','.o')
                self.assertEqual(records[0]['object_paths'][name],records[1]['object_paths'][name])
                self.assertEqual(records[0]['object_sha256'][name],records[1]['object_sha256'][name])
            for i,v in ((7,'half'),(8,'eighth')):
                extra=['-DKKT_EXPERIMENT_EIGHTH_SAMPLING'] if v=='eighth' else []
                self.assertEqual(commands[i],base+extra+['-c','kkt/kkt.cpp','-o',str(build/v/'kkt/kkt.o')])
            self.assertEqual(commands[9],base+['-c','benchmark/retention_control.cpp','-o',str(build/'shared/benchmark/retention_control.o')])
            for i,v in ((10,'half'),(11,'eighth')):
                link=base+[
                    str(build/'shared/boruvka/boruvka.o'),str(build/'shared/kruskal/kruskal.o'),
                    str(build/'shared/prim/prim.o'),str(build/'shared/lca/lca.o'),
                    str(build/'shared/union_find/union_find.o'),str(build/'shared/graph_utils/graph_utils.o'),
                    str(build/'shared/verifier/verifier_v2.o'),str(build/v/'kkt/kkt.o'),
                    str(build/'shared/benchmark/retention_control.o'),'-L'+sdk+'/usr/lib',
                    '-Wl,-stack_size,0x20000000','-o',str(root/'bin/eighth-sampling/timing-build'/v/'retention_control')]
                self.assertEqual(commands[i],link);self.assertEqual(records[i-10]['link_command'],link)
            self.assertNotEqual(records[0]['object_sha256']['kkt/kkt.o'],records[1]['object_sha256']['kkt/kkt.o'])
            for variant,record in zip(('half','eighth'),records):
                for descriptor in (record,record['executables'][0]):
                    self.assertEqual(descriptor['sampling_policy'],variant)
                    self.assertEqual(descriptor['private_acceptance_mask'],1 if variant=='half' else 7)
                    self.assertIs(type(descriptor['private_acceptance_mask']),int)
                    self.assertEqual(descriptor['sampling_words_per_visited_edge'],1)
                    self.assertIs(type(descriptor['sampling_words_per_visited_edge']),int)

    def test_local_seeds_and_parent_helper_restore_on_failure(self):
        original = control.GRAPH_SEEDS, control.SAMPLING_SEED
        with fixture() as (root,args,parent):
            spec=next(iter(experiment.cases_from_manifest(args.manifest).values()))
            for seed in SAMPLERS:
                identity=dict(case_id=spec['case_id'],graph_seed=15000011,kkt_seed=seed)
                with mock.patch.object(control,'command',side_effect=AssertionError('parent command called')):
                    argv=experiment.command(args.half_binary,spec,identity)
                self.assertEqual(argv[-6:],['--kkt-seed',str(seed),'--repetitions','6','--warmups','1'])
                raw=root/'local.csv';rows=control_tests.rows_for(['/usr/bin/time','-l',*argv])
                with raw.open('w',newline='') as stream:
                    writer=csv.DictWriter(stream,fieldnames=control.FIELDS);writer.writeheader();writer.writerows(rows)
                with mock.patch.object(control,'check_rows',side_effect=AssertionError('parent row validator called')):
                    self.assertEqual(len(experiment.check_rows(raw,spec,15000011,seed)[0]),42)
            helper=experiment.parent_engine.helpers
            with mock.patch.object(experiment.parent_engine,'check_freeze',side_effect=RuntimeError('synthetic')):
                with self.assertRaisesRegex(RuntimeError,'synthetic'):experiment.parent_record(args.parent_freeze)
            self.assertIs(experiment.parent_engine.helpers,helper)
            with self.assertRaisesRegex(ValueError,'seed'):
                experiment.command(args.half_binary,spec,{**identity,'kkt_seed':1801})
        self.assertEqual((control.GRAPH_SEEDS, control.SAMPLING_SEED), original)

    def test_full_schedule_all_ratios_and_power(self):
        with fixture() as (root, args, parent):
            info, factory = capture(root, args)
            self.assertEqual((len(factory.children), info['checked_rows'], info['checked_timed_rows'], info['checked_warmup_rows']), (48, 2016, 1728, 288))
            cases=[f'{f}_n{n}_d{d}_p{p}' for f,n,d,p in EXPECTED]
            expected_schedule=[dict(variant=v,case_id=c,graph_seed=g,kkt_seed=s)
                for gi,g in enumerate((15000011,15000031)) for si,s in enumerate((2609,2617))
                for c in (cases if gi==0 else list(reversed(cases)))
                for v in (('half','eighth') if (gi+si)%2==0 else ('eighth','half'))]
            self.assertEqual([{key: item[key] for key in ('variant','case_id','graph_seed','kkt_seed')}
                              for item in info['captures']], expected_schedule)
            for gi in range(2):
                for si in range(2):
                    block = info['captures'][gi*24+si*12:gi*24+si*12+12]
                    variants = ['half','eighth'] if (gi+si)%2 == 0 else ['eighth','half']
                    self.assertEqual([item['variant'] for item in block], variants*6)
            loaded = experiment.load(root / 'paired.json'); tables = experiment.aggregate(loaded[2])
            self.assertEqual({key: len(value) for key, value in tables.items()}, experiment.TABLE_COUNTS)
            self.assertEqual(experiment.DECLARED_CASES,EXPECTED)
            self.assertEqual(len(experiment.crossovers(tables,loaded[1])),30)
            for item in info['captures']:
                native_rows=[row for _,row in control.native.base.read_csv(Path(item['csv']),control.FIELDS)]
                for algorithm in ALGORITHMS:
                    self.assertEqual(sorted(int(row['order']) for row in native_rows
                        if row['phase']=='timed' and row['algorithm']==algorithm),list(range(6)))
            self.assertEqual({row['algorithm'] for row in tables['variant_comparisons']}, set(control.ALGORITHMS))
            for row in tables['variant_pairs']:
                self.assertEqual(row['eighth_over_half'], row['eighth_ns'] / row['half_ns'])
            self.assertTrue(all(row['median_paired_ratio'] == (.8 if row['algorithm'] == 'kkt' else 1) and row['trials'] == 24 for row in tables['variant_comparisons']))
            for row in tables['comparisons']:
                scale = 1 if row['variant'] == 'half' else .8
                self.assertAlmostEqual(row['median_paired_ratio'], scale / (1 + control.ALGORITHMS.index(row['competitor'])))
            power = root / 'power.log'
            power.write_text('2000-01-01 00:00:00 +0000 Sleep Entering Sleep state\n2000-01-01 00:00:00 +0000 Wake Requests request=Maintenance\n2000-01-01 00:00:01 +0000 Wake Wake from Deep Idle\n')
            experiment.analyze(argparse.Namespace(capture=root / 'paired.json', output_dir=root / 'analysis', power_log=power))
            self.assertEqual(control.analysis.read_json(root / 'analysis/provenance.json')['power_audit']['logged_overlap_calls'], 2016)
            with self.assertRaisesRegex(ValueError, 'overwrite'): capture(root, args)

    def test_schedule_metadata_native_exit_and_identity_fail_closed(self):
        with fixture() as (root, args, parent):
            good, _ = capture(root, args)
            mutations = {
                'missing child': lambda x: x['captures'].pop(),
                'wrong variant': lambda x: x['captures'][0].update(variant='eighth'),
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
            rows[0]['variant'] = 'eighth'; control.analysis.write_csv(combined, rows)
            good['output_sha256'] = control.native.sha(combined); control.write_json(root / 'paired.json', good)
            with self.assertRaisesRegex(ValueError, 'concatenation'): experiment.load(root / 'paired.json')

    def test_provenance_source_helpers_objects_flags_and_parent_drift(self):
        with fixture() as (root, args, parent):
            record = control.analysis.read_json(args.eighth_build_record)
            for path in (args.eighth_binary, args.protocol, args.manifest, args.parent_freeze,
                         root / 'benchmark/retention_control.cpp', root / 'verifier/verifier_v2.cpp',
                         root / 'benchmark/build_eighth_sampling.py', Path(record['object_paths']['verifier/verifier_v2.o']),
                         Path(record['main_object'])):
                before = path.read_bytes(); path.write_bytes(before + b'drift'); factory = Factory()
                with self.subTest(path=path), self.assertRaises(ValueError): capture(root, args, factory=factory)
                self.assertFalse(factory.children); path.write_bytes(before)
            helpers = control.helpers(); changed = dict(helpers); changed[next(iter(changed))] = '0' * 64
            with mock.patch.object(control, 'helpers', return_value=changed), self.assertRaisesRegex(ValueError, 'compressed-query helper copies changed'):
                experiment.check_freeze(args.freeze)
            mutations = {
                'NDEBUG': lambda x: x['build_commands'][0].insert(3, '-DNDEBUG'),
                'stats': lambda x: x['common_compile_flags'].append('-DKKT_ENABLE_WORK_STATS'),
                'wrong dispatch': lambda x: x['build_commands'][8].remove('-DKKT_EXPERIMENT_EIGHTH_SAMPLING'),
                'wrong link': lambda x: x['link_command'].insert(-2, 'foreign.o'),
                'wrong shared object': lambda x: x['object_sha256'].update({'verifier/verifier_v2.o': '0'*64}),
                'wrong sdk': lambda x: x.update(sdk='other'),
                'wrong parent': lambda x: x.update(parent_compressed_freeze_sha256='0'*64),
                'compression absent': lambda x:x['build_commands'][6].remove('-DKKT_EXPERIMENT_COMPRESSED_QUERIES'),
                'compression on KKT': lambda x:x['build_commands'][7].insert(3,'-DKKT_EXPERIMENT_COMPRESSED_QUERIES'),
                'compression metadata': lambda x:x.update(compressed_queries_fixed=False),
                'verifier policy': lambda x:x.update(verifier_policy='uncompressed'),
                'overlay metadata': lambda x:x.update(source_overlay_sha256={}),
                'public sampling metadata': lambda x:x.update(public_scalar_sampling_fixed=False),
                'shared objects metadata': lambda x:x.update(seven_non_kkt_objects_identical_by_construction=False),
                'reference note': lambda x:x.update(reference_note='historical parent'),
                'executed timing role': lambda x:x.update(role='correctness'),
                'descriptor mismatch': lambda x:x['executables'][0].update(role='correctness'),
                'wrong predicate': lambda x:x.update(sampling_policy='half'),
                'wrong mask': lambda x:x.update(private_acceptance_mask=1),
                'mask float': lambda x:x.update(private_acceptance_mask=7.0),
                'words bool': lambda x:x.update(sampling_words_per_visited_edge=True),
                'words float': lambda x:x.update(sampling_words_per_visited_edge=1.0),
                'missing predicate': lambda x:x.pop('sampling_policy'),
                'descriptor predicate': lambda x:x['executables'][0].update(sampling_policy='half'),
                'descriptor mask float': lambda x:x['executables'][0].update(private_acceptance_mask=7.0),
                'descriptor words bool': lambda x:x['executables'][0].update(sampling_words_per_visited_edge=True),
            }
            for name, mutate in mutations.items():
                changed = copy.deepcopy(record); mutate(changed); control.write_json(args.eighth_build_record, changed)
                with self.subTest(name=name), self.assertRaises(ValueError):
                    experiment.build_record(args.eighth_build_record, args.eighth_binary, root, parent, args.parent_freeze, 'eighth')
            control.write_json(args.eighth_build_record, record)
            with self.assertRaisesRegex(ValueError, 'released'):
                experiment.capture(argparse.Namespace(freeze=args.freeze, output=root/'unreleased.csv', released=False))

    def test_clock_flags_preserved_and_pair_median_pools_twenty_four_trials(self):
        with fixture() as (root, args, parent):
            info, _ = capture(root, args, factory=Factory(mutation=lambda rows: rows[0].update(elapsed_ns=2_000_000_000)))
            self.assertEqual(info['flagged_calls'], 48)
            rows = experiment.load(root/'paired.json')[2]
            self.assertEqual(len(rows), 2016)
            self.assertTrue(all(not row['excluded'] for row in info['call_diagnostics']))
            case = rows[0]['case_id']
            values = dict(zip(experiment.GRAPH_SEEDS, ([1,2,10,20,30,40], [3,4,5,6,7,8])))
            for row in rows:
                if row['case_id'] == case and row['phase'] == 'timed' and row['algorithm'] == 'kkt':
                    value = values[row['graph_seed']][row['repetition']] if row['variant'] == 'eighth' else 1
                    row.update(elapsed_ns=value*100, process_cpu_elapsed_ns=value*100)
            compared = experiment.aggregate(rows)['variant_comparisons']
            self.assertTrue(all(row['median_paired_ratio'] == 6.5 for row in compared if row['case_id'] == case and row['algorithm'] == 'kkt'))
            rows = [row for row in rows if not (row['case_id'] == case and row['phase'] == 'timed' and row['algorithm'] == 'kkt' and row['variant'] == 'eighth' and row['repetition'] == 0)]
            with self.assertRaises(ValueError): experiment.aggregate(rows)

    def test_twins_sampler_marginals_manifest_and_parent_scope(self):
        with fixture() as (root, args, parent):
            info, _ = capture(root, args)
            rows = experiment.load(root / 'paired.json')[2]
            tables = experiment.aggregate(rows)
            for prefix, trials in (('realization_', 6), ('graph_', 12), ('sampling_', 12)):
                for name in ('comparisons', 'summary', 'variant_comparisons'):
                    self.assertTrue(all(row['trials'] == trials for row in tables[prefix + name]))
            for field, message in (('topology_fingerprint', 'different topology'), ('input_fingerprint', 'identical weighted')):
                changed = copy.deepcopy(rows)
                for row in changed:
                    if row['family'] == 'leaf_shuffled4':
                        row[field] = 999 if field == 'topology_fingerprint' else 9
                with self.subTest(field=field), self.assertRaisesRegex(ValueError, message):
                    experiment.check_fingerprints(changed, complete=True)
            changed = copy.deepcopy(rows)
            for row in changed:
                if row['kkt_seed'] == experiment.SAMPLING_SEEDS[1]: row['input_fingerprint'] += 1
            with self.assertRaisesRegex(ValueError, 'fingerprints'): experiment.check_fingerprints(changed)
            # Consistently change one child's certificate and CSV so local checks
            # pass; cross-sampler graph identity must still reject it.
            index = next(i for i, child in enumerate(info['captures']) if child['kkt_seed'] == experiment.SAMPLING_SEEDS[1])
            item = info['captures'][index]; raw, log = Path(item['csv']), Path(item['log'])
            saved_raw, saved_log = raw.read_bytes(), log.read_bytes()
            child = [row for _, row in control.native.base.read_csv(raw, control.FIELDS)]
            for row in child: row['input_fingerprint'] = '99'
            control.analysis.write_csv(raw, child)
            certificate = {field: (int(child[0][field]) if field not in ('case_id','validation') else child[0][field])
                           for field in control.native.CERTIFICATE_FIELDS}
            log.write_text(control.native.CERTIFICATE_PREFIX + json.dumps(certificate) + '\n')
            altered = copy.deepcopy(info); altered['captures'][index].update(certificate=certificate,
                output_sha256=control.native.sha(raw), log_sha256=control.native.sha(log))
            control.write_json(root/'paired.json', altered)
            with self.assertRaisesRegex(ValueError, 'fingerprints'): experiment.load(root/'paired.json')
            raw.write_bytes(saved_raw); log.write_bytes(saved_log); control.write_json(root/'paired.json', info)
            before = args.manifest.read_bytes(); args.manifest.write_bytes(before.replace(b'65536', b'131072', 1))
            with self.assertRaisesRegex(ValueError, 'six eighth'): experiment.cases_from_manifest(args.manifest)
            args.manifest.write_bytes(before)
            original = experiment.parent_engine.helpers
            with mock.patch.object(experiment.parent_engine, 'check_freeze', side_effect=RuntimeError('parent failure')):
                with self.assertRaisesRegex(RuntimeError, 'parent failure'): experiment.parent_record(args.parent_freeze)
            self.assertIs(experiment.parent_engine.helpers, original)
            self.assertEqual(len(experiment.crossovers(tables, experiment.cases_from_manifest(args.manifest))), 30)

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

    def test_invalid_native_rows_and_certificates_stop_after_one_child(self):
        for name,mutation in (('missing timed',lambda rows:rows.pop()),
                              ('missing warmup',lambda rows:rows.pop(0)),
                              ('duplicate',lambda rows:rows.__setitem__(-1,dict(rows[-2]))),
                              ('reordered',lambda rows:rows.reverse()),
                              ('bad clock',lambda rows:rows[-1].update(process_cpu_end_ns=0)),
                              ('bad validation',lambda rows:rows[-1].update(validation='failed')),
                              ('missing column',None),('absent certificate',None),('false certificate',None)):
            with self.subTest(name=name),fixture() as (root,args,parent):
                factory=Factory(mutation=mutation)
                if name=='missing column':factory.fields=[field for field in control.FIELDS if field!='validation']
                if name=='absent certificate':factory.omit_certificate=True
                if name=='false certificate':factory.false_certificate=True
                with self.assertRaises(ValueError):capture(root,args,factory=factory)
                self.assertEqual(len(factory.children),1)
                failed=control.analysis.read_json(root/'paired.json')
                self.assertEqual(failed['validation'],'failed');self.assertIn('error',failed)
                self.assertFalse(failed['native_process_may_still_be_running'])
                child=failed['captures'][0]
                self.assertEqual(child['group_exit_verification']['members'],[])
                self.assertTrue(Path(child['csv']).exists());self.assertTrue(Path(child['log']).exists())

    @staticmethod
    def arithmetic_rows():
        rows=[]
        for ci,(family,n,d,p) in enumerate(EXPECTED):
            for vi,variant in enumerate(('half','eighth')):
                for gi,graph in enumerate(GRAPHS):
                    for si,seed in enumerate(SAMPLERS):
                        for rep in range(6):
                            for ai,algorithm in enumerate(ALGORITHMS):
                                rows.append(dict(variant=variant,case_id=f'{family}_n{n}_d{d}_p{p}',
                                    family=family,n=n,m=n*d,density=d,intrusion_per_mille=p,
                                    graph_seed=graph,kkt_seed=seed,repetition=rep,algorithm=algorithm,phase='timed',
                                    input_fingerprint=10+ci+gi,topology_fingerprint=20+ci+gi,
                                    elapsed_ns=1000003+10007*ci+2113*gi+1231*si+421*rep+113*ai+
                                        vi*(4001+73*ci+41*gi+29*si+17*rep+13*ai+7*rep*ai),
                                    process_cpu_elapsed_ns=600001+7013*ci+1747*gi+997*si+307*rep+89*ai+
                                        vi*(2039+47*ci+37*gi+23*si+19*rep+11*ai+5*rep*ai)))
        return rows

    def test_all_raw_pair_identities_and_four_summary_scopes(self):
        rows=self.arithmetic_rows();tables=experiment.aggregate(rows)
        self.assertEqual({name:len(table) for name,table in tables.items()},
            {'paired_ratios':2880,'comparisons':120,'realization_comparisons':480,
             'graph_comparisons':240,'sampling_comparisons':240,'summary':144,'realization_summary':576,
             'graph_summary':288,'sampling_summary':288,'variant_pairs':1728,'variant_comparisons':72,
             'realization_variant_comparisons':288,'graph_variant_comparisons':144,'sampling_variant_comparisons':144})
        cases=[f'{f}_n{n}_d{d}_p{p}' for f,n,d,p in EXPECTED]
        raw={(r['variant'],r['case_id'],r['graph_seed'],r['kkt_seed'],r['repetition'],r['algorithm']):r for r in rows}
        identities={(v,c,g,s,r,a) for v in ('half','eighth') for c in cases
                    for g in GRAPHS for s in SAMPLERS for r in range(6) for a in ALGORITHMS}
        self.assertEqual(len(rows),1728);self.assertEqual(set(raw),identities);self.assertEqual(len(raw),len(rows))
        vp,wp={},{};collections={name:{} for name in ('summary','comparisons','variant_comparisons')}
        def add(name,key,g,s,value):collections[name].setdefault(key,{}).setdefault((g,s),[]).append(value)
        for c in cases:
            for g in GRAPHS:
                for s in SAMPLERS:
                    for rep in range(6):
                        for metric,field in (('wall','elapsed_ns'),('cpu','process_cpu_elapsed_ns')):
                            for a in ALGORITHMS:
                                half=raw[('half',c,g,s,rep,a)][field];eighth=raw[('eighth',c,g,s,rep,a)][field]
                                ratio=Fraction(eighth,half);vp[(c,g,s,rep,a,metric)]=(half,eighth,ratio)
                                add('variant_comparisons',(c,a,metric),g,s,ratio)
                                for v in ('half','eighth'):
                                    value=raw[(v,c,g,s,rep,a)][field];add('summary',(v,c,a,metric),g,s,value)
                                    if a!='kkt':
                                        numerator=raw[(v,c,g,s,rep,'kkt')][field];ratio=Fraction(numerator,value)
                                        wp[(v,c,g,s,rep,a,metric)]=(numerator,value,ratio)
                                        add('comparisons',(v,c,a,metric),g,s,ratio)
        def check_pairs(actual,expected,fields,first,second,ratio):
            indexed={tuple(row[k] for k in fields):row for row in actual}
            self.assertEqual(len(indexed),len(actual));self.assertEqual(set(indexed),set(expected))
            for key,(a,b,value) in expected.items():
                self.assertEqual((indexed[key][first],indexed[key][second]),(a,b))
                self.assertEqual(indexed[key][ratio],float(value))
        for name,expected,fields,first,second,ratio in (
            ('variant_pairs',vp,('case_id','graph_seed','kkt_seed','repetition','algorithm','metric'),'half_ns','eighth_ns','eighth_over_half'),
            ('paired_ratios',wp,('variant','case_id','graph_seed','kkt_seed','repetition','competitor','metric'),'kkt_ns','competitor_ns','kkt_over_competitor')):
            check_pairs(tables[name],expected,fields,first,second,ratio)
            for error in ('duplicate','missing','opposite clock'):
                damaged=copy.deepcopy(tables[name])
                if error=='duplicate':damaged[-1]=copy.deepcopy(damaged[0])
                elif error=='missing':damaged.pop()
                else:
                    key=tuple(damaged[0][k] for k in fields);other=expected[(*key[:-1],'cpu' if key[-1]=='wall' else 'wall')]
                    damaged[0][first],damaged[0][second]=other[:2];damaged[0][ratio]=float(other[2])
                with self.subTest(name=name,error=error),self.assertRaises(AssertionError):
                    check_pairs(damaged,expected,fields,first,second,ratio)
        for name,groups in collections.items():
            fields=('case_id','algorithm','metric') if name=='variant_comparisons' else (
                'variant','case_id','competitor' if name=='comparisons' else 'algorithm','metric')
            ratio=name!='summary';value_field='median_paired_ratio' if ratio else 'median_ns'
            for prefix,extra in (('',()),('realization_',('graph_seed','kkt_seed')),
                                 ('graph_',('graph_seed',)),('sampling_',('kkt_seed',))):
                expected={}
                for key,realizations in groups.items():
                    self.assertEqual(set(realizations),{(g,s) for g in GRAPHS for s in SAMPLERS})
                    self.assertTrue(all(len(values)==6 for values in realizations.values()))
                    for (g,s),values in realizations.items():
                        suffix=() if not prefix else (g,s) if prefix=='realization_' else (g,) if prefix=='graph_' else (s,)
                        expected.setdefault((*key,*suffix),[]).extend(values)
                actual=tables[prefix+name];indexed={tuple(r[k] for k in (*fields,*extra)):r for r in actual}
                self.assertEqual(len(actual),len(indexed));self.assertEqual(set(indexed),set(expected))
                for key,values in expected.items():
                    row=indexed[key];median=float(statistics.median(values))
                    self.assertAlmostEqual(row[value_field],median,delta=2*math.ulp(median))
                    self.assertEqual((row['trial_min'],row['trial_max'],row['trials']),
                                     (float(min(values)),float(max(values)),len(values)))
                    if ratio:self.assertEqual(row['individual_wins'],sum(v<1 for v in values))

    def test_exact_crossover_all_four_realizations_both_clocks(self):
        cases={f'{f}_n{n}_d{d}_p{p}':dict(family=f,n=n,density=d,intrusion_per_mille=p) for f,n,d,p in EXPECTED}
        base=experiment.aggregate(self.arithmetic_rows());target=('eighth','leaf_hierarchy4','multigraph_boruvka')
        def evaluate(low,high,change=None):
            tables=copy.deepcopy(base)
            for row in tables['paired_ratios']:
                if tuple(row[k] for k in ('variant','family','competitor'))==target:
                    value=low if row['n']==65536 else high
                    if change:value=change(row,value)
                    row['kkt_ns'],row['competitor_ns']=value.numerator,value.denominator
            out=experiment.crossovers(tables,cases);self.assertEqual(len(out),30)
            return next(row for row in out if tuple(row[k] for k in ('variant','family','competitor'))==target)
        loss,strong,tie=Fraction(11,10),Fraction(9,10),Fraction(1)
        self.assertTrue(evaluate(loss,strong)['strong_crossover'])
        self.assertFalse(evaluate(tie,strong)['strong_crossover'])
        self.assertFalse(evaluate(strong,strong)['strong_crossover'])
        self.assertFalse(evaluate(loss,Fraction(91,100))['strong_crossover'])
        self.assertEqual(evaluate(strong,loss)['large_state'],'loss')
        for g in GRAPHS:
            for s in SAMPLERS:
                for metric in ('wall','cpu'):
                    changed=evaluate(loss,strong,lambda row,value:
                        Fraction(900000000000000001,10**18) if row['n']==1048576 and
                        (row['graph_seed'],row['kkt_seed'],row['metric'])==(g,s,metric) else value)
                    self.assertFalse(changed['strong_crossover'])
        for error in ('duplicate','missing','bool endpoint'):
            damaged=copy.deepcopy(base)
            if error=='duplicate':damaged['paired_ratios'].append(copy.deepcopy(damaged['paired_ratios'][0]))
            elif error=='missing':damaged['paired_ratios'].pop()
            else:damaged['paired_ratios'][0]['kkt_ns']=True
            with self.subTest(error=error),self.assertRaises(ValueError):experiment.crossovers(damaged,cases)


if __name__ == '__main__': unittest.main(verbosity=2)
