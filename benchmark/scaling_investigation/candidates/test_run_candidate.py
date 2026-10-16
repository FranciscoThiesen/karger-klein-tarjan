#!/usr/bin/env python3
"""Focused synthetic candidate gates; no native subprocess or sampler is invoked."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('depth_candidate_tested',HERE/'run_candidate.py')
run=importlib.util.module_from_spec(spec);spec.loader.exec_module(run)


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve();self.real_root=run.ROOT;self.real_here=run.HERE
    def test_fixed_matrices_and_balanced_noinline_positions(self):
        expected={'smoke':(3,2,1),'work':(72,1,1),'timing':(36,2,3),'phase':(18,2,3),
                  'allocation':(18,2,1),'inline-control':(6,3,3),'inline-phase':(6,3,3)}
        for mode,(cases,policies,reps) in expected.items():
            matrix,p,_,r=run.schedule(mode)
            self.assertEqual((len(matrix),len(p),r),(cases,policies,reps))
            self.assertEqual(len({run.identity(c) for c in matrix}),cases)
        cases,_,_,_=run.schedule('timing')
        self.assertEqual({x['sampling_seed'] for x in cases},{3001})
        self.assertEqual({x['graph_seed'] for x in cases},{19000013,19000043})
        self.assertEqual({x['n'] for x in cases},{1024,4096,16384,65536,262144,1048576})
        _,p,_,_=run.schedule('inline-control')
        for policy in p:
            self.assertEqual([sum(run.policy_order(p,i)[j]==policy for i in range(6)) for j in range(3)],[2,2,2])
    def test_snapshot_preserves_all_sources_and_rejects_bad_mapping(self):
        here=self.root/'benchmark/scaling_investigation/candidates';here.mkdir(parents=True)
        files=[here.parent/'run.py',self.root/'benchmark/work_metrics.hpp',self.root/'verifier/verifier_v2.cpp']
        for i,path in enumerate(files):path.parent.mkdir(parents=True,exist_ok=True);path.write_text('source'+str(i))
        source={str(p):run.sha(p) for p in files}
        build=self.root/'build.json';run.write(build,{'validation':'pass','source_sha256':source})
        with mock.patch.object(run,'ROOT',self.root),mock.patch.object(run,'HERE',here):
            run.snapshot(self.root/'snapshot',build)
            path=self.root/'snapshot/snapshot.json';value,_,_=run.check_snapshot(path)
            self.assertEqual(set(value['copies']),set(source))
            files[-1].write_text('candidate source')
            run.check_snapshot(path)  # only source is deliberately relocated
            for change in ('omit','extra','wrong-copy'):
                bad=copy.deepcopy(value)
                if change=='omit':bad['copies'].pop(str(files[-1]))
                elif change=='extra':bad['copies']['undeclared']='nonexistent'
                else:bad['copies'][str(files[-1])]=str(files[-1])
                run.write(path,bad)
                with self.subTest(change=change),self.assertRaises(RuntimeError):run.check_snapshot(path)
            run.write(path,value);Path(value['copies'][str(files[-1])]).write_text('corrupt archive')
            with self.assertRaisesRegex(RuntimeError,'drift'):run.check_snapshot(path)
    def test_all65_exact_delta_and_zero_dispatch_rejection(self):
        fields=run.base.work_fields();old=dict.fromkeys(fields,0)
        old.update(lca_vertices=7,initialized_slots=50,lca_queries=11,verifier_queries=22,path_query_visits=48)
        new=dict(old,initialized_slots=43)
        run.equal_work(old,new,'depth');run.equal_work(old,old,'reference')
        for change in ('wrong-delta','extra-field','missing-field','other-counter','zero-dispatch'):
            a,b=copy.deepcopy(old),copy.deepcopy(new)
            if change=='wrong-delta':b['initialized_slots']+=1
            elif change=='extra-field':b['surprise']=0
            elif change=='missing-field':b.pop('current_depth')
            elif change=='other-counter':b['lca_queries']+=1
            else:a['lca_vertices']=b['lca_vertices']=0;b['initialized_slots']=a['initialized_slots']
            with self.subTest(change=change),self.assertRaises(RuntimeError):run.equal_work(a,b,'depth')
    def receipt(self):
        return dict(command=['mock'],cwd=str(run.ROOT),validation='pass',exit_code=0,group_empty=True,
                    native_process_may_still_be_running=False,pgid=123,started_monotonic_ns=10,
                    exit_monotonic_ns=20,finished_monotonic_ns=30,deadline_seconds=1,rss_limit_bytes=4096,
                    observations=[{'validation':'pass','rss_kib':1}],
                    cleanup=dict(native_exit_known=True,group_exit_known=True,native_process_may_still_be_running=False,
                                 returncode=0,process_group=123,group_verification={'validation':'pass','members':[]}))
    def test_native_receipt_deadline_empty_resource_and_typed_identity(self):
        path=self.root/'receipt.json';good=self.receipt();run.write(path,good)
        run.check_receipt(path,['mock'],{})
        for change in ('late','unknown','member','nonzero','bool-group','rss','unavailable'):
            value=copy.deepcopy(good)
            if change=='late':value.update(exit_monotonic_ns=1000000011,finished_monotonic_ns=1000000020)
            elif change=='unknown':value['cleanup']['group_exit_known']=False
            elif change=='member':value['cleanup']['group_verification']['members']=[123]
            elif change=='nonzero':value['exit_code']=1
            elif change=='bool-group':value['pgid']=True
            elif change=='rss':value['observations'][0]['rss_kib']=5
            else:value['observations']=[{'validation':'unavailable'}]*3
            run.write(path,value)
            with self.subTest(change=change),self.assertRaises(RuntimeError):run.check_receipt(path,['mock'],{})
    def test_first_invalid_child_preserves_failed_campaign_and_stops(self):
        case=run.schedule('smoke')[0][0];out=self.root/'capture';build_path=self.root/'build.json';old_path=self.root/'old.json'
        build_path.write_text('{}');old_path.write_text('{}')
        build={'snapshot':str(self.root/'snapshot.json'),'variants':{'reference-work':{'binary':'/mock/reference'}}}
        def child(command,folder,label,**kwargs):
            (folder/(label+'.stdout')).write_text('{}\n');return {'validation':'pass'}
        with mock.patch.object(run,'check_build',return_value=(build,{})), \
             mock.patch.object(run,'baseline_work',return_value=({},{})), \
             mock.patch.object(run.base,'historical_inputs',return_value={run.identity(case):(32768,1,2)}), \
             mock.patch.object(run.base,'run_owned',side_effect=child) as launch, \
             mock.patch.object(run,'check_receipt',return_value={'stdout_sha256':'x','stderr_sha256':'y'}):
            with self.assertRaisesRegex(RuntimeError,'missing/extra'):run.capture(out,build_path,old_path,'smoke',[])
            self.assertEqual(launch.call_count,1)
        value,_=run.read(out/'capture.json')
        self.assertEqual(value['validation'],'failed');self.assertEqual(value['captures'],[])
    def test_conflicting_provenance_and_missing_correctness_gates(self):
        file=self.root/'artifact';file.write_text('first');bound={};run.add(bound,file)
        file.write_text('second')
        with self.assertRaisesRegex(RuntimeError,'conflicting'):run.add(bound,file)
        with self.assertRaisesRegex(RuntimeError,'needs smoke'):run.prerequisites([],self.root/'build.json',{}, {})
        bad=self.root/'bad-gate.json';run.write(bad,{'validation':'failed'})
        with self.assertRaisesRegex(RuntimeError,'failed candidate'):run.prerequisites([bad,bad,bad],self.root/'build.json',{}, {})
    def test_noinline_object_and_isolated_source_proof(self):
        variants={name:{'objects':{name+'/kkt.o':'same',name+'/verifier_v2.o':policy}}
                  for name,(policy,kind) in run.VARIANTS.items()}
        run.paired_objects(variants)
        bad=copy.deepcopy(variants);bad['depth_noinline-reference']['objects']['depth_noinline-reference/kkt.o']='changed'
        with self.assertRaisesRegex(RuntimeError,'noinline'):run.paired_objects(bad)
        files={name:self.root/name for name in (*run.CHANGED,'kkt/kkt.cpp')}
        for path in files.values():path.parent.mkdir(parents=True,exist_ok=True);path.write_text('original')
        source={str(p):run.sha(p) for p in files.values()}
        for name in run.CHANGED:files[name].write_text('depth candidate')
        new=self.root/run.NEW_HEADER;new.write_text('private depth RMQ')
        current={**source,str(new):run.sha(new)}
        with mock.patch.object(run,'ROOT',self.root),mock.patch.object(run.base,'source_inventory',return_value=current):
            self.assertEqual(run.isolated_sources({'source_sha256':source}),sorted(run.CHANGED))
            files['kkt/kkt.cpp'].write_text('unexpected policy edit')
            with self.assertRaisesRegex(RuntimeError,'source delta'):run.isolated_sources({'source_sha256':source})
    def test_reconstructed_prerequisite_must_be_originally_bound(self):
        build_path=self.root/'build.json';old_path=self.root/'old.json';gate=self.root/'gate-evidence'
        for path in (build_path,old_path,gate):path.write_text('{}')
        build={'snapshot':str(self.root/'snapshot.json')}
        # Matrix correctness is tested separately; this isolates the original-bound-inventory rule.
        with mock.patch.object(run,'schedule',return_value=([],run.POLICIES,'reference',3)), \
             mock.patch.object(run,'check_build',side_effect=lambda p:(build,{str(build_path):run.sha(build_path)})), \
             mock.patch.object(run,'baseline_work',side_effect=lambda *args:({}, {str(old_path):run.sha(old_path)})), \
             mock.patch.object(run.base,'historical_inputs',return_value={}), \
             mock.patch.object(run,'prerequisites',side_effect=lambda paths,bp,record,bound:run.add(bound,gate)):
            declaration=run.declaration_for('timing');run.write(self.root/'declaration.json',declaration)
            bound={str(p):run.sha(p) for p in (build_path,old_path,self.root/'declaration.json')}
            info=dict(schema='kkt_depth_candidate_capture_v1',validation='pass',native_process_may_still_be_running=False,
                      mode='timing',build_record=str(build_path),build_record_sha256=run.sha(build_path),baseline_work=str(old_path),
                      baseline_work_sha256=run.sha(old_path),declaration=declaration,captures=[],gates=[],bound_sha256=bound,duration_s=1)
            path=self.root/'capture.json';run.write(path,info)
            with self.assertRaisesRegex(RuntimeError,'omitted required bound'):run.load(path)
            info['bound_sha256'][str(gate)]=run.sha(gate);run.write(path,info)
            self.assertEqual(run.load(path)[1],[])
    def test_complete_smoke_reload_and_self_consistent_metadata_negatives(self):
        out=self.root/'capture';out.mkdir();build_path=self.root/'build.json';old_path=self.root/'old.json'
        build_path.write_text('{}');old_path.write_text('{}')
        build={'snapshot':str(self.root/'snapshot.json'),'variants':{p+'-work':{'binary':'/mock/'+p} for p in run.POLICIES}}
        fields=run.base.work_fields();work=dict.fromkeys(fields,0)
        work.update(kkt_calls=2,kkt_vertices=1024,hash_insert_items=1023,lca_vertices=7,initialized_slots=50,
                    sampling_edge_visits=100,sampled_edges=12,filtered_edges=30,verifier_forest_edges=4,
                    fbt_input_vertices=4,verifier_queries=2,path_query_visits=5,path_binary_search_steps=6,
                    contraction_edge_visits=300,contraction_edges=100)
        cases,policies,_,_=run.schedule('smoke');expected={};baseline={};captures=[]
        bound={str(build_path):run.sha(build_path),str(old_path):run.sha(old_path)}
        declaration=run.declaration_for('smoke');run.write(out/'declaration.json',declaration)
        bound[str(out/'declaration.json')]=run.sha(out/'declaration.json')
        for index,case in enumerate(cases):
            expected[run.identity(case)]=(case['n']*(16 if case['family']=='gnm_random' else 32),index+1,index+10)
            baseline[run.identity(case)]=[{'work':work}]
            for policy in run.policy_order(policies,index):
                label=f'{index:03d}-{policy}';raw=out/(label+'.stdout');err=out/(label+'.stderr');rp=out/(label+'.json')
                w=dict(work,initialized_slots=43 if policy=='depth' else 50)
                m,weighted,topology=expected[run.identity(case)]
                rows=[dict(schema='kkt_scaling_diagnostic_v1',**case,m=m,input_fingerprint=weighted,
                    topology_fingerprint=topology,repetition=i,warmup=i==0,wall_ns=100,cpu_ns=90,
                    utc_start_ns=10,utc_end_ns=110,phase_total_ns=0,peak_live_usable_bytes=0,returned_live_usable_bytes=0,
                    phases={name:dict.fromkeys(run.base.PHASE_FIELDS,0) for name in run.base.PHASES},
                    work=w,work_proxy=sum(w[k] for k,v in fields.items() if v),validation='pass') for i in range(2)]
                raw.write_text(''.join(json.dumps(row)+'\n' for row in rows));err.write_text('')
                receipt=self.receipt();receipt['command']=['/usr/bin/arch','-arm64','/mock/'+policy,case['family'],str(case['n']),str(case['graph_seed']),str(case['sampling_seed']),'1']
                receipt.update(stdout_sha256=run.sha(raw),stderr_sha256=run.sha(err));run.write(rp,receipt)
                for path in (raw,err,rp):bound[str(path)]=run.sha(path)
                captures.append(dict(case=case,policy=policy,variant=policy+'-work',label=label,rows=2,stdout=str(raw),receipt=str(rp)))
        info=dict(schema='kkt_depth_candidate_capture_v1',validation='pass',native_process_may_still_be_running=False,
                  mode='smoke',build_record=str(build_path),build_record_sha256=run.sha(build_path),baseline_work=str(old_path),
                  baseline_work_sha256=run.sha(old_path),declaration=declaration,captures=captures,bound_sha256=bound,duration_s=1)
        path=out/'capture.json';run.write(path,info)
        with mock.patch.object(run,'check_build',side_effect=lambda p:(build,{str(build_path):run.sha(build_path)})), \
             mock.patch.object(run,'baseline_work',side_effect=lambda *args:(baseline,{str(old_path):run.sha(old_path)})), \
             mock.patch.object(run.base,'historical_inputs',return_value=expected):
            self.assertEqual(len(run.load(path)[1]),12)
            for change in ('relaxed-limit','typed-warmups','omitted-declaration','omitted-raw','different-declaration'):
                bad=copy.deepcopy(info);doc=copy.deepcopy(declaration)
                if change=='relaxed-limit':bad['declaration']['child_limit_seconds']=301;doc=bad['declaration']
                elif change=='typed-warmups':bad['declaration']['warmups']=True;doc=bad['declaration']
                elif change=='omitted-declaration':bad['bound_sha256'].pop(str(out/'declaration.json'))
                elif change=='omitted-raw':bad['bound_sha256'].pop(captures[0]['stdout'])
                else:doc['mode']='work'
                run.write(out/'declaration.json',doc)
                if str(out/'declaration.json') in bad['bound_sha256']:
                    bad['bound_sha256'][str(out/'declaration.json')]=run.sha(out/'declaration.json')
                run.write(path,bad)
                with self.subTest(change=change),self.assertRaises(RuntimeError):run.load(path)


if __name__=='__main__':unittest.main(verbosity=2)
