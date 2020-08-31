#ifndef VERIFIERV2_H
#define VERIFIERV2_H

#include <tuple>
#include <vector>

using namespace std;

// Queremos computar todas as arestas que são F-Heavy, dado um grafo G e uma
// spanning tree G
vector<tuple<int, int, int>>
	verify_mst(const vector<tuple<int, int, int>>& graph,
			   const vector<tuple<int, int, int>>& spanning_tree, const int n);

vector<tuple<int, int, int>>
	verify_general_graph(const vector<tuple<int, int, int>>& graph,
						 const vector<tuple<int, int, int>>& general_graph,
						 const int n);

#endif
