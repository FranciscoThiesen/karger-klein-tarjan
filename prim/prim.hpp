#ifndef PRIM_H
#define PRIM_H

#include <utility>
#include <vector>

using namespace std;

// Source: https://cp-algorithms.com/graph/mst_prim.html
// Complexity: O(m log n)

vector<tuple<int, int, int>> prim(const vector<tuple<int, int, int>>& edges,
								  int n);

#endif
