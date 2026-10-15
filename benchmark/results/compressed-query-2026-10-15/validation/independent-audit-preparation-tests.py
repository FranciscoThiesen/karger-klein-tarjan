#!/usr/bin/env python3
"""Synthetic checks of the standalone audit; no collector or native imports.

These check arithmetic, domains, table comparison and crossover predicates.
They do not substitute for a post-capture raw provenance/certificate audit.
"""
import copy
import csv
from fractions import Fraction
import importlib.util
from pathlib import Path
import tempfile
import unittest

PATH = Path(__file__).with_name('independent_numerical_audit.py')
SPEC = importlib.util.spec_from_file_location('compressed_independent_audit', PATH)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def fixture():
    specs, rows = {}, []
    for c, (family, n, density, intrusion) in enumerate(sorted(audit.EXPECTED_CASES)):
        case = f'{family}_n{n}_d{density}_p{intrusion}'
        spec = dict(case_id=case, family=family, n=n, m=n*density,
                    density=density, intrusion_per_mille=intrusion)
        specs[case] = spec
        for v, variant in enumerate(('reference', 'compressed')):
            for g, graph in enumerate((8000009, 8000023)):
                for phase, repeats in (('warmup', 1), ('timed', 6)):
                    for rep in range(repeats):
                        for order in range(6):
                            a = (order + rep) % 6
                            wall = 100003 + 1009*c + 307*g + 103*rep + 41*a + v*(503 + 11*a + 7*rep*a)
                            cpu = 70001 + 701*c + 211*g + 79*rep + 23*a + v*(307 + 13*a + 3*rep*a)
                            rows.append(dict(variant=variant, **spec, graph_seed=graph,
                                kkt_seed=1801, phase=phase, repetition=rep, order=order,
                                algorithm=audit.ALGORITHMS[a], elapsed_ns=wall,
                                process_cpu_elapsed_ns=cpu, input_fingerprint=17+c,
                                topology_fingerprint=29+c, validation='pass'))
    return specs, rows


