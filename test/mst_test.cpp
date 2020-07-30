#include "../boruvka/boruvka.hpp"
#include "../kruskal/kruskal.hpp"
#include "../prim/prim.hpp"
#include "../graph_utils/graph_utils.hpp"
#include "gtest/gtest.h"

TEST(stress_test, random_graph)
{
    for(int i = 0; i < 100; ++i)
    {
        auto random_graph = build_random_connected_graph(100, 500);
        auto boruvka_mst = boruvka(random_graph, 100);
        auto kruskal_mst = kruskal(random_graph, 100);
        auto prim_mst = prim(random_graph, 100);

        EXPECT_EQ(sum_of_costs(boruvka_mst), sum_of_costs(kruskal_mst));
        EXPECT_EQ(static_cast<int>(boruvka_mst.size()), 100 - 1);
    }
}
