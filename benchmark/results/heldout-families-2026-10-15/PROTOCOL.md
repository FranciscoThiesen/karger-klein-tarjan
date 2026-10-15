# Prospective held-out family and size matrix

**Prospective declaration, 2026-10-15. Native performance is not released.** This matrix, seeds and analysis rule were prepared while the compressed-query paired study was still running. The package is now installed for nonperformance validation; execution receipts under `validation/` distinguish planned from completed gates. Root may release performance only after the parent study's validation and direct solver comparisons justify further investigation. Release does not permit changing this matrix in response to those observations. A decision not to run is recorded as unexecuted; a different matrix requires a new prospective declaration.

## Question and fixed inputs

Does the already frozen compressed-query KKT candidate show a useful, sustained measured crossover on existing ancestry-order or spatial-order graph families, against each of five unchanged MST competitors? This is a new generalization study, not a second optimization experiment and not a complexity fit. No historical timing is pooled, adjusted, normalized, or replaced.

Here, "held out" means this prospectively fixed new matrix and graph/sampling seeds. It does not mean the family names have never been investigated: `leaf_distance4` and the spatial generators already exist, and some have prior measurements. Those earlier observations motivate the question but are not incorporated into these estimates.

| Matched weight twins | Vertex counts n | Density m/n | Intrusion |
|---|---|---:|---:|
| `leaf_distance4`, `leaf_shuffled4` | 1,024; 4,096; 16,384; 65,536; 262,144; 1,048,576 | 32 | 0 |
| `grid2d_metric`, `grid2d_random` | same six sizes | 32 | 0 |
| `line_metric`, `line_random` | same six sizes | 32 | 0 |

All **36 cases** are mandatory. The exact ordered [manifest](manifest.csv) is part of the freeze. Two graph seeds, **9000011 and 9000049**, and one scalar KKT sampling seed, **2003**, are assigned prospectively. Their nonreuse must be rechecked before freeze, without selecting alternatives based on favorable outputs. There are **72 native children**, each containing one checked warmup and six timed repetitions for all six solvers: **3,024 certified outputs = 2,592 timed + 432 warmups**. No early stopping for a favorable result, deletion of a family/size, extension to a larger endpoint, or additional sampling seed is part of this protocol.

Each graph/sampler combination is one realization. Six repetitions measure that same realization, not six independent graph or forest draws. The two graph medians characterize these two realizations only; one sampling seed does not establish robustness to sampling variability.

## Existing generators and matched controls

`leaf_distance4` is the existing synthetic ancestry-order family. Every core edge, including a shortcut, receives a tier `floor(log2(u xor v))`, with distinct ranks within tiers; three cheaper leaves per core vertex force the initial star collapse. It already exists and must not be described as a new generator. The forced core path and ancestry tiers enforce dyadic sibling-block contraction. Shortcuts can belong to its MST. Its deterministic contraction partitions and retained-edge counts agree with the hierarchy construction on the same topology, while KKT's sampled forest and verifier work can differ. The `leaf_shuffled4` twin shuffles the core ranks while retaining the cheap leaves; it is not a global shuffle of all weights.

For attachments, with `q=n/4`, `core_m=32n-3q=125q`; average core degree is exactly 250 at every size. At `n=1024`, the 256-vertex core has 32,000 of 32,640 possible pairs, occupancy 50/51. This is the smallest legal power-of-two attachment size at this density; `n=512` would exceed simple-core capacity. Large cores occupy a smaller fraction of their possible pairs despite constant average degree. Finite density, shortcut locality and quotient multiplicity can therefore change across the size range. Graph generation is outside solver timing.

