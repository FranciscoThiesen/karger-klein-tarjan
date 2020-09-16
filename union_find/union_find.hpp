#ifndef UNION_FIND_H
#define UNION_FIND_H

#include <vector>

// Implementation of Union Find (Disjoint Set Union)
// Code includes Path Compression and Union by Rank for speeding it up
// Complexity: unite -> O( inverse_ack(n) ), find_parent( inverse_ack(n) )
struct UnionFind
{
	UnionFind(int _n);
	int find_parent(int node);
	bool unite(int x, int y);
	std::vector<int> parent, rank;
	int n, cc;
};

#endif
