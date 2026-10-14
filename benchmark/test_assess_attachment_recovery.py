#!/usr/bin/env python3
"""Bounded stdlib recovery gates; reads retained evidence, launches no native work."""
import argparse
import copy
import itertools
import json
from pathlib import Path
import unittest
from unittest import mock

import analyze_mst_search as analysis
import assess_attachment_composite as composite
import assess_attachment_confirmation as rule
import assess_attachment_recovery as recovery
import audit_mst_search_power as power

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/"benchmark/results/search-2026-10-13"


class PrefixEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid=recovery.prefix_evidence(ROOT,FOLDER)

    def changed(self,mutator):
        original=recovery.read_json
        def read(path):
            value=original(path)
            if path.name=="attachment-confirmation-b-timing.json":
                value=copy.deepcopy(value);mutator(value)
            return value
        with mock.patch.object(recovery,"read_json",read):
            with self.assertRaises((ValueError,KeyError,TypeError)):
                recovery.prefix_evidence(ROOT,FOLDER)

    def test_exact_completed_native_prefix_including_unfinalized_child(self):
        data=self.valid
        self.assertEqual((len(data["rows"]),len(data["certificates"])),(1800,60))
        self.assertEqual(data["certificates"][-1]["original_wrapper_validation"],"not_finalized")
        self.assertEqual(data["certificates"][-1]["native_exit_status"],0)
        self.assertEqual(data["info"]["validation"],"failed")
        self.assertTrue(any(row["diagnostic_flags"] for row in data["diagnostics"]))
        self.assertTrue(all(row["excluded"] is False for row in data["diagnostics"]))
        self.assertEqual(len({row["case_id"] for row in data["rows"]}),10)

    def test_reject_incomplete_failed_unknown_or_relabelled_native_evidence(self):
        mutations={
            "capture falsely successful":lambda x:x.update(validation="pass"),
            "missing native child":lambda x:x["captures"].pop(),
            "nonzero native exit":lambda x:x["captures"][-1].update(exit_status=1),
            "unknown native exit":lambda x:x["captures"][-1].update(exit_status=None),
            "unknown running child":lambda x:x["captures"][-1].update(native_process_may_still_be_running=True),
            "wrong final seed":lambda x:x["captures"][-1].update(kkt_seed=401),
            "forged wrapper pass":lambda x:x["captures"][-1].update(validation="pass"),
            "lost wrapper interruption":lambda x:x["captures"][-1].update(interruption=None),
            "wrong recorded certificate":lambda x:x["captures"][0]["certificate"].update(input_fingerprint=1),
            "missing clock diagnostic":lambda x:x["call_diagnostics"].pop(),
            "source inventory drift":lambda x:x["source_sha256"].update({"kkt/kkt.cpp":"0"*64}),
            "overlapping child interval":lambda x:x["captures"][1].update(started_monotonic_ns=x["captures"][0]["started_monotonic_ns"]),
        }
        for name,mutate in mutations.items():
            with self.subTest(name=name):self.changed(mutate)

    def test_original_combined_prefix_mismatch_is_not_silently_accepted(self):
        original=rule.read_csv
        for kind in ("added child60","removed child59"):
            def read(path,fields=None):
                values=original(path,fields)
                if path.name=="attachment-confirmation-b-timing.csv":
                    values=(values+recovery.serialized(self.valid["rows"][-30:]) if kind=="added child60" else values[:-30])
                return values
            with self.subTest(kind=kind),mock.patch.object(rule,"read_csv",read):
                with self.assertRaises(ValueError):recovery.prefix_evidence(ROOT,FOLDER)

    def test_old_strict_loader_still_rejects_original_failed_b(self):
        with self.assertRaisesRegex(ValueError,"validation"):
            analysis.load(FOLDER/"attachment-confirmation-b-timing.csv")


class PowerTransitions(unittest.TestCase):
    def test_wake_requests_do_not_end_logged_sleep(self):
        text="\n".join((
            "2026-10-14 00:00:00 +0000 Sleep Entering Sleep state due to 'Clamshell Sleep' 803 secs",
            "2026-10-14 00:00:01 +0000 Wake Requests [process=example request=Maintenance]",
            "2026-10-14 00:13:23 +0000 Wake Wake from Deep Idle",
            "2026-10-14 00:15:00 +0000 Sleep Entering Sleep state 9 secs",
            "2026-10-14 00:15:09 +0000 DarkWake DarkWake from Deep Idle"))
        events,malformed,reversals,requests=recovery.transition_events(text)
        self.assertFalse(malformed);self.assertFalse(reversals);self.assertEqual(len(requests),1)
        intervals=power.sleep_intervals(events)
        self.assertEqual((intervals[0]["end_ns"]-intervals[0]["start_ns"])/1e9,803)
        self.assertEqual(intervals[1]["end_event"],"DarkWake")


