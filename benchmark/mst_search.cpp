// Five unchanged MST algorithms on one independently certified input.
// "boruvka" is the original public baseline; "compacting_boruvka" repeats
// production boruvka_step with the same continuation/output operations as
// continuation_search.cpp. No result representation is normalized while timed.
#include "crossover_fixtures.hpp"
#include "continuation_fixtures.hpp"
#include "search_fixtures.hpp"
#include "core_attachment_fixtures.hpp"
#include "mst_certificate.hpp"
#include "../kkt/kkt.hpp"
#include "../kruskal/kruskal.hpp"
#include "../prim/prim.hpp"
#include "../boruvka/boruvka.hpp"

#include <algorithm>
#include <array>
#include <cerrno>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <system_error>
#include <time.h>
#include <tuple>
#include <unordered_set>
#include <utility>
#include <vector>

#ifdef KKT_ENABLE_WORK_STATS
#error "mst_search is a timing-only target; compile without work counters"
#endif

// Existing production entry point, also used by continuation_search.cpp.
std::pair<std::vector<int>, problem> boruvka_step(const problem& input);

namespace {
using Graph = benchmark_fixtures::Graph;
using Spec = benchmark_continuation::Spec;
using Ids = std::unordered_set<int>;
using Clock = std::chrono::steady_clock;
constexpr std::array<const char*, 5> algorithms = {
    "kkt", "compacting_boruvka", "kruskal", "prim", "boruvka"
};
constexpr int vertex_limit = 1 << 22;
constexpr std::int64_t edge_limit = INT64_C(1) << 27;

void require(bool value, const std::string& message) {
    if (!value) throw std::runtime_error(message);
}

unsigned int number(const std::string& value) {
    require(!value.empty() && value.find_first_not_of("0123456789") == std::string::npos,
            "invalid unsigned integer: " + value);
    const auto result = std::stoull(value);
    require(result <= std::numeric_limits<unsigned int>::max(), "integer out of range");
    return static_cast<unsigned int>(result);
}

struct Options {
    Spec spec{"", 0, 0, 0};
    unsigned int graph_seed = 17;
    unsigned int kkt_seed = 0;
    int repetitions = 5;
    int warmups = 1;
};

Options options(int argc, char** argv) {
    Options result;
    std::unordered_set<std::string> seen;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        require(seen.insert(arg).second, "duplicate option: " + arg);
        require(++i < argc, arg + " requires a value");
        const std::string value = argv[i];
        if (arg == "--family") result.spec.family = value;
        else if (arg == "--graph-seed") result.graph_seed = number(value);
        else if (arg == "--kkt-seed") result.kkt_seed = number(value);
        else if (arg == "--n" || arg == "--density" ||
                 arg == "--repetitions" || arg == "--warmups") {
            const auto parsed = number(value);
            require(parsed <= static_cast<unsigned int>(std::numeric_limits<int>::max()),
                    arg + " exceeds integer range");
            const int count = static_cast<int>(parsed);
            if (arg == "--n") result.spec.n = count;
            else if (arg == "--density") result.spec.density = count;
            else if (arg == "--repetitions") result.repetitions = count;
            else result.warmups = count;
        } else throw std::runtime_error("unknown option: " + arg);
    }
    require(seen.count("--family") && seen.count("--n") && seen.count("--density"),
            "--family, --n and --density are required");
    require(result.repetitions >= 5 && result.repetitions <= 100 && result.repetitions % 5 == 0,
            "repetitions must be a multiple of five in [5,100]");
    require(result.warmups >= 1 && result.warmups <= 100, "warmups must be in [1,100]");
    require(result.spec.n >= 32 && result.spec.n <= vertex_limit,
            "n must be in [32,4194304]");
    require(result.spec.density > 0 &&
            static_cast<std::int64_t>(result.spec.n) * result.spec.density <= edge_limit,
            "edge target must be positive and at most 134217728");
    return result;
}

bool crossover_family(const std::string& family) {
    return std::find(benchmark_crossover::families.begin(), benchmark_crossover::families.end(),
                     family) != benchmark_crossover::families.end();
}

// Validate the model-specific domain and exact target before any graph allocation.
int fixture_edge_count(const Spec& spec) {
    if (benchmark_attachments::known(spec.family))
        return benchmark_attachments::edge_count(spec);
    if (benchmark_search::known(spec.family))
        return benchmark_search::edge_count(spec);
    if (crossover_family(spec.family))
        return benchmark_crossover::edge_count({spec.family, spec.n, spec.density});
    return benchmark_continuation::edge_count(spec);
}

Graph fixture(const Spec& spec, unsigned int seed) {
    if (benchmark_attachments::known(spec.family))
        return benchmark_attachments::make_fixture(spec, seed).graph;
    if (benchmark_search::known(spec.family))
        return benchmark_search::make_fixture(spec, seed).graph;
    if (crossover_family(spec.family)) {
        auto generated = benchmark_crossover::make_fixture({spec.family, spec.n, spec.density}, seed);
        std::cerr << "crossover_topology_attempts=" << generated.topology_attempts << '\n';
        return std::move(generated.graph);
    }
    // The one-case CLI fixes all continuation cases at p=0.
    return benchmark_continuation::make_fixture(spec, seed).graph;
}

