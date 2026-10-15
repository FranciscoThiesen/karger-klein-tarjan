#!/usr/bin/env python3
"""Prepared synthetic density-search gates; no native execution or builds."""
import argparse
import contextlib
import copy
import csv
import json
from pathlib import Path
import threading
import unittest
from unittest import mock

import run_density_search as density
import test_edge_view_experiment as paired_tests

control = density.control
old = paired_tests.old


@contextlib.contextmanager
def fixture():
    with paired_tests.fixture() as (root, parent_args, _):
        manifest = root / 'density-manifest.csv'
        with manifest.open('w', newline='') as stream:
            writer = csv.writer(stream); writer.writerow(control.native.base.MANIFEST_FIELDS)
            writer.writerows((family,n,d,0) for d in (32,64) for n in (65536,1048576)
                             for family in ('leaf_hierarchy4','leaf_shuffled4'))
        protocol = root/'DENSITY.md'; protocol.write_text('Synthetic prospective density screen.\n')
        args = argparse.Namespace(parent_freeze=parent_args.freeze, manifest=manifest, protocol=protocol, freeze=root/'density-freeze.json')
        with mock.patch.object(density, 'PARENT_SHA256', control.native.sha(parent_args.freeze)):
            density.preflight(args)
            yield root, args, parent_args


class Factory(paired_tests.control_tests.Factory):
    def __call__(self, argv, **kwargs):
        rows = paired_tests.control_tests.rows_for(argv)
        for row in rows: row['input_fingerprint'] = 9 if row['family'] == 'leaf_hierarchy4' else 10
        certificate = {name: rows[0][name] for name in control.native.CERTIFICATE_FIELDS}
        kwargs['stderr'].write(control.native.CERTIFICATE_PREFIX + json.dumps(certificate) + '\n')
        if self.mutation: self.mutation(rows)
        writer = csv.DictWriter(kwargs['stdout'], fieldnames=control.FIELDS); writer.writeheader(); writer.writerows(rows)
        process = old.FakeProcess(75000+len(self.children), self.status, self.finishes)
        self.children.append((argv,process)); return process


def capture(root,args,factory=None,sampler=None,output='density.csv'):
    factory = factory or Factory()
    def provider(group):
        process = next(process for _,process in factory.children if process.pid == group)
        return {'process_group':group,'members':[]} if process.returncode is not None else old.provider(group)
    sampler = sampler or control.monitor.BoundedSampler(provider,.1)
    info = density.capture(argparse.Namespace(freeze=args.freeze,output=root/output,released=True),sampler=sampler,popen=factory)
    return info,factory


