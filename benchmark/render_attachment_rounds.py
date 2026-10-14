#!/usr/bin/env python3
"""Add actual compacting Boruvka rounds to a certified small-instance viewer.

No KKT sampling, filtering or recursive subproblems are represented. Contractions
are computed from actual exported endpoints and costs, including random controls.
The base viewer is reused without changing its behavior.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import render_attachment_view as base


def contraction_rounds(data: dict[str, Any]) -> dict[str, Any]:
    """Independently select sorted incidence minima, union, and compact pairs."""
    base.validate_export(data)
    certified = set(data["certified_mst_ids"])
    selected_so_far: set[int] = set()
    vertices = [[v] for v in range(data["n"])]
    edges = [dict(edge) for edge in data["edges"]]
    states: list[dict[str, Any]] = []
    while True:
        count = len(vertices)
        state = {"round": len(states), "component_count": count,
                 # A finished MST has one logical component, but production
                 # removes its isolated quotient vertex: zero active vertices.
                 "active_vertices": count if edges else 0,
                 "vertices": vertices, "edges": edges, "selected_for_next": [],
                 "mst_edges_selected_so_far": len(selected_so_far)}
        states.append(state)
        if count == 1:
            base.require(not edges, "terminal quotient retains edges")
            base.require(vertices[0] == list(range(data["n"])), "terminal component misses vertices")
            base.require(selected_so_far == certified, "round selections differ from the certified MST")
            break
        base.require(bool(edges), "nonterminal quotient has no edges")
        # This explicit sorted-incidence oracle does not invoke the native
        # compactor, use expected star partitions, or inspect generator ranks.
        incidence = sorted((vertex, edge["weight"], edge["id"])
                           for edge in edges for vertex in (edge["from"], edge["to"]))
        minimum: dict[int, int] = {}
        for vertex, _weight, edge_id in incidence:
            if vertex not in minimum:
                minimum[vertex] = edge_id
        base.require(set(minimum) == set(range(count)), "isolated nonterminal quotient component")
        chosen = sorted(set(minimum.values()))
        base.require(set(chosen) <= certified, "a minimum outgoing edge is outside the certified MST")
        base.require(not (set(chosen) & selected_so_far), "an original edge was selected twice")
        state["selected_for_next"] = chosen
        parent = list(range(count))
        def root(v: int) -> int:
            while parent[v] != v:
                v = parent[v]
            return v
        by_id = {edge["id"]: edge for edge in edges}
        for edge_id in chosen:
            edge = by_id[edge_id]
            a, b = root(edge["from"]), root(edge["to"])
            base.require(a != b, "minimum-edge selections contain a cycle")
            parent[max(a, b)] = min(a, b)
        buckets: dict[int, list[int]] = {}
        for vertex in range(count):
            buckets.setdefault(root(vertex), []).append(vertex)
        groups = sorted(buckets.values(), key=lambda group: min(vertices[v][0] for v in group))
        base.require(len(groups) <= count // 2, "minimum-edge contraction failed to halve components")
        component = [0] * count
        next_vertices: list[list[int]] = []
        for index, group in enumerate(groups):
            next_vertices.append(sorted(original for v in group for original in vertices[v]))
            for v in group:
                component[v] = index
        representative: dict[tuple[int, int], dict[str, int]] = {}
        for edge in edges:
            a, b = component[edge["from"]], component[edge["to"]]
            if a == b:
                continue
            pair = (min(a, b), max(a, b))
            previous = representative.get(pair)
            if previous is None or (edge["weight"], edge["id"]) < (previous["weight"], previous["id"]):
                representative[pair] = {"from": pair[0], "to": pair[1],
                                        "weight": edge["weight"], "id": edge["id"]}
        selected_so_far.update(chosen)
        vertices = next_vertices
        edges = sorted(representative.values(), key=lambda edge: edge["id"])
    return {"schema": "attachment_rounds_v1", "validation": "pass",
            "algorithm": "compacting Boruvka using actual minimum outgoing edges",
            "shows_kkt_sampling_or_filtering": False, "rounds": states}


CONTROLS = r'''<div class="full"><h2>Compacting Borůvka rounds</h2>
<p class="small muted">First two shared with KKT. This slider shows the full compacting Borůvka continuation; KKT sampling, filtering and recursion are not shown.</p>
<label class="range" for="round">Contractions completed <output id="round-value" style="float:right"></output></label>
<input id="round" type="range" min="0" step="1" value="0">
<div class="buttons"><button id="round-back">Previous</button><button id="round-forward">Next</button></div>
<p class="small" id="round-counts"></p><p class="small muted" id="round-stage"></p>
<label class="check"><input id="show-next" type="checkbox" checked><span class="swatch" style="background:#c3a4ff"></span><span>Chosen for next contraction</span></label>
<p class="small muted">Chosen edges are highlighted only when their edge and rank filters are enabled. Each chosen original ID belongs to the independently certified MST.</p></div>'''


EXTENSION = r'''
<script type="application/json" id="contraction-data">__ROUNDS__</script>
<script>
'use strict';
const roundData=JSON.parse(document.getElementById('contraction-data').textContent);
const roundSlider=$('round'), roundStates=roundData.rounds;
roundSlider.max=roundStates.length-1;
let state, currentEdges=[], currentPositions, currentProjected, currentDegree, currentMstDegree, nextIds;
const originalEdges=new Map(edges.map(edge=>[edge.id,edge]));
function setRound(){
  state=roundStates[Number(roundSlider.value)];
  chosen=-1;hover=-1;
  currentEdges=state.edges.map(edge=>({...edge,local:originalEdges.get(edge.id).local,mst:selectedIds.has(edge.id)}));
  currentDegree=new Uint32Array(state.component_count);currentMstDegree=new Uint32Array(state.component_count);
  for(const edge of currentEdges){currentDegree[edge.from]++;currentDegree[edge.to]++;if(edge.mst){currentMstDegree[edge.from]++;currentMstDegree[edge.to]++;}}
  nextIds=new Set(state.selected_for_next);
  currentPositions=new Float64Array(3*state.component_count);currentProjected=new Float64Array(3*state.component_count);
  state.vertices.forEach((members,index)=>{for(const label of members)for(let axis=0;axis<3;axis++)currentPositions[3*index+axis]+=positions[3*label+axis]/members.length;});
  $('round-value').textContent=state.round;
  $('round-counts').textContent=`${fmt(state.active_vertices)} active vertices · ${fmt(currentEdges.length)} quotient edges · ${fmt(state.component_count)} logical component${state.component_count===1?'':'s'}`;
  $('round-stage').textContent=state.component_count===1
    ? `Finished tree: all ${fmt(data.n-1)} selected original IDs equal the certified MST. The isolated final quotient vertex is removed by the native compactor; its centroid is shown here.`
    : `${fmt(state.mst_edges_selected_so_far)} MST edges selected so far; ${fmt(nextIds.size)} chosen next. ${state.round<2?'The next contraction is one of the first two rounds shared with KKT.':'Further rounds here belong to the full compacting Borůvka run.'}`;
  $('round-back').disabled=state.round===0;$('round-forward').disabled=state.round===roundStates.length-1;
  inspect();schedule();
}
const baseLayout=layout;
layout=function(){baseLayout();if(state)setRound();};
group=function(mst,local,color,lineWidth,alpha){
  if(!(mst?$('show-mst').checked:$('show-other').checked)||!(local?$('show-local').checked:$('show-core').checked))return 0;
  context.beginPath();let count=0;
  for(const edge of currentEdges){if(edge.mst!==mst||edge.local!==local||edge.weight>Number(rank.value))continue;context.moveTo(currentProjected[3*edge.from],currentProjected[3*edge.from+1]);context.lineTo(currentProjected[3*edge.to],currentProjected[3*edge.to+1]);count++;}
  context.strokeStyle=color;context.globalAlpha=alpha;context.lineWidth=lineWidth;context.stroke();return count;
};
draw=function(time){
  pending=false;
  if($('auto').checked){if(lastTime!==null)yaw+=Math.min(time-lastTime,50)*.00018;lastTime=time;}else lastTime=null;
  context.globalAlpha=1;context.fillStyle='#08111f';context.fillRect(0,0,width,height);
  const cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch),distance=4.5,scale=.38*Math.min(width,height)*zoom;
  for(let v=0;v<state.component_count;v++){const i=3*v,x=currentPositions[i],y=currentPositions[i+1],z=currentPositions[i+2],rx=cy*x+sy*z,rz=-sy*x+cy*z,ry=cp*y-sp*rz,depth=sp*y+cp*rz,perspective=distance/(distance-depth);currentProjected[i]=width*.5+rx*scale*perspective;currentProjected[i+1]=height*.51-ry*scale*perspective;currentProjected[i+2]=depth;}
  const other=group(false,false,'#879ab7',.65,.20)+group(false,true,'#879ab7',.7,.24);
  const localMst=group(true,true,'#53dfb9',1.0,.78),coreMst=group(true,false,'#ffcf70',1.15,.82),total=other+localMst+coreMst;
  const focused=chosen>=0?chosen:hover;
  function emphasize(predicate,color,lineWidth){context.beginPath();for(const edge of currentEdges){if(!visible(edge)||!predicate(edge))continue;context.moveTo(currentProjected[3*edge.from],currentProjected[3*edge.from+1]);context.lineTo(currentProjected[3*edge.to],currentProjected[3*edge.to+1]);}context.strokeStyle=color;context.lineWidth=lineWidth;context.globalAlpha=.95;context.stroke();}
  if($('show-next').checked)emphasize(edge=>nextIds.has(edge.id),'#c3a4ff',1.8);
  if(focused>=0)emphasize(edge=>edge.from===focused||edge.to===focused,'#e9d9ff',2.4);
  const vertices=Array.from({length:state.component_count},(_,i)=>i).sort((a,c)=>currentProjected[3*a+2]-currentProjected[3*c+2]);
  for(const v of vertices){const x=currentProjected[3*v],y=currentProjected[3*v+1];if(x<-8||y<-8||x>width+8||y>height+8)continue;const members=state.vertices[v],singleton=members.length===1,center=singleton&&originalByLabel[members[0]]%b===0,radius=singleton?(center?2.35:1.3):Math.min(6,2.7+.35*Math.log2(members.length));context.beginPath();context.arc(x,y,radius*clamp(.8+.2*zoom,1,2.2),0,Math.PI*2);context.fillStyle=singleton?(center?'#e2edfc':'#7eabc2'):'#d5e9fc';context.globalAlpha=singleton ? .78 : .95;context.fill();}
  if(focused>=0){context.beginPath();context.arc(currentProjected[3*focused],currentProjected[3*focused+1],9,0,Math.PI*2);context.strokeStyle='#e7ccff';context.globalAlpha=1;context.lineWidth=1.8;context.stroke();}
  context.globalAlpha=1;context.fillStyle='#09101be8';context.fillRect(0,0,width,78);context.fillStyle='#d9e6f7';context.font='600 13px system-ui';context.fillText(`${data.family} · ${state.round} contractions completed`,16,23);context.font='11px system-ui';context.fillStyle='#a9bad2';context.fillText(`Compacting Borůvka rounds; first two shared with KKT · no sampling/filtering shown`,16,44);context.fillText(`Illustrative centroids · active V=${fmt(state.active_vertices)}, E=${fmt(currentEdges.length)} · visible ${fmt(total)} · rank ≤ ${fmt(Number(rank.value))}`,16,63);
  const countText=`${fmt(total)} visible quotient edges: ${fmt(localMst+coreMst)} certified-MST + ${fmt(other)} other.`;if(countText!==lastCount){$('visible-count').textContent=countText;lastCount=countText;}rankValue.textContent=fmt(Number(rank.value));
  if($('auto').checked)schedule();
};
nearest=function(x,y){let best=-1,distance=10*10;for(let v=0;v<state.component_count;v++){const dx=currentProjected[3*v]-x,dy=currentProjected[3*v+1]-y,test=dx*dx+dy*dy;if(test<distance){best=v;distance=test;}}return best;};
inspect=function(){
  if(chosen<0){$('inspector').textContent='Click a current component to inspect its original members and retained degrees.';return;}
  const members=state.vertices[chosen],blocks=new Set(members.map(label=>Math.floor(originalByLabel[label]/b))),preview=members.slice(0,6).join(', ')+(members.length>6?', …':'');
  $('inspector').textContent=`Current component: ${chosen}\nOriginal vertices: ${fmt(members.length)} · original star blocks touched: ${fmt(blocks.size)}\nGraph labels: ${preview}\nRetained degree: ${currentDegree[chosen]} · retained MST degree: ${currentMstDegree[chosen]}\nCoordinates are the mean of original illustrative positions. Degrees ignore display filters.`;
};
roundSlider.addEventListener('input',setRound);
$('round-back').addEventListener('click',()=>{roundSlider.value=Math.max(0,Number(roundSlider.value)-1);setRound();});
$('round-forward').addEventListener('click',()=>{roundSlider.value=Math.min(roundStates.length-1,Number(roundSlider.value)+1);setRound();});
$('show-next').addEventListener('change',schedule);
// The base registered its original layout function before this extension.
// Its listener runs first; then rebuild centroids from the new coordinates.
$('layout-mode').addEventListener('change',setRound);
$('reset').addEventListener('click',()=>{roundSlider.value=0;$('show-next').checked=true;setRound();});
setRound();
// Replace any initial base-view paint already queued before the overrides.
requestAnimationFrame(draw);
</script>
'''


def render_rounds_html(data: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    rounds = contraction_rounds(data)
    document = base.render_html(data)
    anchor = '<div class="full"><h2>Exact exported instance</h2>'
    base.require(document.count(anchor) == 1 and document.count("</body></html>") == 1,
                 "base viewer structure changed; update the optional extension")
    document = document.replace(anchor, CONTROLS + anchor)
    payload = json.dumps(rounds, separators=(",", ":"), ensure_ascii=True)
    payload = payload.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    document = document.replace("</body></html>", EXTENSION.replace("__ROUNDS__", payload) + "</body></html>")
    return document, {"schema": rounds["schema"], "validation": "pass", "n": data["n"],
                      "m": data["m"], "contractions": len(rounds["rounds"]) - 1,
                      "terminal_selected_edges": rounds["rounds"][-1]["mst_edges_selected_so_far"],
                      "native_trace_identity": "not asserted; abstract minimum-edge quotients",
                      "shows_kkt_sampling_or_filtering": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        document, summary = render_rounds_html(data)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(document, encoding="utf-8")
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.error(str(error))
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
