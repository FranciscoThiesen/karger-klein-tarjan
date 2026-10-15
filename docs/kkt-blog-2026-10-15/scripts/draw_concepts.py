#!/usr/bin/env python3
"""Draw checked explanatory toys for the KKT article; never run native solvers.

The two graph examples are deliberately constructed, not timing inputs, sampled
benchmark runs, or estimates of typical behavior. All edges are drawn. Kruskal,
independent cut-based Boruvka, and explicit forest paths check the claims before
any image is saved. Historical bookkeeping is a schematic, not a byte/time plot.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrowPatch

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "assets"
ROOT = HERE.parents[2]
PAPER = "#fbfaf7"
INK = "#172c38"
TEAL = "#007f82"
ORANGE = "#bd571e"
MUTED = "#65767c"
LINE = "#d7ddda"
PALE_TEAL = "#e4f0ed"
PALE_ORANGE = "#f6e9df"
WHITE = "#ffffff"

# Records are (u, v, weight, ID); IDs preserve pair enumeration order.
def toy_core():
    path_weights = [1, 5, 2, 7, 3, 6, 4]
    chosen = {(0, 2): 8, (2, 4): 9, (4, 6): 10}
    next_weight = 11
    result = []
    for ident, (u, v) in enumerate(itertools.combinations(range(8), 2)):
        if v == u + 1:
            weight = path_weights[u]
        elif (u, v) in chosen:
            weight = chosen[u, v]
        else:
            weight = next_weight
            next_weight += 1
        result.append((u, v, weight, ident))
    assert sorted(e[2] for e in result) == list(range(1, 29))
    return result


class DSU:
    def __init__(self, n):
        self.parent = list(range(n))

    def find(self, v):
        while self.parent[v] != v:
            v = self.parent[v]
        return v

    def join(self, u, v):
        u, v = self.find(u), self.find(v)
        if u == v:
            return False
        self.parent[v] = u
        return True

    def groups(self):
        groups = {}
        for v in range(len(self.parent)):
            groups.setdefault(self.find(v), []).append(v)
        return sorted(groups.values())


def kruskal(n, edges):
    dsu = DSU(n)
    return [e for e in sorted(edges, key=lambda e: e[2]) if dsu.join(e[0], e[1])]


def path_edges(n, forest, source, target):
    adj = [[] for _ in range(n)]
    for edge in forest:
        u, v, _, _ = edge
        adj[u].append((v, edge))
        adj[v].append((u, edge))
    todo = [(source, [])]
    seen = {source}
    for vertex, path in todo:
        if vertex == target:
            return path
        for neighbor, edge in adj[vertex]:
            if neighbor not in seen:
                seen.add(neighbor)
                todo.append((neighbor, path + [edge]))
    return None


def check_mst(n, graph, tree):
    """Cycle-property certificate, separate from sorted-edge construction."""
    assert len(tree) == n - 1
    ids = {e[3] for e in tree}
    assert len(ids) == n - 1 and ids <= {e[3] for e in graph}
    tree_by_id = {e[3]: e for e in tree}
    assert all(tree_by_id[e[3]] == e for e in graph if e[3] in ids)
    for u, v, weight, ident in graph:
        path = path_edges(n, tree, u, v)
        assert path is not None
        if ident not in ids:
            assert max(e[2] for e in path) < weight


def boruvka(n, graph):
    """Compute every component's cut minimum before simultaneous union."""
    dsu = DSU(n)
    partitions = [dsu.groups()]
    crossing = [len(graph)]
    chosen = set()
    while len(partitions[-1]) > 1:
        selected = {}
        for group in partitions[-1]:
            vertices = set(group)
            cut = [e for e in graph if (e[0] in vertices) != (e[1] in vertices)]
            assert cut, "these toys must stay connected"
            edge = min(cut, key=lambda e: e[2])
            selected[edge[3]] = edge
        for edge in selected.values():
            chosen.add(edge[3])
            dsu.join(edge[0], edge[1])
        partitions.append(dsu.groups())
        crossing.append(sum(dsu.find(e[0]) != dsu.find(e[1]) for e in graph))
        assert len(partitions[-1]) < len(partitions[-2])
    tree = [e for e in graph if e[3] in chosen]
    check_mst(n, graph, tree)
    assert chosen == {e[3] for e in kruskal(n, graph)}
    return {"partitions": partitions, "component_counts": list(map(len, partitions)),
            "crossing_edges": crossing, "selected_ids": sorted(chosen)}


