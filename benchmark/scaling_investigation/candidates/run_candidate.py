#!/usr/bin/env python3
"""Isolated depth-query experiment; reuse frozen process controls and retain every input."""
import argparse
import importlib.util
import json
from pathlib import Path
import signal
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
_spec = importlib.util.spec_from_file_location('scaling_candidate_base', HERE.parent/'run.py')
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)
require, sha, write = base.require, base.sha, base.write
POLICIES = ('reference', 'depth')
KINDS = ('reference', 'work', 'phase', 'allocation')
CHANGED = {'verifier/verifier_v2.cpp', 'verifier/experimental_compressed_queries.hpp'}
NEW_HEADER = 'verifier/experimental_depth_queries.hpp'
VARIANTS = {p+'-'+k: (p, k) for k in KINDS for p in POLICIES}
VARIANTS.update({'depth_noinline-'+k: ('depth_noinline',k) for k in ('reference','phase')})


def defines(policy, kind):
    return (base.VARIANTS[kind] + (['-DKKT_EXPERIMENT_DEPTH_QUERIES'] if policy != 'reference' else [])
            + (['-DKKT_EXPERIMENT_DEPTH_QUERY_NOINLINE'] if policy == 'depth_noinline' else []))


def policy_order(policies, index):
    if len(policies) == 3:
        offset=index%3; return policies[offset:]+policies[:offset]
    return policies if index%2 == 0 else tuple(reversed(policies))


def read(path):
    path = Path(path).resolve(); before = sha(path)
    value = base.strict_json(path.read_text())
    require(sha(path) == before, 'JSON changed while reading: '+str(path))
    return value, before


def add(bound, path, digest=None):
    path = str(Path(path).resolve()); digest = sha(path) if digest is None else digest
    require(path not in bound or bound[path] == digest, 'conflicting provenance: '+path)
    bound[path] = digest


def identity(case):
    return tuple(case[k] for k in ('family', 'n', 'graph_seed', 'sampling_seed'))


def exact(a,b):
    return json.dumps(a,sort_keys=True,allow_nan=False)==json.dumps(b,sort_keys=True,allow_nan=False)


def snapshot(out, build_record):
    """Run before applying the patch. Copy every source, never raw data or binaries."""
    out.mkdir(parents=True, exist_ok=False)
    record, digest = read(build_record)
    require(record['validation'] == 'pass', 'baseline build did not pass')
    source = record['source_sha256']; base.recheck(source)
    copies = {}
    for original, expected in source.items():
        destination = out/'sources'/Path(original).resolve().relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as stream: stream.write(Path(original).read_bytes())
        require(sha(destination) == expected, 'source changed during snapshot')
        copies[original] = str(destination.resolve())
    base.recheck(source); require(sha(build_record) == digest, 'baseline build drift')
    result = dict(schema='kkt_scaling_source_snapshot_v1', validation='pass',
                  baseline_build_record=str(build_record.resolve()), baseline_build_record_sha256=digest,
                  source_sha256=source, copies=copies)
    write(out/'snapshot.json', result)


def check_snapshot(path):
    value, digest = read(path)
    require(value['schema'] == 'kkt_scaling_source_snapshot_v1' and value['validation'] == 'pass', 'bad snapshot')
    old, old_digest = read(value['baseline_build_record'])
    require(old_digest == value['baseline_build_record_sha256'] and old['validation'] == 'pass', 'baseline build drift')
    require(value['source_sha256'] == old['source_sha256'] and set(value['copies']) == set(old['source_sha256']), 'incomplete source snapshot')
    bound = {}; add(bound, path, digest); add(bound, value['baseline_build_record'], old_digest)
    for original, expected in value['source_sha256'].items():
        add(bound, value['copies'][original], expected)
    # The imported validator stays live at the original path and must be the frozen one.
    for original in (HERE.parent/'run.py', ROOT/'benchmark/work_metrics.hpp'):
        add(bound, original, value['source_sha256'][str(original)])
    base.recheck(bound)
    return value, old, bound