class DensitySearchTests(unittest.TestCase):
    def test_scope_restores_even_nested_failure(self):
        before = control.GRAPH_SEEDS,control.SAMPLING_SEED
        with self.assertRaises(RuntimeError):
            with density.configured():
                self.assertEqual((control.GRAPH_SEEDS,control.SAMPLING_SEED),(density.GRAPH_SEEDS,1217))
                with density.configured(): raise RuntimeError('synthetic')
        self.assertEqual((control.GRAPH_SEEDS,control.SAMPLING_SEED),before)

    def test_full_matrix_strict_analysis_matched_controls_and_power(self):
        with fixture() as (root,args,parent_args):
            info,factory=capture(root,args)
            self.assertEqual((len(factory.children),info['checked_rows'],info['checked_timed_rows'],info['checked_warmup_rows']),(16,672,576,96))
            self.assertEqual([item['case_id'] for item in info['captures'][:8]],list(reversed([item['case_id'] for item in info['captures'][8:]])))
            self.assertTrue(all(item['command'][0] == str(parent_args.edge_binary) for item in info['captures']))
            rows=density.load(root/'density.json')[2];tables=density.aggregate(rows)
            self.assertEqual({name:len(values) for name,values in tables.items()}, {'paired_ratios':960,'comparisons':80,'graph_comparisons':160,'summary':96,'graph_summary':192})
            self.assertTrue(all(row['trials']==12 for row in tables['comparisons']))
            power=root/'power.log';power.write_text('2000-01-01 00:00:00 +0000 Sleep Entering Sleep state\n2000-01-01 00:00:00 +0000 Wake Requests request=Maintenance\n2000-01-01 00:00:01 +0000 Wake Wake from Deep Idle\n')
            density.analyze(argparse.Namespace(capture=root/'density.json',output_dir=root/'analysis',power_log=power))
            self.assertEqual(control.analysis.read_json(root/'analysis/provenance.json')['power_audit']['logged_overlap_calls'],672)
            with self.assertRaisesRegex(ValueError,'overwrite'):capture(root,args)

    def test_parent_binary_build_sources_helpers_and_manifest_drift_block_launch(self):
        with fixture() as (root,args,parent_args):
            for path in (args.parent_freeze,args.protocol,args.manifest,parent_args.edge_binary,parent_args.edge_build_record,
                         root/'benchmark/retention_control.cpp',root/'verifier/verifier_v2.cpp'):
                before=path.read_bytes();path.write_bytes(before+b'drift');factory=Factory()
                with self.subTest(path=path),self.assertRaises(ValueError):capture(root,args,factory=factory)
                self.assertFalse(factory.children);path.write_bytes(before)
            helpers=density.helpers();changed=dict(helpers);changed[str(density.HERE)]='0'*64
            with mock.patch.object(density,'helpers',return_value=changed),self.assertRaises(ValueError):density.check_freeze(args.freeze)
            with self.assertRaisesRegex(ValueError,'released'):
                density.capture(argparse.Namespace(freeze=args.freeze,output=root/'unreleased.csv',released=False))
            frozen=control.analysis.read_json(args.freeze);frozen['binary']=str(parent_args.tuple_binary)
            control.write_json(args.freeze,frozen)
            with self.assertRaisesRegex(ValueError,'inherited'):density.check_freeze(args.freeze)

    def test_bad_case_set_metadata_raw_certificate_and_combined_file(self):
        with fixture() as (root,args,parent_args):
            good,_=capture(root,args)
            for mutation in (lambda x:x['captures'].pop(),lambda x:x['captures'][0].update(graph_seed=4000037),
                             lambda x:x.update(checked_rows=840),lambda x:x['captures'][0].update(exit_status=None),
                             lambda x:x['captures'][0].update(group_exit_verification={}),
                             lambda x:x['captures'][0]['certificate'].update(m=1),lambda x:x.update(rows_removed=1)):
                changed=copy.deepcopy(good);mutation(changed);control.write_json(root/'density.json',changed)
                with self.assertRaises((ValueError,KeyError)):density.load(root/'density.json')
            control.write_json(root/'density.json',good)
            raw=Path(good['captures'][0]['csv']);original_raw=raw.read_bytes()
            raw.write_text(raw.read_text().replace(',1217,',',1013,'))
            changed=copy.deepcopy(good);changed['captures'][0]['output_sha256']=control.native.sha(raw);control.write_json(root/'density.json',changed)
            with self.assertRaises(ValueError):density.load(root/'density.json')
            raw.write_bytes(original_raw)
            combined=root/'density.csv'
            combined_rows=[row for _,row in control.native.base.read_csv(combined,control.FIELDS)]
            combined_rows[0]['elapsed_ns']=str(int(combined_rows[0]['elapsed_ns'])+1)
            control.analysis.write_csv(combined,combined_rows)
            changed=copy.deepcopy(good);changed['output_sha256']=control.native.sha(combined)
            control.write_json(root/'density.json',changed)
            with self.assertRaisesRegex(ValueError,'concatenation'):density.load(root/'density.json')
            bad=root/'bad-manifest.csv';bad.write_text(args.manifest.read_text().replace('leaf_shuffled4','leaf_random4'))
            with self.assertRaisesRegex(ValueError,'eight density'):density.cases_from_manifest(bad)

    def test_matched_control_topology_and_nonvacuous_weights(self):
        rows=[]
        for seed in density.GRAPH_SEEDS:
            for n in (65536,1048576):
                for d in (32,64):
                    for family,fingerprint in (('leaf_hierarchy4',9),('leaf_shuffled4',10)):
                        rows.append({'case_id':f'{family}_n{n}_d{d}_p0','family':family,'n':n,'density':d,
                                     'graph_seed':seed,'input_fingerprint':fingerprint,'topology_fingerprint':8})
        density.check_fingerprints(rows,complete=True)
        bad=copy.deepcopy(rows);bad[1]['topology_fingerprint']=7
        with self.assertRaises(ValueError):density.check_fingerprints(bad,complete=True)
        bad=copy.deepcopy(rows);bad[1]['input_fingerprint']=9
        with self.assertRaisesRegex(ValueError,'identical weighted'):density.check_fingerprints(bad,complete=True)
        with self.assertRaisesRegex(ValueError,'incomplete'):density.check_fingerprints(rows[:-1],complete=True)

    def test_clock_flags_preserved_monitor_failures_and_poison(self):
        with fixture() as (root,args,parent_args):
            info,_=capture(root,args,factory=Factory(mutation=lambda rows:rows[0].update(elapsed_ns=2_000_000_000)))
            self.assertEqual(info['flagged_calls'],16);self.assertEqual(len(density.load(root/'density.json')[2]),672)
        for failure in ('ceiling','unavailable','nonempty exit','unavailable exit','crash'):
            with self.subTest(failure=failure),fixture() as (root,args,parent_args):
                factory=Factory(status=-11 if failure=='crash' else 0,finishes=failure!='unavailable')
                def provider(group):
                    exited=factory.children[-1][1].returncode is not None
                    if failure=='unavailable' or (failure=='unavailable exit' and exited):raise OSError('synthetic')
                    result=old.provider(group)
                    if failure=='ceiling':result['members'][0]['rss_kib']=control.RULE['rss_limit_kib']+1
                    return result
                with mock.patch.object(control.monitor,'bounded_terminate',return_value={'native_process_may_still_be_running':True}),self.assertRaises(ValueError):
                    capture(root,args,factory=factory,sampler=control.monitor.BoundedSampler(provider,.1))
                self.assertEqual(len(factory.children),1)
        with fixture() as (root,args,parent_args):
            gate=threading.Event();factory=Factory();sampler=control.monitor.BoundedSampler(lambda group:(gate.wait(),old.provider(group))[1],.01)
            try:
                with mock.patch.object(control.monitor,'bounded_terminate',return_value={'native_process_may_still_be_running':True}),self.assertRaisesRegex(ValueError,'timed out'):
                    capture(root,args,factory=factory,sampler=sampler)
                second=Factory()
                with self.assertRaisesRegex(ValueError,'forbids launching'):capture(root,args,factory=second,sampler=sampler,output='second.csv')
                self.assertEqual((len(factory.children),len(second.children),sampler.workers_started),(1,0,1))
            finally:gate.set()


if __name__=='__main__':unittest.main(verbosity=2)
