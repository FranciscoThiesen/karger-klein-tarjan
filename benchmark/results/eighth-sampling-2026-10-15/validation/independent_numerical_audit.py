#!/usr/bin/env python3
"""Independent eighth-sampling raw numerical audit; no collector code is imported.

PREPARED ONLY during timing. Execute after root releases post-capture analysis.
Exact Fraction arithmetic checks all pairs, crossed-realization summaries and
crossover predicates. This supplements the frozen collector's strict analysis.
"""
import argparse
from collections import Counter, defaultdict
import csv
import datetime
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parent.parent
ALGORITHMS = ('kkt', 'compacting_boruvka', 'multigraph_boruvka', 'kruskal', 'prim', 'boruvka')
VARIANTS = ('half', 'eighth')
GRAPHS, SAMPLERS = (15000011, 15000031), (2609, 2617)
REALIZATIONS = {(graph, sampler) for graph in GRAPHS for sampler in SAMPLERS}
PARENT_SHA256 = 'bd65da13058d3e9cfa58919a0fe5e02b8a46b1d0b8fe7f05801692d5a0866df9'
FREEZE_SHA256 = '2be7556d15b58f3f65cc380ac22b67c57fdf8aea747d651b9d648c6a1aa59d2f'
TEXT = {'case_id', 'family', 'phase', 'algorithm', 'validation'}
FIELDS = ('case_id', 'family', 'n', 'm', 'density', 'intrusion_per_mille', 'graph_seed', 'kkt_seed',
          'input_fingerprint', 'topology_fingerprint', 'phase', 'repetition', 'order', 'warmups', 'algorithm',
          'elapsed_ns', 'utc_start_ns', 'utc_end_ns', 'process_cpu_start_ns', 'process_cpu_end_ns',
          'process_cpu_elapsed_ns', 'validation')
CERTIFICATE = ('case_id', 'graph_seed', 'kkt_seed', 'n', 'm', 'input_fingerprint', 'topology_fingerprint', 'validation')
IDENTITY = ('case_id', 'family', 'n', 'm', 'density', 'intrusion_per_mille')
METRICS = {'wall': 'elapsed_ns', 'cpu': 'process_cpu_elapsed_ns'}
EXPECTED_CASES = {(family, n, 32, 0) for family in ('leaf_hierarchy4', 'leaf_shuffled4') for n in (65536, 1048576)} \
    | {('gnm_random', n, 16, 0) for n in (4096, 1048576)}
DECLARED_CASES = (('leaf_hierarchy4',65536,32,0),('leaf_shuffled4',65536,32,0),
                  ('leaf_hierarchy4',1048576,32,0),('leaf_shuffled4',1048576,32,0),
                  ('gnm_random',4096,16,0),('gnm_random',1048576,16,0))
TABLE_COUNTS = {'paired_ratios': 2880, 'comparisons': 120, 'realization_comparisons': 480,
                'graph_comparisons': 240, 'sampling_comparisons': 240,
                'summary': 144, 'realization_summary': 576, 'graph_summary': 288, 'sampling_summary': 288,
                'variant_pairs': 1728, 'variant_comparisons': 72, 'realization_variant_comparisons': 288,
                'graph_variant_comparisons': 144, 'sampling_variant_comparisons': 144,
                'strong_crossover_classifications': 30}
INPUTS = {}


def require(condition, message):
    if not condition: raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked(path, expected=None):
    path = Path(path).resolve(strict=True); value = digest(path)
    require(expected is None or value == expected, 'hash mismatch: ' + str(path))
    require(str(path) not in INPUTS or INPUTS[str(path)] == value, 'input changed during audit: ' + str(path))
    INPUTS[str(path)] = value
    return path


def parse_json(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate JSON key: ' + key); result[key] = value
        return result
    def nonfinite(value): raise ValueError('nonfinite JSON: ' + value)
    return json.loads(text, object_pairs_hook=unique, parse_constant=nonfinite)


def read_json(path, expected=None):
    return parse_json(checked(path, expected).read_text())


def read_csv(path, fields=None):
    with Path(path).open(newline='') as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames is not None and len(set(reader.fieldnames)) == len(reader.fieldnames), 'duplicate/absent CSV header')
        require(fields is None or tuple(reader.fieldnames) == fields, 'CSV header mismatch: ' + str(path))
        rows = list(reader)
    require(all(None not in row and None not in row.values() for row in rows), 'malformed CSV')
    return rows


def native_integer(value,name):
    require(type(value) is str and bool(value) and all('0' <= char <= '9' for char in value),
            'expected unsigned decimal native field: '+name)
    result = int(value)
    require(result <= (2**63-1 if name.endswith('_ns') else 2**64-1),
            'native integer outside its recorded domain: '+name)
    return result


