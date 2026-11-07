#ifndef KKT_H
#define KKT_H

#include <cstdint>
#include <unordered_set>
#include <vector>
#include <tuple>
#include "../common/edge.hpp"
#include "../common/work_stats.hpp"

using namespace std;

struct problem {
    int num_vertices;
    std::int64_t max_edge_id;  // Legacy metadata; never used to size algorithm storage
    vector<Edge> graph_edges;

    problem(int nv = 0, vector<Edge> ge = vector<Edge>())
        : num_vertices(nv), max_edge_id(0), graph_edges(std::move(ge)) {
        // Compute max_edge_id from edges
        for (const Edge& e : graph_edges) {
            if (e.id >= max_edge_id) max_edge_id = static_cast<std::int64_t>(e.id) + 1;
        }
    }

    // Constructor with explicit max_edge_id (for internal use after contraction)
    problem(int nv, vector<Edge> ge, std::int64_t max_id)
        : num_vertices(nv), max_edge_id(max_id), graph_edges(std::move(ge)) {}

    // Constructor from tuple vector for backwards compatibility
    problem(int nv, const vector<tuple<int, int, int, int>>& ge)
        : num_vertices(nv), max_edge_id(0) {
        KKT_WORK_ADD(edge_materializations, ge.size());
        KKT_WORK_ADD(kkt_edge_visits, ge.size());
        graph_edges.reserve(ge.size());
        for (const auto& e : ge) {
            graph_edges.emplace_back(e);
            int id = std::get<3>(e);
            if (id >= max_edge_id) max_edge_id = static_cast<std::int64_t>(id) + 1;
        }
    }

    bool operator !=(const problem& rhs) const {
        if(num_vertices != rhs.num_vertices) return true;
        if(static_cast<int>(graph_edges.size()) != static_cast<int>(rhs.graph_edges.size())) return true;
        return false;
    }
};

// Accumulate cost of edges
int get_solution_cost(const problem& P, const unordered_set<int>& used);

// Get MST edges from their respective indices.
vector<Edge> get_mst_edges_from_problem(const unordered_set<int>& mst_id, const problem& P);

// Return the minimum spanning forest's original edge IDs, each exactly once.
// Input: undirected, loop-free graph with distinct weights, unique edge IDs,
// and endpoints in [0, num_vertices). Disconnected graphs and isolates are
// supported. IDs may be sparse or negative; they are not storage indices.
// Inputs and representability of internal int indices are not validated.
// The input is unchanged; seed initializes one private stream per invocation.
// Result order is unspecified. Output uses the internal vector directly, with
// amortized linear append work and no ID hashing or sorting. Expected O(n+m)
// work still relies on the KKT sampling and linear-verifier assumptions.
vector<int> kkt_edge_ids(const problem& P, unsigned int seed = 0);

// Compatibility wrapper with the same input contract. Adds hash-set creation
// to kkt_edge_ids; expected O(n+m) additionally requires constant expected hash
// insertion cost. Arbitrary IDs can produce quadratic collision-chain work.
unordered_set<int> kkt(problem& P, unsigned int seed = 0);

#endif
