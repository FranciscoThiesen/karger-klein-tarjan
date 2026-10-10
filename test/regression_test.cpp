// Deterministic correctness regressions; no external test framework or timings.
#include "../kkt/kkt.hpp"
#include "../kkt/random_sampling.hpp"
#include "../kruskal/kruskal.hpp"
#include "../lca/lca.hpp"
#include "../verifier/median_table.hpp"
#include "../verifier/verifier_v2.hpp"

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_set>
#include <utility>
#include <vector>

// Existing non-consuming isolation entry point.
problem remove_isolated_vertices(const problem& input);

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

void test_parallel_edges_after_contraction() {
    Graph graph;
    // Leave isolated vertices between groups, exercising supernode renumbering.
    const auto vertex = [](int raw) { return raw + raw / 8; };
    for (int pair = 0; pair < 16; ++pair) {
        graph.emplace_back(vertex(pair * 2), vertex(pair * 2 + 1), pair + 1, 0);
    }

    const auto add_parallel = [&](int from_pair, int to_pair, int base, int offset) {
        for (int i = 0; i < 8; ++i) {
            int from = vertex(from_pair * 2 + (i & 1));
            int to = vertex(to_pair * 2 + ((i >> 1) & 1));
            if (i >= 4) std::swap(from, to);
            // The minimum occurs at different positions in different buckets.
            graph.emplace_back(from, to, base + (i + offset) % 8, 0);
        }
    };

    // Cheap pair edges force the first contraction. This supernode tree has
    // both many destinations for source 0 and a shared destination 15 across
    // many sources, so deduplication must reset its per-source state correctly.
    int tree_edge = 0;
    for (int leaf = 1; leaf <= 7; ++leaf) {
        add_parallel(0, leaf, 1000 + tree_edge * 100, tree_edge);
        ++tree_edge;
    }
    for (int leaf = 8; leaf <= 14; ++leaf) {
        add_parallel(leaf, 15, 1000 + tree_edge * 100, tree_edge);
        ++tree_edge;
    }
    add_parallel(0, 15, 1000 + tree_edge * 100, tree_edge);

    // Heavy chords fill every supernode pair. For tree pairs, the survivor's
    // cost and original ID must both be replaced when a cheaper edge is found.
    int chord = 0;
    for (int from = 0; from < 16; ++from) {
        for (int to = from + 1; to < 16; ++to) {
            add_parallel(from, to, 100000 + chord * 100, chord);
            ++chord;
        }
    }

    check_id_layouts(graph, 36, "forced contraction parallel edges, ordered");
    std::reverse(graph.begin(), graph.end());
    check_id_layouts(graph, 36, "forced contraction parallel edges, reversed");
    std::mt19937 rng(271828);
    std::shuffle(graph.begin(), graph.end(), rng);
    check_id_layouts(graph, 36, "forced contraction parallel edges, shuffled");
}

void test_median_tables() {
    for (int height = 0; height <= 20; ++height) {
        const auto table = verifier_detail::median_table(height);
        const unsigned int size = 1u << (height + 1);
        require(table.size() == size, "median table size at height " +
                                         std::to_string(height));
        require(table[0] == 0, "empty mask must have median zero");
        for (unsigned int mask = 1; mask < size; ++mask) {
            // Independent rank oracle: enumerate set-bit positions in order,
            // then select the upper median directly, without a recurrence.
            int positions[21];
            int count = 0;
            for (int bit = 0; bit <= height; ++bit) {
                if ((mask & (1u << bit)) != 0) positions[count++] = bit;
            }
            if (table[mask] != positions[count / 2]) {
                throw std::runtime_error("median mismatch at height " +
                                         std::to_string(height) + ", mask " +
                                         std::to_string(mask));
            }
        }
    }
}

