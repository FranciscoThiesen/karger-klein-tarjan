#ifndef GRAPH_UTILS_H
#define GRAPH_UTILS_H

#include <vector>
#include <utility>
#include <tuple>

using namespace std;

// Retorna a soma dos custos das arestas de um grafo
long long sum_of_costs(const vector< tuple<int, int, int> >& graph);

// Gera uma spanning tree aleatória a partir de um grafo
vector< tuple<int, int, int> > get_random_spanning_tree(const vector< tuple<int, int, int> >& graph, int num_vertices);

// Retorna um grafo conexo, com o numero especificado de vertices e arestas
// O grafo é retornado como uma lista de arestas, onde cada elemento é da forma
// (u, v, cost). Estamos trabalhando com arestas não direcionadas!
vector< tuple<int, int, int> > build_random_connected_graph(int num_vertices, int num_edges);

#endif
