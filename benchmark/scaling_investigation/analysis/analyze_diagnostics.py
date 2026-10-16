#!/usr/bin/env python3
"""Strict matched-input diagnostic tables; no solver, compiler or subprocess."""
import argparse
from collections import defaultdict
import csv
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import statistics
import sys

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
OLD=Path('/Users/random_person/Desktop/kkt-eighth-sampling')
GOOGLE=ROOT/'benchmark/results/current-complexity-2026-10-15/capture-attempt01/capture.json'
GOOGLE_SHA='2d2d95769fe6c7cd6e7608450ba891fcbf5dacd97938fe700ff8058577db6206'
BASELINE_BUILD=ROOT/'.build/scaling-investigation/build04/build.json'
BASELINE_BUILD_SHA='5f7d4bb8d580ed4360f4dd15999256cdbccc1bd78ca7de36e6b6fcdeb4732a96'
BASELINE_SOURCE_MAP_SHA='4f620da80b86e29c14648bbd83886f5e7845c3fb8c15660f9c3aceb9e8347098'
FAMILIES=('leaf_hierarchy4','leaf_shuffled4','gnm_random')
GRAPHS=(19000013,19000043)
SEEDS=(3001,3011)
SIZES=(1024,4096,16384,65536,262144,1048576)
CASE=('family','n','graph_seed','sampling_seed')
IDENTITY=(*CASE,'m','input_fingerprint','topology_fingerprint')
PHASES=tuple('api input recursion contraction minimum_scan sampling isolation forest_recovery partition tree_setup fbt lca_build queries query_gather mark_scatter path_solve median_table path_walk filtering output'.split())
PHASE_FIELDS=tuple('wall_ns calls allocations requested_bytes usable_bytes deallocations freed_usable_bytes'.split())
VARIANTS={'reference':[],'phase':['-DKKT_ENABLE_PHASE_STATS'],
          'allocation':['-DKKT_ENABLE_PHASE_STATS','-DKKT_SCALING_ALLOCATIONS'],
          'work':['-DKKT_ENABLE_WORK_STATS']}
CPP=('boruvka/boruvka.cpp','kruskal/kruskal.cpp','prim/prim.cpp','lca/lca.cpp',
     'union_find/union_find.cpp','graph_utils/graph_utils.cpp','verifier/verifier_v2.cpp','kkt/kkt.cpp',
     'benchmark/scaling_investigation/diagnostic.cpp')
IMPORTANT=('contraction_edge_visits','sampling_edge_visits','verifier_edge_visits','path_query_visits',
           'lca_queries','initialized_slots','edge_materializations','median_entries')
FIT_COUNTS=('kkt_edges','contraction_edge_visits','verifier_queries','path_binary_search_steps',
            'lca_sparse_cells','initialized_slots','edge_materializations')
HISTORICAL_COUNTS=tuple(dict.fromkeys(('work_proxy',*IMPORTANT,*FIT_COUNTS)))


