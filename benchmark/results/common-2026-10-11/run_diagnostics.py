#!/usr/bin/env python3
"""Run ablation and Google Benchmark diagnostics serially into fresh outputs.
Usage: python3 THIS_FILE ABLATION_BINARY COMPLEXITY_BINARY NEW_OUTPUT_DIR
Build/test first. Never run this concurrently with the primary campaign.
"""
import csv
import datetime
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if len(sys.argv) != 4:
        raise ValueError(__doc__)
    ablation, complexity = (Path(s).resolve(strict=True) for s in sys.argv[1:3])
    out = Path(sys.argv[3]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    protected = [out/'metadata.json', out/'timing.json'] + [out/(tag+suffix)
        for tag in ('trace', 'primary', 'repeat', 'complexity') for suffix in ('.csv','.log')]
    if any(p.exists() for p in protected):
        raise ValueError('refusing to overwrite evidence')
    root = Path.cwd()
    source_hashes = {str(p): digest(p) for p in sorted(set(root.glob('*/*.cpp'))|set(root.glob('*/*.hpp')))}
    meta = {'revision': subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'source_sha256': source_hashes, 'runner_sha256': digest(__file__),
        'platform': platform.platform(), 'machine': platform.machine(),
        'protocol': 'See ../PROTOCOL.md. Serial trace, paired ablation primary/repeat, then Google Benchmark manual timing. Same algorithm source, separate build profiles.',
        'profiles': {'ablation':'Native Make -O3 -march=native; assertions enabled',
                     'complexity':'Bazel -c opt --copt=-O3, arm64 Apple SDK; NDEBUG, no -march=native'},
        'runs': {}}
    def save(): (out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    save()
    tasks = [('trace',ablation,['--work'],None),
             ('primary',ablation,[],1440), ('repeat',ablation,[],1440),
             ('complexity',complexity,['--common','--benchmark_out='+str(out/'timing.json'),
                                      '--benchmark_out_format=json'],None)]
    for tag, binary, args, expected in tasks:
        command = [str(binary),*args]
        info = {'command': command, 'binary_sha256':digest(binary),
                'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        meta['runs'][tag]=info;save()
        start=time.monotonic()
        with (out/(tag+'.csv')).open('w') as stdout, (out/(tag+'.log')).open('w') as stderr:
            run=subprocess.run(['/usr/bin/time','-l',*command],stdout=stdout,stderr=stderr)
        info.update(exit_status=run.returncode,wall_seconds_including_setup=time.monotonic()-start,
                    finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        info['output_sha256']={suffix:digest(out/(tag+suffix)) for suffix in ('.csv','.log')}
        save()
        if run.returncode: raise RuntimeError(f'{tag} failed')
        if tag=='complexity':
            document=json.loads((out/'timing.json').read_text())
            rows=[r for r in document['benchmarks'] if r.get('run_type')=='iteration']
            if len(rows)!=810 or any(r.get('error_occurred') or r.get('iterations')!=3 for r in rows):
                raise RuntimeError('invalid complexity matrix')
            info['basic_validated_rows']=810;info['timed_calls']=2430
            info['timing_json_sha256']=digest(out/'timing.json')
        else:
            rows=list(csv.DictReader((out/(tag+'.csv')).open(newline='')))
            if any(r['validation']!='pass' for r in rows) or (expected and len(rows)!=expected):
                raise RuntimeError(f'{tag} invalid rows')
            if tag=='trace' and len({(r['case_id'],r['graph_seed']) for r in rows})!=60:
                raise RuntimeError('incomplete trace')
            info['basic_validated_rows']=len(rows)
            if expected:info['checked_warmup_calls']=360
        if any(digest(path)!=value for path,value in source_hashes.items()):
            raise RuntimeError('source changed during diagnostics')
        save();print(tag+': checked',flush=True)

if __name__=='__main__':main()
