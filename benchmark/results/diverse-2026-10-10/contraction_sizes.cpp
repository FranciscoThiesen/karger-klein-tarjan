// Fixture structure probe only; no timing or algorithm changes.
#define main diverse_benchmark_original_main
#include "../../diverse_benchmark.cpp"
#undef main

extern std::pair<std::vector<int>, problem> boruvka_step(const problem&);

int main() {
    std::cout << "family,graph_seed,initial_n,initial_m,round,remaining_n,remaining_m,selected_edges\n";
    for (const Case item : std::vector<Case>{{"random_32", 1024}, {"random_32", 16384},
                                            {"random_32", 65536}, {"random_dense_anchor", 1000}}) {
        const auto graph = make_graph(item, 17, false);
        problem input(item.n, graph);
        auto first = boruvka_step(input);
        std::cout << item.family << ",17," << item.n << ',' << graph.size()
                  << ",1," << first.second.num_vertices << ',' << first.second.graph_edges.size()
                  << ',' << first.first.size() << '\n';
        auto second = boruvka_step(first.second);
        std::cout << item.family << ",17," << item.n << ',' << graph.size()
                  << ",2," << second.second.num_vertices << ',' << second.second.graph_edges.size()
                  << ',' << second.first.size() << '\n';
    }
}
