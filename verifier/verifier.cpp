#include "verifier.hpp"
#include "../union_find/union_find.hpp"
#include "../kruskal/kruskal.hpp"
#include "../boruvka/boruvka.hpp"
#include "../prim/prim.hpp"
#include "../lca/lca.hpp"
#include "../graph_utils/graph_utils.hpp"

#include <vector>
#include <utility>
#include <unordered_map>
#include <iostream>
#include <tuple>
#include <functional>

using namespace std;

// Macros para debuggar
#define TRACE(x)
#define WATCH(x) TRACE( cout << #x" = " << x << endl)
#define PRINT(x) TRACE(printf(x))
#define WATCHR(a, b) TRACE( for(auto c = a; c != b;) cout << *(c++) << " "; cout << endl)
#define WATCHC(V) TRACE({cout << #V" = "; WATCHR(V.begin(), V.end()); } )

// Logica para imprimir tuplas com o operator <<
template <size_t n, typename... T>
typename std::enable_if<(n >= sizeof...(T))>::type
    print_tuple(std::ostream&, const std::tuple<T...>&)
{}

template <size_t n, typename... T>
typename std::enable_if<(n < sizeof...(T))>::type
    print_tuple(std::ostream& os, const std::tuple<T...>& tup)
{
    if (n != 0)
        os << ", ";
    os << std::get<n>(tup);
    print_tuple<n+1>(os, tup);
}

template <typename... T>
std::ostream& operator<<(std::ostream& os, const std::tuple<T...>& tup)
{
    os << "[";
    print_tuple<0>(os, tup);
    return os << "]";
}

// Aqui vou implementar o processo de reducao de uma Spanning Tree T, para
// uma Full Branching Tree B, como descrito no paper de King.
//
// Dada uma Árvore de tamanho N, vamos produzir uma full branching tree de
// tamanho no máximo 2*N. Os nós de T serão folhas em B e é garantido que a
// distância entre as folhas de B é equivalente as distâncias dos nós em B.
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

// Aqui esta a alma da verificacao!
// Vou precisar construir todos os vetores como ele define no paper, a partir do
// vetor de tuplas que eh a arvore reduzida
struct tree_path_maxima {
    int height, n, m, root;
    vector<int> depth, D, L, Lnext, answer, median, P, upper, lower, child,
        sibling, weight;

    tree_path_maxima(int _root, vector<int> _child, vector<int> _sibling,
                     vector<int> _weight, vector<int> _upper, vector<int> _lower) {
        height = 0, n = static_cast<int>(_child.size()),
        m = static_cast<int>(_upper.size());
        depth.assign(n, 0);
        D.assign(n, 0);
        L.assign(n, 0);
        Lnext.assign(m, 0);
        answer.assign(m, 0);
        upper = _upper;
        lower = _lower;
        child = _child;
        sibling = _sibling;
        weight = _weight;
        root = _root;
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
        vector<int> median_T(1 << (h + 1), 0);

        std::function<int(int, int, int)> subsets = [&](int x, int y, int z) {
            if (x < y) return z;
            if (y == 0) {
                T[z] = 0;
                return z + 1;
            }
            int q = subsets(x - 1, y - 1, z);
            for (int i = z; i < q; ++i) T[i] |= 1 << (x - 1);
            return subsets(x - 1, y, q);
        };

        for (int s = 0; s <= h; ++s) {
            for (int k = 0; k <= s; ++k) {
                int p = subsets(h - s, k, 0);
                int q = subsets(s, k, p);
                q = subsets(s, k + 1, q);
                for (int i = 0; i < p; ++i) {
                    int b = (1 << (s + 1)) * T[i] + (1 << s);
                    for (int j = p; j < q; ++j) {
                        median_T[b + T[j]] = s;
                    }
                }
            }
        }
        return median_T;
    }

    int down(int A, int B) { return B & (~(A | B) ^ (A + (A | ~B))); }

    void visit(int v, int S) {
        auto binary_search = [&](int w, int S) {
            if (S == 0) return 0;
            int j = median[S];
            while (S != 1 << j) {
                S &= (weight[P[j]] > w) ? ~((1 << j) - 1) : (1 << j) - 1;
                j = median[S];
            }
            return (weight[P[j]] > w) ? j : 0;
        };

        P[depth[v]] = v;
        int k = binary_search(weight[v], down(D[v], S));
        S = down(D[v], (S & (1 << ((k + 1) - 1))) | (1 << depth[v]));
        for (int i = L[v]; i >= 0; i = Lnext[i]) {
            answer[i] = P[median[down(1 << depth[upper[i]], S)]];
        }
        for (int z = child[v]; z >= 0; z = sibling[z]) visit(z, S);
    }

    vector<int> compute_answer() {
        fill(L.begin(), L.end(), -1);
        fill(Lnext.begin(), Lnext.end(), -1);
        for (int i = 0; i < m; ++i) {
            Lnext[i] = L[lower[i]];
            L[lower[i]] = i;
        }
        fill(D.begin(), D.end(), 0);
        init(root, 0);
        P = vector<int>(height + 1, 0);
        median = median_table(height);
        visit(root, 0);
        return answer;
    }
};

