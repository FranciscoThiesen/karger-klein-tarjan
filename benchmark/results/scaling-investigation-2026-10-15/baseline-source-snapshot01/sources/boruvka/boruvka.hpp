#ifndef BORUVKA_H
#define BORUVKA_H

#include <utility>
#include <vector>

using namespace std;

// Implementation of Boruvka's algorithm for finding a MST
// Complexity: O(m log n)
vector<tuple<int, int, int, int>> boruvka(const vector<tuple<int, int, int, int>>& edges,
									 int n);

#endif
