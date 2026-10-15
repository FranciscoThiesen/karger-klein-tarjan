#!/usr/bin/env python3
"""Read-only gate for a future real Google Benchmark/library/main build.

No library is downloaded, built or executed by this module. Receipt production
is specified separately in BUILD_GATE_PLAN.md and remains unreleased.
"""
import hashlib
import importlib.util
import ipaddress
from pathlib import Path
import re
import shlex
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = Path.cwd().resolve()
_previous_path = sys.path[:]
try:
    sys.path.insert(0, str(ROOT / "benchmark"))
    import run_eighth_sampling as parent_engine
finally:
    sys.path[:] = _previous_path

# The repository also has a historical module named analyze_complexity.
# Bind this gate to its reviewed sibling regardless of path order/module cache.
_analyzer_spec = importlib.util.spec_from_file_location(
    "current_complexity_build_analyzer", HERE / "analyze_complexity.py")
if _analyzer_spec is None or _analyzer_spec.loader is None:
    raise ImportError("cannot load the current complexity analyzer")
analyzer = importlib.util.module_from_spec(_analyzer_spec)
sys.modules[_analyzer_spec.name] = analyzer
_analyzer_spec.loader.exec_module(analyzer)

native = parent_engine.control.native
require = analyzer.require
COMMIT = analyzer.COMMIT
PARENT_SHA = analyzer.PARENT_SHA
FLAGS = ["-std=c++17", "-O3", "-Wall", "-Wextra", "-march=native",
         "-DKKT_EXPERIMENT_RETAIN_PARALLEL", "-DKKT_EXPERIMENT_EDGE_VIEW"]
# Pinned v1.5.2 has an unused accumulator under Apple Clang 15's newer
# diagnostic. Keep the warning visible; relax only its promotion to an error.
# This applies to the upstream library/test build, never production objects.
LIBRARY_WARNING_FLAG = "-Wno-error=unused-but-set-variable"
ORIGIN = "https://github.com/google/benchmark.git"
EMPTY_ENVIRONMENT = ("CPLUS_INCLUDE_PATH", "C_INCLUDE_PATH", "CFLAGS", "CXXFLAGS", "CPPFLAGS", "LDFLAGS",
                     "CC", "CXX", "CMAKE_GENERATOR", "CMAKE_TOOLCHAIN_FILE", "CMAKE_POLICY_VERSION_MINIMUM",
                     "CMAKE_OSX_ARCHITECTURES", "MACOSX_DEPLOYMENT_TARGET", "APPVEYOR")


def exact(actual, expected, label):
    require(type(actual) is type(expected) and actual == expected, label)
    if type(expected) is dict:
        for key in expected: exact(actual[key], expected[key], label + ": " + str(key))
    elif type(expected) in (list, tuple):
        for index, value in enumerate(expected): exact(actual[index], value, label + ": " + str(index))


def read(path):
    return analyzer.parse_json(Path(path).read_text())


def bind(bound, path, expected):
    require(Path(path).is_absolute(), "artifact paths must be absolute")
    return analyzer.add_bound(bound, path, expected)


def output(command):
    # Read-only metadata tools, never compiler/library/solver execution.
    return subprocess.check_output(command, text=True, timeout=10)


def output_bytes(command):
    return subprocess.check_output(command, timeout=10)


def acquisition_command(source, resolution=None):
    command=["/usr/bin/git"]
    if resolution is not None:
        require(type(resolution) is str and resolution.startswith("github.com:443:"),"only an explicit public GitHub TLS resolution is allowed")
        address=resolution[len("github.com:443:"):]
        require(str(ipaddress.IPv4Address(address)) == address,"noncanonical public GitHub IPv4 override")
        require(ipaddress.IPv4Address(address).is_global,"resolution override must be public")
        command += ["-c","http.curloptResolve="+resolution]
    return command+["clone","--depth","1","--branch","v1.5.2","--single-branch",ORIGIN,str(source)]