def write_csv(directory, name, rows):
    require(bool(rows), 'empty output table: ' + name)
    with (directory / (name + '.csv')).open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def exact_fields(value, name):
    value = Fraction(value)
    return {name: float(value), name + '_numerator': value.numerator, name + '_denominator': value.denominator}


def hash_freeze(path, expected=None, seen=None):
    """Reread declared original-parent and current artifacts without importing their checkers."""
    seen = set() if seen is None else seen
    path = checked(path, expected); require(str(path) not in seen, 'cyclic parent proof'); seen.add(str(path))
    frozen = read_json(path)
    root = Path(frozen['working_directory'])
    for field in ('source_sha256', 'build_recipe_sha256'):
        for name, value in frozen[field].items(): checked(root / name, value)
    for name, value in frozen['python_source_sha256'].items(): checked(name, value)
    for field in ('manifest', 'protocol'): checked(frozen[field], frozen[field + '_sha256'])
    items = list(frozen['variants'].values()) if 'variants' in frozen else [frozen]
    for item in items:
        checked(item['binary'], item['binary_sha256'])
        record = read_json(item['build']['path'], item['build']['sha256'])
        require(record == item['build']['record'] and record['build_exit_status'] == 0, 'build receipt mismatch')
        require(record['source_sha256'] == frozen['source_sha256'], 'build/freeze source inventory differs')
        checked(record['build_log'], record['build_log_sha256'])
        for name, object_path in record.get('object_paths', {}).items(): checked(object_path, record['object_sha256'][name])
        if 'main_object' in record: checked(record['main_object'], record['main_object_sha256'])
    if 'parent_freeze' in frozen: hash_freeze(frozen['parent_freeze'], frozen['parent_freeze_sha256'], seen)
    return frozen


def parse_utc(value):
    parsed = datetime.datetime.fromisoformat(value)
    require(parsed.tzinfo is not None and parsed.utcoffset() == datetime.timedelta(0), 'timestamp is not explicit UTC')
    return parsed


def utc_flags(info):
    start = parse_utc(info['started_utc']); finish = parse_utc(info['finished_utc'])
    result = []; previous = start
    if finish < start: result.append({'scope': 'capture', 'flag': 'utc_reversed_interval'})
    for index, child in enumerate(info['captures'], 1):
        a = parse_utc(child['started_utc']); b = parse_utc(child['finished_utc'])
        scope = 'child ' + str(index)
        if b < a: result.append({'scope': scope, 'flag': 'utc_reversed_interval'})
        if a < previous: result.append({'scope': scope, 'flag': 'utc_reversed_between_children'})
        if a < start or b > finish: result.append({'scope': scope, 'flag': 'utc_interval_outside_capture'})
        previous = b
    return result


def resources(child):
    observations = [parse_json(line) for line in checked(child['rss_log'], child['rss_sha256']).read_text().splitlines()]
    require(observations, 'missing resource evidence')
    events = child['recovery_monitor']['observations']
    require(len(events) == len(observations) == child['rss_observations'], 'resource/event count mismatch')
    prior = None; unavailable = consecutive = nonempty = 0; peaks = []
    for observation, event in zip(observations, events):
        request = observation['monotonic_ns']; returned = event['returned_monotonic_ns']
        require(type(request) is int and child['started_monotonic_ns'] <= request <= returned <= child['finished_monotonic_ns'], 'invalid resource interval')
        require(prior is None or request > prior, 'nonincreasing resource observations')
        require(observation['process_group'] == event['process_group'] == child['process_group'] and
                event['requested_monotonic_ns'] == request, 'wrong monitored group/request')
        require(event['previous_request_gap_ns'] == (None if prior is None else request-prior) and
                event['sampler_duration_ns'] == returned-request, 'wrong monitor duration/gap')
        require(request <= event['provider_started_monotonic_ns'] <= event['provider_finished_monotonic_ns'] <= returned,
                'invalid bounded-provider interval')
        require(event['outcome'] == observation['validation'] and event['outcome'] in ('pass','unavailable'), 'poisoned/invalid sampler')
        parse_utc(observation['utc']); prior = request
        if observation['validation'] == 'unavailable':
            unavailable += 1; consecutive += 1
            require(consecutive < 3, 'three unavailable observations'); continue
        consecutive = 0; members = observation['members']; pids = set()
        for member in members:
            require(type(member['pid']) is int and member['pid'] > 0 and member['pid'] not in pids and
                    type(member['rss_kib']) is int and member['rss_kib'] >= 0, 'invalid resource member')
            pids.add(member['pid'])
        require(observation['rss_kib'] == sum(member['rss_kib'] for member in members) <= 40*1024*1024, 'RSS sum/ceiling mismatch')
        peaks.append(observation['rss_kib']); nonempty += bool(members)
    require(child['rss_unavailable'] == unavailable and child['rss_nonempty_observations'] == nonempty and
            child['sampled_peak_rss_kib'] == max(peaks, default=None), 'resource summary mismatch')
    require(child['recovery_monitor']['max_sampler_duration_ns'] == max(event['sampler_duration_ns'] for event in events) and
            child['recovery_monitor']['max_request_gap_ns'] == max(event['previous_request_gap_ns'] or 0 for event in events), 'monitor summary mismatch')
    last = observations[-1]
    require(child['group_exit_verification'] == last and last['validation'] == 'pass' and not last['members'] and
            child['started_monotonic_ns'] <= child['wrapper_exit_monotonic_ns'] <= last['monotonic_ns'], 'unverified final empty group')


