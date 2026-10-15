// Independent correctness gates for the opt-in multigraph contraction.
// No performance timings. The existing public simple-quotient test is separate.
#include "../kkt/experimental_multigraph_contraction.hpp"
#include "../benchmark/mst_certificate.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <random>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

namespace {
using Ids = std::unordered_set<int>;
using Result = std::pair<std::vector<int>, problem>;
std::size_t quotient_cases = 0, solver_calls = 0, exhaustive_cases = 0;
std::size_t simple_certificates = 0, certificate_rejections = 0;

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

// Slow relabel unions deliberately share no successor-walk or production DSU.
struct Partition {
    std::vector<int> labels;
    explicit Partition(int n) : labels(n) { std::iota(labels.begin(), labels.end(), 0); }
    bool join(int first, int second) {
        first = labels[first];
        second = labels[second];
        if (first == second) return false;
        for (int& label : labels) if (label == second) label = first;
        return true;
    }
};

Result quotient_oracle(const problem& input) {
    Partition partition(input.num_vertices);
    std::set<std::size_t> selected_positions;
    std::vector<int> selected;
    // Scan every edge separately for every vertex, preserving first-min ties.
    for (int vertex = 0; vertex < input.num_vertices; ++vertex) {
        std::size_t best = input.graph_edges.size();
        for (std::size_t i = 0; i < input.graph_edges.size(); ++i) {
            const Edge& edge = input.graph_edges[i];
            if (edge.from != vertex && edge.to != vertex) continue;
            if (best == input.graph_edges.size() || edge.cost < input.graph_edges[best].cost)
                best = i;
        }
        if (best == input.graph_edges.size() || !selected_positions.insert(best).second) continue;
        const Edge& edge = input.graph_edges[best];
        selected.push_back(edge.id);
        partition.join(edge.from, edge.to);
    }
    std::map<int, int> renumber;
    std::set<int> active;
    for (const Edge& edge : input.graph_edges) {
        if (partition.labels[edge.from] != partition.labels[edge.to]) {
            active.insert(partition.labels[edge.from]);
            active.insert(partition.labels[edge.to]);
        }
    }
    int next = 0;
    for (int label : partition.labels) {
        if (active.count(label) && renumber.emplace(label, next).second) ++next;
    }
    std::vector<Edge> quotient;
    for (const Edge& edge : input.graph_edges) {
        const int first = partition.labels[edge.from], second = partition.labels[edge.to];
        if (first != second) {
            const auto endpoints = std::minmax(renumber.at(first), renumber.at(second));
            quotient.emplace_back(endpoints.first, endpoints.second, edge.cost, edge.id);
        }
    }
    return {std::move(selected), problem(next, std::move(quotient), input.max_edge_id)};
}

void check_quotient(const problem& input, const std::string& context) {
    const auto original = input.graph_edges;
    const auto expected = quotient_oracle(input);
    Result actual;
#ifdef KKT_ENABLE_WORK_STATS
    kkt_work::WorkStats stats;
    {
        kkt_work::ScopedWorkStats scope(stats);
        actual = kkt_experiment::retain_parallel_step(input);
    }
    const std::uint64_t n = input.num_vertices, m = input.graph_edges.size();
    require(stats.contraction_calls == 1 && stats.contraction_vertices == n &&
            stats.contraction_edges == m, context + ": missing input counters");
    require(stats.contraction_edge_visits <= 3 * m, context + ": more than three edge scans");
    require(stats.contraction_arc_visits <= 2 * n, context + ": repeated successor walks");
    require(stats.contraction_vertex_visits <= 5 * n, context + ": excess vertex visits");
    require(stats.initialized_slots <= 4 * n, context + ": edge-sized scratch storage");
    require(stats.contraction_output_vertices == static_cast<std::uint64_t>(expected.second.num_vertices) &&
            stats.contraction_output_edges == expected.second.graph_edges.size() &&
            stats.edge_materializations == expected.second.graph_edges.size(),
            context + ": output counters differ");
    if (!expected.second.graph_edges.empty())
        require(stats.contraction_edge_visits == 3 * m, context + ": nonterminal scan accounting");
#else
    actual = kkt_experiment::retain_parallel_step(input);
#endif
    require(actual.first == expected.first, context + ": selected ID/order mismatch");
    require(actual.second.num_vertices == expected.second.num_vertices &&
            actual.second.graph_edges == expected.second.graph_edges &&
            actual.second.max_edge_id == input.max_edge_id,
            context + ": retained quotient endpoint/ID/cost/order/metadata mismatch");
    require(input.graph_edges == original, context + ": changed input");
    ++quotient_cases;
}

Ids sorted_forest_oracle(const problem& input) {
    auto ordered = input.graph_edges;
    std::sort(ordered.begin(), ordered.end(), [](const Edge& a, const Edge& b) { return a.cost < b.cost; });
    Partition partition(input.num_vertices);
    Ids result;
    for (const Edge& edge : ordered) if (partition.join(edge.from, edge.to)) result.insert(edge.id);
    return result;
}

// Separate multigraph-aware cycle certificate. It uses explicit tree walks,
// not KKT's verifier, binary lifting, the sorted oracle, or production DSU.
void certify_forest(const problem& input, const Ids& selected) {
    std::set<int> input_ids, weights;
    std::map<int, const Edge*> by_id;
    for (const Edge& edge : input.graph_edges) {
        require(edge.from >= 0 && edge.to >= 0 && edge.from < input.num_vertices &&
                edge.to < input.num_vertices && edge.from != edge.to, "certificate invalid endpoint");
        require(input_ids.insert(edge.id).second && weights.insert(edge.cost).second,
                "certificate duplicate ID or weight");
        by_id.emplace(edge.id, &edge);
    }
    std::vector<std::vector<std::pair<int, int>>> tree(input.num_vertices);
    Partition partition(input.num_vertices);
    for (int id : selected) {
        require(by_id.count(id) != 0, "certificate unknown ID");
        const Edge& edge = *by_id.at(id);
        require(partition.join(edge.from, edge.to), "certificate cycle");
        tree[edge.from].emplace_back(edge.to, edge.cost);
        tree[edge.to].emplace_back(edge.from, edge.cost);
    }
    for (const Edge& edge : input.graph_edges) {
        std::vector<int> maximum(input.num_vertices, std::numeric_limits<int>::min());
        std::vector<bool> seen(input.num_vertices, false);
        std::vector<int> pending{edge.from};
        seen[edge.from] = true;
        for (std::size_t position = 0; position < pending.size(); ++position) {
            const int vertex = pending[position];
            for (const auto& [next, cost] : tree[vertex]) {
                if (seen[next]) continue;
                maximum[next] = std::max(maximum[vertex], cost);
                seen[next] = true;
                pending.push_back(next);
            }
        }
        require(seen[edge.to], "certificate forest fails to span an input component");
        require(maximum[edge.to] <= edge.cost, "certificate improving cycle");
    }
}

void exhaustive_check(const problem& input, const Ids& expected) {
    require(input.graph_edges.size() <= 14, "exhaustive fixture too large");
    Partition input_partition(input.num_vertices);
    for (const Edge& edge : input.graph_edges) input_partition.join(edge.from, edge.to);
    std::int64_t best = std::numeric_limits<std::int64_t>::max();
    Ids best_ids;
    const std::uint64_t subsets = std::uint64_t{1} << input.graph_edges.size();
    for (std::uint64_t mask = 0; mask < subsets; ++mask) {
        Partition chosen(input.num_vertices);
        bool valid = true;
        std::int64_t cost = 0;
        Ids ids;
        for (std::size_t i = 0; i < input.graph_edges.size(); ++i) {
            if ((mask & (std::uint64_t{1} << i)) == 0) continue;
            const Edge& edge = input.graph_edges[i];
            if (!chosen.join(edge.from, edge.to)) { valid = false; break; }
            cost += edge.cost;
            ids.insert(edge.id);
        }
        if (!valid) continue;
        for (int a = 0; a < input.num_vertices; ++a)
            for (int b = 0; b < input.num_vertices; ++b)
                if ((input_partition.labels[a] == input_partition.labels[b]) !=
                    (chosen.labels[a] == chosen.labels[b])) valid = false;
        if (valid && cost < best) { best = cost; best_ids = std::move(ids); }
    }
    require(best_ids == expected && best != std::numeric_limits<std::int64_t>::max(),
            "exhaustive minimum forest disagrees");
    ++exhaustive_cases;
}

void check_solver(problem input, const std::string& context, bool exhaustive = false,
                  bool simple_fixture = false) {
    const auto expected = sorted_forest_oracle(input);
    certify_forest(input, expected);
    if (exhaustive) exhaustive_check(input, expected);
    const auto before = input.graph_edges;
    const auto metadata = input.max_edge_id;
    const auto vertices = input.num_vertices;
    const std::vector<unsigned int> seeds = {0u, 1u, 2u, 3u, 7u, 11u, 17u, 42u,
        97u, 149u, 401u, 503u, 1009u, 65537u, 123456789u,
        std::numeric_limits<unsigned int>::max()};
    for (unsigned int seed : seeds) {
        const auto actual = kkt(input, seed);
        require(actual == expected, context + ": solver mismatch seed " + std::to_string(seed));
        certify_forest(input, actual);
        require(input.graph_edges == before && input.max_edge_id == metadata &&
                input.num_vertices == vertices, context + ": solver mutated input");
        if (simple_fixture) {
            benchmark_validation::Graph graph, tree;
            for (const Edge& edge : input.graph_edges) {
                graph.emplace_back(edge.from, edge.to, edge.cost, edge.id);
                if (actual.count(edge.id)) tree.emplace_back(edge.from, edge.to, edge.cost, edge.id);
            }
            benchmark_validation::certify_mst(graph, tree, input.num_vertices);
            ++simple_certificates;
        }
        ++solver_calls;
    }
}

problem with_extreme_ids(problem input) {
    for (std::size_t i = 0; i < input.graph_edges.size(); ++i) {
        int id;
        if (i == 0) id = std::numeric_limits<int>::min();
        else if (i == 1) id = std::numeric_limits<int>::max();
        else if (i == 2) id = -1;
        else if (i == 3) id = 0;
        else id = (i % 2 ? -1 : 1) * static_cast<int>(i) * 100003;
        input.graph_edges[i].id = id;
    }
    input.max_edge_id = std::numeric_limits<std::int64_t>::max();
    return input;
}

void check_orders(problem input, const std::string& name, bool exhaustive = false,
                  bool simple_fixture = false) {
    for (int order = 0; order < 3; ++order) {
        if (order == 1) std::reverse(input.graph_edges.begin(), input.graph_edges.end());
        if (order == 2) {
            std::mt19937 rng(20261014);
            std::shuffle(input.graph_edges.begin(), input.graph_edges.end(), rng);
        }
        const std::string context = name + " order=" + std::to_string(order);
        check_quotient(input, context);
        check_solver(input, context, exhaustive, simple_fixture);
        auto extreme = with_extreme_ids(input);
        check_quotient(extreme, context + " extreme IDs");
        check_solver(extreme, context + " extreme IDs", exhaustive);
        extreme.max_edge_id = 0;
        check_solver(extreme, context + " zero metadata", exhaustive);
    }
}

void certificate_negative_gates() {
    const problem input(3, std::vector<Edge>{{0, 1, 1, 0}, {0, 1, 4, 1},
                                           {1, 2, 2, 2}, {0, 2, 3, 3}});
    for (const Ids& bad : {Ids{0, 99}, Ids{0}, Ids{0, 1, 2}, Ids{1, 3}}) {
        bool rejected = false;
        try { certify_forest(input, bad); } catch (const std::runtime_error&) { rejected = true; }
        require(rejected, "certificate accepted a deliberately invalid forest");
        ++certificate_rejections;
    }
}

void linked_candidate_gate() {
    std::vector<Edge> edges;
    for (int vertex = 1; vertex < 16; ++vertex) {
        int level = 0;
        for (int value = vertex; value % 2 == 0; value /= 2) ++level;
        edges.emplace_back(vertex - 1, vertex, level * 16 + vertex,
                           static_cast<int>(edges.size()));
    }
    for (int first = 0; first < 16; ++first) for (int second = first + 2; second < 16; ++second) {
        const int id = static_cast<int>(edges.size());
        edges.emplace_back(first, second, 1000 + id, id);
    }
    problem input(16, edges);
#ifdef KKT_ENABLE_WORK_STATS
    // A macro on this test TU alone is insufficient: these counters prove
    // that the linked kkt.cpp actually retained parallels after both rounds.
    kkt_work::WorkStats stats;
    {
        kkt_work::ScopedWorkStats scope(stats);
        const auto actual = kkt(input, 401);
        require(actual == sorted_forest_oracle(input), "linked candidate MST mismatch");
        certify_forest(input, actual);
        ++solver_calls;
    }
    require(stats.root_after_two_vertices == 4 && stats.root_after_two_edges == 96 &&
            stats.verifier_calls > 0, "linked KKT is not using the multigraph candidate");
#endif
    check_orders(input, "hierarchical complete linked dispatch", false, true);
    // Shift all costs below zero, including INT_MIN. Ordering, and therefore
    // the unique MSF, is unchanged; the verifier must not assume positive costs.
    for (Edge& edge : edges) edge.cost += std::numeric_limits<int>::min();
    edges.front().cost = std::numeric_limits<int>::min();
    edges.back().cost = std::numeric_limits<int>::max();
    check_orders(problem(16, edges), "signed extreme weights");
}
}  // namespace

