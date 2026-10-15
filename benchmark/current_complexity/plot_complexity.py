#!/usr/bin/env python3
"""Plot only complete, strictly validated current-candidate complexity evidence.

Source preparation only. No data, fit, library availability or visual result is
established by this file. Use a bounded outer invocation after explicit release.
"""
import argparse
import csv
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import sys

FAMILIES = ("leaf_hierarchy4", "leaf_shuffled4", "gnm_random")
ALGORITHMS = ("kkt", "multigraph_boruvka")
GRAPHS, SAMPLERS = (19000013, 19000043), (3001, 3011)
SIZES = tuple(1 << exponent for exponent in range(10, 21))
CLOCKS = ("native_steady", "native_process_cpu", "library_manual", "library_process_cpu")
MODELS = ("(1)", "lgN", "N", "NlgN", "N^2", "N^3")
COUNTS = dict(means=3168, model_fits=1152, size_summaries=1056,
              log_log_slopes=192, adjacent_slopes=960, google_selection=24)
NAMES = dict(leaf_hierarchy4="Ordered hierarchy · m = 32n",
             leaf_shuffled4="Shuffled weights · m = 32n", gnm_random="Connected G(n,m) · m = 16n")
ALGORITHM_NAMES = dict(kkt="KKT (eighth policy)", multigraph_boruvka="Retained-edge Borůvka")
CLOCK_NAMES = dict(native_steady="Native steady wall clock", native_process_cpu="Native process CPU clock",
                   library_manual="Google Benchmark manual clock", library_process_cpu="Google Benchmark process CPU clock")
COLORS = dict(kkt="#087f8c", multigraph_boruvka="#c85f28")


def require(value, message):
    if not value: raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bind(bound, path, expected):
    path = Path(path).resolve(strict=True)
    require(type(expected) is str and len(expected) == 64, "invalid expected SHA-256")
    require(str(path) not in bound or bound[str(path)] == expected, "conflicting input hash")
    require(digest(path) == expected, "changed input: " + str(path))
    bound[str(path)] = expected
    return path


def checked_text(bound, path, expected):
    path = bind(bound, path, expected)
    text = path.read_text()
    bind(bound, path, expected)
    return text


