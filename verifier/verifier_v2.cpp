// OBSERVACAO IMPORTANTE
// DO JEITO QUE ESTA, essa verificação SÓ FUNCIONA SE OS PESOS DAS ARESTAS FOREM
// ÚNICOS!!!!!

#include "verifier_v2.hpp"
#include "median_table.hpp"
#include "../common/work_stats.hpp"
// #include "../boruvka/boruvka.hpp"
// #include "../graph_utils/graph_utils.hpp"
// #include "../kruskal/kruskal.hpp"
#include "../lca/lca.hpp"
// #include "../prim/prim.hpp"
// #include "../union_find/union_find.hpp"

#include <cassert>
#include <iostream>
#include <limits>
#include <numeric>
#include <tuple>
#include <utility>
#include <vector>

using namespace std;

// A few macros and functions that are useful for debugging
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
// End of debugging macros and functions

// This function reduces any tree graph to a full branching tree version of it.
// Such reduction is made performing a strategy similar to the Boruvka
// algorithm. It is guaranteed that the size of the generated full branching
// tree has at most O(2 * n) vertices. Assumptions: We receive the edges of a
// proper Spanning Tree Complexity: O(n)
vector<tuple<int, int, int, int>>
	fbt_reduction(const vector<tuple<int, int, int, int>>& edges,
				  int total_nodes)
{
	KKT_WORK_ADD(fbt_calls, 1);
	KKT_WORK_ADD(fbt_input_vertices, total_nodes);
	KKT_WORK_ADD(edge_materializations, edges.size());
	vector<tuple<int, int, int, int>> active_edges = edges;
	vector<int> component_list(total_nodes);
	KKT_WORK_ADD(initialized_slots, total_nodes);
	KKT_WORK_ADD(fbt_vertex_visits, total_nodes);
	iota(component_list.begin(), component_list.end(), 0);

	// Every contraction creates fresh IDs, and a full branching tree has
	// fewer than 2n nodes. An ID is active in just one round, so these dense
	// arrays need no per-round clearing or hashing.
	const size_t capacity = 2 * static_cast<size_t>(total_nodes);
	vector<int> cheapest_edge(capacity, -1);
	vector<int> super_node_id(capacity, -1);
	vector<vector<int>> current_graph(capacity);
	KKT_WORK_ADD(initialized_slots, 3 * capacity);
	vector<int> dfs_stack;
	vector<tuple<int, int, int, int>> new_edges;
	new_edges.reserve(capacity);
	int prox_node_id = total_nodes;

	while (component_list.size() > 1)
	{
		KKT_WORK_ADD(fbt_rounds, 1);
		KKT_WORK_ADD(fbt_round_vertices, component_list.size());
		KKT_WORK_ADD(fbt_round_edges, active_edges.size());
		KKT_WORK_ADD(fbt_edge_visits, 2 * active_edges.size());
		KKT_WORK_ADD(fbt_vertex_visits, 3 * component_list.size());
		for (int i = 0; i < static_cast<int>(active_edges.size()); ++i)
		{
			int from, to, cost;
			tie(from, to, cost, ignore) = active_edges[i];
			if (cheapest_edge[from] == -1 ||
				cost < get<2>(active_edges[cheapest_edge[from]]))
				cheapest_edge[from] = i;
			if (cheapest_edge[to] == -1 ||
				cost < get<2>(active_edges[cheapest_edge[to]]))
				cheapest_edge[to] = i;
		}

		for (int node: component_list)
		{
			const auto& edge = active_edges[cheapest_edge[node]];
			int from = get<0>(edge), to = get<1>(edge);
			current_graph[from].push_back(to);
			current_graph[to].push_back(from);
		}

		vector<int> new_component_ids;
		new_component_ids.reserve(component_list.size() / 2);
		for (int start_id: component_list)
		{
			if (super_node_id[start_id] != -1) continue;
			int new_id = prox_node_id++;
			new_component_ids.push_back(new_id);
			super_node_id[start_id] = new_id;
			dfs_stack.push_back(start_id);
			while (!dfs_stack.empty())
			{
				int node = dfs_stack.back();
				dfs_stack.pop_back();
				KKT_WORK_ADD(fbt_vertex_visits, 1);
				for (int next: current_graph[node])
				{
					KKT_WORK_ADD(fbt_arc_visits, 1);
					if (super_node_id[next] != -1) continue;
					super_node_id[next] = new_id;
					dfs_stack.push_back(next);
				}
			}
		}

		for (int node: component_list)
		{
			const auto& edge = active_edges[cheapest_edge[node]];
			new_edges.emplace_back(node, super_node_id[node],
								   get<2>(edge), get<3>(edge));
			KKT_WORK_ADD(edge_materializations, 1);
		}

		vector<tuple<int, int, int, int>> relevant_edges;
		relevant_edges.reserve(new_component_ids.size() - 1);
		for (const auto& e: active_edges)
		{
			int from, to, cost, id;
			tie(from, to, cost, id) = e;
			if (super_node_id[from] != super_node_id[to])
			{
				relevant_edges.emplace_back(super_node_id[to],
											 super_node_id[from], cost, id);
				KKT_WORK_ADD(edge_materializations, 1);
			}
		}
		active_edges = std::move(relevant_edges);
		component_list = std::move(new_component_ids);
	}

	// Returning edges of the generated full-branching tree
	KKT_WORK_ADD(fbt_output_vertices, prox_node_id);
	return new_edges;
}

