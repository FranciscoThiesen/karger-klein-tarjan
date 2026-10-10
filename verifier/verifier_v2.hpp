#ifndef VERIFIERV2_H
#define VERIFIERV2_H

#include <tuple>
#include <vector>
#include <unordered_set>

using namespace std;

namespace verifier_detail {

// Internal KKT exchange: one byte per edge of this graph, in input order.
// A nonzero byte marks an F-heavy edge. Original edge IDs are opaque and
// never used as array indices; edges between forest components stay light.
vector<unsigned char> heavy_edge_marks(
    const vector<tuple<int, int, int, int>>& graph,
    const vector<tuple<int, int, int, int>>& forest, int n);

}  // namespace verifier_detail

// Implementation of the linear MST verification algorithm. It returns the indices
// of all the edges from the graph that are F-heavy, following the concept of the
// Karger-Klein-Tarjan paper. All the edges that are F-heavy can be discarded 
// from the search for the MST.
//
// Assumptions: It receives a graph, following the edge convention of
// (from, to, cost, id) and a spanning tree for that graph.
// Complexity: O(m + n)
unordered_set<int>
	verify_mst(const vector<tuple<int, int, int, int>>& graph,
			   const vector<tuple<int, int, int, int>>& spanning_tree, const int n);

// Implementation of the minimum spanning forest verification. It computes all
// the F-heavy edges, as defined by the Karger-Klein-Tarjan paper and 
// return their indices.
// 
// Assumptions: It receives a graph and a spanning forest of that graph,
// following the edge convention of (from, to, cost, id).
unordered_set<int>
	verify_general_graph(const vector<tuple<int, int, int, int>>& graph,
						 const vector<tuple<int, int, int, int>>& general_graph,
						 const int n);

#endif