def recheck(bound):
    for path, expected in bound.items(): bind(bound, path, expected)


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "cannot load reviewed source")
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def load_evidence(args):
    """Reuse the checked analyzer; this is not another independent raw audit."""
    own = Path(__file__).resolve()
    bound = {str(own): digest(own)}
    analyzer_path = bind(bound, args.analyzer, args.analyzer_sha256)
    collector_path = bind(bound, args.collector, args.collector_sha256)
    require(analyzer_path.parent == collector_path.parent, "analyzer/collector package differs")
    provenance_path = (args.analysis / "provenance.json").resolve(strict=True)
    provenance_text = checked_text(bound, provenance_path, digest(provenance_path))
    old_path = sys.path[:]
    try:
        sys.path.insert(0, str(analyzer_path.parent))
        analyzer = module(analyzer_path, "current_complexity_plot_analysis")
        provenance = analyzer.parse_json(provenance_text)
        for key, expected in dict(schema="current_complexity_analysis_v1", validation="pass", rows_removed=0,
                                  rows_adjusted=0, checked_curves=24, checked_raw_rows=2376, table_counts=COUNTS).items():
            require(type(provenance[key]) is type(expected) and provenance[key] == expected, "analysis metadata: " + key)
        require(provenance["schema_contract"] == analyzer.SCHEMA_CONTRACT, "analysis schema contract differs")
        for path, expected in provenance["input_sha256"].items(): bind(bound, path, expected)
        require(provenance["input_sha256"].get(str(analyzer_path)) == args.analyzer_sha256 and
                provenance["input_sha256"].get(str(collector_path)) == args.collector_sha256,
                "analysis did not bind the requested analyzer/collector")
        capture = bind(bound, provenance["capture"], provenance["capture_sha256"])
        collector = module(collector_path, "current_complexity_plot_collector")
        info, records, inherited = collector.load(capture)
        for path, expected in inherited.items(): bind(bound, path, expected)
        analyzer.validate_smoke(info, bound, analyzer_path)
        require([record["spec"] for record in records] == analyzer.schedule(), "capture schedule differs")
        require(tuple(analyzer.FAMILIES) == FAMILIES and tuple(analyzer.ALGORITHMS) == ALGORITHMS and
                tuple(analyzer.GRAPHS) == GRAPHS and tuple(analyzer.SAMPLERS) == SAMPLERS and
                tuple(analyzer.SIZES) == SIZES and tuple(analyzer.CLOCKS) == CLOCKS and tuple(analyzer.MODELS) == MODELS,
                "plot declaration differs from reviewed analysis")
        curves, flags, documents = [], [], []
        for record in records:
            raw = checked_text(bound, record["raw_csv"], record["raw_sha256"])
            log = checked_text(bound, record["log"], record["log_sha256"])
            document = analyzer.parse_json(checked_text(bound, record["benchmark_json"], record["benchmark_sha256"]))
            native, current_flags = analyzer.validate_native(raw, log, record["spec"])
            library = analyzer.validate_curve_library(document, record["spec"], native)
            curves.append(dict(spec=record["spec"], native_rows=native, library=library))
            flags.extend(current_flags)
            documents.append(dict(spec=record["spec"], context=library["context"], reports=library["reports"]))
        tables = analyzer.aggregate(curves)
        expected_files = {str((args.analysis / (name + ".csv")).resolve()) for name in COUNTS}
        expected_files |= {str((args.analysis / name).resolve()) for name in ("clock_flags.json", "library_reports.json")}
        require(set(provenance["output_sha256"]) == expected_files, "incomplete/extra canonical output inventory")
        copies = {}
        for name, rows in tables.items():
            path = (args.analysis / (name + ".csv")).resolve()
            text = checked_text(bound, path, provenance["output_sha256"][str(path)])
            reader = csv.DictReader(io.StringIO(text))
            require(reader.fieldnames == list(rows[0]), "canonical table header differs: " + name)
            expected = [{key: "" if value is None else str(value) for key, value in row.items()} for row in rows]
            require(list(reader) == expected and len(rows) == COUNTS[name], "canonical table values differ: " + name)
            copies[path.name] = text
        for name, expected in (("clock_flags.json", flags), ("library_reports.json", documents)):
            path = (args.analysis / name).resolve()
            text = checked_text(bound, path, provenance["output_sha256"][str(path)])
            require(analyzer.parse_json(text) == expected, "canonical JSON differs: " + name)
        require(provenance["clock_flag_count"] == len(flags) and provenance["flagged_call_count"] == info["flagged_calls"],
                "clock flag totals differ")
        recheck(bound)
        return tables, copies, bound, provenance
    finally:
        sys.path[:] = old_path


def identity(row):
    return tuple(row[key] for key in ("family", "algorithm", "graph_seed", "sampling_seed"))


def curve_order():
    return [(family, algorithm, graph, sampler) for family in FAMILIES for algorithm in ALGORITHMS
            for graph in GRAPHS for sampler in SAMPLERS]


