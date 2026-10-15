#!/usr/bin/env python3
"""Synthetic independent eighth-audit gates; no native or collector imports.

Prepared source only. Execute after root releases post-capture validation.
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

PATH = Path(__file__).with_name('independent_numerical_audit.py')
SPEC = importlib.util.spec_from_file_location('independent_eighth_audit', PATH)
audit = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(audit)
ALGORITHMS = ('kkt','compacting_boruvka','multigraph_boruvka','kruskal','prim','boruvka')
VARIANTS = ('half','eighth')
GRAPHS, SAMPLERS = (15000011,15000031),(2609,2617)
CASES = (('leaf_hierarchy4',65536,32),('leaf_shuffled4',65536,32),
         ('leaf_hierarchy4',1048576,32),('leaf_shuffled4',1048576,32),
         ('gnm_random',4096,16),('gnm_random',1048576,16))


def fixture():
    specs = {}
    for family,n,density in CASES:
        case = f'{family}_n{n}_d{density}_p0'
        specs[case] = dict(case_id=case,family=family,n=n,m=n*density,density=density,intrusion_per_mille=0)
    schedule = [dict(variant=variant,case_id=case,graph_seed=graph,kkt_seed=sampler)
        for gi,graph in enumerate(GRAPHS) for si,sampler in enumerate(SAMPLERS)
        for case in (list(specs) if gi == 0 else list(reversed(specs)))
        for variant in (VARIANTS if (gi+si)%2 == 0 else tuple(reversed(VARIANTS)))]
    rows = []
    for child,identity in enumerate(schedule):
        variant,case,graph,sampler = (identity[k] for k in ('variant','case_id','graph_seed','kkt_seed'))
        vi,ci,gi,si = VARIANTS.index(variant),list(specs).index(case),GRAPHS.index(graph),SAMPLERS.index(sampler)
        cpu = 0; utc = 946684800_000000000+child*2_000000000
        for phase,count in (('warmup',1),('timed',6)):
            for rep in range(count):
                for order in range(6):
                    ai = (rep+order)%6
                    # Every identity dimension and both clocks vary independently.
                    wall = 100003+1009*ci+701*gi+503*si+307*vi+103*rep+41*ai+7*rep*ai+29*vi*ai
                    duration = 70001+701*ci+503*gi+307*si+211*vi+79*rep+23*ai+3*rep*ai+17*vi*ai
                    rows.append(dict(variant=variant,**specs[case],graph_seed=graph,kkt_seed=sampler,
                        input_fingerprint=1000+ci+gi*200,topology_fingerprint=100+ci//2+gi*100,
                        phase=phase,repetition=rep,order=order,warmups=1,algorithm=ALGORITHMS[ai],
                        elapsed_ns=wall,utc_start_ns=utc,utc_end_ns=utc+wall,process_cpu_start_ns=cpu,
                        process_cpu_end_ns=cpu+duration,process_cpu_elapsed_ns=duration,validation='pass'))
                    cpu += duration+10; utc += wall+10
    return specs,schedule,rows


def median(values):
    values = sorted(values); middle = len(values)//2
    return (Fraction(values[middle-1])+Fraction(values[middle]))/2


def write_json(path,value): path.write_text(json.dumps(value,indent=2)+'\n')


def write_rows(path,rows,fields=None):
    with path.open('w',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=fields or tuple(rows[0]));writer.writeheader();writer.writerows(rows)


@contextlib.contextmanager
def raw_fixture():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary).resolve(); (root/'benchmark').mkdir()
        source = root/'benchmark/retention_control.cpp'; source.write_text('synthetic source')
        specs,schedule,rows = fixture(); manifest = root/'manifest.csv'
        write_rows(manifest,[{k:r[k] for k in ('family','n','density','intrusion_per_mille')} for r in specs.values()])
        shared = {f'shared_{i}.o':str(root/f'{i}.o') for i in range(7)}
        hashes = {name:'shared-'+name for name in shared}
        commands = [['synthetic',str(i)] for i in range(12)]
        commands[6] = ['synthetic','-DKKT_EXPERIMENT_COMPRESSED_QUERIES','-c','verifier/verifier_v2.cpp']
        commands[8] = ['synthetic','-DKKT_EXPERIMENT_EIGHTH_SAMPLING','-c','kkt/kkt.cpp']
        artifacts = {}
        for variant,mask in (('half',1),('eighth',7)):
            policy = dict(sampling_policy=variant,private_acceptance_mask=mask,sampling_words_per_visited_edge=1,verifier_policy='compressed')
            record = dict(schema='eighth_sampling_build_v1',profile='timing-build',variant=variant,role='timing_never_executed',
                compressed_queries_fixed=True,public_scalar_sampling_fixed=True,seven_non_kkt_objects_identical_by_construction=True,
                source_sha256={'benchmark/retention_control.cpp':audit.digest(source)},build_recipe_sha256={},
                compiler='synthetic',compiler_command=['synthetic'],sdk='/synthetic/sdk',build_commands=commands,
                main_object=str(root/'main.o'),main_object_sha256='main',
                object_paths={**shared,'kkt/kkt.o':str(root/(variant+'.o'))},object_sha256={**hashes,'kkt/kkt.o':variant},
                binary_profile={'file_description':'Mach-O 64-bit executable arm64','main_stack_bytes':536870912},
                executables=[policy],**policy)
            artifacts[variant] = {'binary':str(root/(variant+'-never-executed')),'build':{'record':record}}
        frozen = dict(schema='eighth_sampling_freeze_v1',working_directory=str(root),variants=artifacts,
            source_sha256={'benchmark/retention_control.cpp':audit.digest(source)},manifest=str(manifest),
            parent_freeze_sha256=audit.PARENT_SHA256,algorithms=list(ALGORITHMS),graph_seeds=list(GRAPHS),
            sampling_seeds=list(SAMPLERS),repetitions=6,warmups=1,schedule=schedule,
            resource_rule={'rss_limit_kib':40*1024*1024,'poll_seconds':2})
        freeze = root/'freeze.json';write_json(freeze,frozen)
        output = root/'paired.csv';folder = root/'paired_cases';folder.mkdir()
        write_rows(output,rows,('variant',*audit.FIELDS))
        utc = lambda seconds:(datetime.datetime(2000,1,1,tzinfo=datetime.timezone.utc)+datetime.timedelta(seconds=seconds)).isoformat()
        info = dict(schema='eighth_sampling_capture_v1',validation='pass',rows_removed=0,rows_adjusted=0,cleanup=[],
            native_process_may_still_be_running=False,freeze=str(freeze),freeze_sha256=audit.digest(freeze),frozen_protocol=frozen,
            output=str(output),output_sha256=audit.digest(output),captures=[],started_monotonic_ns=0,
            finished_monotonic_ns=96_000000000,monotonic_elapsed_seconds=96.0,started_utc=utc(0),finished_utc=utc(96),
            checked_rows=2016,checked_timed_rows=1728,checked_warmup_rows=288,flagged_calls=0,capture_clock_flags=[],call_diagnostics=[])
        for index,identity in enumerate(schedule,1):
            selected = rows[(index-1)*42:index*42]; spec = specs[identity['case_id']]
            raw = folder/f"{index:04d}_{identity['variant']}_{identity['case_id']}_g{identity['graph_seed']}_s{identity['kkt_seed']}.csv"
            write_rows(raw,[{k:r[k] for k in audit.FIELDS} for r in selected],audit.FIELDS)
            certificate = {name:selected[0][name] for name in audit.CERTIFICATE};log = raw.with_suffix('.log')
            log.write_text('reference_certificate_v1 '+json.dumps(certificate)+'\n')
            start = (index-1)*2_000000000;end = start+1_000000000;group = 10000+index
            requests = (start+100,end-500)
            observations = [dict(utc=utc(2*(index-1)),monotonic_ns=request,process_group=group,validation='pass',
                members=[{'pid':group,'rss_kib':1024}] if i == 0 else [],rss_kib=1024 if i == 0 else 0)
                for i,request in enumerate(requests)]
            events = [dict(process_group=group,requested_monotonic_ns=request,returned_monotonic_ns=request+10,
                provider_started_monotonic_ns=request+1,provider_finished_monotonic_ns=request+9,
                previous_request_gap_ns=None if i == 0 else request-requests[i-1],sampler_duration_ns=10,outcome='pass')
                for i,request in enumerate(requests)]
            rss = raw.with_suffix('.rss.jsonl');rss.write_text(''.join(json.dumps(r)+'\n' for r in observations))
            argv = [artifacts[identity['variant']]['binary'],'--family',spec['family'],'--n',str(spec['n']),
                '--density',str(spec['density']),'--graph-seed',str(identity['graph_seed']),
                '--kkt-seed',str(identity['kkt_seed']),'--repetitions','6','--warmups','1']
            info['captures'].append({**identity,'exit_status':0,'validation':'pass','interruption':None,'rows':42,
                'started_monotonic_ns':start,'finished_monotonic_ns':end,'monotonic_elapsed_seconds':1.0,
                'started_utc':utc(2*(index-1)),'finished_utc':utc(2*(index-1)+1),'csv':str(raw),'output_sha256':audit.digest(raw),
                'log':str(log),'log_sha256':audit.digest(log),'rss_log':str(rss),'rss_sha256':audit.digest(rss),
                'command':argv,'launch_command':['/usr/bin/time','-l',*argv],'process_group':group,'certificate':certificate,'flagged_calls':0,
                'rss_observations':2,'rss_unavailable':0,'rss_nonempty_observations':1,'sampled_peak_rss_kib':1024,
                'recovery_monitor':{'observations':events,'max_sampler_duration_ns':10,'max_request_gap_ns':requests[1]-requests[0]},
                'wrapper_exit_monotonic_ns':end-1000,'group_exit_verification':observations[-1]})
            for row in selected:
                wall,cpu = row['elapsed_ns'],row['process_cpu_elapsed_ns']
                info['call_diagnostics'].append({**identity,**{name:row[name] for name in ('phase','repetition','order','algorithm')},
                    'elapsed_ns':wall,'process_cpu_elapsed_ns':cpu,'utc_elapsed_ns':wall,'steady_minus_cpu_ns':wall-cpu,
                    'utc_minus_steady_ns':0,'diagnostic_flags':[],'excluded':False})
        path = output.with_suffix('.json');write_json(path,info)
        with mock.patch.object(audit,'hash_freeze',return_value=frozen),mock.patch.object(audit,'FREEZE_SHA256',audit.digest(freeze)):
            yield root,path,info,rows


class IndependentAuditTests(unittest.TestCase):
    def setUp(self):audit.INPUTS.clear()

    def test_all4608_pairs_and3024_summary_rows_from_raw_cartesian_identities(self):
        specs,schedule,rows = fixture();self.assertEqual((len(schedule),len(rows)),(48,2016))
        tables,points,brackets = audit.numerical_tables(rows,specs)
        self.assertEqual({k:len(v) for k,v in tables.items()},audit.TABLE_COUNTS)
        raw = {(r['variant'],r['case_id'],r['graph_seed'],r['kkt_seed'],r['repetition'],r['algorithm']):r
               for r in rows if r['phase'] == 'timed'}
        expected_within,expected_across = {},{};groups = {}
        def add(name,key,value):groups.setdefault(name,{}).setdefault(key,[]).append(value)
        def summaries(prefix,key,graph,sampler,value):
            add(prefix,key,value);add('realization_'+prefix,(*key,graph,sampler),value)
            add('graph_'+prefix,(*key,graph),value);add('sampling_'+prefix,(*key,sampler),value)
        for case in specs:
            for graph in GRAPHS:
                for sampler in SAMPLERS:
                    for rep in range(6):
                        for metric,field in (('wall','elapsed_ns'),('cpu','process_cpu_elapsed_ns')):
                            for algorithm in ALGORITHMS:
                                half,eighth = (raw[v,case,graph,sampler,rep,algorithm][field] for v in VARIANTS)
                                ratio = Fraction(eighth,half);key = (case,algorithm,metric,graph,sampler,rep)
                                expected_across[key] = ratio
                                summaries('variant_comparisons',(case,algorithm,metric),graph,sampler,ratio)
                                for variant in VARIANTS:
                                    value = raw[variant,case,graph,sampler,rep,algorithm][field]
                                    summaries('summary',(variant,case,algorithm,metric),graph,sampler,Fraction(value))
                                    if algorithm == 'kkt':continue
                                    ratio = Fraction(raw[variant,case,graph,sampler,rep,'kkt'][field],value)
                                    expected_within[variant,case,algorithm,metric,graph,sampler,rep] = ratio
                                    summaries('comparisons',(variant,case,algorithm,metric),graph,sampler,ratio)
        for name,expected,field in (('paired_ratios',expected_within,'kkt_over_competitor'),
                                    ('variant_pairs',expected_across,'eighth_over_half')):
            actual = {tuple(r[k] for k in audit.table_keys(name)):r[field] for r in tables[name]}
            self.assertEqual(len(actual),len(tables[name]));self.assertEqual(actual,expected)
        self.assertEqual((len(expected_within),len(expected_across)),(2880,1728))
        self.assertEqual(sum(map(len,groups.values())),3024)
        for name,group in groups.items():
            actual = {tuple(r[k] for k in audit.table_keys(name)):r for r in tables[name]}
            self.assertEqual(len(actual),len(tables[name]));self.assertEqual(set(actual),set(group))
            field = 'median_ns' if name.endswith('summary') else 'median_paired_ratio'
            for key,values in group.items():
                self.assertEqual(actual[key][field],median(values));self.assertEqual(actual[key]['trials'],len(values))
                self.assertEqual((actual[key]['trial_min'],actual[key]['trial_max']),(min(values),max(values)))
                if field == 'median_paired_ratio':self.assertEqual(actual[key]['individual_wins'],sum(x<1 for x in values))
                if name in ('comparisons','variant_comparisons','summary'):
                    for prefix,seeds in (('graph',GRAPHS),('sampling',SAMPLERS)):
                        marginal=[median(groups[prefix+'_'+name][(*key,seed)]) for seed in seeds]
                        self.assertEqual((actual[key][prefix+'_min'],actual[key][prefix+'_max']),(min(marginal),max(marginal)))
                    realizations=[median(groups['realization_'+name][(*key,g,s)]) for g in GRAPHS for s in SAMPLERS]
                    self.assertEqual((actual[key]['realization_min'],actual[key]['realization_max']),
                                     (min(realizations),max(realizations)))
        self.assertEqual((len(points),len(brackets)),(60,30))

    def test_exact_thresholds_all_eight_realization_clocks_and_reversal(self):
        specs,_,rows = fixture();original,_,_ = audit.numerical_tables(rows,specs)
        for kind,low,high,expected in (('boundary',Fraction(11,10),Fraction(9,10),True),
            ('epsilon',Fraction(11,10),Fraction(9,10)+Fraction(1,10**30),False),
            ('small_tie',Fraction(1),Fraction(4,5),False),('already',Fraction(4,5),Fraction(4,5),False),
            ('reversal',Fraction(4,5),Fraction(11,10),False),('one_clock',Fraction(11,10),Fraction(4,5),False)):
            tables = copy.deepcopy(original)
            for row in tables['realization_comparisons']:
                if row['variant']=='eighth' and row['family']=='leaf_hierarchy4' and row['competitor']=='multigraph_boruvka':
                    row['median_paired_ratio'] = low if row['n']==65536 else high
                    if kind=='one_clock' and row['n']==1048576 and row['metric']=='cpu' and row['graph_seed']==GRAPHS[1] and row['kkt_seed']==SAMPLERS[1]:
                        row['median_paired_ratio']=Fraction(1)
            got,points,brackets = audit.crossovers(tables,specs)
            selected = next(r for r in got if r['variant']=='eighth' and r['family']=='leaf_hierarchy4' and r['competitor']=='multigraph_boruvka')
            self.assertEqual(selected['strong_crossover'],expected,kind)
            self.assertEqual((len(got),len(points),len(brackets)),(30,60,30))

    def test_full48_raw_rows_certificates_resources_schedule_and_concat(self):
        with raw_fixture() as (root,path,info,rows):
            result = audit.raw_capture(path);self.assertEqual(result[2],rows)
            self.assertEqual((len(result[2]),len(result[3]),len(result[4])),(2016,48,4))
            original=copy.deepcopy(info);raw=Path(info['captures'][0]['csv']);raw_bytes=raw.read_bytes()
            log=Path(info['captures'][0]['log']);log_bytes=log.read_bytes();output=Path(info['output']);output_bytes=output.read_bytes()
            rss=Path(info['captures'][0]['rss_log']);rss_bytes=rss.read_bytes()
            for kind in ('missing','duplicate','negative','certificate','group','schedule','combined'):
                raw.write_bytes(raw_bytes);log.write_bytes(log_bytes);output.write_bytes(output_bytes);rss.write_bytes(rss_bytes)
                changed=copy.deepcopy(original);child=changed['captures'][0]
                if kind in ('missing','duplicate','negative'):
                    native=audit.read_csv(raw);combined=audit.read_csv(output)
                    if kind=='missing':native.pop();combined.pop(41)
                    elif kind=='duplicate':native[0]=dict(native[1]);combined[0]=dict(combined[1])
                    else:native[0]['process_cpu_start_ns']='-1';combined[0]['process_cpu_start_ns']='-1'
                    write_rows(raw,native);write_rows(output,combined)
                    child['output_sha256']=audit.digest(raw);changed['output_sha256']=audit.digest(output)
                elif kind=='certificate':
                    child['certificate']['validation']='failed';log.write_text('reference_certificate_v1 '+json.dumps(child['certificate'])+'\n');child['log_sha256']=audit.digest(log)
                elif kind=='group':
                    values=[json.loads(line) for line in rss.read_text().splitlines()];values[-1]['members']=[{'pid':child['process_group'],'rss_kib':1024}];values[-1]['rss_kib']=1024
                    rss.write_text(''.join(json.dumps(r)+'\n' for r in values));child['rss_sha256']=audit.digest(rss)
                    child['group_exit_verification']=values[-1];child['rss_nonempty_observations']=2
                elif kind=='schedule':changed['captures'][0],changed['captures'][1]=changed['captures'][1],changed['captures'][0]
                else:
                    values=audit.read_csv(output);values[0]['elapsed_ns']='1';write_rows(output,values);changed['output_sha256']=audit.digest(output)
                write_json(path,changed);audit.INPUTS.clear()
                with self.subTest(kind=kind),self.assertRaises(ValueError):audit.raw_capture(path)

    def test_typed_policy_macro_shared_object_and_manifest_identity(self):
        with raw_fixture() as (root,path,info,rows):
            frozen=copy.deepcopy(info['frozen_protocol'])
            for mode in ('mask_bool','public','verifier','macro','shared','manifest_order','freeze'):
                changed=copy.deepcopy(frozen)
                record=changed['variants']['eighth']['build']['record']
                if mode=='mask_bool':record['private_acceptance_mask']=True
                elif mode=='public':record['public_scalar_sampling_fixed']=False
                elif mode=='verifier':record['executables'][0]['verifier_policy']='reference'
                elif mode=='macro':
                    for variant in VARIANTS:changed['variants'][variant]['build']['record']['build_commands'][6].append('-DKKT_EXPERIMENT_EIGHTH_SAMPLING')
                elif mode=='shared':record['object_sha256']['shared_0.o']='other'
                elif mode=='manifest_order':
                    values=audit.read_csv(Path(frozen['manifest']));values.reverse();write_rows(Path(frozen['manifest']),values)
                changed_info=copy.deepcopy(info);changed_info['frozen_protocol']=changed
                if mode=='freeze':changed_info['freeze_sha256']='0'*64
                write_json(path,changed_info);audit.INPUTS.clear()
                with mock.patch.object(audit,'hash_freeze',return_value=changed),self.subTest(mode=mode),self.assertRaises(ValueError):
                    audit.raw_capture(path)
                if mode=='manifest_order':
                    specs,_,_=fixture();write_rows(Path(frozen['manifest']),[{k:r[k] for k in ('family','n','density','intrusion_per_mille')} for r in specs.values()])

    def test_recursive_declared_artifact_hash_proof_and_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();files={name:root/name for name in ('source','recipe','helper','manifest','protocol','binary','object','main','log')}
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

    def test_table_numeric_mutations_identity_sets_and_native_domains(self):
        specs,_,rows=fixture();tables,_,_=audit.numerical_tables(rows,specs)
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)
            for name,values in tables.items():
                plain=[{k:float(v) if isinstance(v,Fraction) else v for k,v in r.items()} for r in values]
                audit.write_csv(directory,name,plain);audit.verify_table(directory/(name+'.csv'),values,audit.table_keys(name))
            for name,field,message in (('paired_ratios','kkt_over_competitor','exact-rational numerical mismatch'),
                ('variant_pairs','eighth_over_half','exact-rational numerical mismatch'),
                ('comparisons','median_paired_ratio','exact-rational numerical mismatch'),
                ('paired_ratios','kkt_ns','exact table field mismatch')):
                values=[{k:float(v) if isinstance(v,Fraction) else v for k,v in r.items()} for r in tables[name]]
                values[0][field]+=1;path=directory/(name+'.csv');write_rows(path,values);audit.INPUTS.clear()
                with self.subTest(table=name,field=field),self.assertRaisesRegex(ValueError,message):
                    audit.verify_table(path,tables[name],audit.table_keys(name))
            for mode in ('duplicate','missing','clock'):
                values=[{k:float(v) if isinstance(v,Fraction) else v for k,v in r.items()} for r in tables['variant_pairs']]
                if mode=='duplicate':values[-1]=dict(values[0])
                elif mode=='missing':values.pop()
                else:
                    source=next(r for r in values if r['case_id']==values[0]['case_id'] and r['algorithm']==values[0]['algorithm'] and
                        r['graph_seed']==values[0]['graph_seed'] and r['kkt_seed']==values[0]['kkt_seed'] and r['repetition']==values[0]['repetition'] and r['metric']!=values[0]['metric'])
                    values[0]['eighth_over_half']=source['eighth_over_half']
                path=directory/'variant_pairs.csv';write_rows(path,values);audit.INPUTS.clear()
                with self.subTest(mode=mode),self.assertRaises(ValueError):audit.verify_table(path,tables['variant_pairs'],audit.table_keys('variant_pairs'))
        for mode in ('missing','duplicate','sampler'):
            changed=copy.deepcopy(rows);index=next(i for i,r in enumerate(changed) if r['phase']=='timed')
            if mode=='missing':changed.pop(index)
            elif mode=='duplicate':changed.append(copy.deepcopy(changed[index]))
            else:changed[index]['kkt_seed']=999
            with self.subTest(mode=mode),self.assertRaises(ValueError):audit.numerical_tables(changed,specs)
        for value in ('-1','1.0','NaN',' 1','١',str(2**64)):
            with self.subTest(value=value),self.assertRaises(ValueError):audit.native_integer(value,'input_fingerprint')
        for text in ('{"x":1,"x":2}','{"x":NaN}'):
            with self.subTest(text=text),self.assertRaises(ValueError):audit.parse_json(text)


if __name__ == '__main__':unittest.main(verbosity=2)