// Instruções de uso
// vetor edges recebe as arestas todas as arestas do grafo, no formato (origem, destino, custo)
// vetor spanning tree recebe todas as arestas de sua spanning tree, que voce deseja verificar
// auto V = test_graph(vector<tuple<int, int, int>> edges, vector<tuple<int, int, int> > spanning_tree, int total_nodes);
// V.verify(); // <- retorna um booleano, e se for falso diz qual aresta eh contra exemplo

struct test_graph {
    // vamos transformar o conjunto de arestas no formato necessario para rodar
    // o tree_path_maxima
    //
    // O tree_path_maxima pede
    // 1 - Uma raiz
    // 2 - Um vetor child que liga um pai ate o seu filho mais a esquerda, ou -1
    // se for folha 
    // 3 - Um vetor sibling, que indica para cada nó qual o "irmão"
    // da direita 
    // 4 - Um vetor weight, que diz o peso que liga um determinado nó
    // ao seu pai 
    // 5 - Além de tudo, isso precisa ser relativo a uma full
    // branching tree..
    // 6 - Vetor de arestas do grafo original
    int root, total_nodes;
    vector<int> child, sibling, weight;
    vector< tuple<int, int, int> > mst;
    vector< tuple<int, int, int> > G;
    LCA lca;
     
    
    test_graph(const vector<tuple<int, int, int>> edges, const vector<tuple<int, int, int> > spanning_tree, const int n) {
        mst = spanning_tree;
        auto fbt_mst = fbt_reduction(mst, n);
        G = edges;
        WATCHC(mst);
        WATCHC(fbt_mst);
        int max_id = n;
        for(const auto& e : fbt_mst) {
            int a, b, c;
            tie(a, b, c) = e;
            max_id = max(max(a, b) + 1, max_id);
        }
        total_nodes = max_id;
        // This N is for LCA
        int N = total_nodes;
        // End of LCA Prep
        vector< vector< pair<int, int> > > adj_list(max_id);
        vector< vector<int> > adj(N);
        //adj.resize(N);

        child.assign(max_id, -1);
        sibling.assign(max_id, -1);
        weight.assign(max_id, -1);
        root = max_id - 1;

        for(const auto& e : fbt_mst) {
            int a, b, c;
            tie(a, b, c) = e;
            adj_list[a].emplace_back(b, c);
            adj_list[b].emplace_back(a, c);
        }

        function<void(int, int)> dfs_lca = [&] (int node, int parent) {
            vector<int> kids;
            for(const auto& edge : adj_list[node]) {
                int to = edge.first;
                int cost = edge.second;
                if(to != parent) {
                    // Preparing the tree for the LCA
                    adj[node].push_back(to);
                    // End of preparation
                    kids.push_back(to);
                    weight[to] = cost;
                    dfs_lca(to, node);
                }
            }
            if(kids.empty()) return;
            child[node] = kids[0];
            for(int i = 0; i < static_cast<int>(kids.size()) - 1; ++i) {
                sibling[kids[i]] = kids[i + 1];
            }
        };
        // adj_list representa garantidamente o grafo de uma full branching tree, com raiz de índice = |V| - 1
        dfs_lca(root, -1);
        TRACE(cout << "iniciei o grafo" << endl; )
        
        // vamos imprimir ADJ
        TRACE(
            cout << "IMPRIMINDO AS ARESTAS DA ARVORE, CONSIDERADAS NO LCA" << '\n';
            for(int i = 0; i < max_id; ++i)
            {
                WATCHC(adj[i]);
            }
            cout << "FIM DA IMPRESSAO" << '\n';
             );
        // aqui estou computando o LCA, supostamente em O(n)
        //precompute_lca(root);
        lca = LCA(N, adj, root); 
        TRACE(cout << "precomputei o LCA" << endl; )
        // Aqui vou criar uma estrutura de LCA

    }

