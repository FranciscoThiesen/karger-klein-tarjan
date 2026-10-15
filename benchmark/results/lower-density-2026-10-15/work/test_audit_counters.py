#!/usr/bin/env python3
"""Focused pure-Python lower-density counter gates; no native proof or launch."""
import copy
import csv
from fractions import Fraction
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import audit_counters as audit


class Tests(unittest.TestCase):
    def fixtures(self):
        fields = audit.field_names()
        values = []
        for identity in audit.declared():
            spec = dict(identity,input_fingerprint=identity['n']*10+identity['density']+identity['graph_seed']+
                        100+(identity['family']=='leaf_shuffled4'),
                        topology_fingerprint=identity['n']*10+identity['density']+identity['graph_seed'])
            n,m = spec['n'],spec['m']; q=n//4; v=n//8; r=m-3*n//4; e=m-7*n//8
            rounds = [dict(round=0,vertices=n,edges=m,selected=n-q,output_vertices=q,output_edges=r),
                      dict(round=1,vertices=q,edges=r,selected=q-v,output_vertices=v,output_edges=e),
                      dict(round=2,vertices=v,edges=e,selected=v-1,output_vertices=0,output_edges=0)]
            raw = {key:value for key,value in spec.items() if key not in ('variant','intrusion_per_mille')}
            raw.update(schema='retention_control_work_v1',validation='pass',certified_output_items=n-1,
                       algorithms={},rounds={})
            for name in audit.ALGORITHMS:
                stats = dict.fromkeys(fields,0)
                stats.update(contraction_calls=3,contraction_vertices=n+q+v,contraction_edges=m+r+e,
                             contraction_edge_visits=3*(m+r+e),contraction_output_vertices=q+v,
                             contraction_output_edges=r+e,hash_insert_items=n-1 if name=='kkt' else None)
                if name == 'kkt':
                    Q = 0 if n == 256 else 6
                    stats.update(root_after_two_vertices=v,root_after_two_edges=e,sampling_calls=1,
                        verifier_calls=1,sampling_edge_visits=e,verifier_edges=e,sampled_edges=e//8,
                        verifier_queries=Q,path_query_visits=2*Q+Q//3,verifier_tree_edges=9,
                        verifier_tree_calls=1,fbt_output_vertices=7)
                else: raw['rounds'][name] = copy.deepcopy(rounds)
                raw['algorithms'][name] = dict(work=stats,hash_insert_items_status='measured' if name=='kkt' else 'unmeasured')
            values.append((spec,raw))
        return fields,values

    def test_complete_schedule_and_every_exact_normalization(self):
        fields,values = self.fixtures()
        self.assertEqual(audit.validate_matrix([s for s,_ in values],values),30)
        tables = audit.reconstruct(values,fields)
        self.assertEqual({name:len(rows) for name,rows in tables.items()},
                         dict(work=180,rounds=360,round_chains=120,query_work=60,normalized_work=11700))
        expected = {}
        for spec,raw in values:
            for algorithm,data in raw['algorithms'].items():
                for field,count in data['work'].items():
                    identity = spec['case_id'],spec['graph_seed'],algorithm,field
                    expected[identity] = count,Fraction(count,spec['m']) if count is not None else None
        seen = set(); nulls = zeros = 0
        for row in tables['normalized_work']:
            identity = row['case_id'],row['graph_seed'],row['algorithm'],row['counter']
            self.assertNotIn(identity,seen); seen.add(identity)
            count,fraction = expected[identity]
            self.assertEqual(row['count'],count)
            if fraction is None:
                nulls += 1
                self.assertEqual((row['status'],row['numerator'],row['denominator'],row['per_original_edge']),
                                 ('unmeasured',None,None,None))
            else:
                zeros += fraction == 0
                self.assertEqual((row['status'],row['numerator'],row['denominator'],row['per_original_edge']),
                                 ('defined',fraction.numerator,fraction.denominator,float(fraction)))
        self.assertEqual((len(seen),nulls),(11700,120)); self.assertGreater(zeros,0)
        for row in tables['query_work']:
            self.assertEqual(row['engine_words'],row['sampling_edge_visits'])
            self.assertEqual((row['U'],row['collapsed_requests']),(row['Q']//3,2*row['Q']//3))
            self.assertEqual(row['U_over_Q'],1/3 if row['Q'] else None)
        self.assertTrue(any(row['query_fraction_status']=='both_zero' for row in tables['query_work']))
        self.assertTrue(all(row['selected_sum']==row['n']-1 and row['rounds']==3 for row in tables['round_chains']))

    def test_literal_identity_twins_types_and_changed_root(self):
        fields,values = self.fixtures(); specs = [s for s,_ in values]
        for changed in (values[:-1],values[:-1]+[values[0]],list(reversed(values))):
            with self.assertRaises(ValueError):audit.validate_matrix([s for s,_ in changed],changed)
        for field,new_value in (('density',8),('graph_seed',1),('kkt_seed',True),('m',1),('variant','half')):
            changed=copy.deepcopy(values); changed[0][0][field]=new_value
            with self.assertRaises(ValueError):audit.validate_matrix([s for s,_ in changed],changed)
        for field in ('topology_fingerprint','input_fingerprint'):
            changed=copy.deepcopy(values)
            value=changed[0][1][field]+(1 if field=='topology_fingerprint' else 0)
            changed[1][0][field]=value;changed[1][1][field]=value
            with self.assertRaisesRegex(ValueError,'twin'):audit.validate_matrix([s for s,_ in changed],changed)
        changed=copy.deepcopy(values);changed[0][1]['n']=float(changed[0][1]['n'])
        with self.assertRaisesRegex(ValueError,'raw input'):audit.validate_matrix(specs,changed)
        changed=copy.deepcopy(values[:1]);changed[0][1]['algorithms']['kkt']['work']['root_after_two_edges']-=1
        with self.assertRaisesRegex(ValueError,'root'):audit.reconstruct(changed,fields)

    def test_all_counter_domains_nulls_replay_queries_and_sampling(self):
        fields,values = self.fixtures(); spec,raw=values[0]
        for field in fields:
            changed=copy.deepcopy(raw);changed['algorithms']['kkt']['work'][field]=True
            with self.assertRaises(ValueError):audit.reconstruct([(spec,changed)],fields)
        for number in (-1,2**64):
            changed=copy.deepcopy(raw);changed['algorithms']['kkt']['work']['initialized_slots']=number
            with self.assertRaises(ValueError):audit.reconstruct([(spec,changed)],fields)
        for key,value in (('selected',0),('edges',1),('round',3),('output_vertices',0)):
            changed=copy.deepcopy(raw);changed['rounds']['multigraph_boruvka'][0][key]=value
            with self.assertRaises(ValueError):audit.reconstruct([(spec,changed)],fields)
        for key,value in (('path_query_visits',11),('path_query_visits',19),('sampled_edges',2**32),
                          ('sampling_calls',0),('current_depth',1),('hash_insert_items',0)):
            changed=copy.deepcopy(raw);changed['algorithms']['kkt']['work'][key]=value
            with self.assertRaises(ValueError):audit.reconstruct([(spec,changed)],fields)
        changed=copy.deepcopy(raw);changed['algorithms']['compacting_boruvka']['work']['hash_insert_items']=0
        with self.assertRaises(ValueError):audit.reconstruct([(spec,changed)],fields)
        changed=copy.deepcopy(raw);changed['algorithms']['kkt']['work'].pop(fields[0])
        with self.assertRaises(ValueError):audit.reconstruct([(spec,changed)],fields)

    def test_every_table_value_order_schema_and_input_hash(self):
        fields,values=self.fixtures();tables=audit.reconstruct(values[:1],fields)
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'table.csv'
            def write(rows):
                with path.open('w',newline='') as stream:
                    writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
            for rows in tables.values():write(rows);audit.check_table(path,rows)
            for field in fields:
                changed=copy.deepcopy(tables['work']);changed[0][field]+=1
                write(changed)
                with self.assertRaises(ValueError):audit.check_table(path,tables['work'])
            for name,field in (('normalized_work','numerator'),('round_chains','selected_sum'),('query_work','engine_words')):
                changed=copy.deepcopy(tables[name]);changed[0][field]+=1
                write(changed)
                with self.assertRaises(ValueError):audit.check_table(path,tables[name])
            for changed in (tables['work'][:-1],list(reversed(tables['work']))):
                write(changed)
                with self.assertRaises(ValueError):audit.check_table(path,tables['work'])
            path.write_text('a,a\n1,1\n')
            with self.assertRaises(ValueError):audit.check_table(path,[{'a':1}])
            for text in ('{"a":1,"a":2}','{"a":NaN}','{"a":1e999}'):
                path.write_text(text)
                with self.assertRaises(ValueError):audit.read_json(path)
            path.write_text('initial');bound={};audit.bind(bound,path);path.write_text('drift')
            with self.assertRaises(ValueError):audit.bind(bound,path)

    def test_strict_provenance_import_path_restored_on_success_and_failure(self):
        before=sys.path[:]; sentinel=object()
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary);capture=directory/'capture.json'
            sibling=directory/'audit_test_sibling.py';sibling.write_text('VALUE=17\n')
            collector=directory/'collect.py'
            for source in ('from audit_test_sibling import VALUE\ndef load(path): return ({"value":VALUE},[])\n',
                           'def load(path): raise ValueError("synthetic strict load failed")\n',
                           'raise ValueError("synthetic import failed")\n'):
                collector.write_text(source)
                with mock.patch.object(audit,'HERE',directory),mock.patch.dict(sys.modules,
                        {'_lower_density_counter_audit_provenance':sentinel}):
                    if source.startswith('from'):
                        self.assertEqual(audit.provenance_load(capture),{'value':17})
                    else:
                        with self.assertRaisesRegex(ValueError,'synthetic'):audit.provenance_load(capture)
                    self.assertEqual(sys.path,before)
                    self.assertIs(sys.modules['_lower_density_counter_audit_provenance'],sentinel)


if __name__=='__main__':unittest.main(verbosity=2)
