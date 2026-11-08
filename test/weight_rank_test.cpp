// Independent ordering and MSF oracles for the optional weight-rank adapter.
#include "../kkt/experimental_weight_ranks.hpp"
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {
void require(bool value, const char* message) {
    if (!value) throw std::runtime_error(message);
}
struct DSU {
    std::vector<int> parent;
    explicit DSU(int n) : parent(n, -1) {}
    int root(int v) {
        while (parent[v] >= 0) {
            if (parent[parent[v]] >= 0) parent[v] = parent[parent[v]];
            v = parent[v];
        }
        return v;
    }
    bool join(int a, int b) {
        a = root(a); b = root(b);
        if (a == b) return false;
        if (parent[a] > parent[b]) std::swap(a, b);
        parent[a] += parent[b]; parent[b] = a;
        return true;
    }
};
std::vector<int> comparison_order(const problem& input) {
    std::vector<int> order(input.graph_edges.size());
    std::iota(order.begin(), order.end(), 0);
    std::sort(order.begin(), order.end(), [&](int a, int b) {
        const int x = input.graph_edges[a].cost, y = input.graph_edges[b].cost;
        return x != y ? x < y : a < b;
    });
    return order;
}
std::vector<int> reference_ids(const problem& input) {
    DSU forest(input.num_vertices);
    std::vector<int> ids;
    for (int position : comparison_order(input)) {
        const Edge& edge = input.graph_edges[position];
        if (forest.join(edge.from, edge.to)) ids.push_back(edge.id);
    }
    std::sort(ids.begin(), ids.end());
    return ids;
}
int edge_id(int position) {
    return position % 2 == 0 ? std::numeric_limits<int>::min() + position * 104729
                             : std::numeric_limits<int>::max() - position * 104729;
}
std::size_t fixture_count = 0, solver_calls = 0;
void check(const problem& input) {
    const problem original = input;
    kkt_experiment::weight_rank_work work;
    auto ranked = kkt_experiment::with_stable_weight_ranks(input, &work);
    require(input.graph_edges == original.graph_edges && input.num_vertices == original.num_vertices &&
            input.max_edge_id == original.max_edge_id, "ranker changed input");
    require(ranked.num_vertices == input.num_vertices && ranked.max_edge_id == input.max_edge_id,
            "ranker changed metadata");
    const auto order = comparison_order(input);
    require(ranked.graph_edges.size() == order.size(), "ranker changed edge count");
    for (std::size_t rank = 0; rank < order.size(); ++rank) {
        const auto& before = input.graph_edges[order[rank]];
        const auto& after = ranked.graph_edges[order[rank]];
        require(after.cost == static_cast<int>(rank), "ranker differs from comparison-sort oracle");
        require(before.from == after.from && before.to == after.to && before.id == after.id,
                "ranker changed endpoints, IDs, or record order");
    }
    const std::size_t m = order.size();
    require(work.radix_passes == (m ? 4 : 0) && work.histogram_edge_visits == 4*m &&
            work.scatter_edge_visits == 4*m && work.copied_edges == m && work.rank_writes == m,
            "rank-work receipt omitted a pass/copy");
    // This independent Kruskal sorts by (original weight, input position).
    const auto expected = reference_ids(input);
    const auto ranked_before = ranked.graph_edges;
    std::vector<std::pair<int, int>> positions;
    for (std::size_t i = 0; i < m; ++i) positions.emplace_back(input.graph_edges[i].id, static_cast<int>(i));
    std::sort(positions.begin(), positions.end());
    for (std::size_t i = 1; i < positions.size(); ++i)
        require(positions[i-1].first != positions[i].first, "fixture has duplicate IDs");
    const auto cost = [&](const std::vector<int>& ids) {
        std::int64_t total = 0;
        for (int id : ids) {
            const auto item = std::lower_bound(positions.begin(), positions.end(), std::make_pair(id, -1));
            require(item != positions.end() && item->first == id, "unknown output ID");
            total += input.graph_edges[item->second].cost; // ORIGINAL weights, widened sum.
        }
        return total;
    };
    for (unsigned seed : {0U, 42U, std::numeric_limits<unsigned>::max()}) {
        auto actual = kkt_edge_ids(ranked, seed);
        std::sort(actual.begin(), actual.end());
        require(std::adjacent_find(actual.begin(), actual.end()) == actual.end(), "duplicate output IDs");
        require(actual == expected, "ranked solver differs from original-weight Kruskal");
        require(cost(actual) == cost(expected), "original MSF cost differs");
        require(ranked.graph_edges == ranked_before && ranked.num_vertices == input.num_vertices &&
                ranked.max_edge_id == input.max_edge_id, "solver changed ranked input");
        ++solver_calls;
    }
    ++fixture_count;
}
void fixtures() {
    check(problem(0, std::vector<Edge>{}));
    check(problem(1000, std::vector<Edge>{}, std::numeric_limits<std::int64_t>::max()));
    check(problem(3, std::vector<Edge>{{0,1,INT32_MAX,INT32_MIN},{1,2,INT32_MAX-1,INT32_MAX}}));
    check(problem(10, std::vector<Edge>{{0,1,INT32_MIN,INT32_MIN},{0,1,INT32_MIN,INT32_MAX},
        {1,2,-1,-1000000007},{2,3,0,700000007},{0,3,INT32_MAX,-1},
        {4,5,7,0},{5,6,7,104729},{4,6,7,-104729}}, INT64_MAX));
    const int values[] = {INT32_MIN, INT32_MIN+1, -65537, -65536, -257, -256, -1, 0,
                          0, 1, 255, 256, 257, 65535, 65536, INT32_MAX-1, INT32_MAX};
    // Repeated signed byte-boundary values exercise stable order across all passes.
    for (bool reverse : {false, true}) {
        std::vector<Edge> edges;
        for (int i = 0; i < 136; ++i) edges.emplace_back(0, 1, values[i%17], edge_id(i));
        if (reverse) std::reverse(edges.begin(), edges.end());
        check(problem(4, std::move(edges), 0));
    }
    std::mt19937 rng(20261107);
    for (int trial = 0; trial < 160; ++trial) {
        const int active = 4 + trial%61;
        const int split = active/2;
        std::vector<Edge> edges;
        for (int i = 0; i < 6*active; ++i) {
            const bool second = (i%2 == 1);
            const int start = second ? split : 0, count = second ? active-split : split;
            const int a = rng()%count;
            int b = rng()%(count-1); if (b >= a) ++b;
            const int weight = values[rng()%17];
            edges.emplace_back(start+a, start+b, weight, edge_id(i));
        }
        std::shuffle(edges.begin(), edges.end(), rng);
        check(problem(active+trial%5, std::move(edges), trial%2 ? INT64_MAX : 0));
    }
    // Hierarchical ordering survives multiple contractions after equal costs are ranked.
    for (int n : {64, 256, 1024}) {
        std::vector<int> cuts(n-1); std::iota(cuts.begin(), cuts.end(), 1);
        std::stable_sort(cuts.begin(), cuts.end(), [](int a, int b) {
            return __builtin_ctz(static_cast<unsigned>(a)) < __builtin_ctz(static_cast<unsigned>(b));
        });
        std::vector<Edge> edges;
        for (int cut : cuts) edges.emplace_back(cut-1, cut, 17, edge_id(static_cast<int>(edges.size())));
        check(problem(n, std::move(edges)));
    }
}
} // namespace
int main() {
    try {
        fixtures();
        std::cout << "PASS weight-rank fixtures=" << fixture_count << " solver_calls=" << solver_calls << '\n';
    } catch (const std::exception& error) { std::cerr << error.what() << '\n'; return 1; }
}
