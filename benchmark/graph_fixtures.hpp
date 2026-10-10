#ifndef BENCHMARK_GRAPH_FIXTURES_HPP
#define BENCHMARK_GRAPH_FIXTURES_HPP

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_set>
#include <vector>

// Shared synthetic fixtures. Keep RNG draws and shuffles stable so published
// timing and logical-work experiments can refer to identical seeded inputs.
namespace benchmark_fixtures {
using Graph = std::vector<std::tuple<int, int, int, int>>;
struct Case { std::string family; int n; };

template<class T> void shuffle(std::vector<T>& values, std::mt19937& rng) {
    // Explicit Fisher-Yates avoids library-specific fixture shuffles.
    for (std::size_t i = values.size(); i > 1; --i)
        std::swap(values[i - 1], values[rng() % i]);
}

struct Builder {
    Graph edges;
    std::unordered_set<std::uint64_t> pairs;
    bool add(int u, int v, int group = 0) {
        if (u == v) return false;
        if (u > v) std::swap(u, v);
        const auto key = (static_cast<std::uint64_t>(u) << 32) | static_cast<unsigned int>(v);
        if (!pairs.insert(key).second) return false;
        edges.emplace_back(u, v, group, static_cast<int>(edges.size()));
        return true;
    }
};

inline Graph make_graph(const Case& item, unsigned int seed, bool smoke = false) {
    const int n = item.n;
    const auto& family = item.family;
    std::mt19937 rng(seed);
    Builder builder;
    auto& graph = builder.edges;
    bool fixed_weights = false;
    if (family == "grid" || family == "geometric_grid") {
        const int side = static_cast<int>(std::sqrt(n));
        if (side * side != n) throw std::runtime_error("grid requires a square vertex count");
        std::vector<double> x(n), y(n), distance;
        for (int v = 0; v < n; ++v) {
            x[v] = v % side + 0.7 * (rng() / 4294967296.0 - 0.5);
            y[v] = v / side + 0.7 * (rng() / 4294967296.0 - 0.5);
        }
        const auto add = [&](int a, int b) {
            if (builder.add(a, b)) {
                const double dx = x[a] - x[b], dy = y[a] - y[b];
                distance.push_back(dx * dx + dy * dy);
            }
        };
        for (int row = 0; row < side; ++row) {
            for (int col = 0; col < side; ++col) {
                const int v = row * side + col;
                if (col + 1 < side) add(v, v + 1);
                if (row + 1 < side) add(v, v + side);
                if (family == "geometric_grid" && row + 1 < side) {
                    if (col + 1 < side) add(v, v + side + 1);
                    if (col > 0) add(v, v + side - 1);
                }
            }
        }
        if (family == "geometric_grid") {
            std::vector<int> order(graph.size());
            std::iota(order.begin(), order.end(), 0);
            std::sort(order.begin(), order.end(), [&](int a, int b) {
                return std::make_pair(distance[a], a) < std::make_pair(distance[b], b);
            });
            for (std::size_t i = 0; i < order.size(); ++i)
                std::get<2>(graph[order[i]]) = static_cast<int>(i) + 1;
            fixed_weights = true;
        }
    } else if (family == "hierarchical_path") {
        for (int v = 1; v < n; ++v) {
            int level = 0;
            for (int x = v; x % 2 == 0; x /= 2) ++level;
            builder.add(v - 1, v, n * level + v);
        }
        fixed_weights = true;
    } else if (family == "complete") {
        for (int u = 0; u < n; ++u)
            for (int v = u + 1; v < n; ++v) builder.add(u, v);
    } else if (family == "clustered") {
        const int clusters = smoke ? 4 : 16;
        const int size = n / clusters;
        for (int c = 0; c < clusters; ++c) {
            for (int v = 1; v < size; ++v)
                builder.add(c * size + v, c * size + static_cast<int>(rng() % v));
        }
        const std::int64_t capacity = 1LL * clusters * size * (size - 1) / 2;
        const int target = static_cast<int>(std::min<std::int64_t>(16LL * n, capacity / 2));
        while (static_cast<int>(graph.size()) < target) {
            const int c = static_cast<int>(rng() % clusters);
            const int u = c * size + static_cast<int>(rng() % size);
            const int v = c * size + static_cast<int>(rng() % size);
            builder.add(u, v);
        }
        for (int c = 1; c < clusters; ++c) {
            const int u = (c - 1) * size + static_cast<int>(rng() % size);
            const int v = c * size + static_cast<int>(rng() % size);
            builder.add(u, v, 1); // Heavy bridges are the only inter-cluster edges.
        }
    } else {
        const bool star = family == "star" || family == "hub";
        for (int v = 1; v < n; ++v) {
            const int parent = star ? 0 : static_cast<int>(rng() % v);
            builder.add(parent, v);
        }
        std::int64_t target = n - 1;
        if (family == "random_4" || family == "hub" || family == "planted_tree") target = 4LL * n;
        else if (family == "random_32") target = 32LL * n;
        else if (family == "random_128") target = 128LL * n;
        else if (family == "random_512") target = 512LL * n;
        else if (family == "random_dense_anchor") target = smoke ? 1500 : 400000;
        else if (family != "random_tree" && family != "star")
            throw std::runtime_error("unknown graph family: " + family);
        if (smoke) target = std::min<std::int64_t>(target, 3LL * n * (n - 1) / 8);
        const std::int64_t capacity = 1LL * n * (n - 1) / 2;
        if (target < n - 1 || target > capacity || target >= 0x3f3f3f3f)
            throw std::runtime_error("edge target exceeds the simple-graph or shared weight domain");
        while (static_cast<std::int64_t>(graph.size()) < target) {
            const int u = static_cast<int>(rng() % n), v = static_cast<int>(rng() % n);
            builder.add(u, v, family == "planted_tree" ? 1 : 0);
        }
    }
    if (!fixed_weights) {
        std::vector<int> low, high;
        for (std::size_t i = 0; i < graph.size(); ++i)
            (std::get<2>(graph[i]) == 0 ? low : high).push_back(static_cast<int>(i));
        shuffle(low, rng);
        shuffle(high, rng);
        int weight = 0;
        for (int i : low) std::get<2>(graph[i]) = ++weight;
        for (int i : high) std::get<2>(graph[i]) = ++weight;
    }
    std::vector<int> labels(n);
    std::iota(labels.begin(), labels.end(), 0);
    shuffle(labels, rng);
    for (auto& edge : graph) {
        std::get<0>(edge) = labels[std::get<0>(edge)];
        std::get<1>(edge) = labels[std::get<1>(edge)];
    }
    shuffle(graph, rng);
    return std::move(graph);
}

} // namespace benchmark_fixtures

#endif
