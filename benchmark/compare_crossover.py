#!/usr/bin/env python3
"""Compare crossover screens and a frozen confirmation pair without pooling.

--config is a strict crossover_comparison_v1 JSON object with `schema`,
`campaigns` (the compare_continuation.load_campaign configuration), and optional
`selection_file`, relative to the config. Every campaign requires timing_metadata
and its adjacent .log. Screen-only output is exploratory. Confirmation requires
exactly two runs and a crossover_selection_v1 file with these exact fields:

  schema, frozen_utc, revision_before_freeze_commit, primary, repeat,
  selected_groups: [{family,density,intrusion_per_mille:0,selected_sizes:[a,b]}],
  graph_seeds:[1000003,1000033,1000037], sampling_seeds:[211,307],
  repetitions:4, warmups:1, campaigns:2,
  criterion:{maximum_case_ratio:0.90,every_graph_ratio_strictly_below:1,
             metrics:["wall","cpu"],both_runs_required:true},
  binary_sha256,
  manifest_sha256:{PRIMARY_NAME:SHA256,REPEAT_NAME:SHA256},
  confirmation_outputs:{PRIMARY_NAME:"primary.csv",REPEAT_NAME:"repeat.csv"},
  screening_evidence:{SCREEN_NAME:{manifest_sha256,timing_csv_sha256,
                                 timing_metadata_sha256,log_sha256}}.

There must be one or two selected new family/density groups. For each, [a,b]
must be the two largest entries of its complete declared screening size menu.
All screened files and both full confirmation manifests, including controls,
are hash-bound. Recorded timestamps complement a pre-run git freeze; they do
not independently authenticate historical order. The paired wall and secondary
CPU rules are checked separately for every run and selected size. No flags or
losses are excluded, and a strong range advantage is not itself a crossover.
"""
import argparse
import copy
import csv
import json
from pathlib import Path
import re
import sys
import tempfile

import analyze_continuation as base
import compare_continuation as prior
import crossover_clocks as clocks

GRAPHS = (1000003, 1000033, 1000037)
SAMPLING = (211, 307)
NEW_FAMILIES = {"line_metric", "line_random", "grid2d_metric", "grid2d_random", "gnm_random"}
CRITERION = {"maximum_case_ratio": 0.90, "every_graph_ratio_strictly_below": 1,
             "metrics": ["wall", "cpu"], "both_runs_required": True}
SELECTION_FIELDS = {"schema", "frozen_utc", "revision_before_freeze_commit", "primary", "repeat",
                    "selected_groups", "graph_seeds", "sampling_seeds", "repetitions", "warmups",
                    "campaigns", "criterion", "binary_sha256", "manifest_sha256", "confirmation_outputs",
                    "screening_evidence"}


def read_json(path):
    return clocks.parse_json(path.read_text())


def evidence(campaign):
    paths = campaign["paths"]
    return {field + "_sha256": prior.sha256(paths[field])
            for field in ("manifest", "timing_csv", "timing_metadata", "log")}