def graph_checks():
    graph = toy_core()
    tree = kruskal(8, graph)
    check_mst(8, graph, tree)
    sample = [e for e in graph if e[2] in (1, 2, 3, 4, 8, 9, 10)]
    forest = kruskal(8, sample)
    assert len(forest) == len(sample) == 7
    check_mst(8, sample, forest)
    heavy = []
    for edge in graph:
        path = path_edges(8, forest, edge[0], edge[1])
        if path is not None and edge[2] > max(e[2] for e in path):
            heavy.append(edge)
    heavy_ids = {e[3] for e in heavy}
    light = [e for e in graph if e[3] not in heavy_ids]
    assert len(light) == 10 and len(heavy) == 18
    assert {e[3] for e in tree} <= {e[3] for e in light}
    assert kruskal(8, light) == tree
    assert len({e[3] for e in forest} - {e[3] for e in tree}) == 3
    example = next(e for e in graph if e[2] == 11)
    example_path = path_edges(8, forest, example[0], example[1])
    assert [example[0], example[1]] == [0, 3]
    assert max(e[2] for e in example_path) == 8

    # A deliberate weight permutation, not a PRNG draw: cheapest core ranks
    # form a star. Topology, edge order, IDs and complete weight multiset match.
    order = [e[3] for e in graph if e[0] == 0]
    order += [e[3] for e in graph if e[0] != 0]
    ranks = {ident: rank + 1 for rank, ident in enumerate(order)}
    permuted = [(u, v, ranks[ident], ident) for u, v, _, ident in graph]
    assert [(u, v, i) for u, v, _, i in graph] == [(u, v, i) for u, v, _, i in permuted]
    assert sorted(e[2] for e in graph) == sorted(e[2] for e in permuted)

    def attach(core):
        leaves = [(4*u, 4*u+j, 3*u+j, 3*u+j-1) for u in range(8) for j in range(1, 4)]
        return leaves + [(4*u, 4*v, weight+24, ident+24) for u, v, weight, ident in core]

    attached, twin = attach(graph), attach(permuted)
    a, b = boruvka(32, attached), boruvka(32, twin)
    assert a["component_counts"] == [32, 8, 4, 2, 1]
    assert b["component_counts"] == [32, 8, 1]
    assert a["crossing_edges"] == [52, 28, 24, 16, 0]
    assert b["crossing_edges"] == [52, 28, 0]
    for item in (a, b):
        assert item["partitions"][1] == [list(range(4*u, 4*u+4)) for u in range(8)]
    return dict(graph=graph, mst=tree, sample=sample, light=light, heavy=heavy,
                heavy_example=example, heavy_example_path=example_path,
                permuted_core=permuted, attached_ordered=attached, attached_permuted=twin,
                ordered_rounds=a, permuted_rounds=b,
                sample_rounds=boruvka(8, sample), full_core_rounds=boruvka(8, graph))


plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "path",
                     "svg.hashsalt": "kkt-blog-concepts-v1",
                     "font.size": 12, "savefig.facecolor": PAPER})


def canvas(width, height):
    fig = plt.figure(figsize=(width / 100, height / 100), dpi=100, facecolor=PAPER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, width); ax.set_ylim(height, 0); ax.axis("off")
    return fig, ax


def text(ax, x, y, value, size=12, color=INK, weight="normal", ha="left", va="top", **kw):
    return ax.text(x, y, value, fontsize=size, color=color, fontweight=weight,
                   ha=ha, va=va, linespacing=1.45, **kw)


def card(ax, x, y, w, h, color=WHITE, border=LINE, radius=14):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radius}",
                              facecolor=color, edgecolor=border, linewidth=.8))


def arrow(ax, x1, y1, x2, y2, color=MUTED):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                mutation_scale=13, color=color, linewidth=1.3))


def save(fig, name, results):
    # Rendering gate: every label must remain inside the logical canvas.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    width, height = fig.canvas.get_width_height()
    for axis in fig.axes:
        for label in axis.texts:
            box = label.get_window_extent(renderer)
            assert box.x0 >= 0 and box.x1 <= width and box.y0 >= 0 and box.y1 <= height, (
                name, label.get_text(), tuple(box.bounds), width, height)
    for suffix in ("svg", "png"):
        output = OUT / f"{name}.{suffix}"
        fig.savefig(output, dpi=200 if suffix == "png" else 100,
                    metadata={"Date": None} if suffix == "svg" else None)
        results[output.name] = dict(sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                                   width_inches=fig.get_figwidth(), height_inches=fig.get_figheight())
    plt.close(fig)