def tool_policy(versions):
    exact(set(versions),{"cmake","ctest"},"missing build tool version")
    parsed={}
    for name in ("cmake","ctest"):
        require(type(versions[name]) is str,"invalid build tool version text")
        match=re.match(name+r" version ([0-9]+)\.([0-9]+)\.([0-9]+)(?:\n|$)",versions[name])
        require(match is not None,"unreviewed prerelease/build tool version")
        parsed[name]=tuple(int(part) for part in match.groups())
    exact(parsed["cmake"],parsed["ctest"],"CMake and CTest versions differ")
    require((3,21,0) <= parsed["cmake"] < (5,0,0),"CMake/CTest requires reviewed 3.21+ or 4.x for JUnit")
    # v1.5.2 already requests 3.5.1; CMake 4 removes only policies below 3.5.
    # Preserve its declared policies, rather than preemptively changing them.
    return dict(cmake_version=list(parsed["cmake"]),ctest_version=list(parsed["ctest"]),
                upstream_minimum="3.5.1",policy_version_override=None,generator="Unix Makefiles")


def environment_policy(value):
    exact(set(value),{"removed","required_empty","retained"},"wrong toolchain environment policy")
    exact(set(value["removed"]),{"CPATH","LIBRARY_PATH"},"different environment removals")
    exact(set(value["required_empty"]),set(EMPTY_ENVIRONMENT),"incomplete environment override check")
    exact(set(value["retained"]),{"SDKROOT","DEVELOPER_DIR"},"different retained toolchain environment")
    require(all(item is None or type(item) is str for group in value.values() for item in group.values()),"invalid environment value type")
    require(all(item in (None,"") for item in value["required_empty"].values()),"unreviewed nonempty toolchain override")


def source_tree(root):
    root = Path(root).resolve(strict=True)
    exact(output(["/usr/bin/git", "-C", str(root), "rev-parse", "HEAD"]).strip(), COMMIT, "wrong library Git commit")
    exact(output(["/usr/bin/git", "-C", str(root), "remote", "get-url", "origin"]).strip(), ORIGIN, "wrong library origin")
    exact(output(["/usr/bin/git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"]), "", "modified library source tree")
    names = output(["/usr/bin/git", "-C", str(root), "ls-files", "-z"]).split("\0")
    names = [name for name in names if name]
    require(names and len(names) == len(set(names)), "empty/duplicate library tracked files")
    result = {}
    for name in names:
        path = root / name
        require(path.resolve().is_relative_to(root), "library tracked path escapes source tree")
        require(path.is_file() and not path.is_symlink(), "unsupported library tracked file type")
        result[str(path)] = analyzer.digest(path)
    return result


def owned_groups(path, expected_commands, intervals):
    value = read(path)
    require(set(value) == {"groups"} and type(value["groups"]) is list, "wrong SerialGuard evidence")
    exact(len(value["groups"]), len(expected_commands), "missing build/smoke groups")
    exact(len(intervals),len(expected_commands),"missing bounded command intervals")
    previous_finish=-1
    for item, command, interval in zip(value["groups"], expected_commands, intervals):
        exact(item["command"], command, "wrong guarded command")
        exact(interval["command"],command,"wrong interval command")
        start,finish=interval["started_monotonic_ns"],interval["finished_monotonic_ns"]
        require(type(start) is int and type(finish) is int and previous_finish <= start < finish and
                finish-start <= 300*1_000_000_000,"guarded command plus cleanup exceeded 300 seconds/overlapped")
        previous_finish=finish
        require(type(item["process_group"]) is int and item["process_group"] > 0, "invalid guarded process group")
        exact(item.get("exit_status"), 0, "failed guarded command")
        require("error" not in item, "guarded command recorded failure")
        cleanup = item["cleanup"]
        require(type(cleanup["started_monotonic_ns"]) is int and type(cleanup["finished_monotonic_ns"]) is int and
                start <= cleanup["started_monotonic_ns"] <= cleanup["finished_monotonic_ns"] <= finish,"cleanup outside bounded interval")
        for key, expected in dict(native_exit_known=True, group_exit_known=True,
                                  native_process_may_still_be_running=False, returncode=0,
                                  process_group=item["process_group"]).items():
            exact(cleanup[key], expected, "unknown/nonzero owned exit: " + key)
        final = cleanup["group_verification"]
        exact(final["validation"], "pass", "unavailable final group proof")
        exact(final["members"], [], "nonempty final group")
        exact(final["rss_kib"], 0, "nonzero final RSS")
        exact(final["process_group"], item["process_group"], "different final group")
        require(type(final["monotonic_ns"]) is int and cleanup["started_monotonic_ns"] <= final["monotonic_ns"] <= cleanup["finished_monotonic_ns"],
                "final empty sample outside cleanup")
        require(type(item["observations"]) is list, "missing resource observations")
        consecutive = 0; previous = -1
        for observation in [*item["observations"], final]:
            exact(observation["process_group"], item["process_group"], "resource group mismatch")
            require(type(observation["monotonic_ns"]) is int and observation["monotonic_ns"] > previous, "resource order changed")
            require(start <= observation["monotonic_ns"] <= finish,"resource observation outside command interval")
            previous = observation["monotonic_ns"]
            if observation["validation"] == "unavailable":
                consecutive += 1; require(consecutive < 3, "three unavailable observations")
            else:
                exact(observation["validation"], "pass", "unsupported observation")
                consecutive = 0
                require(type(observation["rss_kib"]) is int and 0 <= observation["rss_kib"] <= 40*1024*1024, "sampled RSS ceiling")
                require(type(observation["members"]) is list, "invalid group members")
                require(all(type(member["pid"]) is int and member["pid"] > 0 and type(member["rss_kib"]) is int and member["rss_kib"] >= 0
                            for member in observation["members"]), "invalid member schema")
                require(sum(member["rss_kib"] for member in observation["members"]) == observation["rss_kib"], "incorrect RSS sum")
    return value


