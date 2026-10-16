# Why linear counted work can still produce an NlogN timing fit

The current evidence supports a specific explanation for the scaling puzzle:
**several important amounts of KKT work grow almost proportionally to the input,
while their measured cost per event rises with input size.** A timing curve can
therefore bend upward even when those counts do not. The next step is to change
a costly access pattern and test it on the same inputs, rather than seek a
reassuring complexity label.

Let `N = n + m`. Even the simple finite model `T(N) = N × c(N)` has rising time
per input unit when `c(N)` rises. On a real machine, a load can become more
expensive as its working set grows; a small helper can generate a different call
sequence after specialization. Neither possibility changes the number of graph
edges visited. These are mechanisms to test, not conclusions from a curve alone.

The completed baseline and fresh 36-input candidate comparison are reported
below. The depth-query candidate reduces median running time on every tested
graph/size, but it does not remove the upward finite scaling curve: both versions
still favor NlogN in the six-size reanalysis. Three wall trials and two CPU trials
lose and remain in the result. Additional controls, phases and the actual new
Google Benchmark run remain pending; no partial result is used.

## Three different questions

| Question | What the present evidence can establish |
|---|---|
| How does theoretical work scale? | KKT's expected linear bound concerns ideal independent sampling and a stated primitive-cost model. It is an expectation over randomness, not a constant-nanoseconds-per-edge promise for every finite seeded execution. |
| What did this implementation count? | Exact counters describe selected loops and data structures on these particular inputs. They do not enumerate all instructions, allocation internals, memory traffic or hardware stalls. |
| Which finite time curve fits better? | A model can predict the measured size range better than another without proving an asymptotic class or identifying its cause. |

The [source audit](source-audit.md) found no remaining unconditional `m log n`
loop in the selected optimized path. In particular, its LCA sparse table is built
over blocks, not all Euler positions, and the path-search work has a linear
aggregate bound under the verifier's full-branching-tree invariants. This is a
source argument with explicit caller, word-width and sampling assumptions. It
should not be replaced by a benchmark fit, nor inflated into a proof that every
real execution has fixed cost per input unit.

This study concerns the opt-in path with retained parallel edges, direct Edge
queries, compressed verifier requests and scalar one-eighth sampling. An ordinary
default build selects a different path. The native public boundary includes
input conversion and internal temporary destruction; input generation,
independent MST certification and returned-result validation are outside it.

## What the completed baseline says

The archived Google Benchmark campaign selected NlogN for all 24 curves: 12 KKT
and 12 retained-Boruvka curves. A
separate [finite-model analysis](../kkt-scaling-model-analysis.md) reproduced the
raw means, the library's fit objective and all exported choices. It also tested
an affine linear model and retrospective larger-size holdouts. NlogN predicted
the final three sizes better than N for all 24 curves under all four recorded
clocks. Thus the upward shape is more substantial than an arbitrary label.

The label still has limited resolution. Google fits through the origin and
minimizes squared error in duration space, so large inputs dominate its choice.
Its NlogN basis has effective slope roughly 1.058–1.076 over the upper range,
whereas some observed KKT slopes are about 1.13–1.16. NlogN can be the closest
menu item without accurately describing the local exponent. The fixed-knot
regressions and blocked checks are exploratory, retrospective analyses of an
already observed campaign, not blind validation.

New diagnostics now match **72 exact Google input identities**, including both
weighted and topology fingerprints: three families, six sizes from 1K to 1M,
two graph seeds and two sampler seeds. The full [diagnostic report](DIAGNOSTICS.md)
and its [independent review](../../benchmark/scaling_investigation/analysis/INDEPENDENT_DIAGNOSTICS_EDITORIAL_REVIEW.md)
keep all inputs, clocks and ranges. The earlier model/source notes describe the
state before these matching diagnostics existed; this report incorporates the
completed follow-up.

Seven selected counters across the twelve family/graph/sampler curves give
**84 count curves**. Every one favors N over NlogN under the same through-origin
formula, applied to counts rather than durations. From 1K to 1M,
`kkt_edges/N` grows only 0.55–2.05%; contraction edge visits/N grow 1.46–6.88%.
This establishes near-linear measured edge volume on this matrix, not linear
instruction count. Counter totals overlap and have different meanings, so they
are not added into a literal total-operation model.

The diagnostic clocks locate substantial increases in query gathering,
component-minimum scans and mark scattering. Across all twelve realizations,
query-gather time per LCA-query event grows 1.93–2.53×; minimum-scan time per
contraction-edge event grows 4.41–5.94×. Query gathering includes request insertion
as well as LCA lookup. These are wall-phase/event ratios with precisely named
denominators, not CPU cost attributed to a single instruction or proof of cache
misses. LCA construction contributes less than 0.21 ns/N at the largest input
and its normalized cost decreases; rebuilding its layout was therefore a weak
first target for this campaign.

