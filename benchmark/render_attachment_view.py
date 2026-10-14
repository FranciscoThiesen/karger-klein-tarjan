#!/usr/bin/env python3
"""Validate one attachment_view_v1 export and create a standalone 3D HTML view.

Standard library only; the generated document makes no network requests.
Validation independently checks the MST cycle property, graph fingerprints and
all exported graph/core/label relationships. Layout coordinates are illustrative
and have no relationship to input weights or physical geometry.

Python schema/certificate tests pass on independent synthetic exports. Native
export compatibility and browser rendering require integration-time checks.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import re
from typing import Any


class InvalidExport(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InvalidExport(message)


def integer(value: Any, name: str, lower: int, upper: int) -> int:
    require(type(value) is int and lower <= value <= upper,
            f"{name} must be an integer in [{lower},{upper}]")
    return value


def object_keys(value: Any, keys: set[str], name: str) -> None:
    require(isinstance(value, dict) and set(value) == keys, f"unexpected {name} object fields")


def fingerprint(edges: list[dict[str, int]], n: int, include_weights: bool) -> str:
    result = 14695981039346656037
    def append(value: int) -> None:
        nonlocal result
        for shift in (0, 8, 16, 24):
            result = ((result ^ ((value >> shift) & 255)) * 1099511628211) & ((1 << 64) - 1)
    append(n)
    for edge in edges:
        append(edge["from"])
        append(edge["to"])
        if include_weights:
            append(edge["weight"])
        append(edge["id"])
    return str(result)


def certify_mst(edges: list[dict[str, int]], selected: list[int], n: int,
                expected_weight: int) -> None:
    """Separate Python tree/cycle certificate; no production solver is called."""
    by_id = {edge["id"]: edge for edge in edges}
    parent = list(range(n))
    size = [1] * n
    def find(vertex: int) -> int:
        while parent[vertex] != vertex:
            parent[vertex] = parent[parent[vertex]]
            vertex = parent[vertex]
        return vertex
    adjacency: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    total = 0
    for edge_id in selected:
        edge = by_id[edge_id]
        u, v, weight = edge["from"], edge["to"], edge["weight"]
        a, b = find(u), find(v)
        require(a != b, "certified_mst_ids contain a cycle")
        if size[a] < size[b]:
            a, b = b, a
        parent[b] = a
        size[a] += size[b]
        adjacency[u].append((v, weight))
        adjacency[v].append((u, weight))
        total += weight
    require(size[find(0)] == n, "certified_mst_ids are not connected")
    require(total == expected_weight, "MST weight does not match actual selected tuples")
    levels = n.bit_length()
    ancestor = [[0] * n for _ in range(levels)]
    maximum = [[0] * n for _ in range(levels)]
    depth = [-1] * n
    depth[0] = 0
    queue = [0]
    for u in queue:
        for v, weight in adjacency[u]:
            if depth[v] >= 0:
                continue
            depth[v] = depth[u] + 1
            ancestor[0][v] = u
            maximum[0][v] = weight
            queue.append(v)
    require(len(queue) == n, "MST traversal did not reach all vertices")
    for level in range(1, levels):
        for v in range(n):
            middle = ancestor[level - 1][v]
            ancestor[level][v] = ancestor[level - 1][middle]
            maximum[level][v] = max(maximum[level - 1][v], maximum[level - 1][middle])
    def path_maximum(a: int, b: int) -> int:
        result = 0
        if depth[a] < depth[b]:
            a, b = b, a
        difference = depth[a] - depth[b]
        bit = 0
        while difference:
            if difference & 1:
                result = max(result, maximum[bit][a])
                a = ancestor[bit][a]
            bit += 1
            difference >>= 1
        if a == b:
            return result
        for level in range(levels - 1, -1, -1):
            if ancestor[level][a] != ancestor[level][b]:
                result = max(result, maximum[level][a], maximum[level][b])
                a, b = ancestor[level][a], ancestor[level][b]
        return max(result, maximum[0][a], maximum[0][b])
    for edge in edges:
        require(path_maximum(edge["from"], edge["to"]) <= edge["weight"],
                f"edge {edge['id']} improves the claimed MST cycle")


def validate_export(data: Any) -> dict[str, int | str]:
    keys = {"schema", "case_id", "family", "n", "m", "density", "graph_seed", "kkt_seed",
            "block_size", "core_vertices", "local_star_edges", "input_fingerprint",
            "topology_fingerprint", "mst_total_weight", "validation", "layout_note",
            "core_rank_note", "original_to_label", "certified_mst_ids", "edges", "core_edges"}
    object_keys(data, keys, "export")
    require(data["schema"] == "attachment_view_v1" and data["validation"] == "pass",
            "unsupported or unsuccessful attachment export")
    require(isinstance(data["family"], str), "family must be text")
    match = re.fullmatch(r"(leaf|community)_(hierarchy|distance|shuffled|random)(4|16)", data["family"])
    require(match is not None, "unknown attachment family")
    endpoint, weight_mode, block_text = match.groups()
    b = integer(data["block_size"], "block_size", 4, 16)
    require(b == int(block_text), "family and block_size disagree")
    n = integer(data["n"], "n", 32, 4096)
    require(n & (n - 1) == 0 and n % b == 0, "n is not a supported dyadic block multiple")
    density = integer(data["density"], "density", 1, 512)
    m = integer(data["m"], "m", n - 1, 65536)
    q, local = n // b, n - n // b
    external = m - local
    require(m == n * density and q - 1 <= external <= q * (q - 1) // 2,
            "edge budget or simple-core capacity is invalid")
    require(data["case_id"] == f"{data['family']}_n{n}_d{density}_p0", "case_id differs from dimensions")
    require(integer(data["core_vertices"], "core_vertices", 2, n) == q and
            integer(data["local_star_edges"], "local_star_edges", 1, m) == local,
            "exported core dimensions disagree")
    for field in ("graph_seed", "kkt_seed"):
        integer(data[field], field, 0, (1 << 32) - 1)
    for field in ("layout_note", "core_rank_note"):
        require(isinstance(data[field], str) and len(data[field]) <= 500, f"invalid {field}")
    labels = data["original_to_label"]
    require(isinstance(labels, list) and len(labels) == n, "invalid label permutation length")
    require({integer(label, "vertex label", 0, n - 1) for label in labels} == set(range(n)),
            "original_to_label is not a permutation")
    original = [0] * n
    for vertex, label in enumerate(labels):
        original[label] = vertex
    edges = data["edges"]
    require(isinstance(edges, list) and len(edges) == m, "edge array length differs from m")
    ids: set[int] = set()
    weights: set[int] = set()
    pairs: set[tuple[int, int]] = set()
    by_id: dict[int, dict[str, int]] = {}
    for edge in edges:
        object_keys(edge, {"from", "to", "weight", "id"}, "graph edge")
        u = integer(edge["from"], "edge.from", 0, n - 1)
        v = integer(edge["to"], "edge.to", 0, n - 1)
        weight = integer(edge["weight"], "edge.weight", 1, m)
        edge_id = integer(edge["id"], "edge.id", 0, m - 1)
        pair = (min(u, v), max(u, v))
        require(u != v and pair not in pairs, "self-loop or repeated original edge pair")
        require(edge_id not in ids and weight not in weights, "duplicate original ID or weight rank")
        pairs.add(pair)
        ids.add(edge_id)
        weights.add(weight)
        by_id[edge_id] = edge
    for edge_id in range(local):
        edge = by_id[edge_id]
        center, clone = divmod(edge_id, b - 1)
        require(original[edge["from"]] == b * center and original[edge["to"]] == b * center + clone + 1,
                "local star edge/ID relationship differs")
    if weight_mode != "random":
        require({by_id[edge_id]["weight"] for edge_id in range(local)} == set(range(1, local + 1)),
                "local-star weight mode does not preserve the cheap prefix")
    core = data["core_edges"]
    require(isinstance(core, list) and len(core) == external, "core edge array length differs")
    core_ids: set[int] = set()
    core_ranks: set[int] = set()
    core_pairs: set[tuple[int, int]] = set()
    for edge in core:
        object_keys(edge, {"from", "to", "rank", "id", "original_edge_id"}, "core edge")
        u = integer(edge["from"], "core.from", 0, q - 1)
        v = integer(edge["to"], "core.to", 0, q - 1)
        rank = integer(edge["rank"], "core.rank", 1, external)
        edge_id = integer(edge["id"], "core.id", 0, external - 1)
        expanded_id = integer(edge["original_edge_id"], "core.original_edge_id", local, m - 1)
        require(u < v and (u, v) not in core_pairs, "noncanonical or duplicate core pair")
        require(edge_id not in core_ids and rank not in core_ranks and expanded_id == local + edge_id,
                "core ID/rank mapping is invalid")
        core_pairs.add((u, v)); core_ids.add(edge_id); core_ranks.add(rank)
        actual = by_id[expanded_id]
        a, c = original[actual["from"]], original[actual["to"]]
        require(a // b == u and c // b == v, "core pair differs from actual projected endpoints")
        if endpoint == "leaf":
            require(a % b == 0 and c % b == 0, "leaf-family external endpoint is not a center")
        if weight_mode != "random":
            require(actual["weight"] == local + rank, "core metadata rank differs from actual cost")
        if edge_id < q - 1:
            require((u, v) == (edge_id, edge_id + 1), "core path IDs differ from endpoints")
    for field, include_weights in (("input_fingerprint", True), ("topology_fingerprint", False)):
        require(isinstance(data[field], str) and re.fullmatch(r"[0-9]+", data[field]) is not None,
                f"{field} must be a decimal string preserving its full 64 bits")
        require(data[field] == fingerprint(edges, n, include_weights), f"{field} does not match actual tuples")
    selected = data["certified_mst_ids"]
    require(isinstance(selected, list) and len(selected) == n - 1, "MST does not contain n-1 IDs")
    require(len({integer(edge_id, "MST ID", 0, m - 1) for edge_id in selected}) == n - 1,
            "MST repeats an edge ID")
    mst_weight = integer(data["mst_total_weight"], "mst_total_weight", 1, (n - 1) * m)
    certify_mst(edges, selected, n, mst_weight)
    return {"validation": "pass", "schema": data["schema"], "n": n, "m": m,
            "mst_edges": n - 1, "core_vertices": q, "core_edges": external,
            "input_fingerprint": data["input_fingerprint"]}


HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; base-uri 'none'">
<title>__TITLE__</title>
<style>
:root{color-scheme:dark;font:15px/1.5 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#080f1b;color:#e6edf7}
*{box-sizing:border-box}body{margin:0;padding:24px;max-width:1700px;margin-inline:auto}h1{font-size:clamp(22px,3vw,34px);line-height:1.2;margin:0 0 9px;letter-spacing:-.03em}p{margin:0 0 12px}.muted{color:#9eacc2}.eyebrow{color:#66d6bb;font-size:12px;text-transform:uppercase;letter-spacing:.12em;margin-bottom:9px}.layout{display:grid;grid-template-columns:310px minmax(0,1fr);gap:18px;margin-top:20px}.panel,.viewport{border:1px solid #29374d;border-radius:14px;background:#101a2a}.panel{padding:19px}.panel h2{font-size:15px;margin:20px 0 9px}.panel h2:first-child{margin-top:0}.check{display:flex;align-items:center;gap:9px;margin:9px 0}.check input{accent-color:#6de2c3;width:17px;height:17px}.swatch{display:inline-block;width:18px;height:3px;flex:0 0 18px}.mst-local{background:#53dfb9}.mst-core{background:#ffcf70}.other{background:#879ab7}button,select{font:inherit;color:inherit;background:#1a2940;border:1px solid #41546f;border-radius:7px;padding:7px 10px}button{cursor:pointer}button:hover{background:#263c59}button:focus-visible,select:focus-visible,input:focus-visible,canvas:focus-visible{outline:2px solid #92e5d0;outline-offset:3px}.buttons{display:flex;flex-wrap:wrap;gap:7px;margin:10px 0}select{width:100%}input[type=range]{width:100%;accent-color:#71d9c3}label.range{display:block;margin:12px 0 4px}.small{font-size:12px}.stats{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin:14px 0}.stat{padding:9px;background:#18243a;border-radius:7px}.stat strong{display:block;font-size:20px;line-height:1.2}.stat span{font-size:12px;color:#a4b4cd}.viewport{position:relative;overflow:hidden;min-height:600px;height:76vh;max-height:1000px}.viewport canvas{display:block;width:100%;height:100%;touch-action:none;cursor:grab}.viewport canvas:active{cursor:grabbing}.viewport .instructions{position:absolute;bottom:12px;left:14px;right:14px;pointer-events:none;font-size:12px;color:#adc0d8;background:#09101bdc;border-radius:6px;padding:7px 10px}.inspector{white-space:pre-line;font-size:12px;min-height:95px;color:#c0cee2}.certificate{padding:11px;background:#132d2b;border:1px solid #2c5750;border-radius:8px;font-size:12px}.footnote{max-width:100ch;font-size:12px;color:#a8b6cb;margin-top:17px}code{overflow-wrap:anywhere;font-size:11px}#visible-count{font-variant-numeric:tabular-nums}#rank-value{float:right;font-variant-numeric:tabular-nums}
@media(max-width:850px){body{padding:15px}.layout{grid-template-columns:1fr}.panel{display:grid;grid-template-columns:1fr 1fr;gap:0 20px}.panel .full{grid-column:1/-1}.viewport{height:66vh;min-height:430px}.panel h2{margin-top:16px}}@media(max-width:480px){.panel{display:block}.viewport{min-height:380px}.small{font-size:11px}}
</style></head><body>
<div class="eyebrow">KKT graph anatomy · offline interactive view</div>
<h1 id="heading"></h1><p class="muted" id="subtitle"></p>
<p class="small muted">Illustrative layout, not physical geometry. Every drawn connection is an actual input edge; edge length does not encode its cost.</p>
<div class="layout">
<aside class="panel">
<div class="full"><h2>Exact exported instance</h2><div class="stats"><div class="stat"><strong id="vertex-count"></strong><span>vertices</span></div><div class="stat"><strong id="edge-count"></strong><span>input edges</span></div><div class="stat"><strong id="core-count"></strong><span>core blocks</span></div><div class="stat"><strong id="block-count"></strong><span>vertices per block</span></div></div></div>
<div><h2>Actual edges</h2><label class="check"><input id="show-mst" type="checkbox" checked><span>Certified MST</span></label><label class="check"><input id="show-other" type="checkbox"><span class="swatch other"></span><span>Other graph edges</span></label><label class="check"><input id="show-local" type="checkbox" checked><span class="swatch mst-local"></span><span>Local star edges</span></label><label class="check"><input id="show-core" type="checkbox" checked><span class="swatch mst-core"></span><span>Between blocks</span></label><label class="range" for="rank">Maximum weight rank <output id="rank-value"></output></label><input id="rank" type="range" min="1" step="1"><p class="small muted">The threshold applies to both MST and other edges. With a lower threshold, the displayed MST may be only a forest.</p><p class="small" id="visible-count" aria-live="polite"></p></div>
<div><h2>Illustrative coordinates</h2><select id="layout-mode" aria-label="Illustrative layout"><option value="dyadic">Dyadic clusters with local stars</option><option value="ring">Core ring with local stars</option></select><div class="buttons"><button id="oblique">Oblique</button><button id="front">Front</button><button id="top">Top</button></div><label class="check"><input id="auto" type="checkbox"><span>Auto rotate</span></label><div class="buttons"><button id="reset">Reset view</button><button id="download">Download PNG</button></div><p class="small muted">Coordinates use original block IDs, so paired weight/endpoint variants share their layout.</p></div>
<div class="full"><h2>Selected vertex</h2><div id="inspector" class="inspector">Click a vertex to inspect its original label, block and degree.</div><button id="clear-selection">Clear selection</button></div>
<div class="full"><h2>Correctness and provenance</h2><p class="certificate">The native export matched KKT against an independently certified MST. This HTML builder also checked the tree and every input edge's cycle condition.</p><p class="small muted" id="certificate-detail"></p><p class="small muted">Input fingerprint<br><code id="fingerprint"></code></p></div>
</aside>
<div class="viewport" id="viewport"><canvas id="graph" tabindex="0" aria-label="Interactive illustrative 3D graph. Drag or use arrow keys to rotate; scroll or use plus and minus to zoom."></canvas><div class="instructions">Drag to rotate · Scroll to zoom · Click a vertex · Arrow keys rotate; + / − zoom</div></div>
</div>
<p class="footnote">This is a small, exact exported graph for inspecting structure. Its layout and interactive rendering are not benchmark measurements. Core metadata ranks in the global-random control are generator priorities, not that graph's actual edge weights; the threshold always uses actual input weights. The file is self-contained and makes no network requests.</p>
<script type="application/json" id="graph-data">__DATA__</script>
<script>
'use strict';
const data=JSON.parse(document.getElementById('graph-data').textContent);
const $=id=>document.getElementById(id), fmt=value=>value.toLocaleString();
$('heading').textContent=data.family;
$('subtitle').textContent=`n = ${fmt(data.n)}, m = ${fmt(data.m)} · graph seed ${data.graph_seed} · KKT seed ${data.kkt_seed} · density ${data.density}`;
$('vertex-count').textContent=fmt(data.n); $('edge-count').textContent=fmt(data.m);
$('core-count').textContent=fmt(data.core_vertices); $('block-count').textContent=data.block_size;
$('certificate-detail').textContent=`${fmt(data.certified_mst_ids.length)} MST edges · total rank weight ${fmt(data.mst_total_weight)}`;
$('fingerprint').textContent=data.input_fingerprint;
const canvas=$('graph'), context=canvas.getContext('2d'), viewport=$('viewport');
const rank=$('rank'), rankValue=$('rank-value'); rank.max=data.m; rank.value=data.m;
const b=data.block_size, q=data.core_vertices, n=data.n;
const originalByLabel=new Int32Array(n), degree=new Uint32Array(n), mstDegree=new Uint32Array(n);
data.original_to_label.forEach((label,original)=>{originalByLabel[label]=original;});
const selectedIds=new Set(data.certified_mst_ids);
const edges=data.edges.map(edge=>{const item={...edge,local:Math.floor(originalByLabel[edge.from]/b)===Math.floor(originalByLabel[edge.to]/b),mst:selectedIds.has(edge.id)}; degree[edge.from]++; degree[edge.to]++; if(item.mst){mstDegree[edge.from]++;mstDegree[edge.to]++;} return item;});
const positions=new Float64Array(n*3), projected=new Float64Array(n*3);
let width=1,height=1,yaw=.65,pitch=-.38,zoom=1,chosen=-1,hover=-1,pending=false,lastTime=null,drag=null,lastCount='';
const clamp=(value,lo,hi)=>Math.max(lo,Math.min(hi,value));
function layout(){
  const levels=Math.round(Math.log2(q)), ring=$('layout-mode').value==='ring';
  const lastScale=Math.pow(.57,Math.max(0,levels-1));
  const starRadius=ring ? .31*2*Math.PI/q : .70*lastScale;
  const golden=Math.PI*(3-Math.sqrt(5)); let radius=0;
  for(let core=0;core<q;core++){
    const center=[0,0,0];
    if(ring){const angle=2*Math.PI*core/q;center[0]=Math.cos(angle);center[1]=Math.sin(angle);}
    else for(let level=0;level<levels;level++){const sign=((core>>(levels-level-1))&1)?1:-1;center[level%3]+=sign*Math.pow(.57,level);}
    for(let clone=0;clone<b;clone++){
      const point=center.slice();
      if(clone){const z=1-2*(clone-.5)/(b-1), radial=Math.sqrt(Math.max(0,1-z*z)),angle=clone*golden;point[0]+=starRadius*radial*Math.cos(angle);point[1]+=starRadius*radial*Math.sin(angle);point[2]+=starRadius*z;}
      const label=data.original_to_label[core*b+clone];
      positions.set(point,label*3);radius=Math.max(radius,Math.hypot(...point));
    }
  }
  for(let i=0;i<positions.length;i++)positions[i]/=radius;
  schedule();
}
function schedule(){if(!pending){pending=true;requestAnimationFrame(draw);}}
function resize(){const rect=viewport.getBoundingClientRect();width=rect.width;height=rect.height;const scale=Math.min(window.devicePixelRatio||1,2);canvas.width=Math.max(1,Math.round(width*scale));canvas.height=Math.max(1,Math.round(height*scale));context.setTransform(scale,0,0,scale,0,0);schedule();}
function visible(edge){return edge.weight<=Number(rank.value)&&(edge.local?$('show-local').checked:$('show-core').checked)&&(edge.mst?$('show-mst').checked:$('show-other').checked);}
function group(mst,local,color,lineWidth,alpha){
  if(!(mst?$('show-mst').checked:$('show-other').checked)||!(local?$('show-local').checked:$('show-core').checked))return 0;
  context.beginPath();let count=0;
  for(const edge of edges){if(edge.mst!==mst||edge.local!==local||edge.weight>Number(rank.value))continue;context.moveTo(projected[3*edge.from],projected[3*edge.from+1]);context.lineTo(projected[3*edge.to],projected[3*edge.to+1]);count++;}
  context.strokeStyle=color;context.globalAlpha=alpha;context.lineWidth=lineWidth;context.stroke();return count;
}
function draw(time){
  pending=false;
  if($('auto').checked){if(lastTime!==null)yaw+=Math.min(time-lastTime,50)*.00018;lastTime=time;}else lastTime=null;
  context.globalAlpha=1;context.fillStyle='#08111f';context.fillRect(0,0,width,height);
  const cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch),distance=4.5,scale=.38*Math.min(width,height)*zoom;
  for(let v=0;v<n;v++){const i=3*v,x=positions[i],y=positions[i+1],z=positions[i+2],rx=cy*x+sy*z,rz=-sy*x+cy*z,ry=cp*y-sp*rz,depth=sp*y+cp*rz,perspective=distance/(distance-depth);projected[i]=width*.5+rx*scale*perspective;projected[i+1]=height*.51-ry*scale*perspective;projected[i+2]=depth;}
  const other=group(false,false,'#879ab7',.65,.20)+group(false,true,'#879ab7',.7,.24);
  const localMst=group(true,true,'#53dfb9',1.0,.78),coreMst=group(true,false,'#ffcf70',1.15,.82),total=other+localMst+coreMst;
  const focused=chosen>=0?chosen:hover;
  if(focused>=0){context.beginPath();for(const edge of edges){if(!visible(edge)||(edge.from!==focused&&edge.to!==focused))continue;context.moveTo(projected[3*edge.from],projected[3*edge.from+1]);context.lineTo(projected[3*edge.to],projected[3*edge.to+1]);}context.strokeStyle='#d4b4ff';context.lineWidth=2.2;context.globalAlpha=.95;context.stroke();}
  const vertices=Array.from({length:n},(_,i)=>i).sort((a,c)=>projected[3*a+2]-projected[3*c+2]);
  for(const v of vertices){const x=projected[3*v],y=projected[3*v+1];if(x<-5||y<-5||x>width+5||y>height+5)continue;const center=originalByLabel[v]%b===0;context.beginPath();context.arc(x,y,(center?2.35:1.3)*clamp(.8+.2*zoom,1,2.2),0,Math.PI*2);context.fillStyle=center?'#e2edfc':'#7eabc2';context.globalAlpha=center ? .92 : .65;context.fill();}
  if(focused>=0){context.beginPath();context.arc(projected[3*focused],projected[3*focused+1],7,0,Math.PI*2);context.strokeStyle='#e7ccff';context.globalAlpha=1;context.lineWidth=1.8;context.stroke();}
  context.globalAlpha=1;context.fillStyle='#09101be8';context.fillRect(0,0,width,62);context.fillStyle='#d9e6f7';context.font='600 13px system-ui';context.fillText(data.family,16,23);context.font='11px system-ui';context.fillStyle='#a9bad2';context.fillText(`Illustrative coordinates · n=${fmt(n)}, m=${fmt(data.m)} · visible edges ${fmt(total)} · rank ≤ ${fmt(Number(rank.value))}`,16,44);
  const countText=`${fmt(total)} visible edges: ${fmt(localMst+coreMst)} MST + ${fmt(other)} other.`;if(countText!==lastCount){$('visible-count').textContent=countText;lastCount=countText;}rankValue.textContent=fmt(Number(rank.value));
  if($('auto').checked)schedule();
}
function nearest(x,y){let best=-1,distance=10*10;for(let v=0;v<n;v++){const dx=projected[3*v]-x,dy=projected[3*v+1]-y,test=dx*dx+dy*dy;if(test<distance){best=v;distance=test;}}return best;}
function inspect(){if(chosen<0){$('inspector').textContent='Click a vertex to inspect its original label, block and degree.';return;}const original=originalByLabel[chosen],clone=original%b;$('inspector').textContent=`Graph label: ${chosen}\nOriginal vertex: ${original}\nCore block: ${Math.floor(original/b)} · ${clone===0?'star center':`clone ${clone}`}\nInput degree: ${degree[chosen]} · MST degree: ${mstDegree[chosen]}\nDegrees use the complete graph, not current filters.`;}
canvas.addEventListener('pointerdown',event=>{if(event.button!==0)return;canvas.focus();canvas.setPointerCapture(event.pointerId);drag={id:event.pointerId,x:event.clientX,y:event.clientY,startX:event.clientX,startY:event.clientY,moved:false};});
canvas.addEventListener('pointermove',event=>{if(drag&&drag.id===event.pointerId){const dx=event.clientX-drag.x,dy=event.clientY-drag.y;drag.moved=drag.moved||Math.hypot(event.clientX-drag.startX,event.clientY-drag.startY)>3;drag.x=event.clientX;drag.y=event.clientY;yaw+=dx*.007;pitch=clamp(pitch+dy*.007,-1.5,1.5);schedule();}else if(!drag){const rect=canvas.getBoundingClientRect(),next=nearest(event.clientX-rect.left,event.clientY-rect.top);if(next!==hover){hover=next;schedule();}}});
canvas.addEventListener('pointerup',event=>{if(!drag||drag.id!==event.pointerId)return;if(!drag.moved){const rect=canvas.getBoundingClientRect();chosen=nearest(event.clientX-rect.left,event.clientY-rect.top);inspect();}drag=null;if(canvas.hasPointerCapture(event.pointerId))canvas.releasePointerCapture(event.pointerId);schedule();});
canvas.addEventListener('pointercancel',()=>{drag=null;});canvas.addEventListener('pointerleave',()=>{hover=-1;schedule();});
canvas.addEventListener('wheel',event=>{event.preventDefault();zoom=clamp(zoom*Math.exp(-event.deltaY*.001),.35,12);schedule();},{passive:false});
canvas.addEventListener('keydown',event=>{const keys=['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','=','-','_'];if(!keys.includes(event.key))return;event.preventDefault();if(event.key==='ArrowLeft')yaw-=.12;if(event.key==='ArrowRight')yaw+=.12;if(event.key==='ArrowUp')pitch=clamp(pitch-.12,-1.5,1.5);if(event.key==='ArrowDown')pitch=clamp(pitch+.12,-1.5,1.5);if(event.key==='+'||event.key==='=')zoom=clamp(zoom*1.15,.35,12);if(event.key==='-'||event.key==='_')zoom=clamp(zoom/1.15,.35,12);schedule();});
for(const id of ['show-mst','show-other','show-local','show-core','auto'])$(id).addEventListener('change',schedule);rank.addEventListener('input',schedule);
$('layout-mode').addEventListener('change',layout);
$('oblique').addEventListener('click',()=>{yaw=.65;pitch=-.38;schedule();});$('front').addEventListener('click',()=>{yaw=0;pitch=0;schedule();});$('top').addEventListener('click',()=>{yaw=0;pitch=-1.48;schedule();});
$('clear-selection').addEventListener('click',()=>{chosen=-1;inspect();schedule();});
$('reset').addEventListener('click',()=>{yaw=.65;pitch=-.38;zoom=1;chosen=-1;hover=-1;$('auto').checked=false;$('show-mst').checked=true;$('show-other').checked=false;$('show-local').checked=true;$('show-core').checked=true;rank.value=data.m;$('layout-mode').value='dyadic';inspect();layout();});
$('download').addEventListener('click',()=>{canvas.toBlob(blob=>{if(!blob)return;const url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=`${data.family}_n${n}_g${data.graph_seed}.png`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);},'image/png');});
new ResizeObserver(resize).observe(viewport);layout();resize();
</script></body></html>
'''


def render_html(data: dict[str, Any]) -> str:
    validate_export(data)
    # Data is inert JSON text. Escape HTML-significant characters even though
    # fixture names are whitelisted, so arbitrary note text cannot end a script.
    payload = json.dumps(data, separators=(",", ":"), ensure_ascii=True)
    payload = payload.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    title = html.escape(f"KKT graph anatomy: {data['family']}", quote=True)
    return HTML.replace("__TITLE__", title).replace("__DATA__", payload)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if not args.validate_only and args.output is None:
        parser.error("--output is required unless --validate-only is used")
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        summary = validate_export(data)
        if not args.validate_only:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(render_html(data), encoding="utf-8")
            summary["html"] = str(args.output)
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.error(str(error))
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
