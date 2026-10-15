#ifndef KKT_EXPERIMENTAL_COMPRESSED_QUERIES_HPP
#define KKT_EXPERIMENTAL_COMPRESSED_QUERIES_HPP

// Experimental private verifier representation. Include from verifier_v2.cpp
// only with KKT_EXPERIMENT_COMPRESSED_QUERIES; the default path is unchanged.
#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <vector>

#include "../common/work_stats.hpp"
#include "median_table.hpp"

namespace verifier_detail {

class compressed_tree_path_maxima {
    int height_ = 0;
    const int n_, root_;
    std::vector<int> depth_, propagated_, median_, path_, values_;
    std::vector<std::uint32_t> requested_;
    std::vector<std::size_t> offsets_;
    const std::vector<int>& child_;
    const std::vector<int>& sibling_;
    const std::vector<int>& weight_;
    std::size_t logical_requests_ = 0;
    bool computed_ = false;

    void set_depths(int vertex, int depth) {
        KKT_WORK_ADD(verifier_vertex_visits, 1);
        depth_[vertex] = depth;
        height_ = std::max(height_, depth);
        for (int next = child_[vertex]; next >= 0; next = sibling_[next])
            set_depths(next, depth + 1);
    }

    void init(int vertex) {
        KKT_WORK_ADD(path_init_vertices, 1);
        propagated_[vertex] = static_cast<int>(requested_[vertex]);
        for (int next = child_[vertex]; next >= 0; next = sibling_[next]) {
            init(next);
            propagated_[vertex] |= propagated_[next] & ~(1 << depth_[vertex]);
        }
    }

    // Keep the reference signed path-state arithmetic and traversal unchanged.
    static int down(int a, int b) {
        return b & (~(a | b) ^ (a + (a | ~b)));
    }

    void visit(int vertex, int state) {
        KKT_WORK_ADD(path_visit_vertices, 1);
        const auto binary_search = [&](int weight, int bits) {
            KKT_WORK_ADD(path_binary_search_calls, 1);
            if (bits == 0) return 0;
            int middle = median_[bits];
            while (bits != 1 << middle) {
                KKT_WORK_ADD(path_binary_search_steps, 1);
                bits &= (weight_[path_[middle]] > weight)
                    ? ~((1 << middle) - 1) : (1 << middle) - 1;
                middle = median_[bits];
            }
            return (weight_[path_[middle]] > weight) ? middle : 0;
        };

        path_[depth_[vertex]] = vertex;
        const int k = binary_search(weight_[vertex], down(propagated_[vertex], state));
        state = down(propagated_[vertex],
                     (state & ((1 << (k + 1)) - 1)) | (1 << depth_[vertex]));

        std::size_t destination = offsets_[vertex];
        std::uint32_t remaining = requested_[vertex];
        while (remaining != 0) {
            // Only enumerate actual requests, in the same order used by rank.
            const int depth = __builtin_ctz(remaining);
            const int node = path_[median_[down(static_cast<int>(bit(depth)), state)]];
            values_[destination++] = weight_[node];
            KKT_WORK_ADD(path_query_visits, 1);
            remaining &= remaining - 1;
        }
        assert(destination == offsets_[vertex + 1]);
        for (int next = child_[vertex]; next >= 0; next = sibling_[next])
            visit(next, state);
    }

public:
    // The supported bit domain matches the reference solver's signed masks.
    // A full tree additionally requires height < numeric_limits<int>::digits.
    static std::uint32_t bit(int depth) {
        assert(depth >= 0 && depth < std::numeric_limits<int>::digits);
        assert(depth < std::numeric_limits<std::uint32_t>::digits);
        return std::uint32_t{1} << depth;
    }

    static std::size_t rank(std::uint32_t mask, int depth) {
        const auto requested_bit = bit(depth);
        assert((mask & requested_bit) != 0);
        return static_cast<std::size_t>(__builtin_popcount(mask & (requested_bit - 1)));
    }

    compressed_tree_path_maxima(int root, const std::vector<int>& child,
                                const std::vector<int>& sibling,
                                const std::vector<int>& weight)
        : n_(static_cast<int>(child.size())), root_(root), depth_(n_, 0),
          propagated_(n_, 0), requested_(n_, 0), offsets_(static_cast<std::size_t>(n_) + 1, 0),
          child_(child), sibling_(sibling), weight_(weight) {
        assert(n_ > 0 && root_ >= 0 && root_ < n_);
        assert(child_.size() == sibling_.size() && child_.size() == weight_.size());
        KKT_WORK_ADD(initialized_slots, 4ULL * n_ + 1);
        set_depths(root_, 0);
        // Validate before constructing any depth mask, not after shifting.
        assert(height_ >= 0 && height_ < std::numeric_limits<int>::digits);
        assert(height_ < std::numeric_limits<std::uint32_t>::digits);
    }

    // The caller supplies an actual proper ancestor obtained from LCA.
    void add_request(int lower, int upper) {
        assert(!computed_);
        assert(lower >= 0 && lower < n_ && upper >= 0 && upper < n_);
        assert(depth_[upper] < depth_[lower]);
        requested_[lower] |= bit(depth_[upper]);
        ++logical_requests_;
        KKT_WORK_ADD(verifier_queries, 1);
        KKT_WORK_ADD(path_query_visits, 1);
    }

    void compute_answer() {
        assert(!computed_);
        KKT_WORK_ADD(verifier_vertex_visits, n_);
        for (int vertex = 0; vertex < n_; ++vertex) {
            const std::size_t count = static_cast<std::size_t>(__builtin_popcount(requested_[vertex]));
            assert(offsets_[vertex] <= std::numeric_limits<std::size_t>::max() - count);
            offsets_[vertex + 1] = offsets_[vertex] + count;
        }
        assert(offsets_.back() <= logical_requests_);
        values_.assign(offsets_.back(), std::numeric_limits<int>::lowest());
        KKT_WORK_ADD(initialized_slots, values_.size());
        init(root_);
        path_.assign(static_cast<std::size_t>(height_) + 1, 0);
        KKT_WORK_ADD(initialized_slots, path_.size());
        KKT_WORK_MAX(path_max_height, height_);
        median_ = median_table(height_);
        visit(root_, 0);
        computed_ = true;
    }

    int lookup(int lower, int upper) const {
        assert(computed_);
        assert(lower >= 0 && lower < n_ && upper >= 0 && upper < n_);
        assert(depth_[upper] < depth_[lower]);
        const std::size_t index = offsets_[lower] + rank(requested_[lower], depth_[upper]);
        assert(index < offsets_[lower + 1]);
        KKT_WORK_ADD(path_query_visits, 1);
        return values_[index];
    }

    std::size_t logical_requests() const { return logical_requests_; }
    std::size_t unique_requests() const {
        assert(computed_);
        return offsets_.back();
    }
};

} // namespace verifier_detail

#endif
