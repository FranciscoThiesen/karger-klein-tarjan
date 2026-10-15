#!/usr/bin/env python3
"""Independently audit the complete half/eighth diagnostic counters and tables.

Standard library only; no collector import or aggregation reuse. Run after the
separate strict collector verification, which owns the full native build proof.
This supplementary audit rehashes that proof's complete bound inventory and
independently reads child identities, certificates, counters and replay chains.
"""
import argparse
import csv
from datetime import datetime, timedelta
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent.parent
VARIANTS = ('half', 'eighth')
ALGORITHMS = ('kkt', 'compacting_boruvka', 'multigraph_boruvka')
GRAPHS = (15000011, 15000031)
SAMPLERS = (2609, 2617)
CASES = (('leaf_hierarchy4',65536,32), ('leaf_shuffled4',65536,32),
         ('leaf_hierarchy4',1048576,32), ('leaf_shuffled4',1048576,32),
         ('gnm_random',4096,16), ('gnm_random',1048576,16))
TIMING_FREEZE_SHA = '2be7556d15b58f3f65cc380ac22b67c57fdf8aea747d651b9d648c6a1aa59d2f'
BOUNDARY = 'Includes tuple-to-Edge input construction, solver, and temporary input destruction; certification and round replay are outside WorkStats.'
IDENTITY = ('variant','case_id','graph_seed','kkt_seed')
CERTIFICATE = ('case_id','graph_seed','kkt_seed','n','m','input_fingerprint','topology_fingerprint','validation')
ROUND_FIELDS = ('round','vertices','edges','selected','output_vertices','output_edges')
FIELDS = tuple('''kkt_calls kkt_vertices kkt_edges current_depth max_depth root_after_two_vertices
root_after_two_edges contraction_calls contraction_vertices contraction_edges contraction_vertex_visits
contraction_edge_visits contraction_arc_visits contraction_output_vertices contraction_output_edges
isolation_calls isolation_vertex_visits isolation_edge_visits sampling_calls sampling_edge_visits
sampled_edges kkt_edge_visits filtered_edges verifier_calls verifier_vertices verifier_edges
verifier_forest_edges verifier_components verifier_tree_calls verifier_tree_vertices verifier_tree_edges
verifier_vertex_visits verifier_edge_visits verifier_arc_visits verifier_queries fbt_calls
fbt_input_vertices fbt_rounds fbt_round_vertices fbt_round_edges fbt_vertex_visits fbt_edge_visits
fbt_arc_visits fbt_output_vertices path_init_vertices path_visit_vertices path_query_visits
path_binary_search_calls path_binary_search_steps path_max_height median_entries lca_calls lca_queries
lca_vertices lca_euler_entries lca_log_entries lca_block_scan_visits lca_sparse_cells lca_mask_slots
lca_micro_tables lca_micro_cells initialized_slots edge_materializations hash_lookup_calls hash_insert_items'''.split())


def require(condition, message):
    if not condition: raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''): digest.update(block)
    return digest.hexdigest()


def checked(path, inputs, expected=None):
    path = Path(path).resolve(strict=True); digest = sha(path)
    require(expected is None or digest == expected, 'hash mismatch: '+str(path))
    require(str(path) not in inputs or inputs[str(path)] == digest, 'input changed: '+str(path))
    inputs[str(path)] = digest
    return path


