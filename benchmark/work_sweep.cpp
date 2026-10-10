// One logical-work observation per fixture/sampling seed. Instrumented runs
// deliberately contain no timers and are not performance measurements.
#include "graph_fixtures.hpp"
#include "mst_certificate.hpp"
#include "work_metrics.hpp"
#include "../kkt/kkt.hpp"
#include "../kruskal/kruskal.hpp"

#include <array>
#include <iostream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_set>
#include <vector>

#ifndef KKT_ENABLE_WORK_STATS
#error "work_sweep must use the instrumented KKT libraries"
#endif

namespace {
using benchmark_fixtures::Case;
using benchmark_fixtures::Graph;
using Ids = std::unordered_set<int>;
constexpr std::array<unsigned int, 3> graph_seeds = {17, 42, 999};
constexpr std::array<unsigned int, 3> sampling_seeds = {0, 1, 7};

Ids ids(const Graph& graph) {
    Ids result;
    result.reserve(graph.size());
    for (const auto& edge : graph) result.insert(std::get<3>(edge));
    return result;
}

std::vector<Case> cases(bool large) {
    std::vector<Case> result;
    for (const char* family : {"random_4", "random_32", "star", "hierarchical_path"}) {
        for (int n : {1024, 4096, 16384, 65536}) result.push_back({family, n});
        if (large) result.push_back({family, 262144});
    }
    return result;
}

void run(bool large) {
    std::cout << "case_id,family,n,m,graph_seed,kkt_seed";
    for (const auto& field : benchmark_work::fields) std::cout << ',' << field.name;
    std::cout << ",total_work_proxy,validation\n";

    for (const auto& item : cases(large)) {
        const std::string case_id = item.family + "_n" + std::to_string(item.n);
        std::cerr << "Counting " << case_id << '\n';
        for (unsigned int graph_seed : graph_seeds) {
            const auto graph = benchmark_fixtures::make_graph(item, graph_seed);
            const auto oracle = kruskal(graph, item.n);
            benchmark_validation::certify_mst(graph, oracle, item.n);
            const auto expected = ids(oracle);
            for (unsigned int sampling_seed : sampling_seeds) {
                kkt_work::WorkStats stats;
                Ids actual;
                {
                    kkt_work::ScopedWorkStats scope(stats);
                    problem input(item.n, graph);
                    actual = kkt(input, sampling_seed);
                }
                if (actual != expected)
                    throw std::runtime_error(case_id + ": incorrect MST at graph seed " +
                                             std::to_string(graph_seed) + ", KKT seed " +
                                             std::to_string(sampling_seed));
                if (stats.kkt_calls == 0 || stats.contraction_edge_visits == 0 ||
                    stats.current_depth != 0)
                    throw std::runtime_error(case_id + ": instrumentation is missing or unbalanced");
                std::cout << case_id << ',' << item.family << ',' << item.n << ',' << graph.size()
                          << ',' << graph_seed << ',' << sampling_seed;
                for (const auto& field : benchmark_work::fields)
                    std::cout << ',' << stats.*field.member;
                std::cout << ',' << benchmark_work::total_work_proxy(stats) << ",pass\n";
            }
        }
        std::cout.flush();
        if (!std::cout) throw std::runtime_error("failed to write work CSV");
    }
}
}  // namespace

int main(int argc, char** argv) {
    bool large = false;
    try {
        for (int i = 1; i < argc; ++i) {
            const std::string argument = argv[i];
            if (argument == "--large") large = true;
            else if (argument == "--help") {
                std::cout << "Usage: " << argv[0] << " [--large]\n"
                          << "Default: 16 cases, n=1024 through 65536, three graph and KKT seeds.\n"
                          << "--large adds n=262144 for all four families (20 cases total).\n"
                          << "Logical counters only; CSV on stdout, progress on stderr.\n";
                return 0;
            } else throw std::runtime_error("unknown argument: " + argument);
        }
        run(large);
    } catch (const std::exception& error) {
        std::cerr << "work sweep: " << error.what() << '\n';
        return 1;
    }
    return 0;
}
