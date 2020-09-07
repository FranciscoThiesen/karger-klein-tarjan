// OBSERVACAO IMPORTANTE
// DO JEITO QUE ESTA, essa verificação SÓ FUNCIONA SE OS PESOS DAS ARESTAS FOREM
// ÚNICOS!!!!!

#include "verifier_v2.hpp"
#include "../boruvka/boruvka.hpp"
#include "../graph_utils/graph_utils.hpp"
#include "../kruskal/kruskal.hpp"
#include "../lca/lca.hpp"
#include "../prim/prim.hpp"
#include "../union_find/union_find.hpp"

#include <cassert>
#include <functional>
#include <iostream>
#include <numeric>
#include <tuple>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace std;

// Macros para debuggar
#define TRACE(x)
#define WATCH(x) TRACE(cout << #x " = " << x << endl)
#define PRINT(x) TRACE(printf(x))
#define WATCHR(a, b)                                                           \
	TRACE(for (auto c = a; c != b;) cout << *(c++) << " "; cout << endl)
#define WATCHC(V)                                                              \
	TRACE({                                                                    \
		cout << #V " = ";                                                      \
		WATCHR(V.begin(), V.end());                                            \
	})

// Logica para imprimir tuplas com o operator <<
template <size_t n, typename... T>
typename std::enable_if<(n >= sizeof...(T))>::type
	print_tuple(std::ostream&, const std::tuple<T...>&)
{
}

