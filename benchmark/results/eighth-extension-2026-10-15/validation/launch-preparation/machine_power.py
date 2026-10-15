#!/usr/bin/env python3
"""Capture bounded, exclusive metadata before/after the frozen extension.

Run only after root release, through the existing nonnative validation guard.
This metadata does not establish sleep inhibition or thermal stability.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('/Users/random_person/Desktop/kkt-eighth-sampling')
STUDY = ROOT/'benchmark/results/eighth-extension-2026-10-15'
COMMANDS = [ ['/usr/bin/arch'], ['/usr/sbin/sysctl','-n','machdep.cpu.brand_string'],
             ['/usr/sbin/sysctl','-n','hw.memsize'], ['/usr/bin/sw_vers'],
             ['/usr/sbin/sysctl','vm.swapusage'], ['/usr/bin/pmset','-g','assertions'] ]


def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):
    with path.open('x') as out: json.dump(value,out,indent=2);out.write('\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=('before','after'),required=True)
    args=parser.parse_args()
    if Path.cwd().resolve()!=ROOT:raise ValueError('fixed worktree required')
    target=STUDY/('machine-'+args.phase+'.json')
    if target.exists():raise ValueError('refusing existing metadata')
    record={'schema':'eighth_extension_machine_metadata_v1','phase':args.phase,'created_utc':now(),
        'source':str(Path(__file__).resolve()),'source_sha256':sha(Path(__file__).resolve()),
        'validation':'pass','commands':[],'sleep_inhibition_verified':False,
        'note':'Metadata only. Prior caffeinate attempts failed; no verified sleep inhibition or thermal stability. Architecture output describes this metadata process, not the already proven arm64 solver binary. Unrelated host activity is uncontrolled.'}
    for command in COMMANDS:
        item={'command':command,'started_utc':now(),'timeout_seconds':15}
        try:
            result=subprocess.run(command,capture_output=True,text=True,timeout=15)
            item.update(exit_status=result.returncode,stdout=result.stdout,stderr=result.stderr)
            if result.returncode!=0:record['validation']='failed'
        except (subprocess.TimeoutExpired,OSError) as error:
            item.update(exit_status=None,error=repr(error));record['validation']='failed'
        item['finished_utc']=now();record['commands'].append(item)
    write(target,record)
    if record['validation']!='pass':raise SystemExit('machine query failed; retained metadata, stop')
    if args.phase=='after':
        folder=STUDY/'extension-power-audit'
        # Never put a full private power log at an unignored path.
        private=folder/'pmset.log'
        ignored=subprocess.run(['/usr/bin/git','check-ignore','--quiet',str(private)],cwd=ROOT,timeout=15)
        if ignored.returncode!=0:raise SystemExit('private power-log ignore rule missing')
        folder.mkdir(exist_ok=False)
        query={'command':['/usr/bin/pmset','-g','log'],'started_utc':now(),'timeout_seconds':60,
               'full_log_private_ignored':True,'sleep_inhibition_verified':False,'validation':'running'}
        with private.open('x') as stdout,(folder/'pmset.stderr').open('x') as stderr:
            try:
                result=subprocess.run(query['command'],stdout=stdout,stderr=stderr,timeout=60)
                query.update(exit_status=result.returncode,validation='pass' if result.returncode==0 else 'failed')
            except (subprocess.TimeoutExpired,OSError) as error:
                query.update(exit_status=None,validation='failed',error=repr(error))
        query.update(finished_utc=now(),log_sha256=sha(private),stderr_sha256=sha(folder/'pmset.stderr'))
        write(folder/'query.json',query)
        if query['validation']!='pass':raise SystemExit('power query failed; retain partial and omit --power-log')
    print(json.dumps({'validation':'pass','phase':args.phase,'machine_metadata':str(target),
                      'machine_sha256':sha(target),'sleep_inhibition_verified':False}))


if __name__=='__main__':main()
