// Untimed correctness gate for the exact six-solver harness and new control.
// Include its implementation so dispatch, CLI, tuple validation, and the
// continuation used by this test cannot silently diverge from the harness.
#define KKT_RETENTION_HARNESS_NO_MAIN
#include "../benchmark/retention_control.cpp"

#include <map>
#include <numeric>
#include <random>
#include <set>

namespace {
std::size_t simple_cases = 0, solver_outputs = 0, raw_cases = 0;
std::size_t rejected_trees = 0, rejected_options = 0, exhaustive_cases = 0;

struct Partition {
    std::vector<int> labels;
    explicit Partition(int n) : labels(n) { std::iota(labels.begin(), labels.end(), 0); }
    bool join(int from, int to) {
        const int first = labels[from], second = labels[to];
        if (first == second) return false;
        for (int& label : labels) if (label == second) label = first;
        return true;
    }
};

// Independent slow multigraph oracle: comparison sort and full label-unions,
// not production Kruskal, DSU, either contraction, or the KKT verifier.
Ids reference_forest(const problem& input) {
    auto sorted = input.graph_edges;
    std::sort(sorted.begin(), sorted.end(), [](const Edge& a, const Edge& b) { return a.cost < b.cost; });
    Partition partition(input.num_vertices);
    Ids expected;
    for (const Edge& edge : sorted)
        if (partition.join(edge.from, edge.to)) expected.insert(edge.id);
    return expected;
}

void certify_raw(const problem& input, const Ids& chosen) {
    std::map<int, const Edge*> by_id;
    std::set<int> weights;
    for (const Edge& edge : input.graph_edges) {
        require(edge.from >= 0 && edge.to >= 0 && edge.from < input.num_vertices &&
                edge.to < input.num_vertices && edge.from != edge.to, "raw invalid endpoint");
        require(by_id.emplace(edge.id, &edge).second && weights.insert(edge.cost).second,
                "raw duplicate ID or weight");
    }
    Partition tree_components(input.num_vertices);
    std::vector<std::vector<std::pair<int, int>>> tree(input.num_vertices);
    for (int id : chosen) {
        require(by_id.count(id), "raw unknown ID");
        const Edge& edge = *by_id.at(id);
        require(tree_components.join(edge.from, edge.to), "raw cycle");
        tree[edge.from].emplace_back(edge.to, edge.cost);
        tree[edge.to].emplace_back(edge.from, edge.cost);
    }
    for (const Edge& edge : input.graph_edges) {
        std::vector<bool> seen(input.num_vertices, false);
        std::vector<int> maximum(input.num_vertices, std::numeric_limits<int>::min());
        std::vector<int> pending{edge.from};
        seen[edge.from] = true;
        for (std::size_t i = 0; i < pending.size(); ++i) {
            const int vertex = pending[i];
            for (const auto& [next, cost] : tree[vertex]) {
                if (seen[next]) continue;
                seen[next] = true;
                maximum[next] = std::max(maximum[vertex], cost);
                pending.push_back(next);
            }
        }
        require(seen[edge.to], "raw forest does not span input component");
        require(maximum[edge.to] <= edge.cost, "raw improving cycle");
    }
}

void exhaustive(const problem& input, const Ids& expected) {
    require(input.graph_edges.size() <= 12, "raw exhaustive fixture too large");
    Partition input_components(input.num_vertices);
    for (const Edge& edge : input.graph_edges) input_components.join(edge.from, edge.to);
    std::int64_t best = std::numeric_limits<std::int64_t>::max();
    Ids best_ids;
    for (std::uint64_t mask = 0; mask < (UINT64_C(1) << input.graph_edges.size()); ++mask) {
        Partition chosen(input.num_vertices);
        bool valid = true;
        std::int64_t cost = 0;
        Ids selected;
        for (std::size_t i = 0; i < input.graph_edges.size(); ++i) if (mask & (UINT64_C(1) << i)) {
            const Edge& edge = input.graph_edges[i];
            if (!chosen.join(edge.from, edge.to)) { valid = false; break; }
            selected.insert(edge.id); cost += edge.cost;
        }
        if (!valid) continue;
        for (int a = 0; a < input.num_vertices; ++a)
            for (int b = 0; b < input.num_vertices; ++b)
                if ((input_components.labels[a] == input_components.labels[b]) !=
                    (chosen.labels[a] == chosen.labels[b])) valid = false;
        if (valid && cost < best) { best = cost; best_ids = std::move(selected); }
    }
    require(best != std::numeric_limits<std::int64_t>::max() && best_ids == expected,
            "exhaustive multigraph optimum differs");
    ++exhaustive_cases;
}

void check_raw(problem original, bool enumerate) {
    const auto expected = reference_forest(original);
    certify_raw(original, expected);
    if (enumerate) exhaustive(original, expected);
    for (unsigned int seed : {0u, 607u, std::numeric_limits<unsigned int>::max()}) {
        for (int algorithm = 0; algorithm < 3; ++algorithm) {
            problem input = original;
            const auto actual = algorithm == 0 ? kkt(input, seed) :
                (algorithm == 1 ? compacting_boruvka(input) : benchmark_retention::multigraph_boruvka(input));
            require(actual == expected, "raw multigraph solver mismatch");
            certify_raw(original, actual);
            if (algorithm == 0) require(input.graph_edges == original.graph_edges &&
                    input.num_vertices == original.num_vertices && input.max_edge_id == original.max_edge_id,
                    "candidate KKT mutated input");
            else require(input.graph_edges.empty() && input.num_vertices ==
                    (original.graph_edges.empty() ? original.num_vertices : 0) &&
                    input.max_edge_id == original.max_edge_id, "continuation did not consume quotient");
            ++solver_outputs;
        }
    }
    ++raw_cases;
}

void check_simple(const Spec& spec, unsigned int graph_seed) {
    const Graph graph = fixture(spec, graph_seed);
    require(graph.size() == static_cast<std::size_t>(fixture_edge_count(spec)), "fixture count mismatch");
    const auto reference = kruskal(graph, spec.n);
    benchmark_validation::certify_mst(graph, reference, spec.n);
    const auto expected = ids(reference);
    std::vector<const Graph::value_type*> by_id(graph.size());
    for (const auto& edge : graph) by_id[std::get<3>(edge)] = &edge;
    for (unsigned int seed : {0u, 607u, std::numeric_limits<unsigned int>::max()}) {
        for (int algorithm = 0; algorithm < 6; ++algorithm) {
            if (algorithm < 3) {
                problem input(spec.n, graph);
                const auto actual = algorithm == 0 ? kkt(input, seed) :
                    (algorithm == 1 ? compacting_boruvka(input) : benchmark_retention::multigraph_boruvka(input));
                require(actual == expected, "six-solver gate ID mismatch: " + std::string(algorithms[algorithm]));
                Graph selected;
                for (const auto& edge : graph) if (actual.count(std::get<3>(edge))) selected.push_back(edge);
                benchmark_validation::certify_mst(graph, selected, spec.n);
            } else {
                const auto solve = algorithm == 3 ? kruskal : (algorithm == 4 ? prim : boruvka);
                const auto actual = solve(graph, spec.n);
                require(valid_tree(actual, expected, by_id), "six-solver gate tuple mismatch");
                benchmark_validation::certify_mst(graph, actual, spec.n);
            }
            ++solver_outputs;
        }
    }
    // Exercise the exact harness validation routine, not a rewritten checker.
    for (int damage = 0; damage < 5; ++damage) {
        auto bad = reference;
        if (damage == 0) std::get<2>(bad.front()) += 1;
        if (damage == 1) std::get<0>(bad.front()) = spec.n;
        if (damage == 2) std::get<3>(bad.front()) = -1;
        if (damage == 3) bad.push_back(bad.front());
        if (damage == 4) bad.pop_back();
        require(!valid_tree(bad, expected, by_id), "harness accepted damaged tuple/ID result");
        ++rejected_trees;
    }
    ++simple_cases;
}

Options parse(std::vector<std::string> arguments) {
    std::vector<char*> argv;
    for (auto& argument : arguments) argv.push_back(argument.data());
    return options(static_cast<int>(argv.size()), argv.data());
}

void cli_gates() {
    const std::vector<std::string> base{"retention_control", "--family", "gnm_random", "--n", "32", "--density", "2"};
    require(parse(base).repetitions == 6 && parse(base).warmups == 1, "six-solver defaults differ");
    for (const std::string value : {"0", "1", "5", "7", "95", "97", "100", "-6", "4294967296", "6x"}) {
        auto arguments = base;
        arguments.insert(arguments.end(), {"--repetitions", value});
        bool rejected = false;
        try { (void)parse(arguments); } catch (const std::exception&) { rejected = true; }
        require(rejected, "unbalanced repetition count accepted"); ++rejected_options;
    }
    for (int repetitions : {6, 12, 96}) {
        auto arguments = base;
        arguments.insert(arguments.end(), {"--repetitions", std::to_string(repetitions)});
        require(parse(arguments).repetitions == repetitions, "balanced repetition count rejected");
        int positions[6][6]{};
        for (int rep = 0; rep < repetitions; ++rep)
            for (int order = 0; order < 6; ++order) ++positions[(order + rep) % 6][order];
        for (const auto& algorithm : positions) for (int count : algorithm)
            require(count == repetitions / 6, "six-algorithm position imbalance");
    }
}
} // namespace

