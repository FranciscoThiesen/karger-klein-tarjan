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
	int w = INF, to = -1;
	bool operator<(Edge const& other) const
	{
		return make_pair(w, to) < make_pair(other.w, other.to);
	}
	Edge()
	{
		w = INF;
		to = -1;
	}
	Edge(int _w, int _to) : w(_w), to(_to) {}
};

vector<tuple<int, int, int>> _prim(const vector<vector<Edge>>& adj, int n)
{
	vector<tuple<int, int, int>> spanning_tree;

	vector<Edge> min_e(n);
	min_e[0].w = 0;
	set<Edge> q;
	q.insert({0, 0});

	vector<bool> selected(n, false);
	for (int i = 0; i < n; ++i)
	{
		if (q.empty())
		{
			cout << "No MST!" << endl;
			exit(0);
		}

		int v = q.begin()->to;
		selected[v] = true;
		q.erase(q.begin());

		if (min_e[v].to != -1)
		{ spanning_tree.emplace_back(min_e[v].to, v, min_e[v].w); }

		for (Edge e: adj[v])
		{
			if (!selected[e.to] && e.w < min_e[e.to].w)
			{
				q.erase({min_e[e.to].w, e.to});
				min_e[e.to] = {e.w, v};
				q.insert({e.w, e.to});
			}
		}
	}
	return spanning_tree;
}

vector<tuple<int, int, int>> prim(const vector<tuple<int, int, int>>& edges,
								  int n)
{
	// First, let's convert edge list into and adjacency list
	vector<vector<Edge>> adj(n);
	for (const auto& e: edges)
	{
		int a, b, c;
		tie(a, b, c) = e;
		adj[a].push_back(Edge(c, b));
		adj[b].push_back(Edge(c, a));
	}

	vector<tuple<int, int, int>> res = _prim(adj, n);

	return res;
}
