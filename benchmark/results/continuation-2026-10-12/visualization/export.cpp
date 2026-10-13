// Small, untimed explanatory fixtures. Link the unchanged production sources.
// This exporter is separate from the frozen timing harness and its source hash.
#include "../../../continuation_fixtures.hpp"
#include "../../../mst_certificate.hpp"
#include "../../../../kkt/kkt.hpp"
#include "../../../../kruskal/kruskal.hpp"

#include <algorithm>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <stdexcept>
#include <tuple>
#include <vector>

std::pair<std::vector<int>, problem> boruvka_step(const problem& input);

namespace {
using Graph = benchmark_fixtures::Graph;

void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

class Components {
    std::vector<int> parent;
public:
    explicit Components(int n) : parent(n) { std::iota(parent.begin(), parent.end(), 0); }
    int find(int v) {
        while (parent[v] != v) v = parent[v];
        return v;
    }
    void join(int a, int b) {
        a = find(a); b = find(b);
        if (a != b) parent[std::max(a, b)] = std::min(a, b);
    }
};

struct Stage {
    std::vector<std::vector<int>> members;
    std::vector<Edge> edges;
    std::vector<int> selected_next;
    int selected_total = 0;
    int loops_removed = 0;
    int parallels_removed = 0;
};

struct Drawing {
    std::string family;
    benchmark_continuation::Fixture fixture;
    std::set<int> mst;
    std::vector<Stage> stages;
};

Drawing make_drawing(const std::string& family) {
    constexpr int n = 64;
    Drawing drawing{family, benchmark_continuation::make_fixture({family, n, 4, 0}, 17), {}, {}};
    const auto& graph = drawing.fixture.graph;
    const auto tree = kruskal(graph, n);
    benchmark_validation::certify_mst(graph, tree, n);
    for (const auto& edge : tree) drawing.mst.insert(std::get<3>(edge));
    problem kkt_input(n, graph);
    const auto kkt_result = kkt(kkt_input, 0);
    require(std::set<int>(kkt_result.begin(), kkt_result.end()) == drawing.mst,
            "KKT differs from independently certified MST");

    problem current(n, graph);
    Stage initial;
    initial.members.resize(n);
    for (int original = 0; original < n; ++original)
        initial.members[drawing.fixture.original_to_label[original]].push_back(original);
    initial.edges = current.graph_edges;
    drawing.stages.push_back(std::move(initial));
    std::set<int> all_selected;
    while (!current.graph_edges.empty()) {
        auto [selected, reduced] = boruvka_step(current);
        std::set<int> independently_selected;
        for (int vertex = 0; vertex < current.num_vertices; ++vertex) {
            const Edge* best = nullptr;
            for (const auto& edge : current.graph_edges) {
                if ((edge.from == vertex || edge.to == vertex) &&
                    (!best || edge.cost < best->cost)) best = &edge;
            }
            require(best != nullptr, "connected intermediate graph has an isolate");
            independently_selected.insert(best->id);
        }
        require(std::set<int>(selected.begin(), selected.end()) == independently_selected,
                "production selected set differs from independent incident minima");
        auto& before = drawing.stages.back();
        before.selected_next = selected;
        std::map<int, Edge> by_id;
        for (const auto& edge : current.graph_edges) by_id.emplace(edge.id, edge);
        Components components(current.num_vertices);
        for (int id : selected) {
            require(drawing.mst.count(id) != 0, "production contraction selected a non-MST edge");
            require(all_selected.insert(id).second, "production contraction repeated an edge ID");
            const auto& edge = by_id.at(id);
            components.join(edge.from, edge.to);
        }

        // Independently reconstruct the selected-edge partition, numbering by
        // minimum current vertex. Verify every production edge against a simple
        // ordered-map implementation of loop removal and minimum parallel edge.
        std::map<int, int> labels;
        std::vector<std::vector<int>> members;
        for (int vertex = 0; vertex < current.num_vertices; ++vertex) {
            const int root = components.find(vertex);
            if (!labels.count(root)) {
                labels[root] = static_cast<int>(members.size());
                members.emplace_back();
            }
            auto& group = members[labels.at(root)];
            group.insert(group.end(), before.members[vertex].begin(), before.members[vertex].end());
        }
        for (auto& group : members) std::sort(group.begin(), group.end());
        std::map<std::pair<int, int>, std::pair<int, int>> cheapest;
        int loops = 0, crossing = 0;
        for (const auto& edge : current.graph_edges) {
            int u = labels.at(components.find(edge.from));
            int v = labels.at(components.find(edge.to));
            if (u == v) { ++loops; continue; }
            ++crossing;
            if (u > v) std::swap(u, v);
            const auto pair = std::make_pair(u, v);
            const auto value = std::make_pair(edge.cost, edge.id);
            if (!cheapest.count(pair) || value < cheapest.at(pair)) cheapest[pair] = value;
        }
        Graph expected_edges, actual_edges;
        for (const auto& [ends, value] : cheapest)
            expected_edges.emplace_back(ends.first, ends.second, value.first, value.second);
        for (const auto& edge : reduced.graph_edges)
            actual_edges.emplace_back(std::min(edge.from, edge.to), std::max(edge.from, edge.to),
                                      edge.cost, edge.id);
        std::sort(actual_edges.begin(), actual_edges.end());
        require(expected_edges == actual_edges, "production reduced graph differs from independent reconstruction");
        const int expected_vertices = members.size() == 1 ? 0 : static_cast<int>(members.size());
        require(reduced.num_vertices == expected_vertices, "production component numbering differs");
        if (expected_vertices == 0) members.clear(); // Completed isolate is dropped by production.
        Stage next;
        next.members = std::move(members);
        next.edges = reduced.graph_edges;
        next.selected_total = static_cast<int>(all_selected.size());
        next.loops_removed = loops;
        next.parallels_removed = crossing - static_cast<int>(cheapest.size());
        require(before.edges.size() == next.edges.size() + next.loops_removed + next.parallels_removed,
                "edge accounting failed");
        drawing.stages.push_back(std::move(next));
        current = std::move(reduced);
    }
    require(all_selected == drawing.mst, "completed production contraction differs from certified MST");
    return drawing;
}

void ints(const std::vector<int>& values) {
    std::cout << '[';
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << values[i];
    }
    std::cout << ']';
}

