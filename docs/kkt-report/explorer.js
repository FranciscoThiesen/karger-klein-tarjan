// Standalone offline 3D graph viewer. All geometry and graph data are embedded.
(() => {
'use strict';
const data = JSON.parse(document.getElementById('graph-data').textContent);
const names = {
 unbalanced_bipartite_16:'Bipartite graph: 16-vertex core', leaf_core_90:'Sparse core with 90% attached leaves',
 ring_cliques_16:'Ring of 16-vertex cliques', grid3d_distance:'3D mesh: distance-ranked weights',
 grid3d_random:'3D mesh: random weights', regular_8:'Connected degree-eight graph', small_world:'Connected small-world variant'
};
const canvas = document.getElementById('graph-canvas'), ctx = canvas.getContext('2d');
const family = document.getElementById('family'), stage = document.getElementById('stage');
const info = document.getElementById('graph-info'), detail = document.getElementById('node-detail');
const layers = [0,1,2,2,2];
let yaw=.35, pitch=-.25, zoom=1, dragging=false, previous=null, points=[];
for (const d of data) { const o=document.createElement('option');o.value=d.family;o.textContent=names[d.family];family.appendChild(o); }
const getGraph=()=>data.find(d=>d.family===family.value);
function project(p,w,h) {
 const x=p[0]*Math.cos(yaw)+p[2]*Math.sin(yaw), z=-p[0]*Math.sin(yaw)+p[2]*Math.cos(yaw);
 const y=p[1]*Math.cos(pitch)-z*Math.sin(pitch), depth=p[1]*Math.sin(pitch)+z*Math.cos(pitch);
 const perspective=3.5/(3.5+depth), scale=Math.min(w,h)*.34*zoom;
 return {x:w/2+x*scale*perspective,y:h/2-y*scale*perspective,z:depth,p:perspective};
}
function render() {
 const d=getGraph(), mode=Number(stage.value), layer=layers[mode], g=d.stages[layer];
 const ratio=window.devicePixelRatio||1, w=canvas.clientWidth,h=canvas.clientHeight;
 canvas.width=Math.round(w*ratio);canvas.height=Math.round(h*ratio);ctx.setTransform(ratio,0,0,ratio,0,0);
 ctx.clearRect(0,0,w,h);
 const pos=d.layouts[layer], selected=new Set(mode<2?d.selected_ids[mode]:[]);
 const forest=new Set(d.sample_forest_ids), heavy=new Set(d.heavy_ids), sampled=new Set(d.sampled_ids);
 points=pos.map((p,i)=>({...project(p,w,h),id:i}));
 const edgeColor=e=>mode<2&&selected.has(e[3])?'#007e88':mode===3&&forest.has(e[3])?'#007e88':mode===4&&heavy.has(e[3])?'#c64d37':mode===4&&forest.has(e[3])?'#007e88':null;
 const paintEdge=(e,highlight)=>{const a=points[e[0]],b=points[e[1]],color=edgeColor(e);if(Boolean(color)!==highlight)return;
   if(!highlight&&!document.getElementById('context-edges').checked)return;
   if(mode===3&&!sampled.has(e[3])&&!highlight)return;
   ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.strokeStyle=color||'rgba(82,102,119,0.16)';ctx.lineWidth=color?1.8:.65;ctx.stroke();};
 g.edges.forEach(e=>paintEdge(e,false));g.edges.forEach(e=>paintEdge(e,true));
 points.slice().sort((a,b)=>b.z-a.z).forEach(p=>{
   const members=d.members[layer][p.id].length, core=layer===0&&d.core_labels.includes(p.id);
   ctx.beginPath();ctx.arc(p.x,p.y,(core?5:2.1+Math.log2(members)*.55)*p.p,0,2*Math.PI);
   ctx.fillStyle=core?'#9c5d9b':'#254b64';ctx.fill();
 });
 const marked=mode<2?selected.size:mode===3?forest.size:mode===4?heavy.size:0;
 const meaning=mode<2?'safe selected edges':mode===3?'sample-forest edges':mode===4?'F-heavy edges removable': 'edges selected for emphasis';
 if(mode===3) {
   info.textContent=`${g.n.toLocaleString()} residual vertices · ${sampled.size.toLocaleString()} sampled edges of ${g.edges.length.toLocaleString()} residual edges · ${forest.size} sample-forest edges`;
 } else if(mode===4) {
   info.textContent=`${g.n.toLocaleString()} residual vertices · ${g.edges.length.toLocaleString()} residual edges · ${heavy.size} F-heavy edges removable · ${g.edges.length-heavy.size} retained edges`;
 } else {
   info.textContent=`${g.n.toLocaleString()} vertices · ${g.edges.length.toLocaleString()} edges${mode===2?'':` · ${marked} ${meaning}`}`;
 }
 document.getElementById('stage-explanation').textContent=[
   'Each vertex chooses its lightest incident edge. Teal edges are safe MST edges; purple nodes identify the designated small core where applicable.',
   'Connected components of the first selection have become supervertices. Parallel edges keep only their minimum. Teal shows the second selection.',
   'This is the graph left after two production contractions. Coordinates are centroids of original member vertices, with a common scale across all stages.',
   'Each residual edge is sampled with probability 1/2, seed 0. All residual vertices remain visible, including sample isolates. Teal is the sample forest; gray edges belong to the sample but not the forest.',
   'This shows the full residual with removable edges marked red, before deletion. Red edges exceed the maximum on their forest path. Teal is the sample forest; gray light edges include connections between forest components.'
 ][mode];
 canvas.setAttribute('aria-label',names[d.family]+'. '+info.textContent+'. Drag to rotate; arrow keys rotate; plus and minus zoom.');
}
function reset(){yaw=.35;pitch=-.25;zoom=1;detail.textContent='Hover a vertex to see its original member count.';render();}
family.addEventListener('change',reset);stage.addEventListener('change',()=>{detail.textContent='Hover a vertex to see its original member count.';render();});
document.getElementById('context-edges').addEventListener('change',render);
document.getElementById('reset-camera').addEventListener('click',reset);
canvas.addEventListener('pointerdown',e=>{dragging=true;previous=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId);});
canvas.addEventListener('pointerup',()=>{dragging=false;});canvas.addEventListener('pointercancel',()=>{dragging=false;});
canvas.addEventListener('pointermove',e=>{
 if(dragging){yaw+=(e.clientX-previous[0])*.008;pitch+=(e.clientY-previous[1])*.008;previous=[e.clientX,e.clientY];render();return;}
 const box=canvas.getBoundingClientRect(), x=e.clientX-box.left,y=e.clientY-box.top;
 let best=null,dist=100;for(const p of points){const r=(p.x-x)**2+(p.y-y)**2;if(r<dist){dist=r;best=p;}}
 const d=getGraph(),layer=layers[Number(stage.value)];
 const degreeLabel=Number(stage.value)>=3?'residual degree':'degree';
 detail.textContent=best?`Vertex ${best.id}: ${d.members[layer][best.id].length} original vertices; ${degreeLabel} ${d.degrees[layer][best.id]}.`:'Hover a vertex to see its original member count.';
});
canvas.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(.4,Math.min(3,zoom*Math.exp(-e.deltaY*.001)));render();},{passive:false});
canvas.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','-','=','r'].includes(e.key)){e.preventDefault();
 if(e.key==='ArrowLeft')yaw-=.1;if(e.key==='ArrowRight')yaw+=.1;if(e.key==='ArrowUp')pitch-=.1;if(e.key==='ArrowDown')pitch+=.1;
 if(e.key==='+'||e.key==='=')zoom=Math.min(3,zoom*1.1);if(e.key==='-')zoom=Math.max(.4,zoom/1.1);if(e.key==='r')reset();render();}});
new ResizeObserver(render).observe(canvas);render();
window.kktExplorer={render,graphCount:data.length,getState:()=>({family:family.value,stage:Number(stage.value),vertices:getGraph().stages[layers[Number(stage.value)]].n})};
})();
