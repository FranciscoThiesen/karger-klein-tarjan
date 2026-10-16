#!/usr/bin/env python3
"""Focused synthetic arithmetic and fail-closed checks; no native child."""
import copy
import re
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from pathlib import Path
import analyze_diagnostics as a


FIELDS=tuple(re.findall(r'\{"([a-z_0-9]+)",\s*&kkt_work::WorkStats::[a-z_0-9]+,',
                       (a.ROOT/'benchmark/work_metrics.hpp').read_text()))


def fixture():
    captures={};old={}
    def row(case,mode,variant,rep):
        n=case['n'];m=n*(16 if case['family']=='gnm_random' else 32)
        r=dict(case,m=m,input_fingerprint=case['graph_seed']+n,topology_fingerprint=case['graph_seed']+n+1,
               mode=mode,variant=variant,repetition=rep,warmup=rep==0,
               peak_live_usable_bytes=10*n,returned_live_usable_bytes=n)
        r['phases']={p:dict(wall_ns=n*(i+1)+rep**2,calls=1,allocations=1,requested_bytes=n,
                           usable_bytes=n+8,deallocations=0,freed_usable_bytes=0)
                     for i,p in enumerate(a.PHASES)}
        r['phase_total_ns']=sum(v['wall_ns'] for v in r['phases'].values())
        r['wall_ns']=r['phase_total_ns']+n+rep;r['cpu_ns']=r['wall_ns']-1
        w={k:n*(i+1) for i,k in enumerate(FIELDS)}
        w.update(verifier_queries=n,path_query_visits=3*n,verifier_edge_visits=10*n,
                 verifier_tree_edges=n,fbt_output_vertices=n,fbt_calls=1)
        r['work']=w;r['work_proxy']=sum(w.values())
        return r
    for mode in ('phase','work','allocation','calibration'):
        captures[mode]=[]
        for case in a.matrix(mode):
            variants=('reference','phase') if mode=='calibration' else (mode,)
            reps=3 if mode in ('phase','calibration') else 1
            for v in variants:
                captures[mode].extend(row(case,mode,v,rep) for rep in range(reps+1))
    for r in captures['work']:
        if not r['warmup']:
            old[a.casekey(r)]=[dict(r,cpu_ns=r['cpu_ns']+i) for i in range(6)]
    return captures,old