def raw_capture(path):
    info = read_json(path)
    require(info['schema'] == 'eighth_sampling_capture_v1' and info['validation'] == 'pass', 'wrong/incomplete capture')
    require(info['rows_removed'] == info['rows_adjusted'] == 0 and info['cleanup'] == [] and
            info['native_process_may_still_be_running'] is False and 'error' not in info, 'altered/uncertain capture')
    require(info['freeze_sha256'] == FREEZE_SHA256, 'wrong prospective eighth freeze')
    freeze = hash_freeze(info['freeze'], FREEZE_SHA256)
    require(freeze == info['frozen_protocol'] and freeze['schema'] == 'eighth_sampling_freeze_v1', 'freeze mismatch')
    require(freeze['parent_freeze_sha256'] == PARENT_SHA256 and set(freeze['variants']) == set(VARIANTS), 'wrong parent/variants')
    root = Path(freeze['working_directory'])
    actual_sources = {str(p.relative_to(root)) for p in set(root.glob('*/*.cpp')) | set(root.glob('*/*.hpp'))}
    require(actual_sources == set(freeze['source_sha256']), 'native source inventory changed')
    first, second = (freeze['variants'][variant]['build']['record'] for variant in VARIANTS)
    for field in ('source_sha256','build_recipe_sha256','compiler','compiler_command','sdk','build_commands','main_object','main_object_sha256'):
        require(first[field] == second[field], 'paired build field differs: ' + field)
    for name in first['object_paths']:
        if name != 'kkt/kkt.o':
            require(first['object_paths'][name] == second['object_paths'][name] and first['object_sha256'][name] == second['object_sha256'][name], 'shared object differs')
    require(first['object_sha256']['kkt/kkt.o'] != second['object_sha256']['kkt/kkt.o'], 'identical KKT objects')
    require(len(first['object_paths']) == len(second['object_paths']) == 8 and
            set(first['object_paths']) == set(second['object_paths']), 'wrong production object inventory')
    for variant,record in zip(VARIANTS,(first,second)):
        policy = {'sampling_policy':variant,'private_acceptance_mask':1 if variant == 'half' else 7,
                  'sampling_words_per_visited_edge':1,'verifier_policy':'compressed'}
        require(record['schema'] == 'eighth_sampling_build_v1' and record['profile'] == 'timing-build' and
                record['variant'] == variant and record['role'] == 'timing_never_executed' and
                record['compressed_queries_fixed'] is True and record['public_scalar_sampling_fixed'] is True and
                record['seven_non_kkt_objects_identical_by_construction'] is True,
                'wrong fresh sampling build policy')
        require(len(record['executables']) == 1, 'wrong timing executable inventory')
        for target in (record,record['executables'][0]):
            require(all(type(target.get(key)) is type(value) and target[key] == value for key,value in policy.items()),
                    'wrong typed predicate policy')
        require(record['binary_profile']['file_description'] == 'Mach-O 64-bit executable arm64' and
                record['binary_profile']['main_stack_bytes'] == 536870912, 'wrong native profile')
    commands = first['build_commands']
    require(len(commands) == 12, 'wrong compile/link command count')
    require([i for i,command in enumerate(commands) if '-DKKT_EXPERIMENT_COMPRESSED_QUERIES' in command] == [6] and
            commands[6][commands[6].index('-c')+1] == 'verifier/verifier_v2.cpp' and
            [i for i,command in enumerate(commands) if '-DKKT_EXPERIMENT_EIGHTH_SAMPLING' in command] == [8] and
            commands[8][commands[8].index('-c')+1] == 'kkt/kkt.cpp', 'opt-in macro placed on wrong object')
    manifest = read_csv(freeze['manifest'], ('family','n','density','intrusion_per_mille')); specs = {}
    for raw in manifest:
        spec = {name: value if name == 'family' else int(value) for name,value in raw.items()}
        spec['m'] = spec['n'] * spec['density']; spec['case_id'] = f"{spec['family']}_n{spec['n']}_d{spec['density']}_p{spec['intrusion_per_mille']}"
        require(spec['case_id'] not in specs, 'duplicate manifest case'); specs[spec['case_id']] = spec
    require(len(specs) == 6 and {(s['family'],s['n'],s['density'],s['intrusion_per_mille']) for s in specs.values()} == EXPECTED_CASES, 'wrong case matrix')
    require(tuple(tuple(s[name] for name in ('family','n','density','intrusion_per_mille')) for s in specs.values())
            == DECLARED_CASES, 'wrong literal manifest order')
    require(freeze['algorithms'] == list(ALGORITHMS) and freeze['graph_seeds'] == list(GRAPHS) and freeze['sampling_seeds'] == list(SAMPLERS)
            and freeze['repetitions'] == 6 and freeze['warmups'] == 1, 'wrong solver/seed/replication matrix')
    require(freeze['resource_rule']['rss_limit_kib'] == 40*1024*1024 and freeze['resource_rule']['poll_seconds'] == 2, 'wrong resource rule')
    schedule = [{'variant': variant, 'case_id': case, 'graph_seed': graph, 'kkt_seed': sampler}
                for gi,graph in enumerate(GRAPHS) for si,sampler in enumerate(SAMPLERS)
                for case in (list(specs) if gi == 0 else list(reversed(specs)))
                for variant in (VARIANTS if (gi+si)%2 == 0 else tuple(reversed(VARIANTS)))]
    require(freeze['schedule'] == schedule and len(info['captures']) == 48, 'wrong adjacent balanced schedule')
    all_rows = []; all_raw = []; diagnostics = []; certificates = []; fingerprints = {}
    output = checked(info['output'],info['output_sha256']); require(output.with_suffix('.json') == Path(path).resolve(), 'sidecar/output mismatch')
    previous_end = info['started_monotonic_ns']; finish = info['finished_monotonic_ns']
    require(info['monotonic_elapsed_seconds'] == (finish-previous_end)/1e9 and finish > previous_end, 'capture duration mismatch')
    for index,(child,identity) in enumerate(zip(info['captures'],schedule),1):
        variant,case,graph,sampler = (identity[name] for name in ('variant','case_id','graph_seed','kkt_seed'))
        require(all(child[name] == value for name,value in identity.items()), 'child schedule mismatch')
        require(child['exit_status'] == 0 and child['validation'] == 'pass' and child['interruption'] is None and child['rows'] == 42, 'incomplete native child')
        require(previous_end <= child['started_monotonic_ns'] < child['finished_monotonic_ns'] <= finish, 'overlapping child intervals')
        require(child['monotonic_elapsed_seconds'] == (child['finished_monotonic_ns']-child['started_monotonic_ns'])/1e9, 'child duration mismatch')
        previous_end = child['finished_monotonic_ns']
        raw_path = output.with_name(output.stem+'_cases') / f'{index:04d}_{variant}_{case}_g{graph}_s{sampler}.csv'
        require(child['csv'] == str(raw_path) and child['log'] == str(raw_path.with_suffix('.log')) and child['rss_log'] == str(raw_path.with_suffix('.rss.jsonl')), 'child evidence paths differ')
        checked(raw_path,child['output_sha256']); log = checked(child['log'],child['log_sha256']); resources(child)
        argv = [freeze['variants'][variant]['binary'],'--family',specs[case]['family'],'--n',str(specs[case]['n']),
                '--density',str(specs[case]['density']),'--graph-seed',str(graph),'--kkt-seed',str(sampler),'--repetitions','6','--warmups','1']
        require(child['command'] == argv and child['launch_command'] == ['/usr/bin/time','-l',*argv], 'native command mismatch')
        raw = read_csv(raw_path,FIELDS); require(len(raw) == 42, 'wrong native row count')
        rows = [{name: value if name in TEXT else native_integer(value,name) for name,value in row.items()} for row in raw]
        expected = [(phase,rep,order,ALGORITHMS[(order+rep)%6]) for phase,reps in (('warmup',1),('timed',6)) for rep in range(reps) for order in range(6)]
        positions = Counter(); previous_cpu = previous_utc = None; child_flags = 0
        for row,call in zip(rows,expected):
            require(all(row[name] == value for name,value in specs[case].items()), 'graph differs from manifest')
            require((row['phase'],row['repetition'],row['order'],row['algorithm']) == call, 'wrong solver position')
            require((row['graph_seed'],row['kkt_seed'],row['warmups'],row['validation']) == (graph,sampler,1,'pass'), 'seed/result differs')
            cpu,wall = row['process_cpu_elapsed_ns'],row['elapsed_ns']; utc = row['utc_end_ns']-row['utc_start_ns']
            require(cpu > 0 and wall > 0 and row['utc_start_ns'] > 0 and row['utc_end_ns'] > 0 and
                    row['process_cpu_end_ns']-row['process_cpu_start_ns'] == cpu, 'clock endpoint/duration mismatch')
            require(previous_cpu is None or row['process_cpu_start_ns'] >= previous_cpu, 'CPU intervals overlap')
            threshold = max(2_000_000_000,cpu); flags = []
            if utc < 0: flags.append('realtime_reversed_within_call')
            if previous_utc is not None and row['utc_start_ns'] < previous_utc: flags.append('realtime_reversed_between_calls')
            if 4*(wall-cpu) > threshold: flags.append('steady_exceeds_process_cpu')
            if 4*(cpu-wall) > threshold: flags.append('process_cpu_exceeds_steady')
            if 4*abs(utc-wall) > threshold: flags.append('utc_steady_duration_disagreement')
            child_flags += bool(flags); previous_cpu,previous_utc = row['process_cpu_end_ns'],row['utc_end_ns']
            diagnostics.append({'variant':variant,'case_id':case,'graph_seed':graph,'kkt_seed':sampler,
                **dict(zip(('phase','repetition','order','algorithm'),call)), 'elapsed_ns':wall,'process_cpu_elapsed_ns':cpu,
                'utc_elapsed_ns':utc,'steady_minus_cpu_ns':wall-cpu,'utc_minus_steady_ns':utc-wall,'diagnostic_flags':flags,'excluded':False})
            fingerprint = row['input_fingerprint'],row['topology_fingerprint']
            require((case,graph) not in fingerprints or fingerprints[(case,graph)] == fingerprint, 'graph differs across variants/samplers')
            fingerprints[(case,graph)] = fingerprint
            if row['phase'] == 'timed': positions[(row['algorithm'],row['order'])] += 1
        require(child_flags == child['flagged_calls'] and positions == Counter({(algorithm,order):1 for algorithm in ALGORITHMS for order in range(6)}), 'flags/rotation mismatch')
        markers = []
        for line in log.read_text().splitlines():
            if line.startswith('reference_certificate'):
                require(line.startswith('reference_certificate_v1 '),'wrong certificate version')
                markers.append(parse_json(line[len('reference_certificate_v1 '):]))
        expected_certificate = {name:rows[0][name] for name in CERTIFICATE}
        require(len(markers) == 1 and markers[0] == child['certificate'] == expected_certificate, 'certificate/input mismatch')
        require(all(type(markers[0][name]) is type(value) for name,value in expected_certificate.items()), 'certificate type mismatch')
        certificates.append({'variant':variant,**markers[0]}); all_rows.extend({'variant':variant,**row} for row in rows)
        all_raw.extend({'variant':variant,**row} for row in raw)
    twins = []
    for n in (65536,1048576):
        for graph in GRAPHS:
            a,b = (fingerprints[(f'{family}_n{n}_d32_p0',graph)] for family in ('leaf_hierarchy4','leaf_shuffled4'))
            require(a[1] == b[1] and a[0] != b[0], 'invalid/vacuous topology twin')
            twins.append({'n':n,'density':32,'graph_seed':graph,'topology_fingerprint':a[1],
                          'hierarchy_input_fingerprint':a[0],'shuffled_input_fingerprint':b[0]})
    counts = len(all_rows),sum(row['phase']=='timed' for row in all_rows),sum(row['phase']=='warmup' for row in all_rows)
    require(counts == (2016,1728,288) == (info['checked_rows'],info['checked_timed_rows'],info['checked_warmup_rows']), 'wrong output counts')
    require(diagnostics == info['call_diagnostics'] and sum(bool(row['diagnostic_flags']) for row in diagnostics) == info['flagged_calls'], 'diagnostics mismatch')
    require(utc_flags(info) == info['capture_clock_flags'], 'capture UTC flags mismatch')
    require(read_csv(output,('variant',*FIELDS)) == all_raw, 'combined CSV not exact child concatenation')
    return info,specs,all_rows,certificates,twins


