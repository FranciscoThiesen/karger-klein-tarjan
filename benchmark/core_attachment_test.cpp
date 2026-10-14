// Independent fixture/solver gates; no timers and no assert-based checks.
#include "core_attachment_fixtures.hpp"
#include "benchmark/mst_certificate.hpp"
#include "boruvka/boruvka.hpp"
#include "kkt/kkt.hpp"
#include "kruskal/kruskal.hpp"
#include "prim/prim.hpp"
#ifdef KKT_ENABLE_WORK_STATS
#include "benchmark/work_metrics.hpp"
#endif

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
using Graph = benchmark_fixtures::Graph;
using Spec = benchmark_continuation::Spec;
using Fixture = benchmark_attachments::Fixture;
using Ids = std::unordered_set<int>;

void require(bool value, const std::string& message) {
    if (!value) throw std::runtime_error(message);
}

struct Counts {
    int fixtures = 0, stages = 0, slow_minimum_crosschecks = 0;
    int certified_outputs = 0, endpoint_trace_pairs = 0, counter_pairs = 0;
    int dense_distance_chords = 0;
} counts;

// Independent union by size and path compression. Canonical quotient labels are
// assigned separately by scanning vertices, never inferred from DSU roots.
class Components {
    std::vector<int> parents, sizes;
public:
    explicit Components(int n) : parents(n), sizes(n, 1) {
        std::iota(parents.begin(), parents.end(), 0);
    }
    int find(int v) {
        int root = v;
        while (parents[root] != root) root = parents[root];
        while (parents[v] != v) {
            const int next = parents[v];
            parents[v] = root;
            v = next;
        }
        return root;
    }
    bool join(int a, int b) {
        a = find(a); b = find(b);
        if (a == b) return false;
        if (sizes[a] < sizes[b]) std::swap(a, b);
        parents[b] = a;
        sizes[a] += sizes[b];
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
    Graph selected;
    for (const auto& edge : graph)
        if (ids.count(std::get<3>(edge))) selected.push_back(edge);
    require(selected.size() == ids.size(), "unknown result ID");
    return selected;
}

std::vector<int> inverse_labels(const Fixture& fixture, int n) {
    require(fixture.original_to_label.size() == static_cast<std::size_t>(n), "missing labels");
    std::vector<int> original(n, -1);
    for (int v = 0; v < n; ++v) {
        const int label = fixture.original_to_label[v];
        require(label >= 0 && label < n && original[label] == -1, "labels are not a permutation");
        original[label] = v;
    }
    return original;
}

std::set<int> sorted_incidence_minima(const problem& input) {
    // Emitted incidences sorted by vertex, then cost and ID; unlike production,
    // this oracle never maintains/update-tests a minimum array in an edge scan.
    std::vector<std::tuple<int, int, int>> incidences;
    incidences.reserve(2 * input.graph_edges.size());
    for (const auto& edge : input.graph_edges) {
        incidences.emplace_back(edge.from, edge.cost, edge.id);
        incidences.emplace_back(edge.to, edge.cost, edge.id);
    }
    std::sort(incidences.begin(), incidences.end());
    std::set<int> selected;
    int last_vertex = -1, vertices = 0;
    for (const auto& [vertex, unused_cost, id] : incidences) {
        (void)unused_cost;
        if (vertex != last_vertex) {
            require(vertex == vertices, "connected quotient has an isolate or invalid vertex");
            selected.insert(id);
            last_vertex = vertex;
            ++vertices;
        }
    }
    require(vertices == input.num_vertices, "minimum oracle did not cover every vertex");
    return selected;
}

std::set<int> slow_minima(const problem& input) {
    std::set<int> selected;
    for (int vertex = 0; vertex < input.num_vertices; ++vertex) {
        const Edge* minimum = nullptr;
        for (const auto& edge : input.graph_edges)
            if ((edge.from == vertex || edge.to == vertex) &&
                (!minimum || edge.cost < minimum->cost)) minimum = &edge;
        require(minimum != nullptr, "slow minimum oracle found an isolate");
        selected.insert(minimum->id);
    }
    return selected;
}

struct Reduction {
    std::set<int> selected;
    int vertices;
    Graph quotient;
};

Reduction independent_reduction(const problem& input) {
    auto selected = sorted_incidence_minima(input);
    if (static_cast<std::uint64_t>(input.num_vertices) * input.graph_edges.size() <= 1000000) {
        require(selected == slow_minima(input), "sorted and vertex-by-edge minima disagree");
        ++counts.slow_minimum_crosschecks;
    }
    Components components(input.num_vertices);
    for (const auto& edge : input.graph_edges)
        if (selected.count(edge.id)) components.join(edge.from, edge.to);
    std::map<int, int> labels;
    for (int vertex = 0; vertex < input.num_vertices; ++vertex) {
        const int root = components.find(vertex);
        if (!labels.count(root)) labels[root] = static_cast<int>(labels.size());
    }
    if (labels.size() == 1) return {std::move(selected), 0, {}};
    std::map<std::pair<int, int>, std::pair<int, int>> cheapest;
    for (const auto& edge : input.graph_edges) {
        int a = labels.at(components.find(edge.from));
        int b = labels.at(components.find(edge.to));
        if (a == b) continue;
        if (a > b) std::swap(a, b);
        const auto key = std::make_pair(a, b);
        const auto found = cheapest.find(key);
        if (found == cheapest.end() || edge.cost < found->second.first)
            cheapest[key] = {edge.cost, edge.id};
    }
    Graph quotient;
    for (const auto& [ends, value] : cheapest)
        quotient.emplace_back(ends.first, ends.second, value.first, value.second);
    return {std::move(selected), static_cast<int>(labels.size()), std::move(quotient)};
}

struct Stage {
    std::vector<int> selected;       // Exact production order, for endpoint twins.
    std::vector<Edge> quotient;     // Exact physical vector, not sorted.
    int quotient_vertices;
    std::vector<int> partition;     // Original vertex -> smallest original member.
};

struct Contractions {
    Ids selected;
    std::vector<Stage> stages;
};

Contractions check_contractions(const Fixture& fixture, int n) {
    problem current(n, fixture.graph);
    Components originals(n);
    std::vector<const Graph::value_type*> by_id(fixture.graph.size(), nullptr);
    for (const auto& edge : fixture.graph) by_id.at(std::get<3>(edge)) = &edge;
    Contractions result;
    while (!current.graph_edges.empty()) {
        const auto before = current.graph_edges;
        const auto expected = independent_reduction(current);
        auto actual = boruvka_step(current);
        require(current.graph_edges == before, "production contraction mutated its input");
        const std::set<int> selected(actual.first.begin(), actual.first.end());
        require(selected.size() == actual.first.size() && selected == expected.selected,
                "contraction selected IDs disagree with independent minimum oracle");
        Graph quotient;
        for (const auto& edge : actual.second.graph_edges)
            quotient.emplace_back(std::min(edge.from, edge.to), std::max(edge.from, edge.to), edge.cost, edge.id);
        std::sort(quotient.begin(), quotient.end());
        require(actual.second.num_vertices == expected.vertices && quotient == expected.quotient,
                "complete quotient/minimum parallel representatives differ from independent map");
        for (int id : actual.first) {
            require(result.selected.insert(id).second, "ID selected in multiple rounds");
            const auto& [a, b, unused, original_id] = *by_id.at(id);
            (void)unused; (void)original_id;
            require(originals.join(a, b), "selected original edges form a cycle");
        }
        std::map<int, int> first;
        std::vector<int> partition(n);
        for (int vertex = 0; vertex < n; ++vertex) {
            const int root = originals.find(fixture.original_to_label[vertex]);
            if (!first.count(root)) first[root] = vertex;
            partition[vertex] = first.at(root);
        }
        result.stages.push_back({std::move(actual.first), actual.second.graph_edges,
                                 actual.second.num_vertices, std::move(partition)});
        require(result.stages.size() <= 30, "contraction failed to terminate");
        current = std::move(actual.second);
        ++counts.stages;
    }
    require(result.selected.size() == static_cast<std::size_t>(n-1), "incomplete contraction MST");
    return result;
}

int level(int a, int b) {
    require(a != b, "loop when computing endpoint-derived dyadic level");
    int result = 0;
    for (int different = a ^ b; different > 1; different >>= 1) ++result;
    return result;
}

void same_topology(const Graph& a, const Graph& b) {
    require(a.size() == b.size(), "paired sizes differ");
    for (std::size_t i = 0; i < a.size(); ++i)
        require(std::get<0>(a[i]) == std::get<0>(b[i]) &&
                std::get<1>(a[i]) == std::get<1>(b[i]) &&
                std::get<3>(a[i]) == std::get<3>(b[i]), "paired endpoints/IDs/physical order differ");
}

void check_structure(const Spec& spec, const Fixture& fixture, const std::vector<int>& original) {
    const int n = spec.n, b = fixture.block_size;
    require(b == (spec.family.back() == '4' ? 4 : 16), "wrong block size metadata");
    const int q = n/b, local = n-q, external = n*spec.density-local;
    const bool random = spec.family.find("_random") != std::string::npos;
    const bool shuffled = spec.family.find("_shuffled") != std::string::npos;
    const bool distance = spec.family.find("_distance") != std::string::npos;
    const bool leaf = spec.family.find("leaf_") == 0;
    require(fixture.core_graph.size() == static_cast<std::size_t>(external), "wrong core size");
    std::vector<int> local_degree(n), total_degree(n), local_weights;
    std::map<std::pair<int, int>, std::pair<int, int>> external_edges;
    std::vector<std::pair<int, std::pair<int, int>>> external_order;
    for (const auto& [u, v, weight, id] : fixture.graph) {
        int a = original.at(u), c = original.at(v);
        if (a > c) std::swap(a, c);
        ++total_degree[a]; ++total_degree[c];
        if (a/b == c/b) {
            require(a%b == 0 && c%b != 0 && id == (a/b)*(b-1)+c%b-1, "wrong local star/ID");
            ++local_degree[a]; ++local_degree[c]; local_weights.push_back(weight);
        } else {
            require(id >= local, "external edge has a local ID");
            if (leaf) require(a%b == 0 && c%b == 0, "leaf model has a non-center external endpoint");
            const auto key = std::make_pair(a/b, c/b);
            require(external_edges.emplace(key, std::make_pair(weight, id-local)).second,
                    "more than one external edge per core pair");
            const int core_id = id-local;
            if (core_id < q-1)
                require(key.first == core_id && key.second == core_id+1, "actual core path IDs differ");
            external_order.push_back({weight, key});
        }
    }
    require(local_weights.size() == static_cast<std::size_t>(local) &&
            external_edges.size() == static_cast<std::size_t>(external), "wrong attachment edge counts");
    for (int vertex = 0; vertex < n; ++vertex) {
        require(local_degree[vertex] == (vertex%b == 0 ? b-1 : 1), "wrong local degree");
        if (leaf && vertex%b != 0) require(total_degree[vertex] == 1, "leaf model peripheral vertex is not a leaf");
    }
    std::vector<bool> core_ids(external), core_weights(external);
    std::set<std::pair<int, int>> core_pairs;
    for (const auto& [u, v, weight, id] : fixture.core_graph) {
        require(u >= 0 && u < q && v >= 0 && v < q && u != v, "invalid core endpoint");
        require(id >= 0 && id < external && !core_ids[id], "core IDs not unique/dense");
        require(weight > 0 && weight <= external && !core_weights[weight-1], "core weights not unique ranks");
        core_ids[id] = true; core_weights[weight-1] = true;
        const auto ends = std::minmax(u, v);
        require(core_pairs.insert(ends).second, "duplicate metadata core pair");
        const auto actual = external_edges.find(ends);
        require(actual != external_edges.end() && actual->second.second == id, "metadata core differs from actual edges");
        if (id < q-1) require(ends.first == id && ends.second == id+1, "core metadata path ID mismatch");
        if (!random) require(actual->second.first == local+weight, "actual/core priority mismatch");
    }
    if (!random) {
        std::sort(local_weights.begin(), local_weights.end());
        for (int i = 0; i < local; ++i) require(local_weights[i] == i+1, "local ranks are not the exact cheap prefix");
        std::sort(external_order.begin(), external_order.end());
        int previous = -1;
        for (std::size_t i = 0; i < external_order.size(); ++i) {
            require(external_order[i].first == local+static_cast<int>(i)+1, "external ranks not an exact suffix");
            const auto [a, c] = external_order[i].second;
            if (!shuffled && (distance || i < static_cast<std::size_t>(q-1))) {
                if (!distance) require(c == a+1, "hierarchy cheap prefix includes a core chord");
                const int current = level(a, c);
                require(current >= previous, "actual endpoint-derived dyadic tiers are out of order");
                previous = current;
            }
        }
    }
}

Ids independent_structured_mst(const Spec& spec, const Fixture& fixture, const std::vector<int>& original) {
    const int b = fixture.block_size, q = spec.n/b, local = spec.n-q;
    Ids result;
    const bool distance = spec.family.find("_distance") != std::string::npos;
    std::map<std::pair<int, int>, std::pair<int, int>> cuts;
    for (const auto& [u, v, weight, id] : fixture.graph) {
        const int a = original[u]/b, c = original[v]/b;
        if (a == c) {
            result.insert(id);
        } else if (!distance) {
            if (id < local+q-1) result.insert(id);
        } else {
            const int tier = level(a, c), width = 1 << (tier+1);
            const auto key = std::make_pair(tier, std::min(a, c)/width*width);
            const auto found = cuts.find(key);
            if (found == cuts.end() || weight < found->second.first) cuts[key] = {weight, id};
        }
    }
    if (distance) {
        require(cuts.size() == static_cast<std::size_t>(q-1), "dyadic cut oracle misses an internal core node");
        for (const auto& [unused, minimum] : cuts) {
            (void)unused;
            require(result.insert(minimum.second).second, "one edge represents multiple dyadic cut minima");
        }
    }
    require(result.size() == static_cast<std::size_t>(spec.n-1), "structured independent MST has wrong size");
    return result;
}

void check_cheap_star_stages(const Spec& spec, const Fixture& fixture, const Contractions& contractions) {
    int width = fixture.block_size;
    const int local = spec.n-spec.n/width, external = spec.n*spec.density-local;
    const auto& first = contractions.stages.front();
    require(first.quotient_vertices == spec.n/width && first.quotient.size() == static_cast<std::size_t>(external),
            "first structured quotient does not preserve all external edges");
    require(first.selected.size() == static_cast<std::size_t>(local), "first round selected a nonlocal edge");
    std::set<int> first_ids(first.selected.begin(), first.selected.end());
    for (int id = 0; id < local; ++id) require(first_ids.count(id) == 1, "first round missed a cheap local edge");
    // Core-shuffled preserves the first local collapse but has no guaranteed
    // dyadic component partition in later rounds.
    if (spec.family.find("_shuffled") != std::string::npos) return;
    for (const auto& stage : contractions.stages) {
        require(width <= spec.n, "extra structured contraction round");
        for (int vertex = 0; vertex < spec.n; ++vertex)
            require(stage.partition[vertex] == vertex/width*width, "original-ID ledger is not the expected dyadic block");
        require(stage.quotient_vertices == (width == spec.n ? 0 : spec.n/width), "wrong structured quotient count");
        width *= 2;
    }
    require(width == 2*spec.n, "structured contraction stopped before the final block");
}

#ifdef KKT_ENABLE_WORK_STATS
Ids compactor_for_counters(problem& input) {
    std::vector<int> ids;
    while (!input.graph_edges.empty()) {
        auto [selected, reduced] = boruvka_step(input);
        ids.insert(ids.end(), selected.begin(), selected.end());
        input = std::move(reduced);
    }
    Ids result;
    result.reserve(ids.size());
    result.insert(ids.begin(), ids.end());
    KKT_WORK_ADD(hash_insert_items, ids.size());
    return result;
}

void equal_counters(const Fixture& first, const Fixture& second, int n, const Ids& expected) {
    for (unsigned seed : {0u, 1u, 101u}) {
        for (int algorithm = 0; algorithm < 2; ++algorithm) {
            if (algorithm == 1 && seed != 0) continue;
            kkt_work::WorkStats stats[2];
            for (int i = 0; i < 2; ++i) {
                Ids actual;
                {
                    kkt_work::ScopedWorkStats scope(stats[i]);
                    problem input(n, (i == 0 ? first : second).graph);
                    actual = algorithm == 0 ? kkt(input, seed) : compactor_for_counters(input);
                }
                require(actual == expected, "instrumented endpoint twin output mismatch");
            }
            for (const auto& field : benchmark_work::fields)
                require(stats[0].*field.member == stats[1].*field.member,
                        std::string("endpoint twins differ in counter: ")+field.name);
            ++counts.counter_pairs;
        }
    }
}
#endif

void check_fixture(const Spec& spec, unsigned seed) {
    const auto fixture = benchmark_attachments::make_fixture(spec, seed);
    const auto replay = benchmark_attachments::make_fixture(spec, seed);
    const auto& graph = fixture.graph;
    const int n = spec.n, m = n*spec.density, b = fixture.block_size;
    require(benchmark_attachments::edge_count(spec) == m && graph.size() == static_cast<std::size_t>(m), "wrong edge budget");
    require(graph == replay.graph && fixture.original_to_label == replay.original_to_label &&
            fixture.core_graph == replay.core_graph && b == replay.block_size, "determinism failure");
    const auto original = inverse_labels(fixture, n);
    std::vector<bool> ids(m), ranks(m);
    std::set<std::pair<int, int>> pairs;
    Components connected(n);
    for (const auto& [u, v, weight, id] : graph) {
        require(u >= 0 && u < n && v >= 0 && v < n && u != v, "invalid expanded endpoint");
        require(id >= 0 && id < m && !ids[id], "expanded IDs not unique/dense");
        require(weight > 0 && weight <= m && !ranks[weight-1], "expanded weights not unique ranks");
        ids[id] = true; ranks[weight-1] = true;
        require(pairs.insert(std::minmax(u, v)).second, "parallel expanded edge");
        connected.join(u, v);
    }
    for (int v = 0; v < n; ++v) require(connected.find(v) == connected.find(0), "disconnected expanded graph");
    check_structure(spec, fixture, original);
    const bool random = spec.family.find("_random") != std::string::npos;
    const bool shuffled = spec.family.find("_shuffled") != std::string::npos;
    const bool leaf = spec.family.find("leaf_") == 0;
    const std::string endpoint = leaf ? "leaf_" : "community_";
    for (const char* mode : {"hierarchy", "distance", "shuffled", "random"}) {
        const auto twin = benchmark_attachments::make_fixture({endpoint+mode+std::to_string(b), n, spec.density, 0}, seed);
        require(fixture.original_to_label == twin.original_to_label && b == twin.block_size, "paired labels/block size differ");
        same_topology(graph, twin.graph);
        same_topology(fixture.core_graph, twin.core_graph);
    }
    const std::string other_family = (leaf ? "community_" : "leaf_")+spec.family.substr(endpoint.size());
    const auto twin = benchmark_attachments::make_fixture({other_family, n, spec.density, 0}, seed);
    require(fixture.original_to_label == twin.original_to_label && fixture.core_graph == twin.core_graph,
            "endpoint ablation changes labels or core metadata");
    for (std::size_t i = 0; i < graph.size(); ++i) {
        require(std::get<2>(graph[i]) == std::get<2>(twin.graph[i]) && std::get<3>(graph[i]) == std::get<3>(twin.graph[i]),
                "endpoint ablation changes per-ID weights or physical order");
        for (int endpoint_index = 0; endpoint_index < 2; ++endpoint_index) {
            const int a = endpoint_index == 0 ? std::get<0>(graph[i]) : std::get<1>(graph[i]);
            const int c = endpoint_index == 0 ? std::get<0>(twin.graph[i]) : std::get<1>(twin.graph[i]);
            require(original[a]/b == original[c]/b, "endpoint ablation changes projected core endpoints");
        }
        if (std::get<3>(graph[i]) < n-n/b) require(graph[i] == twin.graph[i], "endpoint ablation changes a local edge");
    }

    const auto reference = kruskal(graph, n);
    benchmark_validation::certify_mst(graph, reference, n); ++counts.certified_outputs;
    const auto expected = edge_ids(reference);
    if (!random && !shuffled) {
        const auto independent = independent_structured_mst(spec, fixture, original);
        require(independent == expected, "independent star/dyadic-cut MST differs from Kruskal");
        benchmark_validation::certify_mst(graph, select_ids(graph, independent), n);
    }
    if (spec.family == "leaf_distance4" && n == 128 && spec.density == 4 && seed == 42) {
        for (const auto& [u, v, unused, id] : reference) {
            (void)unused; (void)id;
            const int a = original[u]/b, c = original[v]/b;
            if (a != c && std::max(a, c)-std::min(a, c) > 1) ++counts.dense_distance_chords;
        }
        require(counts.dense_distance_chords > 0, "dense distance regression selected no core chord");
    }
    for (const auto& candidate : {prim(graph, n), boruvka(graph, n)}) {
        benchmark_validation::certify_mst(graph, candidate, n); ++counts.certified_outputs;
        require(edge_ids(candidate) == expected, "classical solver differs from unique MST");
    }
    for (unsigned sampling : {0u, 1u, 101u}) {
        problem input(n, graph);
        const auto actual = kkt(input, sampling);
        benchmark_validation::certify_mst(graph, select_ids(graph, actual), n); ++counts.certified_outputs;
        require(actual == expected, "KKT differs from unique MST");
    }
    const auto contractions = check_contractions(fixture, n);
    benchmark_validation::certify_mst(graph, select_ids(graph, contractions.selected), n); ++counts.certified_outputs;
    require(contractions.selected == expected, "full compactor differs from unique MST");
    if (!random) {
        check_cheap_star_stages(spec, fixture, contractions);
        if (leaf) {
            const auto other = check_contractions(twin, n);
            require(other.selected == expected && contractions.stages.size() == other.stages.size(),
                    "endpoint twin compactor result/stage count differs");
            for (std::size_t i = 0; i < contractions.stages.size(); ++i) {
                const auto& a = contractions.stages[i]; const auto& c = other.stages[i];
                require(a.selected == c.selected && a.quotient == c.quotient &&
                        a.quotient_vertices == c.quotient_vertices && a.partition == c.partition,
                        "endpoint twins differ in physical selected vector or complete quotient trajectory");
            }
            ++counts.endpoint_trace_pairs;
#ifdef KKT_ENABLE_WORK_STATS
            if (seed == 42 && ((b == 4 && n == 512 && spec.density == 16) ||
                               (b == 16 && n == 1024 && spec.density == 2)))
                equal_counters(fixture, twin, n, expected);
#endif
        }
    }
    ++counts.fixtures;
}

} // namespace