EdgeIds slow_heavy_edges(const Graph& graph, const Graph& forest, int n) {
    std::vector<std::vector<std::pair<int, int>>> adjacency(n);
    for (const auto& edge : forest) {
        const auto [from, to, weight, id] = edge;
        (void)id;
        adjacency[from].emplace_back(to, weight);
        adjacency[to].emplace_back(from, weight);
    }

    EdgeIds heavy;
    for (const auto& edge : graph) {
        const auto [from, to, weight, id] = edge;
        std::vector<bool> visited(n, false);
        std::vector<int> maximum(n, std::numeric_limits<int>::min());
        std::vector<int> pending{from};
        visited[from] = true;
        while (!pending.empty() && !visited[to]) {
            const int vertex = pending.back();
            pending.pop_back();
            for (const auto& [next, cost] : adjacency[vertex]) {
                if (visited[next]) continue;
                visited[next] = true;
                maximum[next] = std::max(maximum[vertex], cost);
                pending.push_back(next);
            }
        }
        // A missing forest path makes the edge F-light regardless of its cost.
        if (visited[to] && weight > maximum[to]) heavy.insert(id);
    }
    return heavy;
}

void check_heavy_marks(const Graph& graph, const Graph& forest, int n,
                       const std::string& context) {
    const Graph original_graph = graph, original_forest = forest;
    const auto expected = slow_heavy_edges(graph, forest, n);
    const auto marks = verifier_detail::heavy_edge_marks(graph, forest, n);
    require(marks.size() == graph.size(), context + ": wrong mark count");
    for (std::size_t i = 0; i < graph.size(); ++i) {
        require(marks[i] <= 1, context + ": mark is not a boolean byte");
        require((marks[i] != 0) == (expected.count(std::get<3>(graph[i])) != 0),
                context + ": wrong mark at graph position " + std::to_string(i));
    }
    require_same_ids(verify_general_graph(graph, forest, n), expected,
                     context + ": public forest ID adapter");
    if (n > 0 && forest.size() == static_cast<std::size_t>(n - 1))
        require_same_ids(verify_mst(graph, forest, n), expected,
                         context + ": public tree ID adapter");
    require(graph == original_graph && forest == original_forest,
            context + ": verifier modified an input");
}

void check_forest_probes(Graph forest, int n, const std::string& context) {
    Graph graph = forest;
    // Probe the strict comparison immediately below, at, and above every
    // forest-edge weight, including parallel edges with equal weights.
    for (const auto& edge : forest) {
        const auto [from, to, weight, id] = edge;
        (void)id;
        for (int delta : {-1, 0, 1}) graph.emplace_back(from, to, weight + delta, 0);
    }
    std::mt19937 rng(12345);
    for (int i = 0; i < n * 8 && n > 1; ++i) {
        const int from = static_cast<int>(rng() % n);
        int to = static_cast<int>(rng() % (n - 1));
        if (to >= from) ++to;
        graph.emplace_back(from, to, static_cast<int>(rng() % (n * 4 + 1)), 0);
    }
    graph = with_ids(std::move(graph), IdLayout::signed_extremes);
    std::copy_n(graph.begin(), forest.size(), forest.begin());
    check_heavy_marks(graph, forest, n, context);
}

void test_heavy_edge_positions() {
    const Graph forest{{0, 1, 4, 100}, {1, 2, 9, 101},
                       {3, 4, 7, 102}, {6, 7, 11, 103}};
    // Interleave component queries with edges that have no forest path.
    // The last tree has no query; vertices 5 and 8 are isolated in the forest.
    const Graph probes{{0, 2, 12, 0}, {0, 3, 1000, 0}, {3, 4, 8, 0},
                       {1, 2, 9, 0}, {0, 1, 3, 0}, {3, 4, 7, 0},
                       {0, 2, 8, 0}, {5, 8, 999, 0}, {2, 0, 10, 0}};
    for (IdLayout layout : {IdLayout::dense, IdLayout::sparse, IdLayout::signed_extremes}) {
        Graph graph = with_ids(probes, layout);
        for (int order = 0; order < 3; ++order) {
            const auto context = "position marks, layout " +
                                 std::to_string(static_cast<int>(layout)) +
                                 ", order " + std::to_string(order);
            check_heavy_marks(graph, forest, 9, context);
            check_heavy_marks(graph, {}, 9, context + ", empty forest");
            std::reverse(graph.begin(), graph.end());
            for (auto& edge : graph) std::swap(std::get<0>(edge), std::get<1>(edge));
            if (order == 1) std::rotate(graph.begin(), graph.begin() + 3, graph.end());
        }
    }
    check_heavy_marks({}, {}, 0, "empty graph position marks");
    check_heavy_marks({}, forest, 9, "forest without query position marks");
}