// This is continuation_search.cpp's record_trace=false body, with the disabled
// work-counter macro omitted. Keep all continuation and result operations equal.
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

Ids ids(const Graph& tree) {
    Ids result;
    result.reserve(tree.size());
    for (const auto& edge : tree) result.insert(std::get<3>(edge));
    return result;
}

// Same public-result checks as diverse_benchmark.cpp. The independent reference
// certificate proves the exact unique-weight ID set; tuple membership additionally
// checks endpoint orientation and original cost for the three tuple-returning APIs.
bool valid_tree(const Graph& tree, const Ids& expected,
                const std::vector<const Graph::value_type*>& by_id) {
    if (tree.size() != expected.size() || ids(tree) != expected) return false;
    for (const auto& edge : tree) {
        int u, v, cost, id;
        std::tie(u, v, cost, id) = edge;
        if (id < 0 || static_cast<std::size_t>(id) >= by_id.size()) return false;
        const auto& original = *by_id[id];
        const int a = std::get<0>(original), b = std::get<1>(original);
        if (cost != std::get<2>(original) || !((u == a && v == b) || (u == b && v == a))) return false;
    }
    return true;
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
    for (const auto& [u, v, w, id] : graph) {
        append(u); append(v); if (include_weights) append(w); append(id);
    }
    return value;
}

std::int64_t clock_nanoseconds(clockid_t clock, const char* name) {
    timespec value{};
    if (clock_gettime(clock, &value) != 0)
        throw std::system_error(errno, std::generic_category(), name);
    constexpr std::int64_t billion = 1000000000;
    require(value.tv_sec >= 0 && value.tv_nsec >= 0 && value.tv_nsec < billion &&
            value.tv_sec <= (std::numeric_limits<std::int64_t>::max() - value.tv_nsec) / billion,
            std::string(name) + ": clock value outside nanosecond range");
    return static_cast<std::int64_t>(value.tv_sec) * billion + value.tv_nsec;
}

struct Measurement {
    std::int64_t elapsed_ns;
    std::int64_t utc_start_ns;
    std::int64_t utc_end_ns;
    std::int64_t process_cpu_start_ns;
    std::int64_t process_cpu_end_ns;
};

Measurement measure(int algorithm, const Graph& graph, int n, unsigned int seed,
                    const Ids& expected, const std::vector<const Graph::value_type*>& by_id) {
    bool valid = false;
    Measurement measured{};
    // Preserve diverse_benchmark's public tuple-input boundaries exactly. No
    // common return-type conversion is forced on any measured implementation.
    // UTC/CPU clock envelopes are slightly wider than the steady interval.
    if (algorithm < 2) {
        measured.utc_start_ns = clock_nanoseconds(CLOCK_REALTIME, "CLOCK_REALTIME");
        measured.process_cpu_start_ns = clock_nanoseconds(CLOCK_PROCESS_CPUTIME_ID, "CLOCK_PROCESS_CPUTIME_ID");
        const auto start = Clock::now();
        const auto result = [&] {
            problem input(n, graph);
            return algorithm == 0 ? kkt(input, seed) : compacting_boruvka(input);
        }();
        const auto finish = Clock::now();
        measured.process_cpu_end_ns = clock_nanoseconds(CLOCK_PROCESS_CPUTIME_ID, "CLOCK_PROCESS_CPUTIME_ID");
        measured.utc_end_ns = clock_nanoseconds(CLOCK_REALTIME, "CLOCK_REALTIME");
        measured.elapsed_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(finish-start).count();
        valid = result == expected;
    } else {
        const auto function = algorithm == 2 ? kruskal : (algorithm == 3 ? prim : boruvka);
        measured.utc_start_ns = clock_nanoseconds(CLOCK_REALTIME, "CLOCK_REALTIME");
        measured.process_cpu_start_ns = clock_nanoseconds(CLOCK_PROCESS_CPUTIME_ID, "CLOCK_PROCESS_CPUTIME_ID");
        const auto start = Clock::now();
        const auto result = function(graph, n);
        const auto finish = Clock::now();
        measured.process_cpu_end_ns = clock_nanoseconds(CLOCK_PROCESS_CPUTIME_ID, "CLOCK_PROCESS_CPUTIME_ID");
        measured.utc_end_ns = clock_nanoseconds(CLOCK_REALTIME, "CLOCK_REALTIME");
        measured.elapsed_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(finish-start).count();
        valid = valid_tree(result, expected, by_id);
    }
    // Each returned result is validated and destroyed after all finish clocks;
    // temporary KKT/compactor input destruction remains inside its original interval.
    require(valid, std::string(algorithms[algorithm]) + ": incorrect MST");
    require(measured.elapsed_ns > 0, "nonpositive elapsed time");
    require(measured.process_cpu_end_ns > measured.process_cpu_start_ns, "nonpositive process CPU time");
    // Realtime reversal is retained in the raw endpoints, never filtered.
    return measured;
}

