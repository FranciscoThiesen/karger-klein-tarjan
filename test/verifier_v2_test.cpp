#include "../boruvka/boruvka.hpp"
#include "../graph_utils/graph_utils.hpp"
#include "../kruskal/kruskal.hpp"
#include "../prim/prim.hpp"
#include "../verifier/verifier_v2.hpp"
#include "gtest/gtest.h"

TEST(test_forest, hardcoded_graph)
{
	vector<tuple<int, int, int>> graph;
	vector<tuple<int, int, int>> spanning_forest;

	vector<pair<int, int>> E = {{0, 1}, {2, 3}, {3, 4}, {4, 5}};

	for (int i = 0; i < 4; ++i)
	{
		graph.emplace_back(E[i].first, E[i].second, i + 1);
		spanning_forest.emplace_back(E[i].first, E[i].second, i + 1);
	}

	graph.emplace_back(0, 2, 0);
	graph.emplace_back(2, 4, 6);
	graph.emplace_back(2, 5, -1);
	graph.emplace_back(3, 5, 5);
	vector<tuple<int, int, int>> known_heavy_edges = {{2, 4, 6}, {3, 5, 5}};

	auto V = verify_general_graph(graph, spanning_forest, 6);
	ASSERT_EQ(V, known_heavy_edges);
	ASSERT_FALSE(V.empty());
	ASSERT_EQ(static_cast<int>(V.size()), 2);
}
