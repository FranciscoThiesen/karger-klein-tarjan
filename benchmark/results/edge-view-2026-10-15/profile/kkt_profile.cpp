// Standalone diagnostic driver. No solver or fixture implementation is changed.
// Build only after the root releases the current paired timing capture.
#define KKT_RETENTION_HARNESS_NO_MAIN
#include "../../../retention_control.cpp"

#include <poll.h>
#include <sys/resource.h>
#include <unistd.h>

#if !defined(__APPLE__) || !defined(__aarch64__)
#error "This diagnostic is prepared for the frozen native Apple arm64 objects"
#endif
#ifndef KKT_EXPERIMENT_EDGE_VIEW
#error "The profiling recipe must select the frozen Edge-view KKT object"
#endif

namespace {
constexpr unsigned int profile_graph_seed = 6000011;
constexpr unsigned int profile_kkt_seed = 1423;
constexpr int profile_calls = 4;

void profile_marker(const char* event, int repetition = -1) {
    std::cout << "profile_v1 {\"event\":\"" << event
              << "\",\"repetition\":" << repetition
              << ",\"utc_ns\":" << clock_nanoseconds(CLOCK_REALTIME, "CLOCK_REALTIME")
              << "}\n" << std::flush;
    require(static_cast<bool>(std::cout), "failed to write profile marker");
}

// Match the six-solver harness's public KKT boundary: tuple conversion,
// production kkt(), and destruction of its temporary problem are included.
// This named frame separates those stacks from certification and validation.
__attribute__((noinline)) Ids profile_kkt_public_boundary(const Graph& graph, int n) {
    return [&] {
        problem input(n, graph);
        return kkt(input, profile_kkt_seed);
    }();
}

// Exact equality to an independently certified unique-weight MST proves each
// returned ID set. Validation and result destruction are outside the KKT frame.
__attribute__((noinline)) void profile_validate_and_release(Ids result, const Ids& expected) {
    require(result == expected, "profile KKT returned incorrect MST IDs");
}

void profile_wait_for_release() {
    pollfd input{STDIN_FILENO, POLLIN, 0};
    require(::poll(&input, 1, 60000) == 1 && (input.revents & POLLIN),
            "profile release was not readable within 60 seconds");
    char token = 0;
    require(::read(STDIN_FILENO, &token, 1) == 1 && token == 'G',
            "profile requires exactly the release byte G");
}

void profile_run() {
    // Whole-process safety bounds, including generation and certification.
    // External owned-process-group RSS and lifecycle monitoring is also required.
    const rlimit cpu_limit{600, 600};
    if (::setrlimit(RLIMIT_CPU, &cpu_limit) != 0)
        throw std::system_error(errno, std::generic_category(), "setrlimit(RLIMIT_CPU)");
    ::alarm(900);

    const Spec spec{"leaf_hierarchy4", 2097152, 16, 0};
    const int expected_edges = fixture_edge_count(spec);
    require(expected_edges == 33554432, "unexpected profiling fixture size");
    profile_marker("GENERATION_BEGIN");
    const Graph graph = fixture(spec, profile_graph_seed);
    require(graph.size() == static_cast<std::size_t>(expected_edges), "fixture edge target mismatch");
    profile_marker("CERTIFICATE_BEGIN");
    const Graph oracle = kruskal(graph, spec.n);
    benchmark_validation::certify_mst(graph, oracle, spec.n);
    const Ids expected = ids(oracle);
    const auto input_hash = fingerprint(graph, spec.n, true);
    const auto topology_hash = fingerprint(graph, spec.n, false);

    std::cout << "profile_v1 {\"event\":\"READY\",\"pid\":" << ::getpid()
              << ",\"family\":\"leaf_hierarchy4\",\"n\":" << spec.n
              << ",\"m\":" << graph.size() << ",\"density\":16"
              << ",\"graph_seed\":" << profile_graph_seed
              << ",\"kkt_seed\":" << profile_kkt_seed
              << ",\"calls\":" << profile_calls
              << ",\"input_fingerprint\":" << input_hash
              << ",\"topology_fingerprint\":" << topology_hash
              << ",\"validation\":\"pass\"}\n" << std::flush;
    require(static_cast<bool>(std::cout), "failed to write READY marker");
    profile_wait_for_release();

    for (int repetition = 0; repetition < profile_calls; ++repetition) {
        profile_marker("KKT_BEGIN", repetition);
        auto result = profile_kkt_public_boundary(graph, spec.n);
        profile_marker("KKT_END", repetition);
        profile_validate_and_release(std::move(result), expected);
        profile_marker("VALIDATED", repetition);
    }
    profile_marker("DONE");
    // Keep the alarm active through graph/reference destruction.
}
} // namespace

int main() {
    try { profile_run(); }
    catch (const std::exception& error) {
        std::cerr << "KKT profile: " << error.what() << '\n';
        return 1;
    }
    return 0;
}
