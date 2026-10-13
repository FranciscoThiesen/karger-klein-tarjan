// Independent structure and correctness checks for the new crossover search.
// This executable is deliberately untimed and does not use assert as a gate.
#include "search_fixtures.hpp"
#include "mst_certificate.hpp"
#include "../boruvka/boruvka.hpp"
#include "../kkt/kkt.hpp"
#include "../kruskal/kruskal.hpp"
#include "../prim/prim.hpp"

#include <algorithm>
#include <cstdint>
#include <cstdlib>
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
using Graph = benchmark_fixtures::Graph;
using Ids = std::unordered_set<int>;
using Spec = benchmark_continuation::Spec;

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

// A separate, intentionally simple DSU: no production union-find or successor
// walks, and no shared certificate implementation.
class Components {
    std::vector<int> parent_;
public:
    explicit Components(int n) : parent_(n) { std::iota(parent_.begin(), parent_.end(), 0); }
    int find(int vertex) const {
        while (parent_[vertex] != vertex) vertex = parent_[vertex];
        return vertex;
    }
    bool join(int a, int b) {
        a = find(a); b = find(b);
        if (a == b) return false;
        parent_[std::max(a, b)] = std::min(a, b);
        return true;
    }
};

Ids edge_ids(const Graph& graph) {
    Ids result;
    for (const auto& edge : graph)
        require(result.insert(std::get<3>(edge)).second, "duplicate result edge ID");
    return result;
}

Graph select_ids(const Graph& graph, const Ids& ids) {
    Graph result;
    for (const auto& edge : graph) if (ids.count(std::get<3>(edge))) result.push_back(edge);
    require(result.size() == ids.size(), "result contains an unknown original ID");
    return result;
}

struct Reduction {
    std::set<int> selected;
    int vertices;
    Graph quotient;
};

// O(nm) vertex-by-edge scanning and an ordered pair map are independent of
// production's edge scan, successor walks and stamped endpoint buckets.
Reduction independent_reduction(const problem& input) {
    Components components(input.num_vertices);
    std::set<int> selected;
    for (int vertex = 0; vertex < input.num_vertices; ++vertex) {
        const Edge* minimum = nullptr;
        for (const auto& edge : input.graph_edges)
            if ((edge.from == vertex || edge.to == vertex) &&
                (!minimum || edge.cost < minimum->cost)) minimum = &edge;
        require(minimum != nullptr, "connected quotient contains an isolate");
        selected.insert(minimum->id);
        components.join(minimum->from, minimum->to);
    }
    std::map<int, int> labels;
    for (int vertex = 0; vertex < input.num_vertices; ++vertex) {
        const int representative = components.find(vertex);
        if (!labels.count(representative)) labels[representative] = static_cast<int>(labels.size());
    }
    if (labels.size() == 1) return {std::move(selected), 0, {}};
    std::map<std::pair<int, int>, std::pair<int, int>> minimum_by_pair;
    for (const auto& edge : input.graph_edges) {
        int a = labels.at(components.find(edge.from));
        int b = labels.at(components.find(edge.to));
        if (a == b) continue;
        if (a > b) std::swap(a, b);
        const auto key = std::make_pair(a, b);
        const auto found = minimum_by_pair.find(key);
        if (found == minimum_by_pair.end() || edge.cost < found->second.first)
            minimum_by_pair[key] = {edge.cost, edge.id};
    }
    Graph quotient;
    for (const auto& [ends, minimum] : minimum_by_pair)
        quotient.emplace_back(ends.first, ends.second, minimum.first, minimum.second);
    return {std::move(selected), static_cast<int>(labels.size()), std::move(quotient)};
}

struct Stage {
    // Original unpermuted vertex -> representative original unpermuted vertex.
    std::vector<int> partition;
    int quotient_vertices;
};

struct Contractions {
    Ids selected;
    std::vector<Stage> stages;
};

