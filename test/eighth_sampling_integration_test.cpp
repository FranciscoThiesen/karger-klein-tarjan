// Compile this TU in place of kkt.o, with all seven shared production objects.
// It exercises the actual private template without a production test hook.
#include "../kkt/kkt.cpp"

#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>

namespace {
void sampling_require(bool value, const char* message) {
    if (!value) throw std::runtime_error(message);
}

bool same_problem(const problem& a, const problem& b) {
    return a.num_vertices == b.num_vertices && a.max_edge_id == b.max_edge_id &&
           a.graph_edges == b.graph_edges;
}

problem sampling_oracle(const problem& input, std::mt19937& engine,
                        bool eighth, bool parent_positions) {
    // Draw all words before mapping positions. Modulo is deliberately
    // independent of the production mask/predicate and dispatch template.
    std::vector<std::uint32_t> words(input.graph_edges.size());
    for (auto& word : words) word = static_cast<std::uint32_t>(engine());
    std::vector<Edge> selected;
    std::vector<bool> used(input.num_vertices, false);
    for (std::size_t i = 0; i < words.size(); ++i) {
        const bool keep = eighth ? words[i] % 8 == 7 : words[i] % 2 == 1;
        if (!keep) continue;
        const auto& edge = input.graph_edges[i];
        selected.emplace_back(edge.from, edge.to, edge.cost,
                              parent_positions ? static_cast<int>(i) : edge.id);
        used[edge.from] = used[edge.to] = true;
    }
    std::vector<int> mapping(input.num_vertices, -1);
    int vertices = 0;
    for (int v = 0; v < input.num_vertices; ++v) if (used[v]) mapping[v] = vertices++;
    for (auto& edge : selected) {
        edge.from = mapping[edge.from];
        edge.to = mapping[edge.to];
    }
    const std::int64_t metadata = parent_positions
        ? static_cast<std::int64_t>(input.graph_edges.size()) : input.max_edge_id;
    return problem(vertices, std::move(selected), metadata);
}

problem actual_sample(const problem& input, std::mt19937& engine, bool private_call) {
#ifdef KKT_ENABLE_WORK_STATS
    kkt_work::WorkStats stats;
    problem result;
    {
        kkt_work::ScopedWorkStats scope(stats);
        result = private_call ? sample_edges<true>(input, engine)
                              : kkt_detail::random_sampling(input, engine);
    }
    sampling_require(stats.sampling_calls == 1 &&
        stats.sampling_edge_visits == input.graph_edges.size() &&
        stats.sampled_edges == result.graph_edges.size() &&
        stats.edge_materializations == result.graph_edges.size(),
        "direct sampling instrumentation changed meaning");
    return result;
#else
    return private_call ? sample_edges<true>(input, engine)
                        : kkt_detail::random_sampling(input, engine);
#endif
}

problem fixture(std::size_t length, bool empty_universe, std::int64_t metadata) {
    std::vector<Edge> edges;
    for (std::size_t i = 0; i < length; ++i) {
        const int id = i == 0 ? std::numeric_limits<int>::min() :
            i == 1 ? std::numeric_limits<int>::max() : -static_cast<int>(i) * 100003;
        const int cost = i == 0 ? std::numeric_limits<int>::min() :
            i == 1 ? std::numeric_limits<int>::max() : static_cast<int>(i) - 50;
        // Disjoint endpoint ranges ensure loop-free input; unreferenced
        // vertices make the stable compaction observable. Parallel records
        // are allowed; IDs and costs remain unique.
        edges.emplace_back(3 + static_cast<int>(i % 37),
                           42 + static_cast<int>((i * 11) % 41), cost, id);
    }
    return problem(length == 0 && empty_universe ? 0 : 99, std::move(edges), metadata);
}
}  // namespace

int main(int argc, char** argv) {
    try {
        sampling_require(argc == 2, "expected half or eighth policy argument");
        const std::string policy = argv[1];
        sampling_require(policy == "half" || policy == "eighth", "invalid policy argument");
        const bool eighth = policy == "eighth";
        static_assert(std::mt19937::word_size == 32, "requires 32-bit MT words");
        static_assert(std::mt19937::min() == 0 && std::mt19937::max() == 0xffffffffu,
                      "requires full-width MT output range");
        std::size_t calls = 0, witnesses = 0;
        for (unsigned seed : {0u, 42u, std::numeric_limits<unsigned>::max()}) {
            std::mt19937 actual(seed), expected(seed), replay(seed);
            std::size_t iteration = 0;
            for (std::size_t length : {0u, 1u, 2u, 7u, 8u, 9u, 31u, 32u, 33u,
                                       63u, 64u, 65u, 97u, 127u, 128u, 129u,
                                       623u, 624u, 625u, 0u, 33u, 0u}) {
                const auto metadata = iteration % 2 ? std::numeric_limits<std::int64_t>::min()
                                                    : std::numeric_limits<std::int64_t>::max();
                const problem input = fixture(length, iteration % 2 == 0, metadata);
                const problem before = input;
                auto half_engine = expected, eighth_engine = expected;
                const auto half = sampling_oracle(input, half_engine, false, true);
                const auto sparse = sampling_oracle(input, eighth_engine, true, true);
                sampling_require(half_engine == eighth_engine,
                                 "one-call policies consumed different word counts");
                for (const auto& edge : sparse.graph_edges) {
                    sampling_require(std::any_of(half.graph_edges.begin(), half.graph_edges.end(),
                        [&](const Edge& candidate) { return edge.id == candidate.id; }),
                        "eighth original positions are not a subset of half");
                }
                const auto& wanted = eighth ? sparse : half;
                expected = half_engine;
                const auto got = actual_sample(input, actual, true);
                const auto repeated = actual_sample(input, replay, true);
                sampling_require(same_problem(got, wanted),
                                 "wrong private policy or sample records/compaction/metadata");
                sampling_require(same_problem(got, repeated) && actual == expected && actual == replay,
                                 "private replay or exact engine advancement differs");
                sampling_require(same_problem(input, before), "private sample modified input");
                if (!same_problem(half, sparse)) ++witnesses;
                ++calls;

                // Interleaved public calls must still implement the legacy
                // odd-word contract at the engine state actually passed in.
                const auto public_wanted = sampling_oracle(input, expected, false, false);
                const auto public_got = actual_sample(input, actual, false);
                const auto public_repeated = actual_sample(input, replay, false);
                sampling_require(same_problem(public_got, public_wanted) &&
                                 same_problem(public_got, public_repeated),
                                 "public legacy sampling records/metadata changed");
                sampling_require(actual == expected && actual == replay,
                                 "public legacy engine advancement changed");
                sampling_require(same_problem(input, before), "public sample modified input");
                ++calls;
                ++iteration;
            }
        }
        sampling_require(calls == 132 && witnesses > 0,
                         "missing complete matrix or half/eighth discrimination witness");
        std::cout << "PASS " << calls << " private/public sampling cases, each replayed; "
                  << witnesses << " half/eighth witnesses; policy=" << policy << '\n';
    } catch (const std::exception& error) {
        std::cerr << "FAIL: " << error.what() << '\n';
        return 1;
    }
}
