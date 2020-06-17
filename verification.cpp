#include <bits/stdc++.h>

#include "UnionFind/UnionFind.hpp"

using namespace std;

// Aqui vou implementar o processo de reducao de uma Spanning Tree T, para
// uma Full Branching Tree B, como descrito no paper de King.
//
// Dada uma Árvore de tamanho N, vamos produzir uma full branching tree de
// tamanho no máximo 2*N. Os nós de T serão folhas em B e é garantido que a
// distância entre as folhas de B é equivalente as distâncias dos nós em B.
vector<tuple<int, int, int>> fbt_reduction(
    int total_nodes, const vector<tuple<int, int, int>>& edges) {
    // para cada nó do grafo original, vamos criar uma folha nova em
    UnionFind components(total_nodes);
    int graph_cc = total_nodes;
    int prox_node_id = total_nodes;
    // [0, current_node_count - 1] -> folhas
    int total_edges = static_cast<int>(edges.size());
    unordered_map<int, int> f_node;
    for (int i = 0; i < total_nodes; ++i) f_node[i] = i;
    vector<tuple<int, int, int>> new_edges;

    while (graph_cc > 1) {
        unordered_map<int, int> cheapest_edge;

        // Aqui vamos atualizar a aresta mais barata que chega em cada
        // componente
        for (int i = 0; i < total_edges; ++i) {
            int from, to, cost;
            tie(from, to, cost) = edges[i];
            to = components.find_parent(to);
            from = components.find_parent(from);
            // Nesse caso os nós já pertencem a mesma componente conexa
            if (to == from) continue;
            if (cheapest_edge.count(from) == 0 ||
                cost < get<2>(edges[cheapest_edge[from]]))
                cheapest_edge[from] = i;
            if (cheapest_edge.count(to) == 0 ||
                cost < get<2>(edges[cheapest_edge[to]]))
                cheapest_edge[to] = i;
        }

        // Aqui vamos guardar a lista dos componentes atuais
        vector<int> component_list;
        for (const auto& cluster : cheapest_edge)
            component_list.push_back(cluster.first);

        for (const auto& cluster : cheapest_edge) {
            int from, to, cost;
            tie(from, to, cost) = edges[cluster.second];
            components.unite(from, to);
        }

        // Aqui vamos guardar a lista dos componentes resultantes após as uniões
        // dessa fase do boruvka
        vector<int> new_component_ids;
        for (const auto& cluster : cheapest_edge) {
            if (components.find_parent(cluster.first) == cluster.first)
                new_component_ids.push_back(cluster.first);
        }

        // Aqui estamos criando nós novos para cada componente conexa resultante
        unordered_map<int, int> new_cc_mapping;
        for (const auto& id : new_component_ids)
            new_cc_mapping[id] = prox_node_id++;

        // Aqui estamos inserindo as arestas no grafo novo!
        for (const auto& cluster : cheapest_edge) {
            int parent_cc = components.find_parent(cluster.first);
            new_edges.emplace_back(f_node[cluster.first],
                                   new_cc_mapping[parent_cc],
                                   get<2>(edges[cluster.second]));
        }

        // Essa linha atualiza o índice de cada uma das componentes conexas
        // resultantes para a próxima fase!
        f_node = new_cc_mapping;

        // Aqui atualizamos a quantidade de componentes. Quando tivermos um
        // único componente, o algoritmo chega ao fim
        graph_cc = static_cast<int>(new_component_ids.size());
    }
    return new_edges;
}

// Aqui esta a alma da verificacao!
// Vou precisar construir todos os vetores como ele define no paper, a partir do
// vetor de tuplas que eh a arvore reduzida
struct tree_path_maxima {
    int height, n, m, root;
    vector<int> depth, D, L, Lnext, answer, median, P, upper, lower, child, sibling, weight;

    tree_path_maxima(int root, vector<int> child, vector<int> sibling,
                     vector<int> weight, vector<int> upper, vector<int> lower) {
        height = 0, n = static_cast<int>(child.size()),
        m = static_cast<int>(upper.size());
        depth.assign(n, 0);
        D.assign(n, 0);
        L.assign(n, 0);
        Lnext.assign(m, 0);
        answer.assign(m, 0);
        upper = upper;
        lower = lower;
        child = child;
        sibling = sibling;
        weight = weight;
        root = root;
    }

    // d = depth of u
    void init(int u, int d) {
        depth[u] = d;
        if (d > height) height = d;  // height of T = maximum depth
        for (int i = L[u]; i >= 0; i = Lnext[i]) D[u] |= 1 << depth[upper[u]];
        for (int v = child[u]; v >= 0; v = sibling[v]) {
            init(v, d + 1);
            D[u] |= D[v] & ~(1 << d);
        }
    }

    vector<int> median_table(int h) {
        vector<int> T((1 << h) + 1, 0);
        vector<int> median_T(1 << h + 1, 0);

        std::function<int(int, int, int) > subsets = [&] (int a, int b, int c) {
            if (a < b) return c;
            if (b == 0) {
                T[c] = 0;
                return c + 1;
            }
            int q = subsets(a - 1, b - 1, c);
            for (int i = c; i < q; ++i) T[i] |= 1 << (a - 1);
            return subsets(a - 1, b, q);
        };

        for(int s = 0; s <= h; ++s) {
            for(int k = 0; k <= s; ++k) {
                int p = subsets(h - s, k, 0);
                int q = subsets(s, k, p);
                q = subsets(s, k + 1, q);
                for(int i = 0; i < p; ++i) {
                    int b = (1 << s + 1) * T[i] + (1 << s);
                    for(int j = p; j < q; ++j) median_T[b + T[j]] = s;
                }
            }
        }
        return median_T;
    }

    int down(int A, int B) { return B&(~(A|B)^(A + (A|~B))); }

    void visit(int v, int S) {
        auto binary_search = [&] (int w, int S) {
            if(S == 0) return 0;
            int j = median[S];
            while (S != 1 << j) {
                S &= (weight[P[j]] > w) ? ~((1<<j) - 1) : (1 << j) - 1;
                j = median[S];
            }
            return (weight[P[j]] > w) ? j : 0;
        };

        P[depth[v]] = v;
        int k = binary_search(weight[v], down(D[v], S));
        S = down(D[v], S&(1 << (k + 1) - 1) | (1 << depth[v]));
        for(int i = L[v]; i >= 0; i = Lnext[i]) {
            answer[i] = P[median[down(1<<depth[upper[i]], S)]];
        }
        for(int z = child[v]; z >= 0; z = sibling[z]) visit(z, S);
    }
    
    vector<int> compute_answer() {
        fill(L.begin(), L.end(), -1);
        fill(Lnext.begin(), Lnext.end(), -1);
        for(int i = 0; i < m; ++i) {
            Lnext[i] = L[lower[i]];
            L[lower[i]] = i;
        }
        fill(D.begin(), D.end(), 0);
        init(root, 0);
        P = vector<int>(height + 1);
        median = median_table(height);
        visit(root, 0);
        return answer; 
    }

};

int main() {
    // Teste do algoritmo
    vector<tuple<int, int, int>> test_tree;
    test_tree.emplace_back(0, 1, 3);
    test_tree.emplace_back(1, 2, 4);
    test_tree.emplace_back(1, 3, 7);

    auto fbt = fbt_reduction(4, test_tree);

    for (const auto& e : fbt) {
        int a, b, c;
        tie(a, b, c) = e;
        cout << a << " " << b << " " << c << '\n';
    }
    return 0;
}
