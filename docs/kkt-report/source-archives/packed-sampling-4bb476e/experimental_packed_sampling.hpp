#ifndef KKT_EXPERIMENTAL_PACKED_SAMPLING_HPP
#define KKT_EXPERIMENTAL_PACKED_SAMPLING_HPP

#include <cstddef>
#include <cstdint>

namespace kkt_detail {

// next_word supplies full-width 32-bit words. Consume low bits first and emit
// accepted positions in input order. A partial final word is discarded here;
// the caller retains the same engine for the next recursive sampling call.
// Empty input consumes no word. This helper does not allocate or retain state.
template <class WordSource, class Emit>
inline void for_each_packed_sample_position(std::size_t count,
                                            WordSource& next_word, Emit&& emit) {
    std::size_t begin = 0;
    while (begin < count) {
        const std::size_t remaining = count - begin;
        const std::size_t length = remaining < 32 ? remaining : 32;
        std::uint32_t word = static_cast<std::uint32_t>(next_word());
        for (std::size_t bit = 0; bit < length; ++bit) {
            if ((word & std::uint32_t{1}) != 0) emit(begin + bit);
            word >>= 1;
        }
        begin += length;
    }
}

}  // namespace kkt_detail

#endif
