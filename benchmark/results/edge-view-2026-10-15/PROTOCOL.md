# Isolated direct-edge verifier experiment

## Motivation and one-change scope

The complete six-solver retention control found candidate KKT slower than
retained-edge Boruvka in all 120 paired trials, on both clocks. Ordered large
cases were about 12–14% slower. This motivates removing a KKT-only materialization:
its full reduced graph is copied into tuples immediately before verification.

Add an internal `vector<Edge>` query overload backed by the same templated
implementation as the tuple overload. Both binaries compile both overloads in
one identical verifier object. The `KKT_EXPERIMENT_EDGE_VIEW` macro changes only
KKT's call site: omit `G_tuples` allocation/copy and read existing edge storage.
Keep tuple forest construction, random draws, recursive control, filtering,
edge order, remapping and subsequent allocations/lifetimes unchanged. Earlier
temporary release and in-place filtering are explicitly separate experiments.

The tuple reference is a **newly refactored tuple implementation**, not the
previous binary. Factoring the verifier may change code generation even for its
tuple overload. Run fresh paired timings; never reuse historical reference
measurements or infer a direct speedup against the old binary by multiplication.
Default production KKT continues using the tuple path. Both experimental builds
retain parallel quotient edges with `KKT_EXPERIMENT_RETAIN_PARALLEL`.

## Build, correctness and provenance gates

Both binaries use identical source inventories and all seven non-KKT production
objects, including the verifier. Only `kkt.o` differs through the Edge-view
selection macro. The six-solver timing harness, all graph generators, other
solvers, result validation, timing boundaries and retained-edge Boruvka helper
stay unchanged from the parent control. Allowed native source changes are only
`kkt/kkt.cpp`, `verifier/verifier_v2.cpp`, `verifier/verifier_v2.hpp`, plus the new
standalone correctness gate. Any additional build scripts/recipes are recorded.

Use explicit native arm64 compilation/linking, Apple Clang 15, C++17,
`-O3 -Wall -Wextra -march=native`, assertions enabled and a 512 MiB stack. No work
counters in timing objects. Freeze exact commands, toolchain, source, objects,
binary profiles/hashes, runtime helpers, protocol and manifest before timing.
Commit source/gates and then the completed freeze before root releases capture.

Independent positional path-walk oracles must compare both verifier overloads
on connected and disconnected forests, parallel/reversed queries, equal-cost
boundaries, signed extremes, arbitrary/repeated query IDs, empty/singleton cases,
and the existing self-loop behavior. Inputs and all verifier work counters must
match exactly. Existing unique-weight full-KKT certification/exhaustive suites
must pass for both variants, including raw multigraphs and the dispatch-sensitive
fixture. Native Clang 22 ASan/UBSan/leak gates must also pass.

Paired instrumented full-KKT gates require identical MST IDs and all work fields
except exactly these two reductions:

```
reference.kkt_edge_visits - edge.kkt_edge_visits
= reference.edge_materializations - edge.edge_materializations
= reference.verifier_edges
= reference.sampling_edge_visits
```

Require positive verifier work on a discriminator input to reject a wrong-linked
candidate. Initialized-slot counts do not decrease: the removed `reserve` never
incremented that counter. These deterministic counts establish isolation, not
elapsed-time savings.

## Prospective paired schedule

Use all ten cases in `manifest.csv`, unchanged from the parent control. Graph
seeds are **4000037 and 4000063**, and starting KKT seed is **1013**. For seed one,
run tuple then Edge variants adjacently in manifest order. For seed two, reverse
both case order and variant order. Every child runs all six algorithms with one
checked warmup and six timed repetitions, cycling each solver once through every
position. This gives **40 children, 1,680 checked outputs, 1,440 timed and 240
warmup**. All inputs are generated identically in both variants and checked by
fingerprint and independent certificate.

The six algorithms remain KKT, deduplicating compacting Boruvka, retained-edge
Boruvka, Kruskal, Prim and original Boruvka. Every comparator is retained even
when faster than KKT. Serial native timing must wait for all competing local
builds, tests, plots and diagnostic work to stop. No threshold or family-specific
algorithm shortcut is added.

## Monitoring, retention and analysis

Preserve the parent's timing boundaries, clock semantics, raw results,
certificates and fail-closed resource rules: bounded owned-group RSS sampling
every two seconds, 40 GiB sampled stop, stop after three unavailable samples or
any poisoned sampler, and bounded verified empty group after every normal exit.
Never advance after an unverified exit; retain partial failed campaigns without
silent recovery. The new paired collector has its own schema and complete
40-child/1,680-output checks, reusing unchanged validation/monitoring primitives.
It must pass complete mocked scheduling and negative provenance/result/resource
tests plus independent review before release.

No verified sleep-prevention assertion exists; both earlier caffeinate attempts
failed. Retain every timing and flag, correlate a separately archived power log
after capture, and publish only scoped audit summaries. No trimming, replacement,
control normalization or timing adjustment is allowed. Periodic process-group
RSS is not continuous peak memory or a KKT-only allocation measurement.

For implementation effects, pair Edge/tuple elapsed and CPU durations by graph,
solver and repetition. The primary case statistic is the median of all twelve
paired ratios, alongside each graph's six-trial median and all trial ranges.
Report unchanged-solver drift without using it to normalize KKT. Separately
report KKT against all five comparators within each variant and identical child,
using the same twelve-pair aggregation. A lead against retained-edge Boruvka must
be measured directly; it cannot be derived by multiplying unrelated ratios.

The strong crossover rule remains: a smaller measured point with each graph
median above one on both clocks, then a larger point with each graph median at
most 0.90 on both clocks, and every still-larger tested point also meeting that
win rule. Compare only the same family/density, report measured endpoints, and
do not interpolate an exact threshold. Wins at every measured size are leads,
not observed crossovers. All inconclusive results and losses remain visible.

This selected follow-up tests one hypothesized constant-factor improvement, not
universal practical superiority, a Google Benchmark complexity fit or a proof
of linear wall time. Two graph seeds and one starting sampling seed are limited
replication; order reversal is confounded with graph seed. No automatic production
promotion or Wikipedia conclusion follows from this experiment.