def load_campaign(raw, folder):
    base.require(isinstance(raw, dict) and "timing_metadata" in raw,
                 "every crossover campaign requires capture metadata and per-call clocks")
    # Reuse the strict matrix, actual row schedule, metadata and optional
    # work/trace validators, without reusing the prior study's seed protocol.
    campaign = prior.load_campaign(raw, folder)
    base.require(campaign["role"] in ("screen", "confirmation"),
                 "this comparison accepts screens and the frozen confirmation pair only")
    paths = campaign["paths"]
    paths["log"] = paths["timing_csv"].with_suffix(".log")
    clock_audit = clocks.audit(paths["timing_csv"], paths["timing_metadata"])
    base.require(Path(clock_audit["manifest"]) == paths["manifest"] and
                 tuple(clock_audit["graph_seeds"]) == campaign["graph_seeds"] and
                 tuple(clock_audit["sampling_seeds"]) == campaign["sampling_seeds"] and
                 clock_audit["repetitions"] == campaign["repetitions"] and
                 clock_audit["warmups"] == campaign["warmups"],
                 campaign["name"] + ": clock metadata protocol differs from comparison configuration")
    # Strict JSON parsing also rejects duplicate keys in provenance, whereas
    # the historical campaign loader remains unchanged for prior reports.
    campaign["provenance"] = read_json(paths["timing_metadata"])
    cpu_rows = {}
    for record in clock_audit["records"]:
        if record["phase"] == "timed":
            key = clocks.timing_key(record, clock=True)
            cpu_rows[key] = {**campaign["timing"][key], "elapsed_ns": record["process_cpu_elapsed_ns"]}
    base.require(set(cpu_rows) == set(campaign["timing"]), "CPU observations differ from timed observations")
    campaign["cpu_tables"] = base.aggregate_timing(cpu_rows, campaign["cases"],
        campaign["graph_seeds"], campaign["sampling_seeds"], campaign["repetitions"])
    campaign["clock_audit"] = clock_audit
    provenance = campaign["provenance"]
    for field in ("analyzer_sha256", "clock_auditor_sha256"):
        base.require(isinstance(provenance.get(field), str) and
                     re.fullmatch(r"[0-9a-f]{64}", provenance[field]), "missing capture " + field)
    started = prior.timestamp(provenance.get("started_utc"), campaign["name"] + " start")
    finished = prior.timestamp(provenance.get("finished_utc"), campaign["name"] + " finish")
    base.require(finished > started, campaign["name"] + ": invalid capture UTC interval")
    campaign["started"] = started
    campaign["finished"] = finished
    return campaign


