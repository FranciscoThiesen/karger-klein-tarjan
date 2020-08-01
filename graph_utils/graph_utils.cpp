#include "graph_utils.hpp"

#include "../union_find/union_find.hpp"
#include <algorithm>
#include <cassert>
#include <random>
#include <unordered_map>

long long sum_of_costs(const vector<tuple<int, int, int>>& graph)
{
	long long answer = 0ll;
	for (const auto& e: graph) answer += get<2>(e);
	return answer;
}

vector<tuple<int, int, int>>
	get_random_spanning_tree(const vector<tuple<int, int, int>>& graph,
							 int num_vertices)
{
	vector<tuple<int, int, int>> edges = graph;
	random_shuffle(edges.begin(), edges.end());
	// Ideia analoga ao kruskal, mas feito com arestas que não estao ordenadas
	// por peso
	vector<tuple<int, int, int>> spanning_tree;
	UnionFind UF(num_vertices);
	for (const auto& e: edges)
	{
		int u = get<0>(e), v = get<1>(e);
		if (UF.unite(u, v)) { spanning_tree.push_back(e); }
	}
	return spanning_tree;
}

vector<tuple<int, int, int>> build_random_connected_graph(int num_vertices,
														  int num_edges)
{
	srand(time(NULL));
	assert(num_edges >= num_vertices - 1);

	int max_w = 100;
	vector<tuple<int, int, int>> random_graph;

	// Primeiro, criamos um grafo de linha, garantidamente conexo
	for (int i = 0; i < num_vertices - 1; ++i)
	{ random_graph.emplace_back(i, i + 1, max_w); }

	int remaining_edges = num_edges - (num_vertices - 1);
	for (int e = 0; e < remaining_edges; ++e)
	{
		int a, b;
		a = (rand() % num_vertices);
		b = (rand() % num_vertices);

		while (b == a) b = (rand() % num_vertices);
		random_graph.emplace_back(a, b, (rand() % max_w));
	}

	assert(static_cast<int>(random_graph.size()) == num_edges);
	return random_graph;
}
