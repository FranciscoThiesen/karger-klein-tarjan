#ifndef BENCHMARK_CORE_ATTACHMENT_FIXTURES_HPP
#define BENCHMARK_CORE_ATTACHMENT_FIXTURES_HPP

#include "continuation_fixtures.hpp"

#include <array>

// Engineered weighted core-and-attachment stress tests, not application data.
// Each core vertex has b-1 cheap star leaves. Each core edge is represented by
// exactly ONE original edge, so the first structured contraction keeps every
// external edge. The community endpoint mode distributes those original edge
// endpoints over clones; the leaf mode attaches them only to star centers.
namespace benchmark_attachments {

using benchmark_continuation::Spec;
using benchmark_fixtures::Graph;

inline constexpr std::array<const char*, 16> families = {
    "leaf_hierarchy4", "leaf_hierarchy16", "leaf_distance4", "leaf_distance16",
    "leaf_shuffled4", "leaf_shuffled16", "leaf_random4", "leaf_random16",
    "community_hierarchy4", "community_hierarchy16", "community_distance4", "community_distance16",
    "community_shuffled4", "community_shuffled16", "community_random4", "community_random16"};

struct Fixture {
    Graph graph;
    // Original vertex u belongs to core block u / block_size. Core vertices
    // retain these original block numbers; only expanded graph labels shuffle.
    std::vector<int> original_to_label;
    Graph core_graph;
    int block_size = 0;
};

inline bool known(const std::string& family) {
    return std::find(families.begin(), families.end(), family) != families.end();
}

inline int block_size(const std::string& family) {
    if (!known(family)) throw std::runtime_error("unknown attachment family: " + family);
    return family.compare(family.size() - 2, 2, "16") == 0 ? 16 : 4;
}

inline int edge_count(const Spec& spec) {
    const int b = block_size(spec.family);
    if (spec.n < 32 || spec.n > (1 << 22) || (spec.n & (spec.n - 1)) != 0 ||
        spec.density < 1 || spec.density > 512 || spec.intrusion_per_mille != 0)
        throw std::runtime_error("invalid attachment dimensions or intrusion parameter");
    const std::int64_t q = spec.n / b;
    const std::int64_t m = static_cast<std::int64_t>(spec.n) * spec.density;
    const std::int64_t local = q * (b - 1);
    const std::int64_t core_m = m - local;
    if (m > 134217728 || m >= 0x3f3f3f3f || core_m < q - 1 ||
        core_m > q * (q - 1) / 2)
        throw std::runtime_error("attachment core exceeds the connected simple-graph or edge-budget domain");
    return static_cast<int>(m);
}

inline Fixture make_fixture(const Spec& spec, unsigned int seed) {
    // Qualified call avoids ADL ambiguity from the aliased continuation Spec.
    const int m = benchmark_attachments::edge_count(spec);
    const int b = block_size(spec.family);
    const int q = spec.n / b;
    const int local = q * (b - 1);
    const int core_m = m - local;
    const bool distance = spec.family.find("_distance") != std::string::npos;
    const bool shuffled = spec.family.find("_shuffled") != std::string::npos;
    const bool random = spec.family.find("_random") != std::string::npos;
    const bool community = spec.family.find("community_") == 0;
    // Distinct streams make paired modes independent of any draw-count changes
    // in weighting, endpoint placement, labels or physical tuple order.
    std::mt19937 topology_rng(seed ^ 0xd1310ba6u);
    std::mt19937 core_weight_rng(seed ^ 0x98dfb5acu);
    std::mt19937 local_weight_rng(seed ^ 0x2ffd72dbu);
    std::mt19937 endpoint_rng(seed ^ 0xd01adfb7u);
    std::mt19937 random_weight_rng(seed ^ 0xb8e1afedu);
    std::mt19937 label_rng(seed ^ 0x6a267e96u);
    std::mt19937 order_rng(seed ^ 0xba7c9045u);
    using benchmark_continuation::detail::bounded;
    using benchmark_continuation::detail::shuffle;

    benchmark_continuation::detail::Builder builder;
    builder.edges.reserve(static_cast<std::size_t>(core_m));
    builder.pairs.reserve(static_cast<std::size_t>(core_m));
    std::vector<int> backbone_levels;
    backbone_levels.reserve(static_cast<std::size_t>(q - 1));
    for (int v = 1; v < q; ++v) {
        builder.add(v - 1, v);
        int level = 0;
        for (int boundary = v; (boundary & 1) == 0; boundary /= 2) ++level;
        backbone_levels.push_back(level);
    }
    while (static_cast<int>(builder.edges.size()) < core_m) {
        const int u = static_cast<int>(bounded(topology_rng, q));
        const int v = static_cast<int>(bounded(topology_rng, q));
        builder.add(u, v);
    }
    // Random controls retain hierarchy-ordered core metadata for diagnostics;
    // their final expanded graph ranks are independently permuted over all m.
    std::vector<std::vector<int>> tiers(23);
    for (const auto& [u, v, unused, id] : builder.edges) {
        (void)unused;
        int level = 22;
        if (distance) {
            level = 0;
            for (int bits = u ^ v; bits > 1; bits >>= 1) ++level;
        } else if (!shuffled && id < q - 1) level = backbone_levels[id];
        tiers[level].push_back(id);
    }
    int next_rank = 1;
    for (auto& ids : tiers) {
        shuffle(ids, core_weight_rng);
        for (int id : ids) std::get<2>(builder.edges[id]) = next_rank++;
    }
    Fixture result;
    result.block_size = b;
    result.core_graph = std::move(builder.edges);
    builder.pairs.clear();
    builder.pairs.rehash(0);

    result.graph.reserve(static_cast<std::size_t>(m));
    for (int u = 0; u < q; ++u)
        for (int clone = 1; clone < b; ++clone)
            result.graph.emplace_back(b * u, b * u + clone, 0, static_cast<int>(result.graph.size()));
    std::vector<int> local_order(static_cast<std::size_t>(local));
    std::iota(local_order.begin(), local_order.end(), 0);
    shuffle(local_order, local_weight_rng);
    for (int rank = 0; rank < local; ++rank)
        std::get<2>(result.graph[local_order[rank]]) = rank + 1;
    for (const auto& [u, v, weight, id] : result.core_graph) {
        const int a = community ? static_cast<int>(bounded(endpoint_rng, b)) : 0;
        const int c = community ? static_cast<int>(bounded(endpoint_rng, b)) : 0;
        result.graph.emplace_back(b * u + a, b * v + c, local + weight, local + id);
    }
    if (static_cast<int>(result.graph.size()) != m)
        throw std::runtime_error("attachment expansion did not meet the exact edge budget");
    if (random) {
        std::vector<int> ids(static_cast<std::size_t>(m));
        std::iota(ids.begin(), ids.end(), 0);
        shuffle(ids, random_weight_rng);
        for (int rank = 0; rank < m; ++rank)
            std::get<2>(result.graph[ids[rank]]) = rank + 1;
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

} // namespace benchmark_attachments

#endif
