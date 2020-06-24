#include <bits/stdc++.h>

#include "UnionFind/UnionFind.hpp"

using namespace std;
#define TRACE(x) x
#define WATCH(x) TRACE( cout << #x" = " << x << endl)
#define PRINT(x) TRACE(printf(x))
#define WATCHR(a, b) TRACE( for(auto c = a; c != b;) cout << *(c++) << " "; cout << endl)
#define WATCHC(V) TRACE({cout << #V" = "; WATCHR(V.begin(), V.end()); } )

// Logica para imprimir tuplas
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
////////////////////////////////

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
        vector<int> median_T(1 << h + 1, 0);

        std::function<int(int, int, int)> subsets = [&](int a, int b, int c) {
            if (a < b) return c;
            if (b == 0) {
                T[c] = 0;
                return c + 1;
            }
            int q = subsets(a - 1, b - 1, c);
            for (int i = c; i < q; ++i) T[i] |= 1 << (a - 1);
            return subsets(a - 1, b, q);
        };

        for (int s = 0; s <= h; ++s) {
            for (int k = 0; k <= s; ++k) {
                int p = subsets(h - s, k, 0);
                int q = subsets(s, k, p);
                q = subsets(s, k + 1, q);
                for (int i = 0; i < p; ++i) {
                    int b = (1 << s + 1) * T[i] + (1 << s);
                    for (int j = p; j < q; ++j) median_T[b + T[j]] = s;
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
        S = down(D[v], S & (1 << (k + 1) - 1) | (1 << depth[v]));
        for (int i = L[v]; i >= 0; i = Lnext[i]) {
            answer[i] = P[median[down(1 << depth[upper[i]], S)]];
        }
        for (int z = child[v]; z >= 0; z = sibling[z]) visit(z, S);
    }

    vector<int> compute_answer() {
        fill(L.begin(), L.end(), -1);
        fill(Lnext.begin(), Lnext.end(), -1);
        TRACE( cout << "preenchendo L" << endl; )
        WATCHC(lower);
        WATCHC(upper);
        for (int i = 0; i < m; ++i) {
            Lnext[i] = L[lower[i]];
            L[lower[i]] = i;
        }
        TRACE( cout << "terminei de preencher L" << endl; )
        fill(D.begin(), D.end(), 0);
        TRACE( cout << "compute answer vai chamar init" << endl; )
        init(root, 0);
        P = vector<int>(height + 1);
        median = median_table(height);
        visit(root, 0);
        WATCHC(answer);
        return answer;
    }
};

// Recebe todas as arestas de um grafo (src, dest, cost) e retorna so as da MST
vector<tuple<int, int, int>> get_kruskal(const vector<tuple<int, int, int>>& g,
                                     int n) {
    UnionFind graph(n);
    vector<tuple<int, int, int>> edges;
    vector<tuple<int, int, int>> mst;
    for (const auto& x : g) {
        int src, dest, cost;
        tie(src, dest, cost) = x;
        edges.emplace_back(cost, src, dest);
    }
    sort(edges.begin(), edges.end());
    for (const auto& e : edges) {
        int cost, from, to;
        tie(cost, from, to) = e;
        if (graph.unite(from, to)) {
            mst.emplace_back(from, to, cost);
        }
    }
    return mst;
}

struct test_graph {
    // vamos transformar o conjunto de arestas no formato necessario para rodar
    // o tree_path_maxima
    //
    // O tree_path_maxima pede
    // 1 - Uma raiz
    // 2 - Um vetor child que liga um pai ate o seu filho mais a esquerda, ou -1
    // se for folha 3 - Um vetor sibling, que indica para cada nó qual o "irmão"
    // da direita 4 - Um vetor weight, que diz o peso que liga um determinado nó
    // ao seu pai 5 - Além de tudo, isso precisa ser relativo a uma full
    // branching tree.. 6 - Vetor de arestas do grafo original
    int root, total_nodes;
    vector<int> child, sibling, weight, upper, lower;
    vector< tuple<int, int, int> > mst;
    vector< tuple<int, int, int> > G;
     
    
    test_graph(vector<tuple<int, int, int>> edges, int n) {
        TRACE(
            cout << "test_graph recebeu as arestas" << endl;
            WATCHC(edges);
        );
        mst = get_kruskal(edges, n);
        TRACE(
            cout << "MST = " << endl;
            WATCHC(mst);
        );
        auto fbt_mst = fbt_reduction(mst, n);
        TRACE(
            cout << "versao full branching tree da MST" << endl;
            WATCHC(fbt_mst);
        );
        G = edges;
        // a raiz arbitraria vai ser o 0
        int max_id = n;
        for(const auto& e : fbt_mst) {
            int a, b, c;
            tie(a, b, c) = e;
            max_id = max(max(a, b) + 1, max_id);
        }
        total_nodes = max_id;
        vector< vector< pair<int, int> > > adj_list(max_id);
        
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
        TRACE( cout << "vou chamar a primeira dfs pra popular a arvore" << endl; )

        function<void(int, int)> dfs = [&] (int node, int parent) {
            vector<int> kids;
            for(const auto& edge : adj_list[node]) {
                int to = edge.first;
                int cost = edge.second;
                if(to != parent) {
                    kids.push_back(to);
                    weight[to] = cost;
                    dfs(to, node);
                }
            }
            if(kids.empty()) return;
            child[node] = kids[0];
            for(int i = 0; i < static_cast<int>(kids.size()) - 1; ++i) {
                sibling[kids[i]] = kids[i + 1];
            }
        };

        // adj_list representa garantidamente o grafo de uma arvore
        // vou fixar a raiz arbitraria dessa arvore em 0...
        dfs(root, -1);
        TRACE( cout << "terminei as dfs" << endl; )
        WATCHC(child);
        WATCHC(sibling);
        WATCHC(weight);
    }

    void verify() {
        vector<int> gabarito;
        for(const auto& e : G) {
            int src, to, cost;
            tie(src, to, cost) = e;
            upper.push_back(src);
            lower.push_back(to);
            gabarito.push_back(cost);
        }
        TRACE( cout << "vou chamar a tree path maxima " << endl; )
        tree_path_maxima caixa_de_pandora = tree_path_maxima(root, child, sibling, weight, lower, upper);
        TRACE( cout << "vou computar a resposta" << endl; ) 
        vector<int> sol = caixa_de_pandora.compute_answer();
        int len = static_cast<int>(lower.size());
        for(int i = 0; i < len; ++i)
        {
            cout << "quero saber a aresta mais barata entre " << lower[i] << " e " << upper[i] << endl;
            cout << "gabarito = " << gabarito[i] << " retorno arvore = " << weight[sol[i]] << endl << endl;
             
        }
    }
};

int main() {
    vector<tuple<int, int, int>> graph;
    graph.emplace_back(0, 1, 1);
    graph.emplace_back(1, 2, 10);
    graph.emplace_back(0, 2, 2);
    
    auto X = test_graph(graph, 3);
    X.verify();
    // Vamos rodar kruskal so pra testar

    return 0;
}
