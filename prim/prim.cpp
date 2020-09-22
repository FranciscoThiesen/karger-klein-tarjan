#include "prim.hpp"

#include <chrono>
#include <iostream>
#include <set>
#include <tuple>
#include <utility>
#include <vector>

using namespace std;

constexpr int INF = 0x3f3f3f3f;

struct Edge
{
	int w = INF, to = -1, id;
	bool operator<(Edge const& other) const
	{
		return make_pair(w, to) < make_pair(other.w, other.to);
	}
	Edge()
	{
		w = INF;
		to = -1;
	}
	Edge(int _w, int _to, int _id) : w(_w), to(_to), id(_id) {}
};

vector<tuple<int, int, int, int>> _prim(const vector<vector<Edge>>& adj, int n)
{
	vector<tuple<int, int, int, int>> spanning_tree;

	vector<Edge> min_e(n);
	min_e[0].w = 0;
	set<Edge> q;
	q.insert({0, 0, -1});

	vector<bool> selected(n, false);
	for (int i = 0; i < n; ++i)
	{
		int v = q.begin()->to;
		selected[v] = true;
		q.erase(q.begin());

		if (min_e[v].to != -1)
		{ spanning_tree.emplace_back(min_e[v].to, v, min_e[v].w, min_e[v].id); }

		for (Edge e : adj[v])
		{
			if (!selected[e.to] && e.w < min_e[e.to].w)
			{
				q.erase({min_e[e.to].w, e.to, e.id});
				min_e[e.to] = {e.w, v, e.id};
				q.insert({e.w, e.to, e.id});
			}
		}
	}
	return spanning_tree;
}

vector<tuple<int, int, int, int>> prim(const vector<tuple<int, int, int, int>>& edges,
								  int n)
{
	vector<vector<Edge>> adj(n);
	for (const auto& e: edges)
	{
		int a, b, c, id;
		tie(a, b, c, id) = e;
		adj[a].push_back(Edge(c, b, id));
		adj[b].push_back(Edge(c, a, id));
	}

	vector<tuple<int, int, int, int>> res = _prim(adj, n);

	return res;
}