def median(values):
    values = sorted(values)
    assert len(values) in (6, 12)
    return (values[len(values)//2-1] + values[len(values)//2]) / 2


class IndependentAuditTests(unittest.TestCase):
    def test_complete_independent_ratios_and_single_sampler_summaries(self):
        specs, rows = fixture()
        self.assertEqual((len(rows), sum(r['phase']=='timed' for r in rows)), (1008, 864))
        tables, points, brackets = audit.numerical_tables(rows, specs)
        self.assertEqual({k:len(v) for k,v in tables.items()}, audit.TABLE_COUNTS)
        self.assertEqual((len(points), len(brackets)), (60, 30))
        raw = {(r['variant'], r['case_id'], r['graph_seed'], r['repetition'], r['algorithm']):r
               for r in rows if r['phase']=='timed'}
        expected_across, expected_within = {}, {}
        groups_across, groups_within = {}, {}
        for case in specs:
            for graph in (8000009, 8000023):
                for rep in range(6):
                    for metric, field in (('wall','elapsed_ns'), ('cpu','process_cpu_elapsed_ns')):
                        for algorithm in audit.ALGORITHMS:
                            value = Fraction(raw['compressed',case,graph,rep,algorithm][field],
                                             raw['reference',case,graph,rep,algorithm][field])
                            expected_across[case,graph,1801,rep,algorithm,metric] = value
                            groups_across.setdefault((case,algorithm,metric,graph), []).append(value)
                        for variant in ('reference','compressed'):
                            for competitor in audit.ALGORITHMS[1:]:
                                value = Fraction(raw[variant,case,graph,rep,'kkt'][field],
                                                 raw[variant,case,graph,rep,competitor][field])
                                expected_within[variant,case,graph,1801,rep,competitor,metric] = value
                                groups_within.setdefault((variant,case,competitor,metric,graph), []).append(value)
        for name, fields, ratio, expected in (
            ('variant_pairs', ('case_id','graph_seed','kkt_seed','repetition','algorithm','metric'),
             'compressed_over_reference', expected_across),
            ('paired_ratios', ('variant','case_id','graph_seed','kkt_seed','repetition','competitor','metric'),
             'kkt_over_competitor', expected_within)):
            actual = {tuple(row[k] for k in fields):row[ratio] for row in tables[name]}
            self.assertEqual(len(actual), len(tables[name]))
            self.assertEqual(actual, expected)
        for name, fields, groups in (
            ('variant_comparisons', ('case_id','algorithm','metric'), groups_across),
            ('comparisons', ('variant','case_id','competitor','metric'), groups_within)):
            for row in tables[name]:
                key = tuple(row[k] for k in fields)
                expected = groups[(*key,8000009)] + groups[(*key,8000023)]
                self.assertEqual(row['median_paired_ratio'], median(expected))
                self.assertEqual(row['trials'], 12)
            for row in tables['graph_'+name]:
                key = tuple(row[k] for k in fields)
                self.assertEqual(row['median_paired_ratio'], median(groups[(*key,row['graph_seed'])]))
                self.assertEqual(row['trials'], 6)
            pooled = {tuple(row[k] for k in fields):row['median_paired_ratio'] for row in tables[name]}
            for row in tables['sampling_'+name]:
                self.assertEqual(row['kkt_seed'], 1801)
                self.assertEqual(row['trials'], 12)
                self.assertEqual(row['median_paired_ratio'], pooled[tuple(row[k] for k in fields)])
        self.assertEqual(sum(len(v) for name,v in tables.items()
            if name not in ('paired_ratios','variant_pairs','strong_crossover_classifications')), 2016)

    def test_exact_thresholds_and_both_clocks_graphs(self):
        specs, rows = fixture(); original = audit.numerical_tables(rows,specs)[0]
        def target(row):
            return (row['variant'],row['family'],row['competitor']) == ('compressed','leaf_hierarchy4','multigraph_boruvka')
        for kind, expected in (('strong',True),('large_epsilon',False),('small_tie',False),('one_graph',False)):
            tables = copy.deepcopy(original)
            for row in tables['realization_comparisons']:
                if not target(row): continue
                small = row['n']==65536
                value = Fraction(11,10) if small else Fraction(9,10)
                if kind=='large_epsilon' and not small and row['metric']=='cpu': value += Fraction(1,10**18)
                if kind=='small_tie' and small: value=Fraction(1)
                if kind=='one_graph' and not small and row['graph_seed']==8000023: value=Fraction(11,10)
                row['median_paired_ratio']=value
            result=audit.crossovers(tables,specs)[0]
            selected=[row for row in result if target(row)]
            self.assertEqual(len(selected),1)
            self.assertEqual(selected[0]['strong_crossover'],expected,kind)

    def test_duplicate_missing_or_foreign_realizations_reject(self):
        specs, rows=fixture()
        for mode in ('duplicate','missing','sampler'):
            changed=copy.deepcopy(rows)
            index=next(i for i,row in enumerate(changed) if row['phase']=='timed')
            if mode=='duplicate': changed.append(copy.deepcopy(changed[index]))
            elif mode=='missing': changed.pop(index)
            else: changed[index]['kkt_seed']=1803
            with self.subTest(mode=mode), self.assertRaises(ValueError): audit.numerical_tables(changed,specs)

    def test_unsigned_clock_domains_and_explicit_utc(self):
        self.assertEqual(audit.native_integer(str(2**63-1),'elapsed_ns'),2**63-1)
        self.assertEqual(audit.native_integer(str(2**64-1),'input_fingerprint'),2**64-1)
        for value in ('-1','+1',' 1','1.0','١','',str(2**63)):
            with self.subTest(value=value), self.assertRaises(ValueError): audit.native_integer(value,'process_cpu_start_ns')
        audit.parse_utc('2026-10-15T00:00:00+00:00')
        for value in ('2026-10-15T00:00:00','2026-10-15T00:00:00+01:00'):
            with self.assertRaises(ValueError): audit.parse_utc(value)

    def test_table_values_and_duplicate_identity_reject(self):
        specs,rows=fixture(); tables=audit.numerical_tables(rows,specs)[0]
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)
            for name,values in tables.items():
                plain=[{key:float(value) if isinstance(value,Fraction) else value for key,value in row.items()}
                       for row in values]
                audit.write_csv(directory,name,plain)
                audit.verify_table(directory/(name+'.csv'),values,audit.table_keys(name))
            name='variant_pairs'; path=directory/(name+'.csv')
            values=audit.read_csv(path); values[-1]=dict(values[0])
            with path.open('w',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=list(values[0])); writer.writeheader(); writer.writerows(values)
            audit.INPUTS.pop(str(path.resolve()))
            with self.assertRaisesRegex(ValueError,'duplicate/foreign'): audit.verify_table(path,tables[name],audit.table_keys(name))


if __name__=='__main__': unittest.main(verbosity=2)