def check_receipt(path, command, bound):
    receipt, digest = read(path); add(bound, path, digest)
    require(receipt['command'] == command and receipt['cwd'] == str(ROOT), 'wrong child command')
    require(receipt['validation'] == 'pass' and type(receipt['exit_code']) is int and receipt['exit_code'] == 0,
            'unsuccessful native child')
    require(receipt['group_empty'] is True and receipt['native_process_may_still_be_running'] is False, 'unknown native group')
    require(type(receipt['pgid']) is int and receipt['pgid'] > 0, 'invalid native group ID')
    start, exited, finished = [receipt[k] for k in ('started_monotonic_ns','exit_monotonic_ns','finished_monotonic_ns')]
    require(all(base.uint(x) for x in (start,exited,finished)) and start <= exited <= finished, 'invalid child interval')
    require(0 < receipt['deadline_seconds'] <= 300 and exited-start <= receipt['deadline_seconds']*1e9, 'native exit deadline')
    cleanup = receipt['cleanup']
    require(cleanup['native_exit_known'] is True and cleanup['group_exit_known'] is True
            and cleanup['native_process_may_still_be_running'] is False, 'incomplete cleanup proof')
    require(type(cleanup['returncode']) is int and cleanup['returncode'] == 0 and cleanup['process_group'] == receipt['pgid'], 'cleanup identity')
    verification = cleanup['group_verification']
    require(verification['validation'] == 'pass' and verification['members'] == [], 'nonempty final group')
    failures = 0
    for event in receipt['observations']:
        require(event['validation'] in ('pass','unavailable'), 'poisoned resource observation')
        failures = failures+1 if event['validation'] != 'pass' else 0
        require(failures < 3, 'three unavailable resource observations')
        if event['validation'] == 'pass':
            require(base.uint(event['rss_kib']) and event['rss_kib']*1024 <= receipt['rss_limit_bytes'], 'resource ceiling')
    require(receipt['rss_limit_bytes'] <= 12*1024**3, 'relaxed RSS ceiling')
    return receipt


def raw_rows(raw, case, kind, repetitions, expected, bound):
    digest = sha(raw)
    values = [base.strict_json(line) for line in Path(raw).read_text().splitlines()]
    base.validate_rows(values, case, kind, repetitions, base.work_fields(), expected)
    require(sha(raw) == digest, 'raw drift during read'); add(bound, raw, digest)
    return values


def baseline_work(path, snapshot_path):
    snap, build, bound = check_snapshot(snapshot_path)
    info, digest = read(path); add(bound, path, digest)
    require(info['validation'] == 'pass' and info['native_process_may_still_be_running'] is False, 'incomplete baseline work')
    # Only original source paths may be redirected, always to identical archived bytes.
    for original, expected in info['bound_sha256'].items():
        add(bound, snap['copies'].get(original, original), expected)
    require(info['bound_sha256'][snap['baseline_build_record']] == snap['baseline_build_record_sha256'], 'work/build mismatch')
    declaration, _ = read(Path(path).parent/'declaration.json')
    require(declaration['mode'] == 'work' and declaration['cases'] == base.matrix('work')
            and declaration['variants'] == ['work'] and declaration['repetitions'] == 1 and declaration['warmups'] == 1,
            'wrong baseline work declaration')
    cases = base.matrix('work'); require(len(info['captures']) == len(cases) == 72, 'missing baseline work inputs')
    historical = base.historical_inputs(); result = {}
    for index, (case, item) in enumerate(zip(cases,info['captures'])):
        label = f'{index:03d}-work'
        require(item['case'] == case and item['variant'] == 'work' and item['label'] == label and item['rows'] == 2, 'baseline order/identity')
        command = ['/usr/bin/arch','-arm64',build['variants']['work']['binary'],case['family'],str(case['n']),
                   str(case['graph_seed']),str(case['sampling_seed']),'1']
        receipt = check_receipt(Path(path).parent/(label+'.json'), command, bound)
        raw = Path(path).parent/(label+'.stdout'); err = Path(path).parent/(label+'.stderr')
        values = raw_rows(raw,case,'work',1,historical[identity(case)],bound)
        require(sha(raw) == item['stdout_sha256'] == receipt['stdout_sha256'], 'baseline raw join')
        add(bound,err,receipt['stderr_sha256']); result[identity(case)] = values
    base.recheck(bound)
    return result, bound


def inventory():
    result = base.source_inventory()
    for path in (Path(__file__), HERE/'CANDIDATE_PROTOCOL.md', HERE/'depth_queries.patch'):
        add(result,path)
    add(result,HERE/'depth_queries_test.cpp')
    return result


