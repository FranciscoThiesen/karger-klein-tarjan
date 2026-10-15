#!/usr/bin/env python3
"""Independent numerical audit; standard library, no collector imports.

Reads immutable native child CSVs and computes exact rational paired ratios.
The recorded schedule, certificates, hashes and six-position balance are checked
independently. This supplements, rather than replaces, full resource reanalysis.
"""
from collections import Counter, defaultdict
import csv
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "validation/independent-numerical-audit"
ALGORITHMS = ("kkt", "compacting_boruvka", "multigraph_boruvka", "kruskal", "prim", "boruvka")
SEEDS = (3000001, 3000029)
TEXT = {"case_id", "family", "phase", "algorithm", "validation"}
FIELDS = ("case_id", "family", "n", "m", "density", "intrusion_per_mille", "graph_seed", "kkt_seed",
          "input_fingerprint", "topology_fingerprint", "phase", "repetition", "order", "warmups", "algorithm",
          "elapsed_ns", "utc_start_ns", "utc_end_ns", "process_cpu_start_ns", "process_cpu_end_ns",
          "process_cpu_elapsed_ns", "validation")
METRICS = {"wall": "elapsed_ns", "cpu": "process_cpu_elapsed_ns"}
INPUTS = {}


def require(value, message):
    if not value: raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked(path, expected=None):
    path = Path(path).resolve(); value = digest(path)
    require(expected is None or value == expected, "hash mismatch: " + str(path))
    INPUTS[str(path)] = value
    return path


def read_csv(path, fields=None):
    with Path(path).open(newline="") as stream:
        reader = csv.DictReader(stream)
        require(fields is None or tuple(reader.fieldnames) == fields, "CSV header mismatch")
        rows = list(reader)
    require(all(None not in row and None not in row.values() for row in rows), "malformed CSV")
    return rows


def write_csv(name, rows):
    with (OUT / name).open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def ratio_fields(value):
    return {"ratio": float(value), "ratio_numerator": value.numerator, "ratio_denominator": value.denominator}


