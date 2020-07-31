#ifndef UNION_FIND_H
#define UNION_FIND_H

#include <vector>

// Implementation of Union Find (Disjoint Set Union)
// Code includes Path Compression and Union by Rank for speeding it up
// Complexity:
//              unite -> O( ackermann_inverse_function(n) )
//              find_parent -> O( ackermann_inverse_function(n) )

struct UnionFind {
    UnionFind(int _n);
    int find_parent(int node);
    bool unite(int x, int y);
    std::vector<int> parent, rank;
    int n, cc;
};

#endif