// Implementation of the tree_path_maxima problem solver.
// It is completely based on the D code that Torben
// Hagerup made available in his 2009 paper. It answers multiple queries and
// each query provides two nodes (a,b) and asks for the maximum edge
// on the path from (a, b) on the tree! (This is why it is called the
// tree-path-maxima problem)
//
// Queries are grouped by their lower endpoint in contiguous ranges. Each
// record stores its upper endpoint and the graph edge whose path it probes.
// Combining its one or two ancestor paths writes one maximum per graph edge.
// As before, the tree is full-branching and every query upper endpoint is a
// proper ancestor of the node whose range contains it.
//
// Complexity: O(n + m)
struct path_query {
	int upper, edge;
};

struct tree_path_maxima
{
	int height, n, root;
	vector<int> depth, D, maximum, median, P;
	const vector<size_t>& query_offsets;
	const vector<path_query>& queries;
	const vector<int>& child;
	const vector<int>& sibling;
	const vector<int>& weight;

	tree_path_maxima(int _root, const vector<int>& _child,
					 const vector<int>& _sibling, const vector<int>& _weight,
					 const vector<size_t>& _query_offsets,
					 const vector<path_query>& _queries, size_t graph_edges)
		: height(0), n(static_cast<int>(_child.size())),
		  root(_root), depth(n, 0), D(n, 0),
		  maximum(graph_edges, numeric_limits<int>::lowest()),
		  query_offsets(_query_offsets), queries(_queries), child(_child),
		  sibling(_sibling), weight(_weight)
	{
		KKT_WORK_ADD(initialized_slots, 2ULL * n + graph_edges);
	}

	void init(int u, int d)
	{
		KKT_WORK_ADD(path_init_vertices, 1);
		depth[u] = d;
		if (d > height) height = d;
		for (size_t i = query_offsets[u]; i < query_offsets[u + 1]; ++i) {
			KKT_WORK_ADD(path_query_visits, 1);
			D[u] |= 1 << depth[queries[i].upper];
		}
		for (int v = child[u]; v >= 0; v = sibling[v])
		{
			init(v, d + 1);
			D[u] |= D[v] & ~(1 << d);
		}
	}

	int down(int A, int B) { return B & (~(A | B) ^ (A + (A | ~B))); }

	void visit(int v, int S)
	{
		KKT_WORK_ADD(path_visit_vertices, 1);
		auto binary_search = [&](int w, int S) {
			KKT_WORK_ADD(path_binary_search_calls, 1);
			if (S == 0) return 0;
			int j = median[S];
			while (S != 1 << j)
			{
				KKT_WORK_ADD(path_binary_search_steps, 1);
				S &= (weight[P[j]] > w) ? ~((1 << j) - 1) : (1 << j) - 1;
				j = median[S];
			}
			return (weight[P[j]] > w) ? j : 0;
		};

		P[depth[v]] = v;
		int k = binary_search(weight[v], down(D[v], S));
		S = down(D[v], (S & ((1 << (k + 1)) - 1)) | (1 << depth[v]));
		for (size_t i = query_offsets[v]; i < query_offsets[v + 1]; ++i)
		{
			KKT_WORK_ADD(path_query_visits, 1);
			const auto& query = queries[i];
			const int node = P[median[down(1 << depth[query.upper], S)]];
			maximum[query.edge] = max(maximum[query.edge], weight[node]);
		}
		for (int z = child[v]; z >= 0; z = sibling[z]) visit(z, S);
	}

