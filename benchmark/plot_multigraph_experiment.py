#!/usr/bin/env python3
"""Render complete paired-experiment tables; preserve both clocks and all cases."""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.analysis.resolve(strict=True)
    output = args.output.resolve()
    assert not output.exists(), "refusing to overwrite figures"
    provenance = json.loads((source / "provenance.json").read_text())
    assert provenance["validation"] == "pass" and provenance["checked_rows"] == 1200
    for name, expected in provenance["input_sha256"].items():
        assert sha(name) == expected, f"changed raw input: {name}"
    inputs = {str(source / "provenance.json"): sha(source / "provenance.json")}

    def read(name):
        path = source / name
        inputs[str(path)] = sha(path)
        with path.open(newline="") as stream:
            return list(csv.DictReader(stream))

    variants = read("variant_comparisons.csv")
    comparisons = {v: read(v + "/comparisons.csv") for v in ("reference", "multigraph")}
    case_order = list(dict.fromkeys(r["case_id"] for r in variants))
    assert len(case_order) == 10 and len(variants) == 100
    identity = {r["case_id"]: r for r in comparisons["multigraph"]}
    labels = {"leaf_hierarchy4": "Leaf hierarchy", "leaf_distance4": "Leaf distance",
              "leaf_shuffled4": "Shuffled leaf core", "leaf_random4": "Random leaf weights",
              "lifted_hierarchy4": "Bundled hierarchy", "lifted_random4": "Random bundled weights",
              "gnm_random": "Connected G(n,m)"}
    names = [f"{labels[identity[c]['family']]}  |  n={int(identity[c]['n']):,}, d={identity[c]['density']}"
             for c in case_order]
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import TwoSlopeNorm
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    output.mkdir(parents=True)
    files = []

    def save(fig, name):
        for ext in ("png", "svg", "pdf"):
            path = output / f"{name}.{ext}"
            fig.savefig(path, dpi=180, bbox_inches="tight")
            files.append(path)
        plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(13, 6), sharey=True)
    for ax, metric, color in zip(axes, ("wall", "cpu"), ("#086788", "#188054")):
        table = {r["case_id"]: r for r in variants if r["algorithm"] == "kkt" and r["metric"] == metric}
        assert set(table) == set(case_order)
        for y, case in enumerate(case_order):
            r = table[case]
            ax.plot([float(r["trial_min_ratio"]), float(r["trial_max_ratio"])], [y, y], color="#c5cbd1", lw=2)
            ax.plot([float(r["graph_min_ratio"]), float(r["graph_max_ratio"])], [y, y], color=color, lw=5)
            ax.plot(float(r["median_paired_ratio"]), y, "o", color=color, ms=6)
        ax.axvline(1, color="#5d6266", ls="--", lw=1)
        ax.set_xlabel("Candidate KKT / reference KKT time")
        ax.set_title("Elapsed time" if metric == "wall" else "Process CPU time")
        ax.set_yticks(range(10), names)
        ax.grid(axis="x", alpha=.18)
        ax.set_xlim(left=0)
    axes[0].invert_yaxis()
    fig.suptitle("KKT with retained parallel edges: complete implementation comparison", fontsize=14)
    fig.text(.5, -.02, "Below 1 favors the candidate. Dots: median of 10 paired trials. Colored bars: two graph medians.\n"
             "Gray bars: full trial range. Both seeds, all cases and all observations retained; ranges are not confidence intervals.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .04, 1, .95))
    save(fig, "implementation_ratios")

    competitors = ("compacting_boruvka", "kruskal", "prim", "boruvka")
    competitor_names = ("Compacting\nBorůvka", "Kruskal", "Prim", "Original\nBorůvka")
    matrices = {}
    for variant in comparisons:
        for metric in ("wall", "cpu"):
            table = {(r["case_id"], r["competitor"]): float(r["median_paired_ratio"])
                     for r in comparisons[variant] if r["metric"] == metric}
            assert len(table) == 40
            matrices[variant, metric] = np.array([[table[c, comp] for comp in competitors] for c in case_order])
    bound = max(1, max(float(np.max(np.abs(np.log2(m)))) for m in matrices.values()))
    fig, axes = plt.subplots(2, 2, figsize=(13, 11), sharey=True)
    for column, variant in enumerate(("reference", "multigraph")):
        for row, metric in enumerate(("wall", "cpu")):
            ax = axes[row, column]
            data = matrices[variant, metric]
            im = ax.imshow(np.log2(data), cmap="RdBu_r", norm=TwoSlopeNorm(vmin=-bound, vcenter=0, vmax=bound), aspect="auto")
            ax.set_xticks(range(4), competitor_names)
            ax.set_yticks(range(10), names)
            ax.set_title(f"{'Reference KKT' if variant == 'reference' else 'Candidate KKT'} · {'elapsed' if metric == 'wall' else 'CPU'}")
            for y in range(10):
                for x in range(4):
                    ax.text(x, y, f"{data[y,x]:.2f}", ha="center", va="center",
                            color="white" if abs(np.log2(data[y,x])) > .6 * bound else "#18212a", fontsize=10)
    fig.suptitle("KKT / competitor time — every comparator and every case", fontsize=14)
    fig.text(.5, .01, "Below 1 (blue) favors KKT; above 1 (red) favors the comparator. Median of each graph's paired-trial median.\n"
             "Two graph seeds × five timed repetitions. Same color scale across builds and clocks; no losses omitted.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .06, .93, .96))
    cax = fig.add_axes((.94, .18, .016, .62))
    colorbar = fig.colorbar(im, cax=cax)
    ticks = [x for x in (-2, -1, 0, 1, 2, 3) if -bound <= x <= bound]
    colorbar.set_ticks(ticks, labels=[f"{2**x:g}×" for x in ticks])
    save(fig, "all_solver_ratios")
    for path, expected in inputs.items():
        assert sha(path) == expected, "figure input changed during rendering"
    record = {"schema": "multigraph_figures_v1", "validation": "pass", "input_sha256": inputs,
              "script_sha256": sha(__file__), "matplotlib_version": matplotlib.__version__,
              "cases": case_order, "rows_removed": 0, "rows_adjusted": 0,
              "output_sha256": {p.name: sha(p) for p in files}, "visual_review": "pending"}
    (output / "provenance.json").write_text(json.dumps(record, indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    main()
