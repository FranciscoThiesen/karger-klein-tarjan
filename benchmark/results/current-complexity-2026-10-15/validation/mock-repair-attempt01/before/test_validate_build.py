#!/usr/bin/env python3
"""Prepared build-gate unit fixtures; no acquisition/build/native execution."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import validate_build as gate
import test_analyze_complexity as samples


def groups_fixture(commands):
    groups=[]; intervals=[]
    for index,command in enumerate(commands):
        start=index*1000+1; group=100+index
        observation=dict(process_group=group,monotonic_ns=start+10,validation="pass",members=[],rss_kib=0)
        final=dict(observation,monotonic_ns=start+80)
        groups.append(dict(command=command,process_group=group,exit_status=0,observations=[observation],
            cleanup=dict(process_group=group,native_exit_known=True,group_exit_known=True,
                native_process_may_still_be_running=False,returncode=0,started_monotonic_ns=start+20,
                finished_monotonic_ns=start+90,group_verification=final)))
        intervals.append(dict(command=command,started_monotonic_ns=start,finished_monotonic_ns=start+100))
    return dict(groups=groups),intervals


class BuildGateTests(unittest.TestCase):
    def test_fixed_library_configuration_and_no_implicit_dependencies(self):
        record=dict(cmake="/tools/cmake",ctest="/tools/ctest",library_source_root="/source",
                    library_build_directory="/build",sdk="/sdk",
                    tool_versions={"cmake":"cmake version 4.1.2\n","ctest":"ctest version 4.1.2\n"})
        record["tool_policy"]=gate.tool_policy(record["tool_versions"])
        configure,build,tests=gate.library_commands(record)
        self.assertEqual(configure[:4],["/usr/bin/arch","-arm64","/tools/cmake","-S"])
        for flag in ("-DBUILD_SHARED_LIBS=OFF","-DBENCHMARK_ENABLE_GTEST_TESTS=OFF","-DBENCHMARK_DOWNLOAD_DEPENDENCIES=OFF",
                     "-DBENCHMARK_ENABLE_TESTING=ON","-DCMAKE_OSX_ARCHITECTURES=arm64","-DCMAKE_CXX_COMPILER=/usr/bin/clang++"):
            self.assertIn(flag,configure)
        self.assertEqual(build,["/usr/bin/arch","-arm64","/tools/cmake","--build","/build","--parallel","1"])
        self.assertEqual(tests[-4:],["--timeout","30","--output-junit","/build/library-tests.xml"])
        self.assertIsNone(record["tool_policy"]["policy_version_override"])
        for version in ("3.20.6","5.0.0","4.1.0-rc1"):
            with self.assertRaises(ValueError): gate.tool_policy({name:f"{name} version {version}\n" for name in ("cmake","ctest")})
        environment=dict(removed={"CPATH":None,"LIBRARY_PATH":"/old"},
                         required_empty={key:None for key in gate.EMPTY_ENVIRONMENT},retained={"SDKROOT":None,"DEVELOPER_DIR":None})
        gate.environment_policy(environment)
        altered=copy.deepcopy(environment); altered["required_empty"]["CXXFLAGS"]="-fsanitize=address"
        with self.assertRaises(ValueError): gate.environment_policy(altered)
        with self.assertRaises(ValueError): gate.library_commands({**record,"cmake":"cmake"})
        self.assertEqual(gate.acquisition_command("/source")[:2],["/usr/bin/git","clone"])
        self.assertEqual(gate.acquisition_command("/source","github.com:443:140.82.112.4")[1:3],
                         ["-c","http.curloptResolve=github.com:443:140.82.112.4"])
        for bad in ("elsewhere:443:140.82.112.4","github.com:443:127.0.0.1","github.com:80:140.82.112.4"):
            with self.assertRaises(ValueError): gate.acquisition_command("/source",bad)

    def test_pinned_clean_source_tree_and_origin(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve(); (root/"source.cc").write_text("// source fixture\n")
            def output(command):
                if command[-2:] == ["rev-parse","HEAD"]: return gate.COMMIT+"\n"
                if command[-3:] == ["remote","get-url","origin"]: return gate.ORIGIN+"\n"
                if command[-3:] == ["status","--porcelain","--untracked-files=all"]: return ""
                if command[-2:] == ["ls-files","-z"]: return "source.cc\0"
                raise AssertionError(command)
            with mock.patch.object(gate,"output",side_effect=output):
                inventory=gate.source_tree(root)
            self.assertEqual(inventory,{str(root/"source.cc"):gate.analyzer.digest(root/"source.cc")})
            for bad in ("wrong commit\n","wrong origin\n"):
                with mock.patch.object(gate,"output",return_value=bad),self.assertRaises(ValueError): gate.source_tree(root)
            def dirty(command):
                return " M source.cc\n" if "status" in command else output(command)
            with mock.patch.object(gate,"output",side_effect=dirty),self.assertRaises(ValueError): gate.source_tree(root)

    def test_actual_library_objects_commands_architecture_and_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve(); source=root/"source"; build=root/"build"
            (source/"src").mkdir(parents=True); build.mkdir()
            entries=[]; hashes={}; argv_list=[]
            for name in ("a.cc","b.cc"):
                cpp=source/"src"/name; cpp.write_text("// synthetic\n")
                obj=build/"src/CMakeFiles/benchmark.dir"/(name+".o"); obj.parent.mkdir(parents=True,exist_ok=True); obj.write_bytes(name.encode())
                argv=["/usr/bin/clang++","-O3","-DNDEBUG","-std=c++11","-arch","arm64","-isysroot","/sdk",
                      "-I"+str(source/"src"),"-I"+str(source/"include"),"-o",str(obj.relative_to(build)),"-c",str(cpp)]
                entries.append(dict(directory=str(build),file=str(cpp),arguments=argv)); hashes[str(obj)]=gate.analyzer.digest(obj); argv_list.append(argv)
            compile_file=build/"compile_commands.json"; compile_file.write_text(json.dumps(entries))
            record=dict(library_source_root=str(source),library_build_directory=str(build),sdk="/sdk",
                        compile_commands_sha256=gate.analyzer.digest(compile_file),library_compile_commands=argv_list,
                        library_object_sha256=hashes,library=str(build/"src/libbenchmark.a"))
            def output(command):
                return "Mach-O 64-bit object arm64\n" if command[0]=="/usr/bin/file" else "a.cc.o\nb.cc.o\n"
            with mock.patch.object(gate,"output",side_effect=output),mock.patch.object(gate,"output_bytes",side_effect=lambda command:command[-1][:-2].encode()):
                self.assertEqual(len(gate.library_objects(record,{})),2)
                changed=copy.deepcopy(entries); changed[0]["arguments"].insert(1,"-fsanitize=address")
                compile_file.write_text(json.dumps(changed)); altered={**record,"compile_commands_sha256":gate.analyzer.digest(compile_file)}
                with self.assertRaisesRegex(ValueError,"unreviewed"): gate.library_objects(altered,{})
            compile_file.write_text(json.dumps(entries))
            with mock.patch.object(gate,"output",side_effect=output),mock.patch.object(gate,"output_bytes",return_value=b"wrong object"):
                with self.assertRaisesRegex(ValueError,"member bytes"): gate.library_objects(record,{})
            with mock.patch.object(gate,"output",return_value="Mach-O 64-bit object x86_64\n"),self.assertRaises(ValueError):
                gate.library_objects(record,{})

    def test_all_groups_deadlines_types_unknown_and_complete_commands(self):
        commands=[["/synthetic/one"],["/synthetic/two"]]; value,intervals=groups_fixture(commands)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"groups.json"
            def check(data,times=intervals):
                path.write_text(json.dumps(data)); return gate.owned_groups(path,commands,times)
            self.assertEqual(len(check(value)["groups"]),2)
            mutations=(lambda x:x["groups"].pop(),lambda x:x["groups"][0].update(exit_status=False),
                       lambda x:x["groups"][0]["cleanup"].update(group_exit_known=False),
                       lambda x:x["groups"][0]["cleanup"].update(native_process_may_still_be_running=True),
                       lambda x:x["groups"][0]["cleanup"].update(started_monotonic_ns=1.0),
                       lambda x:x["groups"][0]["cleanup"]["group_verification"].update(monotonic_ns=19),
                       lambda x:x["groups"][0]["observations"][0].update(monotonic_ns=0),
                       lambda x:x["groups"][0]["cleanup"]["group_verification"].update(members=[dict(pid=1,rss_kib=1)]),
                       lambda x:x["groups"][0].update(command=["/wrong"]))
            for mutation in mutations:
                changed=copy.deepcopy(value); mutation(changed)
                with self.assertRaises(ValueError): check(changed)
            late=copy.deepcopy(intervals); late[0]["finished_monotonic_ns"]+=300*10**9
            with self.assertRaisesRegex(ValueError,"300 seconds"): check(value,late)

    def test_real_smoke_requires_both_final_binary_curves_and_bound_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve(); smoke_path=root/"schema-smoke.json"; details_path=root/"schema-smoke-details.json"
            specs=[spec for spec in samples.declared_specs() if spec["family"]=="gnm_random" and spec["graph_seed"]==19000013 and spec["sampling_seed"]==3001]
            curves=[]; bound={}; commands=[]
            build=dict(binary="/final/synthetic-never-executed",driver_sha256="a"*64,binary_sha256="b"*64,library_sha256="c"*64)
            for index,spec in enumerate(specs):
                rows,log=samples.make_native(spec); raw=root/f"{index}.csv"; log_path=root/f"{index}.log"
                library=root/f"{index}.json"; console=root/f"{index}.txt"
                raw.write_text(samples.encode_rows(rows)); log_path.write_text(log)
                library.write_text(json.dumps(samples.make_library(spec,rows))); console.write_text("synthetic console\n")
                command=["/usr/bin/arch","-arm64",build["binary"],spec["family"],spec["algorithm"],str(spec["graph_seed"]),
                         str(spec["sampling_seed"]),spec["size_order"],str(raw),str(library)]
                curves.append(dict(spec=spec,raw_csv=str(raw),log=str(log_path),benchmark_json=str(library),console=str(console),command=command))
                commands.append(command)
                for path in (raw,log_path,library,console): bound[str(path)]=gate.analyzer.digest(path)
            groups,intervals=groups_fixture(commands); group_path=root/"groups.json"; group_path.write_text(json.dumps(groups))
            bound[str(group_path)]=gate.analyzer.digest(group_path)
            details=dict(schema="current_complexity_smoke_details_v1",curves=curves,owned_groups=str(group_path),command_intervals=intervals,
                         checked_curves=2,checked_raw_rows=198,checked_certificates=66,used_in_study_analysis=False,
                         native_execution=True,owned_groups_verified_empty=True)
            sources={str(gate.HERE/name):gate.analyzer.digest(gate.HERE/name)
                     for name in ("analyze_complexity.py","collect.py","validate_build.py","current_complexity.cpp")}
            smoke=dict(schema="current_complexity_schema_smoke_v1",validation="pass",google_benchmark_commit=gate.COMMIT,
                       **{key:build[key] for key in ("driver_sha256","binary_sha256","library_sha256")},source_sha256=sources,
                       bound_sha256=bound,schema_contract=gate.analyzer.SCHEMA_CONTRACT,native_execution=True,owned_groups_verified_empty=True)
            def check(value):
                details_path.write_text(json.dumps(value)); bound[str(details_path)]=gate.analyzer.digest(details_path)
                smoke_path.write_text(json.dumps(smoke)); return gate.check_schema_smoke(smoke_path,build,gate.analyzer.SCHEMA_CONTRACT)
            self.assertEqual(check(details)["checked_raw_rows"],198)
            for mutation in (lambda x:x["curves"].pop(),lambda x:x.update(used_in_study_analysis=True),
                             lambda x:x["curves"][0]["command"].__setitem__(2,"/wrong/final-binary"),
                             lambda x:x.update(checked_certificates=65)):
                changed=copy.deepcopy(details); mutation(changed)
                with self.assertRaises(ValueError): check(changed)
            changed=copy.deepcopy(details); changed["curves"][0]["spec"]["sampling_seed"]=3011
            with self.assertRaises(ValueError): check(changed)
            check(details)
            original_read=gate.read
            def mutate_after_read(path):
                value=original_read(path)
                if Path(path)==smoke_path: smoke_path.write_text(smoke_path.read_text()+"\n")
                return value
            with mock.patch.object(gate,"read",side_effect=mutate_after_read),self.assertRaises(ValueError):
                gate.check_schema_smoke(smoke_path,build,gate.analyzer.SCHEMA_CONTRACT)


if __name__ == "__main__": unittest.main(verbosity=2)