def validate_selection(selection, campaigns, selection_folder):
    base.require(type(selection) is dict and set(selection) == SELECTION_FIELDS and
                 selection["schema"] == "crossover_selection_v1", "unexpected frozen selection schema")
    base.require(type(selection["revision_before_freeze_commit"]) is str and
                 re.fullmatch(r"[0-9a-f]{40}", selection["revision_before_freeze_commit"]),
                 "selection requires the full pre-freeze git revision")
    base.require(type(selection["binary_sha256"]) is str and
                 re.fullmatch(r"[0-9a-f]{64}", selection["binary_sha256"]), "invalid frozen binary SHA256")
    for field, expected in (("graph_seeds", list(GRAPHS)), ("sampling_seeds", list(SAMPLING)),
                            ("repetitions", 4), ("warmups", 1), ("campaigns", 2)):
        actual = selection[field]
        base.require(type(actual) is type(expected) and actual == expected and
                     (not isinstance(actual, list) or all(type(x) is int for x in actual)),
                     "frozen protocol mismatch: " + field)
    criterion = selection["criterion"]
    base.require(type(criterion) is dict and set(criterion) == set(CRITERION) and criterion == CRITERION and
                 type(criterion["maximum_case_ratio"]) in (int, float) and
                 type(criterion["every_graph_ratio_strictly_below"]) in (int, float) and
                 type(criterion["both_runs_required"]) is bool,
                 "frozen criterion differs from the fixed wall-and-CPU rule")
    by_name = {c["name"]: c for c in campaigns}
    names = selection["primary"], selection["repeat"]
    base.require(all(type(name) is str and name in by_name for name in names) and names[0] != names[1],
                 "selection must name two distinct configured confirmation runs")
    a, b = (by_name[name] for name in names)
    base.require({c["name"] for c in campaigns if c["role"] == "confirmation"} == set(names),
                 "exactly the frozen pair must have confirmation roles; no replacement runs")
    base.require(a["cases"] == b["cases"] and list(b["cases"]) == list(reversed(a["cases"])),
                 "confirmation must use identical cases in exactly reversed manifest order")
    frozen = prior.timestamp(selection["frozen_utc"], "selection freeze")
    screens = [c for c in campaigns if c["role"] == "screen"]
    base.require(screens, "confirmation requires the complete preceding screening set")
    base.require(selection["screening_evidence"] == {c["name"]: evidence(c) for c in screens},
                 "frozen screening hashes differ from the complete declared screening set")
    base.require(selection["manifest_sha256"] ==
                 {c["name"]: prior.sha256(c["paths"]["manifest"]) for c in (a, b)},
                 "full confirmation manifests differ from their frozen hashes")
    outputs = selection["confirmation_outputs"]
    base.require(type(outputs) is dict and set(outputs) == set(names) and
                 all(type(path) is str and path and Path(path).suffix == ".csv" for path in outputs.values()),
                 "freeze both original confirmation output CSV paths")
    for c in (a, b):
        target = (selection_folder / outputs[c["name"]]).resolve()
        base.require(c["paths"]["timing_csv"] == target and
                     c["paths"]["timing_metadata"] == target.with_suffix(".json"),
                     "confirmation file differs from the frozen original output; replacements cannot rescue the rule")
    for c in screens:
        base.require(c["finished"] < frozen, c["name"] + ": screen did not finish before selection freeze")
        base.require(not set(c["graph_seeds"]) & set(GRAPHS) and
                     not set(c["sampling_seeds"]) & set(SAMPLING), "screen used held-out seeds")
    for c in (a, b):
        base.require(c["graph_seeds"] == GRAPHS and c["sampling_seeds"] == SAMPLING and
                     c["repetitions"] == 4 and c["warmups"] == 1,
                     "confirmation differs from the fixed fresh-seed protocol")
        base.require(c["started"] > frozen, c["name"] + ": confirmation began before selection freeze")
        base.require(c["provenance"]["binary_sha256"] == selection["binary_sha256"],
                     "confirmation binary differs from the frozen binary")
    base.require(b["started"] > a["finished"], "repeat must follow the completed primary campaign")
    for field in ("binary_sha256", "profile", "platform", "machine", "source_sha256",
                  "runner_sha256", "analyzer_sha256", "clock_auditor_sha256"):
        base.require(a["provenance"][field] == b["provenance"][field],
                     "confirmation provenance differs between runs: " + field)
    base.require(set(a["timing"]) == set(b["timing"]), "confirmation observation identities differ")
    for field in ("work", "traces"):
        if a[field] and b[field]:
            base.require(a[field] == b[field], "identical repeated graphs have inconsistent " + field)
    raw_groups = selection["selected_groups"]
    base.require(type(raw_groups) is list and 1 <= len(raw_groups) <= 2,
                 "select one or two candidate family/density groups")
    groups = {}
    for raw in raw_groups:
        base.require(type(raw) is dict and set(raw) == {*prior.GROUP_FIELDS, "selected_sizes"},
                     "invalid selected group fields")
        base.require(type(raw["family"]) is str and raw["family"] in NEW_FAMILIES and
                     type(raw["density"]) is int and type(raw["intrusion_per_mille"]) is int and
                     raw["intrusion_per_mille"] == 0, "candidate must be a new unperturbed family/density group")
        key = prior.group(raw)
        sizes = raw["selected_sizes"]
        base.require(key not in groups and type(sizes) is list and len(sizes) == 2 and
                     all(type(n) is int for n in sizes) and sizes == sorted(set(sizes)),
                     "duplicate group or invalid two-size selection")
        menu = sorted({spec["n"] for c in screens for spec in c["cases"].values() if prior.group(spec) == key})
        base.require(len(menu) >= 2 and sizes == menu[-2:],
                     "selected sizes must be adjacent largest entries of the complete screened group menu")
        base.require(sorted(spec["n"] for spec in a["cases"].values() if prior.group(spec) == key) == sizes,
                     "confirmation candidate cases differ from frozen selected sizes")
        groups[key] = sizes
    return a, b, groups


