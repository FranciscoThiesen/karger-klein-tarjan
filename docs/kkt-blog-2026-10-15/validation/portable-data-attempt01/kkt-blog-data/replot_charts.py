#!/usr/bin/env python3
"""Replot exported blog tables, without native solvers or raw-audit dependencies.

Requires Python >=3.9 and matplotlib. The portable manifest checks table and
generator bytes; it does not recreate the study's native correctness proofs.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def require(ok,message):
    if not ok: raise ValueError(message)

def main():
    here=Path(__file__).resolve().parent
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,default=here/'data')
    parser.add_argument('--generator',type=Path,default=here/'plot_results.py')
    parser.add_argument('--manifest',type=Path,default=here/'provenance.json')
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args(); output=args.output_dir.resolve()
    require(not output.exists(),'refusing to overwrite an existing output directory')
    manifest=args.manifest.resolve(strict=True); manifest_hash=sha(manifest)
    proof=json.loads(manifest.read_text())
    require(proof['schema']=='kkt_blog_portable_chart_data_v1' and proof['validation']=='pass',
            'unsupported or unaccepted portable data manifest')
    bindings={str(manifest):manifest_hash}
    for path,name in ((args.generator,'plot_results.py'),(Path(__file__),'replot_charts.py')):
        path=path.resolve(strict=True); expected=proof['portable_files_sha256'][name]
        require(sha(path)==expected,'generator/replot source hash differs');bindings[str(path)]=expected
    values={}
    for name,count in proof['chart_table_counts'].items():
        path=(args.data_dir/(name+'.csv')).resolve(strict=True)
        expected=proof['portable_files_sha256']['data/'+name+'.csv']
        require(sha(path)==expected,'exported CSV hash differs: '+name);bindings[str(path)]=expected
        with path.open(newline='') as stream:rows=list(csv.DictReader(stream))
        require(len(rows)==count,'exported row count differs: '+name)
        for row in rows:
            if name in ('crossover','endpoints','endpoint_ratios','reversal'):
                for key in ('value','minimum','maximum','g1','g2'):row[key]=float(row[key])
            elif name=='volume':row['count']=int(row['count']);row['per_m']=float(row['per_m'])
            elif name=='partition':
                for key in ('graph_seed','m','base','partition','total'):row[key]=int(row[key])
                for key in ('base_per_m','partition_per_m'):row[key]=float(row[key])
            require(all(not isinstance(v,float) or math.isfinite(v) for v in row.values()),'nonfinite CSV number')
        values[name]=rows
    spec=importlib.util.spec_from_file_location('accepted_blog_chart_generator',args.generator)
    require(spec is not None and spec.loader is not None,'cannot import accepted chart renderer')
    generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
    # Import defines the original data() and main(), but invokes neither.
    # Only the pure exported-table presentation function is called below.
    output.mkdir(parents=True);files=[]
    for mobile in (False,True):
        generated,version=generator.render(values,output,mobile);files.extend(generated)
    for path,value in bindings.items():require(sha(path)==value,'input changed during replot')
    report=dict(schema='kkt_blog_portable_replot_v1',validation='pass',matplotlib_version=version,
                expected_original_matplotlib_version=proof['matplotlib_version'],
                native_solver_execution=False,raw_audit_recomputed=False,new_aggregation_or_model_fits=False,
                input_sha256=bindings,chart_table_counts=proof['chart_table_counts'],
                output_sha256={p.name:sha(p) for p in files},visual_review='pending in the new environment')
    with (output/'replot-receipt.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps({'validation':'pass','assets':len(files),'native_solver_execution':False}))


if __name__=='__main__':main()
