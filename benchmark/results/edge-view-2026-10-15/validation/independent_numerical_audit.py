#!/usr/bin/env python3
"""Independent exact-rational paired-six audit; imports no collector code.

Run only after capture and the collector's strict analysis finish. Raw native
children are the numerical source. This supplements the collector's full owned
process-group/resource reanalysis rather than replacing it.
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
VARIANTS = ('tuple', 'edge')
SEEDS = (4000037, 4000063)
SAMPLING_SEED = 1013
PARENT_SHA256 = '57459498d3a87d6b128ec7ca9cb89a5cda809350865b1c83208ad39f50b92359'
TEXT = {'case_id', 'family', 'phase', 'algorithm', 'validation'}
FIELDS = ('case_id', 'family', 'n', 'm', 'density', 'intrusion_per_mille', 'graph_seed', 'kkt_seed',
          'input_fingerprint', 'topology_fingerprint', 'phase', 'repetition', 'order', 'warmups', 'algorithm',
          'elapsed_ns', 'utc_start_ns', 'utc_end_ns', 'process_cpu_start_ns', 'process_cpu_end_ns',
          'process_cpu_elapsed_ns', 'validation')
CERTIFICATE = ('case_id', 'graph_seed', 'kkt_seed', 'n', 'm', 'input_fingerprint', 'topology_fingerprint', 'validation')
IDENTITY = ('case_id', 'family', 'n', 'm', 'density', 'intrusion_per_mille')
METRICS = {'wall': 'elapsed_ns', 'cpu': 'process_cpu_elapsed_ns'}
EXPECTED_CASES = {(family, n, 16, 0) for family in ('leaf_hierarchy4', 'leaf_distance4')
                  for n in (65536, 262144, 2097152)} \
    | {('gnm_random', n, 16, 0) for n in (4096, 1048576)} \
    | {('gnm_random', n, 128, 0) for n in (4096, 262144)}
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


def read_csv(path, fields=None):
    with Path(path).open(newline='') as stream:
        reader = csv.DictReader(stream)
        require(fields is None or tuple(reader.fieldnames) == fields, 'CSV header mismatch: ' + str(path))
        rows = list(reader)
    require(all(None not in row and None not in row.values() for row in rows), 'malformed CSV')
    return rows


def write_csv(directory, name, rows):
    require(bool(rows), 'empty output table: ' + name)
    with (directory / (name + '.csv')).open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def rational_fields(value, name='ratio'):
    value = Fraction(value)
    return {name: float(value), name + '_numerator': value.numerator, name + '_denominator': value.denominator}


def utc_flags(info):
    start = datetime.datetime.fromisoformat(info['started_utc'])
    finish = datetime.datetime.fromisoformat(info['finished_utc'])
    result = []
    if finish < start: result.append({'scope': 'capture', 'flag': 'utc_reversed_interval'})
    previous = start
    for index, child in enumerate(info['captures'], 1):
        a = datetime.datetime.fromisoformat(child['started_utc']); b = datetime.datetime.fromisoformat(child['finished_utc'])
        scope = 'child ' + str(index)
        if b < a: result.append({'scope': scope, 'flag': 'utc_reversed_interval'})
        if a < previous: result.append({'scope': scope, 'flag': 'utc_reversed_between_children'})
        if a < start or b > finish: result.append({'scope': scope, 'flag': 'utc_interval_outside_capture'})
        previous = b
    return result


def raw_capture(path):
    info = json.loads(checked(path).read_text())
    require(info['schema'] == 'edge_view_experiment_capture_v1' and info['validation'] == 'pass', 'wrong/incomplete capture')
    require(info['rows_removed'] == info['rows_adjusted'] == 0 and info['cleanup'] == [] and
            info['native_process_may_still_be_running'] is False and 'error' not in info, 'altered/uncertain capture')
    freeze = json.loads(checked(info['freeze'], info['freeze_sha256']).read_text())
    require(freeze == info['frozen_protocol'] and freeze['schema'] == 'edge_view_experiment_freeze_v1', 'frozen protocol mismatch')
    require(freeze['parent_freeze_sha256'] == PARENT_SHA256, 'wrong parent control freeze')
    checked(freeze['parent_freeze'], PARENT_SHA256)
    checked(freeze['protocol'], freeze['protocol_sha256'])
    source_root = Path(freeze['working_directory'])
    for field in ('source_sha256', 'build_recipe_sha256'):
        for name, value in freeze[field].items(): checked(source_root / name, value)
    for name, value in freeze['python_source_sha256'].items(): checked(name, value)
    require(set(freeze['variants']) == set(VARIANTS), 'wrong variant inventory')
    for item in freeze['variants'].values():
        checked(item['binary'], item['binary_sha256'])
        build = json.loads(checked(item['build']['path'], item['build']['sha256']).read_text())
        require(build == item['build']['record'], 'build record differs')
        for name, value in build['object_sha256'].items(): checked(build['object_paths'][name], value)
        checked(build['main_object'], build['main_object_sha256'])
    manifest = read_csv(checked(freeze['manifest'], freeze['manifest_sha256']),
                        ('family', 'n', 'density', 'intrusion_per_mille'))
    specs = {}
    for raw in manifest:
        spec = {name: value if name == 'family' else int(value) for name, value in raw.items()}
        spec['m'] = spec['n'] * spec['density']
        spec['case_id'] = f"{spec['family']}_n{spec['n']}_d{spec['density']}_p{spec['intrusion_per_mille']}"
        require(spec['case_id'] not in specs, 'duplicate manifest case'); specs[spec['case_id']] = spec
    require(len(specs) == 10 and {(s['family'], s['n'], s['density'], s['intrusion_per_mille']) for s in specs.values()} == EXPECTED_CASES,
            'wrong declared case matrix')
    require(freeze['algorithms'] == list(ALGORITHMS) and freeze['graph_seeds'] == list(SEEDS) and
            freeze['sampling_seeds'] == [SAMPLING_SEED] and freeze['repetitions'] == 6 and freeze['warmups'] == 1,
            'wrong declared solver/seed/replication matrix')
    schedule = [{'variant': variant, 'case_id': case, 'graph_seed': seed, 'kkt_seed': SAMPLING_SEED}
                for index, seed in enumerate(SEEDS)
                for case in (list(specs) if index == 0 else list(reversed(specs)))
                for variant in (VARIANTS if index == 0 else tuple(reversed(VARIANTS)))]
    require(freeze['schedule'] == schedule and len(info['captures']) == 40, 'wrong adjacent balanced schedule')
    all_rows = []; all_raw = []; diagnostics = []; certificates = []; fingerprints = {}
    output = checked(info['output'], info['output_sha256'])
    require(output.with_suffix('.json') == Path(path).resolve(), 'sidecar/output mismatch')
    previous_end = info['started_monotonic_ns']; finish = info['finished_monotonic_ns']
    for index, (child, identity) in enumerate(zip(info['captures'], schedule), 1):
        variant, case, seed = identity['variant'], identity['case_id'], identity['graph_seed']
        require(all(child[name] == value for name, value in identity.items()), 'child schedule mismatch')
        require(child['exit_status'] == 0 and child['validation'] == 'pass' and child['interruption'] is None and child['rows'] == 42,
                'unsuccessful/incomplete native child')
        require(previous_end <= child['started_monotonic_ns'] < child['finished_monotonic_ns'] <= finish, 'overlapping child intervals')
        previous_end = child['finished_monotonic_ns']
        raw_path = output.with_name(output.stem + '_cases') / f'{index:04d}_{variant}_{case}_g{seed}_s{SAMPLING_SEED}.csv'
        require(child['csv'] == str(raw_path) and child['log'] == str(raw_path.with_suffix('.log')) and
                child['rss_log'] == str(raw_path.with_suffix('.rss.jsonl')), 'native evidence path mismatch')
        checked(raw_path, child['output_sha256']); log = checked(child['log'], child['log_sha256'])
        checked(child['rss_log'], child['rss_sha256'])
        argv = [freeze['variants'][variant]['binary'], '--family', specs[case]['family'], '--n', str(specs[case]['n']),
                '--density', str(specs[case]['density']), '--graph-seed', str(seed), '--kkt-seed', str(SAMPLING_SEED),
                '--repetitions', '6', '--warmups', '1']
        require(child['command'] == argv and child['launch_command'] == ['/usr/bin/time', '-l', *argv], 'native command mismatch')
        raw = read_csv(raw_path, FIELDS); require(len(raw) == 42, 'wrong native child row count')
        rows = [{name: value if name in TEXT else int(value) for name, value in row.items()} for row in raw]
        positions = Counter(); previous_cpu = previous_utc = None; child_flags = 0
        expected = [(phase, rep, order, ALGORITHMS[(order + rep) % 6])
                    for phase, reps in (('warmup', 1), ('timed', 6)) for rep in range(reps) for order in range(6)]
        for row, call in zip(rows, expected):
            require(all(row[name] == value for name, value in specs[case].items()), 'native graph differs from manifest')
            require((row['phase'], row['repetition'], row['order'], row['algorithm']) == call, 'native solver position mismatch')
            require((row['graph_seed'], row['kkt_seed'], row['warmups'], row['validation']) == (seed, SAMPLING_SEED, 1, 'pass'),
                    'native seed/result mismatch')
            cpu, wall = row['process_cpu_elapsed_ns'], row['elapsed_ns']; utc = row['utc_end_ns'] - row['utc_start_ns']
            require(cpu > 0 and wall > 0 and row['utc_start_ns'] > 0 and row['utc_end_ns'] > 0 and
                    row['process_cpu_end_ns'] - row['process_cpu_start_ns'] == cpu, 'invalid clock endpoints/duration')
            require(previous_cpu is None or row['process_cpu_start_ns'] >= previous_cpu, 'CPU intervals overlap')
            threshold = max(2_000_000_000, cpu); flags = []
            if utc < 0: flags.append('realtime_reversed_within_call')
            if previous_utc is not None and row['utc_start_ns'] < previous_utc: flags.append('realtime_reversed_between_calls')
            if 4 * (wall - cpu) > threshold: flags.append('steady_exceeds_process_cpu')
            if 4 * (cpu - wall) > threshold: flags.append('process_cpu_exceeds_steady')
            if 4 * abs(utc - wall) > threshold: flags.append('utc_steady_duration_disagreement')
            child_flags += bool(flags); previous_cpu, previous_utc = row['process_cpu_end_ns'], row['utc_end_ns']
            diagnostics.append({'variant': variant, 'case_id': case, 'graph_seed': seed, 'kkt_seed': SAMPLING_SEED,
                                **dict(zip(('phase', 'repetition', 'order', 'algorithm'), call)),
                                'elapsed_ns': wall, 'process_cpu_elapsed_ns': cpu, 'utc_elapsed_ns': utc,
                                'steady_minus_cpu_ns': wall-cpu, 'utc_minus_steady_ns': utc-wall,
                                'diagnostic_flags': flags, 'excluded': False})
            fingerprint = row['input_fingerprint'], row['topology_fingerprint']
            require((case, seed) not in fingerprints or fingerprints[(case, seed)] == fingerprint, 'cross-variant input fingerprint changed')
            fingerprints[(case, seed)] = fingerprint
            if row['phase'] == 'timed': positions[(row['algorithm'], row['order'])] += 1
        require(child_flags == child['flagged_calls'], 'child clock-flag count mismatch')
        require(positions == Counter({(algorithm, order): 1 for algorithm in ALGORITHMS for order in range(6)}), 'six-position imbalance')
        markers = []
        for line in log.read_text().splitlines():
            if line.startswith('reference_certificate'):
                require(line.startswith('reference_certificate_v1 '), 'invalid certificate version')
                markers.append(json.loads(line[len('reference_certificate_v1 '):]))
        expected_certificate = {name: rows[0][name] for name in CERTIFICATE}
        require(len(markers) == 1 and markers[0] == child['certificate'] == expected_certificate, 'certificate/input mismatch')
        require(all(type(markers[0][name]) is type(value) for name, value in expected_certificate.items()), 'certificate type mismatch')
        certificates.append({'variant': variant, **markers[0]})
        all_rows.extend({'variant': variant, **row} for row in rows)
        all_raw.extend({'variant': variant, **row} for row in raw)
    counts = (len(all_rows), sum(row['phase'] == 'timed' for row in all_rows), sum(row['phase'] == 'warmup' for row in all_rows))
    require(counts == (1680, 1440, 240) and counts == (info['checked_rows'], info['checked_timed_rows'], info['checked_warmup_rows']), 'wrong output counts')
    require(diagnostics == info['call_diagnostics'], 'independent call diagnostics mismatch')
    require(sum(bool(row['diagnostic_flags']) for row in diagnostics) == info['flagged_calls'], 'clock flag total mismatch')
    require(utc_flags(info) == info['capture_clock_flags'], 'capture/child UTC flags mismatch')
    require(read_csv(output, ('variant', *FIELDS)) == all_raw, 'combined file not exact ordered child concatenation')
    return info, specs, all_rows, certificates


def summarize(values, dimensions, specs, value_name='ratio'):
    """Exact graph medians and pooled twelve-trial case medians."""
    graph_rows = []; case_rows = []; graph_medians = {}; case_medians = {}; pools = defaultdict(list)
    for key, sample in values.items():
        require(len(sample) == 6, 'wrong per-graph replication')
        median = statistics.median(sample); graph_medians[key] = median; pools[key[:-1]].extend(sample)
        identity = dict(zip((*dimensions, 'graph_seed'), key))
        graph_rows.append({**specs[identity['case_id']], **identity, **rational_fields(median, value_name),
                           'trial_min': float(min(sample)), 'trial_max': float(max(sample)), 'trials': 6,
                           **({'individual_wins': sum(value < 1 for value in sample)} if value_name == 'ratio' else {})})
    for key, sample in pools.items():
        require(len(sample) == 12 and all((*key, seed) in graph_medians for seed in SEEDS), 'wrong pooled replication')
        median = statistics.median(sample); case_medians[key] = median
        identity = dict(zip(dimensions, key)); graph_values = [graph_medians[(*key, seed)] for seed in SEEDS]
        case_rows.append({**specs[identity['case_id']], **identity, **rational_fields(median, value_name),
                          'graph_min': float(min(graph_values)), 'graph_max': float(max(graph_values)),
                          'trial_min': float(min(sample)), 'trial_max': float(max(sample)), 'trials': 12,
                          **({'individual_wins': sum(value < 1 for value in sample)} if value_name == 'ratio' else {})})
    return graph_medians, case_medians, graph_rows, case_rows


def comparisons(rows, specs):
    blocks = {}; variants = {}; runtimes = defaultdict(list)
    for row in rows:
        if row['phase'] != 'timed': continue
        block_key = row['variant'], row['case_id'], row['graph_seed'], row['repetition']
        block = blocks.setdefault(block_key, {}); require(row['algorithm'] not in block, 'duplicate solver'); block[row['algorithm']] = row
        pair_key = row['case_id'], row['graph_seed'], row['repetition'], row['algorithm']
        pair = variants.setdefault(pair_key, {}); require(row['variant'] not in pair, 'duplicate variant'); pair[row['variant']] = row
        for metric, field in METRICS.items():
            runtimes[(row['variant'], row['case_id'], row['algorithm'], metric, row['graph_seed'])].append(Fraction(row[field]))
    within = []; across = []; wvalues = defaultdict(list); avalues = defaultdict(list)
    for (variant, case, graph, rep), block in blocks.items():
        require(set(block) == set(ALGORITHMS), 'incomplete six-solver block')
        for competitor in ALGORITHMS[1:]:
            for metric, field in METRICS.items():
                ratio = Fraction(block['kkt'][field], block[competitor][field])
                wvalues[(variant, case, competitor, metric, graph)].append(ratio)
                within.append({'variant': variant, 'case_id': case, 'graph_seed': graph, 'kkt_seed': SAMPLING_SEED,
                               'repetition': rep, 'competitor': competitor, 'metric': metric, 'kkt_ns': block['kkt'][field],
                               'competitor_ns': block[competitor][field], **rational_fields(ratio)})
    for (case, graph, rep, algorithm), block in variants.items():
        require(set(block) == set(VARIANTS), 'incomplete paired variant block')
        for metric, field in METRICS.items():
            ratio = Fraction(block['edge'][field], block['tuple'][field])
            avalues[(case, algorithm, metric, graph)].append(ratio)
            across.append({'case_id': case, 'graph_seed': graph, 'kkt_seed': SAMPLING_SEED, 'repetition': rep,
                           'algorithm': algorithm, 'metric': metric, 'tuple_ns': block['tuple'][field],
                           'edge_ns': block['edge'][field], **rational_fields(ratio)})
    require(len(within) == 2400 and len(across) == 1440, 'wrong paired ratio cardinality')
    return within, across, summarize(wvalues, ('variant', 'case_id', 'competitor', 'metric'), specs), \
        summarize(avalues, ('case_id', 'algorithm', 'metric'), specs), \
        summarize(runtimes, ('variant', 'case_id', 'algorithm', 'metric'), specs, 'median_ns')


def verify_table(path, expected_rows, key_fields, float_fields, exact_fields=()):
    actual = read_csv(checked(path)); expected = {tuple(str(row[field]) for field in key_fields): row for row in expected_rows}
    require(len(expected) == len(expected_rows) == len(actual), 'summary cardinality mismatch: ' + path.name)
    seen = set()
    for row in actual:
        key = tuple(row[field] for field in key_fields)
        require(key in expected and key not in seen, 'summary duplicate/foreign identity: ' + path.name); seen.add(key)
        target = expected[key]
        for actual_name, expected_name in float_fields.items():
            require(math.isclose(float(row[actual_name]), float(target[expected_name]), rel_tol=1e-15, abs_tol=0),
                    'independent numerical mismatch: ' + path.name + '/' + actual_name)
        for field in exact_fields: require(row[field] == str(target[field]), 'independent exact field mismatch: ' + field)
    require(seen == set(expected), 'missing summary identities')


def crossovers(specs, graph_medians):
    groups = defaultdict(list)
    for case, spec in specs.items(): groups[(spec['family'], spec['density'])].append((spec['n'], case))
    points = []; brackets = []
    for variant in VARIANTS:
        for (family, density), cases in sorted(groups.items()):
            cases.sort()
            for competitor in ALGORITHMS[1:]:
                states = []
                for n, case in cases:
                    medians = [graph_medians[(variant, case, competitor, metric, seed)] for metric in METRICS for seed in SEEDS]
                    state = 'loss' if all(value > 1 for value in medians) else 'strong_win' if all(value <= Fraction(9,10) for value in medians) else 'mixed_or_narrow'
                    states.append(state)
                    points.append({'variant': variant, 'family': family, 'density': density, 'competitor': competitor, 'n': n, 'state': state,
                                   **{f'{metric}_g{seed}': float(graph_medians[(variant, case, competitor, metric, seed)]) for metric in METRICS for seed in SEEDS}})
                candidates = [(cases[max(i for i in range(j) if states[i] == 'loss')][0], cases[j][0])
                              for j in range(1,len(cases)) if all(value == 'strong_win' for value in states[j:]) and 'loss' in states[:j]]
                bracket = candidates[0] if candidates else None
                classification = 'strong_observed_crossover' if bracket else 'strong_lead_entire_measured_range' if all(value == 'strong_win' for value in states) else 'loss_entire_measured_range' if all(value == 'loss' for value in states) else 'no_strong_observed_crossover'
                brackets.append({'variant': variant, 'family': family, 'density': density, 'competitor': competitor,
                                 'classification': classification, 'lower_measured_n': bracket[0] if bracket else None,
                                 'upper_measured_n': bracket[1] if bracket else None,
                                 'point_states': ';'.join(f'{n}:{state}' for (n,_),state in zip(cases,states))})
    require(len(points) == 100 and len(brackets) == 40, 'wrong protocol state cardinality')
    return points, brackets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, default=ROOT/'paired.json')
    parser.add_argument('--analysis-dir', type=Path, default=ROOT/'analysis')
    parser.add_argument('--output-dir', type=Path, default=ROOT/'validation/independent-numerical-audit')
    args = parser.parse_args(); require(not args.output_dir.exists(), 'refusing to overwrite independent audit')
    info, specs, rows, certificates = raw_capture(args.capture)
    within, across, wsummary, asummary, runtime_summary = comparisons(rows, specs)
    wg, wc, wgrows, wcrows = wsummary; ag, ac, agrows, acrows = asummary; rg, rc, rgrows, rcrows = runtime_summary
    require((len(wcrows),len(wgrows),len(acrows),len(agrows),len(rcrows),len(rgrows)) == (200,400,120,240,240,480), 'wrong summary counts')
    wdims = ('variant','case_id','competitor','metric'); adims = ('case_id','algorithm','metric'); rdims = ('variant','case_id','algorithm','metric')
    ranges = {'trial_min':'trial_min','trial_max':'trial_max'}; pooled_ranges = {**ranges,'graph_min':'graph_min','graph_max':'graph_max'}
    verify_table(args.analysis_dir/'paired_ratios.csv', within, (*wdims,'graph_seed','kkt_seed','repetition'), {'kkt_over_competitor':'ratio'}, ('kkt_ns','competitor_ns'))
    verify_table(args.analysis_dir/'variant_pairs.csv', across, (*adims,'graph_seed','kkt_seed','repetition'), {'edge_over_tuple':'ratio'}, ('tuple_ns','edge_ns'))
    for name, expected, dimensions, numerical, exact in (
        ('comparisons',wcrows,wdims,{'median_paired_ratio':'ratio',**pooled_ranges},('trials','individual_wins')),
        ('graph_comparisons',wgrows,(*wdims,'graph_seed'),{'median_paired_ratio':'ratio',**ranges},('trials','individual_wins')),
        ('variant_comparisons',acrows,adims,{'median_paired_ratio':'ratio',**pooled_ranges},('trials','individual_wins')),
        ('graph_variant_comparisons',agrows,(*adims,'graph_seed'),{'median_paired_ratio':'ratio',**ranges},('trials','individual_wins')),
        ('summary',rcrows,rdims,{'median_ns':'median_ns',**pooled_ranges},('trials',)),
        ('graph_summary',rgrows,(*rdims,'graph_seed'),{'median_ns':'median_ns',**ranges},('trials',))):
        verify_table(args.analysis_dir/(name+'.csv'), expected, dimensions, numerical, exact)
    provenance = json.loads(checked(args.analysis_dir/'provenance.json').read_text())
    require(provenance['schema'] == 'edge_view_experiment_analysis_v1' and provenance['validation'] == 'pass' and
            provenance['capture'] == info and provenance['checked_rows'] == 1680, 'strict analysis provenance mismatch')
    points, brackets = crossovers(specs, wg)
    wins = [{'variant': variant, 'competitor': solver, 'metric': metric,
             'individual_wins':sum(row['individual_wins'] for row in wcrows if (row['variant'],row['competitor'],row['metric']) == (variant,solver,metric)),
             'individual_pairs':120} for variant in VARIANTS for solver in ALGORITHMS[1:] for metric in METRICS]
    drift = [{'algorithm': solver, 'metric': metric,
              'edge_faster_pairs':sum(row['individual_wins'] for row in acrows if (row['algorithm'],row['metric']) == (solver,metric)),
              'individual_pairs':120,'pooled_case_ratio_min':float(min(value for key,value in ac.items() if key[1:] == (solver,metric))),
              'pooled_case_ratio_max':float(max(value for key,value in ac.items() if key[1:] == (solver,metric)))}
             for solver in ALGORITHMS for metric in METRICS]
    checked(__file__)
    for name,value in INPUTS.items(): require(digest(name) == value, 'input changed during independent audit')
    args.output_dir.mkdir(parents=True)
    for name, values in (('within_variant_pairs',within),('cross_variant_pairs',across),('within_variant_case_medians',wcrows),
                         ('within_variant_graph_medians',wgrows),('cross_variant_case_medians',acrows),('cross_variant_graph_medians',agrows),
                         ('absolute_case_medians',rcrows),('absolute_graph_medians',rgrows),('protocol_point_states',points),
                         ('strong_crossover_brackets',brackets)):
        write_csv(args.output_dir,name,values)
    report = {'schema':'independent_edge_view_numerical_audit_v1','validation':'pass','collector_imported':False,
              'raw_native_children':40,'certificates':len(certificates),'checked_outputs':1680,'timed_outputs':1440,'warmup_outputs':240,
              'within_variant_clock_pairs':len(within),'cross_variant_clock_pairs':len(across),
              'within_variant_case_medians':len(wcrows),'within_variant_graph_medians':len(wgrows),
              'cross_variant_case_medians':len(acrows),'cross_variant_graph_medians':len(agrows),
              'absolute_case_medians':len(rcrows),'absolute_graph_medians':len(rgrows),
              'clock_flagged_calls':info['flagged_calls'],'capture_clock_flags':info['capture_clock_flags'],
              'strict_analyzer_pairs_medians_ranges_counts_agree':True,
              'arithmetic':'Exact Fraction ratios, medians and crossover predicates. Decimal CSV columns are convenience conversions.',
              'scope':'Independent raw numeric, schedule, certificate, clock and hash audit. Full resource/group validation is the separate strict collector analysis. No power claim is made here.',
              'within_variant_wins':wins,'cross_variant_drift':drift,'crossover_results':brackets,'input_sha256':INPUTS}
    (args.output_dir/'audit.json').open('x').write(json.dumps(report,indent=2)+'\n')
    text = ['# Independent paired-six numerical review','','PASS: read all 40 raw child CSVs, checking 1,680 outputs (1,440 timed, 240 warmup), '
            'six-position balance, adjacent/reversed variant schedule, exact input certificates, clock diagnostics and source/artifact hashes. '
            'No collector code was imported. All 1,440 Edge/tuple ratios and 2,400 within-variant KKT/comparator ratios, '
            'all 1,680 case/graph medians, ranges, counts and wins agree with strict analysis. Ratios and crossover predicates use exact rational arithmetic.','',
            '| Case | Edge / tuple KKT | Tuple KKT / multigraph B | Edge KKT / multigraph B |','|---|---:|---:|---:|']
    for case in specs:
        text.append(f"| {case} | {float(ac[(case,'kkt','wall')]):.6f} | {float(wc[('tuple',case,'multigraph_boruvka','wall')]):.6f} | {float(wc[('edge',case,'multigraph_boruvka','wall')]):.6f} |")
    text += ['','The table shows pooled twelve-trial wall ratios. Both clocks, every graph median, all six solvers’ cross-variant drift '
             'and both variants’ five direct KKT comparisons remain in the CSVs. Controls are never used to normalize KKT.','',
             f"Clock flags retained: {info['flagged_calls']} call flags and {len(info['capture_clock_flags'])} capture/child UTC flags.",'',
             'Strong crossover brackets:','']
    selected = [row for row in brackets if row['classification'] == 'strong_observed_crossover']
    for row in selected:
        text.append(f"- {row['variant']}: {row['family']}, d={row['density']} versus {row['competitor']}: ({row['lower_measured_n']:,}, {row['upper_measured_n']:,}] vertices.")
    if not selected: text.append('No declared strong crossover bracket was observed.')
    text += ['','Each bracket requires both graph medians above one at its lower measured size, at most 0.90 at its upper size '
             'on both clocks, and the same strong win at every still-larger tested size. Brackets are measured endpoints, '
             'not interpolated thresholds. All forty classifications, losses and inconclusive results remain available.','']
    (args.output_dir/'README.md').open('x').write('\n'.join(text))
    print(json.dumps({'validation':'pass','checked_outputs':1680,'within_variant_pairs':len(within),'cross_variant_pairs':len(across),
                      'strong_crossovers':selected,'within_variant_wins':wins,'cross_variant_drift':drift},indent=2))


if __name__ == '__main__': main()