Contractions check_contractions(const Graph& graph, int n, const std::vector<int>& original_to_label) {
    problem current(n, graph);
    Components original_components(n);
    std::vector<const Graph::value_type*> by_id(graph.size(), nullptr);
    for (const auto& edge : graph) by_id.at(std::get<3>(edge)) = &edge;
    Contractions result;
    while (!current.graph_edges.empty()) {
        const auto input_before = current.graph_edges;
        const auto expected = independent_reduction(current);
        auto actual = boruvka_step(current);
        require(current.graph_edges == input_before, "contraction mutated its input");
        const std::set<int> selected(actual.first.begin(), actual.first.end());
        require(selected.size() == actual.first.size() && selected == expected.selected,
                "selected IDs disagree with independent per-vertex minimum oracle");
        Graph quotient;
        for (const auto& edge : actual.second.graph_edges)
            quotient.emplace_back(std::min(edge.from, edge.to), std::max(edge.from, edge.to),
                                  edge.cost, edge.id);
        std::sort(quotient.begin(), quotient.end());
        require(actual.second.num_vertices == expected.vertices && quotient == expected.quotient,
                "quotient partition or minimum parallel representative is wrong");
        for (int id : actual.first) {
            require(result.selected.insert(id).second, "ID selected in multiple contraction rounds");
            const auto& [u, v, unused, original_id] = *by_id.at(id);
            (void)unused; (void)original_id;
            require(original_components.join(u, v), "selected original edges contain a cycle");
        }
        std::vector<int> partition(n);
        std::map<int, int> first_original;
        for (int vertex = 0; vertex < n; ++vertex) {
            const int root = original_components.find(original_to_label.at(vertex));
            if (!first_original.count(root)) first_original[root] = vertex;
            partition[vertex] = first_original.at(root);
        }
        result.stages.push_back({std::move(partition), actual.second.num_vertices});
        require(result.stages.size() <= 30, "contraction did not finish");
        current = std::move(actual.second);
    }
    return result;
}

int dyadic_level(int a, int b) {
    require(a != b, "a core edge is a loop");
    int level = 0;
    for (int difference = a ^ b; difference > 1; difference /= 2) ++level;
    return level;
}

void check_pairing(const Graph& first, const Graph& second) {
    require(first.size() == second.size(), "paired graph sizes differ");
    for (std::size_t i = 0; i < first.size(); ++i)
        require(std::get<0>(first[i]) == std::get<0>(second[i]) &&
                std::get<1>(first[i]) == std::get<1>(second[i]) &&
                std::get<3>(first[i]) == std::get<3>(second[i]),
                "paired weight control changes endpoints, IDs or input order");
}

