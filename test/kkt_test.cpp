#include "../boruvka/boruvka.hpp"
#include "../graph_utils/graph_utils.hpp"
#include "../kkt/kkt.hpp"
#include "../kruskal/kruskal.hpp"
#include "../prim/prim.hpp"
#include "gtest/gtest.h"
#include <fstream>

using namespace std;

/*
TEST(hardcoded_test, fixed_graph) {
	constexpr int N = 20;
	vector< tuple<int, int, int, int> > random_graph;
	vector< tuple<int, int, int> > g;
	// Inserindo em random_graph
	random_graph.emplace_back(0, 1, 12, 0);
	random_graph.emplace_back(1, 2, 15, 1);
	random_graph.emplace_back(2, 3, 20, 2);
	random_graph.emplace_back(3, 4, 1, 3);
	random_graph.emplace_back(4, 5, 9, 4);
	random_graph.emplace_back(5, 6, 25, 5);
	random_graph.emplace_back(6, 7, 24, 6);
	random_graph.emplace_back(7, 8, 6, 7);
	random_graph.emplace_back(8, 9, 10, 8);
	random_graph.emplace_back(9, 10, 7, 9);
	random_graph.emplace_back(10, 11, 16, 10);
	random_graph.emplace_back(11, 12, 11, 11);
	random_graph.emplace_back(12, 13, 8, 12);
	random_graph.emplace_back(13, 14, 14, 13);
	random_graph.emplace_back(14, 15, 4, 14);
	random_graph.emplace_back(15, 16, 19, 15);
	random_graph.emplace_back(16, 17, 18, 16);
	random_graph.emplace_back(17, 18, 2, 17);
	random_graph.emplace_back(18, 19, 23, 18);
	random_graph.emplace_back(8, 13, 21, 19);
	random_graph.emplace_back(8, 18, 22, 20);
	random_graph.emplace_back(0, 11, 29, 21);
	random_graph.emplace_back(0, 19, 5, 22);
	random_graph.emplace_back(5, 16, 3, 23);
	random_graph.emplace_back(5, 7, 17, 24);
	random_graph.emplace_back(5, 9, 26, 25);
	random_graph.emplace_back(0, 18, 13, 26);
	random_graph.emplace_back(7, 12, 28, 27);
	random_graph.emplace_back(14, 17, 27, 28);
	random_graph.emplace_back(2, 18, 0, 29);





	g.emplace_back(0, 1, 12);
	g.emplace_back(1, 2, 15);
	g.emplace_back(2, 3, 20);
	g.emplace_back(3, 4, 1);
	g.emplace_back(4, 5, 9);
	g.emplace_back(5, 6, 25);
	g.emplace_back(6, 7, 24);
	g.emplace_back(7, 8, 6);
	g.emplace_back(8, 9, 10);
	g.emplace_back(9, 10, 7);
	g.emplace_back(10, 11, 16);
	g.emplace_back(11, 12, 11);
	g.emplace_back(12, 13, 8);
	g.emplace_back(13, 14, 14);
	g.emplace_back(14, 15, 4);
	g.emplace_back(15, 16, 19);
	g.emplace_back(16, 17, 18);
	g.emplace_back(17, 18, 2);
	g.emplace_back(18, 19, 23);
	g.emplace_back(8, 13, 21);
	g.emplace_back(8, 18, 22);
	g.emplace_back(0, 11, 29);
	g.emplace_back(0, 19, 5);
	g.emplace_back(5, 16, 3);
	g.emplace_back(5, 7, 17);
	g.emplace_back(5, 9, 26);
	g.emplace_back(0, 18, 13);
	g.emplace_back(7, 12, 28);
	g.emplace_back(14, 17, 27);
	g.emplace_back(2, 18, 0);



	problem P = problem(N, random_graph);

	unordered_set<int> res = kkt(P);
	auto kruskal_mst = kruskal(g, 20);
	int truth = sum_of_costs(kruskal_mst);
	ASSERT_EQ(static_cast<int>(res.size()), 19);
	ASSERT_EQ(get_solution_cost(P, res), truth);
}
*/

TEST(stress_test, random_graph)
{
	constexpr int N = 100;
	constexpr int M = 500;

	for (int i = 0; i < 100; ++i)
	{
		auto random_graph = build_random_connected_graph(N, M);
		auto kruskal_mst = kruskal(random_graph, N);
		// Asserting that canonical algo's agree!!

		vector<tuple<int, int, int, int>> problem_edges;

		for (int e = 0; e < M; ++e)
		{
			int from, to, cost;
			tie(from, to, cost) = random_graph[e];
			problem_edges.emplace_back(from, to, cost, e);
		}

		problem P = problem(N, problem_edges);
		unordered_set<int> res = kkt(P);

		int truth = sum_of_costs(kruskal_mst);

		ASSERT_EQ(static_cast<int>(res.size()), N - 1);
		ASSERT_EQ(get_solution_cost(P, res), truth);
	}
}
