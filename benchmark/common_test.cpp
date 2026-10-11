// Structural tests protect the graph models independently of MST timings.
#include "common_graph_fixtures.hpp"

#include <iostream>
#include <queue>
#include <stdexcept>
#include <unordered_set>

namespace {
using benchmark_fixtures::Case;

void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

std::uint64_t pair_key(int u, int v) {
    if (u > v) std::swap(u, v);
    return (static_cast<std::uint64_t>(u) << 32) | static_cast<unsigned int>(v);
}

int expected_core(const Case& item) {
    if (item.family == "unbalanced_bipartite_16") return 16;
    if (item.family == "unbalanced_bipartite_256") return 256;
    if (item.family == "unbalanced_bipartite_sqrt") {
        int k = 1;
        while ((k + 1) * (k + 1) <= item.n) ++k;
        return k;
    }
    return 0;
}

std::array<int, 3> independent_dimensions(const Case& item) {
    const int axes = item.family.find("grid2d") == 0 ? 2 : 3;
    std::array<int, 3> dimensions{1, 1, 1};
    int remaining = item.n;
    for (int axis = 0; remaining > 1; axis = (axis + 1) % axes) {
        dimensions[axis] *= 2;
        remaining /= 2;
    }
    return dimensions;
}

std::size_t independent_edge_count(const Case& item) {
    if (const int k = expected_core(item)) return 4u * (item.n - k);
    if (item.family == "leaf_core_50") return item.n + 3u * (item.n / 2);
    if (item.family == "leaf_core_90") return item.n + 3u * (item.n / 10);
    if (item.family == "ring_cliques_16") return (item.n / 16) * (16u * 15 / 2 + 1);
    if (item.family.find("grid") == 0) {
        const auto dimensions = independent_dimensions(item);
        const int x = dimensions[0], y = dimensions[1], z = dimensions[2];
        return (x - 1u) * y * z + x * (y - 1u) * z + x * y * (z - 1u);
    }
    return 4u * item.n;
}

void check(const Case& item, unsigned seed) {
    const auto fixture = benchmark_common::make_fixture(item, seed);
    const auto& graph = fixture.graph;
    const auto& family = item.family;
    const int n = item.n, m = static_cast<int>(independent_edge_count(item));
    require(graph.size() == static_cast<std::size_t>(m), "incorrect model edge count");
    require(graph.size() == benchmark_common::expected_edge_count(item), "edge-count helper disagrees");
    const auto replay = benchmark_common::make_fixture(item, seed);
    require(graph == replay.graph && fixture.positions == replay.positions &&
            fixture.original_to_label == replay.original_to_label, "fixture replay changed");
    const bool control = family == "hub" || family == "random_4";
    if (control) {
        require(graph == benchmark_fixtures::make_graph(item, seed), "original control changed");
        require(fixture.positions.empty() && fixture.original_to_label.empty(), "control invents metadata");
    }

    std::vector<int> original(n, -1);
    if (!control) {
        require(fixture.original_to_label.size() == static_cast<std::size_t>(n), "missing vertex map");
        for (int v = 0; v < n; ++v) {
            const int label = fixture.original_to_label[v];
            require(label >= 0 && label < n && original[label] == -1, "vertex labels not a permutation");
            original[label] = v;
        }
    }
    std::vector<std::vector<int>> adjacent(n);
    std::vector<bool> ids(m), weights(m);
    std::unordered_set<std::uint64_t> pairs;
    std::vector<std::pair<int, int>> original_edges(m);
    for (const auto& [u, v, weight, id] : graph) {
        require(u >= 0 && u < n && v >= 0 && v < n && u != v, "invalid graph endpoints");
        require(id >= 0 && id < m && !ids[id], "edge IDs not a permutation");
        require(weight >= 1 && weight <= m && !weights[weight - 1], "weights not distinct ranks");
        ids[id] = true;
        weights[weight - 1] = true;
        require(pairs.insert(pair_key(u, v)).second, "parallel edge in simple fixture");
        adjacent[u].push_back(v);
        adjacent[v].push_back(u);
        if (!control) original_edges[id] = {original[u], original[v]};
    }
    std::queue<int> pending;
    std::vector<bool> visited(n);
    pending.push(0);
    visited[0] = true;
    int count = 0;
    while (!pending.empty()) {
        const int u = pending.front(); pending.pop(); ++count;
        for (int v : adjacent[u]) if (!visited[v]) { visited[v] = true; pending.push(v); }
    }
    require(count == n, "fixture is disconnected");

    if (const int k = expected_core(item)) {
        for (const auto& [u, v] : original_edges)
            require((u < k) != (v < k), "edge violates the bipartition");
        for (int v = k; v < n; ++v)
            require(adjacent[fixture.original_to_label[v]].size() == 4, "peripheral degree differs from four");
        for (int v = 0; v < k; ++v) {
            const int peripheral = fixture.original_to_label[k + v];
            require(pairs.count(pair_key(peripheral, fixture.original_to_label[v])) == 1 &&
                    pairs.count(pair_key(peripheral, fixture.original_to_label[(v + 1) % k])) == 1,
                    "bipartite connecting cycle changed");
        }
    } else if (family == "leaf_core_50" || family == "leaf_core_90") {
        const int core = family == "leaf_core_50" ? n / 2 : n / 10;
        int internal = 0;
        for (const auto& [u, v] : original_edges) {
            require(u < core || v < core, "edge joins two designated leaves");
            internal += u < core && v < core;
        }
        require(internal == 4 * core, "core has wrong density");
        for (int v = core; v < n; ++v)
            require(adjacent[fixture.original_to_label[v]].size() == 1, "designated leaf is not degree one");
    } else if (family == "ring_cliques_16") {
        std::vector<int> internal(n / 16), bridges(n / 16);
        for (const auto& [u, v] : original_edges) {
            const int a = u / 16, b = v / 16;
            if (a == b) ++internal[a];
            else if ((a + 1) % (n / 16) == b) ++bridges[a];
            else if ((b + 1) % (n / 16) == a) ++bridges[b];
            else require(false, "bridge does not join neighboring cliques");
        }
        for (int value : internal) require(value == 120, "clique is incomplete");
        for (int value : bridges) require(value == 1, "clique cycle has wrong bridge count");
    } else if (family == "regular_8") {
        for (const auto& neighbors : adjacent) require(neighbors.size() == 8, "regular degree changed");
        for (int v = 0; v < n; ++v)
            require(pairs.count(pair_key(fixture.original_to_label[v],
                    fixture.original_to_label[(v + 1) % n])) == 1, "protected cycle edge changed");
    }

    const bool spatial = family.find("grid") == 0;
    require(spatial == !fixture.positions.empty(), "coordinates missing or attached to nonspatial model");
    if (spatial) {
        const auto dimensions = independent_dimensions(item);
        require(dimensions == benchmark_common::grid_dimensions(item), "grid dimensions changed");
        require(fixture.positions.size() == static_cast<std::size_t>(n), "wrong coordinate count");
        const std::array<int, 3> stride{1, dimensions[0], dimensions[0] * dimensions[1]};
        for (int v = 0; v < n; ++v) {
            int expected_degree = 0;
            for (int axis = 0; axis < 3; ++axis) {
                const int index = v / stride[axis] % dimensions[axis];
                const double point = fixture.positions[fixture.original_to_label[v]][axis];
                require(std::abs(point - index) <= 200.0 / 1024, "coordinate jitter exceeds bound");
                require(point * 1024 == std::floor(point * 1024), "coordinates not fixed-point");
                expected_degree += (index > 0) + (index + 1 < dimensions[axis]);
            }
            require(adjacent[fixture.original_to_label[v]].size() == static_cast<std::size_t>(expected_degree),
                    "open-grid degree changed");
        }
        for (const auto& [u, v] : original_edges) {
            int manhattan = 0;
            for (int axis = 0; axis < 3; ++axis)
                manhattan += std::abs(u / stride[axis] % dimensions[axis] - v / stride[axis] % dimensions[axis]);
            require(manhattan == 1, "grid contains a non-neighbor edge");
        }
        if (family.find("distance") != std::string::npos) {
            std::vector<std::pair<std::int64_t, int>> ranked(m);
            for (const auto& [u, v, weight, id] : graph) {
                std::int64_t distance = 0;
                for (int axis = 0; axis < 3; ++axis) {
                    const auto delta = static_cast<std::int64_t>(
                        1024 * (fixture.positions[u][axis] - fixture.positions[v][axis]));
                    distance += delta * delta;
                }
                ranked[weight - 1] = {distance, id};
            }
            require(std::is_sorted(ranked.begin(), ranked.end()), "distance weights violate length/ID order");
            const std::string partner = family.substr(0, 6) + "_random";
            const auto paired = benchmark_common::make_fixture({partner, n}, seed);
            require(fixture.positions == paired.positions && fixture.original_to_label == paired.original_to_label,
                    "paired spatial geometry or labels changed");
            int changed_weights = 0;
            for (int i = 0; i < m; ++i) {
                const auto& a = graph[i]; const auto& b = paired.graph[i];
                require(std::get<0>(a) == std::get<0>(b) && std::get<1>(a) == std::get<1>(b) &&
                        std::get<3>(a) == std::get<3>(b), "paired spatial topology, IDs or edge order changed");
                changed_weights += std::get<2>(a) != std::get<2>(b);
            }
            require(changed_weights > m / 2, "paired weight variants unexpectedly agree");
        }
    }
}
} // namespace

