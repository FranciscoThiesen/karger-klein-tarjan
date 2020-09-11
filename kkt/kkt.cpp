#include "kkt.hpp"
#include "../verifier/verifier_v2.hpp"
#include <algorithm>
#include <cassert>
#include <functional>
#include <iostream>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

// Isso aqui é apenas uma implementação inicial
// Nessa versão, não vou me preocupar com encontrar a MST em si, estou
// satisfeito em encontrar apenas o custo

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

// Templates úteis para hashing de pares
template <typename T> inline void hash_combine(std::size_t& seed, const T& val)
{
	seed ^= std::hash<T>()(val) + 0x9e3779b9 + (seed << 6) + (seed >> 2);
}
// auxiliary generic functions to create a hash value using a seed
template <typename T> inline void hash_val(std::size_t& seed, const T& val)
{
	hash_combine(seed, val);
}
template <typename T, typename... Types>
inline void hash_val(std::size_t& seed, const T& val, const Types&... args)
{
	hash_combine(seed, val);
	hash_val(seed, args...);
}

template <typename... Types> inline std::size_t hash_val(const Types&... args)
{
	std::size_t seed = 0;
	hash_val(seed, args...);
	return seed;
}

struct pair_hash
{
	template <class T1, class T2>
	std::size_t operator()(const std::pair<T1, T2>& p) const
	{
		return hash_val(p.first, p.second);
	}
};
// Fim dos templates de hashing

// Essa função vai aplicar o passo Boruvka, descrito no paper do KKT. A ideia é
// diminuir a quantidade de vértices pela metade, ainda em tempo linear.

// Se eu quiser retornar as arestas utilizadas, preciso pensar em manter para
// cada nó, qual super-nó ele pertence.. Mesmo que as extremidades das arestas
// mudem ao longo do tempo, posso manter um índice que permite que cada aresta
// da MST seja mapeada para alguma das arestas originais.
pair<unordered_set<int>, problem> boruvka_step(problem P)
{
	TRACE(cout << "chamamos o Boruvka!" << endl;)
	// Assume-se que o grafo recebido aqui é CONEXO!!!!
	// implementar!
	// Aqui, preciso retornar o grafo resultante e também as arestas que foram
	// utilizadas!

	int n = P.num_vertices;

	vector<int> smallest_incident_edge(n, -1);
	int total_edges = static_cast<int>(P.graph_edges.size());

	for (int i = 0; i < total_edges; ++i)
	{
		int from, to, cost;
		tie(from, to, cost, ignore) = P.graph_edges[i];
		if (smallest_incident_edge[from] == -1 ||
			cost < get<2>(P.graph_edges[smallest_incident_edge[from]]))
		{ smallest_incident_edge[from] = i; }
		if (smallest_incident_edge[to] == -1 ||
			cost < get<2>(P.graph_edges[smallest_incident_edge[to]]))
		{ smallest_incident_edge[to] = i; }
	}

	TRACE(for (int i = 0; i < n; ++i)
	{
		cout << "custo da menor aresta incidindo em " << i << " => "
			 << get<2>(P.graph_edges[smallest_incident_edge[i]]) << endl;
	});

	vector<bool> used(total_edges, false);
	unordered_set<int> used_edges;

	vector<vector<int>> component_graph(n);

	int cost_for_used_edges = 0;

	for (int i = 0; i < n; ++i)
	{
		if (smallest_incident_edge[i] == -1) continue;
		used[smallest_incident_edge[i]] = true;
		int from, to, cost;
		tie(from, to, cost, ignore) = P.graph_edges[smallest_incident_edge[i]];
		component_graph[from].push_back(to);
		component_graph[to].push_back(from);

		// Se tiver algum problema, é necessário se certificar que não ocorre
		// overflow aqui!
		cost_for_used_edges += cost;
		used_edges.insert(get<3>(P.graph_edges[smallest_incident_edge[i]]));
	}

	// Agora são feitos os passos mais importantes
	// 1 - Remoção de super-nós isolados
	// 2 - Se existem múltiplas arestas entre os mesmos dois super-componentes,
	// queremos manter apenas a menor! 3 - Remover self-loops que ligam um
	// super-nó em si mesmo

	int next_component_id = 0;
	vector<int> super_node_id(n, -1);

	function<void(int, int)> dfs = [&](int root, int parent) {
		if (parent == -1) super_node_id[root] = next_component_id++;
		else
			super_node_id[root] = super_node_id[parent];

		for (const auto& viz: component_graph[root])
		{
			if (super_node_id[viz] == -1) { dfs(viz, root); }
		}
	};

	for (int i = 0; i < n; ++i)
		if (super_node_id[i] == -1) dfs(i, -1);

	vector<int> super_node_degree(next_component_id, 0);
	vector<int> super_node_new_id(next_component_id, 0);

	for (int i = 0; i < total_edges; ++i)
	{
		int from, to, cost;
		tie(from, to, cost, ignore) = P.graph_edges[i];
		if (super_node_id[from] != super_node_id[to])
		{
			super_node_degree[super_node_id[from]]++;
			super_node_degree[super_node_id[to]]++;
		}
	}

	// Agora, vou remapear os super-nós. Isso vai permitir remover do problema
	// os super_node isolados!
	int next_non_isolated_id = 0;
	for (int i = 0; i < next_component_id; ++i)
	{
		if (super_node_degree[i] > 0)
		{
			// Agora, o que vou fazer é mudar o índice desse componente... Nova
			// numeração exclui os isolados!
			super_node_new_id[i] = next_non_isolated_id++;
		}
	}

	vector<tuple<int, int, int, int>> remaining_problem_edges;

	// Agora, quero apenas guardar qual é a aresta mais barata entre
	// supercomponentes. Para manter o tempo esperado linear, preciso usar
	// hash_table para isso
	unordered_map<pair<int, int>, int, pair_hash> minimal_edge;

	for (int i = 0; i < total_edges; ++i)
	{
		int from, to, cost, id;
		tie(from, to, cost, id) = P.graph_edges[i];
		if (used_edges.find(id) != used_edges.end()) continue;
		if (super_node_id[from] != super_node_id[to])
		{
			// vamos construir essa aresta no grafo novo!
			int f = super_node_new_id[super_node_id[from]];
			int t = super_node_new_id[super_node_id[to]];
			if (f > t) swap(f, t);
			if (minimal_edge.count(make_pair(f, t)) == 0)
				minimal_edge[make_pair(f, t)] = i;
			else
			{
				int current_cost =
					get<2>(P.graph_edges[minimal_edge[make_pair(f, t)]]);
				if (cost < current_cost) { minimal_edge[make_pair(f, t)] = i; }
			}
		}
	}

	for (const auto& E: minimal_edge)
	{
		int from, to, cost, id;
		tie(from, to, cost, id) = P.graph_edges[E.second];
		remaining_problem_edges.emplace_back(E.first.first, E.first.second,
											 cost, id);
	}

	problem remaining_problem =
		problem(next_non_isolated_id, remaining_problem_edges);

	return make_pair(used_edges, remaining_problem);
}

