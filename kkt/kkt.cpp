#include "kkt.hpp"
#include "random_sampling.hpp"
#ifdef KKT_EXPERIMENT_RETAIN_PARALLEL
#include "experimental_multigraph_contraction.hpp"
#endif
#include "../common/work_stats.hpp"
#include "../verifier/verifier_v2.hpp"
#include <algorithm>
#include <cassert>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace std;

// Debugging macros
#define TRACE(x)
#define WATCH(x) TRACE(cout << #x " = " << x << endl)

// Boruvka Step: reduces the number of vertices by at least half
// Returns: (selected edge IDs, reduced problem)
// Complexity: O(n + m)
pair<vector<int>, problem> boruvka_step(const problem& P)
{
    int n = P.num_vertices;
    vector<int> smallest_incident_edge(n, -1);
    int total_edges = static_cast<int>(P.graph_edges.size());
    KKT_WORK_ADD(contraction_calls, 1);
    KKT_WORK_ADD(contraction_vertices, n);
    KKT_WORK_ADD(contraction_edges, total_edges);
    KKT_WORK_ADD(initialized_slots, n);

    // Find minimum incident edge for each vertex
    KKT_WORK_ADD(contraction_edge_visits, total_edges);
    for (int i = 0; i < total_edges; ++i) {
        const Edge& e = P.graph_edges[i];
        if (smallest_incident_edge[e.from] == -1 ||
            e.cost < P.graph_edges[smallest_incident_edge[e.from]].cost) {
            smallest_incident_edge[e.from] = i;
        }
        if (smallest_incident_edge[e.to] == -1 ||
            e.cost < P.graph_edges[smallest_incident_edge[e.to]].cost) {
            smallest_incident_edge[e.to] = i;
        }
    }

    vector<int> selected_edges;
    selected_edges.reserve(min(n, total_edges));

    // Only an edge's endpoints can select it. If both do, the first endpoint
    // in vertex order emits it; otherwise its sole selecting endpoint does.
    // This preserves selected-ID order without an m-sized duplicate bitmap.
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

    // Each non-isolated vertex points to its cheapest-edge neighbor. The
    // weak components of this functional graph are exactly the components
    // of the selected undirected edges; no adjacency lists are necessary.
    // Mark a successor walk, then finalize the same walk with either an
    // existing component ID or a new ID when it reaches its own cycle.
    // Every vertex is marked and finalized once. Isolated vertices are
    // singleton components. Ascending start vertices retain the previous
    // numbering by each component's smallest original vertex.
    const int unassigned = -n - 1;
    vector<int> super_node_id(n, unassigned);
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
        // Valid vertex indices are at most n-1, so this negative marker
        // cannot equal -n-1 or any finalized nonnegative component ID.
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

    // With at most one component every input edge is internal, including
    // the empty-graph case. No edge bucketing or degree scan is needed.
    if (next_component_id <= 1) {
        return {std::move(selected_edges), problem(0, vector<Edge>{}, P.max_edge_id)};
    }

    // Count degrees of super-nodes to remove isolated ones
    vector<int> super_node_degree(next_component_id, 0);
    KKT_WORK_ADD(initialized_slots, next_component_id);
    KKT_WORK_ADD(contraction_edge_visits, total_edges);
    for (int i = 0; i < total_edges; ++i) {
        const Edge& e = P.graph_edges[i];
        if (super_node_id[e.from] != super_node_id[e.to]) {
            super_node_degree[super_node_id[e.from]]++;
            super_node_degree[super_node_id[e.to]]++;
        }
    }

    // Renumber non-isolated super-nodes
    vector<int> super_node_new_id(next_component_id, 0);
    KKT_WORK_ADD(initialized_slots, next_component_id);
    int next_non_isolated_id = 0;
    KKT_WORK_ADD(contraction_vertex_visits, next_component_id);
    for (int i = 0; i < next_component_id; ++i) {
        if (super_node_degree[i] > 0) {
            super_node_new_id[i] = next_non_isolated_id++;
        }
    }

    // Bucket crossing edges by their smaller endpoint. Stamping destinations
    // within each bucket keeps only its cheapest edge in deterministic O(n+m)
    // work, without hashing or clearing an n-sized array for every bucket.
    vector<int> bucket_head(next_non_isolated_id, -1);
    vector<int> bucket_next(total_edges, -1);
    KKT_WORK_ADD(initialized_slots, static_cast<std::uint64_t>(next_non_isolated_id) + total_edges);
    KKT_WORK_ADD(contraction_edge_visits, total_edges);
    for (int i = 0; i < total_edges; ++i) {
        const Edge& e = P.graph_edges[i];
        if (super_node_id[e.from] == super_node_id[e.to]) continue;
        const int from = min(super_node_new_id[super_node_id[e.from]],
                             super_node_new_id[super_node_id[e.to]]);
        bucket_next[i] = bucket_head[from];
        bucket_head[from] = i;
    }

    vector<int> seen_from(next_non_isolated_id, -1);
    vector<int> output_index(next_non_isolated_id, -1);
    KKT_WORK_ADD(initialized_slots, 2ULL * next_non_isolated_id);
    vector<Edge> remaining_edges;
    const long long max_pairs = 1LL * next_non_isolated_id * (next_non_isolated_id - 1) / 2;
    remaining_edges.reserve(static_cast<size_t>(min<long long>(total_edges, max_pairs)));
    KKT_WORK_ADD(contraction_vertex_visits, next_non_isolated_id);
    for (int from = 0; from < next_non_isolated_id; ++from) {
        for (int i = bucket_head[from]; i != -1; i = bucket_next[i]) {
            KKT_WORK_ADD(contraction_edge_visits, 1);
            const Edge& e = P.graph_edges[i];
            const int to = max(super_node_new_id[super_node_id[e.from]],
                               super_node_new_id[super_node_id[e.to]]);
            if (seen_from[to] != from) {
                seen_from[to] = from;
                output_index[to] = static_cast<int>(remaining_edges.size());
                remaining_edges.emplace_back(from, to, e.cost, e.id);
                KKT_WORK_ADD(edge_materializations, 1);
            } else if (e.cost < remaining_edges[output_index[to]].cost) {
                remaining_edges[output_index[to]] = Edge(from, to, e.cost, e.id);
                KKT_WORK_ADD(edge_materializations, 1);
            }
        }
    }

    KKT_WORK_ADD(contraction_output_vertices, next_non_isolated_id);
    KKT_WORK_ADD(contraction_output_edges, remaining_edges.size());
    return {std::move(selected_edges),
            problem(next_non_isolated_id, std::move(remaining_edges), P.max_edge_id)};
}

