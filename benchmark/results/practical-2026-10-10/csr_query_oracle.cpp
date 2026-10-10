// Independent parent-walk oracle for the internal ancestor-query solver.
// Compile this translation unit with lca/lca.cpp; do not separately compile
// verifier_v2.cpp, whose current implementation is included below.
#include "../../../verifier/verifier_v2.cpp"

#include <algorithm>
#include <stdexcept>
#include <string>

namespace {

void require(bool value, const std::string& message) {
    if (!value) throw std::runtime_error(message);
}

void check_tree(const std::vector<int>& parent, const std::vector<int>& weight,
                int root) {
    const int n = static_cast<int>(parent.size());
    std::vector<int> child(n, -1), sibling(n, -1), depth(n, 0);
    for (int node = 0; node < n; ++node) {
        if (node == root) continue;
        sibling[node] = child[parent[node]];
        child[parent[node]] = node;
        for (int ancestor = node; ancestor != root; ancestor = parent[ancestor])
            ++depth[node];
    }
    const auto common_ancestor = [&](int a, int b) {
        while (depth[a] > depth[b]) a = parent[a];
        while (depth[b] > depth[a]) b = parent[b];
        while (a != b) { a = parent[a]; b = parent[b]; }
        return a;
    };
    std::vector<std::vector<path_query>> grouped(n);
    std::vector<int> expected;
    for (int from = 0; from < n; ++from) {
        for (int to = 0; to < n; ++to) {
            const int edge = static_cast<int>(expected.size());
            const int ancestor = common_ancestor(from, to);
            int maximum = std::numeric_limits<int>::lowest();
            for (int node = from; node != ancestor; node = parent[node])
                maximum = std::max(maximum, weight[node]);
            for (int node = to; node != ancestor; node = parent[node])
                maximum = std::max(maximum, weight[node]);
            expected.push_back(maximum);
            if (from != ancestor) grouped[from].push_back({ancestor, edge});
            if (to != ancestor) grouped[to].push_back({ancestor, edge});
        }
    }
    std::vector<std::size_t> offsets(1, 0);
    std::vector<path_query> queries;
    for (auto& group : grouped) {
        // Reversing within each endpoint also checks order independence.
        std::reverse(group.begin(), group.end());
        queries.insert(queries.end(), group.begin(), group.end());
        offsets.push_back(queries.size());
    }
    tree_path_maxima solver(root, child, sibling, weight, offsets, queries,
                            expected.size());
    require(solver.compute_answer() == expected,
            "internal ancestor paths differ from parent-walk maxima");

    const std::vector<std::size_t> no_offsets(n + 1, 0);
    const std::vector<path_query> no_queries;
    tree_path_maxima empty_solver(root, child, sibling, weight,
                                 no_offsets, no_queries, 3);
    require(empty_solver.compute_answer() == std::vector<int>(
                3, std::numeric_limits<int>::lowest()),
            "zero-query solver changed empty maxima");
}

}  // namespace

int main() {
    const int lowest = std::numeric_limits<int>::lowest();
    // All endpoint pairs include ancestor endpoints, two-half paths, and
    // zero-half self paths. Internal nodes obey the full-branching premise.
    check_tree({4, 4, 5, 5, 6, 6, 6},
               {lowest, -20, -100, -60, -10, -30, -1}, 6);
    check_tree({4, 4, 5, 5, 6, 6, 6}, {3, 7, 2, 6, 5, 9, -1}, 6);
    check_tree({3, 3, 3, 3}, {lowest, -11, 0, -1}, 3);
    std::cout << "PASS internal CSR ancestor/zero-query oracle\n";
}