void test_forest_heavy_edges() {
    check_forest_probes({}, 7, "verifier isolated vertices and cross-component edges");
    for (int n : {2, 9, 32, 65, 256}) {
        check_forest_probes(hierarchical_path(n), n,
                           "verifier hierarchical path n=" + std::to_string(n));
    }

    std::mt19937 rng(98123);
    Graph forest;
    append_component(forest, 0, 25, 24, rng);
    append_component(forest, 25, 17, 16, rng);
    append_component(forest, 42, 9, 8, rng);
    assign_unique_weights(forest, rng);
    check_forest_probes(forest, 58, "verifier disconnected forest and isolated vertices");
}

void test_verifier_query_layout() {
    const int lowest = std::numeric_limits<int>::lowest();
    const Graph forest{{0, 1, lowest, 100}, {1, 2, -20, 101},
                       {2, 3, -10, 102}, {4, 5, -30, 103}};
    // Probe negative maxima, including an exact INT_MIN result, and retain
    // equal-cost queries to check that only strictly heavier edges are marked.
    Graph queries{{0, 1, lowest, 0}, {1, 0, lowest + 1, 1},
                  {0, 2, -20, 2}, {2, 0, -21, 3},
                  {3, 0, -9, 4}, {0, 3, -10, 5},
                  {4, 5, -29, 6}, {5, 4, -30, 7},
                  {2, 4, std::numeric_limits<int>::max(), 8}};
    for (int order = 0; order < 3; ++order) {
        check_heavy_marks(queries, forest, 8,
                          "contiguous queries with negative costs, order " +
                              std::to_string(order));
        std::rotate(queries.begin(), queries.begin() + 2, queries.end());
        for (auto& edge : queries) std::swap(std::get<0>(edge), std::get<1>(edge));
    }

    // Self-loops previously created no ancestor query and remained unmarked.
    // Preserve that API behavior separately from the nonempty-path oracle.
    const Graph loops{{0, 0, lowest, 20}, {1, 1, -11, 21},
                      {3, 3, 0, 22}, {4, 4, 7, 23},
                      {7, 7, std::numeric_limits<int>::max(), 24}};
    const auto loop_marks = verifier_detail::heavy_edge_marks(loops, forest, 8);
    require(loop_marks == std::vector<unsigned char>(loops.size(), 0),
            "self-loop-only queries should remain unmarked");
    require(verify_general_graph(loops, forest, 8).empty(),
            "self-loop-only public forest adapter");
    Graph mixed = queries;
    mixed.insert(mixed.end(), loops.begin(), loops.end());
    const auto mixed_marks = verifier_detail::heavy_edge_marks(mixed, forest, 8);
    const auto query_marks = verifier_detail::heavy_edge_marks(queries, forest, 8);
    require(mixed_marks.size() == mixed.size(), "mixed self-loop mark count");
    require(std::equal(query_marks.begin(), query_marks.end(), mixed_marks.begin()),
            "self-loop queries changed nonempty-path answers");
    require(std::all_of(mixed_marks.begin() + queries.size(), mixed_marks.end(),
                        [](unsigned char mark) { return mark == 0; }),
            "mixed self-loop queries should remain unmarked");
    require_same_ids(verify_general_graph(mixed, forest, 8),
                     slow_heavy_edges(queries, forest, 8),
                     "mixed self-loop public forest adapter");

    const Graph tree(forest.begin(), forest.begin() + 3);
    const Graph tree_loops(loops.begin(), loops.begin() + 3);
    require(verify_mst(tree_loops, tree, 4).empty(),
            "self-loop-only public tree adapter");
}