def main():
    metadata = checked(ROOT / "followup.json")
    info = json.loads(metadata.read_text())
    require(info["validation"] == "pass" and info["rows_removed"] == info["rows_adjusted"] == 0, "capture not complete/unmodified")
    freeze_path = checked(info["freeze"], info["freeze_sha256"])
    freeze = json.loads(freeze_path.read_text())
    checked(freeze["protocol"], freeze["protocol_sha256"])
    manifest = read_csv(checked(freeze["manifest"], freeze["manifest_sha256"]))
    specs = {}
    for row in manifest:
        spec = {name: (value if name == "family" else int(value)) for name, value in row.items()}
        spec["m"] = spec["n"] * spec["density"]
        spec["case_id"] = f"{spec['family']}_n{spec['n']}_d{spec['density']}_p{spec['intrusion_per_mille']}"
        require(spec["case_id"] not in specs, "duplicate manifest case"); specs[spec["case_id"]] = spec
    require(len(specs) == 10 and freeze["algorithms"] == list(ALGORITHMS), "wrong case/solver matrix")
    schedule = [(case, seed) for index, seed in enumerate(SEEDS) for case in (list(specs) if index == 0 else list(reversed(specs)))]
    require(len(info["captures"]) == 20, "wrong child count")
    all_rows = []; all_raw = []; certificates = []; blocks = {}; fingerprints = {}; flag_count = 0
    for child, (case, seed) in zip(info["captures"], schedule):
        require((child["case_id"], child["graph_seed"], child["kkt_seed"], child["exit_status"], child["validation"], child["interruption"])
                == (case, seed, 809, 0, "pass", None), "child differs from expected schedule/success")
        raw_path = checked(child["csv"], child["output_sha256"])
        log_path = checked(child["log"], child["log_sha256"])
        checked(child["rss_log"], child["rss_sha256"])
        raw = read_csv(raw_path, FIELDS); require(len(raw) == 42, "wrong native child row count")
        rows = [{name: (value if name in TEXT else int(value)) for name, value in row.items()} for row in raw]
        expected = [(phase, rep, order, ALGORITHMS[(order + rep) % 6])
                    for phase, reps in (("warmup", 1), ("timed", 6)) for rep in range(reps) for order in range(6)]
        positions = Counter(); previous_cpu = previous_utc = None
        for row, identity in zip(rows, expected):
            require(all(row[name] == value for name, value in specs[case].items()), "native graph differs from manifest")
            require((row["phase"], row["repetition"], row["order"], row["algorithm"]) == identity, "native solver position mismatch")
            require((row["graph_seed"], row["kkt_seed"], row["warmups"], row["validation"]) == (seed, 809, 1, "pass"), "native seed/result mismatch")
            cpu, wall = row["process_cpu_elapsed_ns"], row["elapsed_ns"]
            utc = row["utc_end_ns"] - row["utc_start_ns"]
            require(cpu > 0 and wall > 0 and row["process_cpu_end_ns"] - row["process_cpu_start_ns"] == cpu, "invalid clock duration")
            require(previous_cpu is None or row["process_cpu_start_ns"] >= previous_cpu, "CPU intervals overlap")
            threshold = max(2_000_000_000, cpu)
            flagged = utc < 0 or (previous_utc is not None and row["utc_start_ns"] < previous_utc) or 4 * abs(wall - cpu) > threshold or 4 * abs(utc - wall) > threshold
            flag_count += flagged
            previous_cpu, previous_utc = row["process_cpu_end_ns"], row["utc_end_ns"]
            fingerprint = (row["input_fingerprint"], row["topology_fingerprint"])
            require((case, seed) not in fingerprints or fingerprints[(case, seed)] == fingerprint, "input fingerprint changed")
            fingerprints[(case, seed)] = fingerprint
            if row["phase"] == "timed":
                positions[(row["algorithm"], row["order"])] += 1
                key = (case, seed, row["repetition"])
                block = blocks.setdefault(key, {})
                require(row["algorithm"] not in block, "duplicate timed algorithm"); block[row["algorithm"]] = row
        require(positions == Counter({(algorithm, order): 1 for algorithm in ALGORITHMS for order in range(6)}), "six-position imbalance")
        markers = [json.loads(line[len("reference_certificate_v1 "):]) for line in log_path.read_text().splitlines() if line.startswith("reference_certificate_v1 ")]
        require(len(markers) == 1 and markers[0] == child["certificate"], "native certificate marker mismatch")
        require(markers[0] == {name: rows[0][name] for name in ("case_id", "graph_seed", "kkt_seed", "n", "m", "input_fingerprint", "topology_fingerprint", "validation")}, "certificate/input mismatch")
        certificates.append(markers[0]); all_rows.extend(rows); all_raw.extend(raw)
    require(len(all_rows) == 840 and sum(row["phase"] == "timed" for row in all_rows) == 720, "wrong full output count")
    require(flag_count == info["flagged_calls"] == 0, "independent clock-flag count mismatch")
    require(read_csv(checked(info["output"], info["output_sha256"]), FIELDS) == all_raw, "combined file not exact child concatenation")
    pairs = []; values = defaultdict(list)
    for (case, seed, rep), block in blocks.items():
        require(set(block) == set(ALGORITHMS), "incomplete paired solver block")
        for comparator in ALGORITHMS[1:]:
            for metric, field in METRICS.items():
                ratio = Fraction(block["kkt"][field], block[comparator][field])
                values[(case, comparator, metric, seed)].append(ratio)
                pairs.append({"case_id": case, "graph_seed": seed, "repetition": rep, "comparator": comparator,
                              "metric": metric, "kkt_ns": block["kkt"][field], "comparator_ns": block[comparator][field], **ratio_fields(ratio)})
    graph_medians = {}; graph_rows = []; summaries = []; case_medians = {}
    for (case, comparator, metric, seed), sample in values.items():
        require(len(sample) == 6, "wrong graph ratio replication")
        median = statistics.median(sample); graph_medians[(case, comparator, metric, seed)] = median
        graph_rows.append({"case_id": case, "comparator": comparator, "metric": metric, "graph_seed": seed,
                           **ratio_fields(median), "trial_min": float(min(sample)), "trial_max": float(max(sample)),
                           "wins": sum(value < 1 for value in sample), "trials": len(sample)})
    for case in specs:
        for comparator in ALGORITHMS[1:]:
            for metric in METRICS:
                sample = [value for seed in SEEDS for value in values[(case, comparator, metric, seed)]]
                median = statistics.median(sample); case_medians[(case, comparator, metric)] = median
                summaries.append({**specs[case], "comparator": comparator, "metric": metric, **ratio_fields(median),
                                  "graph_min": float(min(graph_medians[(case, comparator, metric, seed)] for seed in SEEDS)),
                                  "graph_max": float(max(graph_medians[(case, comparator, metric, seed)] for seed in SEEDS)),
                                  "trial_min": float(min(sample)), "trial_max": float(max(sample)),
                                  "wins": sum(value < 1 for value in sample), "trials": len(sample)})
    groups = defaultdict(list)
    for case, spec in specs.items(): groups[(spec["family"], spec["density"])].append((spec["n"], case))
    points = []; brackets = []
    for (family, density), cases in sorted(groups.items()):
        cases.sort()
        for comparator in ALGORITHMS[1:]:
            statuses = []
            for n, case in cases:
                medians = [graph_medians[(case, comparator, metric, seed)] for metric in METRICS for seed in SEEDS]
                state = "loss" if all(value > 1 for value in medians) else "strong_win" if all(value <= Fraction(9, 10) for value in medians) else "mixed_or_narrow"
                statuses.append(state)
                points.append({"family": family, "density": density, "comparator": comparator, "n": n, "state": state,
                               **{f"{metric}_g{seed}": float(graph_medians[(case, comparator, metric, seed)]) for metric in METRICS for seed in SEEDS}})
            candidates = [(cases[max(i for i in range(j) if statuses[i] == "loss")][0], cases[j][0])
                          for j in range(1, len(cases)) if all(value == "strong_win" for value in statuses[j:]) and "loss" in statuses[:j]]
            bracket = candidates[0] if candidates else None
            classification = "strong_observed_crossover" if bracket else "strong_lead_entire_measured_range" if all(value == "strong_win" for value in statuses) else "loss_entire_measured_range" if all(value == "loss" for value in statuses) else "no_strong_observed_crossover"
            brackets.append({"family": family, "density": density, "comparator": comparator, "classification": classification,
                             "lower_measured_n": bracket[0] if bracket else None, "upper_measured_n": bracket[1] if bracket else None,
                             "point_states": ";".join(f"{n}:{state}" for (n, _), state in zip(cases, statuses))})
    comparisons_path = checked(ROOT / "analysis/comparisons.csv")
    graph_path = checked(ROOT / "analysis/graph_comparisons.csv")
    comparison_rows, comparison_graphs = read_csv(comparisons_path), read_csv(graph_path)
    require(len(comparison_rows) == 100 and len(comparison_graphs) == 200, "strict analyzer summary cardinality mismatch")
    for row in comparison_rows:
        expected = case_medians[(row["case_id"], row["competitor"], row["metric"])]
        require(math.isclose(float(row["median_paired_ratio"]), float(expected), rel_tol=1e-15, abs_tol=0), "strict analyzer case median differs")
    for row in comparison_graphs:
        expected = graph_medians[(row["case_id"], row["competitor"], row["metric"], int(row["graph_seed"]))]
        require(math.isclose(float(row["median_paired_ratio"]), float(expected), rel_tol=1e-15, abs_tol=0), "strict analyzer graph median differs")
    checked(__file__)
    for path, expected in INPUTS.items(): require(digest(path) == expected, "input changed during independent audit")
    OUT.mkdir()
    for name, rows in (("paired_ratios.csv", pairs), ("graph_medians.csv", graph_rows), ("case_medians.csv", summaries),
                       ("protocol_point_states.csv", points), ("strong_crossover_brackets.csv", brackets)):
        write_csv(name, rows)
    wins = [{"comparator": comparator, "metric": metric, "individual_wins": sum(row["wins"] for row in summaries if row["comparator"] == comparator and row["metric"] == metric), "individual_pairs": 120}
            for comparator in ALGORITHMS[1:] for metric in METRICS]
    report = {"schema": "independent_retention_numerical_audit_v1", "validation": "pass", "collector_imported": False,
              "raw_native_children": 20, "certificates": len(certificates), "checked_outputs": 840, "timed_outputs": 720,
              "warmup_outputs": 120, "paired_ratios": len(pairs), "case_medians": len(summaries), "graph_medians": len(graph_rows),
              "clock_flagged_calls": flag_count, "strict_analyzer_medians_agree": True,
              "arithmetic": "Exact Fraction ratios and medians; decimal CSV values are convenience conversions. Crossover predicates evaluated on exact fractions.",
              "scope": "Independent numeric/schedule/certificate/hash audit; full process-group resource validation is the separate strict collector analysis.",
              "individual_wins": wins, "crossover_results": brackets, "input_sha256": INPUTS}
    (OUT / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    text = ["# Independent six-solver numerical review", "", "PASS: independently read all 20 native child CSVs and certificate markers, "
            "checking 840 outputs (720 timed, 120 warmup), six-position balance, input identities, hashes and exact combined-file order. "
            "No collector or aggregation code was imported. All 100 case medians and 200 graph medians agree with the strict analyzer. "
            "The 1,200 paired ratios and crossover predicates were computed using exact rational arithmetic.", "",
            "| Case | KKT / compacting B | KKT / multigraph B | KKT / Kruskal | KKT / Prim | KKT / original B |", "|---|---:|---:|---:|---:|---:|"]
    for case in specs:
        text.append("| " + case + " | " + " | ".join(f"{float(case_medians[(case, solver, 'wall')]):.6f}" for solver in ALGORITHMS[1:]) + " |")
    text += ["", "The table shows pooled twelve-trial wall ratios. CPU medians, each graph's six-trial median, all trials and all losses remain in the CSVs.", "", "Declared strong crossover results:", ""]
    for item in brackets:
        if item["classification"] == "strong_observed_crossover":
            text.append(f"- {item['family']}, d={item['density']} versus {item['comparator']}: ({item['lower_measured_n']:,}, {item['upper_measured_n']:,}] vertices.")
    text += ["", "Every bracket requires both graph medians above one at its lower measured point, both at most 0.90 at its upper point "
             "on both clocks, and that same win condition at every larger tested size. These are measured brackets, not interpolated thresholds. "
             "All twenty family/density/comparator classifications are retained in `strong_crossover_brackets.csv`.", ""]
    (OUT / "README.md").write_text("\n".join(text))
    print(json.dumps({"validation": "pass", "outputs": 840, "pairs": len(pairs), "strong_crossovers": [item for item in brackets if item["classification"] == "strong_observed_crossover"], "individual_wins": wins}, indent=2))


if __name__ == "__main__": main()
