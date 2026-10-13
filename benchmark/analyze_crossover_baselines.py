#!/usr/bin/env python3
"""Validate and summarize the completed three-case large-stack classical adjunct.

Uses the wrapper's exact per-case schedule/clock checker. Reports wall and CPU
separately, retains warmups and losses, and never imports compactor timings.
Matplotlib is imported only with --plot; no native program is executed.
"""
import argparse
import json
import os
from pathlib import Path
import re
import statistics
import sys

import analyze_continuation as base
import compare_crossover as comparison
import run_crossover_baselines as capture

PLAN = (("hierarchical_path", 1048576), ("line_metric", 4194304), ("grid2d_metric", 1048576))
METRICS = {"wall": "elapsed_ns", "cpu": "process_cpu_elapsed_ns"}
NAMES = {"kkt": "KKT", "kruskal": "Kruskal", "prim": "Prim", "boruvka": "Original Borůvka"}


def equal(data, key, expected, context):
    base.require(type(data.get(key)) is type(expected) and data[key] == expected, f"{context}: incorrect {key}")


def file_record(path):
    return {"path": str(path.resolve()), "sha256": capture.sha(path)}


def check_hash(path, expected, context):
    base.require(type(expected) is str and re.fullmatch(r"[0-9a-f]{64}", expected) and
                 capture.sha(path) == expected, f"{context}: file hash mismatch: {path}")


def hash_inventory(value, context):
    base.require(type(value) is dict and value and all(
        type(name) is str and name and type(digest) is str and re.fullmatch(r"[0-9a-f]{64}", digest)
        for name, digest in value.items()), f"{context}: invalid source hash inventory")


def stack_profile(path, metadata):
    stack = comparison.read_json(path)
    equal(stack, "schema", "classical_large_stack_validation_v1", "stack validation")
    equal(stack, "validation", "pass", "stack validation")
    equal(stack, "requested_stack_bytes", 536870912, "stack validation")
    equal(stack, "entire_text_byte_identical", True, "stack validation")
    equal(stack, "original_sources_binary_objects_preserved", True, "stack validation")
    base.require(stack["large_binary_sha256"] == metadata["binary_sha256"] and
                 Path(stack["large_binary"]).resolve() == Path(metadata["binary"]).resolve() and
                 stack["source_sha256"] == metadata["source_sha256"],
                 "capture binary/source differs from the validated large-stack profile")
    original, large = stack["original_macho"], stack["large_macho"]
    base.require(type(original["text_sha256"]) is str and re.fullmatch(r"[0-9a-f]{64}", original["text_sha256"]) and
                 original["text_sha256"] == large["text_sha256"] and type(original["text_size"]) is int and
                 original["text_size"] > 0 and original["text_size"] == large["text_size"] and
                 original["main_stack_size"] == 0 and large["main_stack_size"] == 536870912,
                 "large-stack text identity or stack-size record is inconsistent")
    for key, value in (("validation", "pass"), ("vertices", 4194304), ("edges", 4194303),
                       ("validated_output_tuples", 4194303), ("weight_sum", 8796090925056),
                       ("forced_maximum_dfs_depth", 4194304)):
        equal(stack["worst_path_result"], key, value, "worst-depth validation")
    base.require(type(stack["commands"]) is list and stack["commands"], "missing stack validation commands")
    for command in stack["commands"]:
        equal(command, "exit_status", 0, "stack validation command")
        for channel in ("stdout", "stderr"):
            check_hash(path.parent / command[channel], command[channel + "_sha256"], "stack validation log")
    for name, field in (("validation_driver.py.txt", "validation_driver_sha256"),
                        ("worst_depth_path.cpp.txt", "test_source_sha256")):
        check_hash(path.parent / name, stack[field], "stack validation source")
    return stack