Allocation diagnostics likewise distinguish near-linear allocated volume from
access cost: stable bytes/N still means a larger absolute working set. They
measure cumulative requested/usable bytes and peak live usable bytes within the
instrumented C++ allocation scope, not RSS or all libc activity. Calibration on
six endpoint inputs found no growing twofold instrumentation factor, but does
not prove that every phase timer is unbiased. The full calibration ranges and
exact additive endpoint decompositions remain in the diagnostic report.

## The first intervention: return the depth the verifier actually needs

The compressed verifier needs an ancestor's **depth** to add and look up its
requests. The generic LCA interface returns an ancestor vertex ID, which the
caller then converts to a depth. Candidate D introduces an opt-in depth-specialized
query/request API, preserving the generic interfaces and the reference path.
The intended benefit is to remove unnecessary representation and access work;
its actual benefit must be measured.

The current [candidate declaration](../../benchmark/scaling_investigation/candidates/CANDIDATE_PROTOCOL.md)
holds contraction, sampling, graph generation, input ordering and the public
boundary fixed. Reference and depth variants are fresh same-source builds; only
the verifier object differs within each pair. The baseline sources were copied
before the patch, and [snapshot validation](../../benchmark/scaling_investigation/analysis/validation/snapshot-reload-attempt01.json)
proved that all completed baseline tables can still be regenerated from those
exact bytes. Historical timing is not substituted for a fresh reference run.

Correctness has passed natively and under the sanitizer profile. In each
profile, the focused test covers 164 trees, 2,499,404 query pairs, 317 marking
cases and 710 dispatch cases. Existing direct-Edge and full-solver MSF suites
also pass. Native wrong-linked-policy and invalid-depth guard cases are required
to fail in the prescribed way. The [complete passing gate](../../benchmark/results/scaling-investigation-2026-10-15/depth-correctness03/gate.json)
binds the actual sources, artifacts, commands and known process exits; earlier
failed validation attempts remain archived.

All 72 candidate work inputs also pass independent exact comparison: **4,608 of
4,680 counter values are unchanged**. The other 72 are `initialized_slots`, each
reduced by exactly the corresponding old `lca_vertices`; all 204 both-zero ratios
remain explicitly undefined. Exact MST IDs, input fingerprints and the existing
work trajectory are checked. This shows the intended narrowly changed accounting
on these inputs, not a speedup. The [work tables and provenance](../../benchmark/scaling_investigation/analysis/depth-work-analysis-attempt01/)
and [analysis review](../../benchmark/scaling_investigation/analysis/INDEPENDENT_CANDIDATE_ARITHMETIC_REVIEW.md)
retain every field.

The [actual object inspection](depth-codegen.md) prevents a misleading causal
story. Both default and explicit-noinline `query_depth` calls remain out of line,
with identical normal query instruction bodies in this build. The generic LCA
query is also out of line. However, reference `add_request` is called out of line,
while the depth-specialized request helper is inlined. Candidate D therefore
bundles representation changes with helper API/code-generation changes. Marking
only the query method noinline cannot isolate those effects, and any eventual
gain must not be called solely query-body inlining or a pure removed-load effect.

## Fresh paired timing: faster, still a rising per-input cost

The completed primary comparison fixes 36 inputs: all three families, six sizes,
both graph seeds and sampler 3001. Each input has a fresh reference/depth process
pair, one checked warmup and three timed calls. All 288 raw outputs pass strict
validation. The 108 paired observations per clock are preserved; wall and process
CPU remain separate. G1 visits sizes ascending and G2 descending, so graph and
size order remain confounded. No baseline diagnostic or historical Google timing
is pooled into this comparison.

Depth wins **105 of 108 wall pairs** and **106 of 108 CPU pairs**. All 36
per-graph medians on each clock favor depth, as do all 18 pooled case medians.
The table reports the median of six matched-repetition depth/reference ratios
(two graphs, three repetitions), not a ratio of separately computed medians.
Ratios below one favor depth; every input remains in the table.

| Family | Vertices n | Wall ratio | Process CPU ratio |
|---|---:|---:|---:|
| Ordered hierarchy | 1,024 | 0.841247 | 0.841671 |
| Ordered hierarchy | 4,096 | 0.887748 | 0.884877 |
| Ordered hierarchy | 16,384 | 0.874474 | 0.876880 |
| Ordered hierarchy | 65,536 | 0.848660 | 0.853138 |
| Ordered hierarchy | 262,144 | 0.905159 | 0.907128 |
| Ordered hierarchy | 1,048,576 | 0.917878 | 0.911371 |
| Shuffled weights | 1,024 | 0.883484 | 0.882797 |
| Shuffled weights | 4,096 | 0.901807 | 0.901411 |
| Shuffled weights | 16,384 | 0.896431 | 0.893493 |
| Shuffled weights | 65,536 | 0.838425 | 0.838402 |
| Shuffled weights | 262,144 | 0.879264 | 0.879131 |
| Shuffled weights | 1,048,576 | 0.892549 | 0.891719 |
| Connected G(n,m) | 1,024 | 0.887958 | 0.888689 |
| Connected G(n,m) | 4,096 | 0.898426 | 0.898819 |
| Connected G(n,m) | 16,384 | 0.904777 | 0.904437 |
| Connected G(n,m) | 65,536 | 0.858825 | 0.859222 |
| Connected G(n,m) | 262,144 | 0.916134 | 0.913135 |
| Connected G(n,m) | 1,048,576 | 0.914812 | 0.914574 |

