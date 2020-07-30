#include "graph_utils.hpp"

#include "../union_find/union_find.hpp"
#include <unordered_map>
#include <cassert>
#include <random>
#include <algorithm>

long long sum_of_costs(const vector< tuple<int, int, int> >& graph)
{
    long long answer = 0ll;
    for(const auto& e : graph) answer += get<2>(e);
    return answer;
}

vector< tuple<int, int, int> > get_random_spanning_tree(const vector< tuple<int, int, int> >& graph, int num_vertices) {
    vector< tuple<int, int, int> > edges = graph;
    random_shuffle(edges.begin(), edges.end());
    // Ideia analoga ao kruskal, mas feito com arestas que não estao ordenadas por peso
    vector< tuple<int, int, int> > spanning_tree;
    UnionFind UF(num_vertices);
    for(const auto& e : edges)
    {
        int u = get<0>(e), v = get<1>(e);
        if(UF.unite(u, v)) {
            spanning_tree.push_back(e);
        }
    }
    return spanning_tree;
}

vector< tuple<int, int, int> > build_random_connected_graph(int num_vertices, int num_edges)
{
    srand(time(NULL));
    assert(num_edges >= num_vertices - 1);
    
    int max_w = 100;
    vector< tuple<int, int, int> > random_graph; 
    
    // Primeiro, criamos um grafo de linha, garantidamente conexo
    for(int i = 0; i < num_vertices - 1; ++i)
    {
        random_graph.emplace_back(i, i + 1, max_w); 
    }
    
    int remaining_edges = num_edges - (num_vertices - 1);
    for(int e = 0; e < remaining_edges; ++e)
    {
        int a, b;
        a = (rand() % num_vertices);
        b = (rand() % num_vertices);

        while(b == a) b = (rand() % num_vertices);
        random_graph.emplace_back(a, b, ( rand() % max_w) );
    }

    assert(static_cast<int>(random_graph.size()) == num_edges);
    return random_graph;
}

vector<tuple<int, int, int>> fbt_reduction(
    const vector<tuple<int, int, int>>& edges, int total_nodes) {
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