def require(ok,why):
    if not ok:raise ValueError(why)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parse(text):
    def pairs(items):
        out={}
        for k,v in items:require(k not in out,'duplicate JSON field');out[k]=v
        return out
    value=json.loads(text,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
    def finite(v):
        if type(v) is float:require(math.isfinite(v),'nonfinite JSON')
        elif type(v) is list:
            for x in v:finite(x)
        elif type(v) is dict:
            for x in v.values():finite(x)
    finite(value);return value


def read(path,bound,expected=None):
    path=Path(path).resolve(strict=True);before=sha(path)
    require(expected is None or before==expected,'hash mismatch: '+str(path))
    require(str(path) not in bound or bound[str(path)]==before,'conflicting input hash')
    text=path.read_text();require(sha(path)==before,'input changed during read')
    bound[str(path)]=before;return text


def bind(path,bound,expected):
    path=Path(path).resolve(strict=True)
    require(sha(path)==expected,'binary/artifact hash mismatch: '+str(path))
    require(str(path) not in bound or bound[str(path)]==expected,'conflicting artifact hash')
    bound[str(path)]=expected


def recheck(bound):
    for path,digest in bound.items():require(sha(path)==digest,'final input drift: '+path)


def source_snapshot(path,bound):
    """Explicit baseline source copies only; never relocate native/raw artifacts."""
    if path is None:return None
    manifest=Path(path).resolve(strict=True);record=parse(read(manifest,bound))
    require(record['schema']=='kkt_scaling_source_snapshot_v1' and record['validation']=='pass','snapshot status/schema')
    require(record['baseline_build_record']==str(BASELINE_BUILD) and
            record['baseline_build_record_sha256']==BASELINE_BUILD_SHA,'snapshot baseline identity')
    original=parse(read(BASELINE_BUILD,bound,BASELINE_BUILD_SHA))
    sources=record['source_sha256']
    digest=hashlib.sha256(json.dumps(sources,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    require(digest==BASELINE_SOURCE_MAP_SHA and sources==original['source_sha256'],'snapshot full baseline source inventory')
    copies=record['copies'];require(set(copies)==set(sources),'snapshot source-copy inventory')
    require(len(set(copies.values()))==len(copies),'snapshot copy alias collision')
    for source,digest in sources.items():
        copy=Path(copies[source]);require(copy.is_absolute() and str(copy.resolve(strict=True))==str(copy),'snapshot copy path')
        require(copy!=Path(source),'snapshot must preserve a separate source copy')
        bind(copy,bound,digest)
    return dict(manifest=str(manifest),manifest_sha256=bound[str(manifest)],source_sha256=sources,copies=copies)


def bind_source_or_artifact(path,bound,digest,snapshot):
    original=str(Path(path))
    if snapshot is not None and original in snapshot['source_sha256']:
        require(digest==snapshot['source_sha256'][original],'snapshot source digest mismatch')
        bind(snapshot['copies'][original],bound,digest)
    else:bind(path,bound,digest)


def identity(row):return tuple(row[k] for k in IDENTITY)
def casekey(row):return tuple(row[k] for k in CASE)
def uint(x):return type(x) is int and 0<=x<2**64


def matrix(mode):
    sizes=(1024,) if mode=='smoke' else (16384,262144,1048576) if mode=='allocation' else (1024,1048576) if mode=='calibration' else SIZES
    graphs=GRAPHS[:1] if mode in ('smoke','calibration') else GRAPHS
    seeds=SEEDS[:1] if mode in ('smoke','allocation','calibration') else SEEDS
    return [dict(family=f,n=n,graph_seed=g,sampling_seed=s)
            for gi,g in enumerate(graphs) for n in (sizes if gi==0 else sizes[::-1]) for f in FAMILIES for s in seeds]


def receipt(record):
    require(record['validation']=='pass' and type(record['exit_code']) is int and record['exit_code']==0,'command status')
    require(record['group_empty'] is True and record['native_process_may_still_be_running'] is False,'unknown owned exit')
    c=record['cleanup']
    require(c.get('native_exit_known') is True and c.get('group_exit_known') is True and
            c.get('native_process_may_still_be_running') is False,'cleanup proof')
    require(uint(record['pgid']) and record['pgid']>0,'invalid process group')
    start,exit_,finish=(record[k] for k in ('started_monotonic_ns','exit_monotonic_ns','finished_monotonic_ns'))
    require(all(uint(x) for x in (start,exit_,finish)) and start<=exit_<=finish,'monotonic interval')
    require(0<record['deadline_seconds']<=300 and exit_-start<=record['deadline_seconds']*1e9,'deadline proof')
    require(record['rss_samples']==len(record['observations']),'RSS count')
    peak=0;unavailable=0
    for item in record['observations']:
        if item['validation']=='pass':
            require(uint(item['rss_kib']),'invalid RSS');peak=max(peak,item['rss_kib']*1024);unavailable=0
        else:unavailable+=1
        require(unavailable<3,'three unavailable resource samples')
    require(peak==record['peak_sampled_group_rss_bytes']<=record['rss_limit_bytes'],'RSS ceiling/peak')


def load_build(folder,bound,snapshot=None):
    folder=Path(folder).resolve(strict=True);path=folder/'build.json'
    info=parse(read(path,bound));require(info['validation']=='pass','incomplete build')
    require(info['variant_defines']==VARIANTS,'variant flag schema')
    require('Apple clang' in info['compiler'] and 'Target: arm64-' in info['compiler'],'compiler profile')
    expected_flags=['-std=c++17','-O3','-march=native','-Wall','-Wextra','-I'+str(ROOT),
                    '-DKKT_EXPERIMENT_RETAIN_PARALLEL','-DKKT_EXPERIMENT_EDGE_VIEW',
                    '-DKKT_EXPERIMENT_COMPRESSED_QUERIES','-DKKT_EXPERIMENT_EIGHTH_SAMPLING',
                    '-isysroot',info['sdk']]
    require(info['flags']==expected_flags,'common build flags')
    controller_path=str(ROOT/'benchmark/scaling_investigation/run.py')
    require(controller_path in info['source_sha256'],'missing controller source binding')
    read(controller_path,bound,info['source_sha256'][controller_path])
    for source,digest in info['source_sha256'].items():
        # Validate executable helper bytes before importing the row validator.
        if source.endswith('.py') or source==str(ROOT/'benchmark/work_metrics.hpp'):bind(source,bound,digest)
    controller=controller_module(bound)
    if snapshot is None:
        require(set(info['source_sha256'])==set(controller.source_inventory()),'incomplete or extra producer source inventory')
    else:
        require(info['source_sha256']==snapshot['source_sha256'],'build differs from preserved baseline source map')
    for source,digest in info['source_sha256'].items():
        bind_source_or_artifact(source,bound,digest,snapshot)
        # The validator still executes unchanged live Python and reads this schema.
        if source.endswith('.py') or source==str(ROOT/'benchmark/work_metrics.hpp'):bind(source,bound,digest)
    commands=[]
    for variant,details in info['variants'].items():
        require(variant in VARIANTS,'unknown build variant')
        profile=details['profile'];require(profile['description']=='Mach-O 64-bit executable arm64' and profile['stack_bytes']==536870912,'binary profile')
        binary=folder/variant/'diagnostic';require(Path(details['binary'])==binary,'binary path')
        bind(binary,bound,details['sha256']);objects=[]
        for i,source in enumerate(CPP):
            obj=folder/variant/(Path(source).stem+'.o');objects.append(str(obj))
            bind(obj,bound,details['objects'][str(obj.relative_to(folder))])
            commands.append((variant,'compile-'+str(i),['/usr/bin/arch','-arm64','/usr/bin/clang++']+
                             expected_flags+VARIANTS[variant]+['-c',str(ROOT/source),'-o',str(obj)]))
        require(set(details['objects'])=={str(Path(o).relative_to(folder)) for o in objects},'object inventory')
        commands.append((variant,'link',['/usr/bin/arch','-arm64','/usr/bin/clang++','-isysroot',info['sdk'],
                        '-L'+info['sdk']+'/usr/lib']+objects+['-Wl,-stack_size,0x20000000','-o',str(binary)]))
    require(len(commands)==len(info['commands']),'build command count')
    for (variant,label,command),embedded in zip(commands,info['commands']):
        stored=parse(read(folder/variant/(label+'.json'),bound))
        require(stored==embedded and stored['command']==command,'build command/receipt identity')
        require(stored['cwd']==str(ROOT),'build working directory')
        require(stored['deadline_seconds']==(60 if label=='link' else 180) and
                stored['rss_limit_bytes']==(12 if label=='link' else 4)*1024**3,'build resource policy')
        receipt(stored)
        read(folder/variant/(label+'.stdout'),bound,stored['stdout_sha256'])
        read(folder/variant/(label+'.stderr'),bound,stored['stderr_sha256'])
    return info


def historical(bound):
    info=parse(read(GOOGLE,bound,GOOGLE_SHA));require(info['validation']=='pass' and len(info['captures'])==24,'Google capture')
    out=defaultdict(list);fingerprints={}
    for child in info['captures']:
        if child['spec']['algorithm']!='kkt':continue
        original=Path(child['raw_csv']);path=ROOT/original.relative_to(OLD)
        rows=list(csv.DictReader(read(path,bound,child['raw_sha256']).splitlines()))
        require(len(rows)==99,'Google native row count')
        for source in rows:
            require(source['validation']=='pass' and source['algorithm']=='kkt','Google validation')
            r={k:(source[k] if k=='family' else int(source[k])) for k in IDENTITY}
            require(r['m']==r['n']*(16 if r['family']=='gnm_random' else 32),'Google dimensions')
            key=casekey(r);fingerprint=identity(r)
            require(key not in fingerprints or fingerprints[key]==fingerprint,'Google fingerprint drift');fingerprints[key]=fingerprint
            if source['phase']=='timed':
                require(int(source['elapsed_ns'])>0 and int(source['process_cpu_elapsed_ns'])>0,'Google clocks')
                out[key].append(dict(r,wall_ns=int(source['elapsed_ns']),cpu_ns=int(source['process_cpu_elapsed_ns']),
                                     invocation=int(source['invocation']),iteration=int(source['iteration'])))
    require(len(out)==132 and all(len(v)==6 for v in out.values()),'Google exact input matrix')
    return out


def controller_module(bound):
    path=ROOT/'benchmark/scaling_investigation/run.py';read(path,bound)
    spec=importlib.util.spec_from_file_location('scaling_diagnostic_row_validator',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    # Import is read-only; no build, capture, sampler or child-launch API is called.
    return module


def row_validator(bound):
    module=controller_module(bound)
    return module.validate_rows,module.work_fields()


def load_capture(folder,mode,build,bound,old,validator,fields,snapshot=None):
    folder=Path(folder).resolve(strict=True)
    info=parse(read(folder/'capture.json',bound));declaration=parse(read(folder/'declaration.json',bound))
    require(info['validation']=='pass' and info['native_process_may_still_be_running'] is False,'incomplete capture')
    require(declaration['schema']=='kkt_scaling_capture_v1' and declaration['mode']==mode,'capture schema/mode')
    cases=matrix(mode);variants=list(VARIANTS) if mode=='smoke' else ['reference','phase'] if mode=='calibration' else [mode]
    repetitions=1 if mode in ('smoke','work','allocation') else 3
    require(declaration['cases']==cases and declaration['variants']==variants and declaration['repetitions']==repetitions and declaration['warmups']==1,'capture declaration matrix')
    require(declaration['build_sha256']==sha(build/'build.json'),'build binding')
    build_record=parse(read(build/'build.json',bound,declaration['build_sha256']))
    require(set(variants)<=set(build_record['variants']),'requested capture variant missing from build')
    require(declaration['global_limit_seconds']==7200 and declaration['child_limit_seconds']==300 and declaration['rss_limit_bytes']==12*1024**3,'resource declaration')
    require(0<info['duration_s']<=7200,'global deadline')
    for path,digest in info['bound_sha256'].items():bind_source_or_artifact(path,bound,digest,snapshot)
    require(info['bound_sha256'].get(str(folder/'declaration.json'))==sha(folder/'declaration.json'),'declaration missing from bound inventory')
    expected=[(i,case,v) for i,case in enumerate(cases) for v in (variants if i%2==0 else variants[::-1])]
    require(len(info['captures'])==len(expected),'capture child count')
    result=[];groups=set()
    for child,(i,case,variant) in zip(info['captures'],expected):
        label=f'{i:03d}-{variant}'
        require(child['case']==case and child['variant']==variant and child['label']==label and child['rows']==repetitions+1,'child schedule')
        raw_path=folder/(label+'.stdout');receipt_path=folder/(label+'.json');err_path=folder/(label+'.stderr')
        for path in (raw_path,receipt_path,err_path):require(str(path) in info['bound_sha256'],'child artifact omitted')
        command=parse(read(receipt_path,bound,child['receipt_sha256']));receipt(command)
        require(command['pgid'] not in groups,'reused process group');groups.add(command['pgid'])
        expected_command=['/usr/bin/arch','-arm64',str(build/variant/'diagnostic'),case['family'],str(case['n']),str(case['graph_seed']),str(case['sampling_seed']),str(repetitions)]
        require(command['command']==expected_command and command['cwd']==str(ROOT),'native command identity')
        require(command['rss_limit_bytes']==12*1024**3,'native RSS policy')
        raw=read(raw_path,bound,child['stdout_sha256']);require(command['stdout_sha256']==child['stdout_sha256'],'stdout hash disagreement')
        read(err_path,bound,command['stderr_sha256'])
        rows=[parse(line) for line in raw.splitlines()]
        historical_row=old[casekey(case)][0]
        expected_fp=tuple(historical_row[k] for k in ('m','input_fingerprint','topology_fingerprint'))
        validator(rows,case,variant,repetitions,fields,expected_fp)
        require(child['utc_reversals']==sum(r['utc_end_ns']<r['utc_start_ns'] for r in rows),'UTC flag count')
        for row in rows:result.append(dict(row,mode=mode,variant=variant))
    return result


def summary(values):
    require(values,'empty summary')
    return dict(observations=len(values),minimum=min(values),median=statistics.median(values),maximum=max(values),mean=statistics.mean(values))


def denom(name,w,row):
    unique=w['path_query_visits']-2*w['verifier_queries']
    mapping={'input':('input_edge_records',row['m']),
             'minimum_scan':('contraction_edges',w['contraction_edges']),
             'sampling':('sampling_edge_visits',w['sampling_edge_visits']),
             'forest_recovery':('verifier_forest_edges',w['verifier_forest_edges']),
             'query_gather':('lca_queries',w['lca_queries']),
             'mark_scatter':('verifier_tree_edges',w['verifier_tree_edges']),
             'median_table':('median_entries',w['median_entries']),
             'path_walk':('path_visit_vertices + unique_requests + path_binary_search_steps',w['path_visit_vertices']+unique+w['path_binary_search_steps']),
             'fbt':('fbt_vertex_visits + fbt_edge_visits + fbt_arc_visits',w['fbt_vertex_visits']+w['fbt_edge_visits']+w['fbt_arc_visits']),
             'lca_build':('lca_euler_entries + lca_log_entries + lca_block_scan_visits + lca_sparse_cells + lca_micro_cells',sum(w[x] for x in ('lca_euler_entries','lca_log_entries','lca_block_scan_visits','lca_sparse_cells','lca_micro_cells'))),
             'filtering':('verifier_edges',w['verifier_edges']),
             'output':('hash_insert_items',w['hash_insert_items'])}
    return mapping.get(name)


def count_fits(work):
    """Google's duration-space formula applied to counts; not a Google run."""
    groups=defaultdict(list);out=[]
    for row in work:
        if row['counter'] in FIT_COUNTS:groups[(row['family'],row['graph_seed'],row['sampling_seed'],row['counter'])].append(row)
    for (family,g,s,counter),rows in groups.items():
        rows.sort(key=lambda r:r['n']);require(tuple(r['n'] for r in rows)==SIZES,'six-size counter curve')
        counts=[r['value'] for r in rows];Ns=[r['N'] for r in rows];mean=statistics.mean(counts)
        fits=[]
        for model in ('N','NlgN'):
            xs=[N if model=='N' else N*math.log2(N) for N in Ns]
            scale=max(xs);basis=[x/scale for x in xs]
            a=math.fsum(x*y for x,y in zip(basis,counts))/math.fsum(x*x for x in basis)
            score=math.sqrt(math.fsum((y-a*x)**2 for x,y in zip(basis,counts))/len(rows))/mean if mean else None
            fits.append(dict(family=family,graph_seed=g,sampling_seed=s,counter=counter,model=model,
                coefficient_counts=a/scale,normalized_rms=score if score is not None else '',status='defined' if mean else 'zero_mean',
                observations=len(rows),small_count_per_N=counts[0]/Ns[0],large_count_per_N=counts[-1]/Ns[-1],
                count_per_N_growth=(counts[-1]/Ns[-1])/(counts[0]/Ns[0]) if counts[0] else '',
                growth_status='defined' if counts[0] else 'zero_denominator'))
        best=min(fits,key=lambda r:r['normalized_rms'])['model'] if mean else None
        for row in fits:row['selected_between_two']=row['model']==best
        out.extend(fits)
    require(len(out)==len(FIT_COUNTS)*12*2,'counter-fit matrix')
    return out


def tables(captures,old,fields):
    out={k:[] for k in ('phase_repetitions','phase_summary','work','phase_per_event','allocation_repetitions',
                        'allocation_summary','calibration_pairs','calibration_summary','historical_cpu_work','endpoint_contributions')}
    phase=defaultdict(list);work={};alloc=defaultdict(list);cal=defaultdict(lambda:defaultdict(list))
    for row in captures['phase']:
        if not row['warmup']:phase[identity(row)].append(row)
    for row in captures['work']:
        if not row['warmup']:
            key=identity(row);require(key not in work,'duplicate work input');work[key]=row
    require(set(phase)==set(work) and len(work)==72,'phase/work full identity join')
    for row in captures['allocation']:
        if not row['warmup']:
            require(identity(row) in work,'allocation full identity join');alloc[identity(row)].append(row)
    for row in captures['calibration']:
        if not row['warmup']:
            require(identity(row) in work,'calibration full identity join');cal[identity(row)][row['variant']].append(row)
    for key,rows in phase.items():
        ident=dict(zip(IDENTITY,key));N=ident['n']+ident['m'];w=work[key]['work']
        counters={**w,'work_proxy':work[key]['work_proxy'],
                  'unique_requests':w['path_query_visits']-2*w['verifier_queries'],
                  'partition_edge_visits':w['verifier_edge_visits']-2*w['verifier_tree_edges']-2*(w['fbt_output_vertices']-w['fbt_calls'])}
        require(counters['unique_requests']>=0 and counters['partition_edge_visits']>=0,'derived counter sign')
        for name,value in counters.items():out['work'].append(dict(ident,N=N,counter=name,value=value,per_N=value/N))
        require(all(identity(r)==key for r in old[casekey(ident)]),'Google full identity join')
        historical_cpu=[r['cpu_ns'] for r in old[casekey(ident)]]
        for name in HISTORICAL_COUNTS:
            value=counters[name]
            out['historical_cpu_work'].append(dict(ident,N=N,counter=name,count=value,count_per_N=value/N,
                historical_observations=len(historical_cpu),historical_median_cpu_ns=statistics.median(historical_cpu),
                historical_cpu_ns_per_N=statistics.median(historical_cpu)/N,
                historical_cpu_ns_per_counter=statistics.median(historical_cpu)/value if value else '',
                historical_minimum_cpu_ns_per_counter=min(historical_cpu)/value if value else '',
                historical_maximum_cpu_ns_per_counter=max(historical_cpu)/value if value else '',
                ratio_status='defined' if value else 'zero_denominator'))
        for name in (*PHASES,'outside_collector','total'):
            values=[]
            for row in rows:
                value=row['wall_ns'] if name=='total' else row['wall_ns']-row['phase_total_ns'] if name=='outside_collector' else row['phases'][name]['wall_ns']
                values.append(value)
                out['phase_repetitions'].append(dict(ident,N=N,phase=name,repetition=row['repetition'],wall_ns=value,ns_per_N=value/N))
            out['phase_summary'].append(dict(ident,N=N,phase=name,**summary(values),median_ns_per_N=statistics.median(values)/N))
            denominator=denom(name,w,ident)
            if denominator:
                label,value=denominator
                out['phase_per_event'].append(dict(ident,N=N,phase=name,denominator_label=label,denominator=value,
                    phase_median_wall_ns=statistics.median(values),ns_per_event=statistics.median(values)/value if value else '',
                    minimum_ns_per_event=min(values)/value if value else '',maximum_ns_per_event=max(values)/value if value else '',
                    ratio_status='defined' if value else 'zero_denominator'))
    for key,rows in alloc.items():
        ident=dict(zip(IDENTITY,key));N=ident['n']+ident['m']
        metrics=defaultdict(list)
        for row in rows:
            values={name:row[name] for name in ('peak_live_usable_bytes','returned_live_usable_bytes')}
            for metric in ('allocations','requested_bytes','usable_bytes','deallocations','freed_usable_bytes'):
                values['cumulative_'+metric]=sum(p[metric] for p in row['phases'].values())
            for phase_name,entry in row['phases'].items():
                for metric in ('allocations','requested_bytes','usable_bytes','freed_usable_bytes'):
                    values[phase_name+'__cumulative_'+metric]=entry[metric]
            for metric,value in values.items():
                out['allocation_repetitions'].append(dict(ident,N=N,metric=metric,repetition=row['repetition'],value=value,per_N=value/N))
                metrics[metric].append(value)
        for metric,values in metrics.items():out['allocation_summary'].append(dict(ident,N=N,metric=metric,**summary(values),median_per_N=statistics.median(values)/N))
    for key,pair in cal.items():
        ident=dict(zip(IDENTITY,key));require(set(pair)=={'reference','phase'},'calibration variants')
        by_variant={v:{r['repetition']:r for r in rows} for v,rows in pair.items()}
        require(all(set(v)=={1,2,3} for v in by_variant.values()),'calibration repetitions')
        for clock in ('wall_ns','cpu_ns'):
            ratios=[]
            for repetition in (1,2,3):
                a,b=(by_variant[v][repetition][clock] for v in ('phase','reference'))
                ratios.append(Fraction(a,b))
                out['calibration_pairs'].append(dict(ident,clock=clock,repetition=repetition,phase_ns=a,reference_ns=b,
                    phase_over_reference=float(Fraction(a,b)),exact_numerator=a,exact_denominator=b))
            a=statistics.median(r[clock] for r in pair['phase']);b=statistics.median(r[clock] for r in pair['reference'])
            out['calibration_summary'].append(dict(ident,clock=clock,median_paired_ratio=float(statistics.median(ratios)),
                minimum_paired_ratio=float(min(ratios)),maximum_paired_ratio=float(max(ratios)),ratio_of_medians=a/b,
                phase_median_ns=a,reference_median_ns=b))
    # Means, not component medians, give an exact additive phase decomposition.
    grouped=defaultdict(dict)
    for key,rows in phase.items():grouped[(key[0],key[2],key[3])][key[1]]=(key,rows)
    for (family,g,s),sizes in grouped.items():
        lo,hi=min(sizes),max(sizes);low_key,low=sizes[lo];high_key,high=sizes[hi]
        totals={}
        for name in (*PHASES,'outside_collector','total'):
            means=[];medians=[]
            for key,rows in ((low_key,low),(high_key,high)):
                N=key[1]+key[4]
                values=[r['wall_ns'] if name=='total' else r['wall_ns']-r['phase_total_ns'] if name=='outside_collector' else r['phases'][name]['wall_ns'] for r in rows]
                means.append(Fraction(sum(values),len(values)*N));medians.append(Fraction(statistics.median(values),N))
            delta=means[1]-means[0];totals[name]=delta
            out['endpoint_contributions'].append(dict(family=family,graph_seed=g,sampling_seed=s,phase=name,small_n=lo,large_n=hi,
                small_mean_ns_per_N=float(means[0]),large_mean_ns_per_N=float(means[1]),mean_delta_ns_per_N=float(delta),
                delta_exact_numerator=delta.numerator,delta_exact_denominator=delta.denominator,
                median_delta_ns_per_N=float(medians[1]-medians[0])))
        require(sum(v for k,v in totals.items() if k!='total')==totals['total'],'endpoint phase additivity')
    out['count_fits']=count_fits(out['work'])
    return out


def write_csv(path,rows):
    require(rows,'empty table')
    with path.open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for mode in ('phase','work','allocation','calibration'):
        parser.add_argument('--'+mode,type=Path,required=True);parser.add_argument('--'+mode+'-build',type=Path)
    parser.add_argument('--build',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source-snapshot',type=Path,help='Verified immutable baseline source-copy manifest; native/raw artifacts stay in place.')
    args=parser.parse_args();output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    bound={};status=dict(schema='kkt_scaling_diagnostic_analysis_v1',validation='running',native_execution=False,
        input_sha256=bound,invocation=sys.argv,rows_removed=0,rows_adjusted=0,
        reused_controller_scope='Read-only row validator and counter schema; no arithmetic aggregation or launch APIs.',
        endpoint_aggregation='Untrimmed means preserve phase additivity; median total deltas separately retained.')
    try:
        read(__file__,bound);read(HERE/'README.md',bound)
        snapshot=source_snapshot(args.source_snapshot,bound);status['source_snapshot']=snapshot
        builds={};captures={};first=None
        for mode in ('phase','work','allocation','calibration'):
            path=(getattr(args,mode+'_build') or args.build).resolve()
            if str(path) not in builds:builds[str(path)]=load_build(path,bound,snapshot)
            info=builds[str(path)]
            proof=(info['source_sha256'],info['flags'],info['compiler'],info['sdk'])
            require(first is None or first==proof,'production source/toolchain differs across diagnostic builds');first=proof
        old=historical(bound);validator,fields=row_validator(bound)
        for mode in ('phase','work','allocation','calibration'):
            build=(getattr(args,mode+'_build') or args.build).resolve()
            captures[mode]=load_capture(getattr(args,mode),mode,build,bound,old,validator,fields,snapshot)
        output_tables=tables(captures,old,fields)
        for name,rows in output_tables.items():write_csv(output/(name+'.csv'),rows)
        # All original warmup/call records remain, even though plots summarize non-warmup repetitions.
        (output/'all_raw_records.json').write_text(json.dumps(captures,indent=2)+'\n')
        recheck(bound);status.update(validation='pass',table_counts={k:len(v) for k,v in output_tables.items()},
            raw_counts={k:len(v) for k,v in captures.items()},exact_google_joins=72,
            warmups_retained=sum(r['warmup'] for v in captures.values() for r in v),
            utc_reversals=sum(r['utc_end_ns']<r['utc_start_ns'] for v in captures.values() for r in v))
    except BaseException as error:status.update(validation='failed',error=repr(error));raise
    finally:
        status['output_sha256']={p.name:sha(p) for p in output.iterdir() if p.is_file()}
        (output/'provenance.json').write_text(json.dumps(status,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:status[k] for k in ('validation','table_counts','raw_counts','exact_google_joins')}))


if __name__=='__main__':main()
