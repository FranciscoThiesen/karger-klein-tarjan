#!/usr/bin/env python3
"""Build offline graph views from independently checked, full small-instance exports.
Run only after all timing has finished. Layout coordinates are explanatory, not
benchmark inputs except for the actual jittered geometric-mesh coordinates.
"""
from pathlib import Path
import json
import math
import networkx as nx
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
NAMES={'unbalanced_bipartite_16':'Bipartite: 16-vertex core','leaf_core_90':'90% attached leaves',
       'ring_cliques_16':'Ring of 16-vertex cliques','grid3d_distance':'3D mesh, distance weights',
       'grid3d_random':'3D mesh, random weights','regular_8':'Connected degree eight','small_world':'Small-world variant'}

def layout(d):
    n=d['stages'][0]['n'];family=d['family'];labels=d['original_to_label']
    core=[]
    if d['positions']:
        xyz=np.array(d['positions'],float)
    elif family in ('unbalanced_bipartite_16','ring_cliques_16'):
        xyz=np.zeros((n,3))
        if family=='unbalanced_bipartite_16':
            core=labels[:16]
            for i in range(n):
                angle=2*math.pi*i/(16 if i<16 else n-16)
                r=.32 if i<16 else 1
                xyz[labels[i]]=[r*math.cos(angle),r*math.sin(angle),.5 if i<16 else -.3]
        else:
            for i in range(n):
                c,v=divmod(i,16);angle=2*math.pi*c/(n/16);local=2*math.pi*v/16
                xyz[labels[i]]=[math.cos(angle)+.16*math.cos(local),math.sin(angle)+.16*math.sin(local),.12*math.sin(3*local)]
    else:
        g=nx.Graph();g.add_nodes_from(range(n));g.add_edges_from((e[0],e[1]) for e in d['stages'][0]['edges'])
        coords=nx.spring_layout(g,dim=3,seed=42,iterations=90)
        xyz=np.array([coords[i] for i in range(n)])
        if family=='leaf_core_90':core=labels[:n//10]
    xyz-=xyz.mean(axis=0);radius=np.max(np.linalg.norm(xyz,axis=1));xyz/=radius
    members=[[[i] for i in range(n)]]
    layouts=[xyz.tolist()]
    for level,map_ in enumerate(d['maps']):
        next_members=[[] for _ in range(d['stages'][level+1]['n'])]
        for v,target in enumerate(map_):
            if not next_members:continue
            next_members[target].extend(members[-1][v])
        members.append(next_members)
        layouts.append([xyz[m].mean(axis=0).tolist() for m in next_members])
    degrees=[]
    for stage in d['stages']:
        deg=[0]*stage['n']
        for u,v,*_ in stage['edges']:deg[u]+=1;deg[v]+=1
        degrees.append(deg)
    d.update(layouts=layouts,members=members,degrees=degrees,core_labels=core)


def draw(ax,d,level,kind='selection'):
    xyz=np.asarray(d['layouts'][level]);g=d['stages'][level]
    # Fixed orthographic projection so stage shrinkage is not hidden by autoscale.
    x=xyz[:,0]*.94+xyz[:,2]*.34;y=xyz[:,1]*.94-xyz[:,2]*.2
    chosen=set(d['selected_ids'][level]) if level<2 and kind=='selection' else set()
    forest=set(d['sample_forest_ids']) if kind in ('sample','heavy') else set()
    heavy=set(d['heavy_ids']) if kind=='heavy' else set()
    sample=set(d['sampled_ids'])
    for highlight in (False,True):
        for u,v,w,id_ in g['edges']:
            if kind=='sample' and id_ not in sample:continue
            color='#c64d37' if id_ in heavy else '#007e88' if id_ in chosen or id_ in forest else None
            if bool(color)!=highlight:continue
            ax.plot([x[u],x[v]],[y[u],y[v]],color=color or '#7e8e9b',alpha=.9 if color else .13,
                    lw=1.05 if color else .45,zorder=2 if color else 1)
    sizes=[7+9*math.log2(len(m)) for m in d['members'][level]]
    colors=['#9c5d9b' if level==0 and i in d['core_labels'] else '#254b64' for i in range(g['n'])]
    ax.scatter(x,y,s=sizes,c=colors,zorder=3,edgecolors='none')
    ax.set_xlim(-1.3,1.3);ax.set_ylim(-1.15,1.15);ax.set_aspect('equal');ax.axis('off')
    if kind=='sample':
        title=f'{g["n"]:,} residual vertices / {len(sample):,} sampled edges\nof {len(g["edges"]):,} residual edges'
    elif kind=='heavy':
        title=f'{g["n"]:,} vertices / {len(g["edges"]):,} residual edges\n{len(heavy):,} heavy; {len(g["edges"])-len(heavy):,} retained'
    else:
        title=f'{g["n"]:,} vertices / {len(g["edges"]):,} edges'
    ax.set_title(title,fontsize=11)


def save(fig,name):
    for ext in ('png','svg'):
        fig.savefig(OUT/'figures'/(name+'.'+ext),dpi=190,bbox_inches='tight',facecolor='white')
    plt.close(fig)


def main():
    (OUT/'figures').mkdir(exist_ok=True)
    data=json.loads((ROOT/'benchmark/results/common-2026-10-11/graph_views.json').read_text())
    for d in data:
        assert d['validation']=='pass_certified_MST_contraction_and_path_oracles'
        layout(d)
    lookup={d['family']:d for d in data}
    (OUT/'graph_data.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    for family,name in [('unbalanced_bipartite_16','core_contraction'),('ring_cliques_16','clique_contraction'),('leaf_core_90','leaf_contraction')]:
        d=lookup[family];fig,axs=plt.subplots(1,3,figsize=(11,3.8),constrained_layout=True)
        for level,ax in enumerate(axs):
            draw(ax,d,level);ax.text(.5,-.04,['Original + first selection','After one contraction + second selection','After two contractions'][level],transform=ax.transAxes,ha='center',fontsize=10)
        fig.suptitle(NAMES[family]+' · complete n=256 instance · graph seed 42',fontsize=13)
        save(fig,name)
    d=lookup['grid3d_distance'];fig,axs=plt.subplots(1,3,figsize=(11,4.3))
    # Leave explicit space for the two-line sample/filter counts; equal-aspect
    # axes otherwise push their titles into the shared figure heading.
    fig.subplots_adjust(left=.025,right=.99,bottom=.13,top=.78,wspace=.1)
    for ax,kind,label in zip(axs,('plain','sample','heavy'),('Residual after two contractions','Half-sample and its MSF','F-heavy (red); forest (teal)')):
        draw(ax,d,2,kind);ax.text(.5,-.04,label,transform=ax.transAxes,ha='center',fontsize=10)
    fig.suptitle('The filtering step on the same full 3D-mesh instance · sample seed 0',fontsize=13)
    save(fig,'filtering_example')
    fig,axs=plt.subplots(2,3,figsize=(11,7.2),constrained_layout=True)
    for ax,family in zip(axs.flat,('unbalanced_bipartite_16','leaf_core_90','ring_cliques_16','grid3d_distance','regular_8','small_world')):
        draw(ax,lookup[family],0);ax.set_title(NAMES[family],fontsize=11)
    fig.suptitle('Full 256-vertex instances; teal edges are the first safe selection',fontsize=14)
    save(fig,'graph_atlas')
    markup='''<div class="explorer" id="explorer">
    <div class="explorer-controls"><label>Graph <select id="family"></select></label>
    <label>Step <select id="stage"><option value="0">1. Original graph</option><option value="1">2. First contraction</option><option value="2">3. Second contraction</option><option value="3">4. Sample forest</option><option value="4">5. Heavy-edge filtering</option></select></label>
    <label><input type="checkbox" id="context-edges" checked> Context edges</label><button id="reset-camera">Reset view</button></div>
    <p id="graph-info" aria-live="polite"></p><canvas id="graph-canvas" tabindex="0" role="img"></canvas>
    <p id="node-detail">Hover a vertex to see its original member count.</p><p id="stage-explanation"></p>
    <p class="caption">Full 256-vertex graphs, seed 42. Drag to rotate; scroll to zoom; arrow keys and +/- also work. Teal: safe/forest edges. Red: removable edges. Purple: designated core. Larger contracted nodes contain more original vertices. Counts describe the graph or sample even when context edges are hidden. Geometry is actual mesh geometry or an explanatory layout; these views are not timing samples.</p></div>'''
    css='''body{margin:0;background:#edf1f3;color:#183043;font:16px/1.55 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:32px}h1{font-size:30px}a{color:#007e88}.explorer{background:#fff;padding:20px;border-radius:8px}.explorer-controls{display:flex;gap:16px;align-items:center;flex-wrap:wrap}select,button{font:inherit;padding:7px;border:1px solid #b9c7d0;border-radius:4px;background:#fff;color:#183043}canvas{width:100%;height:540px;touch-action:none;cursor:grab;background:linear-gradient(#f8fbfc,#fff)}canvas:focus{outline:2px solid #007e88}.caption,#node-detail{font-size:13px;color:#536571}#graph-info{font-variant-numeric:tabular-nums;font-weight:600}@media(max-width:650px){main{padding:12px}.explorer{padding:12px}canvas{height:430px}}'''
    script=(OUT/'explorer.js').read_text()
    fragment=markup+'<script id="graph-data" type="application/json">'+json.dumps(data,separators=(',',':'))+'</script><script>'+script+'</script>'
    (OUT/'explorer_fragment.html').write_text(fragment)
    (OUT/'graph-explorer.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>KKT: inspect the graph transformations</title><style>'+css+'</style><main><h1>Watch the graph become smaller</h1><p>These are actual production contraction and verification results, checked against independent oracles. <a href="report.html">Return to the report</a>.</p>'+fragment+'</main></html>')
    (OUT/'explorer.css').write_text(css)
    print('Built seven complete graph views and five static figures.')

if __name__=='__main__':main()
