#ifndef VERIFIERV2_H
#define VERIFIERV2_H

#include <tuple>
#include <vector>
#include <unordered_set>

using namespace std;

// Implementation of the linear MST verification algorithm. It returns the indices
// of all the edges from the graph that are F-heavy, following the concept of the
// Karger-Klein-Tarjan paper. All the edges that are F-heavy can be discarded 
// from the search for the MST.
//
// Assumptions: It receives a graph, following the edge convention of
// (from, to, cost, id) and a spanning tree for that graph.
// Complexity: O(m + n)
unordered_set<int>
	verify_mst2(const vector<tuple<int, int, int, int>>& graph,
			   const vector<tuple<int, int, int, int>>& spanning_tree, const int n);

// Implementation of the minimum spanning forest verification. It computes all
// the F-heavy edges, as defined by the Karger-Klein-Tarjan paper and 
// return their indices.
// 
// Assumptions: It receives a graph and a spanning forest of that graph,
// following the edge convention of (from, to, cost, id).
unordered_set<int>
	verify2_general_graph(const vector<tuple<int, int, int, int>>& graph,
						 const vector<tuple<int, int, int, int>>& general_graph,
						 const int n);

#endif
