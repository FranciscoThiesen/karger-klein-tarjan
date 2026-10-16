#ifndef KKT_EXPERIMENTAL_MULTIGRAPH_CONTRACTION_HPP
#define KKT_EXPERIMENTAL_MULTIGRAPH_CONTRACTION_HPP

// Opt-in experiment, not a replacement for the public simple-quotient step.
// Keep every crossing edge after contracting the selected forest. The KKT
// sampling/filtering recursion accepts parallel edges; repeated Boruvka's
// public step continues to deduplicate them. Input order is preserved here,
// so enabling this experiment changes subsequent random sampling trajectories.
#include "kkt.hpp"
#include "../common/phase_stats.hpp"

#include <algorithm>
#include <cassert>
#include <utility>
#include <vector>

namespace kkt_experiment {

inline std::pair<std::vector<int>, problem> retain_parallel_step(const problem& P)
{
    KKT_PHASE(contraction);
    const int n = P.num_vertices;
    const int total_edges = static_cast<int>(P.graph_edges.size());
    std::vector<int> smallest_incident_edge(n, -1);
    KKT_WORK_ADD(contraction_calls, 1);
    KKT_WORK_ADD(contraction_vertices, n);
    KKT_WORK_ADD(contraction_edges, total_edges);
    KKT_WORK_ADD(initialized_slots, n);
    KKT_WORK_ADD(contraction_edge_visits, total_edges);
    {
    KKT_PHASE(minimum_scan);
    for (int i = 0; i < total_edges; ++i) {
        const Edge& edge = P.graph_edges[i];
        if (smallest_incident_edge[edge.from] == -1 ||
            edge.cost < P.graph_edges[smallest_incident_edge[edge.from]].cost) {
            smallest_incident_edge[edge.from] = i;
        }
        if (smallest_incident_edge[edge.to] == -1 ||
            edge.cost < P.graph_edges[smallest_incident_edge[edge.to]].cost) {
            smallest_incident_edge[edge.to] = i;
        }
    }
    }

    std::vector<int> selected_edges;
    selected_edges.reserve(std::min(n, total_edges));
    KKT_WORK_ADD(contraction_vertex_visits, n);
    for (int vertex = 0; vertex < n; ++vertex) {
        const int edge_index = smallest_incident_edge[vertex];
        if (edge_index == -1) continue;
        const Edge& edge = P.graph_edges[edge_index];
        const int other = edge.from == vertex ? edge.to : edge.from;
        if (vertex <= other || smallest_incident_edge[other] != edge_index) {
            selected_edges.push_back(edge.id);
        }
    }

    // Identical selection and component numbering to boruvka_step. A selected
    // edge's endpoints belong to one component, so it cannot remain below.
    const int unassigned = -n - 1;
    std::vector<int> super_node_id(n, unassigned);
    KKT_WORK_ADD(initialized_slots, n);
    const auto successor = [&](int vertex) {
        const Edge& edge = P.graph_edges[smallest_incident_edge[vertex]];
        return edge.from == vertex ? edge.to : edge.from;
    };
    int next_component_id = 0;
    KKT_WORK_ADD(contraction_vertex_visits, n);
    for (int start = 0; start < n; ++start) {
        if (super_node_id[start] != unassigned) continue;
        if (smallest_incident_edge[start] == -1) {
            super_node_id[start] = next_component_id++;
            continue;
        }
        const int marker = -start - 1;
        int vertex = start;
        while (super_node_id[vertex] == unassigned) {
            KKT_WORK_ADD(contraction_vertex_visits, 1);
            KKT_WORK_ADD(contraction_arc_visits, 1);
            super_node_id[vertex] = marker;
            vertex = successor(vertex);
        }
        assert(super_node_id[vertex] >= 0 || super_node_id[vertex] == marker);
        const int component = super_node_id[vertex] >= 0
            ? super_node_id[vertex] : next_component_id++;
        vertex = start;
        while (super_node_id[vertex] == marker) {
            KKT_WORK_ADD(contraction_vertex_visits, 1);
            KKT_WORK_ADD(contraction_arc_visits, 1);
            super_node_id[vertex] = component;
            vertex = successor(vertex);
        }
    }
    if (next_component_id <= 1) {
        return {std::move(selected_edges), problem(0, std::vector<Edge>{}, P.max_edge_id)};
    }

    std::vector<int> super_node_degree(next_component_id, 0);
    KKT_WORK_ADD(initialized_slots, next_component_id);
    KKT_WORK_ADD(contraction_edge_visits, total_edges);
    std::size_t crossing_edges = 0;
    for (const Edge& edge : P.graph_edges) {
        const int from = super_node_id[edge.from];
        const int to = super_node_id[edge.to];
        if (from != to) {
            ++super_node_degree[from];
            ++super_node_degree[to];
            ++crossing_edges;
        }
    }

    std::vector<int> super_node_new_id(next_component_id, 0);
    KKT_WORK_ADD(initialized_slots, next_component_id);
    KKT_WORK_ADD(contraction_vertex_visits, next_component_id);
    int next_non_isolated_id = 0;
    for (int component = 0; component < next_component_id; ++component) {
        if (super_node_degree[component] > 0) {
            super_node_new_id[component] = next_non_isolated_id++;
        }
    }

    // There can be more crossing edges than pairs of quotient vertices.
    // Reserve the exact count from the degree pass, not the simple-graph bound.
    std::vector<Edge> remaining_edges;
    remaining_edges.reserve(crossing_edges);
    KKT_WORK_ADD(contraction_edge_visits, total_edges);
    for (const Edge& edge : P.graph_edges) {
        const int first = super_node_id[edge.from];
        const int second = super_node_id[edge.to];
        if (first == second) continue;
        const int from = super_node_new_id[first];
        const int to = super_node_new_id[second];
        remaining_edges.emplace_back(std::min(from, to), std::max(from, to),
                                     edge.cost, edge.id);
        KKT_WORK_ADD(edge_materializations, 1);
    }
    KKT_WORK_ADD(contraction_output_vertices, next_non_isolated_id);
    KKT_WORK_ADD(contraction_output_edges, remaining_edges.size());
    return {std::move(selected_edges),
            problem(next_non_isolated_id, std::move(remaining_edges), P.max_edge_id)};
}

}  // namespace kkt_experiment

#endif
