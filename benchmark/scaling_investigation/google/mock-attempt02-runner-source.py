#!/usr/bin/env python3
"""Fresh six-curve Google Benchmark comparison; no historical times are pooled."""
import argparse
import importlib.util
from pathlib import Path
import signal
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def module(path, name):
    previous = list(sys.path)
    try:
        sys.path.insert(0, str(path.parent))
        spec = importlib.util.spec_from_file_location(name, path)
        value = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(value)
        return value
    finally:
        sys.path[:] = previous


candidate = module(HERE.parent/'candidates/run_candidate.py', 'depth_google_candidate')
base = candidate.base
require, sha, write, read, add = base.require, base.sha, base.write, candidate.read, candidate.add
OLD_PACKAGE = ROOT/'benchmark/current_complexity'
trace = module(OLD_PACKAGE/'collect.py', 'depth_google_trace')
analyzer = module(OLD_PACKAGE/'analyze_complexity.py', 'depth_google_schema')
FAMILIES = ('leaf_hierarchy4', 'leaf_shuffled4', 'gnm_random')
POLICIES = ('reference', 'depth')
GRAPH, SAMPLER = 19000013, 3001
CHILD_SECONDS, CAMPAIGN_SECONDS, RSS = 600, 4200, 12*1024**3
COMMIT = '73d4d5e8d6d449fc8663765a42aa8aeeee844489'


def schedule():
    return [(policy, dict(family=family, algorithm='kkt', graph_seed=GRAPH,
                         sampling_seed=SAMPLER, size_order='ascending'))
            for index, family in enumerate(FAMILIES)
            for policy in candidate.policy_order(POLICIES, index)]


def inventory():
    return {str(p): sha(p) for p in (Path(__file__).resolve(), HERE/'PROTOCOL.md',
            OLD_PACKAGE/'current_complexity.cpp', OLD_PACKAGE/'collect.py', OLD_PACKAGE/'analyze_complexity.py')}


def historical():
    """Reuse a hash-pinned completed proof, not the old binary's timing values.

    The immutable completed capture contains its full previously checked freeze.
    Recheck every frozen dependency at its original physical path. This neither
    redirects that check to new objects nor mutates the old collector's globals.
    """
    info, digest = read(base.GOOGLE_CAPTURE)
    require(digest == base.GOOGLE_SHA and info['validation'] == 'pass', 'historical capture drift')
    frozen = info['frozen_protocol']; bound = {}
    add(bound, base.GOOGLE_CAPTURE, digest)
    value, freeze_hash = read(info['freeze'])
    require(freeze_hash == info['freeze_sha256'] and candidate.exact(value, frozen), 'historical freeze drift')
    add(bound, info['freeze'], freeze_hash)
    for key in ('bound_sha256', 'source_sha256', 'parent_helpers'):
        for path, expected in frozen[key].items(): add(bound, path, expected)
    old, old_hash = read(frozen['build_record'])
    require(old_hash == frozen['build_record_sha256'] and old['validation'] == 'pass'
            and old['google_benchmark_commit'] == COMMIT, 'historical library build drift')
    add(bound, frozen['build_record'], old_hash)
    require(bound.get(old['library']) == old['library_sha256'], 'archive absent from original full proof')
    smoke, smoke_hash = read(frozen['schema_smoke'])
    require(smoke_hash == frozen['schema_smoke_sha256'] and smoke['validation'] == 'pass', 'historical schema smoke drift')
    add(bound, frozen['schema_smoke'], smoke_hash)
    for name in ('collect.py', 'analyze_complexity.py', 'current_complexity.cpp'):
        original = str(Path(old['driver']).parent/name)
        require(sha(OLD_PACKAGE/name) == frozen['source_sha256'][original], 'reused driver/parser changed')
        add(bound, OLD_PACKAGE/name)
    expected = {}
    for policy, spec in schedule()[::2]:
        matches = [item for item in info['captures'] if candidate.exact(item['spec'], spec)]
        require(len(matches) == 1, 'historical input curve missing')
        item = matches[0]; add(bound, item['raw_csv'], item['raw_sha256'])
        rows, _ = trace.check_rows(item['raw_csv'], spec)
        for row in rows:
            key = row['family'], row['n']
            pair = row['input_fingerprint'], row['topology_fingerprint']
            require(key not in expected or expected[key] == pair, 'historical input drift')
            expected[key] = pair
    require(len(expected) == 33, 'incomplete historical input identities')
    base.recheck(bound)
    return old, expected, bound


def objects(build_path, record, policy):
    folder = Path(build_path).parent/(policy+'-reference')
    result = [folder/(Path(source).stem+'.o') for source in base.SOURCES]
    declared = record['variants'][policy+'-reference']['objects']
    require(len(result) == 8 and all(declared[str(p.relative_to(Path(build_path).parent))] == sha(p)
                                    for p in result), 'wrong eight production objects')
    return result


