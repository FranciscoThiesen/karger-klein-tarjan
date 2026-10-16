#ifndef KKT_WORK_STATS_HPP
#define KKT_WORK_STATS_HPP

#include <cstdint>

namespace kkt_work {

// Logical work, not elapsed time or CPU instructions. Counts include all
// recursive subproblems within a scope. Materializations count explicitly
// copied/constructed edge records; initialized slots count explicit vector
// initialization/reset elements (including nested-vector headers), not allocator bytes, capacity,
// implicit growth copies, hash probes, or deallocation work.
struct WorkStats {
    std::uint64_t kkt_calls = 0, kkt_vertices = 0, kkt_edges = 0;
    std::uint64_t current_depth = 0, max_depth = 0;
    std::uint64_t root_after_two_vertices = 0, root_after_two_edges = 0;
    std::uint64_t contraction_calls = 0, contraction_vertices = 0, contraction_edges = 0;
    std::uint64_t contraction_vertex_visits = 0, contraction_edge_visits = 0;
    std::uint64_t contraction_arc_visits = 0;
    std::uint64_t contraction_output_vertices = 0, contraction_output_edges = 0;
    std::uint64_t isolation_calls = 0, isolation_vertex_visits = 0, isolation_edge_visits = 0;
    std::uint64_t sampling_calls = 0, sampling_edge_visits = 0, sampled_edges = 0;
    std::uint64_t kkt_edge_visits = 0, filtered_edges = 0;
    std::uint64_t verifier_calls = 0, verifier_vertices = 0, verifier_edges = 0;
    std::uint64_t verifier_forest_edges = 0, verifier_components = 0;
    std::uint64_t verifier_tree_calls = 0, verifier_tree_vertices = 0, verifier_tree_edges = 0;
    std::uint64_t verifier_vertex_visits = 0, verifier_edge_visits = 0, verifier_arc_visits = 0;
    std::uint64_t verifier_queries = 0;
    std::uint64_t fbt_calls = 0, fbt_input_vertices = 0, fbt_rounds = 0;
    std::uint64_t fbt_round_vertices = 0, fbt_round_edges = 0;
    std::uint64_t fbt_vertex_visits = 0, fbt_edge_visits = 0, fbt_arc_visits = 0;
    std::uint64_t fbt_output_vertices = 0;
    std::uint64_t path_init_vertices = 0, path_visit_vertices = 0, path_query_visits = 0;
    std::uint64_t path_binary_search_calls = 0, path_binary_search_steps = 0;
    // median_entries excludes the zero mask: it counts loop iterations.
    std::uint64_t path_max_height = 0, median_entries = 0;
    std::uint64_t lca_calls = 0, lca_queries = 0, lca_vertices = 0;
    std::uint64_t lca_euler_entries = 0, lca_log_entries = 0;
    std::uint64_t lca_block_scan_visits = 0, lca_sparse_cells = 0;
    // Micro cells count the computed upper triangle, not its square allocation.
    std::uint64_t lca_mask_slots = 0, lca_micro_tables = 0, lca_micro_cells = 0;
    std::uint64_t initialized_slots = 0, edge_materializations = 0;
    // One lookup call or attempted range/individual insertion per item;
    // these do not count internal hash invocations, rehashing, or collisions.
    std::uint64_t hash_lookup_calls = 0, hash_insert_items = 0;
};

#ifdef KKT_ENABLE_WORK_STATS
inline thread_local WorkStats* active = nullptr;

// Nested scopes restore their previous collector. Resetting is explicit so
// callers can choose whether a scope records one invocation or an aggregate.
class ScopedWorkStats {
    WorkStats* previous;
public:
    explicit ScopedWorkStats(WorkStats& stats) : previous(active) { active = &stats; }
    ~ScopedWorkStats() { active = previous; }
    ScopedWorkStats(const ScopedWorkStats&) = delete;
    ScopedWorkStats& operator=(const ScopedWorkStats&) = delete;
};

class RecursionScope {
    WorkStats* stats;
public:
    RecursionScope() : stats(active) {
        if (stats && ++stats->current_depth > stats->max_depth)
            stats->max_depth = stats->current_depth;
    }
    ~RecursionScope() { if (stats) --stats->current_depth; }
};
#endif

}  // namespace kkt_work

#ifdef KKT_ENABLE_WORK_STATS
#define KKT_WORK_ADD(field, amount) do { \
    if (::kkt_work::active) ::kkt_work::active->field += static_cast<std::uint64_t>(amount); \
} while (false)
#define KKT_WORK_MAX(field, value) do { \
    if (::kkt_work::active) { \
        const std::uint64_t kkt_work_value = static_cast<std::uint64_t>(value); \
        if (kkt_work_value > ::kkt_work::active->field) ::kkt_work::active->field = kkt_work_value; \
    } \
} while (false)
#define KKT_WORK_ROOT_SET(field, value) do { \
    if (::kkt_work::active && ::kkt_work::active->current_depth == 1) \
        ::kkt_work::active->field = static_cast<std::uint64_t>(value); \
} while (false)
#define KKT_WORK_RECURSION() ::kkt_work::RecursionScope kkt_work_recursion_scope
#else
// Arguments intentionally disappear, including expressions with side effects.
#define KKT_WORK_ADD(field, amount) ((void)0)
#define KKT_WORK_MAX(field, value) ((void)0)
#define KKT_WORK_ROOT_SET(field, value) ((void)0)
#define KKT_WORK_RECURSION() ((void)0)
#endif

#endif
