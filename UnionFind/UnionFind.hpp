#ifndef UNION_FIND_H
#define UNION_FIND_H

#include <vector>

struct UnionFind {
    UnionFind(int _n);
    int find_parent(int node);
    bool unite(int x, int y);
    std::vector<int> parent, rank;
    int n;
};

#endif
