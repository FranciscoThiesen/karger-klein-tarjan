#ifndef KRUSKAL_H
#define KRUSKAL_H

#include <vector>
#include <utility>

using namespace std;

// Implementation of Kruskal algorithm for finding MST
// Complexity: O(m log n)

vector< tuple<int, int, int> > kruskal(const vector< tuple<int, int, int> >& X, int n);

#endif