	const vector<int>& compute_answer()
	{
		init(root, 0);
		P = vector<int>(height + 1, 0);
		KKT_WORK_ADD(initialized_slots, height + 1);
		KKT_WORK_MAX(path_max_height, height);
		median = verifier_detail::median_table(height);
		visit(root, 0);
		return maximum;
	}
};

// This test_graph structure makes use of the tree_path_maxima for verifying
// a minimum spanning tree in linear time.
//
// Assumptions: It receives a vector of graph edges in the format
// (from, to, cost, id) and a spanning tree, using the same edge convention.
// It returns whether that spanning tree is a minimum spanning tree or not.
//
// Complexity: O(n + m)
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
	const vector<tuple<int, int, int, int>>& G;
	LCA lca;

	test_graph(const vector<tuple<int, int, int, int>>& edges,
			   const vector<tuple<int, int, int, int>>& spanning_tree,
			   const int n) : G(edges)
	{
		auto fbt_mst = fbt_reduction(spanning_tree, n);
		KKT_WORK_ADD(verifier_edge_visits, 2 * fbt_mst.size());
		// Each tuple already records child -> parent, and fresh parent IDs
		// increase monotonically. The last parent is therefore the root.
		total_nodes = n;
		for (const auto& e: fbt_mst)
			total_nodes = max(total_nodes, get<1>(e) + 1);
		root = total_nodes - 1;
		child.assign(total_nodes, -1);
		sibling.assign(total_nodes, -1);
		weight.assign(total_nodes, -1);
		vector<vector<int>> adj(total_nodes);
		KKT_WORK_ADD(initialized_slots, 4ULL * total_nodes);
		for (const auto& e: fbt_mst)
		{
			int node, parent, cost;
			tie(node, parent, cost, ignore) = e;
			sibling[node] = child[parent];
			child[parent] = node;
			weight[node] = cost;
			adj[parent].push_back(node);
		}
		lca = LCA(total_nodes, adj, root);
	}

	// This functions return all the F-heavy edges of a graph taking into
	// account the weights of some spanning tree, this is precisely
	// explained on the Karger-Klein-Tarjan' 1995 paper.
	vector<unsigned char> compute_heavy_marks()
	{
		int M = static_cast<int>(G.size());
		vector<size_t> query_offsets(static_cast<size_t>(total_nodes) + 1, 0);
		vector<path_query> queries;
		KKT_WORK_ADD(initialized_slots, query_offsets.size());
		{
			// Retain one LCA per graph edge while building its endpoint ranges.
			// This temporary is released before either tree traversal starts.
			vector<int> ancestors(G.size());
			KKT_WORK_ADD(initialized_slots, ancestors.size());
			KKT_WORK_ADD(verifier_edge_visits, G.size());
			for (int i = 0; i < M; ++i) {
				const int from = get<0>(G[i]), to = get<1>(G[i]);
				const int ancestor = ancestors[i] = lca.query(from, to);
				if (ancestor != from) {
					++query_offsets[from + 1];
					KKT_WORK_ADD(path_query_visits, 1);
				}
				if (ancestor != to) {
					++query_offsets[to + 1];
					KKT_WORK_ADD(path_query_visits, 1);
				}
			}
			KKT_WORK_ADD(verifier_vertex_visits, total_nodes);
			for (int i = 1; i <= total_nodes; ++i)
				query_offsets[i] += query_offsets[i - 1];
			queries.resize(query_offsets.back());
			KKT_WORK_ADD(initialized_slots, queries.size());
			vector<size_t> next_query = query_offsets;
			KKT_WORK_ADD(initialized_slots, next_query.size());
			KKT_WORK_ADD(verifier_edge_visits, G.size());
			for (int i = 0; i < M; ++i) {
				const int from = get<0>(G[i]), to = get<1>(G[i]);
				const int ancestor = ancestors[i];
				if (ancestor != from) {
					queries[next_query[from]++] = {ancestor, i};
					KKT_WORK_ADD(path_query_visits, 1);
				}
				if (ancestor != to) {
					queries[next_query[to]++] = {ancestor, i};
					KKT_WORK_ADD(path_query_visits, 1);
				}
			}
		}

		KKT_WORK_ADD(verifier_queries, queries.size());
		tree_path_maxima verifier(root, child, sibling, weight,
							  query_offsets, queries, G.size());
		const vector<int>& sol = verifier.compute_answer();
		vector<unsigned char> heavy_marks(G.size(), 0);
		KKT_WORK_ADD(initialized_slots, heavy_marks.size());

		KKT_WORK_ADD(verifier_edge_visits, G.size());
		for (int i = 0; i < M; ++i)
		{
			// A self-loop produced no ancestor query in the previous layout;
			// preserve its unmarked result instead of reading an empty path.
			if (get<0>(G[i]) != get<1>(G[i]) && sol[i] < get<2>(G[i]))
				heavy_marks[i] = 1;
		}
		return heavy_marks;
	}
};

