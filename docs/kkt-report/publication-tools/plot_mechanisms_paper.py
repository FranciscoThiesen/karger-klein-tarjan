#!/usr/bin/env python3
"""Paper-width layouts of the checked retention model and tiny witness.

Source preparation only. No measured timing/counter input or native solver is
read. Recompute the original small checks and require exact archived values.
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


def require(value,message):
    if not value:raise ValueError(message)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bind(bound,path,expected=None):
    path=Path(path).resolve(strict=True);actual=sha(path)
    require(expected is None or actual==expected,'changed input: '+str(path))
    require(str(path) not in bound or bound[str(path)]==actual,'conflicting input')
    bound[str(path)]=actual;return path


def recheck(bound):
    for path,digest in bound.items():bind(bound,path,digest)


def canonical(value):
    # Normalize JSON's integer-key conversion before sorting; keep numeric types.
    normalized=json.loads(json.dumps(value,allow_nan=False))
    return json.dumps(normalized,sort_keys=True,separators=(',',':'),allow_nan=False)


def same(actual,expected,message):require(canonical(actual)==canonical(expected),message)


def write_json(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False)


def checked_csv(path,records):
    with path.open(newline='') as stream:
        reader=csv.DictReader(stream);require(reader.fieldnames==list(records[0]),'canonical CSV header differs')
        actual=list(reader)
    expected=[{key:'' if value is None else str(value) for key,value in row.items()} for row in records]
    require(actual==expected,'canonical CSV values differ')


def load(args):
    bound={};bind(bound,__file__)
    directory=args.standalone.resolve(strict=True)
    provenance=json.loads(bind(bound,directory/'provenance.json').read_text())
    schema='analytic_hierarchy_retention_figure_v1' if args.kind=='retention' else 'illustrative_sampling_witness_figure_v1'
    require(provenance['schema']==schema and provenance['validation']=='pass','wrong standalone mechanism provenance')
    same(provenance['measured_input_files'],[],'mechanism must not use measured inputs')
    for path,digest in provenance['source_sha256'].items():bind(bound,path,digest)
    source=args.source_plot.resolve(strict=True)
    require(str(source) in provenance['source_sha256'],'source not bound by original mechanism figure')
    stem='hierarchy_expectation' if args.kind=='retention' else 'sampling_witness'
    names={stem+'.'+suffix for suffix in ('png','svg','pdf')}
    names|={'theoretical_values.csv','enumeration_checks.json'} if args.kind=='retention' else {'witness_edges.csv','independent_checks.json'}
    require(set(provenance['output_sha256'])==names,'incomplete original mechanism artifact inventory')
    for name,digest in provenance['output_sha256'].items():bind(bound,directory/name,digest)
    spec=importlib.util.spec_from_file_location('reviewed_original_mechanism',source)
    require(spec is not None and spec.loader is not None,'cannot load reviewed source')
    original=importlib.util.module_from_spec(spec);sys.modules[spec.name]=original;spec.loader.exec_module(original)
    if args.kind=='retention':
        same(provenance['theoretical_expectation_only'],True,'theory scope changed')
        same(original.declared_manifest(),provenance['manifest'],'model declaration changed')
        checks=original.enumeration_checks();rows=original.theoretical_rows();values=original.exported(rows)
        same(json.loads((directory/'enumeration_checks.json').read_text()),checks,'enumeration checks changed')
        require(len(rows)==55==provenance['rows'],'retention model incomplete')
        checked_csv(directory/'theoretical_values.csv',values)
        payload=dict(rows=rows,values=values,checks=checks)
    else:
        same(provenance['native_executed'],False,'unexpected native witness')
        edges,sample,light,checks=original.checked_witness()
        same(json.loads((directory/'independent_checks.json').read_text()),checks,'tiny graph checks changed')
        values=[{**edge,'in_original_mst':edge['id'] in checks['true_mst_ids'],
                 'sampled':edge['id'] in checks['sample_forest_ids'],
                 'forest_path_maximum':checks['path_maxima'][edge['id']],
                 'f_light':edge['id'] in checks['light_ids']} for edge in edges]
        checked_csv(directory/'witness_edges.csv',values)
        positions={v:(math.cos(math.pi/2-2*math.pi*v/original.N),math.sin(math.pi/2-2*math.pi*v/original.N))
                   for v in range(original.N)}
        same(provenance['positions'],positions,'original illustrative geometry changed')
        payload=dict(edges=edges,sample=sample,light=light,checks=checks,values=values,positions=positions)
    recheck(bound)
    return original,provenance,payload,bound


def save(plt,figure,output,name):
    for suffix in ('png','svg','pdf'):figure.savefig(output/(name+'.'+suffix),dpi=220,facecolor='white')
    plt.close(figure)


def retention_render(original,provenance,payload,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9.5,'axes.spines.top':False,
                         'axes.spines.right':False,'svg.fonttype':'none','pdf.fonttype':42})
    rows=payload['rows'];fields=('expected_input_over_m','expected_cumulative_input_over_m')
    fig,axes=plt.subplots(2,1,figsize=(7.1,8.6));fig.subplots_adjust(left=.14,right=.98,bottom=.19,top=.87,hspace=.43)
    colors,markers=('#1768ac','#d97816','#25854b'),('o','s','^')
    coverage=[];points=[]
    for index,n in enumerate(original.SIZES):
        selected=[row for row in rows if row['n']==n];rounds=[row['full_contraction_round'] for row in selected]
        require(rounds==list(range(1,selected[0]['core_rounds']+2)),'missing model round')
        for axis,field in zip(axes,fields):
            values=[float(row[field]) for row in selected]
            axis.plot(rounds,values,color=colors[index],marker=markers[index],ms=4,lw=1.5,
                      label=f'n={n:,}: {len(rounds)} rounds')
            coverage.append(dict(panel=field,n=n,rounds=rounds,points=len(rounds),extrapolated_rounds=0))
            points.extend(dict(n=n,round=r,field=field,value=value) for r,value in zip(rounds,values))
    for axis,title,label in zip(axes,('Input volume of each contraction','Accumulated contraction input'),
                                ('Expected input / original m','Expected accumulated input / original m')):
        axis.set_title(title,loc='left',fontsize=11);axis.set_xlabel('Full contraction round (stars collapse in round 1)',fontsize=9)
        axis.set_ylabel(label,fontsize=9);axis.set_xticks(range(1,22,2));axis.set_xlim(.5,21.5)
        axis.tick_params(labelsize=9);axis.grid(alpha=.18)
    axes[0].set_ylim(0,1.05);axes[1].set_ylim(0,1.07*max(float(row[fields[1]]) for row in rows))
    for axis,field in zip(axes,fields):
        low,high=axis.get_ylim();require(all(low<=float(row[field])<=high for row in rows),'model point clipped')
    same(coverage,provenance['coverage'],'paper model coverage differs from standalone')
    require(len(points)==110,'model point count changed')
    expected=[dict(n=n,round=row['full_contraction_round'],field=field,value=float(row[field]))
              for n in original.SIZES for field in fields for row in rows if row['n']==n]
    same(points,expected,'model plotted values changed')
    fig.suptitle('THEORETICAL EXPECTATION: retained hierarchy edges',fontsize=12,y=.98)
    fig.text(.5,.94,'Uniform nonpath chords; m/n=32. No measured timings or counters.',ha='center',fontsize=9.5)
    handles,labels=axes[0].get_legend_handles_labels();require(len(labels)==3,'missing size legend')
    fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.5,.105),ncol=1,frameon=False,fontsize=9)
    fig.text(.5,.055,'Every defined input round is shown; each curve stops at its own final contraction.',ha='center',fontsize=8.5)
    fig.text(.5,.027,'One input-edge count per call: not measured scans, CPU cost, memory or runtime.',ha='center',fontsize=8.5)
    save(plt,fig,output,'paper_hierarchy_expectation')
    return dict(values=payload['values'],checks=payload['checks'],points=points,coverage=coverage,
                matplotlib_version=matplotlib.__version__)


def witness_render(original,provenance,payload,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9.5,'svg.fonttype':'none','pdf.fonttype':42})
    edges,sample,light,checks=(payload[key] for key in ('edges','sample','light','checks'))
    positions=payload['positions'];mst=set(checks['true_mst_ids']);forest=set(checks['sample_forest_ids'])
    colors=dict(mst='#1768ac',sample_chord='#d97816',other='#a9afb8')
    fig,axes=plt.subplots(3,1,figsize=(7.1,9.0));fig.subplots_adjust(left=.06,right=.98,bottom=.17,top=.91,hspace=.29)
    titles=(f'Parent: {len(edges)} edges; {len(checks["boruvka_rounds"]["full"])} Borůvka rounds',
            f'Chosen sample H=F: {len(sample)} edges; {checks["non_mst_sample_forest_edges"]} non-MST chords; {len(checks["boruvka_rounds"]["sample"])} rounds',
            f'F-light parent: {len(light)} edges; {checks["heavy_edges"]} removed; {len(checks["boruvka_rounds"]["light"])} rounds')
    coverage=[];drawn_records=[]
    for panel,(axis,graph,title) in enumerate(zip(axes,(edges,sample,light),titles)):
        drawn=[]
        for edge in sorted(graph,key=lambda e:(e['id'] in mst or e['id'] in forest,e['weight'])):
            category='mst' if edge['id'] in mst else 'sample_chord' if edge['id'] in forest else 'other'
            a,b=positions[edge['u']],positions[edge['v']];important=category!='other'
            axis.plot((a[0],b[0]),(a[1],b[1]),color=colors[category],lw=2 if important else .65,
                      alpha=1 if important else .48,ls='--' if category=='sample_chord' else '-',zorder=2 if important else 1)
            if important:
                axis.text((a[0]+b[0])/2,(a[1]+b[1])/2,str(edge['weight']),ha='center',va='center',
                          fontsize=8.5,color=colors[category],zorder=4,
                          bbox=dict(boxstyle='round,pad=.1',fc='white',ec='none',alpha=.95))
            drawn.append(edge['id']);drawn_records.append(dict(panel=panel,edge=edge,category=category))
        for vertex,(x,y) in positions.items():
            axis.scatter([x],[y],s=155,facecolor='white',edgecolor='#303640',lw=1,zorder=5)
            axis.text(x,y,str(vertex),ha='center',va='center',zorder=6,fontsize=9)
        axis.set_aspect('equal');axis.set_xlim(-1.18,1.18);axis.set_ylim(-1.18,1.18);axis.axis('off')
        axis.set_title(title,fontsize=10,pad=7)
        require(len(drawn)==len(graph) and set(drawn)=={edge['id'] for edge in graph},'witness edge omitted or duplicated')
        coverage.append(dict(panel=panel,vertices_drawn=original.N,edge_ids_drawn=drawn,
                             weight_labels=[edge['weight'] for edge in graph if edge['id'] in mst|forest]))
    same(coverage,provenance['coverage'],'paper witness coverage differs from standalone')
    require(len(drawn_records)==45,'missing witness stage record')
    expected=[dict(panel=panel,edge=edge,category='mst' if edge['id'] in mst else
                   'sample_chord' if edge['id'] in forest else 'other')
              for panel,graph in enumerate((edges,sample,light))
              for edge in sorted(graph,key=lambda e:(e['id'] in mst or e['id'] in forest,e['weight']))]
    same(drawn_records,expected,'witness plotted edge values changed')
    handles=[Line2D([],[],color=colors['mst'],lw=2,label='Edges of the original unique MST'),
             Line2D([],[],color=colors['sample_chord'],lw=2,ls='--',label='Sampled forest chords outside that MST'),
             Line2D([],[],color=colors['other'],lw=1,label='Other high chords')]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.075),ncol=1,frameon=False,fontsize=8.5)
    fig.suptitle('ILLUSTRATIVE WITNESS: a different tree can filter safely',fontsize=12,y=.982)
    fig.text(.5,.949,'All edges drawn; important labels are distinct weights; positions are illustrative.',ha='center',fontsize=8.5)
    fig.text(.5,.043,'Every original MST edge survives. Chosen sample, not a timing input or typical draw.',ha='center',fontsize=8.5)
    heavy=[e['weight'] for e in edges if e['id'] in checks['heavy_ids']]
    fig.text(.5,.019,f'Other high chords have weights {min(heavy)}-{max(heavy)}. Counts and full round traces remain archived.',ha='center',fontsize=8.5)
    save(plt,fig,output,'paper_sampling_witness')
    return dict(values=payload['values'],checks=checks,positions=positions,coverage=coverage,
                drawn_records=drawn_records,matplotlib_version=matplotlib.__version__)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind',choices=('retention','witness'),required=True)
    for name in ('standalone','source-plot','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--released',action='store_true');args=parser.parse_args()
    require(args.released,'explicit nonperformance paper release required')
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    metadata=dict(schema='kkt_mechanism_paper_figure_v1',validation='running',invocation=sys.argv,
                  native_solver_execution=False,measured_inputs=[],visual_review='pending')
    try:
        original,provenance,payload,bound=load(args);metadata['input_sha256']=bound
        result=(retention_render if args.kind=='retention' else witness_render)(original,provenance,payload,output)
        write_json(output/'paper_values.json',result);recheck(bound)
        # Retain the exact original canonical bytes as well as the rendered inventory.
        names=('theoretical_values.csv','enumeration_checks.json') if args.kind=='retention' else ('witness_edges.csv','independent_checks.json')
        for name in names:
            data=(args.standalone/name).read_bytes()
            with (output/name).open('xb') as stream:stream.write(data)
            require(sha(output/name)==provenance['output_sha256'][name],'copied canonical data differs')
        recheck(bound)
        metadata.update(validation='rendered_pending_visual_qa',kind=args.kind,figures=1,
                        panels=2 if args.kind=='retention' else 3,figure_width_inches=7.1,
                        minimum_text_points=8.5,original_canonical_values_equal=True,
                        all_original_panels_preserved=True,original_artifacts_modified=False,
                        mathematical_illustration_only=True,performance_claim=False)
    except BaseException as error:metadata.update(validation='failed',error=repr(error));raise
    finally:
        metadata['output_sha256']={str(p.relative_to(output)):sha(p) for p in output.rglob('*') if p.is_file()}
        write_json(output/'provenance.json',metadata)
    print(json.dumps({key:metadata[key] for key in ('validation','kind','panels')}))


if __name__=='__main__':main()
