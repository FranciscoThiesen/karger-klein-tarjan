// Untimed logical-work and contraction diagnostics for lifted/attachment models.
// Counter scopes match continuation_search's public tuple-input boundary. All
// certificates, result checks and component-ledger reconstruction are outside
// those scopes; this executable intentionally contains no timers.
#include "search_fixtures.hpp"
#include "core_attachment_fixtures.hpp"
#include "component_moments.hpp"
#include "mst_certificate.hpp"
#include "work_metrics.hpp"
#include "../kkt/kkt.hpp"
#include "../kruskal/kruskal.hpp"

#include <cstdint>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_set>
#include <utility>
#include <vector>

#ifndef KKT_ENABLE_WORK_STATS
#error "search_work requires instrumented production object files"
#endif

std::pair<std::vector<int>, problem> boruvka_step(const problem& input);

namespace {
using benchmark_continuation::Spec;
using benchmark_fixtures::Graph;
using Ids = std::unordered_set<int>;

void require(bool value, const std::string& message) {
    if (!value) throw std::runtime_error(message);
}

int fixture_edge_count(const Spec& spec) {
    if (benchmark_attachments::known(spec.family)) return benchmark_attachments::edge_count(spec);
    return benchmark_search::edge_count(spec);
}

Graph fixture(const Spec& spec, unsigned int seed) {
    if (benchmark_attachments::known(spec.family)) return benchmark_attachments::make_fixture(spec, seed).graph;
    return benchmark_search::make_fixture(spec, seed).graph;
}

unsigned int number(const std::string& value) {
    require(!value.empty() && value.find_first_not_of("0123456789") == std::string::npos,
            "invalid unsigned integer: " + value);
    const auto parsed = std::stoull(value);
    require(parsed <= std::numeric_limits<unsigned int>::max(), "unsigned integer overflow");
    return static_cast<unsigned int>(parsed);
}

struct Options {
    Spec spec{"", 0, 0, 0};
    unsigned int graph_seed = 17;
    unsigned int kkt_seed = 0;
};

Options options(int argc, char** argv) {
    Options result;
    std::unordered_set<std::string> seen;
    for (int i = 1; i < argc; ++i) {
        const std::string flag = argv[i];
        require(seen.insert(flag).second, "duplicate option: " + flag);
        require(++i < argc, flag + " requires a value");
        const std::string value = argv[i];
        if (flag == "--family") result.spec.family = value;
        else if (flag == "--graph-seed") result.graph_seed = number(value);
        else if (flag == "--kkt-seed") result.kkt_seed = number(value);
        else if (flag == "--n" || flag == "--density") {
            const auto parsed = number(value);
            require(parsed <= static_cast<unsigned int>(std::numeric_limits<int>::max()),
                    flag + " exceeds integer range");
            if (flag == "--n") result.spec.n = static_cast<int>(parsed);
            else result.spec.density = static_cast<int>(parsed);
        } else throw std::runtime_error("unknown option: " + flag);
    }
    require(seen.count("--family") && seen.count("--n") && seen.count("--density"),
            "--family, --n and --density are required");
    // Validate exact model, dimensions and all integer/edge limits before allocation.
    (void)fixture_edge_count(result.spec);
    return result;
}

Ids edge_ids(const Graph& graph) {
    Ids ids;
    ids.reserve(graph.size());
    for (const auto& edge : graph)
        require(ids.insert(std::get<3>(edge)).second, "reference repeats an edge ID");
    return ids;
}

std::uint64_t fingerprint(const Graph& graph, int n, bool include_weights) {
    std::uint64_t value = UINT64_C(14695981039346656037);
    const auto append = [&](int number) {
        const auto bits = static_cast<std::uint32_t>(number);
        for (unsigned int shift = 0; shift < 32; shift += 8) {
            value ^= (bits >> shift) & 0xffu;
            value *= UINT64_C(1099511628211);
        }
    };
    append(n);
    for (const auto& [u, v, weight, id] : graph) {
        append(u); append(v); if (include_weights) append(weight); append(id);
    }
    return value;
}

struct Round {
    int input_vertices;
    std::size_t input_edges;
    int output_vertices;
    std::size_t output_edges;
    std::vector<int> selected_ids;
    int component_count = 0;
    std::uint64_t sum_squared_sizes = 0;
    int largest_component = 0;
};

Ids compacting_boruvka(problem& input, std::vector<Round>& trace) {
    std::vector<int> selected_ids;
    while (!input.graph_edges.empty()) {
        auto [selected, reduced] = boruvka_step(input);
        selected_ids.insert(selected_ids.end(), selected.begin(), selected.end());
        trace.push_back({input.num_vertices, input.graph_edges.size(), reduced.num_vertices,
                         reduced.graph_edges.size(), std::move(selected)});
        input = std::move(reduced);
    }
    Ids result;
    result.reserve(selected_ids.size());
    result.insert(selected_ids.begin(), selected_ids.end());
    KKT_WORK_ADD(hash_insert_items, selected_ids.size());
    return result;
}

void write_stats(const kkt_work::WorkStats& stats) {
    std::cout << '{';
    for (const auto& field : benchmark_work::fields)
        std::cout << '"' << field.name << "\":" << stats.*field.member << ',';
    std::cout << "\"total_work_proxy\":" << benchmark_work::total_work_proxy(stats) << '}';
}

void run(const Options& config) {
    const auto& spec = config.spec;
    const auto case_id = benchmark_continuation::case_id(spec);
    require(kkt_work::active == nullptr, "unexpected active work collector at setup");
    const Graph graph = fixture(spec, config.graph_seed);
    require(graph.size() == static_cast<std::size_t>(fixture_edge_count(spec)),
            "fixture edge count differs from validated target");
    const auto reference = kruskal(graph, spec.n);
    benchmark_validation::certify_mst(graph, reference, spec.n);
    const auto expected = edge_ids(reference);
    std::int64_t mst_weight = 0;
    for (const auto& edge : reference) mst_weight += std::get<2>(edge);
    const auto input_hash = fingerprint(graph, spec.n, true);
    const auto topology_hash = fingerprint(graph, spec.n, false);
    std::cerr << "reference_certificate_v1 {\"case_id\":\"" << case_id
              << "\",\"graph_seed\":" << config.graph_seed << ",\"kkt_seed\":" << config.kkt_seed
              << ",\"n\":" << spec.n << ",\"m\":" << graph.size()
              << ",\"input_fingerprint\":" << input_hash
              << ",\"topology_fingerprint\":" << topology_hash << ",\"validation\":\"pass\"}\n";
    require(static_cast<bool>(std::cerr), "failed to write reference certificate marker");

    kkt_work::WorkStats kkt_stats, compact_stats;
    std::vector<Round> trace;
    for (int algorithm = 0; algorithm < 2; ++algorithm) {
        auto& stats = algorithm == 0 ? kkt_stats : compact_stats;
        Ids result;
        {
            kkt_work::ScopedWorkStats scope(stats);
            problem input(spec.n, graph);
            result = algorithm == 0 ? kkt(input, config.kkt_seed) : compacting_boruvka(input, trace);
        }
        require(kkt_work::active == nullptr, "work collector escaped its solver scope");
        require(result == expected, "work solver differs from independently certified unique MST IDs");
        require(stats.current_depth == 0 && stats.contraction_calls > 0 &&
                stats.contraction_edges >= graph.size() && stats.filtered_edges <= stats.verifier_edges,
                "invalid work counters");
        if (algorithm == 0)
            require(stats.kkt_calls > 0 && stats.sampling_calls == stats.verifier_calls &&
                    stats.sampling_edge_visits == stats.verifier_edges,
                    "KKT sampling/verifier work mismatch");
        else
            require(stats.kkt_calls == 0 && stats.verifier_calls == 0 && stats.sampling_calls == 0,
                    "compactor unexpectedly recursed, sampled or verified");
        require(stats.hash_insert_items == expected.size(), "result hash insertion count differs from MST size");
    }

    // Trace storage is uncounted auxiliary diagnostics. Reconstruct original
    // components only after all algorithm counter scopes have finished.
    benchmark_diagnostics::ComponentMoments moments(graph, spec.n);
    std::uint64_t input_edges = 0, input_vertices = 0, output_edges = 0, output_vertices = 0;
    std::size_t selected_total = 0;
    for (auto& round : trace) {
        require(!round.selected_ids.empty() && round.output_vertices <= round.input_vertices / 2 &&
                round.output_edges < round.input_edges, "invalid contraction progress");
        input_edges += round.input_edges; input_vertices += round.input_vertices;
        output_edges += round.output_edges; output_vertices += round.output_vertices;
        selected_total += round.selected_ids.size();
        moments.accept_selected(round.selected_ids);
        require(moments.count() == (round.output_vertices == 0 ? 1 : round.output_vertices),
                "original component ledger disagrees with quotient vertex count");
        round.component_count = moments.count();
        round.sum_squared_sizes = moments.sum_squares();
        round.largest_component = moments.max_size();
    }
    require(selected_total == expected.size() && moments.count() == 1,
            "trace did not produce the complete original MST");
    require(compact_stats.contraction_calls == trace.size() && compact_stats.contraction_edges == input_edges &&
            compact_stats.contraction_vertices == input_vertices && compact_stats.contraction_output_edges == output_edges &&
            compact_stats.contraction_output_vertices == output_vertices,
            "compactor counters disagree with full contraction trajectory");
    if (trace.size() >= 2)
        require(kkt_stats.root_after_two_vertices == static_cast<std::uint64_t>(trace[1].output_vertices) &&
                kkt_stats.root_after_two_edges == trace[1].output_edges,
                "KKT root contraction counters disagree with compactor trajectory");
    else
        require(kkt_stats.root_after_two_vertices == 0 && kkt_stats.root_after_two_edges == 0,
                "KKT recorded a nonexistent second contraction");
    // Hierarchy/distance and attachment core-only shuffled weights all keep
    // local stars cheaper than external edges. Global-random weights do not.
    if (spec.family.find("_random") == std::string::npos) {
        const bool attachment = benchmark_attachments::known(spec.family);
        const int b = attachment ? benchmark_attachments::block_size(spec.family) : spec.family.back() - '0';
        const std::size_t local = static_cast<std::size_t>(spec.n / b) * (b - 1);
        const std::size_t core_edges = attachment ? graph.size() - local : (graph.size() - local) / (b * b);
        require(trace.front().output_vertices == spec.n / b && trace.front().output_edges == core_edges,
                "first structured contraction did not recover exact core dimensions");
    }

    // One complete JSON document is emitted only after both certified outputs
    // and every trace/counter consistency gate have passed. There are no times.
    std::cout << "{\"schema\":\"search_work_v1\",\"case_id\":\"" << case_id
              << "\",\"family\":\"" << spec.family << "\",\"n\":" << spec.n
              << ",\"m\":" << graph.size() << ",\"density\":" << spec.density
              << ",\"intrusion_per_mille\":0,\"graph_seed\":" << config.graph_seed
              << ",\"kkt_seed\":" << config.kkt_seed << ",\"input_fingerprint\":" << input_hash
              << ",\"topology_fingerprint\":" << topology_hash << ",\"mst_edge_count\":" << expected.size()
              << ",\"mst_total_weight\":" << mst_weight << ",\"validation\":\"pass\",\"algorithms\":{\"kkt\":";
    write_stats(kkt_stats);
    std::cout << ",\"compacting_boruvka\":";
    write_stats(compact_stats);
    std::cout << "},\"trace\":[";
    for (std::size_t i = 0; i < trace.size(); ++i) {
        if (i != 0) std::cout << ',';
        const auto& round = trace[i];
        std::cout << "{\"round\":" << i + 1 << ",\"input_vertices\":" << round.input_vertices
                  << ",\"input_edges\":" << round.input_edges << ",\"selected_edges\":" << round.selected_ids.size()
                  << ",\"output_vertices\":" << round.output_vertices << ",\"output_edges\":" << round.output_edges
                  << ",\"component_count\":" << round.component_count
                  << ",\"sum_squared_sizes\":" << round.sum_squared_sizes
                  << ",\"largest_component\":" << round.largest_component << '}';
    }
    std::cout << "]}\n";
    std::cout.flush();
    require(static_cast<bool>(std::cout), "failed to write work JSON");
}
} // namespace

int main(int argc, char** argv) {
    if (argc == 2 && std::string(argv[1]) == "--help") {
        std::cout << "Usage: search_work --family NAME --n N --density D [--graph-seed SEED] [--kkt-seed SEED]\n"
                     "Supports six lifted and sixteen attachment families; defaults are graph seed 17, KKT seed 0.\n"
                     "Outputs one certified search_work_v1 JSON with KKT/compactor work counters and a compactor trace.\n"
                     "Logical counters are not elapsed time, CPU instructions, allocated bytes or distinct root edges.\n";
        return 0;
    }
    try { run(options(argc, argv)); }
    catch (const std::exception& error) {
        std::cerr << "search work: " << error.what() << '\n';
        return 1;
    }
    return 0;
}
