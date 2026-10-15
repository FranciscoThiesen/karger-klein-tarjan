#!/usr/bin/env python3
"""Archive one bounded nonperformance Python validation attempt; no overwrite."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def sha(path):
    with Path(path).open('rb') as stream:
        digest=hashlib.sha256()
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix',type=Path,required=True)
    parser.add_argument('--source',type=Path,action='append',default=[])
    parser.add_argument('--timeout',type=float,default=180)
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args();command=args.command
    if command[:1]==['--']:command=command[1:]
    if len(command)<3 or command[0]!='/usr/bin/python3' or command[1]!='-B':
        raise ValueError('only an explicit /usr/bin/python3 -B validation is permitted')
    prefix=args.prefix.resolve();prefix.parent.mkdir(parents=True,exist_ok=True)
    paths={name:Path(str(prefix)+'.'+suffix) for name,suffix in
           (('receipt','json'),('stdout','stdout'),('stderr','stderr'))}
    if any(path.exists() for path in paths.values()):raise ValueError('refusing overwrite')
    sources=[Path(__file__).resolve(),*[path.resolve(strict=True) for path in args.source]]
    before={str(path):sha(path) for path in sources};started=time.monotonic_ns()
    info=dict(schema='independent_postcapture_validation_v1',validation='running',command=command,
        working_directory=str(Path.cwd()),started_utc=now(),started_monotonic_ns=started,
        source_sha256_before=before,native_solver_execution=False,owned_groups_verified_empty=False)
    with paths['receipt'].open('x') as stream:json.dump(info,stream,indent=2);stream.write('\n')
    process=None
    try:
        with paths['stdout'].open('x') as out,paths['stderr'].open('x') as err:
            process=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
            info['process_group']=process.pid
            try:info['exit_status']=process.wait(timeout=args.timeout)
            except BaseException as error:
                info['interruption']=repr(error)
                for sig,budget in ((signal.SIGTERM,3),(signal.SIGKILL,3)):
                    if process.poll() is not None:break
                    try:os.killpg(process.pid,sig)
                    except ProcessLookupError:pass
                    try:process.wait(timeout=budget)
                    except subprocess.TimeoutExpired:pass
                info['exit_status']=process.poll()
                raise
        # A separate bounded OS process-table read proves no member remains in
        # this owned group. Unrelated process information is not persisted.
        result=subprocess.run(['/bin/ps','-axo','pid=,pgid='],capture_output=True,text=True,timeout=3,check=True)
        pairs=[tuple(map(int,line.split())) for line in result.stdout.splitlines() if line.strip()]
        members=[pid for pid,group in pairs if group==process.pid]
        info['group_exit_verification']=dict(validation='pass',process_group=process.pid,members=members,
            monotonic_ns=time.monotonic_ns(),utc=now(),method='/bin/ps -axo pid=,pgid=',query_exit_status=result.returncode)
        info['owned_groups_verified_empty']=not members
        after={str(path):sha(path) for path in sources};info['source_sha256_after']=after
        if info['exit_status']!=0 or members or before!=after:raise ValueError('validation, exit, group or source gate failed')
        info['validation']='pass'
    except BaseException as error:
        info.update(validation='failed',error=repr(error))
    finally:
        info.update(finished_utc=now(),finished_monotonic_ns=time.monotonic_ns())
        info['elapsed_seconds']=(info['finished_monotonic_ns']-started)/1e9
        for name in ('stdout','stderr'):
            info[name]=str(paths[name])
            if paths[name].exists():info[name+'_sha256']=sha(paths[name])
        paths['receipt'].write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps({name:info.get(name) for name in
        ('validation','exit_status','elapsed_seconds','owned_groups_verified_empty','error')},indent=2))
    raise SystemExit(0 if info['validation']=='pass' else 1)


if __name__=='__main__':main()