int main() {
    try {
        int checked = 0;
        for (bool smoke : {true, false}) {
            const auto cases = benchmark_common::cases(smoke);
            require(cases.size() == (smoke ? 13u : 52u), "incorrect common case count");
            std::unordered_set<std::string> unique;
            for (const auto& item : cases) {
                require(unique.insert(item.family + std::to_string(item.n)).second, "duplicate common case");
                for (unsigned seed : {17u, 42u, 999u}) { check(item, seed); ++checked; }
            }
        }
        for (const char* family : benchmark_common::families) {
            for (int n : {64, 256}) {
                if (std::string(family) == "unbalanced_bipartite_256" ||
                    (std::string(family) == "leaf_core_90" && n == 64)) continue;
                check({family, n}, 17); ++checked;
            }
        }
        // Odd exponents exercise nonsquare meshes and floor(sqrt(n)); a
        // million-vertex sparse tree-core case checks the optional upper limit.
        for (const Case& item : {Case{"grid2d_distance", 2048}, Case{"grid3d_distance", 8192},
                                Case{"unbalanced_bipartite_sqrt", 32768},
                                Case{"leaf_core_90", 1048576}}) {
            check(item, 999); ++checked;
        }
        for (const Case& bad : {Case{"unknown", 1024}, Case{"regular_8", 512},
                               Case{"grid3d_random", 1000}, Case{"random_4", 2097152},
                               Case{"unbalanced_bipartite_256", 256}, Case{"leaf_core_90", 64}}) {
            bool rejected = false;
            try { benchmark_common::make_fixture(bad, 17); }
            catch (const std::runtime_error&) { rejected = true; }
            require(rejected, "unsupported common fixture accepted");
        }
        std::cout << "Validated " << checked << " common fixtures, paired spatial weights, controls, and invalid inputs.\n";
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
