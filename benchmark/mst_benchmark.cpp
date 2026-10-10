#include "benchmark/benchmark.h"

#include "../boruvka/boruvka.hpp"
#include "../graph_utils/graph_utils.hpp"
#include "../kkt/kkt.hpp"
#include "../kruskal/kruskal.hpp"
#include "../prim/prim.hpp"
#include <cmath>

static void bm_boruvka(benchmark::State& state)
{
	auto G = build_random_connected_graph(state.range(0), state.range(1));
	for (auto _: state)
	{ benchmark::DoNotOptimize(boruvka(G, state.range(0))); }
}

static void bm_kkt(benchmark::State& state)
{
	auto G = build_random_connected_graph(state.range(0), state.range(1));
	auto P = problem(state.range(0), G);
	for (auto _: state) { benchmark::DoNotOptimize(kkt(P)); }
}

static void bm_kruskal(benchmark::State& state)
{
	auto G = build_random_connected_graph(state.range(0), state.range(1));
	for (auto _: state)
	{ benchmark::DoNotOptimize(kruskal(G, state.range(0))); }
}

static void bm_prim(benchmark::State& state)
{
	auto G = build_random_connected_graph(state.range(0), state.range(1));
	for (auto _: state) { benchmark::DoNotOptimize(prim(G, state.range(0))); }
}

static void CustomArguments(benchmark::internal::Benchmark* b)
{
	b->Args({10000, 1250000});
	b->Args({10000, 2500000});
	b->Args({10000, 5000000});
	b->Args({10000, 10000000});
	b->Args({10000, 20000000});
}

BENCHMARK(bm_boruvka)->Apply(CustomArguments);
BENCHMARK(bm_kkt)->Apply(CustomArguments);
BENCHMARK(bm_kruskal)->Apply(CustomArguments);
BENCHMARK(bm_prim)->Apply(CustomArguments);

/*
BENCHMARK(bm_boruvka)->Ranges({{2048, 2048}, {1 << 13, 1 << 16}});
BENCHMARK(bm_kkt)->Ranges({{2048, 2048}, {1 << 13, 1 << 16}});
BENCHMARK(bm_kruskal)->Ranges({{2048, 2048}, {1 << 13, 1 << 16}});
BENCHMARK(bm_prim)->Ranges({{2048, 2048}, {1 << 13, 1 << 16}});
*/
BENCHMARK_MAIN();