int main() {
    try {
#ifndef KKT_EXPERIMENT_RETAIN_PARALLEL
        throw std::runtime_error("this gate requires the candidate compile-time switch");
#endif
        certificate_negative_gates();
        linked_candidate_gate();
        check_orders(problem(0, std::vector<Edge>{}), "empty", true);
        check_orders(problem(1, std::vector<Edge>{}), "singleton", true);
        check_orders(problem(12, std::vector<Edge>{}), "isolates", true);
        check_orders(problem(2, std::vector<Edge>{{0, 1, 1, 0}, {1, 0, 3, 1}, {0, 1, 2, 2}}),
                     "two vertex parallel", true);
        check_orders(problem(9, std::vector<Edge>{{0, 2, 1, 0}, {2, 4, 4, 1}, {0, 4, 6, 2},
            {2, 0, 3, 3}, {1, 3, 2, 4}, {3, 5, 5, 5}, {1, 5, 8, 6}, {5, 1, 7, 7}}),
            "disconnected parallel and isolates", true);

        // Simple inputs deliberately create large parallel bundles after the
        // first contraction. The existing simple-graph cycle certificate is
        // applied unchanged to every returned full-KKT solution.
        for (int pairs : {4, 8, 16, 32}) {
            std::vector<Edge> edges;
            for (int pair = 0; pair < pairs; ++pair)
                edges.emplace_back(2 * pair, 2 * pair + 1, pair + 1, static_cast<int>(edges.size()));
            for (int a = 0; a < pairs; ++a) for (int b = a + 1; b < pairs; ++b)
                for (int u = 0; u < 2; ++u) for (int v = 0; v < 2; ++v) {
                    const int id = static_cast<int>(edges.size());
                    edges.emplace_back(2 * a + u, 2 * b + v, id + 1, id);
                }
            problem input(2 * pairs, edges);
            const auto quotient = kkt_experiment::retain_parallel_step(input).second;
            require(quotient.graph_edges.size() == static_cast<std::size_t>(2 * pairs * (pairs - 1)),
                    "forced parallel quotient lost edges");
            check_orders(input, "complete paired simple n=" + std::to_string(2 * pairs), false, true);
            // Triple every original edge with distinct weights, then force a
            // sparse-ID multigraph through the same quotient and solver gate.
            const auto original = edges;
            for (int copy = 0; copy < 2; ++copy) for (const Edge& edge : original) {
                const int id = static_cast<int>(edges.size());
                edges.emplace_back(edge.to, edge.from, id + 1, id);
            }
            check_orders(problem(2 * pairs + 3, edges), "dense parallel with isolates");
        }

        std::mt19937 rng(20261014);
        for (int trial = 0; trial < 80; ++trial) {
            const int n = 2 + static_cast<int>(rng() % 47);
            const int m = trial < 8 ? 12 : static_cast<int>(rng() % (n * 7));
            std::vector<int> costs(m);
            std::iota(costs.begin(), costs.end(), 1);
            std::shuffle(costs.begin(), costs.end(), rng);
            std::vector<Edge> edges;
            for (int i = 0; i < m; ++i) {
                const int from = static_cast<int>(rng() % n);
                int to = static_cast<int>(rng() % (n - 1));
                if (to >= from) ++to;
                edges.emplace_back(from, to, costs[i], i);
            }
            check_orders(problem(n + trial % 3, edges), "random multigraph " + std::to_string(trial),
                         trial < 8);
        }

        // Prefix semantics only: ties and self-loops are outside full KKT's
        // unique-weight loop-free contract, but copying selection must not
        // accidentally change this helper's component/order behavior.
        for (int trial = 0; trial < 200; ++trial) {
            const int n = 1 + static_cast<int>(rng() % 24);
            std::vector<Edge> edges;
            const int m = static_cast<int>(rng() % 96);
            for (int i = 0; i < m; ++i)
                edges.emplace_back(rng() % n, rng() % n, static_cast<int>(rng() % 11) - 5, i);
            check_quotient(problem(n, edges), "prefix tie/loop " + std::to_string(trial));
        }
        std::cout << "PASS quotient_cases=" << quotient_cases << " solver_calls=" << solver_calls
                  << " exhaustive_cases=" << exhaustive_cases << " simple_certificates=" << simple_certificates
                  << " certificate_rejections=" << certificate_rejections << '\n';
    } catch (const std::exception& error) {
        std::cerr << "FAIL " << error.what() << '\n';
        return 1;
    }
}
