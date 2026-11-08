#ifndef KKT_EXPERIMENTAL_WEIGHT_RANKS_HPP
#define KKT_EXPERIMENTAL_WEIGHT_RANKS_HPP

// Opt-in adapter for tied signed-32-bit weights; not used by the public solver.
// Stable rank order is (original cost, input position). The four radix passes
// avoid comparison sorting and preserve original endpoints, IDs and edge order.
#include "kkt.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <vector>

namespace kkt_experiment {

struct weight_rank_work {
    std::size_t radix_passes = 0;
    std::size_t histogram_edge_visits = 0;
    std::size_t scatter_edge_visits = 0;
    std::size_t histogram_slots = 0;
    std::size_t prefix_slots = 0;
    std::size_t index_initializations = 0;
    std::size_t copied_edges = 0;
    std::size_t rank_writes = 0;
};

inline problem with_stable_weight_ranks(const problem& input,
                                       weight_rank_work* work = nullptr) {
    static_assert(std::numeric_limits<int>::digits == 31,
                  "weight rank adapter requires signed 32-bit int");
    const std::size_t m = input.graph_edges.size();
    if (m > static_cast<std::size_t>(std::numeric_limits<int>::max()))
        throw std::length_error("weight rank adapter requires int-sized edge positions");
    weight_rank_work counted;
    problem ranked = input; // Include the full copy in this adapter's work.
    counted.copied_edges = m;
    if (m != 0) {
        std::vector<int> order(m), scratch(m);
        std::iota(order.begin(), order.end(), 0);
        // Two value-initialized arrays and the explicit iota pass.
        counted.index_initializations = 3 * m;
        const auto digit = [&](int position, unsigned shift) {
            const std::uint32_t key =
                std::uint32_t(input.graph_edges[position].cost) ^ UINT32_C(0x80000000);
            return static_cast<std::size_t>((key >> shift) & UINT32_C(255));
        };
        for (unsigned shift = 0; shift < 32; shift += 8) {
            std::array<std::size_t, 256> next{};
            for (int position : order) ++next[digit(position, shift)];
            std::size_t offset = 0;
            for (std::size_t& count : next) {
                const std::size_t previous = count;
                count = offset;
                offset += previous;
            }
            for (int position : order)
                scratch[next[digit(position, shift)]++] = position;
            order.swap(scratch);
            ++counted.radix_passes;
            counted.histogram_edge_visits += m;
            counted.scatter_edge_visits += m;
            counted.histogram_slots += next.size();
            counted.prefix_slots += next.size();
        }
        for (std::size_t rank = 0; rank < m; ++rank)
            ranked.graph_edges[order[rank]].cost = static_cast<int>(rank);
        counted.rank_writes = m;
    }
    if (work) *work = counted;
    return ranked;
}

} // namespace kkt_experiment
#endif
