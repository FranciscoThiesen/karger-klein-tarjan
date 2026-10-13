// Independent geometric, paired-input and MST checks; no timings or assert.
#include "crossover_fixtures.hpp"
#include "component_moments.hpp"
#include "mst_certificate.hpp"
#include "../kkt/kkt.hpp"
#include "../kruskal/kruskal.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <numeric>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_set>
#include <utility>
#include <vector>

std::pair<std::vector<int>, problem> boruvka_step(const problem& input);

namespace {
using benchmark_crossover::Fixture;
using benchmark_crossover::Spec;
using benchmark_fixtures::Graph;

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

std::uint64_t pair_key(int u, int v) {
    if (u > v) std::swap(u, v);
    return (static_cast<std::uint64_t>(u) << 32) | static_cast<unsigned int>(v);
}

std::unordered_set<int> ids(const Graph& graph) {
    std::unordered_set<int> result;
    for (const auto& edge : graph)
        require(result.insert(std::get<3>(edge)).second, "duplicate MST ID");
    return result;
}

std::array<int, 2> independent_dimensions(int n) {
    std::array<int, 2> result{1, 1};
    for (int axis = 0; n > 1; n /= 2, axis = 1 - axis) result[axis] *= 2;
    return result;
}

void paired_check(const Fixture& metric, const Fixture& random) {
    require(metric.graph.size() == random.graph.size() &&
            metric.original_positions == random.original_positions &&
            metric.original_to_label == random.original_to_label &&
            metric.backbone_ids == random.backbone_ids &&
            metric.grid_dimensions == random.grid_dimensions, "paired metadata differs");
    bool changed_weight = false;
    for (std::size_t i = 0; i < metric.graph.size(); ++i) {
        const auto& a = metric.graph[i];
        const auto& b = random.graph[i];
        require(std::get<0>(a) == std::get<0>(b) && std::get<1>(a) == std::get<1>(b) &&
                std::get<3>(a) == std::get<3>(b), "paired topology, IDs or order differs");
        changed_weight |= std::get<2>(a) != std::get<2>(b);
    }
    require(changed_weight, "fixed test seed did not exercise different weight modes");
}

int check(const Spec& spec, unsigned seed, bool check_mst) {
    const auto fixture = benchmark_crossover::make_fixture(spec, seed);
    const auto replay = benchmark_crossover::make_fixture(spec, seed);
    const bool line = spec.family.find("line_") == 0;
    const bool gnm = spec.family == "gnm_random";
    const bool metric = spec.family.find("_metric") != std::string::npos;
    const int n = spec.n, m = n * spec.density;
    require(fixture.graph == replay.graph &&
            fixture.original_positions == replay.original_positions &&
            fixture.original_to_label == replay.original_to_label &&
            fixture.backbone_ids == replay.backbone_ids &&
            fixture.grid_dimensions == replay.grid_dimensions &&
            fixture.topology_attempts == replay.topology_attempts, "fixture replay changed");
    require(fixture.graph.size() == static_cast<std::size_t>(m) &&
            benchmark_crossover::edge_count(spec) == m, "wrong exact edge count");
    require(fixture.original_positions.size() == static_cast<std::size_t>(gnm ? 0 : n) &&
            fixture.original_to_label.size() == static_cast<std::size_t>(n), "geometry metadata missing");
    require(fixture.topology_attempts >= 1 &&
            fixture.topology_attempts <= (gnm ? benchmark_crossover::gnm_attempt_limit : 1),
            "invalid whole-topology attempt count");
    std::vector<int> original(n, -1);
    for (int v = 0; v < n; ++v) {
        const int label = fixture.original_to_label[v];
        require(label >= 0 && label < n && original[label] == -1, "labels not a permutation");
        original[label] = v;
    }
    const auto dimensions = independent_dimensions(n);
    const int base = gnm ? 0 : line ? n - 1 : 2 * n - dimensions[0] - dimensions[1];
    require(fixture.backbone_ids.size() == static_cast<std::size_t>(base), "wrong scaffold size");
    for (int i = 0; i < base; ++i) require(fixture.backbone_ids[i] == i, "scaffold ID metadata changed");
    if (gnm) {
        require(fixture.grid_dimensions == std::array<int, 2>{0, 0}, "G(n,m) has grid metadata");
    } else if (line) {
        require(fixture.grid_dimensions == std::array<int, 2>{0, 0}, "line has grid metadata");
        require(fixture.original_positions[0] == benchmark_crossover::Position{0, 0}, "line origin moved");
        for (int v = 1; v < n; ++v) {
            const auto gap = fixture.original_positions[v][0] - fixture.original_positions[v - 1][0];
            require(gap >= 1 && gap <= 1024 && fixture.original_positions[v][1] == 0,
                    "line gap is not in [1,1024] or leaves the axis");
        }
    } else {
        require(fixture.grid_dimensions == dimensions, "grid dimensions differ from independent construction");
        for (int v = 0; v < n; ++v) {
            const auto& p = fixture.original_positions[v];
            const auto dx = p[0] - 1024LL * (v % dimensions[0]);
            const auto dy = p[1] - 1024LL * (v / dimensions[0]);
            require(dx >= -200 && dx <= 200 && dy >= -200 && dy <= 200, "grid jitter exceeds bound");
        }
    }

    std::vector<bool> seen_ids(m), seen_weights(m);
    std::unordered_set<std::uint64_t> pairs;
    std::set<std::pair<int, int>> scaffold;
    std::vector<std::vector<int>> adjacent(n);
    std::vector<std::pair<std::uint64_t, int>> ranked(m);
    Graph line_tree;
    for (const auto& edge : fixture.graph) {
        const auto [u, v, weight, id] = edge;
        require(u >= 0 && u < n && v >= 0 && v < n && u != v, "invalid endpoint or loop");
        require(id >= 0 && id < m && !seen_ids[id], "ID permutation invalid");
        require(weight >= 1 && weight <= m && !seen_weights[weight - 1], "weight permutation invalid");
        seen_ids[id] = true; seen_weights[weight - 1] = true;
        require(pairs.insert(pair_key(u, v)).second, "parallel edge");
        adjacent[u].push_back(v); adjacent[v].push_back(u);
        int a = original[u], b = original[v];
        if (a > b) std::swap(a, b);
        if (id < base) {
            scaffold.emplace(a, b);
            if (line) { require(b == a + 1, "line scaffold skips a neighbor"); line_tree.push_back(edge); }
            else require((b == a + 1 && a / dimensions[0] == b / dimensions[0]) ||
                         b == a + dimensions[0], "grid scaffold has a non-neighbor edge");
        }
        if (!gnm) {
            const auto& pa = fixture.original_positions[a];
            const auto& pb = fixture.original_positions[b];
            // Independent reconstruction does not call the generator's key helper.
            const auto dx = pa[0] - pb[0], dy = pa[1] - pb[1];
            const std::uint64_t key = line ? static_cast<std::uint64_t>(pb[0] - pa[0])
                                          : static_cast<std::uint64_t>(dx * dx + dy * dy);
            require(key > 0, "zero geometric edge length");
            ranked[weight - 1] = {key, id};
        }
    }
    require(scaffold.size() == static_cast<std::size_t>(base), "scaffold edges repeat");
    for (int v = 0; v < n; ++v) {
        if (gnm) continue;
        if (line) { if (v + 1 < n) require(scaffold.count({v, v + 1}) == 1, "missing path edge"); }
        else {
            if (v % dimensions[0] + 1 < dimensions[0])
                require(scaffold.count({v, v + 1}) == 1, "missing horizontal grid edge");
            if (v / dimensions[0] + 1 < dimensions[1])
                require(scaffold.count({v, v + dimensions[0]}) == 1, "missing vertical grid edge");
        }
    }
    std::queue<int> pending;
    std::vector<bool> visited(n);
    pending.push(0); visited[0] = true;
    int reached = 0;
    while (!pending.empty()) {
        const int u = pending.front(); pending.pop(); ++reached;
        for (int v : adjacent[u]) if (!visited[v]) { visited[v] = true; pending.push(v); }
    }
    require(reached == n, "fixture disconnected");
    if (metric) {
        require(std::is_sorted(ranked.begin(), ranked.end()), "metric ranks violate exact length/ID order");
        const auto twin = benchmark_crossover::make_fixture({line ? "line_random" : "grid2d_random", n, spec.density}, seed);
        paired_check(fixture, twin);
    }
    if (!check_mst) return 0;
    const auto oracle = kruskal(fixture.graph, n);
    benchmark_validation::certify_mst(fixture.graph, oracle, n);
    const auto expected = ids(oracle);
    if (line && metric) {
        // Every cut between successive positions has its unique shortest
        // crossing edge in the path, regardless of all added shortcuts.
        benchmark_validation::certify_mst(fixture.graph, line_tree, n);
        require(expected == ids(line_tree), "line-distance MST differs from adjacent-path oracle");
    }
    for (unsigned sampling_seed : {0u, 1u, 7u}) {
        problem input(n, fixture.graph);
        require(kkt(input, sampling_seed) == expected, "KKT differs from certified exact MST");
    }
    return 3;
}

template<class Action> void require_rejected(Action action, const std::string& message) {
    bool rejected = false;
    try { action(); } catch (const std::runtime_error&) { rejected = true; }
    require(rejected, message);
}

void check_moments_against_bfs(const Graph& graph, int n, const std::vector<int>& selected,
                             const benchmark_diagnostics::ComponentMoments& moments) {
    std::unordered_set<int> selected_set(selected.begin(), selected.end());
    require(selected_set.size() == selected.size(), "contraction selected an ID twice");
    std::vector<std::vector<int>> adjacent(n);
    for (const auto& [u, v, weight, id] : graph) {
        (void)weight;
        if (selected_set.count(id)) { adjacent[u].push_back(v); adjacent[v].push_back(u); }
    }
    std::vector<bool> visited(n);
    int count = 0, largest = 0;
    std::uint64_t squares = 0;
    for (int start = 0; start < n; ++start) if (!visited[start]) {
        int size = 0;
        std::queue<int> pending;
        pending.push(start); visited[start] = true;
        while (!pending.empty()) {
            const int u = pending.front(); pending.pop(); ++size;
            for (int v : adjacent[u]) if (!visited[v]) { visited[v] = true; pending.push(v); }
        }
        ++count;
        largest = std::max(largest, size);
        squares += static_cast<std::uint64_t>(size) * size;
    }
    require(moments.count() == count && moments.max_size() == largest &&
            moments.sum_squares() == squares, "component moments differ from independent BFS");
    require(moments.count() == n - static_cast<int>(selected.size()), "selected-forest count identity failed");
}

void check_component_moments() {
    using benchmark_diagnostics::ComponentMoments;
    const Graph graph{{2, 3, 30, 1}, {0, 1, 10, 2}, {1, 2, 20, 0}};
    ComponentMoments moments(graph, 5);
    require(moments.count() == 5 && moments.sum_squares() == 5 && moments.max_size() == 1,
            "initial isolated moments wrong");
    moments.accept_selected({2});
    require(moments.count() == 4 && moments.sum_squares() == 7 && moments.max_size() == 2,
            "first selected pair moments wrong");
    moments.accept_selected({1});
    require(moments.count() == 3 && moments.sum_squares() == 9 && moments.max_size() == 2,
            "two disjoint pairs moments wrong");
    moments.accept_selected({0});
    check_moments_against_bfs(graph, 5, {2, 1, 0}, moments);
    require(moments.count() == 2 && moments.sum_squares() == 17 && moments.max_size() == 4,
            "uneven component moments wrong");
    for (int invalid : {-1, 0, 3})
        require_rejected([&] { moments.accept_selected({invalid}); }, "invalid selected ID accepted");
    const Graph cycle{{0, 1, 1, 0}, {1, 2, 2, 1}, {0, 2, 3, 2}};
    ComponentMoments cycle_moments(cycle, 3);
    cycle_moments.accept_selected({0, 1});
    require_rejected([&] { cycle_moments.accept_selected({2}); }, "cycle-forming selected edge accepted");
    const Graph empty;
    ComponentMoments zero(empty, 0);
    zero.accept_selected({});
    require(zero.count() == 0 && zero.sum_squares() == 0 && zero.max_size() == 0, "empty moments wrong");
    for (const Graph& bad : {Graph{{0, 1, 1, 1}}, Graph{{0, 1, 1, -1}},
         Graph{{0, 1, 1, 0}, {1, 2, 2, 0}}, Graph{{0, 3, 1, 0}}, Graph{{0, 0, 1, 0}}})
        require_rejected([&] { ComponentMoments invalid(bad, 3); }, "invalid input graph accepted by moments");
    require_rejected([&] { ComponentMoments invalid(empty, -1); }, "negative vertex count accepted");

    // Verify 64-bit accumulation without allocating a large dense graph.
    Graph star;
    std::vector<int> selected;
    for (int v = 1; v < 65536; ++v) { star.emplace_back(0, v, v, v - 1); selected.push_back(v - 1); }
    ComponentMoments large(star, 65536);
    large.accept_selected(selected);
    require(large.count() == 1 && large.max_size() == 65536 &&
            large.sum_squares() == (std::uint64_t{1} << 32), "component second moment overflowed 32 bits");

    for (const char* family : benchmark_crossover::families) {
        const auto fixture = benchmark_crossover::make_fixture(
            {family, 128, std::string(family) == "gnm_random" ? 16 : 8}, 42);
        ComponentMoments actual(fixture.graph, 128);
        std::vector<int> cumulative;
        problem current(128, fixture.graph);
        check_moments_against_bfs(fixture.graph, 128, cumulative, actual);
        while (!current.graph_edges.empty()) {
            auto round = boruvka_step(current);
            require(!round.first.empty(), "nonempty connected contraction made no progress");
            actual.accept_selected(round.first);
            cumulative.insert(cumulative.end(), round.first.begin(), round.first.end());
            check_moments_against_bfs(fixture.graph, 128, cumulative, actual);
            require(actual.count() == (round.second.graph_edges.empty() ? 1 : round.second.num_vertices),
                    "original-vertex component count differs from contraction output");
            current = std::move(round.second);
        }
        require(actual.count() == 1 && actual.sum_squares() == 128ULL * 128 && actual.max_size() == 128,
                "terminal component moments wrong");
    }
}
} // namespace

