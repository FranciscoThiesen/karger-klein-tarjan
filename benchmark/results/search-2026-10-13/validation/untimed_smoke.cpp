#define main mst_search_program_main
#include "/Users/random_person/Desktop/karger-klein-tarjan/benchmark/mst_search.cpp"
#undef main
int main() {
    int fixtures = 0;
    for (const char* family : {"hierarchical_path", "hierarchical_tree", "low_path", "random_path", "random_tree", "distance_path", "distance_tree", "line_metric", "line_wide_metric", "line_random", "grid2d_metric", "grid2d_random", "gnm_random"}) {
        for (unsigned seed : {17u, 42u}) {
            Spec spec{family, 128, std::string(family) == "gnm_random" ? 16 : 4, 0};
            Graph graph = fixture(spec, seed);
            require(graph.size() == static_cast<std::size_t>(fixture_edge_count(spec)), "dimension");
            const Graph oracle = kruskal(graph, spec.n);
            benchmark_validation::certify_mst(graph, oracle, spec.n);
            const auto expected = ids(oracle);
            std::vector<const Graph::value_type*> by_id(graph.size());
            for (const auto& edge : graph) by_id[std::get<3>(edge)] = &edge;
            require(valid_tree(oracle, expected, by_id), "Kruskal mismatch");
            require(valid_tree(prim(graph, spec.n), expected, by_id), "Prim mismatch");
            require(valid_tree(boruvka(graph, spec.n), expected, by_id), "Boruvka mismatch");
            problem input(spec.n, graph);
            require(compacting_boruvka(input) == expected, "Compactor mismatch");
            for (unsigned sampling : {0u, 1u, 7u}) {
                problem sample_input(spec.n, graph);
                require(kkt(sample_input, sampling) == expected, "KKT mismatch");
            }
            Graph wrong = oracle;
            std::get<2>(wrong.front()) += 1;
            require(!valid_tree(wrong, expected, by_id), "Changed cost accepted");
            wrong = oracle;
            wrong.pop_back();
            require(!valid_tree(wrong, expected, by_id), "Missing edge accepted");
            wrong = oracle;
            wrong.back() = wrong.front();
            require(!valid_tree(wrong, expected, by_id), "Duplicate edge accepted");
            ++fixtures;
        }
    }
    std::cout << "{\"validation\":\"pass\",\"fixtures\":" << fixtures
              << ",\"solver_checks\":" << 7 * fixtures
              << ",\"malformed_tuple_checks\":" << 3 * fixtures
              << ",\"measured_calls\":0}\n";
}
