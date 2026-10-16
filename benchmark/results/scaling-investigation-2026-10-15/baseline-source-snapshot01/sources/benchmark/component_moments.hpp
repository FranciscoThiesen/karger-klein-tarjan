#ifndef BENCHMARK_COMPONENT_MOMENTS_HPP
#define BENCHMARK_COMPONENT_MOMENTS_HPP

#include "graph_fixtures.hpp"

#include <algorithm>
#include <cstdint>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <vector>

namespace benchmark_diagnostics {

// Untimed reconstruction of original-vertex component sizes from selected
// original edge IDs. The input Graph must outlive this object. Input IDs must
// be a permutation of [0,m); their tuple positions may be arbitrarily shuffled.
// Each accepted edge joins distinct components. Invalid batches fail at the
// offending edge; earlier edges in that batch have already been incorporated.
class ComponentMoments {
    const benchmark_fixtures::Graph& graph_;
    std::vector<int> id_to_index_, parent_, size_;
    int count_ = 0;
    int max_size_ = 0;
    std::uint64_t sum_squares_ = 0;

    int find(int v) {
        while (parent_[v] != v) {
            parent_[v] = parent_[parent_[v]];
            v = parent_[v];
        }
        return v;
    }

public:
    ComponentMoments(const benchmark_fixtures::Graph& graph, int n) : graph_(graph) {
        if (n < 0 || graph.size() > static_cast<std::size_t>(std::numeric_limits<int>::max()))
            throw std::runtime_error("invalid component-moment dimensions");
        id_to_index_.assign(graph.size(), -1);
        for (std::size_t index = 0; index < graph.size(); ++index) {
            const auto [u, v, weight, id] = graph[index];
            (void)weight;
            if (u < 0 || u >= n || v < 0 || v >= n || u == v ||
                id < 0 || static_cast<std::size_t>(id) >= graph.size() || id_to_index_[id] != -1)
                throw std::runtime_error("invalid component-moment endpoint or dense edge ID");
            id_to_index_[id] = static_cast<int>(index);
        }
        parent_.resize(n);
        std::iota(parent_.begin(), parent_.end(), 0);
        size_.assign(n, 1);
        count_ = n;
        max_size_ = n == 0 ? 0 : 1;
        sum_squares_ = static_cast<std::uint64_t>(n);
    }

    void accept_selected(const std::vector<int>& ids) {
        for (int id : ids) {
            if (id < 0 || static_cast<std::size_t>(id) >= id_to_index_.size())
                throw std::runtime_error("unknown selected edge ID in component moments");
            const auto& edge = graph_[id_to_index_[id]];
            int a = find(std::get<0>(edge)), b = find(std::get<1>(edge));
            if (a == b)
                throw std::runtime_error("repeated or cycle-forming selected edge in component moments");
            if (size_[a] < size_[b]) std::swap(a, b);
            sum_squares_ += std::uint64_t{2} * static_cast<std::uint64_t>(size_[a]) *
                            static_cast<std::uint64_t>(size_[b]);
            parent_[b] = a;
            size_[a] += size_[b];
            max_size_ = std::max(max_size_, size_[a]);
            --count_;
        }
    }

    int count() const { return count_; }
    std::uint64_t sum_squares() const { return sum_squares_; }
    int max_size() const { return max_size_; }
};

} // namespace benchmark_diagnostics

#endif
