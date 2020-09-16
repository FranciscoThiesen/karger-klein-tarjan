#ifndef VERIFIER_H
#define VERIFIER_H

#include <tuple>
#include <vector>

using namespace std;

// Implementation of MST Verification, as described by Hagerup 2009. His version
// uses the idea of reducing the spanning tree to a full branching tree in order
// to achieve a simpler/cleaner implementation. The first linear time verification
// algorithm for MST's is from Dixon-Rauch-Tarjan 1997.
//
// Assumptions: graph should be connected and the spanning_tree parameter should be
// a tree in the corresponding graph
// Complexity: O(n + m)

bool verify_mst(const vector<tuple<int, int, int, int>>& graph,
				const vector<tuple<int, int, int, int>>& spanning_tree, const int n);

#endif