def isolated_sources(snap):
    altered={str(Path(p).relative_to(ROOT)) for p,h in snap['source_sha256'].items() if sha(p)!=h}
    require(altered==CHANGED and (ROOT/NEW_HEADER).is_file(),'unexpected native/source delta')
    require(set(base.source_inventory())==set(snap['source_sha256'])|{str(ROOT/NEW_HEADER)},'unexpected added/removed native sources')
    return sorted(altered)


def paired_objects(variants):
    for kind in KINDS:
        a,b=[{Path(p).name:h for p,h in variants[policy+'-'+kind]['objects'].items()}
             for policy in POLICIES]
        require(set(a)==set(b) and {key for key in a if a[key]!=b[key]}=={'verifier_v2.o'},'paired object identity drift')
    for kind in ('reference','phase'):
        a,b=[{Path(p).name:h for p,h in variants[policy+'-'+kind]['objects'].items()}
             for policy in ('depth','depth_noinline')]
        require(set(a)==set(b) and {key for key in a if a[key]!=b[key]}<={'verifier_v2.o'},'noinline object identity drift')


def build(out, snapshot_path):
    out.mkdir(parents=True, exist_ok=False)
    snap, parent, inherited = check_snapshot(snapshot_path)
    current = inventory()
    altered = isolated_sources(snap)
    # Shared original helper/driver/protocol files remain unchanged; all new recipe bytes are bound.
    sdk = base.bounded_output(['/usr/bin/arch','-arm64','/usr/bin/xcrun','--show-sdk-path']).strip()
    compiler = base.bounded_output(['/usr/bin/arch','-arm64','/usr/bin/clang++','--version'])
    require(sdk == parent['sdk'] and compiler == parent['compiler'], 'compiler/SDK changed')
    flags = base.BASE_FLAGS+['-isysroot',sdk]
    records, variants = [], {}
    status = dict(schema='kkt_depth_candidate_build_v1', validation='running', source_sha256=current,
                  snapshot=str(snapshot_path.resolve()), snapshot_sha256=sha(snapshot_path), sdk=sdk, compiler=compiler,
                  base_flags=flags, variants=variants, commands=records, changed_original_paths=altered)
    try:
        for name,(policy,kind) in VARIANTS.items():
            folder=out/name; folder.mkdir(); objects=[]
            macros=defines(policy,kind)
            for index,source in enumerate(base.SOURCES+['benchmark/scaling_investigation/diagnostic.cpp']):
                base.recheck(current); base.recheck(inherited)
                obj=folder/(Path(source).stem+'.o'); objects.append(str(obj))
                command=['/usr/bin/arch','-arm64','/usr/bin/clang++']+flags+macros+['-c',str(ROOT/source),'-o',str(obj)]
                records.append(base.run_owned(command,folder,f'compile-{index}',timeout=180,rss_cap=4*1024**3))
            binary=folder/'diagnostic'
            command=['/usr/bin/arch','-arm64','/usr/bin/clang++','-isysroot',sdk,'-L'+sdk+'/usr/lib']+objects+['-Wl,-stack_size,0x20000000','-o',str(binary)]
            records.append(base.run_owned(command,folder,'link',timeout=60))
            variants[name]=dict(policy=policy,instrumentation=kind,defines=macros,binary=str(binary),sha256=sha(binary),
                                profile=base.binary_profile(binary),objects={str(Path(p).relative_to(out)):sha(p) for p in objects})
        paired_objects(variants)
        base.recheck(current); base.recheck(inherited); status['validation']='pass'
    except BaseException as error:
        status.update(validation='failed',error=repr(error)); raise
    finally: write(out/'build.json',status)


