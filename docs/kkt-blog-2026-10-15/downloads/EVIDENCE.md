# Evidence behind “Maybe KKT is not galactic after all”

Prepared 2026-10-15. The article is a synthesis of completed experiments, not a new benchmark run. Figure generation independently recomputed summaries from the archived timing and work records. No measurements were trimmed, synthesized, or extrapolated to produce the blog's plots.

## Scope of the download

[kkt-blog-data.zip](kkt-blog-data.zip), beside this file, includes the plotted tables, exact figure source, a portable chart reproduction command, and provenance. It reproduces the five quantitative charts from the exported tables. It is not a complete native benchmark environment or a replacement for the experiment's raw-data audits. The three conceptual figures are independently checked constructions, not measured benchmark fixtures; their source and checks are in [kkt-concepts.zip](kkt-concepts.zip).

The project is [FranciscoThiesen/karger-klein-tarjan](https://github.com/FranciscoThiesen/karger-klein-tarjan). Source references below are repository-relative. The research snapshot used when preparing this article is `ab46700bc4c67a08508c24c3d7f55c5b8557e348`, on `codex/kkt-eighth-sampling`. A public checkout must contain that research history to resolve these references; an ordinary default build is not the experimental executable measured here.

## The headline experiment

Repository directory: `benchmark/results/lower-density-2026-10-15/`.

- Families: `leaf_distance4` and `leaf_shuffled4`, with three cheap leaves per core vertex. The latter permutes the core weights while preserving topology, IDs, labels, edge order, and the exact core-weight multiset.
- Density 16: n = 512, 2048, 8192, 32768, 131072, 524288, 2097152; m = 16n.
- Density 8: n = 256, 1024, 4096, 16384, 65536, 262144, 1048576, 4194304; m = 8n.
- Graph seeds: 23000003 and 23000029. Sampler seed: 3407. The sample is reused across repetitions of the same input.
- Six implementations: KKT; deduplicating compacting Borůvka; retained-edge compacting Borůvka; Kruskal; Prim; original Borůvka. Dijkstra is not included because its shortest-path tree is not generally a minimum spanning tree.
- One certified warmup and six timed repetitions per solver/input. Solver positions rotate. Graph 1 runs sizes upward and graph 2 downward; graph and schedule are confounded.
- 30 cases, 60 input processes, 2,160 timed solver calls and 360 warmups. All 2,520 answers passed the study's independent certificate checks.

The headline ratio is the median of matched KKT/comparator timing ratios. It is not the ratio of separate time medians. A strong point requires every graph median on both wall and process-CPU clocks to be ≤0.90. A sustained strong crossover additionally requires an earlier loss and strong points at every remaining measured larger size. The bracket is a measured interval, with no interpolation or extrapolation.

At distance-ranked m=16n, the sustained strong bracket is (512,8192]. At n=2097152, the wall ratio is 0.708792201; all twelve trial ratios are between 0.68581075 and 0.73112705. Kruskal wins every matched trial at all four largest lower-density endpoints. None of the 30 cases beats all five controls by the declared pooled both-clock medians.

Primary records: `lower-density.csv`, `lower-density.json`, `analysis-attempt01/validated_calls.csv`, `analysis-attempt01/comparisons.csv`, `analysis-attempt01/graph_comparisons.csv`, `analysis-attempt01/crossover_points.csv`, and `independent-audit-attempt01/audit.json`.

The exact timing executable SHA-256 is:

```text
954068775a83e1c42db62ffb6777c398dc05fd5792c60d2f293df6532130951a
```

Its opt-in configuration enables retained parallel quotient edges, direct Edge verifier inputs, compressed verifier requests, and scalar private eighth sampling. Relevant switches are `KKT_EXPERIMENT_RETAIN_PARALLEL`, `KKT_EXPERIMENT_EDGE_VIEW`, `KKT_EXPERIMENT_COMPRESSED_QUERIES` on the verifier object, and `KKT_EXPERIMENT_EIGHTH_SAMPLING` on the KKT object. Public half sampling and the ordinary default path remain separate. No packed-half gain is multiplied into these results.

## Machine and timing boundary

Apple M3 Max, 128 GiB RAM, 16 logical cores; macOS 26.6.2 (25G83); Apple Clang 15 with SDK 14.5; C++17, `-O3 -march=native`, assertions enabled, 512 MiB stack. These are native single-solver measurements, not a cross-machine result.

All solvers start with the same tuple list. Input conversion and construction of returned results are timed. KKT and the continuation controls return ID sets; classical solvers return edge vectors. Generation, independent certification, returned-result checking and returned-result destruction are outside the solver interval. Temporary input destruction is inside. A different application's input/output representation could alter rankings.

Both wall and process CPU clocks are kept; their agreement is not an independent replication. No control-drift correction was applied. There were no clock-flagged calls or logged sleep overlaps in this series. Sleep inhibition was attempted but not verified. RSS sampling is not peak-allocation instrumentation. Two graph instances on one host do not establish a population confidence interval.

## Logical work and the reversal

Repository directory: `benchmark/results/lower-density-2026-10-15/work/`.

The work campaign uses the same input fingerprints as the timing campaign. Its counts are untimed. All 180 solver outputs passed certification. The independent audit checked 11,700 counter cells (including 120 explicitly null entries), 120 contraction chains, and 60 verifier-query rows.

“Contraction input / m” sums the input lengths of all contraction steps; for KKT this includes all recursive branches. It is neither distinct edges nor CPU time. On the largest distance-ranked d16 input, this is about 2.403m for KKT and 17.906m for retained Borůvka. KKT's other work is deliberately not hidden inside this comparison.

At distance-ranked d8/n=4194304, disconnected-wrapper partition visits are 11,478,993 versus 78,826,591 for the two graphs. Source-derived aggregate inequalities prove a connected root sampled forest for graph 1 and a nonempty disconnected root sampled forest for graph 2. This is a counter-based inference, not a direct root trace, an isolated-vertex count, or a CPU attribution.

Primary records: `analysis-attempt01/work.csv`, `analysis-attempt01/round_chains.csv`, `analysis-attempt01/query_work.csv`, `independent-counter-audit-attempt01/audit.json`, `partition-analysis-attempt01/partition.csv`, and the independent review records in `partition-analysis-attempt01/` and `root-inference-attempt01/`.

## Empirical complexity

Repository directory: `benchmark/results/current-complexity-2026-10-15/`.

Google Benchmark 1.5.2 is pinned to `73d4d5e8d6d449fc8663765a42aa8aeeee844489`. The code supplies `SetComplexityN(n+m)` with `Complexity(oAuto)`. The library selects the model using CPU time, then fits manual time to the selected class; exported RMS is for CPU time.

Three workloads: ordered hierarchical and shuffled cores at m=32n, plus connected random graphs at m=16n. Eleven doublings from n=1024 to 1048576. Graph seeds 19000013 and 19000043; sampler seeds 3001 and 3011. Two solvers, four labeled curves per solver/family: 24 curves in all. Retained Borůvka ignores the sampler seed, so its four curves repeat two distinct graphs.

All 24 Google selections, including all twelve KKT selections, are N log N. All 192 independently computed full/upper-window clock fits also choose N log N. The chart uses independently recorded native process CPU, not Google's manual-time coefficient. The graph/schedule confounding and repeated inputs are retained. These fits neither prove a superlinear asymptotic bound nor demonstrate measured linear runtime.

Primary records: `capture-attempt01/capture.json`, its 24 `capture_curves/*.csv`, `analysis-attempt01/google_selection.csv`, `analysis-attempt01/size_summaries.csv`, and `arithmetic-audit-attempt01/audit.json`.

## Separate experiments cited in the text

These results are not pooled into one curve or multiplied together.

| Claim | Repository directory |
|---|---|
| Private half versus eighth sampling | `benchmark/results/eighth-sampling-2026-10-15/` |
| Ordered hierarchy at m=32n | `benchmark/results/eighth-extension-2026-10-15/` |
| Distance-ranked cores at m=32n | `benchmark/results/eighth-distance-2026-10-15/` |
| Shortcut lines and grids, compressed half sampler | `benchmark/results/heldout-families-2026-10-15/` |
| Earlier common-family four-way comparison | `benchmark/results/common-2026-10-11/` |
| Earlier implementation repair comparison | `benchmark/results/repair-2026-10-09/` |

Historical bipartite results omitted the later retained-edge control. The common-family sweep includes weighted-input aliases; its labels must not be counted as independent graph families. The small-cover mechanism primarily explains contraction, and does not by itself establish that sampling/filtering adds value.

## Failure chronology and repair map

The audited baseline `693c6a5f0945982ef3460e27632687e55cfb8de9` is dated January 11, 2026. It introduced root-ID-sized bitmaps. The 2022 code used sets, so this later regression cannot explain the old post's timings.

| Defect or change | Source history |
|---|---|
| Root-ID-range bookkeeping | Introduced `693c6a5`; repaired `60c65b4` |
| Repeated subset enumeration in median lookup table | Present by `805a330` (June 2020), copied into verifier v2 at `8a56a5a`; repaired `312954e` |
| Recursive global RNG restart | Present by `93f6c54` (September 2020), present in 2022 `ae02010`; repaired `ccb833f` |
| Prim/KKT incompatible global Edge definitions | Repaired `17aa5cf` |
| Flat deduplicating contraction | `e45e861` |
| Verifier storage simplification | `a3a4395` |
| Positional heavy marks | `4eb3ca1` |
| Contiguous query ranges | `2749ced` |
| Cheapest-neighbor component walks | `2e37b4e` |
| Direct sample-edge recovery | `af12309` |
| Owned graph compaction | `ba39977` |
| Final result reserve | `2d4fbf1` |
| Retained parallel quotients | `ae03ec6` |
| Direct Edge verifier inputs | `b7aa02b` |
| Compressed verifier requests | `a7cb2d6` |
| Private eighth sampler | `116c316` |

The prefix-mask parenthesization typo described in the old post was already repaired at `a5fcc78c82b978d216c2d8e4df28e052792edabd` on September 10, 2020. It is historical context, not a new repair. A legacy `int` cost helper remains; it is not the correctness gate used for these measurements.

## Theory and sources

- [Karger, Klein and Tarjan: A randomized linear-time algorithm to find minimum spanning trees, 1995](https://www.cs.cmu.edu/~guyb/paralg/papers/KargerKleinTarjan95.pdf). The published algorithm uses half sampling and deduplicated quotients. The retained-edge and fixed-p accounting is documented separately in the local research report; do not attribute that implementation verbatim to the paper.
- [Google Benchmark's pinned complexity fitter](https://raw.githubusercontent.com/google/benchmark/73d4d5e8d6d449fc8663765a42aa8aeeee844489/src/complexity.cc).
- [The 2022 post](https://chico.dev/Linear-Time-MST/). Its fitted extrapolation is historical, not a current estimate.

With two Borůvka steps q≤n/4 and r≤m, independent fixed-p sampling gives expected pr sample edges and at most q/p surviving records. The expected-linear work argument is conditional on linear local/verifier work, expected hashing, fresh ideal random choices, and the relevant represented/machine-word bounds. An MT19937 stream supplies reproducible pseudorandom draws, not literal mathematical independence.

The complete internal research report is `docs/kkt-report/current-2026-10-15/html-attempt03/REPORT.md`, with a 40-page PDF in the neighboring `pdf-attempt03/` directory. The blog is a deliberately shorter account. Neither the blog nor its data ZIP claims that KKT is fastest across all graph families, that Google Benchmark observed linear time, or that a finite crossover predicts permanent dominance.