def commands(out, build_path, record, old):
    # Preserve the historical main's exact flags, including its two macro flags.
    # The additional compressed/eighth/depth policies live in the linked objects.
    old_compile = old['build_commands'][0]
    flags = old_compile[:old_compile.index('-c')]
    flags = ['-I'+str(ROOT) if arg == '-I'+old['working_directory'] else arg for arg in flags]
    require(record['compiler'] == old['compiler'] and record['sdk'] == old['sdk'], 'main/library toolchain mismatch')
    main = out/'current_complexity.o'
    result = [('compile-main', flags+['-c',str(OLD_PACKAGE/'current_complexity.cpp'),'-o',str(main)])]
    for policy in POLICIES:
        result.append(('link-'+policy, flags+list(map(str,objects(build_path,record,policy)))
                       +[str(main),old['library'],'-lpthread','-L'+record['sdk']+'/usr/lib',
                         '-Wl,-stack_size,0x20000000','-o',str(out/policy)]))
    return result


def build(out, build_path):
    out.mkdir(parents=True, exist_ok=False)
    record, bound = candidate.check_build(build_path)
    old, _, prior = historical()
    for p,h in prior.items(): add(bound,p,h)
    sources = inventory()
    for p,h in sources.items(): add(bound,p,h)
    result = dict(schema='kkt_depth_google_build_v1', validation='running',
                  candidate_build=str(build_path), candidate_build_sha256=sha(build_path),
                  source_sha256=sources, commands=[], variants={})
    try:
        require(base.bounded_output(['/usr/bin/arch','-arm64','/usr/bin/clang++','--version']) == record['compiler'], 'compiler drift')
        require(base.bounded_output(['/usr/bin/arch','-arm64','/usr/bin/xcrun','--show-sdk-path']).strip() == record['sdk'], 'SDK drift')
        for label, command in commands(out,build_path,record,old):
            base.recheck(bound)
            receipt = base.run_owned(command,out,label,timeout=180)
            require(candidate.check_receipt(out/(label+'.json'),command,bound) == receipt, 'build receipt drift')
            add(bound,out/(label+'.stdout'),receipt['stdout_sha256']); add(bound,out/(label+'.stderr'),receipt['stderr_sha256'])
            result['commands'].append(command)
        add(bound,out/'current_complexity.o')
        result['main_object_sha256'] = sha(out/'current_complexity.o')
        for policy in POLICIES:
            binary = out/policy; profile = base.binary_profile(binary)
            require(profile['description']=='Mach-O 64-bit executable arm64' and profile['stack_bytes']==536870912, 'non-native Google binary')
            add(bound,binary)
            result['variants'][policy] = dict(binary=str(binary),sha256=sha(binary),profile=profile,
                                              objects={str(p):sha(p) for p in objects(build_path,record,policy)})
        require(result['variants']['reference']['sha256'] != result['variants']['depth']['sha256'], 'identical policy binaries')
        base.recheck(bound); result['validation']='pass'
    except BaseException as error:
        result.update(validation='failed',error=repr(error)); raise
    finally:
        result['bound_sha256']=bound; write(out/'build.json',result)


def check_build(path):
    value, digest = read(path)
    require(value['schema']=='kkt_depth_google_build_v1' and value['validation']=='pass', 'incomplete Google build')
    parent_path = Path(value['candidate_build'])
    record,bound = candidate.check_build(parent_path)
    require(sha(parent_path)==value['candidate_build_sha256'], 'candidate build changed')
    old,expected,prior = historical()
    for p,h in prior.items(): add(bound,p,h)
    require(value['source_sha256']==inventory(), 'Google recipe/source drift')
    for p,h in value['source_sha256'].items(): add(bound,p,h)
    required=set(bound)
    recipe=commands(path.parent,parent_path,record,old)
    require(value['commands']==[command for _,command in recipe], 'main compile/link recipe drift')
    for label,command in recipe:
        receipt=candidate.check_receipt(path.parent/(label+'.json'),command,bound)
        add(bound,path.parent/(label+'.stdout'),receipt['stdout_sha256'])
        add(bound,path.parent/(label+'.stderr'),receipt['stderr_sha256'])
    add(bound,path.parent/'current_complexity.o',value['main_object_sha256'])
    require(set(value['variants'])==set(POLICIES), 'missing Google policy')
    for policy in POLICIES:
        variant=value['variants'][policy]; binary=path.parent/policy
        require(variant['binary']==str(binary) and variant['objects']=={str(p):sha(p) for p in objects(parent_path,record,policy)}, 'linked object substitution')
        require(variant['profile']['description']=='Mach-O 64-bit executable arm64' and variant['profile']['stack_bytes']==536870912, 'binary profile drift')
        add(bound,binary,variant['sha256'])
    require(value['variants']['reference']['sha256'] != value['variants']['depth']['sha256'], 'identical policies')
    required.update(bound)
    require(required<=set(value['bound_sha256']), 'build omitted mandatory proof')
    for p,h in value['bound_sha256'].items(): add(bound,p,h)
    add(bound,path,digest); base.recheck(bound)
    return value,record,expected,bound


