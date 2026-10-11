// Finite-range timing fits, independent of the instrumented logical-work tests.
#include "benchmark/benchmark.h"

#include "graph_fixtures.hpp"
#include "common_graph_fixtures.hpp"
#include "mst_certificate.hpp"
#include "../kkt/kkt.hpp"
#include "../kruskal/kruskal.hpp"

#include <array>
#include <chrono>
#include <cstdint>
#include <exception>
#include <string>
#include <tuple>
#include <unordered_set>
#include <vector>

namespace {

using Graph = benchmark_fixtures::Graph;
using EdgeIds = std::unordered_set<int>;
using Clock = std::chrono::steady_clock;

constexpr std::array<unsigned int, 3> graph_seeds = {17, 42, 999};
constexpr std::array<unsigned int, 3> sampling_seeds = {0, 1, 7};
bool benchmark_failed = false;

enum class Algorithm { kkt, kruskal };

EdgeIds edge_ids(const Graph& edges) {
    EdgeIds result;
    result.reserve(edges.size());
    for (const auto& edge : edges) result.insert(std::get<3>(edge));
    return result;
}

bool valid_tree(const Graph& tree, const EdgeIds& expected,
                const std::vector<const Graph::value_type*>& by_id) {
    if (tree.size() != expected.size() || edge_ids(tree) != expected) return false;
    for (const auto& edge : tree) {
        const int id = std::get<3>(edge);
        if (id < 0 || static_cast<std::size_t>(id) >= by_id.size()) return false;
        const auto& original = *by_id[id];
        const int from = std::get<0>(edge), to = std::get<1>(edge);
        const int original_from = std::get<0>(original), original_to = std::get<1>(original);
        if (std::get<2>(edge) != std::get<2>(original) ||
            !((from == original_from && to == original_to) ||
              (from == original_to && to == original_from))) return false;
    }
    return true;
}

void fail(benchmark::State& state, const char* message) {
    benchmark_failed = true;
    state.SkipWithError(message);
}

void measure(benchmark::State& state, Algorithm algorithm,
             const std::string& family, unsigned int graph_seed, bool common_families) {
    try {
        const int n = static_cast<int>(state.range(0));
        const auto graph = common_families
            ? benchmark_common::make_graph({family, n}, graph_seed)
            : benchmark_fixtures::make_graph({family, n}, graph_seed);
        const auto oracle = kruskal(graph, n);
        benchmark_validation::certify_mst(graph, oracle, n);
        const auto expected = edge_ids(oracle);
        // Certification has established unique dense IDs and valid endpoints.
        std::vector<const Graph::value_type*> by_id(graph.size());
        for (const auto& edge : graph) by_id[std::get<3>(edge)] = &edge;

        // Each registration varies n within one fixed-density or tree family.
        // Mixing density families under a common fit would change its meaning.
        state.SetComplexityN(static_cast<std::int64_t>(n) +
                             static_cast<std::int64_t>(graph.size()));
        state.counters["vertices"] = n;
        state.counters["edges"] = static_cast<double>(graph.size());
        state.counters["graph_seed"] = graph_seed;
        state.counters["sampling_seeds"] = sampling_seeds.size();

        std::size_t iteration = 0;
        for (auto unused : state) {
            (void)unused;
            const unsigned int seed = sampling_seeds[iteration++ % sampling_seeds.size()];
            bool valid = false;
            if (algorithm == Algorithm::kkt) {
                const auto start = Clock::now();
                const auto result = [&] {
                    // Same tuple-input boundary as the diverse/large harness:
                    // conversion and temporary input destruction are included.
                    problem input(n, graph);
                    return kkt(input, seed);
                }();
                const auto finish = Clock::now();
                state.SetIterationTime(std::chrono::duration<double>(finish - start).count());
                state.PauseTiming();
                benchmark::DoNotOptimize(result);
                valid = result == expected;
                // result destruction occurs with CPU timing paused, after the
                // manual interval. Both clocks therefore exclude validation.
            } else {
                const auto start = Clock::now();
                const auto result = kruskal(graph, n);
                const auto finish = Clock::now();
                state.SetIterationTime(std::chrono::duration<double>(finish - start).count());
                state.PauseTiming();
                benchmark::DoNotOptimize(result);
                valid = valid_tree(result, expected, by_id);
            }
            if (!valid) {
                fail(state, "measured MST differs from the independently certified reference");
                break;
            }
            state.ResumeTiming();
        }
    } catch (const std::exception& error) {
        fail(state, error.what());
    }
}

void register_benchmarks(bool common_families) {
    const std::vector<const char*> families = common_families
        ? std::vector<const char*>{"unbalanced_bipartite_16", "ring_cliques_16",
              "grid3d_distance", "leaf_core_90", "regular_8"}
        : std::vector<const char*>{"random_4", "random_32", "star"};
    for (const char* family : families) {
        for (unsigned int graph_seed : graph_seeds) {
            for (Algorithm algorithm : {Algorithm::kkt, Algorithm::kruskal}) {
                const std::string algorithm_name = algorithm == Algorithm::kkt ? "KKT" : "Kruskal";
                const std::string name = algorithm_name + "/" + family + "/graph_" + std::to_string(graph_seed);
                const std::string family_name = family;
                auto* registration = benchmark::RegisterBenchmark(
                    name.c_str(), [algorithm, family_name, graph_seed, common_families](benchmark::State& state) {
                        measure(state, algorithm, family_name, graph_seed, common_families);
                    });
                for (int n = 1024; n <= (common_families ? 262144 : 65536); n *= 2) registration->Arg(n);
                registration->Iterations(sampling_seeds.size())
                    ->Repetitions(3)
                    ->UseManualTime()
                    ->Unit(benchmark::kMillisecond)
                    ->Complexity(benchmark::oAuto)
                    ->ReportAggregatesOnly(false);
            }
        }
    }
}

}  // namespace

int main(int argc, char** argv) {
    // In Google Benchmark 1.5.2, oAuto chooses a model using CPU time and then
    // fits manual/real time to that model. The validation/destruction pauses
    // keep the CPU interval comparable, but these labels are only finite-range
    // fits. Analyze exported real_time values separately for timing conclusions.
    bool common_families = false;
    for (int i = 1; i < argc; ++i) {
        if (std::string(argv[i]) == "--common") {
            common_families = true;
            for (int j = i; j + 1 < argc; ++j) argv[j] = argv[j + 1];
            argv[--argc] = nullptr;
            --i;
        }
    }
    register_benchmarks(common_families);
    benchmark::Initialize(&argc, argv);
    if (benchmark::ReportUnrecognizedArguments(argc, argv)) return 1;
    const auto matched = benchmark::RunSpecifiedBenchmarks();
    return benchmark_failed || matched == 0 ? 1 : 0;
}
