// Untimed companion to the paired contraction experiment. It deliberately uses
// independent simple-input certification; no production validation is relaxed.
#include "core_attachment_fixtures.hpp"
#include "search_fixtures.hpp"
#include "crossover_fixtures.hpp"
#include "mst_certificate.hpp"
#include "work_metrics.hpp"
#include "../kkt/kkt.hpp"
#include "../kruskal/kruskal.hpp"

#include <cstdint>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_set>

#ifndef KKT_ENABLE_WORK_STATS
#error "This untimed diagnostic requires instrumented production objects"
#endif

std::pair<std::vector<int>, problem> boruvka_step(const problem&);

namespace {
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}
unsigned int number(const std::string& text) {
    require(!text.empty() && text.find_first_not_of("0123456789") == std::string::npos,
            "expected unsigned integer");
    const auto value = std::stoull(text);
    require(value <= std::numeric_limits<unsigned int>::max(), "integer overflow");
    return static_cast<unsigned int>(value);
}
std::uint64_t fingerprint(const benchmark_fixtures::Graph& graph, int n, bool weighted) {
    std::uint64_t value = UINT64_C(14695981039346656037);
    const auto append = [&](int item) {
        const auto bits = static_cast<std::uint32_t>(item);
        for (unsigned int shift = 0; shift < 32; shift += 8) {
            value ^= (bits >> shift) & 0xffu;
            value *= UINT64_C(1099511628211);
        }
    };
    append(n);
    for (const auto& [u, v, cost, id] : graph) {
        append(u); append(v); if (weighted) append(cost); append(id);
    }
    return value;
}
void stats(const kkt_work::WorkStats& work) {
    std::cout << '{';
    bool first = true;
    for (const auto& field : benchmark_work::fields) {
        if (!first) std::cout << ',';
        first = false;
        std::cout << '"' << field.name << "\":" << work.*field.member;
    }
    std::cout << '}';
}
}

int main(int argc, char** argv) {
    try {
        require(argc == 6, "usage: multigraph_work FAMILY N D GRAPH_SEED KKT_SEED");
        const unsigned int n = number(argv[2]), d = number(argv[3]);
        require(n >= 32 && n <= (1u << 22) && d >= 1 && d <= 512 &&
                static_cast<std::uint64_t>(n) * d <= (1u << 27), "size outside experiment limits");
        const unsigned int graph_seed = number(argv[4]), kkt_seed = number(argv[5]);
        const benchmark_continuation::Spec spec{argv[1], static_cast<int>(n), static_cast<int>(d), 0};
        benchmark_fixtures::Graph graph;
        if (benchmark_attachments::known(spec.family))
            graph = benchmark_attachments::make_fixture(spec, graph_seed).graph;
        else if (benchmark_search::known(spec.family))
            graph = benchmark_search::make_fixture(spec, graph_seed).graph;
        else {
            require(spec.family == "gnm_random", "unsupported diagnostic family");
            graph = benchmark_crossover::make_fixture({spec.family, spec.n, spec.density}, graph_seed).graph;
        }
        require(graph.size() == static_cast<std::size_t>(n) * d, "incorrect input edge count");
        const auto reference = kruskal(graph, spec.n);
        benchmark_validation::certify_mst(graph, reference, spec.n);
        std::unordered_set<int> expected;
        for (const auto& edge : reference)
            require(expected.insert(std::get<3>(edge)).second, "repeated reference edge ID");
        kkt_work::WorkStats work[2];
        for (int algorithm = 0; algorithm < 2; ++algorithm) {
            std::unordered_set<int> result;
            {
                kkt_work::ScopedWorkStats scope(work[algorithm]);
                problem input(spec.n, graph);
                if (algorithm == 0) result = kkt(input, kkt_seed);
                else {
                    std::vector<int> selected;
                    while (!input.graph_edges.empty()) {
                        auto [edges, reduced] = boruvka_step(input);
                        selected.insert(selected.end(), edges.begin(), edges.end());
                        input = std::move(reduced);
                    }
                    result.reserve(selected.size());
                    result.insert(selected.begin(), selected.end());
                    KKT_WORK_ADD(hash_insert_items, selected.size());
                }
            }
            require(result == expected, "solver differs from independently certified unique MST");
            require(work[algorithm].current_depth == 0 &&
                    work[algorithm].hash_insert_items == expected.size(), "invalid scope or result counters");
        }
        require(work[0].sampling_edge_visits == work[0].verifier_edges &&
                work[0].sampling_calls == work[0].verifier_calls, "KKT sampling/verifier counter mismatch");
        require(work[1].kkt_calls == 0 && work[1].verifier_calls == 0, "compactor invoked KKT/verifier");
#ifdef KKT_EXPERIMENT_RETAIN_PARALLEL
        const char* variant = "multigraph";
        require(work[0].contraction_edge_visits <= 3 * work[0].contraction_edges,
                "retention contraction exceeds three input edge scans");
#else
        const char* variant = "reference";
#endif
        std::cout << "{\"schema\":\"multigraph_work_v1\",\"variant\":\"" << variant
                  << "\",\"family\":\"" << spec.family << "\",\"n\":" << n
                  << ",\"density\":" << d << ",\"m\":" << graph.size()
                  << ",\"graph_seed\":" << graph_seed << ",\"kkt_seed\":" << kkt_seed
                  << ",\"input_fingerprint\":" << fingerprint(graph, spec.n, true)
                  << ",\"topology_fingerprint\":" << fingerprint(graph, spec.n, false)
                  << ",\"validation\":\"pass\",\"algorithms\":{\"kkt\":";
        stats(work[0]); std::cout << ",\"compacting_boruvka\":"; stats(work[1]);
        std::cout << "}}\n";
        std::cout.flush(); require(static_cast<bool>(std::cout), "failed to emit diagnostic output");
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