At 1M vertices, the pooled median time reduction is about 8–11%, depending on
family and clock. This is a within-KKT comparison, not a new result against
Boruvka, Prim or Kruskal. Only one sampling seed is timed; the extra work-only
sampler is not additional timing evidence.

The five losing clock observations come from three calls. G1/G2 below mean
19000013/19000043; every call uses sampler 3001.

| Family / n | Graph | Repetition | Losing wall ratio | Losing CPU ratio |
|---|---|---:|---:|---:|
| Connected G(n,m) / 1,024 | G1 | 2 | 1.013688 | 1.018149 |
| Shuffled / 4,096 | G2 | 1 | 1.190134 | None; CPU wins |
| Shuffled / 1,024 | G2 | 3 | 1.558948 | 1.390582 |

No explanation or removal of these observations is assumed. Individual ratio
ranges, both graph medians and all absolute times remain in the
[complete tables](../../benchmark/scaling_investigation/analysis/depth-timing-analysis-attempt01/)
and [all-size summary](../../benchmark/scaling_investigation/analysis/depth-timing-summary-attempt01/all-size-ratios.csv).
The timing capture uses separate adjacent processes and pairs repetition labels;
it is not a simultaneous same-host-state observation of both implementations.

### The finite shape has not become linear

For each policy, family, graph and clock, the analysis fits both `a*N` and
`a*N*log2(N)` using Google's through-origin duration-space objective. It keeps two
versions: all 18 timed calls and the six per-size means. Balanced repetitions
give the same fitted coefficient; the first objective additionally retains
within-size variation in its residual RMS.

**All 48 two-model selections favor NlogN**, covering both policies, both clocks,
six family/graph curves and both aggregations. This is custom numerical
reanalysis of the fresh native calls, not Google Benchmark's emitted BigO/RMS
rows. The actual candidate library run is still pending. All
[96 fitted models](../../benchmark/scaling_investigation/analysis/depth-timing-analysis-attempt01/timing-fits.csv)
and [1,152 residual records](../../benchmark/scaling_investigation/analysis/depth-timing-analysis-attempt01/timing-residuals.csv)
remain available.

Lower elapsed time does not imply a flatter relative curve. Based on each graph's
own endpoint median, reference CPU time/N grows 2.16–2.44× from 1K to 1M across
the six curves; depth grows 2.11–2.66×. The candidate improves each endpoint's
median while leaving other size-dependent costs. Those endpoint growth ratios
also depend on the retained small-input observations and are not asymptotic
exponent estimates.

| Evidence | Current status | Scope |
|---|---|---|
| Exact work comparison | Complete, 72 inputs | Selected counter preservation and the initialization delta |
| Fresh reference/depth timing | Complete, 36 inputs | Within-KKT improvement on this fixed matrix, with every losing trial retained |
| Six-input three-policy control | Pending | Query-method noinline control; helper changes remain bundled |
| Paired phases and allocation | Pending | Diagnostic explanation, not an uninstrumented performance result |
| New Google Benchmark curves | Pending | Actual library fit, distinct from the six-size reanalysis above |

Compact figures await the next quiet rendering interval. The central
three-family view will show logical `kkt_edges/N` relative to its own 1K value
alongside both fresh time/N curves relative to the **same reference 1K time/N**.
These distinct dimensionless baselines will be explicit; the overlay is not time
per counted event. Separate plots retain every paired ratio and the six-input
control's three comparison directions. The
[analysis and plotting protocol](../../benchmark/scaling_investigation/analysis/CANDIDATE_ANALYSIS.md)
documents the arithmetic and passed synthetic gates.

The fresh comparison supports a useful implementation improvement without a
linear timing label. Phase/control evidence is still needed to explain how the
depth-specialized API and its generated code produce that gain; the object
inspection above rules out a simple query-body-inlining story.

## A separate next hypothesis

The minimum scan is another plausible target. A [packed-argmin design](packed-minimum-design.md)
would keep cost and selected index together, avoiding a dependent gather of the
previous minimum edge's cost. It doubles the per-vertex state width, which can
also hurt locality. It is prospective: no implementation, correctness result or
performance claim is included here. It must remain a separate experiment so
that any effect is distinguishable from the depth-query change, and the shared
retained-B helper policy must be stated if that comparison is revisited.

The baseline already answers part of the puzzle: selected work counts near N
and a finite NlogN time fit can coexist. The fresh depth-query comparison reduces time but retains the rising finite
curve. Its phase and compiler controls will narrow which costs changed; another
optimization should answer a separate measured hypothesis.