class DiagnosticAnalysis(unittest.TestCase):
    def test_build_omitted_source_is_rejected(self):
        controller=str(a.ROOT/'benchmark/scaling_investigation/run.py')
        record=dict(validation='pass',variant_defines=a.VARIANTS,compiler='Apple clang\nTarget: arm64-test',sdk='/sdk',
                    flags=['-std=c++17','-O3','-march=native','-Wall','-Wextra','-I'+str(a.ROOT),
                           '-DKKT_EXPERIMENT_RETAIN_PARALLEL','-DKKT_EXPERIMENT_EDGE_VIEW',
                           '-DKKT_EXPERIMENT_COMPRESSED_QUERIES','-DKKT_EXPERIMENT_EIGHTH_SAMPLING','-isysroot','/sdk'],
                    source_sha256={controller:'0'*64})
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(a,'read',side_effect=lambda path,*args:a.json.dumps(record) if Path(path).name=='build.json' else ''),\
                 patch.object(a,'bind'),\
                 patch.object(a,'controller_module',return_value=SimpleNamespace(source_inventory=lambda:{controller:'0'*64,'missing.hpp':'1'*64})):
                with self.assertRaisesRegex(ValueError,'source inventory'):a.load_build(Path(directory),{})

    def test_complete_matrix_additivity_and_all_counters(self):
        captures,old=fixture();out=a.tables(captures,old,FIELDS)
        expected=dict(phase_repetitions=4752,phase_summary=1584,work=4896,phase_per_event=864,
                      allocation_repetitions=1566,allocation_summary=1566,calibration_pairs=36,
                      calibration_summary=12,historical_cpu_work=936,endpoint_contributions=264,count_fits=168)
        self.assertEqual({k:len(v) for k,v in out.items()},expected)
        self.assertEqual(set(r['counter'] for r in out['historical_cpu_work']),set(a.HISTORICAL_COUNTS))
        self.assertTrue(set(a.FIT_COUNTS)<=set(a.HISTORICAL_COUNTS))
        self.assertTrue(all(r['selected_between_two']==(r['model']=='N') for r in out['count_fits']))
        for g in a.GRAPHS:
            for s in a.SEEDS:
                for family in a.FAMILIES:
                    rows=[r for r in out['endpoint_contributions'] if (r['family'],r['graph_seed'],r['sampling_seed'])==(family,g,s)]
                    fractions={r['phase']:a.Fraction(r['delta_exact_numerator'],r['delta_exact_denominator']) for r in rows}
                    self.assertEqual(sum(v for k,v in fractions.items() if k!='total'),fractions['total'])

    def test_identity_mismatch_and_missing_input_rejected(self):
        captures,old=fixture();changed=copy.deepcopy(captures)
        changed['work'][1]['input_fingerprint']+=1
        with self.assertRaises(ValueError):a.tables(changed,old,FIELDS)
        changed=copy.deepcopy(captures);changed['phase']=changed['phase'][4:]
        with self.assertRaises(ValueError):a.tables(changed,old,FIELDS)
        old[next(iter(old))][0]['topology_fingerprint']+=1
        with self.assertRaises(ValueError):a.tables(captures,old,FIELDS)

    def test_pair_ratio_is_not_ratio_of_medians(self):
        captures,old=fixture();key=a.identity(captures['calibration'][0])
        for r in captures['calibration']:
            if a.identity(r)==key and not r['warmup']:
                r['wall_ns']=(100,50,6)[r['repetition']-1] if r['variant']=='phase' else (10,100,2)[r['repetition']-1]
        rows=a.tables(captures,old,FIELDS)['calibration_summary']
        r=next(r for r in rows if a.identity(r)==key and r['clock']=='wall_ns')
        self.assertEqual(r['median_paired_ratio'],3)
        self.assertEqual(r['ratio_of_medians'],5)

    def test_path_denominator_and_zero_retained(self):
        captures,old=fixture();row=captures['work'][1];w=row['work']
        label,value=a.denom('path_walk',w,row)
        self.assertEqual(value,w['path_visit_vertices']+w['verifier_queries']+w['path_binary_search_steps'])
        for r in captures['work']:r['work']['median_entries']=0
        out=a.tables(captures,old,FIELDS)
        zeros=[r for r in out['phase_per_event'] if r['phase']=='median_table']
        self.assertEqual(len(zeros),72)
        self.assertTrue(all(r['ns_per_event']=='' and r['ratio_status']=='zero_denominator' for r in zeros))

    def test_hash_and_json_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'file';path.write_text('before');bound={};a.read(path,bound)
            path.write_text('after')
            with self.assertRaises(ValueError):a.recheck(bound)
        with self.assertRaises(ValueError):a.parse('{"a":1,"a":2}')
        with self.assertRaises(ValueError):a.parse('{"a":1e999}')

    def test_source_snapshot_inventory_copies_and_artifact_scope(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();original=root/'original.cpp';original.write_text('original')
            copied=root/'copy.cpp';copied.write_text('original');sources={str(original):a.sha(original)}
            build=root/'build.json';build.write_text(a.json.dumps(dict(source_sha256=sources)))
            manifest=root/'snapshot.json'
            record=dict(schema='kkt_scaling_source_snapshot_v1',validation='pass',baseline_build_record=str(build),
                baseline_build_record_sha256=a.sha(build),source_sha256=sources,copies={str(original):str(copied)})
            map_digest=a.hashlib.sha256(a.json.dumps(sources,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            with patch.object(a,'BASELINE_BUILD',build),patch.object(a,'BASELINE_BUILD_SHA',a.sha(build)),patch.object(a,'BASELINE_SOURCE_MAP_SHA',map_digest):
                manifest.write_text(a.json.dumps(record));bound={};snapshot=a.source_snapshot(manifest,bound)
                original.write_text('changed production source')
                a.bind_source_or_artifact(original,bound,sources[str(original)],snapshot)
                self.assertIn(str(copied),bound);self.assertNotIn(str(original),bound)
                artifact=root/'binary';artifact.write_text('old');expected=a.sha(artifact);artifact.write_text('new')
                with self.assertRaisesRegex(ValueError,'hash mismatch'):a.bind_source_or_artifact(artifact,{},expected,snapshot)
                for mutate in ('missing','extra','wrong_baseline','live_copy','bad_copy'):
                    changed=copy.deepcopy(record)
                    if mutate=='missing':changed['copies']={}
                    elif mutate=='extra':changed['source_sha256']['extra']='0'*64
                    elif mutate=='wrong_baseline':changed['baseline_build_record_sha256']='0'*64
                    elif mutate=='live_copy':changed['copies'][str(original)]=str(original)
                    else:copied.write_text('drift')
                    manifest.write_text(a.json.dumps(changed))
                    with self.subTest(mutation=mutate),self.assertRaises(ValueError):a.source_snapshot(manifest,{})
                    copied.write_text('original')
                a.recheck({str(copied):sources[str(original)]})

    def test_failed_unknown_and_late_receipts_rejected(self):
        record=dict(validation='pass',exit_code=0,group_empty=True,native_process_may_still_be_running=False,
            cleanup=dict(native_exit_known=True,group_exit_known=True,native_process_may_still_be_running=False),
            pgid=12,started_monotonic_ns=1,exit_monotonic_ns=100,finished_monotonic_ns=200,deadline_seconds=1,
            rss_samples=1,observations=[dict(validation='pass',rss_kib=2)],peak_sampled_group_rss_bytes=2048,rss_limit_bytes=4096)
        a.receipt(record)
        for name,value in (('exit_code',False),('group_empty',False),('native_process_may_still_be_running',True),('exit_monotonic_ns',2_000_000_001)):
            bad=copy.deepcopy(record);bad[name]=value
            with self.assertRaises(ValueError):a.receipt(bad)


if __name__=='__main__':unittest.main()
