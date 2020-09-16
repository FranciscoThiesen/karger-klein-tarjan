#include "kruskal.hpp"
#include "../union_find/union_find.hpp"

#include <algorithm>
#include <iostream>
#include <tuple>
#include <utility>

using namespace std;

vector<tuple<int, int, int, int>> kruskal(const vector<tuple<int, int, int, int>>& X,
									 int n)
{
	UnionFind graph(n);
	vector<tuple<int, int, int, int>> edges;
	vector<tuple<int, int, int, int>> spanning_tree;

	edges = X;

	sort(edges.begin(), edges.end(),
		 [&](const tuple<int, int, int, int>& a, const tuple<int, int, int, int>& b) {
			 return get<2>(a) < get<2>(b);
		 });

	for (const auto& edge: edges)
	{
		int from, to, cost, id;
		tie(from, to, cost, id) = edge;
		if (graph.unite(from, to))
		{ spanning_tree.emplace_back(from, to, cost, id); }
	}

	return spanning_tree;
}
