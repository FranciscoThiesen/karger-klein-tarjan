// Paired discovery/confirmation of unchanged KKT versus its own production
// contraction continued to completion. No solver dispatch uses fixture shape.
#include "continuation_fixtures.hpp"
#include "crossover_fixtures.hpp"
#include "component_moments.hpp"
#include "graph_fixtures.hpp"
#include "mst_certificate.hpp"
#include "work_metrics.hpp"
#include "../kkt/kkt.hpp"
#include "../kruskal/kruskal.hpp"

#include <algorithm>
#include <cerrno>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <system_error>
#include <time.h>
#include <unordered_set>
#include <utility>
#include <vector>

std::pair<std::vector<int>, problem> boruvka_step(const problem& input);

namespace {
using Graph = benchmark_fixtures::Graph;
using Spec = benchmark_continuation::Spec;
using Ids = std::unordered_set<int>;
constexpr const char* algorithms[] = {"kkt", "compacting_boruvka"};

void require(bool value, const std::string& message) {
    if (!value) throw std::runtime_error(message);
}

unsigned int number(const std::string& value) {
    require(!value.empty() && value.find_first_not_of("0123456789") == std::string::npos,
            "invalid unsigned integer: " + value);
    const auto result = std::stoull(value);
    require(result <= std::numeric_limits<unsigned int>::max(), "integer out of range");
    return static_cast<unsigned int>(result);
}

std::vector<std::string> split(const std::string& value) {
    std::vector<std::string> result;
    std::size_t start = 0;
    for (;;) {
        const auto end = value.find(',', start);
        result.push_back(value.substr(start, end == std::string::npos ? end : end-start));
        if (end == std::string::npos) return result;
        start = end + 1;
    }
}

std::vector<unsigned int> seeds(const std::string& value) {
    std::vector<unsigned int> result;
    for (const auto& part : split(value)) {
        const auto seed = number(part);
        require(std::find(result.begin(), result.end(), seed) == result.end(), "duplicate seed");
        result.push_back(seed);
    }
    return result;
}

struct Options {
    std::string manifest;
    std::string mode = "timing";
    std::vector<unsigned int> graph_seeds = {17, 42};
    std::vector<unsigned int> sampling_seeds = {0, 1};
    int repetitions = 2;
    int warmups = 1;
};

Options options(int argc, char** argv) {
    Options result;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        require(++i < argc, arg + " requires a value");
        const std::string value = argv[i];
        if (arg == "--manifest") result.manifest = value;
        else if (arg == "--mode") result.mode = value;
        else if (arg == "--graph-seeds") result.graph_seeds = seeds(value);
        else if (arg == "--sampling-seeds") result.sampling_seeds = seeds(value);
        else if (arg == "--repetitions" || arg == "--warmups") {
            const auto count = number(value);
            require(count <= 100, "count exceeds 100");
            if (arg == "--repetitions") result.repetitions = static_cast<int>(count);
            else result.warmups = static_cast<int>(count);
        } else throw std::runtime_error("unknown option: " + arg);
    }
    require(!result.manifest.empty(), "--manifest is required");
    require(result.repetitions >= 2 && result.repetitions % 2 == 0,
            "positive even repetitions required for balanced order");
    require(result.warmups >= 1, "at least one checked warmup required");
#ifdef KKT_ENABLE_WORK_STATS
    require(result.mode == "work", "instrumented binary supports only --mode work");
#else
    require(result.mode == "timing" || result.mode == "trace", "native mode must be timing or trace");
#endif
    return result;
}

using benchmark_continuation::case_id;

Graph fixture(const Spec& spec, unsigned int seed) {
    if (spec.family == "line_metric" || spec.family == "line_random" ||
        spec.family == "grid2d_metric" || spec.family == "grid2d_random" || spec.family == "gnm_random") {
        require(spec.intrusion_per_mille == 0, "geometric crossover fixtures require p=0");
        auto generated = benchmark_crossover::make_fixture({spec.family, spec.n, spec.density}, seed);
        std::cerr << "crossover_topology_attempts=" << generated.topology_attempts << '\n';
        return std::move(generated.graph);
    }
    if (spec.family == "legacy_random") {
        require(spec.intrusion_per_mille == 0 &&
                (spec.density == 4 || spec.density == 32 || spec.density == 128),
                "legacy_random supports densities 4,32,128 without intrusion");
        return benchmark_fixtures::make_graph({"random_" + std::to_string(spec.density), spec.n}, seed);
    }
    return benchmark_continuation::make_fixture(spec, seed).graph;
}

