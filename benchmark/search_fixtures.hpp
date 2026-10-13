#ifndef BENCHMARK_SEARCH_FIXTURES_HPP
#define BENCHMARK_SEARCH_FIXTURES_HPP

#include "continuation_fixtures.hpp"

#include <array>
#include <limits>

// Engineered graph substitutions, not application datasets. All algorithms
// receive the expanded simple edge list, never the core or clone metadata.
namespace benchmark_search {

using benchmark_continuation::Spec;
using benchmark_fixtures::Graph;
inline constexpr std::array<const char*, 6> families = {
    "lifted_hierarchy2", "lifted_hierarchy4", "lifted_distance2",
    "lifted_distance4", "lifted_random2", "lifted_random4"};

struct Fixture {
    Graph graph;
    std::vector<int> original_to_label;
    Graph core_graph;
    int bundle_size = 0;
};

inline bool known(const std::string& family) {
    return std::find(families.begin(), families.end(), family) != families.end();
}

inline int edge_count(const Spec& spec) {
    if (!known(spec.family)) throw std::runtime_error("unknown lifted family: " + spec.family);
    if (spec.n < 32 || spec.n > (1 << 22) || (spec.n & (spec.n - 1)) != 0 ||
        spec.density < 1 || spec.density > 512 || spec.intrusion_per_mille != 0)
        throw std::runtime_error("invalid lifted dimensions or intrusion parameter");
    const int b = spec.family.back() - '0';
    const std::int64_t q = spec.n / b;
    const std::int64_t m = static_cast<std::int64_t>(spec.n) * spec.density;
    const std::int64_t local = q * (b - 1);
    if (q < b*b || m > 134217728 || m >= 0x3f3f3f3f || m < local ||
        (m - local) % (b*b) != 0)
        throw std::runtime_error("lifted size exceeds budget or integral core domain");
    const std::int64_t core_m = (m - local) / (b*b);
    if (core_m < q - 1 || core_m > q * (q - 1) / 2)
        throw std::runtime_error("lifted core cannot meet connected simple-graph budget");
    return static_cast<int>(m);
}

inline Fixture make_fixture(const Spec& spec, unsigned int seed) {
    const int m = benchmark_search::edge_count(spec);
    const int b = spec.family.back() - '0';
    const int q = spec.n / b;
    const int local = q * (b - 1);
    const int core_m = (m - local) / (b*b);
    const bool distance = spec.family.find("lifted_distance") == 0;
    const bool random = spec.family.find("lifted_random") == 0;
    std::mt19937 topology_rng(seed ^ 0x243f6a88u);
    std::mt19937 core_weight_rng(seed ^ 0x85a308d3u);
    std::mt19937 local_weight_rng(seed ^ 0x13198a2eu);
    std::mt19937 bundle_weight_rng(seed ^ 0x03707344u);
    std::mt19937 random_weight_rng(seed ^ 0xa4093822u);
    std::mt19937 label_rng(seed ^ 0x299f31d0u);
    std::mt19937 order_rng(seed ^ 0x082efa98u);
    using benchmark_continuation::detail::bounded;
    using benchmark_continuation::detail::shuffle;

    benchmark_continuation::detail::Builder builder;
    builder.edges.reserve(static_cast<std::size_t>(core_m));
    builder.pairs.reserve(static_cast<std::size_t>(core_m));
    std::vector<int> backbone_levels;
    backbone_levels.reserve(static_cast<std::size_t>(q-1));
    for (int v = 1; v < q; ++v) {
        builder.add(v-1, v);
        int level = 0;
        for (int boundary = v; (boundary & 1) == 0; boundary /= 2) ++level;
        backbone_levels.push_back(level);
    }
    while (static_cast<int>(builder.edges.size()) < core_m) {
        const int u = static_cast<int>(bounded(topology_rng, q));
        const int v = static_cast<int>(bounded(topology_rng, q));
        builder.add(u, v);
    }
    // The random twin's retained core metadata uses the hierarchy order, but
    // its expanded weights below are independently permuted over ALL edges.
    std::vector<std::vector<int>> tiers(23);
    for (const auto& edge : builder.edges) {
        const int id = std::get<3>(edge);
        int level = 22; // Every hierarchy shortcut is above every tree edge.
        if (distance) {
            level = 0;
            for (int bits = std::get<0>(edge) ^ std::get<1>(edge); bits > 1; bits >>= 1) ++level;
        } else if (id < q-1) {
            level = backbone_levels[id];
        }
        tiers[level].push_back(id);
    }
    int next_rank = 1;
    for (auto& ids : tiers) {
        shuffle(ids, core_weight_rng);
        for (int id : ids) std::get<2>(builder.edges[id]) = next_rank++;
    }
    Fixture result;
    result.bundle_size = b;
    result.core_graph = std::move(builder.edges);
    // The pair set belongs only to untimed generation; release it before
    // allocating the much larger expansion.
    builder.pairs.clear();
    builder.pairs.rehash(0);
    result.graph.reserve(static_cast<std::size_t>(m));
    for (int u = 0; u < q; ++u)
        for (int k = 1; k < b; ++k)
            result.graph.emplace_back(b*u, b*u+k, 0, static_cast<int>(result.graph.size()));
    std::vector<int> local_order(static_cast<std::size_t>(local));
    std::iota(local_order.begin(), local_order.end(), 0);
    shuffle(local_order, local_weight_rng);
    for (int rank = 0; rank < local; ++rank)
        std::get<2>(result.graph[local_order[rank]]) = rank+1;
    std::vector<int> bundle_order(static_cast<std::size_t>(b*b));
    for (const auto& [u, v, weight, id] : result.core_graph) {
        (void)id;
        const int start = static_cast<int>(result.graph.size());
        for (int a = 0; a < b; ++a)
            for (int c = 0; c < b; ++c)
                result.graph.emplace_back(b*u+a, b*v+c, 0, static_cast<int>(result.graph.size()));
        std::iota(bundle_order.begin(), bundle_order.end(), 0);
        shuffle(bundle_order, bundle_weight_rng);
        for (int rank = 0; rank < b*b; ++rank)
            std::get<2>(result.graph[start+bundle_order[rank]]) = local+(weight-1)*b*b+rank+1;
    }
    if (static_cast<int>(result.graph.size()) != m)
        throw std::runtime_error("lifted expansion did not meet the exact edge budget");
    if (random) {
        std::vector<int> ids(static_cast<std::size_t>(m));
        std::iota(ids.begin(), ids.end(), 0);
        shuffle(ids, random_weight_rng);
        for (int rank = 0; rank < m; ++rank)
            std::get<2>(result.graph[ids[rank]]) = rank+1;
    }
    result.original_to_label.resize(static_cast<std::size_t>(spec.n));
    std::iota(result.original_to_label.begin(), result.original_to_label.end(), 0);
    shuffle(result.original_to_label, label_rng);
    for (auto& edge : result.graph) {
        std::get<0>(edge) = result.original_to_label[std::get<0>(edge)];
        std::get<1>(edge) = result.original_to_label[std::get<1>(edge)];
    }
    shuffle(result.graph, order_rng);
    return result;
}

} // namespace benchmark_search

#endif
