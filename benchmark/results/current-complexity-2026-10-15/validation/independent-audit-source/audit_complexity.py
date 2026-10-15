#!/usr/bin/env python3
"""Independently audit raw complexity means, six-model fits and Google choices.

The strict collector is reused for artifact/lifecycle proof only; it indirectly
imports the original analyzer validator. Independent arithmetic below does not
call that analyzer or use its computed values. Descriptive slopes and per-size
summary tables remain hash-bound, outside this narrow arithmetic audit.
"""
import argparse
import csv
from fractions import Fraction
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import re
import sys

FAMILIES = ('leaf_hierarchy4','leaf_shuffled4','gnm_random')
ALGORITHMS = ('kkt','multigraph_boruvka')
GRAPHS = (19000013,19000043)
SAMPLERS = (3001,3011)
SIZES = tuple(2**power for power in range(10,21))
CLOCKS = ('native_steady','native_process_cpu','library_manual','library_process_cpu')
MODELS = ('(1)','lgN','N','NlgN','N^2','N^3')
SPEC = ('family','algorithm','graph_seed','sampling_seed','size_order')
NATIVE_FIELDS = tuple('family,algorithm,n,m,N,graph_seed,sampling_seed,input_fingerprint,topology_fingerprint,size_order,invocation,phase,iteration,elapsed_ns,utc_start_ns,utc_end_ns,process_cpu_start_ns,process_cpu_end_ns,process_cpu_elapsed_ns,validation'.split(','))
TEXT_FIELDS = {'family','algorithm','size_order','phase','validation'}
BASE = {'name','run_name','run_type','repetitions','threads'}
COUNTERS = {'vertices','edges','graph_seed','sampling_seed'}
TIMES = {'iterations','real_time','cpu_time','time_unit'}
SUFFIX = '/iterations:2/repeats:3/process_time/manual_time'
TABLE_COUNTS = dict(means=3168,model_fits=1152,size_summaries=1056,log_log_slopes=192,adjacent_slopes=960,google_selection=24)
HEADERS = {
    'means':(*SPEC,'clock','n','N','invocation','mean_ns','exact_numerator','exact_denominator'),
    'model_fits':(*SPEC,'clock','window','observations','sizes','model','coefficient_ns','normalized_rms','selected_for_this_clock','google_exported_selection'),
    'google_selection':(*SPEC,'selected_model','cpu_coefficient_ns','manual_coefficient_ns','cpu_normalized_rms','manual_reconstructed_normalized_rms','manual_rms_exported'),
}
FLOAT_FIELDS = {'mean_ns','coefficient_ns','normalized_rms','cpu_coefficient_ns','manual_coefficient_ns','cpu_normalized_rms','manual_reconstructed_normalized_rms'}
RELATIVE_TOLERANCE = 2e-10
RMS_ABSOLUTE_TOLERANCE = 1e-12


def require(value,message):
    if not value: raise ValueError(message)


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parse_json(text):
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result,'duplicate JSON key');result[key]=value
        return result
    def invalid(value): raise ValueError('nonfinite JSON: '+value)
    result=json.loads(text,object_pairs_hook=pairs,parse_constant=invalid)
    def finite(value):
        if type(value) is float: require(math.isfinite(value),'nonfinite JSON numeric overflow')
        elif type(value) is dict:
            for item in value.values():finite(item)
        elif type(value) is list:
            for item in value:finite(item)
    finite(result);return result


def exact(actual,expected,label):
    require(type(actual) is type(expected) and actual==expected,label)
    if type(expected) is dict:
        for key in expected:exact(actual[key],expected[key],label+': '+key)
    elif type(expected) is list:
        for left,right in zip(actual,expected):exact(left,right,label)


def number(value,label,positive=False):
    require(type(value) in (int,float) and math.isfinite(value) and (value>0 if positive else value>=0),'invalid number: '+label)
    return float(value)


def close(actual,expected,label,rms=False):
    actual=number(actual,label)
    require(math.isclose(actual,expected,rel_tol=RELATIVE_TOLERANCE,
                         abs_tol=RMS_ABSOLUTE_TOLERANCE if rms else 0.0),'numerical mismatch: '+label)


def bind(bound,path,expected):
    path=Path(path).resolve(strict=True)
    require(type(expected) is str and re.fullmatch('[0-9a-f]{64}',expected),'invalid digest')
    require(str(path) not in bound or bound[str(path)]==expected,'conflicting digest')
    require(digest(path)==expected,'artifact changed: '+str(path));bound[str(path)]=expected
    return path


