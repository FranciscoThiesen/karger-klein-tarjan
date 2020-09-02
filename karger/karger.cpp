#include <bits/stdc++.h>
#include <boost/functional/hash.hpp>

// Isso aqui é apenas uma implementação inicial
// Nessa versão, não vou me preocupar com encontrar a MST em si, estou satisfeito em encontrar apenas o custo

using namespace std;

// Essa função vai aplicar o passo Boruvka, descrito no paper do KKT. A ideia é diminuir 
// a quantidade de vértices pela metade, ainda em tempo linear.

// Se eu quiser retornar as arestas utilizadas, preciso pensar em manter para cada nó, qual super-nó ele pertence..
// Mesmo que as extremidades das arestas mudem ao longo do tempo, posso manter um índice que permite que cada aresta
// da MST seja mapeada para alguma das arestas originais.
pair<int, vector< tuple<int, int, int, int> > > boruvka_step(const vector< tuple<int, int, int, int> >& G, int n) {
    // Assume-se que o grafo recebido aqui é CONEXO!!!!
    // implementar!
    // Aqui, preciso retornar o grafo resultante e também as arestas que foram utilizadas!
    vector< int > smallest_incident_edge(n, -1);
    int total_edges = static_cast<int>(G.size());
    
    for(int i = 0; i < total_edges; ++i) {
        int from, to, cost;
        tie(from, to, cost, ignore) = G[i];
        if(smallest_incident_edge[from] == -1 || cost < get<2>(G[smallest_incident_edge[from]])) {
            smallest_incident_edge[from] = i; 
        }
        if(smallest_incident_edge[to] == -1 || cost < get<2>(G[smallest_incident_edge[to]])) {
            smallest_incident_edge[to] = i;
        }
    }
    
    vector< bool > used(total_edges, false);
    vector< tuple<int, int, int, int> > used_edges;

    vector< vector<int> > component_graph(n);
    int cost_for_used_edges = 0; 
    
    for(int i = 0; i < n; ++i) {
        if(smallest_incident_edge[i] == -1) continue;
        used[ smallest_incident_edge[i] ] = true;
        int from, to, cost;
        tie(from, to, cost) = G[smallest_incident_edge[i]];
        component_graph[from].push_back(to);
        component_graph[to].push_back(from);
        
        // Se tiver algum problema, é necessário se certificar que não ocorre overflow aqui!
        cost_for_used_edges += cost;
        used_edges.emplace_back(G[smallest_incident_edge[i]]);
    }

    // Agora são feitos os passos mais importantes
    // 1 - Remoção de super-nós isolados
    // 2 - Se existem múltiplas arestas entre os mesmos dois super-componentes, queremos manter apenas a menor!
    // 3 - Remover self-loops que ligam um super-nó em si mesmo
    
    int next_component_id = 0;
    vector<int> super_node_id(n, -1);
    
    function<void(int, int)> dfs = [&] (int root, int parent) {
        if(parent == -1) super_node_id[root] = next_component_id++;
        else super_node_id[root] = super_node_id[parent];

        for(const auto& viz : component_graph[root]) {
            if(super_node_id[viz] == -1) {
                dfs(viz, root);
            }
        }
    };

    for(int i = 0; i < n; ++i) if(super_node_id[i] == -1) dfs(i, -1);
    
    vector<int> super_node_degree(next_component_id, 0);
    vector<int> super_node_new_id(next_component_id, 0);
    
    for(int i = 0; i < total_edges; ++i) {
        int from, to, cost;
        tie(from, to, cost, ignore) = G[i];
        if(super_node_id[from] != super_node_id[cost]) {
            super_node_degree[ super_node_id[from] ]++;
            super_node_degree[ super_node_id[to] ]++;
        }
    }
    
    // Agora, vou remapear os super-nós. Isso vai permitir remover do problema os super_node isolados!
    int next_non_isolated_id = 0;
    for(int i = 0; i < next_component_id; ++i) {
        if(super_node_degree[i] > 0) {
            // Agora, o que vou fazer é mudar o índice desse componente... Nova numeração exclui os isolados!
            super_node_new_id[i] = next_non_isolated_id++;
        }
    }

    vector< tuple<int, int, int> > remaining_problem;
    
    // Agora, quero apenas guardar qual é a aresta mais barata entre supercomponentes.
    // Para manter o tempo esperado linear, preciso usar hash_table para isso
    unordered_map< pair<int, int>, int, boost::hash<pair<int, int> > > minimal_edge;
    
    for(int i = 0; i < total_edges; ++i) {
        if(used[i]) continue;
        int from, to, cost, id;
        tie(from, to, cost, id) = G[i];
        if(super_node_id[from] != super_node_id[to]) {
            // vamos construir essa aresta no grafo novo!
            int f = super_node_new_id[super_node_id[from]];
            int t = super_node_new_id[super_node_id[to]];
            if(f > t) swap(f, t);
            if(minimal_edge.count(make_pair(f,t)) == 0) minimal_edge[make_pair(f, t)] = i;
            else {
                int current_cost = get<2>(G[minimal_edge[make_pair(f, t)]]);
                if(cost < current_cost) {
                    minimal_edge[make_pair(f, t)] = i;
                }
            } 
        }     
    }
    
    for(const auto& P : minimal_edge) {
        int from, to, cost, id;
        tie(from, to, cost, id) = G[P.second];
        remaning_problem.emplace_back(P.first.first, P.first.second, cost, id);
    }
    
    // Vou precisar retornar o remaining-problem tbm!
    return make_pair(cost_for_used_edges, remaining_problem);
}

// Seleciona arestas de G com probabilidade = 1/2. Esse processo é descrito no paper do KKT,
// onde essa etapa é chamada de Random Sampling.
vector< tuple<int, int, int> > random_sampling(const vector< tuple<int, int, int> >& G) {
    vector< tuple<int, int, int> > H;
    for(const auto& E : G) {
        int b = (rand() & 1);
        if(b) H.push_back(E);
    }
    return H;
}

// Retorna o custo da minimum-spanning-tree, em tempo esperado linear.
// Seguindo o processo descrito pelo paper KKT.
vector< tuple<int, int, int> > kkt(const vector< tuple<int, int, int> >& G) {
    vector< tuple<int, int, int> > resp;
    if(G.empty()) return resp;
    

    // Contract twice..
    

}