std::vector<Spec> load_manifest(const std::string& path) {
    std::ifstream stream(path);
    require(static_cast<bool>(stream), "cannot open manifest: " + path);
    std::string line;
    require(static_cast<bool>(std::getline(stream, line)) &&
            line == "family,n,density,intrusion_per_mille", "unexpected manifest header");
    std::vector<Spec> result;
    std::unordered_set<std::string> unique;
    while (std::getline(stream, line)) {
        const auto fields = split(line);
        require(fields.size() == 4, "manifest must contain four fields per row");
        const auto n = number(fields[1]), density = number(fields[2]), intrusion = number(fields[3]);
        const bool crossover = std::find(benchmark_crossover::families.begin(),
            benchmark_crossover::families.end(), fields[0]) != benchmark_crossover::families.end();
        require(n <= (crossover ? (1u<<23) : (1u<<22)) && density <= 512 && intrusion <= 1000,
                "manifest range exceeded");
        Spec spec{fields[0], static_cast<int>(n), static_cast<int>(density), static_cast<int>(intrusion)};
        require(n >= 32 && (n & (n-1)) == 0 && density >= 1, "invalid graph dimensions");
        require(unique.insert(case_id(spec)).second, "duplicate manifest case");
        result.push_back(spec);
    }
    require(!result.empty(), "empty manifest");
    return result;
}

Ids ids(const Graph& tree) {
    Ids result;
    result.reserve(tree.size());
    for (const auto& edge : tree) result.insert(std::get<3>(edge));
    require(result.size() == tree.size(), "reference has repeated IDs");
    return result;
}

std::uint64_t fingerprint(const Graph& graph, int n, bool include_weights) {
    std::uint64_t value = UINT64_C(14695981039346656037);
    const auto append = [&](int number) {
        const auto bits = static_cast<std::uint32_t>(number);
        for (unsigned int shift = 0; shift < 32; shift += 8) {
            value ^= (bits >> shift) & 0xffu;
            value *= UINT64_C(1099511628211);
        }
    };
    append(n);
    for (const auto& [u,v,w,id] : graph) {
        append(u);append(v);if (include_weights) append(w);append(id);
    }
    return value;
}

struct Round {
    int input_vertices;
    std::size_t input_edges;
    std::size_t selected_edges;
    int output_vertices;
    std::size_t output_edges;
    // Kept only in the untimed trace instantiation, for an independent ledger
    // over original vertices after the production contraction has completed.
    std::vector<int> selected_ids;
};

// Identical continuation/output operations to contraction_ablation.cpp.
template <bool record_trace>
Ids compacting_boruvka(problem& input, std::vector<Round>* trace = nullptr) {
    std::vector<int> selected_ids;
    while (!input.graph_edges.empty()) {
        auto [selected, reduced] = boruvka_step(input);
        selected_ids.insert(selected_ids.end(), selected.begin(), selected.end());
        if constexpr (record_trace) {
            trace->push_back({input.num_vertices, input.graph_edges.size(), selected.size(),
                              reduced.num_vertices, reduced.graph_edges.size(), std::move(selected)});
        }
        input = std::move(reduced);
    }
    Ids result;
    result.reserve(selected_ids.size());
    result.insert(selected_ids.begin(), selected_ids.end());
    KKT_WORK_ADD(hash_insert_items, selected_ids.size());
    return result;
}

#ifndef KKT_ENABLE_WORK_STATS
std::int64_t clock_nanoseconds(clockid_t clock, const char* name) {
    timespec value{};
    if (clock_gettime(clock, &value) != 0)
        throw std::system_error(errno, std::generic_category(), name);
    constexpr std::int64_t billion = 1000000000;
    require(value.tv_sec >= 0 && value.tv_nsec >= 0 && value.tv_nsec < billion &&
            value.tv_sec <= (std::numeric_limits<std::int64_t>::max() - value.tv_nsec) / billion,
            std::string(name) + ": clock value outside nanosecond range");
    return static_cast<std::int64_t>(value.tv_sec) * billion + value.tv_nsec;
}

