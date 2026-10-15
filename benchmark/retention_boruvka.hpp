#ifndef BENCHMARK_RETENTION_BORUVKA_HPP
#define BENCHMARK_RETENTION_BORUVKA_HPP

#include "../kkt/experimental_multigraph_contraction.hpp"

#include <unordered_set>
#include <utility>
#include <vector>

namespace benchmark_retention {

// Exact compacting_boruvka continuation and result construction, changing
// only the contraction call. Every crossing edge survives until it becomes
// internal; no sampling, filtering, graph-family shortcut, or deduplication.
inline std::unordered_set<int> multigraph_boruvka(problem& input) {
    std::vector<int> selected_ids;
    while (!input.graph_edges.empty()) {
        auto [selected, reduced] = kkt_experiment::retain_parallel_step(input);
        selected_ids.insert(selected_ids.end(), selected.begin(), selected.end());
        input = std::move(reduced);
    }
    std::unordered_set<int> result;
    result.reserve(selected_ids.size());
    result.insert(selected_ids.begin(), selected_ids.end());
    return result;
}

} // namespace benchmark_retention
#endif
