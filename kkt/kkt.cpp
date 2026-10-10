#include "kkt.hpp"
#include "../verifier/verifier_v2.hpp"
#include <algorithm>
#include <cassert>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace std;

// Debugging macros
#define TRACE(x)
#define WATCH(x) TRACE(cout << #x " = " << x << endl)

// Hash function for pair<int, int>
struct pair_hash {
    size_t operator()(const pair<int, int>& p) const {
        return hash<long long>()(static_cast<long long>(p.first) << 32 | p.second);
    }
};

// Boruvka Step: reduces the number of vertices by at least half
// Returns: (selected edge IDs, reduced problem)
// Complexity: O(n + m)
pair<vector<int>, problem> boruvka_step(const problem& P)
{
    int n = P.num_vertices;
    vector<int> smallest_incident_edge(n, -1);
    int total_edges = static_cast<int>(P.graph_edges.size());

    // Find minimum incident edge for each vertex
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

    vector<bool> used_edges(total_edges, false);  // Indexed within this subproblem
    vector<int> selected_edges;
    selected_edges.reserve(n);
    vector<vector<int>> component_graph(n);

    // Build component graph from selected edges
    for (int i = 0; i < n; ++i) {
        if (smallest_incident_edge[i] == -1) continue;
        int edge_index = smallest_incident_edge[i];
        if (used_edges[edge_index]) continue;
        used_edges[edge_index] = true;
        const Edge& e = P.graph_edges[edge_index];
        selected_edges.push_back(e.id);
        component_graph[e.from].push_back(e.to);
        component_graph[e.to].push_back(e.from);
    }

    // Find connected components using iterative DFS (avoids std::function overhead)
    int next_component_id = 0;
    vector<int> super_node_id(n, -1);
    vector<pair<int, size_t>> dfs_stack;  // (node, neighbor_index)
    dfs_stack.reserve(n);

    for (int start = 0; start < n; ++start) {
        if (super_node_id[start] != -1) continue;

        super_node_id[start] = next_component_id++;
        dfs_stack.emplace_back(start, 0);

        while (!dfs_stack.empty()) {
            auto& [node, idx] = dfs_stack.back();
            const auto& neighbors = component_graph[node];

            // Find next unvisited neighbor
            while (idx < neighbors.size() && super_node_id[neighbors[idx]] != -1) {
                ++idx;
            }

            if (idx < neighbors.size()) {
                int next = neighbors[idx];
                ++idx;
                super_node_id[next] = super_node_id[node];
                dfs_stack.emplace_back(next, 0);
            } else {
                dfs_stack.pop_back();
            }
        }
    }

    // Count degrees of super-nodes to remove isolated ones
    vector<int> super_node_degree(next_component_id, 0);
    for (int i = 0; i < total_edges; ++i) {
        const Edge& e = P.graph_edges[i];
        if (super_node_id[e.from] != super_node_id[e.to]) {
            super_node_degree[super_node_id[e.from]]++;
            super_node_degree[super_node_id[e.to]]++;
        }
    }

    // Renumber non-isolated super-nodes
    vector<int> super_node_new_id(next_component_id, 0);
    int next_non_isolated_id = 0;
    for (int i = 0; i < next_component_id; ++i) {
        if (super_node_degree[i] > 0) {
            super_node_new_id[i] = next_non_isolated_id++;
        }
    }

    // Keep only cheapest edge between each pair of super-nodes
    unordered_map<pair<int, int>, int, pair_hash> minimal_edge;
    for (int i = 0; i < total_edges; ++i) {
        const Edge& e = P.graph_edges[i];
        if (super_node_id[e.from] != super_node_id[e.to]) {
            int f = super_node_new_id[super_node_id[e.from]];
            int t = super_node_new_id[super_node_id[e.to]];
            if (f > t) swap(f, t);
            auto key = make_pair(f, t);
            if (minimal_edge.count(key) == 0 ||
                e.cost < P.graph_edges[minimal_edge[key]].cost) {
                minimal_edge[key] = i;
            }
        }
    }

    // Build remaining problem edges
    vector<Edge> remaining_edges;
    remaining_edges.reserve(minimal_edge.size());
    for (const auto& [key, idx] : minimal_edge) {
        const Edge& e = P.graph_edges[idx];
        remaining_edges.emplace_back(key.first, key.second, e.cost, e.id);
    }

    return {std::move(selected_edges),
            problem(next_non_isolated_id, std::move(remaining_edges), P.max_edge_id)};
}