def library_commands(record):
    cmake, ctest = record["cmake"], record["ctest"]
    require(Path(cmake).is_absolute() and Path(cmake).name == "cmake", "wrong CMake executable")
    require(Path(ctest).is_absolute() and Path(ctest).name == "ctest", "wrong CTest executable")
    source, build, sdk = record["library_source_root"], record["library_build_directory"], record["sdk"]
    exact(record["tool_policy"],tool_policy(record["tool_versions"]),"different source-declared CMake policy")
    configure = ["/usr/bin/arch", "-arm64", cmake, "-S", source, "-B", build,"-G","Unix Makefiles",
                 "-DCMAKE_CXX_COMPILER=/usr/bin/clang++", "-DCMAKE_BUILD_TYPE=Release",
                 "-DCMAKE_CXX_FLAGS="+LIBRARY_WARNING_FLAG,
                 "-DCMAKE_OSX_ARCHITECTURES=arm64", "-DCMAKE_OSX_SYSROOT="+sdk,
                 "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", "-DBUILD_SHARED_LIBS=OFF",
                 "-DBENCHMARK_ENABLE_TESTING=ON", "-DBENCHMARK_ENABLE_GTEST_TESTS=OFF",
                 "-DBENCHMARK_ENABLE_ASSEMBLY_TESTS=OFF", "-DBENCHMARK_ENABLE_LTO=OFF",
                 "-DBENCHMARK_DOWNLOAD_DEPENDENCIES=OFF", "-DBENCHMARK_ENABLE_INSTALL=OFF"]
    build_command = ["/usr/bin/arch", "-arm64", cmake, "--build", build, "--parallel", "1"]
    tests = ["/usr/bin/arch", "-arm64", ctest, "--test-dir", build, "--output-on-failure", "--parallel", "1",
             "--timeout", "30", "--output-junit", str(Path(build)/"library-tests.xml")]
    return [configure, build_command, tests]


