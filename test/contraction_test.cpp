// Standalone, independent oracle for one contraction step. This checks the
// existing contraction semantics (including its tie order), not full-KKT
// correctness on tied weights or self-loops.
#include "../kkt/kkt.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <random>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

std::pair<std::vector<int>, problem> boruvka_step(const problem& input);

namespace {
using Result = std::pair<std::vector<int>, problem>;
using Graph = std::vector<std::tuple<int, int, int, int>>;

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

Result reference(const problem& input) {
    const auto& edges = input.graph_edges;
    const int n = input.num_vertices;
    std::vector<int> group(n);
    std::iota(group.begin(), group.end(), 0);
    std::set<int> chosen_positions;
    std::vector<int> selected;
    // Deliberately use a separate O(n*m) vertex/edge oracle and O(n) relabel
    // unions. Neither successor walking nor adjacency traversal is shared.
    for (int vertex = 0; vertex < n; ++vertex) {
        int best = -1;
        for (int i = 0; i < static_cast<int>(edges.size()); ++i) {
            const Edge& edge = edges[i];
            if (edge.from != vertex && edge.to != vertex) continue;
            if (best == -1 || edge.cost < edges[best].cost) best = i;
        }
        if (best == -1 || !chosen_positions.insert(best).second) continue;
        selected.push_back(edges[best].id);
        const int first = group[edges[best].from];
        const int second = group[edges[best].to];
        for (int& value : group) if (value == second) value = first;
    }

    std::map<int, int> component_number;
    std::vector<int> component(n);
    int next_component = 0;
    for (int vertex = 0; vertex < n; ++vertex) {
        const auto inserted = component_number.emplace(group[vertex], next_component);
        if (inserted.second) ++next_component;
        component[vertex] = inserted.first->second;
    }
    std::vector<bool> active(next_component, false);
    for (const Edge& edge : edges) {
        const int first = component[edge.from], second = component[edge.to];
        if (first != second) active[first] = active[second] = true;
    }
    std::vector<int> compact(next_component, -1);
    int next_vertex = 0;
    for (int c = 0; c < next_component; ++c)
        if (active[c]) compact[c] = next_vertex++;

    struct Bucket { int best = -1; int last = -1; };
    using Pair = std::pair<int, int>;
    std::map<Pair, Bucket> buckets;
    for (int i = 0; i < static_cast<int>(edges.size()); ++i) {
        const Edge& edge = edges[i];
        const int first = component[edge.from], second = component[edge.to];
        if (first == second) continue;
        const Pair pair = std::minmax(compact[first], compact[second]);
        auto& bucket = buckets[pair];
        // Existing linked buckets visit original positions in reverse order:
        // among equal minima, the last original edge survives deduplication.
        if (bucket.best == -1 || edge.cost <= edges[bucket.best].cost) bucket.best = i;
        bucket.last = i;
    }
    std::vector<std::pair<Pair, Bucket>> order(buckets.begin(), buckets.end());
    std::sort(order.begin(), order.end(), [](const auto& a, const auto& b) {
        if (a.first.first != b.first.first) return a.first.first < b.first.first;
        return a.second.last > b.second.last;
    });
    std::vector<Edge> remaining;
    for (const auto& entry : order) {
        const auto& pair = entry.first;
        const Edge& edge = edges[entry.second.best];
        remaining.emplace_back(pair.first, pair.second, edge.cost, edge.id);
    }
    return {std::move(selected), problem(next_vertex, std::move(remaining), input.max_edge_id)};
}

void check(const std::string& name, const problem& input) {
    const auto before = input.graph_edges;
    const auto expected = reference(input);
    Result actual;
#ifdef KKT_ENABLE_WORK_STATS
    kkt_work::WorkStats stats;
    {
        kkt_work::ScopedWorkStats scope(stats);
        actual = boruvka_step(input);
    }
    const std::uint64_t n = input.num_vertices, m = input.graph_edges.size();
    require(stats.contraction_calls == 1, name + ": missing contraction instrumentation");
    require(stats.contraction_edge_visits <= 4 * m, name + ": too many edge visits");
    require(stats.contraction_arc_visits <= 2 * n, name + ": successor walks revisit vertices");
    require(stats.contraction_vertex_visits <= 6 * n, name + ": too many vertex visits");
    require(stats.initialized_slots <= m + 7 * n, name + ": redundant contraction storage");
#else
    actual = boruvka_step(input);
#endif
    require(actual.first == expected.first, name + ": selected IDs or their order differ");
    require(actual.second.num_vertices == expected.second.num_vertices,
            name + ": compact vertex count differs");
    require(actual.second.graph_edges == expected.second.graph_edges,
            name + ": compact endpoints, parallel winner, or edge order differs");
    require(actual.second.max_edge_id == input.max_edge_id, name + ": legacy metadata changed");
    require(input.graph_edges == before, name + ": input graph changed");
}
} // namespace