def numerical_tables(rows,specs):
    """Group raw integers independently; all ratios, medians and ranges stay rational."""
    blocks = {}; pairs = {}; durations = defaultdict(list)
    for row in rows:
        if row['phase'] != 'timed': continue
        variant,case,graph,sampler,rep,algorithm = (row[name] for name in ('variant','case_id','graph_seed','kkt_seed','repetition','algorithm'))
        block = blocks.setdefault((variant,case,graph,sampler,rep),{})
        require(algorithm not in block,'duplicate solver'); block[algorithm] = row
        pair = pairs.setdefault((case,graph,sampler,rep,algorithm),{})
        require(variant not in pair,'duplicate variant'); pair[variant] = row
        for metric,field in METRICS.items(): durations[(variant,case,algorithm,metric,graph,sampler)].append(Fraction(row[field]))
    tables = defaultdict(list); within = defaultdict(list); across = defaultdict(list)
    for (variant,case,graph,sampler,rep),block in blocks.items():
        require(set(block) == set(ALGORITHMS),'incomplete solver block')
        for competitor in ALGORITHMS[1:]:
            for metric,field in METRICS.items():
                ratio = Fraction(block['kkt'][field],block[competitor][field])
                within[(variant,case,competitor,metric,graph,sampler)].append(ratio)
                tables['paired_ratios'].append({'variant':variant,**specs[case],'graph_seed':graph,'kkt_seed':sampler,
                    'repetition':rep,'competitor':competitor,'metric':metric,'kkt_ns':block['kkt'][field],
                    'competitor_ns':block[competitor][field],'kkt_over_competitor':ratio})
    for (case,graph,sampler,rep,algorithm),block in pairs.items():
        require(set(block) == set(VARIANTS),'incomplete variant block')
        for metric,field in METRICS.items():
            ratio = Fraction(block['eighth'][field],block['half'][field])
            across[(case,algorithm,metric,graph,sampler)].append(ratio)
            tables['variant_pairs'].append({**specs[case],'graph_seed':graph,'kkt_seed':sampler,'repetition':rep,
                'algorithm':algorithm,'metric':metric,'half_ns':block['half'][field],
                'eighth_ns':block['eighth'][field],'eighth_over_half':ratio})

    def summarize(collection,dimensions,name,value_name,is_ratio):
        pools = defaultdict(dict)
        for key,values in collection.items():
            identity = dict(zip((*dimensions,'graph_seed','kkt_seed'),key))
            require(len(values) == 6,'wrong per-realization replication')
            realization = key[-2:]; require(realization in REALIZATIONS,'wrong realization')
            pools[key[:-2]][realization] = values
        for key,realizations in pools.items():
            require(set(realizations) == REALIZATIONS,'incomplete realization matrix')
            identity = dict(zip(dimensions,key)); common = {**specs[identity['case_id']],**identity}
            def summary(values,extra=None):
                result = {**common,**(extra or {}),value_name:statistics.median(values),
                          'trial_min':min(values),'trial_max':max(values),'trials':len(values)}
                if is_ratio: result['individual_wins'] = sum(value < 1 for value in values)
                return result
            for (graph,sampler),values in realizations.items():
                tables['realization_'+name].append(summary(values,{'graph_seed':graph,'kkt_seed':sampler}))
            extrema = {}
            for prefix,index,seeds,field in (('graph',0,GRAPHS,'graph_seed'),('sampling',1,SAMPLERS,'kkt_seed')):
                medians = []
                for seed in seeds:
                    values = [value for realization,group in realizations.items() if realization[index] == seed for value in group]
                    require(len(values) == 12,'wrong marginal replication')
                    row = summary(values,{field:seed}); tables[prefix+'_'+name].append(row); medians.append(row[value_name])
                extrema.update({prefix+'_min':min(medians),prefix+'_max':max(medians)})
            values = [value for group in realizations.values() for value in group]
            require(len(values) == 24,'wrong pooled replication')
            medians = [statistics.median(group) for group in realizations.values()]
            tables[name].append(summary(values,{'realization_min':min(medians),'realization_max':max(medians),**extrema}))
    summarize(within,('variant','case_id','competitor','metric'),'comparisons','median_paired_ratio',True)
    summarize(across,('case_id','algorithm','metric'),'variant_comparisons','median_paired_ratio',True)
    summarize(durations,('variant','case_id','algorithm','metric'),'summary','median_ns',False)
    tables['strong_crossover_classifications'],points,brackets = crossovers(tables,specs)
    require({name:len(values) for name,values in tables.items()} == TABLE_COUNTS,'wrong numerical table cardinalities')
    return dict(tables),points,brackets


