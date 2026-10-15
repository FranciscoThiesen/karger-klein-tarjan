#!/usr/bin/env python3
"""Released, serial library/new-main and actual-final-binary schema gates.

Every output directory is exclusive. This producer never runs the 24-curve study
and never rebuilds any of the eight frozen production objects.
"""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import sys
import time

import validate_build as gate
import analyze_complexity as analyzer

ROOT, HERE = gate.ROOT, gate.HERE
sys.path.insert(0,str(ROOT/"benchmark"))
import build_compressed_queries as inherited


def save(path,value):
    with path.open("x") as stream:
        json.dump(value,stream,indent=2,allow_nan=False); stream.write("\n")


def hash_field(record,key,path):
    record[key]=str(path); record[key+"_sha256"]=analyzer.digest(path)


def recipes():
    return {str(path):analyzer.digest(path) for path in
            (HERE/"build_library_main.py",HERE/"validate_build.py",HERE/"analyze_complexity.py",HERE/"collect.py",
             HERE/"current_complexity.cpp",ROOT/"benchmark/build_compressed_queries.py")}


def guarded(guard,command,stream,intervals,state,stderr=None,env=None):
    gate.exact(recipes(),state["recipe_sha256"],"source recipe changed before next child")
    stream.write("\n$ "+shlex.join(command)+"\n"); stream.flush()
    interval=dict(command=command,started_monotonic_ns=time.monotonic_ns()); intervals.append(interval)
    state["attempted_commands"].append(command)
    state.setdefault("command_intervals",[]).append(interval)
    try:
        if stderr is None: guard.run(command,stdout=stream,env=env)
        else: guard.run(command,stdout=stream,stderr=stderr,env=env)
    finally:
        interval["finished_monotonic_ns"]=time.monotonic_ns()
    gate.require(interval["finished_monotonic_ns"]-interval["started_monotonic_ns"] <= 300*10**9,
                 "guarded command including cleanup exceeded 300 seconds")


