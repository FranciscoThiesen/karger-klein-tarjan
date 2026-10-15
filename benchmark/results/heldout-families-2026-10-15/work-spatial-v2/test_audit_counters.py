#!/usr/bin/env python3
"""Focused pure-Python arithmetic/schema gates for the supplementary audit."""
import copy
import csv
import tempfile
from pathlib import Path
import unittest
import audit_counters as audit


class Tests(unittest.TestCase):
    def fixture(self):
        fields = audit.field_names()
        spec = dict(variant='compressed',case_id='synthetic',family='line_metric',n=4,m=6,density=1,
                    intrusion_per_mille=0,graph_seed=9000011,kkt_seed=2003,input_fingerprint=1,topology_fingerprint=2)
        raw = dict(certified_output_items=3,algorithms={},rounds={})
        for name in audit.ALGORITHMS:
            stats = dict.fromkeys(fields,0)
            stats['hash_insert_items'] = 3 if name == 'kkt' else None
            raw['algorithms'][name] = dict(hash_insert_items_status='measured' if name == 'kkt' else 'unmeasured',work=stats)
            if name == 'kkt':
                stats.update(verifier_queries=4,path_query_visits=10,verifier_tree_edges=9,verifier_tree_calls=1,fbt_output_vertices=7)
            else:
                stats.update(contraction_calls=1,contraction_vertices=4,contraction_edges=6,contraction_edge_visits=6)
                raw['rounds'][name] = [dict(round=0,vertices=4,edges=6,selected=3,output_vertices=0,output_edges=0)]
        return spec,raw,fields

    def test_exact_queries_zero_and_bounds(self):
        spec,raw,fields = self.fixture()
        tables,exact = audit.reconstruct([(spec,raw)],fields)
        row = tables['query_work'][0]
        self.assertEqual((row['Q'],row['U'],row['collapsed_requests'],row['U_over_Q']),(4,2,2,.5))
        self.assertEqual(next((r['numerator'],r['denominator']) for r in exact if r['quantity']=='U'),(1,3))
        work = raw['algorithms']['kkt']['work']
        for visits in (7,13):
            work['path_query_visits'] = visits
            with self.assertRaises(ValueError): audit.reconstruct([(spec,raw)],fields)
        work.update(verifier_queries=0,path_query_visits=0)
        zero = audit.reconstruct([(spec,raw)],fields)[0]['query_work'][0]
        self.assertIsNone(zero['U_over_Q']); self.assertEqual(zero['query_fraction_status'],'both_zero')

    def test_rounds_and_65_counter_domains(self):
        spec,raw,fields = self.fixture()
        for field in fields:
            changed = copy.deepcopy(raw); changed['algorithms']['kkt']['work'][field] = True
            with self.assertRaises(ValueError): audit.reconstruct([(spec,changed)],fields)
        for field,value in (('selected',2),('edges',7),('round',1),('output_vertices',1)):
            changed = copy.deepcopy(raw); changed['rounds']['multigraph_boruvka'][0][field] = value
            with self.assertRaises(ValueError): audit.reconstruct([(spec,changed)],fields)
        changed = copy.deepcopy(raw); changed['algorithms']['compacting_boruvka']['work']['hash_insert_items'] = 0
        with self.assertRaises(ValueError): audit.reconstruct([(spec,changed)],fields)

    def test_every_counter_table_cell_and_order(self):
        spec,raw,fields = self.fixture(); tables,_ = audit.reconstruct([(spec,raw)],fields)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'table.csv'
            def write(rows):
                with path.open('w',newline='') as stream:
                    writer = csv.DictWriter(stream,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
            for expected in tables.values():
                write(expected); audit.check_table(path,expected)
            expected = tables['work']
            for field in fields:
                changed = copy.deepcopy(expected); changed[0][field] += 1
                write(changed)
                with self.assertRaises(ValueError): audit.check_table(path,expected)
            write(list(reversed(expected)))
            with self.assertRaises(ValueError): audit.check_table(path,expected)
            write(expected[:-1])
            with self.assertRaises(ValueError): audit.check_table(path,expected)

    def test_duplicate_nonfinite_and_csv_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'input'
            for text in ('{"a":1,"a":2}','{"a":NaN}','{"a":Infinity}'):
                path.write_text(text)
                with self.assertRaises(ValueError): audit.read_json(path)
            path.write_text('a,a\n1,1\n')
            with self.assertRaises(ValueError): audit.check_table(path,[{'a':1}])


if __name__ == '__main__': unittest.main(verbosity=2)