    // Essa funcao efetua a verificacao de fato
    bool verify() {
        vector<int> gabarito, upper, lower, corresponding_edge;
        // LCA Prep
        TRACE( cout << "entrei em verify" << endl; )
        int M = static_cast<int>(G.size());
        int upper_len = 0;
        vector< pair<int, int> > decomposed_query;
        
        for(int i = 0; i < M; ++i) {
            int src, to, cost;
            tie(src, to, cost) = G[i];
            // Agora preciso usar a LCA
            int anc = lca.query(src, to);
            pair<int, int> qry = {-1, -1};    
            if(anc != src) {
                upper.emplace_back(anc);
                lower.emplace_back(src);
                gabarito.emplace_back(cost);
                corresponding_edge.emplace_back(i);
                qry.first = upper_len;
                upper_len++;
            }
            if(anc != to) {
                upper.emplace_back(anc);
                lower.emplace_back(to);
                gabarito.emplace_back(cost);
                corresponding_edge.emplace_back(i);
                qry.second = upper_len;
                upper_len++;
            }

            if(qry.first == -1 && qry.second == -1) continue;
            else if(qry.first == -1) qry.first = qry.second;
            else if(qry.second == -1) qry.second = qry.first;
            
            decomposed_query.emplace_back(qry);
        }

        tree_path_maxima verifier = tree_path_maxima(root, child, sibling, weight, upper, lower);
        vector<int> sol = verifier.compute_answer();
        
        for(const auto& qry : decomposed_query) {
            int id_fst = qry.first, id_snd = qry.second;
            int edge_cost = gabarito[id_fst]; // vai ser igual para os dois indices, pois eh relativo a mesma aresta
            int heavy_combine = max( weight[sol[id_fst]], weight[sol[id_snd]] );
            if( heavy_combine > edge_cost ) {
                
                WATCH(upper[id_fst]);
                WATCH(lower[id_fst]);
                WATCH(upper[id_snd]);
                WATCH(lower[id_snd]);
                cout << "o peso da maior aresta = " << heavy_combine << '\n'; 
                cout << "A Spanning Tree nao é mínima!" << '\n';
                cout << "a aresta " << G[corresponding_edge[id_fst]] << " deveria fazer parte dela..." << '\n';
                cout << "Na MST, o menor custo entre " << get<0>(G[corresponding_edge[id_fst]]) << " e " << get<1>(G[corresponding_edge[id_fst]]) << " = " << heavy_combine << '\n';
                return false;
            }
        }
        return true;
    }
};

bool verify_mst(const vector< tuple<int, int, int> > graph, const vector< tuple<int, int, int> > spanning_tree, const int n)
{
    auto verifier = test_graph(graph, spanning_tree, n);
    return verifier.verify();
}

int main()
{
     
    vector< tuple<int, int, int> > graph;

    graph.emplace_back(0, 1, 1);
    graph.emplace_back(1, 2, 1);
    graph.emplace_back(2, 3, 4);
    graph.emplace_back(0, 3, 2);

    auto X = kruskal(graph, 4);
    WATCHC(X);
    auto Y = prim(graph, 4);
    WATCHC(Y);
    auto Z = boruvka(graph, 4);
    WATCHC(Z);

    // Vamos testar o verifier
    vector< tuple<int, int, int> > non_MST;
     
    non_MST.emplace_back(graph[0]);
    non_MST.emplace_back(graph[1]);
    non_MST.emplace_back(graph[2]);

    auto verifier = test_graph(graph, X, 4);
    if(verifier.verify() == true) {
        cout << "Kruskal gerou uma MST" << endl;
    }
    else cout << "Kruskal nao gerou uma MSt" << endl;
    
    auto verifier2 = test_graph(graph, non_MST, 4);
    if(verifier2.verify() == true) {
        cout << "verifier is broken" << endl;
    }
    else cout << "verifier working as expected" << endl;
    
    /*
    ios::sync_with_stdio(false); cin.tie(nullptr);
    constexpr int vertices = 5;

    vector< tuple<int, int, int> > G;
    
    // ifstream in("soc-pokec-relationships.txt");
    // int u, v;
    // srand(0);
    auto st = std::chrono::high_resolution_clock::now();

    while(in >> u >> v) {
        --u; --v;
        // Graph has no weight, so let's randomly attribute one..
        G.emplace_back(u, v, rand() % 1000);
    }
    // Agora eu tenho um grafo que quebra a verificacao!!!!
    G.emplace_back(0, 1, 100);
    G.emplace_back(1, 2, 100);
    G.emplace_back(2, 3, 100);
    G.emplace_back(4, 5, 100);

    G.emplace_back(2, 4, 34);
    G.emplace_back(1, 2, 40);
    G.emplace_back(0, 3, 36);
    G.emplace_back(0, 1, 98);
    G.emplace_back(1, 2, 47);

    WATCHC(G);

    auto nd = std::chrono::high_resolution_clock::now();

    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(nd - st);

    cout << "A leitura do grafo demorou um total de " << duration.count() << " milisegundos" << endl; 
    TRACE( cout << "terminei de ler o grafo" << endl; )

    auto MST_PRIM = kruskal(G, vertices);
    TRACE( cout << "terminei de rodar o Kruskal" << endl);
    long long MST_COST = 0ll;

    for(const auto& edge : MST_PRIM) {
        MST_COST += get<2>(edge);
    }

    TRACE( cout << "CUSTO MST PRIM = " << MST_COST << '\n');
    
    auto st2 = std::chrono::high_resolution_clock::now(); 
    auto verifier = test_graph(G, MST_PRIM, vertices);

    if(verifier.verify() == true) {
        cout << "verifier is working as expected" << '\n';
    }
    else cout << "verifier is broken" << '\n';
    
    auto nd2 = std::chrono::high_resolution_clock::now(); 
    auto duration2 = std::chrono::duration_cast<std::chrono::milliseconds>(nd2 - st2);
    cout << "A verificacao da MST demorou " << duration2.count() << " milisegundos" << endl; 
    */ 
    return 0;
}
