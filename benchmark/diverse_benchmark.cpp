// Compare repository MST implementations from a common tuple edge-list input.
#include "kkt/kkt.hpp"
#include "kruskal/kruskal.hpp"
#include "prim/prim.hpp"
#include "boruvka/boruvka.hpp"
#include "mst_certificate.hpp"
#include "graph_fixtures.hpp"
#include "extended_graph_fixtures.hpp"
#include "common_graph_fixtures.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
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
using benchmark_fixtures::Graph;
using benchmark_fixtures::Case;
using benchmark_fixtures::make_graph;
using Ids = std::unordered_set<int>;
using Clock = std::chrono::steady_clock;
constexpr std::array<const char*, 4> algorithms = {"kkt", "kruskal", "prim", "boruvka"};
constexpr std::array<unsigned int, 3> graph_seeds = {17, 42, 999};
constexpr std::array<unsigned int, 3> sampling_seeds = {0, 1, 7};

struct Options {
    bool smoke = false;
    bool large = false;
    bool shapes = false;
    bool common = false;
    int repetitions = 4;
    int warmups = 1;
    std::string case_filter;
    int graph_seed_filter = -1;
    int kkt_seed_filter = -1;
};

int count(const std::string& value, bool allow_zero) {
    std::size_t used = 0;
    const auto result = std::stoll(value, &used);
    if (used != value.size() || result < (allow_zero ? 0 : 1) || result > 1000)
        throw std::runtime_error("invalid count: " + value);
    return static_cast<int>(result);
}

Options options(int argc, char** argv) {
    Options result;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--smoke") { result.smoke = true; result.large = false; result.shapes = false; result.common = false; }
        else if (arg == "--scale") { result.smoke = false; result.large = false; result.shapes = false; result.common = false; }
        else if (arg == "--large") { result.smoke = false; result.large = true; result.shapes = false; result.common = false; }
        else if (arg == "--shapes" || arg == "--smoke-shapes") {
            result.smoke = arg == "--smoke-shapes";
            result.large = false;
            result.shapes = true;
            result.common = false;
        }
        else if (arg == "--common" || arg == "--smoke-common") {
            result.smoke = arg == "--smoke-common";
            result.large = false;
            result.shapes = false;
            result.common = true;
        }
        else if (arg == "--case") {
            if (++i == argc) throw std::runtime_error(arg + " requires a case ID");
            result.case_filter = argv[i];
        }
        else if (arg == "--graph-seed" || arg == "--kkt-seed") {
            if (++i == argc) throw std::runtime_error(arg + " requires a seed");
            const int seed = count(argv[i], true);
            const auto& supported = arg == "--graph-seed" ? graph_seeds : sampling_seeds;
            if (std::find(supported.begin(), supported.end(), static_cast<unsigned int>(seed)) == supported.end())
                throw std::runtime_error("unsupported seed for " + arg + ": " + argv[i]);
            if (arg == "--graph-seed") result.graph_seed_filter = seed;
            else result.kkt_seed_filter = seed;
        }
        else if (arg == "--repetitions" || arg == "--warmups") {
            if (++i == argc) throw std::runtime_error(arg + " requires a count");
            const int value = count(argv[i], arg == "--warmups");
            if (arg == "--repetitions") result.repetitions = value;
            else result.warmups = value;
        } else throw std::runtime_error("unknown argument: " + arg);
    }
    return result;
}

std::vector<Case> cases(bool smoke) {
    std::vector<Case> result;
    const std::vector<int> sizes = smoke ? std::vector<int>{64, 256}
                                        : std::vector<int>{1024, 4096, 16384};
    for (const char* family : {"random_4", "random_32", "random_128", "grid",
             "geometric_grid", "hub", "clustered", "planted_tree", "random_tree",
             "star", "hierarchical_path"}) {
        for (int n : sizes) result.push_back({family, n});
    }
    for (int n : (smoke ? std::vector<int>{32, 64} : std::vector<int>{256, 512, 1024}))
        result.push_back({"complete", n});
    if (!smoke) {
        result.push_back({"random_4", 65536});
        result.push_back({"random_32", 65536});
    }
    result.push_back({"random_dense_anchor", smoke ? 64 : 1000});
    // Reproducible mixed case order reduces systematic family/size drift.
    std::mt19937 rng(20261010);
    for (std::size_t i = result.size(); i > 1; --i)
        std::swap(result[i - 1], result[rng() % i]);
    return result;
}

std::vector<Case> large_cases() {
    std::vector<Case> result;
    for (const char* family : {"random_4", "random_32", "random_128"})
        for (int n : {65536, 262144}) result.push_back({family, n});
    for (const char* family : {"random_4", "random_32"})
        result.push_back({family, 1048576});
    result.push_back({"random_512", 65536});
    for (const char* family : {"hub", "star"})
        for (int n : {65536, 262144, 1048576}) result.push_back({family, n});
    for (int n : {2048, 4096, 8192}) result.push_back({"complete", n});
    // Keep the original scale/smoke matrix and its order unchanged.
    std::mt19937 rng(20261011);
    for (std::size_t i = result.size(); i > 1; --i)
        std::swap(result[i - 1], result[rng() % i]);
    return result;
}


Ids ids(const Graph& tree) {
    Ids result;
    result.reserve(tree.size());
    for (const auto& edge : tree) result.insert(std::get<3>(edge));
    return result;
}

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

