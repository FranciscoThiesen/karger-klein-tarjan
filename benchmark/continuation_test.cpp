// Independent structure and MST checks for the continuation experiment.
// This executable contains no timings and does not use assert for validation.
#include "continuation_fixtures.hpp"
#include "mst_certificate.hpp"
#include "../kkt/kkt.hpp"
#include "../kruskal/kruskal.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_set>
#include <utility>
#include <vector>

std::pair<std::vector<int>, problem> boruvka_step(const problem& input);

namespace {
using Graph = std::vector<std::tuple<int, int, int, int>>;
using benchmark_continuation::Fixture;
using benchmark_continuation::Spec;

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

// Separate from both the production union-find and certificate's DSU.
class Components {
    std::vector<int> parent;
public:
    explicit Components(int n) : parent(n) { std::iota(parent.begin(), parent.end(), 0); }
    int find(int v) {
        while (parent[v] != v) v = parent[v];
        return v;
    }
    bool join(int u, int v) {
        u = find(u); v = find(v);
        if (u == v) return false;
        parent[std::max(u, v)] = std::min(u, v);
        return true;
    }
};

std::uint64_t pair_key(int u, int v) {
    if (u > v) std::swap(u, v);
    return (static_cast<std::uint64_t>(u) << 32) | static_cast<unsigned int>(v);
}

std::unordered_set<int> edge_ids(const Graph& graph) {
    std::unordered_set<int> result;
    for (const auto& edge : graph) require(result.insert(std::get<3>(edge)).second, "duplicate tree ID");
    return result;
}

struct Reduction {
    std::set<int> selected;
    int vertices;
    Graph canonical_edges;
};

// The deliberately simple vertex-by-edge scan and ordered pair map do not
// share production's successor-walk or stamped-bucket implementation.
Reduction independent_reduction(const problem& input) {
    Components components(input.num_vertices);
    std::set<int> selected;
    for (int vertex = 0; vertex < input.num_vertices; ++vertex) {
        const Edge* best = nullptr;
        for (const auto& edge : input.graph_edges) {
            if ((edge.from == vertex || edge.to == vertex) &&
                (!best || edge.cost < best->cost)) best = &edge;
        }
        require(best != nullptr, "connected contraction input has an isolate");
        selected.insert(best->id);
        components.join(best->from, best->to);
    }
    std::map<int, int> labels;
    for (int vertex = 0; vertex < input.num_vertices; ++vertex) {
        const int representative = components.find(vertex);
        if (!labels.count(representative)) labels.emplace(representative, static_cast<int>(labels.size()));
    }
    if (labels.size() == 1) return {std::move(selected), 0, {}};
    std::map<std::pair<int, int>, std::pair<int, int>> cheapest;
    for (const auto& edge : input.graph_edges) {
        int u = labels.at(components.find(edge.from));
        int v = labels.at(components.find(edge.to));
        if (u == v) continue;
        if (u > v) std::swap(u, v);
        const auto key = std::make_pair(u, v);
        const auto found = cheapest.find(key);
        if (found == cheapest.end() || edge.cost < found->second.first)
            cheapest[key] = {edge.cost, edge.id};
    }
    Graph edges;
    for (const auto& [ends, value] : cheapest)
        edges.emplace_back(ends.first, ends.second, value.first, value.second);
    return {std::move(selected), static_cast<int>(labels.size()), std::move(edges)};
}

int check_contractions(const Graph& graph, int n, bool exact_halving) {
    problem current(n, graph);
    int rounds = 0;
    while (!current.graph_edges.empty()) {
        const auto before = current.graph_edges;
        const auto expected = independent_reduction(current);
        auto actual = boruvka_step(current);
        require(current.graph_edges == before, "contraction modified its input");
        const std::set<int> selected(actual.first.begin(), actual.first.end());
        require(selected.size() == actual.first.size() && selected == expected.selected,
                "selected IDs disagree with independent minimum-edge union");
        Graph canonical;
        for (const auto& edge : actual.second.graph_edges)
            canonical.emplace_back(std::min(edge.from, edge.to), std::max(edge.from, edge.to),
                                   edge.cost, edge.id);
        std::sort(canonical.begin(), canonical.end());
        require(actual.second.num_vertices == expected.vertices && canonical == expected.canonical_edges,
                "contracted partition or minimum parallel edge differs from independent oracle");
        ++rounds;
        if (exact_halving) {
            const int remaining = n >> rounds;
            require(actual.second.num_vertices == (remaining == 1 ? 0 : remaining),
                    "hierarchical graph did not merge exactly paired dyadic blocks");
        }
        require(rounds <= 30, "contraction did not finish");
        current = std::move(actual.second);
    }
    return rounds;
}

std::vector<int> backbone_order(const Fixture& fixture, int n) {
    std::vector<std::pair<int, int>> ranked;
    for (const auto& [u, v, cost, id] : fixture.graph) {
        (void)u; (void)v;
        if (id < n - 1) ranked.emplace_back(cost, id);
    }
    std::sort(ranked.begin(), ranked.end());
    std::vector<int> result;
    for (const auto& [cost, id] : ranked) { (void)cost; result.push_back(id); }
    return result;
}

void check_paired_topology(const Fixture& a, const Fixture& b) {
    require(a.graph.size() == b.graph.size() && a.original_to_label == b.original_to_label &&
            a.backbone_ids == b.backbone_ids && a.hierarchy_levels == b.hierarchy_levels,
            "paired variants changed labels or topology metadata");
    for (std::size_t i = 0; i < a.graph.size(); ++i) {
        require(std::get<0>(a.graph[i]) == std::get<0>(b.graph[i]) &&
                std::get<1>(a.graph[i]) == std::get<1>(b.graph[i]) &&
                std::get<3>(a.graph[i]) == std::get<3>(b.graph[i]),
                "paired variants changed endpoints, edge IDs, or input order");
    }
}

// When every lower dyadic level precedes every higher level, both children
// already have their MSTs before this cut is considered. Select its unique
// minimum directly, independently of Kruskal or production contraction.
Graph dyadic_cut_mst(const Graph& graph, const std::vector<int>& original, int n) {
    Graph result;
    for (int width = 2; width <= n; width *= 2) {
        for (int base = 0; base < n; base += width) {
            const int middle = base + width / 2, end = base + width;
            const Graph::value_type* best = nullptr;
            for (const auto& edge : graph) {
                int u = original[std::get<0>(edge)], v = original[std::get<1>(edge)];
                if (u > v) std::swap(u, v);
                if (u >= base && u < middle && v >= middle && v < end &&
                    (!best || std::get<2>(edge) < std::get<2>(*best))) best = &edge;
            }
            require(best != nullptr, "dyadic children lack a joining edge");
            result.push_back(*best);
        }
    }
    return result;
}

int check_fixture(const Spec& spec, unsigned seed) {
    const int n = spec.n;
    const std::int64_t expected_m = static_cast<std::int64_t>(n) * spec.density;
    const auto fixture = benchmark_continuation::make_fixture(spec, seed);
    const auto& graph = fixture.graph;
    require(static_cast<std::int64_t>(graph.size()) == expected_m &&
            benchmark_continuation::edge_count(spec) == expected_m, "edge count differs from density*n");
    const int m = static_cast<int>(expected_m);
    const auto replay = benchmark_continuation::make_fixture(spec, seed);
    require(graph == replay.graph && fixture.original_to_label == replay.original_to_label &&
            fixture.backbone_ids == replay.backbone_ids && fixture.hierarchy_levels == replay.hierarchy_levels,
            "fixture replay changed");
    require(fixture.original_to_label.size() == static_cast<std::size_t>(n) &&
            fixture.hierarchy_levels.size() == graph.size(), "missing fixture metadata");
    std::vector<int> original(n, -1);
    for (int v = 0; v < n; ++v) {
        const int label = fixture.original_to_label[v];
        require(label >= 0 && label < n && original[label] == -1, "labels are not a permutation");
        original[label] = v;
    }
    std::vector<int> expected_backbone(n - 1);
    std::iota(expected_backbone.begin(), expected_backbone.end(), 0);
    require(fixture.backbone_ids == expected_backbone, "backbone metadata is not IDs0..n-2");

    Components connected(n), backbone_components(n);
    std::unordered_set<std::uint64_t> pairs;
    std::vector<bool> ids(m), ranks(m);
    std::vector<int> actual_levels(m, -1);
    std::map<std::pair<int, int>, int> dyadic_bridges;
    Graph backbone;
    const bool path = spec.family.find("path") != std::string::npos;
    const bool random_weights = spec.family.find("random_") == 0;
    const bool hierarchy = spec.family.find("hierarchical_") == 0;
    const bool distance = spec.family.find("distance_") == 0;
    const bool cheap_backbone = !random_weights && !distance;
    const int q = static_cast<int>(static_cast<std::int64_t>(n) * spec.intrusion_per_mille / 1000);
    int cheap_chords = 0;
    for (const auto& edge : graph) {
        const auto [u, v, weight, id] = edge;
        require(u >= 0 && u < n && v >= 0 && v < n && u != v, "invalid endpoints or self-loop");
        require(id >= 0 && id < m && !ids[id], "IDs are not distinct dense integers");
        require(weight >= 1 && weight <= m && !ranks[weight - 1], "weights are not distinct ranks1..m");
        ids[id] = true; ranks[weight - 1] = true;
        require(pairs.insert(pair_key(u, v)).second, "parallel fixture edge");
        connected.join(u, v);
        if (id < n - 1) {
            require(backbone_components.join(u, v), "backbone is cyclic");
            backbone.push_back(edge);
            int a = original[u], b = original[v];
            if (a > b) std::swap(a, b);
            if (path) require(a == id && b == id + 1, "path backbone changed");
            int level = 0;
            for (int differing = a ^ b; differing > 1; differing >>= 1) ++level;
            actual_levels[id] = level;
            ++dyadic_bridges[{level, a >> (level + 1)}];
            if (cheap_backbone) require(weight <= n - 1 + q, "backbone outside cheap-rank prefix");
        } else if (cheap_backbone && weight <= n - 1 + q) {
            ++cheap_chords;
        }
        require(fixture.hierarchy_levels[id] == actual_levels[id], "hierarchy metadata differs from dyadic endpoints");
    }
    require(backbone.size() == static_cast<std::size_t>(n - 1), "wrong backbone size");
    for (int v = 0; v < n; ++v) {
        require(connected.find(v) == connected.find(0), "fixture is disconnected");
        require(backbone_components.find(v) == backbone_components.find(0), "backbone is disconnected");
    }
    for (int level = 0, block_size = 2; block_size <= n; ++level, block_size *= 2)
        for (int block = 0; block < n / block_size; ++block)
            require(dyadic_bridges[{level, block}] == 1, "missing or repeated dyadic backbone bridge");
    if (cheap_backbone) require(cheap_chords == q, "wrong number of promoted chords");
    if (hierarchy) {
        const auto order = backbone_order(fixture, n);
        for (std::size_t i = 1; i < order.size(); ++i)
            require(actual_levels[order[i - 1]] <= actual_levels[order[i]], "hierarchy weight order is broken");
    }
    if (distance) {
        // Recover every edge's level from unshuffled endpoints. Metadata marks
        // chords as -1 and is deliberately insufficient for this check.
        std::vector<int> ranked_levels(m, -1);
        for (const auto& [u, v, weight, id] : graph) {
            (void)id;
            int width = 2, level = 0;
            while (original[u] / width != original[v] / width) { width *= 2; ++level; }
            ranked_levels[weight - 1] = level;
        }
        require(std::is_sorted(ranked_levels.begin(), ranked_levels.end()),
                "distance ranks do not globally order all edges by dyadic level");
    }

    const auto random_partner = benchmark_continuation::make_fixture(
        {path ? "random_path" : "random_tree", n, spec.density, 0}, seed);
    check_paired_topology(fixture, random_partner);
    if (path) check_paired_topology(fixture, benchmark_continuation::make_fixture(
        {"low_path", n, spec.density, 0}, seed));
    if (spec.intrusion_per_mille != 0) {
        const auto unperturbed = benchmark_continuation::make_fixture({spec.family, n, spec.density, 0}, seed);
        check_paired_topology(fixture, unperturbed);
        require(backbone_order(fixture, n) == backbone_order(unperturbed, n),
                "intrusion changed relative backbone weight order");
    }

    const auto oracle = kruskal(graph, n);
    benchmark_validation::certify_mst(graph, oracle, n);
    const auto expected_ids = edge_ids(oracle);
    if (cheap_backbone && q == 0) {
        // A separate certificate checks the intentionally planted MST rather
        // than assuming the reference algorithm returns the backbone.
        benchmark_validation::certify_mst(graph, backbone, n);
        require(expected_ids == edge_ids(backbone), "cheap-backbone fixture has a different MST");
    }
    if (distance) {
        const auto dyadic_oracle = dyadic_cut_mst(graph, original, n);
        benchmark_validation::certify_mst(graph, dyadic_oracle, n);
        require(expected_ids == edge_ids(dyadic_oracle),
                "MST differs from independent minimum-edge-per-dyadic-cut oracle");
    }
    for (unsigned sampling_seed : {0u, 1u, 7u}) {
        problem input(n, graph);
        require(kkt(input, sampling_seed) == expected_ids, "KKT differs from independently certified MST IDs");
    }
    const bool exact_halving = distance || (hierarchy && q == 0);
    const int rounds = check_contractions(graph, n, exact_halving);
    if (exact_halving) {
        int expected_rounds = 0;
        for (int remaining = n; remaining > 1; remaining /= 2) ++expected_rounds;
        require(rounds == expected_rounds, "hierarchical graph finished in an unexpected number of rounds");
    }
    int backbone_overlap = 0;
    for (int id : expected_ids) backbone_overlap += id < n - 1;
    return backbone_overlap;
}

} // namespace

