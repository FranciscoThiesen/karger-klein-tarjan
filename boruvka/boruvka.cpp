#include "boruvka.hpp"
#include "../union_find/union_find.hpp"

#include <vector>
#include <tuple>
#include <iostream>

using namespace std;

vector< tuple<int, int, int> > boruvka(const vector<tuple<int, int, int> >&edges, int n)
{
	UnionFind graph(n);
	vector<int> cheapest(n, -1);
	vector<tuple<int, int, int> > ans;

    int m = static_cast<int>(edges.size());
	while(graph.cc > 1)
	{
		fill(cheapest.begin(), cheapest.end(), -1);
		for(int i = 0; i < m; ++i)
		{
			int from, to, cost;
			tie(from, to, cost) = edges[i];
			to = graph.find_parent(to);
			from = graph.find_parent(from);
            if(from == to) continue;
            if(cheapest[from] == -1 || cost < get<2>(edges[cheapest[from]]) ) cheapest[from] = i;
            if(cheapest[to] == -1 || cost < get<2>(edges[cheapest[to]]) ) cheapest[to] = i;
		}

		for(int i = 0; i < n; ++i)
		{
			if(graph.parent[i] != i) continue;
			int from, to, cost;
			tie(from, to, cost) = edges[cheapest[i]];

			bool pay = false;
			if(i == from) pay = graph.unite(i, to);
			else pay = graph.unite(i, from);
			if(pay) ans.emplace_back(from, to, cost);
		}
	}

	return ans;
}
