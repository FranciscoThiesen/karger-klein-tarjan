#ifndef VERIFIER_MEDIAN_TABLE_HPP
#define VERIFIER_MEDIAN_TABLE_HPP

#include <cassert>
#include <cstddef>
#include <limits>
#include <vector>
#include "../common/work_stats.hpp"

namespace verifier_detail {

// Index of the upper median set bit of every mask of at most height + 1 bits.
// Removing both extreme set bits preserves that median. The remaining mask
// is smaller, so one lookup suffices per entry: O(2^height) time and space.
inline std::vector<int> median_table(int height) {
    assert(height >= 0 && height < std::numeric_limits<int>::digits);
    std::vector<int> median(std::size_t{1} << (height + 1), 0);
    KKT_WORK_ADD(initialized_slots, median.size());
    KKT_WORK_ADD(median_entries, median.size() - 1);
    std::size_t highest_bit = 1;
    int highest_index = 0;
    for (std::size_t mask = 1; mask < median.size(); ++mask) {
        if (mask == highest_bit * 2) {
            highest_bit = mask;
            ++highest_index;
        }
        const std::size_t inner = (mask & (mask - 1)) & (highest_bit - 1);
        // With one or two set bits, the upper median is the highest bit.
        median[mask] = inner == 0 ? highest_index : median[inner];
    }
    return median;
}

}  // namespace verifier_detail

#endif