def crossovers(tables,specs):
    medians = {(r['variant'],r['case_id'],r['competitor'],r['metric'],r['graph_seed'],r['kkt_seed']):r['median_paired_ratio']
               for r in tables['realization_comparisons']}
    require(len(medians) == 480,'duplicate realization medians')
    groups = defaultdict(list)
    for case,spec in specs.items(): groups[(spec['family'],spec['density'])].append((spec['n'],case))
    def state(values):
        if all(value <= Fraction(9,10) for value in values): return 'strong_lead'
        if all(value < 1 for value in values): return 'narrow_lead'
        if all(value > 1 for value in values): return 'loss'
        return 'mixed_or_tied'
    rows = []; points = []; brackets = []
    for variant in VARIANTS:
        for (family,density),cases in sorted(groups.items()):
            cases.sort(); require(len(cases) == 2,'wrong crossover endpoints')
            for competitor in ALGORITHMS[1:]:
                values = []
                for n,case in cases:
                    sample = [medians[(variant,case,competitor,metric,graph,sampler)]
                              for metric in METRICS for graph in GRAPHS for sampler in SAMPLERS]
                    values.append(sample)
                    points.append({'variant':variant,'family':family,'density':density,'competitor':competitor,'n':n,'state':state(sample),
                        **{f'{metric}_g{graph}_s{sampler}':medians[(variant,case,competitor,metric,graph,sampler)]
                           for metric in METRICS for graph in GRAPHS for sampler in SAMPLERS}})
                low,high = values; small_state,large_state = state(low),state(high)
                strong = all(value > 1 for value in low) and all(value <= Fraction(9,10) for value in high)
                rows.append({'variant':variant,'family':family,'density':density,'competitor':competitor,
                    'small_n':cases[0][0],'large_n':cases[1][0],'small_state':small_state,'large_state':large_state,
                    'strong_crossover':strong,'small_realization_clock_min':min(low),'small_realization_clock_max':max(low),
                    'large_realization_clock_min':min(high),'large_realization_clock_max':max(high)})
                for field in ('small_realization_clock_min','small_realization_clock_max',
                              'large_realization_clock_min','large_realization_clock_max'):
                    value = rows[-1][field]
                    rows[-1][field+'_numerator'] = value.numerator
                    rows[-1][field+'_denominator'] = value.denominator
                classification = ('strong_observed_crossover' if strong else 'strong_lead_entire_measured_range'
                    if small_state == large_state == 'strong_lead' else 'loss_entire_measured_range'
                    if small_state == large_state == 'loss' else 'no_strong_observed_crossover')
                brackets.append({'variant':variant,'family':family,'density':density,'competitor':competitor,
                    'classification':classification,'lower_measured_n':cases[0][0] if strong else None,
                    'upper_measured_n':cases[1][0] if strong else None,'small_state':small_state,'large_state':large_state})
    require(len(rows) == len(brackets) == 30 and len(points) == 60,'wrong crossover cardinalities')
    return rows,points,brackets


