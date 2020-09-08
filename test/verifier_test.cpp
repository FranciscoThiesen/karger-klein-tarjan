#include "../boruvka/boruvka.hpp"
#include "../graph_utils/graph_utils.hpp"
#include "../kruskal/kruskal.hpp"
#include "../prim/prim.hpp"
#include "../verifier/verifier.hpp"
#include "gtest/gtest.h"

TEST(positive_verification, random_graph)
{
	auto random_graph = build_random_connected_graph(100, 500);
	auto kruskal_mst = kruskal(random_graph, 100);
	ASSERT_TRUE(verify_mst(random_graph, kruskal_mst, 100));
	auto boruvka_mst = boruvka(random_graph, 100);
	ASSERT_TRUE(verify_mst(random_graph, boruvka_mst, 100));
	auto prim_mst = prim(random_graph, 100);
	ASSERT_TRUE(verify_mst(random_graph, prim_mst, 100));
}

TEST(negative_verification, fixed_graph)
{
	vector<tuple<int, int, int>> simple_graph;
	simple_graph.emplace_back(0, 1, 1);
	simple_graph.emplace_back(1, 2, 1);
	simple_graph.emplace_back(0, 2, 2);

	vector<tuple<int, int, int>> non_minimum_spanning_tree;
	non_minimum_spanning_tree.emplace_back(0, 2, 2);
	non_minimum_spanning_tree.emplace_back(1, 2, 1);

	ASSERT_FALSE(verify_mst(simple_graph, non_minimum_spanning_tree, 3));
}

TEST(stress_test, random_small_graph)
{
	auto random_graph = build_random_connected_graph(10, 40);
	auto kruskal_mst = kruskal(random_graph, 10);
	long long mst_cost = sum_of_costs(kruskal_mst);

	for (int i = 0; i < 100; ++i)
	{
		auto random_spanning_tree = get_random_spanning_tree(random_graph, 10);
		long long spanning_tree_cost = sum_of_costs(random_spanning_tree);
		bool is_mst = (spanning_tree_cost == mst_cost);
		bool verifier_result =
			verify_mst(random_graph, random_spanning_tree, 10);
		ASSERT_EQ(is_mst, verifier_result);
	}
}

TEST(stress_test, random_medium_graph)
{
	auto random_graph = build_random_connected_graph(100, 500);
	auto kruskal_mst = kruskal(random_graph, 100);
	long long mst_cost = sum_of_costs(kruskal_mst);

	for (int i = 0; i < 10; ++i)
	{
		auto random_spanning_tree = get_random_spanning_tree(random_graph, 100);
		long long spanning_tree_cost = sum_of_costs(random_spanning_tree);
		bool is_mst = (spanning_tree_cost == mst_cost);
		bool verifier_result =
			verify_mst(random_graph, random_spanning_tree, 100);
		ASSERT_EQ(is_mst, verifier_result);
	}
}

TEST(stress_test, random_large_graph)
{
	auto random_graph = build_random_connected_graph(10000, 100000);
	auto kruskal_mst = kruskal(random_graph, 10000);
	long long mst_cost = sum_of_costs(kruskal_mst);

	for (int i = 0; i < 10; ++i)
	{
		auto random_spanning_tree =
			get_random_spanning_tree(random_graph, 10000);
		long long spanning_tree_cost = sum_of_costs(random_spanning_tree);
		bool is_mst = (spanning_tree_cost == mst_cost);
		bool verifier_result =
			verify_mst(random_graph, random_spanning_tree, 10000);
		ASSERT_EQ(is_mst, verifier_result);
	}
}