def read_bound(bound,path,expected):
    path=bind(bound,path,expected);text=path.read_text();bind(bound,path,expected);return text


def recheck(bound):
    for path,expected in bound.items():bind(bound,path,expected)


def schedule():
    result=[]
    for family in FAMILIES:
        for gi,graph in enumerate(GRAPHS):
            for si,sampler in enumerate(SAMPLERS):
                for algorithm in ALGORITHMS if (gi+si)%2==0 else tuple(reversed(ALGORITHMS)):
                    result.append(dict(family=family,algorithm=algorithm,graph_seed=graph,sampling_seed=sampler,
                                       size_order='ascending' if gi==0 else 'descending'))
    return result


def native_rows(text,spec):
    reader=csv.DictReader(io.StringIO(text));exact(tuple(reader.fieldnames or ()),NATIVE_FIELDS,'native header')
    source=list(reader);require(len(source)==99,'incomplete native99 rows')
    sizes=SIZES if spec['size_order']=='ascending' else tuple(reversed(SIZES))
    identities=[(n,repetition,phase,iteration) for n in sizes for repetition in range(3)
                for phase,iteration in (('warmup',0),('timed',0),('timed',1))]
    result=[];previous=None
    for raw,identity in zip(source,identities):
        require(set(raw)==set(NATIVE_FIELDS) and None not in raw.values(),'malformed native row')
        row={}
        for key,value in raw.items():
            if key in TEXT_FIELDS:row[key]=value
            else:
                require(re.fullmatch('0|[1-9][0-9]*',value),'noncanonical integer')
                row[key]=int(value);require(row[key]<(1<<(63 if key.endswith('_ns') else 64)),'integer overflow')
        exact({key:row[key] for key in SPEC},spec,'wrong native curve')
        exact((row['n'],row['invocation'],row['phase'],row['iteration']),identity,'wrong native identity/order')
        m=row['n']*(16 if spec['family']=='gnm_random' else 32)
        require(row['m']==m and row['N']==row['n']+m and row['validation']=='pass','wrong input/validation')
        require(row['elapsed_ns']>0 and row['process_cpu_elapsed_ns']>0 and
                row['process_cpu_end_ns']-row['process_cpu_start_ns']==row['process_cpu_elapsed_ns'],'invalid native clocks')
        require(row['utc_start_ns']>0 and row['utc_end_ns']>0 and
                (previous is None or row['process_cpu_start_ns']>=previous['process_cpu_end_ns']),'invalid native endpoints')
        previous=row
        result.append(row)
    return result


def basis(model,N,compatible=False):
    require(N>0 and model in MODELS,'invalid model/domain')
    if model=='(1)':return 1.0
    if model=='N':return float(N)
    if model=='N^2':return math.pow(N,2) if compatible else float(N*N)
    if model=='N^3':return math.pow(N,3) if compatible else float(N*N*N)
    if compatible:
        return (1.44269504088896340736*math.log(float(N)) if model=='lgN'
                else 1.44269504088896340736*N*math.log(float(N)))
    logarithm=math.log2(N)
    return logarithm if model=='lgN' else N*logarithm


def independent_fit(points,model):
    """Scaled dot products with fsum; distinct from production sequential sums."""
    require(len(points)>=2,'too few fit points')
    xs=[basis(model,N) for N,_ in points];ys=[number(t,'fit time',True) for _,t in points]
    xscale=max(xs);yscale=max(ys)
    xn=[x/xscale for x in xs];yn=[y/yscale for y in ys]
    coefficient=math.fsum(x*y for x,y in zip(xn,yn))/math.fsum(x*x for x in xn)
    residual=math.fsum((y-coefficient*x)**2 for x,y in zip(xn,yn))
    score=math.sqrt(residual/len(points))/(math.fsum(yn)/len(points))
    return dict(model=model,coefficient_ns=(coefficient*yscale)/xscale,normalized_rms=score)


def selected_model(points):
    """Replay v1.5.2's strict floating-point order only for discrete labels.

    Model residual/coefficient evidence is independently recomputed above.
    Google chooses on seconds; canonical custom fits choose on nanoseconds.
    A different summation/log implementation cannot safely resolve a near tie
    on behalf of the library; the label check therefore preserves its order.
    """
    best=None
    for model in MODELS:
        numerator=denominator=total=0.0
        values=[]
        for N,time in points:
            x=basis(model,N,compatible=True);y=float(time);values.append((x,y))
            numerator+=x*y;denominator+=x*x;total+=y
        coefficient=numerator/denominator;residual=0.0
        for x,y in values:residual+=math.pow(y-coefficient*x,2)
        score=math.sqrt(residual/len(values))/(total/len(values))
        if best is None or score<best[1]:best=(model,score)
    return best[0]