void run(const Options& config) {
    const auto& spec = config.spec;
    const int expected_edges = fixture_edge_count(spec);
    const std::string case_id = benchmark_continuation::case_id(spec);
    std::cerr << "Running five-algorithm MST search " << case_id
              << " graph_seed=" << config.graph_seed << " kkt_seed=" << config.kkt_seed << '\n';
    const auto generation_start = Clock::now();
    const Graph graph = fixture(spec, config.graph_seed);
    const auto generation_finish = Clock::now();
    require(graph.size() == static_cast<std::size_t>(expected_edges), "fixture edge target mismatch");
    const auto oracle = kruskal(graph, spec.n);
    benchmark_validation::certify_mst(graph, oracle, spec.n);
    const auto certificate_finish = Clock::now();
    const Ids expected = ids(oracle);
    std::vector<const Graph::value_type*> by_id(graph.size());
    for (const auto& edge : graph) by_id[std::get<3>(edge)] = &edge;
    const auto input_hash = fingerprint(graph, spec.n, true);
    const auto topology_hash = fingerprint(graph, spec.n, false);
    std::cerr << "generation_seconds="
              << std::chrono::duration<double>(generation_finish-generation_start).count()
              << " reference_certificate_seconds="
              << std::chrono::duration<double>(certificate_finish-generation_finish).count() << '\n';
    // The certificate marker binds successful independent verification to the
    // exact input subsequently measured. Fixture names are fixed safe identifiers.
    std::cerr << "reference_certificate_v1 {\"case_id\":\"" << case_id
              << "\",\"graph_seed\":" << config.graph_seed
              << ",\"kkt_seed\":" << config.kkt_seed
              << ",\"n\":" << spec.n << ",\"m\":" << graph.size()
              << ",\"input_fingerprint\":" << input_hash
              << ",\"topology_fingerprint\":" << topology_hash
              << ",\"validation\":\"pass\"}\n";
    std::cout << "case_id,family,n,m,density,intrusion_per_mille,graph_seed,kkt_seed,"
                 "input_fingerprint,topology_fingerprint,phase,repetition,order,warmups,algorithm,"
                 "elapsed_ns,utc_start_ns,utc_end_ns,process_cpu_start_ns,process_cpu_end_ns,"
                 "process_cpu_elapsed_ns,validation\n";
    for (int phase = 0; phase < 2; ++phase) {
        const int count = phase == 0 ? config.warmups : config.repetitions;
        for (int repetition = 0; repetition < count; ++repetition) {
            for (int order = 0; order < 5; ++order) {
                // A full five-repetition cycle places each algorithm once in
                // every position. Warmups rotate by the same rule and are kept
                // as separately marked raw rows, never mixed into timing summaries.
                const int algorithm = (order + repetition) % 5;
                const auto result = measure(algorithm, graph, spec.n, config.kkt_seed, expected, by_id);
                std::cout << case_id << ',' << spec.family << ',' << spec.n << ',' << graph.size()
                          << ',' << spec.density << ",0," << config.graph_seed << ',' << config.kkt_seed
                          << ',' << input_hash << ',' << topology_hash << ',' << (phase == 0 ? "warmup" : "timed")
                          << ',' << repetition << ',' << order << ',' << config.warmups << ',' << algorithms[algorithm]
                          << ',' << result.elapsed_ns << ',' << result.utc_start_ns << ',' << result.utc_end_ns
                          << ',' << result.process_cpu_start_ns << ',' << result.process_cpu_end_ns
                          << ',' << result.process_cpu_end_ns-result.process_cpu_start_ns << ",pass\n";
                std::cout.flush();
                require(static_cast<bool>(std::cout), "failed to write CSV");
            }
        }
    }
}
} // namespace

int main(int argc, char** argv) {
    if (argc == 2 && std::string(argv[1]) == "--help") {
        std::cout << "Usage: " << argv[0]
                  << " --family NAME --n N --density D [--graph-seed SEED] [--kkt-seed SEED]\n"
                     "       [--repetitions N] [--warmups N]\n"
                     "Defaults: graph seed 17, KKT seed 0, 5 repetitions, 1 checked warmup.\n"
                     "Repetitions must be a multiple of five in [5,100]; warmups in [1,100].\n"
                     "Supports six lifted, sixteen leaf/community attachment, crossover and continuation families.\n"
                     "Attachment modes: hierarchy, distance, shuffled core, and global random; intrusion is fixed at zero.\n"
                     "Limits: n <= 4194304 and m <= 134217728, plus each fixture domain.\n"
                     "CSV retains both warmup and timed rows; UTC/CPU clocks are diagnostic envelopes.\n"
                     "boruvka is the original public baseline, not compacting_boruvka.\n";
        return 0;
    }
    try { run(options(argc, argv)); }
    catch (const std::exception& error) {
        std::cerr << "mst search: " << error.what() << '\n';
        return 1;
    }
    return 0;
}
