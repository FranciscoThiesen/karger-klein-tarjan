// Deterministic finite-word predicate gates; no sampling-frequency estimate.
#include "../kkt/experimental_eighth_sampling.hpp"

#include <cstdint>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <vector>

namespace {
void require(bool value, const char* message) {
    if (!value) throw std::runtime_error(message);
}

void check_word(std::uint32_t word) {
    // Independent arithmetic oracle, without copying the production bitmask.
    const bool half = kkt_detail::accept_scalar_sample_word<false>(word);
    const bool eighth = kkt_detail::accept_scalar_sample_word<true>(word);
    require(half == (word % 2 == 1), "half predicate differs from arithmetic oracle");
    require(eighth == (word % 8 == 7), "eighth predicate differs from arithmetic oracle");
    require(!eighth || half, "eighth accepts a word rejected by half");
}

void exhaustive_residues() {
    // All eight residues at varied high bits. Counts prove this finite map,
    // not independence of different outputs of a deterministic PRNG.
    for (std::uint32_t high : {0u, 0x100u, 0x80000000u, 0xfffffff8u,
                               0xaaaaaaa8u, 0x55555550u, 0x12345678u}) {
        unsigned half = 0, eighth = 0;
        for (std::uint32_t low = 0; low < 8; ++low) {
            const auto word = high + low;
            check_word(word);
            half += kkt_detail::accept_scalar_sample_word<false>(word);
            eighth += kkt_detail::accept_scalar_sample_word<true>(word);
        }
        require(half == 4 && eighth == 1, "wrong exact low-three-bit mapping");
    }
    for (std::uint32_t word = 0; word < 65536; ++word) check_word(word);
}

void word_extremes_and_bits() {
    for (std::uint32_t word : {0u, 1u, 2u, 3u, 4u, 5u, 6u, 7u, 8u, 15u,
                               0xffffffffu, 0xfffffffeu, 0x80000000u,
                               0xaaaaaaaau, 0x55555555u}) check_word(word);
    for (unsigned bit = 0; bit < 32; ++bit) {
        const auto word = std::uint32_t{1} << bit;
        check_word(word);
        check_word(~word);
    }
}

void scripted_positions_and_scalar_boundaries() {
    const std::vector<std::uint32_t> words{0u, 7u, 1u, 15u, 2u, 3u, 0xffffffffu,
        0x80000007u, 6u, 5u, 23u, 8u, 31u, 0u, 7u, 4u, 0x55555555u};
    std::size_t first = 0;
    for (std::size_t count : {0u, 1u, 2u, 7u, 0u, 3u, 4u, 0u}) {
        std::vector<std::size_t> half, eighth, wanted_half, wanted_eighth;
        require(first + count <= words.size(), "script is too short");
        for (std::size_t position = 0; position < count; ++position) {
            const auto word = words[first + position];
            if (kkt_detail::accept_scalar_sample_word<false>(word)) half.push_back(position);
            if (kkt_detail::accept_scalar_sample_word<true>(word)) eighth.push_back(position);
            if (word % 2 == 1) wanted_half.push_back(position);
            if (word % 8 == 7) wanted_eighth.push_back(position);
        }
        require(half == wanted_half && eighth == wanted_eighth,
                "scripted positions differ across scalar call boundaries");
        first += count;
    }
    require(first == words.size(), "script did not consume one word per position");
    // The helper has no engine or tail state; actual engine consumption and
    // private/public dispatch are checked in eighth_sampling_integration_test.
}
}  // namespace

int main() {
    try {
        exhaustive_residues();
        word_extremes_and_bits();
        scripted_positions_and_scalar_boundaries();
        std::cout << "PASS: three deterministic eighth-sampling predicate groups\n";
    } catch (const std::exception& error) {
        std::cerr << "FAIL: " << error.what() << '\n';
        return 1;
    }
}