def id_budget(mobile, results):
    w, h = (360, 900) if mobile else (720, 590)
    fig, ax = canvas(w, h)
    text(ax, 24, 26, "Smaller graph.\nSmaller bookkeeping." if mobile else
         "Smaller graph. Smaller bookkeeping.", size=16 if mobile else 19, weight="bold")
    text(ax, 24, 94 if mobile else 73, "Edge IDs label the data.\nThey need not size recursive arrays." if mobile else
         "Original IDs identify edges. They need not size a recursive array.", size=11.5, color=MUTED)
    top = 160 if mobile else 120
    cw = 312 if mobile else 324
    starts = [(24, top), (24, top+325)] if mobile else [(24, top), (372, top)]
    for repaired, (x, y) in enumerate(starts):
        color = TEAL if repaired else ORANGE
        card(ax, x, y, cw, 300, PALE_TEAL if repaired else PALE_ORANGE, border="none")
        text(ax, x+18, y+18, "LOCAL POSITIONS" if repaired else "ORIGINAL ID RANGE", size=11, color=color, weight="bold")
        text(ax, x+18, y+49, "Work follows the child" if repaired else "Work follows the root", size=14, weight="bold")
        for idx, (label, short) in enumerate((("1,000,000 edge records", 1), ("10,000 edge records", .63), ("12 edge records", .20))):
            yy = y+97+idx*58
            text(ax, x+18, yy-4, label, size=11)
            length = (cw-36)*(short if repaired else 1)
            for cell in range(18):
                if repaired and cell >= round(18*short): break
                dx = (cw-36)/18
                ax.add_patch(FancyBboxPatch((x+18+cell*dx, yy+22), dx-2, 11,
                    boxstyle="round,pad=0,rounding_size=2", facecolor=color, edgecolor="none", alpha=.75))
        text(ax, x+18, y+273, "Current records + selected IDs" if repaired else "Same R-sized clear / merge scan", size=10.7, color=color)
    end = 810 if mobile else 450
    text(ax, 24, end, "R = 1 + largest original ID", size=12, weight="bold")
    text(ax, 24, end+33, "Schematic array extents; not to scale.\nCounts illustrate the bug, not a timing run." if mobile else
         "Schematic array extents; not to scale. Counts illustrate the bug, not a timing run.", size=10.3, color=MUTED)
    if not mobile:
        text(ax, 24, 538, "The repair: carry original IDs as data; bound local work by local input.", size=11.4, color=TEAL)
    save(fig, "concept-id-budget" + ("-mobile" if mobile else ""), results)


def ring_positions(cx, cy, radius):
    return {u: (cx+radius*math.cos(-math.pi/2 + u*2*math.pi/8),
                cy+radius*math.sin(-math.pi/2 + u*2*math.pi/8)) for u in range(8)}


def draw_graph(ax, edges, pos, colors, node_labels=True, labels=None, leaves=False):
    if leaves:
        cx = sum(p[0] for p in pos.values())/8
        cy = sum(p[1] for p in pos.values())/8
        for u, (x, y) in pos.items():
            angle = math.atan2(y-cy, x-cx)
            for delta in (-.48, 0, .48):
                nx, ny = x+25*math.cos(angle+delta), y+25*math.sin(angle+delta)
                ax.plot([x,nx], [y,ny], color=TEAL, lw=1.4, alpha=.60, zorder=1)
                ax.add_patch(Circle((nx,ny), 3.6, facecolor=PALE_TEAL, edgecolor=TEAL, lw=.6,zorder=2))
    ordered = sorted(edges, key=lambda e: colors(e)[2])
    for edge in ordered:
        u, v, _, _ = edge
        color, lw, priority = colors(edge)
        a, b = pos[u], pos[v]
        ax.plot([a[0],b[0]], [a[1],b[1]], color=color, lw=lw,
                zorder=2+priority, alpha=.48 if priority==0 else 1, solid_capstyle="round")
        if labels and edge[3] in labels:
            mx,my=(a[0]+b[0])/2,(a[1]+b[1])/2
            text(ax,mx,my,str(edge[2]),size=10.5,ha="center",va="center",color=color,
                 bbox=dict(facecolor=PAPER,edgecolor="none",pad=1.5),zorder=8)
    for vertex,(x,y) in pos.items():
        ax.add_patch(Circle((x,y),10 if node_labels else 7,facecolor=PAPER,edgecolor=INK,lw=1.1,zorder=9))
        if node_labels:text(ax,x,y,str(vertex),size=10.2,ha="center",va="center",zorder=10)


