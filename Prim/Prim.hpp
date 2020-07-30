#ifndef PRIM_H
#define PRIM_H

#include <vector>
#include <utility>

using namespace std;

vector< tuple<int, int, int> > prim(const vector<tuple<int, int, int>>& edges, int n);

#endif
