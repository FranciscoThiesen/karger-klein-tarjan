// Finite-range Google Benchmark fits for the frozen eighth-sampling candidate.
// This new main must link the eight recorded production objects unchanged.
#include "benchmark/benchmark.h"
#define KKT_RETENTION_HARNESS_NO_MAIN
#include "benchmark/retention_control.cpp"

#include <cstdio>
#include <fcntl.h>
#include <map>
#include <memory>
#include <sstream>
#include <unistd.h>

namespace current_complexity {
constexpr int measured_iterations = 2;
constexpr int benchmark_repetitions = 3;
constexpr std::array<int, 11> sizes = {
    1024, 2048, 4096, 8192, 16384, 32768,
    65536, 131072, 262144, 524288, 1048576
};

struct Configuration {
    std::string family;
    int algorithm;
    unsigned int graph_seed;
    unsigned int sampling_seed;
    bool descending;
};

using File = std::unique_ptr<FILE, int (*)(FILE*)>;
File exclusive_file(const char* path) {
    const int descriptor = open(path, O_WRONLY | O_CREAT | O_EXCL, 0600);
    if (descriptor < 0) throw std::system_error(errno, std::generic_category(), path);
    FILE* stream = fdopen(descriptor, "w");
    if (!stream) {
        const int saved = errno;
        close(descriptor);
        throw std::system_error(saved, std::generic_category(), path);
    }
    return File(stream, &std::fclose);
}

void write(FILE* file, const std::string& value) {
    require(std::fputs(value.c_str(), file) >= 0 && std::fflush(file) == 0,
            "failed to preserve raw complexity trace");
}

void trace(FILE* file, const Configuration& config, int n, std::size_t m,
           std::uint64_t input_hash, std::uint64_t topology_hash,
           int invocation, const char* phase, int iteration, const Measurement& measured) {
    std::ostringstream row;
    row << config.family << ',' << algorithms[config.algorithm] << ',' << n << ',' << m
        << ',' << static_cast<std::int64_t>(n) + static_cast<std::int64_t>(m)
        << ',' << config.graph_seed << ',' << config.sampling_seed
        << ',' << input_hash << ',' << topology_hash
        << ',' << (config.descending ? "descending" : "ascending")
        << ',' << invocation << ',' << phase << ',' << iteration
        << ',' << measured.elapsed_ns << ',' << measured.utc_start_ns << ',' << measured.utc_end_ns
        << ',' << measured.process_cpu_start_ns << ',' << measured.process_cpu_end_ns
        << ',' << measured.process_cpu_end_ns - measured.process_cpu_start_ns << ",pass\n";
    write(file, row.str());
}

struct Context {
    Configuration config;
    FILE* trace_file;
    std::map<int, int> invocations;
    bool failed = false;
};

void run_size(benchmark::State& state, Context& context) {
    try {
        require(!context.failed, "previous callback failed; no further solver calls");
        const auto& config = context.config;
        const int n = static_cast<int>(state.range(0));
        require(std::find(sizes.begin(), sizes.end(), n) != sizes.end(), "undeclared size");
        const int invocation = context.invocations[n]++;
        require(invocation < benchmark_repetitions, "unexpected benchmark callback repetition");
        const int density = config.family == "gnm_random" ? 16 : 32;
        const Spec spec{config.family, n, density, 0};
        const int target = fixture_edge_count(spec);
        const Graph graph = fixture(spec, config.graph_seed);
        require(graph.size() == static_cast<std::size_t>(target), "fixture edge target mismatch");
        const auto oracle = kruskal(graph, n);
        benchmark_validation::certify_mst(graph, oracle, n);
        const Ids expected = ids(oracle);
        std::vector<const Graph::value_type*> by_id(graph.size());
        for (const auto& edge : graph) by_id[std::get<3>(edge)] = &edge;
        const auto input_hash = fingerprint(graph, n, true);
        const auto topology_hash = fingerprint(graph, n, false);
        std::cerr << "complexity_certificate_v1 {\"family\":\"" << config.family
                  << "\",\"algorithm\":\"" << algorithms[config.algorithm]
                  << "\",\"n\":" << n << ",\"m\":" << graph.size()
                  << ",\"graph_seed\":" << config.graph_seed
                  << ",\"sampling_seed\":" << config.sampling_seed
                  << ",\"invocation\":" << invocation
                  << ",\"input_fingerprint\":" << input_hash
                  << ",\"topology_fingerprint\":" << topology_hash
                  << ",\"validation\":\"pass\"}\n";

        // The benchmark timer has not started before entering the State loop.
        // Each callback gets one checked warmup, retained as a separate raw row.
        const auto warmup = measure(config.algorithm, graph, n, config.sampling_seed, expected, by_id);
        trace(context.trace_file, config, n, graph.size(), input_hash, topology_hash,
              invocation, "warmup", 0, warmup);
        state.SetComplexityN(static_cast<std::int64_t>(n) + static_cast<std::int64_t>(graph.size()));
        state.counters["vertices"] = n;
        state.counters["edges"] = static_cast<double>(graph.size());
        state.counters["graph_seed"] = config.graph_seed;
        state.counters["sampling_seed"] = config.sampling_seed;

        int iteration = 0;
        for (auto unused : state) {
            (void)unused;
            {
                Measurement measured{};
                measured.utc_start_ns = clock_nanoseconds(CLOCK_REALTIME, "CLOCK_REALTIME");
                measured.process_cpu_start_ns = clock_nanoseconds(CLOCK_PROCESS_CPUTIME_ID, "CLOCK_PROCESS_CPUTIME_ID");
                const auto start = Clock::now();
                const auto result = [&] {
                    // Same public tuple-input boundary as retention_control:
                    // includes tuple conversion and temporary input destruction.
                    problem input(n, graph);
                    if (config.algorithm == 0) return kkt(input, config.sampling_seed);
                    if (config.algorithm == 1) return compacting_boruvka(input);
                    return benchmark_retention::multigraph_boruvka(input);
                }();
                const auto finish = Clock::now();
                measured.process_cpu_end_ns = clock_nanoseconds(CLOCK_PROCESS_CPUTIME_ID, "CLOCK_PROCESS_CPUTIME_ID");
                measured.utc_end_ns = clock_nanoseconds(CLOCK_REALTIME, "CLOCK_REALTIME");
                state.PauseTiming();
                measured.elapsed_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(finish-start).count();
                state.SetIterationTime(std::chrono::duration<double>(finish-start).count());
                benchmark::DoNotOptimize(result);
                require(result == expected, "measured MST differs from certified reference");
                require(measured.elapsed_ns > 0 &&
                        measured.process_cpu_end_ns > measured.process_cpu_start_ns,
                        "nonpositive measured clock interval");
                trace(context.trace_file, config, n, graph.size(), input_hash, topology_hash,
                      invocation, "timed", iteration++, measured);
                // Returned-result destruction, checking and trace I/O are paused
                // and excluded from both explicitly recorded clock intervals.
            }
            state.ResumeTiming();
        }
        require(iteration == measured_iterations, "unexpected iteration count");
    } catch (const std::exception& error) {
        context.failed = true;
        state.SkipWithError(error.what());
    }
}
} // namespace current_complexity