def declaration():
    return dict(schedule=[dict(policy=p,spec=s) for p,s in schedule()], sizes=list(trace.SIZES),
                child_seconds=CHILD_SECONDS,campaign_seconds=CAMPAIGN_SECONDS,rss_bytes=RSS,
                rows=594,warmup_rows=198,timed_rows=396,certificates=198,
                callbacks_per_size=3,timed_calls_per_callback=2,rows_removed=0,rows_adjusted=0)


def receipt(path,command,bound):
    """Same owned-controller facts, separately declared 600 s Google ceiling."""
    value,digest=read(path); add(bound,path,digest)
    require(value['command']==command and value['cwd']==str(ROOT), 'curve argv/cwd drift')
    require(value['validation']=='pass' and type(value['exit_code']) is int and value['exit_code']==0,
            'unsuccessful Google child')
    require(value['group_empty'] is True and value['native_process_may_still_be_running'] is False, 'unknown group')
    require(type(value['pgid']) is int and value['pgid']>0, 'invalid group identity')
    start,exited,finished=[value[k] for k in ('started_monotonic_ns','exit_monotonic_ns','finished_monotonic_ns')]
    require(all(base.uint(x) for x in (start,exited,finished)) and start<=exited<=finished, 'invalid child interval')
    require(type(value['deadline_seconds']) in (int,float) and 0<value['deadline_seconds']<=CHILD_SECONDS
            and exited-start<=value['deadline_seconds']*1e9, 'Google curve deadline')
    require(type(value['rss_limit_bytes']) is int and value['rss_limit_bytes']==RSS, 'RSS ceiling changed')
    cleanup=value['cleanup']; final=cleanup['group_verification']
    require(cleanup['native_exit_known'] is True and cleanup['group_exit_known'] is True
            and cleanup['native_process_may_still_be_running'] is False
            and type(cleanup['returncode']) is int and cleanup['returncode']==0
            and type(cleanup['process_group']) is int and cleanup['process_group']==value['pgid']
            and final['validation']=='pass' and final['members']==[], 'incomplete group cleanup')
    failures=0
    for event in value['observations']:
        require(event['validation'] in ('pass','unavailable'), 'poisoned resource sampler')
        failures=failures+1 if event['validation']=='unavailable' else 0
        require(failures<3, 'three unavailable resource observations')
        if event['validation']=='pass': require(base.uint(event['rss_kib']) and event['rss_kib']*1024<=RSS, 'RSS limit')
    return value


def files(out,index):
    return dict(raw_csv=out/f'{index:02d}.csv',benchmark_json=out/f'{index:02d}.benchmark.json')


def curve(out,index,policy,spec,build,expected,bound):
    paths=files(out,index); label=f'curve-{index:02d}'
    command=trace.command(build['variants'][policy]['binary'],spec,paths)
    child=receipt(out/(label+'.json'),command,bound)
    for suffix,key in (('.stdout','stdout_sha256'),('.stderr','stderr_sha256')):
        add(bound,out/(label+suffix),child[key])
    for path in paths.values(): add(bound,path)
    rows,diagnostics=trace.check_rows(paths['raw_csv'],spec)
    certs=trace.certificates(out/(label+'.stderr'),rows)
    document,_=read(paths['benchmark_json'])
    checked=analyzer.validate_curve_library(document,spec,rows)
    for row in rows:
        require((row['input_fingerprint'],row['topology_fingerprint'])==expected[(row['family'],row['n'])], 'input changed from declared workload')
    trace.fingerprint_matrix(rows)
    base.recheck(bound)
    return dict(policy=policy,spec=spec,label=label,raw_csv=str(paths['raw_csv']),
                benchmark_json=str(paths['benchmark_json']),certificates=certs,
                diagnostics=diagnostics,library_big_o=checked['reports'][-2],library_rms=checked['reports'][-1]),rows,child