def sample_filter(data, mobile, results):
    w,h=(360,1230) if mobile else (720,930)
    fig,ax=canvas(w,h)
    text(ax,24,25,"A sample can certify\nwhat to throw away." if mobile else
         "A sample can certify what to throw away.",size=16 if mobile else 19,weight="bold")
    text(ax,24,90 if mobile else 72,"Checked 8-vertex example.\nConstructed, not a benchmark input." if mobile else
         "Checked 8-vertex example · constructed, not a benchmark input.",size=11,color=MUTED)
    mst_ids={e[3] for e in data['mst']}; sample_ids={e[3] for e in data['sample']}
    stages=[("01",data['graph'],"28", "Start with the graph", "The teal path is its\nunique minimum tree."),
            ("02",data['sample'],"7", "Solve a chosen sample", "Its forest contains three\nnon-MST edges in orange."),
            ("03",data['light'],"10", "Keep only light edges", "Discard 18 edges;\nkeep the exact original MST.")]
    for idx,(number,edges,count,title,explanation) in enumerate(stages):
        y=(152+idx*278) if mobile else (120+idx*201)
        card(ax,18,y,w-36,262 if mobile else 185,border=LINE)
        if mobile:
            text(ax,34,y+15,number,size=11,color=ORANGE,weight="bold")
            text(ax,67,y+14,title,size=12.5,weight="bold")
            pos=ring_positions(112,y+138,63)
            text(ax,224,y+65,count,size=30,weight="bold",color=TEAL)
            text(ax,224,y+111,"edges",size=11,color=MUTED)
            text(ax,34,y+212,explanation,size=11)
        else:
            pos=ring_positions(166,y+94,67)
            text(ax,40,y+16,number,size=11,color=ORANGE,weight="bold")
            text(ax,292,y+21,title,size=15,weight="bold")
            text(ax,292,y+66,count,size=32,weight="bold",color=TEAL)
            text(ax,365,y+82,"edges",size=12,color=MUTED)
            text(ax,292,y+122,explanation,size=11.5)
        def colors(e):
            if e[3] in mst_ids:return TEAL,2.4,2
            if idx>0 and e[3] in sample_ids:return ORANGE,2.2,1
            return MUTED,.7,0
        draw_graph(ax,edges,pos,colors)
    bottom=1000 if mobile else 748
    card(ax,18,bottom,w-36,208 if mobile else 160,PALE_ORANGE,border="none")
    text(ax,34,bottom+14,"The safe-discard test: 11 > 8",size=11.6,weight="bold",color=ORANGE)
    text(ax,34,bottom+47,"Heavier than every edge on that path." if mobile else
         "The forest path has weights 8 and 2.\nIts maximum is 8.\nThe edge of weight 11 is safe to discard.",size=10.4)
    px,py=(89,bottom+108) if mobile else (442,bottom+67)
    points=[(px,py),(px+80,py),(px+160,py)]
    for index,weight in enumerate((8,2)):
        a,b=points[index:index+2]
        ax.plot([a[0],b[0]],[a[1],b[1]],color=TEAL,lw=2.6)
        text(ax,(a[0]+b[0])/2,py-24,str(weight),size=12,ha="center",color=TEAL,weight="bold")
    ax.add_patch(FancyArrowPatch(points[0],points[2],connectionstyle="arc3,rad=.5",arrowstyle="-",
                               color=ORANGE,linestyle="--",linewidth=1.8))
    text(ax,px+80,py+36,"11",size=12,ha="center",color=ORANGE,weight="bold",
         bbox=dict(facecolor=PALE_ORANGE,edgecolor="none",pad=1.3))
    for vertex,(xx,yy) in zip((0,2,3),points):
        ax.add_patch(Circle((xx,yy),10,facecolor=PAPER,edgecolor=INK,lw=1,zorder=9))
        text(ax,xx,yy,str(vertex),size=10.2,ha="center",va="center",zorder=10)
    if mobile:text(ax,34,bottom+177,"Dashed edge: discarded. Path: retained.",size=10.3)
    save(fig,"concept-sample-filter"+("-mobile" if mobile else ""),results)