int main() {
    try {
        int fixtures = 0, mst_checks = 0;
        for (const char* family : {"line_metric", "line_random", "grid2d_metric", "grid2d_random"})
            for (int n : {32, 128, 1024})
                for (int density : {2, 8})
                    for (unsigned seed : {17u, 42u, 999u}) {
                        mst_checks += check({family, n, density}, seed, true); ++fixtures;
                    }
        for (const char* family : {"line_metric", "line_random", "grid2d_metric", "grid2d_random"}) {
            mst_checks += check({family, 32, 15}, 17, true); ++fixtures;
            mst_checks += check({family, 4096, 16}, 42, false); ++fixtures;
        }
        for (const char* family : {"line_metric", "line_random"}) {
            mst_checks += check({family, 128, 1}, 999, true); ++fixtures;
        }
        for (int n : {128, 1024}) for (unsigned seed : {17u, 42u, 999u}) {
            mst_checks += check({"gnm_random", n, 16}, seed, true); ++fixtures;
        }
        mst_checks += check({"gnm_random", 128, 32}, 999, true); ++fixtures;
        mst_checks += check({"gnm_random", 4096, 16}, 42, false); ++fixtures;
        require(!benchmark_crossover::detail::connected(Graph{{0, 1, 1, 0}, {2, 3, 2, 1}}, 4),
                "G(n,m) rejection predicate accepted disconnected graph");
        require(benchmark_crossover::detail::connected(Graph{{0, 1, 1, 0}, {1, 2, 2, 1}}, 3),
                "G(n,m) rejection predicate rejected connected graph");
        for (const Spec& bad : {Spec{"unknown", 32, 2}, Spec{"line_metric", 16, 2},
             Spec{"line_random", 96, 2}, Spec{"grid2d_metric", 32, 1},
             Spec{"line_metric", 32, 16}, Spec{"grid2d_random", 128, 0},
             Spec{"line_metric", 1 << 23, 16}, Spec{"line_metric", 1 << 22, 512},
             Spec{"gnm_random", 128, 15}, Spec{"gnm_random", 32, 16}}) {
            bool rejected = false;
            try { benchmark_crossover::edge_count(bad); }
            catch (const std::runtime_error&) { rejected = true; }
            require(rejected, "invalid crossover specification accepted");
        }
        require(benchmark_crossover::edge_count({"line_metric", 1 << 22, 16}) == 67108864,
                "maximum planned line dimensions rejected");
        require(benchmark_crossover::grid_dimensions(1 << 22) == std::array<int, 2>{2048, 2048},
                "maximum grid dimensions invalid");
        const std::int64_t longest_line = ((std::int64_t{1} << 22) - 1) * 1024;
        require(benchmark_crossover::detail::distance_key(true, {0, 0}, {longest_line, 0}) ==
                static_cast<std::uint64_t>(longest_line), "line distance truncated above INT_MAX");
        check_component_moments();
        std::cout << "Validated " << fixtures << " crossover fixtures, " << mst_checks
                  << " KKT/certificate checks, geometry/twins, line-MST oracle, component moments, and invalid domains.\n";
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