namespace {

vector<unsigned char>
	verify_tree_marks(const vector<tuple<int, int, int, int>>& graph,
					  const vector<tuple<int, int, int, int>>& spanning_tree,
					  const int n)
{
	if (n == 0 || graph.empty() || spanning_tree.empty()) {
		KKT_WORK_ADD(initialized_slots, graph.size());
		return vector<unsigned char>(graph.size(), 0);
	}
	KKT_WORK_ADD(verifier_tree_calls, 1);
	KKT_WORK_ADD(verifier_tree_vertices, n);
	KKT_WORK_ADD(verifier_tree_edges, graph.size());
	auto verifier = test_graph(graph, spanning_tree, n);
	return verifier.compute_heavy_marks();
}

unordered_set<int>
	heavy_edge_ids(const vector<tuple<int, int, int, int>>& graph,
				   const vector<unsigned char>& marks)
{
	unordered_set<int> result;
	KKT_WORK_ADD(verifier_edge_visits, graph.size());
	for (size_t i = 0; i < graph.size(); ++i) {
		if (!marks[i]) continue;
		result.insert(get<3>(graph[i]));
		KKT_WORK_ADD(hash_insert_items, 1);
	}
	return result;
}

}  // namespace

unordered_set<int>
	verify_mst(const vector<tuple<int, int, int, int>>& graph,
			   const vector<tuple<int, int, int, int>>& spanning_tree,
			   const int n)
{
	return heavy_edge_ids(graph, verify_tree_marks(graph, spanning_tree, n));
}

