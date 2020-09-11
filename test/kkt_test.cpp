#include "../boruvka/boruvka.hpp"
#include "../graph_utils/graph_utils.hpp"
#include "../kkt/kkt.hpp"
#include "../kruskal/kruskal.hpp"
#include "../prim/prim.hpp"
#include "gtest/gtest.h"
#include <fstream>

using namespace std;

// Correctenss tests
TEST(stress_test, random_small_graphs)
{
	constexpr int N = 10;
	constexpr int M = 30;

	for (int i = 0; i < 10000; ++i)
	{
		auto random_graph = build_random_connected_graph(N, M);
		auto kruskal_mst = kruskal(random_graph, N);

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

TEST(stress_test, random_medium_graphs)
{
	constexpr int N = 1000;
	constexpr int M = 50000;

	for (int i = 0; i < 100; ++i)
	{
		auto random_graph = build_random_connected_graph(N, M);
		auto kruskal_mst = kruskal(random_graph, N);

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

TEST(stress_test, random_large_graphs)
{
	constexpr int N = 10000;
	constexpr int M = 500000;

	for (int i = 0; i < 10; ++i)
	{
		auto random_graph = build_random_connected_graph(N, M);
		auto kruskal_mst = kruskal(random_graph, N);

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
