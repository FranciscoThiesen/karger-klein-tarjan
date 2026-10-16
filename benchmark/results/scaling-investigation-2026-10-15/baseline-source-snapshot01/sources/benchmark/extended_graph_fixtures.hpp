#ifndef BENCHMARK_EXTENDED_GRAPH_FIXTURES_HPP
#define BENCHMARK_EXTENDED_GRAPH_FIXTURES_HPP

#include "graph_fixtures.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

// Additional bounded synthetic models. Existing fixtures remain untouched.
// All new families are connected, simple, undirected graphs. Every new graph
// receives one global permutation of weights 1..m, then shuffled vertex labels
// and edge order. No topology class receives preferentially light/heavy weights.
// Separate seeded streams keep weight/label/order draws out of topology code;
// shuffles use the same explicit Fisher-Yates helper as the original fixtures.
namespace benchmark_extended {
using benchmark_fixtures::Case;
using benchmark_fixtures::Graph;

inline constexpr std::array<const char*, 8> families = {
    "preferential_attachment", "small_world", "multi_hub", "community_sparse",
    "balanced_bipartite", "balanced_binary_tree", "hub", "random_4"
};

inline bool supported_size(int n) {
    return n == 256 || n == 4096 || n == 16384 || n == 65536;
}

inline std::size_t expected_edge_count(const Case& item) {
    if (!supported_size(item.n))
        throw std::runtime_error("extended fixtures require n=256,4096,16384,65536");
    const auto n = static_cast<std::size_t>(item.n);
    if (item.family == "preferential_attachment") return 4 * n - 10;
    if (item.family == "multi_hub") return 4 * n - 49;
    if (item.family == "balanced_binary_tree") return n - 1;
    if (item.family == "small_world" || item.family == "community_sparse" ||
        item.family == "balanced_bipartite" || item.family == "hub" ||
        item.family == "random_4") return 4 * n;
    throw std::runtime_error("unknown extended graph family: " + item.family);
}

inline std::vector<Case> cases(bool smoke = false) {
    std::vector<Case> result;
    for (const char* family : families) {
        if (smoke) result.push_back({family, 256});
        else for (int n : {4096, 16384, 65536}) result.push_back({family, n});
    }
    std::mt19937 order_rng(20261010);
    benchmark_fixtures::shuffle(result, order_rng);
    return result;
}

namespace detail {

// Explicit rejection sampling avoids modulo bias and library-dependent
// uniform_int_distribution mappings for the topology draws.
inline std::uint32_t draw(std::mt19937& rng, std::uint32_t bound) {
    if (bound == 0) throw std::runtime_error("empty extended-fixture draw domain");
    const std::uint32_t threshold = (std::uint32_t{0} - bound) % bound;
    std::uint32_t value;
    do { value = static_cast<std::uint32_t>(rng()); } while (value < threshold);
    return value % bound;
}

inline std::uint64_t pair_key(int u, int v) {
    if (u > v) std::swap(u, v);
    return (static_cast<std::uint64_t>(u) << 32) | static_cast<unsigned int>(v);
}

inline void randomize_records(Graph& graph, int n, unsigned int seed) {
    std::mt19937 weight_rng(seed ^ 0x9e3779b9U);
    std::mt19937 label_rng(seed ^ 0x243f6a88U);
    std::mt19937 order_rng(seed ^ 0xb7e15162U);
    std::vector<int> positions(graph.size());
    std::iota(positions.begin(), positions.end(), 0);
    benchmark_fixtures::shuffle(positions, weight_rng);
    for (std::size_t rank = 0; rank < positions.size(); ++rank)
        std::get<2>(graph[positions[rank]]) = static_cast<int>(rank) + 1;

    std::vector<int> labels(n);
    std::iota(labels.begin(), labels.end(), 0);
    benchmark_fixtures::shuffle(labels, label_rng);
    for (auto& edge : graph) {
        std::get<0>(edge) = labels[std::get<0>(edge)];
        std::get<1>(edge) = labels[std::get<1>(edge)];
    }
    benchmark_fixtures::shuffle(graph, order_rng);
}

} // namespace detail

inline Graph make_graph(const Case& item, unsigned int seed) {
    const auto target = expected_edge_count(item); // Validate before allocating.
    if (item.family == "hub" || item.family == "random_4")
        return benchmark_fixtures::make_graph(item, seed);

    const int n = item.n;
    std::mt19937 rng(seed);
    benchmark_fixtures::Builder builder;
    builder.edges.reserve(target);
    builder.pairs.reserve(target);
    const auto draw = [&](int bound) {
        return static_cast<int>(detail::draw(rng, static_cast<std::uint32_t>(bound)));
    };

    if (item.family == "preferential_attachment") {
        // Simple BA-style model: begin with K5; each later vertex chooses four
        // distinct older targets proportional to their current degrees.
        // Repeated urn entries are degree tickets, not distinct neighbors.
        // Select all four targets before appending this vertex's tickets, so
        // the new vertex can never select itself. m = 10 + 4(n-5) = 4n-10.
        std::vector<int> urn;
        urn.reserve(2 * target);
        const auto attach = [&](int u, int v) {
            if (!builder.add(u, v))
                throw std::runtime_error("duplicate preferential-attachment edge");
            urn.push_back(u);
            urn.push_back(v);
        };
        for (int u = 0; u < 5; ++u)
            for (int v = u + 1; v < 5; ++v) attach(u, v);
        for (int v = 5; v < n; ++v) {
            std::array<int, 4> chosen{};
            int count = 0;
            while (count < 4) {
                const int candidate = urn[detail::draw(
                    rng, static_cast<std::uint32_t>(urn.size()))];
                if (std::find(chosen.begin(), chosen.begin() + count, candidate) ==
                    chosen.begin() + count) chosen[count++] = candidate;
            }
            for (int u : chosen) attach(u, v);
        }
    } else if (item.family == "small_world") {
        // Connected Watts-Strogatz-like variant, not the unrestricted model:
        // start with clockwise offsets 1..4 (degree 8, m=4n). Protect offset 1
        // as a cycle. Rewire each original offset-2..4 edge with probability
        // 1/10, retaining its original source and choosing uniformly among
        // current non-neighbors. Excluding the old target forces an actual
        // change; skip if the source has no non-neighbor. Each edge slot and
        // ID survive; duplicates/loops cannot arise.
        for (int offset = 1; offset <= 4; ++offset)
            for (int u = 0; u < n; ++u) builder.add(u, (u + offset) % n);
        std::vector<int> degree(n, 8);
        for (int offset = 2; offset <= 4; ++offset) {
            for (int u = 0; u < n; ++u) {
                if (draw(10) != 0 || degree[u] == n - 1) continue;
                int v;
                do { v = draw(n); }
                while (v == u || builder.pairs.count(detail::pair_key(u, v)) != 0);
                const auto index = static_cast<std::size_t>((offset - 1) * n + u);
                auto& edge = builder.edges[index];
                const int old_target = std::get<0>(edge) == u
                    ? std::get<1>(edge) : std::get<0>(edge);
                if (builder.pairs.erase(detail::pair_key(std::get<0>(edge),
                                                        std::get<1>(edge))) != 1)
                    throw std::runtime_error("missing small-world edge during rewiring");
                builder.pairs.insert(detail::pair_key(u, v));
                --degree[old_target];
                ++degree[v];
                std::get<0>(edge) = std::min(u, v);
                std::get<1>(edge) = std::max(u, v);
            }
        }
    } else if (item.family == "multi_hub") {
        // Sixteen hubs form a random recursive tree. Every nonhub chooses
        // four distinct hubs uniformly. No nonhub-nonhub edges.
        // m = 15 + 4(n-16) = 4n-49; all weights are assigned globally later.
        constexpr int hubs = 16;
        for (int h = 1; h < hubs; ++h) builder.add(h, draw(h));
        for (int v = hubs; v < n; ++v) {
            int added = 0;
            while (added < 4) if (builder.add(v, draw(hubs))) ++added;
        }
    } else if (item.family == "community_sparse") {
        // Sixteen equal communities each contain a random recursive tree.
        // A random recursive tree on communities connects random endpoints.
        // Fill to exactly max(15,n/64) cross edges and 4n total edges. Additional
        // cross pairs and internal pairs are uniform among the corresponding
        // missing pairs. This is a connected block-model variant, not G(n,p)
        // or a uniform draw from all connected graphs. No weight separation.
        constexpr int communities = 16;
        const int size = n / communities;
        for (int c = 0; c < communities; ++c)
            for (int v = 1; v < size; ++v)
                builder.add(c * size + v, c * size + draw(v));
        for (int c = 1; c < communities; ++c) {
            const int parent = draw(c);
            const int u = c * size + draw(size);
            const int v = parent * size + draw(size);
            builder.add(u, v);
        }
        const int cross_target = std::max(communities - 1, n / 64);
        int cross_edges = communities - 1;
        while (cross_edges < cross_target) {
            const int u = draw(n), v = draw(n);
            if (u / size != v / size && builder.add(u, v)) ++cross_edges;
        }
        while (builder.edges.size() < target) {
            const int c = draw(communities);
            const int u = c * size + draw(size), v = c * size + draw(size);
            builder.add(u, v);
        }
    } else if (item.family == "balanced_bipartite") {
        // Equal even/odd partitions. Each vertex joins one uniformly chosen
        // older vertex in the opposite partition, producing a connected tree.
        // Add uniformly chosen missing cross-partition pairs until m=4n.
        // The connected-tree seed makes this a model variant, not uniform G(n,m).
        for (int v = 1; v < n; ++v) {
            const int opposite_count = (v + 1) / 2;
            const int parent = 2 * draw(opposite_count) + (v % 2 == 0 ? 1 : 0);
            builder.add(parent, v);
        }
        while (builder.edges.size() < target) {
            const int u = 2 * draw(n / 2), v = 2 * draw(n / 2) + 1;
            builder.add(u, v);
        }
    } else if (item.family == "balanced_binary_tree") {
        // Heap-indexed complete binary-tree shape: parent(v)=floor((v-1)/2),
        // m=n-1. The last level may be incomplete; labels/weights/order vary.
        for (int v = 1; v < n; ++v) builder.add((v - 1) / 2, v);
    }

    if (builder.edges.size() != target || builder.pairs.size() != target)
        throw std::runtime_error("extended fixture has an unexpected edge count");
    detail::randomize_records(builder.edges, n, seed);
    return std::move(builder.edges);
}

} // namespace benchmark_extended

#endif
