#!/usr/bin/env python3
"""Strict completed-run summaries; optional plotting is a separate release."""
import argparse
import csv
import importlib.util
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('host_memory_analysis_source', HERE/'run_host_memory.py')
host = importlib.util.module_from_spec(spec); spec.loader.exec_module(host)
base, proof = host.base, host.proof
MODES = ((1, 'one dependent chain'), (4, 'four independent chains'), (8, 'eight independent chains'), (0, 'contiguous scan'))

def read(path, bound):
    host.bind(bound, path); value = base.strict_json(Path(path).read_text()); base.recheck(bound)
    return value

def receipt(path, argv, expected, bound):
    value = proof.check_receipt(path, argv, bound)
    base.require(proof.exact(value, expected), 'receipt content mismatch')
    base.require(type(value['deadline_seconds']) is int and value['deadline_seconds'] == 300
                 and type(value['rss_limit_bytes']) is int and value['rss_limit_bytes'] == host.CAP, 'resource declaration drift')
    for suffix, field in (('.stdout', 'stdout_sha256'), ('.stderr', 'stderr_sha256')):
        log = path.with_suffix(suffix); host.bind(bound, log)
        base.require(base.sha(log) == value[field], 'log digest mismatch')
    return path.with_suffix('.stdout').read_text()

def load(path):
    path = path.resolve(); bound = host.initial(); host.bind(bound, Path(__file__))
    info = read(path, bound)
    base.require(info['schema'] == 'host_memory_run_v1' and info['validation'] == 'pass'
                 and info['native_process_may_still_be_running'] is False and info['assembly_review_acknowledged'] is True, 'incomplete run')
    for key, expected in (('checked_rows', 224), ('measured_rows', 168), ('warmup_rows', 56)):
        base.require(type(info[key]) is int and info[key] == expected, 'run count mismatch')
    base.recheck(info['bound_sha256'])
    for p in info['bound_sha256']: host.bind(bound, p)
    build_path = Path(info['build_record']); build = read(build_path, bound); sdk = Path(build['sdk'])
    binary = build_path.parent/'host_memory'; required = set(host.initial())
    required.update(str(p.resolve()) for p in (host.COMPILER, sdk/'SDKSettings.json', binary))
    base.require(build['schema'] == 'host_memory_build_v1' and build['validation'] == 'pass'
                 and build['native_process_may_still_be_running'] is False and len(build['commands']) == 7
                 and sdk.is_absolute() and sdk == sdk.resolve() and build['binary'] == str(binary), 'invalid build')
    base.recheck(build['bound_sha256'])
    for (label, argv), item in zip(host.recipe(build_path.parent, sdk), build['commands']):
        child = build_path.parent/(label+'.json')
        required.update(str(child.with_suffix(s)) for s in ('.json', '.stdout', '.stderr'))
        text = receipt(child, argv, item, bound); host.metadata(label, text, sdk)
        if label == 'compiler': base.require(build['compiler'] == text, 'compiler metadata drift')
    base.require(required <= set(build['bound_sha256']), 'omitted build proof')
    required.update(build['bound_sha256']); required.add(str(build_path))
    for key, artifact in (('binary_sha256', binary), ('source_sha256', host.SOURCE), ('compiler_sha256', host.COMPILER), ('sdk_settings_sha256', sdk/'SDKSettings.json')):
        base.require(base.sha(artifact) == build[key], 'build hash field drift')
    base.require(len(info['commands']) == 2, 'wrong child count'); values = []
    for order, item in zip(('ascending', 'descending'), info['commands']):
        child = path.parent/(order+'.json'); required.update(str(child.with_suffix(s)) for s in ('.json', '.stdout', '.stderr'))
        values.extend(host.rows(receipt(child, ['/usr/bin/arch', '-arm64', str(binary), order], item, bound), order))
    base.require(required <= set(info['bound_sha256']), 'omitted run proof')
    for p, digest in info['bound_sha256'].items(): base.require(bound[p] == digest, 'binding mismatch')
    for size in host.SIZES:
        group = [r for r in values if r['bytes'] == size]
        base.require(len({r['fingerprint'] for r in group}) == 1, 'array fingerprint drift')
        for chains, _ in MODES:
            base.require(len({(tuple(r['positions']), r['checksum']) for r in group if r['chains'] == chains}) == 1, 'result replay mismatch')
    base.recheck(bound)
    return values, bound