std::int64_t measure(int algorithm, const Graph& graph, int n, unsigned int seed,
                     const Ids& expected, const std::string& case_name,
                     unsigned int graph_seed, const char* phase, int repetition, int order) {
    // These diagnostic clocks enclose the original steady-clock interval.
    // Keep their reads and all logging outside the solver timing boundary.
    const auto utc_start = clock_nanoseconds(CLOCK_REALTIME, "CLOCK_REALTIME");
    const auto cpu_start = clock_nanoseconds(CLOCK_PROCESS_CPUTIME_ID, "CLOCK_PROCESS_CPUTIME_ID");
    const auto start = std::chrono::steady_clock::now();
    const auto result = [&] {
        problem input(n, graph);
        return algorithm == 0 ? kkt(input, seed) : compacting_boruvka<false>(input);
    }();
    const auto finish = std::chrono::steady_clock::now();
    const auto cpu_finish = clock_nanoseconds(CLOCK_PROCESS_CPUTIME_ID, "CLOCK_PROCESS_CPUTIME_ID");
    const auto utc_finish = clock_nanoseconds(CLOCK_REALTIME, "CLOCK_REALTIME");
    const auto elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(finish-start).count();
    require(result == expected, std::string(algorithms[algorithm]) + ": incorrect MST IDs");
    require(elapsed > 0, "nonpositive elapsed time");
    require(cpu_finish >= cpu_start, "process CPU clock moved backward");
    // Realtime may move backward after a wall-clock correction. Retain both
    // values; the capture analyzer must report that rather than reject a row.
    std::ostringstream clock_record;
    clock_record << "call_clock_v1 {\"case_id\":" << std::quoted(case_name)
              << ",\"graph_seed\":" << graph_seed << ",\"sampling_seed\":" << seed
              << ",\"phase\":" << std::quoted(phase) << ",\"repetition\":" << repetition
              << ",\"order\":" << order << ",\"algorithm\":" << std::quoted(algorithms[algorithm])
              << ",\"utc_start_ns\":" << utc_start << ",\"utc_end_ns\":" << utc_finish
              << ",\"process_cpu_start_ns\":" << cpu_start << ",\"process_cpu_end_ns\":" << cpu_finish
              << ",\"process_cpu_elapsed_ns\":" << cpu_finish-cpu_start
              << ",\"steady_elapsed_ns\":" << elapsed << ",\"validation\":\"pass\"}\n";
    std::cerr << clock_record.str();
    require(static_cast<bool>(std::cerr), "failed writing call clock record");
    return elapsed;
}
#endif

void prefix(const Spec& spec, std::size_t m, unsigned int graph_seed, std::uint64_t hash, std::uint64_t topology_hash) {
    std::cout << case_id(spec) << ',' << spec.family << ',' << spec.n << ',' << m
              << ',' << spec.density << ',' << spec.intrusion_per_mille << ',' << graph_seed << ',' << hash
              << ',' << topology_hash;
}