void write(const Drawing& drawing) {
    const auto& fixture = drawing.fixture;
    std::vector<int> original(64);
    for (int v = 0; v < 64; ++v) original[fixture.original_to_label[v]] = v;
    Graph by_id(fixture.graph.size());
    for (const auto& edge : fixture.graph) by_id[std::get<3>(edge)] = edge;
    int backbone_in_mst = 0;
    for (int id : drawing.mst) if (id < 63) ++backbone_in_mst;
    std::cout << "{\"family\":\"" << drawing.family << "\",\"n\":64,\"m\":256,\"density\":4,"
                 "\"graph_seed\":17,\"validation\":\"pass\",\"kkt_seed0_validation\":\"pass\","
                 "\"mst_backbone_count\":" << backbone_in_mst << ",\"original_to_label\":";
    ints(fixture.original_to_label);
    std::cout << ",\"backbone_ids\":"; ints(fixture.backbone_ids);
    std::vector<int> input_order;
    for (const auto& edge : fixture.graph) input_order.push_back(std::get<3>(edge));
    std::cout << ",\"input_order\":"; ints(input_order);
    std::cout << ",\"source_edges\":[";
    for (std::size_t i = 0; i < by_id.size(); ++i) {
        if (i) std::cout << ',';
        const auto [from, to, weight, id] = by_id[i];
        const int u = original[from], v = original[to];
        int level = 0;
        for (int difference = u ^ v; difference > 1; difference >>= 1) ++level;
        std::cout << '[' << u << ',' << v << ',' << weight << ',' << id << ',' << level << ','
                  << (id < 63 ? 1 : 0) << ',' << (drawing.mst.count(id) ? 1 : 0) << ']';
    }
    std::cout << "],\"stages\":[";
    for (std::size_t i = 0; i < drawing.stages.size(); ++i) {
        if (i) std::cout << ',';
        const auto& stage = drawing.stages[i];
        std::cout << "{\"round\":" << i << ",\"selected_total\":" << stage.selected_total
                  << ",\"loops_removed\":" << stage.loops_removed
                  << ",\"parallels_removed\":" << stage.parallels_removed << ",\"vertices\":[";
        for (std::size_t j = 0; j < stage.members.size(); ++j) {
            if (j) std::cout << ',';
            ints(stage.members[j]);
        }
        std::cout << "],\"edges\":[";
        for (std::size_t j = 0; j < stage.edges.size(); ++j) {
            if (j) std::cout << ',';
            const auto& edge = stage.edges[j];
            std::cout << '[' << edge.from << ',' << edge.to << ',' << edge.id << ']';
        }
        std::cout << "],\"selected_next\":"; ints(stage.selected_next);
        std::cout << '}';
    }
    std::cout << "]}";
}
} // namespace

int main() {
    try {
        // Finish and certify every fixture before emitting any JSON.
        std::vector<Drawing> drawings;
        for (const char* family : {"hierarchical_path", "distance_path", "low_path", "random_path",
                                   "hierarchical_tree", "distance_tree", "random_tree"})
            drawings.push_back(make_drawing(family));
        std::cout << "{\"schema\":1,\"description\":\"Engineered n64,d4 fixtures; actual production contraction, not KKT sampling.\","
                     "\"source_edge_fields\":[\"original_u\",\"original_v\",\"weight_rank\",\"id\",\"dyadic_level\",\"backbone\",\"mst\"],\"fixtures\":[";
        for (std::size_t i = 0; i < drawings.size(); ++i) {
            if (i) std::cout << ',';
            write(drawings[i]);
        }
        std::cout << "]}\n";
        require(static_cast<bool>(std::cout), "JSON write failed");
        std::cerr << "Exported seven independently certified fixtures and all production contraction stages.\n";
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
