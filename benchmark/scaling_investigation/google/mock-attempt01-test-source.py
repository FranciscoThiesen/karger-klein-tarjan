#!/usr/bin/env python3
"""Focused synthetic gates. No compiler, solver or Google process is launched."""
from contextlib import contextmanager
import copy
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest import mock

import run_google as target

fixtures = target.module(target.OLD_PACKAGE/'test_analyze_complexity.py', 'depth_google_fixtures')


def passing_receipt(command, started, finished):
    return dict(command=command,cwd=str(target.ROOT),exit_code=0,validation='pass',pgid=12345,
                group_empty=True,native_process_may_still_be_running=False,
                started_monotonic_ns=started,exit_monotonic_ns=finished,finished_monotonic_ns=finished,
                deadline_seconds=600,rss_limit_bytes=12*1024**3,observations=[],
                cleanup=dict(native_exit_known=True,group_exit_known=True,native_process_may_still_be_running=False,
                             returncode=0,process_group=12345,group_verification=dict(validation='pass',members=[])))


@contextmanager
def capture_fixture(root, mutation=None):
    build_path=root/'build.json'; build_path.write_text('{}\n')
    prerequisite=root/'required-gate-artifact'; prerequisite.write_text('required\n')
    build=dict(candidate_build=str(root/'candidate-build.json'),variants={
        policy:dict(binary='/synthetic/never-launched/'+policy) for policy in ('reference','depth')})
    expected={}
    for _,spec in target.schedule():
        for row in fixtures.make_native(spec)[0]:
            expected[(row['family'],row['n'])]=(row['input_fingerprint'],row['topology_fingerprint'])
    launched=[]
    def gate(paths,build,record,bound): target.add(bound,prerequisite)
    def launch(command,out,label,**kwargs):
        launched.append(command)
        started=time.monotonic_ns()
        spec=dict(family=command[3],algorithm=command[4],graph_seed=int(command[5]),
                  sampling_seed=int(command[6]),size_order=command[7])
        rows,certs=fixtures.make_native(spec)
        document=fixtures.make_library(spec,rows)
        if mutation: mutation(rows,document)
        Path(command[8]).write_text(fixtures.encode_rows(rows))
        Path(command[9]).write_text(json.dumps(document))
        stdout=out/(label+'.stdout'); stderr=out/(label+'.stderr')
        stdout.write_text('synthetic Google console\n'); stderr.write_text(certs)
        value=passing_receipt(command,started,time.monotonic_ns())
        value.update(deadline_seconds=kwargs['timeout'],rss_limit_bytes=kwargs['rss_cap'],
                     stdout_sha256=target.sha(stdout),stderr_sha256=target.sha(stderr))
        target.write(out/(label+'.json'),value)
        return value
    with mock.patch.object(target,'check_build',return_value=(build,{},expected,{})), \
         mock.patch.object(target.candidate,'prerequisites',side_effect=gate), \
         mock.patch.object(target.base,'run_owned',side_effect=launch), \
         mock.patch.object(target.base,'_launch_blocked',False):
        yield build_path,prerequisite,launched


