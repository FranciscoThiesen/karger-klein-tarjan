// Prepared source only: paired reference/depth verifier objects plus generic LCA.
// See DEPTH_QUERIES_PREPARATION.md for the four renamed candidate symbols.
#include "lca/lca.hpp"
#include "verifier/verifier_v2.hpp"
#include "verifier/experimental_depth_queries.hpp"
#include "verifier/experimental_compressed_queries.hpp"
#include "common/edge.hpp"
#include "benchmark/work_metrics.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

#ifndef KKT_ENABLE_WORK_STATS
#error "The paired correctness gate requires instrumented objects"
#endif
#ifdef NDEBUG
#error "This correctness source requires active assertion guards"
#endif

namespace verifier_detail {
std::vector<unsigned char> depth_heavy_edge_marks(
    const std::vector<std::tuple<int,int,int,int>>&,
    const std::vector<std::tuple<int,int,int,int>>&, int);
std::vector<unsigned char> depth_heavy_edge_marks(
    const std::vector<Edge>&,
    const std::vector<std::tuple<int,int,int,int>>&, int);
}

namespace {
using Graph = std::vector<std::tuple<int,int,int,int>>;
using Marks = std::vector<unsigned char>;
using Stats = kkt_work::WorkStats;
std::uint64_t tree_cases = 0, query_pairs = 0, mark_cases = 0, dispatch_cases = 0;

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

void same_stats(const Stats& a, const Stats& b) {
    for (const auto& field : benchmark_work::fields)
        require(a.*field.member == b.*field.member,
                std::string("overload field mismatch: ") + field.name);
}

void paired_stats(const Stats& reference, const Stats& depth) {
    for (const auto& field : benchmark_work::fields) {
        const auto a = reference.*field.member, b = depth.*field.member;
        if (std::string(field.name) == "initialized_slots")
            require(a >= b && a - b == reference.lca_vertices,
                    "depth dispatch / exact removed-height initialization mismatch");
        else require(a == b, std::string("paired field mismatch: ") + field.name);
    }
    if (reference.lca_vertices) ++dispatch_cases;
}

int parent_lca(int u, int v, const std::vector<int>& parent,
               const std::vector<int>& depth) {
    while (depth[u] > depth[v]) u = parent[u];
    while (depth[v] > depth[u]) v = parent[v];
    while (u != v) { u = parent[u]; v = parent[v]; }
    return u;
}

// Exact path maximum on the supplied forest, independent of FBT/LCA code.
Marks forest_oracle(const Graph& graph, const Graph& forest, int n) {
    std::vector<std::vector<std::pair<int,int>>> adjacency(n);
    for (const auto& [u,v,w,id] : forest) {
        (void)id; adjacency[u].emplace_back(v,w); adjacency[v].emplace_back(u,w);
    }
    Marks result(graph.size(), 0);
    for (std::size_t i = 0; i < graph.size(); ++i) {
        const auto [u,v,w,id] = graph[i]; (void)id;
        if (u == v) continue; // Preserve the verifier's legacy loop contract.
        std::vector<unsigned char> seen(n, 0);
        std::vector<int> maximum(n, std::numeric_limits<int>::lowest()), queue{u};
        seen[u] = 1;
        for (std::size_t j = 0; j < queue.size(); ++j)
            for (const auto& [next,weight] : adjacency[queue[j]]) {
                if (seen[next]) continue;
                seen[next] = 1;
                maximum[next] = std::max(maximum[queue[j]], weight);
                queue.push_back(next);
            }
        if (seen[v] && w > maximum[v]) result[i] = 1;
    }
    return result;
}

void check_marks(const Graph& graph, const Graph& forest, int n) {
    const auto before = graph, forest_before = forest;
    std::vector<Edge> edges(graph.begin(), graph.end());
    const auto edges_before = edges;
    const auto wanted = forest_oracle(graph, forest, n);
    Stats reference_tuple, depth_tuple, reference_edge, depth_edge;
    Marks a,b,c,d;
    { kkt_work::ScopedWorkStats scope(reference_tuple);
      a = verifier_detail::heavy_edge_marks(graph, forest, n); }
    { kkt_work::ScopedWorkStats scope(depth_tuple);
      b = verifier_detail::depth_heavy_edge_marks(graph, forest, n); }
    { kkt_work::ScopedWorkStats scope(reference_edge);
      c = verifier_detail::heavy_edge_marks(edges, forest, n); }
    { kkt_work::ScopedWorkStats scope(depth_edge);
      d = verifier_detail::depth_heavy_edge_marks(edges, forest, n); }
    require(a == wanted && b == wanted && c == wanted && d == wanted,
            "independent positional heavy-mark mismatch");
    same_stats(reference_tuple, reference_edge); same_stats(depth_tuple, depth_edge);
    paired_stats(reference_tuple, depth_tuple); paired_stats(reference_edge, depth_edge);
    require(graph == before && forest == forest_before && edges == edges_before,
            "verifier mutated its input");
    ++mark_cases;
}

void check_tree(int n, int shape, bool reverse_labels) {
    std::vector<int> parent(n), depth(n);
    std::vector<std::vector<int>> children(n);
    auto label = [&](int v) { return reverse_labels ? n - 1 - v : v; };
    const int root = label(0); parent[root] = root;
    std::mt19937 rng(1009u + static_cast<unsigned>(n * 17 + shape));
    Graph forest;
    for (int v = 1; v < n; ++v) {
        const int p = shape == 0 ? v - 1 : shape == 1 ? 0
                    : shape == 2 ? (v - 1) / 2 : static_cast<int>(rng() % v);
        parent[label(v)] = label(p); depth[label(v)] = depth[label(p)] + 1;
        children[label(p)].push_back(label(v));
        forest.emplace_back(label(p), label(v), v * 7 - n * 3, v);
    }
    if (reverse_labels) for (auto& row : children) std::reverse(row.begin(), row.end());
    std::vector<int> a,b; a.reserve(static_cast<std::size_t>(n)*n); b.reserve(a.capacity());
    Stats sa,sb;
    {
        kkt_work::ScopedWorkStats scope(sa); LCA reference(n, children, root);
        for (int u = 0; u < n; ++u) for (int v = 0; v < n; ++v) {
            const int ancestor = reference.query(u,v);
            require(ancestor == parent_lca(u,v,parent,depth), "generic LCA oracle mismatch");
            a.push_back(depth[ancestor]);
        }
    }
    {
        kkt_work::ScopedWorkStats scope(sb); verifier_detail::depth_lca candidate(n, children, root);
        for (int u = 0; u < n; ++u) for (int v = 0; v < n; ++v) {
            const int answer = candidate.query_depth(u,v);
            require(answer == depth[parent_lca(u,v,parent,depth)], "depth LCA oracle mismatch");
            b.push_back(answer);
        }
    }
    require(a == b, "LCA answer depths differ"); paired_stats(sa,sb);
    query_pairs += a.size(); ++tree_cases;
    if (n <= 33) {
        Graph queries = forest;
        for (int u = 0; u < n; ++u) for (int v = 0; v < n; ++v)
            queries.emplace_back(u,v,(u * 29 + v * 17) % (n * 13 + 1) - n * 4,
                                 (u+v)%2 ? std::numeric_limits<int>::max() : -1);
        check_marks(queries,forest,n);
        Graph disconnected;
        for (std::size_t i = 0; i < forest.size(); ++i)
            if (i % 3 != 0) disconnected.push_back(forest[i]);
        check_marks(queries,disconnected,n);
        std::reverse(queries.begin(),queries.end()); std::reverse(disconnected.begin(),disconnected.end());
        check_marks(queries,disconnected,n);
    }
}

void helper_api_parity() {
    // Equal-depth four-leaf FBT with an actual ancestor at depth zero.
    const std::vector<int> child{-1,-1,-1,-1,0,2,4};
    const std::vector<int> sibling{1,-1,3,-1,5,-1,-1};
    const std::vector<int> weight{-11,7,19,-5,2,13,-1};
    verifier_detail::compressed_tree_path_maxima ids(6,child,sibling,weight);
    verifier_detail::compressed_tree_path_maxima depths(6,child,sibling,weight);
    Stats a,b;
    { kkt_work::ScopedWorkStats scope(a);
      for (int leaf = 0; leaf < 4; ++leaf) {
          ids.add_request(leaf,6); ids.add_request(leaf,6); ids.add_request(leaf,leaf<2?4:5);
      }
      ids.compute_answer();
      for (int leaf = 0; leaf < 4; ++leaf) {
          require(ids.lookup(leaf,6) == std::max(weight[leaf],weight[leaf<2?4:5]), "ID helper root oracle");
          require(ids.lookup(leaf,leaf<2?4:5) == weight[leaf], "ID helper parent oracle");
      }
    }
    { kkt_work::ScopedWorkStats scope(b);
      for (int leaf = 0; leaf < 4; ++leaf) {
          depths.add_request_depth(leaf,0); depths.add_request_depth(leaf,0); depths.add_request_depth(leaf,1);
      }
      depths.compute_answer();
      for (int leaf = 0; leaf < 4; ++leaf) {
          require(depths.lookup_depth(leaf,0) == std::max(weight[leaf],weight[leaf<2?4:5]), "depth helper root oracle");
          require(depths.lookup_depth(leaf,1) == weight[leaf], "depth helper parent oracle");
      }
    }
    same_stats(a,b);
}

// Run each guard case as a separately bounded child after release. Acceptance
// requires actual SIGABRT from an assertion, not an arbitrary nonzero exit.
void invalid_depth_case(const std::string& mode) {
    const std::vector<int> child{-1,-1,-1,-1,0,2,4};
    const std::vector<int> sibling{1,-1,3,-1,5,-1,-1};
    const std::vector<int> weight{-11,7,19,-5,2,13,-1};
    verifier_detail::compressed_tree_path_maxima helper(6,child,sibling,weight);
    if (mode == "guard-add-negative") helper.add_request_depth(0,-1);
    else if (mode == "guard-add-equal") helper.add_request_depth(0,2);
    else if (mode == "guard-add-deeper") helper.add_request_depth(0,3);
    else if (mode == "guard-lookup-absent") {
        helper.compute_answer(); (void)helper.lookup_depth(0,0);
    } else throw std::runtime_error("unknown guard case");
}
}