def capture(out,build_path,gates):
    out.mkdir(parents=True,exist_ok=False)
    build,parent,expected,bound=check_build(build_path)
    candidate.prerequisites(gates,Path(build['candidate_build']),parent,bound)
    write(out/'declaration.json',declaration()); add(bound,out/'declaration.json')
    start=time.monotonic_ns(); values=[]; children=[]
    info=dict(schema='kkt_depth_google_capture_v1',validation='running',build_record=str(build_path),
              build_record_sha256=sha(build_path),gates=[str(p) for p in gates],declaration=declaration(),
              started_monotonic_ns=start,captures=children)
    try:
        for index,(policy,spec) in enumerate(schedule()):
            base.recheck(bound); remaining=CAMPAIGN_SECONDS-(time.monotonic_ns()-start)/1e9
            require(remaining>0,'Google campaign deadline')
            command=trace.command(build['variants'][policy]['binary'],spec,files(out,index))
            base.run_owned(command,out,f'curve-{index:02d}',timeout=min(CHILD_SECONDS,remaining),rss_cap=RSS)
            item,rows,_=curve(out,index,policy,spec,build,expected,bound)
            children.append(item); values.extend(rows)
            write(out/'progress.json',dict(validation='in_progress',completed=len(children),total=6))
            print(f'Google curves: {len(children)}/6',flush=True)
        require(len(values)==594 and len(children)==6,'incomplete Google matrix')
        trace.fingerprint_matrix(values); base.recheck(bound)
        require(time.monotonic_ns()-start<=CAMPAIGN_SECONDS*1e9,'Google campaign deadline')
        info['validation']='pass'
    except BaseException as error:
        info.update(validation='failed',error=repr(error)); raise
    finally:
        info.update(finished_monotonic_ns=time.monotonic_ns(),bound_sha256=bound,
                    native_process_may_still_be_running=base._launch_blocked)
        write(out/'capture.json',info)


def load(path):
    info,digest=read(path)
    require(info['schema']=='kkt_depth_google_capture_v1' and info['validation']=='pass'
            and info['native_process_may_still_be_running'] is False and 'error' not in info, 'failed Google capture')
    build,parent,expected,bound=check_build(Path(info['build_record']))
    require(sha(info['build_record'])==info['build_record_sha256'],'Google build drift')
    candidate.prerequisites(info['gates'],Path(build['candidate_build']),parent,bound)
    actual,dh=read(path.parent/'declaration.json'); add(bound,path.parent/'declaration.json',dh)
    require(candidate.exact(actual,declaration()) and candidate.exact(info['declaration'],actual), 'declaration drift')
    start,end=info['started_monotonic_ns'],info['finished_monotonic_ns']
    require(base.uint(start) and base.uint(end) and 0<=end-start<=CAMPAIGN_SECONDS*1e9,'campaign interval')
    require(len(info['captures'])==6,'missing curve')
    rows=[]; previous=start
    for index,((policy,spec),stored) in enumerate(zip(schedule(),info['captures'])):
        item,values,child=curve(path.parent,index,policy,spec,build,expected,bound)
        require(candidate.exact(item,stored),'curve metadata/raw mismatch')
        require(previous<=child['started_monotonic_ns']<=child['finished_monotonic_ns']<=end,'overlapping/outside curve groups')
        previous=child['finished_monotonic_ns']
        rows.extend(dict(row,policy=policy) for row in values)
    require(set(bound)<=set(info['bound_sha256']),'capture omitted required proof')
    for p,h in info['bound_sha256'].items(): add(bound,p,h)
    require(len(rows)==594,'wrong row total'); trace.fingerprint_matrix(rows)
    add(bound,path,digest); base.recheck(bound)
    return info,rows,bound


def main():
    parser=argparse.ArgumentParser(); sub=parser.add_subparsers(dest='operation',required=True)
    build_parser=sub.add_parser('build'); build_parser.add_argument('output',type=Path)
    build_parser.add_argument('--candidate-build',type=Path,required=True); build_parser.add_argument('--released',action='store_true')
    cap=sub.add_parser('capture'); cap.add_argument('output',type=Path); cap.add_argument('--build',type=Path,required=True)
    cap.add_argument('--gate',type=Path,action='append',required=True); cap.add_argument('--released',action='store_true')
    check=sub.add_parser('check'); check.add_argument('capture',type=Path)
    args=parser.parse_args(); previous=signal.getsignal(signal.SIGTERM)
    def stopped(signum,frame): raise KeyboardInterrupt('Google controller received SIGTERM')
    signal.signal(signal.SIGTERM,stopped)
    try:
        if args.operation=='check':
            info,rows,_=load(args.capture.resolve()); print('PASS 6 curves / '+str(len(rows))+' native calls')
        else:
            require(args.released,'explicit root release required')
            if args.operation=='build': build(args.output.resolve(),args.candidate_build.resolve())
            else: capture(args.output.resolve(),args.build.resolve(),[p.resolve() for p in args.gate])
    finally: signal.signal(signal.SIGTERM,previous)


if __name__=='__main__': main()