// Verify the lifted topology and its weight mechanism from original endpoints
// and actual expanded weights. core_graph is checked against those facts, but
// is not used as an oracle for the dyadic ordering we want to establish.
void check_structure(const Spec& spec, const benchmark_search::Fixture& fixture,
                     const std::vector<int>& original) {
    const int n = spec.n, b = fixture.bundle_size;
    require((b == 2 || b == 4) && n % b == 0, "unexpected clone block size");
    const int q = n / b;
    const int local_count = q * (b - 1);
    const int core_count = (n * spec.density - local_count) / (b * b);
    const bool random = spec.family.find("_random") != std::string::npos;
    const bool distance = spec.family.find("_distance") != std::string::npos;
    require(fixture.core_graph.size() == static_cast<std::size_t>(core_count),
            "metadata core has the wrong edge count");

    std::map<std::pair<int, int>, std::vector<int>> bundles;
    std::map<std::pair<int, int>, std::set<std::pair<int, int>>> lifted_pairs;
    std::vector<int> local_degree(n), local_weights;
    for (const auto& [u, v, weight, id] : fixture.graph) {
        (void)id;
        int a = original.at(u), c = original.at(v);
        if (a > c) std::swap(a, c);
        if (a / b == c / b) {
            require(a % b == 0 && c % b != 0, "local clone edges do not form the specified star");
            ++local_degree[a]; ++local_degree[c];
            local_weights.push_back(weight);
        } else {
            const auto key = std::make_pair(a / b, c / b);
            bundles[key].push_back(weight);
            require(lifted_pairs[key].insert({a % b, c % b}).second,
                    "a core bundle repeats a lifted endpoint pair");
        }
    }
    require(local_weights.size() == static_cast<std::size_t>(local_count), "wrong local star edge count");
    for (int vertex = 0; vertex < n; ++vertex)
        require(local_degree[vertex] == (vertex % b == 0 ? b - 1 : 1),
                "local star center or leaf degree is wrong");
    require(bundles.size() == static_cast<std::size_t>(core_count), "wrong number of core bundles");
    std::map<std::pair<int, int>, std::pair<int, int>> core_metadata;
    std::vector<bool> core_ids(core_count), core_ranks(core_count);
    for (const auto& [from, to, weight, id] : fixture.core_graph) {
        require(from >= 0 && from < q && to >= 0 && to < q && from != to,
                "invalid original core endpoint");
        require(id >= 0 && id < core_count && !core_ids[id], "metadata core IDs are not dense and unique");
        require(weight >= 1 && weight <= core_count && !core_ranks[weight - 1],
                "metadata core weights are not a rank permutation");
        core_ids[id] = true; core_ranks[weight - 1] = true;
        const auto key = std::minmax(from, to);
        require(core_metadata.emplace(key, std::make_pair(weight, id)).second, "metadata repeats a core pair");
        if (id < q - 1)
            require(key.first == id && key.second == id + 1, "metadata core path backbone differs");
    }
    std::vector<std::pair<int, std::pair<int, int>>> bundle_order;
    for (auto& [ends, weights] : bundles) {
        require(weights.size() == static_cast<std::size_t>(b * b) &&
                lifted_pairs.at(ends).size() == static_cast<std::size_t>(b * b),
                "core edge did not expand into a complete bipartite bundle");
        require(core_metadata.count(ends) == 1, "expanded bundle is absent from metadata core");
        std::sort(weights.begin(), weights.end());
        if (!random) {
            require(weights.front() > local_count, "core bundle competes with cheap local star edges");
            for (int j = 1; j < b * b; ++j)
                require(weights[j] == weights[0] + j, "bundle weights are not one contiguous rank interval");
            require((weights[0] - local_count - 1) % (b * b) == 0,
                    "bundle rank interval is not aligned");
            const int expanded_priority = (weights[0] - local_count - 1) / (b * b) + 1;
            require(core_metadata.at(ends).first == expanded_priority,
                    "metadata core priority differs from its expanded rank interval");
            bundle_order.push_back({weights[0], ends});
        }
    }
    if (!random) {
        std::sort(local_weights.begin(), local_weights.end());
        for (int i = 0; i < local_count; ++i)
            require(local_weights[i] == i + 1, "local stars are not the entire cheap-rank prefix");
        std::sort(bundle_order.begin(), bundle_order.end());
        int last_level = -1;
        for (std::size_t index = 0; index < bundle_order.size(); ++index) {
            const auto [a, c] = bundle_order[index].second;
            if (distance || index < static_cast<std::size_t>(q - 1)) {
                if (!distance) require(c == a + 1, "hierarchy's cheap core prefix is not its path backbone");
                const int level = dyadic_level(a, c);
                require(level >= last_level, "core priorities do not follow independent dyadic endpoint levels");
                last_level = level;
            }
        }
    }
}

