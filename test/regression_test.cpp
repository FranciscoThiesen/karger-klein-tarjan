// Deterministic correctness regressions; no external test framework or timings.
#include "../kkt/kkt.hpp"
#include "../kruskal/kruskal.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_set>
#include <vector>

namespace {

using GraphEdge = std::tuple<int, int, int, int>;
using Graph = std::vector<GraphEdge>;
using EdgeIds = std::unordered_set<int>;

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

void require_same_ids(const EdgeIds& actual, const EdgeIds& expected,
                      const std::string& context) {
    if (actual == expected) return;

    std::string detail = context + ": expected " + std::to_string(expected.size()) +
                         " edges, got " + std::to_string(actual.size());
    for (int id : expected) {
        if (actual.count(id) == 0) {
            detail += "; missing ID " + std::to_string(id);
            break;
        }
    }
    for (int id : actual) {
        if (expected.count(id) == 0) {
            detail += "; unexpected ID " + std::to_string(id);
            break;
        }
    }
    throw std::runtime_error(detail);
}

std::vector<Edge> as_edges(const Graph& graph) {
    std::vector<Edge> edges;
    edges.reserve(graph.size());
    for (const auto& edge : graph) edges.emplace_back(edge);
    return edges;
}

EdgeIds kruskal_ids(const Graph& graph, int n) {
    EdgeIds ids;
    for (const auto& edge : kruskal(graph, n)) ids.insert(std::get<3>(edge));
    return ids;
}

void check_problem(problem input, const EdgeIds& expected,
                   const std::string& context) {
    const auto original_edges = input.graph_edges;
    const auto original_max_id = input.max_edge_id;
    const int original_vertices = input.num_vertices;
    for (unsigned int seed : {0u, 1u, 7u, 42u,
                              std::numeric_limits<unsigned int>::max()}) {
        require_same_ids(kkt(input, seed), expected,
                         context + ", seed " + std::to_string(seed));
        require(input.graph_edges == original_edges &&
                    input.max_edge_id == original_max_id &&
                    input.num_vertices == original_vertices,
                context + ": KKT modified its input");
    }
}

// Exact edge-set equality is meaningful because all fixture weights are unique.
void check_constructors(const Graph& graph, int n, const std::string& context) {
    const auto expected = kruskal_ids(graph, n);
    check_problem(problem(n, graph), expected, context + ", tuples");
    check_problem(problem(n, as_edges(graph)), expected, context + ", Edge vector");
    // Legacy metadata must not control result storage or ID lookups.
    check_problem(problem(n, as_edges(graph), 0), expected,
                  context + ", zero legacy max ID");
    check_problem(problem(n, as_edges(graph), std::numeric_limits<std::int64_t>::max()),
                  expected, context + ", oversized legacy max ID");
}

enum class IdLayout { dense, sparse, signed_extremes };

Graph with_ids(Graph graph, IdLayout layout) {
    for (std::size_t i = 0; i < graph.size(); ++i) {
        int id = static_cast<int>(i);
        if (layout == IdLayout::sparse) {
            id = std::numeric_limits<int>::max() - static_cast<int>(i) * 100003;
        } else if (layout == IdLayout::signed_extremes) {
            if (i == 0) id = std::numeric_limits<int>::max();
            else if (i == 1) id = std::numeric_limits<int>::min();
            else if (i == 2) id = -1;
            else if (i == 3) id = 0;
            else id = (i % 2 == 0 ? 1 : -1) * static_cast<int>(i) * 100003;
        }
        std::get<3>(graph[i]) = id;
    }
    return graph;
}

void check_id_layouts(const Graph& graph, int n, const std::string& context) {
    check_constructors(with_ids(graph, IdLayout::dense), n, context + ", dense IDs");
    check_constructors(with_ids(graph, IdLayout::sparse), n, context + ", sparse IDs");
    check_constructors(with_ids(graph, IdLayout::signed_extremes), n,
                       context + ", signed boundary IDs");
}

Graph hierarchical_path(int n) {
    Graph graph;
    for (int i = 1; i < n; ++i) {
        int level = 0;
        for (int j = i; j % 2 == 0; j /= 2) ++level;
        // Each Boruvka round joins neighboring pairs. The path therefore
        // survives repeated contractions, and every original edge is required.
        graph.emplace_back(i - 1, i, level * n + i, i - 1);
    }
    return graph;
}

void append_component(Graph& graph, int first, int count, int edge_count,
                      std::mt19937& rng) {
    for (int i = 1; i < count; ++i) {
        graph.emplace_back(first + i, first + static_cast<int>(rng() % i), 0, 0);
    }
    for (int i = count - 1; i < edge_count; ++i) {
        int from = static_cast<int>(rng() % count);
        int to = static_cast<int>(rng() % (count - 1));
        if (to >= from) ++to;
        graph.emplace_back(first + from, first + to, 0, 0);
    }
}

void assign_unique_weights(Graph& graph, std::mt19937& rng) {
    std::vector<int> weights(graph.size());
    std::iota(weights.begin(), weights.end(), 1);
    std::shuffle(weights.begin(), weights.end(), rng);
    for (std::size_t i = 0; i < graph.size(); ++i) std::get<2>(graph[i]) = weights[i];
    std::shuffle(graph.begin(), graph.end(), rng);
}

void test_id_metadata() {
    const Graph graph = {{0, 1, 1, std::numeric_limits<int>::max()}};
    const std::int64_t expected_max =
        static_cast<std::int64_t>(std::numeric_limits<int>::max()) + 1;
    require(problem(2, graph).max_edge_id == expected_max,
            "tuple constructor overflowed max edge ID");
    require(problem(2, as_edges(graph)).max_edge_id == expected_max,
            "Edge constructor overflowed max edge ID");
    check_id_layouts(graph, 2, "single edge selected by both endpoints");
}

void test_empty_graphs() {
    check_constructors(Graph{}, 0, "empty graph");
    check_constructors(Graph{}, 9, "isolated vertices");
}

void test_recursive_paths() {
    for (int n : {16, 65, 256}) {
        auto graph = hierarchical_path(n);
        std::mt19937 rng(static_cast<unsigned int>(n));
        std::shuffle(graph.begin(), graph.end(), rng);
        check_id_layouts(graph, n, "hierarchical path n=" + std::to_string(n));
    }
}

void test_random_graphs() {
    std::mt19937 rng(20261009);
    for (int n : {3, 17, 64, 129}) {
        Graph graph;
        append_component(graph, 0, n, n * 6, rng);
        assign_unique_weights(graph, rng);
        check_id_layouts(graph, n, "connected graph n=" + std::to_string(n));
    }
}

void test_disconnected_graphs() {
    std::mt19937 rng(8675309);
    Graph graph;
    append_component(graph, 0, 48, 48 * 4, rng);
    append_component(graph, 48, 31, 31 * 6, rng);
    append_component(graph, 79, 17, 16, rng);
    assign_unique_weights(graph, rng);
    // Seven isolated vertices coexist with three nontrivial components.
    check_id_layouts(graph, 103, "disconnected graph with isolated vertices");
}

}  // namespace

int main() {
    int passed = 0;
    int failed = 0;
    const auto run = [&](const char* name, void (*test)()) {
        try {
            test();
            std::cout << "PASS " << name << '\n';
            ++passed;
        } catch (const std::exception& error) {
            std::cerr << "FAIL " << name << ": " << error.what() << '\n';
            ++failed;
        }
    };
    run("edge ID metadata and duplicate endpoint selection", test_id_metadata);
    run("empty graphs and isolated vertices", test_empty_graphs);
    run("recursive hierarchical paths", test_recursive_paths);
    run("deterministic random graphs", test_random_graphs);
    run("disconnected minimum spanning forests", test_disconnected_graphs);
    std::cout << passed << " passed, " << failed << " failed\n";
    return failed == 0 ? 0 : 1;
}
