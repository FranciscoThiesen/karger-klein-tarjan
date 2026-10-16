#!/usr/bin/env python3
"""Mocked controller gates. No compiler, solver, process provider or native child runs."""
import copy
import importlib.util
import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('scaling_run_tested', HERE.parent/'run.py')
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)
FIELDS = run.work_fields()
CASE = {'family': 'leaf_hierarchy4', 'n': 1024, 'graph_seed': 19000013, 'sampling_seed': 3001}
EXPECTED = (32768, 12345, 67890)
EMPTY = {'native_exit_known': True, 'group_exit_known': True,
         'native_process_may_still_be_running': False}


def rows(variant='reference', repetitions=1):
    phases = {name: dict.fromkeys(run.PHASE_FIELDS, 0) for name in run.PHASES}
    work = dict.fromkeys(FIELDS, 0)
    if variant in ('phase', 'allocation'):
        phases['contraction'].update(wall_ns=40, calls=2)
    if variant == 'allocation':
        phases['contraction'].update(allocations=2, requested_bytes=60, usable_bytes=64,
                                     deallocations=1, freed_usable_bytes=32)
    if variant == 'work':
        work.update(kkt_calls=2, kkt_vertices=1100, hash_insert_items=1023,
                    sampling_edge_visits=100, sampled_edges=12, filtered_edges=30,
                    verifier_forest_edges=4, fbt_input_vertices=4, verifier_queries=2,
                    path_query_visits=5, path_binary_search_steps=6,
                    contraction_edge_visits=300, contraction_edges=100)
    return [dict(schema='kkt_scaling_diagnostic_v1', **CASE, m=EXPECTED[0],
                 input_fingerprint=EXPECTED[1], topology_fingerprint=EXPECTED[2],
                 repetition=i, warmup=i == 0, wall_ns=100, cpu_ns=90,
                 utc_start_ns=123, utc_end_ns=223, phase_total_ns=40 if variant in ('phase','allocation') else 0,
                 peak_live_usable_bytes=64 if variant == 'allocation' else 0,
                 returned_live_usable_bytes=32 if variant == 'allocation' else 0,
                 phases=copy.deepcopy(phases), work=copy.deepcopy(work),
                 work_proxy=sum(work[k] for k,v in FIELDS.items() if v), validation='pass')
            for i in range(repetitions+1)]


class Guard:
    def __init__(self, observations=None, poison=False):
        self.poisoned=False; self.observations=iter(observations or [{'validation':'pass','rss_kib':1}]); self.poison=poison
    def sample(self, pid):
        result=next(self.observations); self.poisoned=self.poison; return result