int main() {
    try {
        cli_gates();
        for (const char* family : benchmark_attachments::families)
            check_simple({family, 1024, 2, 0}, 4000037);
        for (const char* family : {"leaf_hierarchy4", "leaf_distance4", "leaf_shuffled4", "leaf_random4"})
            check_simple({family, 512, 16, 0}, 4000039);
        for (const char* family : benchmark_search::families)
            check_simple({family, 256, 16, 0}, 4000037);
        for (const auto& spec : {Spec{"gnm_random", 64, 16, 0}, Spec{"gnm_random", 256, 16, 0}})
            check_simple(spec, 4000039);
        // Raw multigraphs are isolated correctness cases, never benchmark inputs.
        check_raw(problem(0, std::vector<Edge>{}), true);
        // Empty quotients retain original isolates because the continuation has
        // no work to consume.
        check_raw(problem(9, std::vector<Edge>{}), true);
        const problem disconnected(7, std::vector<Edge>{{0, 1, -10, -1}, {1, 0, 3, 100},
            {1, 2, -5, std::numeric_limits<int>::min()}, {0, 2, 9, 0},
            {3, 4, 2, std::numeric_limits<int>::max()}, {4, 3, 8, 19}}, INT64_MAX);
        check_raw(disconnected, true);
        std::mt19937 rng(20261015);
        for (int trial = 0; trial < 32; ++trial) {
            const int n = 2 + static_cast<int>(rng() % 7);
            std::vector<Edge> edges;
            for (int i = 0; i < 10; ++i) {
                const int from = static_cast<int>(rng() % n);
                int to = static_cast<int>(rng() % (n - 1)); if (to >= from) ++to;
                edges.emplace_back(from, to, i - 7, 1000000 - i * 100003);
            }
            std::shuffle(edges.begin(), edges.end(), rng);
            check_raw(problem(n + 2, edges, 0), true);
        }
        std::cout << "PASS simple_cases=" << simple_cases << " solver_outputs=" << solver_outputs
                  << " raw_cases=" << raw_cases << " exhaustive_cases=" << exhaustive_cases
                  << " rejected_trees=" << rejected_trees << " rejected_options=" << rejected_options << '\n';
    } catch (const std::exception& error) {
        std::cerr << "FAIL " << error.what() << '\n'; return 1;
    }
}
