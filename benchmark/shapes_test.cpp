// Structural checks protect the meaning of the new benchmark families.
#include "extended_graph_fixtures.hpp"

#include <iostream>
#include <queue>
#include <stdexcept>
#include <unordered_set>

namespace {
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

void check(const benchmark_fixtures::Case& item, unsigned seed) {
    const auto graph = benchmark_extended::make_graph(item, seed);
    const int n = item.n;
    const auto& family = item.family;
    const int m = family == "preferential_attachment" ? 4 * n - 10
                : family == "multi_hub" ? 4 * n - 49
                : family == "balanced_binary_tree" ? n - 1 : 4 * n;
    require(graph.size() == static_cast<std::size_t>(m), "wrong edge count");
    require(graph == benchmark_extended::make_graph(item, seed), "fixture is not reproducible");
    if (family == "hub" || family == "random_4")
        require(graph == benchmark_fixtures::make_graph(item, seed), "control fixture changed");

    std::vector<std::vector<int>> adjacent(n);
    std::vector<bool> ids(m), weights(m);
    std::unordered_set<std::uint64_t> edges;
    for (const auto& [u, v, w, id] : graph) {
        require(u >= 0 && u < n && v >= 0 && v < n && u != v, "invalid endpoints");
        require(id >= 0 && id < m && !ids[id], "invalid or repeated ID");
        require(w >= 1 && w <= m && !weights[w - 1], "weights are not a unique rank permutation");
        ids[id] = true;
        weights[w - 1] = true;
        const auto key = (static_cast<std::uint64_t>(std::min(u, v)) << 32) |
                         static_cast<unsigned>(std::max(u, v));
        require(edges.insert(key).second, "parallel edges");
        adjacent[u].push_back(v);
        adjacent[v].push_back(u);
    }
    std::queue<int> pending;
    std::vector<int> color(n, -1);
    color[0] = 0;
    pending.push(0);
    int visited = 0;
    while (!pending.empty()) {
        const int u = pending.front(); pending.pop(); ++visited;
        for (int v : adjacent[u]) {
            if (family == "balanced_bipartite")
                require(color[v] < 0 || color[v] != color[u], "bipartite fixture has an odd cycle");
            if (color[v] < 0) { color[v] = 1 - color[u]; pending.push(v); }
        }
    }
    require(visited == n, "fixture is disconnected");
    if (family == "balanced_bipartite")
        require(std::count(color.begin(), color.end(), 0) == n / 2, "bipartition is not balanced");
    if (family == "balanced_binary_tree") {
        int leaves = 0;
        for (const auto& neighbors : adjacent) {
            require(neighbors.size() <= 3, "binary tree has excessive degree");
            leaves += neighbors.size() == 1;
        }
        require(leaves == n / 2, "binary tree has wrong leaf count");
    }
    if (family == "multi_hub") {
        int periphery = 0;
        for (const auto& neighbors : adjacent) periphery += neighbors.size() == 4;
        require(periphery == n - 16, "multi-hub periphery does not have four hub neighbors");
    }
}
}

int main() {
    try {
        int checked = 0;
        for (bool smoke : {true, false}) {
            const auto cases = benchmark_extended::cases(smoke);
            require(cases.size() == (smoke ? 8u : 24u), "wrong preset case count");
            std::unordered_set<std::string> unique;
            for (const auto& item : cases) {
                require(unique.insert(item.family + std::to_string(item.n)).second, "duplicate case");
                for (unsigned seed : {17u, 42u, 999u}) { check(item, seed); ++checked; }
            }
        }
        for (const benchmark_fixtures::Case& bad : {
                 benchmark_fixtures::Case{"unknown", 256},
                 benchmark_fixtures::Case{"small_world", 1},
                 benchmark_fixtures::Case{"multi_hub", 1000}}) {
            bool rejected = false;
            try { benchmark_extended::make_graph(bad, 17); }
            catch (const std::exception&) { rejected = true; }
            require(rejected, "unsupported fixture accepted");
        }
        std::cout << "Validated " << checked << " seeded fixtures, unchanged controls, and invalid inputs.\n";
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
