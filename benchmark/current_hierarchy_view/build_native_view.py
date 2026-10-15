#!/usr/bin/env python3
"""Build only a new root-view main, export once, and revalidate its full proof."""
import argparse
import hashlib
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

import validate_export as oracle

HERE=Path(__file__).resolve().parent
ROOT=Path('/Users/random_person/Desktop/kkt-eighth-sampling')
sys.path.insert(0,str(ROOT/'benchmark'))
import run_eighth_sampling as parent_engine
import build_compressed_queries as inherited

PARENT=ROOT/'benchmark/results/eighth-sampling-2026-10-15/freeze.json'
PARENT_SHA='2be7556d15b58f3f65cc380ac22b67c57fdf8aea747d651b9d648c6a1aa59d2f'
FLAGS=['-std=c++17','-O3','-Wall','-Wextra','-march=native','-DKKT_EXPERIMENT_RETAIN_PARALLEL','-DKKT_EXPERIMENT_EDGE_VIEW']
EMPTY_ENV=('CPLUS_INCLUDE_PATH','C_INCLUDE_PATH','CC','CXX','CFLAGS','CXXFLAGS','CPPFLAGS','LDFLAGS','MACOSX_DEPLOYMENT_TARGET')
require=oracle.require

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return oracle.read(Path(path))
def save(path,value,exclusive=True):inherited.save(path,value,exclusive=exclusive)
def exact(actual,expected,label):
    require(type(actual) is type(expected) and actual==expected,label)
    if type(expected) is dict:
        for key in expected:exact(actual[key],expected[key],label+': '+key)
    elif type(expected) is list:
        for a,b in zip(actual,expected):exact(a,b,label)
def output(command):return subprocess.check_output(command,cwd=ROOT,text=True,timeout=10)
def check_bound(bound):
    for path,digest in bound.items():require(Path(path).is_absolute() and sha(path)==digest,'artifact changed: '+path)

def parent_proof():
    require(sha(PARENT)==PARENT_SHA,'wrong eighth freeze')
    frozen,_=parent_engine.check_freeze(PARENT) # Full unscoped original proof.
    record=frozen['variants']['eighth']['build']['record']
    exact(record['common_compile_flags'],FLAGS,'different frozen main flags')
    require(len(record['object_paths'])==8 and record['private_acceptance_mask']==7 and
            record['sampling_policy']=='eighth' and record['sampling_words_per_visited_edge']==1 and
            record['verifier_policy']=='compressed','wrong frozen production policy')
    return frozen,record

def source_inventory(frozen):
    bound={str(PARENT):PARENT_SHA}
    bound.update({str(ROOT/name):digest for key in ('source_sha256','build_recipe_sha256') for name,digest in frozen[key].items()})
    bound.update(frozen['python_source_sha256'])
    for variant in frozen['variants'].values():
        artifact=variant['build'];record=artifact['record']
        bound.update({artifact['path']:artifact['sha256'],record['binary']:record['binary_sha256'],
                      record['main_object']:record['main_object_sha256'],record['build_log']:record['build_log_sha256']})
        bound.update({path:record['object_sha256'][name] for name,path in record['object_paths'].items()})
    for path in HERE.iterdir():
        if path.suffix in ('.py','.cpp','.html','.md'):bound[str(path.resolve())]=sha(path)
    check_bound(bound);return bound

def commands(parent,directory):
    base=['/usr/bin/arch','-arm64','/usr/bin/clang++','-isysroot',parent['sdk'],*FLAGS,'-I'+str(ROOT)]
    main=directory/'root_view.o';binary=directory/'root_view'
    return [base+['-c',str(HERE/'export_root_view.cpp'),'-o',str(main)],
            base+list(parent['object_paths'].values())+[str(main),'-L'+parent['sdk']+'/usr/lib','-Wl,-stack_size,0x20000000','-o',str(binary)],
            ['/usr/bin/arch','-arm64',str(binary)]]

def environment_policy(value):
    exact(set(value),{'removed','required_empty','retained'},'environment schema')
    exact(set(value['removed']),{'CPATH','LIBRARY_PATH'},'environment removals')
    exact(set(value['required_empty']),set(EMPTY_ENV),'missing environment checks')
    exact(set(value['retained']),{'SDKROOT','DEVELOPER_DIR'},'retained environment keys')
    require(all(item is None or type(item) is str for values in value.values() for item in values.values()),'environment value type')
    require(all(item in (None,'') for item in value['required_empty'].values()),'unreviewed compiler environment override')

