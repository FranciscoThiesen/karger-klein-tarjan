// Focused correctness gate. Build with assertions and KKT_ENABLE_WORK_STATS.
// Link to either reference or candidate verifier; pass the expected policy at
// runtime so a wrongly linked binary cannot self-identify as the desired one.
#include "../verifier/experimental_compressed_queries.hpp"
#include "../verifier/verifier_v2.hpp"
#include "../common/edge.hpp"
#include "../common/work_stats.hpp"

#include <algorithm>
#include <csignal>
#include <cstdio>
#include <functional>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_set>
#include <vector>
#include <sys/wait.h>
#include <unistd.h>

#ifdef NDEBUG
#error This correctness gate requires assertion guards.
#endif
#ifndef KKT_ENABLE_WORK_STATS
#error This correctness gate requires the actual-dispatch work discriminator.
#endif

namespace {
using Graph = std::vector<std::tuple<int, int, int, int>>;
using Marks = std::vector<unsigned char>;
using Solver = verifier_detail::compressed_tree_path_maxima;
constexpr int low = std::numeric_limits<int>::min();
constexpr int high = std::numeric_limits<int>::max();
std::size_t oracle_cases = 0, rejected_cases = 0;

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

// Explicit forest walk per edge position: no LCA, FBT, masks, or production DSU.
Marks oracle(const Graph& graph, const Graph& forest, int n) {
    std::vector<std::vector<std::pair<int, int>>> adjacency(n);
    for (const auto& [u, v, cost, id] : forest) {
        (void)id;
        adjacency[u].emplace_back(v, cost);
        adjacency[v].emplace_back(u, cost);
    }
    Marks result(graph.size(), 0);
    for (std::size_t i = 0; i < graph.size(); ++i) {
        const auto [from, to, cost, id] = graph[i];
        (void)id;
        if (from == to) continue; // Preserve this API's established loop rule.
        std::vector<bool> seen(n, false);
        std::vector<int> maximum(n, low), queue{from};
        seen[from] = true;
        for (std::size_t next = 0; next < queue.size(); ++next) {
            const int vertex = queue[next];
            for (const auto& [neighbor, weight] : adjacency[vertex]) {
                if (seen[neighbor]) continue;
                seen[neighbor] = true;
                maximum[neighbor] = std::max(maximum[vertex], weight);
                queue.push_back(neighbor);
            }
        }
        if (seen[to] && maximum[to] < cost) result[i] = 1;
    }
    return result;
}

void check_marks(const Graph& graph, const Graph& forest, int n) {
    const auto expected = oracle(graph, forest, n);
    const auto before = graph, forest_before = forest;
    std::vector<Edge> edges(graph.begin(), graph.end());
    const auto edges_before = edges;
    require(verifier_detail::heavy_edge_marks(graph, forest, n) == expected, "tuple positional oracle");
    require(verifier_detail::heavy_edge_marks(edges, forest, n) == expected, "Edge positional oracle");
    std::unordered_set<int> ids;
    for (std::size_t i = 0; i < graph.size(); ++i)
        if (expected[i]) ids.insert(std::get<3>(graph[i]));
    require(verify_general_graph(graph, forest, n) == ids, "public forest ID adapter");
    if (n == 0 || forest.size() == static_cast<std::size_t>(n - 1))
        require(verify_mst(graph, forest, n) == ids, "public tree ID adapter");
    require(before == graph && forest_before == forest && edges_before == edges, "input mutation");
    ++oracle_cases;
}

void orders(Graph graph, Graph forest, int n) {
    for (int order = 0; order < 3; ++order) {
        check_marks(graph, forest, n);
        check_marks(graph, {}, n);
        check_marks({}, forest, n);
        std::reverse(graph.begin(), graph.end());
        std::reverse(forest.begin(), forest.end());
        for (auto& edge : graph) std::swap(std::get<0>(edge), std::get<1>(edge));
        for (auto& edge : forest) std::swap(std::get<0>(edge), std::get<1>(edge));
        if (!graph.empty()) std::rotate(graph.begin(), graph.begin() + graph.size() / 3, graph.end());
    }
}

void mark_oracles() {
    orders({}, {}, 0);
    orders({{0, 0, low, low}, {0, 0, high, high}}, {}, 1);
    const Graph forest{{0, 1, low, 7}, {1, 2, -7, 8}, {2, 3, high, 9},
                       {4, 5, -11, 10}};
    Graph graph;
    for (int u = 0; u < 7; ++u)
        for (int v = 0; v < 7; ++v)
            for (int cost : {low, -11, -7, 0, high})
                graph.emplace_back(u, v, cost, (u + v) % 2 ? low : high);
    orders(graph, forest, 7); // Isolate, cross-component edges, loops, repeated IDs.

    // Balanced path ranks generate multiple ancestor depths and duplicate keys.
    Graph path;
    for (int v = 1; v < 16; ++v) {
        int level = 0;
        for (int boundary = v; (boundary & 1) == 0; boundary >>= 1) ++level;
        path.emplace_back(v - 1, v, level * 100 + v - 400, v);
    }
    graph.clear();
    for (int u = 0; u < 16; ++u)
        for (int v = u; v < 16; ++v)
            for (int cost : {low, -390, -250, 0, high})
                graph.emplace_back(u, v, cost, -100003);
    orders(graph, path, 16);

    std::mt19937 engine(8089);
    for (int trial = 0; trial < 24; ++trial) {
        const int n = 2 + trial % 20;
        Graph random_forest, queries;
        for (int v = 1; v < n; ++v) {
            if (trial % 3 != 0 && engine() % 4 == 0) continue;
            random_forest.emplace_back(v, engine() % v, v * 7 - n * 3, v);
        }
        for (int i = 0; i < n * 10; ++i) {
            const int cost = i % 7 == 0 ? low : i % 7 == 1 ? high
                : static_cast<int>(engine() % 400) - 200;
            queries.emplace_back(engine() % n, engine() % n, cost, i % 2 ? low : high);
        }
        orders(queries, random_forest, n);
    }
}

struct TreeFixture {
    // Leaves 0..3, parents 4/5, root 6; every original leaf has depth two.
    std::vector<int> child{-1, -1, -1, -1, 0, 2, 4};
    std::vector<int> sibling{1, -1, 3, -1, 5, -1, -1};
    std::vector<int> weight{low, -7, 5, high, 2, -3, -1};
    std::vector<int> parent{4, 4, 5, 5, 6, 6, -1};
};

int ancestor_walk(const TreeFixture& fixture, int lower, int upper) {
    int answer = low;
    for (int vertex = lower; vertex != upper; vertex = fixture.parent[vertex]) {
        require(vertex >= 0, "test query is not an ancestor path");
        answer = std::max(answer, fixture.weight[vertex]);
    }
    return answer;
}

void helper_requests_and_rank() {
    TreeFixture fixture;
    Solver solver(6, fixture.child, fixture.sibling, fixture.weight);
    const std::vector<std::pair<int, int>> requests{
        {0, 6}, {0, 4}, {0, 6}, {1, 6}, {1, 4}, {2, 6},
        {2, 5}, {3, 6}, {3, 5}, {4, 6}, {5, 6}, {0, 4}};
    for (const auto& [lower, upper] : requests) solver.add_request(lower, upper);
    solver.compute_answer();
    require(solver.logical_requests() == 12 && solver.unique_requests() == 10,
            "logical versus unique request counts");
    for (const auto& [lower, upper] : requests)
        require(solver.lookup(lower, upper) == ancestor_walk(fixture, lower, upper),
                "direct ancestor path oracle");
    Solver empty(6, fixture.child, fixture.sibling, fixture.weight);
    empty.compute_answer();
    require(empty.logical_requests() == 0 && empty.unique_requests() == 0, "zero requests");

    for (const std::uint32_t mask : {1u, 2u, 0x40000000u, 0x40000083u, 0x7fffffffu}) {
        std::size_t expected_rank = 0;
        for (int depth = 0; depth < 31; ++depth) {
            if ((mask & (std::uint32_t{1} << depth)) == 0) continue;
            require(Solver::rank(mask, depth) == expected_rank, "root/high/noncontiguous rank");
            ++expected_rank;
        }
    }
}

void must_assert(const std::function<void()>& action, const char* name) {
    const pid_t pid = fork();
    require(pid >= 0, "fork failed");
    if (pid == 0) {
        (void)std::freopen("/dev/null", "w", stderr);
        action();
        _exit(0);
    }
    int status = 0;
    require(waitpid(pid, &status, 0) == pid, "waitpid failed");
    require(WIFSIGNALED(status) && WTERMSIG(status) == SIGABRT,
            std::string("malformed lookup was not assertion-rejected: ") + name);
    ++rejected_cases;
}

void malformed_lookup_guards() {
    must_assert([] { (void)Solver::rank(0, 0); }, "empty mask");
    must_assert([] { (void)Solver::rank(1, 1); }, "missing depth");
    must_assert([] { (void)Solver::bit(-1); }, "negative shift");
    must_assert([] { (void)Solver::bit(31); }, "unsupported shift");
    must_assert([] {
        TreeFixture f;
        Solver solver(6, f.child, f.sibling, f.weight);
        (void)solver.lookup(0, 6);
    }, "lookup before solve");
    must_assert([] {
        TreeFixture f;
        Solver solver(6, f.child, f.sibling, f.weight);
        solver.add_request(0, 6);
        solver.compute_answer();
        (void)solver.lookup(0, 4);
    }, "proper but unrequested ancestor");
    must_assert([] {
        TreeFixture f;
        Solver solver(6, f.child, f.sibling, f.weight);
        solver.add_request(0, 6);
        solver.compute_answer();
        (void)solver.lookup(0, 0);
    }, "nonproper ancestor");
}

void actual_dispatch_gate(bool compressed) {
    // All four vertices contract to a single root in the first FBT round.
    const Graph tree{{0, 1, -3, 0}, {0, 2, -2, 1}, {0, 3, -1, 2}};
    Graph queries;
    for (int from = 0; from < 4; ++from)
        for (int to = 0; to < 4; ++to)
            if (from != to) queries.emplace_back(from, to, from - to, -77);
    kkt_work::WorkStats stats;
    Marks result;
    {
        kkt_work::ScopedWorkStats scope(stats);
        result = verifier_detail::heavy_edge_marks(queries, tree, 4);
    }
    require(result == oracle(queries, tree, 4), "dispatch fixture oracle");
    require(stats.verifier_queries == 24, "logical request counter changed");
    require(stats.path_query_visits == (compressed ? 52 : 96), "wrong linked query representation");
    require(stats.path_max_height == 1 && stats.lca_queries == 12,
            "dispatch fixture structural counters");

    queries = {{0, 0, high, low}, {1, 1, low, high}, {3, 3, 0, -77}};
    stats = {};
    {
        kkt_work::ScopedWorkStats scope(stats);
        result = verifier_detail::heavy_edge_marks(queries, tree, 4);
    }
    require(result == Marks(3, 0) && stats.verifier_queries == 0 && stats.path_query_visits == 0,
            "all-loop Q=U=0 behavior");
}
} // namespace

int main(int argc, char** argv) {
    try {
        require(argc == 2, "expected reference or compressed policy argument");
        const std::string policy = argv[1];
        require(policy == "reference" || policy == "compressed", "unknown query policy");
        helper_requests_and_rank();
        malformed_lookup_guards();
        mark_oracles();
        actual_dispatch_gate(policy == "compressed");
        std::cout << "PASS " << oracle_cases << " positional cases, " << rejected_cases
                  << " malformed lookups; actual linked policy=" << policy << '\n';
    } catch (const std::exception& error) {
        std::cerr << "FAIL: " << error.what() << '\n';
        return 1;
    }
}
