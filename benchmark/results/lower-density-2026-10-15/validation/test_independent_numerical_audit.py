#!/usr/bin/env python3
"""Synthetic standalone-audit gates; no native solver launches.

No collector code, native binary or timing observations are imported. The full
raw fixture mocks only the already separate ancestor-artifact proof; a separate
temporary-file test exercises that recursive hash proof without native calls.
"""
import contextlib
import copy
import csv
import datetime
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

PATH=Path(__file__).with_name('independent_numerical_audit.py')
SPEC=importlib.util.spec_from_file_location('lower_density_independent_audit',PATH)
audit=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(audit)
LADDERS=((16,(512,2048,8192,32768,131072,524288,2097152)),
         (8,(256,1024,4096,16384,65536,262144,1048576,4194304)))
FAMILIES=('leaf_distance4','leaf_shuffled4')
GRAPHS=(23000003,23000029)
ALGORITHMS=('kkt','compacting_boruvka','multigraph_boruvka','kruskal','prim','boruvka')


def fixture():
    specs={};rows=[]
    for density,sizes in LADDERS:
      for n in sizes:
        for family in FAMILIES:
            case=f'{family}_n{n}_d{density}_p0'
            specs[case]=dict(case_id=case,family=family,n=n,m=density*n,density=density,intrusion_per_mille=0)
    for gi,graph in enumerate(GRAPHS):
        for ci,case in enumerate(list(specs) if gi==0 else list(reversed(specs))):
            spec=specs[case];fi=FAMILIES.index(spec['family'])
            di=0 if spec['density']==16 else 1;ni=LADDERS[di][1].index(spec['n'])
            cpu=0;utc=946684800_000000000+(gi*30+ci)*2_000000000
            for phase,count in (('warmup',1),('timed',6)):
                for rep in range(count):
                    for order in range(6):
                        ai=(rep+order)%6
                        wall=100003+1009*fi+701*ni+307*gi+103*rep+41*ai+7*rep*ai+1399*di
                        duration=70001+701*fi+503*ni+211*gi+79*rep+23*ai+3*rep*ai+1193*di
                        rows.append(dict(**spec,graph_seed=graph,kkt_seed=3407,input_fingerprint=1000+fi+ni*20+gi*200+di*10000,
                            topology_fingerprint=100+fi//2+ni*10+gi*100+di*10000,phase=phase,repetition=rep,order=order,
                            warmups=1,algorithm=ALGORITHMS[ai],elapsed_ns=wall,utc_start_ns=utc,utc_end_ns=utc+wall,
                            process_cpu_start_ns=cpu,process_cpu_end_ns=cpu+duration,process_cpu_elapsed_ns=duration,validation='pass'))
                        cpu+=duration+10;utc+=wall+10
    return specs,rows


def median(values):
    values=sorted(values);middle=len(values)//2
    return (Fraction(values[middle-1])+Fraction(values[middle]))/2


def write_json(path,value):path.write_text(json.dumps(value,indent=2)+'\n')


def write_rows(path,rows,fields=audit.FIELDS):
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)