vector<unsigned char>
	verifier_detail::heavy_edge_marks(const vector<tuple<int, int, int, int>>& graph,
									 const vector<tuple<int, int, int, int>>& general_graph,
									 const int n)
{
	KKT_WORK_ADD(verifier_calls, 1);
	KKT_WORK_ADD(verifier_vertices, n);
	KKT_WORK_ADD(verifier_edges, graph.size());
	KKT_WORK_ADD(verifier_forest_edges, general_graph.size());
	if (n == 0 || graph.empty() || general_graph.empty()) {
		KKT_WORK_ADD(initialized_slots, graph.size());
		return vector<unsigned char>(graph.size(), 0);
	}
	int total_number_of_edges = static_cast<int>(general_graph.size());

	// Checking that the general_graph does not have too many edges.
	assert(total_number_of_edges <= n - 1);

	// This is the case in which the forest that we receive is actually a tree.
	if (static_cast<int>(general_graph.size()) == n - 1)
	{
		KKT_WORK_ADD(verifier_components, 1);
		return verify_tree_marks(graph, general_graph, n);
	}

	// Given that the general graph is a forest of the graph, we will break it
	// into several trees and perform the verification in each one of them.
	int next_id = 0;
	vector<int> connected_component_id(n, -1);

	vector<vector<int>> gg_adj_list(n);
	KKT_WORK_ADD(initialized_slots, 2ULL * n);
	KKT_WORK_ADD(verifier_edge_visits, general_graph.size());
	for (const auto& edg: general_graph)
	{
		int from, to;
		tie(from, to, ignore, ignore) = edg;
		gg_adj_list[from].push_back(to);
		gg_adj_list[to].push_back(from);
	}

	// Iterative DFS for connected components (avoids std::function overhead)
	vector<pair<int, size_t>> dfs_stack;  // (node, neighbor_index)

	KKT_WORK_ADD(verifier_vertex_visits, n);
	for (int start = 0; start < n; ++start)
	{
		if (connected_component_id[start] != -1) continue;

		connected_component_id[start] = next_id++;
		dfs_stack.emplace_back(start, 0);

		while (!dfs_stack.empty())
		{
			auto& [node, idx] = dfs_stack.back();
			const auto& neighbors = gg_adj_list[node];

			// Find next unvisited neighbor
			while (idx < neighbors.size() && connected_component_id[neighbors[idx]] != -1)
			{
				KKT_WORK_ADD(verifier_arc_visits, 1);
				++idx;
			}

			if (idx < neighbors.size())
			{
				KKT_WORK_ADD(verifier_arc_visits, 1);
				int next = neighbors[idx];
				++idx;
				connected_component_id[next] = connected_component_id[node];
				dfs_stack.emplace_back(next, 0);
			}
			else
			{
				dfs_stack.pop_back();
			}
		}
	}

	vector<int> next_id_by_component(next_id, 0);
	vector<vector<tuple<int, int, int, int>>> spanning_tree(next_id);
	vector<vector<tuple<int, int, int, int>>> subgraph(next_id);
	vector<int> node_mapping(n);
	KKT_WORK_ADD(initialized_slots, 3ULL * next_id + n);
	KKT_WORK_ADD(verifier_components, next_id);

	KKT_WORK_ADD(verifier_vertex_visits, n);
	for (int i = 0; i < n; ++i)
	{
		int new_id = next_id_by_component[connected_component_id[i]]++;
		node_mapping[i] = new_id;
	}

	KKT_WORK_ADD(verifier_edge_visits, general_graph.size());
	for (const auto& edg: general_graph)
	{
		int from, to, cost, id;
		tie(from, to, cost, id) = edg;

		if (connected_component_id[from] == connected_component_id[to])
		{
			spanning_tree[connected_component_id[from]].emplace_back(
				node_mapping[from], node_mapping[to], cost, id);
			KKT_WORK_ADD(edge_materializations, 1);
		}
	}

	KKT_WORK_ADD(verifier_edge_visits, graph.size());
	for (size_t position = 0; position < graph.size(); ++position)
	{
		int from, to, cost;
		tie(from, to, cost, ignore) = graph[position];

		if (connected_component_id[from] == connected_component_id[to])
		{
			// Component queries carry their parent graph position in the ID
			// slot. The tree verifier only reads endpoints/weights when
			// classifying an edge; the caller's original IDs remain in graph.
			subgraph[connected_component_id[from]].emplace_back(
				node_mapping[from], node_mapping[to], cost, static_cast<int>(position));
			KKT_WORK_ADD(edge_materializations, 1);
		}
	}

	vector<unsigned char> heavy_marks(graph.size(), 0);
	KKT_WORK_ADD(initialized_slots, heavy_marks.size());

	KKT_WORK_ADD(verifier_vertex_visits, next_id);
	for (int i = 0; i < next_id; ++i)
	{
		if (subgraph[i].empty() || spanning_tree[i].empty()) continue;
		const auto component_marks =
			verify_tree_marks(subgraph[i], spanning_tree[i], next_id_by_component[i]);
		KKT_WORK_ADD(verifier_edge_visits, component_marks.size());
		for (size_t j = 0; j < component_marks.size(); ++j) {
			if (component_marks[j]) heavy_marks[get<3>(subgraph[i][j])] = 1;
		}
	}

	return heavy_marks;
}

unordered_set<int>
	verify_general_graph(const vector<tuple<int, int, int, int>>& graph,
						 const vector<tuple<int, int, int, int>>& general_graph,
						 const int n)
{
	return heavy_edge_ids(graph, verifier_detail::heavy_edge_marks(graph, general_graph, n));
}