def collect(config, folder):
    base.require(type(config) is dict and {"schema", "campaigns"} <= set(config) <=
                 {"schema", "campaigns", "selection_file"} and
                 config["schema"] == "crossover_comparison_v1", "unexpected comparison schema")
    base.require(type(config["campaigns"]) is list and config["campaigns"], "empty campaign list")
    campaigns = [load_campaign(raw, folder) for raw in config["campaigns"]]
    base.require(len({c["name"] for c in campaigns}) == len(campaigns), "duplicate campaign name")
    base.require(len({c["paths"]["timing_csv"] for c in campaigns}) == len(campaigns),
                 "a raw campaign cannot be reused under multiple names")
    base.check_fingerprints(row for c in campaigns for row in c["timing"].values())
    reference = campaigns[0]["provenance"]
    for c in campaigns:
        base.require(all(c["provenance"]["source_sha256"][f] == reference["source_sha256"][f]
                         for f in prior.PRODUCTION_FILES), "listed production-library source changed across campaigns")
        base.require(all(c["provenance"][f] == reference[f] for f in ("profile", "platform", "machine")),
                     "build/machine profile changed across campaigns")
    confirmation = None
    selection_path = None
    if "selection_file" in config:
        base.require(type(config["selection_file"]) is str and config["selection_file"], "invalid selection path")
        selection_path = (folder / config["selection_file"]).resolve()
        confirmation = validate_selection(read_json(selection_path), campaigns, selection_path.parent)
    else:
        base.require(all(c["role"] == "screen" for c in campaigns), "confirmation requires frozen selection")
    return campaigns, confirmation, selection_path


def confirmation_tables(campaigns, confirmation):
    if confirmation is None:
        return [], []
    a, b, selected = confirmation
    lookup = {(c["name"], metric): {r["case_id"]: r for r in c[field][0]}
              for c in (a, b) for metric, field in (("wall", "tables"), ("cpu", "cpu_tables"))}
    cases = []
    for case, spec in a["cases"].items():
        row = {**spec, "selected_candidate": prior.group(spec) in selected}
        for name, c in (("primary", a), ("repeat", b)):
            for metric in ("wall", "cpu"):
                measured = lookup[c["name"], metric][case]
                for field in ("paired_runtime_ratio", "graph_min_ratio", "graph_max_ratio",
                              "kkt_median_ns", "compacting_boruvka_median_ns",
                              "kkt_slower_observations", "equal_observations", "paired_observations"):
                    row[name + "_" + metric + "_" + field] = measured[field]
                row[name + "_" + metric + "_passes"] = (measured["paired_runtime_ratio"] <= 0.90 and
                                                          measured["graph_max_ratio"] < 1)
        row["passes_both_metrics_both_runs"] = all(row[n + "_" + m + "_passes"]
                                                    for n in ("primary", "repeat") for m in ("wall", "cpu"))
        cases.append(row)
    groups = []
    for key, sizes in selected.items():
        included = [r for r in cases if prior.group(r) == key]
        result = {**dict(zip(prior.GROUP_FIELDS, key)), "selected_sizes": ",".join(map(str, sizes))}
        for name in ("primary", "repeat"):
            for metric in ("wall", "cpu"):
                result[name + "_" + metric + "_passes_both_sizes"] = all(
                    row[name + "_" + metric + "_passes"] for row in included)
                result[name + "_" + metric + "_all_case_medians_below_one"] = all(
                    row[name + "_" + metric + "_paired_runtime_ratio"] < 1 for row in included)
                result[name + "_" + metric + "_all_graph_medians_below_one"] = all(
                    row[name + "_" + metric + "_graph_max_ratio"] < 1 for row in included)
        result["confirmed_clear_advantage"] = all(row["passes_both_metrics_both_runs"] for row in included)
        # A smaller observed pilot loss is reported separately. It is neither
        # required for a clear range advantage nor proof of a population onset.
        for metric, field in (("wall", "tables"), ("cpu", "cpu_tables")):
            losses = [f'{c["name"]}:{r["case_id"]}' for c in campaigns if c["role"] == "screen"
                      for r in c[field][0] if prior.group(r) == key and r["n"] < sizes[0] and
                      r["paired_runtime_ratio"] >= 1]
            result["smaller_screen_" + metric + "_loss_or_tie"] = bool(losses)
            result["smaller_screen_" + metric + "_loss_cases"] = ";".join(losses)
        groups.append(result)
    return cases, groups


