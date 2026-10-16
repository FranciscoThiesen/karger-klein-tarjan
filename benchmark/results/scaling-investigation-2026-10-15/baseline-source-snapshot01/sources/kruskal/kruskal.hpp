#ifndef KRUSKAL_H
#define KRUSKAL_H

#include <utility>
#include <vector>

using namespace std;

// Implementation of Kruskal's algorithm for finding MST
// Assumptions: We receive the edges of a connected graph.
// Complexity: O(m log n)
vector<tuple<int, int, int, int>> kruskal(const vector<tuple<int, int, int, int>>& graph_edges,
									 int n);

#endif