@contextlib.contextmanager
def raw_fixture():
    with tempfile.TemporaryDirectory() as temporary:
        root=Path(temporary).resolve();(root/'benchmark').mkdir();source=root/'benchmark/retention_control.cpp';source.write_text('synthetic source')
        specs,rows=fixture();study=root/'benchmark/results/lower-density-2026-10-15';study.mkdir(parents=True)
        manifest=study/'manifest.csv';protocol=study/'PROTOCOL.md';protocol.write_text('synthetic declaration')
        collector=root/'benchmark/run_lower_density.py';collector.write_text('synthetic collector')
        write_rows(manifest,[{k:r[k] for k in ('family','n','density','intrusion_per_mille')} for r in specs.values()],
                   ('family','n','density','intrusion_per_mille'))
        policy={'sampling_policy':'eighth','private_acceptance_mask':7,'sampling_words_per_visited_edge':1,'verifier_policy':'compressed'}
        commands=[[] for _ in range(12)]
        commands[6]=['-DKKT_EXPERIMENT_COMPRESSED_QUERIES','-c','verifier/verifier_v2.cpp']
        commands[8]=['-DKKT_EXPERIMENT_EIGHTH_SAMPLING','-c','kkt/kkt.cpp']
        record={'schema':'eighth_sampling_build_v1','profile':'timing-build','variant':'eighth','role':'timing_never_executed',
                'compressed_queries_fixed':True,'public_scalar_sampling_fixed':True,
                'seven_non_kkt_objects_identical_by_construction':True,**policy,'executables':[dict(policy)],
                'object_paths':{str(i):str(root/f'{i}.o') for i in range(8)},'build_commands':commands,
                'binary_profile':{'file_description':'Mach-O 64-bit executable arm64','main_stack_bytes':536870912}}
        artifact={'binary':str(root/'synthetic-never-executed'),'binary_sha256':'unused','build':{'record':record}}
        parent={'schema':'eighth_sampling_freeze_v1','working_directory':str(root),'variants':{'half':{},'eighth':artifact},
                'source_sha256':{'benchmark/retention_control.cpp':audit.digest(source)},'build_recipe_sha256':{}}
        parent_path=root/'parent.json';write_json(parent_path,parent)
        schedule=[dict(case_id=case,graph_seed=graph,kkt_seed=3407)
                  for gi,graph in enumerate(GRAPHS) for case in (list(specs) if gi==0 else list(reversed(specs)))]
        freeze={'schema':'lower_density_freeze_v1','candidate_variant':'eighth','working_directory':str(root),**artifact,
                'source_sha256':parent['source_sha256'],'build_recipe_sha256':{},'parent_freeze':str(parent_path),
                'parent_freeze_sha256':audit.digest(parent_path),'manifest':str(manifest),'manifest_sha256':audit.digest(manifest),
                'protocol':str(protocol),'protocol_sha256':audit.digest(protocol),
                'python_source_sha256':{str(collector):audit.digest(collector)},'algorithms':list(ALGORITHMS),
                'graph_seeds':list(GRAPHS),'sampling_seeds':[3407],'repetitions':6,'warmups':1,'schedule':schedule,
                'resource_rule':{'rss_limit_kib':40*1024*1024,'poll_seconds':2}}
        frozen_path=root/'freeze.json';write_json(frozen_path,freeze)
        output=root/'lower-density.csv';folder=root/'lower-density_cases';folder.mkdir();write_rows(output,rows)
        utc=lambda seconds:(datetime.datetime(2000,1,1,tzinfo=datetime.timezone.utc)+datetime.timedelta(seconds=seconds)).isoformat()
        info={'schema':'lower_density_capture_v1','validation':'pass','rows_removed':0,'rows_adjusted':0,'cleanup':[],
              'native_process_may_still_be_running':False,'freeze':str(frozen_path),'freeze_sha256':audit.digest(frozen_path),
              'frozen_protocol':freeze,'output':str(output),'output_sha256':audit.digest(output),'captures':[],
              'started_monotonic_ns':0,'finished_monotonic_ns':128_000000000,'monotonic_elapsed_seconds':128.0,
              'started_utc':utc(0),'finished_utc':utc(128),'checked_rows':2520,'checked_timed_rows':2160,
              'checked_warmup_rows':360,'flagged_calls':0,'capture_clock_flags':[],'call_diagnostics':[]}
        for index,identity in enumerate(schedule,1):
            selected=rows[(index-1)*42:index*42];spec=specs[identity['case_id']]
            raw=folder/f"{index:04d}_{identity['case_id']}_g{identity['graph_seed']}_s3407.csv";write_rows(raw,selected)
            cert={name:selected[0][name] for name in audit.CERTIFICATE};log=raw.with_suffix('.log')
            log.write_text('reference_certificate_v1 '+json.dumps(cert)+'\n')
            start=(index-1)*2_000000000;end=start+1_000000000;group=10000+index
            requests=(start+100,end-500)
            observations=[dict(utc=utc(2*(index-1)),monotonic_ns=request,process_group=group,validation='pass',
                               members=[{'pid':group,'rss_kib':1024}] if i==0 else [],rss_kib=1024 if i==0 else 0)
                          for i,request in enumerate(requests)]
            events=[dict(process_group=group,requested_monotonic_ns=request,returned_monotonic_ns=request+10,
                         provider_started_monotonic_ns=request+1,provider_finished_monotonic_ns=request+9,
                         previous_request_gap_ns=None if i==0 else request-requests[i-1],sampler_duration_ns=10,outcome='pass')
                    for i,request in enumerate(requests)]
            rss=raw.with_suffix('.rss.jsonl');rss.write_text(''.join(json.dumps(r)+'\n' for r in observations))
            argv=[artifact['binary'],'--family',spec['family'],'--n',str(spec['n']),'--density',str(spec['density']),'--graph-seed',str(identity['graph_seed']),
                  '--kkt-seed','3407','--repetitions','6','--warmups','1']
            info['captures'].append({**identity,'exit_status':0,'validation':'pass','interruption':None,'rows':42,
                'started_monotonic_ns':start,'finished_monotonic_ns':end,'monotonic_elapsed_seconds':1.0,
                'started_utc':utc(2*(index-1)),'finished_utc':utc(2*(index-1)+1),'csv':str(raw),'output_sha256':audit.digest(raw),
                'log':str(log),'log_sha256':audit.digest(log),'rss_log':str(rss),'rss_sha256':audit.digest(rss),
                'command':argv,'launch_command':['/usr/bin/time','-l',*argv],'process_group':group,'certificate':cert,'flagged_calls':0,
                'rss_observations':2,'rss_unavailable':0,'rss_nonempty_observations':1,'sampled_peak_rss_kib':1024,
                'recovery_monitor':{'observations':events,'max_sampler_duration_ns':10,'max_request_gap_ns':requests[1]-requests[0]},
                'wrapper_exit_monotonic_ns':end-1000,'group_exit_verification':observations[-1]})
            for row in selected:
                wall,cpu=row['elapsed_ns'],row['process_cpu_elapsed_ns']
                info['call_diagnostics'].append({**identity,**{name:row[name] for name in ('phase','repetition','order','algorithm')},
                    'elapsed_ns':wall,'process_cpu_elapsed_ns':cpu,'utc_elapsed_ns':wall,'steady_minus_cpu_ns':wall-cpu,
                    'utc_minus_steady_ns':0,'diagnostic_flags':[],'excluded':False})
        path=output.with_suffix('.json');write_json(path,info)
        declarations={str(p.relative_to(root)):audit.digest(p) for p in (collector,protocol,manifest)}
        with mock.patch.object(audit,'hash_freeze',return_value=freeze),mock.patch.object(audit,'PARENT_SHA256',audit.digest(parent_path)),\
                mock.patch.object(audit,'DECLARATION_SHA256',declarations):
            yield root,path,info,rows


