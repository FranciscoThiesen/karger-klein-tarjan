#include "mst_certificate.hpp"

#include <iostream>

using benchmark_validation::Graph;
using benchmark_validation::certify_mst;

void rejects(const Graph& graph, const Graph& tree, int n, const char* label) {
    try {
        certify_mst(graph, tree, n);
    } catch (const std::runtime_error&) {
        return;
    }
    throw std::runtime_error(std::string("accepted invalid certificate: ") + label);
}

int main() {
    try {
        const Graph graph{{0, 1, 1, 0}, {1, 2, 3, 1}, {2, 3, 2, 2},
                          {0, 3, 5, 3}, {0, 2, 4, 4}};
        const Graph tree{graph[0], graph[1], graph[2]};
        certify_mst(graph, tree, 4);
        auto reversed = tree;
        for (auto& edge : reversed) std::swap(std::get<0>(edge), std::get<1>(edge));
        certify_mst(graph, reversed, 4);
        // Total weight exceeds INT_MAX, while each edge is below Prim's sentinel.
        const Graph high_cost{{0, 1, 900000000, 0}, {1, 2, 900000001, 1},
                              {2, 3, 900000002, 2}};
        certify_mst(high_cost, high_cost, 4);
        rejects(graph, {graph[0], graph[2], graph[3]}, 4, "nonminimal tree");
        rejects(graph, {graph[0], graph[1]}, 4, "wrong edge count");
        rejects(graph, {graph[0], graph[0], graph[2]}, 4, "duplicate tree ID");
        rejects(graph, {graph[0], graph[1], graph[4]}, 4, "cyclic disconnected tree");
        auto wrong_id = tree;
        std::get<3>(wrong_id[0]) = 99;
        rejects(graph, wrong_id, 4, "unknown tree ID");
        auto wrong_tuple = tree;
        std::get<1>(wrong_tuple[0]) = 2;
        rejects(graph, wrong_tuple, 4, "mismatched tuple");
        auto bad_graph = graph;
        std::get<3>(bad_graph[4]) = 0;
        rejects(bad_graph, tree, 4, "duplicate input ID");
        bad_graph = graph;
        std::get<2>(bad_graph[4]) = 3;
        rejects(bad_graph, tree, 4, "duplicate weight");
        bad_graph = graph;
        std::get<0>(bad_graph[4]) = 4;
        rejects(bad_graph, tree, 4, "invalid endpoint");
        bad_graph = graph;
        std::get<0>(bad_graph[4]) = 1;
        rejects(bad_graph, tree, 4, "parallel edge");
        bad_graph = graph;
        std::get<2>(bad_graph[4]) = 0x3f3f3f3f;
        rejects(bad_graph, tree, 4, "weight outside Prim domain");
        const Graph disconnected{{0, 1, 1, 0}, {1, 2, 2, 1}, {0, 2, 3, 2}};
        rejects(disconnected, disconnected, 4, "disconnected fixture");
        std::cout << "PASS independent MST certificate positive and negative cases\n";
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