def check_groups(path,wanted,intervals):
    proof=read(path);require(set(proof)=={'groups'} and len(proof['groups'])==len(wanted)==len(intervals)==3,'incomplete three-command matrix')
    previous=-1
    for row,command,interval in zip(proof['groups'],wanted,intervals):
        exact(row['command'],command,'different native command');exact(interval['command'],command,'interval command')
        start,finish=interval['started_monotonic_ns'],interval['finished_monotonic_ns']
        require(type(start) is int and type(finish) is int and previous<=start<finish and finish-start<=300*10**9,'command overlap/deadline')
        previous=finish;pid=row['process_group'];require(type(pid) is int and pid>0,'invalid group ID')
        exact(row.get('exit_status'),0,'native command failed');require('error' not in row,'native command error')
        cleanup=row['cleanup'];final=cleanup['group_verification']
        for key,value in dict(native_exit_known=True,group_exit_known=True,native_process_may_still_be_running=False,returncode=0,process_group=pid).items():
            exact(cleanup[key],value,'unknown owned exit '+key)
        a,b=cleanup['started_monotonic_ns'],cleanup['finished_monotonic_ns']
        require(type(a) is int and type(b) is int and start<=a<=b<=finish,'cleanup interval')
        exact(final['validation'],'pass','final observation unavailable');exact(final['members'],[],'owned group nonempty');exact(final['rss_kib'],0,'nonempty final RSS')
        require(type(final['monotonic_ns']) is int and a<=final['monotonic_ns']<=b,'final sample outside cleanup')
        last=-1;unavailable=0
        for observation in [*row['observations'],final]:
            exact(observation['process_group'],pid,'wrong observed group')
            now=observation['monotonic_ns'];require(type(now) is int and start<=now<=finish and now>last,'observation order/interval');last=now
            if observation['validation']=='unavailable':
                unavailable+=1;require(unavailable<3,'three unavailable observations')
            else:
                exact(observation['validation'],'pass','unsupported observation');unavailable=0
                rss=observation['rss_kib'];require(type(rss) is int and 0<=rss<=40*1024*1024,'RSS limit/type')
                members=observation['members'];require(type(members) is list and
                    all(type(m['pid']) is int and m['pid']>0 and type(m['rss_kib']) is int and m['rss_kib']>=0 for m in members) and
                    sum(m['rss_kib'] for m in members)==rss,'RSS member sum')

def check_objects(record,parent):
    for key in ('object_paths','object_sha256','compiler','compiler_command','sdk'):
        exact(record[key],parent[key],'frozen physical objects/toolchain '+key)
    for name,path in record['object_paths'].items():require(sha(path)==record['object_sha256'][name],'changed frozen object')