def library_means(document,spec,native):
    exact(set(document),{'context','benchmarks'},'unsupported library root')
    required={'date','host_name','num_cpus','mhz_per_cpu','caches','load_avg','library_build_type'}
    require(type(document['context']) is dict and required<=set(document['context'])<=required|{'executable','cpu_scaling_enabled'},'library context')
    reports=document['benchmarks'];require(type(reports) is list and len(reports)==68,'library68 report count')
    native_by_id={(row['n'],row['invocation'],row['iteration']):row for row in native if row['phase']=='timed'}
    sizes=SIZES if spec['size_order']=='ascending' else tuple(reversed(SIZES))
    identities=[(n,kind,index) for n in sizes for kind,index in
                [('iteration',i) for i in range(3)]+[('aggregate',name) for name in ('mean','median','stddev')]]
    identities.extend([(None,'aggregate','BigO'),(None,'aggregate','RMS')])
    stem=f"{spec['algorithm']}/{spec['family']}/graph_{spec['graph_seed']}/sampler_{spec['sampling_seed']}"
    means=[];big_o=rms=None
    for report,(n,kind,index) in zip(reports,identities):
        fields=(BASE|{'aggregate_name','cpu_coefficient','real_coefficient','big_o','time_unit'} if index=='BigO'
                else BASE|{'aggregate_name','rms'} if index=='RMS'
                else BASE|TIMES|COUNTERS|({'repetition_index'} if kind=='iteration' else {'aggregate_name'}))
        exact(set(report),fields,'unsupported library fields/error row')
        run=stem+('' if n is None else '/'+str(n))+SUFFIX
        for key,value in dict(run_name=run,name=run+('_'+str(index) if kind=='aggregate' else ''),run_type=kind,threads=1,repetitions=3).items():
            exact(report[key],value,'library identity: '+key)
        if kind=='aggregate':exact(report['aggregate_name'],index,'aggregate identity')
        if index=='RMS':number(report['rms'],'exported RMS');rms=report;continue
        exact(report['time_unit'],'ns' if index=='BigO' else 'ms','per-report unit')
        if index=='BigO':
            require(report['big_o'] in MODELS,'unknown model');number(report['cpu_coefficient'],'CPU coefficient',True)
            number(report['real_coefficient'],'manual coefficient',True);big_o=report;continue
        exact(report['iterations'],2 if kind=='iteration' else 3,'iteration count')
        number(report['real_time'],'manual time',kind=='iteration');number(report['cpu_time'],'CPU time',kind=='iteration')
        for key in COUNTERS:number(report[key],key)
        m=n*(16 if spec['family']=='gnm_random' else 32)
        if index!='stddev':
            for key,value in dict(vertices=n,edges=m,graph_seed=spec['graph_seed'],sampling_seed=spec['sampling_seed']).items():
                require(report[key]==value,'wrong graph counter')
        if kind!='iteration':continue
        exact(report['repetition_index'],index,'wrong repetition index')
        calls=[native_by_id[(n,index,i)] for i in (0,1)]
        manual=report['real_time']*1000000
        require(math.isclose(manual,float(Fraction(sum(row['elapsed_ns'] for row in calls),2)),
                             rel_tol=5e-12,abs_tol=1.0),'manual mean does not join native calls')
        means.append(dict(n=n,N=n+m,invocation=index,library_manual=manual,
                          library_process_cpu=report['cpu_time']*1000000,
                          manual_seconds=report['real_time']*.001,cpu_seconds=report['cpu_time']*.001))
    require(len(means)==33 and big_o is not None and rms is not None,'missing library inputs')
    cpu=[(row['N'],row['cpu_seconds']) for row in means]
    manual=[(row['N'],row['manual_seconds']) for row in means]
    selected=selected_model(cpu);exact(big_o['big_o'],selected,'Google CPU model selection')
    cpu_fit=independent_fit(cpu,selected);manual_fit=independent_fit(manual,selected)
    close(big_o['cpu_coefficient'],cpu_fit['coefficient_ns']*1e9,'exported CPU coefficient')
    close(big_o['real_coefficient'],manual_fit['coefficient_ns']*1e9,'exported manual coefficient on CPU model')
    close(rms['rms'],cpu_fit['normalized_rms'],'exported CPU RMS',rms=True)
    selection=dict(selected_model=selected,cpu_coefficient_ns=cpu_fit['coefficient_ns']*1e9,
                   manual_coefficient_ns=manual_fit['coefficient_ns']*1e9,cpu_normalized_rms=cpu_fit['normalized_rms'],
                   manual_reconstructed_normalized_rms=manual_fit['normalized_rms'],manual_rms_exported=False)
    return means,selection