int check_fixture(const Spec& spec, unsigned seed) {
    const auto fixture = benchmark_search::make_fixture(spec, seed);
    const auto replay = benchmark_search::make_fixture(spec, seed);
    const auto& graph = fixture.graph;
    const int n = spec.n, m = n * spec.density;
    require(benchmark_search::edge_count(spec) == m && graph.size() == static_cast<std::size_t>(m),
            "fixture edge count is not n*density");
    require(graph == replay.graph && fixture.original_to_label == replay.original_to_label &&
            fixture.core_graph == replay.core_graph && fixture.bundle_size == replay.bundle_size,
            "fixture replay is not deterministic");
    require(fixture.original_to_label.size() == static_cast<std::size_t>(n), "missing vertex-label permutation");
    std::vector<int> original(n, -1);
    for (int vertex = 0; vertex < n; ++vertex) {
        const int label = fixture.original_to_label[vertex];
        require(label >= 0 && label < n && original[label] == -1, "labels are not a permutation");
        original[label] = vertex;
    }
    std::vector<bool> ids(m), ranks(m);
    std::set<std::pair<int, int>> pairs;
    Components connected(n);
    for (const auto& [u, v, weight, id] : graph) {
        require(u >= 0 && u < n && v >= 0 && v < n && u != v, "invalid graph endpoint");
        require(id >= 0 && id < m && !ids[id], "graph IDs are not dense and unique");
        require(weight >= 1 && weight <= m && !ranks[weight - 1], "graph weights are not ranks 1..m");
        ids[id] = true; ranks[weight - 1] = true;
        require(pairs.insert(std::minmax(u, v)).second, "parallel edge in lifted graph");
        connected.join(u, v);
    }
    for (int vertex = 0; vertex < n; ++vertex)
        require(connected.find(vertex) == connected.find(0), "lifted graph is disconnected");
    check_structure(spec, fixture, original);

    const bool random = spec.family.find("_random") != std::string::npos;
    for (const char* weight_model : {"hierarchy", "distance", "random"}) {
        const std::string twin_family = "lifted_" + std::string(weight_model) +
                                        std::to_string(fixture.bundle_size);
        const auto twin = benchmark_search::make_fixture({twin_family, n, spec.density, 0}, seed);
        require(fixture.original_to_label == twin.original_to_label && fixture.bundle_size == twin.bundle_size,
                "paired control changes labels or bundle size");
        check_pairing(graph, twin.graph);
        check_pairing(fixture.core_graph, twin.core_graph);
    }

    const auto reference = kruskal(graph, n);
    benchmark_validation::certify_mst(graph, reference, n);
    const Ids expected = edge_ids(reference);
    if (spec.family == "lifted_distance4" && n == 64 && spec.density == 30 && seed == 42) {
        int core_chords = 0;
        for (const auto& [u, v, weight, id] : reference) {
            (void)weight; (void)id;
            const int a = original[u] / fixture.bundle_size;
            const int b = original[v] / fixture.bundle_size;
            core_chords += std::abs(a - b) > 1;
        }
        require(core_chords > 0, "dense distance regression never uses a non-backbone core edge");
        std::cout << "Dense distance regression selects " << core_chords
                  << " non-backbone core bundles in its certified MST.\n";
    }
    for (const auto& candidate : {prim(graph, n), boruvka(graph, n)}) {
        benchmark_validation::certify_mst(graph, candidate, n);
        require(edge_ids(candidate) == expected, "classical solver disagrees with unique certified MST");
    }
    for (unsigned sampling_seed : {0u, 1u, 101u}) {
        problem input(n, graph);
        const auto actual = kkt(input, sampling_seed);
        benchmark_validation::certify_mst(graph, select_ids(graph, actual), n);
        require(actual == expected, "KKT differs from unique certified MST");
    }
    const auto contractions = check_contractions(graph, n, fixture.original_to_label);
    benchmark_validation::certify_mst(graph, select_ids(graph, contractions.selected), n);
    require(contractions.selected == expected, "compacting Boruvka differs from unique certified MST");
    if (!random) {
        int width = fixture.bundle_size;
        for (const auto& stage : contractions.stages) {
            for (int vertex = 0; vertex < n; ++vertex)
                require(stage.partition[vertex] == vertex / width * width,
                        "known clone/dyadic block partition differs from original-ID ledger");
            require(stage.quotient_vertices == (width == n ? 0 : n / width),
                    "known clone/dyadic quotient count is wrong");
            width *= 2;
        }
        require(width == 2 * n, "known hierarchy stopped at the wrong stage");
    }
    return static_cast<int>(contractions.stages.size());
}

} // namespace