// Remove isolates while consuming the existing edge vector. Only endpoints
// change: edge order, weights, IDs, and legacy metadata are preserved.
// Complexity: O(n + m)
static problem remove_isolated_vertices_owned(problem P)
{
    int prev_size = P.num_vertices;
    vector<int> degree(prev_size, 0);
    KKT_WORK_ADD(isolation_calls, 1);
    KKT_WORK_ADD(initialized_slots, prev_size);
    KKT_WORK_ADD(isolation_edge_visits, P.graph_edges.size());

    for (const Edge& e : P.graph_edges) {
        degree[e.from]++;
        degree[e.to]++;
    }

    // An empty vertex set has no minimum degree. It needs no compaction.
    if (prev_size == 0) return P;
    KKT_WORK_ADD(isolation_vertex_visits, prev_size);
    int min_degree = *min_element(degree.begin(), degree.end());
    if (min_degree > 0) return P;

    // Renumber non-isolated vertices
    int next_id = 0;
    vector<int> new_node_id(prev_size, -1);
    KKT_WORK_ADD(initialized_slots, prev_size);
    KKT_WORK_ADD(isolation_vertex_visits, prev_size);
    for (int i = 0; i < prev_size; ++i) {
        if (degree[i] > 0) {
            new_node_id[i] = next_id++;
        }
    }

    // Relabel the already-owned records instead of allocating/copying them.
    KKT_WORK_ADD(isolation_edge_visits, P.graph_edges.size());
    for (Edge& e : P.graph_edges) {
        e.from = new_node_id[e.from];
        e.to = new_node_id[e.to];
    }
    P.num_vertices = next_id;
    return P;
}

