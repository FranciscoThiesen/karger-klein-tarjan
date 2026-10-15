# Prospective larger hierarchy/shuffled screen

**Source preparation only, 2026-10-15. No import, syntax check, tests, preflight,
freeze or native call has been performed for this package.** The six cases and
seeds below are fixed during the separate 72-child held-out study. That study's
partial timing results were not consulted, and its protocol is unchanged. This
screen remains separately declared regardless of that study's outcome. A
decision not to run must be recorded as unexecuted; any different matrix needs
a new prospective declaration.

## Fixed question and matrix

Does the frozen compressed-query KKT candidate's hierarchy advantage over
retained-edge Borůvka become stronger at the existing largest supported size,
and does it outperform any of the other four controls? The shuffled twin tests
whether the ordered core weights matter. The question is motivated by completed
compressed-query timing and work evidence; no historical observations enter
these estimates. This is a finite size screen, not a complexity fit.

| Weight twins | Vertex counts n | Density m/n | Intrusion |
|---|---|---:|---:|
| `leaf_hierarchy4`, `leaf_shuffled4` | 65,536; 1,048,576; 4,194,304 | 32 | 0 |

The exact six-row [manifest](manifest.csv) is mandatory. Graph seeds are
**11000009 and 11000027**; scalar KKT sampling seed is **2203**. The source-only
[freshness audit](SEED_FRESHNESS.md) found no prior declared use. Recheck the
declarations before freeze; never select a replacement seed using measured
outputs. Keep both weight twins and every lower point. No extra size, sampler,
alternative attachment block size, favorable early stopping or substitution
after failure is authorized by this protocol.

Graph one follows the manifest in increasing size with twins adjacent. Graph
two reverses the entire manifest, also reversing twin order. Each child runs
KKT, compacting Borůvka, retained-edge multigraph Borůvka, Kruskal, Prim and
original Borůvka. The unchanged harness checks one warmup and six timed calls
per solver, rotating every solver through all six positions. Thus **12 children
produce 504 certified outputs: 432 timed and 72 warmups**. Each graph/sampler
combination is one realization; the six repetitions are not six independent
graphs or forests. Two graph seeds remain confounded with order/host history.

These are existing engineered attachment graphs. Three cheap leaves per core
vertex force an initial star collapse. The hierarchy's forced core path has
weights ordered by dyadic boundary level, with every chord heavier; the shuffled
twin permutes core ranks while retaining cheap leaves. Separate generator RNG
streams preserve topology, IDs, vertex labels and physical edge order. Require
equal topology fingerprints and different weighted fingerprints at all **six
size/graph twin pairs**. No graph, certificate or measured boundary is weakened.

## Exact inherited binary and unchanged domain

Use the existing compressed binary, without rebuilding:

- Worktree: `/Users/random_person/Desktop/kkt-compressed-queries`.
- Parent freeze: `benchmark/results/compressed-query-2026-10-15/freeze.json`.
- Parent freeze SHA-256: `bd65da13058d3e9cfa58919a0fe5e02b8a46b1d0b8fe7f05801692d5a0866df9`.
- Binary: `bin/compressed-query/timing-build/compressed/retention_control`.
- Binary SHA-256: `74e604830c4c730395cd6c9e9dc61287a6d88a34cc89983bb4ee61dc3272a1b2`.

The new collector invokes the unchanged compressed collector's complete strict
freeze proof, including both parent variants and their ancestor artifacts. It
inherits the exact compressed executable, native sources, eight objects, shared
harness, compiler/SDK/flags, recipe/log hashes and arm64/512 MiB-stack profile.
It adds its own helper hash, this protocol, the exact manifest, seeds and
schedule. No parent helper or native file changes. Command and row validation
are local to this collector: it never overrides parent-module seed globals.
The existing aggregator has no seed-global dependency and receives fully
validated rows. Sampling remains scalar; packed sampling is not enabled.

At n=4,194,304, m=134,217,728 exactly reaches the existing inclusive n and m
limits. The core has q=1,048,576 vertices, 3q=3,145,728 local edges, and
core_m=131,072,000=125q, within simple-core capacity. IDs and positive unique
weight ranks fit the existing contract. **No 8M case or domain relaxation.**