def table_keys(name):
    if name == 'strong_crossover_classifications': return ('variant','family','density','competitor')
    across = name == 'variant_pairs' or name.endswith('variant_comparisons')
    absolute = name.endswith('summary')
    keys = (*(() if across else ('variant',)),'case_id','algorithm' if across or absolute else 'competitor','metric')
    if name in ('paired_ratios','variant_pairs'): return (*keys,'graph_seed','kkt_seed','repetition')
    if name.startswith('realization_'): return (*keys,'graph_seed','kkt_seed')
    if name.startswith('graph_'): return (*keys,'graph_seed')
    if name.startswith('sampling_'): return (*keys,'kkt_seed')
    return keys


def verify_table(path,expected_rows,keys):
    actual = read_csv(checked(path)); expected = {tuple(str(row[field]) for field in keys):row for row in expected_rows}
    require(len(expected) == len(expected_rows) == len(actual),'table cardinality mismatch: '+path.name)
    seen = set()
    for row in actual:
        key = tuple(row[field] for field in keys)
        require(key in expected and key not in seen,'duplicate/foreign table identity: '+path.name); seen.add(key)
        target = expected[key]; require(set(row) == set(target),'table field schema mismatch: '+path.name)
        for field,value in target.items():
            if isinstance(value,Fraction):
                require(math.isclose(float(row[field]),float(value),rel_tol=1e-15,abs_tol=0),
                        'exact-rational numerical mismatch: '+path.name+'/'+field)
            else:
                require(row[field] == str(value),'exact table field mismatch: '+path.name+'/'+field)
    require(seen == set(expected),'missing table identities')