def prepare(tables):
    summaries = {}
    for row in tables["size_summaries"]:
        key = (*identity(row), row["clock"], row["n"])
        require(key not in summaries, "duplicate size point")
        expected_m = row["n"] * (16 if row["family"] == "gnm_random" else 32)
        require(row["N"] == row["n"] + expected_m, "not represented input N=n+m")
        expected_scope, count = ("six_native_calls", 6) if row["clock"].startswith("native_") else ("three_library_two_call_means", 3)
        require(row["observation_scope"] == expected_scope and row["observations"] == count, "range scope differs")
        values = [row[key] / row["N"] for key in ("minimum_ns", "median_ns", "maximum_ns")]
        require(all(math.isfinite(value) and value > 0 for value in values) and values == sorted(values), "invalid normalized range")
        require(row["median_ns_per_N"] == values[1], "normalized median differs from median_ns/N")
        summaries[key] = dict(row, minimum_ns_per_N=values[0], maximum_ns_per_N=values[2])
    expected = {(*curve, clock, n) for curve in curve_order() for clock in CLOCKS for n in SIZES}
    require(set(summaries) == expected, "incomplete normalization matrix")
    low = min(row["minimum_ns_per_N"] for row in summaries.values()) * .8
    high = max(row["maximum_ns_per_N"] for row in summaries.values()) * 1.25
    require(0 < low < high < math.inf, "invalid common normalized-time limits")
    selection = {identity(row): row for row in tables["google_selection"]}
    require(len(selection) == 24 and set(selection) == set(curve_order()), "incomplete Google choices")
    fits = {}
    for row in tables["model_fits"]:
        key = (*identity(row), row["clock"], row["window"], row["model"])
        require(key not in fits and math.isfinite(row["normalized_rms"]) and row["normalized_rms"] >= 0, "invalid fit row")
        fits[key] = row
    expected_fits = {(*curve, clock, window, model) for curve in curve_order() for clock in CLOCKS
                     for window in ("full11", "upper6") for model in MODELS}
    require(set(fits) == expected_fits, "incomplete all-model/four-clock matrix")
    for curve in curve_order():
        require(selection[curve]["selected_model"] in MODELS and selection[curve]["manual_rms_exported"] is False,
                "unsupported Google selection semantics")
        for window, count in (("full11", 33), ("upper6", 18)):
            rows = [fits[(*curve, "library_process_cpu", window, model)] for model in MODELS]
            require(all(row["observations"] == count for row in rows) and
                    sum(row["selected_for_this_clock"] is True for row in rows) == 1, "invalid custom fit window")
    return summaries, fits, selection, (low, high)