class Process:
    pid=1234
    def __init__(self, code=0, waiting=None): self.returncode=code; self.waiting=waiting
    def poll(self): return self.returncode
    def wait(self, timeout):
        if self.waiting is not None: raise self.waiting
        self.returncode=0; return 0


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name); run._launch_blocked=False
        self.prior=signal.getsignal(signal.SIGTERM)
        self.addCleanup(signal.signal, signal.SIGTERM, self.prior)
    def owned(self, process, guard=None, cleanup=None, label='child', **kwargs):
        def terminate(proc, monitor):
            self.assertEqual(signal.getsignal(signal.SIGTERM), signal.SIG_IGN)
            if isinstance(cleanup, BaseException): raise cleanup
            return copy.deepcopy(EMPTY if cleanup is None else cleanup)
        with mock.patch.object(run,'sampler',return_value=guard or Guard()), \
             mock.patch.object(run.subprocess,'Popen',side_effect=process if isinstance(process,BaseException) else None,return_value=process), \
             mock.patch.object(run.monitor,'bounded_terminate',side_effect=terminate):
            return run.run_owned(['mock-native'],self.path,label,**kwargs)
    def receipt(self,label='child'): return run.strict_json((self.path/(label+'.json')).read_text())
    def test_literal_matrices_and_valid_four_builds(self):
        self.assertEqual({m:len(run.matrix(m)) for m in ('phase','work','allocation','calibration','smoke')},
                         {'phase':72,'work':72,'allocation':18,'calibration':6,'smoke':3})
        self.assertEqual(len(FIELDS),65)
        for variant in run.VARIANTS:
            self.assertEqual(len(run.validate_rows(rows(variant),CASE,variant,1,FIELDS,EXPECTED)),2)
        self.assertEqual(run.matrix('phase')[36]['n'],1048576)
        self.assertEqual(run.matrix('phase')[-1]['n'],1024)
    def test_typed_rows_and_accounting_negative_boundaries(self):
        mutations=[('reference',lambda r:r.pop('validation')),
                   ('reference',lambda r:r.update(n=True)),
                   ('reference',lambda r:r.update(warmup=1)),
                   ('reference',lambda r:r.update(input_fingerprint=7)),
                   ('reference',lambda r:r.update(cpu_ns=0)),
                   ('reference',lambda r:r.update(work_proxy=1)),
                   ('reference',lambda r:r['work'].update(hash_lookup_calls=-1)),
                   ('phase',lambda r:r.update(phase_total_ns=41)),
                   ('phase',lambda r:r['phases']['contraction'].update(calls=0)),
                   ('phase',lambda r:r['phases']['contraction'].update(allocations=1)),
                   ('allocation',lambda r:r.update(returned_live_usable_bytes=31)),
                   ('work',lambda r:r['work'].update(path_query_visits=7)),
                   ('work',lambda r:r['work'].update(path_binary_search_steps=23)),
                   ('work',lambda r:r['work'].update(contraction_edge_visits=301)),
                   ('work',lambda r:r['work'].update(filtered_edges=93)),
                   ('work',lambda r:r['work'].update(hash_insert_items=1022))]
        for variant,change in mutations:
            with self.subTest(variant=variant,change=change):
                data=rows(variant); change(data[0])
                # Refresh proxy after work mutations so independent bounds are reached.
                if variant=='work':
                    data[0]['work_proxy']=sum(data[0]['work'][k] for k,v in FIELDS.items() if v)
                    data[1]['work']=copy.deepcopy(data[0]['work']); data[1]['work_proxy']=data[0]['work_proxy']
                with self.assertRaises(RuntimeError): run.validate_rows(data,CASE,variant,1,FIELDS,EXPECTED)
        with self.assertRaises(RuntimeError): run.validate_rows(rows()[:1],CASE,'reference',1,FIELDS,EXPECTED)
        valid=rows(); valid[0]['utc_end_ns']=1
        run.validate_rows(valid,CASE,'reference',1,FIELDS,EXPECTED)  # descriptive UTC reversal retained
    def test_strict_json_and_exclusive_output(self):
        for text in ('{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}','{"x":[1e999]}'):
            with self.assertRaises((ValueError,RuntimeError)): run.strict_json(text)
        self.owned(Process())
        with self.assertRaisesRegex(RuntimeError,'collision'): self.owned(Process())
    def test_toolchain_environment_removes_only_declared_overrides(self):
        original={'PATH':'/unchanged', 'CPATH':'/foreign/include', 'LIBRARY_PATH':'/foreign/lib',
                  'SDKROOT':'/declared/sdk', 'DEVELOPER_DIR':'/declared/developer'}
        with mock.patch.dict(run.os.environ,original,clear=True):
            environment,policy=run.clean_environment()
            self.assertNotIn('CPATH',environment); self.assertNotIn('LIBRARY_PATH',environment)
            self.assertEqual(environment,{k:v for k,v in original.items() if k not in ('CPATH','LIBRARY_PATH')})
            self.assertEqual(policy['removed'],{'CPATH':'/foreign/include','LIBRARY_PATH':'/foreign/lib'})
            record=self.owned(Process(),label='environment')
            self.assertEqual(record['environment_policy'],policy)
            for key in ('CPLUS_INCLUDE_PATH','CXXFLAGS','DYLD_INSERT_LIBRARIES'):
                with self.subTest(key=key),mock.patch.dict(run.os.environ,{key:'/unexpected'}):
                    with self.assertRaisesRegex(RuntimeError,'unreviewed'): run.clean_environment()
    def test_exit_deadline_and_handler_restoration(self):
        self.assertEqual(self.owned(Process())['validation'],'pass')
        self.assertEqual(signal.getsignal(signal.SIGTERM),self.prior)
        with self.assertRaisesRegex(RuntimeError,'nonzero'): self.owned(Process(1),label='bad')
        self.assertTrue(self.receipt('bad')['group_empty'])
        with mock.patch.object(run.time,'monotonic_ns',side_effect=[0,2000000000,2000000000]):
            with self.assertRaisesRegex(RuntimeError,'after deadline'): self.owned(Process(),label='late',timeout=1)
        self.assertEqual(self.receipt('late')['validation'],'failed')
    def test_resource_failures_cleanup_and_no_poison_continuation(self):
        waiting=subprocess.TimeoutExpired(['mock'],1)
        for label,guard,message in [('rss',Guard([{'validation':'pass','rss_kib':2}]),'RSS'),
                                     ('unavailable',Guard([{'validation':'unavailable'}]*3),'unavailable'),
                                     ('poison',Guard([{'validation':'unavailable'}],poison=True),'unavailable')]:
            run._launch_blocked=False
            with self.subTest(label=label), self.assertRaisesRegex(RuntimeError,message):
                self.owned(Process(None,waiting),guard,label=label,rss_cap=1024)
            self.assertEqual(self.receipt(label)['validation'],'failed')
            self.assertTrue(self.receipt(label)['group_empty'])
        self.assertTrue(run._launch_blocked)
        with mock.patch.object(run.subprocess,'Popen') as popen:
            with self.assertRaisesRegex(RuntimeError,'forbids'): run.run_owned(['no-next'],self.path,'never')
            popen.assert_not_called()
    def test_interruption_unknown_cleanup_and_popen_uncertainty(self):
        with self.assertRaises(KeyboardInterrupt): self.owned(Process(None,KeyboardInterrupt('stop')))
        self.assertEqual(self.receipt()['validation'],'failed'); self.assertTrue(self.receipt()['group_empty'])
        for label,process,cleanup in [('unknown',Process(),dict(EMPTY,group_exit_known=False)),
                                      ('cleanup',Process(),RuntimeError('cleanup failed')),
                                      ('popen',OSError('launch uncertain'),None)]:
            run._launch_blocked=False
            with self.subTest(label=label), self.assertRaises((RuntimeError,OSError)):
                self.owned(process,cleanup=cleanup,label=label)
            self.assertTrue(run._launch_blocked)
            self.assertTrue(self.receipt(label)['native_process_may_still_be_running'])
            self.assertEqual(signal.getsignal(signal.SIGTERM),self.prior)
    def capture_fixture(self):
        build=self.path/'build'; build.mkdir(); binary=build/'diagnostic'; binary.write_text('synthetic')
        historical=self.path/'google.json'; historical.write_text('{}')
        source=self.path/'source'; source.write_text('pinned')
        run.write(build/'build.json',{'validation':'pass','source_sha256':{str(source):run.sha(source)},
                 'variants':{'work':{'binary':str(binary),'sha256':run.sha(binary),'objects':{}}}})
        return build,historical,source
    def test_capture_malformed_child_preserves_failed_campaign_and_stops(self):
        build,historical,source=self.capture_fixture()
        def fake_owned(command,directory,label,**kwargs):
            (directory/(label+'.stdout')).write_text('{}\n')
            return {'validation':'pass'}
        with mock.patch.object(run,'GOOGLE_CAPTURE',historical),mock.patch.object(run,'GOOGLE_SHA',run.sha(historical)), \
             mock.patch.object(run,'historical_inputs',return_value={tuple(CASE[k] for k in ('family','n','graph_seed','sampling_seed')):EXPECTED}), \
             mock.patch.object(run,'matrix',return_value=[CASE,CASE]),mock.patch.object(run,'run_owned',side_effect=fake_owned) as launch:
            with self.assertRaisesRegex(RuntimeError,'missing/extra'): run.capture(self.path/'capture',build,'work')
            self.assertEqual(launch.call_count,1)
        result=run.strict_json((self.path/'capture/capture.json').read_text())
        self.assertEqual(result['validation'],'failed'); self.assertEqual(result['captures'],[])
        self.assertFalse(result['native_process_may_still_be_running'])
    def test_capture_final_source_drift_is_failed_and_cli_restores_handler(self):
        build,historical,source=self.capture_fixture()
        def fake_owned(command,directory,label,**kwargs):
            (directory/(label+'.stdout')).write_text(''.join(json.dumps(row)+'\n' for row in rows('work')))
            (directory/(label+'.stderr')).write_text('')
            run.write(directory/(label+'.json'),{'validation':'pass'})
            source.write_text('changed during last child')
            return {'validation':'pass'}
        with mock.patch.object(run,'GOOGLE_CAPTURE',historical),mock.patch.object(run,'GOOGLE_SHA',run.sha(historical)), \
             mock.patch.object(run,'historical_inputs',return_value={tuple(CASE[k] for k in ('family','n','graph_seed','sampling_seed')):EXPECTED}), \
             mock.patch.object(run,'matrix',return_value=[CASE]),mock.patch.object(run,'run_owned',side_effect=fake_owned):
            with self.assertRaisesRegex(RuntimeError,'artifact drift'): run.capture(self.path/'capture',build,'work')
        self.assertEqual(run.strict_json((self.path/'capture/capture.json').read_text())['validation'],'failed')
        def interrupted(*args):
            handler=signal.getsignal(signal.SIGTERM); self.assertTrue(callable(handler)); handler(signal.SIGTERM,None)
        with mock.patch.object(sys,'argv',['run.py','build',str(self.path/'cli')]),mock.patch.object(run,'build',side_effect=interrupted):
            with self.assertRaises(KeyboardInterrupt): run.main()
        self.assertEqual(signal.getsignal(signal.SIGTERM),self.prior)


if __name__=='__main__': unittest.main(verbosity=2)
