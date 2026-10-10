// Deterministic logical-work regressions. No wall-clock slopes or sampled
// averages are asserted: the randomized expected bound is not a per-seed bound.
#include "../benchmark/graph_fixtures.hpp"
#include "../benchmark/mst_certificate.hpp"
#include "../benchmark/work_metrics.hpp"
#include "../kkt/kkt.hpp"
#include "../kruskal/kruskal.hpp"
#include "../verifier/verifier_v2.hpp"

#include <gtest/gtest.h>

#include <array>
#include <cstdint>
#include <string>
#include <tuple>
#include <unordered_set>

#ifndef KKT_ENABLE_WORK_STATS
#error "complexity_test must use the instrumented KKT libraries"
#endif

namespace {
using benchmark_fixtures::Graph;
using Ids = std::unordered_set<int>;
using kkt_work::WorkStats;

Ids ids(const Graph& graph) {
    Ids result;
    for (const auto& edge : graph) result.insert(std::get<3>(edge));
    return result;
}

Ids certified_ids(const Graph& graph, int n) {
    const auto tree = kruskal(graph, n);
    benchmark_validation::certify_mst(graph, tree, n);
    return ids(tree);
}

struct Run { Ids result; WorkStats stats; };

Run collect(const Graph& graph, int n, unsigned int seed) {
    Run run;
    {
        kkt_work::ScopedWorkStats scope(run.stats);
        problem input(n, graph);
        run.result = kkt(input, seed);
    }
    return run;
}

void expect_local_bounds(const WorkStats& stats) {
    EXPECT_EQ(stats.current_depth, 0u);
    EXPECT_GT(stats.kkt_calls, 0u);
    EXPECT_GT(stats.contraction_edge_visits, 0u);
    EXPECT_GT(benchmark_work::total_work_proxy(stats), 0u);
    // Three full edge passes plus at most one bucket visit per crossing edge.
    EXPECT_LE(stats.contraction_edge_visits, 4 * stats.contraction_edges);
    EXPECT_LE(stats.contraction_arc_visits, 2 * stats.contraction_vertices);
    EXPECT_LE(stats.sampled_edges, stats.sampling_edge_visits);
    EXPECT_LE(stats.verifier_queries, 2 * stats.verifier_tree_edges);
    // Count endpoints, scatter into their contiguous ranges, then traverse
    // each query once during tree initialization and once while answering.
    EXPECT_EQ(stats.path_query_visits, 4 * stats.verifier_queries);
    // Each full-branching round at least halves the active vertex count.
    EXPECT_LE(stats.fbt_round_vertices, 2 * stats.fbt_input_vertices);
    EXPECT_LE(stats.fbt_output_vertices, 2 * stats.fbt_input_vertices);
    // A height-h full-branching tree has at least 2^h original leaves;
    // its 2^(h+1)-1 nonzero median masks therefore cost less than 2n.
    EXPECT_LE(stats.median_entries, 2 * stats.fbt_input_vertices);
}

TEST(Complexity, StarFinishesInOneContractionWithoutSamplingOrVerifier) {
    for (int n : {2, 65, 4096}) {
        SCOPED_TRACE(n);
        const auto graph = benchmark_fixtures::make_graph({"star", n}, 17);
        const auto run = collect(graph, n, 7);
        EXPECT_EQ(run.result, ids(graph)); // Every edge of a tree is required.
        EXPECT_EQ(run.stats.kkt_calls, 1u);
        EXPECT_EQ(run.stats.kkt_edges, graph.size());
        EXPECT_EQ(run.stats.contraction_calls, 1u);
        EXPECT_EQ(run.stats.contraction_edges, graph.size());
        EXPECT_EQ(run.stats.sampling_calls, 0u);
        EXPECT_EQ(run.stats.verifier_calls, 0u);
        EXPECT_EQ(run.stats.verifier_tree_calls, 0u);
        EXPECT_EQ(run.stats.median_entries, 0u);
        EXPECT_EQ(run.stats.max_depth, 1u);
        EXPECT_GE(run.stats.edge_materializations, graph.size());
        expect_local_bounds(run.stats);
    }
}

TEST(Complexity, CounterScopesRestoreTheirPreviousCollector) {
    const auto graph = benchmark_fixtures::make_graph({"star", 65}, 42);
    const auto expected = ids(graph);
    problem input(65, graph);
    WorkStats outer, inner;
    {
        kkt_work::ScopedWorkStats outer_scope(outer);
        EXPECT_EQ(kkt(input, 0), expected);
        {
            kkt_work::ScopedWorkStats inner_scope(inner);
            EXPECT_EQ(kkt(input, 1), expected);
        }
        EXPECT_EQ(kkt(input, 7), expected);
    }
    EXPECT_EQ(kkt(input, 0), expected); // Outside either collector.
    EXPECT_EQ(outer.kkt_calls, 2u);
    EXPECT_EQ(inner.kkt_calls, 1u);
    EXPECT_EQ(outer.current_depth, 0u);
    EXPECT_EQ(inner.current_depth, 0u);
    EXPECT_GT(outer.contraction_edge_visits, 0u);
    EXPECT_GT(inner.contraction_edge_visits, 0u);
}

TEST(Complexity, BillionScaleSparseEdgeIdsDoNotIncreaseAnyWorkCounter) {
    const int n = 256;
    const auto graph = benchmark_fixtures::make_graph({"random_4", n}, 42);
    const auto expected = certified_ids(graph, n);
    Graph relabeled = graph;
    const auto label = [](int id) { return 1000000000 + 104729 * id; };
    Ids relabeled_expected;
    for (int id : expected) relabeled_expected.insert(label(id));
    for (auto& edge : relabeled) std::get<3>(edge) = label(std::get<3>(edge));

    for (unsigned int seed : {0u, 1u, 7u}) {
        SCOPED_TRACE(seed);
        const auto baseline = collect(graph, n, seed);
        const auto sparse = collect(relabeled, n, seed);
        ASSERT_EQ(baseline.result, expected);
        ASSERT_EQ(sparse.result, relabeled_expected);
        for (const auto& field : benchmark_work::fields) {
            SCOPED_TRACE(field.name);
            EXPECT_EQ(baseline.stats.*field.member, sparse.stats.*field.member);
        }
    }
}

TEST(Complexity, HierarchicalPathsHaveGeometricallyBoundedRecursiveEdgeVolume) {
    for (int n : {64, 256, 1024, 4096, 16384}) {
        SCOPED_TRACE(n);
        const auto graph = benchmark_fixtures::make_graph({"hierarchical_path", n}, 17);
        const auto expected = ids(graph);
        const std::uint64_t m = graph.size();
        for (unsigned int seed : {0u, 1u, 7u}) {
            SCOPED_TRACE(seed);
            const auto run = collect(graph, n, seed);
            ASSERT_EQ(run.result, expected);
            EXPECT_GT(run.stats.sampling_calls, 0u);
            EXPECT_GT(run.stats.max_depth, 1u);
            // For a forest, two contractions leave at most m/4 edges. Each
            // recursive child has at most that many, giving W(m) <= 2m.
            EXPECT_LE(run.stats.kkt_edges, 2 * m);
            EXPECT_GE(run.stats.kkt_edges, m);
            EXPECT_LE(run.stats.contraction_edges, 3 * m);
            EXPECT_LE(run.stats.root_after_two_edges, m / 4);
            EXPECT_LE(run.stats.root_after_two_vertices, static_cast<std::uint64_t>(n / 4));
            expect_local_bounds(run.stats);
        }
    }
}

TEST(Complexity, MedianTableWorkIsBoundedByFullBranchingTreeLeaves) {
    for (int height : {4, 6, 8, 10, 12}) {
        SCOPED_TRACE(height);
        const int n = 1 << height;
        const auto tree = benchmark_fixtures::make_graph({"hierarchical_path", n}, 999);
        WorkStats stats;
        Ids heavy;
        {
            kkt_work::ScopedWorkStats scope(stats);
            heavy = verify_general_graph(tree, tree, n);
        }
        EXPECT_TRUE(heavy.empty());
        EXPECT_EQ(stats.fbt_calls, 1u);
        EXPECT_EQ(stats.lca_calls, stats.fbt_calls);
        EXPECT_GT(stats.lca_euler_entries, 0u);
        EXPECT_EQ(stats.fbt_input_vertices, static_cast<std::uint64_t>(n));
        EXPECT_EQ(stats.path_max_height, static_cast<std::uint64_t>(height));
        EXPECT_GT(stats.median_entries, static_cast<std::uint64_t>(n));
        EXPECT_LE(stats.median_entries, 2 * stats.fbt_input_vertices);
        EXPECT_LE(stats.fbt_output_vertices, 2 * stats.fbt_input_vertices - 1);
        EXPECT_LE(stats.fbt_round_vertices, 2 * stats.fbt_input_vertices);
    }
}

TEST(Complexity, InstrumentedRandomRunsMatchIndependentlyCertifiedMsts) {
    for (const auto& item : std::array<benchmark_fixtures::Case, 3>{{
             {"random_4", 128}, {"random_32", 128}, {"random_32", 1024}}}) {
        SCOPED_TRACE(item.family + " n=" + std::to_string(item.n));
        for (unsigned int graph_seed : {17u, 42u, 999u}) {
            SCOPED_TRACE(graph_seed);
            const auto graph = benchmark_fixtures::make_graph(item, graph_seed);
            // Generation, reference construction, and independent certificate
            // are deliberately outside every instrumentation scope.
            const auto expected = certified_ids(graph, item.n);
            for (unsigned int seed : {0u, 1u, 7u}) {
                SCOPED_TRACE(seed);
                const auto run = collect(graph, item.n, seed);
                EXPECT_EQ(run.result, expected);
                expect_local_bounds(run.stats);
                // Only the public result set still inserts hashed edge IDs.
                EXPECT_EQ(run.stats.hash_lookup_calls, 0u);
                EXPECT_EQ(run.stats.hash_insert_items, run.result.size());
            }
        }
    }
}
}  // namespace
