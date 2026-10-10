// Untimed family diagnosis using the exact shared benchmark generators.
// Compile this file and all KKT/verifier/LCA translation units with
// KKT_ENABLE_WORK_STATS; add the repository root to the include path and link
// the existing KKT, verifier, LCA, Kruskal, and UnionFind implementations.
// No clocks are read. Output: 162 CSV rows; progress goes to stderr.
//
// The independent certificate validates one reference MST per generated graph;
// exact ID equality transfers that certificate to each KKT result. Every graph
// has unique weights, so its certified MST edge set is unique.
//
// All raw counters cover one complete KKT invocation, including input tuple
// conversion. They aggregate all recursion levels. Derived light/heavy volumes
// are edge incidences across verifier calls, not distinct original edges.
// Observed heavy removal demonstrates sampling/filtering activity, not a
// causal runtime advantage over a version with no sampling.

#include "benchmark/graph_fixtures.hpp"
#include "benchmark/mst_certificate.hpp"
#include "benchmark/work_metrics.hpp"
#include "kkt/kkt.hpp"
#include "kruskal/kruskal.hpp"

#include <array>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_set>

#ifndef KKT_ENABLE_WORK_STATS
#error "family_work requires instrumented KKT/verifier/LCA translation units"
#endif

namespace {

using benchmark_fixtures::Case;
using benchmark_fixtures::Graph;
using Ids = std::unordered_set<int>;
constexpr std::array<const char*, 6> families = {
    "hub", "star", "clustered", "random_4", "random_32", "geometric_grid"};
constexpr std::array<int, 3> sizes = {1024, 16384, 65536};
constexpr std::array<unsigned int, 3> graph_seeds = {17, 42, 999};
constexpr std::array<unsigned int, 3> sampling_seeds = {0, 1, 7};

void require(bool value, const std::string& message) {
    if (!value) throw std::runtime_error(message);
}

Ids ids(const Graph& tree) {
    Ids result;
    result.reserve(tree.size());
    for (const auto& edge : tree) result.insert(std::get<3>(edge));
    require(result.size() == tree.size(), "reference contains repeated IDs");
    return result;
}

// FNV-1a over n followed by ordered (from,to,cost,id) tuples, each encoded as
// four little-endian bytes. This records input order as well as graph content.
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

double ratio(std::uint64_t numerator, std::uint64_t denominator) {
    return denominator == 0 ? 0.0 :
        static_cast<double>(numerator) / static_cast<double>(denominator);
}

const char* regime(const kkt_work::WorkStats& stats) {
    if (stats.sampling_calls != 0)
        return stats.filtered_edges < stats.verifier_edges
            ? "sampling_with_heavy_removal" : "sampling_without_heavy_removal";
    if (stats.contraction_calls == 1) return "one_boruvka_round";
    if (stats.contraction_calls == 2) return "two_boruvka_rounds";
    throw std::runtime_error("nonempty fixture has an inconsistent no-sampling regime");
}

void check_counters(const kkt_work::WorkStats& stats, std::uint64_t m,
                    int n, const std::string& context) {
    require(stats.kkt_calls != 0 && stats.contraction_calls != 0 &&
                stats.contraction_edge_visits != 0 && stats.current_depth == 0,
            context + ": missing or unbalanced instrumentation");
    require(stats.kkt_edges >= m && stats.kkt_vertices >= static_cast<std::uint64_t>(n),
            context + ": recursive volumes exclude the root input");
    require(stats.sampling_calls == stats.verifier_calls &&
                stats.sampling_edge_visits == stats.verifier_edges,
            context + ": sampled and verified graph volumes disagree");
    require(stats.sampled_edges <= stats.sampling_edge_visits &&
                stats.filtered_edges <= stats.verifier_edges,
            context + ": sampled or light edge volume exceeds its input");
    if (stats.sampling_calls == 0) {
        require(stats.kkt_calls == 1 && stats.verifier_edges == 0 &&
                    stats.filtered_edges == 0 && stats.root_after_two_edges == 0,
                context + ": no-sampling execution unexpectedly recursed or filtered");
    } else {
        require(stats.root_after_two_vertices > 0 && stats.root_after_two_edges > 0,
                context + ": sampling did not follow a nonempty root contraction");
    }
}

void run() {
    std::cout << std::setprecision(17);
    std::cout << "case_id,family,n,m,graph_seed,kkt_seed,input_fingerprint,regime";
    for (const auto& field : benchmark_work::fields) std::cout << ',' << field.name;
    std::cout << ",light_edge_incidences,heavy_edge_incidences"
                 ",recursive_vertex_volume,recursive_edge_volume"
                 ",all_kkt_vertices_over_n,all_kkt_edges_over_m"
                 ",root_after_two_edges_over_m,sample_retention_fraction"
                 ",light_fraction,heavy_fraction,total_work_proxy,validation\n";

    std::size_t rows = 0;
    for (const char* family : families) {
        for (int n : sizes) {
            const Case item{family, n};
            const std::string case_id = item.family + "_n" + std::to_string(n);
            for (unsigned int graph_seed : graph_seeds) {
                std::cerr << "Counting " << case_id << " graph_seed=" << graph_seed << '\n';
                const Graph graph = benchmark_fixtures::make_graph(item, graph_seed);
                const auto oracle = kruskal(graph, n);
                benchmark_validation::certify_mst(graph, oracle, n);
                const auto expected = ids(oracle);
                const auto input_fingerprint = fingerprint(graph, n);
                const auto m = static_cast<std::uint64_t>(graph.size());

                for (unsigned int sampling_seed : sampling_seeds) {
                    const auto context = case_id + ", graph seed " +
                        std::to_string(graph_seed) + ", KKT seed " +
                        std::to_string(sampling_seed);
                    kkt_work::WorkStats stats;
                    Ids actual;
                    {
                        kkt_work::ScopedWorkStats scope(stats);
                        problem input(n, graph);
                        actual = kkt(input, sampling_seed);
                    }
                    require(actual == expected, context + ": KKT differs from certified MST IDs");
                    check_counters(stats, m, n, context);
                    const auto heavy_edges = stats.verifier_edges - stats.filtered_edges;
                    std::cout << case_id << ',' << item.family << ',' << n << ',' << m
                              << ',' << graph_seed << ',' << sampling_seed
                              << ',' << input_fingerprint << ',' << regime(stats);
                    for (const auto& field : benchmark_work::fields)
                        std::cout << ',' << stats.*field.member;
                    std::cout << ',' << stats.filtered_edges << ',' << heavy_edges
                              << ',' << stats.kkt_vertices - static_cast<std::uint64_t>(n)
                              << ',' << stats.kkt_edges - m
                              << ',' << ratio(stats.kkt_vertices, n)
                              << ',' << ratio(stats.kkt_edges, m)
                              << ',' << ratio(stats.root_after_two_edges, m)
                              << ',' << ratio(stats.sampled_edges, stats.sampling_edge_visits)
                              << ',' << ratio(stats.filtered_edges, stats.verifier_edges)
                              << ',' << ratio(heavy_edges, stats.verifier_edges)
                              << ',' << benchmark_work::total_work_proxy(stats)
                              << ",pass_certified_oracle_exact_ids\n";
                    ++rows;
                }
                // Preserve each complete graph-seed block if a later one fails.
                std::cout.flush();
                require(static_cast<bool>(std::cout), "failed writing diagnostic CSV");
            }
        }
    }
    require(rows == 162, "diagnostic matrix is incomplete");
    std::cerr << "Validated " << rows << " untimed observations from 54 certified graphs.\n"
              << "Light/heavy counts sum verifier incidences across recursion. Fractions with\n"
              << "no verifier input are zero; use regime to distinguish contraction collapse.\n";
}

}  // namespace

int main(int argc, char**) {
    try {
        require(argc == 1, "family_work takes no arguments; writes the fixed 162-row matrix to stdout");
        run();
    } catch (const std::exception& error) {
        std::cerr << "family work: " << error.what() << '\n';
        return 1;
    }
    return 0;
}