int main(int argc, char** argv) {
    try {
        if (argc == 2) {
            invalid_depth_case(argv[1]);
            std::cerr << "invalid depth call returned instead of asserting\n";
            return 0; // A negative gate must reject this normal exit.
        }
        require(argc == 1, "unexpected arguments");
        helper_api_parity();
        for (int n : {1,2,3,4,7,8,9,15,16,17,31,32,33,63,64,65,127,128,129,257,513})
            for (int shape = 0; shape < 4; ++shape) {
                if (shape == 0 && n > 129) continue;
                check_tree(n,shape,false); check_tree(n,shape,true);
            }
        const int low = std::numeric_limits<int>::min(), high = std::numeric_limits<int>::max();
        check_marks({}, {}, 0);
        check_marks({{0,0,low,high},{0,0,high,low}}, {}, 1);
        const Graph forest{{0,1,low,high},{1,2,-20,low},{2,3,5,-1},{4,5,high-1,42}};
        const Graph queries{{0,1,low,low},{1,0,low+1,low},{0,2,-20,high},{2,0,-21,high},
            {0,3,6,-1},{3,0,5,-1},{4,5,high,17},{5,4,high-1,17},
            {2,5,high,0},{6,7,high,0},{0,0,high,low},{7,7,low,high}};
        require(forest_oracle(queries,forest,8) == Marks{0,1,0,0,1,0,1,0,0,0,0,0}, "explicit boundary oracle");
        check_marks(queries,forest,8); check_marks(queries,{},8); check_marks({},forest,8);
        require(dispatch_cases > 0 && mark_cases > 0 && query_pairs > 0, "empty test coverage");
        std::cout << "depth_queries_test pass trees=" << tree_cases << " query_pairs=" << query_pairs
                  << " marks=" << mark_cases << " dispatch_cases=" << dispatch_cases << '\n';
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n'; return 1;
    }
}
