#!/usr/bin/env python3
"""Focused standard-library tests; all process launches are mocked."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import build_native_view as gate
import build_view as view
import validate_export as oracle


def sample_fixture():
    root=dict(n=4,m=7,edges=[[0,1,1,0],[1,2,2,1],[0,2,5,2],[2,3,3,3],[0,3,9,4],[1,3,7,5],[0,1,4,6]])
    half=dict(policy='half',mask=1,engine_words=7,sample_edges=4,forest_edges=3,forest_components=1,
              heavy_edges=4,light_edges=3,selected_parent_positions=[0,1,3,4],sampled_ids=[0,1,3,4],
              forest_ids=[0,1,3],heavy_ids=[2,4,5,6])
    eighth=dict(policy='eighth',mask=7,engine_words=7,sample_edges=2,forest_edges=2,forest_components=2,
                heavy_edges=1,light_edges=6,selected_parent_positions=[0,3],sampled_ids=[0,3],forest_ids=[0,3],heavy_ids=[6])
    return root,[half,eighth]


class ExportTests(unittest.TestCase):
    def test_mt_known_answer_and_strict_json(self):
        # Standard's required default-seeded 10,000th word crosses many twists:
        # https://eel.is/c++draft/rand.predef#3 ; recurrence rand.eng.mers.
        generated=list(oracle.words(5489,10000));self.assertEqual(generated[-1],4123659995)
        self.assertEqual(list(oracle.words(0,0)),[])
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'value.json'
            for text in ('{"x":1,"x":2}','{"x":NaN}','{"x":1e999}'):
                path.write_text(text)
                with self.assertRaises(ValueError):oracle.read(path)
            path.write_text('{"elapsed_seconds":1.25,"count":0}');self.assertEqual(oracle.read(path)['count'],0)

    def test_contraction_keeps_every_parallel_record_and_order(self):
        before=dict(n=4,m=5,edges=[[0,1,1,0],[2,3,2,1],[1,2,5,2],[0,3,6,3],[0,2,7,4]])
        after=dict(n=2,m=3,edges=[[0,1,5,2],[0,1,6,3],[0,1,7,4]])
        oracle.contraction(before,after,[0,1],[0,0,1,1])
        for changed in ([after['edges'][0]],list(reversed(after['edges']))):
            invalid={**after,'edges':changed,'m':len(changed)}
            with self.assertRaisesRegex(ValueError,'parallel records'):oracle.contraction(before,invalid,[0,1],[0,0,1,1])
        with self.assertRaisesRegex(ValueError,'minima'):oracle.contraction(before,after,[0,1,2],[0,0,1,1])
        with self.assertRaisesRegex(ValueError,'quotient map'):oracle.contraction(before,after,[0,1],[1,1,0,0])

    def test_independent_heavy_marks_disconnection_order_and_zero(self):
        root,samples=sample_fixture()
        with mock.patch.object(oracle,'words',return_value=iter([7,3,0,7,1,0,2])):
            oracle.samples(root,samples,[0,1,3])
        mutations=[lambda s:s[0]['heavy_ids'].pop(),lambda s:s[1]['heavy_ids'].append(2),
                   lambda s:s[0].update(forest_ids=[0,3,4]),lambda s:s[0]['selected_parent_positions'].reverse(),
                   lambda s:s[1].update(mask=1),lambda s:s[0].update(engine_words=6),
                   lambda s:s[1].update(forest_components=1),lambda s:s[0].update(forest_ids=[True,0,3])]
        for mutation in mutations:
            value=copy.deepcopy(samples);mutation(value)
            with self.subTest(value=value),mock.patch.object(oracle,'words',return_value=iter([7,3,0,7,1,0,2])):
                with self.assertRaises(ValueError):oracle.samples(root,value,[0,1,3])
        empty=[dict(policy=policy,mask=mask,engine_words=0,sample_edges=0,forest_edges=0,forest_components=2,
                    heavy_edges=0,light_edges=0,selected_parent_positions=[],sampled_ids=[],forest_ids=[],heavy_ids=[])
               for policy,mask in (('half',1),('eighth',7))]
        oracle.samples(dict(n=2,m=0,edges=[]),empty,[])

    def test_complete_timing_identities_fingerprints_and_position(self):
        graph=dict(family='leaf_hierarchy4',input_fingerprint='123',topology_fingerprint='456')
        rows=[dict(family=graph['family'],n='1024',graph_seed='17000011',algorithm=algorithm,phase=phase,repetition=str(rep),
                   validation='pass',kkt_seed='2801',m='32768',density='32',intrusion_per_mille='0',warmups='1',
                   order=str((position-rep)%6),input_fingerprint='123',topology_fingerprint='456')
              for position,algorithm in enumerate(view.ALGORITHMS) for phase,rep in [('warmup',0),*[('timed',i) for i in range(6)]]]
        view.check_timing_join(rows,graph)
        for mutation in (lambda r:r.pop(),lambda r:r.__setitem__(0,copy.deepcopy(r[1])),
                         lambda r:r[0].update(input_fingerprint='789'),lambda r:r[0].update(order='5'),
                         lambda r:r[0].update(kkt_seed='2803'),lambda r:r[0].update(warmups='0')):
            changed=copy.deepcopy(rows);mutation(changed)
            with self.assertRaises(ValueError):view.check_timing_join(changed,graph)

    def test_original_physical_objects_and_declared_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            paths={}
            for i in range(8):
                path=Path(directory)/f'production{i}.o';path.write_bytes(bytes([i]));paths[str(i)]=str(path)
            parent=dict(object_paths=paths,object_sha256={name:gate.sha(path) for name,path in paths.items()},
                        compiler='synthetic Apple clang',compiler_command=['/usr/bin/arch','-arm64','/usr/bin/clang++','--version'],sdk='/SDK')
            record=copy.deepcopy(parent);gate.check_objects(record,parent)
            for mutation in (lambda r:r['object_paths'].update({'0':str(Path(directory)/'substitute.o')}),
                             lambda r:r['object_sha256'].update({'0':'0'*64}),lambda r:r.update(sdk='/different')):
                changed=copy.deepcopy(record);mutation(changed)
                with self.assertRaises(ValueError):gate.check_objects(changed,parent)
            Path(paths['0']).write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'changed frozen object'):gate.check_objects(record,parent)
        policy=dict(removed={'CPATH':'old','LIBRARY_PATH':None},required_empty={key:None for key in gate.EMPTY_ENV},
                    retained={'SDKROOT':None,'DEVELOPER_DIR':None})
        gate.environment_policy(policy);policy['required_empty']['CXXFLAGS']='-O0'
        with self.assertRaises(ValueError):gate.environment_policy(policy)

    def test_three_complete_intervals_resource_and_exit_proof(self):
        commands=[['compile'],['link'],['export']];groups=[];intervals=[]
        for i,command in enumerate(commands):
            start=i*100;finish=start+90;pid=100+i
            observation=dict(validation='pass',process_group=pid,monotonic_ns=start+10,rss_kib=4,members=[dict(pid=pid,rss_kib=4)])
            final=dict(validation='pass',process_group=pid,monotonic_ns=start+80,rss_kib=0,members=[])
            cleanup=dict(native_exit_known=True,group_exit_known=True,native_process_may_still_be_running=False,
                returncode=0,process_group=pid,started_monotonic_ns=start+70,finished_monotonic_ns=start+85,group_verification=final)
            groups.append(dict(command=command,process_group=pid,exit_status=0,observations=[observation],cleanup=cleanup))
            intervals.append(dict(command=command,started_monotonic_ns=start,finished_monotonic_ns=finish))
        proof={'groups':groups}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'groups.json';path.write_text(json.dumps(proof));gate.check_groups(path,commands,intervals)
            mutations=[lambda g:g.pop(),lambda g:g[1].update(exit_status=True),
                       lambda g:g[2]['cleanup'].update(group_exit_known=False),
                       lambda g:g[0]['cleanup']['group_verification'].update(monotonic_ns=69),
                       lambda g:g[1]['observations'][0].update(monotonic_ns=99),
                       lambda g:g[0]['observations'][0].update(rss_kib=40*1024*1024+1),
                       lambda g:g[0].update(observations=[dict(validation='unavailable',process_group=100,monotonic_ns=x)
                                                          for x in (10,20,30)])]
            for mutation in mutations:
                changed=copy.deepcopy(groups);mutation(changed);path.write_text(json.dumps({'groups':changed}))
                with self.assertRaises(ValueError):gate.check_groups(path,commands,intervals)
            path.write_text(json.dumps(proof));late=copy.deepcopy(intervals);late[2]['finished_monotonic_ns']=late[2]['started_monotonic_ns']+300*10**9+1
            with self.assertRaisesRegex(ValueError,'deadline'):gate.check_groups(path,commands,late)

if __name__=='__main__':unittest.main(verbosity=2)
