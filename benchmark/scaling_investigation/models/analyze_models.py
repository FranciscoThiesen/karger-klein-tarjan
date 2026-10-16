#!/usr/bin/env python3
"""Exploratory fits from untouched archived integer calls; never launches solvers."""
import argparse
import csv
from fractions import Fraction
import hashlib
import io
import json
import math
from pathlib import Path
import re
import statistics
import sys
from collections import defaultdict

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'benchmark/results/current-complexity-2026-10-15'
OLD_ROOT = Path('/Users/random_person/Desktop/kkt-eighth-sampling')
FAMILIES = ('leaf_hierarchy4', 'leaf_shuffled4', 'gnm_random')
ALGORITHMS = ('kkt', 'multigraph_boruvka')
GRAPHS = (19000013, 19000043)
SAMPLERS = (3001, 3011)
SIZES = tuple(2**p for p in range(10, 21))
CLOCKS = ('native_steady', 'native_process_cpu', 'library_manual', 'library_process_cpu')
SPEC = ('family', 'algorithm', 'graph_seed', 'sampling_seed', 'size_order')
FIELDS = tuple('family,algorithm,n,m,N,graph_seed,sampling_seed,input_fingerprint,topology_fingerprint,size_order,invocation,phase,iteration,elapsed_ns,utc_start_ns,utc_end_ns,process_cpu_start_ns,process_cpu_end_ns,process_cpu_elapsed_ns,validation'.split(','))
TEXT = {'family', 'algorithm', 'size_order', 'phase', 'validation'}
GOOGLE = ('(1)', 'lgN', 'N', 'NlgN', 'N^2', 'N^3')
MODELS = ('N', 'NlgN', 'affine_N', 'affine_NlgN', 'hinge_16384', 'hinge_65536', 'hinge_262144')
WINDOWS = {'full11': SIZES, 'upper6': SIZES[5:]}
FOLDS = {'first5_next2': (SIZES[:5], SIZES[5:7]),
         'first7_next2': (SIZES[:7], SIZES[7:9]),
         'first8_last3': (SIZES[:8], SIZES[8:]),
         'first9_last2': (SIZES[:9], SIZES[9:])}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parse_json(text):
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, 'duplicate JSON key')
            out[key] = value
        return out
    return json.loads(text, object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def schedule():
    return [dict(family=f, algorithm=a, graph_seed=g, sampling_seed=s,
                 size_order='descending' if gi else 'ascending')
            for f in FAMILIES for gi, g in enumerate(GRAPHS)
            for si, s in enumerate(SAMPLERS)
            for a in (ALGORITHMS if (gi + si) % 2 == 0 else ALGORITHMS[::-1])]


def relocated(path):
    path = Path(path)
    if path.is_relative_to(OLD_ROOT):
        return ROOT / path.relative_to(OLD_ROOT)
    return path


def read_bound(path, bound, expected=None):
    path = Path(path).resolve(strict=True)
    before = sha(path)
    require(expected is None or before == expected, 'hash mismatch: ' + str(path))
    require(str(path) not in bound or bound[str(path)] == before, 'input drift')
    data = path.read_text()
    require(sha(path) == before, 'input changed during read')
    bound[str(path)] = before
    return data


def native(text, log, spec):
    reader = csv.DictReader(io.StringIO(text))
    require(tuple(reader.fieldnames or ()) == FIELDS, 'native schema')
    raw = list(reader)
    sizes = SIZES if spec['size_order'] == 'ascending' else SIZES[::-1]
    identities = [(n, j, phase, i) for n in sizes for j in range(3)
                  for phase, i in (('warmup', 0), ('timed', 0), ('timed', 1))]
    require(len(raw) == len(identities) == 99, 'native count')
    out = []
    for source, identity in zip(raw, identities):
        require(set(source) == set(FIELDS) and None not in source.values(), 'malformed CSV')
        row = {}
        for key, value in source.items():
            if key in TEXT:
                row[key] = value
            else:
                require(re.fullmatch(r'0|[1-9][0-9]*', value), 'unsigned integer required')
                row[key] = int(value)
                require(row[key] < 2**(63 if key.endswith('_ns') else 64), 'integer bound')
        require({k: row[k] for k in SPEC} == spec, 'curve mismatch')
        require(tuple(row[k] for k in ('n', 'invocation', 'phase', 'iteration')) == identity, 'call order')
        require(row['m'] == row['n'] * (16 if spec['family'] == 'gnm_random' else 32), 'm mismatch')
        require(row['N'] == row['m'] + row['n'] and row['validation'] == 'pass', 'input/validation')
        require(row['elapsed_ns'] > 0 and row['process_cpu_elapsed_ns'] > 0, 'nonpositive clock')
        require(row['process_cpu_end_ns'] - row['process_cpu_start_ns'] == row['process_cpu_elapsed_ns'], 'CPU endpoints')
        require(not out or row['process_cpu_start_ns'] >= out[-1]['process_cpu_end_ns'], 'CPU order')
        out.append(row)
    markers = [line for line in log.splitlines() if 'complexity_certificate' in line]
    require(len(markers) == 33, 'certificate count')
    for line, row in zip(markers, out[::3]):
        require(line.startswith('complexity_certificate_v1 '), 'unsupported certificate')
        cert = parse_json(line.split(' ', 1)[1])
        expected = {k: row[k] for k in ('family', 'algorithm', 'n', 'm', 'graph_seed', 'sampling_seed',
                    'invocation', 'input_fingerprint', 'topology_fingerprint', 'validation')}
        require(set(cert) == set(expected), 'certificate schema')
        require(all(type(cert[k]) is type(v) and cert[k] == v for k, v in expected.items()), 'certificate identity')
    return out


def load(bound):
    audit = parse_json(read_bound(STUDY / 'arithmetic-audit-attempt01/audit.json', bound))
    require(audit['validation'] == 'pass', 'prior independent audit not passing')
    original = OLD_ROOT / STUDY.relative_to(ROOT)
    capture_path = STUDY / 'capture-attempt01/capture.json'
    capture = parse_json(read_bound(capture_path, bound, audit['input_sha256'][str(original / 'capture-attempt01/capture.json')]))
    require(capture['validation'] == 'pass' and capture['checked_raw_rows'] == 2376 and
            capture['checked_timed_rows'] == 1584 and capture['checked_warmup_rows'] == 792 and
            capture['rows_removed'] == capture['rows_adjusted'] == 0 and
            capture['native_process_may_still_be_running'] is False, 'capture status')
    freeze = parse_json(read_bound(STUDY / 'freeze.json', bound, capture['freeze_sha256']))
    # Pin the exact model and harness source whose semantics are discussed.
    for path, digest in {**freeze['source_sha256'], **freeze['bound_sha256']}.items():
        if path.endswith(('/current_complexity.cpp', '/src/complexity.cc', '/src/json_reporter.cc')):
            read_bound(relocated(path), bound, digest)
    require([c['spec'] for c in capture['captures']] == schedule(), '24-curve order')
    means, calls, library_choices = [], [], []
    fingerprints = {}
    for child in capture['captures']:
        require(child['exit_status'] == 0 and child['validation'] == 'pass', 'native exit')
        require(child['group_exit_verification']['validation'] == 'pass' and
                child['group_exit_verification']['members'] == [], 'owned group proof')
        spec = child['spec']
        rows = native(read_bound(relocated(child['raw_csv']), bound, child['raw_sha256']),
                      read_bound(relocated(child['log']), bound, child['log_sha256']), spec)
        calls.extend(rows)
        for row in rows:
            key = (row['family'], row['n'], row['graph_seed'])
            fp = (row['input_fingerprint'], row['topology_fingerprint'])
            require(key not in fingerprints or fingerprints[key] == fp, 'graph changed')
            fingerprints[key] = fp
        document = parse_json(read_bound(relocated(child['benchmark_json']), bound, child['benchmark_sha256']))
        reports = document['benchmarks']
        require(len(reports) == 68, 'Google report count')
        iterations = [r for r in reports if r['run_type'] == 'iteration']
        require(len(iterations) == 33, 'Google iteration count')
        sizes = SIZES if spec['size_order'] == 'ascending' else SIZES[::-1]
        for report, (n, j) in zip(iterations, [(n, j) for n in sizes for j in range(3)]):
            expected_name = f"{spec['algorithm']}/{spec['family']}/graph_{spec['graph_seed']}/sampler_{spec['sampling_seed']}/{n}/iterations:2/repeats:3/process_time/manual_time"
            require(report['name'] == expected_name and report['repetition_index'] == j and
                    report['iterations'] == 2 and report['time_unit'] == 'ms', 'Google iteration identity')
            pair = [r for r in rows if r['phase'] == 'timed' and r['n'] == n and r['invocation'] == j]
            require(len(pair) == 2, 'two-call mean')
            for clock, field in (('native_steady', 'elapsed_ns'), ('native_process_cpu', 'process_cpu_elapsed_ns')):
                exact = Fraction(sum(r[field] for r in pair), 2)
                means.append(dict(spec, clock=clock, n=n, N=pair[0]['N'], invocation=j,
                                  mean_ns=float(exact), exact_numerator=exact.numerator, exact_denominator=exact.denominator))
            for clock, field in (('library_manual', 'real_time'), ('library_process_cpu', 'cpu_time')):
                value = report[field] * 1_000_000
                require(math.isfinite(value) and value > 0, 'Google duration')
                if clock == 'library_manual':
                    require(math.isclose(value, (pair[0]['elapsed_ns'] + pair[1]['elapsed_ns']) / 2,
                                        rel_tol=5e-12, abs_tol=1), 'manual/native join')
                means.append(dict(spec, clock=clock, n=n, N=pair[0]['N'], invocation=j,
                                  mean_ns=value, exact_numerator='', exact_denominator=''))
        big = [r for r in reports if r.get('aggregate_name') == 'BigO']
        rms = [r for r in reports if r.get('aggregate_name') == 'RMS']
        require(len(big) == len(rms) == 1 and big[0]['time_unit'] == 'ns', 'Google fits')
        library_choices.append(dict(spec, model=big[0]['big_o'], cpu_coefficient=big[0]['cpu_coefficient'],
                                    manual_coefficient=big[0]['real_coefficient'], rms=rms[0]['rms']))
    for n in SIZES:
        for g in GRAPHS:
            a, b = (fingerprints[(f, n, g)] for f in FAMILIES[:2])
            require(a[1] == b[1] and a[0] != b[0], 'topology twins')
    require(len(means) == 3168 and len(calls) == 2376, 'complete raw matrix')
    canonical = list(csv.DictReader(io.StringIO(read_bound(STUDY / 'analysis-attempt01/means.csv', bound,
                  audit['input_sha256'][str(original / 'analysis-attempt01/means.csv')]))))
    key = lambda r: tuple(str(r[k]) for k in (*SPEC, 'clock', 'n', 'invocation'))
    found = {key(r): r for r in canonical}
    require(len(found) == len(means), 'canonical means identities')
    for row in means:
        old = found[key(row)]
        require(float(old['mean_ns']) == row['mean_ns'] and
                old['exact_numerator'] == str(row['exact_numerator']) and
                old['exact_denominator'] == str(row['exact_denominator']), 'canonical mean mismatch')
    return means, calls, library_choices


def feature(model, N):
    if model == '(1)': return np.ones_like(N)
    if model == 'lgN': return np.log2(N)
    if model == 'N': return N
    if model == 'NlgN': return N * np.log2(N)
    if model == 'N^2': return N * N
    if model == 'N^3': return N * N * N
    raise ValueError(model)


def design(model, N, n, scale):
    x = N / scale
    if model in GOOGLE:
        # Column rescaling changes coefficients, not the fitted model/objective.
        return np.column_stack([feature(model, N) / float(feature(model, np.array([scale]))[0])])
    if model == 'affine_N': return np.column_stack([np.ones_like(x), x])
    if model == 'affine_NlgN': return np.column_stack([np.ones_like(x), x * np.log2(N) / math.log2(scale)])
    knot_n = int(model.split('_')[1])
    knot_N = knot_n * (N[0] / n[0])
    return np.column_stack([np.ones_like(x), x, np.maximum(N - knot_N, 0) / scale])


def fit(rows, model, relative=False):
    N = np.array([r['N'] for r in rows], dtype=float)
    n = np.array([r['n'] for r in rows], dtype=float)
    y = np.array([r['mean_ns'] for r in rows], dtype=float)
    scale, yscale = float(max(N)), float(max(y))
    X = design(model, N, n, scale)
    weights = yscale / y if relative else np.ones_like(y)
    coefficients, _, rank, singular = np.linalg.lstsq(X * weights[:, None], (y / yscale) * weights, rcond=None)
    if rank != X.shape[1]:
        return None
    coefficients *= yscale
    return dict(model=model, N_scale=scale, coefficients=coefficients,
                parameters=X.shape[1], design_condition=float(singular[0] / singular[-1]))


def predict(fitted, rows):
    N = np.array([r['N'] for r in rows], dtype=float)
    n = np.array([r['n'] for r in rows], dtype=float)
    return design(fitted['model'], N, n, fitted['N_scale']) @ fitted['coefficients']


def metrics(rows, prediction):
    y = np.array([r['mean_ns'] for r in rows], dtype=float)
    errors = prediction - y
    return dict(normalized_rms=float(np.sqrt(np.mean(errors**2)) / np.mean(y)),
                relative_rms=float(np.sqrt(np.mean((errors / y)**2))),
                median_absolute_relative_error=float(np.median(np.abs(errors / y))),
                max_absolute_relative_error=float(np.max(np.abs(errors / y))),
                signed_relative_bias=float(np.mean(errors / y)),
                nonpositive_predictions=int(np.sum(prediction <= 0)), observations=len(rows))


def residual_components(rows, prediction):
    """Exact ANOVA identity, not a stochastic noise model or confidence interval."""
    by_size=defaultdict(list)
    for row, predicted in zip(rows,prediction): by_size[row['n']].append((row['mean_ns'],float(predicted)))
    within=between=total=0.0
    for values in by_size.values():
        observed=statistics.mean(y for y,_ in values)
        require(all(p==values[0][1] for _,p in values),'prediction differs at one size')
        within+=math.fsum((y-observed)**2 for y,_ in values)
        between+=len(values)*(values[0][1]-observed)**2
        total+=math.fsum((p-y)**2 for y,p in values)
    require(math.isclose(within+between,total,rel_tol=2e-12,abs_tol=1e-5),'residual decomposition')
    scale=statistics.mean(r['mean_ns'] for r in rows)
    return dict(within_size_sse=within, size_mean_shape_sse=between, total_sse=total,
                within_size_share=within/total if total else 0,
                within_size_normalized_rms=math.sqrt(within/len(rows))/scale,
                size_mean_shape_normalized_rms=math.sqrt(between/len(rows))/scale)


def parameters(fitted):
    c = fitted['coefficients']
    scale = fitted['N_scale']
    model = fitted['model']
    return dict(parameters=fitted['parameters'], design_condition=fitted['design_condition'],
                intercept_ns=float(c[0]) if model not in GOOGLE else 0.0,
                linear_slope_ns_per_N=float(c[1] / scale) if model == 'affine_N' or model.startswith('hinge_') else '',
                hinge_delta_ns_per_N=float(c[2] / scale) if model.startswith('hinge_') else '',
                coefficient_scaled_ns=json.dumps(c.tolist()), N_scale=scale)


def analyze(means, choices):
    tables = {name: [] for name in ('google_reproduction', 'fits', 'residuals', 'blocked_predictions',
                'holdouts', 'relative_objective', 'window_slopes', 'adjacent_slopes', 'identifiability', 'clock_differences', 'residual_components')}
    groups = defaultdict(list)
    for row in means: groups[tuple(row[k] for k in (*SPEC, 'clock'))].append(row)
    google_choice = {tuple(r[k] for k in SPEC): r for r in choices}
    for key, rows in groups.items():
        identity = dict(zip((*SPEC, 'clock'), key))
        rows.sort(key=lambda r: (r['n'], r['invocation']))
        for window, sizes in WINDOWS.items():
            sample = [r for r in rows if r['n'] in sizes]
            google_fits = []
            for model in GOOGLE:
                fitted = fit(sample, model)
                metric = metrics(sample, predict(fitted, sample))
                coefficient = fitted['coefficients'][0] / feature(model, np.array([fitted['N_scale']]))[0]
                google_fits.append(dict(identity, window=window, model=model,
                    coefficient_ns=float(coefficient), normalized_rms=metric['normalized_rms']))
            best = min(google_fits, key=lambda r: r['normalized_rms'])['model']
            for r in google_fits: r['selected'] = r['model'] == best
            tables['google_reproduction'].extend(google_fits)
            if window == 'full11' and identity['clock'] in ('library_process_cpu', 'library_manual'):
                old = google_choice[key[:-1]]
                chosen = next(r for r in google_fits if r['model'] == old['model'])
                field = 'cpu_coefficient' if identity['clock'] == 'library_process_cpu' else 'manual_coefficient'
                require(math.isclose(chosen['coefficient_ns'], old[field], rel_tol=2e-10), 'Google coefficient mismatch')
                if identity['clock'] == 'library_process_cpu':
                    require(best == old['model'] and math.isclose(chosen['normalized_rms'], old['rms'], rel_tol=2e-10), 'Google selection/RMS mismatch')
            for model in MODELS:
                fitted = fit(sample, model)
                if fitted is None:
                    tables['fits'].append(dict(identity, window=window, model=model, status='rank_deficient'))
                    continue
                prediction = predict(fitted, sample)
                tables['fits'].append(dict(identity, window=window, model=model, status='identified',
                                           **parameters(fitted), **metrics(sample, prediction)))
                tables['residual_components'].append(dict(identity, window=window, model=model,
                                                          **residual_components(sample,prediction)))
                for row, predicted in zip(sample, prediction):
                    tables['residuals'].append(dict(identity, window=window, model=model, n=row['n'],
                        invocation=row['invocation'], observed_ns=row['mean_ns'], predicted_ns=float(predicted),
                        residual_ns=float(predicted-row['mean_ns']), relative_residual=float(predicted/row['mean_ns']-1)))
            for model in ('N', 'NlgN'):
                fitted = fit(sample, model, relative=True)
                tables['relative_objective'].append(dict(identity, window=window, model=model,
                        objective='pointwise_relative_squared_error', **parameters(fitted), **metrics(sample, predict(fitted, sample))))
            N = np.array([r['N'] for r in sample], dtype=float)
            a, b = N / max(N), N*np.log2(N) / max(N*np.log2(N))
            cosine = float(a @ b / np.linalg.norm(a) / np.linalg.norm(b))
            last = sorted(set(N))[-3:]
            tables['identifiability'].append(dict(identity, window=window, cosine_N_NlogN=cosine,
                origin_unit_shape_nrms=float(np.sqrt(np.mean((a-b)**2))/np.mean(a)),
                largest3_N_leverage=float(np.sum(a[np.isin(N,last)]**2)/np.sum(a**2)),
                largest3_NlogN_leverage=float(np.sum(b[np.isin(N,last)]**2)/np.sum(b**2)),
                NlogN_local_exponent_min=float(1+1/math.log(max(N))),
                NlogN_local_exponent_max=float(1+1/math.log(min(N)))))
        for fold, (train_sizes, test_sizes) in FOLDS.items():
            train = [r for r in rows if r['n'] in train_sizes]
            test = [r for r in rows if r['n'] in test_sizes]
            for model in MODELS:
                fitted = fit(train, model)
                base = dict(identity, fold=fold, model=model, train_min_n=min(train_sizes), train_max_n=max(train_sizes),
                            test_min_n=min(test_sizes), test_max_n=max(test_sizes))
                if fitted is None:
                    tables['holdouts'].append(dict(base, status='rank_deficient')); continue
                predictions = predict(fitted, test)
                tables['holdouts'].append(dict(base, status='identified', **parameters(fitted), **metrics(test, predictions)))
                for row, predicted in zip(test, predictions):
                    tables['blocked_predictions'].append(dict(base, n=row['n'], invocation=row['invocation'],
                        observed_ns=row['mean_ns'], predicted_ns=float(predicted), relative_error=float(predicted/row['mean_ns']-1)))
        for count in range(4, 12):
            sample = [r for r in rows if r['n'] in SIZES[-count:]]
            x = np.log([r['N'] for r in sample]); y = np.log([r['mean_ns'] for r in sample])
            alpha = float(np.dot(x-x.mean(), y-y.mean()) / np.dot(x-x.mean(), x-x.mean()))
            tables['window_slopes'].append(dict(identity, trailing_sizes=count, min_n=SIZES[-count], max_n=SIZES[-1],
                log_log_alpha=alpha, observations=len(sample)))
        medians = {n: statistics.median(r['mean_ns'] for r in rows if r['n']==n) for n in SIZES}
        for a, b in zip(SIZES, SIZES[1:]):
            tables['adjacent_slopes'].append(dict(identity, lower_n=a, upper_n=b,
                alpha=math.log2(medians[b]/medians[a]), lower_median_ns=medians[a], upper_median_ns=medians[b],
                ns_per_N_growth=(medians[b]/b)/(medians[a]/a)))
    by_id = defaultdict(dict)
    for row in means:
        by_id[tuple(row[k] for k in (*SPEC, 'n', 'N', 'invocation'))][row['clock']] = row['mean_ns']
    for key, r in by_id.items():
        tables['clock_differences'].append(dict(zip((*SPEC, 'n', 'N', 'invocation'), key),
            library_cpu_minus_native_cpu_ns=r['library_process_cpu']-r['native_process_cpu'],
            library_cpu_over_native_cpu=r['library_process_cpu']/r['native_process_cpu'],
            manual_minus_native_steady_ns=r['library_manual']-r['native_steady']))
    return tables


def write_csv(path, rows):
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with path.open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys); writer.writeheader(); writer.writerows(rows)


