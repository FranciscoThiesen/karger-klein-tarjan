#!/usr/bin/env python3
"""Assess the frozen attachment confirmation rule AFTER both campaigns finish.

Standard library only. This does not launch solvers or rerun the capture
validator. It binds completed strict-analysis evidence and independently
recomputes its paired aggregates. Never execute during native measurement.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import statistics
import subprocess

REVISION = "d641ca8"
FAMILIES = ("leaf_hierarchy4", "leaf_distance4")
CONTROLS = ("leaf_shuffled4", "leaf_random4")
SIZES = (65536, 262144, 524288, 1048576, 2097152)
UPPER = (1048576, 2097152)
GRAPHS = (1000039, 1000081, 1000099)
SAMPLES = (401, 503)
COMPETITORS = ("compacting_boruvka", "kruskal", "prim", "boruvka")
ALGORITHMS = ("kkt", *COMPETITORS)
METRICS = {"wall": "elapsed_ns", "cpu": "process_cpu_elapsed_ns"}
IDENTITY = ("case_id", "family", "n", "m", "density", "intrusion_per_mille")
PAIR_FIELDS = (*IDENTITY, "metric", "competitor", "graph_seed", "kkt_seed",
               "repetition", "kkt_ns", "competitor_ns", "kkt_over_competitor")
GRAPH_FIELDS = (*IDENTITY, "metric", "competitor", "graph_seed", "median_paired_ratio",
                "trial_min_ratio", "trial_max_ratio", "individual_wins",
                "individual_losses", "individual_ties", "pairs")
CASE_FIELDS = (*IDENTITY, "metric", "competitor", "median_paired_ratio",
               "graph_min_ratio", "graph_max_ratio", "trial_min_ratio", "trial_max_ratio",
               "individual_wins", "individual_losses", "individual_ties", "graph_seeds", "pairs")
DIAGNOSTIC_FIELDS = ("case_id", "graph_seed", "kkt_seed", "phase", "repetition", "order",
                     "algorithm", "elapsed_ns", "process_cpu_elapsed_ns", "utc_elapsed_ns",
                     "steady_minus_cpu_ns", "utc_minus_steady_ns", "diagnostic_flags", "excluded")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def json_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def read_json(path):
    def invalid(value):
        raise ValueError("nonfinite JSON token: " + value)
    return json.loads(path.read_text(), object_pairs_hook=json_pairs, parse_constant=invalid)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def same(actual, expected, context):
    require(type(actual) is type(expected) and actual == expected, context + " differs")


def track(path, inputs, expected=None):
    path = Path(path).resolve(strict=True)
    value = sha(path)
    require(expected is None or (type(expected) is str and
            re.fullmatch(r"[0-9a-f]{64}", expected) and value == expected),
            "input hash mismatch: " + str(path))
    require(str(path) not in inputs or inputs[str(path)] == value,
            "input changed during assessment: " + str(path))
    inputs[str(path)] = value
    return path


def bind(registry, inputs):
    require(type(registry) is dict and registry, "missing hash registry")
    for name, digest in registry.items():
        require(type(name) is str and Path(name).is_absolute(), "hash-registry path must be absolute")
        track(name, inputs, digest)


def read_csv(path, fields=None):
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        if fields is not None:
            require(tuple(reader.fieldnames or ()) == fields, "unexpected CSV schema: " + str(path))
        rows = list(reader)
    require(rows and all(None not in row and all(value is not None for value in row.values())
                        for row in rows), "empty or malformed CSV: " + str(path))
    return rows


def natural(value, context, minimum=0):
    require(type(value) is str and re.fullmatch(r"[0-9]+", value), "invalid integer " + context)
    result = int(value)
    require(minimum <= result < 2**64, "integer outside range: " + context)
    return result


def finite(value, context):
    result = float(value)
    require(math.isfinite(result), "nonfinite value: " + context)
    return result


def specification(family, n):
    return {"case_id": f"{family}_n{n}_d16_p0", "family": family, "n": n,
            "m": n*16, "density": 16, "intrusion_per_mille": 0}


def frozen_plans(root, folder, inputs):
    plans = {}
    for name in ("ATTACHMENT_CONFIRMATION.md", "attachment-confirmation-a.csv",
                 "attachment-confirmation-b.csv"):
        path = folder/name
        original = subprocess.check_output(["git", "show", REVISION+":"+path.relative_to(root).as_posix()], cwd=root)
        track(path, inputs, hashlib.sha256(original).hexdigest())
    expected = {specification(family, n)["case_id"]: specification(family, n)
                for family, n in itertools.product(FAMILIES, SIZES)}
    expected.update({specification(family, SIZES[-1])["case_id"]: specification(family, SIZES[-1])
                     for family in CONTROLS})
    for campaign in ("a", "b"):
        rows = read_csv(folder/f"attachment-confirmation-{campaign}.csv",
                        ("family", "n", "density", "intrusion_per_mille"))
        order = []
        for row in rows:
            spec = specification(row["family"], natural(row["n"], "manifest.n"))
            require(row["density"] == "16" and row["intrusion_per_mille"] == "0"
                    and expected.get(spec["case_id"]) == spec, "unexpected confirmation case")
            order.append(spec["case_id"])
        require(len(order) == len(set(order)) == 12 and set(order) == set(expected), "incomplete confirmation grid")
        plans[campaign] = order
    require(plans["b"] == list(reversed(plans["a"])), "B does not reverse A's complete case order")
    return expected, plans


def identity(row, expected):
    require(row["case_id"] in expected, "unexpected case: " + row["case_id"])
    result = {field: row[field] if field in ("family", "case_id") else natural(row[field], field)
              for field in IDENTITY}
    require(result == expected[row["case_id"]], "case dimensions differ")
    return result


def compare_derived(path, fields, rows, keys):
    actual = read_csv(path, fields)
    expected = {tuple(str(row[key]) for key in keys): row for row in rows}
    require(len(actual) == len(expected), "derived row count differs: " + str(path))
    seen = set()
    for row in actual:
        key = tuple(row[k] for k in keys)
        require(key in expected and key not in seen, "missing/duplicated derived key: " + str(path))
        seen.add(key)
        for name, value in expected[key].items():
            if name == "campaign":
                continue
            observed = (natural(row[name], name) if type(value) is int else
                        finite(row[name], name) if type(value) is float else row[name])
            same(observed, value, "independently recomputed " + name)


def load_campaign(root, folder, campaign, expected, order, inputs):
    stem = "attachment-confirmation-"+campaign
    raw = folder/(stem+"-timing.csv")
    metadata = read_json(track(raw.with_suffix(".json"), inputs))
    analysis = folder/(stem+"-analysis")
    provenance = read_json(track(analysis/"provenance.json", inputs))
    controller = read_json(track(folder/(stem+"-controller.json"), inputs))
    for field, value in (("schema", "attachment_confirmation_controller_v1"), ("validation", "pass"),
                         ("campaign", stem), ("capture_exit_status", 0), ("analysis_exit_status", 0),
                         ("power_audit_exit_status", 0), ("power_audit_validation", "pass")):
        same(controller.get(field), value, "controller "+field)
    require(not any(k in controller for k in ("error", "termination_warning", "native_process_may_still_be_running")),
            "controller has incomplete termination or an error")
    bind(controller["retained_artifact_sha256"], inputs)
    bind(controller["analysis_bound_sha256"], inputs)
    track(folder/"run_attachment_confirmation.py", inputs, controller["controller_sha256"])
    same(controller["frozen_declaration_revision"], REVISION, "declaration revision")
    bind(controller["frozen_declaration_sha256"], inputs)
    for field, value in (("schema", "mst_search_capture_v1"), ("validation", "pass"),
                         ("case_order", order), ("graph_seeds", list(GRAPHS)), ("sampling_seeds", list(SAMPLES)),
                         ("algorithms", list(ALGORITHMS)), ("repetitions", 5), ("warmups", 1),
                         ("checked_rows", 2160), ("checked_timed_rows", 1800), ("checked_warmup_rows", 360),
                         ("rows_removed", 0), ("rows_adjusted", 0)):
        same(metadata.get(field), value, campaign+" capture "+field)
    require("error" not in metadata and len(metadata["captures"]) == 72, "failed/incomplete capture")
    for field, value in (("schema", "mst_search_analysis_v1"), ("validation", "pass"), ("cases", 12),
                         ("checked_rows", 2160), ("timed_rows", 1800), ("warmup_rows", 360),
                         ("rows_removed", 0), ("rows_adjusted", 0)):
        same(provenance.get(field), value, campaign+" analysis "+field)
    snapshot = dict(provenance["capture_metadata"])
    same(snapshot.pop("raw_csv"), str(raw), "analysis raw path")
    snapshot.pop("raw_csv_link")
    same(snapshot, metadata, "analysis/capture metadata")
    bind(provenance["input_sha256"], inputs)
    track(raw, inputs, metadata["output_sha256"])
    derived = provenance["derived_sha256"]
    required = {"paired_ratios.csv", "graph_comparisons.csv", "comparisons.csv", "validated_calls.csv", "call_diagnostics.csv"}
    require(required <= set(derived), "strict analysis is missing required derived tables")
    for name, digest in derived.items():
        require(Path(name).name == name, "nonlocal derived artifact name")
        track(analysis/name, inputs, digest)
    same(provenance["analysis_source_sha256"], metadata["python_source_sha256"], "strict analyzer helper inventory")
    # Confirm the known strict analyzer, rather than accepting an unbound pass label.
    bind(provenance["analysis_source_sha256"], inputs)
    power = read_json(track(folder/(stem+"-power-audit")/"audit.json", inputs))
    same(power.get("validation"), "pass", "completed power audit")
    same(power.get("checked_calls"), 2160, "power audit calls")
    # Its output is controller-bound. Do not require unpublished whole-machine
    # pmset logs to read these already computed performance results.
    calls = read_csv(analysis/"validated_calls.csv")
    same(len(calls), 2160, "validated call count")
    raw_lookup, fingerprints = {}, {}
    for row in calls:
        identity(row, expected)
        key = (row["case_id"], natural(row["graph_seed"], "graph_seed"),
               natural(row["kkt_seed"], "kkt_seed"), row["phase"],
               natural(row["repetition"], "repetition"), row["algorithm"])
        require(key not in raw_lookup and row["validation"] == "pass", "duplicate/failed validated call")
        raw_lookup[key] = row
        physical = (row["case_id"], key[1])
        fingerprint = (natural(row["input_fingerprint"], "input_fingerprint"),
                       natural(row["topology_fingerprint"], "topology_fingerprint"))
        require(physical not in fingerprints or fingerprints[physical] == fingerprint,
                "sampling seeds/calls changed the input graph")
        fingerprints[physical] = fingerprint
    expected_calls = {(case, g, s, phase, rep, algorithm)
                      for case, g, s in itertools.product(order, GRAPHS, SAMPLES)
                      for phase, count in (("warmup", 1), ("timed", 5))
                      for rep, algorithm in itertools.product(range(count), ALGORITHMS)}
    require(set(raw_lookup) == expected_calls, "validated call matrix incomplete")
    pair_rows, pair_index = [], {}
    for row in read_csv(analysis/"paired_ratios.csv", PAIR_FIELDS):
        spec = identity(row, expected)
        g, s, rep = (natural(row[name], name) for name in ("graph_seed", "kkt_seed", "repetition"))
        metric, competitor = row["metric"], row["competitor"]
        key = (row["case_id"], metric, competitor, g, s, rep)
        require(key not in pair_index and metric in METRICS and competitor in COMPETITORS,
                "duplicate or unknown paired observation")
        kkt_ns, competitor_ns = (natural(row[name], name, 1) for name in ("kkt_ns", "competitor_ns"))
        require(g in GRAPHS and s in SAMPLES and rep in range(5), "unexpected paired seed/repetition")
        for algorithm, duration in (("kkt", kkt_ns), (competitor, competitor_ns)):
            same(natural(raw_lookup[(row["case_id"],g,s,"timed",rep,algorithm)][METRICS[metric]], "raw duration", 1),
                 duration, "pair/validated-call duration")
        ratio = kkt_ns/competitor_ns
        same(finite(row["kkt_over_competitor"], "paired ratio"), ratio, "paired ratio arithmetic")
        pair_index[key] = ratio
        pair_rows.append({"campaign": campaign, **spec, "metric": metric, "competitor": competitor,
                          "graph_seed": g, "kkt_seed": s, "repetition": rep,
                          "kkt_ns": kkt_ns, "competitor_ns": competitor_ns, "kkt_over_competitor": ratio})
    require(set(pair_index) == set(itertools.product(order, METRICS, COMPETITORS, GRAPHS, SAMPLES, range(5))),
            "paired-ratio matrix incomplete")
    graphs, cases = [], []
    for case, metric, competitor in itertools.product(order, METRICS, COMPETITORS):
        graph_medians, all_values = [], []
        for g in GRAPHS:
            sample_medians, values = [], []
            for s in SAMPLES:
                trial = [pair_index[(case,metric,competitor,g,s,rep)] for rep in range(5)]
                sample_medians.append(statistics.median(trial)); values.extend(trial)
            median = statistics.median(sample_medians)
            graphs.append({"campaign": campaign, **expected[case], "metric": metric, "competitor": competitor,
                           "graph_seed": g, "median_paired_ratio": median, "trial_min_ratio": min(values),
                           "trial_max_ratio": max(values), "individual_wins": sum(v<1 for v in values),
                           "individual_losses": sum(v>1 for v in values), "individual_ties": sum(v==1 for v in values), "pairs": len(values)})
            graph_medians.append(median); all_values.extend(values)
        cases.append({"campaign": campaign, **expected[case], "metric": metric, "competitor": competitor,
                      "median_paired_ratio": statistics.median(graph_medians), "graph_min_ratio": min(graph_medians),
                      "graph_max_ratio": max(graph_medians), "trial_min_ratio": min(all_values),
                      "trial_max_ratio": max(all_values), "individual_wins": sum(v<1 for v in all_values),
                      "individual_losses": sum(v>1 for v in all_values), "individual_ties": sum(v==1 for v in all_values),
                      "graph_seeds": 3, "pairs": len(all_values)})
    compare_derived(analysis/"graph_comparisons.csv", GRAPH_FIELDS, graphs, ("case_id","metric","competitor","graph_seed"))
    compare_derived(analysis/"comparisons.csv", CASE_FIELDS, cases, ("case_id","metric","competitor"))
    diagnostics = read_csv(analysis/"call_diagnostics.csv", DIAGNOSTIC_FIELDS)
    same(len(diagnostics), 2160, "clock diagnostic count")
    diagnostic_keys = set()
    for row in diagnostics:
        key = (row["case_id"], natural(row["graph_seed"], "g"), natural(row["kkt_seed"], "s"),
               row["phase"], natural(row["repetition"], "rep"), row["algorithm"])
        require(key in raw_lookup and key not in diagnostic_keys and row["excluded"] == "False",
                "clock diagnostics duplicated, absent or excluded")
        diagnostic_keys.add(key)
    same(sum(bool(row["diagnostic_flags"]) for row in diagnostics), metadata["flagged_calls"], "retained flagged-call count")
    return {"campaign": campaign, "metadata": metadata, "controller": controller, "power_audit": power,
            "fingerprints": fingerprints,
            "cases": cases, "graphs": graphs, "pairs": pair_rows,
            "diagnostics": [{"campaign": campaign, **row} for row in diagnostics]}


def assess(campaigns):
    lookup = {(r["campaign"],r["family"],r["n"],r["metric"],r["competitor"]): r
              for campaign in campaigns for r in campaign["cases"]}
    result = []
    for family, competitor in itertools.product(FAMILIES, COMPETITORS):
        upper_checks, onset = [], []
        for campaign, metric in itertools.product(("a","b"), METRICS):
            for n in UPPER:
                row = lookup[(campaign,family,n,metric,competitor)]
                upper_checks.append({"campaign": campaign, "metric": metric, "n": n,
                                     "median_paired_ratio": row["median_paired_ratio"],
                                     "maximum_graph_median": row["graph_max_ratio"],
                                     "median_at_most_0_90": row["median_paired_ratio"] <= .90,
                                     "every_graph_median_below_1": row["graph_max_ratio"] < 1})
            curve = [lookup[(campaign,family,n,metric,competitor)] for n in SIZES]
            def brackets(threshold, left_inclusive):
                return [{"lower_n": left["n"], "upper_n": right["n"],
                         "lower_paired_median": left["median_paired_ratio"],
                         "upper_paired_median": right["median_paired_ratio"]}
                        for left,right in zip(curve,curve[1:])
                        if (left["median_paired_ratio"] >= threshold if left_inclusive else left["median_paired_ratio"] > threshold)
                        and (right["median_paired_ratio"] < threshold if left_inclusive else right["median_paired_ratio"] <= threshold)]
            onset.append({"campaign": campaign, "metric": metric,
                          "smaller_loss_or_tie_sizes": [row["n"] for row in curve
                                                        if row["n"] < UPPER[0] and row["median_paired_ratio"] >= 1],
                          "adjacent_parity_crossings": brackets(1, True),
                          "adjacent_10_percent_threshold_crossings": brackets(.9, False)})
        result.append({"family": family, "density": 16, "competitor": competitor,
                       "declared_upper_size_advantage_pass": all(x["median_at_most_0_90"] and x["every_graph_median_below_1"] for x in upper_checks),
                       "upper_checks": upper_checks, "onset_evidence": onset,
                       "smaller_loss_or_tie_in_each_campaign_and_clock": all(x["smaller_loss_or_tie_sizes"] for x in onset),
                       "observed_parity_crossing_in_each_campaign_and_clock": all(x["adjacent_parity_crossings"] for x in onset)})
    return result


def topology_coupling(campaigns):
    """Check the shared 2M interventions, without claiming hash injectivity."""
    rows = []
    families = (*FAMILIES, *CONTROLS)
    for campaign in campaigns:
        for g in GRAPHS:
            fingerprints = {family: campaign["fingerprints"][(specification(family, UPPER[-1])["case_id"], g)]
                            for family in families}
            topologies = {family: pair[1] for family, pair in fingerprints.items()}
            require(len(set(topologies.values())) == 1,
                    f"{campaign['campaign']}, graph seed {g}: 2M weight controls have different topology/order fingerprints")
            weighted = {family: pair[0] for family, pair in fingerprints.items()}
            equal_pairs = [list(pair) for pair in itertools.combinations(families, 2)
                           if weighted[pair[0]] == weighted[pair[1]]]
            rows.append({"campaign": campaign["campaign"], "n": UPPER[-1], "density": 16,
                         "graph_seed": g, "families": list(families),
                         "topology_fingerprints": topologies, "matched_topology_fingerprint": True,
                         "weighted_fingerprints": weighted,
                         "all_four_weighted_fingerprints_distinct": not equal_pairs,
                         "equal_weighted_fingerprint_pairs": equal_pairs,
                         "weight_fingerprint_review_required": bool(equal_pairs)})
    return rows


def markdown(result, campaigns, coupling):
    lines = ["# Frozen attachment confirmation assessment", "",
             "Both complete campaigns are retained separately. Ratios are paired within each graph, sampling seed and repetition, then medians are taken over repetitions, sampling seeds and graphs. They are not ratios of separate runtime medians.", "",
             "The declared advantage rule requires a paired case median ≤0.90 and every graph median <1 at both 1,048,576 and 2,097,152 vertices, in both campaigns and on both wall and process-CPU clocks. Onset is reported separately; a 10% advantage does not by itself establish a parity crossing.", "",
             "| Family | Competitor | Upper-size rule | Smaller loss/tie in each campaign/clock | Observed adjacent parity bracket in each |",
             "|---|---|---|---|---|"]
    for row in result:
        lines.append("| "+" | ".join((row["family"],row["competitor"],
            "PASS" if row["declared_upper_size_advantage_pass"] else "FAIL",
            "yes" if row["smaller_loss_or_tie_in_each_campaign_and_clock"] else "no",
            "yes" if row["observed_parity_crossing_in_each_campaign_and_clock"] else "no"))+" |")
    for campaign in campaigns:
        lines += ["", "## Campaign "+campaign["campaign"].upper(), "",
                  f"1,800 timed calls and 360 checked warmups; {campaign['metadata']['flagged_calls']} flagged calls retained. Capture/child UTC flags are preserved in assessment.json.", "",
                  "| Case | Clock | Compactor | Kruskal | Prim | Original Borůvka |", "|---|---|---:|---:|---:|---:|"]
        index = {(r["case_id"],r["metric"],r["competitor"]):r for r in campaign["cases"]}
        for case,metric in itertools.product(campaign["metadata"]["case_order"],METRICS):
            lines.append(f"| {case} | {metric} | "+" | ".join(f"{index[(case,metric,c)]['median_paired_ratio']:.6f}" for c in COMPETITORS)+" |")
    lines += ["", "## Matched topology at the shared control size", "",
              "At n = 2,097,152 and m = 16n, all four leaf families are checked together for each graph seed in each campaign. Matching captured topology/order fingerprints corroborate the generator's weight-intervention invariant; these finite noncryptographic fingerprints are not a proof of graph identity.", "",
              "| Campaign | Graph seed | All four topology fingerprints equal | All four weighted fingerprints distinct |",
              "|---|---:|---|---|"]
    for row in coupling:
        lines.append(f"| {row['campaign'].upper()} | {row['graph_seed']} | yes | "+
                     ("yes" if row["all_four_weighted_fingerprints_distinct"] else "NO — review equal pairs in assessment.json")+" |")
    lines += ["", "Distinct weighted fingerprints are reported from the captured data, not assumed for every seed: randomized ranks can in principle coincide and a finite fingerprint can collide. Equality is retained and flagged for review; it is not silently treated as a proven identical weighted graph or discarded.", "",
              "Leaf-mode star spokes remain forced MST edges even under global-random weights because their outer endpoints have degree one. Ordered and shuffled-core modes put all local spokes below all core edges, so the first round forms exactly the star blocks. Global random retains the forced spokes but may also select core edges in that round and merge multiple blocks.", "",
              "All 12 cases, including shuffled-core and global-random controls, all four competitors, all individual paired ratios and every call-clock diagnostic are retained in the accompanying CSVs. No clock flag causes exclusion or adjustment. B repeats A's graphs; it is not a new independent graph sample.", "",
              "assessment.json gives each of the eight upper-size checks per family/comparator and all adjacent measured parity/10% brackets separately by campaign and clock. Brackets are between tested points, not fitted transition locations. A parity crossing and meeting the 10% threshold are different observations. There are no confidence intervals, statistical-significance claims, pooled campaigns, extrapolation above the tested range or claims about all graph instances.", "",
              "This assessor binds existing successful capture/analysis artifacts and independently recomputes the paired aggregation; the underlying strict analyzer remains responsible for native certificate, schedule and clock-schema validation. Power-audit outputs are retained as previously computed, not rerun here. Source, frozen plan, raw and derived hashes are in provenance.json.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        root = args.repo_root.resolve(strict=True)
        folder = root/"benchmark/results/search-2026-10-13"
        require(not args.output_dir.exists(), "output directory already exists")
        inputs = {}; track(__file__, inputs)
        expected, plans = frozen_plans(root, folder, inputs)
        campaigns = [load_campaign(root,folder,name,expected,plans[name],inputs) for name in ("a","b")]
        first,second = campaigns
        for field in ("binary_sha256","binary_profile","profile","source_sha256","python_source_sha256","build_recipe_sha256"):
            same(first["metadata"][field], second["metadata"][field], "A/B "+field)
        same(first["controller"]["controller_sha256"], second["controller"]["controller_sha256"], "A/B controller source")
        same(first["fingerprints"], second["fingerprints"], "A/B actual graph fingerprints")
        results = assess(campaigns)
        coupling = topology_coupling(campaigns)
        assessment = {"schema":"attachment_confirmation_assessment_v1", "validation":"pass",
                      "frozen_declaration_revision":REVISION, "selected_families":list(FAMILIES),
                      "upper_sizes":list(UPPER), "comparators":list(COMPETITORS), "criterion_results":results,
                      "shared_control_size_topology_coupling":coupling,
                      "weight_fingerprint_review_required":any(row["weight_fingerprint_review_required"] for row in coupling),
                      "all_four_competitors_pass_by_family":{family:all(r["declared_upper_size_advantage_pass"] for r in results if r["family"]==family) for family in FAMILIES},
                      "campaigns":[{"campaign":c["campaign"],"timed_calls":1800,"warmups":360,
                                    "flagged_calls":c["metadata"]["flagged_calls"],
                                    "capture_clock_flags":c["metadata"]["capture_clock_flags"],
                                    "power_audit":c["power_audit"]} for c in campaigns],
                      "rows_removed":0,"rows_adjusted":0,"campaigns_pooled":False,
                      "infer_beyond_tested_range":False}
        for name,digest in inputs.items():
            same(sha(name),digest,"final input hash")
        args.output_dir.mkdir(parents=True,exist_ok=False)
        for kind in ("cases","graphs","pairs","diagnostics"):
            rows = [row for c in campaigns for row in c[kind]]
            with (args.output_dir/(kind+".csv")).open("x",newline="") as stream:
                writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        (args.output_dir/"assessment.json").write_text(json.dumps(assessment,indent=2,allow_nan=False)+"\n")
        (args.output_dir/"README.md").write_text(markdown(results,campaigns,coupling))
        provenance = {"schema":"attachment_confirmation_assessor_provenance_v1", "validation":"pass",
                      "input_sha256":inputs,"derived_sha256":{p.name:sha(p) for p in sorted(args.output_dir.iterdir())},
                      "counts":{"campaigns":2,"cases_per_campaign":12,"timed_calls":3600,"warmups":720,
                                "paired_rows":5760,"case_comparisons":192,"graph_comparisons":576}}
        (args.output_dir/"provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
        print(json.dumps({"validation":"pass","output_dir":str(args.output_dir.resolve()),"criteria":len(results)}))
    except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as error:
        parser.exit(2,"confirmation assessment: "+str(error)+"\n")


if __name__ == "__main__":
    main()
