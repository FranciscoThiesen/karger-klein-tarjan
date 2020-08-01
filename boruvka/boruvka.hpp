#ifndef BORUVKA_H
#define BORUVKA_H

#include <utility>
#include <vector>

using namespace std;

// Implementation of the Boruvka for finding MST
// Complexity: O(m log n)

vector<tuple<int, int, int>> boruvka(const vector<tuple<int, int, int>>& edges,
									 int n);

#endif