def build(args,state):
    parent_path=args.parent_freeze.resolve(strict=True)
    gate.require(analyzer.digest(parent_path)==gate.PARENT_SHA,"wrong eighth parent freeze")
    parent,_=gate.parent_engine.check_freeze(parent_path)
    frozen=parent["variants"]["eighth"]["build"]["record"]
    source=args.library_source.resolve(); destination=args.build_directory.resolve()
    gate.require(not source.exists() and not destination.exists(),"fresh library source/build directories required")
    gate.require(not source.is_relative_to(ROOT),"library checkout must remain outside frozen native inventory")
    gate.require(source != destination and not source.is_relative_to(destination) and not destination.is_relative_to(source),"separate library source/build roots required")
    source.parent.mkdir(parents=True,exist_ok=True); destination.mkdir(parents=True)
    cmake=shutil.which("cmake"); ctest=shutil.which("ctest")
    gate.require(cmake is not None and ctest is not None,"CMake/CTest unavailable; do not substitute/install implicitly")
    cmake,ctest=(str(Path(value).resolve(strict=True)) for value in (cmake,ctest))
    environment=dict(os.environ)
    state["environment_policy"]=dict(removed={key:environment.pop(key,None) for key in ("CPATH","LIBRARY_PATH")},
        required_empty={key:environment.get(key) for key in gate.EMPTY_ENVIRONMENT},
        retained={key:environment.get(key) for key in ("SDKROOT","DEVELOPER_DIR")})
    gate.environment_policy(state["environment_policy"])
    versions={"cmake":gate.output([cmake,"--version"]),"ctest":gate.output([ctest,"--version"])}
    policy=gate.tool_policy(versions)
    state.update(tool_versions=versions,tool_policy=policy)
    compiler=gate.output(frozen["compiler_command"])
    gate.exact(compiler,frozen["compiler"],"current Apple compiler differs")
    sdk=gate.output(["/usr/bin/arch","-arm64","/usr/bin/xcrun","--show-sdk-path"]).strip()
    gate.exact(sdk,frozen["sdk"],"current SDK differs")
    acquisition=gate.acquisition_command(source,args.git_resolve)
    acquire_log=args.output/"acquisition.log"; acquire_groups=args.output/"acquisition-groups.json"
    acquisition_intervals=[]; acquire_guard=inherited.SerialGuard(acquire_groups)
    with acquire_log.open("x") as stream:
        guarded(acquire_guard,acquisition,stream,acquisition_intervals,state,env=environment)
    library_sources=gate.source_tree(source)
    record=dict(schema="current_complexity_build_v1",validation="pass",working_directory=str(ROOT),
                created_utc=gate.native.now(),parent_freeze=str(parent_path),parent_freeze_sha256=gate.PARENT_SHA,
                google_benchmark_commit=gate.COMMIT,owned_groups_verified_empty=True,
                **{key:frozen[key] for key in ("compiler","compiler_command","sdk","object_paths","object_sha256")},
                library_source_root=str(source),library_build_directory=str(destination),library_source_sha256=library_sources,
                library_link_flags=["-lpthread"],recipe_sha256=state["recipe_sha256"],environment_policy=state["environment_policy"],
                acquisition_command=acquisition,acquisition_interval=acquisition_intervals[0],git_resolve=args.git_resolve)
    hash_field(record,"cmake",Path(cmake)); hash_field(record,"ctest",Path(ctest))
    record.update(tool_versions=versions,tool_policy=policy)
    record["library_commands"]=gate.library_commands(record)
    main_object=destination/"current_complexity.o"; binary=destination/"current_complexity"
    library=destination/"src/libbenchmark.a"
    base=["/usr/bin/arch","-arm64","/usr/bin/clang++","-isysroot",sdk,*gate.FLAGS,
          "-I"+str(ROOT),"-I"+str(source/"include")]
    main_commands=[base+["-c",str(HERE/"current_complexity.cpp"),"-o",str(main_object)],
                   base+list(record["object_paths"].values())+[str(main_object),str(library),"-lpthread",
                        "-L"+sdk+"/usr/lib","-Wl,-stack_size,0x20000000","-o",str(binary)]]
    log=args.output/"build.log"; groups=args.output/"build-groups.json"; intervals=[]
    guard=inherited.SerialGuard(groups)
    with log.open("x") as stream:
        stream.write(compiler+"SDK: "+sdk+"\n"+json.dumps(state["environment_policy"])+"\n")
        for command in [*record["library_commands"],*main_commands]:
            guarded(guard,command,stream,intervals,state,env=environment)
    record.update(build_commands=main_commands,link_command=main_commands[-1],command_intervals=intervals)
    for key,path in (("driver",HERE/"current_complexity.cpp"),("main_object",main_object),("binary",binary),("library",library),
                     ("build_log",log),("owned_groups",groups),("library_test_xml",destination/"library-tests.xml"),
                     ("cmake_cache",destination/"CMakeCache.txt"),("library_link_interface",destination/"src/generated/benchmark.pc"),
                     ("acquisition_log",acquire_log),("acquisition_groups",acquire_groups)):
        hash_field(record,key,path)
    record["binary_profile"]=gate.native.binary_profile(binary)
    compile_file=destination/"compile_commands.json"; record["compile_commands_sha256"]=analyzer.digest(compile_file)
    library_cpp={str(path) for path in (source/"src").glob("*.cc") if path.name != "benchmark_main.cc"}
    selected=[entry for entry in gate.read(compile_file) if entry["file"] in library_cpp]
    record["library_compile_commands"]=[entry.get("arguments") or shlex.split(entry["command"]) for entry in selected]
    record["library_object_sha256"]={str(destination/"src/CMakeFiles/benchmark.dir"/(Path(entry["file"]).name+".o")):
        analyzer.digest(destination/"src/CMakeFiles/benchmark.dir"/(Path(entry["file"]).name+".o")) for entry in selected}
    path=args.output/"build-record.json"; save(path,record)
    try:
        gate.check_record(path)
        gate.exact(recipes(),state["recipe_sha256"],"source recipe changed during build gate")
    except BaseException:
        record["validation"]="failed"
        path.write_text(json.dumps(record,indent=2,allow_nan=False)+"\n")
        raise
    state.update(build_record=str(path),build_record_sha256=analyzer.digest(path),all_owned_groups_verified_empty=True)


