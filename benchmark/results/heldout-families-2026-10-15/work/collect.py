#!/usr/bin/env python3
"""Untimed work for all 72 held-out inputs using the existing compressed artifact.

No rebuild and no algorithm timing. Every input joins its completed timing
fingerprint; all three solvers, 65 counters and both round replays are retained.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve(); WORK = HERE.parent; ROOT = WORK.parents[3]
sys.path.insert(0,str(ROOT/'benchmark'))
import run_heldout_families as timing

native,analysis,monitor = timing.native,timing.analysis,timing.monitor
require,write_json,RULE = timing.require,timing.write_json,timing.RULE
PREVIOUS_PATH = ROOT/'benchmark/results/compressed-query-2026-10-15/work/collect.py'
PREVIOUS_SHA256 = '6bba53051d5ce6565b6eaff43a9118f20d4eeb5491ac25686e2707c50233fda1'
PARENT_WORK_FREEZE = PREVIOUS_PATH.parent/'freeze.json'
PARENT_WORK_FREEZE_SHA256 = '6fe07ed1d07ab5fc0a374a4e2090022589e3f91ade3f15940c48a58b34549a2b'
HELDOUT_FREEZE_SHA256 = '6b120affb241e447ce5875645e7b746dfd1164a03aeabefffd4d42f5a01ba28f'
require(native.sha(PREVIOUS_PATH) == PREVIOUS_SHA256,'inherited work checker changed')
module_spec = importlib.util.spec_from_file_location('heldout_inherited_compressed_work',PREVIOUS_PATH)
previous = importlib.util.module_from_spec(module_spec); module_spec.loader.exec_module(previous)
ALGORITHMS,FIELDS,BOUNDARY = previous.ALGORITHMS,previous.FIELDS,previous.BOUNDARY
DEADLINE_SECONDS = 1800
CHILDREN,SOLVER_OUTPUTS,REPLAY_CHAINS = 72,216,144


def merge_paths(*groups):
    result = {}
    for group in groups:
        for name,digest in group.items():
            require(name not in result or result[name] == digest,'conflicting provenance digest: '+name)
            result[name] = digest
    return result


def provenance(timing_capture):
    info,cases,rows,_,_,paths = timing.load(timing_capture)
    frozen = info['frozen_protocol']
    analysis.hash_check(Path(info['freeze']),HELDOUT_FREEZE_SHA256)
    analysis.hash_check(PREVIOUS_PATH,PREVIOUS_SHA256)
    analysis.hash_check(PARENT_WORK_FREEZE,PARENT_WORK_FREEZE_SHA256)
    parent_work = previous.check_freeze(PARENT_WORK_FREEZE)
    current_sources = native.source_inventory(ROOT)
    require(current_sources == frozen['source_sha256'],'diagnostic/timing native sources differ')
    declarations = re.findall(r'\{\s*"([a-z_0-9]+)"\s*,\s*&kkt_work::WorkStats::([a-z_0-9]+)\s*,\s*(?:true|false)\s*\}',
                              (ROOT/'benchmark/work_metrics.hpp').read_text())
    require(len(declarations) == len(set(FIELDS)) == len(FIELDS) == 65 and
            [name for name,member in declarations] == FIELDS and all(name == member for name,member in declarations),
            'counter member/name schema differs')
    artifact = parent_work['variants']['compressed']
    build = analysis.read_json(Path(artifact['instrumented_build_record']))
    inherited = frozen['build']['record']
    require(build['variant'] == 'compressed' and build['source_sha256'] == current_sources,
            'wrong instrumented variant/source inventory')
    for name in ('compiler','compiler_command','sdk','build_recipe_sha256','base_commit','parent_edge_freeze','parent_edge_freeze_sha256'):
        analysis.equal(build,name,inherited[name],'same timing/instrumented production proof')
    paths = merge_paths(paths,parent_work['bound_sha256'],timing.helpers(),
        {str(HERE):native.sha(HERE),str(WORK/'PROTOCOL.md'):native.sha(WORK/'PROTOCOL.md'),
         str(WORK/'test_collect.py'):native.sha(WORK/'test_collect.py'),
         str(PREVIOUS_PATH):PREVIOUS_SHA256,str(PARENT_WORK_FREEZE):PARENT_WORK_FREEZE_SHA256},
        {str(ROOT/name):digest for name,digest in current_sources.items()})
    fingerprints = {}
    for row in rows:
        key = tuple(row[name] for name in ('case_id','graph_seed','kkt_seed'))
        value = {name:row[name] for name in ('input_fingerprint','topology_fingerprint')}
        require(key not in fingerprints or fingerprints[key] == value,'timing input fingerprints vary')
        fingerprints[key] = value
    schedule = [{'variant':'compressed',**identity,**cases[identity['case_id']],
                 **fingerprints[tuple(identity[name] for name in ('case_id','graph_seed','kkt_seed'))]}
                for identity in timing.schedule(cases)]
    require(len(schedule) == len(fingerprints) == CHILDREN and len(rows) == 3024,
            'incomplete held-out timing/work input matrix')
    for path,digest in paths.items(): analysis.hash_check(Path(path),digest)
    return artifact,schedule,paths


def prepare(args):
    source = args.timing_capture.resolve(strict=True); artifact,schedule,paths = provenance(source)
    data = dict(schema='heldout_work_freeze_v1',timing_capture=str(source),artifact=artifact,schedule=schedule,
                parent_work_freeze=str(PARENT_WORK_FREEZE),parent_work_freeze_sha256=PARENT_WORK_FREEZE_SHA256,
                heldout_freeze_sha256=HELDOUT_FREEZE_SHA256,bound_sha256=paths,counter_fields=FIELDS,
                algorithms=list(ALGORITHMS),counter_boundary=BOUNDARY,resource_rule=RULE,
                child_deadline_seconds=DEADLINE_SECONDS,expected_children=CHILDREN,
                expected_solver_outputs=SOLVER_OUTPUTS,expected_replay_chains=REPLAY_CHAINS,created_utc=native.now())
    write_json(args.freeze,data,exclusive=True)
    print('Prepared all 72 held-out inputs / 216 solver records; no native execution')


def check_freeze(path):
    data = analysis.read_json(path); artifact,schedule,paths = provenance(Path(data['timing_capture']))
    for key,value in dict(schema='heldout_work_freeze_v1',artifact=artifact,schedule=schedule,
            parent_work_freeze=str(PARENT_WORK_FREEZE),parent_work_freeze_sha256=PARENT_WORK_FREEZE_SHA256,
            heldout_freeze_sha256=HELDOUT_FREEZE_SHA256,bound_sha256=paths,counter_fields=FIELDS,
            algorithms=list(ALGORITHMS),counter_boundary=BOUNDARY,resource_rule=RULE,
            child_deadline_seconds=DEADLINE_SECONDS,expected_children=CHILDREN,
            expected_solver_outputs=SOLVER_OUTPUTS,expected_replay_chains=REPLAY_CHAINS).items():
        analysis.equal(data,key,value,'held-out diagnostic freeze')
    return data


def query_diagnostics(work):
    q,m,t,n = (work[field] for field in ('verifier_queries','verifier_tree_edges','verifier_tree_calls','fbt_output_vertices'))
    u = work['path_query_visits']-2*q
    require(0 <= u <= q,'compressed cumulative U outside [0,Q]')
    return dict(Q=q,U=u,M=m,T=t,Nsum=n,U_over_Q=u/q if q else None,
                query_fraction_status='defined' if q else 'both_zero',collapsed_requests=q-u)


def check_output(path,spec):
    require(spec['variant'] == 'compressed','only existing compressed artifact is allowed')
    value = previous.check_output(path,spec)
    query_diagnostics(value['algorithms']['kkt']['work'])
    # These fixtures are connected. A nonterminal contracted graph remains
    # connected; the terminal singleton is removed by isolated-vertex cleanup.
    for name in ALGORITHMS[1:]:
        for row in value['rounds'][name]:
            require(all(count < 2**64 for count in row.values()),'replay integer overflow')
            require((row['output_edges'] == 0) == (row['output_vertices'] == 0),'invalid terminal replay graph')
            remaining = row['output_vertices'] if row['output_edges'] else 1
            require(row['selected'] == row['vertices']-remaining,'selected edges differ from connected contraction')
    retained = value['rounds']['multigraph_boruvka']
    if len(retained) < 2:
        require(value['algorithms']['kkt']['work']['root_after_two_vertices'] == 0 and
                value['algorithms']['kkt']['work']['root_after_two_edges'] == 0,'early root exit dimensions differ')
    return value


def complete(values):
    require(len(values) == CHILDREN and len({tuple(spec[key] for key in ('case_id','graph_seed','kkt_seed'))
                for spec,value in values}) == CHILDREN,'incomplete/duplicate diagnostic inputs')
    timing.check_fingerprints([value for spec,value in values],complete=True)
    require(any(query_diagnostics(value['algorithms']['kkt']['work'])['Q'] > 0 for spec,value in values),
            'no positive compressed-query input in full matrix')


command = previous.command
resources = previous.resources


def child_paths(output,index,spec):
    stem = f"{index:04d}_{spec['case_id']}_g{spec['graph_seed']}_s{spec['kkt_seed']}"
    folder = output.with_name(output.stem+'_cases')
    return tuple(folder/(stem+suffix) for suffix in ('.json','.log','.rss.jsonl'))


def cleanup_owned_group(process,sampler,info):
    prior_unknown = info['native_process_may_still_be_running']; info['native_process_may_still_be_running'] = True
    prior_handler = signal.getsignal(signal.SIGTERM)
    receipt = dict(process_group=process.pid if process else None,started_monotonic_ns=time.monotonic_ns(),
                   native_exit_known=False,group_exit_known=False,native_process_may_still_be_running=True)
    try:
        signal.signal(signal.SIGTERM,signal.SIG_IGN)
        try: receipt = monitor.bounded_terminate(process,sampler)
        except BaseException as error: receipt.update(error=repr(error),finished_monotonic_ns=time.monotonic_ns())
        finally:
            info['cleanup'].append(receipt)
            proved_empty = receipt.get('native_exit_known') is True and receipt.get('group_exit_known') is True and receipt.get('native_process_may_still_be_running') is False
            info['native_process_may_still_be_running'] = prior_unknown or not proved_empty
    finally: signal.signal(signal.SIGTERM,prior_handler)
    return receipt


def capture(args,sampler=None,popen=None):
    require(args.released,'work capture requires explicit root --released scheduling')
    freeze_path = args.freeze.resolve(strict=True); frozen = check_freeze(freeze_path)
    paths = merge_paths(frozen['bound_sha256'],{str(freeze_path):native.sha(freeze_path)})
    output = args.output.resolve(); folder = output.with_name(output.stem+'_cases')
    require(output.suffix == '.json' and not output.exists() and not folder.exists(),'refusing to overwrite evidence')
    output.parent.mkdir(parents=True,exist_ok=True); folder.mkdir()
    sampler = sampler if sampler is not None else monitor.BoundedSampler(monitor.LibprocProvider())
    popen = popen if popen is not None else subprocess.Popen
    info = dict(schema='heldout_work_capture_v1',validation='running',freeze=str(freeze_path),freeze_sha256=paths[str(freeze_path)],
                bound_sha256=paths,captures=[],cleanup=[],native_process_may_still_be_running=False,
                started_utc=native.now(),started_monotonic_ns=time.monotonic_ns(),counter_boundary=BOUNDARY,
                purpose='Untimed logical work; durations and sampled RSS are not algorithm performance data.')
    write_json(output,info); old = signal.getsignal(signal.SIGTERM)
    def interrupted(signum,frame): raise KeyboardInterrupt(f'signal {signum}')
    signal.signal(signal.SIGTERM,interrupted); values = []
    try:
        for index,spec in enumerate(frozen['schedule'],1):
            for path,digest in paths.items(): analysis.hash_check(Path(path),digest)
            require(not sampler.poisoned,'poisoned sampler forbids another child')
            raw,log,rss = child_paths(output,index,spec); argv = command(frozen['artifact']['binary'],spec)
            item = dict(spec=spec,command=argv,launch_command=argv,raw=str(raw),log=str(log),rss_log=str(rss),
                        started_utc=native.now(),started_monotonic_ns=time.monotonic_ns())
            info['captures'].append(item); write_json(output,info)
            process = None; failure = None; observations = []; unavailable = 0
            try:
                with raw.open('x') as stdout,log.open('x') as stderr,rss.open('x') as resource:
                    process = popen(argv,cwd=ROOT,stdout=stdout,stderr=stderr,start_new_session=True); item['process_group'] = process.pid
                    def observe():
                        observation = sampler.sample(process.pid); observations.append(observation)
                        resource.write(json.dumps(observation,allow_nan=False)+'\n'); resource.flush(); return observation
                    while True:
                        observation = observe(); require(not sampler.poisoned,'sampler timed out')
                        if observation['validation'] == 'pass':
                            unavailable = 0; require(observation['rss_kib'] <= RULE['rss_limit_kib'],'sampled RSS ceiling exceeded')
                        else:
                            unavailable += 1; require(unavailable < 3,'three consecutive unavailable resource samples')
                        remaining = DEADLINE_SECONDS*10**9-(time.monotonic_ns()-item['started_monotonic_ns'])
                        require(remaining > 0,'diagnostic deadline exceeded')
                        try:
                            process.wait(timeout=min(RULE['poll_seconds'],remaining/1e9))
                            item['wrapper_exit_monotonic_ns'] = time.monotonic_ns()
                            require(item['wrapper_exit_monotonic_ns']-item['started_monotonic_ns'] <= DEADLINE_SECONDS*10**9,
                                    'diagnostic native exit exceeded deadline'); break
                        except subprocess.TimeoutExpired: pass
                    require(process.returncode == 0,'diagnostic child failed')
                    item['group_exit_verification'] = observe()
                    require(not sampler.poisoned and observations[-1]['validation'] == 'pass' and not observations[-1]['members'],
                            'owned group exit unknown')
            except BaseException as error:
                failure = error; cleanup_owned_group(process,sampler,info)
            item.update(exit_status=process.returncode if process else None,interruption=repr(failure) if failure else None,
                finished_utc=native.now(),finished_monotonic_ns=time.monotonic_ns(),
                raw_sha256=native.sha(raw) if raw.exists() else None,log_sha256=native.sha(log) if log.exists() else None,
                rss_sha256=native.sha(rss) if rss.exists() else None,rss_observations=len(observations),
                rss_unavailable=sum(row['validation'] != 'pass' for row in observations),
                rss_nonempty_observations=sum(row['validation'] == 'pass' and bool(row['members']) for row in observations),
                sampled_peak_rss_kib=max((row['rss_kib'] for row in observations if row['validation'] == 'pass'),default=None),
                recovery_monitor=monitor.recovery_monitor(sampler.events.get(process.pid,[])[:len(observations)] if process else []))
            item['monotonic_elapsed_seconds'] = (item['finished_monotonic_ns']-item['started_monotonic_ns'])/1e9
            write_json(output,info)
            if failure: raise failure
            for path,digest in paths.items(): analysis.hash_check(Path(path),digest)
            value = check_output(raw,spec); item['certificate'] = native.check_certificate(log,[value]); resources(item)
            timing.check_fingerprints([prior_value for _,prior_value in values]+[value])
            values.append((spec,value)); item['validation'] = 'pass'; write_json(output,info)
            print(f'Untimed held-out work {index}/72 certified',flush=True)
        complete(values); info.update(validation='pass',checked_children=CHILDREN,checked_solver_outputs=SOLVER_OUTPUTS,
                                      checked_replay_chains=REPLAY_CHAINS)
    except BaseException as error: info.update(validation='failed',error=repr(error)); raise
    finally:
        signal.signal(signal.SIGTERM,old)
        info.update(finished_utc=native.now(),finished_monotonic_ns=time.monotonic_ns()); write_json(output,info)
    load(output)


def load(path):
    info = analysis.read_json(path)
    for key,value in dict(schema='heldout_work_capture_v1',validation='pass',cleanup=[],native_process_may_still_be_running=False,
            checked_children=CHILDREN,checked_solver_outputs=SOLVER_OUTPUTS,checked_replay_chains=REPLAY_CHAINS,counter_boundary=BOUNDARY).items():
        analysis.equal(info,key,value,'held-out work capture')
    require('error' not in info,'failed capture')
    freeze_path = Path(info['freeze']); analysis.hash_check(freeze_path,info['freeze_sha256']); frozen = check_freeze(freeze_path)
    paths = merge_paths(frozen['bound_sha256'],{str(freeze_path):native.sha(freeze_path)})
    analysis.equal(info,'bound_sha256',paths,'frozen work provenance')
    require(len(info['captures']) == len(frozen['schedule']) == CHILDREN,'incomplete diagnostic matrix')
    begin,end = analysis.monotonic_interval(info); analysis.timestamp(info['started_utc']); analysis.timestamp(info['finished_utc'])
    previous_end = begin; values = []
    for index,(spec,item) in enumerate(zip(frozen['schedule'],info['captures']),1):
        argv = command(frozen['artifact']['binary'],spec)
        for key,value in dict(spec=spec,validation='pass',exit_status=0,interruption=None,command=argv,launch_command=argv).items():
            analysis.equal(item,key,value,'diagnostic identity')
        start,finish = analysis.monotonic_interval(item); analysis.timestamp(item['started_utc']); analysis.timestamp(item['finished_utc'])
        require(previous_end <= start < finish <= end,'child overlap/interval invalid'); previous_end = finish
        analysis.equal(item,'monotonic_elapsed_seconds',(finish-start)/1e9,'diagnostic duration')
        for field,expected,digest in zip(('raw','log','rss_log'),child_paths(Path(path).resolve(),index,spec),('raw_sha256','log_sha256','rss_sha256')):
            analysis.equal(item,field,str(expected),'diagnostic raw path'); analysis.hash_check(expected,item[digest])
        value = check_output(Path(item['raw']),spec)
        analysis.equal(item,'certificate',native.check_certificate(Path(item['log']),[value]),'independent certificate')
        resources(item); values.append((spec,value))
    complete(values)
    for source,digest in paths.items(): analysis.hash_check(Path(source),digest)
    return info,values


def summarize(args):
    capture_path = args.capture.resolve(strict=True); initial_hash = native.sha(capture_path); info,values = load(capture_path)
    output = args.output_dir.resolve(); require(not output.exists(),'refusing to overwrite work analysis')
    rows,rounds,chains,queries = [],[],[],[]
    for spec,value in values:
        for name in ALGORITHMS:
            record = value['algorithms'][name]
            rows.append({**spec,'algorithm':name,'hash_insert_items_status':record['hash_insert_items_status'],**record['work']})
            if name == 'kkt': continue
            replay = value['rounds'][name]
            rounds.extend({**spec,'algorithm':name,**row} for row in replay)
            chains.append({**spec,'algorithm':name,'round_count':len(replay),'selected_edges':sum(row['selected'] for row in replay),
                           **{field:record['work'][field] for field in ('contraction_calls','contraction_vertices','contraction_edges',
                               'contraction_edge_visits','contraction_output_vertices','contraction_output_edges')}})
        diagnostic = query_diagnostics(value['algorithms']['kkt']['work'])
        queries.append({**spec,**diagnostic,**{name+'_per_original_edge':diagnostic[name]/spec['m']
                        for name in ('Q','U','M','T','Nsum','collapsed_requests')}})
    require((len(rows),len(chains),len(queries)) == (SOLVER_OUTPUTS,REPLAY_CHAINS,CHILDREN),'incomplete work summaries')
    output.mkdir(parents=True)
    for name,data in (('work',rows),('rounds',rounds),('round_chains',chains),('query_work',queries)):
        analysis.write_csv(output/(name+'.csv'),data)
    for source,digest in info['bound_sha256'].items(): analysis.hash_check(Path(source),digest)
    for item in info['captures']:
        for field,digest in (('raw','raw_sha256'),('log','log_sha256'),('rss_log','rss_sha256')):
            analysis.hash_check(Path(item[field]),item[digest])
    analysis.hash_check(capture_path,initial_hash)
    write_json(output/'provenance.json',dict(schema='heldout_work_analysis_v1',validation='pass',capture=str(capture_path),
        capture_sha256=initial_hash,bound_sha256=info['bound_sha256'],counter_boundary=BOUNDARY,
        solver_rows=SOLVER_OUTPUTS,counter_fields=65,counter_cells=14040,unmeasured_hash_counter_cells=144,
        replay_chains=REPLAY_CHAINS,replay_round_rows=len(rounds),cumulative_query_rows=CHILDREN,
        reference_compression_pairs=0,performance_claim=False,memory_peak_claim=False,
        unique_request_scope='U is inferred from the fixed compressed representation; cumulative sum of per-call distinct requests, not global distinctness or a per-call distribution.'),exclusive=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); actions = parser.add_subparsers(dest='action',required=True)
    prepare_parser = actions.add_parser('prepare'); prepare_parser.add_argument('--timing-capture',type=Path,required=True); prepare_parser.add_argument('--freeze',type=Path,required=True)
    capture_parser = actions.add_parser('capture'); capture_parser.add_argument('--freeze',type=Path,required=True); capture_parser.add_argument('--output',type=Path,required=True); capture_parser.add_argument('--released',action='store_true')
    verify_parser = actions.add_parser('verify'); verify_parser.add_argument('--capture',type=Path,required=True)
    analyze_parser = actions.add_parser('analyze'); analyze_parser.add_argument('--capture',type=Path,required=True); analyze_parser.add_argument('--output-dir',type=Path,required=True)
    args = parser.parse_args()
    if args.action == 'prepare': prepare(args)
    elif args.action == 'capture': capture(args)
    elif args.action == 'verify': load(args.capture.resolve(strict=True)); print('Verified all 72 untimed held-out inputs')
    else: summarize(args)
