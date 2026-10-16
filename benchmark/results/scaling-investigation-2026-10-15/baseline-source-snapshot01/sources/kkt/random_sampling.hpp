#ifndef KKT_RANDOM_SAMPLING_HPP
#define KKT_RANDOM_SAMPLING_HPP

#include "kkt.hpp"
#include <random>

namespace kkt_detail {

// Keep the generator alive across samples so recursive calls consume new bits.
problem random_sampling(const problem& input, std::mt19937& rng);

}  // namespace kkt_detail

#endif
