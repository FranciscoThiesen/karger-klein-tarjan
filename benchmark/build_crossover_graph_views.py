#!/usr/bin/env python3
"""Export certified small fixtures and draw their actual geometry and contractions.

Run ONLY outside benchmark timing windows. By default this compiles the embedded
C++ exporter in TemporaryDirectory, links unchanged production implementations,
and executes five n=128,d=4 fixtures. No C++ file is written to the repository.
The fixture header must already support line_wide_metric; there is no fallback
or approximate Python generator. --reuse-data redraws a previously hashed export.
These are educational small instances, not the large measured benchmark inputs.
"""
import argparse
import collections
import colorsys
import csv
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

FAMILIES = ("line_metric", "line_wide_metric", "line_random", "grid2d_metric", "grid2d_random")
N, DENSITY, GRAPH_SEED, KKT_SEED = 128, 4, 3037, 101
SOURCES = ("kkt/kkt.cpp", "verifier/verifier_v2.cpp", "lca/lca.cpp",
           "kruskal/kruskal.cpp", "union_find/union_find.cpp")

EXPORTER = r'''#include "benchmark/crossover_fixtures.hpp"
#include "benchmark/mst_certificate.hpp"
#include "kkt/kkt.hpp"
#include "kruskal/kruskal.hpp"
#include <algorithm>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <tuple>
#include <unordered_set>
#include <vector>

#ifdef KKT_ENABLE_WORK_STATS
#error "Educational exporter must use uninstrumented production sources"
#endif
std::pair<std::vector<int>, problem> boruvka_step(const problem&);

namespace {
void require(bool ok, const char* message) {
    if (!ok) throw std::runtime_error(message);
}
void ints(const std::vector<int>& values) {
    std::cout << '[';
    for (std::size_t i=0; i<values.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << values[i];
    }
    std::cout << ']';
}

// Independent original-vertex ledger, not repository UnionFind and not the
// production quotient's component labels. Canonical names are original minima.
class Ledger {
    std::vector<int> parent, size;
public:
    explicit Ledger(int n) : parent(n), size(n,1) {
        std::iota(parent.begin(),parent.end(),0);
    }
    int find(int v) {
        while (parent[v]!=v) { parent[v]=parent[parent[v]]; v=parent[v]; }
        return v;
    }
    void join(int u, int v) {
        u=find(u);v=find(v);
        require(u!=v,"selected original IDs repeat or form a cycle");
        if (size[u]<size[v]) std::swap(u,v);
        parent[v]=u;size[u]+=size[v];
    }
    std::vector<int> membership() {
        const int n=static_cast<int>(parent.size());
        std::vector<int> minimum(n,n), result(n);
        for (int v=0;v<n;++v) minimum[find(v)]=std::min(minimum[find(v)],v);
        for (int v=0;v<n;++v) result[v]=minimum[find(v)];
        return result;
    }
};

void fixture(const char* family) {
    constexpr int n=128, density=4;
    constexpr unsigned int graph_seed=3037, kkt_seed=101;
    auto data=benchmark_crossover::make_fixture({family,n,density},graph_seed);
    const auto& graph=data.graph;
    const auto reference=kruskal(graph,n);
    benchmark_validation::certify_mst(graph,reference,n);
    std::unordered_set<int> expected;
    for (const auto& e:reference) expected.insert(std::get<3>(e));
    problem input(n,graph);
    const auto actual=kkt(input,kkt_seed);
    require(actual==expected,"production KKT disagrees with certified unique MST");
    std::vector<int> mst(expected.begin(),expected.end());
    std::sort(mst.begin(),mst.end());
    std::vector<int> inverse(n), position(graph.size(),-1);
    for (int v=0;v<n;++v) inverse[data.original_to_label[v]]=v;
    for (std::size_t i=0;i<graph.size();++i) position[std::get<3>(graph[i])]=static_cast<int>(i);
    std::cout << "{\"family\":" << std::quoted(family)
              << ",\"n\":" << n << ",\"m\":" << graph.size()
              << ",\"density\":" << density << ",\"graph_seed\":" << graph_seed
              << ",\"kkt_seed\":" << kkt_seed << ",\"certificate\":\"pass\",\"kkt_validation\":\"pass\""
              << ",\"original_to_label\":";
    ints(data.original_to_label);
    std::cout << ",\"positions\":[";
    for (int v=0;v<n;++v) {
        if (v) std::cout << ',';
        std::cout << '[' << data.original_positions[v][0] << ',' << data.original_positions[v][1] << ']';
    }
    std::cout << "],\"grid_dimensions\":[" << data.grid_dimensions[0] << ',' << data.grid_dimensions[1]
              << "],\"scaffold_ids\":";
    ints(data.backbone_ids);
    std::cout << ",\"edges\":[";
    for (std::size_t i=0;i<graph.size();++i) {
        if (i) std::cout << ',';
        const auto [u,v,w,id]=graph[i];
        std::cout << '[' << u << ',' << v << ',' << w << ',' << id << ',' << inverse[u] << ',' << inverse[v] << ']';
    }
    std::cout << "],\"mst_ids\":";ints(mst);
    std::vector<int> kkt_ids(actual.begin(),actual.end());
    std::sort(kkt_ids.begin(),kkt_ids.end());
    std::cout << ",\"kkt_ids\":";ints(kkt_ids);
    Ledger ledger(n);
    problem remaining(n,graph);
    std::cout << ",\"rounds\":[";
    for (int round=1;round<=2;++round) {
        require(remaining.num_vertices>=2 && !remaining.graph_edges.empty(),
                "fixture finished before two actual nonempty contraction calls");
        const int before_n=remaining.num_vertices;
        const auto before_m=remaining.graph_edges.size();
        auto [selected,reduced]=boruvka_step(remaining);
        for (int id:selected) {
            require(expected.count(id)==1,"contraction selected a non-MST edge");
            const auto& e=graph[position.at(id)];
            ledger.join(inverse[std::get<0>(e)],inverse[std::get<1>(e)]);
        }
        const auto membership=ledger.membership();
        const std::unordered_set<int> components(membership.begin(),membership.end());
        require(components.size()==static_cast<std::size_t>(reduced.num_vertices ? reduced.num_vertices : 1),
                "independent original membership disagrees with quotient vertex count");
        if (round>1) std::cout << ',';
        std::cout << "{\"round\":" << round << ",\"input_n\":" << before_n
                  << ",\"input_m\":" << before_m << ",\"selected_ids\":";
        ints(selected);
        std::cout << ",\"component_of_original\":";ints(membership);
        std::cout << ",\"residual_n\":" << reduced.num_vertices
                  << ",\"residual_m\":" << reduced.graph_edges.size() << ",\"residual_edges\":[";
        for (std::size_t i=0;i<reduced.graph_edges.size();++i) {
            if (i) std::cout << ',';
            const auto& e=reduced.graph_edges[i];
            std::cout << '[' << e.from << ',' << e.to << ',' << e.cost << ',' << e.id << ']';
        }
        std::cout << "],\"validation\":\"pass\"}";
        remaining=std::move(reduced);
    }
    std::cout << "]}";
}
} // namespace
int main() {
    try {
        std::cout << "{\"schema\":\"crossover_graph_views_v1\",\"fixtures\":[";
        bool comma=false;
        for (const char* family:{"line_metric","line_wide_metric","line_random","grid2d_metric","grid2d_random"}) {
            if (comma) std::cout << ',';
            comma=true;fixture(family);
        }
        std::cout << "],\"validation\":\"pass\"}\n";
    } catch (const std::exception& error) {
        std::cerr << "graph-view export: " << error.what() << '\n';return 1;
    }
}
'''


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strict_json(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key: " + key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("nonfinite JSON value: " + value)
    return json.loads(text, object_pairs_hook=unique, parse_constant=invalid)


class Ledger:
    def __init__(self, n):
        self.parent = list(range(n))

    def find(self, v):
        while self.parent[v] != v:
            self.parent[v] = self.parent[self.parent[v]]
            v = self.parent[v]
        return v

    def join(self, a, b):
        a, b = self.find(a), self.find(b)
        require(a != b, "selected IDs repeat or create a cycle")
        self.parent[max(a, b)] = min(a, b)

    def membership(self):
        return [self.find(v) for v in range(len(self.parent))]


def integers(values, length=None):
    return type(values) is list and (length is None or len(values) == length) and all(type(v) is int for v in values)


def validate(data):
    require(type(data) is dict and set(data) == {"schema", "fixtures", "validation"} and
            data["schema"] == "crossover_graph_views_v1" and data["validation"] == "pass", "invalid export schema")
    require(type(data["fixtures"]) is list and len(data["fixtures"]) == len(FAMILIES), "incomplete fixture set")
    summaries = []
    by_family = {}
    fields = {"family", "n", "m", "density", "graph_seed", "kkt_seed", "certificate", "kkt_validation",
              "original_to_label", "positions", "grid_dimensions", "scaffold_ids", "edges", "mst_ids", "kkt_ids", "rounds"}
    round_fields = {"round", "input_n", "input_m", "selected_ids", "component_of_original",
                    "residual_n", "residual_m", "residual_edges", "validation"}
    for family, fixture in zip(FAMILIES, data["fixtures"]):
        require(type(fixture) is dict and set(fixture) == fields and fixture["family"] == family, "wrong fixture schema/order")
        for field, expected in (("n", N), ("m", N*DENSITY), ("density", DENSITY),
                                ("graph_seed", GRAPH_SEED), ("kkt_seed", KKT_SEED)):
            require(type(fixture[field]) is int and fixture[field] == expected, "wrong fixture " + field)
        require(fixture["certificate"] == fixture["kkt_validation"] == "pass", "native correctness check failed")
        label = fixture["original_to_label"]
        require(integers(label, N) and sorted(label) == list(range(N)), "invalid original label permutation")
        positions = fixture["positions"]
        require(type(positions) is list and len(positions) == N and all(integers(p, 2) for p in positions),
                "missing exact integer coordinates")
        require(integers(fixture["grid_dimensions"], 2), "invalid grid dimensions")
        if family.startswith("line"):
            limit = 2**32 if family == "line_wide_metric" else 1024
            require(fixture["grid_dimensions"] == [0, 0] and positions[0] == [0, 0] and
                    all(p[1] == 0 for p in positions) and
                    all(1 <= positions[i][0]-positions[i-1][0] <= limit for i in range(1, N)),
                    "line coordinates violate their declared gap distribution support")
        else:
            require(fixture["grid_dimensions"] == [16, 8] and all(
                abs(p[0]-1024*(i % 16)) <= 200 and abs(p[1]-1024*(i // 16)) <= 200
                for i, p in enumerate(positions)), "grid coordinates violate the exact jittered lattice")
        edges = fixture["edges"]
        require(type(edges) is list and len(edges) == N*DENSITY and all(integers(e, 6) for e in edges), "invalid edge export")
        require(sorted(e[3] for e in edges) == list(range(len(edges))) and
                sorted(e[2] for e in edges) == list(range(1, len(edges)+1)), "IDs or weight ranks are not permutations")
        require(all(0 <= u < N and 0 <= v < N and u != v and 0 <= a < N and 0 <= b < N and
                    label[a] == u and label[b] == v for u, v, _, _, a, b in edges), "original/labeled endpoints disagree")
        require(len({tuple(sorted((e[0], e[1]))) for e in edges}) == len(edges), "duplicate undirected input pair")
        by_id = {e[3]: e for e in edges}
        scaffold = [i-1 for i in range(1, N)] if family.startswith("line") else list(range(2*N-16-8))
        require(fixture["scaffold_ids"] == scaffold and integers(fixture["scaffold_ids"]), "incorrect scaffold IDs")
        if family.startswith("line"):
            expected_scaffold = [(v-1, v) for v in range(1, N)]
        else:
            expected_scaffold = []
            for v in range(N):
                if v % 16 < 15: expected_scaffold.append((v, v+1))
                if v // 16 < 7: expected_scaffold.append((v, v+16))
        require(all(tuple(sorted(by_id[id_][4:6])) == pair for id_, pair in enumerate(expected_scaffold)),
                "scaffold IDs do not describe the original path/grid geometry")
        mst = fixture["mst_ids"]
        require(integers(mst, N-1) and mst == sorted(set(mst)) and set(mst) <= set(by_id) and
                fixture["kkt_ids"] == mst and integers(fixture["kkt_ids"]), "invalid certified/KKT MST IDs")
        tree = Ledger(N)
        for id_ in mst: tree.join(*by_id[id_][4:6])
        require(len(set(tree.membership())) == 1, "exported MST is disconnected")
        if family in ("line_metric", "line_wide_metric"):
            require(mst == scaffold, "metric-line MST must be exactly its consecutive path")
        if family.endswith("metric"):
            def length(e):
                a, b = positions[e[4]], positions[e[5]]
                dx, dy = a[0]-b[0], a[1]-b[1]
                return abs(dx) if family.startswith("line") else dx*dx+dy*dy
            require([e[3] for e in sorted(edges, key=lambda e: e[2])] ==
                    [e[3] for e in sorted(edges, key=lambda e: (length(e), e[3]))], "metric ranks differ from exact distances/ID ties")
        ledger, selected = Ledger(N), set()
        before_n, before_m = N, len(edges)
        require(type(fixture["rounds"]) is list and len(fixture["rounds"]) == 2, "two production rounds required")
        for index, stage in enumerate(fixture["rounds"], 1):
            require(type(stage) is dict and set(stage) == round_fields and stage["validation"] == "pass", "invalid round schema")
            for field, expected in (("round", index), ("input_n", before_n), ("input_m", before_m)):
                require(type(stage[field]) is int and stage[field] == expected, "broken round chain: " + field)
            chosen = stage["selected_ids"]
            require(integers(chosen) and len(chosen) == len(set(chosen)) and
                    set(chosen) <= set(mst) and not selected.intersection(chosen), "invalid selected edge IDs")
            for id_ in chosen: ledger.join(*by_id[id_][4:6])
            selected.update(chosen)
            membership = ledger.membership()
            require(stage["component_of_original"] == membership and integers(stage["component_of_original"], N),
                    "Python reconstruction disagrees with native original-component ledger")
            sizes = collections.Counter(membership)
            q = len(sizes)
            require(type(stage["residual_n"]) is int and stage["residual_n"] == (q if q > 1 else 0) and
                    len(chosen) == before_n-q and q <= before_n//2, "incorrect quotient/selected counts")
            # Independently deduplicate ALL original crossing edges. A retained
            # quotient edge must be the unique cheapest member of its pair.
            cheapest = {}
            for edge in edges:
                a, b = membership[edge[4]], membership[edge[5]]
                if a == b: continue
                pair = tuple(sorted((a, b)))
                if pair not in cheapest or edge[2] < cheapest[pair][2]: cheapest[pair] = edge
            residual = stage["residual_edges"]
            require(type(residual) is list and all(integers(e, 4) for e in residual) and
                    type(stage["residual_m"]) is int and stage["residual_m"] == len(residual) and
                    len(residual) == len(cheapest) and {e[3] for e in residual} == {e[3] for e in cheapest.values()},
                    "production residual IDs do not match independent cheapest-pair reduction")
            mapping = {}
            for u, v, cost, id_ in residual:
                require(0 <= u < q and 0 <= v < q and u != v and cost == by_id[id_][2], "invalid residual tuple")
                a, b = membership[by_id[id_][4]], membership[by_id[id_][5]]
                # Production may canonicalize the edge's orientation. Compare
                # unordered component incidences, not arbitrary quotient labels.
                mapping.setdefault(u, set(sizes)).intersection_update((a, b))
                mapping.setdefault(v, set(sizes)).intersection_update((a, b))
            require(not residual or set(mapping) == set(range(q)), "residual quotient omits a component")
            # For q=2 a simultaneous exchange of both labels is immaterial.
            if q > 2:
                # A quotient leaf has just one incident unordered pair. Its
                # neighbor has degree >=2 in this connected simple graph and
                # is already uniquely identified by intersecting incidences.
                resolved = {v: next(iter(options)) for v, options in mapping.items() if len(options) == 1}
                known = set(resolved.values())
                for v, options in mapping.items():
                    if v not in resolved:
                        remaining = options-known
                        require(len(remaining) == 1, "ambiguous/inconsistent residual leaf label")
                        resolved[v] = next(iter(remaining))
                require(len(set(resolved.values())) == q and all(
                        {resolved[u], resolved[v]} ==
                        {membership[by_id[id_][4]], membership[by_id[id_][5]]}
                        for u, v, _, id_ in residual),
                        "residual labels do not consistently identify reconstructed components")
            before_n, before_m = stage["residual_n"], stage["residual_m"]
        summaries.append({"family": family, "n": N, "m": len(edges), "graph_seed": GRAPH_SEED,
            "kkt_seed": KKT_SEED, "after_two_components": q,
            "after_two_effective_components": N*N/sum(value*value for value in sizes.values()),
            "after_two_largest_fraction": max(sizes.values())/N, "after_two_residual_edges": before_m,
            "validation": "pass"})
        by_family[family] = fixture
    for metric, control in (("line_metric", "line_random"), ("grid2d_metric", "grid2d_random")):
        a, b = by_family[metric], by_family[control]
        require(a["positions"] == b["positions"] and a["original_to_label"] == b["original_to_label"] and
                [[*e[:2], *e[3:]] for e in a["edges"]] == [[*e[:2], *e[3:]] for e in b["edges"]],
                "paired metric/random controls differ in topology, geometry, IDs or input order")
    a, b = by_family["line_metric"], by_family["line_wide_metric"]
    require(a["positions"] != b["positions"] and a["original_to_label"] == b["original_to_label"] and
            [[*e[:2], *e[3:]] for e in a["edges"]] == [[*e[:2], *e[3:]] for e in b["edges"]],
            "wide line must preserve topology/IDs/order while changing geometry")
    return summaries


def inventory(root):
    return {str(path.relative_to(root)): sha(path) for pattern in ("*/*.cpp", "*/*.hpp")
            for path in sorted(root.glob(pattern))}


def export(root, output, compiler):
    sources = inventory(root)
    metadata = {"source_sha256": sources, "embedded_exporter_sha256": hashlib.sha256(EXPORTER.encode()).hexdigest(),
                "validation": "exporting",
                "profile": "Educational correctness export only; C++17 O2, no work counters, no performance measurements"}
    version = subprocess.run([compiler, "--version"], text=True, capture_output=True, check=True)
    metadata["compiler_version"] = version.stdout
    with tempfile.TemporaryDirectory(prefix="kkt-graph-views-") as temporary:
        folder = Path(temporary)
        source, binary = folder/"export.cpp", folder/"export"
        source.write_text(EXPORTER)
        command = [compiler, "-std=c++17", "-O2", "-Wall", "-Wextra", "-I", str(root)]
        if sys.platform == "darwin":
            sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
            metadata["macos_sdk"] = sdk
            command += ["-isysroot", sdk, "-L" + str(Path(sdk)/"usr/lib")]
        command += [str(source), *(str(root/name) for name in SOURCES), "-o", str(binary)]
        metadata["compiler_command"] = command
        (output/"provenance.json").write_text(json.dumps(metadata, indent=2)+"\n")
        build = subprocess.run(command, text=True, capture_output=True)
        (output/"build.log").write_text(build.stdout+build.stderr)
        metadata["compiler_exit_status"] = build.returncode
        (output/"provenance.json").write_text(json.dumps(metadata, indent=2)+"\n")
        require(build.returncode == 0, "exporter compilation failed; see build.log")
        metadata["binary_sha256"] = sha(binary)
        metadata["export_command"] = [str(binary)]
        process = subprocess.run([str(binary)], text=True, capture_output=True)
        (output/"export.log").write_text(process.stderr)
        (output/"graph_data.json").write_text(process.stdout)
        metadata["export_exit_status"] = process.returncode
        (output/"provenance.json").write_text(json.dumps(metadata, indent=2)+"\n")
        require(process.returncode == 0, "native certificate/export failed; see export.log (wide fixture support is required)")
    require(inventory(root) == sources, "source inventory changed during educational export")
    return strict_json(process.stdout), metadata


def render(data, summaries, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    from matplotlib.lines import Line2D
    from matplotlib.path import Path as PlotPath
    from matplotlib.patches import PathPatch
    plt.rcParams.update({"font.size": 10, "svg.fonttype": "none"})
    fig, axes = plt.subplots(len(FAMILIES), 2, figsize=(14, 17))
    summary = {row["family"]: row for row in summaries}
    names = {"line_metric": "Line · gaps 1–1024 · distance ranks",
             "line_wide_metric": "Line · gaps 1–2³² · distance ranks",
             "line_random": "Same narrow-line geometry · random ranks",
             "grid2d_metric": "Jittered 2D grid · distance ranks",
             "grid2d_random": "Same jittered 2D grid · random ranks"}
    for row, fixture in enumerate(data["fixtures"]):
        family, positions = fixture["family"], fixture["positions"]
        is_line = family.startswith("line")
        by_id = {edge[3]: edge for edge in fixture["edges"]}
        membership = fixture["rounds"][-1]["component_of_original"]
        components = sorted(set(membership))
        colors = {component: colorsys.hsv_to_rgb((i*.61803398875) % 1, .72, .78)
                  for i, component in enumerate(components)}
        x, y = zip(*positions)
        span = max(x)-min(x)

        def draw_edges(axis, ids, color, width, alpha, zorder):
            if is_line:
                for id_ in ids:
                    edge = by_id[id_]
                    a, b = edge[4:6]
                    xa, xb = sorted((x[a], x[b]))
                    if abs(a-b) == 1:
                        axis.plot((xa, xb), (0, 0), color=color, lw=width, alpha=alpha, zorder=zorder)
                    else:
                        # Vertices retain their exact one-dimensional coordinates.
                        # Curvature is routing for visibility, not physical y.
                        path = PlotPath(((xa, 0), ((xa+xb)/2, .45*(xb-xa)), (xb, 0)),
                                        (PlotPath.MOVETO, PlotPath.CURVE3, PlotPath.CURVE3))
                        axis.add_patch(PathPatch(path, fill=False, color=color, lw=width, alpha=alpha, zorder=zorder))
            else:
                segments = [(positions[by_id[id_][4]], positions[by_id[id_][5]]) for id_ in ids]
                axis.add_collection(LineCollection(segments, colors=[color], linewidths=width, alpha=alpha, zorder=zorder))

        original, contracted = axes[row]
        mst = set(fixture["mst_ids"])
        draw_edges(original, [id_ for id_ in by_id if id_ not in mst], "#7E8B95", .45, .15 if is_line else .11, 1)
        draw_edges(original, sorted(mst), "#713FA0", 1.65, .90, 3)
        original.scatter(x, y, s=10, c="#293340", linewidths=0, zorder=4)
        original.set_title(names[family], loc="left", fontsize=11)
        original.text(.99, .98, "Certified MST: 127 edges\nInput: 128 vertices, 512 edges", transform=original.transAxes,
                      ha="right", va="top", fontsize=8, bbox={"facecolor": "white", "edgecolor": "none", "alpha": .85})
        selected = [id_ for stage in fixture["rounds"] for id_ in stage["selected_ids"]]
        for component in components:
            inside = [id_ for id_ in selected if membership[by_id[id_][4]] == component]
            draw_edges(contracted, inside, colors[component], 1.1, .35, 2)
        retained = [edge[3] for edge in fixture["rounds"][-1]["residual_edges"]]
        draw_edges(contracted, retained, "#465664", .8, .38, 1)
        contracted.scatter(x, y, s=16, c=[colors[c] for c in membership], linewidths=0, zorder=4)
        result = summary[family]
        contracted.set_title("After two production contractions · original positions", loc="left", fontsize=10)
        contracted.text(.99, .98,
            f"q = {result['after_two_components']}; q_eff = {result['after_two_effective_components']:.2f}\n"
            f"largest / n = {result['after_two_largest_fraction']:.1%}; residual m = {result['after_two_residual_edges']}",
            transform=contracted.transAxes, ha="right", va="top", fontsize=8,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": .88})
        for axis in (original, contracted):
            axis.spines[["top", "right"]].set_visible(False)
            axis.set_xlabel("Exact x coordinate (generator units)", fontsize=8)
            axis.tick_params(labelsize=8)
            if is_line:
                axis.set_xlim(min(x)-.015*span, max(x)+.015*span)
                axis.set_ylim(-.025*span, .265*span)
                axis.set_yticks([])
                axis.spines["left"].set_visible(False)
                axis.set_xlabel("Exact x coordinate (generator units)\nVertices have y=0; arcs only route edges", fontsize=8)
                axis.ticklabel_format(axis="x", style="sci", scilimits=(-3, 5), useOffset=False)
            else:
                axis.set_aspect("equal", adjustable="box")
                axis.autoscale_view()
                # Reserve clear space for the two-line summary, so it never
                # hides the upper row of the actual jittered grid vertices.
                height = max(y)-min(y)
                axis.set_ylim(min(y)-.06*height, max(y)+.28*height)
                axis.set_ylabel("Exact y coordinate", fontsize=8)
    fig.suptitle("Actual small graph fixtures and their first two contractions", fontsize=17, y=.992)
    handles = [Line2D([0], [0], color="#7E8B95", lw=1, label="Other original edges"),
               Line2D([0], [0], color="#713FA0", lw=2, label="Certified MST"),
               Line2D([0], [0], color="#465664", lw=1, label="Retained quotient edge at original endpoints"),
               Line2D([0], [0], marker="o", linestyle="none", color="#DA7831", label="Color = reconstructed component")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.5, .037), ncol=2, fontsize=9, frameon=False)
    fig.text(.02, .014,
        "Educational instances only: n=128, m=4n, graph seed3037; these are not the large timed inputs.\n"
        "Weights are distinct ranks. Narrow-line and grid controls preserve geometry/topology; the wide line changes geometry. "
        "q_eff = n² / Σ size².", fontsize=8)
    fig.tight_layout(rect=(0, .085, 1, .975), h_pad=2.6)
    files = []
    for extension in ("png", "svg"):
        path = output/("graph_views."+extension)
        fig.savefig(path, dpi=190, bbox_inches="tight", facecolor="white")
        if extension == "svg":
            path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines())+"\n")
        files.append(path.name)
    plt.close(fig)
    return files, matplotlib.__version__


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cxx", default="/usr/bin/clang++" if sys.platform == "darwin" else "c++")
    parser.add_argument("--reuse-data", type=Path, help="Previously exported graph_data.json with adjacent matching provenance.json")
    parser.add_argument("--validate-only", action="store_true", help="Export/check data without importing matplotlib")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    require(not output.exists() or not any(output.iterdir()), "use a new or empty output directory; retain previous evidence")
    output.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parent.parent
    if args.reuse_data:
        original = args.reuse_data.resolve()
        provenance = strict_json((original.parent/"provenance.json").read_text())
        require(provenance.get("validation") == "pass" and provenance.get("data_sha256") == sha(original),
                "reused export lacks matching successful provenance")
        data = strict_json(original.read_text())
        metadata = {"reused_export": str(original), "reused_provenance_sha256": sha(original.parent/"provenance.json"),
                    "native_checks": "Reused archived certified export; native producer was not rerun"}
        shutil.copyfile(original, output/"graph_data.json")
    else:
        compiler = shutil.which(args.cxx)
        require(compiler is not None, "C++ compiler not found: " + args.cxx)
        data, metadata = export(root, output, compiler)
    summaries = validate(data)
    with (output/"graph_summary.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summaries[0])); writer.writeheader(); writer.writerows(summaries)
    metadata.update(schema="crossover_graph_views_provenance_v1", validation="pass",
        script_sha256=sha(Path(__file__)), data_sha256=sha(output/"graph_data.json"),
        python=platform.python_version(), families=list(FAMILIES), n=N, density=DENSITY,
        graph_seed=GRAPH_SEED, kkt_seed=KKT_SEED,
        edge_columns=["labeled_u", "labeled_v", "weight_rank", "original_edge_id", "original_u", "original_v"],
        residual_edge_columns=["quotient_u", "quotient_v", "weight_rank", "original_edge_id"],
        validation_scope="Native independent MST certificate plus production KKT exact IDs; independent C++ and Python selected-ID ledgers, Python quotient minimum-edge and geometry/rank checks. No performance measurements.")
    if not args.validate_only:
        metadata["figures"], metadata["matplotlib_version"] = render(data, summaries, output)
        metadata["figure_sha256"] = {name: sha(output/name) for name in metadata["figures"]}
    (output/"provenance.json").write_text(json.dumps(metadata, indent=2, allow_nan=False)+"\n")
    lines = ["# Actual small graph illustrations", "",
        "These are exact n=128, m=512 fixtures with graph seed3037, not the large timed inputs. The native exporter "
        "certified the reference MST independently and checked production KKT (seed101). It then called production "
        "`boruvka_step` twice; separate original-edge ledgers reconstruct membership. Python rechecks the ledgers, "
        "the cheapest crossing edge for every quotient pair, and metric ranks against the exported exact coordinates.", "",
        "Left: all original edges, with the certified MST highlighted. Right: original vertices colored by their "
        "component after two contractions; dark edges are the retained quotient representatives drawn at their original "
        "endpoints, and faint colored edges show the selected forest. Components have not been relocated to invented centroids.", "",
        "Line vertices retain exact x positions and y=0. Arcs only route edges visibly; arc height is not a geometric "
        "coordinate. Grid edges are straight in the actual jittered coordinates. Metric weights are distance ranks, "
        "not raw metric lengths. Narrow-line/random and grid/random twins share geometry; wide-line coordinates differ.", "",
        "`q_eff=n²/Σ size²`; q counts reconstructed original components even if a terminal quotient uses zero vertices. "
        "These small examples illustrate definitions and do not explain a large-instance performance result by themselves.", "",
        "[Full original data and both rounds](graph_data.json), [component summaries](graph_summary.csv), "
        "[source/compiler/export provenance](provenance.json).", ""]
    if not args.validate_only: lines += ["![Actual fixtures and contractions](graph_views.png)", "", "[Vector SVG](graph_views.svg)"]
    (output/"README.md").write_text("\n".join(lines).rstrip()+"\n")
    print(f"Validated five exact small fixtures and ten production contraction calls; wrote {output}")


if __name__ == "__main__":
    try: main()
    except (ValueError, OSError, subprocess.SubprocessError, KeyError, TypeError) as error:
        print("crossover graph views: " + str(error), file=sys.stderr)
        sys.exit(1)