void test_verifier_empty_components() {
    for (int n : {0, 1}) {
        require(verify_mst({}, {}, n).empty(), "empty or singleton tree verification");
        require(verify_general_graph({}, {}, n).empty(),
                "empty or singleton forest verification");
    }

    const Graph tree{{0, 1, 3, 10}};
    require(verify_mst({}, tree, 2).empty(), "tree without edge queries");
    require(verify_general_graph({}, tree, 4).empty(), "forest without edge queries");
    require(verify_general_graph(tree, {}, 4).empty(), "empty forest makes edges light");

    const Graph forest{{0, 1, 3, 10}, {2, 3, 5, 11}};
    const Graph queries{{0, 1, 4, 20}, {0, 2, 100, 21}, {0, 4, 101, 22}};
    // The second tree has no internal query; vertex 4 is isolated. Only edge
    // 20 has a forest path, so the other two edges remain light at any cost.
    require_same_ids(verify_general_graph(queries, forest, 5), EdgeIds{20},
                     "forest component without queries and isolated vertex");
}

LCA lca_from_local_adjacency() {
    const std::vector<std::vector<int>> adjacency{{1, 2}, {0, 3, 4}, {0}, {1}, {1}};
    return LCA(5, adjacency, 0);
}

void test_lca_adjacency_lifetime() {
    const auto check = [](LCA& index, const std::string& context) {
        const int expected[5][5] = {
            {0, 0, 0, 0, 0},
            {0, 1, 0, 1, 1},
            {0, 0, 2, 0, 0},
            {0, 1, 0, 3, 1},
            {0, 1, 0, 1, 4},
        };
        for (int from = 0; from < 5; ++from) {
            for (int to = 0; to < 5; ++to) {
                require(index.query(from, to) == expected[from][to],
                        context + ": wrong LCA for " + std::to_string(from) +
                            ", " + std::to_string(to));
            }
        }
    };

    auto from_local = lca_from_local_adjacency();
    check(from_local, "destroyed local adjacency");
    LCA from_temporary(5, {{1, 2}, {3, 4}, {}, {}, {}}, 0);
    check(from_temporary, "temporary directed adjacency");

    std::vector<std::vector<int>> adjacency{{1, 2}, {0, 3, 4}, {0}, {1}, {1}};
    LCA from_cleared(5, adjacency, 0);
    adjacency.clear();
    adjacency.shrink_to_fit();
    check(from_cleared, "cleared adjacency");
}

void test_isolated_vertex_compaction() {
    const auto check = [](const problem& input, int expected_vertices,
                          const Graph& expected_edges, const std::string& context) {
        const auto original_edges = input.graph_edges;
        const int original_vertices = input.num_vertices;
        const auto original_max_id = input.max_edge_id;
        const auto compacted = remove_isolated_vertices(input);
        require(compacted.num_vertices == expected_vertices &&
                    compacted.graph_edges == as_edges(expected_edges) &&
                    compacted.max_edge_id == original_max_id,
                context + ": wrong compacted graph, edge order, IDs, or metadata");
        require(input.graph_edges == original_edges &&
                    input.num_vertices == original_vertices &&
                    input.max_edge_id == original_max_id,
                context + ": isolation modified its const input");
    };

    const Graph graph{{1, 4, 7, std::numeric_limits<int>::min()},
                      {4, 6, -3, std::numeric_limits<int>::max()},
                      {1, 6, 9, -1}, {6, 4, 12, 0}};
    const Graph compacted{{0, 1, 7, std::numeric_limits<int>::min()},
                          {1, 2, -3, std::numeric_limits<int>::max()},
                          {0, 2, 9, -1}, {2, 1, 12, 0}};
    check(problem(8, as_edges(graph), 0), 3, compacted, "isolate compaction");
    check(problem(3, as_edges(compacted), -7), 3, compacted, "no isolates");
    for (int n : {0, 9}) {
        const problem empty(n, std::vector<Edge>{}, 123456789);
        check(empty, 0, {}, "empty isolation n=" + std::to_string(n));
        std::mt19937 rng(918273);
        const auto before = rng;
        const auto sample = kkt_detail::random_sampling(empty, rng);
        require(sample.num_vertices == 0 && sample.graph_edges.empty() &&
                    sample.max_edge_id == empty.max_edge_id,
                "empty public sampling changed vertices or metadata");
        require(rng == before, "empty public sampling consumed random draws");
        require(empty.num_vertices == n && empty.graph_edges.empty(),
                "empty public sampling modified its input");
    }
}