int main() {
    try {
        for (const char* family : benchmark_attachments::families) {
            const int b = std::string(family).back() == '4' ? 4 : 16;
            const std::vector<std::pair<int, int>> dimensions = b == 4 ?
                std::vector<std::pair<int, int>>{{32,1},{64,2},{128,4},{512,16}} :
                std::vector<std::pair<int, int>>{{64,1},{1024,2},{2048,4},{8192,16}};
            for (const auto& [n, density] : dimensions) {
                const auto seeds = n >= 8192 ? std::vector<unsigned>{42} : std::vector<unsigned>{17,42,999};
                for (unsigned seed : seeds) {
                    const Spec spec{family, n, density, 0};
                    try { check_fixture(spec, seed); }
                    catch (const std::exception& error) {
                        throw std::runtime_error(benchmark_continuation::case_id(spec)+" seed="+
                                                 std::to_string(seed)+": "+error.what());
                    }
                }
            }
        }
        int caps = 0, invalid = 0;
        for (const char* family : benchmark_attachments::families)
            for (const auto& [n, d] : {std::pair<int,int>{1<<22,32}, {1<<18,512}}) {
                require(benchmark_attachments::edge_count({family,n,d,0}) == 134217728,
                        "exact maximum edge budget rejected");
                ++caps;
            }
        for (const Spec& spec : {Spec{"unknown",64,1,0}, Spec{"leaf_hierarchy8",64,1,0},
                Spec{"leaf_hierarchy4",0,1,0}, Spec{"leaf_hierarchy4",-32,1,0},
                Spec{"leaf_hierarchy4",16,1,0}, Spec{"leaf_hierarchy4",96,1,0},
                Spec{"leaf_hierarchy16",32,1,0}, Spec{"leaf_hierarchy4",32,2,0},
                Spec{"community_distance16",512,2,0}, Spec{"leaf_random4",64,0,0},
                Spec{"leaf_random4",64,-1,0}, Spec{"leaf_random4",64,513,0},
                Spec{"leaf_hierarchy4",64,4,0}, Spec{"community_hierarchy16",64,2,0},
                Spec{"leaf_hierarchy4",128,4,-1}, Spec{"community_distance16",2048,4,1},
                Spec{"leaf_random4",128,4,1001}, Spec{"leaf_distance4",1<<22,33,0},
                Spec{"community_random16",1<<23,1,0}, Spec{"leaf_hierarchy4",1<<30,512,0}}) {
            bool rejected = false;
            try { (void)benchmark_attachments::edge_count(spec); }
            catch (const std::runtime_error&) { rejected = true; }
            require(rejected, "invalid dimensions accepted: "+benchmark_continuation::case_id(spec));
            ++invalid;
        }
        require(counts.fixtures == 176 && counts.certified_outputs == 7*counts.fixtures &&
                counts.slow_minimum_crosschecks > 0 && counts.endpoint_trace_pairs > 0 &&
                counts.dense_distance_chords > 0, "incomplete fixture coverage");
#ifdef KKT_ENABLE_WORK_STATS
        require(counts.counter_pairs == 24, "missing instrumented endpoint-counter pairs");
#else
        require(counts.counter_pairs == 0, "unexpected native counter checks");
#endif
        std::cout << "Validated " << counts.fixtures << " attachment fixtures, " << counts.stages
                  << " full independent contraction stages, " << counts.slow_minimum_crosschecks
                  << " sorted/slow minimum crosschecks, " << counts.certified_outputs
                  << " certified solver outputs, " << counts.endpoint_trace_pairs
                  << " exact endpoint-twin trajectories, " << counts.counter_pairs
                  << " all-field counter pairs, " << counts.dense_distance_chords
                  << " dense-distance core chords, " << invalid << " rejected dimensions and "
                  << caps << " nonallocating maximum-edge checks.\n";
    } catch (const std::exception& error) {
        std::cerr << "core attachment fixture test: " << error.what() << '\n';
        return 1;
    }
}
