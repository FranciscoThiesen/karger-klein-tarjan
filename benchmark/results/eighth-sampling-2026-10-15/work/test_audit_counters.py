#!/usr/bin/env python3
"""Synthetic standalone counter-audit gates; no collector/native imports."""
import copy
import csv
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
module = importlib.util.spec_from_file_location('independent_eighth_counter_audit_test',HERE/'audit_counters.py')
audit = importlib.util.module_from_spec(module); module.loader.exec_module(audit)


def synthetic_values():
    cases = [('leaf_hierarchy4',65536,32),('leaf_shuffled4',65536,32),
             ('leaf_hierarchy4',1048576,32),('leaf_shuffled4',1048576,32),
             ('gnm_random',4096,16),('gnm_random',1048576,16)]
    values = []
    for gi,graph in enumerate((15000011,15000031)):
        for si,sampler in enumerate((2609,2617)):
            for family,n,density in (cases if gi == 0 else cases[::-1]):
                case_index = cases.index((family,n,density)); m = n*density
                topology = n+graph+density
                for variant in (('half','eighth') if gi == si else ('eighth','half')):
                    spec = dict(variant=variant,case_id=f'{family}_n{n}_d{density}_p0',graph_seed=graph,kkt_seed=sampler,
                        family=family,n=n,density=density,intrusion_per_mille=0,m=m,
                        input_fingerprint=topology+100+case_index,topology_fingerprint=topology)
                    rounds = [dict(round=0,vertices=n,edges=m,selected=n//2,output_vertices=n//2,output_edges=m//2),
                              dict(round=1,vertices=n//2,edges=m//2,selected=n//4,output_vertices=n//4,output_edges=m//4),
                              dict(round=2,vertices=n//4,edges=m//4,selected=n//4-1,output_vertices=0,output_edges=0)]
                    algorithms = {}
                    for name in ('kkt','compacting_boruvka','multigraph_boruvka'):
                        stats = dict.fromkeys(audit.FIELDS,0)
                        stats.update(contraction_calls=3,contraction_vertices=n+n//2+n//4,contraction_edges=m+m//2+m//4,
                            contraction_edge_visits=3*(m+m//2+m//4),contraction_output_vertices=n//2+n//4,
                            contraction_output_edges=m//2+m//4)
                        if name == 'kkt':
                            eighth = variant == 'eighth'; q = 0 if n == 4096 else 17+case_index+gi+si+int(eighth)
                            stats.update(kkt_calls=3+int(eighth),root_after_two_vertices=n//4,root_after_two_edges=m//4,
                                sampling_calls=1,verifier_calls=1,sampling_edge_visits=m//4,verifier_edges=m//4,
                                sampled_edges=m//(32 if eighth else 8),hash_insert_items=n-1,verifier_queries=q,
                                path_query_visits=2*q+q//3,verifier_tree_edges=q+5,verifier_tree_calls=int(q > 0),
                                fbt_output_vertices=2*q,initialized_slots=7 if eighth else 0,
                                hash_lookup_calls=0 if eighth else 5,
                                edge_materializations=21+case_index+gi+si if eighth else 31+case_index+gi+si)
                        else: stats['hash_insert_items'] = None
                        algorithms[name] = dict(work=stats,hash_insert_items_status='measured' if name == 'kkt' else 'unmeasured')
                    raw = dict(schema='retention_control_work_v1',validation='pass',certified_output_items=n-1,
                               **{key:value for key,value in spec.items() if key not in ('variant','intrusion_per_mille')},
                               algorithms=algorithms,rounds={name:copy.deepcopy(rounds) for name in ('compacting_boruvka','multigraph_boruvka')})
                    values.append((spec,raw))
    return values


def expected_tables(values):
    """Literal raw-table oracle; no audit aggregation calls."""
    tables = {key:[] for key in ('work','rounds','round_chains','query_work','paired_kkt_work')}
    by_identity = {}; first_seen = []
    for spec,raw in values:
        for name in ('kkt','compacting_boruvka','multigraph_boruvka'):
            counters = raw['algorithms'][name]['work']
            tables['work'].append({**spec,'algorithm':name,'hash_insert_items_status':raw['algorithms'][name]['hash_insert_items_status'],**counters})
            if name != 'kkt':
                replay = raw['rounds'][name]
                tables['rounds'].extend({**spec,'algorithm':name,**r} for r in replay)
                sums = {field+'_sum':sum(row[field] for row in replay)
                        for field in ('vertices','edges','selected','output_vertices','output_edges')}
                tables['round_chains'].append({**spec,'algorithm':name,'rounds':len(replay),**sums})
        counters = raw['algorithms']['kkt']['work']; q = counters['verifier_queries']; u = counters['path_query_visits']-q-q
        tables['query_work'].append({**spec,'Q':q,'U':u,'M':counters['verifier_tree_edges'],'T':counters['verifier_tree_calls'],
            'Nsum':counters['fbt_output_vertices'],'U_over_Q':Fraction(u,q) if q else None,
            'query_fraction_status':'defined' if q else 'both_zero','collapsed_requests':q-u,
            'sampling_calls':counters['sampling_calls'],'sampling_edge_visits':counters['sampling_edge_visits'],
            'engine_words':counters['sampling_edge_visits'],'engine_word_method':'exact_scalar_one_draw_per_visited_edge'})
        key = spec['case_id'],spec['graph_seed'],spec['kkt_seed']
        if key not in first_seen: first_seen.append(key)
        by_identity[key+(spec['variant'],)] = (spec,counters)
    for key in first_seen:
        spec,half = by_identity[key+('half',)]; _,eighth = by_identity[key+('eighth',)]
        for field in audit.FIELDS:
            a,b = half[field],eighth[field]
            tables['paired_kkt_work'].append({**{k:v for k,v in spec.items() if k != 'variant'},'counter':field,
                'half':a,'eighth':b,'eighth_minus_half':b-a,'eighth_over_half':Fraction(b,a) if a else None,
                'ratio_status':'defined' if a else 'half_zero' if b else 'both_zero'})
    return tables


def json_file(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,allow_nan=False)+'\n')


def csv_file(path,rows):
    with path.open('w',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=list(rows[0])); writer.writeheader()
        writer.writerows({key:float(value) if isinstance(value,Fraction) else value for key,value in row.items()} for row in rows)


def fixture(directory):
    root = Path(directory).resolve(); values = synthetic_values(); capture = root/'capture-attempt01.json'
    registry = root/'work_metrics.hpp'
    registry.write_text('\n'.join('{"'+name+'", &kkt_work::WorkStats::'+name+', false},' for name in audit.FIELDS))
    binaries = {variant:root/(variant+'-binary') for variant in ('half','eighth')}
    for path in binaries.values(): path.write_text('synthetic not executable: '+path.name)
    identities = [{key:spec[key] for key in ('variant','case_id','graph_seed','kkt_seed')} for spec,raw in values]
    timing_freeze = root/'timing-freeze.json'; json_file(timing_freeze,{'schedule':identities})
    timing_capture = root/'eighth.json'; timed = []
    for identity,(spec,raw) in zip(identities,values):
        certificate = {key:raw[key] for key in ('case_id','graph_seed','kkt_seed','n','m','input_fingerprint','topology_fingerprint','validation')}
        timed.append(dict(identity,validation='pass',rows=42,certificate=certificate))
    json_file(timing_capture,dict(schema='eighth_sampling_capture_v1',validation='pass',freeze=str(timing_freeze),
        freeze_sha256=audit.sha(timing_freeze),frozen_protocol={'schedule':identities},captures=timed))
    bound = {str(path):audit.sha(path) for path in (registry,timing_freeze,timing_capture,*binaries.values())}
    freeze = root/'freeze.json'
    frozen = dict(schema='eighth_sampling_work_freeze_v1',timing_capture=str(timing_capture),counter_fields=list(audit.FIELDS),
        counter_boundary=audit.BOUNDARY,expected_children=48,expected_solver_outputs=144,child_deadline_seconds=1800,
        resource_rule={'rss_limit_kib':40*1024*1024,'poll_seconds':2},bound_sha256=bound,
        variants={key:{'binary':str(path)} for key,path in binaries.items()},schedule=[spec for spec,raw in values])
    json_file(freeze,frozen); capture_bound = {**bound,str(freeze):audit.sha(freeze)}; items = []
    stamp = '2026-10-15T00:00:00+00:00'
    for index,(spec,raw) in enumerate(values,1):
        stem = f"{index:04d}_{spec['variant']}_{spec['case_id']}_g{spec['graph_seed']}_s{spec['kkt_seed']}"
        directory = root/'capture-attempt01_cases'; directory.mkdir(exist_ok=True)
        raw_path,log_path,rss_path = (directory/(stem+suffix) for suffix in ('.json','.log','.rss.jsonl'))
        json_file(raw_path,raw); cert = timed[index-1]['certificate']; log_path.write_text('reference_certificate_v1 '+json.dumps(cert)+'\n')
        start = index*1000; group = 100+index; observations = []; events = []
        for offset,members in ((1,[{'pid':group,'rss_kib':3}]),(40,[])):
            request = start+offset
            observations.append(dict(validation='pass',process_group=group,monotonic_ns=request,utc=stamp,
                                     members=members,rss_kib=sum(row['rss_kib'] for row in members)))
            events.append(dict(process_group=group,requested_monotonic_ns=request,returned_monotonic_ns=request+2,
                provider_started_monotonic_ns=request,provider_finished_monotonic_ns=request+1,
                previous_request_gap_ns=None if offset == 1 else 39,sampler_duration_ns=2,outcome='pass'))
        rss_path.write_text(''.join(json.dumps(row)+'\n' for row in observations))
        command = ['/usr/bin/arch','-arm64',str(binaries[spec['variant']]),spec['family'],
                   str(spec['n']),str(spec['density']),str(spec['graph_seed']),str(spec['kkt_seed'])]
        items.append(dict(spec=spec,validation='pass',exit_status=0,interruption=None,command=command,launch_command=command,
            process_group=group,started_utc=stamp,finished_utc=stamp,started_monotonic_ns=start,finished_monotonic_ns=start+50,
            wrapper_exit_monotonic_ns=start+30,monotonic_elapsed_seconds=50/1e9,
            raw=str(raw_path),raw_sha256=audit.sha(raw_path),log=str(log_path),log_sha256=audit.sha(log_path),
            rss_log=str(rss_path),rss_sha256=audit.sha(rss_path),rss_observations=2,rss_unavailable=0,
            rss_nonempty_observations=1,sampled_peak_rss_kib=3,group_exit_verification=observations[-1],
            recovery_monitor={'observations':events,'max_sampler_duration_ns':2,'max_request_gap_ns':39},certificate=cert))
    info = dict(schema='eighth_sampling_work_capture_v1',validation='pass',cleanup=[],native_process_may_still_be_running=False,
        checked_children=48,checked_solver_outputs=144,counter_boundary=audit.BOUNDARY,freeze=str(freeze),
        freeze_sha256=audit.sha(freeze),bound_sha256=capture_bound,captures=items,started_utc=stamp,finished_utc=stamp,
        started_monotonic_ns=1,finished_monotonic_ns=49000)
    json_file(capture,info); analysis = root/'analysis'; analysis.mkdir()
    for name,rows in expected_tables(values).items(): csv_file(analysis/(name+'.csv'),rows)
    json_file(analysis/'provenance.json',dict(validation='pass',capture=str(capture),capture_sha256=audit.sha(capture),
        bound_sha256=capture_bound,counter_boundary=audit.BOUNDARY,solver_rows=144,paired_kkt_counter_rows=1560,
        query_rows=48,replay_chains=96,engine_words_exact=True,performance_claim=False))
    return capture,analysis,registry,audit.sha(timing_freeze)


class AuditTests(unittest.TestCase):
    def test_complete_cartesian_numeric_oracle(self):
        values = synthetic_values(); tables,exact,twins = audit.reconstruct(values)
        self.assertEqual(tables,expected_tables(values))
        self.assertEqual({name:len(rows) for name,rows in tables.items()},
                         {'work':144,'rounds':288,'round_chains':96,'query_work':48,'paired_kkt_work':1560})
        self.assertEqual(len(exact),1608); self.assertEqual(twins,4)
        self.assertEqual(sum(row['hash_insert_items'] is None for row in tables['work']),96)
        pairs = tables['paired_kkt_work']
        self.assertEqual({row['ratio_status'] for row in pairs},{'defined','both_zero','half_zero'})
        self.assertTrue(any(row['eighth_minus_half'] > 0 for row in pairs))
        self.assertTrue(any(row['eighth_minus_half'] < 0 for row in pairs))
        self.assertTrue(any(row['ratio_status'] == 'defined' and row['eighth_over_half'] == Fraction(0) and
                            row['half'] > 0 and row['eighth_minus_half'] < 0 for row in pairs))
        self.assertTrue(any(row['Q'] == 0 for row in tables['query_work']))
        for row in tables['query_work']: self.assertEqual(row['engine_words'],row['sampling_edge_visits'])

    def test_counter_schema_domains_replays_and_policy_controls(self):
        def mutate(kind):
            values = synthetic_values(); spec,raw = values[0]; kkt = raw['algorithms']['kkt']['work']
            if kind == 'bool': kkt['max_depth'] = True
            elif kind == 'overflow': kkt['max_depth'] = 2**64
            elif kind == 'negative': kkt['max_depth'] = -1
            elif kind == 'missing': del kkt['max_depth']
            elif kind == 'null': raw['algorithms']['multigraph_boruvka']['work']['hash_insert_items'] = 0
            elif kind == 'comparator': values[1][1]['algorithms']['compacting_boruvka']['work']['median_entries'] = 1
            elif kind == 'root': kkt['root_after_two_edges'] += 1
            elif kind == 'Q': kkt['path_query_visits'] = kkt['verifier_queries']
            elif kind == 'sample': kkt['sampled_edges'] = kkt['sampling_edge_visits']+1
            elif kind == 'replay': raw['rounds']['multigraph_boruvka'][1]['selected'] -= 1
            elif kind == 'sum': raw['algorithms']['compacting_boruvka']['work']['contraction_vertices'] += 1
            elif kind == 'certificate': raw['certified_output_items'] -= 1
            elif kind == 'graph': values[1][0]['input_fingerprint'] += 1; values[1][1]['input_fingerprint'] += 1
            elif kind == 'order': values[0],values[1] = values[1],values[0]
            elif kind == 'missing_child': values.pop()
            elif kind == 'duplicate_child': values[-1] = copy.deepcopy(values[0])
            elif kind == 'no_Q':
                for _,record in values:
                    record['algorithms']['kkt']['work'].update(verifier_queries=0,path_query_visits=0)
            return values
        for kind in ('bool','overflow','negative','missing','null','comparator','root','Q','sample','replay','sum',
                     'certificate','graph','order','missing_child','duplicate_child','no_Q'):
            with self.subTest(kind=kind),self.assertRaises(ValueError): audit.reconstruct(mutate(kind))

    def test_full_raw_and_analysis_fixture_no_collector_import(self):
        with tempfile.TemporaryDirectory() as directory:
            capture,analysis,registry,pin = fixture(directory)
            with mock.patch.object(audit,'TIMING_FREEZE_SHA',pin):
                result = audit.audit(capture,analysis,Path(directory)/'audit',registry)
            self.assertEqual((result['counter_cells'],result['paired_kkt_counter_rows'],result['replay_chains']),(9360,1560,96))
            self.assertFalse(result['collector_imported']); self.assertFalse(result['native_execution'])
            with mock.patch.object(audit,'TIMING_FREEZE_SHA',pin),self.assertRaises(ValueError):
                audit.audit(capture,analysis,Path(directory)/'audit',registry)

    def test_raw_certificate_schedule_resource_hash_and_binding_negatives(self):
        for kind in ('missing','order','certificate','false_certificate','extra_version','wrong_version','float_certificate',
                     'float_sidecar_certificate','schema','late_exit','group','hash','bound','timing_join'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as directory:
                capture,analysis,registry,pin = fixture(directory); info = json.loads(capture.read_text()); item = info['captures'][0]
                if kind == 'missing': info['captures'].pop()
                elif kind == 'order': info['captures'][0],info['captures'][1] = info['captures'][1],info['captures'][0]
                elif kind in ('certificate','false_certificate'):
                    certificate = dict(item['certificate']); certificate['validation'] = 'failed'
                    Path(item['log']).write_text('' if kind == 'certificate' else 'reference_certificate_v1 '+json.dumps(certificate)+'\n')
                    item['log_sha256'] = audit.sha(item['log'])
                elif kind in ('extra_version','wrong_version','float_certificate'):
                    path = Path(item['log']); certificate = dict(item['certificate'])
                    if kind == 'float_certificate':
                        certificate['n'] = float(certificate['n'])
                        path.write_text('reference_certificate_v1 '+json.dumps(certificate)+'\n')
                    elif kind == 'extra_version': path.write_text(path.read_text()+'reference_certificate_v2 '+json.dumps(certificate)+'\n')
                    else: path.write_text('reference_certificate_v2 '+json.dumps(certificate)+'\n')
                    item['log_sha256'] = audit.sha(path)
                elif kind == 'float_sidecar_certificate': item['certificate']['n'] = float(item['certificate']['n'])
                elif kind == 'schema': info['checked_solver_outputs'] = True
                elif kind == 'late_exit': item['wrapper_exit_monotonic_ns'] += 1800*10**9
                elif kind == 'group': item['group_exit_verification']['members'] = [{'pid':999,'rss_kib':1}]
                elif kind == 'hash': Path(item['raw']).write_text('{}\n')
                elif kind == 'bound': info['bound_sha256'].pop(str(registry))
                elif kind == 'timing_join': item['spec']['input_fingerprint'] += 1
                json_file(capture,info)
                with mock.patch.object(audit,'TIMING_FREEZE_SHA',pin),self.assertRaises(ValueError): audit.raw_capture(capture,{})

    def test_same_identity_numeric_null_and_table_shape_mutations(self):
        tables = expected_tables(synthetic_values())
        for kind in ('integer','ratio','null','delta','identity','missing','duplicate','header'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/'table.csv'; expected = tables['paired_kkt_work']; rows = copy.deepcopy(expected)
                if kind == 'integer': rows[0]['half'] += 1
                elif kind == 'ratio': rows[0]['eighth_over_half'] += Fraction(1,7)
                elif kind == 'null': next(row for row in rows if row['ratio_status'] == 'half_zero')['eighth_over_half'] = Fraction(0)
                elif kind == 'delta': rows[0]['eighth_minus_half'] *= -1
                elif kind == 'identity': rows[0]['counter'] = 'wrong'
                elif kind == 'missing': rows.pop()
                elif kind == 'duplicate': rows[-1] = copy.deepcopy(rows[0])
                csv_file(path,rows)
                if kind == 'header': path.write_text('counter,counter\nx,x\n')
                with self.assertRaises(ValueError): audit.check_table(path,expected)

    def test_strict_json_registry_and_analysis_provenance(self):
        for text in ('{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}'):
            with self.assertRaises(ValueError): audit.parse_json(text)
        with self.assertRaises(ValueError): audit.utc('2026-10-15T00:00:00-07:00')
        for kind in ('metadata','registry','artifact'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as directory:
                capture,analysis,registry,pin = fixture(directory)
                if kind == 'metadata':
                    metadata = json.loads((analysis/'provenance.json').read_text()); metadata['engine_words_exact'] = False
                    json_file(analysis/'provenance.json',metadata)
                elif kind == 'registry': registry.write_text(registry.read_text().replace('WorkStats::max_depth','WorkStats::min_depth'))
                else: (Path(directory)/'half-binary').write_text('changed')
                with mock.patch.object(audit,'TIMING_FREEZE_SHA',pin),self.assertRaises(ValueError):
                    audit.audit(capture,analysis,Path(directory)/'audit',registry)


if __name__ == '__main__': unittest.main(verbosity=2)