def load(timing_path, manifest_path, stack_path):
    metadata_path = timing_path.with_suffix(".json")
    metadata = comparison.read_json(metadata_path)
    for field, expected in (("schema", "crossover_classical_capture_v1"), ("validation", "pass"),
                            ("graph_seed", 3037), ("kkt_seed", 101), ("repetitions", 4), ("warmups", 1),
                            ("rows_removed", 0), ("rows_adjusted", 0), ("checked_rows", 60),
                            ("checked_timed_rows", 48), ("checked_warmup_rows", 12)):
        equal(metadata, field, expected, "classical capture")
    base.require("error" not in metadata, "capture retains a failure status")
    for field in ("revision", "profile", "platform", "machine"):
        base.require(type(metadata.get(field)) is str and metadata[field], "capture: missing " + field)
    base.require(type(metadata.get("binary_sha256")) is str and
                 re.fullmatch(r"[0-9a-f]{64}", metadata["binary_sha256"]), "capture: invalid binary hash")
    hash_inventory(metadata.get("source_sha256"), "C++ capture")
    hash_inventory(metadata.get("python_source_sha256"), "Python capture")
    base.require(all(name in metadata["source_sha256"] for name in comparison.prior.PRODUCTION_FILES),
                 "capture: incomplete production source inventory")
    helper_names = {Path(name).name for name in metadata["python_source_sha256"]}
    base.require(helper_names == {"run_crossover_baselines.py", "run_crossover.py", "crossover_clocks.py",
                                  "analyze_continuation.py"} and len(metadata["python_source_sha256"]) == 4,
                 "capture: incorrect Python wrapper/validator inventory")
    capture_start = comparison.prior.timestamp(metadata.get("started_utc"), "capture start")
    capture_finish = comparison.prior.timestamp(metadata.get("finished_utc"), "capture finish")
    base.require(capture_finish > capture_start, "capture: invalid enclosing UTC interval")
    cases = base.load_manifest(manifest_path)
    wanted = [base.case_id({"family": f, "n": n, "density": 16, "intrusion_per_mille": 0}) for f, n in PLAN]
    base.require(list(cases) == wanted and metadata["case_order"] == wanted and
                 metadata["algorithms"] == list(capture.ALGORITHMS), "incorrect fixed adjunct case/algorithm matrix")
    base.require(Path(metadata["manifest"]).resolve() == manifest_path.resolve(), "capture manifest path differs")
    check_hash(timing_path, metadata["output_sha256"], "combined capture")
    check_hash(manifest_path, metadata["manifest_sha256"], "capture manifest")
    reference_path = Path(metadata["reference_timing_csv"])
    check_hash(reference_path, metadata["reference_timing_sha256"], "original discovery reference")
    reference = capture.reference_fingerprints(reference_path, cases, 3037)
    stack = stack_profile(stack_path, metadata)
    base.require(type(metadata["captures"]) is list and len(metadata["captures"]) == 3,
                 "incomplete per-case capture provenance")
    rows, diagnostics, inputs = [], [], {}
    previous_finish = None
    for index, ((case, spec), recorded) in enumerate(zip(cases.items(), metadata["captures"]), 1):
        for field, expected in (("case_id", case), ("exit_status", 0), ("interruption", None),
                                ("validation", "pass"), ("rows", 20)):
            equal(recorded, field, expected, f"capture{index}")
        raw = timing_path.with_name(timing_path.stem + "_cases") / f"{index:02d}_{case}.csv"
        log = raw.with_suffix(".log")
        base.require(Path(recorded["csv"]).resolve() == raw.resolve() and Path(recorded["log"]).resolve() == log.resolve(),
                     "per-case capture path differs from the complete rerun")
        check_hash(raw, recorded["output_sha256"], case)
        check_hash(log, recorded["log_sha256"], case)
        expected_command = [metadata["binary"], "--family", spec["family"], "--n", str(spec["n"]),
            "--density", "16", "--graph-seed", "3037", "--kkt-seed", "101", "--repetitions", "4", "--warmups", "1"]
        base.require(recorded["command"] == expected_command, "per-case command differs from the frozen protocol")
        start = comparison.prior.timestamp(recorded["started_utc"], case + " start")
        finish = comparison.prior.timestamp(recorded["finished_utc"], case + " finish")
        base.require(capture_start <= start < finish <= capture_finish and
                     (previous_finish is None or start >= previous_finish),
                     "case captures overlap, reverse or escape the enclosing interval")
        previous_finish = finish
        checked, flags = capture.check_rows(raw, spec, 3037, 101, 4, 1, reference)
        for field in ("input_fingerprint", "topology_fingerprint"):
            equal(recorded, field, checked[0][field], case)
        equal(recorded, "flagged_calls", sum(bool(r["diagnostic_flags"]) for r in flags), case)
        expected_medians = {a: {field: statistics.median(r[field] for r in checked
            if r["phase"] == "timed" and r["algorithm"] == a) for field in METRICS.values()} for a in capture.ALGORITHMS}
        base.require(recorded["timed_medians"] == expected_medians, "wrapper medians differ from raw observations")
        rows.extend(checked); diagnostics.extend(flags)
        inputs[case + "_csv"], inputs[case + "_log"] = file_record(raw), file_record(log)
    base.check_fingerprints(rows)
    combined = list(base.read_csv(timing_path, capture.FIELDS))
    base.require(len(combined) == len(rows) == 60 and all(
        all(raw[field] == str(expected[field]) for field in capture.FIELDS)
        for (_, raw), expected in zip(combined, rows)), "combined CSV differs from complete ordered per-case captures")
    base.require(metadata["call_diagnostics"] == diagnostics, "wrapper diagnostic records differ from raw clocks")
    equal(metadata, "flagged_calls", sum(bool(r["diagnostic_flags"]) for r in diagnostics), "capture flags")
    inputs.update(timing_csv=file_record(timing_path), capture_metadata=file_record(metadata_path),
                  manifest=file_record(manifest_path), reference_timing_csv=file_record(reference_path),
                  stack_provenance=file_record(stack_path))
    return cases, rows, diagnostics, metadata, stack, inputs


