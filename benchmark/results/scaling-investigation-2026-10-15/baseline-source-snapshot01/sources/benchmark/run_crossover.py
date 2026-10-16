#!/usr/bin/env python3
"""Capture a serial crossover campaign and audit every native call's clocks.

Derived from the archived continuation runner. Raw timings and logs are never
filtered or overwritten; process CPU clocks are diagnostics, not substitutions
for the original elapsed-time measurement.
"""
import argparse
import csv
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import time

from crossover_clocks import audit


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_inventory(root):
    return {str(path.relative_to(root)): sha(path) for pattern in ('*/*.cpp', '*/*.hpp')
            for path in sorted(root.glob(pattern))}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binary', required=True, type=Path)
    p.add_argument('--manifest', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--mode', choices=['timing', 'trace', 'work'], default='timing')
    p.add_argument('--graph-seeds', default='17,42')
    p.add_argument('--sampling-seeds', default='0,1')
    p.add_argument('--repetitions', type=int, default=2)
    p.add_argument('--warmups', type=int, default=1)
    args = p.parse_args()
    out = args.output.resolve()
    if out.suffix != '.csv':
        raise ValueError('--output must end in .csv; log and metadata use distinct suffixes')
    out.parent.mkdir(parents=True, exist_ok=True)
    log, metadata = out.with_suffix('.log'), out.with_suffix('.json')
    clock_output = out.with_name(out.stem + '_clocks.json')
    if any(path.exists() for path in [out, log, metadata, clock_output]):
        raise ValueError('refusing to overwrite evidence')
    root = Path.cwd()
    binary, manifest = args.binary.resolve(strict=True), args.manifest.resolve(strict=True)
    source = source_inventory(root)
    command = [str(binary), '--manifest', str(manifest), '--mode', args.mode,
               '--graph-seeds', args.graph_seeds, '--sampling-seeds', args.sampling_seeds,
               '--repetitions', str(args.repetitions), '--warmups', str(args.warmups)]
    info = {'command': command, 'mode': args.mode,
            'working_directory': str(root.resolve()),
            'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            'source_sha256': source, 'binary_sha256': sha(binary),
            'manifest_sha256': sha(manifest), 'runner_sha256': sha(__file__),
            'profile': 'Native Make Apple clang C++17 -O3 -march=native; assertions enabled; work binary separately instrumented',
            'platform': platform.platform(), 'machine': platform.machine(),
            'clock_auditor_sha256': sha(Path(__file__).with_name('crossover_clocks.py')),
            'analyzer_sha256': sha(Path(__file__).with_name('analyze_continuation.py')),
            'clock_schema': 'call_clock_v1',
            'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    with metadata.open('x') as stream:
        stream.write(json.dumps(info, indent=2) + '\n')
    begin = time.monotonic()
    process = None
    interrupted = None
    def terminate(signum, frame):
        raise KeyboardInterrupt(f'capture received signal {signum}')
    signal.signal(signal.SIGTERM, terminate)
    with out.open('x') as stdout, log.open('x') as stderr:
        try:
            process = subprocess.Popen(['/usr/bin/time', '-l', *command], stdout=stdout,
                                       stderr=stderr, start_new_session=True)
            exit_status = process.wait()
        except BaseException as error:
            interrupted = repr(error)
            if process is not None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    exit_status = process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    exit_status = process.wait()
            else:
                exit_status = -1
    info.update(exit_status=exit_status, interruption=interrupted,
                wall_seconds_including_setup=time.monotonic()-begin,
                finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                output_sha256=sha(out), log_sha256=sha(log))
    info['monotonic_elapsed_seconds'] = info['wall_seconds_including_setup']
    info['utc_elapsed_seconds'] = (
        datetime.datetime.fromisoformat(info['finished_utc']) -
        datetime.datetime.fromisoformat(info['started_utc'])).total_seconds()
    metadata.write_text(json.dumps(info, indent=2) + '\n')
    if exit_status or interrupted:
        raise RuntimeError(f'campaign failed; retained {out} and {log}')
    with out.open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    if not rows or any(row['validation'] != 'pass' for row in rows):
        raise RuntimeError('campaign contains missing or unsuccessful output')
    with manifest.open() as stream:
        cases = list(csv.DictReader(stream))
    graph_count = len(cases) * len(args.graph_seeds.split(','))
    if args.mode == 'timing':
        expected = graph_count * len(args.sampling_seeds.split(',')) * args.repetitions * 2
        if len(rows) != expected:
            raise RuntimeError(f'incomplete timing row count {len(rows)} != {expected}')
        info['checked_warmup_calls'] = graph_count * len(args.sampling_seeds.split(',')) * args.warmups * 2
    elif args.mode == 'work':
        expected = graph_count * (len(args.sampling_seeds.split(',')) + 1)
        if len(rows) != expected:
            raise RuntimeError('incomplete work row count')
    if source_inventory(root) != source:
        raise RuntimeError('C++ source changed during campaign')
    if sha(binary) != info['binary_sha256'] or sha(manifest) != info['manifest_sha256']:
        raise RuntimeError('binary or manifest changed during campaign')
    if (sha(__file__) != info['runner_sha256'] or
            sha(Path(__file__).with_name('crossover_clocks.py')) != info['clock_auditor_sha256'] or
            sha(Path(__file__).with_name('analyze_continuation.py')) != info['analyzer_sha256']):
        raise RuntimeError('capture or analysis code changed during campaign')
    info['basic_validated_rows'] = len(rows)
    metadata.write_text(json.dumps(info, indent=2) + '\n')
    if args.mode == 'timing':
        try:
            clocks = audit(out, metadata)
            with clock_output.open('x') as stream:
                stream.write(json.dumps(clocks, indent=2) + '\n')
        except Exception as error:
            info['clock_audit_error'] = repr(error)
            metadata.write_text(json.dumps(info, indent=2) + '\n')
            raise
    print(f'{args.mode}: {len(rows)} checked rows; {info["wall_seconds_including_setup"]:.1f}s including setup')


if __name__ == '__main__':
    main()
