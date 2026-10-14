// Export actual small attachment fixtures for offline views.
// No timers, native graph layout, invented graph edges, or algorithm dispatch.
#include "core_attachment_fixtures.hpp"
#include "benchmark/mst_certificate.hpp"
#include "kkt/kkt.hpp"
#include "kruskal/kruskal.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_set>
#include <vector>

namespace {
using benchmark_continuation::Spec;
using benchmark_fixtures::Graph;

void require(bool value, const std::string& message) {
    if (!value) throw std::runtime_error(message);
}

unsigned int number(const std::string& value) {
    require(!value.empty() && value.find_first_not_of("0123456789") == std::string::npos,
            "invalid unsigned integer: " + value);
    const auto parsed = std::stoull(value);
    require(parsed <= std::numeric_limits<unsigned int>::max(), "unsigned integer overflow");
    return static_cast<unsigned int>(parsed);
}

struct Options {
    Spec spec{"", 1024, 2, 0};
    unsigned int graph_seed = 5009;
    unsigned int kkt_seed = 149;
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
    require(seen.count("--family"), "--family is required");
    const int edges = benchmark_attachments::edge_count(result.spec);
    require(result.spec.n <= 4096 && edges <= 65536,
            "offline visual export is limited to 4096 vertices and 65536 edges");
    return result;
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

void write_ints(const std::vector<int>& values) {
    std::cout << '[';
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i != 0) std::cout << ',';
        std::cout << values[i];
    }
    std::cout << ']';
}

