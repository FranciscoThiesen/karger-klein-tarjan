#!/usr/bin/env python3
"""Validate repair benchmark CSVs and summarize matched observations.

CSV goes to stdout (or --output); validation and measurement caveats go to stderr.
Speedup always means earlier elapsed time / later elapsed time: below one is a
loss. Missing verifier.csv is reported, never replaced by an earlier phase.
"""

import argparse
import csv
import itertools
import statistics
import sys
from collections import defaultdict
from pathlib import Path


PHASES = ("original", "core_repairs", "contraction", "verifier")
COMPARISONS = (
    ("original", "verifier"),
    ("core_repairs", "contraction"),
    ("contraction", "verifier"),
)
FIELDS = (
    "series", "family", "n", "m", "graph_seed", "kkt_seed", "repetition",
    "order", "warmups", "algorithm", "elapsed_ns", "validation",
)
INTEGER_FIELDS = (
    "n", "m", "graph_seed", "kkt_seed", "repetition", "order", "warmups",
    "elapsed_ns",
)
GRAPH_SEEDS = (17, 42, 999)
KKT_SEEDS = (0, 1, 7)
REPETITIONS = (0, 1, 2)
ALGORITHMS = ("kkt", "kruskal")
EXPECTED_ROWS = 702
EXPECTED_CASES = 13


def case_key(row):
    return tuple(row[name] for name in ("series", "family", "n", "m"))


def sample_key(row):
    return case_key(row) + tuple(
        row[name] for name in ("graph_seed", "kkt_seed", "repetition", "algorithm")
    )


def load_phase(path):
    observations = {}
    with path.open(newline="") as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError(f"{path}: unexpected CSV header")
        for line, raw in enumerate(reader, 2):
            if None in raw or any(value is None for value in raw.values()):
                raise ValueError(f"{path}:{line}: malformed CSV record")
            if raw["validation"] != "pass":
                raise ValueError(f"{path}:{line}: measured MST did not pass validation")
            row = dict(raw)
            for field in INTEGER_FIELDS:
                try:
                    row[field] = int(raw[field])
                except ValueError as error:
                    raise ValueError(f"{path}:{line}: invalid integer {field}") from error
            if row["n"] < 2 or row["m"] < row["n"] - 1:
                raise ValueError(f"{path}:{line}: invalid connected graph dimensions")
            if row["elapsed_ns"] <= 0 or row["warmups"] < 0:
                raise ValueError(f"{path}:{line}: nonpositive timing or invalid warmups")
            if row["order"] not in (0, 1):
                raise ValueError(f"{path}:{line}: order must be zero or one")
            key = sample_key(row)
            if key in observations:
                raise ValueError(f"{path}:{line}: duplicate observation {key}")
            observations[key] = row
    if len(observations) != EXPECTED_ROWS:
        raise ValueError(f"{path}: expected {EXPECTED_ROWS} observations, got {len(observations)}")
    cases = {key[:4] for key in observations}
    if len(cases) != EXPECTED_CASES:
        raise ValueError(f"{path}: expected {EXPECTED_CASES} cases, got {len(cases)}")
    expected_keys = {
        case + (graph_seed, kkt_seed, repetition, algorithm)
        for case, graph_seed, kkt_seed, repetition, algorithm in itertools.product(
            cases, GRAPH_SEEDS, KKT_SEEDS, REPETITIONS, ALGORITHMS
        )
    }
    if observations.keys() != expected_keys:
        raise ValueError(f"{path}: cases do not contain the complete seed/repetition/algorithm matrix")
    for case, graph_seed, kkt_seed, repetition in itertools.product(
        cases, GRAPH_SEEDS, KKT_SEEDS, REPETITIONS
    ):
        prefix = case + (graph_seed, kkt_seed, repetition)
        orders = {observations[prefix + (algorithm,)]["order"] for algorithm in ALGORITHMS}
        if orders != {0, 1}:
            raise ValueError(f"{path}: algorithms do not have distinct execution orders for {prefix}")
    return observations


def load_phases(directory, require_all):
    phases = {}
    for phase in PHASES:
        path = directory / f"{phase}.csv"
        if not path.is_file():
            if phase != "verifier" or require_all:
                raise ValueError(f"missing input: {path}")
            print(f"Missing {path}; final-phase medians and comparisons are omitted.", file=sys.stderr)
            continue
        phases[phase] = load_phase(path)
    reference = phases["original"]
    for phase, observations in phases.items():
        if observations.keys() != reference.keys():
            raise ValueError(f"{phase}: case/seed/repetition/algorithm keys differ from original")
        for key, row in observations.items():
            if (row["order"], row["warmups"]) != (
                reference[key]["order"], reference[key]["warmups"]
            ):
                raise ValueError(f"{phase}: order/warmup settings differ from original for {key}")
    print(
        f"Validated {EXPECTED_ROWS} passing observations per phase: {', '.join(phases)}. "
        f"All {EXPECTED_CASES} cases have matched seeds, repetitions, orders, and warmups.",
        file=sys.stderr,
    )
    return phases


def sample_keys(case, algorithm):
    return [
        case + (graph_seed, kkt_seed, repetition, algorithm)
        for graph_seed, kkt_seed, repetition in itertools.product(
            GRAPH_SEEDS, KKT_SEEDS, REPETITIONS
        )
    ]