def library_objects(record, bound):
    source, build = Path(record["library_source_root"]), Path(record["library_build_directory"])
    compile_file = build/"compile_commands.json"
    bind(bound, str(compile_file), record["compile_commands_sha256"])
    commands = read(compile_file); require(type(commands) is list, "invalid CMake compile commands")
    expected_sources = {str(path) for path in (source/"src").glob("*.cc") if path.name != "benchmark_main.cc"}
    accepted = {}; selected = []
    for entry in commands:
        if entry["file"] not in expected_sources: continue
        exact(entry["directory"], str(build/"src"), "different library build directory")
        argv = entry.get("arguments") or shlex.split(entry["command"])
        exact(argv[0], "/usr/bin/clang++", "different library compiler")
        name = Path(entry["file"]).name
        obj = build/"src/CMakeFiles/benchmark.dir"/(name+".o")
        require(argv[-4:] == ["-o", str(obj.relative_to(build/"src")), "-c", entry["file"]] or
                argv[-4:] == ["-o", str(obj), "-c", entry["file"]], "unexpected library compile output")
        flags = argv[1:-4]
        for pair in (("-arch", "arm64"), ("-isysroot", record["sdk"])):
            require(flags.count(pair[0]) == 1, "missing/duplicate native library flag")
            index=flags.index(pair[0]); exact(flags[index:index+2], list(pair), "wrong native library flag")
        require(flags.count("-O3") == 1 and flags.count("-DNDEBUG") == 1 and flags.count("-std=c++11") == 1,
                "unexpected library optimization/language profile")
        require(flags.count(LIBRARY_WARNING_FLAG) == 1,
                "missing/duplicate exact library warning compatibility flag")
        allowed = {"-O3", "-DNDEBUG", "-std=c++11", "-Wall", "-Wextra", "-Wshadow", "-Werror", "-Wshorten-64-to-32",
                   LIBRARY_WARNING_FLAG,
                   "-fstrict-aliasing", "-Wno-deprecated-declarations", "-Wno-deprecated", "-Wstrict-aliasing", "-Wthread-safety",
                   "-DHAVE_STD_REGEX", "-DHAVE_GNU_POSIX_REGEX", "-DHAVE_POSIX_REGEX", "-DHAVE_STEADY_CLOCK", "-DHAVE_THREAD_SAFETY_ATTRIBUTES",
                   "-arch", "arm64", "-isysroot", record["sdk"]}
        include_roots={(source/"include").resolve(),(source/"src").resolve()}
        require(all(flag in allowed or (flag.startswith("-I") and Path(flag[2:]).is_absolute() and
                    Path(flag[2:]).resolve() in include_roots) for flag in flags),
                "unreviewed library compiler flag; review actual configure before freeze")
        require(entry["file"] not in accepted, "duplicate library source compile")
        accepted[entry["file"]] = str(obj); selected.append(argv)
        require(output(["/usr/bin/file", "-b", str(obj)]).strip() == "Mach-O 64-bit object arm64", "translated library object")
    exact(set(accepted), expected_sources, "incomplete static library source matrix")
    exact(record["library_compile_commands"], selected, "actual library compile argv differs")
    exact(set(record["library_object_sha256"]), set(accepted.values()), "incomplete library object inventory")
    for path, expected in record["library_object_sha256"].items(): bind(bound, path, expected)
    # Archive contents/profile are independently recorded and rechecked; the
    # final linked API smoke checks the actual archive, not merely these objects.
    exact(output(["/usr/bin/ar", "-t", record["library"]]).splitlines(), [Path(path).name for path in accepted.values()], "static archive member inventory")
    for path in accepted.values():
        contents=output_bytes(["/usr/bin/ar","-p",record["library"],Path(path).name])
        exact(hashlib.sha256(contents).hexdigest(),record["library_object_sha256"][path],"static archive member bytes differ from compiled object")
    return accepted