def check_record(path):
    path=Path(path).resolve(strict=True);initial=sha(path);record=read(path)
    frozen,parent=parent_proof();sources=source_inventory(frozen)
    for key,value in dict(schema='current_hierarchy_export_build_v1',validation='pass',working_directory=str(ROOT),
                          parent_freeze=str(PARENT),parent_freeze_sha256=PARENT_SHA,native_execution=True,
                          only_new_main=True,production_objects_rebuilt=False,performance_execution=False,owned_groups_verified_empty=True).items():
        exact(record.get(key),value,'export record '+key)
    exact(record['source_sha256'],sources,'initial source inventory changed');check_objects(record,parent)
    environment_policy(record['environment_policy'])
    exact(output(parent['compiler_command']),parent['compiler'],'current compiler differs')
    exact(output(['/usr/bin/arch','-arm64','/usr/bin/xcrun','--show-sdk-path']).strip(),parent['sdk'],'current SDK differs')
    directory=path.parent/'native';wanted=commands(parent,directory)
    exact(record['commands'],wanted,'different two-command build/export recipe')
    expected_paths=dict(main_object=directory/'root_view.o',binary=directory/'root_view',export_json=path.parent/'export.json',
                        build_log=path.parent/'build.log',export_log=path.parent/'export.stderr',owned_groups=path.parent/'owned-groups.json')
    bound=dict(sources)
    for key,expected in expected_paths.items():
        exact(record[key],str(expected),'unexpected artifact path '+key)
        require(sha(expected)==record[key+'_sha256'],'artifact hash differs '+key);bound[str(expected)]=record[key+'_sha256']
    exact(output(['/usr/bin/file','-b',record['main_object']]).strip(),'Mach-O 64-bit object arm64','translated new main')
    exact(record['binary_profile'],parent_engine.control.native.binary_profile(Path(record['binary'])),'actual executable profile differs')
    exact(record['binary_profile']['file_description'],'Mach-O 64-bit executable arm64','wrong architecture')
    exact(record['binary_profile']['main_stack_bytes'],536870912,'wrong main stack')
    check_groups(record['owned_groups'],wanted,record['command_intervals'])
    exact(record['export_validation'],oracle.validate(read(Path(record['export_json']))),'independent export validation differs')
    final,_=parent_proof();exact(final,frozen,'full parent proof changed during check')
    bound[str(path)]=initial;check_bound(bound)
    # Build-view's stable interface uses export_sha256; the persisted canonical
    # path/hash field remains export_json[_sha256]. Both name identical bytes.
    return {**record,'export_sha256':record['export_json_sha256'],'bound_sha256':bound}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--released',action='store_true');args=parser.parse_args()
    require(args.released,'explicit root native-export release required')
    require(Path.cwd().resolve()==ROOT and inherited.ROOT==ROOT and HERE==ROOT/'benchmark/current_hierarchy_view',
            'install the reviewed package at benchmark/current_hierarchy_view and run from the frozen eighth worktree')
    args.output=args.output.resolve();args.output.mkdir(parents=True,exist_ok=False)
    state=dict(schema='current_hierarchy_export_attempt_v1',validation='running',invocation=sys.argv,
               started_monotonic_ns=time.monotonic_ns(),native_execution_authorized=True,performance_execution=False,
               owned_groups_verified_empty=False,native_process_may_still_be_running=False,command_intervals=[])
    save(args.output/'invocation.json',state)
    try:
        frozen,parent=parent_proof();sources=source_inventory(frozen)
        exact(output(parent['compiler_command']),parent['compiler'],'compiler changed before build')
        exact(output(['/usr/bin/arch','-arm64','/usr/bin/xcrun','--show-sdk-path']).strip(),parent['sdk'],'SDK changed before build')
        environment=dict(os.environ);policy=dict(removed={key:environment.pop(key,None) for key in ('CPATH','LIBRARY_PATH')},
            required_empty={key:environment.get(key) for key in EMPTY_ENV},retained={key:environment.get(key) for key in ('SDKROOT','DEVELOPER_DIR')})
        environment_policy(policy);state.update(source_sha256=sources,environment_policy=policy)
        directory=args.output/'native';directory.mkdir();wanted=commands(parent,directory)
        guard=inherited.SerialGuard(args.output/'owned-groups.json')
        for index,command in enumerate(wanted):
            check_bound(sources);interval=dict(command=command,started_monotonic_ns=time.monotonic_ns());state['command_intervals'].append(interval)
            state['native_process_may_still_be_running']=True
            try:
                if index<2:
                    with (args.output/'build.log').open('x' if index==0 else 'a') as stream:
                        stream.write('$ '+shlex.join(command)+'\n');stream.flush();guard.run(command,stdout=stream,env=environment)
                else:
                    with (args.output/'export.json').open('x') as out,(args.output/'export.stderr').open('x') as error:
                        guard.run(command,stdout=out,stderr=error,env=environment)
            finally:interval['finished_monotonic_ns']=time.monotonic_ns()
            require(interval['finished_monotonic_ns']-interval['started_monotonic_ns']<=300*10**9,'complete command interval exceeds 300 seconds')
        validation=oracle.validate(read(args.output/'export.json'))
        check_bound(sources);exact(parent_proof()[0],frozen,'parent changed during build/export')
        record=dict(schema='current_hierarchy_export_build_v1',validation='pass',working_directory=str(ROOT),
                    parent_freeze=str(PARENT),parent_freeze_sha256=PARENT_SHA,native_execution=True,only_new_main=True,
                    production_objects_rebuilt=False,performance_execution=False,owned_groups_verified_empty=True,
                    source_sha256=sources,environment_policy=policy,commands=wanted,command_intervals=state['command_intervals'],
                    export_validation=validation,**{key:parent[key] for key in ('object_paths','object_sha256','compiler','compiler_command','sdk')})
        for key,path_ in dict(main_object=directory/'root_view.o',binary=directory/'root_view',export_json=args.output/'export.json',
                             build_log=args.output/'build.log',export_log=args.output/'export.stderr',owned_groups=args.output/'owned-groups.json').items():
            record[key]=str(path_);record[key+'_sha256']=sha(path_)
        record['binary_profile']=parent_engine.control.native.binary_profile(directory/'root_view')
        receipt=args.output/'build-record.json';save(receipt,record)
        try:check_record(receipt)
        except BaseException:
            record['validation']='failed';save(receipt,record,exclusive=False);raise
        state.update(validation='pass',owned_groups_verified_empty=True,native_process_may_still_be_running=False,
                     build_record=str(receipt),build_record_sha256=sha(receipt),export_validation=validation)
    except BaseException as error:state.update(validation='failed',error=repr(error));raise
    finally:
        state['finished_monotonic_ns']=time.monotonic_ns();save(args.output/'attempt.json',state)
    print('Native root export fully checked; three owned command groups empty. No performance measurement.')

if __name__=='__main__':main()
