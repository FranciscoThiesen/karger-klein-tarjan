#!/usr/bin/env python3
"""Compare two observed dyadic-contraction traces with the conditional expectation.

This plots edge counts, never solver times. The input is the complete compacting
trace for hierarchical_path/tree, n=524288/1048576, d=16, p=0, seeds17/42.
Evaluation uses the exact hypergeometric formula with stable log products. When
the no-hit probability is at most exp(-50), a documented tail cap avoids a huge
product. The tail error bound excludes ordinary floating-point roundoff.
"""

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


FAMILIES = ("hierarchical_path", "hierarchical_tree")
SIZES = (524288, 1048576)
SEEDS = (17, 42)
DENSITY = 16
MAX_PRODUCT_TERMS = 2_000_000
SATURATION_EXPONENT = 50
FIELDS = {
    "case_id", "family", "n", "m", "density", "intrusion_per_mille", "graph_seed",
    "input_fingerprint", "topology_fingerprint", "round", "input_vertices",
    "input_edges", "selected_edges", "output_vertices", "output_edges",
    "total_rounds", "total_selected_edges", "validation",
}
INTEGER_FIELDS = FIELDS - {"case_id", "family", "validation"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def positive_integer(value, field, line, zero=False):
    require(isinstance(value, str) and value.isascii() and value.isdecimal(),
            f"line {line}: invalid integer {field}")
    result = int(value)
    require(result >= (0 if zero else 1), f"line {line}: invalid {field}")
    return result


def load_trace(path):
    groups = defaultdict(list)
    excluded = defaultdict(int)
    seen = set()
    zero_fields = {"intrusion_per_mille", "output_vertices", "output_edges",
                   "input_fingerprint", "topology_fingerprint"}
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames is not None and len(reader.fieldnames) == len(FIELDS)
                and set(reader.fieldnames) == FIELDS, "unexpected compacting-trace schema")
        for line, raw in enumerate(reader, 2):
            require(None not in raw and all(value is not None for value in raw.values()),
                    f"line {line}: malformed CSV row")
            require(raw["validation"] == "pass", f"line {line}: failed trace validation")
            row = dict(raw)
            for field in INTEGER_FIELDS:
                row[field] = positive_integer(raw[field], field, line, field in zero_fields)
            family, n, seed = row["family"], row["n"], row["graph_seed"]
            # The archived million-vertex manifest also contains this explicitly
            # named nonhierarchical control. Its partitions need not be dyadic,
            # so the conditional model is inapplicable. Preserve the exclusion
            # in provenance rather than silently relabeling or plotting it.
            if (family == "low_path" and n == 1048576 and row["density"] == DENSITY
                    and row["intrusion_per_mille"] == 0 and seed in SEEDS):
                require(row["case_id"] == "low_path_n1048576_d16_p0", "invalid excluded control ID")
                excluded[(row["case_id"], seed)] += 1
                continue
            require(family in FAMILIES and n in SIZES and seed in SEEDS,
                    f"line {line}: unexpected family, size or graph seed")
            require(row["density"] == DENSITY and row["intrusion_per_mille"] == 0
                    and row["m"] == DENSITY * n, f"line {line}: incorrect density/weight model")
            expected_id = f"{family}_n{n}_d{DENSITY}_p0"
            require(row["case_id"] == expected_id, f"line {line}: case ID does not match dimensions")
            for field in ("input_fingerprint", "topology_fingerprint"):
                require(row[field] < 2**64, f"line {line}: invalid fingerprint")
            key = (family, n, seed)
            require((*key, row["round"]) not in seen, f"line {line}: duplicate trace round")
            seen.add((*key, row["round"]))
            groups[key].append(row)
    expected_groups = {(family, n, seed) for family in FAMILIES for n in SIZES for seed in SEEDS}
    require(set(groups) == expected_groups, "missing or unexpected complete graph traces")
    for (family, n, seed), rows in groups.items():
        rows.sort(key=lambda row: row["round"])
        rounds = n.bit_length() - 1
        require([row["round"] for row in rows] == list(range(1, rounds + 1)),
                f"{family}, n={n}, seed={seed}: missing contraction rounds")
        require(rows[0]["input_edges"] == DENSITY * n, "first round is not the original graph")
        require(len({row["input_fingerprint"] for row in rows}) == 1 and
                len({row["topology_fingerprint"] for row in rows}) == 1,
                "fixture fingerprint changes within trace")
        for i, row in enumerate(rows):
            before_n = n >> i
            after_n = 0 if before_n == 2 else before_n // 2
            require(row["input_vertices"] == before_n and row["output_vertices"] == after_n,
                    "hierarchical trace does not follow exact dyadic halving")
            require(row["selected_edges"] == before_n // 2, "incorrect selected-edge count")
            require(row["total_rounds"] == rounds and row["total_selected_edges"] == n-1,
                    "inconsistent whole-trace totals")
            require(row["input_edges"] <= before_n * (before_n-1) // 2,
                    "input graph exceeds simple-graph capacity")
            require(row["output_edges"] <= after_n * (after_n-1) // 2,
                    "output graph exceeds simple-graph capacity")
            require(row["input_edges"] >= before_n-1 and
                    (after_n == 0 or row["output_edges"] >= after_n-1),
                    "trace lost connectedness")
            require(row["output_edges"] <= row["input_edges"] - row["selected_edges"],
                    "trace does not remove selected edges")
            if i:
                require(row["input_edges"] == rows[i-1]["output_edges"],
                        "adjacent trace edge counts disagree")
        require(sum(row["selected_edges"] for row in rows) == n-1, "wrong total MST edge count")
        require(rows[-1]["output_edges"] == 0, "trace did not terminate")
    require(len(seen) == 156, "expected 156 raw contraction-round observations")
    return dict(groups), [{"case_id": case_id, "graph_seed": seed, "rows": count,
                          "reason": "Nonhierarchical low_path control; dyadic expectation does not apply."}
                         for (case_id, seed), count in sorted(excluded.items())]


def expected_residual(n, density, completed_rounds):
    """Evaluate E[m_r] for fixed backbone and uniformly drawn distinct chords.

    q=n/2^r, b=2^r, B=dn-n+1, U=C(n,2)-n+1, S=C(q,2)-(q-1).
    A non-backbone component pair has k=b² possible chords. Its no-hit
    probability is C(U-B,k)/C(U,k), equivalently C(U-k,B)/C(U,B).
    """
    require(isinstance(n, int) and not isinstance(n, bool) and n >= 4 and n & (n-1) == 0
            and isinstance(density, int) and not isinstance(density, bool) and density >= 1
            and n * density <= n * (n-1) // 2
            and isinstance(completed_rounds, int) and not isinstance(completed_rounds, bool)
            and 0 <= completed_rounds <= n.bit_length()-1, "unsupported expectation dimensions")
    m = n * density
    b = 1 << completed_rounds
    q = n // b
    B = m - n + 1
    U = n * (n-1) // 2 - n + 1
    S = q * (q-1) // 2 - q + 1
    guaranteed = q - 1
    k = b * b
    terms = 0
    tail_bound = 0.0
    if completed_rounds == 0:
        occupied = B / U
        expected = float(m)
        method = "original_graph_identity"
    elif S == 0:
        occupied = 0.0  # Irrelevant: no shortcut-only component pairs exist.
        expected = float(guaranteed)
        method = "no_shortcut_only_pairs"
    elif k > U - B:
        occupied = 1.0
        expected = float(guaranteed + S)
        method = "zero_no_hit_probability"
    elif B * k >= SATURATION_EXPONENT * U:
        # For each factor, 1-B/(U-j) <= exp(-B/U), so
        # P(no hit) <= exp(-Bk/U) <= exp(-50). The plotted approximation
        # overestimates E[m_r] by at most S*exp(-50), mathematically.
        # The numeric bound below is a floating representation of that bound;
        # no certified interval claim about libm or accumulated roundoff is made.
        occupied = 1.0
        expected = float(guaranteed + S)
        tail_bound = S * math.exp(-SATURATION_EXPONENT)
        method = "tail_capped_no_hit_le_exp_minus_50"
    else:
        require(k <= MAX_PRODUCT_TERMS, "exact product would exceed the explicit work bound")
        terms = k
        log_no_hit = math.fsum(math.log1p(-B / (U-j)) for j in range(k))
        occupied = -math.expm1(log_no_hit)
        expected = guaranteed + S * occupied
        method = "hypergeometric_log_product"
    require(math.isfinite(expected) and 0 <= expected <= q * (q-1) / 2,
            "nonfinite or impossible residual expectation")
    return {
        "completed_rounds": completed_rounds,
        "mathematical_components": q,
        "original_vertices_per_component": b,
        "guaranteed_backbone_pairs": guaranteed,
        "shortcut_only_pairs_modeled": S,
        "eligible_original_chords_per_modeled_pair": k,
        "modeled_pair_occupancy_probability_estimate": occupied,
        "expected_occupied_shortcut_only_pairs_estimate": S * occupied,
        "expected_edges_estimate": expected,
        "saturation_error_bound_edges": tail_bound,
        "numeric_method": method,
        "product_terms": terms,
    }


def make_tables(groups):
    # One model evaluation per size/round; both backbones and both graph seeds
    # share the same conditional expectation, not independent fitted curves.
    theories = {
        n: [expected_residual(n, DENSITY, r) for r in range(n.bit_length())]
        for n in SIZES
    }
    combined, summaries = [], []
    for family in FAMILIES:
        for n in SIZES:
            m = n * DENSITY
            theory_volume = math.fsum(point["expected_edges_estimate"] for point in theories[n][:-1])
            for seed in SEEDS:
                trace = groups[family, n, seed]
                observed = [row["input_edges"] for row in trace] + [trace[-1]["output_edges"]]
                actual_volume = sum(row["input_edges"] for row in trace)
                summaries.append({
                    "case_id": trace[0]["case_id"], "family": family, "n": n, "m": m,
                    "graph_seed": seed, "observed_contraction_input_edge_volume": actual_volume,
                    "expected_contraction_input_edge_volume_estimate": theory_volume,
                    "observed_volume_per_original_edge": actual_volume / m,
                    "expected_volume_per_original_edge_estimate": theory_volume / m,
                    "volume_saturation_error_bound": math.fsum(
                        point["saturation_error_bound_edges"] for point in theories[n][:-1]),
                })
                for point, actual in zip(theories[n], observed):
                    combined.append({
                        "case_id": trace[0]["case_id"], "family": family, "n": n, "m": m,
                        "density": DENSITY, "graph_seed": seed,
                        "input_fingerprint": trace[0]["input_fingerprint"],
                        "topology_fingerprint": trace[0]["topology_fingerprint"],
                        **point, "observed_edges": actual,
                        "observed_edge_fraction": actual / m,
                        "expected_edge_fraction_estimate": point["expected_edges_estimate"] / m,
                        "observed_minus_expected_edges": actual - point["expected_edges_estimate"],
                    })
    return theories, combined, summaries


def write_csv(path, rows):
    require(bool(rows), "cannot write an empty result table")
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plot(theories, groups, output_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "svg.hashsalt": "continuation-retention-v1",
                         "pdf.fonttype": 42, "ps.fonttype": 42})
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.2), sharey=True)
    for i, family in enumerate(FAMILIES):
        for j, n in enumerate(SIZES):
            ax = axes[i, j]
            m = n * DENSITY
            points = theories[n]
            rounds = [point["completed_rounds"] for point in points]
            guaranteed = [point["guaranteed_backbone_pairs"] / m for point in points]
            expected = [point["expected_edges_estimate"] / m for point in points]
            ax.fill_between(rounds, 0, guaranteed, color="#e3bd86", alpha=.7, zorder=0)
            ax.fill_between(rounds, guaranteed, expected, color="#d5e8ee", alpha=.9, zorder=0)
            ax.plot(rounds, expected, color="#18394b", linewidth=1.8, zorder=2)
            actual_volumes = []
            for seed, marker, color in ((17, "o", "#c26525"), (42, "^", "#17878c")):
                rows = groups[family, n, seed]
                observed = [row["input_edges"] / m for row in rows] + [0.0]
                actual_volumes.append(sum(row["input_edges"] for row in rows) / m)
                ax.plot(rounds, observed, linestyle="none", marker=marker, markersize=5.2,
                        markerfacecolor="none", markeredgecolor=color, markeredgewidth=1.15, zorder=3)
            model_volume = math.fsum(point["expected_edges_estimate"] for point in points[:-1]) / m
            ax.text(.98, .95, f"Sum of round inputs / m\nModel: {model_volume:.4f}\n"
                    f"Two graphs: {min(actual_volumes):.4f}–{max(actual_volumes):.4f}",
                    transform=ax.transAxes, ha="right", va="top", fontsize=9,
                    bbox={"boxstyle": "round,pad=.4", "facecolor": "white", "alpha": .9,
                          "edgecolor": "#d8e2e6"})
            title = "Hierarchical path" if family.endswith("path") else "Hierarchical tree"
            ax.set_title(f"{title} · n = {n:,}", loc="left", fontweight="bold", pad=10)
            ax.set_xlim(0, rounds[-1])
            ax.set_ylim(-.015, 1.045)
            ax.set_xticks(range(0, rounds[-1]+1, 2))
            ax.grid(axis="y", color="#dbe3e7", linewidth=.6)
            ax.set_axisbelow(True)
            ax.set_xlabel("Completed contraction rounds (0 = original input)")
            if j == 0:
                ax.set_ylabel("Remaining edges / original m")
    handles = [
        Patch(facecolor="#e3bd86", label="Guaranteed backbone component pairs"),
        Patch(facecolor="#d5e8ee", label="Occupied shortcut-only pairs: expectation"),
        Line2D([], [], color="#18394b", linewidth=1.8, label="Conditional expected total"),
        Line2D([], [], linestyle="none", marker="o", markerfacecolor="none", markeredgecolor="#c26525", label="Observed graph seed 17"),
        Line2D([], [], linestyle="none", marker="^", markerfacecolor="none", markeredgecolor="#17878c", label="Observed graph seed 42"),
    ]
    fig.suptitle("Edges retained by continued production contraction", x=.07, ha="left",
                 y=.98, fontsize=18, fontweight="bold")
    fig.text(.07, .94, "m = 16n · Zero-intrusion engineered hierarchies · A theoretical expectation and two observed graph draws", fontsize=10.5)
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.5, .043), ncol=3,
               frameon=False, fontsize=9)
    fig.text(.5, .016, "Shading decomposes expected occupied component pairs; it is not a confidence band. These are edge counts, not time predictions.",
             ha="center", fontsize=9, color="#4b606d")
    fig.subplots_adjust(left=.075, right=.98, top=.885, bottom=.165, hspace=.38, wspace=.16)
    for extension in ("png", "svg", "pdf"):
        metadata = {"Date": None} if extension == "svg" else ({"CreationDate": None, "ModDate": None} if extension == "pdf" else None)
        fig.savefig(output_dir / f"contraction_retention.{extension}", dpi=180, metadata=metadata)
    plt.close(fig)
    return matplotlib.__version__


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path, help="million_trace.csv: complete eight-graph compacting traces")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    groups, excluded = load_trace(args.trace)
    theories, combined, summaries = make_tables(groups)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "retention.csv", combined)
    write_csv(args.output_dir / "edge_volume.csv", summaries)
    matplotlib_version = plot(theories, groups, args.output_dir)
    model_points = [point for points in theories.values() for point in points]
    provenance = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "trace_path": str(args.trace.resolve()),
        "trace_sha256": hashlib.sha256(args.trace.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "raw_round_rows": sum(len(rows) for rows in groups.values()),
        "excluded_trace_groups": excluded,
        "total_source_rows": sum(len(rows) for rows in groups.values()) + sum(row["rows"] for row in excluded),
        "graph_traces": len(groups), "retention_rows_including_terminal_zero": len(combined),
        "families": list(FAMILIES), "sizes": list(SIZES), "density": DENSITY,
        "graph_seeds": list(SEEDS), "intrusion_per_mille": 0,
        "round_alignment": "Trace round1 input is model m_0. Final output adds m_log2(n)=0; production drops the final isolate.",
        "expectation": "Conditioned on a fixed dyadic backbone, over uniform B-subsets of its U eligible shortcut pairs.",
        "formula": "E[m_r]=(q-1)+(C(q,2)-q+1)*(1-C(U-B,b^2)/C(U,b^2))",
        "definitions": "q=n/2^r; b=2^r; B=16n-n+1; U=C(n,2)-n+1",
        "numeric_method": "fsum(log1p(-B/(U-j))), followed by -expm1; exact structural boundary identities",
        "saturation_rule": "If B*b^2 >= 50*U, set no-hit to0; true no-hit <=exp(-50), so expected-edge overestimate <=S*exp(-50).",
        "numeric_bound_scope": "Saturation bound is mathematical; floating values representing it are not certified rounding intervals. Ordinary floating-point roundoff is not included.",
        "max_saturation_error_bound_edges": max(point["saturation_error_bound_edges"] for point in model_points),
        "max_product_terms_used": max(point["product_terms"] for point in model_points),
        "configured_max_product_terms": MAX_PRODUCT_TERMS,
        "total_product_terms_evaluated": sum(point["product_terms"] for point in model_points),
        "plot_scope": "Shaded areas are expected pair categories, not uncertainty bands. Two graph seeds are two draws, not a fitted model or timing prediction.",
        "matplotlib_version": matplotlib_version,
    }
    (args.output_dir / "provenance.json").write_text(json.dumps(provenance, indent=2, allow_nan=False) + "\n")
    print(f"Validated {provenance['raw_round_rows']} rounds from eight graphs; wrote {args.output_dir}")


if __name__ == "__main__":
    main()
