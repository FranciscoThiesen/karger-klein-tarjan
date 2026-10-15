#!/usr/bin/env python3
"""Read-only failure/owned-group audit of the preserved first diagnostic attempt."""
import importlib.util
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('heldout_work_failure_audit',HERE/'collect.py')
work = importlib.util.module_from_spec(spec); spec.loader.exec_module(work)
capture = HERE/'capture-attempt01.json'; controller = HERE/'capture-controller-attempt01.json'
failed = work.analysis.read_json(capture); outer = work.analysis.read_json(controller)
frozen = work.check_freeze(Path(failed['freeze']))
work.require(failed['validation'] == outer['validation'] == 'failed','expected preserved failed attempt')
work.require(len(failed['captures']) == 3 and failed['native_process_may_still_be_running'] is False,
             'unexpected partial matrix or unknown child')
groups = []
for index,item in enumerate(failed['captures']):
    work.require(item['spec'] == frozen['schedule'][index],'partial schedule changed')
    for field,digest in (('raw','raw_sha256'),('log','log_sha256'),('rss_log','rss_sha256')):
        work.analysis.hash_check(Path(item[field]),item[digest])
    if index < 2:
        work.require(item['validation'] == 'pass' and item['exit_status'] == 0,'earlier child failed')
        value = work.check_output(Path(item['raw']),item['spec'])
        work.require(item['certificate'] == work.native.check_certificate(Path(item['log']),[value]),'certificate changed')
        work.resources(item)
        evidence = item['group_exit_verification']
    else:
        work.require(item['exit_status'] == 1 and Path(item['log']).read_text() == 'unsupported diagnostic family\n'
                     and Path(item['raw']).stat().st_size == 0,'unexpected native failure')
        work.require(len(failed['cleanup']) == 1,'unexpected cleanup count')
        cleanup = failed['cleanup'][0]
        work.require(cleanup['process_group'] == item['process_group'] and cleanup['returncode'] == 1
                     and cleanup['native_exit_known'] is True and cleanup['group_exit_known'] is True
                     and cleanup['native_process_may_still_be_running'] is False,'failed child exit not proved')
        evidence = cleanup['group_verification']
    work.require(evidence['validation'] == 'pass' and evidence['members'] == []
                 and evidence['process_group'] == item['process_group'],'child group not empty')
    groups.append(item['process_group'])
cleanup = outer['outer_cleanup']
work.require(outer['exit_status'] == cleanup['returncode'] == 1 and cleanup['native_exit_known'] is True
             and cleanup['group_exit_known'] is True and cleanup['native_process_may_still_be_running'] is False
             and cleanup['group_verification']['validation'] == 'pass'
             and cleanup['group_verification']['members'] == [],'outer group exit not proved')
groups.append(outer['outer_process_group'])
work.require(cleanup['process_group'] == groups[-1] == cleanup['group_verification']['process_group'],
             'outer group identity changed')
result = subprocess.run(['/bin/ps','-axo','pid=,pgid='],capture_output=True,text=True,check=True,timeout=3)
members = [dict(pid=pid,process_group=group) for pid,group in
           (tuple(map(int,line.split())) for line in result.stdout.splitlines() if line.strip()) if group in groups]
work.require(not members,'a launched owned group is still populated')
record = dict(schema='heldout_failed_work_audit_v1',validation='pass',capture_validation='failed',
    completed_children=2,attempted_children=3,reason='Diagnostic frontend rejects grid2d_metric before generation or solver execution.',
    all_launched_owned_groups_verified_empty=True,owned_groups=groups,current_members=members,
    current_observation_utc=work.native.now(),current_observation_monotonic_ns=time.monotonic_ns(),
    process_query_command=['/bin/ps','-axo','pid=,pgid='],process_query_exit_status=result.returncode,
    source_sha256={str(path):work.native.sha(path) for path in (Path(__file__).resolve(),HERE/'collect.py',capture,controller)},
    native_solver_execution=False,failed_capture_relabelled=False,retry_launched=False)
work.write_json(HERE/'failure-audit-attempt01.json',record,exclusive=True)
print(json.dumps(record,indent=2))
