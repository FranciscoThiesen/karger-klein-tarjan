#ifndef GRAPH_UTILS_H
#define GRAPH_UTILS_H
#include <vector>
#include <utility>
#include <tuple>

using namespace std;
// Retorna um grafo conexo, com o numero especificado de vertices e arestas
// O grafo é retornado como uma lista de arestas, onde cada elemento é da forma
// (u, v, cost). Estamos trabalhando com arestas não direcionadas!
vector< tuple<int, int, int> > build_random_connected_graph(int num_vertices, int num_edges);

// Recebe uma árvore geradora mínima e a transforma em uma Full Branching Tree,
// de tamanho no máximo 2 * |n|, onde n é a quantidade de vértices da árvore da entrada.
// O algoritmo de conversão é completamente baseado no Boruvka, uma explicação em mais
// detalhes pode ser encontrada em (inserir link do king ou hageerup)
vector< tuple<int, int, int> > fbt_reduction(const vector< tuple<int, int, int> >& edges, int total_nodes);

#endif