def check_record(path):
    path=Path(path).resolve(strict=True); initial=analyzer.digest(path); record=read(path); bound={}
    for key,value in dict(schema="current_complexity_build_v1", validation="pass", working_directory=str(ROOT),
                          parent_freeze_sha256=PARENT_SHA, google_benchmark_commit=COMMIT,
                          owned_groups_verified_empty=True).items(): exact(record.get(key),value,"build metadata: "+key)
    bind(bound,record["parent_freeze"],PARENT_SHA)
    parent,_=parent_engine.check_freeze(Path(record["parent_freeze"]))
    frozen=parent["variants"]["eighth"]["build"]["record"]
    for key in ("object_paths","object_sha256","compiler","compiler_command","sdk"):
        exact(record[key],frozen[key],"eight frozen objects/toolchain: "+key)
    exact(output(record["compiler_command"]),record["compiler"],"current compiler identity changed")
    exact(output(["/usr/bin/arch","-arm64","/usr/bin/xcrun","--show-sdk-path"]).strip(),record["sdk"],"current SDK selection changed")
    environment_policy(record["environment_policy"])
    for name in ("cmake","ctest"):
        exact(output([record[name],"--version"]),record["tool_versions"][name],"current build tool version differs")
    exact(record["driver"],str(HERE/"current_complexity.cpp"),"wrong main source")
    for key in ("driver","main_object","binary","library","cmake","ctest"):
        bind(bound,record[key],record[key+"_sha256"])
    require(record["main_object"] not in record["object_paths"].values(),"new main aliases a frozen production object")
    require(record["binary"] != parent["variants"]["eighth"]["binary"],"new main aliases parent timing binary")
    for name,source in record["object_paths"].items(): bind(bound,source,record["object_sha256"][name])
    exact(record["library_source_sha256"],source_tree(record["library_source_root"]),"changed pinned library source")
    for source,expected in record["library_source_sha256"].items(): bind(bound,source,expected)
    exact(record["library_commands"],library_commands(record),"library configure/build/test command differs")
    base=["/usr/bin/arch","-arm64","/usr/bin/clang++","-isysroot",record["sdk"],*FLAGS,
          "-I"+str(ROOT),"-I"+str(Path(record["library_source_root"])/"include")]
    compile_command=base+["-c",record["driver"],"-o",record["main_object"]]
    # The pinned upstream benchmark.pc.in explicitly declares -lpthread for
    # static consumers. Recheck the actual generated file before accepting it.
    exact(record["library_link_flags"],["-lpthread"],"unreviewed platform library dependencies")
    link_command=base+list(record["object_paths"].values())+[record["main_object"],record["library"],
                         "-lpthread","-L"+record["sdk"]+"/usr/lib","-Wl,-stack_size,0x20000000","-o",record["binary"]]
    exact(record["build_commands"],[compile_command,link_command],"exact two new-main commands")
    exact(record["link_command"],link_command,"different final link")
    for key in ("build_log","owned_groups","library_test_xml","cmake_cache","library_link_interface","acquisition_log","acquisition_groups"):
        bind(bound,record[key],record[key+"_sha256"])
    library_build=Path(record["library_build_directory"])
    exact(record["library"],str(library_build/"src/libbenchmark.a"),"archive differs from configured target")
    exact(record["library_test_xml"],str(library_build/"library-tests.xml"),"wrong upstream test report")
    exact(record["cmake_cache"],str(library_build/"CMakeCache.txt"),"wrong configured cache")
    exact(record["library_link_interface"],str(library_build/"src/generated/benchmark.pc"),"wrong generated static interface")
    private=[line.partition(":")[2].strip() for line in Path(record["library_link_interface"]).read_text().splitlines()
             if line.startswith("Libs.private:")]
    exact(private,["-lpthread"],"configured library dependency interface")
    cache={}
    for line in Path(record["cmake_cache"]).read_text().splitlines():
        if not line or line.startswith(("#","//")): continue
        head,separator,value=line.partition("=")
        require(separator and ":" in head,"malformed CMake cache")
        key=head.partition(":")[0]; require(key not in cache,"duplicate cache key"); cache[key]=value
    for key,value in dict(CMAKE_HOME_DIRECTORY=record["library_source_root"],CMAKE_GENERATOR="Unix Makefiles",CMAKE_CXX_COMPILER="/usr/bin/clang++",
                          CMAKE_BUILD_TYPE="Release",CMAKE_OSX_ARCHITECTURES="arm64",CMAKE_OSX_SYSROOT=record["sdk"],
                          CMAKE_CXX_FLAGS=LIBRARY_WARNING_FLAG,
                          CMAKE_EXPORT_COMPILE_COMMANDS="ON",BUILD_SHARED_LIBS="OFF",BENCHMARK_ENABLE_TESTING="ON",
                          BENCHMARK_ENABLE_GTEST_TESTS="OFF",BENCHMARK_ENABLE_ASSEMBLY_TESTS="OFF",BENCHMARK_ENABLE_LTO="OFF",
                          BENCHMARK_DOWNLOAD_DEPENDENCIES="OFF",BENCHMARK_ENABLE_INSTALL="OFF").items():
        exact(cache.get(key),value,"configured library option differs: "+key)
    require("CMAKE_POLICY_VERSION_MINIMUM" not in cache,"unreviewed CMake policy override")
    owned_groups(record["owned_groups"],[*record["library_commands"],*record["build_commands"]],record["command_intervals"])
    acquisition=acquisition_command(record["library_source_root"],record["git_resolve"])
    exact(record["acquisition_command"],acquisition,"different library acquisition")
    owned_groups(record["acquisition_groups"],[acquisition],[record["acquisition_interval"]])
    exact(record["binary_profile"],native.binary_profile(Path(record["binary"])),"final native executable profile")
    exact(record["binary_profile"]["main_stack_bytes"],536870912,"wrong main stack")
    exact(record["binary_profile"]["file_description"],"Mach-O 64-bit executable arm64","wrong binary architecture")
    exact(output(["/usr/bin/file","-b",record["main_object"]]).strip(),"Mach-O 64-bit object arm64","translated new main")
    library_objects(record,bound)
    tests=ET.parse(record["library_test_xml"]).getroot()
    cases=list(tests.iter("testcase")); require(cases,"no actual library test cases")
    require(all(not any(child.tag in ("failure","error","skipped") for child in case) and case.get("status","run") in ("run","passed") for case in cases),
            "library test failed/skipped")
    require({case.get("name") for case in cases} >= {"complexity_benchmark","options_benchmarks","basic_benchmark"},"missing required upstream API/complexity tests")
    bind(bound,str(path),initial)
    for source,expected in record["recipe_sha256"].items(): bind(bound,source,expected)
    require(record["recipe_sha256"].get(str(Path(__file__).resolve())) == analyzer.digest(__file__),"record did not bind validator source")
    producer=HERE/"build_library_main.py"
    require(producer.is_file() and record["recipe_sha256"].get(str(producer)) == analyzer.digest(producer),
            "missing actual reviewed build producer recipe")
    analyzer.check_bound(bound)
    # Return a derived inventory; never trust a caller-supplied reduced one.
    return {**record,"bound_sha256":bound}