def check_build(path):
    path=Path(path).resolve()
    record,digest=read(path); require(record['schema']=='kkt_depth_candidate_build_v1' and record['validation']=='pass','bad candidate build')
    snap,parent,bound=check_snapshot(Path(record['snapshot'])); add(bound,path,digest)
    require(sha(record['snapshot'])==record['snapshot_sha256'],'snapshot changed')
    require(record['sdk']==parent['sdk'] and record['compiler']==parent['compiler'],'compiler/SDK drift')
    require(record['changed_original_paths']==isolated_sources(snap),'declared source delta drift')
    for p,h in record['source_sha256'].items(): add(bound,p,h)
    require(set(record['variants'])==set(VARIANTS),'missing build variants')
    require(record['source_sha256']==inventory(),'source inventory differs from recipe')
    expected_commands=[]
    flags=base.BASE_FLAGS+['-isysroot',record['sdk']]
    require(record['base_flags']==flags,'different build flags')
    for name,(policy,kind) in VARIANTS.items():
        value=record['variants'][name]; folder=Path(path).parent/name
        require(value['policy']==policy and value['instrumentation']==kind and value['defines']==defines(policy,kind), 'variant flags drift')
        objects=[]
        for index,source in enumerate(base.SOURCES+['benchmark/scaling_investigation/diagnostic.cpp']):
            obj=folder/(Path(source).stem+'.o'); objects.append(str(obj))
            expected_commands.append((folder/f'compile-{index}.json',
                ['/usr/bin/arch','-arm64','/usr/bin/clang++']+flags+defines(policy,kind)+['-c',str(ROOT/source),'-o',str(obj)]))
        expected_commands.append((folder/'link.json',
            ['/usr/bin/arch','-arm64','/usr/bin/clang++','-isysroot',record['sdk'],'-L'+record['sdk']+'/usr/lib']
            +objects+['-Wl,-stack_size,0x20000000','-o',str(folder/'diagnostic')]))
        require(value['binary']==str(folder/'diagnostic') and set(value['objects'])=={str(Path(p).relative_to(Path(path).parent)) for p in objects}, 'binary/object path drift')
        require(value['profile']['description']=='Mach-O 64-bit executable arm64' and value['profile']['stack_bytes']==536870912,'binary profile drift')
        add(bound,value['binary'],value['sha256'])
        for p,h in value['objects'].items(): add(bound,Path(path).parent/p,h)
    require(len(record['commands'])==len(expected_commands)==100,'incomplete build commands')
    for recorded,(receipt_path,command) in zip(record['commands'],expected_commands):
        require(check_receipt(receipt_path,command,bound)==recorded,'build command receipt drift')
        add(bound,receipt_path.with_suffix('.stdout'),recorded['stdout_sha256'])
        add(bound,receipt_path.with_suffix('.stderr'),recorded['stderr_sha256'])
    paired_objects(record['variants'])
    base.recheck(bound)
    return record,bound


def schedule(mode):
    if mode=='work': return base.matrix('work'),('depth',),'work',1
    if mode=='smoke': return base.matrix('smoke'),POLICIES,'work',1
    if mode=='timing': return [c for c in base.matrix('work') if c['sampling_seed']==3001],POLICIES,'reference',3
    if mode=='phase': return base.matrix('allocation'),POLICIES,'phase',3
    if mode=='allocation': return base.matrix('allocation'),POLICIES,'allocation',1
    if mode=='inline-control': return base.matrix('calibration'),('reference','depth','depth_noinline'),'reference',3
    if mode=='inline-phase': return base.matrix('calibration'),('reference','depth','depth_noinline'),'phase',3
    raise ValueError('unknown candidate mode')


def declaration_for(mode):
    cases,policies,kind,reps=schedule(mode)
    return dict(mode=mode,cases=cases,policies=list(policies),instrumentation=kind,repetitions=reps,warmups=1,
                input_boundary='unchanged tuple conversion + solver + temporary input destruction',
                global_limit_seconds=7200,child_limit_seconds=300,rss_limit_bytes=12*1024**3)


def equal_work(old,new,policy):
    require(set(old)==set(new)==set(base.work_fields()),'counter schema mismatch')
    for field in old:
        delta=old['lca_vertices'] if field=='initialized_slots' and policy!='reference' else 0
        require(old[field]-new[field]==delta,'unexpected counter delta: '+field)
    if policy!='reference': require(old['lca_vertices']>0,'missing actual depth dispatch witness')


def prerequisites(paths,build_path,record,bound):
    require(len(paths)==3,'timing needs smoke, work and native/sanitizer gate receipts')
    seen=set()
    for path in paths:
        gate,digest=read(path); add(bound,path,digest)
        require(gate['validation']=='pass','failed candidate gate')
        if gate.get('schema')=='kkt_depth_candidate_capture_v1':
            require(gate['mode'] in ('smoke','work'),'only correctness captures are timing prerequisites')
            checked,_,gate_bound=load(path)
            require(checked['build_record_sha256']==sha(build_path),'gate uses different build')
            for p,h in gate_bound.items(): add(bound,p,h)
            seen.add(checked['mode'])
        else:
            require(gate['schema']=='kkt_depth_correctness_gate_v1' and gate['source_sha256']==record['source_sha256']
                    and gate['native_pass'] is True and gate['sanitizers_pass'] is True
                    and gate['owned_groups_empty'] is True,'invalid native/sanitizer gate')
            require(type(gate['bound_sha256']) is dict and gate['bound_sha256'],'missing native gate artifacts')
            for p,h in gate['bound_sha256'].items(): add(bound,p,h)
            seen.add('correctness')
    require(seen=={'smoke','work','correctness'},'missing exact prerequisite gate types')
    base.recheck(bound)


