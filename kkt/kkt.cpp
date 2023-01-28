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

// Debugging macros and functions
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
// End of useful debugging macros and functions

// Useful hashing templates
template <typename T> inline void hash_combine(std::size_t& seed, const T& val)
{
	seed ^= std::hash<T>()(val) + 0x9e3779b9 + (seed << 6) + (seed >> 2);
}

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
// End of hashing related templates

// This function applies the Boruvka Step described by the Karger-Klein-Tarjan
// paper. The idea of this step is to reduce the number of vertices of the
// graph. It guarantees that the number of vertices after the step is <= N / 2.
// It returns the reduced problem and the id's of the edges that were contracted
// in the current step.
// Assumptions: The graph P.graph_edges is connected.
// Complexity: O(n + m)
pair<unordered_set<int>, problem> boruvka_step(const problem& P)
{
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

	vector<bool> used(total_edges, false);
	unordered_set<int> used_edges;

	vector<vector<int>> component_graph(n);

	int cost_for_used_edges = 0;

	// Building the component graph, a graph formed by each node and the
	// edge incident to it that has the smallest cost
	for (int i = 0; i < n; ++i)
	{
		if (smallest_incident_edge[i] == -1) continue;
		used[smallest_incident_edge[i]] = true;
		int from, to, cost;
		tie(from, to, cost, ignore) = P.graph_edges[smallest_incident_edge[i]];
		component_graph[from].push_back(to);
		component_graph[to].push_back(from);

		// watch out for overflow
		cost_for_used_edges += cost;
		used_edges.insert(get<3>(P.graph_edges[smallest_incident_edge[i]]));
	}

	// Here a few important things are performed
	// 1 - Removal of isolated super-nodes. As described by the KKT paper.
	// 2 - If there are multiple edges between two supernodes, we will
	//     only store the cheapest one.

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

	int next_non_isolated_id = 0;
	for (int i = 0; i < next_component_id; ++i)
	{
		if (super_node_degree[i] > 0)
		{ super_node_new_id[i] = next_non_isolated_id++; }
	}

	vector<tuple<int, int, int, int>> remaining_problem_edges;

	unordered_map<pair<int, int>, int, pair_hash> minimal_edge;

	for (int i = 0; i < total_edges; ++i)
	{
		int from, to, cost, id;
		tie(from, to, cost, id) = P.graph_edges[i];
		if (used_edges.find(id) != used_edges.end()) continue;
		if (super_node_id[from] != super_node_id[to])
		{
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

// Function that removes isolated vertices from the graph.
// Complexity: O(n + m)
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
	if (min_degree > 0) return P;

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

// This function selects edges of P.graph_edges with probability 1/2.
// It is a key part of the KKT algorithm and it is described on the paper.
problem random_sampling(problem& P, unsigned int seed = 0)
{
	srand(seed);
	vector<tuple<int, int, int, int>> H;
	for (const auto& E: P.graph_edges)
	{
		int b = (rand() & 1);
		if (b) H.push_back(E);
	}

	problem P_H = problem(P.num_vertices, H);
	return remove_isolated_vertices(P_H);
}

// Utility function for getting the accumulated cost of the solution
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

// Utility function for printing the graph
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

vector<tuple<int, int, int, int>>
	get_mst_edges_from_problem(const unordered_set<int>& mst_id,
							   const problem& P)
{
	vector<tuple<int, int, int, int>> MST;
	for (const auto& idx: mst_id) { MST.push_back(P.graph_edges[idx]); }
	return MST;
}

// Performs the KKT algorithm, using the Hagerup verification proposal.
unordered_set<int> kkt(problem& P, unsigned int seed)
{
	unordered_set<int> result;
	if (P.graph_edges.empty()) { return result; }
	// Apply Boruvka Step (twice)
	auto boruvka_first = boruvka_step(problem(P.num_vertices, P.graph_edges));
	for (const auto& val: boruvka_first.first) result.insert(val);
	problem& reduced = boruvka_first.second;

	if (reduced.graph_edges.empty() || reduced.num_vertices == 0)
	{ return result; }

	auto boruvka_second =
		boruvka_step(problem(reduced.num_vertices, reduced.graph_edges));
	for (const auto& val: boruvka_second.first) result.insert(val);
	if (boruvka_second.second.num_vertices == 0 ||
		boruvka_second.second.graph_edges.empty())
	{ return result; }

	// G corresponds to the initial graph, after applying the boruvka_step twice
	problem G = boruvka_second.second;

	// H selects edge from G with edge probability = 1/2
	problem H = random_sampling(G, seed);

	unordered_set<int> kkt_h = kkt(H, seed);

	// KKT_H will return the indices of the minimum spanning forest edges.
	vector<tuple<int, int, int, int>> H_MSF;
	for (const auto& E: G.graph_edges)
	{
		if (kkt_h.find(get<3>(E)) != kkt_h.end()) { H_MSF.push_back(E); }
	}

	// Given H_MST, we will now find all the edges from G that are H_MST-heavy.
	// As described on the KKT paper.
	auto G_heavy = verify2_general_graph(G.graph_edges, H_MSF, G.num_vertices);

	// Now we are filtering only the edges from G that are not H_MST-heavy.
	vector<tuple<int, int, int, int>> relevant_edges;
	for (const auto& E: G.graph_edges)
	{
		if (G_heavy.find(get<3>(E)) == G_heavy.end())
		{ relevant_edges.emplace_back(E); }
	}

	problem P_G = problem(G.num_vertices, relevant_edges);
	problem G_remaining = remove_isolated_vertices(P_G);

	// And now we apply kkt to the remaining graph in a recursive manner.
	unordered_set<int> g_res = kkt(G_remaining, seed);
	for (const auto& val: g_res) result.insert(val);

	return result;
}