def paired_ratios(phases, earlier, later, case, algorithm):
    return [
        phases[earlier][key]["elapsed_ns"] / phases[later][key]["elapsed_ns"]
        for key in sample_keys(case, algorithm)
    ]


def summarize(phases):
    available_comparisons = [pair for pair in COMPARISONS if all(phase in phases for phase in pair)]
    fields = ["series", "family", "n", "m", "observations_per_phase_algorithm"]
    for phase in phases:
        for algorithm in ALGORITHMS:
            fields.append(f"{phase}_{algorithm}_median_ms")
    for earlier, later in available_comparisons:
        prefix = f"{earlier}_to_{later}"
        fields.extend([
            f"{prefix}_kkt_paired_speedup_median",
            f"{prefix}_kkt_slower_pairs",
            f"{prefix}_kruskal_paired_speedup_median",
        ])
    output = []
    cases = sorted({key[:4] for key in phases["original"]})
    for case in cases:
        row = dict(zip(("series", "family", "n", "m"), case))
        row["observations_per_phase_algorithm"] = 27
        for phase, observations in phases.items():
            for algorithm in ALGORITHMS:
                elapsed = [observations[key]["elapsed_ns"] for key in sample_keys(case, algorithm)]
                row[f"{phase}_{algorithm}_median_ms"] = f"{statistics.median(elapsed) / 1e6:.6f}"
        for earlier, later in available_comparisons:
            prefix = f"{earlier}_to_{later}"
            ratios = paired_ratios(phases, earlier, later, case, "kkt")
            row[f"{prefix}_kkt_paired_speedup_median"] = f"{statistics.median(ratios):.6f}"
            row[f"{prefix}_kkt_slower_pairs"] = sum(ratio < 1.0 for ratio in ratios)
            control = paired_ratios(phases, earlier, later, case, "kruskal")
            row[f"{prefix}_kruskal_paired_speedup_median"] = f"{statistics.median(control):.6f}"
        output.append(row)
    return fields, output, cases, available_comparisons


def report_caveats(phases, cases, comparisons):
    print(
        "Ratios are medians of matched earlier_ns/later_ns observations, not ratios of medians. "
        "A ratio below 1 is a regression; slower-pair counts retain individual losses.",
        file=sys.stderr,
    )
    for earlier, later in comparisons:
        controls = [
            statistics.median(paired_ratios(phases, earlier, later, case, "kruskal"))
            for case in cases
        ]
        losses = sum(
            statistics.median(paired_ratios(phases, earlier, later, case, "kkt")) < 1.0
            for case in cases
        )
        print(
            f"{earlier} -> {later}: Kruskal per-case median paired ratios span "
            f"{min(controls):.3f}x to {max(controls):.3f}x; "
            f"KKT has a median paired loss in {losses}/{len(cases)} cases.",
            file=sys.stderr,
        )
    for phase, observations in phases.items():
        repeats = defaultdict(list)
        for key, row in observations.items():
            if row["algorithm"] == "kruskal":
                # Fixed graph and sampling seed; only repetition changes.
                repeats[key[:6]].append(row["elapsed_ns"])
        repeat_spreads = [max(values) / min(values) for values in repeats.values()]
        print(
            f"{phase}: within-fixture Kruskal max/min over three repetitions has "
            f"median {statistics.median(repeat_spreads):.3f}x and maximum {max(repeat_spreads):.3f}x.",
            file=sys.stderr,
        )
    shortest = min(row["elapsed_ns"] for observations in phases.values() for row in observations.values())
    print(
        "Measurement caveats: matched seeds align workloads, not machine state across separately run phases. "
        "If Kruskal code and build flags are unchanged, its phase-to-phase movement is a useful control "
        "for cache, allocator, scheduling, thermal, and CPU-frequency effects; it is not a correction factor. "
        "Alternating algorithm order and warmups reduce some bias but do not eliminate it. "
        "steady_clock avoids wall-clock adjustments, but nanosecond units do not establish nanosecond "
        f"resolution or accuracy (shortest observation: {shortest / 1e3:.3f} us). "
        "Three repetitions are too few to establish stable confidence intervals. "
        "These finite measurements do not prove an asymptotic complexity bound.",
        file=sys.stderr,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "directory", nargs="?", type=Path,
        default=Path("benchmark/results/repair-2026-10-09"),
        help="directory containing phase CSVs (default: %(default)s)",
    )
    parser.add_argument("--output", type=Path, help="write summary CSV here instead of stdout")
    parser.add_argument("--require-all", action="store_true", help="fail if verifier.csv is absent")
    args = parser.parse_args()
    try:
        if args.output and any(
            args.output.resolve() == (args.directory / f"{phase}.csv").resolve()
            for phase in PHASES
        ):
            raise ValueError("summary output must not overwrite a raw input CSV")
        phases = load_phases(args.directory, args.require_all)
        fields, rows, cases, comparisons = summarize(phases)
        if args.output:
            with args.output.open("w", newline="") as destination:
                writer = csv.DictWriter(destination, fieldnames=fields, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
        else:
            writer = csv.DictWriter(sys.stdout, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        report_caveats(phases, cases, comparisons)
    except (OSError, ValueError) as error:
        print(f"summary error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