def aggregate(cases, rows):
    summary, pairs, comparisons = [], [], []
    for metric, field in METRICS.items():
        for case, spec in cases.items():
            timed = {(r["algorithm"], r["repetition"]): r for r in rows if r["case_id"] == case and r["phase"] == "timed"}
            for algorithm in capture.ALGORITHMS:
                values = [timed[algorithm, repetition][field] for repetition in range(4)]
                summary.append({"metric": metric, **spec, "algorithm": algorithm, "graph_seed": 3037, "kkt_seed": 101,
                    "repetitions": 4, "warmups": 1, "median_ns": statistics.median(values),
                    "minimum_ns": min(values), "maximum_ns": max(values)})
                if algorithm == "kkt": continue
                selected = []
                for repetition in range(4):
                    kkt, baseline = timed["kkt", repetition], timed[algorithm, repetition]
                    row = {"metric": metric, **spec, "baseline": algorithm, "graph_seed": 3037, "kkt_seed": 101,
                        "repetition": repetition, "kkt_order": kkt["order"], "baseline_order": baseline["order"],
                        "kkt_ns": kkt[field], "baseline_ns": baseline[field], "kkt_over_baseline": kkt[field]/baseline[field]}
                    pairs.append(row); selected.append(row)
                ratios = [r["kkt_over_baseline"] for r in selected]
                comparisons.append({"metric": metric, **spec, "baseline": algorithm, "paired_median_ratio": statistics.median(ratios),
                    "minimum_pair_ratio": min(ratios), "maximum_pair_ratio": max(ratios),
                    "kkt_slower_pairs": sum(r > 1 for r in ratios), "equal_pairs": sum(r == 1 for r in ratios), "pairs": 4})
    return summary, pairs, comparisons


