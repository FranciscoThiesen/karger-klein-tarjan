#include "../boruvka/boruvka.hpp"
#include "../graph_utils/graph_utils.hpp"
#include "../kkt/kkt.hpp"
#include "../kruskal/kruskal.hpp"
#include "../prim/prim.hpp"
#include "gtest/gtest.h"
#include <fstream>

using namespace std;

// Correctness tests
TEST(stress_test, random_small_graphs)
{
	constexpr int N = 10;
	constexpr int M = 30;

	for (int i = 0; i < 10000; ++i)
	{
		SCOPED_TRACE(i);
		const unsigned int graph_seed = static_cast<unsigned int>(i);
		const unsigned int sampling_seed = 0x9e3779b9u + graph_seed;
		auto random_graph = build_random_connected_graph(N, M, graph_seed);
		auto kruskal_mst = kruskal(random_graph, N);

		problem P = problem(N, random_graph);
		unordered_set<int> res = kkt(P, sampling_seed);

		unordered_set<int> expected;
		for (const auto& edge : kruskal_mst) expected.insert(get<3>(edge));
		long long truth = sum_of_costs(kruskal_mst);
		long long actual = 0;
		for (const auto& edge : random_graph)
			if (res.count(get<3>(edge))) actual += get<2>(edge);

		ASSERT_EQ(static_cast<int>(res.size()), N - 1);
		ASSERT_EQ(res, expected);
		ASSERT_EQ(actual, truth);
	}
}

TEST(stress_test, random_medium_graphs)
{
	constexpr int N = 1000;
	constexpr int M = 50000;

	for (int i = 0; i < 100; ++i)
	{
		SCOPED_TRACE(i);
		const unsigned int graph_seed = 10000u + static_cast<unsigned int>(i);
		const unsigned int sampling_seed = 0x9e3779b9u + graph_seed;
		auto random_graph = build_random_connected_graph(N, M, graph_seed);
		auto kruskal_mst = kruskal(random_graph, N);

		problem P = problem(N, random_graph);
		unordered_set<int> res = kkt(P, sampling_seed);

		unordered_set<int> expected;
		for (const auto& edge : kruskal_mst) expected.insert(get<3>(edge));
		long long truth = sum_of_costs(kruskal_mst);
		long long actual = 0;
		for (const auto& edge : random_graph)
			if (res.count(get<3>(edge))) actual += get<2>(edge);

		ASSERT_EQ(static_cast<int>(res.size()), N - 1);
		ASSERT_EQ(res, expected);
		ASSERT_EQ(actual, truth);
	}
}

TEST(stress_test, random_large_graphs)
{
	constexpr int N = 10000;
	constexpr int M = 500000;

	for (int i = 0; i < 10; ++i)
	{
		SCOPED_TRACE(i);
		const unsigned int graph_seed = 20000u + static_cast<unsigned int>(i);
		const unsigned int sampling_seed = 0x9e3779b9u + graph_seed;
		auto random_graph = build_random_connected_graph(N, M, graph_seed);
		auto kruskal_mst = kruskal(random_graph, N);

		problem P = problem(N, random_graph);
		unordered_set<int> res = kkt(P, sampling_seed);

		unordered_set<int> expected;
		for (const auto& edge : kruskal_mst) expected.insert(get<3>(edge));
		long long truth = sum_of_costs(kruskal_mst);
		long long actual = 0;
		for (const auto& edge : random_graph)
			if (res.count(get<3>(edge))) actual += get<2>(edge);

		ASSERT_EQ(static_cast<int>(res.size()), N - 1);
		ASSERT_EQ(res, expected);
		ASSERT_EQ(actual, truth);
	}
}
