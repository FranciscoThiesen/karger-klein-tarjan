#!/usr/bin/env python3
"""Bounded, sequential diagnostic builds/capture; never run old campaign drivers."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
SOURCES=['boruvka/boruvka.cpp','kruskal/kruskal.cpp','prim/prim.cpp','lca/lca.cpp',
         'union_find/union_find.cpp','graph_utils/graph_utils.cpp','verifier/verifier_v2.cpp','kkt/kkt.cpp']
BASE_FLAGS=['-std=c++17','-O3','-march=native','-Wall','-Wextra','-I'+str(ROOT),
            '-DKKT_EXPERIMENT_RETAIN_PARALLEL','-DKKT_EXPERIMENT_EDGE_VIEW',
            '-DKKT_EXPERIMENT_COMPRESSED_QUERIES','-DKKT_EXPERIMENT_EIGHTH_SAMPLING']
VARIANTS={'reference':[], 'phase':['-DKKT_ENABLE_PHASE_STATS'],
          'allocation':['-DKKT_ENABLE_PHASE_STATS','-DKKT_SCALING_ALLOCATIONS'],
          'work':['-DKKT_ENABLE_WORK_STATS']}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,data):Path(path).write_text(json.dumps(data,indent=2)+'\n')

def run_owned(command,directory,label,timeout=300,rss_cap=12*1024**3):
    """Own a fresh process group; retain actual exit, clocks, and sampled RSS."""
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    out=directory/(label+'.stdout');err=directory/(label+'.stderr')
    assert not out.exists() and not err.exists(),'output collision'
    start=time.monotonic();started=time.time_ns();peak=0;failure=None;samples=0
    with out.open('xb') as stdout,err.open('xb') as stderr:
        child=subprocess.Popen(command,cwd=ROOT,stdout=stdout,stderr=stderr,start_new_session=True)
        try:
            while child.poll() is None:
                if time.monotonic()-start>timeout:failure='deadline';break
                snap=subprocess.run(['/bin/ps','-axo','pid=,pgid=,rss='],capture_output=True,text=True,check=True)
                rss=sum(int(x.split()[2])*1024 for x in snap.stdout.splitlines()
                        if len(x.split())==3 and int(x.split()[1])==child.pid)
                peak=max(peak,rss);samples+=1
                if rss>rss_cap:failure='rss_limit';break
                time.sleep(.2)
        except BaseException:
            failure='controller_exception';raise
        finally:
            if child.poll() is None:
                os.killpg(child.pid,signal.SIGTERM)
                try:child.wait(timeout=2)
                except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
            code=child.wait()
            try:os.killpg(child.pid,0);empty=False
            except ProcessLookupError:empty=True
            record={'command':command,'cwd':str(ROOT),'pgid':child.pid,'exit_code':code,
                    'group_empty':empty,'failure':failure,'start_utc_ns':started,'end_utc_ns':time.time_ns(),
                    'duration_s':time.monotonic()-start,'peak_sampled_group_rss_bytes':peak,'rss_samples':samples,
                    'stdout_sha256':sha(out),'stderr_sha256':sha(err)}
            write(directory/(label+'.json'),record)
    if failure or code or not empty:raise RuntimeError('child failed: '+str(directory/label))
    return record

def build(out,variant_names):
    out.mkdir(parents=True,exist_ok=False)
    sdk=subprocess.check_output(['/usr/bin/xcrun','--show-sdk-path'],text=True).strip()
    flags=BASE_FLAGS+['-isysroot',sdk]
    inputs={str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob('*.hpp') if '.build' not in p.parts}
    inputs.update({name:sha(ROOT/name) for name in SOURCES})
    inputs[str((HERE/'diagnostic.cpp').relative_to(ROOT))]=sha(HERE/'diagnostic.cpp')
    results={}
    for variant in variant_names:
        folder=out/variant;folder.mkdir();objects=[]
        for i,source in enumerate(SOURCES+['benchmark/scaling_investigation/diagnostic.cpp']):
            obj=folder/(Path(source).stem+'.o');objects.append(str(obj))
            run_owned(['/usr/bin/clang++']+flags+VARIANTS[variant]+['-c',str(ROOT/source),'-o',str(obj)],
                      folder,'compile-'+str(i),timeout=180,rss_cap=4*1024**3)
        binary=folder/'diagnostic'
        run_owned(['/usr/bin/clang++','-isysroot',sdk]+objects+['-Wl,-stack_size,0x20000000','-o',str(binary)],folder,'link',timeout=60)
        results[variant]={'binary':str(binary),'sha256':sha(binary),'objects':{str(Path(o).relative_to(out)):sha(o) for o in objects}}
    assert all(sha(ROOT/name)==h for name,h in inputs.items()),'source changed during build'
    write(out/'build.json',{'validation':'pass','source_sha256':inputs,'flags':flags,'variant_defines':VARIANTS,
                          'variants':results,'compiler':subprocess.check_output(['/usr/bin/clang++','--version'],text=True)})
    print(json.dumps({'build':'pass','variants':list(results),'directory':str(out)}),flush=True)

def matrix(mode):
    sizes=[1024,4096,16384,65536,262144,1048576]
    graphs=[19000013,19000043];samples=[3001,3011]
    if mode=='smoke':sizes=[1024];graphs=graphs[:1];samples=samples[:1]
    if mode=='allocation':sizes=[16384,262144,1048576];samples=samples[:1]
    if mode=='calibration':sizes=[1024,1048576];samples=samples[:1];graphs=graphs[:1]
    rows=[]
    for gi,g in enumerate(graphs):
        for n in (sizes if gi==0 else list(reversed(sizes))):
            for family in ['leaf_hierarchy4','leaf_shuffled4','gnm_random']:
                for s in samples:rows.append({'family':family,'n':n,'graph_seed':g,'sampling_seed':s})
    return rows

def capture(out,build_dir,mode):
    out.mkdir(parents=True,exist_ok=False);record=json.loads((build_dir/'build.json').read_text())
    variants=(['reference','phase','allocation','work'] if mode=='smoke' else
              ['reference','phase'] if mode=='calibration' else [mode])
    cases=matrix(mode);repetitions=1 if mode in ('smoke','allocation','work') else 3
    declaration={'schema':'kkt_scaling_capture_v1','mode':mode,'cases':cases,'variants':variants,
                 'repetitions':repetitions,'warmups':1,'build_sha256':sha(build_dir/'build.json'),
                 'global_limit_seconds':7200,'child_limit_seconds':300,'rss_limit_bytes':12*1024**3,
                 'timing_claim':'phase/allocation/work builds are diagnostic; only reference is uninstrumented'}
    write(out/'declaration.json',declaration);started=time.monotonic();captures=[]
    for index,case in enumerate(cases):
        for v in (variants if index%2==0 else list(reversed(variants))):
            assert time.monotonic()-started<7200,'global capture deadline'
            info=record['variants'][v];binary=Path(info['binary']);assert sha(binary)==info['sha256']
            label=f'{index:03d}-{v}'
            run_owned([str(binary),case['family'],str(case['n']),str(case['graph_seed']),str(case['sampling_seed']),str(repetitions)],out,label)
            rows=[json.loads(line) for line in (out/(label+'.stdout')).read_text().splitlines()]
            assert len(rows)==repetitions+1 and [r['repetition'] for r in rows]==list(range(repetitions+1))
            assert all(r['validation']=='pass' and all(r[k]==val for k,val in case.items()) for r in rows)
            assert all(r['warmup']==(r['repetition']==0) for r in rows)
            assert all(r['input_fingerprint']==rows[0]['input_fingerprint'] for r in rows)
            if v=='work':
                assert all(r['work']==rows[0]['work'] for r in rows),'nonreproducible counters'
                w=rows[0]['work'];assert w['sampled_edges']+w['filtered_edges']<=w['sampling_edge_visits']+w['verifier_forest_edges']
                assert w['kkt_vertices']<=2*case['n'] and w['current_depth']==0
                assert w['path_binary_search_steps']<=4*w['fbt_input_vertices']+3*w['verifier_queries']
            captures.append({'case':case,'variant':v,'label':label,'rows':len(rows),
                             'stdout_sha256':sha(out/(label+'.stdout')),'receipt_sha256':sha(out/(label+'.json'))})
            write(out/'progress.json',{'completed':captures,'validation':'in_progress'})
            print(json.dumps({'completed':len(captures),'total':len(cases)*len(variants),'case':case,'variant':v}),flush=True)
    write(out/'capture.json',{'validation':'pass','declaration_sha256':sha(out/'declaration.json'),
                            'duration_s':time.monotonic()-started,'captures':captures})

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
    b=sub.add_parser('build');b.add_argument('output',type=Path);b.add_argument('--variants',nargs='+',choices=list(VARIANTS),default=list(VARIANTS))
    c=sub.add_parser('capture');c.add_argument('output',type=Path);c.add_argument('--build',required=True,type=Path);c.add_argument('--mode',choices=['smoke','phase','work','allocation','calibration'],required=True)
    args=p.parse_args()
    if args.action=='build':build(args.output.resolve(),args.variants)
    else:capture(args.output.resolve(),args.build.resolve(),args.mode)
if __name__=='__main__':main()
