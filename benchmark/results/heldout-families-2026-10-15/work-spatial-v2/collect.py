#!/usr/bin/env python3
"""Fresh full-matrix diagnostics using the narrowly extended spatial frontend."""
import argparse
import contextlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve(); WORK = HERE.parent
PARENT = WORK.parent/'work'
PARENT_FREEZE = PARENT/'freeze.json'
PARENT_SHA = 'db107c2370735e7bdcec777320ea069374c8247d8d02ba67684528541561bcaf'
ENGINE_SHA = '8f6742f286ffcc227908ace7710a5cebfb14a00e1d09a3cacaa3e026e002640a'


def module(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


engine = module('heldout_spatial_inherited_work',PARENT/'collect.py')
native,analysis,require = engine.native,engine.analysis,engine.require
ROOT,monitor,write_json = engine.ROOT,engine.monitor,engine.write_json
ORIGINAL_CHECK_FREEZE = engine.check_freeze
analysis.hash_check(PARENT/'collect.py',ENGINE_SHA)
builder = module('heldout_spatial_frontend_build',WORK/'build_driver.py')


def parent():
    analysis.hash_check(PARENT_FREEZE,PARENT_SHA)
    analysis.hash_check(PARENT/'collect.py',ENGINE_SHA)
    # Call the saved original function, even inside an active adapter scope.
    # Its provenance path does not use the temporarily replaced entry point.
    return ORIGINAL_CHECK_FREEZE(PARENT_FREEZE)


def provenance():
    old = parent(); record = builder.check_record(WORK/'build-record.json')
    require(record['schema'] == 'heldout_spatial_work_build_v1','wrong spatial frontend build schema')
    for key in ('object_paths','object_sha256'):
        require(record[key] == old['artifact'][key],'production objects changed: '+key)
    require(len(record['object_paths']) == 8 and len(record['build_commands']) == 2,
            'only one new main compile and link are allowed')
    artifact = {key:record[key] for key in ('binary','binary_sha256','binary_profile','main_object',
                 'main_object_sha256','object_paths','object_sha256')}
    artifact.update(frontend_build_record=str(WORK/'build-record.json'),
                    frontend_build_record_sha256=native.sha(WORK/'build-record.json'),
                    parent_instrumented_build_record=old['artifact']['instrumented_build_record'],
                    role='untimed_work_spatial_frontend')
    own = {str(path):native.sha(path) for path in
           (HERE,WORK/'test_collect.py',WORK/'PROTOCOL.md',WORK/'build-record.json',PARENT_FREEZE)}
    paths = engine.merge_paths(old['bound_sha256'],record['bound_sha256'],own)
    for path,digest in paths.items(): analysis.hash_check(Path(path),digest)
    return old,artifact,paths


def declaration():
    old,artifact,paths = provenance()
    return dict(schema='heldout_spatial_work_freeze_v1',parent_work_freeze=str(PARENT_FREEZE),
        parent_work_freeze_sha256=PARENT_SHA,timing_capture=old['timing_capture'],artifact=artifact,
        schedule=old['schedule'],bound_sha256=paths,counter_fields=engine.FIELDS,
        algorithms=list(engine.ALGORITHMS),counter_boundary=engine.BOUNDARY,resource_rule=engine.RULE,
        child_deadline_seconds=engine.DEADLINE_SECONDS,expected_children=72,expected_solver_outputs=216,
        expected_replay_chains=144,prior_successes_reused=0,
        capture_schema='heldout_work_capture_v1',analysis_schema='heldout_work_analysis_v1')


def prepare(args):
    value = declaration(); value['created_utc'] = native.now()
    engine.write_json(args.freeze,value,exclusive=True)
    print('Prepared fresh spatial frontend diagnostics: all72 inputs, no prior successes reused')


def check_freeze(path):
    value = analysis.read_json(path)
    for key,expected in declaration().items(): analysis.equal(value,key,expected,'spatial work freeze')
    return value


@contextlib.contextmanager
def configured():
    previous = engine.check_freeze
    try:
        engine.check_freeze = check_freeze
        yield
    finally:
        engine.check_freeze = previous


def capture(args,**kwargs):
    with configured(): return engine.capture(args,**kwargs)


def load(path):
    with configured(): return engine.load(path)


def summarize(args):
    with configured(): return engine.summarize(args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest='action',required=True)
    prepare_parser = actions.add_parser('prepare'); prepare_parser.add_argument('--freeze',type=Path,required=True)
    capture_parser = actions.add_parser('capture'); capture_parser.add_argument('--freeze',type=Path,required=True)
    capture_parser.add_argument('--output',type=Path,required=True); capture_parser.add_argument('--released',action='store_true')
    verify_parser = actions.add_parser('verify'); verify_parser.add_argument('--capture',type=Path,required=True)
    analyze_parser = actions.add_parser('analyze'); analyze_parser.add_argument('--capture',type=Path,required=True)
    analyze_parser.add_argument('--output-dir',type=Path,required=True)
    args = parser.parse_args()
    if args.action == 'prepare': prepare(args)
    elif args.action == 'capture': capture(args)
    elif args.action == 'verify': load(args.capture.resolve(strict=True)); print('Verified72 fresh diagnostic inputs')
    else: summarize(args)
