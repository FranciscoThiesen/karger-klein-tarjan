#ifndef BENCHMARK_CROSSOVER_FIXTURES_HPP
#define BENCHMARK_CROSSOVER_FIXTURES_HPP

#include "continuation_fixtures.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

// Geometric scaffold plus uniformly drawn distinct shortcuts, and connected
// G(n,m) with independently ranked weights. The spatial models are synthetic,
// not k-nearest-neighbor or road datasets.
// Narrow metric/random twins share geometry, topology, labels, IDs and input
// order. The wide-gap line ablation changes only geometry and distance ranks;
// its topology, labels, IDs and input order match both existing line families.
// Metric weights are DISTINCT RANKS of (exact distance key, original edge ID),
// so they preserve distance ordering but need not themselves satisfy a metric.
namespace benchmark_crossover {

using benchmark_fixtures::Graph;
using Position = std::array<std::int64_t, 2>;

struct Spec {
    std::string family;
    int n;
    int density;
};

struct Fixture {
    Graph graph;
    // Geometry uses original labels; this map converts them to graph labels.
    std::vector<Position> original_positions;
    std::vector<int> original_to_label;
    // Path edges for line models; ALL nearest-neighbor grid edges for grids.
    // The grid scaffold is connected but is not a tree.
    std::vector<int> backbone_ids;
    std::array<int, 2> grid_dimensions{0, 0};
    // Geometric scaffolds need one attempt. G(n,m) rejects whole disconnected
    // topologies, never adds repair edges, and fails after the documented cap.
    int topology_attempts = 1;
};

inline constexpr std::array<const char*, 6> families = {
    "line_metric", "line_random", "grid2d_metric", "grid2d_random", "gnm_random", "line_wide_metric"
};
inline constexpr int gnm_attempt_limit = 32;

inline bool supported_size(int n) {
    return n >= 32 && n <= (1 << 23) && (n & (n - 1)) == 0;
}

inline std::array<int, 2> grid_dimensions(int n) {
    if (!supported_size(n)) throw std::runtime_error("unsupported crossover grid size");
    int exponent = 0;
    for (int value = n; value > 1; value /= 2) ++exponent;
    return {1 << ((exponent + 1) / 2), 1 << (exponent / 2)};
}

inline int edge_count(const Spec& spec) {
    if (std::find(families.begin(), families.end(), spec.family) == families.end())
        throw std::runtime_error("unknown crossover family: " + spec.family);
    if (!supported_size(spec.n) || spec.density < 1 || spec.density > 512)
        throw std::runtime_error("crossover requires dyadic n in [32,2^23] and density in [1,512]");
    if (spec.family == "gnm_random" && spec.density < 16)
        throw std::runtime_error("connected G(n,m) crossover requires density >= 16");
    const std::int64_t m = static_cast<std::int64_t>(spec.n) * spec.density;
    std::int64_t base = spec.n - 1;
    if (spec.family.compare(0, 6, "grid2d") == 0) {
        const auto dimensions = grid_dimensions(spec.n);
        base = 2LL * spec.n - dimensions[0] - dimensions[1];
    }
    if (m < base || m > static_cast<std::int64_t>(spec.n) * (spec.n - 1) / 2 ||
        m >= 0x3f3f3f3f)
        throw std::runtime_error("crossover edge target violates scaffold, simple-graph or weight bounds");
    return static_cast<int>(m);
}

namespace detail {

inline bool connected(const Graph& edges, int n) {
    std::vector<int> parent(n), sizes(n, 1);
    std::iota(parent.begin(), parent.end(), 0);
    const auto find = [&](int v) {
        while (parent[v] != v) {
            parent[v] = parent[parent[v]];
            v = parent[v];
        }
        return v;
    };
    int components = n;
    for (const auto& [u, v, unused, id] : edges) {
        (void)unused; (void)id;
        int a = find(u), b = find(v);
        if (a == b) continue;
        if (sizes[a] < sizes[b]) std::swap(a, b);
        parent[b] = a;
        sizes[a] += sizes[b];
        if (--components == 1) return true;
    }
    return components <= 1;
}

inline std::uint64_t distance_key(bool line, const Position& a, const Position& b) {
    const std::int64_t dx = a[0] - b[0];
    if (line) {
        // At n=2^23 the wide-gap line span is below 2^55. Do not square it:
        // Euclidean length in one dimension is its exact absolute difference.
        return static_cast<std::uint64_t>(dx < 0 ? -dx : dx);
    }
    const std::int64_t dy = a[1] - b[1];
    // Grid axes have at most 4096 points, spaced 1024 with jitter +/-200.
    // Squared lengths therefore fit safely in int64_t throughout this domain.
    return static_cast<std::uint64_t>(dx * dx + dy * dy);
}

} // namespace detail

inline Fixture make_fixture(const Spec& spec, unsigned int seed) {
    const int m = edge_count(spec);
    const int n = spec.n;
    const bool gnm = spec.family == "gnm_random";
    const bool line = spec.family.compare(0, 4, "line") == 0;
    const bool wide_line = spec.family == "line_wide_metric";
    const bool metric = spec.family.find("_metric") != std::string::npos;
    std::mt19937 topology_rng(seed ^ 0x6a09e667u);
    std::mt19937 geometry_rng(seed ^ 0x510e527fu);
    std::mt19937 weight_rng(seed ^ 0x3c6ef372u);
    std::mt19937 label_rng(seed ^ 0x9b05688cu);
    std::mt19937 order_rng(seed ^ 0x1f83d9abu);
    using benchmark_continuation::detail::bounded;
    using benchmark_continuation::detail::shuffle;

    // Reuse the mixed endpoint-pair hash and unbiased bounded RNG without
    // changing any existing fixture implementation or its output stream.
    benchmark_continuation::detail::Builder builder;
    builder.edges.reserve(static_cast<std::size_t>(m));
    builder.pairs.reserve(static_cast<std::size_t>(m));
    Fixture result;
    if (!gnm) result.original_positions.resize(n);
    if (line) {
        result.original_positions[0] = {0, 0};
        for (int v = 1; v < n; ++v) {
            if (wide_line) {
                // A full uniform 32-bit word gives gaps in [1,2^32]. This
                // separate branch preserves the narrow family's exact draws.
                result.original_positions[v] = {
                    result.original_positions[v - 1][0] + 1LL +
                        static_cast<std::uint32_t>(geometry_rng()), 0};
            } else {
                result.original_positions[v] = {
                    result.original_positions[v - 1][0] + 1 + bounded(geometry_rng, 1024), 0};
            }
            builder.add(v - 1, v);
        }
    } else if (!gnm) {
        result.grid_dimensions = grid_dimensions(n);
        const int width = result.grid_dimensions[0];
        const int height = result.grid_dimensions[1];
        for (int v = 0; v < n; ++v) {
            const int x = v % width, y = v / width;
            result.original_positions[v] = {
                1024LL * x + static_cast<int>(bounded(geometry_rng, 401)) - 200,
                1024LL * y + static_cast<int>(bounded(geometry_rng, 401)) - 200};
            if (x + 1 < width) builder.add(v, v + 1);
            if (y + 1 < height) builder.add(v, v + width);
        }
    }
    result.backbone_ids.resize(builder.edges.size());
    std::iota(result.backbone_ids.begin(), result.backbone_ids.end(), 0);

    // Uniform ordered endpoint proposals, rejecting loops and existing edges,
    // sample uniformly without replacement from non-scaffold unordered pairs.
    for (;;) {
        while (static_cast<int>(builder.edges.size()) < m) {
            const int u = static_cast<int>(bounded(topology_rng, static_cast<std::uint32_t>(n)));
            const int v = static_cast<int>(bounded(topology_rng, static_cast<std::uint32_t>(n)));
            builder.add(u, v);
        }
        if (!gnm || detail::connected(builder.edges, n)) break;
        if (result.topology_attempts == gnm_attempt_limit)
            throw std::runtime_error("connected G(n,m) exhausted whole-topology rejection attempts");
        ++result.topology_attempts;
        builder.edges.clear();
        builder.pairs.clear();
    }
    // G(n,m) starts with no scaffold and draws m pairs uniformly without
    // replacement. Whole-topology rejection samples G(n,m) conditioned on
    // connectivity (conditioned also on succeeding within the finite cap).
    // No weight, label or order stream was consumed by rejected attempts.
    // No later stage needs pair membership. Release generation-only nodes and
    // buckets before allocating metric keys and sorting potentially large m.
    builder.pairs.clear();
    builder.pairs.rehash(0);

    std::vector<int> ranks(static_cast<std::size_t>(m));
    std::iota(ranks.begin(), ranks.end(), 0);
    if (metric) {
        std::vector<std::uint64_t> distance(static_cast<std::size_t>(m));
        for (const auto& [u, v, unused, id] : builder.edges) {
            (void)unused;
            distance[id] = detail::distance_key(line, result.original_positions[u],
                                                     result.original_positions[v]);
        }
        std::sort(ranks.begin(), ranks.end(), [&](int a, int b) {
            return std::make_pair(distance[a], a) < std::make_pair(distance[b], b);
        });
    } else shuffle(ranks, weight_rng);
    for (int rank = 0; rank < m; ++rank)
        std::get<2>(builder.edges[ranks[rank]]) = rank + 1;

    result.original_to_label.resize(n);
    std::iota(result.original_to_label.begin(), result.original_to_label.end(), 0);
    shuffle(result.original_to_label, label_rng);
    for (auto& edge : builder.edges) {
        std::get<0>(edge) = result.original_to_label[std::get<0>(edge)];
        std::get<1>(edge) = result.original_to_label[std::get<1>(edge)];
    }
    shuffle(builder.edges, order_rng);
    result.graph = std::move(builder.edges);
    return result;
}

inline Graph make_graph(const Spec& spec, unsigned int seed) {
    return make_fixture(spec, seed).graph;
}

} // namespace benchmark_crossover

#endif