// Remoção de vértices isolados. Isso é um passo necessário para o KKT
problem remove_isolated_vertices(const problem& P)
{
	int prev_size = P.num_vertices;
	vector<int> degree(prev_size, 0);
	vector<vector<int>> g(prev_size);

	for (const auto& e: P.graph_edges)
	{
		int from, to;
		tie(from, to, ignore, ignore) = e;
		degree[from]++;
		degree[to]++;
		g[from].push_back(to);
		g[to].push_back(from);
	}

	int min_degree = *(min_element(degree.begin(), degree.end()));
	if (min_degree > 0) return P; // nao tem vertice isolado

	int next_id = 0;
	vector<int> new_node_id(prev_size, -1);
	for (int i = 0; i < prev_size; ++i)
	{
		if (degree[i]) { new_node_id[i] = next_id++; }
	}

	vector<tuple<int, int, int, int>> new_edges;
	for (const auto& e: P.graph_edges)
	{
		int from, to, cost, id;
		tie(from, to, cost, id) = e;
		new_edges.emplace_back(new_node_id[from], new_node_id[to], cost, id);
	}
	return problem(next_id, new_edges);
}

// Seleciona arestas de G com probabilidade = 1/2. Esse processo é descrito no
// paper do KKT, onde essa etapa é chamada de Random Sampling.
problem random_sampling(problem& P)
{
    srand(0);
	vector<tuple<int, int, int, int>> H;
	for (const auto& E: P.graph_edges)
	{
		int b = (rand() & 1);
		if (b) H.push_back(E);
	}

	problem P_H = problem(P.num_vertices, H);
	return remove_isolated_vertices(P_H);
}

int get_solution_cost(const problem& P, const unordered_set<int>& used)
{
	int res = 0;
	for (const auto& E: P.graph_edges)
	{
		int id = get<3>(E);
		if (used.find(id) != used.end()) { res += get<2>(E); }
	}
	return res;
}

inline void print_problem(const problem& X)
{
	cout << "Impressao do problema: " << endl;
	cout << "num_vertices = " << X.num_vertices << endl;
	cout << "arestas do problema = [ " << endl;
	for (const auto& E: X.graph_edges)
	{
		int from, to, cost, id;
		tie(from, to, cost, id) = E;
		cout << from << " " << to << " " << cost << " " << id << endl;
	}
	cout << "]" << endl << endl;
}

