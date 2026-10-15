#ifndef KKT_EXPERIMENTAL_EIGHTH_SAMPLING_HPP
#define KKT_EXPERIMENTAL_EIGHTH_SAMPLING_HPP

#include <cstdint>

namespace kkt_detail {

// A pure predicate: the caller still obtains exactly one word per edge.
// Under an ideal uniform 32-bit word, the all-ones low-bit masks accept
// exactly 1/2 or 1/8 of words. This does not assert MT seed independence.
template <bool use_eighth>
inline bool accept_scalar_sample_word(std::uint32_t word) {
    constexpr std::uint32_t mask = use_eighth ? 7u : 1u;
    return (word & mask) == mask;
}

}  // namespace kkt_detail

#endif