def parse_json(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate JSON key'); result[key] = value
        return result
    def nonfinite(value): raise ValueError('nonfinite JSON: '+value)
    return json.loads(text, object_pairs_hook=unique, parse_constant=nonfinite)


def read_json(path, inputs, expected=None):
    return parse_json(checked(path, inputs, expected).read_text())


def equal(actual, expected, message):
    require(type(actual) is type(expected) and actual == expected, message)


def certificate_equal(actual, expected, message):
    require(type(actual) is dict and set(actual) == set(expected) == set(CERTIFICATE), message+' schema')
    for key in CERTIFICATE: equal(actual[key], expected[key], message+' '+key)


def integer(value):
    require(type(value) is int and 0 <= value < 2**64, 'invalid unsigned native integer')
    return value


def utc(text):
    value = datetime.fromisoformat(text)
    require(value.utcoffset() == timedelta(0), 'timestamp is not UTC')


def declared_schedule():
    cases = [dict(case_id=f'{family}_n{n}_d{density}_p0', family=family, n=n,
                  density=density, intrusion_per_mille=0, m=n*density) for family,n,density in CASES]
    return [dict(variant=variant, **case, graph_seed=graph, kkt_seed=sampler)
            for gi,graph in enumerate(GRAPHS) for si,sampler in enumerate(SAMPLERS)
            for case in (cases if gi == 0 else list(reversed(cases)))
            for variant in (VARIANTS if (gi+si)%2 == 0 else tuple(reversed(VARIANTS)))]


def resources(item, inputs):
    observations = [parse_json(line) for line in checked(item['rss_log'], inputs, item['rss_sha256']).read_text().splitlines()]
    events = item['recovery_monitor']['observations']
    require(observations and len(events) == len(observations) == item['rss_observations'], 'missing resource evidence')
    previous = None; unavailable = consecutive = nonempty = 0; peaks = []
    for observation,event in zip(observations,events):
        request = integer(observation['monotonic_ns']); returned = integer(event['returned_monotonic_ns'])
        require(item['started_monotonic_ns'] <= request <= returned <= item['finished_monotonic_ns'], 'resource interval')
        require(previous is None or request > previous, 'resource observations out of order')
        require(observation['process_group'] == event['process_group'] == item['process_group'] and
                event['requested_monotonic_ns'] == request, 'resource group/request mismatch')
        equal(event['previous_request_gap_ns'], None if previous is None else request-previous, 'request gap')
        equal(event['sampler_duration_ns'], returned-request, 'sampler duration')
        require(request <= integer(event['provider_started_monotonic_ns']) <=
                integer(event['provider_finished_monotonic_ns']) <= returned, 'provider interval')
        require(event['outcome'] == observation['validation'] and event['outcome'] in ('pass','unavailable'), 'poisoned monitor')
        utc(observation['utc']); previous = request
        if observation['validation'] == 'unavailable':
            unavailable += 1; consecutive += 1
            require(consecutive < 3, 'three unavailable observations'); continue
        consecutive = 0; members = observation['members']; pids = set()
        require(type(members) is list, 'invalid resource members')
        for member in members:
            pid = integer(member['pid']); integer(member['rss_kib'])
            require(pid > 0 and pid not in pids, 'duplicate/invalid resource PID'); pids.add(pid)
        rss = integer(observation['rss_kib'])
        require(rss == sum(member['rss_kib'] for member in members) <= 40*1024*1024, 'RSS sum/limit')
        peaks.append(rss); nonempty += bool(members)
    equal(item['rss_unavailable'], unavailable, 'unavailable resource count')
    equal(item['rss_nonempty_observations'], nonempty, 'nonempty resource count')
    equal(item['sampled_peak_rss_kib'], max(peaks,default=None), 'sampled peak')
    equal(item['recovery_monitor']['max_sampler_duration_ns'], max(event['sampler_duration_ns'] for event in events), 'max sampler duration')
    equal(item['recovery_monitor']['max_request_gap_ns'], max(event['previous_request_gap_ns'] or 0 for event in events), 'max request gap')
    last = observations[-1]; equal(item['group_exit_verification'], last, 'final group evidence')
    require(last['validation'] == 'pass' and last['members'] == [], 'final owned group not known empty')
    exit_time = integer(item['wrapper_exit_monotonic_ns'])
    require(item['started_monotonic_ns'] <= exit_time <= last['monotonic_ns'] <= item['finished_monotonic_ns'] and
            exit_time-item['started_monotonic_ns'] <= 1800*10**9, 'late/unknown native exit')


def raw_capture(path, inputs):
    capture = checked(path, inputs); info = read_json(capture, inputs)
    for key,value in dict(schema='eighth_sampling_work_capture_v1', validation='pass', cleanup=[],
            native_process_may_still_be_running=False, checked_children=48, checked_solver_outputs=144,
            counter_boundary=BOUNDARY).items(): equal(info[key], value, 'capture '+key)
    require('error' not in info, 'failed capture')
    frozen = read_json(info['freeze'], inputs, info['freeze_sha256'])
    for key,value in dict(schema='eighth_sampling_work_freeze_v1', counter_fields=list(FIELDS),
            counter_boundary=BOUNDARY, expected_children=48, expected_solver_outputs=144,
            child_deadline_seconds=1800).items(): equal(frozen[key], value, 'freeze '+key)
    equal(frozen['resource_rule']['rss_limit_kib'], 40*1024*1024, 'RSS declaration')
    equal(frozen['resource_rule']['poll_seconds'], 2, 'poll declaration')
    bound = dict(frozen['bound_sha256']); bound[str(Path(info['freeze']).resolve())] = info['freeze_sha256']
    equal(info['bound_sha256'], bound, 'complete frozen bound inventory')
    for source,digest in bound.items(): checked(source, inputs, digest)
    timing_path = str(Path(frozen['timing_capture']).resolve(strict=True))
    require(timing_path in bound, 'timing capture not bound')
    timing = read_json(timing_path, inputs, bound[timing_path])
    equal(timing['schema'], 'eighth_sampling_capture_v1', 'timing capture schema')
    equal(timing['validation'], 'pass', 'timing capture status')
    equal(timing['freeze_sha256'], TIMING_FREEZE_SHA, 'timing declaration changed')
    timing_freeze = read_json(timing['freeze'], inputs, TIMING_FREEZE_SHA)
    equal(timing['frozen_protocol'], timing_freeze, 'timing frozen declaration')
    schedules = declared_schedule()
    require(len(info['captures']) == len(frozen['schedule']) == len(timing['captures']) == 48, 'incomplete child matrix')
    equal(timing_freeze['schedule'], [{k:spec[k] for k in IDENTITY} for spec in schedules], 'timing schedule')
    begin,end = integer(info['started_monotonic_ns']),integer(info['finished_monotonic_ns'])
    require(begin < end, 'capture interval'); utc(info['started_utc']); utc(info['finished_utc'])
    previous = begin; values = []
    for index,(declared,spec,item,timed) in enumerate(zip(schedules,frozen['schedule'],info['captures'],timing['captures']),1):
        require(set(spec) == set(declared) | {'input_fingerprint','topology_fingerprint'}, 'work spec schema')
        for key,value in declared.items(): equal(spec[key], value, 'prospective work identity '+key)
        for name in ('input_fingerprint','topology_fingerprint'): integer(spec[name])
        equal(item['spec'], spec, 'child spec')
        for key,value in dict(validation='pass', exit_status=0, interruption=None).items(): equal(item[key], value, 'child '+key)
        for key in IDENTITY: equal(timed[key], spec[key], 'timing join '+key)
        equal(timed['validation'], 'pass', 'timing child status'); equal(timed['rows'],42,'timing child rows')
        certificate = {key:('pass' if key == 'validation' else spec[key]) for key in CERTIFICATE}
        certificate_equal(timed['certificate'], certificate, 'timing certificate/fingerprint join')
        integer(item['process_group']); require(item['process_group'] > 0, 'invalid owned group')
        start,finish = integer(item['started_monotonic_ns']),integer(item['finished_monotonic_ns'])
        require(previous <= start < finish <= end, 'overlapping/invalid child interval'); previous = finish
        equal(item['monotonic_elapsed_seconds'], (finish-start)/1e9, 'child elapsed time')
        utc(item['started_utc']); utc(item['finished_utc'])
        binary = frozen['variants'][spec['variant']]['binary']
        require(binary in bound, 'diagnostic binary not bound')
        command = ['/usr/bin/arch','-arm64',binary,spec['family'],*[str(spec[k]) for k in ('n','density','graph_seed','kkt_seed')]]
        equal(item['command'], command, 'native command'); equal(item['launch_command'], command, 'native launch command')
        stem = f"{index:04d}_{spec['variant']}_{spec['case_id']}_g{spec['graph_seed']}_s{spec['kkt_seed']}"
        directory = capture.with_name(capture.stem+'_cases')
        for field,suffix,hash_field in (('raw','.json','raw_sha256'),('log','.log','log_sha256'),('rss_log','.rss.jsonl','rss_sha256')):
            equal(item[field], str(directory/(stem+suffix)), 'raw evidence path')
            checked(item[field], inputs, item[hash_field])
        lines = [line for line in Path(item['log']).read_text().splitlines() if line.startswith('reference_certificate')]
        require(len(lines) == 1 and lines[0].startswith('reference_certificate_v1 '), 'absent/duplicate/unsupported certificate')
        certificate_equal(parse_json(lines[0][len('reference_certificate_v1 '):]), certificate, 'raw independent certificate')
        certificate_equal(item['certificate'], certificate, 'sidecar certificate'); resources(item, inputs)
        values.append((spec,read_json(item['raw'], inputs, item['raw_sha256'])))
    return info,values


def reconstruct(values):
    require(len(values) == 48, 'incomplete counter matrix')
    seen = set(); graph_identity = {}; comparators = {}; paired = {}; positive_q = False
    tables = {name:[] for name in ('work','rounds','round_chains','query_work','paired_kkt_work')}
    exact = []
    for declared,(spec,raw) in zip(declared_schedule(),values):
        for key,value in declared.items(): equal(spec[key],value,'counter matrix identity '+key)
        identity = tuple(spec[k] for k in IDENTITY); require(identity not in seen,'duplicate counter input'); seen.add(identity)
        base = {'schema':'retention_control_work_v1','validation':'pass','certified_output_items':spec['n']-1,
                **{key:value for key,value in spec.items() if key not in ('variant','intrusion_per_mille')}}
        require(set(raw) == set(base) | {'algorithms','rounds'}, 'raw output schema')
        for key,value in base.items(): equal(raw[key],value,'raw output '+key)
        require(set(raw['algorithms']) == set(ALGORITHMS) and set(raw['rounds']) == set(ALGORITHMS[1:]), 'solver/replay set')
        graph_key = spec['case_id'],spec['graph_seed']; fingerprints = tuple(spec[k] for k in ('input_fingerprint','topology_fingerprint'))
        require(graph_key not in graph_identity or graph_identity[graph_key] == fingerprints, 'graph changes across policies/samplers')
        graph_identity[graph_key] = fingerprints
        signature = ([raw['algorithms'][name] for name in ALGORITHMS[1:]],raw['rounds'])
        require(graph_key not in comparators or comparators[graph_key] == signature, 'comparator changes across policies/samplers')
        comparators[graph_key] = signature
        for name in ALGORITHMS:
            record = raw['algorithms'][name]; require(set(record) == {'work','hash_insert_items_status'},'algorithm schema')
            stats = record['work']; require(set(stats) == set(FIELDS), 'counter schema')
            for field,count in stats.items():
                if name != 'kkt' and field == 'hash_insert_items': require(count is None,'invented comparator hash count')
                else: integer(count)
            status = 'measured' if name == 'kkt' else 'unmeasured'
            equal(record['hash_insert_items_status'],status,'hash measurement status')
            equal(stats['current_depth'],0,'recursion not unwound')
            require(stats['contraction_edge_visits'] <= (4 if name == 'compacting_boruvka' else 3)*stats['contraction_edges'], 'contraction scan bound')
            tables['work'].append(dict(spec,algorithm=name,hash_insert_items_status=status,**stats))
            if name == 'kkt': continue
            require(all(stats[k] == 0 for k in ('kkt_calls','sampling_calls','verifier_calls')), 'comparator invokes KKT')
            replay = raw['rounds'][name]; require(type(replay) is list and len(replay) == stats['contraction_calls'],'round count')
            vertices,edges,selected = spec['n'],spec['m'],0
            sums = {key:0 for key in ROUND_FIELDS if key != 'round'}
            for index,row in enumerate(replay):
                require(set(row) == set(ROUND_FIELDS),'round schema')
                for count in row.values(): integer(count)
                require((row['round'],row['vertices'],row['edges']) == (index,vertices,edges),'broken round chain')
                require(row['output_vertices'] <= vertices//2 and row['output_edges'] <= edges,'round failed to shrink')
                require((row['output_vertices'] == 0) == (row['output_edges'] == 0),'terminal dimensions')
                require(row['selected'] == vertices-(row['output_vertices'] if row['output_edges'] else 1),'connected selected-edge count')
                selected += row['selected']; vertices,edges = row['output_vertices'],row['output_edges']
                for key in sums: sums[key] += row[key]
                tables['rounds'].append(dict(spec,algorithm=name,**row))
            require(vertices == edges == 0 and selected == spec['n']-1,'incomplete spanning replay')
            for key in ('vertices','edges','output_vertices','output_edges'):
                equal(stats['contraction_'+key],sums[key],'replay counter sum')
            tables['round_chains'].append(dict(spec,algorithm=name,rounds=len(replay),**{key+'_sum':value for key,value in sums.items()}))
        stats = raw['algorithms']['kkt']['work']; equal(stats['hash_insert_items'],spec['n']-1,'certified unique MST count')
        require(stats['sampling_calls'] == stats['verifier_calls'] and stats['sampling_edge_visits'] == stats['verifier_edges'] and
                stats['sampled_edges'] <= stats['sampling_edge_visits'] and
                (stats['sampling_calls'] > 0 or stats['sampling_edge_visits'] == 0),'sampling/verifier accounting')
        retained = raw['rounds']['multigraph_boruvka']
        for key in ('vertices','edges'):
            equal(stats['root_after_two_'+key],retained[1]['output_'+key] if len(retained) >= 2 else 0,'shared first two contractions')
        q = stats['verifier_queries']; u = stats['path_query_visits']-2*q; require(0 <= u <= q,'cumulative U outside [0,Q]')
        positive_q |= q > 0
        fraction = Fraction(u,q) if q else None
        tables['query_work'].append(dict(spec,Q=q,U=u,M=stats['verifier_tree_edges'],T=stats['verifier_tree_calls'],
            Nsum=stats['fbt_output_vertices'],U_over_Q=fraction,query_fraction_status='defined' if q else 'both_zero',
            collapsed_requests=q-u,sampling_calls=stats['sampling_calls'],sampling_edge_visits=stats['sampling_edge_visits'],
            engine_words=stats['sampling_edge_visits'],engine_word_method='exact_scalar_one_draw_per_visited_edge'))
        exact.append(dict(spec,quantity='U_over_Q',numerator=None if fraction is None else fraction.numerator,
                          denominator=None if fraction is None else fraction.denominator,status='defined' if q else 'both_zero'))
        paired.setdefault(tuple(spec[k] for k in ('case_id','graph_seed','kkt_seed')), {})[spec['variant']] = (spec,stats)
    require(len(seen) == 48 and len(graph_identity) == 12 and len(paired) == 24 and positive_q,'incomplete/nonpositive full matrix')
    twins = 0
    for n in (65536,1048576):
        for graph in GRAPHS:
            first = graph_identity[f'leaf_hierarchy4_n{n}_d32_p0',graph]
            second = graph_identity[f'leaf_shuffled4_n{n}_d32_p0',graph]
            require(first[1] == second[1] and first[0] != second[0],'topology twins or nonvacuous weights'); twins += 1
    for variants in paired.values():
        require(set(variants) == set(VARIANTS),'missing rate pair')
        spec,half = variants['half']; _,eighth = variants['eighth']; common = {key:value for key,value in spec.items() if key != 'variant'}
        for field in FIELDS:
            a,b = half[field],eighth[field]; ratio = Fraction(b,a) if a else None
            status = 'defined' if a else 'both_zero' if b == 0 else 'half_zero'
            tables['paired_kkt_work'].append(dict(common,counter=field,half=a,eighth=b,eighth_minus_half=b-a,
                                                 eighth_over_half=ratio,ratio_status=status))
            exact.append(dict(common,quantity=field,numerator=None if ratio is None else ratio.numerator,
                              denominator=None if ratio is None else ratio.denominator,status=status))
    require(len(tables['work']) == 144 and len(tables['round_chains']) == 96 and len(tables['query_work']) == 48 and
            len(tables['paired_kkt_work']) == 1560,'counter table coverage')
    return tables,exact,twins


def check_table(path, expected):
    with Path(path).open(newline='') as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames is not None and len(set(reader.fieldnames)) == len(reader.fieldnames),'duplicate/absent CSV header')
        rows = list(reader)
    require(len(rows) == len(expected),'table row count: '+str(path))
    for actual,wanted in zip(rows,expected):
        require(set(actual) == set(wanted) and None not in actual and None not in actual.values(),'table schema: '+str(path))
        for key,value in wanted.items():
            # The producer exports native ints exactly and rational convenience
            # values through Python's nearest binary64 division, not a decimal fit.
            text = '' if value is None else str(float(value)) if isinstance(value,Fraction) else str(value)
            require(actual[key] == text,'table value differs: '+str(path)+' '+key)


def audit(capture, analysis_dir, output, metrics_header=ROOT/'benchmark/work_metrics.hpp'):
    output = Path(output).resolve(); require(not output.exists(),'refusing audit overwrite')
    inputs = {}; checked(__file__,inputs); info,values = raw_capture(capture,inputs)
    metrics = checked(metrics_header,inputs)
    require(str(metrics) in info['bound_sha256'],'counter registry not bound')
    pairs = re.findall(r'\{\s*"([a-z_0-9]+)"\s*,\s*&kkt_work::WorkStats::([a-z_0-9]+)\s*,\s*(?:true|false)\s*\}',metrics.read_text())
    require(pairs == [(name,name) for name in FIELDS] and len(FIELDS) == len(set(FIELDS)) == 65,'member-bound counter registry')
    tables,exact,twins = reconstruct(values)
    for name,rows in tables.items(): check_table(checked(Path(analysis_dir)/(name+'.csv'),inputs),rows)
    metadata = read_json(Path(analysis_dir)/'provenance.json',inputs)
    for key,value in dict(validation='pass',capture=str(Path(capture).resolve()),capture_sha256=inputs[str(Path(capture).resolve())],
            bound_sha256=info['bound_sha256'],counter_boundary=BOUNDARY,solver_rows=144,paired_kkt_counter_rows=1560,
            query_rows=48,replay_chains=96,engine_words_exact=True,performance_claim=False).items(): equal(metadata[key],value,'analysis provenance '+key)
    for path,digest in inputs.items(): require(sha(path) == digest,'audit input drift: '+path)
    output.mkdir(parents=True)
    # A uniform schema accommodates 48 per-solve query and 1,560 cross-rate rows.
    keys = list(dict.fromkeys(key for row in exact for key in row))
    with (output/'exact_counter_ratios.csv').open('x',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=keys); writer.writeheader(); writer.writerows(exact)
    result = dict(schema='independent_eighth_work_counter_audit_v1',validation='pass',checked_children=48,solver_rows=144,
        counter_fields=65,counter_cells=9360,unmeasured_hash_counter_cells=96,replay_chains=96,
        replay_round_rows=len(tables['rounds']),query_rows=48,paired_kkt_counter_rows=1560,exact_ratio_records=len(exact),
        topology_twins=twins,comparator_graph_identities=12,engine_words_exact=True,cross_rate_equal_work_required=False,
        collector_imported=False,aggregation_reused=False,native_execution=False,performance_claim=False,
        strict_native_build_proof='Separate completed collector verification required; full bound inventory rehashed here.',
        input_sha256=inputs,bound_sha256=info['bound_sha256'])
    with (output/'audit.json').open('x') as stream: json.dump(result,stream,indent=2); stream.write('\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',type=Path,required=True)
    parser.add_argument('--analysis-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args = parser.parse_args(); result = audit(args.capture,args.analysis_dir,args.output_dir)
    print(json.dumps({key:value for key,value in result.items() if key not in ('input_sha256','bound_sha256')},indent=2))