def capture(out, build_path, baseline_path, mode, gates):
    out.mkdir(parents=True,exist_ok=False)
    record,bound=check_build(build_path)
    baseline,old_bound=baseline_work(baseline_path,Path(record['snapshot']))
    for p,h in old_bound.items(): add(bound,p,h)
    # Timing is never allowed before both counter gates and separately archived correctness checks.
    if mode in ('timing','inline-control'):
        prerequisites(gates,build_path,record,bound)
    cases,policies,kind,reps=schedule(mode); historical=base.historical_inputs()
    declaration=declaration_for(mode)
    write(out/'declaration.json',declaration); add(bound,out/'declaration.json')
    captures=[]; started=time.monotonic_ns()
    status=dict(schema='kkt_depth_candidate_capture_v1',validation='running',mode=mode,build_record=str(build_path.resolve()),
                build_record_sha256=sha(build_path),baseline_work=str(baseline_path.resolve()),baseline_work_sha256=sha(baseline_path),
                gates=[str(p.resolve()) for p in gates],declaration=declaration,captures=captures)
    try:
        for index,case in enumerate(cases):
            for policy in policy_order(policies,index):
                base.recheck(bound); remaining=7200-(time.monotonic_ns()-started)/1e9
                require(remaining>0,'candidate campaign deadline')
                name=policy+'-'+kind; label=f'{index:03d}-{policy}'
                command=['/usr/bin/arch','-arm64',record['variants'][name]['binary'],case['family'],str(case['n']),str(case['graph_seed']),str(case['sampling_seed']),str(reps)]
                base.run_owned(command,out,label,timeout=min(300,remaining))
                require(time.monotonic_ns()-started<=7200*1e9,'candidate campaign deadline')
                receipt=check_receipt(out/(label+'.json'),command,bound)
                values=raw_rows(out/(label+'.stdout'),case,kind,reps,historical[identity(case)],bound)
                add(bound,out/(label+'.stderr'),receipt['stderr_sha256'])
                require(sha(out/(label+'.stdout'))==receipt['stdout_sha256'],'native raw hash mismatch')
                if kind=='work':
                    for row in values: equal_work(baseline[identity(case)][0]['work'],row['work'],policy)
                captures.append(dict(case=case,policy=policy,variant=name,label=label,rows=len(values),
                                     stdout=str(out/(label+'.stdout')),receipt=str(out/(label+'.json'))))
                write(out/'progress.json',dict(validation='in_progress',completed=len(captures),total=len(cases)*len(policies)))
                print(f'{mode}: {len(captures)}/{len(cases)*len(policies)}',flush=True)
        require(len(captures)==len(cases)*len(policies),'incomplete candidate matrix')
        base.recheck(bound); require(time.monotonic_ns()-started<=7200*1e9,'candidate campaign deadline')
        status['validation']='pass'
    except BaseException as error:
        status.update(validation='failed',error=repr(error)); raise
    finally:
        status.update(duration_s=(time.monotonic_ns()-started)/1e9,bound_sha256=bound,
                      native_process_may_still_be_running=base._launch_blocked)
        write(out/'capture.json',status)