int main() {
    try {
        int fixtures = 0, stages = 0, invalid = 0;
        for (const char* family : benchmark_search::families) {
            const int b = std::string(family).find('2') == std::string::npos ? 4 : 2;
            const std::vector<int> densities = b == 2 ? std::vector<int>{3, 4, 8} : std::vector<int>{5, 8, 16};
            for (int n : {64, 128, 256}) for (int density : densities) for (unsigned seed : {17u, 42u, 999u}) {
                const Spec spec{family, n, density, 0};
                try { stages += check_fixture(spec, seed); }
                catch (const std::exception& error) {
                    throw std::runtime_error(benchmark_continuation::case_id(spec) + " seed=" +
                                             std::to_string(seed) + ": " + error.what());
                }
                ++fixtures;
            }
        }
        // Near-complete cores exercise distinct-pair rejection, while the
        // smallest accepted block-size-2 case exercises the lower n boundary.
        for (const Spec& spec : {Spec{"lifted_hierarchy2", 32, 15, 0},
                                 Spec{"lifted_distance2", 32, 3, 0},
                                 Spec{"lifted_hierarchy4", 64, 30, 0},
                                 Spec{"lifted_distance4", 64, 30, 0},
                                 Spec{"lifted_random4", 64, 30, 0}}) {
            stages += check_fixture(spec, 42); ++fixtures;
        }
        // Accepted dimension extremes are checked without allocating the
        // largest fixture; actual small instances above exercise generation.
        for (const char* family : benchmark_search::families)
            require(benchmark_search::edge_count({family, 1 << 22, 32, 0}) == 134217728,
                    "exact maximum supported edge budget was rejected");
        for (const Spec& spec : {Spec{"unknown", 64, 8, 0},
                                 Spec{"lifted_random8", 64, 8, 0},
                                 Spec{"lifted_hierarchy2", 0, 8, 0},
                                 Spec{"lifted_hierarchy2", -32, 8, 0},
                                 Spec{"lifted_hierarchy2", 16, 8, 0},
                                 Spec{"lifted_hierarchy2", 96, 8, 0},
                                 Spec{"lifted_hierarchy4", 32, 8, 0},
                                 Spec{"lifted_hierarchy2", 64, 0, 0},
                                 Spec{"lifted_hierarchy2", 64, -1, 0},
                                 Spec{"lifted_hierarchy2", 64, 513, 0},
                                 Spec{"lifted_hierarchy2", 64, 2, 0},
                                 Spec{"lifted_hierarchy4", 64, 4, 0},
                                 Spec{"lifted_hierarchy2", 32, 16, 0},
                                 Spec{"lifted_hierarchy4", 64, 31, 0},
                                 Spec{"lifted_hierarchy2", 64, 8, -1},
                                 Spec{"lifted_distance2", 64, 8, 1},
                                 Spec{"lifted_random4", 64, 8, 1001},
                                 Spec{"lifted_hierarchy2", 1 << 22, 33, 0},
                                 Spec{"lifted_hierarchy4", 1 << 23, 512, 0},
                                 Spec{"lifted_hierarchy4", 1 << 30, 8, 0}}) {
            bool rejected = false;
            try { (void)benchmark_search::edge_count(spec); }
            catch (const std::runtime_error&) { rejected = true; }
            require(rejected, "invalid lifted dimensions accepted: " + benchmark_continuation::case_id(spec));
            ++invalid;
        }
        std::cout << "Validated " << fixtures << " lifted fixtures, " << stages
                  << " independently reconstructed contraction stages, " << fixtures * 7
                  << " certified solver outputs across all five algorithms (three KKT seeds), "
                  << "paired topology controls, clone/dyadic partitions, and " << invalid
                  << " invalid dimension cases.\n";
    } catch (const std::exception& error) {
        std::cerr << "search fixture test: " << error.what() << '\n';
        return 1;
    }
}
