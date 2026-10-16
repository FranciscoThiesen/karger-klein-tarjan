#ifndef BENCHMARK_WORK_METRICS_HPP
#define BENCHMARK_WORK_METRICS_HPP

#include "../common/work_stats.hpp"

#include <cstddef>
#include <cstdint>
#include <type_traits>

namespace benchmark_work {

struct Field {
    const char* name;
    std::uint64_t kkt_work::WorkStats::*member;
    bool contributes_to_proxy;
};

// Declaration order is also the stable CSV column order. The proxy sums
// observed loop visits, table writes, initialized slots, edge materializations,
// and hash API items. These are different logical events, not CPU instructions:
// visiting an edge and copying it can both count. Input/output volumes, depths,
// call counts, and query-volume summaries are excluded. lca_queries counts the
// actual constant-time query operation; verifier_queries describes query volume
// already traversed by path_query_visits. lca_mask_slots is excluded because its
// only work is initialization, already included in initialized_slots.
inline constexpr Field fields[] = {
    {"kkt_calls", &kkt_work::WorkStats::kkt_calls, false},
    {"kkt_vertices", &kkt_work::WorkStats::kkt_vertices, false},
    {"kkt_edges", &kkt_work::WorkStats::kkt_edges, false},
    {"current_depth", &kkt_work::WorkStats::current_depth, false},
    {"max_depth", &kkt_work::WorkStats::max_depth, false},
    {"root_after_two_vertices", &kkt_work::WorkStats::root_after_two_vertices, false},
    {"root_after_two_edges", &kkt_work::WorkStats::root_after_two_edges, false},
    {"contraction_calls", &kkt_work::WorkStats::contraction_calls, false},
    {"contraction_vertices", &kkt_work::WorkStats::contraction_vertices, false},
    {"contraction_edges", &kkt_work::WorkStats::contraction_edges, false},
    {"contraction_vertex_visits", &kkt_work::WorkStats::contraction_vertex_visits, true},
    {"contraction_edge_visits", &kkt_work::WorkStats::contraction_edge_visits, true},
    {"contraction_arc_visits", &kkt_work::WorkStats::contraction_arc_visits, true},
    {"contraction_output_vertices", &kkt_work::WorkStats::contraction_output_vertices, false},
    {"contraction_output_edges", &kkt_work::WorkStats::contraction_output_edges, false},
    {"isolation_calls", &kkt_work::WorkStats::isolation_calls, false},
    {"isolation_vertex_visits", &kkt_work::WorkStats::isolation_vertex_visits, true},
    {"isolation_edge_visits", &kkt_work::WorkStats::isolation_edge_visits, true},
    {"sampling_calls", &kkt_work::WorkStats::sampling_calls, false},
    {"sampling_edge_visits", &kkt_work::WorkStats::sampling_edge_visits, true},
    {"sampled_edges", &kkt_work::WorkStats::sampled_edges, false},
    {"kkt_edge_visits", &kkt_work::WorkStats::kkt_edge_visits, true},
    {"filtered_edges", &kkt_work::WorkStats::filtered_edges, false},
    {"verifier_calls", &kkt_work::WorkStats::verifier_calls, false},
    {"verifier_vertices", &kkt_work::WorkStats::verifier_vertices, false},
    {"verifier_edges", &kkt_work::WorkStats::verifier_edges, false},
    {"verifier_forest_edges", &kkt_work::WorkStats::verifier_forest_edges, false},
    {"verifier_components", &kkt_work::WorkStats::verifier_components, false},
    {"verifier_tree_calls", &kkt_work::WorkStats::verifier_tree_calls, false},
    {"verifier_tree_vertices", &kkt_work::WorkStats::verifier_tree_vertices, false},
    {"verifier_tree_edges", &kkt_work::WorkStats::verifier_tree_edges, false},
    {"verifier_vertex_visits", &kkt_work::WorkStats::verifier_vertex_visits, true},
    {"verifier_edge_visits", &kkt_work::WorkStats::verifier_edge_visits, true},
    {"verifier_arc_visits", &kkt_work::WorkStats::verifier_arc_visits, true},
    {"verifier_queries", &kkt_work::WorkStats::verifier_queries, false},
    {"fbt_calls", &kkt_work::WorkStats::fbt_calls, false},
    {"fbt_input_vertices", &kkt_work::WorkStats::fbt_input_vertices, false},
    {"fbt_rounds", &kkt_work::WorkStats::fbt_rounds, false},
    {"fbt_round_vertices", &kkt_work::WorkStats::fbt_round_vertices, false},
    {"fbt_round_edges", &kkt_work::WorkStats::fbt_round_edges, false},
    {"fbt_vertex_visits", &kkt_work::WorkStats::fbt_vertex_visits, true},
    {"fbt_edge_visits", &kkt_work::WorkStats::fbt_edge_visits, true},
    {"fbt_arc_visits", &kkt_work::WorkStats::fbt_arc_visits, true},
    {"fbt_output_vertices", &kkt_work::WorkStats::fbt_output_vertices, false},
    {"path_init_vertices", &kkt_work::WorkStats::path_init_vertices, true},
    {"path_visit_vertices", &kkt_work::WorkStats::path_visit_vertices, true},
    {"path_query_visits", &kkt_work::WorkStats::path_query_visits, true},
    {"path_binary_search_calls", &kkt_work::WorkStats::path_binary_search_calls, false},
    {"path_binary_search_steps", &kkt_work::WorkStats::path_binary_search_steps, true},
    {"path_max_height", &kkt_work::WorkStats::path_max_height, false},
    {"median_entries", &kkt_work::WorkStats::median_entries, true},
    {"lca_calls", &kkt_work::WorkStats::lca_calls, false},
    {"lca_queries", &kkt_work::WorkStats::lca_queries, true},
    {"lca_vertices", &kkt_work::WorkStats::lca_vertices, false},
    {"lca_euler_entries", &kkt_work::WorkStats::lca_euler_entries, true},
    {"lca_log_entries", &kkt_work::WorkStats::lca_log_entries, true},
    {"lca_block_scan_visits", &kkt_work::WorkStats::lca_block_scan_visits, true},
    {"lca_sparse_cells", &kkt_work::WorkStats::lca_sparse_cells, true},
    {"lca_mask_slots", &kkt_work::WorkStats::lca_mask_slots, false},
    {"lca_micro_tables", &kkt_work::WorkStats::lca_micro_tables, false},
    {"lca_micro_cells", &kkt_work::WorkStats::lca_micro_cells, true},
    {"initialized_slots", &kkt_work::WorkStats::initialized_slots, true},
    {"edge_materializations", &kkt_work::WorkStats::edge_materializations, true},
    {"hash_lookup_calls", &kkt_work::WorkStats::hash_lookup_calls, true},
    {"hash_insert_items", &kkt_work::WorkStats::hash_insert_items, true},
};

inline constexpr std::size_t field_count = sizeof(fields) / sizeof(fields[0]);
static_assert(std::is_standard_layout<kkt_work::WorkStats>::value,
              "WorkStats must remain a plain counter record");
// WorkStats currently consists exclusively of uint64_t fields. This guard
// forces an explicit schema review whenever a counter is added or removed.
static_assert(sizeof(kkt_work::WorkStats) == field_count * sizeof(std::uint64_t),
              "Update the work-metric registry for the changed counter record");

constexpr bool distinct_fields() {
    for (std::size_t i = 0; i < field_count; ++i)
        for (std::size_t j = i + 1; j < field_count; ++j)
            if (fields[i].member == fields[j].member) return false;
    return true;
}
static_assert(distinct_fields(), "A counter appears twice in the CSV registry");

inline std::uint64_t total_work_proxy(const kkt_work::WorkStats& stats) {
    std::uint64_t total = 0;
    for (const auto& field : fields)
        if (field.contributes_to_proxy) total += stats.*field.member;
    return total;
}

}  // namespace benchmark_work

#endif