The spatial families are an existing line or grid scaffold plus uniformly sampled distinct shortcuts. They are not road networks, application graphs, or pure planar grids. `line_metric` orders positive-gap line distances; its MST is the forced path, and the finite gap alphabet limits generalization of its contraction mechanism. `grid2d_metric` orders squared distances on a jittered square-grid geometry; its MST can use shortcuts and need not have exact dyadic contraction. The six vertex counts yield square grids with side lengths 32, 64, 128, 256, 512 and 1,024. Spatial random twins shuffle all ranks while keeping topology and geometry generation fixed.

The line-family limit is concrete: its path gaps are integers in `[1,1024]`, and equal-distance path edges are ranked by increasing original edge ID from left to right, before label and physical-order shuffles. A shortcut is longer than each path edge that it spans, so deterministic Borůvka components remain contiguous intervals and their cheapest exits are path boundaries. At each round, all remaining path boundaries with the smallest gap disappear: within an equal-gap run, each right-hand component chooses its lower-ranked left boundary. Thus these full-graph Borůvka variants need at most 1,024 rounds (and also obey the usual logarithmic round bound). This fixed alphabet cannot establish an unbounded logarithmic round separation as n grows. The statement does not apply to arbitrary sampled subgraphs inside KKT, and it makes no prediction about measured constants or winners.

All stored weights are distinct ordinal ranks. An order induced by geometric or ultrametric distances is not a claim that the stored integers satisfy a triangle inequality. Report these as synthetic graph/weight families, not an application distribution.

For every family pair, size, and graph seed, the collector requires equal topology fingerprints and different weighted-input fingerprints. These **36 twin checks** bind topology, edge IDs, vertex labels and physical edge order, while excluding a vacuous equal-weight control. Within a child, all six solvers receive the same certified weighted input. No generator, reference-certificate, conversion, timed-boundary or input-destruction change is allowed.

## Exact binary and full parent proof

Run the single compressed candidate already frozen in the current compressed-query worktree; do not rebuild. Parent freeze:

- Worktree: `/Users/random_person/Desktop/kkt-compressed-queries`.
- Freeze: `benchmark/results/compressed-query-2026-10-15/freeze.json`.
- Freeze SHA-256: `bd65da13058d3e9cfa58919a0fe5e02b8a46b1d0b8fe7f05801692d5a0866df9`.
- Native binary: `bin/compressed-query/timing-build/compressed/retention_control`.
- Binary SHA-256: `74e604830c4c730395cd6c9e9dc61287a6d88a34cc89983bb4ee61dc3272a1b2`.

The new collector invokes the unchanged compressed collector's complete strict freeze checker, unscoped, before inheriting its compressed artifact. This retains all ancestor source/helper/native-build proofs, binary profile, objects, harness main, compiler/SDK/flags, exact link recipe, build-log hashes and reference-body/scalar-sampling assertions. The parent checker continues to validate its reference artifact as part of the full paired proof. The new freeze adds the new collector/helper hashes, this protocol, ordered manifest, seeds, schedule and monitoring policy. No parent helper or native source changes are permitted. Temporary seed scoping applies only to existing command/row validators and is restored on nested exits and exceptions.

The native six-solver order remains KKT, compacting Borůvka, retained-edge multigraph Borůvka, Kruskal, Prim and original Borůvka. Every solver occupies every timed position once in six repetitions. Keep the native arm64 AppleClang optimized profile and 512 MiB main-thread stack. This candidate retains parallel edges, uses the direct Edge verifier view and compressed query buckets, with **scalar one-draw-per-edge sampling**, not the packed-sampling experiment.

## Schedule, timing and resource controls

Graph seed one follows the 36-row manifest. Sizes ascend; twins are adjacent. The three pair groups rotate by size index: leaf/grid/line, grid/line/leaf, line/leaf/grid, repeated for the larger three sizes. Graph seed two reverses the entire manifest, which also reverses each pair's member order. This counterbalances order but does not remove graph-seed/order/host-state confounding. No baseline drift normalization is performed.