// Preserve the existing non-consuming entry point for callers with an lvalue.
problem remove_isolated_vertices(const problem& P)
{
    KKT_WORK_ADD(edge_materializations, P.graph_edges.size());
    return remove_isolated_vertices_owned(P);
}

// Sampling and filtering already construct temporary problems; transfer their
// vectors into the owned helper without a second allocation or edge copy.
static problem remove_isolated_vertices(problem&& P)
{
    return remove_isolated_vertices_owned(std::move(P));
}

// Random sampling consumes one draw per edge, preserving input order.
// Only a temporary recursive sample substitutes parent-graph positions for IDs;
// the public sampling wrapper retains its caller's IDs and legacy metadata.
template <bool use_parent_positions>
static problem sample_edges(const problem& P, std::mt19937& rng)
{
    vector<Edge> H;
    H.reserve(P.graph_edges.size() / 2);
    KKT_WORK_ADD(sampling_calls, 1);
    KKT_WORK_ADD(sampling_edge_visits, P.graph_edges.size());

    for (size_t position = 0; position < P.graph_edges.size(); ++position) {
        if (rng() & 1u) {
            const Edge& e = P.graph_edges[position];
            const int id = use_parent_positions ? static_cast<int>(position) : e.id;
            H.emplace_back(e.from, e.to, e.cost, id);
        }
    }

    KKT_WORK_ADD(sampled_edges, H.size());
    KKT_WORK_ADD(edge_materializations, H.size());
    const std::int64_t max_id = use_parent_positions
        ? static_cast<std::int64_t>(P.graph_edges.size()) : P.max_edge_id;
    return remove_isolated_vertices(problem(P.num_vertices, std::move(H), max_id));
}

problem kkt_detail::random_sampling(const problem& P, std::mt19937& rng)
{
    return sample_edges<false>(P, rng);
}

// Accumulate cost of edges in solution
int get_solution_cost(const problem& P, const unordered_set<int>& used)
{
    int res = 0;
    for (const Edge& e : P.graph_edges) {
        if (used.count(e.id)) {
            res += e.cost;
        }
    }
    return res;
}

// Get MST edges from their indices
vector<Edge> get_mst_edges_from_problem(const unordered_set<int>& mst_id, const problem& P)
{
    vector<Edge> MST;
    MST.reserve(mst_id.size());
    for (const Edge& e : P.graph_edges) {
        if (mst_id.count(e.id)) {
            MST.push_back(e);
        }
    }
    return MST;
}