// Retorna o custo da minimum-spanning-tree, em tempo esperado linear.
// Seguindo o processo descrito pelo paper KKT.
unordered_set<int> kkt(problem& P)
{
	cout << "Chamada de KKT" << endl;
	print_problem(P);

	unordered_set<int> result;
	if (P.graph_edges.empty())
	{
		cout << "0 - MST/F cost = 0" << endl;
		return result;
	}
	// Apply Boruvka Step (twice)
	auto boruvka_first = boruvka_step(problem(P.num_vertices, P.graph_edges));
	for (const auto& val: boruvka_first.first) result.insert(val);
	problem& reduced = boruvka_first.second;

	int total_cost = 0;
	TRACE(cout << "Chamei o boruvka pela primeira vez" << endl;)
	if (reduced.graph_edges.empty() || reduced.num_vertices == 0)
	{
		// seria legal calcular a soma dos custos antes de retornar..
		for (const auto& v: P.graph_edges)
		{
			if (result.find(get<3>(v)) != result.end())
			{ total_cost += get<2>(v); }
		}
        cout << "1 - MST/F cost = " << total_cost;
		return result;
	}
	TRACE(cout << "Após o primeiro boruvka, temos " << endl;)
	TRACE(print_problem(reduced);)

	TRACE(cout << "Chamei o boruvka pela segunda vez" << endl;)
	auto boruvka_second =
		boruvka_step(problem(reduced.num_vertices, reduced.graph_edges));
	for (const auto& val: boruvka_second.first) result.insert(val);
	if (boruvka_second.second.num_vertices == 0 ||
		boruvka_second.second.graph_edges.empty())
	{
		for (const auto& e: P.graph_edges)
		{
			int id = get<3>(e);
			if (result.find(id) != result.end()) { total_cost += get<2>(e); }
		}
		cout << "2 - MST/F cost = " << total_cost << endl;
		return result;
	}
	// Problema reduzido após 2 passos do boruvka

	problem G = boruvka_second.second;
	TRACE(cout << "Problema que sobrou, após aplicar 2 boruvkas!" << endl;)
	print_problem(G);

	TRACE(cout << endl << "Vou gerar H, via random_sampling" << endl;)
	// Processo de random sampling
	problem H = random_sampling(G);

	TRACE(print_problem(H);)
	
	TRACE(cout << "imprimi H " << endl;)
	assert(P != H);

	unordered_set<int> kkt_h = kkt(H);

	TRACE(cout << "Vamos imprimir o resultado de KKT(H)" << endl;)
	vector<tuple<int, int, int, int>> H_MSF;
	for (const auto& E: G.graph_edges)
	{
		if (kkt_h.find(get<3>(E)) != kkt_h.end())
		{
			int a, b, c, d;
			tie(a, b, c, d) = E;
			cout << a << " " << b << " " << c << " " << d << endl;
			H_MSF.push_back(E);
		}
	}
	TRACE(cout << endl << endl;)

	auto G_heavy = verify_general_graph(G.graph_edges, H_MSF, G.num_vertices);
	TRACE(cout << "Arestas de G = " << endl;)
	for (const auto& e: G.graph_edges)
	{
		int a, b, c, d;
		tie(a, b, c, d) = e;
		cout << a << " " << b << " " << c << " " << d << endl;
	}
	TRACE(cout << endl;)
	TRACE(cout << "Arestas de H = " << endl;)
	for (const auto& e: H_MSF)
	{
		int a, b, c, d;
		tie(a, b, c, d) = e;
		cout << a << " " << b << " " << c << " " << d << endl;
	}
	TRACE(cout << endl << endl;)

	TRACE(cout << "imprimindo heavy-edges" << endl;)

	TRACE(
		for (const auto& v: G_heavy) cout << v << endl;
	cout << endl << endl;);
	// Agora temos que remover todas essas arestas pesadas de G

	vector<tuple<int, int, int, int>> relevant_edges;
	for (const auto& E: G.graph_edges)
	{
		if (G_heavy.find(get<3>(E)) == G_heavy.end())
		{ relevant_edges.emplace_back(E); }
	}

	problem P_G = problem(G.num_vertices, relevant_edges);
	problem G_remaining = remove_isolated_vertices(P_G);

	unordered_set<int> g_res = kkt(G_remaining);
	for (const auto& val: g_res) result.insert(val);

	// Agora vamos imprimir a MST (:
	for (const auto& E: P.graph_edges)
	{
		if (result.find(get<3>(E)) != result.end())
		{
			int from, to, cost, id;
			tie(from, to, cost, id) = E;
			// cout << "usamos a aresta = (" << from << ", " << to << ", " <<
			// cost << ")" << endl;
			total_cost += cost;
		}
	}

	cout << endl << endl << "3 - custo total da MST/F = " << total_cost << endl;

	return result;
}