class GoogleTests(unittest.TestCase):
    def test_fixed_six_curves_and_exact_shared_main_recipe(self):
        pairs=[(p,s['family']) for p,s in target.schedule()]
        self.assertEqual(pairs,[('reference','leaf_hierarchy4'),('depth','leaf_hierarchy4'),
                               ('depth','leaf_shuffled4'),('reference','leaf_shuffled4'),
                               ('reference','gnm_random'),('depth','gnm_random')])
        self.assertEqual(target.declaration()['rows'],594)
        self.assertTrue(all(s['graph_seed']==19000013 and s['sampling_seed']==3001
                            and s['size_order']=='ascending' for _,s in target.schedule()))
        old=dict(working_directory='/old',sdk='/sdk',compiler='same',library='/library.a',
                 build_commands=[['/usr/bin/arch','-arm64','/usr/bin/clang++','-I/old',
                                  '-DKKT_EXPERIMENT_EDGE_VIEW','-c','/old/main','-o','/old/main.o']])
        with mock.patch.object(target,'objects',side_effect=lambda p,r,s:[Path('/'+s+str(i)+'.o') for i in range(8)]):
            recipe=target.commands(Path('/new'),Path('/candidate/build.json'),dict(sdk='/sdk',compiler='same'),old)
        self.assertEqual(len(recipe),3)
        self.assertEqual(recipe[0][1][-4:],['-c',str(target.OLD_PACKAGE/'current_complexity.cpp'),'-o','/new/current_complexity.o'])
        for _,command in recipe[1:]:
            self.assertEqual(command.count('/new/current_complexity.o'),1)
            self.assertEqual(command.count('/library.a'),1)
            self.assertNotIn('/old/main.o',command)
            self.assertNotIn('-DKKT_EXPERIMENT_DEPTH_QUERIES',command)

    def test_full_matrix_raw_library_validation_and_missing_binding(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve()
            with capture_fixture(root) as (build,required,launched):
                output=root/'capture'; target.capture(output,build,[root/'gate1',root/'gate2',root/'gate3'])
                info,rows,bound=target.load(output/'capture.json')
                self.assertEqual((len(launched),len(rows)),(6,594))
                self.assertEqual(sum(r['phase']=='timed' for r in rows),396)
                self.assertTrue(all(x['library_big_o']['big_o']=='N^2' for x in info['captures']))
                self.assertTrue(all(x['library_rms']['aggregate_name']=='RMS' for x in info['captures']))
                self.assertIn(str(required),bound)
                changed=copy.deepcopy(info); del changed['bound_sha256'][str(required)]
                target.write(output/'capture.json',changed)
                with self.assertRaisesRegex(RuntimeError,'omitted required proof'): target.load(output/'capture.json')

    def test_failed_curve_stops_and_retains_attempt(self):
        for mutation in (lambda rows,doc: rows.pop(),
                         lambda rows,doc: rows[0].update(input_fingerprint=1),
                         lambda rows,doc: doc['benchmarks'][-2].update(big_o='N')):
            with tempfile.TemporaryDirectory() as folder:
                root=Path(folder).resolve()
                with capture_fixture(root,mutation) as (build,_,launched):
                    with self.assertRaises((RuntimeError,ValueError)):
                        target.capture(root/'capture',build,[root/'a',root/'b',root/'c'])
                    info,_=target.read(root/'capture/capture.json')
                    self.assertEqual(len(launched),1)
                    self.assertEqual(info['validation'],'failed')
                    self.assertTrue((root/'capture/00.csv').is_file())
                    self.assertTrue((root/'capture/curve-00.json').is_file())

    def test_receipt_late_exit_unknown_group_and_rss(self):
        command=['never','launched']
        good=passing_receipt(command,10**9,2*10**9)
        mutations=(lambda v:v.update(exit_monotonic_ns=602*10**9,finished_monotonic_ns=602*10**9),
                   lambda v:v.update(native_process_may_still_be_running=True),
                   lambda v:v['cleanup']['group_verification'].update(members=[{'pid':12345}]),
                   lambda v:v.update(exit_code=False),
                   lambda v:v.update(observations=[dict(validation='unavailable')]*3),
                   lambda v:v.update(observations=[dict(validation='pass',rss_kib=12*1024**2+1)]))
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'receipt.json'
            target.write(path,good); target.receipt(path,command,{})
            for change in mutations:
                value=copy.deepcopy(good); change(value); target.write(path,value)
                with self.assertRaises(RuntimeError): target.receipt(path,command,{})

    def test_declaration_and_input_changes_cannot_be_self_consistently_accepted(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve()
            with capture_fixture(root) as (build,_,launched):
                output=root/'capture'; target.capture(output,build,[root/'a',root/'b',root/'c'])
                info,_=target.read(output/'capture.json'); declaration,_=target.read(output/'declaration.json')
                declaration['child_seconds']=601
                target.write(output/'declaration.json',declaration)
                info['declaration']=declaration; info['bound_sha256'][str(output/'declaration.json')]=target.sha(output/'declaration.json')
                target.write(output/'capture.json',info)
                with self.assertRaisesRegex(RuntimeError,'declaration drift'): target.load(output/'capture.json')


if __name__=='__main__': unittest.main()
