#include "graph_utils.hpp"

#include "../union_find/union_find.hpp"
#include <algorithm>
#include <cassert>
#include <random>
#include <unordered_map>
#include <ctime>
#include <set>
#include <numeric>

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
    random_device rd;
	mt19937 g(rd());
	shuffle(edges.begin(), edges.end(), g);
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

// Para funcionar com o KKT do jeito que está, temos que garantir alguns invariantes sobre o grafo gerado:
// 1 - Os custos das arestas são únicos
// 2 - Não existem arestas paralelas
// 3 - Não existem loops
vector<tuple<int, int, int>> build_random_connected_graph(int num_vertices,
														  int num_edges)
{
	srand(time(NULL));
	assert(num_edges >= num_vertices - 1);
    assert(num_edges <= (num_vertices * (num_vertices - 1)) / 2);

    vector<int> W(num_edges, 0);
    iota(W.begin(), W.end(), 0);
    
    random_device rd;
    mt19937 g(rd());
    shuffle(W.begin(), W.end(), g);
    

	vector<tuple<int, int, int>> random_graph;
    int nxt = 0;
    set< pair<int, int> > edges;
    
    // Primeiro, criamos um grafo de linha, garantidamente conexo
	for (int i = 0; i < num_vertices - 1; ++i)
	{ random_graph.emplace_back(i, i + 1, W[nxt++]); edges.emplace(i, i + 1); }
    
	int remaining_edges = num_edges - (num_vertices - 1);
	for (int e = 0; e < remaining_edges; ++e)
	{
		int a, b;
		a = (rand() % num_vertices);
		b = (rand() % num_vertices);
        if(a > b) swap(a, b);
		while (b == a || edges.find(make_pair(a,b)) != edges.end()) {
            a = (rand() % num_vertices);
            b = (rand() % num_vertices);
            if(a > b) swap(a, b); 
        }
		random_graph.emplace_back(a, b, W[nxt++]);
        edges.emplace(a,b);
	}

	assert(static_cast<int>(random_graph.size()) == num_edges);
	return random_graph;
}