int main() {
    try {
        int checked = 0;
        std::set<std::string> names;
        for (const char* family : {"hierarchical_path", "hierarchical_tree", "low_path", "random_path", "random_tree",
                                   "distance_path", "distance_tree"}) {
            for (int n : {32, 64, 128, 256}) for (int density : {1, 4}) {
                const bool structured = std::string(family).find("hierarchical_") == 0 ||
                                        std::string(family) == "low_path";
                const std::vector<int> intrusions = structured && density == 4
                    ? std::vector<int>{0, 125, 1000} : std::vector<int>{0};
                for (int intrusion : intrusions) {
                    const Spec spec{family, n, density, intrusion};
                    require(names.insert(benchmark_continuation::case_id(spec)).second, "duplicate case ID");
                    for (unsigned seed : {17u, 42u, 999u}) { check_fixture(spec, seed); ++checked; }
                }
            }
        }
        // Nearly complete fixtures exercise chord rejection sampling; a
        // rounded nonzero intrusion parameter exercises floor(n*p/1000).
        for (const Spec& spec : {Spec{"hierarchical_path", 32, 15, 1000},
                                 Spec{"hierarchical_tree", 32, 15, 0},
                                 Spec{"hierarchical_path", 32, 1, 31},
                                 Spec{"hierarchical_tree", 32, 1, 32},
                                 Spec{"low_path", 64, 4, 17}}) {
            check_fixture(spec, 42); ++checked;
        }
        // Check that the hierarchy-distance model does not simply plant the
        // original backbone as its MST. This is a selected dense-fixture
        // regression, not an assumed overlap fraction for arbitrary inputs.
        for (const char* family : {"distance_path", "distance_tree"}) {
            for (unsigned seed : {17u, 42u, 999u}) {
                const Spec spec{family, 64, 16, 0};
                const int overlap = check_fixture(spec, seed); ++checked;
                require(overlap < spec.n - 1, "dense distance fixture's MST never uses a chord");
                std::cout << benchmark_continuation::case_id(spec) << " graph_seed=" << seed
                          << " backbone_overlap=" << overlap << '/' << spec.n - 1 << '\n';
            }
        }
        for (const Spec& bad : {Spec{"unknown", 32, 1, 0},
                                Spec{"hierarchical_path", 16, 1, 0},
                                Spec{"hierarchical_tree", 48, 1, 0},
                                Spec{"hierarchical_path", 32, 0, 0},
                                Spec{"hierarchical_tree", 32, -1, 0},
                                Spec{"hierarchical_path", 32, 513, 0},
                                Spec{"hierarchical_path", 32, 16, 0},
                                Spec{"hierarchical_tree", 32, 4, -1},
                                Spec{"low_path", 32, 4, 1001},
                                Spec{"low_path", 32, 1, 1000},
                                Spec{"random_path", 32, 4, 1},
                                Spec{"random_tree", 32, 4, 1},
                                Spec{"distance_path", 32, 4, 1},
                                Spec{"distance_tree", 32, 4, 1},
                                Spec{"hierarchical_path", 1 << 22, 512, 0},
                                Spec{"hierarchical_path", 1 << 30, 4, 0}}) {
            bool rejected = false;
            try { (void)benchmark_continuation::edge_count(bad); }
            catch (const std::runtime_error&) { rejected = true; }
            require(rejected, "invalid fixture accepted by dimension validation");
        }
        std::cout << "Validated " << checked << " continuation fixtures, paired controls, independent contractions, "
                  << 3 * checked << " certified KKT outputs, and invalid dimensions.\n";
    } catch (const std::exception& error) {
        std::cerr << "continuation fixture test: " << error.what() << '\n';
        return 1;
    }
}
