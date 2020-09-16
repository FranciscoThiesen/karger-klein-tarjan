#include "verifier.hpp"
#include "../boruvka/boruvka.hpp"
#include "../graph_utils/graph_utils.hpp"
#include "../kruskal/kruskal.hpp"
#include "../lca/lca.hpp"
#include "../prim/prim.hpp"
#include "../union_find/union_find.hpp"

#include <functional>
#include <iostream>
#include <numeric>
#include <tuple>
#include <unordered_map>
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
// Such reduction is made performing a strategy similar to the Boruvka algorithm.
// It is guaranteed that the size of the generated full branching tree has at
// most O(2 * n) vertices. 
// Assumptions: We receive the edges of a proper Spanning Tree
// Complexity: O(n)
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
		
        // Finding the cheapest edge that touches each component
        unordered_map<int, int> cheapest_edge;

	    // Adjacency list for each component that is still active by the
        // current iteration.
        unordered_map<int, vector<int>> current_graph;

		for (int i = 0; i < total_edges; ++i)
		{
			int from, to, cost;
			tie(from, to, cost, ignore) = active_edges[i];

			if (cheapest_edge.count(from) == 0 ||
				cost < get<2>(active_edges[cheapest_edge[from]]))
				cheapest_edge[from] = i;
			if (cheapest_edge.count(to) == 0 ||
				cost < get<2>(active_edges[cheapest_edge[to]]))
				cheapest_edge[to] = i;
		}

	    // Storing the list of components that are still active by now	
        vector<int> component_list;
		for (const auto& par: cheapest_edge)
			component_list.push_back(par.first);

	    // This loops construct the graph that takes into account only the
        // current active components
        for (const auto& par: cheapest_edge)
		{
			int from, to, cost;
			tie(from, to, cost, ignore) = active_edges[par.second];
			current_graph[from].push_back(to);
			current_graph[to].push_back(from);
		}

		vector<int> new_component_ids;
		unordered_map<int, int>
			super_node_id; 

	    // This lambda functions explores the current graph.
        // This is required, because next we will merge each
        // of the connected components into a single new node
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
        
        // Calling the explore_cc method for each node that is unexplored
		for (const auto& id: component_list)
		{
			if (super_node_id.count(id) == 0) explore_cc(id, -1);
		}
        
        // Connecting each of the nodes of the current step to it's
        // corresponding super_node.
		for (const auto& par: cheapest_edge)
		{
			int super_node_cc = super_node_id[par.first];
			new_edges.emplace_back(par.first, super_node_cc,
								   get<2>(active_edges[par.second]), get<3>(active_edges[par.second]));
		}
        
        // We are now removing self-loops and changing the 
        // endpoints edges, so as to reflect that collapse
        // of several nodes into a single super_node
		vector<tuple<int, int, int, int>> relevant_edges;
		for (const auto& e: active_edges)
		{
			int from, to, cost, id;
			tie(from, to, cost, id) = e;
			if (super_node_id[from] != super_node_id[to])
			{
				relevant_edges.emplace_back(super_node_id[to],
											super_node_id[from], cost, id);
			}
		}

        // Updating the active edges, total number of edges
        // and the number of connected components
		active_edges = relevant_edges;
		total_edges = static_cast<int>(active_edges.size());
		graph_cc = static_cast<int>(new_component_ids.size());
	}
    
    // Returning edges of the generated full-branching tree 
    return new_edges;
}

// Implementation of the tree_path_maxima problem solver.
// It is completely based on the D code that Torben
// Hagerup made available in his 2009 paper. It answers multiple queries and
// each query provides two nodes (a,b) and asks for the maximum edge
// on the path from (a, b) on the tree! (This is why it is called the
// tree-path-maxima problem)
//
// Assumptions: It received a full-branching-tree in the format specified
// on the paper. And it receives multiple tree_path_maxima queries, where
// query i is defined by (lower[i], upper[i]).
// 
// Complexity: O(n + m)
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

	void init(int u, int d)
	{
		depth[u] = d;
		if (d > height) height = d;
		for (int i = L[u]; i >= 0; i = Lnext[i]) D[u] |= 1 << depth[upper[i]];
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
		S = down(D[v], (S & ((1 << (k + 1)) - 1)) | (1 << depth[v]));
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
	vector<tuple<int, int, int, int>> mst;
	vector<tuple<int, int, int, int>> G;
	LCA lca;

	test_graph(const vector<tuple<int, int, int, int>> edges,
			   const vector<tuple<int, int, int, int>> spanning_tree, const int n)
	{
		mst = spanning_tree;
		auto fbt_mst = fbt_reduction(mst, n);
		G = edges;
        int max_id = n;
		for (const auto& e: fbt_mst)
		{
			int a, b, c;
			tie(a, b, c, ignore) = e;
			max_id = max(max(a, b) + 1, max_id);
		}
		total_nodes = max_id;
	    // total_nodes is different than n, because it represents
        // the total number of nodes on the full-branching tree
        
		int N = total_nodes;
		
        vector<vector<pair<int, int>>> adj_list(max_id);
		vector<vector<int>> adj(N);

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
        
        // This function performs the dfs on the full-branching-tree
        // graph and also converts the graph to a format that is
        // compatible with the tree_path_maxima call.
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
		
        dfs_lca(root, -1);

        // This structure perform the required LCA precomputations in O(n + m),
        // in order to answer LCA queries in O(1) time
        lca = LCA(N, adj, root);
	}

    // This function performs the verification per se.	
    bool verify()
	{
		vector<int> gabarito, upper, lower, corresponding_edge;
		int M = static_cast<int>(G.size());
		int upper_len = 0;
		vector<pair<int, int>> decomposed_query;

		for (int i = 0; i < M; ++i)
		{
			int src, to, cost;
			tie(src, to, cost, ignore) = G[i];
			
            // Every query of the form (u, v) has to be
            // split into (u, lca(u, v)), (v, lca(u, v)). This is a 
            // requisite for the tree_path_maxima algorithm.
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

		for (const auto& qry: decomposed_query)
		{
			int id_fst = qry.first, id_snd = qry.second;
			int edge_cost =
				gabarito[id_fst]; 
			
            int heavy_combine = max(weight[sol[id_fst]], weight[sol[id_snd]]);
			if (heavy_combine > edge_cost)
			{
                // We have encountered a edge that should be part of the
                // Spanning Tree. That guarantees that it is not minimal.
				return false;
			}
		}
		return true;
	}
};

bool verify_mst(const vector<tuple<int, int, int, int>>& graph,
				const vector<tuple<int, int, int, int>>& spanning_tree, const int n)
{
	auto verifier = test_graph(graph, spanning_tree, n);
	return verifier.verify();
}
