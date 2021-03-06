#include "graph_utils.hpp"

#include "../union_find/union_find.hpp"
#include <algorithm>
#include <cassert>
#include <ctime>
#include <numeric>
#include <random>
#include <set>
#include <unordered_map>

long long sum_of_costs(const vector<tuple<int, int, int, int>>& graph)
{
	long long answer = 0ll;
	for (const auto& e: graph) answer += get<2>(e);
	return answer;
}

vector<tuple<int, int, int, int>>
	get_random_spanning_tree(const vector<tuple<int, int, int, int>>& graph,
							 int num_vertices)
{
	vector<tuple<int, int, int, int>> edges = graph;
	random_device rd;
	mt19937 g(rd());
	shuffle(edges.begin(), edges.end(), g);
	vector<tuple<int, int, int, int>> spanning_tree;
	UnionFind UF(num_vertices);

	for (const auto& e: edges)
	{
		int u = get<0>(e), v = get<1>(e);
		if (UF.unite(u, v)) { spanning_tree.push_back(e); }
	}
	return spanning_tree;
}

vector<tuple<int, int, int, int>>
	build_random_connected_graph(int num_vertices, int num_edges,
								 unsigned int seed)
{
	srand(seed);
	assert(num_edges >= (num_vertices - 1));
	assert(1ll * num_edges <= (1ll * num_vertices * (num_vertices - 1)) / 2);

	vector<int> W(num_edges, 0);
	iota(W.begin(), W.end(), 0);

	random_device rd;
	mt19937 g(seed);
	shuffle(W.begin(), W.end(), g);

	vector<tuple<int, int, int, int>> random_graph;
	int nxt = 0;
	set<pair<int, int>> edges;

	for (int i = 0; i < num_vertices - 1; ++i)
	{
		random_graph.emplace_back(i, i + 1, W[nxt], nxt);
		++nxt;
		edges.emplace(i, i + 1);
	}

	int remaining_edges = num_edges - (num_vertices - 1);
	for (int e = 0; e < remaining_edges; ++e)
	{
		int a, b;
		a = (rand() % num_vertices);
		b = (rand() % num_vertices);
		if (a > b) swap(a, b);
		while (b == a || edges.find(make_pair(a, b)) != edges.end())
		{
			a = (rand() % num_vertices);
			b = (rand() % num_vertices);
			if (a > b) swap(a, b);
		}
		random_graph.emplace_back(a, b, W[nxt], nxt);
		++nxt;
		edges.emplace(a, b);
	}
	assert(static_cast<int>(random_graph.size()) == num_edges);
	return random_graph;
}
