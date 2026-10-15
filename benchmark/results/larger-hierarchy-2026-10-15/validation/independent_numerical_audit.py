#!/usr/bin/env python3
"""Independent larger-hierarchy raw numerical audit; no collector code is imported.

Execute only after root releases post-capture analysis of the new study.
Exact Fraction arithmetic checks all pairs, two-graph summaries and
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
GRAPHS, SAMPLERS = (11000009, 11000027), (2203,)
REALIZATIONS = {(graph, sampler) for graph in GRAPHS for sampler in SAMPLERS}
FREEZE_SHA256 = 'd4600df2dee18c98d263a9bc043d2881c16a6cc253d9c99047aede4aaa334f27'
PARENT_SHA256 = 'bd65da13058d3e9cfa58919a0fe5e02b8a46b1d0b8fe7f05801692d5a0866df9'
SIZES = (65536, 1048576, 4194304)
PAIRS = (('leaf_hierarchy4','leaf_shuffled4'),)
# Spell the entire prospective manifest independently of the collector.
DECLARED_CASES = (('leaf_hierarchy4',65536,32,0), ('leaf_shuffled4',65536,32,0),
                  ('leaf_hierarchy4',1048576,32,0), ('leaf_shuffled4',1048576,32,0),
                  ('leaf_hierarchy4',4194304,32,0), ('leaf_shuffled4',4194304,32,0))
TEXT = {'case_id', 'family', 'phase', 'algorithm', 'validation'}
FIELDS = ('case_id', 'family', 'n', 'm', 'density', 'intrusion_per_mille', 'graph_seed', 'kkt_seed',
          'input_fingerprint', 'topology_fingerprint', 'phase', 'repetition', 'order', 'warmups', 'algorithm',
          'elapsed_ns', 'utc_start_ns', 'utc_end_ns', 'process_cpu_start_ns', 'process_cpu_end_ns',
          'process_cpu_elapsed_ns', 'validation')
CERTIFICATE = ('case_id', 'graph_seed', 'kkt_seed', 'n', 'm', 'input_fingerprint', 'topology_fingerprint', 'validation')
IDENTITY = ('case_id', 'family', 'n', 'm', 'density', 'intrusion_per_mille')
METRICS = {'wall': 'elapsed_ns', 'cpu': 'process_cpu_elapsed_ns'}
TABLE_COUNTS = {'paired_ratios':720, 'comparisons':60, 'graph_comparisons':120,
                'summary':72, 'graph_summary':144, 'crossover_points':30,
                'crossover_brackets':30, 'crossover_summary':10}
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
    require(info['schema'] == 'larger_hierarchy_capture_v1' and info['validation'] == 'pass', 'wrong/incomplete capture')
    require(info['rows_removed'] == info['rows_adjusted'] == 0 and info['cleanup'] == [] and
            info['native_process_may_still_be_running'] is False and 'error' not in info, 'altered/uncertain capture')
    require(info['freeze_sha256'] == FREEZE_SHA256, 'wrong larger-hierarchy freeze identity')
    freeze = hash_freeze(info['freeze'], FREEZE_SHA256)
    require(freeze == info['frozen_protocol'] and freeze['schema'] == 'larger_hierarchy_freeze_v1', 'freeze mismatch')
    require(freeze['parent_freeze_sha256'] == PARENT_SHA256, 'wrong compressed parent')
    parent = read_json(freeze['parent_freeze'], PARENT_SHA256)
    inherited = {**parent['variants']['compressed'], **{name:parent[name] for name in ('source_sha256','build_recipe_sha256')}}
    require(all(freeze[name] == value for name,value in inherited.items()), 'not the exact inherited compressed artifact')
    require(freeze['working_directory'] == parent['working_directory'], 'wrong parent worktree')
    require('benchmark/retention_control.cpp' in freeze['source_sha256'], 'missing timed harness main source')
    root = Path(freeze['working_directory'])
    actual_sources = {str(p.relative_to(root)) for p in set(root.glob('*/*.cpp')) | set(root.glob('*/*.hpp'))}
    require(actual_sources == set(freeze['source_sha256']), 'native source inventory changed')
    record = freeze['build']['record']
    require(record['schema'] == 'compressed_query_build_v1' and record['profile'] == 'timing-build' and
            record['variant'] == 'compressed' and record['role'] == 'timing_never_executed', 'wrong candidate build')
    require(record['base_commit'] == '30728a3dedb9f6fc9b52289053e05d78a47ceffd' and
            record['scalar_sampling_fixed'] is True and record['reference_source_textually_unchanged'] is True and
            record['seven_non_verifier_objects_identical_by_construction'] is True, 'missing parent source-isolation proof')
    require(len(record['object_paths']) == 8 and len(record['build_commands']) == 12, 'wrong parent build inventory')
    require(record['binary_profile']['file_description'] == 'Mach-O 64-bit executable arm64' and
            record['binary_profile']['main_stack_bytes'] == 536870912, 'wrong executable profile')
    manifest = read_csv(freeze['manifest'], ('family','n','density','intrusion_per_mille')); specs = {}
    for raw in manifest:
        spec = {name: value if name == 'family' else native_integer(value,name) for name,value in raw.items()}
        spec['m'] = spec['n'] * spec['density']; spec['case_id'] = f"{spec['family']}_n{spec['n']}_d{spec['density']}_p{spec['intrusion_per_mille']}"
        require(spec['case_id'] not in specs, 'duplicate manifest case'); specs[spec['case_id']] = spec
    require(tuple((s['family'],s['n'],s['density'],s['intrusion_per_mille']) for s in specs.values()) == DECLARED_CASES,
            'wrong ordered six-case matrix')
    require(freeze['algorithms'] == list(ALGORITHMS) and freeze['graph_seeds'] == list(GRAPHS) and freeze['sampling_seeds'] == list(SAMPLERS)
            and freeze['repetitions'] == 6 and freeze['warmups'] == 1, 'wrong solver/seed/replication matrix')
    require(freeze['resource_rule']['rss_limit_kib'] == 40*1024*1024 and freeze['resource_rule']['poll_seconds'] == 2, 'wrong resource rule')
    schedule = [{'case_id':case,'graph_seed':graph,'kkt_seed':2203}
                for gi,graph in enumerate(GRAPHS) for case in (list(specs) if gi == 0 else list(reversed(specs)))]
    require(freeze['schedule'] == schedule and len(info['captures']) == 12, 'wrong reversed 12-child schedule')
    all_rows = []; all_raw = []; diagnostics = []; certificates = []; fingerprints = {}
    output = checked(info['output'],info['output_sha256']); require(output.with_suffix('.json') == Path(path).resolve(), 'sidecar/output mismatch')
    previous_end = info['started_monotonic_ns']; finish = info['finished_monotonic_ns']
    require(info['monotonic_elapsed_seconds'] == (finish-previous_end)/1e9 and finish > previous_end, 'capture duration mismatch')
    for index,(child,identity) in enumerate(zip(info['captures'],schedule),1):
        case,graph,sampler = (identity[name] for name in ('case_id','graph_seed','kkt_seed'))
        require(all(child[name] == value for name,value in identity.items()), 'child schedule mismatch')
        require(child['exit_status'] == 0 and child['validation'] == 'pass' and child['interruption'] is None and child['rows'] == 42, 'incomplete native child')
        require(previous_end <= child['started_monotonic_ns'] < child['finished_monotonic_ns'] <= finish, 'overlapping child intervals')
        require(child['monotonic_elapsed_seconds'] == (child['finished_monotonic_ns']-child['started_monotonic_ns'])/1e9, 'child duration mismatch')
        previous_end = child['finished_monotonic_ns']
        raw_path = output.with_name(output.stem+'_cases') / f'{index:04d}_{case}_g{graph}_s{sampler}.csv'
        require(child['csv'] == str(raw_path) and child['log'] == str(raw_path.with_suffix('.log')) and child['rss_log'] == str(raw_path.with_suffix('.rss.jsonl')), 'child evidence paths differ')
        checked(raw_path,child['output_sha256']); log = checked(child['log'],child['log_sha256']); resources(child)
        argv = [freeze['binary'],'--family',specs[case]['family'],'--n',str(specs[case]['n']),
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
            diagnostics.append({'case_id':case,'graph_seed':graph,'kkt_seed':sampler,
                **dict(zip(('phase','repetition','order','algorithm'),call)), 'elapsed_ns':wall,'process_cpu_elapsed_ns':cpu,
                'utc_elapsed_ns':utc,'steady_minus_cpu_ns':wall-cpu,'utc_minus_steady_ns':utc-wall,'diagnostic_flags':flags,'excluded':False})
            fingerprint = row['input_fingerprint'],row['topology_fingerprint']
            require((case,graph) not in fingerprints or fingerprints[(case,graph)] == fingerprint, 'graph fingerprint differs within child')
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
        certificates.append(markers[0]); all_rows.extend(rows)
        all_raw.extend(raw)
    twins = []
    for structured,randomized in PAIRS:
        for n in SIZES:
            for graph in GRAPHS:
                a,b = (fingerprints[(f'{family}_n{n}_d32_p0',graph)] for family in (structured,randomized))
                require(a[1] == b[1] and a[0] != b[0], 'invalid/vacuous topology twin')
                twins.append({'structured_family':structured,'randomized_family':randomized,'n':n,'density':32,
                              'graph_seed':graph,'topology_fingerprint':a[1],
                              'structured_input_fingerprint':a[0],'randomized_input_fingerprint':b[0]})
    require(len(twins) == 6, 'incomplete topology twins')
    counts = len(all_rows),sum(row['phase']=='timed' for row in all_rows),sum(row['phase']=='warmup' for row in all_rows)
    require(counts == (504,432,72) == (info['checked_rows'],info['checked_timed_rows'],info['checked_warmup_rows']), 'wrong output counts')
    require(diagnostics == info['call_diagnostics'] and sum(bool(row['diagnostic_flags']) for row in diagnostics) == info['flagged_calls'], 'diagnostics mismatch')
    require(utc_flags(info) == info['capture_clock_flags'], 'capture UTC flags mismatch')
    require(read_csv(output,FIELDS) == all_raw, 'combined CSV not exact child concatenation')
    return info,specs,all_rows,certificates,twins


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
                require(row[field] == ('' if value is None else str(value)),'exact table field mismatch: '+path.name+'/'+field)
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


def numerical_tables(rows,specs):
    """Build exact tables from native calls without using collector aggregators."""
    blocks = {}; times = defaultdict(lambda: defaultdict(list))
    for row in rows:
        require(row['case_id'] in specs and (row['graph_seed'],row['kkt_seed']) in REALIZATIONS,
                'foreign raw case or realization')
        require(all(row[name] == value for name,value in specs[row['case_id']].items()), 'raw identity differs')
        require(row['phase'] in ('warmup','timed'), 'unknown raw phase')
        if row['phase'] != 'timed': continue
        require(type(row['repetition']) is int and row['repetition'] in range(6) and row['algorithm'] in ALGORITHMS,
                'unknown repetition/solver')
        key = row['case_id'],row['graph_seed'],row['repetition']
        block = blocks.setdefault(key,{})
        require(row['algorithm'] not in block, 'duplicate raw solver call'); block[row['algorithm']] = row
        for metric,field in METRICS.items():
            require(type(row[field]) is int and row[field] > 0, 'nonpositive/noninteger duration')
            times[(row['case_id'],row['algorithm'],metric)][row['graph_seed']].append(row[field])
    expected = {(case,graph,rep) for case in specs for graph in GRAPHS for rep in range(6)}
    require(set(blocks) == expected and all(set(block) == set(ALGORITHMS) for block in blocks.values()),
            'incomplete Cartesian solver blocks')
    pairs = []; ratios = defaultdict(lambda: defaultdict(list))
    for (case,graph,rep),block in blocks.items():
        for comparator in ALGORITHMS[1:]:
            for metric,field in METRICS.items():
                numerator,denominator = block['kkt'][field],block[comparator][field]
                value = Fraction(numerator,denominator)
                pairs.append({**specs[case],'graph_seed':graph,'kkt_seed':2203,'repetition':rep,
                              'competitor':comparator,'metric':metric,'kkt_ns':numerator,
                              'competitor_ns':denominator,'kkt_over_competitor':value})
                ratios[(case,comparator,metric)][graph].append(value)
    tables = {'paired_ratios':pairs,'comparisons':[],'graph_comparisons':[],'summary':[],'graph_summary':[]}
    for grouped,solver_field,median_field,case_name,graph_name in (
            (ratios,'competitor','median_paired_ratio','comparisons','graph_comparisons'),
            (times,'algorithm','median_ns','summary','graph_summary')):
        for (case,solver,metric),graphs in grouped.items():
            require(set(graphs) == set(GRAPHS) and all(len(v)==6 for v in graphs.values()), 'incomplete summary realization')
            graph_medians = []; pooled = []
            for graph in GRAPHS:
                values = graphs[graph]; median = statistics.median([Fraction(value) for value in values])
                graph_medians.append(median); pooled.extend(values)
                item = {**specs[case],solver_field:solver,'metric':metric,'graph_seed':graph,
                        median_field:median,'trial_min':min(values),'trial_max':max(values),'trials':6}
                if solver_field=='competitor':item['individual_wins']=sum(value<1 for value in values)
                tables[graph_name].append(item)
            item = {**specs[case],solver_field:solver,'metric':metric,
                    median_field:statistics.median([Fraction(value) for value in pooled]),
                    'graph_min':min(graph_medians),'graph_max':max(graph_medians),
                    'trial_min':min(pooled),'trial_max':max(pooled),'trials':12}
            if solver_field=='competitor':item['individual_wins']=sum(value<1 for value in pooled)
            tables[case_name].append(item)
    tables.update(crossovers(tables,specs))
    require({name:len(values) for name,values in tables.items()} == TABLE_COUNTS, 'wrong independent table counts')
    return tables


def crossovers(tables,specs):
    """Independently classify every measured point and every size interval."""
    medians = {}
    for row in tables['graph_comparisons']:
        key = row['case_id'],row['competitor'],row['metric'],row['graph_seed']
        require(key not in medians and row['trials']==6, 'duplicate/wrong graph median')
        require(isinstance(row['median_paired_ratio'],Fraction), 'graph median is not exact')
        medians[key]=row['median_paired_ratio']
    expected = {(case,competitor,metric,graph) for case in specs for competitor in ALGORITHMS[1:]
                for metric in METRICS for graph in GRAPHS}
    require(set(medians)==expected, 'missing/foreign crossover medians')
    points,brackets,summaries = [],[],[]
    for family in (family for pair in PAIRS for family in pair):
        cases = sorted((spec['n'],case) for case,spec in specs.items() if spec['family']==family)
        require(tuple(n for n,_ in cases)==SIZES, 'wrong measured size endpoints')
        for competitor in ALGORITHMS[1:]:
            states=[]
            for n,case in cases:
                exact = {(clock,graph):medians[(case,competitor,clock,graph)] for clock in METRICS for graph in GRAPHS}
                values = list(exact.values())
                if max(values)<=Fraction(9,10):state='strong_lead'
                elif max(values)<1:state='narrow_lead'
                elif min(values)>1:state='loss'
                else:state='mixed_or_tied'
                states.append(state)
                row={'family':family,'density':32,'competitor':competitor,'case_id':case,'n':n,'state':state}
                for (clock,graph),value in exact.items():
                    field=f'{clock}_g{graph}'
                    row.update({field:value,field+'_numerator':value.numerator,field+'_denominator':value.denominator})
                points.append(row)
            eligible=[]
            for upper in range(1,3):
                suffix_holds=states[upper+1:]==['strong_lead']*(2-upper)
                for lower in range(upper):
                    passes=states[lower]=='loss' and states[upper]=='strong_lead' and suffix_holds
                    brackets.append({'family':family,'density':32,'competitor':competitor,
                        'lower_n':SIZES[lower],'upper_n':SIZES[upper],'lower_state':states[lower],
                        'upper_state':states[upper],'all_larger_measured_points_strong':suffix_holds,'strong_crossover':passes})
                    if passes:eligible.append((upper,lower))
            first=min((upper for upper,lower in eligible),default=None)
            last_loss=max((lower for upper,lower in eligible if upper==first),default=None)
            summaries.append({'family':family,'density':32,'competitor':competitor,
                'strong_crossover':bool(eligible),'qualifying_brackets':len(eligible),
                'primary_lower_n':None if last_loss is None else SIZES[last_loss],
                'primary_upper_n':None if first is None else SIZES[first],
                'smallest_state':states[0],'largest_state':states[-1],
                'strong_lead_at_every_measured_size':states==['strong_lead']*3,
                'loss_at_every_measured_size':states==['loss']*3})
    require((len(points),len(brackets),len(summaries))==(30,30,10), 'wrong crossover cardinalities')
    return {'crossover_points':points,'crossover_brackets':brackets,'crossover_summary':summaries}


def table_keys(name):
    if name.startswith('crossover_'):
        return ('family','density','competitor') + (('n',) if name=='crossover_points' else
                ('lower_n','upper_n') if name=='crossover_brackets' else ())
    keys=('case_id','algorithm' if name.endswith('summary') else 'competitor','metric')
    if name=='paired_ratios':return (*keys,'graph_seed','kkt_seed','repetition')
    if name.startswith('graph_'):return (*keys,'graph_seed')
    return keys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',type=Path,default=ROOT/'larger.json')
    parser.add_argument('--analysis-dir',type=Path,default=ROOT/'analysis')
    parser.add_argument('--output-dir',type=Path,default=ROOT/'validation/independent-numerical-audit')
    args=parser.parse_args();require(not args.output_dir.exists(),'refusing to overwrite independent audit')
    INPUTS.clear();checked(__file__)
    info,specs,rows,certificates,twins=raw_capture(args.capture)
    tables=numerical_tables(rows,specs)
    for name,values in tables.items():verify_table(args.analysis_dir/(name+'.csv'),values,table_keys(name))
    validated=read_csv(checked(args.analysis_dir/'validated_calls.csv'),FIELDS)
    require(validated==[{name:str(row[name]) for name in FIELDS} for row in rows], 'analyzer native-call table differs')
    provenance=read_json(args.analysis_dir/'provenance.json')
    require(provenance['schema']=='larger_hierarchy_analysis_v1' and provenance['validation']=='pass' and
            provenance['checked_rows']==504 and provenance['capture']==info and
            provenance['rows_removed']==provenance['rows_adjusted']==0, 'strict analysis provenance mismatch')
    for path,value in provenance['input_sha256'].items():checked(path,value)
    for path,value in INPUTS.items():require(digest(path)==value,'input changed during independent audit')
    args.output_dir.mkdir(parents=True)
    for name,values in {**tables,'certificates':certificates,'matched_topology_twins':twins}.items():
        write_csv(args.output_dir,name,rational_export(values))
    wins=[{'competitor':competitor,'metric':metric,'individual_pairs':72,
           'individual_wins':sum(row['individual_wins'] for row in tables['comparisons']
                                 if (row['competitor'],row['metric'])==(competitor,metric))}
          for competitor in ALGORITHMS[1:] for metric in METRICS]
    report={'schema':'independent_larger_hierarchy_numerical_audit_v1','validation':'pass','collector_imported':False,
            'raw_native_children':12,'checked_outputs':504,'timed_outputs':432,'warmup_outputs':72,
            'table_counts':{name:len(values) for name,values in tables.items()},'matched_topology_twins':len(twins),
            'certificates':len(certificates),'owned_groups_verified_empty':12,'clock_flagged_calls':info['flagged_calls'],
            'capture_clock_flags':info['capture_clock_flags'],'strict_analyzer_pairs_medians_ranges_counts_agree':True,
            'arithmetic':'Exact Fraction pairs, medians, ranges and all measured crossover predicates; decimal exports are convenience conversions.',
            'scope':'Independent raw numeric, schedule, certificate, fingerprint, clock, resource, concatenation and complete frozen ancestor artifact-hash audit. Supplements the frozen collector source/build recipe proof. No power or sleep-inhibition claim.',
            'within_variant_wins':wins,'crossover_summary':tables['crossover_summary'],'input_sha256':dict(INPUTS)}
    with (args.output_dir/'audit.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    lines=['# Independent larger-hierarchy numerical audit','','PASS: 12 children and 504 outputs, including 432 timed calls and 72 checked warmups. '
           'All 720 paired clock ratios and all 396 comparison/absolute medians, ranges and counts match the strict analyzer. '
           'All 30 point states, 30 endpoint pairs and 10 sustained-crossover summaries were independently recomputed with exact Fraction arithmetic. '
           'All 12 certificates, six topology twins, raw/combined concatenation and known-empty process-group evidence were rechecked; '
           'the complete frozen parent artifact chain was reread. No collector code was imported.','',
           '| Family | Comparator | Strong measured bracket | Smallest state | Largest state |',
           '|---|---|---|---|---|']
    for row in tables['crossover_summary']:
        interval=f"({row['primary_lower_n']:,}, {row['primary_upper_n']:,}]" if row['strong_crossover'] else 'none'
        lines.append(f"| {row['family']} | {row['competitor']} | {interval} | {row['smallest_state']} | {row['largest_state']} |")
    lines+=['',f"Retained flags: {info['flagged_calls']} calls and {len(info['capture_clock_flags'])} capture/child UTC flags.",'',
            'A bracket requires loss on both graphs/clocks at the lower endpoint, at least a 10% lead at the upper endpoint, '
            'and the same lead at every larger measured point. All endpoints and earlier reversals remain in the tables. '
            'These are measured brackets, not interpolated crossings or proof of asymptotic dominance. Six repetitions reuse '
            'each graph realization and one fixed scalar sampling seed; they are not independent forest samples. '
            'No historical timing or control-based normalization is used, and a win against one comparator is not an all-solver win.','']
    with (args.output_dir/'README.md').open('x') as stream:stream.write('\n'.join(lines))
    print(json.dumps({'validation':'pass','checked_outputs':504,'table_counts':report['table_counts'],
                      'within_variant_wins':wins,'crossover_summary':tables['crossover_summary']},indent=2))


if __name__=='__main__':main()