def plot(summary, cases, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    colors = ("#7946A5", "#138478", "#C26B20", "#277BA8")
    files = []
    plt.rcParams.update({"font.size": 10, "svg.fonttype": "none", "pdf.fonttype": 42})
    for metric in METRICS:
        fig, axes = plt.subplots(1, 3, figsize=(13, 4.6))
        for axis, (case, spec) in zip(axes, cases.items()):
            values = [next(r for r in summary if r["metric"] == metric and r["case_id"] == case and r["algorithm"] == a)
                      for a in capture.ALGORITHMS]
            medians = [r["median_ns"]/1e9 for r in values]
            axis.bar(range(4), medians, color=colors)
            axis.errorbar(range(4), medians, yerr=[[m-r["minimum_ns"]/1e9 for m,r in zip(medians, values)],
                          [r["maximum_ns"]/1e9-m for m,r in zip(medians, values)]], fmt="none", ecolor="#25303A", capsize=4)
            axis.set_xticks(range(4), [NAMES[a] for a in capture.ALGORITHMS], rotation=22, ha="right")
            axis.set_title(f"{spec['family']}\nn={spec['n']:,}; m=16n", fontsize=10)
            axis.set_yscale("log"); axis.set_ylabel("Seconds per call (log; lower is better)")
            axis.spines[["top", "right"]].set_visible(False); axis.grid(axis="y", alpha=.2); axis.set_axisbelow(True)
        fig.suptitle("Classical adjunct · " + ("steady elapsed time" if metric == "wall" else "process CPU diagnostic"), fontsize=14)
        fig.text(.015, .018, "One graph per case; four rotated repetitions. Whiskers: observed trial range, not confidence intervals.\n"
                 "All four solvers use the separate 512 MiB stack executable. Original Borůvka is not the compacting continuation.", fontsize=8)
        fig.tight_layout(rect=(0,.13,1,.93))
        for extension in ("png", "svg", "pdf"):
            path = output / f"classical_{metric}.{extension}"; fig.savefig(path, dpi=190, bbox_inches="tight")
            if extension == "svg": path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
            files.append(path.name)
        plt.close(fig)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("timing-csv", "manifest", "stack-provenance"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()
    base.require(args.validate_only or args.output_dir is not None, "--output-dir is required unless --validate-only")
    cases, rows, diagnostics, captured, stack, inputs = load(args.timing_csv.resolve(), args.manifest.resolve(), args.stack_provenance.resolve())
    summary, pairs, comparisons = aggregate(cases, rows)
    metadata = {"schema": "crossover_classical_analysis_v1", "validation": "pass", "cases": 3,
        "timed_rows": 48, "warmup_rows": 12, "rows_removed": 0, "rows_adjusted": 0,
        "flagged_calls": captured["flagged_calls"], "inputs": inputs,
        "capture_binary_sha256": captured["binary_sha256"], "capture_source_sha256": captured["source_sha256"],
        "capture_python_source_sha256": captured["python_source_sha256"],
        "stack_profile": stack["profile"], "stack_bytes": stack["requested_stack_bytes"],
        "source_sha256": {Path(module.__file__).name: capture.sha(module.__file__) for module in
                          (base, capture, comparison, comparison.prior, comparison.clocks)},
        "script_sha256": capture.sha(__file__),
        "scope": "Selected single-graph adjunct only. Original Boruvka differs from compacting Boruvka. No cross-campaign timing pooling."}
    if args.validate_only: print(json.dumps(metadata, indent=2, allow_nan=False)); return
    output = args.output_dir; output.mkdir(parents=True, exist_ok=True)
    for row in diagnostics: row["diagnostic_flags"] = ";".join(row["diagnostic_flags"])
    for name, values in (("algorithm_summary", summary), ("paired_ratios", pairs), ("comparisons", comparisons),
                         ("validated_calls", rows), ("call_diagnostics", diagnostics)):
        base.write_csv(output / (name + ".csv"), values)
    metadata["figures"] = plot(summary, cases, output) if args.plot else []
    (output / "provenance.json").write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n")
    report = ["# Selected classical baselines: separate large-stack profile", "",
        "Validated all three declared cases, 48 timed calls and 12 checked warmups. The original-stack capture failed "
        "and remains separate; this is the complete 512 MiB stack rerun. The archived stack validation records "
        "byte-identical executable __TEXT,__text and a correct worst-depth four-million-vertex path. No algorithm "
        "source change is claimed. Every solver in this rerun uses the same large-stack executable.", "",
        "One graph seed 3037 and KKT seed 101, four fully rotated timed repetitions, one warmup. Steady elapsed time "
        "is primary; process CPU is a secondary enclosing-clock diagnostic. Trial minima/maxima are descriptive "
        "ranges, not confidence intervals. All flags and individual losses remain. These selected inputs do not "
        "establish a population ranking or an asymptotic crossover.", "",
        "The original public Borůvka below is not compacting Borůvka. KKT returns an ID set while the classical "
        "algorithms return edge tuples; their public input boundaries are retained. No absolute timings from the "
        "compactor campaigns are imported or paired with this rerun.", ""]
    for metric in METRICS:
        report += [f"## {metric.upper()}: algorithm times", "", "| Case | Algorithm | Median seconds | Trial range seconds |",
                   "|---|---|---:|---:|"]
        for row in summary:
            if row["metric"] == metric:
                report.append(f"| {row['case_id']} | {NAMES[row['algorithm']]} | {row['median_ns']/1e9:.4f} | "
                              f"{row['minimum_ns']/1e9:.4f}–{row['maximum_ns']/1e9:.4f} |")
        report += ["", "| Case | KKT / baseline | Paired median | Pair range | KKT losses / pairs |", "|---|---|---:|---:|---:|"]
        for row in comparisons:
            if row["metric"] == metric:
                report.append(f"| {row['case_id']} | {NAMES[row['baseline']]} | {row['paired_median_ratio']:.4f} | "
                              f"{row['minimum_pair_ratio']:.4f}–{row['maximum_pair_ratio']:.4f} | {row['kkt_slower_pairs']}/4 |")
        report.append("")
    report += ["Ratios pair calls within a repetition before taking their median. This need not equal the ratio "
               "of the separately displayed algorithm medians. Warmups are retained in validated_calls.csv but excluded "
               "from the timed summaries. Reference matching checks the selected graph fingerprints; full discovery "
               "protocol validation belongs to its separate screen analysis.", "",
               f"Clock flags: {captured['flagged_calls']}; no flagged calls removed. Absence of flags does not establish thermal/power control.", "",
               "[Algorithm summary](algorithm_summary.csv), [all paired ratios](paired_ratios.csv), "
               "[comparisons](comparisons.csv), [all calls including warmups](validated_calls.csv), "
               "[clock diagnostics](call_diagnostics.csv), [provenance](provenance.json).", ""]
    for name in ("timing_csv", "capture_metadata", "manifest", "reference_timing_csv", "stack_provenance"):
        report.append(f"- [{name}]({os.path.relpath(inputs[name]['path'], output.resolve())})")
    for name in metadata["figures"]:
        if name.endswith(".png"): report += ["", f"![{name}]({name})"]
    (output / "report.md").write_text("\n".join(report).rstrip() + "\n")
    print(f"Validated 48 timed and 12 warmup classical calls; wrote {output}")


if __name__ == "__main__":
    try: main()
    except (ValueError, OSError, KeyError, TypeError) as error:
        print("classical analysis: " + str(error), file=sys.stderr); sys.exit(1)