def reconstruct(curves):
    exact([curve['spec'] for curve in curves],schedule(),'incomplete fixed24 matrix')
    tables=dict(means=[],model_fits=[],google_selection=[]);fingerprints={}
    for curve in curves:
        spec=curve['spec'];native=native_rows(curve['raw'],spec)
        for row in native:
            key=(spec['family'],spec['graph_seed'],row['n']);value=(row['input_fingerprint'],row['topology_fingerprint'])
            require(key not in fingerprints or fingerprints[key]==value,'graph changed across algorithms/samplers')
            fingerprints[key]=value
        library,selection=library_means(curve['document'],spec,native)
        tables['google_selection'].append(dict(spec,**selection))
        current=[]
        for row in library:
            calls=[item for item in native if item['phase']=='timed' and item['n']==row['n'] and item['invocation']==row['invocation']]
            require(len(calls)==2,'native two-call identity')
            for clock in CLOCKS:
                fraction=None
                if clock in ('native_steady','native_process_cpu'):
                    field='elapsed_ns' if clock=='native_steady' else 'process_cpu_elapsed_ns'
                    fraction=Fraction(calls[0][field]+calls[1][field],2);mean=float(fraction)
                else:mean=row[clock]
                current.append(dict(spec,clock=clock,n=row['n'],N=row['N'],invocation=row['invocation'],mean_ns=mean,
                    exact_numerator=fraction.numerator if fraction is not None else '',
                    exact_denominator=fraction.denominator if fraction is not None else ''))
        tables['means'].extend(current)
        for clock in CLOCKS:
            for window,sizes in (('full11',SIZES),('upper6',SIZES[5:])):
                points=[(row['N'],row['mean_ns']) for row in current if row['clock']==clock and row['n'] in sizes]
                require(len(points)==3*len(sizes),'fit input count');selected=selected_model(points)
                for model in MODELS:
                    tables['model_fits'].append(dict(spec,clock=clock,window=window,observations=len(points),sizes=len(sizes),
                        **independent_fit(points,model),selected_for_this_clock=model==selected,
                        google_exported_selection=window=='full11' and clock=='library_process_cpu' and model==selection['selected_model']))
    for n in SIZES:
        for graph in GRAPHS:
            a=fingerprints[('leaf_hierarchy4',graph,n)];b=fingerprints[('leaf_shuffled4',graph,n)]
            require(a[1]==b[1] and a[0]!=b[0],'topology twin mismatch')
    exact({name:len(rows) for name,rows in tables.items()},{name:TABLE_COUNTS[name] for name in HEADERS},'arithmetic table counts')
    return tables


def compare_csv(text,rows,name):
    reader=csv.DictReader(io.StringIO(text));exact(tuple(reader.fieldnames or ()),HEADERS[name],'canonical table header')
    actual=list(reader);require(len(actual)==len(rows),'canonical row count')
    for index,(found,wanted) in enumerate(zip(actual,rows)):
        require(set(found)==set(HEADERS[name]) and None not in found.values(),'malformed canonical table')
        for key,value in wanted.items():
            label=f'{name}[{index}].{key}'
            if key in FLOAT_FIELDS:
                parsed=float(found[key]);require(math.isfinite(parsed),'nonfinite canonical value')
                if key=='mean_ns':require(parsed==value,'exact mean mismatch: '+label)
                else:close(parsed,value,label,rms='rms' in key)
            else:exact(found[key],str(value),'exact canonical identity/value: '+label)


def provenance_load(collector,capture):
    """Allow the frozen deep package's ordinary sibling imports, then restore."""
    previous_path=list(sys.path)
    name='complexity_audit_checked_collector';previous_module=sys.modules.get(name)
    try:
        sys.path.insert(0,str(collector.parent))
        spec=importlib.util.spec_from_file_location(name,collector)
        require(spec is not None and spec.loader is not None,'cannot import checked collector')
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
        # The original collector indirectly imports its analyzer validator.
        # Its arithmetic results are not inputs to this audit's reconstruction.
        return module.load(capture)
    finally:
        sys.path[:]=previous_path
        if previous_module is None:sys.modules.pop(name,None)
        else:sys.modules[name]=previous_module