def smoke(args,state):
    build_record=args.build_record.resolve(strict=True); record=gate.check_record(build_record)
    evidence={str(build_record):analyzer.digest(build_record)}
    curves=[]; commands=[]; intervals=[]; groups=args.output/"schema-smoke-groups.json"
    guard=inherited.SerialGuard(groups)
    for index,algorithm in enumerate(("kkt","multigraph_boruvka"),1):
        spec=dict(family="gnm_random",algorithm=algorithm,graph_seed=19000013,sampling_seed=3001,size_order="ascending")
        raw=args.output/f"smoke-{index}.csv"; library=args.output/f"smoke-{index}.json"
        log=args.output/f"smoke-{index}.log"; console=args.output/f"smoke-{index}.console.txt"
        command=["/usr/bin/arch","-arm64",record["binary"],spec["family"],algorithm,"19000013","3001","ascending",str(raw),str(library)]
        with console.open("x") as stdout,log.open("x") as stderr:
            guarded(guard,command,stdout,intervals,state,stderr=stderr)
        rows,_=analyzer.validate_native(raw.read_text(),log.read_text(),spec)
        analyzer.validate_curve_library(gate.read(library),spec,rows)
        curves.append(dict(spec=spec,raw_csv=str(raw),benchmark_json=str(library),log=str(log),console=str(console),command=command))
        commands.append(command)
        for path in (raw,library,log,console): evidence[str(path)]=analyzer.digest(path)
    gate.owned_groups(groups,commands,intervals)
    evidence[str(groups)]=analyzer.digest(groups)
    details=dict(schema="current_complexity_smoke_details_v1",curves=curves,owned_groups=str(groups),command_intervals=intervals,
                 checked_curves=2,checked_raw_rows=198,checked_certificates=66,used_in_study_analysis=False,
                 native_execution=True,owned_groups_verified_empty=True)
    details_path=args.output/"schema-smoke-details.json"; save(details_path,details); evidence[str(details_path)]=analyzer.digest(details_path)
    sources=state["recipe_sha256"]
    receipt=dict(schema="current_complexity_schema_smoke_v1",validation="pass",google_benchmark_commit=gate.COMMIT,
                 **{key:record[key] for key in ("driver_sha256","binary_sha256","library_sha256")},source_sha256=sources,
                 bound_sha256={**record["bound_sha256"],**evidence},schema_contract=analyzer.SCHEMA_CONTRACT,
                 native_execution=True,owned_groups_verified_empty=True)
    path=args.output/"schema-smoke.json"; save(path,receipt)
    try:
        gate.check_record(build_record)
        gate.check_schema_smoke(path,record,analyzer.SCHEMA_CONTRACT)
        gate.exact(recipes(),state["recipe_sha256"],"source recipe changed during smoke gate")
    except BaseException:
        receipt["validation"]="failed"; path.write_text(json.dumps(receipt,indent=2,allow_nan=False)+"\n"); raise
    state.update(schema_smoke=str(path),schema_smoke_sha256=analyzer.digest(path),all_owned_groups_verified_empty=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__); commands=parser.add_subparsers(dest="phase",required=True)
    build_parser=commands.add_parser("build")
    build_parser.add_argument("--parent-freeze",type=Path,required=True)
    build_parser.add_argument("--library-source",type=Path,required=True)
    build_parser.add_argument("--build-directory",type=Path,required=True)
    build_parser.add_argument("--git-resolve")
    smoke_parser=commands.add_parser("smoke"); smoke_parser.add_argument("--build-record",type=Path,required=True)
    for command in (build_parser,smoke_parser):
        command.add_argument("--output",type=Path,required=True); command.add_argument("--released",action="store_true")
    args=parser.parse_args(); gate.require(args.released,"explicit nonperformance build/smoke release required")
    gate.require(inherited.ROOT==ROOT,"unchanged native guard must use the frozen eighth worktree")
    args.output=args.output.resolve(); args.output.mkdir(parents=True,exist_ok=False)
    state=dict(schema="current_complexity_gate_attempt_v1",phase=args.phase,validation="running",invocation=sys.argv,
               started_utc=gate.native.now(),started_monotonic_ns=time.monotonic_ns(),attempted_commands=[],
               native_library_or_solver_execution_authorized=True,performance_capture=False,
               all_owned_groups_verified_empty=False,recipe_sha256=recipes())
    save(args.output/"invocation.json",state)
    try:
        (build if args.phase=="build" else smoke)(args,state)
        gate.exact(recipes(),state["recipe_sha256"],"source recipe changed during gate")
        state["validation"]="pass"
    except BaseException as error:
        state.update(validation="failed",error=repr(error)); raise
    finally:
        state.update(finished_utc=gate.native.now(),finished_monotonic_ns=time.monotonic_ns())
        save(args.output/"attempt.json",state)
    print(json.dumps({key:state[key] for key in ("phase","validation","all_owned_groups_verified_empty")},sort_keys=True))


if __name__ == "__main__": main()
