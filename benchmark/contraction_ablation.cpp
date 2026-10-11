// Isolate the net cost of KKT sampling/filtering versus continuing the same
// production contraction. This is not the repository's older Boruvka baseline.
// Both algorithms consume the same tuple-input boundary and construct the same
// reserved unordered_set output. --work records an untimed contraction trace;
// it is not an instrumented runtime measurement or a KKT recursion trace.
#include "common_graph_fixtures.hpp"
#include "extended_graph_fixtures.hpp"
#include "mst_certificate.hpp"
#include "../kkt/kkt.hpp"
#include "../kruskal/kruskal.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_set>
#include <utility>
#include <vector>

// Link exactly the production implementation, also exercised by contraction_test.
std::pair<std::vector<int>, problem> boruvka_step(const problem& input);

namespace {

using benchmark_fixtures::Case;
using benchmark_fixtures::Graph;
using Ids = std::unordered_set<int>;
using Clock = std::chrono::steady_clock;
constexpr std::array<const char*, 2> algorithms = {"kkt", "compacting_boruvka"};
constexpr std::array<unsigned int, 3> graph_seeds = {17, 42, 999};
constexpr std::array<unsigned int, 3> sampling_seeds = {0, 1, 7};

struct Options {
    bool smoke = false;
    bool work = false;
    int repetitions = 4;
    int warmups = 1;
    std::string case_filter;
    int graph_seed_filter = -1;
    int kkt_seed_filter = -1;
};

int count(const std::string& value, bool allow_zero) {
    std::size_t used = 0;
    const auto result = std::stoll(value, &used);
    if (used != value.size() || result < (allow_zero ? 0 : 1) || result > 1000)
        throw std::runtime_error("invalid count: " + value);
    return static_cast<int>(result);
}

Options options(int argc, char** argv) {
    Options result;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--smoke") result.smoke = true;
        else if (arg == "--scale") result.smoke = false;
        else if (arg == "--work") result.work = true;
        else if (arg == "--case") {
            if (++i == argc) throw std::runtime_error(arg + " requires a case ID");
            result.case_filter = argv[i];
        } else if (arg == "--graph-seed" || arg == "--kkt-seed") {
            if (++i == argc) throw std::runtime_error(arg + " requires a seed");
            const int seed = count(argv[i], true);
            const auto& bank = arg == "--graph-seed" ? graph_seeds : sampling_seeds;
            if (std::find(bank.begin(), bank.end(), static_cast<unsigned int>(seed)) == bank.end())
                throw std::runtime_error("unsupported seed for " + arg + ": " + argv[i]);
            if (arg == "--graph-seed") result.graph_seed_filter = seed;
            else result.kkt_seed_filter = seed;
        } else if (arg == "--repetitions" || arg == "--warmups") {
            if (++i == argc) throw std::runtime_error(arg + " requires a count");
            const int value = count(argv[i], arg == "--warmups");
            if (arg == "--repetitions") result.repetitions = value;
            else result.warmups = value;
        } else throw std::runtime_error("unknown argument: " + arg);
    }
    if (result.work && result.kkt_seed_filter >= 0)
        throw std::runtime_error("--work is a deterministic contraction trace; it has no KKT seed");
    return result;
}

std::vector<Case> cases(bool smoke) {
    std::vector<Case> result;
    const auto sizes = smoke ? std::vector<int>{64, 256}
                             : std::vector<int>{4096, 65536, 262144};
    for (const char* family : {"unbalanced_bipartite_16", "ring_cliques_16",
                              "grid3d_distance", "leaf_core_90", "regular_8", "random_4"}) {
        for (int n : sizes) {
            // A six-vertex core cannot contain the prescribed 4c simple edges.
            if (std::string(family) == "leaf_core_90" && n == 64) continue;
            result.push_back({family, n});
        }
    }
    // The unchanged extended fixture supports no 262,144-vertex small-world case.
    for (int n : (smoke ? std::vector<int>{256} : std::vector<int>{4096, 65536}))
        result.push_back({"small_world", n});
    std::mt19937 order_rng(20261012);
    for (std::size_t i = result.size(); i > 1; --i)
        std::swap(result[i - 1], result[order_rng() % i]);
    return result;
}