def components_strip(ax,x,y,width,groups):
    """Eight original core positions; colored spans show computed components."""
    unit=width/8
    palette=[TEAL,ORANGE,"#506b80","#8d7258"]
    for index,group in enumerate(groups):
        # Attached vertices map to original core IDs. Toy components are
        # contiguous for ordered case; the permuted terminal spans all eight.
        cores=sorted({v//4 for v in group})
        for core in cores:
            card(ax,x+core*unit+1,y,unit-2,19,palette[index%len(palette)],border="none",radius=3)


def weight_order(data,mobile,results):
    w,h=(360,1130) if mobile else (720,790)
    fig,ax=canvas(w,h)
    text(ax,24,26,"Same topology.\nDifferent work." if mobile else "Same topology. Different work.",
         size=17 if mobile else 21,weight="bold")
    text(ax,24,96 if mobile else 74,"Move the weights, not the edges.\nA constructed pair, not a random draw." if mobile else
         "Move the weights, not the edges. A constructed pair, not a random draw.",size=11,color=MUTED)
    for variant in range(2):
        x=18 if mobile else 18+variant*351
        y=158+variant*407 if mobile else 118
        cw=324 if mobile else 333
        card(ax,x,y,cw,389 if mobile else 405)
        text(ax,x+18,y+17,"ORDERED CORE" if not variant else "PERMUTED CORE",size=11,
             color=TEAL if not variant else ORANGE,weight="bold")
        text(ax,x+18,y+44,"Cheap path + high chords" if not variant else "Cheap edges form a star",size=12.2,weight="bold")
        core=data['graph'] if not variant else data['permuted_core']
        pos=ring_positions(x+cw/2,y+180,77)
        colors=lambda e:(TEAL if e[2]<=7 else MUTED,2.4 if e[2]<=7 else .65,2 if e[2]<=7 else 0)
        draw_graph(ax,core,pos,colors,node_labels=False,leaves=True)
        text(ax,x+18,y+300,"32 → 8 → 4 → 2 → 1" if not variant else "32 → 8 → 1",size=15.5,weight="bold")
        text(ax,x+18,y+332,"component count after each round",size=10.2,color=MUTED)
        text(ax,x+18,y+(362 if mobile else 367),"52 → 28 → 24 → 16 → 0 edges" if not variant else
             "52 → 28 → 0 crossing edges",size=10.5 if mobile else 11,color=MUTED)
    y=996 if mobile else 552
    text(ax,24,y,"Why the ordered case lingers",size=13.2,weight="bold")
    text(ax,24,y+35,"Small blocks merge, but many chords\nstill cross between them." if mobile else
         "Small blocks merge, but many chords still cross between them.",size=11.8)
    if not mobile:
        for row,groups in enumerate(data['ordered_rounds']['partitions'][1:4]):
            yy=628+row*36
            text(ax,24,yy+2,f"{len(groups)} blocks",size=11)
            components_strip(ax,140,yy,340,groups)
            text(ax,510,yy+2,f"{data['ordered_rounds']['crossing_edges'][row+1]} crossing edges",size=11,color=MUTED)
        text(ax,24,759,"Both toys: 32 vertices, 52 edges, identical IDs, edge order and weight multiset.",size=10,color=MUTED)
    else:
        text(ax,24,1085,"Both: 32 vertices · 52 edges · same weights",size=10.2,color=MUTED)
    save(fig,"concept-weight-order"+("-mobile" if mobile else ""),results)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    data=graph_checks()
    outputs={}
    for mobile in (False,True):
        id_budget(mobile,outputs)
        sample_filter(data,mobile,outputs)
        weight_order(data,mobile,outputs)
    checks={"schema":"kkt_blog_concepts_v1","validation":"pass",
            "native_solver_execution":False,"benchmark_input":False,
            "sampling_typicality_claim":False,"fixture":data,
            "source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "outputs":outputs,
            "source_references":{
              "original_id_bookkeeping":"revision 693c6a5:kkt/kkt.cpp; max_edge_id-sized used_edges/kkt_h_result and merging scans",
              "repaired_local_bookkeeping":"revision 60c65b4, documented in final report section2",
              "sample_witness":"benchmark/results/larger-hierarchy-2026-10-15/SAMPLING_MECHANISM.md",
              "attachment_construction":"benchmark/core_attachment_fixtures.hpp; note: the illustrated complete-core toy is not a timing fixture"}}
    (OUT/'concept-checks.json').write_text(json.dumps(checks,indent=2)+"\n")
    print(json.dumps({"validation":"pass","output_files":len(outputs),
                      "full_sample_light_heavy":[len(data[k]) for k in ('graph','sample','light','heavy')],
                      "ordered_components":data['ordered_rounds']['component_counts'],
                      "permuted_components":data['permuted_rounds']['component_counts']}))


if __name__=='__main__':main()
