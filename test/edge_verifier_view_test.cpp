// Untimed tests for the graph-record overload and exact paired KKT work.
#include "../verifier/verifier_v2.hpp"
#include "../kkt/kkt.hpp"
#include "../benchmark/work_metrics.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

#ifndef KKT_ENABLE_WORK_STATS
#error "This correctness gate requires instrumented production objects"
#endif
#ifndef KKT_EXPERIMENT_RETAIN_PARALLEL
#error "Both paired variants must retain parallel edges"
#endif

namespace {
using Graph = std::vector<std::tuple<int, int, int, int>>;
using Marks = std::vector<unsigned char>;
std::size_t mark_cases = 0, solver_cases = 0;

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

// One explicit forest walk per query. IDs play no part in classification,
// so repeated IDs cannot conceal different marks at different positions.
Marks oracle(const Graph& graph, const Graph& forest, int n) {
    std::vector<std::vector<std::pair<int, int>>> adjacency(n);
    for (const auto& [u, v, cost, id] : forest) {
        (void)id;
        adjacency[u].emplace_back(v, cost);
        adjacency[v].emplace_back(u, cost);
    }
    Marks result(graph.size(), 0);
    for (std::size_t i = 0; i < graph.size(); ++i) {
        const auto [from, to, cost, id] = graph[i];
        (void)id;
        // Preserve the existing API's self-loop behavior explicitly.
        if (from == to) continue;
        std::vector<bool> seen(n, false);
        std::vector<int> maximum(n, std::numeric_limits<int>::min());
        std::vector<int> pending{from};
        seen[from] = true;
        for (std::size_t j = 0; j < pending.size(); ++j) {
            const int vertex = pending[j];
            for (const auto& [next, weight] : adjacency[vertex]) {
                if (seen[next]) continue;
                seen[next] = true;
                maximum[next] = std::max(maximum[vertex], weight);
                pending.push_back(next);
            }
        }
        if (seen[to] && cost > maximum[to]) result[i] = 1;
    }
    return result;
}

void check_marks(const Graph& graph, const Graph& forest, int n) {
    const auto graph_before = graph, forest_before = forest;
    std::vector<Edge> edges(graph.begin(), graph.end());
    const auto edges_before = edges;
    const Marks expected = oracle(graph, forest, n);
    Marks tuple_marks, edge_marks;
    kkt_work::WorkStats tuple_stats, edge_stats;
    {
        kkt_work::ScopedWorkStats scope(tuple_stats);
        tuple_marks = verifier_detail::heavy_edge_marks(graph, forest, n);
    }
    {
        kkt_work::ScopedWorkStats scope(edge_stats);
        edge_marks = verifier_detail::heavy_edge_marks(edges, forest, n);
    }
    require(tuple_marks == expected && edge_marks == expected, "positional mark oracle mismatch");
    for (const auto& field : benchmark_work::fields)
        require(tuple_stats.*field.member == edge_stats.*field.member,
                std::string("verifier overload counter mismatch: ") + field.name);
    std::unordered_set<int> expected_ids;
    for (std::size_t i = 0; i < graph.size(); ++i)
        if (expected[i]) expected_ids.insert(std::get<3>(graph[i]));
    // These typed function pointers also retain the exact public signatures.
    using PublicVerifier = std::unordered_set<int> (*)(const Graph&, const Graph&, int);
    const PublicVerifier general = verify_general_graph, tree = verify_mst;
    require(general(graph, forest, n) == expected_ids, "public forest adapter mismatch");
    if (n == 0 || forest.size() == static_cast<std::size_t>(n - 1))
        require(tree(graph, forest, n) == expected_ids, "public tree adapter mismatch");
    require(graph == graph_before && forest == forest_before && edges == edges_before,
            "verifier modified an input");
    ++mark_cases;
}

void orders(Graph graph, Graph forest, int n) {
    for (int order = 0; order < 4; ++order) {
        check_marks(graph, forest, n);
        check_marks(graph, {}, n);
        check_marks({}, forest, n);
        std::reverse(graph.begin(), graph.end());
        std::reverse(forest.begin(), forest.end());
        for (auto& edge : graph) std::swap(std::get<0>(edge), std::get<1>(edge));
        for (auto& edge : forest) std::swap(std::get<0>(edge), std::get<1>(edge));
        if (!graph.empty()) std::rotate(graph.begin(), graph.begin() + graph.size() / 3, graph.end());
    }
}

void direct_tests() {
    const int low = std::numeric_limits<int>::min(), high = std::numeric_limits<int>::max();
    orders({}, {}, 0);
    orders({{0, 0, low, high}, {0, 0, high, low}}, {}, 1);
    const Graph forest{{0, 1, low, high}, {1, 2, -20, low},
                       {2, 3, 5, -1}, {4, 5, high - 1, 42}};
    Graph queries{{0, 1, low, low}, {1, 0, low + 1, low},
                  {0, 2, -20, high}, {2, 0, -21, high},
                  {0, 3, 6, -1}, {3, 0, 5, -1},
                  {4, 5, high, 99999999}, {5, 4, high - 1, 99999999},
                  {2, 5, high, 0}, {6, 7, high, 0},
                  {0, 0, high, low}, {7, 7, low, high}};
    require(oracle(queries, forest, 8) == Marks{0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0},
            "independent oracle failed explicit boundary fixture");
    orders(queries, forest, 8);
    orders(Graph(queries.begin(), queries.begin() + 6), Graph(forest.begin(), forest.begin() + 3), 4);

    std::mt19937 rng(20261015);
    for (int trial = 0; trial < 100; ++trial) {
        const int n = 2 + static_cast<int>(rng() % 79);
        Graph tree;
        for (int v = 1; v < n; ++v) {
            if (trial % 3 != 0 && rng() % 4 == 0) continue;
            tree.emplace_back(v, static_cast<int>(rng() % v), v * 7 - n * 3, v);
        }
        Graph graph;
        for (const auto& [u, v, cost, id] : tree) {
            (void)id;
            for (int delta : {-1, 0, 1}) graph.emplace_back(u, v, cost + delta, high);
        }
        for (int i = 0; i < n * 8; ++i) {
            const int id = i % 3 == 0 ? low : (i % 3 == 1 ? high : -100003);
            graph.emplace_back(rng() % n, rng() % n, static_cast<int>(rng() % (n * 9)) - n * 4, id);
        }
        orders(graph, tree, n);
    }
}

// Slow label replacement is independent of the production DSU and KKT's
// cheapest-neighbor walks. Sorting unique weights specifies a unique MSF.
std::unordered_set<int> sorted_oracle(const problem& input) {
    auto edges = input.graph_edges;
    std::sort(edges.begin(), edges.end(), [](const Edge& a, const Edge& b) { return a.cost < b.cost; });
    std::vector<int> labels(input.num_vertices);
    std::iota(labels.begin(), labels.end(), 0);
    std::unordered_set<int> result;
    for (const Edge& edge : edges) {
        const int first = labels[edge.from], second = labels[edge.to];
        if (first == second) continue;
        for (int& label : labels) if (label == second) label = first;
        result.insert(edge.id);
    }
    return result;
}

std::uint64_t fingerprint(const problem& input) {
    std::uint64_t hash = UINT64_C(14695981039346656037);
    const auto append = [&](int value) {
        const auto bits = static_cast<std::uint32_t>(value);
        for (int shift = 0; shift < 32; shift += 8) {
            hash ^= (bits >> shift) & 255u;
            hash *= UINT64_C(1099511628211);
        }
    };
    append(input.num_vertices);
    for (const Edge& edge : input.graph_edges) {
        append(edge.from); append(edge.to); append(edge.cost); append(edge.id);
    }
    return hash;
}

void check_solver(problem input, int fixture, int order, unsigned seed) {
    const auto expected = sorted_oracle(input);
    const auto before = input.graph_edges;
    const auto metadata = input.max_edge_id;
    kkt_work::WorkStats stats;
    std::unordered_set<int> actual;
    {
        kkt_work::ScopedWorkStats scope(stats);
        actual = kkt(input, seed);
    }
    require(actual == expected, "full KKT differs from sorted independent oracle");
    require(input.graph_edges == before && input.max_edge_id == metadata, "KKT modified input");
    require(stats.sampling_edge_visits == stats.verifier_edges &&
            stats.sampling_calls == stats.verifier_calls && stats.current_depth == 0,
            "invalid KKT work accounting");
    if (fixture == 0)
        require(stats.root_after_two_vertices == 4 && stats.root_after_two_edges == 96 &&
                stats.verifier_edges > 0, "linked retention/verifier discriminator failed");
    std::vector<int> ids(actual.begin(), actual.end());
    std::sort(ids.begin(), ids.end());
    std::cout << "{\"fixture\":" << fixture << ",\"order\":" << order << ",\"seed\":" << seed
              << ",\"fingerprint\":" << fingerprint(input) << ",\"ids\":[";
    for (std::size_t i = 0; i < ids.size(); ++i) std::cout << (i ? "," : "") << ids[i];
    std::cout << "],\"stats\":{";
    bool first = true;
    for (const auto& field : benchmark_work::fields) {
        if (!first) std::cout << ',';
        first = false;
        std::cout << '"' << field.name << "\":" << stats.*field.member;
    }
    std::cout << "}}\n";
    ++solver_cases;
}

void solver_tests() {
    std::vector<problem> fixtures;
    std::vector<Edge> hierarchy;
    for (int v = 1; v < 16; ++v) {
        int level = 0;
        for (int x = v; x % 2 == 0; x /= 2) ++level;
        hierarchy.emplace_back(v - 1, v, level * 16 + v, hierarchy.size());
    }
    for (int u = 0; u < 16; ++u) for (int v = u + 2; v < 16; ++v) {
        const int id = static_cast<int>(hierarchy.size());
        hierarchy.emplace_back(u, v, 1000 + id, id);
    }
    fixtures.emplace_back(16, hierarchy);
    auto signed_hierarchy = hierarchy;
    for (Edge& edge : signed_hierarchy) edge.cost += std::numeric_limits<int>::min();
    signed_hierarchy.front().cost = std::numeric_limits<int>::min();
    signed_hierarchy.back().cost = std::numeric_limits<int>::max();
    fixtures.emplace_back(16, signed_hierarchy);
    fixtures.emplace_back(0, std::vector<Edge>{});
    fixtures.emplace_back(1, std::vector<Edge>{});
    fixtures.emplace_back(17, std::vector<Edge>{});
    fixtures.emplace_back(2, std::vector<Edge>{{0, 1, -3, -1}, {1, 0, 4, 8}});
    std::mt19937 rng(156842);
    for (int trial = 0; trial < 50; ++trial) {
        const int n = 4 + static_cast<int>(rng() % 64);
        const int m = 8 + static_cast<int>(rng() % (n * 10));
        std::vector<int> costs(m);
        std::iota(costs.begin(), costs.end(), -m / 2);
        std::shuffle(costs.begin(), costs.end(), rng);
        std::vector<Edge> edges;
        for (int i = 0; i < m; ++i) {
            // Some fixtures have two separate components plus isolates.
            const int size = trial % 2 ? n : n / 2;
            const int offset = trial % 2 || i % 2 ? 0 : n / 2;
            int u = static_cast<int>(rng() % size), v = static_cast<int>(rng() % (size - 1));
            if (v >= u) ++v;
            edges.emplace_back(offset + u, offset + v, costs[i], i);
        }
        fixtures.emplace_back(n + 2, edges);
    }
    const std::vector<unsigned> seeds{0, 1, 2, 17, 401, 809, 65537, std::numeric_limits<unsigned>::max()};
    for (std::size_t f = 0; f < fixtures.size(); ++f) {
        problem input = fixtures[f];
        for (int order = 0; order < 3; ++order) {
            if (order == 1) std::reverse(input.graph_edges.begin(), input.graph_edges.end());
            if (order == 2) {
                std::shuffle(input.graph_edges.begin(), input.graph_edges.end(), rng);
                for (std::size_t i = 0; i < input.graph_edges.size(); ++i) {
                    Edge& edge = input.graph_edges[i];
                    std::swap(edge.from, edge.to);
                    edge.id = i == 0 ? std::numeric_limits<int>::min() :
                        i == 1 ? std::numeric_limits<int>::max() : -static_cast<int>(i) * 100003;
                }
                input.max_edge_id = std::numeric_limits<std::int64_t>::max();
            }
            for (unsigned seed : seeds) check_solver(input, static_cast<int>(f), order, seed);
        }
    }
}
}  // namespace

int main() {
    try {
        direct_tests();
        solver_tests();
        std::cout.flush();
        require(static_cast<bool>(std::cout), "failed to write paired records");
        std::cerr << "PASS " << mark_cases << " positional oracle cases; " << solver_cases
                  << " independently checked full KKT records\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL: " << error.what() << '\n';
        return 1;
    }
}
