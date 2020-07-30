#include "kruskal.hpp"
#include "../union_find/union_find.hpp"

#include <tuple>
#include <utility>
#include <chrono>
#include <iostream>
#include <algorithm>

using namespace std;

// Recebe arestas da forma (src, to, cost) e a quantidade de vertices
// Se o grafo nao for conexo, vai retornar as arestas da Minimum Spanning Forest
vector< tuple<int, int, int> > kruskal(const vector< tuple<int, int, int> >& X, int n) 
{
	UnionFind graph(n);
    vector< tuple<int, int, int> > edges;
	vector< tuple<int, int, int> > spanning_tree;

	for(const auto& e : X) {
		int src, to, cost;
		tie(src, to, cost) = e;
		edges.emplace_back(cost, src, to);
	}
        
    // O real trabalho do algoritmo comeca aqui
    auto start_time = std::chrono::high_resolution_clock::now();

    sort(edges.begin(), edges.end());
    
    for(const auto& edge : edges) 
    {
        int cost, from, to;
        tie(cost, from, to) = edge;
        if(graph.unite(from, to)) {
        	spanning_tree.emplace_back(from, to, cost);
        }
    }

    auto end_time = std::chrono::high_resolution_clock::now();

    // vamos imprimir a duracao em milisegundos
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);

    cout << "Kruskal levou " << duration.count() << " milisegundos para retornar uma minimum spanning tree" << '\n';
    return spanning_tree;
}
