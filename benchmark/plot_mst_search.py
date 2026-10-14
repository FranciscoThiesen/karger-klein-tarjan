#!/usr/bin/env python3
"""Render validated five-solver analyses after native capture has stopped.

Each --analysis-dir is a separate campaign: no pooling, smoothing, omitted
families or loss filtering. Matplotlib is imported only when rendering starts.
This derived-table integrity check does not replace analyze_mst_search.py.
"""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re

ALGORITHMS = ("kkt", "compacting_boruvka", "kruskal", "prim", "boruvka")
METRICS = ("wall", "cpu")
IDENTITY = ("case_id", "family", "n", "m", "density", "intrusion_per_mille")
COMPARISON_FIELDS = (*IDENTITY, "metric", "competitor", "median_paired_ratio",
    "graph_min_ratio", "graph_max_ratio", "trial_min_ratio", "trial_max_ratio",
    "individual_wins", "individual_losses", "individual_ties", "graph_seeds", "pairs")
SUMMARY_FIELDS = (*IDENTITY, "metric", "algorithm", "median_ns", "graph_min_ns",
    "graph_max_ns", "trial_min_ns", "trial_max_ns", "graph_seeds", "timed_calls")
LABELS = {"kkt": "KKT", "compacting_boruvka": "Compacting Borůvka",
          "kruskal": "Kruskal", "prim": "Prim", "boruvka": "Original Borůvka"}
COLORS = {"kkt": "#161616", "compacting_boruvka": "#0072B2", "kruskal": "#D55E00",
          "prim": "#009E73", "boruvka": "#CC79A7"}