Graph make_fixture(const Case& item, unsigned int seed) {
    return item.family == "small_world" ? benchmark_extended::make_graph(item, seed)
                                         : benchmark_common::make_graph(item, seed);
}

Ids ids(const Graph& tree) {
    Ids result;
    result.reserve(tree.size());
    for (const auto& edge : tree) result.insert(std::get<3>(edge));
    return result;
}

struct ContractionRound {
    int input_vertices;
    std::size_t input_edges;
    std::size_t selected_edges;
    int output_vertices;
    std::size_t output_edges;
};

template <bool record_trace>
Ids compacting_boruvka(problem& input, std::vector<ContractionRound>* trace = nullptr) {
    std::vector<int> selected_ids;
    while (!input.graph_edges.empty()) {
        auto [selected, reduced] = boruvka_step(input);
        selected_ids.insert(selected_ids.end(), selected.begin(), selected.end());
        if constexpr (record_trace) {
            trace->push_back({input.num_vertices, input.graph_edges.size(), selected.size(),
                              reduced.num_vertices, reduced.graph_edges.size()});
        }
        input = std::move(reduced);
    }
    // Match kkt()'s public output construction exactly, including its lack of
    // selected_ids reserve. No intermediate MST algorithm or new fast path.
    Ids result;
    result.reserve(selected_ids.size());
    result.insert(selected_ids.begin(), selected_ids.end());
    return result;
}

std::int64_t measure(int algorithm, const Graph& graph, int n, unsigned int seed,
                     const Ids& expected) {
    const auto start = Clock::now();
    const auto result = [&] {
        problem input(n, graph);
        return algorithm == 0 ? kkt(input, seed) : compacting_boruvka<false>(input);
    }();
    const auto finish = Clock::now();
    const auto elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(finish - start).count();
    // Exact equality transfers the independent unique-MST certificate. Checking
    // the result and destroying it both occur after the finish timestamp.
    if (result != expected)
        throw std::runtime_error(std::string(algorithms[algorithm]) + ": incorrect MST IDs");
    if (elapsed <= 0) throw std::runtime_error("nonpositive elapsed time");
    return elapsed;
}

// Same FNV-1a input encoding as common_work: n then ordered tuple fields, each
// represented by four little-endian bytes. This is provenance, not a certificate.
std::uint64_t fingerprint(const Graph& graph, int n) {
    std::uint64_t value = UINT64_C(14695981039346656037);
    const auto append = [&](int number) {
        const auto bits = static_cast<std::uint32_t>(number);
        for (unsigned int shift = 0; shift < 32; shift += 8) {
            value ^= (bits >> shift) & 0xffu;
            value *= UINT64_C(1099511628211);
        }
    };
    append(n);
    for (const auto& [from, to, cost, id] : graph) {
        append(from); append(to); append(cost); append(id);
    }
    return value;
}

void write_trace(const Case& item, unsigned int graph_seed, const Graph& graph,
                 const Ids& expected) {
    const std::string case_id = item.family + "_n" + std::to_string(item.n);
    std::vector<ContractionRound> trace;
    problem input(item.n, graph);
    const auto result = compacting_boruvka<true>(input, &trace);
    std::size_t total_selected = 0;
    for (const auto& round : trace) {
        total_selected += round.selected_edges;
        if (round.selected_edges == 0 || round.output_vertices > round.input_vertices / 2 ||
            round.output_edges >= round.input_edges)
            throw std::runtime_error(case_id + ": invalid contraction progress");
    }
    if (result != expected || total_selected != expected.size() || trace.empty())
        throw std::runtime_error(case_id + ": contraction trace differs from certified MST");
    const auto input_fingerprint = fingerprint(graph, item.n);
    for (std::size_t i = 0; i < trace.size(); ++i) {
        const auto& round = trace[i];
        std::cout << case_id << ',' << item.family << ',' << item.n << ',' << graph.size()
                  << ',' << graph_seed << ",compacting_boruvka," << i + 1
                  << ',' << round.input_vertices << ',' << round.input_edges
                  << ',' << round.selected_edges << ',' << round.output_vertices
                  << ',' << round.output_edges << ',' << trace.size() << ',' << total_selected
                  << ',' << input_fingerprint << ",pass\n";
    }
}