def check_schema_smoke(path, build, contract):
    path=Path(path).resolve(strict=True); initial=analyzer.digest(path); smoke=read(path); bound={}
    bind(bound,str(path),initial)
    frozen={**{key:build[key] for key in ("driver_sha256","binary_sha256","library_sha256")},
            "parent_freeze_sha256":PARENT_SHA,"schema_smoke":str(path),"schema_smoke_sha256":initial}
    analyzer.validate_smoke(dict(frozen_protocol=frozen),bound,HERE/"analyze_complexity.py")
    exact(smoke["schema_contract"],contract,"different smoke schema contract")
    for source,expected in smoke["source_sha256"].items(): bind(bound,source,expected)
    for source,expected in smoke["bound_sha256"].items(): bind(bound,source,expected)
    for source in (HERE/"analyze_complexity.py",HERE/"collect.py",HERE/"validate_build.py",HERE/"current_complexity.cpp"):
        exact(smoke["source_sha256"].get(str(source)),analyzer.digest(source),"smoke did not bind parser/main sources")
    details_path=path.with_name("schema-smoke-details.json")
    require(str(details_path) in bound,"missing actual smoke details")
    details=read(details_path)
    exact(details["schema"],"current_complexity_smoke_details_v1","wrong smoke details schema")
    specs=[dict(family="gnm_random",algorithm=algorithm,graph_seed=19000013,sampling_seed=3001,size_order="ascending")
           for algorithm in ("kkt","multigraph_boruvka")]
    require(len(details["curves"]) == 2,"missing actual final-binary smoke curve")
    commands=[]; fingerprints={}
    for curve,spec in zip(details["curves"],specs):
        exact(curve["spec"],spec,"different diagnostic smoke input")
        for key in ("raw_csv","benchmark_json","log","console"):
            require(curve[key] in bound,"smoke evidence not bound: "+key)
        argv=["/usr/bin/arch","-arm64",build["binary"],spec["family"],spec["algorithm"],str(spec["graph_seed"]),
              str(spec["sampling_seed"]),spec["size_order"],curve["raw_csv"],curve["benchmark_json"]]
        exact(curve["command"],argv,"smoke did not run final binary"); commands.append(argv)
        rows,_=analyzer.validate_native(Path(curve["raw_csv"]).read_text(),Path(curve["log"]).read_text(),spec)
        analyzer.validate_curve_library(read(curve["benchmark_json"]),spec,rows)
        for row in rows:
            value=row["input_fingerprint"],row["topology_fingerprint"]
            require(row["n"] not in fingerprints or fingerprints[row["n"]] == value,"smoke algorithms saw different graph")
            fingerprints[row["n"]]=value
    require(details["owned_groups"] in bound,"smoke owned-group receipt not bound")
    owned_groups(details["owned_groups"],commands,details["command_intervals"])
    for key,value in dict(checked_curves=2,checked_raw_rows=198,checked_certificates=66,
                          used_in_study_analysis=False,native_execution=True,owned_groups_verified_empty=True).items():
        exact(details[key],value,"incomplete/non-diagnostic smoke: "+key)
    analyzer.check_bound(bound)
    return details
