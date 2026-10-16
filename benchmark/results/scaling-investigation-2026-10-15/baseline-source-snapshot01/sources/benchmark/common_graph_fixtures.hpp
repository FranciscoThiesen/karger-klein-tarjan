#ifndef BENCHMARK_COMMON_GRAPH_FIXTURES_HPP
#define BENCHMARK_COMMON_GRAPH_FIXTURES_HPP

#include "graph_fixtures.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

// Bounded, explicitly defined connected models, not uniform draws from all
// graphs with the corresponding topology label. Existing controls are forwarded
// without changing any RNG draws. All new weights are distinct ranks 1..m;
// only the distance variants correlate their ranks with geometric positions.
namespace benchmark_common {
using benchmark_fixtures::Case;
using benchmark_fixtures::Graph;

inline constexpr std::array<const char*, 13> families = {
    "unbalanced_bipartite_16", "unbalanced_bipartite_256",
    "unbalanced_bipartite_sqrt", "leaf_core_50", "leaf_core_90",
    "ring_cliques_16", "grid2d_random", "grid2d_distance",
    "grid3d_random", "grid3d_distance", "regular_8", "hub", "random_4"
};

inline bool supported_size(int n) {
    return n == 64 || n == 256 ||
        (n >= 1024 && n <= 1048576 && (n & (n - 1)) == 0);
}

inline bool is_grid(const std::string& family) {
    return family == "grid2d_random" || family == "grid2d_distance" ||
           family == "grid3d_random" || family == "grid3d_distance";
}

inline int bipartite_core_size(const Case& item) {
    if (item.family == "unbalanced_bipartite_16") return 16;
    if (item.family == "unbalanced_bipartite_256") return 256;
    if (item.family == "unbalanced_bipartite_sqrt") {
        int k = static_cast<int>(std::sqrt(item.n));
        while (1LL * (k + 1) * (k + 1) <= item.n) ++k;
        while (1LL * k * k > item.n) --k;
        return k;
    }
    return 0;
}

inline int leaf_core_size(const Case& item) {
    if (item.family == "leaf_core_50") return item.n / 2;
    if (item.family == "leaf_core_90") return item.n / 10;
    return 0;
}

// For a dyadic n, balance the binary exponents across axes, giving one extra
// exponent to each earlier axis until exhausted. Unused axes have length one.
inline std::array<int, 3> grid_dimensions(const Case& item) {
    if (!supported_size(item.n) || !is_grid(item.family))
        throw std::runtime_error("grid dimensions require a supported grid case");
    const int axes = item.family.compare(0, 6, "grid2d") == 0 ? 2 : 3;
    int exponent = 0;
    for (int value = item.n; value > 1; value /= 2) ++exponent;
    std::array<int, 3> dimensions{1, 1, 1};
    for (int axis = 0; axis < axes; ++axis)
        dimensions[axis] = 1 << (exponent / axes + (axis < exponent % axes));
    return dimensions;
}

inline std::size_t expected_edge_count(const Case& item) {
    if (!supported_size(item.n))
        throw std::runtime_error("common fixtures require n=64,256 or dyadic 1024..1048576");
    const auto n = static_cast<std::size_t>(item.n);
    if (const int k = bipartite_core_size(item)) {
        if (k < 4 || 2 * k > item.n)
            throw std::runtime_error("bipartite fixture needs at least k peripheral vertices");
        return 4 * (n - static_cast<std::size_t>(k));
    }
    if (const int core = leaf_core_size(item)) {
        if (core < 9)
            throw std::runtime_error("leaf-core fixture needs capacity for 4c core edges");
        return n + 3 * static_cast<std::size_t>(core);
    }
    if (item.family == "ring_cliques_16") return 121 * (n / 16);
    if (is_grid(item.family)) {
        const auto dimensions = grid_dimensions(item);
        std::size_t edges = 0;
        for (int length : dimensions) edges += (length - 1) * (n / length);
        return edges;
    }
    if (item.family == "regular_8" || item.family == "hub" || item.family == "random_4")
        return 4 * n;
    throw std::runtime_error("unknown common graph family: " + item.family);
}

inline std::vector<Case> cases(bool smoke = false) {
    std::vector<Case> result;
    for (const char* family : families) {
        if (smoke) result.push_back({family, 1024});
        else for (int n : {4096, 16384, 65536, 262144}) result.push_back({family, n});
    }
    std::mt19937 order_rng(20261011);
    benchmark_fixtures::shuffle(result, order_rng);
    return result;
}

// Coordinates are indexed by shuffled vertex label, in lattice units. They are
// empty for nonspatial models. New models expose original->shuffled labels for
// structural tests and visualization; old controls leave that map empty.
struct Fixture {
    Graph graph;
    std::vector<std::array<double, 3>> positions;
    std::vector<int> original_to_label;
};

namespace detail {
inline std::uint32_t draw(std::mt19937& rng, std::uint32_t bound) {
    if (!bound) throw std::runtime_error("empty common-fixture draw domain");
    const std::uint32_t threshold = (std::uint32_t{0} - bound) % bound;
    std::uint32_t value;
    do { value = static_cast<std::uint32_t>(rng()); } while (value < threshold);
    return value % bound;
}

inline std::uint64_t pair_key(int u, int v) {
    if (u > v) std::swap(u, v);
    return (static_cast<std::uint64_t>(u) << 32) | static_cast<unsigned int>(v);
}

inline void set_endpoints(std::tuple<int, int, int, int>& edge, int u, int v) {
    std::get<0>(edge) = std::min(u, v);
    std::get<1>(edge) = std::max(u, v);
}
} // namespace detail

inline Fixture make_fixture(const Case& item, unsigned int seed) {
    const auto target = expected_edge_count(item);
    if (item.family == "hub" || item.family == "random_4")
        return {benchmark_fixtures::make_graph(item, seed), {}, {}};
    const int n = item.n;
    std::mt19937 topology_rng(seed);
    std::mt19937 coordinate_rng(seed ^ 0xa4093822U);
    std::mt19937 weight_rng(seed ^ 0x9e3779b9U);
    std::mt19937 label_rng(seed ^ 0x243f6a88U);
    std::mt19937 order_rng(seed ^ 0xb7e15162U);
    const auto draw = [&](int bound) {
        return static_cast<int>(detail::draw(topology_rng, static_cast<std::uint32_t>(bound)));
    };
    benchmark_fixtures::Builder builder;
    builder.edges.reserve(target);
    builder.pairs.reserve(target);
    std::vector<std::array<int, 3>> coordinates;
    bool distance_weights = false;

    if (const int k = bipartite_core_size(item)) {
        // The first k peripheral vertices link consecutive core vertices in a
        // cycle, making the entire core connected without core-core edges.
        // Complete every peripheral vertex to four distinct uniform core
        // neighbors. m=4(n-k). Seeded cycle pairs are topology-only: their
        // weights are randomized together with every other edge.
        for (int v = k; v < n; ++v) {
            int count = 0;
            if (v < 2 * k) {
                builder.add(v, v - k);
                builder.add(v, (v - k + 1) % k);
                count = 2;
            }
            while (count < 4) if (builder.add(v, draw(k))) ++count;
        }
    } else if (const int core = leaf_core_size(item)) {
        // A random recursive tree seeds the core; uniform missing pairs fill
        // it to 4c edges. Each of the n-c remaining vertices attaches once to
        // a uniform core vertex. c=floor(n/2) or floor(n/10), m=n+3c.
        for (int v = 1; v < core; ++v) builder.add(v, draw(v));
        while (builder.edges.size() < static_cast<std::size_t>(4 * core)) {
            const int u = draw(core), v = draw(core);
            builder.add(u, v);
        }
        for (int v = core; v < n; ++v) builder.add(v, draw(core));
    } else if (item.family == "ring_cliques_16") {
        constexpr int size = 16;
        const int cliques = n / size;
        for (int c = 0; c < cliques; ++c)
            for (int u = 0; u < size; ++u)
                for (int v = u + 1; v < size; ++v)
                    builder.add(c * size + u, c * size + v);
        for (int c = 0; c < cliques; ++c) {
            const int u = c * size + draw(size);
            const int v = ((c + 1) % cliques) * size + draw(size);
            builder.add(u, v);
        }
    } else if (is_grid(item.family)) {
        const auto dimensions = grid_dimensions(item);
        const std::array<int, 3> stride{1, dimensions[0], dimensions[0] * dimensions[1]};
        coordinates.resize(n);
        for (int v = 0; v < n; ++v) {
            for (int axis = 0; axis < 3; ++axis) {
                const int index = (v / stride[axis]) % dimensions[axis];
                // Fixed-point jitter keeps rank comparisons exact and replay
                // independent of floating-point sorting. 2D z remains zero.
                const int jitter = dimensions[axis] == 1 ? 0 :
                    static_cast<int>(detail::draw(coordinate_rng, 401)) - 200;
                coordinates[v][axis] = 1024 * index + jitter;
                if (index + 1 < dimensions[axis]) builder.add(v, v + stride[axis]);
            }
        }
        distance_weights = item.family == "grid2d_distance" || item.family == "grid3d_distance";
    } else if (item.family == "regular_8") {
        // Connected nonuniform regular model. Protect offset-1 Hamiltonian
        // cycle; start other edges at offsets2..4. Attempt 20n random two-edge
        // switches on those 3n slots, preserving all degrees. Reject switches
        // with repeated endpoints or existing replacement edges. No claim of
        // mixing to a uniform random regular-graph distribution is made.
        for (int offset = 1; offset <= 4; ++offset)
            for (int u = 0; u < n; ++u) builder.add(u, (u + offset) % n);
        for (int attempt = 0; attempt < 20 * n; ++attempt) {
            const int first = n + draw(3 * n), second = n + draw(3 * n);
            if (first == second) continue;
            auto& a = builder.edges[first];
            auto& b = builder.edges[second];
            const int u = std::get<0>(a), v = std::get<1>(a);
            int x = std::get<0>(b), y = std::get<1>(b);
            if (draw(2)) std::swap(x, y);
            if (u == x || u == y || v == x || v == y) continue;
            const auto ux = detail::pair_key(u, x), vy = detail::pair_key(v, y);
            if (builder.pairs.count(ux) || builder.pairs.count(vy)) continue;
            if (builder.pairs.erase(detail::pair_key(u, v)) != 1 ||
                builder.pairs.erase(detail::pair_key(x, y)) != 1)
                throw std::runtime_error("regular fixture lost an edge during switching");
            builder.pairs.insert(ux);
            builder.pairs.insert(vy);
            detail::set_endpoints(a, u, x);
            detail::set_endpoints(b, v, y);
        }
    }
    if (builder.edges.size() != target || builder.pairs.size() != target)
        throw std::runtime_error("common fixture has an unexpected edge count");

    std::vector<int> weight_order(target);
    std::iota(weight_order.begin(), weight_order.end(), 0);
    if (distance_weights) {
        std::vector<std::int64_t> squared_distance(target);
        for (const auto& [u, v, unused_weight, id] : builder.edges) {
            (void)unused_weight;
            for (int axis = 0; axis < 3; ++axis) {
                const std::int64_t delta = coordinates[u][axis] - coordinates[v][axis];
                squared_distance[id] += delta * delta;
            }
        }
        std::sort(weight_order.begin(), weight_order.end(), [&](int a, int b) {
            return std::make_pair(squared_distance[a], a) < std::make_pair(squared_distance[b], b);
        });
    } else benchmark_fixtures::shuffle(weight_order, weight_rng);
    for (std::size_t rank = 0; rank < target; ++rank)
        std::get<2>(builder.edges[weight_order[rank]]) = static_cast<int>(rank) + 1;

    Fixture result;
    result.original_to_label.resize(n);
    std::iota(result.original_to_label.begin(), result.original_to_label.end(), 0);
    benchmark_fixtures::shuffle(result.original_to_label, label_rng);
    if (!coordinates.empty()) {
        result.positions.resize(n);
        for (int v = 0; v < n; ++v)
            for (int axis = 0; axis < 3; ++axis)
                result.positions[result.original_to_label[v]][axis] = coordinates[v][axis] / 1024.0;
    }
    for (auto& edge : builder.edges) {
        std::get<0>(edge) = result.original_to_label[std::get<0>(edge)];
        std::get<1>(edge) = result.original_to_label[std::get<1>(edge)];
    }
    benchmark_fixtures::shuffle(builder.edges, order_rng);
    result.graph = std::move(builder.edges);
    return result;
}

inline Graph make_graph(const Case& item, unsigned int seed) {
    return make_fixture(item, seed).graph;
}

} // namespace benchmark_common

#endif
