#!/usr/bin/env python3
"""Untimed path-only Boruvka diagnostics for the two metric-line gap alphabets.

The embedded C++ program is compiled in a temporary directory. It generates no
shortcuts and invokes no production MST solver. Full-graph traces must separately
validate its component moments before using it to explain a measured fixture.
No simulator duration is reported as algorithm-performance evidence.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import tempfile

import analyze_continuation as base
import analyze_crossover_moments as moments


FAMILIES = ("line_metric", "line_wide_metric")
FIELDS = ("family", "n", "graph_seed", "stage", "component_count", "sum_squared_sizes",
          "largest_component", "boundary_count", "selected_edges", "total_selected_edges",
          "min_gap", "max_gap", "max_gap_count", "distinct_gap_count")

CPP_SOURCE = r'''
#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using u32 = std::uint32_t;
using u64 = std::uint64_t;
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}
struct Boundary {
    // Store gap-1 so the entire [1,2^32] alphabet fits in 32 bits.
    u32 value, original_id;
    bool operator==(const Boundary& other) const {
        return value == other.value && original_id == other.original_id;
    }
};
bool less(const Boundary& a, const Boundary& b) {
    return a.value < b.value || (a.value == b.value && a.original_id < b.original_id);
}
struct State { std::vector<u32> sizes; std::vector<Boundary> boundaries; };

State generated(const std::string& family, u32 n, u32 seed) {
    require(family == "line_metric" || family == "line_wide_metric", "unknown gap family");
    require(n >= 2 && n <= (1u<<23) && (n & (n-1)) == 0, "invalid diagnostic size");
    State state;
    state.sizes.assign(n, 1);
    state.boundaries.reserve(n-1);
    std::mt19937 rng(seed ^ 0x510e527fu);
    for (u32 id=0; id<n-1; ++id) {
        u32 word = static_cast<u32>(rng());
        // bounded(rng,1024) has zero rejection threshold, so this exactly
        // reproduces the old fixture stream, including its narrow/wide coupling.
        if (family == "line_metric") word %= 1024;
        state.boundaries.push_back({word,id});
    }
    return state;
}

State step(const State& state) {
    const std::size_t q = state.sizes.size();
    require(q >= 2 && state.boundaries.size()+1 == q, "invalid path state");
    State next;
    next.sizes.reserve(q/2);
    next.boundaries.reserve(q/2);
    u64 size = state.sizes[0];
    for (std::size_t i=0; i<state.boundaries.size(); ++i) {
        // An endpoint always selects its only edge. An internal boundary is
        // unselected by both adjacent components iff it is a strict local max
        // in the total order (raw gap, original physical-path edge ID).
        const bool survives = i>0 && i+1<state.boundaries.size() &&
            less(state.boundaries[i-1],state.boundaries[i]) &&
            less(state.boundaries[i+1],state.boundaries[i]);
        if (survives) {
            next.sizes.push_back(static_cast<u32>(size));
            next.boundaries.push_back(state.boundaries[i]);
            size = state.sizes[i+1];
        } else size += state.sizes[i+1];
    }
    next.sizes.push_back(static_cast<u32>(size));
    require(next.sizes.size() <= q/2, "path contraction failed to halve vertices");
    return next;
}

void emit(const std::string& family, u32 n, u32 seed, u32 stage, u32 selected, const State& state) {
    u64 sum=0, squares=0, largest=0;
    for (u32 size : state.sizes) {
        require(size>0, "empty original-vertex component");
        sum += size; squares += u64{size}*size; largest = std::max(largest,u64{size});
    }
    require(sum==n && state.sizes.size()==state.boundaries.size()+1, "invalid component accounting");
    u64 minimum=0, maximum=0, max_count=0, distinct=0;
    std::array<u64,1024> histogram{};
    for (const auto& boundary : state.boundaries) {
        const u64 gap = u64{boundary.value}+1;
        if (minimum==0 || gap<minimum) minimum=gap;
        if (gap>maximum) { maximum=gap; max_count=1; }
        else if (gap==maximum) ++max_count;
        if (family=="line_metric") {
            require(boundary.value<1024, "narrow gap outside alphabet");
            if (histogram[boundary.value]++==0) ++distinct;
        }
    }
    std::cout << family << ',' << n << ',' << seed << ',' << stage << ',' << state.sizes.size()
              << ',' << squares << ',' << largest << ',' << state.boundaries.size() << ',' << selected
              << ',' << n-state.sizes.size() << ',' << minimum << ',' << maximum << ',' << max_count << ',';
    if (family=="line_metric" || state.boundaries.empty()) std::cout << distinct;
    else std::cout << "na";
    std::cout << '\n';
}

// Independent small-graph oracle: each current vertex explicitly chooses its
// minimum incident edge, then DSU reconstructs connected components. It does
// not use the local-maximum characterization used by step().
State oracle(const State& state) {
    const int q=static_cast<int>(state.sizes.size());
    std::vector<int> parent(q);
    std::iota(parent.begin(),parent.end(),0);
    const auto find = [&](int v) {
        while (parent[v]!=v) { parent[v]=parent[parent[v]]; v=parent[v]; }
        return v;
    };
    for (int v=0; v<q; ++v) {
        int chosen = v==0 ? 0 : v-1;
        if (v>0 && v+1<q && less(state.boundaries[v],state.boundaries[chosen])) chosen=v;
        int a=find(chosen), b=find(chosen+1);
        if (a!=b) parent[b]=a;
    }
    State next;
    int previous=-1;
    for (int v=0; v<q; ++v) {
        const int root=find(v);
        if (root!=previous) {
            if (v) next.boundaries.push_back(state.boundaries[v-1]);
            next.sizes.push_back(state.sizes[v]);
        } else next.sizes.back()+=state.sizes[v];
        previous=root;
    }
    return next;
}

void self_test() {
    u64 cases=0, stages=0;
    const auto check = [&](State state) {
        ++cases;
        while (state.sizes.size()>1) {
            const auto expected=oracle(state);
            auto actual=step(state);
            require(actual.sizes==expected.sizes && actual.boundaries==expected.boundaries,
                    "local-maximum transition differs from independent minimum-edge DSU oracle");
            ++stages; state=std::move(actual);
        }
    };
    // Exhaust all paths with 1..7 boundaries over three gap values, including
    // the largest legal wide gap. This includes ties and monotone/alternating orders.
    const std::array<u32,3> alphabet{0,1,UINT32_MAX};
    u32 combinations=1;
    for (u32 edges=1; edges<=7; ++edges) {
        combinations*=3;
        for (u32 code=0; code<combinations; ++code) {
            State state; state.sizes.assign(edges+1,1);
            u32 rest=code;
            for (u32 id=0; id<edges; ++id) {
                state.boundaries.push_back({alphabet[rest%3],id}); rest/=3;
            }
            check(std::move(state));
        }
    }
    for (const std::string family : {"line_metric","line_wide_metric"})
        for (u32 n : {32u,128u,256u}) for (u32 seed : {17u,42u,3037u}) check(generated(family,n,seed));
    std::cout << "{\"validation\":\"pass\",\"independent_path_cases\":" << cases
              << ",\"independent_transition_checks\":" << stages << "}\n";
}

u32 number(const char* value) {
    const std::string text(value);
    require(!text.empty() && text.find_first_not_of("0123456789")==std::string::npos,"invalid integer");
    const auto parsed=std::stoull(text);
    require(parsed<=UINT32_MAX,"integer exceeds uint32");
    return static_cast<u32>(parsed);
}
int main(int argc, char** argv) {
    try {
        if (argc==2 && std::string(argv[1])=="--self-test") { self_test(); return 0; }
        require(argc>=4 && (argc-1)%3==0,"expected family/n/seed triples");
        std::cout << "family,n,graph_seed,stage,component_count,sum_squared_sizes,largest_component,boundary_count,"
                     "selected_edges,total_selected_edges,min_gap,max_gap,max_gap_count,distinct_gap_count\n";
        for (int i=1; i<argc; i+=3) {
            const std::string family=argv[i];
            const u32 n=number(argv[i+1]), seed=number(argv[i+2]);
            State state=generated(family,n,seed);
            u32 stage=0;
            emit(family,n,seed,stage,0,state);
            while (state.sizes.size()>1) {
                const u32 before=static_cast<u32>(state.sizes.size());
                state=step(state);
                emit(family,n,seed,++stage,before-static_cast<u32>(state.sizes.size()),state);
            }
        }
        require(static_cast<bool>(std::cout),"failed diagnostic output");
    } catch (const std::exception& error) {
        std::cerr << "line-gap diagnostic: " << error.what() << '\n'; return 1;
    }
}
'''


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_simulation(path):
    groups = {}
    for context, raw in base.read_csv(Path(path), FIELDS):
        row = dict(raw)
        base.require(row["family"] in FAMILIES, context+": unsupported line family")
        for field in FIELDS[1:]:
            if field == "distinct_gap_count" and row[field] == "na":
                continue
            row[field] = base.integer(row[field], context+" "+field)
        n, q, squares, largest = (row[f] for f in ("n","component_count","sum_squared_sizes","largest_component"))
        base.require(32 <= n <= 2**23 and n & (n-1) == 0 and row["graph_seed"] < 2**32,
                     context+": invalid simulated dimensions/seed")
        key = row["family"], n, row["graph_seed"]
        stages = groups.setdefault(key, [])
        base.require(row["stage"] == len(stages), context+": duplicate/missing/reordered stage")
        base.require(1 <= q <= n and row["boundary_count"] == q-1 and
                     row["total_selected_edges"] == n-q and 1 <= largest <= n-q+1 and q*largest >= n,
                     context+": invalid component/boundary accounting")
        a, remainder = divmod(n,q)
        balanced = (q-remainder)*a*a+remainder*(a+1)*(a+1)
        base.require(balanced <= squares <= (n-q+1)**2+q-1 and
                     largest*largest+n-largest <= squares <= largest*n and (squares-n)%2 == 0,
                     context+": impossible component moments")
        if not stages:
            base.require(q == n and squares == n and largest == 1 and row["selected_edges"] == 0,
                         context+": invalid initial state")
        else:
            previous = stages[-1]
            base.require(previous["component_count"] > 1 and q <= previous["component_count"]//2 and
                         row["selected_edges"] == previous["component_count"]-q and
                         squares >= previous["sum_squared_sizes"]+2*row["selected_edges"] and
                         largest >= previous["largest_component"], context+": invalid contraction progress")
            if previous["min_gap"] == previous["max_gap"]:
                base.require(q == 1, context+": equal remaining gaps did not merge in one round")
            if q > 1:
                base.require(row["min_gap"] > previous["min_gap"] and row["max_gap"] <= previous["max_gap"],
                             context+": boundary gaps do not form the required surviving subset")
        if q == 1:
            base.require((squares,largest) == (n*n,n) and all(row[f] == 0 for f in
                ("boundary_count","min_gap","max_gap","max_gap_count","distinct_gap_count")),
                context+": invalid terminal state")
        else:
            alphabet = 1024 if row["family"] == "line_metric" else 2**32
            base.require(1 <= row["min_gap"] <= row["max_gap"] <= alphabet and
                         1 <= row["max_gap_count"] <= q-1 and
                         (row["min_gap"] == row["max_gap"]) == (row["max_gap_count"] == q-1),
                         context+": invalid gap extrema/counts")
            if row["family"] == "line_metric":
                base.require(type(row["distinct_gap_count"]) is int and
                             1 <= row["distinct_gap_count"] <= min(1024,q-1) and
                             (row["distinct_gap_count"] == 1) == (row["min_gap"] == row["max_gap"]),
                             context+": invalid narrow distinct-gap count")
            else:
                base.require(row["distinct_gap_count"] == "na", context+": wide distinct count must be explicitly unmeasured")
        stages.append(row)
    base.require(groups and all(rows[-1]["component_count"] == 1 for rows in groups.values()),
                 "empty/incomplete line simulation")
    return groups


def compile_cpp(folder, compiler):
    source, binary = folder/"line_gap_diagnostic.cpp", folder/"line_gap_diagnostic"
    source.write_text(CPP_SOURCE)
    command = [compiler,"-std=c++17","-O2","-Wall","-Wextra","-pedantic",str(source),"-o",str(binary)]
    if platform.system() == "Darwin":
        sdk = subprocess.check_output(["xcrun","--show-sdk-path"],text=True).strip()
        command += ["-isysroot",sdk]
    result = subprocess.run(command,text=True,capture_output=True)
    if result.returncode:
        raise RuntimeError("temporary diagnostic compile failed:\n"+result.stderr)
    return binary, {"compile_command":command,"compile_stderr":result.stderr,
                    "embedded_cpp_sha256":sha(source),"binary_sha256":sha(binary),
                    "compiler_version":subprocess.check_output([compiler,"--version"],text=True)}


def run(args):
    families = tuple(args.families.split(","))
    sizes = tuple(base.integer(value,"size",2**23) for value in args.sizes.split(","))
    seeds = base.seed_bank(args.graph_seeds)
    base.require(families and len(set(families)) == len(families) and all(f in FAMILIES for f in families),
                 "invalid/repeated gap family")
    base.require(sizes and len(set(sizes)) == len(sizes) and all(n>=32 and n & (n-1)==0 for n in sizes),
                 "sizes must be distinct dyadic values in [32,2^23]")
    output = args.output.resolve()
    base.require(output.suffix == ".csv", "simulation output must end in .csv")
    metadata, log = output.with_suffix(".json"), output.with_suffix(".log")
    base.require(not any(path.exists() for path in (output,metadata,log)),"refusing to overwrite gap evidence")
    output.parent.mkdir(parents=True,exist_ok=True)
    wanted = [(family,n,seed) for family in families for n in sizes for seed in seeds]
    info = {"schema":"line_gap_simulation_v1","validation":"running","script_sha256":sha(__file__),
            "scope":"Path-only structural diagnostic. No shortcuts, no production MST solver, no runtime claims.",
            "full_graph_validation":"pending separate check against production trace/moment logs",
            "requested_graphs":[{"family":f,"n":n,"graph_seed":g} for f,n,g in wanted],
            "gap_rng":"mt19937(seed xor0x510e527f), one word per boundary; narrow1+(word%1024), wide1+word",
            "wide_distinct_count":"not measured; CSV uses na except zero at the terminal state"}
    with metadata.open("x") as stream:
        stream.write(json.dumps(info,indent=2)+"\n")
    try:
        with tempfile.TemporaryDirectory(prefix="kkt-gap-diagnostic-") as directory:
            binary, compilation = compile_cpp(Path(directory),args.compiler)
            info.update(compilation)
            command = [str(binary),*(str(value) for graph in wanted for value in graph)]
            info["command"] = command
            with output.open("x") as stdout, log.open("x") as stderr:
                result = subprocess.run(command,stdout=stdout,stderr=stderr)
            info["exit_status"] = result.returncode
            base.require(result.returncode == 0,"path diagnostic failed; partial CSV/log retained")
        groups = load_simulation(output)
        base.require(list(groups) == wanted,"simulator output differs from requested graph matrix/order")
        info.update(validation="pass",graphs=len(groups),stages=sum(map(len,groups.values())))
    except BaseException as error:
        info.update(validation="failed",error=repr(error))
        raise
    finally:
        for path,key in ((output,"output_sha256"),(log,"log_sha256")):
            if path.exists():info[key]=sha(path)
        metadata.write_text(json.dumps(info,indent=2)+"\n")
    print(f"Validated {info['graphs']} path-only graphs and {info['stages']} stages; full-graph comparison still required")


def check(args):
    simulation = load_simulation(args.simulation_csv)
    simulation_metadata = args.simulation_csv.with_suffix(".json")
    simulation_log = args.simulation_csv.with_suffix(".log")
    provenance = json.loads(simulation_metadata.read_text())
    base.require(type(provenance) is dict and provenance.get("schema") == "line_gap_simulation_v1" and
                 provenance.get("validation") == "pass" and type(provenance.get("exit_status")) is int and
                 provenance["exit_status"] == 0, "simulation capture did not complete successfully")
    base.require(provenance.get("output_sha256") == sha(args.simulation_csv) and
                 provenance.get("log_sha256") == sha(simulation_log), "simulation CSV/log changed after capture")
    base.require(provenance.get("embedded_cpp_sha256") == hashlib.sha256(CPP_SOURCE.encode()).hexdigest(),
                 "simulation used a different embedded C++ diagnostic")
    requested = [{"family":family,"n":n,"graph_seed":seed} for family,n,seed in simulation]
    base.require(provenance.get("requested_graphs") == requested and
                 type(provenance.get("graphs")) is int and provenance["graphs"] == len(simulation) and
                 type(provenance.get("stages")) is int and
                 provenance["stages"] == sum(map(len,simulation.values())),
                 "simulation metadata graph/stage matrix differs from CSV")
    cases = base.load_manifest(args.manifest)
    seeds = base.seed_bank(args.graph_seeds)
    traces = base.load_traces(args.trace_csv,cases,seeds)
    observed = moments.load_moments(args.trace_log,traces)
    diagnostics = json.loads(args.diagnostics_provenance.read_text())
    base.require(type(diagnostics) is dict and diagnostics.get("schema") == "crossover_diagnostics_v1" and
                 diagnostics.get("validation") == "pass", "full-graph diagnostics did not validate successfully")
    # The diagnostics analyzer binds these exact files to successful native
    # captures and the independently certified timing-input fingerprints. A
    # structurally plausible substituted trace is insufficient evidence here.
    for key,path in (("trace_csv",args.trace_csv),("log",args.trace_log),("manifest",args.manifest)):
        entry = diagnostics.get("inputs",{}).get(key,{})
        base.require(type(entry) is dict and entry.get("path") == str(path.resolve()) and
                     entry.get("sha256") == sha(path),
                     "full-graph diagnostics provenance does not bind the supplied "+key)
    for key,expected_count in (("case_count",len(cases)),("trace_graphs",len(traces)),
                               ("trace_stages",sum(map(len,traces.values()))),
                               ("rows_removed",0),("rows_adjusted",0)):
        base.require(type(diagnostics.get(key)) is int and diagnostics[key] == expected_count,
                     "full-graph diagnostics provenance has inconsistent "+key)
    base.require(diagnostics.get("graph_seeds") == list(seeds),
                 "full-graph diagnostics provenance graph-seed matrix differs")
    matched = []
    covered = set()
    for (case,seed), rounds in traces.items():
        spec = cases[case]
        key = spec["family"],spec["n"],seed
        if key not in simulation:
            continue
        expected = simulation[key]
        base.require(len(expected) == len(rounds)+1,f"{case}: simulator/full-graph round counts differ")
        for row,trace in zip(expected[1:],rounds):
            measured = observed[case,seed,trace["round"]]
            base.require(row["stage"] == trace["round"] and all(row[field] == measured[field] for field in
                         ("component_count","sum_squared_sizes","largest_component")) and
                         row["selected_edges"] == trace["selected_edges"] and
                         row["total_selected_edges"] == spec["n"]-row["component_count"],
                         f"{case}/{trace['round']}: path-only diagnostic differs from full-graph contraction")
        covered.add(key)
        matched.append({"case_id":case,"graph_seed":seed,"stages":len(rounds),
                        "input_fingerprint":rounds[0]["input_fingerprint"],
                        "topology_fingerprint":rounds[0]["topology_fingerprint"]})
    base.require(covered == set(simulation),"full-graph trace does not cover every simulated graph")
    result = {"schema":"line_gap_full_graph_check_v1","validation":"pass",
              "scope":"Exact agreement of counts, second moments, maxima and per-round selected counts; no runtime claim.",
              "matched_graphs":matched,"unmatched_full_graph_controls":len(traces)-len(matched),
              "simulation_metadata":str(simulation_metadata.resolve()),
              "simulation_metadata_sha256":sha(simulation_metadata),
              "simulation_log":str(simulation_log.resolve()),"simulation_log_sha256":sha(simulation_log),
              "diagnostics_provenance":str(args.diagnostics_provenance.resolve()),
              "diagnostics_provenance_sha256":sha(args.diagnostics_provenance),
              "script_sha256":sha(__file__)}
    for name in ("simulation_csv","trace_csv","trace_log","manifest"):
        path = getattr(args,name)
        result[name] = str(path.resolve()); result[name+"_sha256"] = sha(path)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x") as stream:
        stream.write(json.dumps(result,indent=2)+"\n")
    print(f"Validated exact path/full-graph moments for {len(matched)} traces; no runtime claims")


def self_test(args):
    with tempfile.TemporaryDirectory(prefix="kkt-gap-test-") as directory:
        folder=Path(directory)
        binary, compilation=compile_cpp(folder,args.compiler)
        oracle=json.loads(subprocess.check_output([str(binary),"--self-test"],text=True))
        raw=folder/"small.csv"
        raw.write_text(subprocess.check_output([str(binary),"line_metric","32","3037",
                       "line_wide_metric","32","3037"],text=True))
        groups=load_simulation(raw)
        base.require(len(groups)==2,"small simulator matrix differs")
        result={"validation":"pass",**oracle,"small_graphs":len(groups),
                "small_stages":sum(map(len,groups.values())),"compilation":compilation,
                "scope":"Independent per-vertex minimum-edge/DSU oracle versus local-maximum path transitions."}
        print(json.dumps(result,indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest="command",required=True)
    simulate=commands.add_parser("run")
    simulate.add_argument("--output",type=Path,required=True)
    simulate.add_argument("--families",default=",".join(FAMILIES))
    simulate.add_argument("--sizes",default="1048576,8388608")
    simulate.add_argument("--graph-seeds",default="3037")
    simulate.add_argument("--compiler",default="/usr/bin/clang++")
    validate=commands.add_parser("check")
    for name in ("simulation-csv","trace-csv","trace-log","manifest","diagnostics-provenance","output"):
        validate.add_argument("--"+name,type=Path,required=True)
    validate.add_argument("--graph-seeds",default="3037")
    test=commands.add_parser("self-test")
    test.add_argument("--compiler",default="/usr/bin/clang++")
    args=parser.parse_args()
    {"run":run,"check":check,"self-test":self_test}[args.command](args)


if __name__ == "__main__":
    main()