// Remove isolated vertices from the graph
// Complexity: O(n + m)
problem remove_isolated_vertices(const problem& P)
{
    int prev_size = P.num_vertices;
    vector<int> degree(prev_size, 0);

    for (const Edge& e : P.graph_edges) {
        degree[e.from]++;
        degree[e.to]++;
    }

    int min_degree = *min_element(degree.begin(), degree.end());
    if (min_degree > 0) return P;

    // Renumber non-isolated vertices
    int next_id = 0;
    vector<int> new_node_id(prev_size, -1);
    for (int i = 0; i < prev_size; ++i) {
        if (degree[i] > 0) {
            new_node_id[i] = next_id++;
        }
    }

    vector<Edge> new_edges;
    new_edges.reserve(P.graph_edges.size());
    for (const Edge& e : P.graph_edges) {
        new_edges.emplace_back(new_node_id[e.from], new_node_id[e.to], e.cost, e.id);
    }

    return problem(next_id, std::move(new_edges), P.max_edge_id);
}

// Random sampling: select edges with probability 1/2
problem random_sampling(problem& P, unsigned int seed)
{
    srand(seed);
    vector<Edge> H;
    H.reserve(P.graph_edges.size() / 2);

    for (const Edge& e : P.graph_edges) {
        if (rand() & 1) {
            H.push_back(e);
        }
    }

    return remove_isolated_vertices(problem(P.num_vertices, std::move(H), P.max_edge_id));
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
static void kkt_internal(problem& P, unsigned int seed, vector<int>& result)
{
    if (P.graph_edges.empty()) {
        return;
    }

    // Apply Boruvka Step twice
    auto [edges1, reduced1] = boruvka_step(P);
    result.insert(result.end(), edges1.begin(), edges1.end());

    if (reduced1.graph_edges.empty() || reduced1.num_vertices == 0) {
        return;
    }

    auto [edges2, reduced2] = boruvka_step(reduced1);
    result.insert(result.end(), edges2.begin(), edges2.end());

    if (reduced2.num_vertices == 0 || reduced2.graph_edges.empty()) {
        return;
    }

    problem G = std::move(reduced2);

    // Random sampling
    problem H = random_sampling(G, seed);

    // Recursive KKT on sampled graph
    vector<int> kkt_h_result;
    kkt_internal(H, seed, kkt_h_result);

    // Membership storage is proportional to this sampled forest, not the ID range.
    unordered_set<int> sampled_ids(kkt_h_result.begin(), kkt_h_result.end());

    // Recover endpoints in G: sampling renumbers vertices in H.
    // Convert selected edges to tuple format for verifier
    vector<tuple<int, int, int, int>> H_MSF;
    H_MSF.reserve(kkt_h_result.size());
    for (const Edge& e : G.graph_edges) {
        if (sampled_ids.count(e.id)) {
            H_MSF.emplace_back(e.from, e.to, e.cost, e.id);
        }
    }

    // Find F-heavy edges
    vector<tuple<int, int, int, int>> G_tuples;
    G_tuples.reserve(G.graph_edges.size());
    for (const Edge& e : G.graph_edges) {
        G_tuples.emplace_back(e.from, e.to, e.cost, e.id);
    }

    auto G_heavy = verify_general_graph(G_tuples, H_MSF, G.num_vertices);

    // Filter out heavy edges
    vector<Edge> relevant_edges;
    relevant_edges.reserve(G.graph_edges.size());
    for (const Edge& e : G.graph_edges) {
        if (G_heavy.count(e.id) == 0) {
            relevant_edges.push_back(e);
        }
    }

    problem G_remaining = remove_isolated_vertices(
        problem(G.num_vertices, std::move(relevant_edges), P.max_edge_id));

    // Recursive KKT on remaining graph
    kkt_internal(G_remaining, seed, result);
}

// KKT algorithm using Hagerup verification
unordered_set<int> kkt(problem& P, unsigned int seed)
{
    if (P.graph_edges.empty()) {
        return unordered_set<int>();
    }

    vector<int> selected_ids;
    kkt_internal(P, seed, selected_ids);
    return unordered_set<int>(selected_ids.begin(), selected_ids.end());
}