def load(path):
    path=Path(path).resolve()
    info,digest=read(path); require(info['schema']=='kkt_depth_candidate_capture_v1' and info['validation']=='pass'
                                  and info['native_process_may_still_be_running'] is False,'incomplete candidate capture')
    build,bound=check_build(Path(info['build_record']))
    require(sha(info['build_record'])==info['build_record_sha256'],'build drift')
    baseline,old_bound=baseline_work(Path(info['baseline_work']),Path(build['snapshot']))
    require(sha(info['baseline_work'])==info['baseline_work_sha256'],'baseline work drift')
    required=set(bound)|set(old_bound)|{str(path.parent/'declaration.json')}
    for values in (old_bound,info['bound_sha256']):
        for p,h in values.items(): add(bound,p,h)
    if info['mode'] in ('timing','inline-control'):
        prerequisites(info['gates'],Path(info['build_record']),build,bound)
        required.update(bound)
    cases,policies,kind,reps=schedule(info['mode']); expected=base.historical_inputs(); rows=[]
    declaration,declaration_hash=read(path.parent/'declaration.json')
    require(exact(info['declaration'],declaration_for(info['mode'])) and exact(declaration,info['declaration']),
            'candidate declaration drift')
    add(bound,path.parent/'declaration.json',declaration_hash)
    matrix=[(i,c,p) for i,c in enumerate(cases) for p in policy_order(policies,i)]
    require(len(info['captures'])==len(matrix),'incomplete captured matrix')
    for index,case,policy in matrix:
        required.update(str(path.parent/(f'{index:03d}-{policy}'+suffix)) for suffix in ('.stdout','.stderr','.json'))
    require(required<=set(info['bound_sha256']),'capture omitted required bound artifacts')
    for (index,case,policy),item in zip(matrix,info['captures']):
        name=policy+'-'+kind; label=f'{index:03d}-{policy}'
        require(item['case']==case and item['policy']==policy and item['variant']==name and item['label']==label
                and item['rows']==reps+1,'capture identity/order drift')
        raw=Path(path).parent/(label+'.stdout'); receipt_path=Path(path).parent/(label+'.json')
        require(Path(item['stdout'])==raw and Path(item['receipt'])==receipt_path,'child path substitution')
        command=['/usr/bin/arch','-arm64',build['variants'][name]['binary'],case['family'],str(case['n']),str(case['graph_seed']),str(case['sampling_seed']),str(reps)]
        receipt=check_receipt(receipt_path,command,bound)
        values=raw_rows(raw,case,kind,reps,expected[identity(case)],bound)
        require(sha(raw)==receipt['stdout_sha256'],'raw/receipt mismatch')
        add(bound,raw.with_suffix('.stderr'),receipt['stderr_sha256'])
        if kind=='work':
            for row in values: equal_work(baseline[identity(case)][0]['work'],row['work'],policy)
        rows.extend(dict(row,policy=policy,variant=name,case_index=index) for row in values)
    require(type(info['duration_s']) in (int,float) and 0<=info['duration_s']<=7200,'campaign duration invalid')
    add(bound,path,digest); base.recheck(bound)
    return info,rows,bound


def main():
    parser=argparse.ArgumentParser(); sub=parser.add_subparsers(dest='action',required=True)
    s=sub.add_parser('snapshot');s.add_argument('output',type=Path);s.add_argument('--baseline-build',required=True,type=Path)
    b=sub.add_parser('build');b.add_argument('output',type=Path);b.add_argument('--snapshot',required=True,type=Path);b.add_argument('--released',action='store_true')
    c=sub.add_parser('capture');c.add_argument('output',type=Path);c.add_argument('--build',required=True,type=Path);c.add_argument('--baseline-work',required=True,type=Path)
    c.add_argument('--mode',choices=['smoke','work','timing','phase','allocation','inline-control','inline-phase'],required=True);c.add_argument('--gate',action='append',type=Path,default=[]);c.add_argument('--released',action='store_true')
    r=sub.add_parser('check');r.add_argument('capture',type=Path)
    args=parser.parse_args(); prior=signal.getsignal(signal.SIGTERM)
    def stopped(signum,frame): raise KeyboardInterrupt('candidate controller received SIGTERM')
    signal.signal(signal.SIGTERM,stopped)
    try:
        if args.action=='snapshot': snapshot(args.output.resolve(),args.baseline_build.resolve())
        elif args.action=='build':
            require(args.released,'build requires explicit release');build(args.output.resolve(),args.snapshot.resolve())
        elif args.action=='capture':
            require(args.released,'capture requires explicit release');capture(args.output.resolve(),args.build.resolve(),args.baseline_work.resolve(),args.mode,args.gate)
        else:
            info,rows,_=load(args.capture.resolve()); print(f'PASS {info["mode"]}: {len(info["captures"])} children, {len(rows)} rows')
    finally: signal.signal(signal.SIGTERM,prior)

if __name__=='__main__': main()