def tables(campaigns, confirmation):
    tagged = prior.tagged_tables(campaigns)
    result = {("wall_" + name if name in ("case_summary", "graph_summary", "paired_pairs", "order_summary")
               else name): rows for name, rows in tagged.items()}
    for name, index in (("case_summary", 0), ("graph_summary", 1), ("paired_pairs", 2), ("order_summary", 3)):
        result["cpu_" + name] = [{"campaign": c["name"], "role": c["role"], **row}
                                for c in campaigns for row in c["cpu_tables"][index]]
    result["call_clocks"] = [{"campaign": c["name"], "role": c["role"], **record,
                             "diagnostic_flags": ";".join(record["diagnostic_flags"])}
                            for c in campaigns for record in c["clock_audit"]["records"]]
    result["confirmation_cases"], result["confirmation_groups"] = confirmation_tables(campaigns, confirmation)
    return result


def report(output, campaigns, derived):
    lines = ["# Crossover campaigns: retained wall and CPU evidence", "",
        "Every campaign remains separate. Ratios pair KKT and compaction within each repetition, then take medians "
        "over repetitions, sampling seeds and graph seeds. Process CPU is a secondary diagnostic envelope; steady elapsed "
        "time remains primary. Clock flags retain every row. Repeated campaigns reuse the same graphs, not independent draws.", "",
        "| Campaign | Role | Cases | Timed calls | Warmups | Flagged calls |", "|---|---|---:|---:|---:|---:|"]
    for c in campaigns:
        lines.append(f'| {c["name"]} | {c["role"]} | {len(c["cases"])} | {len(c["timing"])} | '
                     f'{c["checked_warmups"]} | {c["clock_audit"]["flagged_calls"]} |')
    lines += ["", "## Frozen outcome", "",
        "A selected group has a clear measured-range advantage only when the paired case ratio is ≤0.90 and every "
        "graph median is <1 at both frozen sizes, for wall and CPU separately in both runs. This is a descriptive rule, "
        "not a significance test or extrapolation. A lower-size observed loss/tie is listed separately; an all-winning "
        "range does not establish a crossover onset.", ""]
    if derived["confirmation_groups"]:
        lines += ["| Group | Sizes | Primary wall | Repeat wall | Primary CPU | Repeat CPU | Clear advantage | Smaller screen wall loss/tie | Smaller screen CPU loss/tie |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for r in derived["confirmation_groups"]:
            values = [r["family"] + f' d={r["density"]}', r["selected_sizes"]]
            values += [r[f"{run}_{metric}_passes_both_sizes"] for metric in ("wall", "cpu") for run in ("primary", "repeat")]
            values += [r["confirmed_clear_advantage"], r["smaller_screen_wall_loss_or_tie"], r["smaller_screen_cpu_loss_or_tie"]]
            lines.append("| " + " | ".join(map(str, values)) + " |")
    else:
        lines.append("No frozen confirmation pair was supplied. All outcomes are exploratory.")
    for metric in ("wall", "cpu"):
        lines += ["", "## All " + metric + " cases", "",
            "Graph ranges are observed ranges, not confidence intervals. Individual losses are retained.", "",
            "| Campaign | Case | Paired ratio [graph range] | KKT ms | Compactor ms | KKT losses / pairs |",
            "|---|---|---:|---:|---:|---:|"]
        for r in derived[metric + "_case_summary"]:
            lines.append(f'| {r["campaign"]} | {r["case_id"]} | {r["paired_runtime_ratio"]:.4f} '
                f'[{r["graph_min_ratio"]:.4f}, {r["graph_max_ratio"]:.4f}] | {r["kkt_median_ns"]/1e6:.3f} | '
                f'{r["compacting_boruvka_median_ns"]/1e6:.3f} | {r["kkt_slower_observations"]}/{r["paired_observations"]} |')
    lines += ["", "Every case, graph, pair and execution-order stratum is retained in `wall_*.csv` and `cpu_*.csv`. "
        "The CPU tables retain the shared aggregation column names but their nanoseconds and ratios are process CPU. "
        "`call_clocks.csv` contains every checked warmup and timed record. Original files are unchanged; hashes and source "
        "provenance are in [comparison_inputs.json](comparison_inputs.json).", "",
        "Frozen and runner timestamps are recorded evidence, not independent authentication. Across screens, automatic "
        "code equality checks cover the listed production libraries; changed harness bodies need separate review. The "
        "confirmation pair requires identical full source inventories, binary and capture/analysis hashes. Fingerprints "
        "are consistency checks, not collision-proof graph certificates. Classical-baseline adjunct evidence is separate."]
    (output / "report.md").write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--plots", action="store_true", help="Render shared wall plots after validation; imports matplotlib lazily")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2)); return
    base.require(args.config is not None and (args.validate_only or args.output_dir is not None),
                 "--config and either --output-dir or --validate-only are required")
    campaigns, confirmation, selection = collect(read_json(args.config), args.config.resolve().parent)
    derived = tables(campaigns, confirmation)
    metadata = {"schema": "crossover_comparison_result_v1", "validation": "pass", "criterion": CRITERION,
        "config": {"path": str(args.config.resolve()), "sha256": prior.sha256(args.config)},
        "selection": {"path": str(selection), "sha256": prior.sha256(selection)} if selection else None,
        "source_sha256": {Path(module.__file__).name: prior.sha256(Path(module.__file__))
                          for module in (base, prior, clocks)},
        "comparison_sha256": prior.sha256(Path(__file__)), "rows_removed": 0, "rows_adjusted": 0,
        "cross_screen_checked_library_files": prior.PRODUCTION_FILES,
        "campaigns": [{"name": c["name"], "role": c["role"], "cases": list(c["cases"]),
                       "graph_seeds": c["graph_seeds"], "sampling_seeds": c["sampling_seeds"],
                       "repetitions": c["repetitions"], "warmups": c["warmups"],
                       "timed_calls": len(c["timing"]), "checked_warmups": c["checked_warmups"],
                       "flagged_calls": c["clock_audit"]["flagged_calls"],
                       "inputs": {key: {"path": str(path), "sha256": prior.sha256(path)}
                                  for key, path in c["paths"].items()}} for c in campaigns]}
    if args.validate_only:
        print(json.dumps(metadata, indent=2, allow_nan=False)); return
    args.output_dir.mkdir(parents=True, exist_ok=True)
    prior.write_tables(args.output_dir, derived)
    if args.plots:
        wall = args.output_dir / "wall_plots"
        wall.mkdir(exist_ok=True)
        for path in wall.iterdir():
            if re.fullmatch(r"(?:ratios|times|work)_[0-9]+\.(?:png|svg|pdf)", path.name): path.unlink()
        prior.plots(wall, campaigns, prior.tagged_tables(campaigns))
    report(args.output_dir, campaigns, derived)
    (args.output_dir / "comparison_inputs.json").write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n")
    print(f"Validated {len(campaigns)} separate campaigns; wrote {args.output_dir}")


def self_test():
    """Stdlib only. Full synthetic raw captures exercise the reused validators."""
    checks = []
    with tempfile.TemporaryDirectory(prefix="crossover-compare-test-") as temporary:
        root = Path(temporary)
        config = {"schema": "crossover_comparison_v1", "campaigns": [], "selection_file": "selection.json"}
        documents = {}
        for index, name in enumerate(("screen", "primary", "repeat")):
            gs, ss, reps = ((3037,), (101,), 2) if index == 0 else (GRAPHS, SAMPLING, 4)
            specs = [{"family": "line_metric", "n": n, "density": 2, "intrusion_per_mille": 0}
                     for n in ((32, 64, 128) if index == 0 else (64, 128))]
            specs.append({"family": "line_random", "n": 128, "density": 2, "intrusion_per_mille": 0})
            if name == "repeat": specs.reverse()
            manifest, timing, meta = (root / (name + suffix) for suffix in ("_manifest.csv", ".csv", ".json"))
            def write(path, fields, rows):
                with path.open("w", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
            write(manifest, base.MANIFEST_FIELDS, specs)
            cases = base.load_manifest(manifest)
            rows, records = [], []
            cpu_clock, utc_clock = 1000, 1000000000000
            for identity in clocks.schedule(cases, gs, ss, reps, 1):
                spec = cases[identity["case_id"]]
                ratio = 1.2 if spec["family"] == "line_random" else (1.1 if spec["n"] == 32 else .9)
                duration = round(10000 * (ratio if identity["algorithm"] == "kkt" else 1))
                records.append({**identity, "utc_start_ns": utc_clock, "utc_end_ns": utc_clock+duration,
                    "process_cpu_start_ns": cpu_clock, "process_cpu_end_ns": cpu_clock+duration,
                    "process_cpu_elapsed_ns": duration, "steady_elapsed_ns": duration, "validation": "pass"})
                cpu_clock += duration + 100; utc_clock += duration + 100
                if identity["phase"] == "timed":
                    topology = spec["n"]*10000000 + identity["graph_seed"]
                    rows.append({**spec, "graph_seed": identity["graph_seed"], "input_fingerprint": topology +
                        (10000000000 if spec["family"] == "line_random" else 0), "topology_fingerprint": topology,
                        "kkt_seed": identity["sampling_seed"], "repetition": identity["repetition"],
                        "order": identity["order"], "warmups": 1, "algorithm": identity["algorithm"],
                        "elapsed_ns": duration, "validation": "pass"})
            write(timing, base.TIMING_FIELDS, rows)
            log = timing.with_suffix(".log")
            log.write_text("".join(clocks.PREFIX + json.dumps(row) + "\n" for row in records))
            metadata = {"mode": "timing", "exit_status": 0, "interruption": None,
                "command": ["/synthetic/binary", "--manifest", str(manifest), "--mode", "timing",
                    "--graph-seeds", ",".join(map(str, gs)), "--sampling-seeds", ",".join(map(str, ss)),
                    "--repetitions", str(reps), "--warmups", "1"],
                "output_sha256": prior.sha256(timing), "manifest_sha256": prior.sha256(manifest),
                "log_sha256": prior.sha256(log), "basic_validated_rows": len(rows),
                "checked_warmup_calls": len(cases)*len(gs)*len(ss)*2,
                "binary_sha256": "a"*64, "runner_sha256": "b"*64, "analyzer_sha256": "c"*64,
                "clock_auditor_sha256": "d"*64, "source_sha256": {f: "e"*64 for f in prior.PRODUCTION_FILES},
                "profile": "synthetic", "platform": "synthetic", "machine": "synthetic",
                "started_utc": f"2026-10-13T0{index*2}:00:00+00:00",
                "finished_utc": f"2026-10-13T0{index*2}:01:00+00:00"}
            meta.write_text(json.dumps(metadata))
            config["campaigns"].append({"name": name, "role": "screen" if index == 0 else "confirmation",
                "manifest": manifest.name, "timing_csv": timing.name, "timing_metadata": meta.name,
                "graph_seeds": list(gs), "sampling_seeds": list(ss), "repetitions": reps, "warmups": 1})
            documents[name] = {"manifest": manifest, "timing_csv": timing, "timing_metadata": meta, "log": log}
        selection = {"schema": "crossover_selection_v1", "frozen_utc": "2026-10-13T01:00:00+00:00",
            "revision_before_freeze_commit": "f"*40, "primary": "primary", "repeat": "repeat",
            "selected_groups": [{"family": "line_metric", "density": 2, "intrusion_per_mille": 0,
                                 "selected_sizes": [64, 128]}], "graph_seeds": list(GRAPHS),
            "sampling_seeds": list(SAMPLING), "repetitions": 4, "warmups": 1, "campaigns": 2,
            "criterion": copy.deepcopy(CRITERION), "binary_sha256": "a"*64,
            "confirmation_outputs": {"primary": "primary.csv", "repeat": "repeat.csv"},
            "manifest_sha256": {name: prior.sha256(documents[name]["manifest"]) for name in ("primary", "repeat")},
            "screening_evidence": {"screen": {field+"_sha256": prior.sha256(path)
                                              for field, path in documents["screen"].items()}}}
        (root / "selection.json").write_text(json.dumps(selection))
        campaigns, confirmed, _ = collect(config, root)
        derived = tables(campaigns, confirmed)
        result = derived["confirmation_groups"][0]
        base.require(result["confirmed_clear_advantage"] and result["smaller_screen_wall_loss_or_tie"] and
                     len(derived["wall_paired_pairs"]) == len(derived["cpu_paired_pairs"]) == 152,
                     "self-test complete matrix or inclusive threshold failed")
        checks.append({"case": "full raw pipeline, inclusive .90, both metrics/runs, lower-size and control losses retained", "status": "pass"})
        changed = copy.deepcopy(campaigns)
        row = next(r for r in changed[2]["cpu_tables"][0] if r["family"] == "line_metric" and r["n"] == 64)
        row["graph_max_ratio"] = 1
        base.require(not confirmation_tables(changed, (changed[1], changed[2], confirmed[2]))[1][0]["confirmed_clear_advantage"],
                     "a CPU graph at parity was incorrectly rescued by wall success")
        checks.append({"case": "secondary CPU graph at parity blocks success without excluding campaign", "status": "pass"})
        changed = copy.deepcopy(campaigns)
        for c in changed[1:]:
            for row in c["tables"][0]:
                if row["family"] == "line_metric":
                    row.update(paired_runtime_ratio=.95, graph_min_ratio=.94, graph_max_ratio=.96)
        near = confirmation_tables(changed, (changed[1], changed[2], confirmed[2]))[1][0]
        base.require(not near["confirmed_clear_advantage"] and near["primary_wall_all_case_medians_below_one"] and
                     near["repeat_wall_all_graph_medians_below_one"] and near["smaller_screen_wall_loss_or_tie"],
                     "directional gains were conflated with the stronger .90 criterion")
        checks.append({"case": "directional .95 gain and smaller pilot loss stay visible while strong criterion fails", "status": "pass"})
        for label, mutation in (
            ("missing selection", lambda cfg, sel: cfg.pop("selection_file")),
            ("third confirmation replacement", lambda cfg, sel: cfg["campaigns"].append({**cfg["campaigns"][-1], "name": "rescue"})),
            ("stale binary", lambda cfg, sel: sel.update(binary_sha256="0"*64)),
            ("stale pilot hash", lambda cfg, sel: sel.update(screening_evidence={})),
            ("stale manifest hash", lambda cfg, sel: sel.update(manifest_sha256={})),
            ("replacement output file", lambda cfg, sel: sel["confirmation_outputs"].update(repeat="repeat_rescue.csv")),
            ("freeze after primary", lambda cfg, sel: sel.update(frozen_utc="2026-10-13T03:00:00Z")),
            ("freeze before pilot finished", lambda cfg, sel: sel.update(frozen_utc="2026-10-12T23:00:00Z")),
            ("nonadjacent selected sizes", lambda cfg, sel: sel["selected_groups"][0].update(selected_sizes=[32,128])),
            ("duplicate candidate", lambda cfg, sel: sel["selected_groups"].append(copy.deepcopy(sel["selected_groups"][0]))),
            ("three candidates", lambda cfg, sel: sel.update(selected_groups=sel["selected_groups"]*3)),
            ("missing fresh graph", lambda cfg, sel: sel.update(graph_seeds=list(GRAPHS[:-1]))),
            ("weakened CPU rule", lambda cfg, sel: sel["criterion"].update(metrics=["wall"])),
            ("changed seed protocol", lambda cfg, sel: cfg["campaigns"][-1].update(sampling_seeds=[211])),
            ("same run twice", lambda cfg, sel: sel.update(repeat="primary")),
            ("unknown selection field", lambda cfg, sel: sel.update(override=True)),
        ):
            cfg, frozen = copy.deepcopy(config), copy.deepcopy(selection)
            mutation(cfg, frozen)
            (root / "selection.json").write_text(json.dumps(frozen))
            try: collect(cfg, root)
            except ValueError as error: checks.append({"case": label, "status": "rejected", "message": str(error)})
            else: raise ValueError("self-test accepted: " + label)
    return {"validation": "pass", "positive_checks": sum(r["status"] == "pass" for r in checks),
            "negative_checks": sum(r["status"] == "rejected" for r in checks), "checks": checks}


if __name__ == "__main__":
    try: main()
    except (ValueError, OSError, KeyError, TypeError) as error:
        print("crossover comparison: " + str(error), file=sys.stderr)
        sys.exit(1)