int main() {
    try {
        check("empty", problem(0, Graph{}));
        check("isolated vertices", problem(9, Graph{}));
        check("mutual endpoint choice", problem(2, Graph{{0, 1, 7, std::numeric_limits<int>::max()}}));
        Graph star;
        for (int vertex = 0; vertex < 9; ++vertex)
            if (vertex != 5) star.emplace_back(5, vertex, 100 - 3 * vertex, -1000000000 + vertex);
        check("star with sparse negative IDs", problem(9, star));
        check("late incoming branches reuse old component IDs", problem(9, Graph{
            {0, 4, 1, 10}, {4, 8, 2, 11}, {1, 3, 3, 12}, {2, 8, 4, 13},
            {5, 6, 5, 14}, {6, 7, 6, 15}, {3, 7, 30, 16}, {8, 7, 40, 17}}));
        check("terminal components and isolated vertices", problem(10, Graph{
            {0, 2, 1, 20}, {2, 4, 2, 21}, {1, 3, 3, 22}, {3, 5, 4, 23},
            {4, 5, 100, 24}, {6, 7, 10, 25}}));
        Graph parallel{{0, 1, 1, 1}, {2, 3, 2, 2}, {4, 5, 3, 3},
                       {0, 2, 10, 4}, {1, 3, 10, 5}, {0, 3, 12, 6},
                       {2, 4, 20, 7}, {3, 5, 15, 8}};
        check("parallel contracted edges with equal minima", problem(6, parallel));
        std::reverse(parallel.begin(), parallel.end());
        check("reversed parallel tie order", problem(6, parallel));
        check("equal-weight triangle", problem(3, Graph{{0, 1, 1, -1}, {1, 2, 1, 0}, {2, 0, 1, 1000000000}}));
        check("self-successor preserves prior contraction semantics", problem(5, Graph{
            {0, 0, -4, 30}, {0, 1, 0, 31}, {1, 2, 3, 32}, {2, 3, 1, 33}, {3, 4, 2, 34}}));
        std::mt19937 rng(20261010);
        for (int trial = 0; trial < 200; ++trial) {
            const int n = 1 + static_cast<int>(rng() % 24);
            Graph graph;
            const int m = static_cast<int>(rng() % 96);
            for (int i = 0; i < m; ++i)
                graph.emplace_back(rng() % n, rng() % n, static_cast<int>(rng() % 11) - 5,
                                   1000000000 + i * 100003);
            problem input(n, graph);
            if (trial % 3 == 0) input.max_edge_id = 0; // Legacy metadata is irrelevant.
            check("deterministic multigraph " + std::to_string(trial), input);
        }
        std::cout << "PASS 210 contraction cases against independent partition/order oracle\n";
    } catch (const std::exception& error) {
        std::cerr << "FAIL " << error.what() << '\n';
        return 1;
    }
}
