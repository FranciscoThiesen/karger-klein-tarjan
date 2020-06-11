#include <bits/stdc++.h>

using namespace std;

struct union_find {
    int n;
    vector<int> parent, rank;

    union_find(int _n) : n(_n) {
        parent.resize(n);
        rank.assign(n, 1);
        iota(parent.begin(), parent.end(), 0);
    }

    int find_parent(int node) {
        if (parent[node] != node) parent[node] = find_parent(parent[node]);
        return parent[node];
    }

    bool unite(int x, int y) {
        x = find_parent(x);
        y = find_parent(y);
        if (x == y) return false;
        if (rank[x] < rank[y])
            parent[x] = y;
        else
            parent[y] = x;
        rank[x] += (rank[x] == rank[y]);
        return true;
    }
};

// Aqui vou implementar o processo de reducao de uma Spanning Tree T, para
// uma Full Branching Tree B, como descrito no paper de King.
//
// Dada uma Árvore de tamanho N, vamos produzir uma full branching tree de tamanho no máximo 2*N.
// Os nós de T serão folhas em B e é garantido que a distância entre as folhas de B é equivalente as distâncias dos nós em B.
vector<tuple<int, int, int> > fbt_reduction(
    int total_nodes, const vector<tuple<int, int, int> >& edges) {
    // para cada nó do grafo original, vamos criar uma folha nova em 
    union_find components(total_nodes);
    int graph_cc = total_nodes;
    int prox_node_id = total_nodes;
    // [0, current_node_count - 1] -> folhas
    int total_edges = static_cast<int>(edges.size());
    unordered_map<int, int> f_node;
    for (int i = 0; i < total_nodes; ++i) f_node[i] = i;
    vector<tuple<int, int, int> > new_edges;

    while (graph_cc > 1) {
        unordered_map<int, int> cheapest_edge;
        
        // Aqui vamos atualizar a aresta mais barata que chega em cada componente
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
        
        // Aqui vamos guardar a lista dos componentes resultantes após as uniões dessa fase do boruvka
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
        
        // Essa linha atualiza o índice de cada uma das componentes conexas resultantes para a próxima fase!
        f_node = new_cc_mapping;

        // Aqui atualizamos a quantidade de componentes. Quando tivermos um único componente, o algoritmo chega ao fim
        graph_cc = static_cast<int>(new_component_ids.size());
    }
    return new_edges;
}

int main() {
    
    // Teste do algoritmo
    vector<tuple<int, int, int> > test_tree;
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