def tables(values):
    raw = [dict(row, positions=';'.join(map(str, row['positions'])),
                wall_ns_per_indexed_load=row['wall_ns']/host.VISITS, cpu_ns_per_indexed_load=row['cpu_ns']/host.VISITS) for row in values]
    summaries = []
    for order in ('ascending', 'descending'):
        for size in host.SIZES:
            for chains, label in MODES:
                cell = [r for r in values if r['size_order'] == order and r['bytes'] == size and r['chains'] == chains and not r['warmup']]
                base.require([r['repetition'] for r in cell] == [1, 2, 3], 'missing timed cell')
                for clock in ('wall', 'cpu'):
                    durations = [r[clock+'_ns'] for r in cell]
                    row = dict(size_order=order, bytes=size, chains=chains, mode=label, clock=clock, logical_loads=host.VISITS)
                    row.update({f'repetition_{i+1}_ns': value for i, value in enumerate(durations)})
                    for name, value in (('min', min(durations)), ('median', statistics.median(durations)), ('max', max(durations))):
                        row[name+'_ns'] = value; row[name+'_ns_per_indexed_load'] = value/host.VISITS
                    summaries.append(row)
    base.require(len(raw) == 224 and len(summaries) == 112, 'table coverage mismatch')
    return raw, summaries

def save_csv(path, values):
    with path.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(values[0])); writer.writeheader(); writer.writerows(values)

def plot(values, summaries, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.9), sharex=True, sharey=True)
    colors = ('#2b6cb0', '#e07a22', '#22916f', '#8a559f')
    for ax, clock in zip(axes, ('wall', 'cpu')):
        for (chains, label), color in zip(MODES, colors):
            for order, style in (('ascending', '-'), ('descending', '--')):
                cell = [r for r in summaries if r['clock'] == clock and r['chains'] == chains and r['size_order'] == order]
                x = [r['bytes'] for r in cell]; y = [r['median_ns_per_indexed_load'] for r in cell]
                ax.plot(x, y, style, marker='o', markersize=3, color=color, label=label+' / '+order)
                ax.vlines(x, [r['min_ns_per_indexed_load'] for r in cell], [r['max_ns_per_indexed_load'] for r in cell], color=color, alpha=.35)
                points = [r for r in values if r['chains'] == chains and r['size_order'] == order and not r['warmup']]
                ax.scatter([r['bytes'] for r in points], [r[clock+'_ns']/host.VISITS for r in points], s=7, color=color, alpha=.25)
        ax.set(xscale='log', yscale='log', title='Wall clock' if clock == 'wall' else 'Process CPU clock', xlabel='Index-array footprint')
        ax.set_xlim(host.SIZES[0]/1.35, host.SIZES[-1]*1.35)
        ax.set_xticks(host.SIZES, ['16 KiB', '64 KiB', '256 KiB', '1 MiB', '4 MiB', '16 MiB', '64 MiB'], rotation=25)
        ax.grid(True, alpha=.2)
    axes[0].set_ylabel('ns per logical indexed-array load (log scale)')
    fig.suptitle('Separate host calibration: dependent access, parallel chains and scan', y=.98)
    handles, labels = axes[0].get_legend_handles_labels(); fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(.5, .09), ncol=4, fontsize=8)
    fig.text(.5, .02, '3 timed calls per cell; median lines and full ranges. Same arrays in both orders; warmups retained in CSV.\nChase costs include loop and hot-stack stores: not pure load latency, cache-miss counts, or KKT attribution.', ha='center', fontsize=9)
    fig.subplots_adjust(left=.07, right=.99, top=.87, bottom=.30, wspace=.12)
    fig.savefig(output/'host-memory.png', dpi=180); fig.savefig(output/'host-memory.svg'); plt.close(fig)

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True); parser.add_argument('--plot', action='store_true')
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    status = dict(schema='host_memory_analysis_v1', validation='running', native_execution=False, figures_requested=args.plot)
    try:
        values, bound = load(args.capture); raw, summaries = tables(values)
        save_csv(args.output/'all-calls.csv', raw); save_csv(args.output/'summary.csv', summaries)
        if args.plot: plot(values, summaries, args.output)
        base.recheck(bound)
        status.update(validation='pass', input_sha256=bound, raw_rows=224, timed_rows=168, warmup_rows=56, summary_rows=112,
                      output_sha256={str(p.resolve()): base.sha(p) for p in args.output.iterdir() if p.is_file()})
    except BaseException as error:
        status.update(validation='failed', error=repr(error)); raise
    finally: base.write(args.output/'analysis.json', status)

if __name__ == '__main__': main()