template <size_t n, typename... T>
typename std::enable_if<(n < sizeof...(T))>::type
	print_tuple(std::ostream& os, const std::tuple<T...>& tup)
{
	if (n != 0) os << ", ";
	os << std::get<n>(tup);
	print_tuple<n + 1>(os, tup);
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
vector<tuple<int, int, int, int>>
	fbt_reduction(const vector<tuple<int, int, int, int>>& edges, int total_nodes)
{
	vector<tuple<int, int, int, int>> active_edges = edges;
	vector<int> component(total_nodes);
	iota(component.begin(), component.end(), 0);

	int graph_cc = total_nodes, prox_node_id = total_nodes;

	int total_edges = static_cast<int>(edges.size());
	vector<tuple<int, int, int, int>> new_edges;

	while (graph_cc > 1)
	{
		// encontra a aresta mais barata incidente em cada um dos componentes
		// existentes na fase atual salva o índice
		unordered_map<int, int> cheapest_edge;

		unordered_map<int, vector<int>> current_graph;
		// lista de adjacencia para cada componente ainda ativa nessa etapa
		// estou usando hash-tables para manter o tempo esperado linear

		for (int i = 0; i < total_edges; ++i)
		{
			int from, to, cost;
			tie(from, to, cost, ignore) = active_edges[i];

			// pensa que não vou precisar mais pegar o pai da componente...
			if (cheapest_edge.count(from) == 0 ||
				cost < get<2>(active_edges[cheapest_edge[from]]))
				cheapest_edge[from] = i;
			if (cheapest_edge.count(to) == 0 ||
				cost < get<2>(active_edges[cheapest_edge[to]]))
				cheapest_edge[to] = i;
		}

		// Aqui vamos guardar a lista de componentes atuais!
		vector<int> component_list;
		for (const auto& par: cheapest_edge)
			component_list.push_back(par.first);

		// Aqui, antigamente faziamos a união das componentes, agora vamos
		// apenas construir o grafo!
		for (const auto& par: cheapest_edge)
		{
			int from, to, cost;
			tie(from, to, cost, ignore) = active_edges[par.second];
			current_graph[from].push_back(to);
			current_graph[to].push_back(from);
		}

		vector<int> new_component_ids;
		unordered_map<int, int>
			super_node_id; // Isso vai marcar quais componentes do
						   // nível atual já foram marcados!

		// Agora vou marcar as componentes conexas de um indice novo, fazendo
		// uma dfs
		function<void(int, int)> explore_cc = [&](int root, int parent) {
			if (parent == -1)
			{
				int new_id = prox_node_id++;
				new_component_ids.push_back(new_id);
				super_node_id[root] = new_id;
			}
			else
			{
				super_node_id[root] = super_node_id[parent];
			}

			for (const auto& viz: current_graph[root])
			{
				if (viz != parent) { explore_cc(viz, root); }
			}
		};

		for (const auto& id: component_list)
		{
			if (super_node_id.count(id) == 0) explore_cc(id, -1);
		}

		for (const auto& par: cheapest_edge)
		{
			int super_node_cc = super_node_id[par.first];
			new_edges.emplace_back(par.first, super_node_cc,
								   get<2>(active_edges[par.second]));
		}

		vector<tuple<int, int, int, int>> relevant_edges;
		for (const auto& e: active_edges)
		{
			int from, to, cost, id;
			tie(from, to, cost, id) = e;
			if (super_node_id[from] != super_node_id[to])
			{
				// Aqui, estou mudando as arestas para refletir os novos
				// super-vértices obtidos nessa etapa
				relevant_edges.emplace_back(super_node_id[to],
											super_node_id[from], cost, id);
			}
		}
		active_edges = relevant_edges;
		total_edges = static_cast<int>(active_edges.size());
		graph_cc = static_cast<int>(new_component_ids.size());
	}
	// Retornando a full branching tree resultante
	return new_edges;
}

// Aqui esta a alma da verificacao!
// Vou precisar construir todos os vetores como ele define no paper, a partir do
// vetor de tuplas que eh a arvore reduzida
struct tree_path_maxima
{
	int height, n, m, root;
	vector<int> depth, D, L, Lnext, answer, median, P, upper, lower, child,
		sibling, weight;

	tree_path_maxima(int _root, vector<int> _child, vector<int> _sibling,
					 vector<int> _weight, vector<int> _upper,
					 vector<int> _lower)
	{
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
	void init(int u, int d)
	{
		depth[u] = d;
		if (d > height) height = d; // height of T = maximum depth
		for (int i = L[u]; i >= 0; i = Lnext[i]) D[u] |= 1 << depth[upper[u]];
		for (int v = child[u]; v >= 0; v = sibling[v])
		{
			init(v, d + 1);
			D[u] |= D[v] & ~(1 << d);
		}
	}

	vector<int> median_table(int h)
	{
		vector<int> T((1 << h) + 1, 0);
		vector<int> median_T(1 << (h + 1), 0);

		std::function<int(int, int, int)> subsets = [&](int x, int y, int z) {
			if (x < y) return z;
			if (y == 0)
			{
				T[z] = 0;
				return z + 1;
			}
			int q = subsets(x - 1, y - 1, z);
			for (int i = z; i < q; ++i) T[i] |= 1 << (x - 1);
			return subsets(x - 1, y, q);
		};

		for (int s = 0; s <= h; ++s)
		{
			for (int k = 0; k <= s; ++k)
			{
				int p = subsets(h - s, k, 0);
				int q = subsets(s, k, p);
				q = subsets(s, k + 1, q);
				for (int i = 0; i < p; ++i)
				{
					int b = (1 << (s + 1)) * T[i] + (1 << s);
					for (int j = p; j < q; ++j) { median_T[b + T[j]] = s; }
				}
			}
		}
		return median_T;
	}

	int down(int A, int B) { return B & (~(A | B) ^ (A + (A | ~B))); }

	void visit(int v, int S)
	{
		auto binary_search = [&](int w, int S) {
			if (S == 0) return 0;
			int j = median[S];
			while (S != 1 << j)
			{
				S &= (weight[P[j]] > w) ? ~((1 << j) - 1) : (1 << j) - 1;
				j = median[S];
			}
			return (weight[P[j]] > w) ? j : 0;
		};

		P[depth[v]] = v;
		int k = binary_search(weight[v], down(D[v], S));
		S = down(D[v], (S & (1 << ((k + 1) - 1))) | (1 << depth[v]));
		for (int i = L[v]; i >= 0; i = Lnext[i])
		{ answer[i] = P[median[down(1 << depth[upper[i]], S)]]; }
		for (int z = child[v]; z >= 0; z = sibling[z]) visit(z, S);
	}

	vector<int> compute_answer()
	{
		fill(L.begin(), L.end(), -1);
		fill(Lnext.begin(), Lnext.end(), -1);
		for (int i = 0; i < m; ++i)
		{
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
// vetor edges recebe as arestas todas as arestas do grafo, no formato (origem,
// destino, custo) vetor spanning tree recebe todas as arestas de sua spanning
// tree, que voce deseja verificar auto V = test_graph(vector<tuple<int, int,
// int>> edges, vector<tuple<int, int, int> > spanning_tree, int total_nodes);
// V.verify(); // <- retorna um booleano, e se for falso diz qual aresta eh
// contra exemplo

struct test_graph
{
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
	vector<tuple<int, int, int, int>> mst;
	vector<tuple<int, int, int, int>> G;
	LCA lca;

	test_graph(const vector<tuple<int, int, int, int>> edges,
			   const vector<tuple<int, int, int, int>> spanning_tree, const int n)
	{
		mst = spanning_tree;
		auto fbt_mst = fbt_reduction(mst, n);
		G = edges;
		WATCHC(mst);
		WATCHC(fbt_mst);
		int max_id = n;
		for (const auto& e: fbt_mst)
		{
			int a, b, c;
			tie(a, b, c, ignore) = e;
			max_id = max(max(a, b) + 1, max_id);
		}
		total_nodes = max_id;
		// This N is for LCA
		int N = total_nodes;
		// End of LCA Prep
		vector<vector<pair<int, int>>> adj_list(max_id);
		vector<vector<int>> adj(N);
		// adj.resize(N);

		child.assign(max_id, -1);
		sibling.assign(max_id, -1);
		weight.assign(max_id, -1);
		root = max_id - 1;

		for (const auto& e: fbt_mst)
		{
			int a, b, c;
			tie(a, b, c, ignore) = e;
			adj_list[a].emplace_back(b, c);
			adj_list[b].emplace_back(a, c);
		}

		function<void(int, int)> dfs_lca = [&](int node, int parent) {
			vector<int> kids;
			for (const auto& edge: adj_list[node])
			{
				int to = edge.first;
				int cost = edge.second;
				if (to != parent)
				{
					// Preparing the tree for the LCA
					adj[node].push_back(to);
					// End of preparation
					kids.push_back(to);
					weight[to] = cost;
					dfs_lca(to, node);
				}
			}
			if (kids.empty()) return;
			child[node] = kids[0];
			for (int i = 0; i < static_cast<int>(kids.size()) - 1; ++i)
			{ sibling[kids[i]] = kids[i + 1]; }
		};
		// adj_list representa garantidamente o grafo de uma full branching
		// tree, com raiz de índice = |V| - 1
		dfs_lca(root, -1);
		TRACE(cout << "iniciei o grafo" << endl;)

		// vamos imprimir ADJ
		TRACE(cout << "IMPRIMINDO AS ARESTAS DA ARVORE, CONSIDERADAS NO LCA"
				   << '\n';
			  for (int i = 0; i < max_id; ++i) { WATCHC(adj[i]); } cout
			  << "FIM DA IMPRESSAO" << '\n';);
		// aqui estou computando o LCA, supostamente em O(n)
		// precompute_lca(root);
		lca = LCA(N, adj, root);
		TRACE(cout << "precomputei o LCA" << endl;)
		// Aqui vou criar uma estrutura de LCA
	}

	// Essa funcao efetua a verificacao de fato
    // IMPORTANTE LEMBRAR, cada aresta precisa ter um peso único!
	unordered_set<int> compute_heavy_edges()
	{
		vector<int> gabarito, upper, lower, corresponding_edge;
		// LCA Prep
		TRACE(cout << "entrei em verify" << endl;)
		int M = static_cast<int>(G.size());
		int upper_len = 0;
		vector<pair<int, int>> decomposed_query;

		for (int i = 0; i < M; ++i)
		{
			int src, to, cost;
			tie(src, to, cost, ignore) = G[i];
			// Agora preciso usar a LCA
			int anc = lca.query(src, to);
			pair<int, int> qry = {-1, -1};
			if (anc != src)
			{
				upper.emplace_back(anc);
				lower.emplace_back(src);
				gabarito.emplace_back(cost);
				corresponding_edge.emplace_back(i);
				qry.first = upper_len;
				upper_len++;
			}
			if (anc != to)
			{
				upper.emplace_back(anc);
				lower.emplace_back(to);
				gabarito.emplace_back(cost);
				corresponding_edge.emplace_back(i);
				qry.second = upper_len;
				upper_len++;
			}

			if (qry.first == -1 && qry.second == -1) continue;
			else if (qry.first == -1)
				qry.first = qry.second;
			else if (qry.second == -1)
				qry.second = qry.first;

			decomposed_query.emplace_back(qry);
		}

		tree_path_maxima verifier =
			tree_path_maxima(root, child, sibling, weight, upper, lower);
		vector<int> sol = verifier.compute_answer();

		unordered_set<int> f_heavy_edges;

		for (const auto& qry: decomposed_query)
		{
			int id_fst = qry.first, id_snd = qry.second;
			int edge_cost =
				gabarito[id_fst]; // vai ser igual para os dois indices,
								  // pois eh relativo a mesma aresta
			int heavy_combine = max(weight[sol[id_fst]], weight[sol[id_snd]]);
			// Lembrar de conferir se os pesos das arestas são únicos!
			if (heavy_combine > edge_cost)
			{
				/*
				WATCH(upper[id_fst]);
				WATCH(lower[id_fst]);
				WATCH(upper[id_snd]);
				WATCH(lower[id_snd]);
				cout << "o peso da maior aresta = " << heavy_combine << '\n';
				cout << "A Spanning Tree nao é mínima!" << '\n';
				cout << "a aresta " << G[corresponding_edge[id_fst]]
					 << " deveria fazer parte dela..." << '\n';
				cout << "Na MST, o menor custo entre "
					 << get<0>(G[corresponding_edge[id_fst]]) << " e "
					 << get<1>(G[corresponding_edge[id_fst]]) << " = "
					 << heavy_combine << '\n';
				return false;
				*/
			}
			// TODA ARESTA DEVE TER CUSTO UNICO! OU PRECISO SOBREESCREVER O
			// OPERADOR < para os custos...
			if (heavy_combine < edge_cost)
			{ 
                int edge_id = get<3>(G[corresponding_edge[id_fst]]);
                f_heavy_edges.insert(edge_id);
            }
		}
		return f_heavy_edges;
	}
};

unordered_set<int>
	verify_mst(const vector<tuple<int, int, int, int>>& graph,
			   const vector<tuple<int, int, int, int>>& spanning_tree, const int n)
{
	auto verifier = test_graph(graph, spanning_tree, n);
	return verifier.compute_heavy_edges();
}

unordered_set<int> verify_general_graph(const vector<tuple<int, int, int, int>>& graph,
						 const vector<tuple<int, int, int, int>>& general_graph,
						 const int n)
{
	int total_number_of_edges = static_cast<int>(general_graph.size());

	// Garantindo que estamos lidando com uma árvore, ou floresta..
	assert(total_number_of_edges <= n - 1);

	if (static_cast<int>(general_graph.size()) == n - 1)
	{
		// Entao o grafo é necessariamente uma árvore!
		return verify_mst(graph, general_graph, n);
	}

	// Agora preciso lidar com o caso do grafo ser uma floresta
	int next_id = 0;
	vector<int> connected_component_id(n, -1);

	vector<vector<int>> gg_adj_list(n);
	for (const auto& edg : general_graph)
	{
		int from, to;
		tie(from, to, ignore, ignore) = edg;
		gg_adj_list[from].push_back(to);
		gg_adj_list[to].push_back(from);
	}

	function<void(int, int)> compute_cc = [&](int root, int parent) {
		if (parent == -1) connected_component_id[root] = next_id++;
		else
			connected_component_id[root] = connected_component_id[parent];

		for (const auto& viz: gg_adj_list[root])
		{
			if (connected_component_id[viz] == -1) { compute_cc(viz, root); }
		}
	};

	for (int i = 0; i < n; ++i)
	{
		if (connected_component_id[i] == -1) { compute_cc(i, -1); }
	}

	vector<vector<int>> connected_components(next_id);
	vector<int> next_id_by_component(next_id, 0);
	vector<vector<tuple<int, int, int, int>>> spanning_tree(next_id);
	vector<vector<tuple<int, int, int, int>>> subgraph(next_id);
	unordered_map<int, int> node_mapping;

	for (int i = 0; i < n; ++i)
	{
		connected_components[connected_component_id[i]].push_back(i);
		int new_id = next_id_by_component[connected_component_id[i]]++;
		node_mapping[i] = new_id;
	}

	// Estou quebrando a floresta em sub-árvores
	for (const auto& edg : general_graph)
	{
		int from, to, cost, id;
		tie(from, to, cost, id) = edg;
		// Só vamos rodar a vericação para arestas entre vértices que estão na
		// mesma componente. Caso contrário, a aresta nunca vai ser F-heavy,
		// porque F(from, to) = inf (pertencem a componentes diferentes)
		if (connected_component_id[from] == connected_component_id[to])
		{
			spanning_tree[connected_component_id[from]].emplace_back(
				node_mapping[from], node_mapping[to], cost, id);
		}
	}

	for (const auto& edg : graph)
	{
		int from, to, cost, id;
		tie(from, to, cost, id) = edg;

		if (connected_component_id[from] == connected_component_id[to])
		{
			subgraph[connected_component_id[from]].emplace_back(
				node_mapping[from], node_mapping[to], cost, id);
		}
	}

    unordered_set<int> f_heavy_edges;

	for (int i = 0; i < next_id; ++i)
	{
		auto V =
			verify_mst(subgraph[i], spanning_tree[i], next_id_by_component[i]);
		for (const auto& edg_id : V)
		{
            f_heavy_edges.insert(edg_id);
		}
	}

	return f_heavy_edges;
}