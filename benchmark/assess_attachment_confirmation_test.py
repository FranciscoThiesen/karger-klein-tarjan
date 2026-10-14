#!/usr/bin/env python3
"""Unexecuted source draft. Run only after BOTH native captures are released.

Standard-library semantic tests for the postprocessor, not native certificates.
The synthetic archive models the already-validated analyzer's output contract.
Its known asymmetric observations distinguish nested from flattened medians.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import importlib.util
import io
import itertools
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


S = None  # Loaded only by main after explicit post-capture release.
FAMILIES = ("leaf_hierarchy4", "leaf_distance4")
CONTROLS = ("leaf_shuffled4", "leaf_random4")
SIZES = (65536, 262144, 524288, 1048576, 2097152)
GRAPHS = (1000039, 1000081, 1000099)
SAMPLES = (401, 503)
COMPETITORS = ("compacting_boruvka", "kruskal", "prim", "boruvka")
ALGOS = ("kkt", *COMPETITORS)


def specification(family, n):
    return {"case_id": f"{family}_n{n}_d16_p0", "family": family,
            "n": n, "m": n*16, "density": 16, "intrusion_per_mille": 0}


def expected_cases():
    specs = [specification(f, n) for f, n in itertools.product(FAMILIES, SIZES)]
    specs += [specification(f, SIZES[-1]) for f in CONTROLS]
    return {s["case_id"]: s for s in specs}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+"\n")


def table(path, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def curve_campaigns():
    """All upper-size checks pass, but there is deliberately no onset."""
    expected = expected_cases()
    return [{"campaign": name, "cases": [
        {"campaign": name, **spec, "metric": metric, "competitor": comp,
         "median_paired_ratio": .8, "graph_max_ratio": .95}
        for spec, metric, comp in itertools.product(expected.values(), ("wall", "cpu"), COMPETITORS)]}
        for name in ("a", "b")]


def curve_row(campaigns, campaign, family, n, metric, competitor):
    return next(row for c in campaigns if c["campaign"] == campaign for row in c["cases"]
                if (row["family"], row["n"], row["metric"], row["competitor"])
                == (family, n, metric, competitor))


def verdict(campaigns, family=FAMILIES[0], competitor=COMPETITORS[0]):
    return next(row for row in S.assess(campaigns)
                if row["family"] == family and row["competitor"] == competitor)


class CriterionTests(unittest.TestCase):
    def test_upper_rule_and_onset_are_separate(self):
        result = S.assess(curve_campaigns())
        self.assertEqual(len(result), 8)
        for row in result:
            self.assertTrue(row["declared_upper_size_advantage_pass"])
            self.assertEqual(len(row["upper_checks"]), 8)
            self.assertFalse(row["smaller_loss_or_tie_in_each_campaign_and_clock"])
            self.assertFalse(row["observed_parity_crossing_in_each_campaign_and_clock"])

    def test_every_family_comparator_upper_size_campaign_and_clock_can_fail(self):
        # Each changed observation invalidates exactly its own family/comparator.
        for family, comp, campaign, metric, n in itertools.product(
                FAMILIES, COMPETITORS, ("a", "b"), ("wall", "cpu"), SIZES[-2:]):
            with self.subTest(family=family, comp=comp, campaign=campaign, metric=metric, n=n):
                data = curve_campaigns()
                curve_row(data, campaign, family, n, metric, comp)["median_paired_ratio"] = .900000001
                results = S.assess(data)
                failed = [(r["family"],r["competitor"]) for r in results
                          if not r["declared_upper_size_advantage_pass"]]
                self.assertEqual(failed, [(family,comp)])

    def test_inclusive_case_threshold_but_strict_graph_threshold(self):
        data = curve_campaigns()
        row = curve_row(data, "b", FAMILIES[0], SIZES[-1], "cpu", COMPETITORS[0])
        row.update(median_paired_ratio=.9, graph_max_ratio=.999999999)
        self.assertTrue(verdict(data)["declared_upper_size_advantage_pass"])
        row["graph_max_ratio"] = 1.0
        self.assertFalse(verdict(data)["declared_upper_size_advantage_pass"])

    def test_every_graph_gate_is_required_without_pooling(self):
        for campaign, metric, n in itertools.product(("a","b"), ("wall","cpu"), SIZES[-2:]):
            with self.subTest(campaign=campaign,metric=metric,n=n):
                data = curve_campaigns()
                curve_row(data,campaign,FAMILIES[0],n,metric,COMPETITORS[0])["graph_max_ratio"] = 1.001
                self.assertFalse(verdict(data)["declared_upper_size_advantage_pass"])

    def test_nonmonotone_onset_and_threshold_brackets_are_distinct(self):
        data = curve_campaigns()
        # Parity brackets: [65k,262k], [524k,1M]. The 10% boundary is only
        # [524k,1M]. Later equality .90 passes the upper-size rule.
        for campaign, metric in itertools.product(("a","b"),("wall","cpu")):
            for n, ratio in zip(SIZES, (1.0,.95,1.1,.9,.9)):
                curve_row(data,campaign,FAMILIES[0],n,metric,COMPETITORS[0]).update(
                    median_paired_ratio=ratio, graph_max_ratio=max(.95,ratio))
        result = verdict(data)
        self.assertTrue(result["declared_upper_size_advantage_pass"])
        self.assertTrue(result["smaller_loss_or_tie_in_each_campaign_and_clock"])
        for evidence in result["onset_evidence"]:
            self.assertEqual(evidence["smaller_loss_or_tie_sizes"], [65536,524288])
            self.assertEqual([(r["lower_n"],r["upper_n"]) for r in evidence["adjacent_parity_crossings"]],
                             [(65536,262144),(524288,1048576)])
            self.assertEqual([(r["lower_n"],r["upper_n"]) for r in evidence["adjacent_10_percent_threshold_crossings"]],
                             [(524288,1048576)])

    def test_bad_controls_are_retained_but_do_not_select_new_families(self):
        data = curve_campaigns()
        for campaign in data:
            for row in campaign["cases"]:
                if row["family"] in CONTROLS:
                    row.update(median_paired_ratio=7.0, graph_max_ratio=9.0)
        self.assertEqual(len(data[0]["cases"]), 96)
        self.assertTrue(all(r["declared_upper_size_advantage_pass"] for r in S.assess(data)))
        self.assertEqual({r["family"] for r in S.assess(data)}, set(FAMILIES))


class Archive:
    """Complete synthetic one-campaign archive, with explicit analytic medians.

    Graph 0: sample ratios [1,1,1,100,100] and [2,2,2,2,2], median 1.5.
    Graph 1: all3 and all4, median3.5. Graph2: all5 and all6, median5.5.
    Thus the nested case median is3.5, whereas flattening30 pairs gives4.
    No production aggregation helper generates these expected medians.
    """
    def __init__(self, root, campaign="a"):
        self.root = root
        self.folder = root/"benchmark/results/search-2026-10-13"
        self.folder.mkdir(parents=True, exist_ok=True)
        self.expected = expected_cases()
        self.order = list(self.expected)
        self.campaign = campaign
        if campaign == "b": self.order.reverse()
        self.stem = "attachment-confirmation-"+campaign
        self.analysis = self.folder/(self.stem+"-analysis")
        self.analysis.mkdir()
        self.raw = self.folder/(self.stem+"-timing.csv")
        self.power = self.folder/(self.stem+"-power-audit/audit.json")
        self.power.parent.mkdir()
        self.controller_path = self.folder/(self.stem+"-controller.json")
        self.controller_source = self.folder/"run_attachment_confirmation.py"
        self.controller_source.write_text("# synthetic retained controller\n")
        self.helper = root/"analyzer.py"
        self.helper.write_text("# synthetic validated analyzer output contract\n")
        self.source = root/"solver.cpp"; self.source.write_text("// synthetic source inventory\n")
        self.recipe = root/"Makefile"; self.recipe.write_text("# synthetic recipe\n")
        self.frozen = {}
        for name in ("ATTACHMENT_CONFIRMATION.md","attachment-confirmation-a.csv","attachment-confirmation-b.csv"):
            path = self.folder/name
            if name.endswith(".md"):
                path.write_text("Synthetic prospective protocol\n")
            else:
                specs = list(self.expected.values())
                if "-b.csv" in name: specs.reverse()
                table(path,[{k:s[k] for k in ("family","n","density","intrusion_per_mille")} for s in specs])
            self.frozen[path.relative_to(root).as_posix()] = path.read_bytes()
        calls,pairs,graphs,cases,diagnostics = [],[],[],[],[]
        patterns = (((1,1,1,100,100),(2,2,2,2,2)),
                    ((3,)*5,(4,)*5), ((5,)*5,(6,)*5))
        for case in self.order:
            spec = self.expected[case]
            case_index = list(self.expected).index(case)
            for gi,g in enumerate(GRAPHS):
                for si,s in enumerate(SAMPLES):
                    for phase,count in (("warmup",1),("timed",5)):
                        for rep in range(count):
                            for order in range(5):
                                algo = ALGOS[(order+rep)%5]
                                duration = 100*patterns[gi][si][rep] if algo=="kkt" else 100
                                row = {**spec,"graph_seed":g,"kkt_seed":s,
                                    "input_fingerprint":100000000+1000*case_index+g,
                                    "topology_fingerprint":100000000+1000*spec["n"]+g,
                                    "phase":phase,"repetition":rep,"order":order,"warmups":1,
                                    "algorithm":algo,"elapsed_ns":duration,"utc_start_ns":1000000,
                                    "utc_end_ns":1000000+duration,"process_cpu_start_ns":2000000,
                                    "process_cpu_end_ns":2000000+duration,"process_cpu_elapsed_ns":duration,
                                    "validation":"pass"}
                                calls.append(row)
                                diagnostics.append({k:row[k] for k in ("case_id","graph_seed","kkt_seed","phase","repetition","order","algorithm")})
                                diagnostics[-1].update(elapsed_ns=duration,process_cpu_elapsed_ns=duration,
                                    utc_elapsed_ns=duration,steady_minus_cpu_ns=0,utc_minus_steady_ns=0,
                                    diagnostic_flags="",excluded=False)
                    for metric,comp,rep in itertools.product(("wall","cpu"),COMPETITORS,range(5)):
                        ratio = patterns[gi][si][rep]
                        pairs.append({**spec,"metric":metric,"competitor":comp,"graph_seed":g,
                            "kkt_seed":s,"repetition":rep,"kkt_ns":100*ratio,"competitor_ns":100,
                            "kkt_over_competitor":float(ratio)})
                for metric,comp in itertools.product(("wall","cpu"),COMPETITORS):
                    graphs.append({**spec,"metric":metric,"competitor":comp,"graph_seed":g,
                        "median_paired_ratio":(1.5,3.5,5.5)[gi],"trial_min_ratio":(1.,3.,5.)[gi],
                        "trial_max_ratio":(100.,4.,6.)[gi],"individual_wins":0,
                        "individual_losses":(7,10,10)[gi],"individual_ties":(3,0,0)[gi],"pairs":10})
            for metric,comp in itertools.product(("wall","cpu"),COMPETITORS):
                cases.append({**spec,"metric":metric,"competitor":comp,"median_paired_ratio":3.5,
                    "graph_min_ratio":1.5,"graph_max_ratio":5.5,"trial_min_ratio":1.,"trial_max_ratio":100.,
                    "individual_wins":0,"individual_losses":27,"individual_ties":3,"graph_seeds":3,"pairs":30})
        # One retained flagged warmup with an explicitly observable UTC gap.
        diagnostics[0].update(utc_elapsed_ns=calls[0]["elapsed_ns"]+1000000000,
                              utc_minus_steady_ns=1000000000,diagnostic_flags="utc_steady_gap")
        calls[0]["utc_end_ns"] += 1000000000
        self.tables = {"validated_calls.csv":calls,"paired_ratios.csv":pairs,
                       "graph_comparisons.csv":graphs,"comparisons.csv":cases,"call_diagnostics.csv":diagnostics}
        self.meta = {"schema":"mst_search_capture_v1","validation":"pass","case_order":self.order,
            "graph_seeds":list(GRAPHS),"sampling_seeds":list(SAMPLES),"algorithms":list(ALGOS),
            "repetitions":5,"warmups":1,"checked_rows":2160,"checked_timed_rows":1800,
            "checked_warmup_rows":360,"rows_removed":0,"rows_adjusted":0,"captures":[{} for _ in range(72)],
            "flagged_calls":1,"capture_clock_flags":[{"kind":"synthetic_retained_utc_reversal"}],
            "binary_sha256":"a"*64,"binary_profile":{"stack_bytes":536870912},"profile":"synthetic",
            "source_sha256":{str(self.source):digest(self.source)},
            "python_source_sha256":{str(self.helper):digest(self.helper)},
            "build_recipe_sha256":{str(self.recipe):digest(self.recipe)}}
        self.provenance_changes = {}; self.controller_changes = {}
        self.power_data = {"validation":"pass","checked_calls":2160,"overlap_count":1}
        self.seal()

    def seal(self):
        for name,rows in self.tables.items(): table(self.analysis/name,rows)
        table(self.raw,self.tables["validated_calls.csv"])
        self.meta["output_sha256"] = digest(self.raw)
        dump(self.raw.with_suffix(".json"),self.meta); dump(self.power,self.power_data)
        bound = {str(path):digest(path) for path in (self.raw,self.raw.with_suffix(".json"),self.helper)}
        prov = {"schema":"mst_search_analysis_v1","validation":"pass","cases":12,
            "checked_rows":2160,"timed_rows":1800,"warmup_rows":360,"rows_removed":0,"rows_adjusted":0,
            "capture_metadata":{**copy.deepcopy(self.meta),"raw_csv":str(self.raw),"raw_csv_link":"../"+self.raw.name},
            "input_sha256":bound,"derived_sha256":{name:digest(self.analysis/name) for name in self.tables},
            "analysis_source_sha256":copy.deepcopy(self.meta["python_source_sha256"])}
        prov.update(self.provenance_changes); dump(self.analysis/"provenance.json",prov)
        retained = {str(path):digest(path) for path in (self.raw,self.raw.with_suffix(".json"),
                    self.analysis/"provenance.json",self.power)}
        control = {"schema":"attachment_confirmation_controller_v1","validation":"pass","campaign":self.stem,
            "capture_exit_status":0,"analysis_exit_status":0,"power_audit_exit_status":0,
            "power_audit_validation":"pass","retained_artifact_sha256":retained,"analysis_bound_sha256":bound,
            "controller_sha256":digest(self.controller_source),"frozen_declaration_revision":"d641ca8",
            "frozen_declaration_sha256":{str(self.root/name):digest(self.root/name) for name in self.frozen}}
        control.update(self.controller_changes); dump(self.controller_path,control)

    def load(self):
        return S.load_campaign(self.root,self.folder,self.campaign,self.expected,self.order,{})

    def git_show(self, command, **unused):
        if command[:2] != ["git","show"] or not command[2].startswith("d641ca8:"):
            raise AssertionError("unexpected git command")
        return self.frozen[command[2].split(":",1)[1]]


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="attachment-assessor-test-")
        self.root = Path(self.temp.name).resolve()
        self.archive = Archive(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_full_matrix_known_nested_medians_controls_and_flags(self):
        result = self.archive.load()
        self.assertEqual((len(result["cases"]),len(result["graphs"]),len(result["pairs"]),len(result["diagnostics"])),
                         (96,288,2880,2160))
        self.assertTrue(all(r["median_paired_ratio"]==3.5 for r in result["cases"]))
        graph0 = [r for r in result["graphs"] if r["graph_seed"]==GRAPHS[0]]
        self.assertTrue(all(r["median_paired_ratio"]==1.5 for r in graph0))
        self.assertEqual({r["family"] for r in result["cases"]},set((*FAMILIES,*CONTROLS)))
        self.assertEqual(sum(r["phase"]=="warmup" for r in result["diagnostics"]),360)
        flagged = [r for r in result["diagnostics"] if r["diagnostic_flags"]]
        self.assertEqual(len(flagged),1); self.assertEqual(flagged[0]["phase"],"warmup")
        self.assertEqual(flagged[0]["excluded"],"False")
        self.assertTrue(result["metadata"]["capture_clock_flags"])

    def invoke_main(self, output):
        with patch.object(S.subprocess,"check_output",side_effect=self.archive.git_show), \
             patch.object(sys,"argv",["assessor","--repo-root",str(self.root),"--output-dir",str(output)]), \
             patch.object(sys,"stdout",io.StringIO()),patch.object(sys,"stderr",io.StringIO()):
            return S.main()

    def test_complete_ab_pipeline_retains_every_control_and_flag(self):
        Archive(self.root,"b")
        output = self.root/"assessment"
        self.invoke_main(output)
        result = json.loads((output/"assessment.json").read_text())
        self.assertEqual(result["validation"],"pass")
        self.assertEqual([c["flagged_calls"] for c in result["campaigns"]],[1,1])
        self.assertEqual(len(result["shared_control_size_topology_coupling"]),6)
        self.assertFalse(result["campaigns_pooled"])
        self.assertTrue(all(not r["declared_upper_size_advantage_pass"] for r in result["criterion_results"]))
        expected = {"cases.csv":192,"graphs.csv":576,"pairs.csv":5760,"diagnostics.csv":4320}
        for name,count in expected.items():
            with (output/name).open(newline="") as stream: rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows),count)
            self.assertEqual({r["campaign"] for r in rows},{"a","b"})
            if name=="cases.csv":
                self.assertEqual(sum(r["family"] in CONTROLS for r in rows),32)
            if name=="diagnostics.csv":
                self.assertEqual(sum(bool(r["diagnostic_flags"]) for r in rows),2)
                self.assertTrue(all(r["excluded"]=="False" for r in rows))
        with self.assertRaises(SystemExit) as failure: self.invoke_main(output)
        self.assertEqual(failure.exception.code,2)

    def test_cross_campaign_source_binary_and_input_mismatches_fail(self):
        second = Archive(self.root,"b")
        initial = copy.deepcopy(second.meta)
        for field,value in (("binary_sha256","b"*64),("profile","different"),
                            ("binary_profile",{"stack_bytes":8388608}),
                            ("source_sha256",{str(second.recipe):digest(second.recipe)})):
            with self.subTest(field=field):
                second.meta = copy.deepcopy(initial); second.meta[field] = value; second.seal()
                output = self.root/("rejected-"+field)
                with self.assertRaises(SystemExit) as failure: self.invoke_main(output)
                self.assertEqual(failure.exception.code,2); self.assertFalse(output.exists())
        second.meta = initial
        case = list(second.expected)[0]
        for row in second.tables["validated_calls.csv"]:
            if row["case_id"]==case and row["graph_seed"]==GRAPHS[0]:
                row["input_fingerprint"] += 1
        second.seal()
        with self.assertRaises(SystemExit) as failure: self.invoke_main(self.root/"bad-fingerprint")
        self.assertEqual(failure.exception.code,2)

    def test_json_duplicate_keys_and_nonfinite_tokens_rejected(self):
        path = self.root/"invalid.json"
        for text in ('{"validation":"pass","validation":"failed"}', '{"ratio":NaN}', '{"ratio":Infinity}'):
            with self.subTest(text=text):
                path.write_text(text)
                with self.assertRaises(ValueError): S.read_json(path)

    def test_flattened_case_median_is_rejected_after_rehash(self):
        self.archive.tables["comparisons.csv"][0]["median_paired_ratio"] = 4.0
        self.archive.seal()
        with self.assertRaisesRegex(ValueError,"recomputed median_paired_ratio"): self.archive.load()

    def test_flattened_graph_median_is_rejected_after_rehash(self):
        self.archive.tables["graph_comparisons.csv"][0]["median_paired_ratio"] = 2.0
        self.archive.seal()
        with self.assertRaisesRegex(ValueError,"recomputed median_paired_ratio"): self.archive.load()

    def test_semantic_corruptions_are_not_just_hash_rejections(self):
        baseline = copy.deepcopy(self.archive.tables)
        changes = [
            ("missing pair", lambda t:t["paired_ratios.csv"].pop()),
            ("duplicate pair", lambda t:t["paired_ratios.csv"].__setitem__(1,copy.deepcopy(t["paired_ratios.csv"][0]))),
            ("wrong paired duration", lambda t:t["paired_ratios.csv"][0].__setitem__("kkt_ns",101)),
            ("wrong ratio", lambda t:t["paired_ratios.csv"][0].__setitem__("kkt_over_competitor",1.01)),
            ("wrong dimension", lambda t:t["paired_ratios.csv"][0].__setitem__("m",123)),
            ("unknown clock", lambda t:t["paired_ratios.csv"][0].__setitem__("metric","adjusted")),
            ("nonfinite ratio", lambda t:t["paired_ratios.csv"][0].__setitem__("kkt_over_competitor","nan")),
            ("missing call", lambda t:t["validated_calls.csv"].pop()),
            ("duplicate call", lambda t:t["validated_calls.csv"].__setitem__(1,copy.deepcopy(t["validated_calls.csv"][0]))),
            ("failed output", lambda t:t["validated_calls.csv"][0].__setitem__("validation","failed")),
            ("call fingerprint drift", lambda t:t["validated_calls.csv"][0].__setitem__("input_fingerprint",777)),
            ("excluded clock", lambda t:t["call_diagnostics.csv"][0].__setitem__("excluded",True)),
            ("missing diagnostic", lambda t:t["call_diagnostics.csv"].pop()),
            ("duplicate diagnostic", lambda t:t["call_diagnostics.csv"].__setitem__(1,copy.deepcopy(t["call_diagnostics.csv"][0]))),
        ]
        for name,change in changes:
            with self.subTest(name=name):
                self.archive.tables = copy.deepcopy(baseline); change(self.archive.tables); self.archive.seal()
                with self.assertRaises((ValueError,KeyError)): self.archive.load()

    def test_malformed_provenance_or_protocol_is_rejected(self):
        original = copy.deepcopy(self.archive.meta)
        for name,value in (("validation","failed"),("graph_seeds",[1,2,3]),("sampling_seeds",[401]),
                           ("repetitions",10),("rows_removed",1),("rows_adjusted",1),("flagged_calls",0),
                           ("case_order",list(reversed(self.archive.order))),("captures",[{}]*71)):
            with self.subTest(field=name):
                self.archive.meta = copy.deepcopy(original); self.archive.meta[name] = value; self.archive.seal()
                with self.assertRaises((ValueError,KeyError)): self.archive.load()

    def test_failed_missing_or_unbound_controller_is_rejected(self):
        for changes in ({"validation":"failed"},{"analysis_exit_status":1},
                        {"termination_warning":"still running"},{"native_process_may_still_be_running":True},
                        {"controller_sha256":"f"*64},{"frozen_declaration_revision":"other"}):
            with self.subTest(changes=changes):
                self.archive.controller_changes = changes; self.archive.seal()
                with self.assertRaises(ValueError): self.archive.load()
        self.archive.controller_changes = {}; self.archive.seal(); self.archive.controller_path.unlink()
        with self.assertRaises(OSError): self.archive.load()

    def test_unrehashable_artifact_change_and_missing_table_fail_closed(self):
        pair_path = self.archive.analysis/"paired_ratios.csv"
        pair_path.write_text(pair_path.read_text()+"\n")
        with self.assertRaisesRegex(ValueError,"hash mismatch"): self.archive.load()
        self.archive.seal(); pair_path.unlink()
        with self.assertRaises(OSError): self.archive.load()

    def test_helper_and_controller_source_mutation_fail_closed(self):
        self.archive.helper.write_text("changed helper\n")
        with self.assertRaisesRegex(ValueError,"hash mismatch"): self.archive.load()
        # Restore the helper's initial bytes; the controller source still has
        # its original captured hash, so only its mutation is being tested.
        self.archive.helper.write_text("# synthetic validated analyzer output contract\n")
        self.archive.controller_source.write_text("changed controller\n")
        with self.assertRaisesRegex(ValueError,"hash mismatch"): self.archive.load()

    def test_frozen_plan_binding_and_exact_reversal(self):
        with patch.object(S.subprocess,"check_output",side_effect=self.archive.git_show):
            expected,plans = S.frozen_plans(self.root,self.archive.folder,{})
            self.assertEqual(expected,self.archive.expected)
            self.assertEqual(plans["b"],list(reversed(plans["a"])))
            plan = self.archive.folder/"ATTACHMENT_CONFIRMATION.md"
            plan.write_text(plan.read_text()+"changed after freeze\n")
            with self.assertRaisesRegex(ValueError,"hash mismatch"):
                S.frozen_plans(self.root,self.archive.folder,{})

    def test_bad_reversal_even_when_synthetic_frozen_hash_agrees(self):
        a = self.archive.folder/"attachment-confirmation-a.csv"
        b = self.archive.folder/"attachment-confirmation-b.csv"
        b.write_bytes(a.read_bytes())
        self.archive.frozen[b.relative_to(self.root).as_posix()] = b.read_bytes()
        with patch.object(S.subprocess,"check_output",side_effect=self.archive.git_show):
            with self.assertRaisesRegex(ValueError,"does not reverse"):
                S.frozen_plans(self.root,self.archive.folder,{})

    def test_cross_family_coupling_and_nonfatal_weight_collision(self):
        result = self.archive.load()
        checked = S.topology_coupling([result])
        self.assertEqual(len(checked),3)
        self.assertTrue(all(r["matched_topology_fingerprint"] and
                            r["all_four_weighted_fingerprints_distinct"] for r in checked))
        key = (specification(CONTROLS[0],2097152)["case_id"],GRAPHS[0])
        other = (specification(FAMILIES[0],2097152)["case_id"],GRAPHS[0])
        result["fingerprints"][key] = result["fingerprints"][other]
        checked = S.topology_coupling([result])
        self.assertTrue(checked[0]["weight_fingerprint_review_required"])
        self.assertEqual(checked[0]["equal_weighted_fingerprint_pairs"],[[FAMILIES[0],CONTROLS[0]]])
        weighted,topology = result["fingerprints"][key]
        result["fingerprints"][key] = (weighted,topology+1)
        with self.assertRaisesRegex(ValueError,"different topology/order"):
            S.topology_coupling([result])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assessor",type=Path,default=Path(__file__).with_name("assess_attachment_confirmation.py"))
    parser.add_argument("--json-report",type=Path)
    args = parser.parse_args()
    global S
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("attachment_assessor_under_test",args.assessor.resolve(strict=True))
    S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
    suite = unittest.TestSuite((unittest.defaultTestLoader.loadTestsFromTestCase(CriterionTests),
                               unittest.defaultTestLoader.loadTestsFromTestCase(ArchiveTests)))
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    print(log.getvalue(),end="")
    report = {"schema":"attachment_assessor_semantic_tests_v1","validation":"pass" if result.wasSuccessful() else "failed",
              "test_methods":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),
              "assessor_sha256":digest(args.assessor.resolve()),"test_source_sha256":digest(Path(__file__).resolve()),
              "native_launches":0,"real_capture_rows_used":0,"log":log.getvalue()}
    if args.json_report:
        with args.json_report.open("x") as stream: stream.write(json.dumps(report,indent=2)+"\n")
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