MARKERS = {"kkt": "*", "compacting_boruvka": "o", "kruskal": "s", "prim": "^", "boruvka": "D"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def read_json(path):
    def invalid(value):
        raise ValueError("nonfinite JSON constant: " + value)
    return json.loads(path.read_text(), object_pairs_hook=json_pairs, parse_constant=invalid)


def integer(value, context):
    require(type(value) is str and re.fullmatch(r"[0-9]+", value), context + ": expected decimal integer")
    return int(value)


def positive(value, context):
    result = float(value)
    require(math.isfinite(result) and result > 0, context + ": expected positive finite value")
    return result


def read_csv(path, fields):
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        require(tuple(reader.fieldnames or ()) == fields, str(path) + ": unexpected header")
        for line, row in enumerate(reader, 2):
            require(None not in row and all(value is not None for value in row.values()),
                    f"{path}:{line}: malformed row")
            yield row


def check_identity(row, context):
    result = {field: row[field] for field in IDENTITY}
    for field in IDENTITY[2:]:
        result[field] = integer(row[field], context + " " + field)
    n, m, d = result["n"], result["m"], result["density"]
    require(re.fullmatch(r"[a-z][a-z0-9_]{0,63}", result["family"]), context + ": invalid family")
    require(32 <= n <= 2**22 and n & (n-1) == 0 and 1 <= d <= 512 and m == n*d and
            m <= min(2**27, n*(n-1)//2) and result["intrusion_per_mille"] == 0,
            context + ": invalid graph dimensions")
    require(result["case_id"] == f'{result["family"]}_n{n}_d{d}_p0', context + ": inconsistent case ID")
    return result


def nested_range(row, fields, context):
    values = [positive(row[field], context + " " + field) for field in fields]
    require(all(a <= b for a, b in zip(values, values[1:])), context + ": invalid observed range")
    return dict(zip(fields, values))


def load_campaign(directory):
    directory = directory.resolve(strict=True)
    provenance_path = directory / "provenance.json"
    provenance = read_json(provenance_path)
    require(type(provenance) is dict and provenance.get("schema") == "mst_search_analysis_v1" and
            provenance.get("validation") == "pass" and provenance.get("rows_removed") == 0 and
            provenance.get("rows_adjusted") == 0, "expected complete validated five-solver analysis")
    metadata = provenance.get("capture_metadata")
    require(type(metadata) is dict and metadata.get("schema") == "mst_search_capture_v1" and
            metadata.get("validation") == "pass" and metadata.get("algorithms") == list(ALGORITHMS),
            "invalid captured five-solver protocol")
    case_order = metadata.get("case_order")
    require(type(case_order) is list and case_order and all(type(c) is str for c in case_order) and
            len(set(case_order)) == len(case_order) and provenance.get("cases") == len(case_order),
            "invalid captured case menu")
    seed_counts = []
    for field in ("graph_seeds", "sampling_seeds"):
        values = metadata.get(field)
        require(type(values) is list and values and all(type(v) is int and 0 <= v < 2**32 for v in values)
                and len(set(values)) == len(values), "invalid seed bank: " + field)
        seed_counts.append(len(values))
    repetitions, warmups = metadata.get("repetitions"), metadata.get("warmups")
    require(type(repetitions) is int and 5 <= repetitions <= 100 and repetitions % 5 == 0 and
            type(warmups) is int and 1 <= warmups <= 100, "invalid repetition/warmup protocol")
    trials = math.prod(seed_counts) * repetitions
    require(provenance.get("timed_rows") == len(case_order)*5*trials and
            provenance.get("warmup_rows") == len(case_order)*5*math.prod(seed_counts)*warmups,
            "analysis counts do not match captured protocol")
    hashes = provenance.get("derived_sha256")
    require(type(hashes) is dict, "missing analysis table hashes")
    inputs = {str(provenance_path): sha(provenance_path)}
    for name in ("comparisons.csv", "summary.csv"):
        path = directory/name
        require(type(hashes.get(name)) is str and re.fullmatch(r"[0-9a-f]{64}", hashes[name]) and
                sha(path) == hashes[name], "derived table hash mismatch: " + str(path))
        inputs[str(path)] = hashes[name]

    identities, comparisons, summaries = {}, {}, {}
    for raw in read_csv(directory/"comparisons.csv", COMPARISON_FIELDS):
        context = "comparison " + raw["case_id"]
        identity = check_identity(raw, context)
        case = identity["case_id"]
        require(case in case_order and (case not in identities or identities[case] == identity),
                context + ": identity differs across rows")
        identities[case] = identity
        metric, algorithm = raw["metric"], raw["competitor"]
        key = (case, metric, algorithm)
        require(metric in METRICS and algorithm in ALGORITHMS[1:] and key not in comparisons,
                context + ": duplicate or unknown metric/comparator")
        row = {**identity, "metric": metric, "competitor": algorithm,
               **nested_range(raw, ("trial_min_ratio", "graph_min_ratio", "median_paired_ratio",
                                    "graph_max_ratio", "trial_max_ratio"), context)}
        for field in ("individual_wins", "individual_losses", "individual_ties", "graph_seeds", "pairs"):
            row[field] = integer(raw[field], context + " " + field)
        require(row["pairs"] == trials and row["graph_seeds"] == seed_counts[0] and
                sum(row[f] for f in ("individual_wins", "individual_losses", "individual_ties")) == trials,
                context + ": incomplete observed pairs")
        comparisons[key] = row
    require(set(comparisons) == {(c, m, a) for c in case_order for m in METRICS for a in ALGORITHMS[1:]},
            "comparison table omits or adds a case/metric/comparator")
    for raw in read_csv(directory/"summary.csv", SUMMARY_FIELDS):
        context = "runtime " + raw["case_id"]
        identity = check_identity(raw, context)
        case, metric, algorithm = identity["case_id"], raw["metric"], raw["algorithm"]
        key = (case, metric, algorithm)
        require(identities.get(case) == identity and metric in METRICS and algorithm in ALGORITHMS and
                key not in summaries, context + ": unknown or duplicate runtime series")
        row = {**identity, "metric": metric, "algorithm": algorithm,
               **nested_range(raw, ("trial_min_ns", "graph_min_ns", "median_ns",
                                    "graph_max_ns", "trial_max_ns"), context)}
        require(integer(raw["graph_seeds"], context) == seed_counts[0] and
                integer(raw["timed_calls"], context) == trials, context + ": missing runtime observations")
        summaries[key] = row
    require(set(summaries) == {(c, m, a) for c in case_order for m in METRICS for a in ALGORITHMS},
            "runtime table omits or adds a case/metric/algorithm")
    groups = defaultdict(list)
    for case in case_order:
        spec = identities[case]
        groups[(spec["family"], spec["density"])].append(spec)
    for specs in groups.values():
        specs.sort(key=lambda spec: spec["n"])
        require(len({spec["n"] for spec in specs}) == len(specs), "duplicate size within a family/density")
    label = directory.parent.name + "/" + directory.name
    return {"directory": directory, "label": label, "metadata": metadata, "groups": groups,
            "comparisons": comparisons, "summaries": summaries, "input_sha256": inputs,
            "cases": len(case_order), "trials_per_algorithm_case": trials}


def limits(campaigns, group, metric, ratios):
    # The same family/density uses matching limits in separate campaign figures.
    values, sizes = ([0.9, 1.0] if ratios else []), set()
    for campaign in campaigns:
        for spec in campaign["groups"].get(group, []):
            sizes.add(spec["n"])
            for algorithm in ALGORITHMS[1:] if ratios else ALGORITHMS:
                row = campaign["comparisons" if ratios else "summaries"][(spec["case_id"], metric, algorithm)]
                suffix = "ratio" if ratios else "ns"
                factor = 1 if ratios else 1e-9
                values.extend([row["trial_min_"+suffix]*factor, row["trial_max_"+suffix]*factor])
    low, high = min(values), max(values)
    pad = math.exp(max(0.08, math.log(high/low)*0.10))
    return sorted(sizes), (low/pad, high*pad)


def save_figure(figure, output, name):
    paths = []
    for extension in ("png", "svg", "pdf"):
        path = output/(name+"."+extension)
        figure.savefig(path, dpi=180, facecolor="white")
        paths.append(path.name)
    return paths


def render_pages(plt, Line2D, FixedLocator, FuncFormatter, campaigns, campaign, index, metric, output, ratios):
    groups = sorted(campaign["groups"])
    figures = []
    algorithms = ALGORITHMS[1:] if ratios else ALGORITHMS
    metric_name = "Steady elapsed time (primary)" if metric == "wall" else "Process CPU time (secondary)"
    kind = "paired_ratios" if ratios else "runtimes"
    for start in range(0, len(groups), 6):
        page_groups = groups[start:start+6]
        columns = min(2, len(page_groups)); rows = math.ceil(len(page_groups)/columns)
        figure, axes = plt.subplots(rows, columns, figsize=(13, 3.4*rows+2.3), squeeze=False)
        figure.subplots_adjust(left=.085, right=.97, top=.80 if rows == 1 else .86,
                               bottom=.18 if rows == 1 else .13,
                               hspace=.49, wspace=.28)
        for axis, group in zip(axes.flat, page_groups):
            family, density = group
            specs = campaign["groups"][group]
            for algorithm in algorithms:
                selected = [campaign["comparisons" if ratios else "summaries"][(spec["case_id"], metric, algorithm)]
                            for spec in specs]
                factor = 1 if ratios else 1e-9
                median = "median_paired_ratio" if ratios else "median_ns"
                suffix = "ratio" if ratios else "ns"
                x = [row["n"] for row in selected]
                y = [row[median]*factor for row in selected]
                error = [[row[median]*factor-row["trial_min_"+suffix]*factor for row in selected],
                         [row["trial_max_"+suffix]*factor-row[median]*factor for row in selected]]
                axis.errorbar(x, y, yerr=error, color=COLORS[algorithm], marker=MARKERS[algorithm],
                              markersize=5.5, linewidth=1.4, elinewidth=.85, capsize=2.2,
                              alpha=.93, label=LABELS[algorithm], zorder=3)
            sizes, bounds = limits(campaigns, group, metric, ratios)
            axis.set_xscale("log", base=2)
            axis.set_yscale("log", base=2 if ratios else 10)
            axis.set_xlim(sizes[0]/1.25, sizes[-1]*1.25)
            axis.set_ylim(*bounds)
            axis.xaxis.set_major_locator(FixedLocator(sizes))
            axis.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"$2^{{{int(round(math.log2(x)))}}}$"))
            axis.tick_params(axis="both", labelsize=8)
            axis.set_xlabel("Vertices n (log scale)", fontsize=9)
            axis.set_ylabel("KKT / comparator (log scale)" if ratios else "Seconds (log scale)", fontsize=9)
            axis.set_title(f"{family}\nm = {density}n", fontsize=11)
            axis.grid(True, which="major", alpha=.20, linewidth=.6)
            if ratios:
                axis.axhline(1, color="#303030", linestyle="--", linewidth=1, zorder=2)
                axis.axhline(.9, color="#777777", linestyle=":", linewidth=1, zorder=2)
        for axis in list(axes.flat)[len(page_groups):]:
            axis.set_visible(False)
        handles = [Line2D([], [], color=COLORS[a], marker=MARKERS[a], markersize=5,
                          linewidth=1.4, label=LABELS[a]) for a in algorithms]
        if ratios:
            handles += [Line2D([], [], color="#303030", linestyle="--", label="Parity: 1.0"),
                        Line2D([], [], color="#777777", linestyle=":", label="10% lower: 0.9")]
        figure.legend(handles=handles, loc="lower center", bbox_to_anchor=(.5, .061),
                      ncol=3 if ratios else 5, frameon=False, fontsize=9)
        protocol = campaign["metadata"]
        counts = (f"{len(protocol['graph_seeds'])} graph seed(s) × "
                  f"{len(protocol['sampling_seeds'])} sampling seed(s) × "
                  f"{protocol['repetitions']} timed repetitions; "
                  f"{protocol['warmups']} checked warmup(s) per algorithm")
        figure.suptitle(f"{campaign['label']}\n{metric_name} — " +
                        ("paired KKT ratios; below 1 favors KKT" if ratios else "separate algorithm runtimes") +
                        "\n" + counts, y=.98, fontsize=12)
        figure.text(.5, .018,
                     "Markers: hierarchical medians. Error bars: observed individual-trial min–max, not confidence intervals.\n"
                     "Lines only connect measured sizes; no smoothing or inferred crossover. Campaigns remain separate.",
                     ha="center", va="bottom", fontsize=8.5)
        name = f"campaign_{index:02d}_{metric}_{kind}_{start//6+1:02d}"
        paths = save_figure(figure, output, name)
        plt.close(figure)
        figures.append({"campaign_index": index, "campaign": campaign["label"], "metric": metric, "kind": kind,
                        "groups": [{"family": family, "density": density} for family, density in page_groups],
                        "files": paths})
    return figures