int main(int argc, char** argv) {
    using namespace current_complexity;
    try {
        require(argc == 8, "Usage: current_complexity FAMILY ALGORITHM GRAPH_SEED SAMPLING_SEED ascending|descending TRACE.csv BENCHMARK.json");
        Configuration config{argv[1], 0, number(argv[3]), number(argv[4]), false};
        require(config.family == "leaf_hierarchy4" || config.family == "leaf_shuffled4" ||
                config.family == "gnm_random", "undeclared family");
        const std::string algorithm = argv[2], order = argv[5];
        require(algorithm == "kkt" || algorithm == "multigraph_boruvka", "undeclared algorithm");
        config.algorithm = algorithm == "kkt" ? 0 : 2;
        require(order == "ascending" || order == "descending", "invalid size order");
        config.descending = order == "descending";
        auto raw = exclusive_file(argv[6]);
        // Reserve the JSON path exclusively. Google Benchmark subsequently opens
        // this owned empty file; an exclusive attempt directory is also required.
        auto reserved_json = exclusive_file(argv[7]);
        require(std::fclose(reserved_json.release()) == 0, "failed to reserve JSON output");
        write(raw.get(), "family,algorithm,n,m,N,graph_seed,sampling_seed,input_fingerprint,topology_fingerprint,size_order,invocation,phase,iteration,elapsed_ns,utc_start_ns,utc_end_ns,process_cpu_start_ns,process_cpu_end_ns,process_cpu_elapsed_ns,validation\n");
        Context context{config, raw.get(), {}, false};
        const std::string name = algorithm + "/" + config.family + "/graph_" +
            std::to_string(config.graph_seed) + "/sampler_" + std::to_string(config.sampling_seed);
        auto* registration = benchmark::RegisterBenchmark(name.c_str(),
            [&context](benchmark::State& state) { run_size(state, context); });
        if (config.descending) {
            for (auto it = sizes.rbegin(); it != sizes.rend(); ++it) registration->Arg(*it);
        } else {
            for (int n : sizes) registration->Arg(n);
        }
        registration->Iterations(measured_iterations)->Repetitions(benchmark_repetitions)
            ->MeasureProcessCPUTime()->UseManualTime()->Unit(benchmark::kMillisecond)
            ->Complexity(benchmark::oAuto)->ReportAggregatesOnly(false);
        // Deliberately accept no external Google Benchmark overrides or filters.
        std::string output = std::string("--benchmark_out=") + argv[7];
        std::string format = "--benchmark_out_format=json", color = "--benchmark_color=false";
        char* google_arguments[] = {argv[0], output.data(), format.data(), color.data(), nullptr};
        int google_argc = 4;
        benchmark::Initialize(&google_argc, google_arguments);
        require(!benchmark::ReportUnrecognizedArguments(google_argc, google_arguments), "unexpected benchmark arguments");
        const auto matched = benchmark::RunSpecifiedBenchmarks();
        require(!context.failed && matched == sizes.size() && context.invocations.size() == sizes.size(),
                "incomplete complexity benchmark");
        for (int n : sizes) require(context.invocations.at(n) == benchmark_repetitions,
                                   "missing callback repetition");
        require(std::fclose(raw.release()) == 0, "failed to close raw trace");
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "current_complexity: " << error.what() << '\n';
        return 1;
    }
}
