#ifndef VERIFIER_H
#define VERIFIER_H

#include <tuple>
#include <vector>

using namespace std;

// Esse método busca utilizar o algoritmo O(n) de verificação descrito por
// Tarjan et. al para verificar se uma determinada arvore geradora eh de fato
// minima Essa função assume que está recebendo uma arvore geradora!
bool verify_mst(const vector<tuple<int, int, int>>& graph,
				const vector<tuple<int, int, int>>& spanning_tree, const int n);

#endif