Run only when root releases quiet serial performance work. The collector must receive `--released`. Native children run one at a time in owned process groups under `/usr/bin/time -l`. Preserve every exact command, exit status, raw CSV, independent certificate/log, RSS observation, monotonic/UTC interval and clock diagnostic. Before any next launch, successful wrapper exit must be followed by a bounded observation that the owned group is empty. Unknown/nonempty group state, sampler poisoning, child failure or monitoring failure stops the campaign; no unverified continuation is permitted.

Keep the established **40 GiB** sampled process-group RSS ceiling, **2-second** polling and stop after **three consecutive unavailable** samples. Use the existing bounded sampler and bounded termination; a timed-out/poisoned provider forbids a new child. Preserve interrupted attempts and partial evidence. Sampled RSS is not a continuous peak-memory measurement.

The native exact MST certificate and ID checks apply to warmups and timed calls. Strict analysis rereads all hashes, child rows, certificates, clock endpoints, schedule, resource evidence and combined-CSV concatenation; it must validate every one of the 3,024 outputs. Flagged calls remain included and unadjusted. Wall and process CPU are separate clocks. Power-log correlation is diagnostic; a `Wake Requests` message is not a wake transition, and an absence of logged overlap does not prove complete log coverage or active sleep inhibition. Archive private raw power logs outside committed artifacts, with study-specific ignore rules before capture.

## Analysis and crossover rule

Pair KKT with each competitor by case, graph seed, sampling seed and repetition on each clock. Export all **4,320** individual KKT/comparator clock ratios and integer endpoints; ratios below one favor KKT. Case estimates are the median of all **12** paired ratios, not a ratio of time medians and not a median of graph medians. Retain each graph's six-trial median, all trial ranges and wins, both clocks and all losses. Also report absolute runtime medians/ranges for every solver.

Expected canonical table sizes are: 360 case comparison rows, 720 graph comparison rows, 432 case absolute summaries and 864 graph absolute summaries. Ranges are descriptive and are not confidence intervals. Retained-edge multigraph Borůvka is the main test of whether KKT filtering repays its additional work; results against compacting Borůvka alone are insufficient. Report Prim and original Borůvka even if either remains faster, and distinguish a single-comparator win from being the fastest measured solver.

For each of six families and five comparators, classify all six measured sizes from the **four exact rational graph medians** (two graph seeds × two clocks):

- `strong_lead`: all four medians are at most **9/10**.
- `narrow_lead`: all four are below one, but the strong criterion fails.
- `loss`: all four exceed one.
- `mixed_or_tied`: every other outcome, including an exact tie on either clock/graph.

A **strong observed crossover bracket** requires an earlier measured size classified `loss`, a later size classified `strong_lead`, and `strong_lead` at **every still-larger measured size**. Fractions are reconstructed from raw integer times before computing graph medians; floating-point rounding cannot turn a value just above 0.90 into a passing threshold. Six repetitions on each graph are combined by the usual median, including the average of the middle pair.

Retain all **180 point classifications**, all **450 earlier/later endpoint pairs**, and all **30 family/comparator summaries**. If several brackets qualify, the representative bracket uses the earliest qualifying upper endpoint and the closest measured loss below it. Every other bracket and earlier reversal remains visible. A lead at every measured size is reported as such, without inventing a crossover. A lead only at the largest point is bounded by the sampled range; no unmeasured persistence is inferred. Do not interpolate a crossing, fit an asymptotic claim, or assume monotonicity between endpoints. An intermediate-size/sampler confirmation would require a separate held-out declaration.

## Outstanding gates before release

The prepared source must pass focused mocked full-schedule, exact arithmetic, twin-control, provenance-drift, lifecycle and failure tests after the current capture releases nonperformance execution. An independent reviewer must inspect the final collector/protocol and test results. Then freeze and commit the new package before any native call. This source-only draft and its existence do not constitute validation or permission to execute it. A later independent raw numerical audit must recompute the reported ratios and crossover classifications without importing collector aggregators.
