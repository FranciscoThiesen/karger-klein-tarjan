#ifndef BENCHMARK_MST_CERTIFICATE_HPP
#define BENCHMARK_MST_CERTIFICATE_HPP

#include <algorithm>
#include <cstdint>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

namespace benchmark_validation {

using Graph = std::vector<std::tuple<int, int, int, int>>;

namespace detail {

// Separate from the repository's UnionFind, so the reference MST does not
// certify its own connectivity through the same implementation.
class DisjointSet {
public:
    explicit DisjointSet(int n) : parent_(n), size_(n, 1), components_(n) {
        std::iota(parent_.begin(), parent_.end(), 0);
    }

    int find(int vertex) {
        int root = vertex;
        while (parent_[root] != root) root = parent_[root];
        while (parent_[vertex] != vertex) {
            const int next = parent_[vertex];
            parent_[vertex] = root;
            vertex = next;
        }
        return root;
    }

    bool unite(int a, int b) {
        a = find(a);
        b = find(b);
        if (a == b) return false;
        if (size_[a] < size_[b]) std::swap(a, b);
        parent_[b] = a;
        size_[a] += size_[b];
        --components_;
        return true;
    }

    int components() const { return components_; }

private:
    std::vector<int> parent_;
    std::vector<int> size_;
    int components_;
};

[[noreturn]] inline void reject(const std::string& message) {
    throw std::runtime_error("MST certificate: " + message);
}

}  // namespace detail

// Certify a benchmark fixture and its candidate MST independently of all four
// measured algorithms. Fixtures are simple connected undirected graphs with
// n >= 2, dense IDs [0,m), and distinct positive weights below Prim's sentinel.
// Sorting the fixture checks and binary lifting take O((m+n) log n) time for
// simple graphs; auxiliary storage is O(m + n log n). Run outside timing.
inline void certify_mst(const Graph& graph, const Graph& tree, int n) {
    if (n < 2) detail::reject("a fixture must contain at least two vertices");
    const std::size_t m = graph.size();
    const std::int64_t max_edges = static_cast<std::int64_t>(n) * (n - 1) / 2;
    if (m < static_cast<std::size_t>(n - 1) ||
        m > static_cast<std::size_t>(max_edges) ||
        m > static_cast<std::size_t>(std::numeric_limits<int>::max())) {
        detail::reject("edge count is incompatible with a simple connected fixture");
    }

    using Edge = Graph::value_type;
    std::vector<const Edge*> by_id(m, nullptr);
    {
        std::vector<int> weights;
        std::vector<std::uint64_t> endpoint_pairs;
        weights.reserve(m);
        endpoint_pairs.reserve(m);
        for (const auto& edge : graph) {
            const auto [from, to, weight, id] = edge;
            if (from < 0 || from >= n || to < 0 || to >= n || from == to) {
                detail::reject("invalid endpoint or self-loop in fixture");
            }
            if (weight <= 0 || weight >= 0x3f3f3f3f) {
                detail::reject("fixture weight is outside the shared algorithm domain");
            }
            if (id < 0 || static_cast<std::size_t>(id) >= m || by_id[id] != nullptr) {
                detail::reject("fixture IDs must be distinct and dense in [0,m)");
            }
            by_id[id] = &edge;
            weights.push_back(weight);
            endpoint_pairs.push_back((static_cast<std::uint64_t>(std::min(from, to)) << 32) |
                                     static_cast<std::uint64_t>(std::max(from, to)));
        }
        std::sort(weights.begin(), weights.end());
        if (std::adjacent_find(weights.begin(), weights.end()) != weights.end()) {
            detail::reject("fixture weights are not unique");
        }
        std::sort(endpoint_pairs.begin(), endpoint_pairs.end());
        if (std::adjacent_find(endpoint_pairs.begin(), endpoint_pairs.end()) != endpoint_pairs.end()) {
            detail::reject("fixture contains parallel edges");
        }
    }

    if (tree.size() != static_cast<std::size_t>(n - 1)) {
        detail::reject("candidate does not contain exactly n-1 edges");
    }
    detail::DisjointSet components(n);
    std::vector<bool> selected(m, false);
    std::vector<std::vector<std::pair<int, int>>> adjacency(n);
    std::int64_t tree_cost = 0;
    for (const auto& edge : tree) {
        const auto [from, to, weight, id] = edge;
        if (id < 0 || static_cast<std::size_t>(id) >= m || selected[id]) {
            detail::reject("candidate contains an unknown or duplicate edge ID");
        }
        const auto [input_from, input_to, input_weight, input_id] = *by_id[id];
        (void)input_id;
        if (weight != input_weight ||
            !((from == input_from && to == input_to) ||
              (from == input_to && to == input_from))) {
            detail::reject("candidate tuple does not match its input edge ID");
        }
        selected[id] = true;
        if (!components.unite(from, to)) detail::reject("candidate contains a cycle");
        adjacency[from].emplace_back(to, weight);
        adjacency[to].emplace_back(from, weight);
        tree_cost += static_cast<std::int64_t>(weight);
    }
    if (components.components() != 1) detail::reject("candidate is disconnected");
    // A connected spanning subgraph also establishes fixture connectivity.

    int levels = 1;
    while ((std::uint64_t{1} << levels) <= static_cast<std::uint64_t>(n)) ++levels;
    std::vector<std::vector<int>> ancestor(levels, std::vector<int>(n, 0));
    std::vector<std::vector<int>> maximum(levels, std::vector<int>(n, 0));
    std::vector<int> depth(n, -1);
    std::vector<int> pending;
    pending.reserve(n);
    pending.push_back(0);
    depth[0] = 0;
    for (std::size_t i = 0; i < pending.size(); ++i) {
        const int vertex = pending[i];
        for (const auto& [next, weight] : adjacency[vertex]) {
            if (depth[next] != -1) continue;
            depth[next] = depth[vertex] + 1;
            ancestor[0][next] = vertex;
            maximum[0][next] = weight;
            pending.push_back(next);
        }
    }
    if (pending.size() != static_cast<std::size_t>(n)) {
        detail::reject("candidate traversal did not reach every vertex");
    }
    for (int level = 1; level < levels; ++level) {
        for (int vertex = 0; vertex < n; ++vertex) {
            const int middle = ancestor[level - 1][vertex];
            ancestor[level][vertex] = ancestor[level - 1][middle];
            maximum[level][vertex] = std::max(maximum[level - 1][vertex],
                                              maximum[level - 1][middle]);
        }
    }

    const auto path_maximum = [&](int a, int b) {
        int result = 0;  // All fixture weights are positive.
        if (depth[a] < depth[b]) std::swap(a, b);
        unsigned int difference = static_cast<unsigned int>(depth[a] - depth[b]);
        for (int level = 0; difference != 0; ++level, difference >>= 1) {
            if ((difference & 1u) == 0) continue;
            result = std::max(result, maximum[level][a]);
            a = ancestor[level][a];
        }
        if (a == b) return result;
        for (int level = levels - 1; level >= 0; --level) {
            if (ancestor[level][a] == ancestor[level][b]) continue;
            result = std::max(result, std::max(maximum[level][a], maximum[level][b]));
            a = ancestor[level][a];
            b = ancestor[level][b];
        }
        return std::max(result, std::max(maximum[0][a], maximum[0][b]));
    };

    for (const auto& edge : graph) {
        const auto [from, to, weight, id] = edge;
        if (path_maximum(from, to) > weight) {
            detail::reject("candidate cost " + std::to_string(tree_cost) +
                           " is nonminimal: input edge " + std::to_string(id) +
                           " improves its tree cycle");
        }
    }
}

}  // namespace benchmark_validation

#endif
