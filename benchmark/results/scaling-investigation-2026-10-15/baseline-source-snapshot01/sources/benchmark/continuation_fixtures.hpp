#ifndef BENCHMARK_CONTINUATION_FIXTURES_HPP
#define BENCHMARK_CONTINUATION_FIXTURES_HPP

#include "graph_fixtures.hpp"

#include <algorithm>
#include <cstdint>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

// Engineered continuation stress tests, not representative application graphs.
// A balanced hierarchy can delay contraction while random shortcut edges remain
// alive. Paired weight controls preserve topology, edge IDs, labels, and order.
namespace benchmark_continuation {

using benchmark_fixtures::Graph;

struct Spec {
    std::string family;
    int n;
    int density;
    int intrusion_per_mille = 0;
};

struct Fixture {
    Graph graph;
    std::vector<int> original_to_label;
    // The first n-1 IDs are the connected tree backbone, in creation order.
    std::vector<int> backbone_ids;
    // Indexed by edge ID, not by shuffled tuple position; chords have level -1.
    std::vector<int> hierarchy_levels;
};

namespace detail {

struct PairHash {
    std::size_t operator()(std::uint64_t value) const noexcept {
        // Mix both endpoints before a library selects the hash bucket. With an
        // identity integer hash, power-of-two bucket counts can ignore the high
        // endpoint bits and make untimed dense-graph generation very expensive.
        value += UINT64_C(0x9e3779b97f4a7c15);
        value = (value ^ (value >> 30)) * UINT64_C(0xbf58476d1ce4e5b9);
        value = (value ^ (value >> 27)) * UINT64_C(0x94d049bb133111eb);
        return static_cast<std::size_t>(value ^ (value >> 31));
    }
};

struct Builder {
    Graph edges;
    std::unordered_set<std::uint64_t, PairHash> pairs;
    bool add(int u, int v, int group = 0) {
        if (u == v) return false;
        if (u > v) std::swap(u, v);
        const auto key = (static_cast<std::uint64_t>(u) << 32) | static_cast<unsigned int>(v);
        if (!pairs.insert(key).second) return false;
        edges.emplace_back(u, v, group, static_cast<int>(edges.size()));
        return true;
    }
};

inline bool tree_topology(const std::string& family) {
    return family == "hierarchical_tree" || family == "random_tree" || family == "distance_tree";
}

inline bool global_random_weights(const std::string& family) {
    return family == "random_path" || family == "random_tree";
}

inline bool distance_weights(const std::string& family) {
    return family == "distance_path" || family == "distance_tree";
}

// Rejection removes modulo bias. Explicit Fisher-Yates and RNG streams avoid
// implementation-specific distributions and weight-dependent input shuffles.
inline std::uint32_t bounded(std::mt19937& rng, std::uint32_t bound) {
    const std::uint32_t threshold = (std::uint32_t{0} - bound) % bound;
    for (;;) {
        const auto value = static_cast<std::uint32_t>(rng());
        if (value >= threshold) return value % bound;
    }
}

template <class T>
inline void shuffle(std::vector<T>& values, std::mt19937& rng) {
    for (std::size_t size = values.size(); size > 1; --size)
        std::swap(values[size - 1], values[bounded(rng, static_cast<std::uint32_t>(size))]);
}

} // namespace detail

inline int edge_count(const Spec& spec) {
    const bool known = detail::tree_topology(spec.family) ||
                       spec.family == "hierarchical_path" || spec.family == "low_path" ||
                       spec.family == "random_path" || spec.family == "distance_path";
    if (!known) throw std::runtime_error("unknown continuation family: " + spec.family);
    if (spec.n < 32 || spec.n > (1 << 22) || (spec.n & (spec.n - 1)) != 0)
        throw std::runtime_error("continuation fixtures require a power-of-two n in [32, 2^22]");
    if (spec.density < 1 || spec.density > 512)
        throw std::runtime_error("continuation density must be in [1, 512]");
    if (spec.intrusion_per_mille < 0 || spec.intrusion_per_mille > 1000)
        throw std::runtime_error("intrusion_per_mille must be in [0, 1000]");
    if (detail::global_random_weights(spec.family) && spec.intrusion_per_mille != 0)
        throw std::runtime_error("global-random controls do not accept intrusions");
    if (detail::distance_weights(spec.family) && spec.intrusion_per_mille != 0)
        throw std::runtime_error("distance-order controls do not accept intrusions");
    const std::int64_t m = static_cast<std::int64_t>(spec.n) * spec.density;
    const std::int64_t capacity = static_cast<std::int64_t>(spec.n) * (spec.n - 1) / 2;
    // Match the finite sentinel used by the shared algorithm weight domain.
    if (m > capacity || m >= 0x3f3f3f3f)
        throw std::runtime_error("edge target exceeds the simple-graph or shared weight domain");
    const std::int64_t intrusions =
        static_cast<std::int64_t>(spec.n) * spec.intrusion_per_mille / 1000;
    if (intrusions > m - (spec.n - 1))
        throw std::runtime_error("requested intrusions exceed available shortcut edges");
    return static_cast<int>(m);
}

inline std::string case_id(const Spec& spec) {
    // The harness also uses this formatting helper for unchanged legacy inputs.
    // Validation belongs to the generator selected for each family.
    return spec.family + "_n" + std::to_string(spec.n) + "_d" +
           std::to_string(spec.density) + "_p" + std::to_string(spec.intrusion_per_mille);
}

inline Fixture make_fixture(const Spec& spec, unsigned int seed) {
    const int m = edge_count(spec);
    const int n = spec.n;
    const int backbone_size = n - 1;
    const int intrusion_count = static_cast<int>(
        static_cast<std::int64_t>(n) * spec.intrusion_per_mille / 1000);
    std::mt19937 topology_rng(seed ^ 0x6a09e667u);
    std::mt19937 backbone_rng(seed ^ 0xbb67ae85u);
    std::mt19937 weight_rng(seed ^ 0x3c6ef372u);
    std::mt19937 intrusion_rng(seed ^ 0xa54ff53au);
    std::mt19937 interleave_rng(seed ^ 0x510e527fu);
    std::mt19937 label_rng(seed ^ 0x9b05688cu);
    std::mt19937 order_rng(seed ^ 0x1f83d9abu);

    detail::Builder builder;
    builder.edges.reserve(static_cast<std::size_t>(m));
    builder.pairs.reserve(static_cast<std::size_t>(m));
    Fixture result;
    result.hierarchy_levels.reserve(static_cast<std::size_t>(m));
    const auto add_backbone = [&](int u, int v, int level) {
        if (!builder.add(u, v)) throw std::runtime_error("duplicate backbone edge");
        result.hierarchy_levels.push_back(level);
    };
    if (detail::tree_topology(spec.family)) {
        // Each level joins the two halves of every aligned dyadic block once.
        // By induction, this is a tree, and its level-r minimum edges pair the
        // level-r blocks regardless of which endpoints were sampled in them.
        int level = 0;
        for (int half = 1; half < n; half *= 2, ++level) {
            const int width = 2 * half;
            for (int base = 0; base < n; base += width) {
                const int u = base + static_cast<int>(detail::bounded(topology_rng, half));
                const int v = base + half + static_cast<int>(detail::bounded(topology_rng, half));
                add_backbone(u, v, level);
            }
        }
    } else {
        // Boundary v separates aligned blocks at level countr_zero(v).
        for (int v = 1; v < n; ++v) {
            int level = 0;
            for (int boundary = v; (boundary & 1) == 0; boundary /= 2) ++level;
            add_backbone(v - 1, v, level);
        }
    }
    result.backbone_ids.resize(static_cast<std::size_t>(backbone_size));
    std::iota(result.backbone_ids.begin(), result.backbone_ids.end(), 0);

    // Rejection sampling chooses uniform distinct unordered non-backbone pairs.
    // The chord stream depends on topology and density, never the weight mode.
    while (static_cast<int>(builder.edges.size()) < m) {
        const int u = static_cast<int>(detail::bounded(topology_rng, n));
        const int v = static_cast<int>(detail::bounded(topology_rng, n));
        if (builder.add(u, v)) result.hierarchy_levels.push_back(-1);
    }

    if (detail::distance_weights(spec.family)) {
        // Engineered dyadic distance ordering on EVERY edge, including chords.
        // Rank weights are order-equivalent to 2^level plus distinct positive
        // perturbations smaller than 1/4. Those realizing costs form a metric;
        // the integer ranks need not, and tie-breaking removes ultrametricity.
        // Levels use original labels, before the independent label permutation.
        // Keep hierarchy_levels as backbone metadata, unchanged across controls.
        std::vector<std::vector<int>> level_ids(22); // n <= 2^22
        for (const auto& [u, v, weight, id] : builder.edges) {
            (void)weight;
            int level = 0;
            for (int differing = u ^ v; differing > 1; differing >>= 1) ++level;
            level_ids[level].push_back(id);
        }
        int next_rank = 1;
        for (auto& ids : level_ids) {
            detail::shuffle(ids, weight_rng);
            for (int id : ids) std::get<2>(builder.edges[id]) = next_rank++;
        }
    } else if (detail::global_random_weights(spec.family)) {
        std::vector<int> order(static_cast<std::size_t>(m));
        std::iota(order.begin(), order.end(), 0);
        detail::shuffle(order, weight_rng);
        for (int rank = 0; rank < m; ++rank)
            std::get<2>(builder.edges[order[rank]]) = rank + 1;
    } else {
        auto cheap_order = result.backbone_ids;
        detail::shuffle(cheap_order, backbone_rng);
        if (spec.family != "low_path") {
            // Stable grouping leaves an unbiased shuffle within each level.
            std::stable_sort(cheap_order.begin(), cheap_order.end(), [&](int a, int b) {
                return result.hierarchy_levels[a] < result.hierarchy_levels[b];
            });
        }
        std::vector<int> chord_order(static_cast<std::size_t>(m - backbone_size));
        std::iota(chord_order.begin(), chord_order.end(), backbone_size);
        detail::shuffle(chord_order, intrusion_rng);
        // The prefix is a uniform ordered selection without replacement. A
        // uniform merge puts these chords among the cheap backbone priorities,
        // preserving its relative ordering across every intrusion setting.
        int backbone_index = 0;
        int intrusion_index = 0;
        int next_rank = 1;
        for (int remaining = backbone_size + intrusion_count; remaining > 0; --remaining) {
            const int intrusions_left = intrusion_count - intrusion_index;
            const bool insert_chord =
                static_cast<int>(detail::bounded(interleave_rng, remaining)) < intrusions_left;
            const int id = insert_chord ? chord_order[intrusion_index++]
                                        : cheap_order[backbone_index++];
            std::get<2>(builder.edges[id]) = next_rank++;
        }
        std::vector<int> high_order(chord_order.begin() + intrusion_count, chord_order.end());
        detail::shuffle(high_order, weight_rng);
        for (int id : high_order) std::get<2>(builder.edges[id]) = next_rank++;
    }

    result.original_to_label.resize(static_cast<std::size_t>(n));
    std::iota(result.original_to_label.begin(), result.original_to_label.end(), 0);
    detail::shuffle(result.original_to_label, label_rng);
    for (auto& edge : builder.edges) {
        std::get<0>(edge) = result.original_to_label[std::get<0>(edge)];
        std::get<1>(edge) = result.original_to_label[std::get<1>(edge)];
    }
    detail::shuffle(builder.edges, order_rng);
    result.graph = std::move(builder.edges);
    return result;
}

} // namespace benchmark_continuation

#endif