void run(const Options& config) {
    const auto cases = load_manifest(config.manifest);
    std::cout << "case_id,family,n,m,density,intrusion_per_mille,graph_seed,input_fingerprint,topology_fingerprint";
    if (config.mode == "timing")
        std::cout << ",kkt_seed,repetition,order,warmups,algorithm,elapsed_ns,validation\n";
    else if (config.mode == "trace")
        std::cout << ",round,input_vertices,input_edges,selected_edges,output_vertices,output_edges,total_rounds,total_selected_edges,validation\n";
    else {
        std::cout << ",kkt_seed,algorithm";
        for (const auto& field : benchmark_work::fields) std::cout << ',' << field.name;
        std::cout << ",total_work_proxy,validation\n";
    }
    for (const auto& spec : cases) {
        for (std::size_t g=0; g<config.graph_seeds.size(); ++g) {
            const auto graph_seed = config.graph_seeds[g];
            std::cerr << config.mode << ' ' << case_id(spec) << " graph_seed=" << graph_seed << '\n';
            const auto setup_start = std::chrono::steady_clock::now();
            const auto graph = fixture(spec, graph_seed);
            const auto generated = std::chrono::steady_clock::now();
            require(graph.size() == static_cast<std::size_t>(spec.density)*spec.n, "unexpected edge count");
            const auto oracle = kruskal(graph, spec.n);
            benchmark_validation::certify_mst(graph, oracle, spec.n);
            const auto expected = ids(oracle);
            const auto certified = std::chrono::steady_clock::now();
            std::cerr << "setup_generation_ms="
                      << std::chrono::duration_cast<std::chrono::milliseconds>(generated-setup_start).count()
                      << " setup_reference_and_certificate_ms="
                      << std::chrono::duration_cast<std::chrono::milliseconds>(certified-generated).count()
                      << '\n';
            if (spec.family != "legacy_random" && spec.family != "line_metric" &&
                spec.family != "line_random" && spec.family != "grid2d_metric" &&
                spec.family != "grid2d_random" && spec.family != "gnm_random") {
                const auto backbone_edges = std::count_if(expected.begin(), expected.end(),
                    [&](int id) { return id < spec.n - 1; });
                std::cerr << "certified_mst_backbone_edges=" << backbone_edges
                          << " total=" << expected.size() << '\n';
            }
            const auto hash = fingerprint(graph, spec.n, true);
            const auto topology_hash = fingerprint(graph, spec.n, false);
#ifndef KKT_ENABLE_WORK_STATS
            if (config.mode == "trace") {
                std::vector<Round> trace;
                problem input(spec.n, graph);
                const auto result = compacting_boruvka<true>(input, &trace);
                require(result == expected, "trace result differs from certified MST");
                std::size_t selected_total = 0;
                for (const auto& r : trace) {
                    selected_total += r.selected_edges;
                    require(r.selected_edges > 0 && r.output_vertices <= r.input_vertices/2 &&
                            r.output_edges < r.input_edges, "invalid contraction progress");
                }
                require(selected_total == expected.size(), "trace selected count mismatch");
                benchmark_diagnostics::ComponentMoments moments(graph, spec.n);
                for (std::size_t i=0; i<trace.size(); ++i) {
                    const auto& r = trace[i];
                    moments.accept_selected(r.selected_ids);
                    require(moments.count() == (r.output_vertices ? r.output_vertices : 1),
                            "original-component ledger disagrees with contraction");
                    std::cerr << "component_moments_v1 {\"case_id\":" << std::quoted(case_id(spec))
                              << ",\"graph_seed\":" << graph_seed << ",\"round\":" << i+1
                              << ",\"n\":" << spec.n << ",\"component_count\":" << moments.count()
                              << ",\"sum_squared_sizes\":" << moments.sum_squares()
                              << ",\"largest_component\":" << moments.max_size()
                              << ",\"validation\":\"pass\"}\n";
                    prefix(spec, graph.size(), graph_seed, hash, topology_hash);
                    std::cout << ',' << i+1 << ',' << r.input_vertices << ',' << r.input_edges
                              << ',' << r.selected_edges << ',' << r.output_vertices << ',' << r.output_edges
                              << ',' << trace.size() << ',' << selected_total << ",pass\n";
                }
            } else
#endif
            {
                for (std::size_t s=0; s<config.sampling_seeds.size(); ++s) {
                    const auto seed = config.sampling_seeds[s];
#ifdef KKT_ENABLE_WORK_STATS
                    for (int a=0; a<2; ++a) {
                        // Deterministic compaction is recorded once per graph.
                        if (a == 1 && s != 0) continue;
                        kkt_work::WorkStats stats;
                        Ids result;
                        {
                            kkt_work::ScopedWorkStats scope(stats);
                            problem input(spec.n, graph);
                            result = a == 0 ? kkt(input, seed) : compacting_boruvka<false>(input);
                        }
                        require(result == expected, "work result differs from certified MST");
                        require(stats.current_depth == 0 && stats.contraction_calls > 0 &&
                                stats.contraction_edges >= graph.size() &&
                                stats.filtered_edges <= stats.verifier_edges, "invalid work counters");
                        if (a == 0) require(stats.sampling_calls == stats.verifier_calls &&
                                            stats.sampling_edge_visits == stats.verifier_edges,
                                            "sampling/verifier work mismatch");
                        else require(stats.kkt_calls == 0 && stats.verifier_calls == 0,
                                     "compactor unexpectedly sampled or verified");
                        prefix(spec, graph.size(), graph_seed, hash, topology_hash);
                        std::cout << ',' << (a == 0 ? std::to_string(seed) : "na") << ',' << algorithms[a];
                        for (const auto& field : benchmark_work::fields) std::cout << ',' << stats.*field.member;
                        std::cout << ',' << benchmark_work::total_work_proxy(stats) << ",pass\n";
                    }
#else
                    for (int w=0; w<config.warmups; ++w)
                        for (int order=0; order<2; ++order)
                            measure((order+w+static_cast<int>(g+s))%2, graph, spec.n, seed, expected,
                                    case_id(spec), graph_seed, "warmup", w, order);
                    for (int rep=0; rep<config.repetitions; ++rep) {
                        for (int order=0; order<2; ++order) {
                            const int a = (order+rep+static_cast<int>(g+s))%2;
                            const auto elapsed = measure(a, graph, spec.n, seed, expected,
                                                         case_id(spec), graph_seed, "timed", rep, order);
                            prefix(spec, graph.size(), graph_seed, hash, topology_hash);
                            std::cout << ',' << seed << ',' << rep << ',' << order << ',' << config.warmups
                                      << ',' << algorithms[a] << ',' << elapsed << ",pass\n";
                        }
                    }
#endif
                }
            }
            std::cout.flush();
            require(static_cast<bool>(std::cout), "failed writing output");
        }
    }
}
} // namespace

int main(int argc, char** argv) {
    if (argc == 2 && std::string(argv[1]) == "--help") {
        std::cout << "Usage: continuation_search --manifest FILE [--mode timing|trace|work]\n"
                     " [--graph-seeds 17,42] [--sampling-seeds 0,1] [--repetitions 2] [--warmups 1]\n"
                     "Manifest header: family,n,density,intrusion_per_mille\n"
                     "Timing/trace require the native binary; work requires continuation_search_work.\n"
                     "Even repetitions balance order; every call matches an independently certified MST.\n";
        return 0;
    }
    try { run(options(argc, argv)); }
    catch (const std::exception& error) {
        std::cerr << "continuation search: " << error.what() << '\n';
        return 1;
    }
    return 0;
}