void test_sampling_stream() {
    const problem input(256, with_ids(hierarchical_path(256), IdLayout::signed_extremes));
    const auto original_edges = input.graph_edges;
    for (unsigned int seed : {0u, 42u, std::numeric_limits<unsigned int>::max()}) {
        std::mt19937 actual_rng(seed);
        std::mt19937 expected_rng(seed);
        std::mt19937 replay_rng(seed);
        for (int round = 0; round < 2; ++round) {
            // Advance an independent engine exactly once per input edge.
            // Keep the complete sequence so a public sample cannot expose its
            // internal recursive position IDs or reorder retained edges.
            std::vector<Edge> expected_edges;
            std::vector<bool> present(input.num_vertices, false);
            for (const auto& edge : input.graph_edges) {
                if ((expected_rng() & 1u) != 0) {
                    expected_edges.push_back(edge);
                    present[edge.from] = present[edge.to] = true;
                }
            }
            // Independently reconstruct the documented removal of isolates:
            // retained vertices are compacted in ascending original order.
            std::vector<int> compact(input.num_vertices, -1);
            int expected_vertices = 0;
            for (int vertex = 0; vertex < input.num_vertices; ++vertex)
                if (present[vertex]) compact[vertex] = expected_vertices++;
            for (auto& edge : expected_edges) {
                edge.from = compact[edge.from];
                edge.to = compact[edge.to];
            }

            const auto sample = kkt_detail::random_sampling(input, actual_rng);
            const std::string context = "sampling seed " + std::to_string(seed) +
                                        ", round " + std::to_string(round);
            require(sample.graph_edges == expected_edges,
                    context + ": public IDs, order, costs, or compact endpoints changed");
            require(sample.num_vertices == expected_vertices,
                    context + ": wrong compact vertex count");
            require(sample.max_edge_id == input.max_edge_id,
                    context + ": public sampling changed legacy ID metadata");
            require(actual_rng == expected_rng, context + ": wrong generator state");
            require(input.graph_edges == original_edges,
                    context + ": sampling modified its input");

            const auto replay = kkt_detail::random_sampling(input, replay_rng);
            require(sample.graph_edges == replay.graph_edges &&
                        sample.num_vertices == replay.num_vertices &&
                        sample.max_edge_id == replay.max_edge_id,
                    context + ": seed replay changed the sample");
        }
    }
}

void test_global_random_state() {
    const Graph graph = hierarchical_path(256);
    const auto expected_ids = kruskal_ids(graph, 256);
    problem input(256, graph);
    std::vector<int> expected_random;
    std::srand(918273);
    for (int i = 0; i < 16; ++i) expected_random.push_back(std::rand());

    for (unsigned int seed : {0u, 42u}) {
        std::srand(918273);
        require(std::rand() == expected_random[0], "C random replay failed");
        // The hierarchical path survives two contractions, reaching sampling.
        require_same_ids(kkt(input, seed), expected_ids, "KKT with independent RNG");
        for (std::size_t i = 1; i < expected_random.size(); ++i) {
            require(std::rand() == expected_random[i], "KKT changed global C random state");
        }
    }
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
    run("parallel edges after forced contractions", test_parallel_edges_after_contraction);
    run("exhaustive upper-median tables through height 20", test_median_tables);
    run("forest heavy edges against direct path searches", test_forest_heavy_edges);
    run("heavy-edge positions preserve IDs and component mappings", test_heavy_edge_positions);
    run("contiguous queries preserve negative, equal, and empty paths", test_verifier_query_layout);
    run("verifier empty inputs and components without queries", test_verifier_empty_components);
    run("LCA queries outlive input adjacency", test_lca_adjacency_lifetime);
    run("isolate compaction preserves inputs and handles empty samples", test_isolated_vertex_compaction);
    run("sampling consumes a continuing reproducible stream", test_sampling_stream);
    run("KKT preserves global C random state", test_global_random_state);
    std::cout << passed << " passed, " << failed << " failed\n";
    return failed == 0 ? 0 : 1;
}
