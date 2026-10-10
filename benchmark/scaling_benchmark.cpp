// Reproducible KKT/Kruskal measurements with correctness checks outside timing.
#include "kkt/kkt.hpp"
#include "kruskal/kruskal.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_set>
#include <vector>

namespace {

using Graph = std::vector<std::tuple<int, int, int, int>>;
using EdgeIds = std::unordered_set<int>;
using Clock = std::chrono::steady_clock;

struct Options {
    bool smoke = false;
    int repetitions = 3;
    int warmups = 1;
};

struct Case {
    const char* series;
    const char* family;
    int vertices;
    int edges;
};

int parse_count(const std::string& text, bool allow_zero) {
    std::size_t consumed = 0;
    const auto value = std::stoll(text, &consumed);
    if (consumed != text.size() || value < (allow_zero ? 0 : 1) ||
        value > std::numeric_limits<int>::max()) {
        throw std::runtime_error("invalid count: " + text);
    }
    return static_cast<int>(value);
}

Options parse_options(int argc, char** argv) {
    Options options;
    bool explicit_repetitions = false;
    for (int i = 1; i < argc; ++i) {
        const std::string argument = argv[i];
        if (argument == "--smoke") options.smoke = true;
        else if (argument == "--scale") options.smoke = false;
        else if (argument == "--repetitions" || argument == "--warmups") {
            if (++i == argc) throw std::runtime_error(argument + " requires a count");
            if (argument == "--repetitions") {
                options.repetitions = parse_count(argv[i], false);
                explicit_repetitions = true;
            } else {
                options.warmups = parse_count(argv[i], true);
            }
        } else {
            throw std::runtime_error("unknown argument: " + argument);
        }
    }
    if (options.smoke && !explicit_repetitions) options.repetitions = 1;
    return options;
}

std::vector<Case> cases(bool smoke) {
    std::vector<Case> result;
    const std::vector<int> sizes = smoke ? std::vector<int>{32, 128}
                                         : std::vector<int>{1024, 4096, 16384};
    const std::vector<int> ratios = smoke ? std::vector<int>{4, 8}
                                          : std::vector<int>{4, 32};
    for (int ratio : ratios) {
        for (int n : sizes) result.push_back({"vertex_growth", "random", n, n * ratio});
    }
    const int fixed_n = smoke ? 128 : 4096;
    for (int ratio : (smoke ? std::vector<int>{4, 8, 16}
                            : std::vector<int>{4, 32, 128})) {
        result.push_back({"density_growth", "random", fixed_n, fixed_n * ratio});
    }
    // Retain a dense case where dropping parallel-edge deduplication regressed.
    if (!smoke) result.push_back({"dense_case", "random", 1000, 400000});
    for (int n : sizes) result.push_back({"vertex_growth", "hierarchical_path", n, n - 1});
    return result;
}

// Explicit Fisher-Yates and mt19937 draws keep fixtures reproducible across
// standard-library shuffle implementations. Small modulo bias is acceptable
// for these benchmark fixtures; this is not a uniform random-graph sampler.
template <typename T>
void shuffle(std::vector<T>& values, std::mt19937& rng) {
    for (std::size_t i = values.size(); i > 1; --i) {
        std::swap(values[i - 1], values[static_cast<std::size_t>(rng()) % i]);
    }
}

Graph make_random_graph(int n, int m, std::mt19937& rng) {
    if (n < 2 || m < n - 1 || m > static_cast<std::int64_t>(n) * (n - 1) / 2) {
        throw std::runtime_error("invalid simple connected graph dimensions");
    }
    Graph graph;
    graph.reserve(static_cast<std::size_t>(m));
    std::unordered_set<std::uint64_t> pairs;
    pairs.reserve(static_cast<std::size_t>(m));
    const auto add_edge = [&](int u, int v) {
        if (u == v) return;
        if (u > v) std::swap(u, v);
        const auto key = (static_cast<std::uint64_t>(u) << 32) |
                         static_cast<std::uint64_t>(v);
        if (pairs.insert(key).second) {
            graph.emplace_back(u, v, 0, static_cast<int>(graph.size()));
        }
    };
    for (int v = 1; v < n; ++v) add_edge(static_cast<int>(rng() % v), v);
    while (static_cast<int>(graph.size()) < m) {
        const int u = static_cast<int>(rng() % n);
        const int v = static_cast<int>(rng() % n);
        add_edge(u, v);
    }
    std::vector<int> weights(static_cast<std::size_t>(m));
    std::iota(weights.begin(), weights.end(), 1);
    shuffle(weights, rng);
    for (int i = 0; i < m; ++i) std::get<2>(graph[i]) = weights[i];
    return graph;
}

Graph make_graph(const Case& item, unsigned int graph_seed) {
    std::mt19937 rng(graph_seed);
    Graph graph;
    if (std::string(item.family) == "random") {
        graph = make_random_graph(item.vertices, item.edges, rng);
    } else {
        graph.reserve(static_cast<std::size_t>(item.edges));
        for (int i = 1; i < item.vertices; ++i) {
            int level = 0;
            for (int j = i; j % 2 == 0; j /= 2) ++level;
            // Distinct weights force successive pairwise Boruvka contractions.
            graph.emplace_back(i - 1, i, level * item.vertices + i, i - 1);
        }
    }
    shuffle(graph, rng);
    return graph;
}

EdgeIds edge_ids(const Graph& tree) {
    EdgeIds ids;
    ids.reserve(tree.size());
    for (const auto& edge : tree) ids.insert(std::get<3>(edge));
    return ids;
}

void require_valid(const EdgeIds& actual, const EdgeIds& expected,
                   const std::string& context) {
    if (actual != expected) throw std::runtime_error(context + ": MST edge IDs differ from oracle");
}

void measure(const Case& item, unsigned int graph_seed, unsigned int sampling_seed,
             int repetition, int order, int warmups, const char* algorithm,
             const Graph& graph, problem& input, const EdgeIds& expected) {
    std::int64_t elapsed = 0;
    bool valid = false;
    if (std::string(algorithm) == "kkt") {
        const auto start = Clock::now();
        const auto result = kkt(input, sampling_seed);
        const auto finish = Clock::now();
        elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(finish - start).count();
        valid = result == expected;
    } else {
        const auto start = Clock::now();
        const auto result = kruskal(graph, item.vertices);
        const auto finish = Clock::now();
        elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(finish - start).count();
        valid = result.size() == expected.size() && edge_ids(result) == expected;
    }
    // Validation, result destruction, and CSV output are outside the interval.
    std::cout << item.series << ',' << item.family << ',' << item.vertices << ','
              << item.edges << ',' << graph_seed << ',' << sampling_seed << ','
              << repetition << ',' << order << ',' << warmups << ',' << algorithm << ','
              << elapsed << ',' << (valid ? "pass" : "FAIL") << '\n';
    if (!valid) throw std::runtime_error(std::string(algorithm) + ": measured MST failed verification");
}

void run(const Options& options) {
    constexpr std::array<unsigned int, 3> graph_seeds = {17, 42, 999};
    constexpr std::array<unsigned int, 3> sampling_seeds = {0, 1, 7};
    std::cout << "series,family,n,m,graph_seed,kkt_seed,repetition,order,warmups,algorithm,elapsed_ns,validation\n";
    std::size_t trial = 0;
    for (const auto& item : cases(options.smoke)) {
        for (unsigned int graph_seed : graph_seeds) {
            // Fixture creation, tuple-to-Edge conversion, and the independent
            // Kruskal oracle are excluded from both algorithms' measurements.
            const auto graph = make_graph(item, graph_seed);
            problem input(item.vertices, graph);
            const auto oracle = kruskal(graph, item.vertices);
            const auto expected = edge_ids(oracle);
            if (oracle.size() != static_cast<std::size_t>(item.vertices - 1) ||
                expected.size() != oracle.size()) {
                throw std::runtime_error("fixture oracle is not a spanning tree with distinct IDs");
            }
            for (unsigned int sampling_seed : sampling_seeds) {
                for (int warmup = 0; warmup < options.warmups; ++warmup) {
                    require_valid(kkt(input, sampling_seed), expected, "KKT warmup");
                    const auto tree = kruskal(graph, item.vertices);
                    require_valid(edge_ids(tree), expected, "Kruskal warmup");
                }
                for (int repetition = 0; repetition < options.repetitions; ++repetition) {
                    const bool kkt_first = trial++ % 2 == 0;
                    for (int order = 0; order < 2; ++order) {
                        const char* algorithm = ((order == 0) == kkt_first) ? "kkt" : "kruskal";
                        measure(item, graph_seed, sampling_seed, repetition, order,
                                options.warmups, algorithm, graph, input, expected);
                    }
                }
            }
        }
    }
    std::cout.flush();
    if (!std::cout) throw std::runtime_error("failed to write CSV output");
}

}  // namespace

int main(int argc, char** argv) {
    if (argc == 2 && std::string(argv[1]) == "--help") {
        std::cout << "Usage: " << argv[0]
                  << " [--scale|--smoke] [--repetitions N] [--warmups N]\n"
                  << "Default: --scale --repetitions 3 --warmups 1.\n"
                  << "Smoke defaults to one repetition; all seeds are preserved.\n"
                  << "CSV goes to stdout; failures go to stderr and return nonzero.\n";
        return 0;
    }
    try {
        run(parse_options(argc, argv));
    } catch (const std::exception& error) {
        std::cerr << "scaling benchmark: " << error.what() << '\n';
        return 1;
    }
    return 0;
}
