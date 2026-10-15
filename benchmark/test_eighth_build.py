#!/usr/bin/env python3
"""Mocked half/eighth build, record and artifact gates; no native jobs."""
import copy
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest import mock

import build_eighth_sampling as builder


def records(eighth=False):
    # Synthetic complete raw matrix, built without a production comparator.
    fields = re.findall(r'\{"([a-z_0-9]+)",', (builder.ROOT/'benchmark/work_metrics.hpp').read_text())
    assert len(fields) == len(set(fields)) == 65
    result = []
    for fixture in range(56):
        for order in range(3):
            for seed in (0,1,2,17,401,809,65537,4294967295):
                stats = dict.fromkeys(fields,0)
                stats.update(sampling_edge_visits=97 if eighth else 96,sampling_calls=2,
                             sampled_edges=12 if eighth else 48,
                             root_after_two_vertices=4,root_after_two_edges=96)
                result.append({'fixture':fixture,'order':order,'seed':seed,'fingerprint':10000+fixture,
                               'ids':[0,2,4],'stats':stats})
    return result


def write(path,rows):
    path.write_text(''.join(json.dumps(row,allow_nan=False)+'\n' for row in rows)); return path


class EighthBuildTests(unittest.TestCase):
    def test_cross_rate_identity_changed_work_and_exact_parent_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            half = write(root/'half.jsonl',records(False)); eighth = write(root/'eighth.jsonl',records(True))
            gate = builder.compare_sampling(half,eighth)
            self.assertEqual(gate['different_recursive_work_pairs'],1344)
            self.assertTrue(gate['identical_root_after_two_dimensions'])
            self.assertEqual(builder.reject_substitution(builder.compare_sampling,half),'rejected')
            with mock.patch.object(builder,'PARENT_RECORDS_SHA256',builder.sha(half)):
                self.assertEqual(builder.compare_half_parent(half,half)['identical_counter_fields'],65)
                with self.assertRaisesRegex(RuntimeError,'exact parent replay'): builder.compare_half_parent(half,eighth)
            for field in ('root_after_two_vertices','root_after_two_edges'):
                changed = records(True); changed[0]['stats'][field] += 1; write(eighth,changed)
                with self.assertRaisesRegex(RuntimeError,'root contractions'): builder.compare_sampling(half,eighth)

    def test_record_schema_identity_input_and_sampling_witness_rejections(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'record.jsonl'; wanted = records()
            mutations = {
                'missing':lambda rows:rows.pop(),
                'duplicate':lambda rows:rows.__setitem__(-1,copy.deepcopy(rows[0])),
                'bool_identity':lambda rows:rows[0].__setitem__('fixture',False),
                'bool_fingerprint':lambda rows:rows[0].__setitem__('fingerprint',False),
                'oversize_fingerprint':lambda rows:rows[0].__setitem__('fingerprint',2**64),
                'duplicate_ids':lambda rows:rows[0].__setitem__('ids',[0,0]),
                'bool_counter':lambda rows:rows[0]['stats'].__setitem__('sampling_calls',True),
                'negative_counter':lambda rows:rows[0]['stats'].__setitem__('sampling_calls',-1),
                'oversize_counter':lambda rows:rows[0]['stats'].__setitem__('sampling_calls',2**64),
                'missing_counter':lambda rows:rows[0]['stats'].pop('sampling_calls'),
                'extra_field':lambda rows:rows[0].__setitem__('extra',0),
            }
            for label,mutation in mutations.items():
                changed = copy.deepcopy(wanted); mutation(changed); write(path,changed)
                with self.subTest(label=label),self.assertRaises(RuntimeError): builder.load_records(path)
            write(path,wanted); text = path.read_text(); path.write_text(text.replace('"fixture": 0','"fixture": 0, "fixture": 0',1))
            with self.assertRaisesRegex(RuntimeError,'duplicate JSON key'): builder.load_records(path)
            write(path,wanted); path.write_text(path.read_text().replace('"fingerprint": 10000','"fingerprint": NaN',1))
            with self.assertRaisesRegex(RuntimeError,'nonfinite'): builder.load_records(path)
            other = Path(temporary)/'other.jsonl'; write(path,wanted)
            changed = records(True); changed[0]['ids'] = [0,2,5]; write(other,changed)
            with self.assertRaisesRegex(RuntimeError,'input/MST'): builder.compare_sampling(path,other)

    def test_focused_native_output_counts_witness_and_expected_policy(self):
        predicate = 'PASS: three deterministic eighth-sampling predicate groups\n'
        compressed = 'PASS 252 positional cases, 7 malformed lookups; actual linked policy=compressed\n'
        for variant in ('half','eighth'):
            integration = f'PASS 132 private/public sampling cases, each replayed; 21 half/eighth witnesses; policy={variant}\n'
            for stem,text in (('eighth_sampling_test',predicate),('compressed_query_test',compressed),
                              ('eighth_sampling_integration_test',integration)):
                builder.check_focused_output(stem,variant,text)
                with self.assertRaises(RuntimeError): builder.check_focused_output(stem,variant,text+'extra')
            for text in (integration.replace('132','131'),integration.replace('21 half','0 half'),
                         integration.replace('21 half','67 half'),integration.replace('replayed','not replayed'),
                         integration.replace('policy='+variant,'policy='+('eighth' if variant == 'half' else 'half'))):
                with self.assertRaises(RuntimeError): builder.check_focused_output('eighth_sampling_integration_test',variant,text)
        with self.assertRaises(RuntimeError): builder.check_focused_output('eighth_sampling_test','half',predicate.replace('three','two'))
        with self.assertRaises(RuntimeError): builder.check_focused_output('compressed_query_test','half',compressed.replace('compressed','reference'))

    def test_original_parent_helper_binding_and_restoration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); freeze = root/'freeze.json'; freeze.touch()
            expected = {str(root/'original/engine.py'):'engine',str(root/'original/monitor.py'):'monitor'}
            copies = {str(root/'copy/engine.py'):'engine',str(root/'copy/monitor.py'):'monitor'}
            original = {'python_source_sha256':expected}; returned = {'full_parent_checked':True}
            def digest(path): return builder.PARENT_SHA256 if Path(path) == freeze else expected[str(path)]
            def checker(path):
                self.assertEqual(path,freeze); self.assertEqual(builder.parent_engine.helpers(),expected)
                return returned,[]
            with mock.patch.object(builder,'sha',side_effect=digest), \
                 mock.patch.object(builder.parent_engine.analysis,'read_json',return_value=original), \
                 mock.patch.object(builder.parent_engine,'helpers',return_value=copies) as helpers, \
                 mock.patch.object(builder.parent_engine,'check_freeze',side_effect=checker) as check:
                self.assertIs(builder.parent_record(freeze),returned)
                self.assertIs(builder.parent_engine.helpers,helpers); check.assert_called_once()
                check.side_effect = RuntimeError('original native artifact changed')
                with self.assertRaisesRegex(RuntimeError,'original native'): builder.parent_record(freeze)
                self.assertIs(builder.parent_engine.helpers,helpers)
                helpers.return_value = {**copies,str(root/'copy/extra.py'):'extra'}
                check.reset_mock()
                with self.assertRaisesRegex(RuntimeError,'helper copies'): builder.parent_record(freeze)
                check.assert_not_called(); self.assertIs(builder.parent_engine.helpers,helpers)

    def test_exact_timing_recipe_has_one_compressed_verifier_and_eighth_kkt_only(self):
        root = Path('/authorized/eighth'); sdk = '/sdk'
        commands,objects,binaries,main,links = builder.expected_timing_commands(root,sdk)
        self.assertEqual(len(commands),12)
        self.assertEqual([c[c.index('-c')+1] for c in commands[:10]],
                         ['boruvka/boruvka.cpp','kruskal/kruskal.cpp','prim/prim.cpp','lca/lca.cpp',
                          'union_find/union_find.cpp','graph_utils/graph_utils.cpp','verifier/verifier_v2.cpp',
                          'kkt/kkt.cpp','kkt/kkt.cpp','benchmark/retention_control.cpp'])
        self.assertEqual([i for i,c in enumerate(commands) if '-DKKT_EXPERIMENT_COMPRESSED_QUERIES' in c],[6])
        self.assertEqual([i for i,c in enumerate(commands) if '-DKKT_EXPERIMENT_EIGHTH_SAMPLING' in c],[8])
        self.assertTrue(all('WORK_STATS' not in flag and 'NDEBUG' not in flag for c in commands for flag in c))
        for name in objects['half']:
            if name != 'kkt/kkt.o': self.assertEqual(objects['half'][name],objects['eighth'][name])
        self.assertEqual(len(objects['half']),8)
        self.assertEqual(commands[-2:],[links['half'],links['eighth']])
        self.assertIn(main,links['half']); self.assertIn(main,links['eighth'])
        self.assertNotEqual(binaries['half'],binaries['eighth'])

        # Independent literal compile/link oracle: no builder FLAGS, SOURCES,
        # returned object mapping or links are used to form expected argv.
        base = ['/usr/bin/arch','-arm64','/usr/bin/clang++','-isysroot','/sdk',
                '-std=c++17','-O3','-Wall','-Wextra','-march=native',
                '-DKKT_EXPERIMENT_RETAIN_PARALLEL','-DKKT_EXPERIMENT_EDGE_VIEW','-I.']
        directory = '/authorized/eighth/.build/eighth-sampling/timing-build/'
        shared = ['boruvka/boruvka','kruskal/kruskal','prim/prim','lca/lca',
                  'union_find/union_find','graph_utils/graph_utils','verifier/verifier_v2']
        expected = [base+(['-DKKT_EXPERIMENT_COMPRESSED_QUERIES'] if name == 'verifier/verifier_v2' else [])+
                    ['-c',name+'.cpp','-o',directory+'shared/'+name+'.o'] for name in shared]
        expected += [base+['-c','kkt/kkt.cpp','-o',directory+'half/kkt/kkt.o'],
                     base+['-DKKT_EXPERIMENT_EIGHTH_SAMPLING','-c','kkt/kkt.cpp','-o',directory+'eighth/kkt/kkt.o'],
                     base+['-c','benchmark/retention_control.cpp','-o',directory+'shared/benchmark/retention_control.o']]
        common_objects = [directory+'shared/'+name+'.o' for name in shared]
        expected += [base+common_objects+[directory+'half/kkt/kkt.o',directory+'shared/benchmark/retention_control.o',
                     '-L/sdk/usr/lib','-Wl,-stack_size,0x20000000','-o','/authorized/eighth/bin/eighth-sampling/timing-build/half/retention_control'],
                     base+common_objects+[directory+'eighth/kkt/kkt.o',directory+'shared/benchmark/retention_control.o',
                     '-L/sdk/usr/lib','-Wl,-stack_size,0x20000000','-o','/authorized/eighth/bin/eighth-sampling/timing-build/eighth/retention_control']]
        self.assertEqual(commands,expected)

    def test_source_allowlist_and_exact_declared_overlay(self):
        original = {'kkt/kkt.cpp':'old-kkt','verifier/verifier_v2.cpp':'fixed-compressed','test/other.cpp':'same'}
        current = {**original,**builder.OVERLAY}
        parent = {'source_sha256':original,'build_recipe_sha256':{'benchmark/build_compressed_queries.py':'old-builder'}}
        def digest(path):
            return builder.inherited.WORK_SOURCE_SHA256 if str(path).endswith(builder.WORK_SOURCE) else 'old-builder'
        with mock.patch.object(builder,'parent_record',return_value=parent),mock.patch.object(builder,'sha',side_effect=digest), \
             mock.patch.object(builder,'inventory',return_value=current) as inventory:
            self.assertEqual(builder.check_source_contract(builder.PARENT_PATH)[1],current)
            changes = []
            for name in builder.OVERLAY:
                changed = dict(current); changed[name] = 'drift'; changes.append(changed)
            changed = dict(current); changed['verifier/verifier_v2.cpp'] = 'different'; changes.append(changed)
            changed = dict(current); changed['test/unexpected.cpp'] = 'new'; changes.append(changed)
            changed = dict(current); changed.pop('test/other.cpp'); changes.append(changed)
            for changed in changes:
                inventory.return_value = changed
                with self.assertRaises(RuntimeError): builder.check_source_contract(builder.PARENT_PATH)

    def test_final_object_receipts_recipe_policy_and_shared_identity(self):
        path = builder.ROOT/'benchmark/results/eighth-sampling-2026-10-15/validation/validate_final_objects.py'
        spec = importlib.util.spec_from_file_location('eighth_final_object_gate_test',path)
        final = importlib.util.module_from_spec(spec); spec.loader.exec_module(final)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary); sdk = '/test-sdk'
            commands,objects,binaries,main,links = builder.expected_timing_commands(builder.ROOT,sdk)
            sources = {'known.cpp':'known'}; toolchain = {'compiler':'native-test','compiler_command':['native-test'],'sdk':sdk}
            parent = {'variants':{'compressed':{'build':{'record':toolchain}}}}
            binary_profile = {'file_description':'Mach-O 64-bit executable arm64','main_stack_bytes':536870912}
            def digest(path): return 'digest:'+str(path)
            originals = {}
            for variant in builder.VARIANTS:
                record = {'schema':'eighth_sampling_build_v1','profile':'timing-build','variant':variant,
                    'working_directory':str(builder.ROOT),'source_sha256':sources,'common_compile_flags':builder.FLAGS,
                    'build_recipe_sha256':{name:digest(builder.ROOT/name) for name in builder.RECIPES},
                    'build_exit_status':0,'parent_compressed_freeze':str(builder.PARENT_PATH),
                    'parent_compressed_freeze_sha256':builder.PARENT_SHA256,
                    'seven_non_kkt_objects_identical_by_construction':True,'compressed_queries_fixed':True,
                    'public_scalar_sampling_fixed':True,'reference_note':builder.REFERENCE_NOTE,
                    'role':'timing_never_executed','verifier_policy':'compressed','source_overlay_sha256':builder.OVERLAY,
                    'sampling_policy':variant,'private_acceptance_mask':7 if variant == 'eighth' else 1,
                    'sampling_words_per_visited_edge':1,
                    **toolchain,'build_command':['python3','-B',str(builder.ROOT/'benchmark/build_eighth_sampling.py'),
                    '--profile','timing-build','--output',str(output),'--parent-freeze',str(builder.PARENT_PATH)],
                    'build_commands':commands,'object_paths':objects[variant],'binary':binaries[variant],
                    'main_object':main,'link_command':links[variant],
                    'object_sha256':{name:digest(path) for name,path in objects[variant].items()},
                    'main_object_sha256':digest(main),'binary_sha256':digest(binaries[variant]),
                    'build_log':str(output/'build.log'),'build_log_sha256':digest(output/'build.log'),
                    'source':'benchmark/retention_control.cpp','binary_profile':binary_profile}
                record['executables'] = [{name:record[name] for name in ('source','main_object','main_object_sha256',
                    'binary','binary_sha256','binary_profile','link_command','verifier_policy','role',
                    'sampling_policy','private_acceptance_mask','sampling_words_per_visited_edge')}]
                originals[variant] = record
            def write_records(data):
                for variant,record in data.items():
                    (output/f'timing-build-{variant}-build-record.json').write_text(json.dumps(record))
            write_records(originals)
            with mock.patch.object(builder,'check_source_contract',return_value=(parent,sources)), \
                 mock.patch.object(builder,'sha',side_effect=digest),mock.patch.object(builder,'profile',return_value=binary_profile):
                self.assertEqual(len(final.checked_records(output)[0]),2)
                mutations = {
                    'compression_macro':lambda r:r['build_commands'][6].remove('-DKKT_EXPERIMENT_COMPRESSED_QUERIES'),
                    'eighth_macro':lambda r:r['build_commands'][8].remove('-DKKT_EXPERIMENT_EIGHTH_SAMPLING'),
                    'shared_verifier_path':lambda r:r['object_paths'].__setitem__('verifier/verifier_v2.o','foreign'),
                    'eighth_object_hash':lambda r:r['object_sha256'].__setitem__('kkt/kkt.o','foreign'),
                    'overlay':lambda r:r['source_overlay_sha256'].__setitem__('kkt/kkt.cpp','foreign'),
                    'role':lambda r:r.__setitem__('role','correctness'),
                    'bool_type':lambda r:r.__setitem__('compressed_queries_fixed',1),
                    'verifier_policy':lambda r:r.__setitem__('verifier_policy','reference'),
                    'sampling_policy':lambda r:r.__setitem__('sampling_policy','half'),
                    'acceptance_mask':lambda r:r.__setitem__('private_acceptance_mask',1),
                    'mask_type':lambda r:r.__setitem__('private_acceptance_mask',True),
                    'word_count':lambda r:r.__setitem__('sampling_words_per_visited_edge',32),
                    'descriptor':lambda r:r['executables'][0].__setitem__('verifier_policy','reference'),
                    'descriptor_mask':lambda r:r['executables'][0].__setitem__('private_acceptance_mask',1),
                    'descriptor_word_bool':lambda r:r['executables'][0].__setitem__('sampling_words_per_visited_edge',True),
                }
                for label,mutation in mutations.items():
                    changed = copy.deepcopy(originals); mutation(changed['eighth']); write_records(changed)
                    with self.subTest(label=label),self.assertRaises(RuntimeError): final.checked_records(output)


if __name__ == '__main__': unittest.main(verbosity=2)