void run(const Options& config) {
    if (config.work) {
        std::cout << "case_id,family,n,m,graph_seed,algorithm,round,input_vertices,input_edges,selected_edges,output_vertices,output_edges,total_rounds,total_selected_edges,input_fingerprint,validation\n";
    } else {
        std::cout << "case_id,family,n,m,graph_seed,kkt_seed,repetition,order,warmups,algorithm,elapsed_ns,validation\n";
    }
    bool found_case = false;
    for (const auto& item : cases(config.smoke)) {
        const std::string case_id = item.family + "_n" + std::to_string(item.n);
        if (!config.case_filter.empty() && config.case_filter != case_id) continue;
        found_case = true;
        for (std::size_t g = 0; g < graph_seeds.size(); ++g) {
            const auto graph_seed = graph_seeds[g];
            if (config.graph_seed_filter >= 0 &&
                graph_seed != static_cast<unsigned int>(config.graph_seed_filter)) continue;
            std::cerr << (config.work ? "Tracing " : "Running ") << case_id
                      << " graph_seed=" << graph_seed << '\n';
            const auto graph = make_fixture(item, graph_seed);
            const auto oracle = kruskal(graph, item.n);
            benchmark_validation::certify_mst(graph, oracle, item.n);
            const auto expected = ids(oracle);
            if (config.work) {
                write_trace(item, graph_seed, graph, expected);
            } else {
                for (std::size_t s = 0; s < sampling_seeds.size(); ++s) {
                    const auto seed = sampling_seeds[s];
                    if (config.kkt_seed_filter >= 0 &&
                        seed != static_cast<unsigned int>(config.kkt_seed_filter)) continue;
                    for (int w = 0; w < config.warmups; ++w) {
                        for (int order = 0; order < 2; ++order) {
                            const int algorithm = (order + w + static_cast<int>(g + s)) % 2;
                            measure(algorithm, graph, item.n, seed, expected);
                        }
                    }
                    for (int repetition = 0; repetition < config.repetitions; ++repetition) {
                        for (int order = 0; order < 2; ++order) {
                            const int algorithm = (order + repetition + static_cast<int>(g + s)) % 2;
                            const auto elapsed = measure(algorithm, graph, item.n, seed, expected);
                            std::cout << case_id << ',' << item.family << ',' << item.n << ',' << graph.size()
                                      << ',' << graph_seed << ',' << seed << ',' << repetition << ',' << order
                                      << ',' << config.warmups << ',' << algorithms[algorithm]
                                      << ',' << elapsed << ",pass\n";
                        }
                        std::cout.flush();
                        if (!std::cout) throw std::runtime_error("failed to write CSV");
                    }
                }
            }
            std::cout.flush();
            if (!std::cout) throw std::runtime_error("failed to write CSV");
        }
    }
    if (!found_case) throw std::runtime_error("unknown case ID: " + config.case_filter);
}

}  // namespace

int main(int argc, char** argv) {
    if (argc == 2 && std::string(argv[1]) == "--help") {
        std::cout << "Usage: " << argv[0] << " [--scale|--smoke] [--work] [--case ID]\n"
                  << "       [--graph-seed 17|42|999] [--kkt-seed 0|1|7] [--repetitions N] [--warmups N]\n"
                  << "Default: 20 cases, 3 graph seeds, 3 KKT seeds, 4 repetitions, 1 warmup per algorithm.\n"
                  << "Six common families at n=4096,65536,262144; small_world only n=4096,65536.\n"
                  << "Compacting Boruvka is deterministic; its KKT seed labels identify repeated matched trials.\n"
                  << "--smoke: 12 cases at n=64,256, with leaf_core_90 and small_world only n=256.\n"
                  << "--work: untimed per-round compacting-Boruvka trace, once per graph; no sampling seeds, warmups, or repeats.\n"
                  << "CSV goes to stdout; progress goes to stderr.\n";
        return 0;
    }
    try { run(options(argc, argv)); }
    catch (const std::exception& error) {
        std::cerr << "contraction ablation: " << error.what() << '\n';
        return 1;
    }
    return 0;
}