class IndependentAuditTests(unittest.TestCase):
    def setUp(self):audit.INPUTS.clear()

    def test_all_pairs_and_1980_exact_summary_medians(self):
        specs,rows=fixture();self.assertEqual((len(rows),sum(r['phase']=='timed' for r in rows)),(2520,2160))
        tables=audit.numerical_tables(rows,specs);self.assertEqual({k:len(v) for k,v in tables.items()},audit.TABLE_COUNTS)
        raw={(r['case_id'],r['graph_seed'],r['repetition'],r['algorithm']):r for r in rows if r['phase']=='timed'}
        expected={};groups={name:{} for name in ('comparisons','graph_comparisons','summary','graph_summary')}
        for case in specs:
            for graph in GRAPHS:
                for rep in range(6):
                    for metric,field in (('wall','elapsed_ns'),('cpu','process_cpu_elapsed_ns')):
                        for algorithm in ALGORITHMS:
                            value=raw[case,graph,rep,algorithm][field]
                            groups['summary'].setdefault((case,algorithm,metric),[]).append(Fraction(value))
                            groups['graph_summary'].setdefault((case,algorithm,metric,graph),[]).append(Fraction(value))
                            if algorithm=='kkt':continue
                            ratio=Fraction(raw[case,graph,rep,'kkt'][field],value)
                            expected[case,algorithm,metric,graph,3407,rep]=ratio
                            groups['comparisons'].setdefault((case,algorithm,metric),[]).append(ratio)
                            groups['graph_comparisons'].setdefault((case,algorithm,metric,graph),[]).append(ratio)
        actual={tuple(r[k] for k in audit.table_keys('paired_ratios')):r['kkt_over_competitor'] for r in tables['paired_ratios']}
        self.assertEqual(len(actual),3600);self.assertEqual(actual,expected)
        for name,group in groups.items():
            actual={tuple(r[k] for k in audit.table_keys(name)):r for r in tables[name]}
            self.assertEqual(len(actual),len(tables[name]));self.assertEqual(set(actual),set(group))
            for key,values in group.items():
                value_field='median_ns' if name.endswith('summary') else 'median_paired_ratio'
                self.assertEqual(actual[key][value_field],median(values));self.assertEqual(actual[key]['trials'],len(values))
                self.assertEqual((actual[key]['trial_min'],actual[key]['trial_max']),(min(values),max(values)))
        self.assertEqual(sum(len(tables[name]) for name in groups),1980)

    def test_all_490_intervals_density_isolation_and_exact_sustained_thresholds(self):
        specs,rows=fixture();base=audit.numerical_tables(rows,specs)
        loss,strong=Fraction(11,10),Fraction(9,10)
        expected_points={(family,density,competitor,n) for density,sizes in LADDERS for family in FAMILIES
                         for competitor in ALGORITHMS[1:] for n in sizes}
        expected_brackets={(family,density,competitor,lo,hi) for density,sizes in LADDERS for family in FAMILIES
                           for competitor in ALGORITHMS[1:] for lo in sizes for hi in sizes if lo<hi}
        expected_groups={(family,density,competitor) for density,_ in LADDERS for family in FAMILIES
                         for competitor in ALGORITHMS[1:]}
        for density,sizes in LADDERS:
          target=lambda r:(r['family'],r['density'],r['competitor'])==('leaf_distance4',density,'multigraph_boruvka')
          count=len(sizes)
          untouched=[r for r in base['crossover_summary'] if r['density']!=density]
          scenarios=(('strong',[loss]+[strong]*(count-1),(True,sizes[0],sizes[1])),
                ('late',[loss]*(count-1)+[strong],(True,sizes[-2],sizes[-1])),
                ('reversal',[loss]+[strong]*(count-2)+[loss],(False,None,None)),
                ('recovered',[loss,strong,loss]+[strong]*(count-3),(True,sizes[2],sizes[3])),
                ('tie',[Fraction(1)]+[strong]*(count-1),(False,None,None)),
                ('all_lead',[strong]*count,(False,None,None)),
                ('last_epsilon',[loss]+[strong]*(count-1),(False,None,None)),
                ('one_graph',[loss]+[strong]*(count-1),(False,None,None)))
          for kind,values,expected in scenarios:
            tables=copy.deepcopy(base)
            for row in tables['graph_comparisons']:
                if not target(row):continue
                value=values[sizes.index(row['n'])]
                if kind=='last_epsilon' and row['n']==sizes[-1] and row['metric']=='cpu':value+=Fraction(1,10**18)
                if kind=='one_graph' and row['n']==sizes[-1] and row['graph_seed']==23000029:value=Fraction(91,100)
                row['median_paired_ratio']=value
            got=audit.crossovers(tables,specs)
            self.assertEqual((len(got['crossover_points']),len(got['crossover_brackets']),len(got['crossover_summary'])),(150,490,20))
            self.assertEqual({(r['family'],r['density'],r['competitor'],r['n']) for r in got['crossover_points']},expected_points)
            self.assertEqual({(r['family'],r['density'],r['competitor'],r['lower_n'],r['upper_n'])
                              for r in got['crossover_brackets']},expected_brackets)
            self.assertEqual({(r['family'],r['density'],r['competitor']) for r in got['crossover_summary']},expected_groups)
            self.assertEqual([r for r in got['crossover_summary'] if r['density']!=density],untouched)
            row=next(r for r in got['crossover_summary'] if target(r))
            self.assertEqual((row['strong_crossover'],row['primary_lower_n'],row['primary_upper_n']),expected,(density,kind))
            for row in got['crossover_brackets']:
                if target(row):
                    lower,upper=sizes.index(row['lower_n']),sizes.index(row['upper_n'])
                    passing=all(v<=Fraction(9,10) for v in values[upper:]) and values[lower]>1
                    if kind in ('last_epsilon','one_graph'):passing=False
                    self.assertEqual(row['strong_crossover'],passing,(density,kind,lower,upper))
        changed=copy.deepcopy(base);changed['graph_comparisons'][0]['density']=8
        with self.assertRaisesRegex(ValueError,'identity/density'):audit.crossovers(changed,specs)

    def test_complete_raw_schema_schedule_certificates_resources_and_concat(self):
        with raw_fixture() as (root,path,info,rows):
            result=audit.raw_capture(path,info['freeze'],info['freeze_sha256'])
            self.assertEqual((len(result[2]),len(result[3]),len(result[4])),(2520,60,30))
            self.assertEqual(result[2],rows)
            original=copy.deepcopy(info);raw=Path(info['captures'][0]['csv']);raw_bytes=raw.read_bytes()
            log=Path(info['captures'][0]['log']);log_bytes=log.read_bytes();output=Path(info['output']);output_bytes=output.read_bytes()
            rss=Path(info['captures'][0]['rss_log']);rss_bytes=rss.read_bytes()
            for kind in ('missing row','duplicate row','negative clock','false certificate','float certificate',
                         'extra certificate version','nonempty group','bad schedule','wrong density','combined mismatch'):
                raw.write_bytes(raw_bytes);log.write_bytes(log_bytes);output.write_bytes(output_bytes);rss.write_bytes(rss_bytes)
                changed=copy.deepcopy(original);child=changed['captures'][0]
                if kind in ('missing row','duplicate row','negative clock','wrong density'):
                    native=audit.read_csv(raw);combined=audit.read_csv(output)
                    if kind=='missing row':native.pop();combined.pop(41)
                    elif kind=='duplicate row':native[0]=dict(native[1]);combined[0]=dict(combined[1])
                    elif kind=='negative clock':native[0]['process_cpu_start_ns']='-1';combined[0]['process_cpu_start_ns']='-1'
                    else:native[0]['density']='8';combined[0]['density']='8'
                    write_rows(raw,native);write_rows(output,combined)
                    child['output_sha256']=audit.digest(raw);changed['output_sha256']=audit.digest(output)
                elif kind=='false certificate':
                    child['certificate']['validation']='failed';log.write_text('reference_certificate_v1 '+json.dumps(child['certificate'])+'\n');child['log_sha256']=audit.digest(log)
                elif kind=='float certificate':
                    child['certificate']['n']=float(child['certificate']['n'])
                    log.write_text('reference_certificate_v1 '+json.dumps(child['certificate'])+'\n');child['log_sha256']=audit.digest(log)
                elif kind=='extra certificate version':
                    log.write_text(log.read_text()+'reference_certificate_v2 {}\n');child['log_sha256']=audit.digest(log)
                elif kind=='nonempty group':
                    values=[json.loads(line) for line in rss.read_text().splitlines()];values[-1]['members']=[{'pid':child['process_group'],'rss_kib':1024}];values[-1]['rss_kib']=1024
                    rss.write_text(''.join(json.dumps(r)+'\n' for r in values));child['rss_sha256']=audit.digest(rss)
                    child['group_exit_verification']=values[-1];child['rss_nonempty_observations']=2
                elif kind=='bad schedule':changed['captures'][0],changed['captures'][1]=changed['captures'][1],changed['captures'][0]
                else:
                    values=audit.read_csv(output);values[0]['elapsed_ns']='1';write_rows(output,values);changed['output_sha256']=audit.digest(output)
                write_json(path,changed);audit.INPUTS.clear()
                with self.subTest(kind=kind),self.assertRaises(ValueError):audit.raw_capture(path,info['freeze'],info['freeze_sha256'])

    def test_recursive_declared_artifact_hash_proof_and_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);files={name:root/name for name in ('source','recipe','helper','manifest','protocol','binary','object','main','log')}
            for name,path in files.items():path.write_text(name)
            record={'build_exit_status':0,'source_sha256':{'source':audit.digest(files['source'])},
                    'build_log':str(files['log']),'build_log_sha256':audit.digest(files['log']),
                    'object_paths':{'object':str(files['object'])},'object_sha256':{'object':audit.digest(files['object'])},
                    'main_object':str(files['main']),'main_object_sha256':audit.digest(files['main'])}
            receipt=root/'build.json';write_json(receipt,record)
            frozen={'working_directory':str(root),'source_sha256':record['source_sha256'],'build_recipe_sha256':{'recipe':audit.digest(files['recipe'])},
                    'python_source_sha256':{str(files['helper']):audit.digest(files['helper'])},'manifest':str(files['manifest']),
                    'manifest_sha256':audit.digest(files['manifest']),'protocol':str(files['protocol']),'protocol_sha256':audit.digest(files['protocol']),
                    'binary':str(files['binary']),'binary_sha256':audit.digest(files['binary']),
                    'build':{'path':str(receipt),'sha256':audit.digest(receipt),'record':record}}
            parent=root/'parent.json';write_json(parent,frozen);child=root/'child.json'
            write_json(child,{**frozen,'parent_freeze':str(parent),'parent_freeze_sha256':audit.digest(parent)})
            audit.hash_freeze(child)
            for path in (*files.values(),receipt,parent):
                before=path.read_bytes();path.write_bytes(before+b'drift');audit.INPUTS.clear()
                with self.subTest(path=path),self.assertRaises(ValueError):audit.hash_freeze(child)
                path.write_bytes(before)

    def test_future_freeze_is_supplied_and_declarations_are_bound(self):
        # Source hashes are predeclared; no future lower-density freeze digest is
        # invented in the audit. Its real path/hash must arrive after freeze.
        self.assertFalse(hasattr(audit,'FREEZE_SHA256'))
        self.assertEqual(tuple(audit.LADDERS),LADDERS)
        self.assertEqual(tuple(audit.GRAPHS),GRAPHS)
        self.assertEqual(tuple(audit.SAMPLERS),(3407,))
        self.assertEqual(audit.DECLARED_CASES,tuple((f,n,density,0) for density,sizes in LADDERS for n in sizes for f in FAMILIES))
        for name,value in audit.DECLARATION_SHA256.items():
            self.assertEqual(audit.digest(audit.ROOT.parents[2]/name),value)
        with raw_fixture() as (root,path,info,rows):
            for value in ('0'*64,'not-a-hash',True):
                audit.INPUTS.clear()
                with self.subTest(digest=value),self.assertRaises(ValueError):
                    audit.raw_capture(path,info['freeze'],value)
            other=root/'other-freeze.json';other.write_bytes(Path(info['freeze']).read_bytes())
            audit.INPUTS.clear()
            with self.assertRaisesRegex(ValueError,'wrong supplied'):
                audit.raw_capture(path,other,info['freeze_sha256'])
            freeze=info['frozen_protocol']
            # Source-preparation placeholders must never become wildcard pins.
            unpinned=dict(audit.DECLARATION_SHA256)
            unpinned[next(iter(unpinned))]=None
            with mock.patch.object(audit,'DECLARATION_SHA256',unpinned),\
                    self.assertRaisesRegex(ValueError,'Unpinned'):
                audit.declared_sources(freeze)
            for name in audit.DECLARATION_SHA256:
                source=root/name;original=source.read_bytes();source.write_bytes(original+b'changed')
                audit.INPUTS.clear()
                with self.subTest(source=name),self.assertRaises(ValueError):audit.declared_sources(freeze)
                source.write_bytes(original)
            changed=copy.deepcopy(freeze);changed['python_source_sha256']={};audit.INPUTS.clear()
            with self.assertRaisesRegex(ValueError,'collector missing'):audit.declared_sources(changed)
            changed=copy.deepcopy(freeze);changed['protocol_sha256']='0'*64;audit.INPUTS.clear()
            with self.assertRaisesRegex(ValueError,'declaration path/hash'):audit.declared_sources(changed)

    def test_table_identity_values_none_and_native_domains(self):
        specs,rows=fixture();tables=audit.numerical_tables(rows,specs)
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)
            for name,values in tables.items():
                plain=[{k:float(v) if isinstance(v,Fraction) else v for k,v in r.items()} for r in values]
                audit.write_csv(directory,name,plain);audit.verify_table(directory/(name+'.csv'),values,audit.table_keys(name))
            path=directory/'paired_ratios.csv';values=audit.read_csv(path);values[-1]=dict(values[0]);write_rows(path,values,tuple(values[0]))
            audit.INPUTS.clear()
            with self.assertRaisesRegex(ValueError,'duplicate/foreign'):audit.verify_table(path,tables['paired_ratios'],audit.table_keys('paired_ratios'))
            # Preserve every identity and table count: these must fail the
            # value checks, not duplicate detection or a stale input hash.
            for name,field,message in (
                    ('paired_ratios','kkt_over_competitor','exact-rational numerical mismatch'),
                    ('comparisons','median_paired_ratio','exact-rational numerical mismatch'),
                    ('paired_ratios','kkt_ns','exact table field mismatch')):
                values=[{k:float(v) if isinstance(v,Fraction) else v for k,v in r.items()} for r in tables[name]]
                values[0][field]+=1
                path=directory/(name+'.csv');write_rows(path,values,tuple(values[0]));audit.INPUTS.clear()
                with self.subTest(table=name,field=field),self.assertRaisesRegex(ValueError,message):
                    audit.verify_table(path,tables[name],audit.table_keys(name))
        for mode in ('missing','duplicate','sampler'):
            changed=copy.deepcopy(rows);index=next(i for i,r in enumerate(changed) if r['phase']=='timed')
            if mode=='missing':changed.pop(index)
            elif mode=='duplicate':changed.append(copy.deepcopy(changed[index]))
            else:changed[index]['kkt_seed']=2005
            with self.subTest(mode=mode),self.assertRaises(ValueError):audit.numerical_tables(changed,specs)
        for text in ('-1','+1',' 1','1.0','١','',str(2**63)):
            with self.assertRaises(ValueError):audit.native_integer(text,'process_cpu_start_ns')
        for text in ('2026-10-15T00:00:00','2026-10-15T00:00:00+01:00'):
            with self.assertRaises(ValueError):audit.parse_utc(text)
        for text in ('{"a":1,"a":2}','{"a":NaN}'):
            with self.assertRaises(ValueError):audit.parse_json(text)


if __name__=='__main__':unittest.main(verbosity=2)
