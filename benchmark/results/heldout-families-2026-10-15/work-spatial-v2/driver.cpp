// Supplementary, untimed driver. This file is explicitly hash-bound separately
// from the frozen timing-source inventory; it changes no production source.
#include "benchmark/core_attachment_fixtures.hpp"
#include "benchmark/crossover_fixtures.hpp"
#include "benchmark/mst_certificate.hpp"
#include "benchmark/retention_boruvka.hpp"
#include "benchmark/work_metrics.hpp"
#include "kruskal/kruskal.hpp"

#include <cstring>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>

#if !defined(KKT_ENABLE_WORK_STATS) || !defined(KKT_EXPERIMENT_RETAIN_PARALLEL)
#error "Supplementary diagnostic requires candidate KKT and work counters"
#endif

std::pair<std::vector<int>, problem> boruvka_step(const problem&);

namespace {
using Graph = benchmark_fixtures::Graph;
using Ids = std::unordered_set<int>;

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

std::uint64_t fingerprint(const Graph& graph, int n, bool weighted) {
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

// Exact frozen six-solver compactor body, including uninstrumented result-set
// insertion. That field is emitted as null for both Boruvka continuations.
Ids compacting_boruvka(problem& input) {
    std::vector<int> selected_ids;
    while (!input.graph_edges.empty()) {
        auto [selected, reduced] = boruvka_step(input);
        selected_ids.insert(selected_ids.end(), selected.begin(), selected.end());
        input = std::move(reduced);
    }
    Ids result;
    result.reserve(selected_ids.size());
    result.insert(selected_ids.begin(), selected_ids.end());
    return result;
}

struct Round {
    std::uint64_t vertices, edges, selected, output_vertices, output_edges;
};

// A separate deterministic replay collects round boundaries without changing
// either frozen continuation. Its work is outside all WorkStats scopes. Check
// every aggregate against the exact helper's instrumented invocation below.
std::vector<Round> trace(const Graph& graph, int n, bool retain, const Ids& expected) {
    require(kkt_work::active == nullptr, "trace leaked into instrumented scope");
    problem input(n, graph);
    std::vector<Round> rounds;
    Ids selected_ids;
    while (!input.graph_edges.empty()) {
        Round round{static_cast<std::uint64_t>(input.num_vertices), input.graph_edges.size(), 0, 0, 0};
        auto [selected, reduced] = retain ? kkt_experiment::retain_parallel_step(input) : boruvka_step(input);
        round.selected = selected.size();
        round.output_vertices = static_cast<std::uint64_t>(reduced.num_vertices);
        round.output_edges = reduced.graph_edges.size();
        require(reduced.num_vertices <= input.num_vertices / 2 &&
                reduced.graph_edges.size() <= input.graph_edges.size(), "contraction failed to shrink");
        for (int id : selected) require(selected_ids.insert(id).second, "trace selected duplicate ID");
        rounds.push_back(round);
        input = std::move(reduced);
    }
    require(selected_ids == expected, "trace does not match certified MST");
    return rounds;
}

void check_trace(const std::vector<Round>& rounds, const kkt_work::WorkStats& work) {
    std::uint64_t vertices = 0, edges = 0, output_vertices = 0, output_edges = 0;
    for (const Round& round : rounds) {
        vertices += round.vertices; edges += round.edges;
        output_vertices += round.output_vertices; output_edges += round.output_edges;
    }
    require(work.contraction_calls == rounds.size() && work.contraction_vertices == vertices &&
            work.contraction_edges == edges && work.contraction_output_vertices == output_vertices &&
            work.contraction_output_edges == output_edges, "round replay/counters mismatch");
}

void emit_stats(const kkt_work::WorkStats& work, bool measured_hash) {
    std::cout << '{';
    bool first = true;
    for (const auto& field : benchmark_work::fields) {
        if (!first) std::cout << ',';
        first = false;
        std::cout << '"' << field.name << "\":";
        if (!measured_hash && std::strcmp(field.name, "hash_insert_items") == 0) std::cout << "null";
        else std::cout << work.*field.member;
    }
    std::cout << '}';
}

void emit_rounds(const std::vector<Round>& rounds) {
    std::cout << '[';
    for (std::size_t i = 0; i < rounds.size(); ++i) {
        if (i) std::cout << ',';
        const auto& r = rounds[i];
        std::cout << "{\"round\":" << i << ",\"vertices\":" << r.vertices << ",\"edges\":" << r.edges
                  << ",\"selected\":" << r.selected << ",\"output_vertices\":" << r.output_vertices
                  << ",\"output_edges\":" << r.output_edges << '}';
    }
    std::cout << ']';
}
} // namespace

int main(int argc, char** argv) {
    try {
        require(argc == 6, "usage: retention_work FAMILY N D GRAPH_SEED KKT_SEED");
        const auto n = number(argv[2]), d = number(argv[3]);
        const auto graph_seed = number(argv[4]), kkt_seed = number(argv[5]);
        require(n >= 32 && n <= (1u << 22) && d >= 1 && d <= 512 &&
                static_cast<std::uint64_t>(n) * d <= (1u << 27), "diagnostic input outside limits");
        const benchmark_continuation::Spec spec{argv[1], static_cast<int>(n), static_cast<int>(d), 0};
        Graph graph;
        if (benchmark_attachments::known(spec.family))
            graph = benchmark_attachments::make_fixture(spec, graph_seed).graph;
        else {
            require(spec.family == "gnm_random" || spec.family == "line_metric" ||
                    spec.family == "line_random" || spec.family == "grid2d_metric" ||
                    spec.family == "grid2d_random", "unsupported diagnostic family");
            graph = benchmark_crossover::make_fixture({spec.family, spec.n, spec.density}, graph_seed).graph;
        }
        require(graph.size() == static_cast<std::size_t>(n) * d, "incorrect edge count");
        const auto reference = kruskal(graph, spec.n);
        benchmark_validation::certify_mst(graph, reference, spec.n);
        Ids expected;
        for (const auto& edge : reference)
            require(expected.insert(std::get<3>(edge)).second, "duplicate certified edge ID");
        const auto case_id = benchmark_continuation::case_id(spec);
        const auto input_hash = fingerprint(graph, spec.n, true), topology_hash = fingerprint(graph, spec.n, false);
        std::cerr << "reference_certificate_v1 {\"case_id\":\"" << case_id
                  << "\",\"graph_seed\":" << graph_seed << ",\"kkt_seed\":" << kkt_seed
                  << ",\"n\":" << n << ",\"m\":" << graph.size()
                  << ",\"input_fingerprint\":" << input_hash << ",\"topology_fingerprint\":" << topology_hash
                  << ",\"validation\":\"pass\"}\n";
        kkt_work::WorkStats work[3];
        for (int algorithm = 0; algorithm < 3; ++algorithm) {
            Ids actual;
            {
                kkt_work::ScopedWorkStats scope(work[algorithm]);
                problem input(spec.n, graph);
                actual = algorithm == 0 ? kkt(input, kkt_seed) :
                    (algorithm == 1 ? compacting_boruvka(input) : benchmark_retention::multigraph_boruvka(input));
            }
            require(actual == expected, "instrumented solver differs from certified MST");
            require(work[algorithm].current_depth == 0, "instrumented scope did not unwind");
            require(work[algorithm].contraction_edge_visits <=
                    (algorithm == 1 ? 4 : 3) * work[algorithm].contraction_edges, "contraction scan bound exceeded");
            if (algorithm == 0) require(work[algorithm].hash_insert_items == expected.size(), "KKT public-set counter mismatch");
            else require(work[algorithm].hash_insert_items == 0 && work[algorithm].kkt_calls == 0 &&
                    work[algorithm].verifier_calls == 0 && work[algorithm].sampling_calls == 0,
                    "continuation invoked sampling/verifier or changed hash accounting");
        }
        require(work[0].sampling_edge_visits == work[0].verifier_edges &&
                work[0].sampling_calls == work[0].verifier_calls, "KKT sample/verifier counters differ");
        const auto compact_rounds = trace(graph, spec.n, false, expected);
        const auto retained_rounds = trace(graph, spec.n, true, expected);
        check_trace(compact_rounds, work[1]); check_trace(retained_rounds, work[2]);
        if (retained_rounds.size() >= 2) require(work[0].root_after_two_vertices == retained_rounds[1].output_vertices &&
                work[0].root_after_two_edges == retained_rounds[1].output_edges, "KKT and MB first two contractions differ");
        std::cout << "{\"schema\":\"retention_control_work_v1\",\"validation\":\"pass\",\"case_id\":\"" << case_id
                  << "\",\"family\":\"" << spec.family << "\",\"n\":" << n << ",\"m\":" << graph.size()
                  << ",\"density\":" << d << ",\"graph_seed\":" << graph_seed << ",\"kkt_seed\":" << kkt_seed
                  << ",\"input_fingerprint\":" << input_hash << ",\"topology_fingerprint\":" << topology_hash
                  << ",\"certified_output_items\":" << expected.size() << ",\"algorithms\":{";
        const char* names[] = {"kkt", "compacting_boruvka", "multigraph_boruvka"};
        for (int algorithm = 0; algorithm < 3; ++algorithm) {
            if (algorithm) std::cout << ',';
            std::cout << '"' << names[algorithm] << "\":{\"hash_insert_items_status\":\""
                      << (algorithm == 0 ? "measured" : "unmeasured") << "\",\"work\":";
            emit_stats(work[algorithm], algorithm == 0);
            std::cout << '}';
        }
        std::cout << "},\"rounds\":{\"compacting_boruvka\":";
        emit_rounds(compact_rounds); std::cout << ",\"multigraph_boruvka\":"; emit_rounds(retained_rounds);
        std::cout << "}}\n";
        std::cout.flush(); require(static_cast<bool>(std::cout), "failed to emit diagnostic JSON");
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n'; return 1;
    }
}