class CompositeArithmetic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected,cls.plans=rule.frozen_plans(ROOT,FOLDER,{})
        _,_,cls.rows,cls.diagnostics,_,_=analysis.load(FOLDER/"attachment-confirmation-a-timing.csv")

    def sample(self):
        rows=copy.deepcopy(self.rows)
        # Distinct nested result: repetition -> sample -> graph = 3.5;
        # flattening all 30 trials gives 4.0. Some actual high-delay and
        # flagged source calls remain identifiable; no result is discarded.
        bank=(((1,1,1,100,100),(2,2,2,2,2)),((3,3,3,3,3),(4,4,4,4,4)),((5,5,5,5,5),(6,6,6,6,6)))
        for row in rows:
            if row["phase"]!="timed":continue
            factor=bank[rule.GRAPHS.index(row["graph_seed"])][rule.SAMPLES.index(row["kkt_seed"])][row["repetition"]]
            for field in ("elapsed_ns","process_cpu_elapsed_ns"):
                row[field]=1000*factor if row["algorithm"]=="kkt" else 1000
        return rows

    def test_known_nested_medians_retain_controls_and_all_clocks(self):
        rows=self.sample()
        result=composite.records(rows,self.diagnostics,"b",self.plans["a"],self.expected)
        self.assertEqual((len(result["cases"]),len(result["graphs"]),len(result["pairs"])),(96,288,2880))
        self.assertTrue(all(row["median_paired_ratio"]==3.5 for row in result["cases"]))
        self.assertEqual({row["median_paired_ratio"] for row in result["graphs"]},{1.5,3.5,5.5})
        self.assertEqual(len(result["diagnostics"]),2160)
        self.assertTrue(set(rule.CONTROLS)<={row["family"] for row in result["cases"]})
        composite.check_tables(result,analysis.aggregate(rows))

    def test_flattened_recomputed_tables_fail(self):
        rows=self.sample();result=composite.records(rows,self.diagnostics,"b",self.plans["a"],self.expected)
        tables=analysis.aggregate(rows);tables["comparisons"][0]["median_paired_ratio"]=4.0
        with self.assertRaises(ValueError):composite.check_tables(result,tables)

    def test_incomplete_duplicate_failed_dimension_or_missing_clock_call_fails(self):
        for change in (lambda rows:rows.pop(),lambda rows:rows.append(rows[-1]),
                       lambda rows:rows[0].update(validation="fail"),lambda rows:rows[0].update(m=1)):
            rows=copy.deepcopy(self.rows);change(rows)
            with self.assertRaises((ValueError,KeyError)):
                composite.records(rows,self.diagnostics,"b",self.plans["a"],self.expected)
        with self.assertRaises(ValueError):composite.records(self.rows,self.diagnostics[:-1],"b",self.plans["a"],self.expected)

    def test_disjoint_explicit_source_parts_and_original_positions(self):
        parts=[{**{k:r[k] for k in recovery.ROW_KEY},"source_part":"interrupted_prefix" if i<1800 else "recovery_tail",
                "original_child_index":i//30+1} for i,r in enumerate(self.rows)]
        composite.check_parts(parts,self.rows)
        for mutation in (lambda p:p[1800].update(source_part="interrupted_prefix"),
                         lambda p:p[1800].update(original_child_index=60),lambda p:p.pop()):
            changed=copy.deepcopy(parts);mutation(changed)
            with self.assertRaises(ValueError):composite.check_parts(changed,self.rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--json-report",type=Path,required=True)
    args=parser.parse_args();rule.require(not args.json_report.exists(),"refusing to overwrite test evidence")
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls) for cls in (PrefixEvidence,PowerTransitions,CompositeArithmetic))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={"validation":"pass" if result.wasSuccessful() else "fail","tests_run":result.testsRun,
            "failures":len(result.failures),"errors":len(result.errors),"native_solver_launches":0,
            "source_sha256":{str(Path(module.__file__).resolve()):rule.sha(module.__file__) for module in (recovery,composite,rule)},
            "test_sha256":rule.sha(__file__),"evidence":"retained failed prefix plus complete A; synthetic semantic mutations; no fabricated tail capture"}
    args.json_report.write_text(json.dumps(report,indent=2)+"\n")
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__=="__main__":main()