def render(tables, output, provenance):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Rectangle
    from matplotlib.colors import Normalize
    summaries, fits, selection, limits = prepare(tables)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "svg.fonttype": "none", "pdf.fonttype": 42})
    realizations = [(graph, sampler) for graph in GRAPHS for sampler in SAMPLERS]
    markers = ("o", "s", "^", "D")
    plotted = dict(normalized_points=[], model_cells=[], google_choices=tables["google_selection"],
                   common_normalized_y_limits=list(limits), clock_flag_count=provenance["clock_flag_count"])
    def save(fig, name):
        for suffix in ("png", "svg", "pdf"):
            fig.savefig(output / (name + "." + suffix), dpi=180, facecolor="white")
        plt.close(fig)
    def compact(value):
        return f"{value/1e6:.2g}M" if value >= 1e6 else f"{value/1e3:.3g}K"
    for clock in CLOCKS:
        fig, axes = plt.subplots(1, 3, figsize=(15.6, 6.1), sharey=True)
        fig.subplots_adjust(left=.07, right=.985, bottom=.26, top=.80, wspace=.13)
        fig.suptitle("Current KKT complexity diagnostics — " + CLOCK_NAMES[clock], fontsize=17, y=.97)
        fig.text(.5, .905, "Time per represented input item: T / (n + m) · all 11 sizes · no pooled curve or fitted extrapolation",
                 ha="center", fontsize=10)
        for axis, family in zip(axes, FAMILIES):
            axis.set_title(NAMES[family], fontsize=12, pad=12)
            for algorithm in ALGORITHMS:
                for realization, (graph, sampler) in enumerate(realizations):
                    rows = [summaries[(family, algorithm, graph, sampler, clock, n)] for n in SIZES]
                    x = [row["N"] for row in rows]
                    y = [row["median_ns_per_N"] for row in rows]
                    low = [row["minimum_ns_per_N"] for row in rows]
                    high = [row["maximum_ns_per_N"] for row in rows]
                    require(all(limits[0] < a <= b <= c < limits[1] for a, b, c in zip(low, y, high)), "clipped time point")
                    axis.errorbar(x, y, yerr=([b-a for a,b in zip(low,y)], [c-b for b,c in zip(y,high)]),
                                  color=COLORS[algorithm], marker=markers[realization], markersize=3.8,
                                  linestyle="-" if graph == GRAPHS[0] else "--", linewidth=.85,
                                  elinewidth=.55, capsize=1.5, alpha=.72)
                    plotted["normalized_points"].extend(dict(row, display_clock=clock) for row in rows)
            axis.set_xscale("log", base=2); axis.set_yscale("log"); axis.set_ylim(*limits)
            factor = 17 if family == "gnm_random" else 33
            ticks = [factor * SIZES[index] for index in (0, 3, 6, 10)]
            axis.set_xticks(ticks, [compact(value) for value in ticks])
            axis.set_xlim(factor*SIZES[0]*.8, factor*SIZES[-1]*1.25)
            axis.set_xlabel("Represented input N = n + m")
            axis.grid(True, which="major", alpha=.22)
            axis.spines[["top", "right"]].set_visible(False)
        axes[0].set_ylabel("Nanoseconds per input item · logarithmic scale")
        handles = [Line2D([], [], color=COLORS[a], linewidth=2, label=ALGORITHM_NAMES[a]) for a in ALGORITHMS]
        handles += [Line2D([], [], color="#52616c", marker=markers[i], linestyle="-" if g==GRAPHS[0] else "--",
                           label=f"G{GRAPHS.index(g)+1}/S{SAMPLERS.index(s)+1}") for i,(g,s) in enumerate(realizations)]
        fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.5,.125), ncol=6, frameon=False, fontsize=9)
        scope = "Median and complete min–max of six native calls" if clock.startswith("native_") else "Median and complete min–max of three library two-call means"
        fig.text(.5,.057,scope+" per realization/size. Lines only connect observations; ranges are not confidence intervals.",ha="center",fontsize=9)
        fig.text(.5,.025,"G1: ascending sizes; G2: descending sizes (graph/order confounded). Two sampler seeds; all flags retained; all four figures share y limits.",ha="center",fontsize=8.5)
        save(fig, "normalized_"+clock)
    fig, axes = plt.subplots(1, 2, figsize=(15.6, 12.7), sharey=True)
    fig.subplots_adjust(left=.235, right=.91, bottom=.125, top=.885, wspace=.11)
    cells = [fits[(*curve,"library_process_cpu",window,model)]["normalized_rms"]*100
             for curve in curve_order() for window in ("full11","upper6") for model in MODELS]
    color_max = max(max(cells), 1e-12)
    labels = [f"{('Ordered' if f==FAMILIES[0] else 'Shuffled' if f==FAMILIES[1] else 'G(n,m)')} / "
              f"{('KKT' if a=='kkt' else 'retained B')} / G{GRAPHS.index(g)+1} S{SAMPLERS.index(s)+1}"
              for f,a,g,s in curve_order()]
    for axis, window in zip(axes, ("full11", "upper6")):
        grid = [[fits[(*curve,"library_process_cpu",window,model)]["normalized_rms"]*100 for model in MODELS]
                for curve in curve_order()]
        image = axis.imshow(grid, aspect="auto", cmap="YlGnBu", norm=Normalize(0,color_max), interpolation="nearest")
        axis.set_xticks(range(6), ["1","log N","N","N log N","N²","N³"])
        axis.set_yticks(range(24),labels,fontsize=9)
        axis.set_title("Full 11 sizes · Google's CPU-selected model" if window=="full11" else "Upper 6 sizes · separate custom selection",fontsize=11,pad=12)
        for index, curve in enumerate(curve_order()):
            selected = selection[curve]["selected_model"] if window=="full11" else next(
                model for model in MODELS if fits[(*curve,"library_process_cpu",window,model)]["selected_for_this_clock"])
            for column, model in enumerate(MODELS):
                value=grid[index][column]
                axis.text(column,index,format(value,".2g"),ha="center",va="center",fontsize=8.5,
                          color="white" if value > .60*color_max else "#173044")
                plotted["model_cells"].append(dict(fits[(*curve,"library_process_cpu",window,model)],
                    plotted_rms_percent=value, outlined=model==selected,
                    outline_scope="google_exported_cpu_selection" if window=="full11" else "custom_upper6_library_cpu"))
            axis.add_patch(Rectangle((MODELS.index(selected)-.46,index-.46),.92,.92,fill=False,edgecolor="#d62728",linewidth=1.7))
        for boundary in (7.5,15.5): axis.axhline(boundary,color="white",linewidth=2)
    color_axis=fig.add_axes((.93,.20,.014,.60));fig.colorbar(image,cax=color_axis,label="Normalized RMS residual (%) · lower is better")
    fig.suptitle("All 24 curves: model residuals and the actual Google Benchmark choice",fontsize=17,y=.965)
    fig.text(.5,.92,"Six zero-intercept models fitted separately to each realization; no pooling across graphs, samplers, families or algorithms.",ha="center",fontsize=10)
    fig.text(.5,.079,"Red outline: reported oAuto CPU choice (left); independently selected upper-window custom fit (right).",ha="center",fontsize=9.5)
    fig.text(.5,.052,"Google uses 33 two-call library CPU means and reuses that model for its manual coefficient. Upper-six fits use 18 means and are not built-in results.",ha="center",fontsize=9)
    fig.text(.5,.026,"Only CPU RMS is exported by Google; manual RMS is reconstructed. Four-clock/all-model fits remain in CSV. Fit labels do not prove asymptotic complexity.",ha="center",fontsize=8.8)
    save(fig,"google_cpu_models")
    require(len(plotted["normalized_points"])==1056 and len(plotted["model_cells"])==288,"plot completeness failure")
    return plotted,matplotlib.__version__


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("analysis","analyzer","collector","output-dir"):parser.add_argument("--"+key,type=Path,required=True)
    parser.add_argument("--analyzer-sha256",required=True);parser.add_argument("--collector-sha256",required=True)
    parser.add_argument("--released",action="store_true")
    args=parser.parse_args();require(args.released,"explicit nonperformance plotting release required")
    output=args.output_dir.resolve();output.mkdir(parents=True,exist_ok=False)
    metadata=dict(schema="current_complexity_figures_v1",validation="running",invocation=sys.argv,
                  source_sha256=digest(__file__),native_solver_execution=False,visual_qa="pending",
                  independent_numerical_audit=False)
    try:
        tables,copies,bound,provenance=load_evidence(args);metadata["input_sha256"]=bound
        plotted,version=render(tables,output,provenance)
        (output/"analysis_tables").mkdir()
        for name,text in copies.items():
            with (output/"analysis_tables"/name).open("x") as stream:stream.write(text)
        with (output/"plotted_values.json").open("x") as stream:json.dump(plotted,stream,indent=2,allow_nan=False)
        recheck(bound)
        metadata.update(validation="rendered_pending_visual_qa",figures=5,formats=["png","svg","pdf"],
                        matplotlib_version=version,table_counts=COUNTS,normalized_points=1056,model_cells=288,
                        google_curves=24,clock_flag_count=provenance["clock_flag_count"],
                        rows_removed=0,rows_adjusted=0)
    except BaseException as error:
        metadata.update(validation="failed",error=repr(error));raise
    finally:
        metadata["output_sha256"]={str(path.relative_to(output)):digest(path) for path in output.rglob("*") if path.is_file()}
        with (output/"provenance.json").open("x") as stream:json.dump(metadata,stream,indent=2,allow_nan=False)
    print(json.dumps({key:metadata[key] for key in ("validation","figures","normalized_points","model_cells")}))


if __name__=="__main__":main()