void run(const Options& config) {
    const auto& spec = config.spec;
    const auto generated = benchmark_attachments::make_fixture(spec, config.graph_seed);
    const auto& graph = generated.graph;
    const int b = benchmark_attachments::block_size(spec.family);
    const int q = spec.n / b, local = spec.n - q;
    require(generated.block_size == b && generated.original_to_label.size() == static_cast<std::size_t>(spec.n),
            "invalid exported block/label metadata");
    require(graph.size() == static_cast<std::size_t>(benchmark_attachments::edge_count(spec)),
            "exported graph misses its edge budget");
    const auto reference = kruskal(graph, spec.n);
    benchmark_validation::certify_mst(graph, reference, spec.n);
    std::unordered_set<int> expected;
    std::vector<int> selected;
    std::int64_t mst_weight = 0;
    for (const auto& edge : reference) {
        const int id = std::get<3>(edge);
        require(expected.insert(id).second, "reference has duplicate IDs");
        selected.push_back(id);
        mst_weight += std::get<2>(edge);
    }
    problem input(spec.n, graph);
    require(kkt(input, config.kkt_seed) == expected, "KKT differs from independently certified MST");
    std::sort(selected.begin(), selected.end());

    // Check the labels and core metadata used by an eventual renderer against
    // actual graph tuples. The MST certificate itself validates only the graph.
    std::vector<int> original(spec.n, -1);
    for (int vertex = 0; vertex < spec.n; ++vertex) {
        const int label = generated.original_to_label[vertex];
        require(label >= 0 && label < spec.n && original[label] == -1, "labels are not a permutation");
        original[label] = vertex;
    }
    std::vector<const Graph::value_type*> by_id(graph.size(), nullptr);
    for (const auto& edge : graph) by_id[std::get<3>(edge)] = &edge;
    for (int id = 0; id < local; ++id) {
        const auto& [u, v, weight, original_id] = *by_id[id];
        (void)weight; (void)original_id;
        const int center = id / (b - 1), clone = id % (b - 1) + 1;
        require(original[u] == b * center && original[v] == b * center + clone,
                "local star metadata does not match actual endpoints");
    }
    const bool random = spec.family.find("_random") != std::string::npos;
    const std::size_t external = graph.size() - static_cast<std::size_t>(local);
    require(generated.core_graph.size() == external, "core metadata has wrong size");
    std::vector<bool> core_ids(external), core_ranks(external);
    for (const auto& [u, v, rank, id] : generated.core_graph) {
        require(u >= 0 && u < q && v >= 0 && v < q && u != v,
                "invalid metadata core endpoint");
        require(id >= 0 && static_cast<std::size_t>(id) < external && !core_ids[id], "invalid metadata core ID");
        require(rank >= 1 && static_cast<std::size_t>(rank) <= external && !core_ranks[rank - 1],
                "invalid metadata core rank");
        core_ids[id] = true; core_ranks[rank - 1] = true;
        const auto& [a, c, weight, original_id] = *by_id[local + id];
        require(original[a] / b == u && original[c] / b == v && original_id == local + id,
                "metadata core pair does not match projected original endpoints");
        if (!random) require(weight == local + rank, "metadata core rank does not match actual cost");
    }
    const auto input_hash = fingerprint(graph, spec.n, true);
    const auto topology_hash = fingerprint(graph, spec.n, false);
    const auto case_id = benchmark_continuation::case_id(spec);
    std::cerr << "attachment_view_certificate_v1 {\"case_id\":\"" << case_id
              << "\",\"graph_seed\":" << config.graph_seed << ",\"kkt_seed\":" << config.kkt_seed
              << ",\"n\":" << spec.n << ",\"m\":" << graph.size()
              << ",\"input_fingerprint\":" << input_hash << ",\"validation\":\"pass\"}\n";
    require(static_cast<bool>(std::cerr), "failed to write certificate marker");

    // Fingerprints are decimal strings so JavaScript viewers preserve all 64 bits.
    std::cout << "{\"schema\":\"attachment_view_v1\",\"case_id\":\"" << case_id
              << "\",\"family\":\"" << spec.family << "\",\"n\":" << spec.n
              << ",\"m\":" << graph.size() << ",\"density\":" << spec.density
              << ",\"graph_seed\":" << config.graph_seed << ",\"kkt_seed\":" << config.kkt_seed
              << ",\"block_size\":" << b << ",\"core_vertices\":" << q
              << ",\"local_star_edges\":" << local << ",\"input_fingerprint\":\"" << input_hash
              << "\",\"topology_fingerprint\":\"" << topology_hash
              << "\",\"mst_total_weight\":" << mst_weight << ",\"validation\":\"pass\""
                 ",\"layout_note\":\"No intrinsic geometry; any plotted layout is illustrative.\""
                 ",\"core_rank_note\":\"Generator core priorities; global-random actual costs are independently permuted.\""
                 ",\"original_to_label\":";
    write_ints(generated.original_to_label);
    std::cout << ",\"certified_mst_ids\":";
    write_ints(selected);
    std::cout << ",\"edges\":[";
    for (std::size_t i = 0; i < graph.size(); ++i) {
        if (i != 0) std::cout << ',';
        const auto& [u, v, weight, id] = graph[i];
        std::cout << "{\"from\":" << u << ",\"to\":" << v << ",\"weight\":" << weight << ",\"id\":" << id << '}';
    }
    std::cout << "],\"core_edges\":[";
    for (std::size_t i = 0; i < generated.core_graph.size(); ++i) {
        if (i != 0) std::cout << ',';
        const auto& [u, v, rank, id] = generated.core_graph[i];
        std::cout << "{\"from\":" << u << ",\"to\":" << v << ",\"rank\":" << rank
                  << ",\"id\":" << id << ",\"original_edge_id\":" << local + id << '}';
    }
    std::cout << "]}\n";
    std::cout.flush();
    require(static_cast<bool>(std::cout), "failed to write visual JSON");
}
} // namespace

int main(int argc, char** argv) {
    if (argc == 2 && std::string(argv[1]) == "--help") {
        std::cout << "Usage: export_attachment_view --family NAME [--n N] [--density D]\n"
                     "       [--graph-seed SEED] [--kkt-seed SEED]\n"
                     "Defaults: n=1024, density=2, graph seed=5009, KKT seed=149.\n"
                     "Only attachment families; bounded to n<=4096 and m<=65536. No timings.\n";
        return 0;
    }
    try { run(options(argc, argv)); }
    catch (const std::exception& error) {
        std::cerr << "attachment view export: " << error.what() << '\n';
        return 1;
    }
    return 0;
}