Completed 1M compressed-child sampled RSS peaks scaled fourfold give a planning
range of roughly 31–32 GiB. This is not a memory bound or prediction: it misses
transient peaks, capacity/allocator changes, recursive overlap and host pressure.
The source-derived hierarchy expectation adds two retained-contraction rounds
from 1M to 4M, with about 11% more input-edge volume per original edge. Neither
projection predicts runtime. The supporting [feasibility note](FEASIBILITY.md)
retains its completed-data origin and explicit qualifications.

## Quiet execution and failure policy

Root must separately release quiet serial performance capture after all source,
mocked and independent review gates pass. The collector requires `--released`.
Use the same native process-group monitor, **40 GiB sampled RSS ceiling**, about
two-second polling, stop after three consecutive unavailable observations and
immediate stop on provider poison. Sampling is not continuous peak measurement.
Preserve `/usr/bin/time -l`, every exact argv, child CSV/certificate/log, RSS
record, UTC/monotonic interval, exit status and clock flag. Verify the owned
group is empty with a bounded observation after wrapper exit and before the
next launch. Use existing bounded cleanup on interruption/failure; mark exit
unknown before cleanup, suppress repeated SIGTERM during its bounded operation,
and restore the prior handler afterward. Clear that unknown state only with an
affirmative native-exit and empty-group proof; preserve any prior unknown state.
An unknown exit forbids continuing. Failed or interrupted evidence is never
overwritten.

Do not raise the ceiling, omit certification, skip a solver, replace the largest
case or discard completed failures. A resource failure is a reported result and
stops this fixed campaign. A retry would need an explicit new attempt with all
partial evidence retained, not silent substitution. There is no change to the
existing solver or certificate semantics for making the largest case fit.

Strict reload rechecks full parent provenance, schedule, all 504 raw rows,
certificates, clocks, resource evidence, empty groups and exact ordered combined
CSV concatenation. Keep flagged calls unchanged. Wall and process CPU are
separate clocks. Optional archived power-log correlation is diagnostic; Wake
Requests is not a wake transition, and no overlap does not establish complete
coverage or active sleep inhibition. Before release add study-specific ignore
rules for private raw power logs; no private events belong in report artifacts.

## Complete analysis and sustained measured brackets

Pair KKT with every competitor by case, graph, sampler and repetition, on both
clocks. The **720 paired ratios** retain integer time endpoints. Case estimates
pool all 12 paired ratios; graph estimates use each graph's six ratios. Neither
is replaced by a ratio of runtime medians. All wins, losses and trial/graph
ranges are descriptive, without confidence-interval or population claims.

| Canonical table | Rows | Derivation |
|---|---:|---|
| `paired_ratios` | 720 | 6 cases × 2 graphs × 6 repeats × 5 controls × 2 clocks |
| `comparisons` | 60 | 6 × 5 × 2 |
| `graph_comparisons` | 120 | 6 × 2 × 5 × 2 |
| `summary` | 72 | 6 cases × 6 solvers × 2 clocks |
| `graph_summary` | 144 | 6 × 2 × 6 × 2 |

For each family/control/size, reconstruct the four graph/clock medians as exact
Fractions of integer endpoints. Median of six is the mean of the middle pair.
Classify `strong_lead` if all four≤9/10; `narrow_lead` if all four<1 but not
strong; `loss` if all four>1; otherwise `mixed_or_tied` (including any exact tie).
Keep all **30 point classifications** (2 families × 5 controls × 3 sizes).

A strong observed crossover bracket requires an earlier `loss`, a later
`strong_lead`, and `strong_lead` at every still-larger measured size. Keep all
**30 earlier/later endpoint pairs** (2×5×3) and **10 family/control summaries**.
Select the earliest qualifying upper endpoint and closest measured loss below
it only as a representative; every earlier reversal and other bracket remains.
A largest-point-only lead has no measured persistence beyond 4M. Leads at all
sizes are not observed crossovers. No interpolation, assumed monotonicity,
historical pooling, drift normalization or asymptotic dominance claim.

Retained-edge Borůvka is the main test of whether filtering repays KKT overhead,
but a win against it is not a win against all six solvers. Report original
Borůvka, Prim and every other control even if faster. Publish absolute runtimes
and both graph medians as well as ratios. Any later extra size or sampler would
require its own declaration. An independent raw numerical audit must recompute
the final estimates and all crossover classifications without calling collector
aggregators.