// Append only selected IDs; recursive work must scale with the current graph.
static void kkt_internal(problem& P, std::mt19937& rng, vector<int>& result)
{
    KKT_WORK_RECURSION();
    KKT_WORK_ADD(kkt_calls, 1);
    KKT_WORK_ADD(kkt_vertices, P.num_vertices);
    KKT_WORK_ADD(kkt_edges, P.graph_edges.size());
    if (P.graph_edges.empty()) {
        return;
    }

    // Apply Boruvka Step twice
#ifdef KKT_EXPERIMENT_RETAIN_PARALLEL
    auto [edges1, reduced1] = kkt_experiment::retain_parallel_step(P);
#else
    auto [edges1, reduced1] = boruvka_step(P);
#endif
    result.insert(result.end(), edges1.begin(), edges1.end());

    if (reduced1.graph_edges.empty() || reduced1.num_vertices == 0) {
        return;
    }

#ifdef KKT_EXPERIMENT_RETAIN_PARALLEL
    auto [edges2, reduced2] = kkt_experiment::retain_parallel_step(reduced1);
#else
    auto [edges2, reduced2] = boruvka_step(reduced1);
#endif
    result.insert(result.end(), edges2.begin(), edges2.end());
    KKT_WORK_ROOT_SET(root_after_two_vertices, reduced2.num_vertices);
    KKT_WORK_ROOT_SET(root_after_two_edges, reduced2.graph_edges.size());

    if (reduced2.num_vertices == 0 || reduced2.graph_edges.empty()) {
        return;
    }

    problem G = std::move(reduced2);

    // Temporary sample IDs are positions in this unchanged parent graph.
    // Recursive contraction/filtering preserves its input ID namespace.
    problem H = sample_edges<true>(G, rng);

    // Recursive KKT on sampled graph
    vector<int> kkt_h_result;
    kkt_internal(H, rng, kkt_h_result);

    // Recover the sampled forest directly in G's vertex/ID namespace.
    // H may renumber vertices, but its returned IDs still index G. Nested
    // samples use their own positions only to construct their own verifiers.
    vector<tuple<int, int, int, int>> H_MSF;
    H_MSF.reserve(kkt_h_result.size());
    KKT_WORK_ADD(kkt_edge_visits, kkt_h_result.size());
    for (int position : kkt_h_result) {
        assert(position >= 0 && static_cast<size_t>(position) < G.graph_edges.size());
        const Edge& e = G.graph_edges[static_cast<size_t>(position)];
        H_MSF.emplace_back(e.from, e.to, e.cost, e.id);
    }
    KKT_WORK_ADD(edge_materializations, H_MSF.size());

    // Find F-heavy edges
#ifdef KKT_EXPERIMENT_EDGE_VIEW
    const auto heavy_marks = verifier_detail::heavy_edge_marks(G.graph_edges, H_MSF, G.num_vertices);
#else
    vector<tuple<int, int, int, int>> G_tuples;
    G_tuples.reserve(G.graph_edges.size());
    KKT_WORK_ADD(kkt_edge_visits, G.graph_edges.size());
    KKT_WORK_ADD(edge_materializations, G.graph_edges.size());
    for (const Edge& e : G.graph_edges) {
        G_tuples.emplace_back(e.from, e.to, e.cost, e.id);
    }

    const auto heavy_marks = verifier_detail::heavy_edge_marks(G_tuples, H_MSF, G.num_vertices);
#endif

    // Filter out heavy edges
    vector<Edge> relevant_edges;
    relevant_edges.reserve(G.graph_edges.size());
    KKT_WORK_ADD(kkt_edge_visits, G.graph_edges.size());
    for (size_t i = 0; i < G.graph_edges.size(); ++i) {
        if (!heavy_marks[i]) {
            relevant_edges.push_back(G.graph_edges[i]);
        }
    }
    KKT_WORK_ADD(filtered_edges, relevant_edges.size());
    KKT_WORK_ADD(edge_materializations, relevant_edges.size());

    problem G_remaining = remove_isolated_vertices(
        problem(G.num_vertices, std::move(relevant_edges), P.max_edge_id));

    // Recursive KKT on remaining graph
    kkt_internal(G_remaining, rng, result);
}

// KKT algorithm using Hagerup verification
unordered_set<int> kkt(problem& P, unsigned int seed)
{
    if (P.graph_edges.empty()) {
        return unordered_set<int>();
    }

    vector<int> selected_ids;
    std::mt19937 rng(seed);
    kkt_internal(P, rng, selected_ids);
    KKT_WORK_ADD(hash_insert_items, selected_ids.size());
    // The result size is known. Reserve buckets once instead of repeatedly
    // growing and relinking the public set while inserting selected edges.
    unordered_set<int> result;
    result.reserve(selected_ids.size());
    result.insert(selected_ids.begin(), selected_ids.end());
    return result;
}
