// Untimed output-API regression. The runner instruments the actual two libc++
// unique-insertion bucket loops in a temporary SDK-header copy.
#include "kkt/kkt.hpp"
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>
#include <unordered_set>
#include <vector>

int main() {
    for (const int edges : {1024, 2048, 4096, 8192}) {
        std::unordered_set<int> probe;
        probe.reserve(static_cast<std::size_t>(edges));
        const std::size_t buckets = probe.bucket_count();
        assert(static_cast<std::uint64_t>(edges - 1) * buckets <=
               static_cast<std::uint64_t>(std::numeric_limits<int>::max()));
        for (const bool collide : {false, true}) {
            const int stride = collide ? static_cast<int>(buckets) : 1;
            std::vector<Edge> graph;
            graph.reserve(edges);
            for (int i = 0; i < edges; ++i) {
                const int id = i * stride;
                assert(std::hash<int>{}(id) == static_cast<std::size_t>(id));
                // This star is already a tree, with a unique MST of all edges.
                graph.emplace_back(0, i + 1, i + 1, id);
            }
            problem input(edges + 1, std::move(graph));
            kkt_work::WorkStats vector_stats;
            for (const bool use_vector : {true, false}) {
                kkt_work::WorkStats stats;
                kkt_hash_probe::unique_insert_visits = 0;
                std::vector<int> ids;
                std::uint64_t visits = 0;
                std::size_t maximum_bucket = 0;
                if (use_vector) {
                    kkt_work::ScopedWorkStats scope(stats);
                    ids = kkt_edge_ids(input, 17);
                    visits = kkt_hash_probe::unique_insert_visits;
                } else {
                    kkt_work::ScopedWorkStats scope(stats);
                    const auto result = kkt(input, 17);
                    visits = kkt_hash_probe::unique_insert_visits;
                    assert(result.bucket_count() == buckets);
                    for (std::size_t i = 0; i < buckets; ++i)
                        maximum_bucket = std::max(maximum_bucket, result.bucket_size(i));
                    assert(maximum_bucket == (collide ? static_cast<std::size_t>(edges) : 1));
                    ids.assign(result.begin(), result.end());
                }
                // Validation avoids a second ID hash table and checks every ID,
                // uniqueness and cardinality, not just the summed weight.
                assert(ids.size() == static_cast<std::size_t>(edges));
                std::vector<bool> seen(edges, false);
                for (int id : ids) {
                    assert(id >= 0 && id % stride == 0 && id / stride < edges);
                    assert(!seen[id / stride]);
                    seen[id / stride] = true;
                }
                assert(std::all_of(seen.begin(), seen.end(), [](bool x) { return x; }));
                const std::uint64_t expected = !use_vector && collide
                    ? static_cast<std::uint64_t>(edges) * (edges - 1) / 2 : 0;
                assert(visits == expected);
                assert(stats.kkt_calls == 1 && stats.contraction_calls == 1);
                assert(stats.sampling_calls == 0 && stats.verifier_calls == 0);
                assert(stats.contraction_edge_visits == static_cast<std::uint64_t>(edges));
                assert(stats.hash_insert_items == (use_vector ? 0 : static_cast<std::uint64_t>(edges)));
                if (use_vector) {
                    vector_stats = stats;
                } else {
                    assert(stats.kkt_edges == vector_stats.kkt_edges);
                    assert(stats.contraction_vertex_visits == vector_stats.contraction_vertex_visits);
                    assert(stats.contraction_edge_visits == vector_stats.contraction_edge_visits);
                    assert(stats.contraction_arc_visits == vector_stats.contraction_arc_visits);
                    assert(stats.initialized_slots == vector_stats.initialized_slots);
                    assert(stats.edge_materializations == vector_stats.edge_materializations);
                }
                std::cout << "{\"api\":\"" << (use_vector ? "kkt_edge_ids" : "kkt")
                          << "\",\"id_layout\":\"" << (collide ? "bucket_multiples" : "dense")
                          << "\",\"vertices\":" << edges + 1
                          << ",\"edges\":" << edges << ",\"buckets\":" << buckets
                          << ",\"id_stride\":" << stride
                          << ",\"maximum_bucket\":" << maximum_bucket
                          << ",\"unique_insert_node_visits\":" << visits
                          << ",\"expected_node_visits\":" << expected
                          << ",\"kkt_calls\":" << stats.kkt_calls
                          << ",\"contraction_calls\":" << stats.contraction_calls
                          << ",\"contraction_vertex_visits\":" << stats.contraction_vertex_visits
                          << ",\"contraction_edge_visits\":" << stats.contraction_edge_visits
                          << ",\"initialized_slots\":" << stats.initialized_slots
                          << ",\"hash_insert_items\":" << stats.hash_insert_items
                          << ",\"correctness\":\"pass\"}\n";
            }
        }
    }
}