std::int64_t measure(int algorithm, const Graph& graph, int n, unsigned int seed,
                     const Ids& expected, const std::vector<const Graph::value_type*>& by_id) {
    bool valid = false;
    std::int64_t elapsed;
    if (algorithm == 0) {
        const auto start = Clock::now();
        const auto result = [&] {
            // Conversion and temporary input destruction belong to the call;
            // only the returned result survives the end timestamp.
            problem input(n, graph);
            return kkt(input, seed);
        }();
        const auto finish = Clock::now();
        elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(finish - start).count();
        valid = result == expected;
    } else {
        const auto function = algorithm == 1 ? kruskal : (algorithm == 2 ? prim : boruvka);
        const auto start = Clock::now();
        const auto result = function(graph, n);
        const auto finish = Clock::now();
        elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(finish - start).count();
        valid = valid_tree(result, expected, by_id);
    }
    // Result validation and destruction are outside the timed interval.
    if (!valid) throw std::runtime_error(std::string(algorithms[algorithm]) + ": incorrect MST");
    return elapsed;
}

void run(const Options& config) {
    std::cout << "case_id,family,n,m,graph_seed,kkt_seed,repetition,order,warmups,algorithm,elapsed_ns,validation\n";
    bool found_case = false;
    const auto selected_cases = config.common ? benchmark_common::cases(config.smoke)
                                             : config.shapes ? benchmark_extended::cases(config.smoke)
                                             : (config.large ? large_cases() : cases(config.smoke));
    for (const auto& item : selected_cases) {
        const std::string case_id = item.family + "_n" + std::to_string(item.n);
        if (!config.case_filter.empty() && config.case_filter != case_id) continue;
        found_case = true;
        std::cerr << "Running " << case_id << '\n';
        for (std::size_t g = 0; g < graph_seeds.size(); ++g) {
            if (config.graph_seed_filter >= 0 &&
                graph_seeds[g] != static_cast<unsigned int>(config.graph_seed_filter)) continue;
            std::cerr << "  graph_seed=" << graph_seeds[g] << " generating fixture\n";
            const auto generation_start = Clock::now();
            const auto graph = config.common ? benchmark_common::make_graph(item, graph_seeds[g])
                                             : config.shapes ? benchmark_extended::make_graph(item, graph_seeds[g])
                                             : make_graph(item, graph_seeds[g], config.smoke);
            const auto generation_finish = Clock::now();
            const auto oracle = kruskal(graph, item.n);
            benchmark_validation::certify_mst(graph, oracle, item.n);
            const auto certificate_finish = Clock::now();
            std::cerr << "  graph_seed=" << graph_seeds[g]
                      << " generation_seconds="
                      << std::chrono::duration<double>(generation_finish - generation_start).count()
                      << " reference_certificate_seconds="
                      << std::chrono::duration<double>(certificate_finish - generation_finish).count()
                      << '\n';
            const auto expected = ids(oracle);
            std::vector<const Graph::value_type*> by_id(graph.size());
            for (const auto& edge : graph) by_id[std::get<3>(edge)] = &edge;
            for (std::size_t s = 0; s < sampling_seeds.size(); ++s) {
                if (config.kkt_seed_filter >= 0 &&
                    sampling_seeds[s] != static_cast<unsigned int>(config.kkt_seed_filter)) continue;
                for (int w = 0; w < config.warmups; ++w)
                    for (int a = 0; a < 4; ++a)
                        measure(a, graph, item.n, sampling_seeds[s], expected, by_id);
                for (int repetition = 0; repetition < config.repetitions; ++repetition) {
                    for (int order = 0; order < 4; ++order) {
                        const int algorithm = (order + repetition + static_cast<int>(g + s)) % 4;
                        const auto elapsed = measure(algorithm, graph, item.n, sampling_seeds[s], expected, by_id);
                        std::cout << case_id << ',' << item.family << ',' << item.n << ',' << graph.size()
                                  << ',' << graph_seeds[g] << ',' << sampling_seeds[s] << ',' << repetition
                                  << ',' << order << ',' << config.warmups << ',' << algorithms[algorithm]
                                  << ',' << elapsed << ",pass\n";
                    }
                    std::cout.flush();
                    if (!std::cout) throw std::runtime_error("failed to write CSV");
                }
            }
        }
    }
    if (!found_case) throw std::runtime_error("unknown case ID: " + config.case_filter);
}
} // namespace

int main(int argc, char** argv) {
    if (argc == 2 && std::string(argv[1]) == "--help") {
        std::cout << "Usage: " << argv[0] << " [--scale|--smoke|--large|--shapes|--smoke-shapes|--common|--smoke-common] [--repetitions N] [--warmups N] [--case ID]\n"
                  << "       [--graph-seed 17|42|999] [--kkt-seed 0|1|7]\n"
                  << "Defaults: --scale --repetitions 4 --warmups 1; CSV on stdout, progress on stderr.\n"
                  << "All presets use all three graph seeds and KKT seeds unless selected explicitly.\n"
                  << "--large selects 18 cases, up to 1,048,576 vertices and 33,554,432 edges.\n"
                  << "--shapes selects six new topology families and two unchanged controls at three sizes.\n"
                  << "--common selects eleven new model variants and two unchanged controls at four sizes.\n";
        return 0;
    }
    try { run(options(argc, argv)); }
    catch (const std::exception& error) {
        std::cerr << "diverse benchmark: " << error.what() << '\n';
        return 1;
    }
    return 0;
}