def audit(args,bound):
    own=Path(__file__).resolve();bind(bound,own,digest(own))
    capture=Path(args.capture).resolve(strict=True);bind(bound,capture,digest(capture))
    collector=bind(bound,args.collector,args.collector_sha256)
    info,records,inherited=provenance_load(collector,capture)
    exact([record['spec'] for record in records],schedule(),'strict collector returned wrong schedule')
    for path,expected in inherited.items():bind(bound,path,expected)
    for key,value in dict(schema='current_complexity_capture_v1',validation='pass',checked_curves=24,checked_raw_rows=2376,checked_timed_rows=1584,
                          checked_warmup_rows=792,rows_removed=0,rows_adjusted=0,native_process_may_still_be_running=False).items():
        exact(info[key],value,'incomplete capture: '+key)
    require(info['frozen_protocol']['source_sha256'].get(str(collector))==args.collector_sha256,'collector not bound by genuine freeze')
    analysis=Path(args.analysis).resolve(strict=True);metadata_path=analysis/'provenance.json'
    metadata=parse_json(read_bound(bound,metadata_path,digest(metadata_path)))
    for key,value in dict(schema='current_complexity_analysis_v1',validation='pass',capture=str(capture),capture_sha256=digest(capture),
                          checked_curves=24,checked_raw_rows=2376,rows_removed=0,rows_adjusted=0,table_counts=TABLE_COUNTS).items():
        exact(metadata[key],value,'analysis metadata: '+key)
    for path,expected in metadata['input_sha256'].items():bind(bound,path,expected)
    for path,expected in inherited.items():require(metadata['input_sha256'].get(path)==expected,'analysis missed checked input')
    output_names={str(analysis/(name+'.csv')) for name in TABLE_COUNTS}|{str(analysis/name) for name in ('clock_flags.json','library_reports.json')}
    exact(set(metadata['output_sha256']),output_names,'canonical output inventory')
    for path,expected in metadata['output_sha256'].items():bind(bound,path,expected)
    curves=[]
    for record in records:
        raw=read_bound(bound,record['raw_csv'],record['raw_sha256'])
        document=parse_json(read_bound(bound,record['benchmark_json'],record['benchmark_sha256']))
        curves.append(dict(spec=record['spec'],raw=raw,document=document))
    tables=reconstruct(curves)
    for name,rows in tables.items():
        path=analysis/(name+'.csv');compare_csv(read_bound(bound,path,metadata['output_sha256'][str(path)]),rows,name)
    recheck(bound)
    return tables,dict(checked_curves=24,checked_native_rows=2376,checked_two_call_means=3168,checked_model_fits=1152,
                       checked_google_choices=24,independently_audited_tables=list(HEADERS),
                       hash_bound_not_independently_recomputed=['size_summaries','log_log_slopes','adjacent_slopes','clock_flags.json','library_reports.json'],
                       clock_flag_count=metadata['clock_flag_count'],flagged_call_count=metadata['flagged_call_count'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('capture','collector','analysis','output-dir'):parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--collector-sha256',required=True);parser.add_argument('--released',action='store_true')
    args=parser.parse_args();require(args.released,'explicit nonperformance audit release required')
    output=args.output_dir.resolve();output.mkdir(parents=True,exist_ok=False);bound={}
    result=dict(schema='current_complexity_independent_arithmetic_audit_v1',validation='running',invocation=sys.argv,
                native_solver_execution=False,original_analyzer_arithmetic_reused_for_independent_calculations=False,
                original_analyzer_validator_indirectly_imported_by_strict_collector=True,rows_removed=0,rows_adjusted=0,
                arithmetic='scaled fsum dot products; source-order discrete selection replay',
                relative_tolerance=RELATIVE_TOLERANCE,rms_absolute_tolerance=RMS_ABSOLUTE_TOLERANCE,
                native_and_library_mean_comparison='exact float of independently reconstructed arithmetic mean/unit conversion',
                ordinary_aggregates_recomputed=False,input_sha256=bound)
    try:
        tables,summary=audit(args,bound)
        for name,rows in tables.items():
            with (output/(name+'.csv')).open('x',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=HEADERS[name]);writer.writeheader();writer.writerows(rows)
        recheck(bound);result.update(validation='pass',**summary)
    except BaseException as error:result.update(validation='failed',error=repr(error));raise
    finally:
        result['output_sha256']={str(path.relative_to(output)):digest(path) for path in output.iterdir() if path.is_file()}
        with (output/'audit.json').open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
    print(json.dumps({key:result[key] for key in ('validation','checked_two_call_means','checked_model_fits','checked_google_choices')}))


if __name__=='__main__':main()
