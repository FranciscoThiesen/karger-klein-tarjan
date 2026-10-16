#!/usr/bin/env python3
"""Light strict completed phase/work inspection; no allocation/calibration claim."""
import argparse
import json
from pathlib import Path
import analyze_diagnostics as a


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('build','phase','work','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--source-snapshot',type=Path);args=p.parse_args()
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False);bound={}
    result=dict(validation='running',native_execution=False,input_sha256=bound,
                scope='Completed phase/work only; full four-mode diagnostic analysis remains separate.')
    try:
        a.read(__file__,bound);a.read(a.__file__,bound);a.read(a.HERE/'README.md',bound)
        snapshot=a.source_snapshot(args.source_snapshot,bound);result['source_snapshot']=snapshot
        build=args.build.resolve();a.load_build(build,bound,snapshot)
        old=a.historical(bound);validator,fields=a.row_validator(bound)
        captures={mode:a.load_capture(getattr(args,mode),mode,build,bound,old,validator,fields,snapshot)
                  for mode in ('phase','work')}
        captures.update(allocation=[],calibration=[])
        tables=a.tables(captures,old,fields)
        for name,rows in tables.items():
            if rows:a.write_csv(output/(name+'.csv'),rows)
        endpoints=[]
        for family in a.FAMILIES:
            for counter in a.HISTORICAL_COUNTS:
                for g in a.GRAPHS:
                    for s in a.SEEDS:
                        rows=sorted((r for r in tables['historical_cpu_work'] if
                            (r['family'],r['counter'],r['graph_seed'],r['sampling_seed'])==(family,counter,g,s)),key=lambda r:r['n'])
                        a.require(len(rows)==6,'exact endpoint curve')
                        lo,hi=rows[0],rows[-1]
                        endpoints.append(dict(family=family,counter=counter,graph_seed=g,sampling_seed=s,
                            small_count_per_N=lo['count_per_N'],large_count_per_N=hi['count_per_N'],
                            count_per_N_growth=hi['count_per_N']/lo['count_per_N'] if lo['count'] else '',
                            small_cpu_ns_per_count=lo['historical_cpu_ns_per_counter'],
                            large_cpu_ns_per_count=hi['historical_cpu_ns_per_counter'],
                            cpu_per_count_growth=hi['historical_cpu_ns_per_counter']/lo['historical_cpu_ns_per_counter'] if lo['count'] and hi['count'] else ''))
        a.write_csv(output/'counter_endpoints.csv',endpoints);a.recheck(bound)
        result.update(validation='pass',exact_google_joins=72,phase_raw_rows=288,work_raw_rows=144,
                      table_counts={k:len(v) for k,v in tables.items() if v},endpoint_rows=len(endpoints))
    except BaseException as error:result.update(validation='failed',error=repr(error));raise
    finally:
        result['output_sha256']={p.name:a.sha(p) for p in output.iterdir() if p.is_file()}
        (output/'provenance.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('input_sha256','output_sha256','source_snapshot')}))


if __name__=='__main__':main()