def verify_original_fits(rows, bound):
    audit = parse_json(read_bound(STUDY / 'arithmetic-audit-attempt01/audit.json', bound))
    old_path = OLD_ROOT / (STUDY / 'analysis-attempt01/model_fits.csv').relative_to(ROOT)
    original = list(csv.DictReader(io.StringIO(read_bound(relocated(old_path), bound,
                    audit['input_sha256'][str(old_path)]))))
    identity = lambda r: tuple(str(r[k]) for k in (*SPEC, 'clock', 'window', 'model'))
    found = {identity(r): r for r in original}
    require(len(found) == len(rows) == 1152, 'original fit matrix')
    for row in rows:
        previous = found[identity(row)]
        for field in ('coefficient_ns', 'normalized_rms'):
            require(math.isclose(float(previous[field]), row[field], rel_tol=2e-10, abs_tol=1e-12), 'original fit mismatch')
        require(previous['selected_for_this_clock'] == str(row['selected']), 'original model choice mismatch')


def summaries(tables):
    result=[]
    for table, extra in (('fits', ('window',)), ('holdouts', ('fold',)), ('relative_objective', ('window',))):
        grouped=defaultdict(list)
        for row in tables[table]:
            if row.get('status', 'identified') == 'identified':
                grouped[tuple(row[k] for k in ('family','algorithm','clock',*extra,'model'))].append(row)
        for key, rows in grouped.items():
            item=dict(zip(('family','algorithm','clock',*extra,'model'),key), table=table, curves=len(rows))
            for metric in ('normalized_rms','relative_rms','median_absolute_relative_error','intercept_ns'):
                values=[r[metric] for r in rows]
                item.update({metric+'_min':min(values),metric+'_median':statistics.median(values),metric+'_max':max(values)})
            item['negative_intercepts']=sum(r['intercept_ns']<0 for r in rows)
            item['nonpositive_predictions']=sum(r['nonpositive_predictions'] for r in rows)
            result.append(item)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    bound = {}
    receipt = dict(schema='kkt_exploratory_scaling_models_v1', validation='running', invocation=sys.argv,
                   python=sys.version, numpy=np.__version__, native_execution=False,
                   evidence_scope='Rechecked archived raw/certificate/hash evidence; original native lifecycle proof inherited, not rerun.',
                   previous_analyzer_arithmetic_imported=False, rows_removed=0, rows_adjusted=0, input_sha256=bound)
    try:
        read_bound(__file__, bound); read_bound(Path(__file__).with_name('PLAN.md'), bound)
        means, calls, choices = load(bound)
        tables = analyze(means, choices)
        verify_original_fits(tables['google_reproduction'], bound)
        tables['summaries'] = summaries(tables)
        tables['means'] = means
        tables['raw_calls'] = calls
        for name, rows in tables.items(): write_csv(output/(name+'.csv'), rows)
        for path, expected in bound.items(): require(sha(path)==expected, 'final input drift')
        receipt.update(validation='pass', table_counts={k: len(v) for k,v in tables.items()},
                       curves=24, raw_rows=len(calls), timed_rows=sum(r['phase']=='timed' for r in calls),
                       two_call_means=len(means), google_choices_verified=24, original_model_fits_verified=1152)
    except BaseException as error:
        receipt.update(validation='failed', error=repr(error)); raise
    finally:
        receipt['output_sha256']={p.name:sha(p) for p in output.iterdir() if p.is_file()}
        (output/'provenance.json').write_text(json.dumps(receipt, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:receipt[k] for k in ('validation','curves','raw_rows','two_call_means','table_counts')}))


if __name__ == '__main__': main()