def render_schematic(plt, Line2D, output):
    """An explicitly invented b=2 graph substitution, not an exported fixture."""
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    points = {(u, clone): (u, .32 if clone else -.32) for u in range(4) for clone in range(2)}
    core = [(0, 1), (1, 2), (2, 3)]
    background = [(0, 3)]
    for u, v in core + background:
        color = "#989898" if (u, v) in core else "#D55E00"
        for a in range(2):
            for b in range(2):
                x1, y1 = points[u, a]; x2, y2 = points[v, b]
                if (u, v) in background:
                    # Route long edges away from unrelated clone vertices.
                    height = .52+.09*(2*a+b)
                    axes[0].plot([x1, x1-.15, x2+.15, x2], [y1, height, height, y2],
                                 color=color, alpha=.45, linewidth=1, zorder=1)
                else:
                    axes[0].plot([x1, x2], [y1, y2], color=color, alpha=.37, linewidth=1, zorder=1)
    for u in range(4):
        axes[0].plot([u, u], [-.32, .32], color="#0072B2", linewidth=3, zorder=2)
        axes[0].scatter([u, u], [-.32, .32], s=85, c="#0072B2", edgecolors="white", zorder=3)
        axes[0].text(u, -.6, f"clone group {u}", ha="center", fontsize=9)
    for u, v in core:
        axes[1].plot([u, v], [0, 0], color="#555555", linewidth=2)
    # Routing a heavy shortcut above the core is a drawing convention only.
    axes[1].plot([0, 0, 3, 3], [0, .55, .55, 0], color="#D55E00", linewidth=1.4)
    axes[1].scatter(range(4), [0]*4, s=130, c="#0072B2", edgecolors="white", zorder=3)
    for u in range(4):
        axes[1].text(u, -.27, f"core {u}", ha="center", fontsize=9)
    axes[1].text(.5, .13, "lower tier", ha="center", fontsize=9)
    axes[1].text(1.5, -.49, "higher tier", ha="center", fontsize=9)
    axes[1].text(2.5, .13, "lower tier", ha="center", fontsize=9)
    axes[0].set_title("Expanded input: cheap clone edges + complete bundles")
    axes[1].set_title("After cheap local contraction: one representative per bundle")
    for axis in axes:
        axis.set_xlim(-.5, 3.5); axis.set_ylim(-.85, 1); axis.axis("off")
    figure.suptitle("Illustrative lifted hierarchy, b = 2", fontsize=15)
    figure.legend(handles=[Line2D([], [], color="#0072B2", linewidth=3, label="Cheap clone edges"),
                           Line2D([], [], color="#777777", linewidth=2, label="Core hierarchy bundles"),
                           Line2D([], [], color="#D55E00", linewidth=2, label="Heavier background bundle")],
                  loc="lower center", bbox_to_anchor=(.5, .08), ncol=3, frameon=False)
    figure.text(.5, .025, "Conceptual drawing only: invented small layout, no measured fixture or timing data. "
                "The cheapest of each bundle's four edges survives.", ha="center", fontsize=9)
    figure.subplots_adjust(left=.04, right=.97, top=.81, bottom=.23, wspace=.15)
    paths = save_figure(figure, output, "illustrative_lifted_hierarchy")
    plt.close(figure)
    return {"kind": "illustration_only", "files": paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-dir", action="append", type=Path, required=True,
                        help="repeat for separate campaigns; each must pass analyze_mst_search.py")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--include-cpu", action="store_true", help="also render secondary process-CPU figures")
    parser.add_argument("--schematic", action="store_true", help="also draw an explicitly illustrative lifted graph")
    args = parser.parse_args()
    campaigns = [load_campaign(path) for path in args.analysis_dir]
    require(len({c["directory"] for c in campaigns}) == len(campaigns), "duplicate campaign directory")
    output = args.output_dir.resolve()
    require(not output.exists(), "refusing to overwrite existing figure evidence")

    # Deliberately lazy: authoring/inspection and import do not start a plotting
    # backend. Execute this entry point only after native captures stop.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FixedLocator, FuncFormatter
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none", "pdf.fonttype": 42})
    output.mkdir(parents=True)
    metrics = METRICS if args.include_cpu else ("wall",)
    figures = []
    for index, campaign in enumerate(campaigns, 1):
        for metric in metrics:
            for ratios in (True, False):
                figures.extend(render_pages(plt, Line2D, FixedLocator, FuncFormatter,
                                             campaigns, campaign, index, metric, output, ratios))
    if args.schematic:
        figures.append(render_schematic(plt, Line2D, output))
    text = ["# Five-solver search figures", "",
            "Each campaign remains separate. Every family/density and measured size in each validated analysis "
            "is plotted, including losses and controls. Ratio markers use median paired ratios over repetitions, "
            "then sampling seeds, then graph seeds; runtime markers use the same nesting separately for each "
            "algorithm. Ratios of runtime medians are not substituted for paired ratios.", "",
            "Error bars show the full observed individual-trial range, not a confidence interval. Sampling seeds "
            "repeat identical inputs for deterministic competitors. Connecting segments are visual guides between "
            "measured sizes, without smoothing or an estimated transition point. Ratio lines at 1 and 0.9 mark "
            "parity and a 10% lower KKT runtime; crossing a line alone is not a confirmation criterion.", "",
            "Axes are logarithmic and fitted per family/density. The same group uses matching limits across "
            "the separate campaign figures. Absolute times are included to keep ratio changes in context. "
            "No call is removed for a clock flag. Warmups are retained in the source analysis but not summarized "
            "as timed observations.", ""]
    for index, campaign in enumerate(campaigns, 1):
        info = campaign["metadata"]
        link = os.path.relpath(campaign["directory"]/"report.md", output)
        text += [f"## Campaign {index}: {campaign['label']}", "",
                 f"[Validated analysis]({link}): {campaign['cases']} cases; "
                 f"{campaign['trials_per_algorithm_case']} timed calls per algorithm/case; "
                 f"{info['flagged_calls']} flagged calls and {len(info['capture_clock_flags'])} capture UTC flags, all retained.", ""]
        for record in figures:
            if record.get("campaign_index") == index:
                text += [f"{record['metric']} / {record['kind']}: " +
                         " · ".join(f"[{Path(p).suffix[1:].upper()}]({p})" for p in record["files"]), ""]
    if args.schematic:
        text += ["## Conceptual illustration", "", "This drawing is invented and contains no benchmark observations. " +
                 " · ".join(f"[{Path(p).suffix[1:].upper()}]({p})" for p in figures[-1]["files"]), ""]
    (output/"README.md").write_text("\n".join(text))
    inputs = {path: digest for campaign in campaigns for path, digest in campaign["input_sha256"].items()}
    require(all(sha(Path(path)) == digest for path, digest in inputs.items()), "analysis changed during rendering")
    provenance = {"schema": "mst_search_figures_v1", "validation": "pass", "rows_removed": 0,
        "campaigns_pooled": False, "metrics": list(metrics), "input_sha256": inputs,
        "script_sha256": sha(Path(__file__).resolve()), "matplotlib_version": matplotlib.__version__,
        "spread": "observed individual-trial min-max; not confidence intervals", "figures": figures,
        "visual_qa": "not performed by this script; inspect the rendered images before publication",
        "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}}
    (output/"provenance.json").write_text(json.dumps(provenance, indent=2, allow_nan=False)+"\n")
    print(f"Rendered {len(figures)} figures from {len(campaigns)} separate campaigns; visual QA still required")


if __name__ == "__main__":
    main()