def rational_export(rows):
    result = []
    for row in rows:
        item = {}
        for name,value in row.items():
            if isinstance(value,Fraction): item.update(exact_fields(value,name))
            else: item[name] = value
        result.append(item)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',type=Path,default=ROOT/'paired.json')
    parser.add_argument('--analysis-dir',type=Path,default=ROOT/'analysis')
    parser.add_argument('--output-dir',type=Path,default=ROOT/'validation/independent-numerical-audit')
    args = parser.parse_args(); require(not args.output_dir.exists(),'refusing to overwrite independent audit')
    info,specs,rows,certificates,twins = raw_capture(args.capture)
    tables,points,brackets = numerical_tables(rows,specs)
    for name,expected in tables.items(): verify_table(args.analysis_dir/(name+'.csv'),expected,table_keys(name))
    provenance = read_json(args.analysis_dir/'provenance.json')
    require(provenance['schema'] == 'eighth_sampling_analysis_v1' and provenance['validation'] == 'pass' and
            provenance['capture'] == info and provenance['checked_rows'] == 2016 and
            provenance['rows_removed'] == provenance['rows_adjusted'] == 0,'strict analysis provenance mismatch')
    for path,value in provenance['input_sha256'].items(): checked(path,value)
    checked(__file__)
    wins = [{'variant':variant,'competitor':competitor,'metric':metric,'individual_pairs':144,
             'individual_wins':sum(row['individual_wins'] for row in tables['comparisons']
                                   if (row['variant'],row['competitor'],row['metric']) == (variant,competitor,metric))}
            for variant in VARIANTS for competitor in ALGORITHMS[1:] for metric in METRICS]
    drift = []
    for algorithm in ALGORITHMS:
        for metric in METRICS:
            selected = [row for row in tables['variant_comparisons'] if (row['algorithm'],row['metric']) == (algorithm,metric)]
            drift.append({'algorithm':algorithm,'metric':metric,'individual_pairs':144,
                'eighth_faster_pairs':sum(row['individual_wins'] for row in selected),
                'pooled_case_ratio_min':float(min(row['median_paired_ratio'] for row in selected)),
                'pooled_case_ratio_max':float(max(row['median_paired_ratio'] for row in selected))})
    for name,value in INPUTS.items(): require(digest(name) == value,'input changed during independent audit')
    args.output_dir.mkdir(parents=True)
    for name,values in {**tables,'protocol_point_states':points,'strong_crossover_brackets':brackets,
                        'matched_topology_twins':twins,'certificates':certificates}.items():
        write_csv(args.output_dir,name,rational_export(values))
    report = {'schema':'independent_eighth_sampling_numerical_audit_v1','validation':'pass','collector_imported':False,
        'raw_native_children':48,'certificates':len(certificates),'checked_outputs':2016,'timed_outputs':1728,'warmup_outputs':288,
        'table_counts':{name:len(values) for name,values in tables.items()},'matched_topology_twins':len(twins),
        'clock_flagged_calls':info['flagged_calls'],'capture_clock_flags':info['capture_clock_flags'],
        'strict_analyzer_pairs_medians_ranges_counts_agree':True,'owned_groups_verified_empty':48,
        'arithmetic':'Exact Fraction ratios, medians, ranges and crossover predicates; decimal CSV columns are convenience conversions.',
        'scope':'Independent raw numerical, schedule, certificate, fingerprint, clock, resource and declared-artifact hash audit. It supplements the strict collector source/build recipe proof. No power or sleep-inhibition claim is made here.',
        'within_variant_wins':wins,'cross_variant_drift':drift,'crossover_results':brackets,'input_sha256':INPUTS}
    with (args.output_dir/'audit.json').open('x') as stream: json.dump(report,stream,indent=2); stream.write('\n')
    pooled_within = {(row['variant'],row['case_id'],row['competitor'],row['metric']):row['median_paired_ratio'] for row in tables['comparisons']}
    pooled_across = {(row['case_id'],row['algorithm'],row['metric']):row['median_paired_ratio'] for row in tables['variant_comparisons']}
    text = ['# Independent eighth-sampling numerical audit','','PASS: 48 raw children, 2,016 outputs (1,728 timed and 288 warmup), '
        '1,728 all-solver eighth/half clock pairs and 2,880 within-variant KKT/comparator clock pairs. '
        'All 3,024 case, realization, graph-marginal and sampling-marginal medians, their ranges/counts/wins, '
        'and all 30 crossover classifications agree with strict analysis. All four topology twins, exact certificates, '
        'balanced schedule, clocks, raw/combined concatenation, resource records and empty-group evidence were rechecked. '
        'No collector code was imported. Ratios and crossover predicates use exact rational arithmetic.','',
        '| Case | Eighth / half KKT | Half KKT / multigraph B | Eighth KKT / multigraph B |','|---|---:|---:|---:|']
    for case in specs:
        text.append(f"| {case} | {float(pooled_across[(case,'kkt','wall')]):.6f} | {float(pooled_within[('half',case,'multigraph_boruvka','wall')]):.6f} | {float(pooled_within[('eighth',case,'multigraph_boruvka','wall')]):.6f} |")
    text += ['','Table: pooled 24-trial wall ratios. CSVs retain both clocks, all six solvers, all five direct comparators, '
        'all four realization medians and both marginal dimensions. Six repetitions reuse each realization; two graph seeds '
        'cross two sampler seeds, so there are not four independent graphs or 24 independent samples. Both policies draw '
        'one word per visited edge, but changed acceptance and recursion can produce different later streams despite '
        'matching initial seed numbers. Compressed verification is fixed. Unchanged controls are never used to normalize KKT.','',
        f"Retained flags: {info['flagged_calls']} calls and {len(info['capture_clock_flags'])} capture/child UTC flags.",'',
        'Strong observed crossover brackets:','']
    selected = [row for row in brackets if row['classification'] == 'strong_observed_crossover']
    for row in selected:
        text.append(f"- {row['variant']}: {row['family']}, d={row['density']}, versus {row['competitor']}: ({row['lower_measured_n']:,}, {row['upper_measured_n']:,}] vertices.")
    if not selected: text.append('No prespecified strong crossover bracket was observed.')
    text += ['','Each bracket requires all four realization medians above one at the smaller measured endpoint and at most 0.90 '
        'at the larger endpoint on both clocks. These are exploratory observed endpoints, not interpolated thresholds or proof '
        'of durable/asymptotic dominance. Every loss, narrow/mixed result and lead at both endpoints remains in the tables.','']
    with (args.output_dir/'README.md').open('x') as stream: stream.write('\n'.join(text))
    print(json.dumps({'validation':'pass','checked_outputs':2016,'table_counts':report['table_counts'],
        'strong_crossovers':selected,'within_variant_wins':wins,'cross_variant_drift':drift},indent=2))


if __name__ == '__main__': main()
