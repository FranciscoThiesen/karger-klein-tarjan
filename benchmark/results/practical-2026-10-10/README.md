# Improving KKT without changing the benchmark

Six accepted performance commits, from `4eb3ca1` through `2d4fbf1`, reduce
internal hashing, query indirection, contraction storage, repeated edge copies,
and public-result rehashing. The minimum-cost cache experiment was rejected;
its patch, raw results, and useful boundary tests are retained below.

The [cumulative report](overall_analysis/report.md) compares the fresh
`0820435` [baseline](baseline.csv) with the primary final
[reserve run](reserve.csv), using the same compiler, fixtures, timing boundary,
39 cases, and all four algorithms. Each phase has 5,616 certified timed results
and 1,404 checked warmups. KKT's matched case medians improve in **39/39 cases**,
with final/baseline ratios from **0.393x to 0.969x**. These are medians of
matched ratios, aggregated over repetitions, sampling seeds, then graph seeds.

| Example | Final / initial KKT runtime | Final KKT / Kruskal | Final KKT / Borůvka |
| --- | ---: | ---: | ---: |
| random_4_n65536 | 0.491x | 1.321x | 0.709x |
| random_32_n65536 | 0.393x | 1.795x | 3.409x |
| star_n16384 | 0.421x | 0.395x | 0.228x |
| geometric_grid_n16384 | 0.815x | 0.966x | 0.521x |

The primary and separate full-matrix confirmation runs both place KKT below
all three competitors by case-level paired medians in six cases: all three
hubs, the two larger stars, and the largest geometric grid. **All three hubs
and the 16,384-vertex star** lead on every graph-level paired median in both
runs. The geometric grid is a near-tie with Kruskal, and the 4,096-vertex
star's case-median lead does not hold on every confirmation graph; see the
[confirmation evidence](confirmation_analysis/report.md).
Substantial gaps remain elsewhere: dense random graphs still favor Borůvka,
and the hierarchical paths still favor Kruskal and Prim. The
[cumulative change plot](overall_analysis/diverse_before_after.png) and
[full competitor plot](overall_analysis/diverse_final_competition.png) show
every case rather than only the wins.

The [large-instance sweep](large_analysis/report.md) extends the comparison to
1,048,576 vertices and 33,554,432 edges. Separate repeated checks support useful
leads on a 262,144-vertex hub and a million-vertex star: paired KKT/Kruskal
ratios are **0.816x** and **0.442x**. This does not extend to general large graphs:
the million-vertex hub loses to Kruskal, all large random cases lose to Kruskal,
and the three complete cases regress against the historical KKT baseline.
The full matrix and the two post hoc confirmations remain separate below.

Case counts do not measure expected performance on an application workload.
Only three graph seeds are independent graph samples; graph ranges are not
confidence intervals. Unchanged competitor timings also moved between phases.
The smallest clustered case even has one graph-level before/after ratio above
one despite its improving case median. Incremental regressions and the
rejected experiment remain in the stage history below. These finite
measurements establish practical improvements on this matrix, not an
asymptotic crossover or universal KKT dominance.

At final source revision `2d4fbf1`, all eight [Bazel test targets](final-bazel.log)
pass with valid cached results. The native correctness suites also
[pass under UBSan](final-ubsan.log), including eight simple tests, 15 regression
groups, 214 independent contraction cases, and the certificate checks.
Every measured MST must match an independently certified reference. The
unchanged harness, fixtures, certificate, and competitor sources are recorded
by hash in [metadata.json](metadata.json).

## Stage 1: local heavy-edge marks

The first accepted change replaces KKT's internal heavy-edge hash sets with
byte marks indexed by the current graph's edge positions. Public verifier APIs
still return the caller's original edge IDs; no storage depends on their range.
The algorithm, random stream, fixtures, competitors, and timing boundary are
unchanged.

The [complete first-stage report](mask_analysis/report.md) compares fresh
baseline and candidate binaries on the original 39 cases, all three graph and
sampling seeds, one warmup, and four repetitions. Each phase retains 5,616
timed results and 1,404 checked warmups. Every result matches an independently
certified MST. All seven Bazel test targets and the Make correctness suites pass.

On random graphs with 65,536 vertices, KKT's paired runtime falls to **70.4%**
of baseline for `m=4n` and **58.3%** for `m=32n`. This is a substantial reduction,
but it does not yet create a new winning graph family: the three measured
four-algorithm wins remain two hub cases and the largest star. All losses and
unchanged-competitor timing drift remain in the report. The smallest star is
essentially unchanged (ratio 1.000094).

[Raw baseline](baseline.csv), [raw candidate](mask.csv), and
[commands, build profile, and source/binary hashes](metadata.json) make the
result reviewable. Source revision starts at `0820435`; the measured candidate
sources are identified by SHA-256. Measurements use the same native Apple clang
Make profile on an Apple M3 Max. No builds, tests, or plots run during timing.

## Stage 2: contiguous verifier queries

The second change groups ancestor-path queries into contiguous endpoint ranges
and writes their maxima directly to graph-edge positions. This removes linked
query traversal and duplicate query metadata. The
[stage 2 report](csr_analysis/report.md) compares the stage 1 binary
([mask.csv](mask.csv)) with the new candidate ([csr.csv](csr.csv)); these are
incremental results, not ratios against the original baseline. The same full
39-case protocol retains 5,616 validated timed outputs and 1,404 checked warmups
per phase.

KKT's paired median improves in **36/39 cases**. At 65,536 vertices, runtime
falls to **81.7%** of stage 1 for `m=4n` and **68.0%** for `m=32n`. The three
observed regressions are retained:

| Case | Stage 2 / stage 1 runtime | Graph-level ratio range |
| --- | ---: | ---: |
| random_128_n1024 | 1.012x | 0.976–1.018x |
| random_128_n16384 | 1.012x | 0.940–1.022x |
| grid_n1024 | 1.065x | 1.049–1.217x |

The small grid also shows substantial movement in unchanged competitors:
Kruskal and Prim's paired ratios rise by about 19%. This run does not isolate
how much of that case's KKT regression comes from the code change. All control movement
and graph ranges remain in the [before/after plot](csr_analysis/diverse_before_after.png)
and raw comparisons; the ranges are not confidence intervals.

By paired runtime ratios, KKT still has three case-level leads over all
competitors: hubs with 4,096 and 16,384 vertices and the 16,384-vertex star.
Only the two hubs lead on
every graph-level median. Ranking the separately aggregated runtime medians
adds the 1,024-vertex hub, but its paired KKT/Kruskal ratio is 1.013x; this close
case is not a confirmed new win. The larger random cases remain losses: for
`random_32_n65536`, KKT is **1.82x** Kruskal's runtime and **3.44x** Borůvka's.
The [complete competitor plot](csr_analysis/diverse_final_competition.png)
retains these remaining gaps.

The four affected Bazel targets and the Make correctness suites pass, including
14 regression groups. An [independent parent-walk oracle](csr_query_oracle.cpp)
checks ancestor endpoints, two-half paths, empty queries, and negative weights
through `INT_MIN`; its [UBSan run passes](csr_query_oracle_ubsan.log).
ASan validation is unavailable for this run: its runtime fails before `main`,
both for the [oracle](csr_query_oracle.log) and an
[empty-program control](asan_empty_control.log). This startup failure is not
counted as a passing sanitizer check. Exact source and binary hashes, validation
results, and commands are in [metadata.json](metadata.json).

## Stage 3: cheaper contraction traversal

The third change labels contraction components by following each vertex's
cheapest neighbor, removing the selected-edge adjacency lists and duplicate
bitmap. Once contraction leaves no inter-component edges, it also skips the
remaining edge scans. Independent oracle checks cover 210 contraction cases;
the Make suites and four affected Bazel targets pass, including instrumented
linear-work bounds.

The [stage 3 report](contraction_analysis/report.md) compares
[stage 2](csr.csv) with [stage 3](contraction.csv), again retaining all 39 cases,
5,616 timed outputs, and 1,404 checked warmups per phase. KKT improves in
**29/39 cases**. The clearest gains are the three stars, whose paired runtimes
fall to **79.2–81.3%** of stage 2. The 65,536-vertex random cases improve by
only about 1–2% in this stage. All ten observed regressions remain visible:

| Case | Stage 3 / stage 2 runtime | Graph-level ratio range |
| --- | ---: | ---: |
| random_4_n1024 | 1.0858x | 0.9897–1.1089x |
| random_32_n1024 | 1.0204x | 0.9679–1.0357x |
| grid_n4096 | 1.0081x | 0.9202–1.0516x |
| hub_n1024 | 1.0712x | 0.9686–1.0833x |
| hub_n4096 | 1.0012x | 0.9756–1.0506x |
| clustered_n4096 | 1.0167x | 0.9893–1.0323x |
| clustered_n16384 | 1.0068x | 0.9777–1.0167x |
| hierarchical_path_n4096 | 1.0066x | 0.9579–1.0382x |
| complete_n512 | 1.0002x | 0.9558–1.0488x |
| complete_n1024 | 1.0306x | 0.9910–1.0629x |

In this run, all three hubs and the 16,384-vertex star beat all competitors
by paired ratios, including every graph-level median. The additional small-hub
lead needs caution: KKT itself takes 7.1% longer than stage 2 while the unchanged
Kruskal control takes 18.6% longer by paired medians. This is an observed lead,
not evidence that the contraction change created a reliable new crossover.
See the [before/after plot](contraction_analysis/diverse_before_after.png) and
[all-competitor plot](contraction_analysis/diverse_final_competition.png) for
the retained gains, losses, and timing movement.

## Stage 4: direct sampled-forest recovery

Temporary sampled branches now carry parent-edge positions, so KKT recovers
the sampled forest directly without a hash lookup for every parent edge.
Public IDs and RNG draws are preserved. Forest tuple order changes, while
exact MST validation remains required. The Make suites and four affected
Bazel targets pass; instrumented checks confirm that internal hash lookups
are gone and hash insertions remain only at the public output boundary.

The [stage 4 report](sample_analysis/report.md) compares
[stage 3](contraction.csv) with [stage 4](sample.csv), preserving all 39 cases,
5,616 validated timed outputs, and 1,404 checked warmups per phase. KKT's paired
runtime improves in **33/39 cases**. The 65,536-vertex `m=4n` random case takes
**92.8%** of stage 3 runtime; the 16,384-vertex planted-tree case takes **92.0%**.
The largest `m=32n` case changes little at 99.2%. All six regressions remain:

| Case | Stage 4 / stage 3 runtime |
| --- | ---: |
| random_32_n1024 | 1.002x |
| random_128_n16384 | 1.066x |
| random_dense_anchor_n1000 | 1.040x |
| clustered_n1024 | 1.052x |
| planted_tree_n1024 | 1.017x |
| star_n4096 | 1.034x |

The two hubs at 4,096 and 16,384 vertices and the 16,384-vertex star remain
below all competitors on every graph-level paired median. The small hub's
earlier lead disappears: its paired KKT/Kruskal ratio is 1.053x despite KKT's
own improvement. Unchanged competitor timings also move between phases,
reinforcing the need to treat close leads cautiously. The
[before/after plot](sample_analysis/diverse_before_after.png) and
[competitor plot](sample_analysis/diverse_final_competition.png) retain the
full comparison and descriptive graph ranges.

## Stage 5: reuse temporary edge storage

Vertex compaction now relabels sampled and filtered edges in their existing
vectors. The non-consuming API preserves its input, and zero-vertex inputs
return before a minimum-degree lookup. Exact compaction and empty-sampling
regressions pass, alongside the Make suites and three affected Bazel targets.

The [stage 5 report](owned_analysis/report.md) compares [stage 4](sample.csv)
with [stage 5](owned.csv) under the same 39-case protocol: 5,616 validated timed
outputs and 1,404 checked warmups per phase. KKT improves in **29/39 cases**;
the 65,536-vertex `m=32n` case takes **89.0%** of stage 4 runtime. The largest
observed gain is the small grid at 83.4%, but all three unchanged competitors
also improve substantially there, so the run does not isolate a code-only
benefit. All ten observed regressions are retained:

| Case | Stage 5 / stage 4 runtime |
| --- | ---: |
| random_4_n1024 | 1.027x |
| random_4_n4096 | 1.013x |
| random_4_n16384 | 1.001x |
| random_128_n1024 | 1.006x |
| random_128_n4096 | 1.003x |
| random_128_n16384 | 1.011x |
| geometric_grid_n1024 | 1.016x |
| hub_n1024 | 1.022x |
| clustered_n1024 | 1.028x |
| planted_tree_n1024 | 1.033x |

The two larger hubs and the largest star remain below all competitors on every
graph-level paired median. The small hub again leads by case-level paired
ratios, but not on every graph; its earlier reversals remain a reason for
caution. The largest `m=32n` case still takes **3.22x** Borůvka's runtime.
The [before/after plot](owned_analysis/diverse_before_after.png) and
[competitor plot](owned_analysis/diverse_final_competition.png) retain every
case and descriptive graph range.

## Rejected experiment: cached contraction minima

Caching each vertex's minimum edge cost adds an integer array, about `4n` bytes
per contraction on this build. The [complete experiment](minimum_analysis/report.md)
compares [stage 5](owned.csv) with [the candidate](minimum.csv), retaining the
same 5,616 timed observations and 1,404 checked warmups per phase. It improves
27/39 paired case medians, mostly modestly, and regresses in 12. The largest
`m=32n` case takes **1.060x** stage 5 runtime. The small grid takes 1.213x,
but unchanged Kruskal takes 1.520x there; these observations do not establish
that the cache caused either slowdown. The
[before/after figure](minimum_analysis/diverse_before_after.png) and
[competitor figure](minimum_analysis/diverse_final_competition.png) preserve
every loss and the movement in unchanged controls.

The extra storage does not show a compelling practical benefit in this run,
so the candidate is **rejected** and archived as
[minimum_candidate.patch](minimum_candidate.patch). Subsequent experiments
start from stage 5, not this candidate. Four new contraction-oracle cases for
`INT_MIN` and `INT_MAX` weights are retained, with the original `m+7n`
initialized-slot bound; rejecting the optimization does not discard its useful
boundary checks.

## Stage 7: reserve public result storage

KKT now reserves the public result set's buckets once, using the known number
of selected edges. The [stage 7 report](reserve_analysis/report.md) compares
[stage 5](owned.csv) with [this candidate](reserve.csv); the rejected minimum
cache is absent. The same full protocol retains 5,616 validated timed outputs
and 1,404 checked warmups per phase. KKT improves in **22/39 cases**. The three
stars take **70.6%, 62.7%, and 53.7%** of stage 5 runtime as their size grows;
the largest random tree takes 84.1%.

This is an accepted tradeoff, not a universal improvement. All **17 observed
regressions** remain in the report and
[before/after figure](reserve_analysis/diverse_before_after.png). In particular,
`random_32_n65536` takes **1.128x**, `random_128_n16384` takes 1.076x, and
`random_128_n4096` takes 1.053x stage 5 runtime. Unchanged competitors also move
between runs, so these measured changes do not isolate code effects from
machine state. The dense cases still lose to Borůvka.

The [competitor figure](reserve_analysis/diverse_final_competition.png) shows
six cases below all competitors on every graph-level paired median: all three
hubs, the two larger stars, and the 16,384-vertex geometric grid. The geometric
grid's primary-run lead over Kruskal is only **3.4%**. The separate full-matrix
confirmation below qualifies that result; this primary campaign remains intact.

## Full-matrix confirmation

The same final binary ran all 39 cases again with the original three graph
seeds, three sampling seeds, four repetitions, and one warmup. All **5,616 timed
outputs and 1,404 warmups** passed correctness checks. The
[confirmation CSV](confirmation.csv) and [report](confirmation_analysis/report.md)
remain separate from the primary [reserve CSV](reserve.csv); neither run is
replaced or selected according to its outcome.

The same six cases lead over all competitors by paired case medians. Only
the three hubs and the 16,384-vertex star also lead on every graph-level median
in both full runs. The geometric grid's confirmation KKT/Kruskal ratio is
**0.9869x**, with a graph range of **0.9780–1.0013x**: a near-tie, not a robust
new dominance claim. The 4,096-vertex star has a stronger case-median ratio of
**0.6999x**, but its graph range reaches **1.0377x**. Its lead is therefore
qualified by a retained graph-level loss.

Despite unchanged code, confirmation/primary KKT ratios span **0.909–1.026x**,
with nine cases slower. The [repeat-run plot](confirmation_analysis/diverse_before_after.png)
shows this variation and the unchanged controls; it is not an additional
optimization result. The [confirmation competitor plot](confirmation_analysis/diverse_final_competition.png)
retains the many cases that still favor another implementation.

The [family diagnosis](FAMILY_DIAGNOSIS.md) adds 162 separately checked,
untimed observations. Every tested hub, clustered, random, and geometric-grid
observation uses sampling and heavy-edge filtering; the hub leads are therefore
not all one-contraction shortcuts. Stars finish in their first contraction and
provide no evidence of sampling's benefit. These counters establish which
paths execute, not that sampling caused the observed timing advantage.

## Final complexity diagnostics

The [final diagnostic report](complexity/report.md) validates **378 raw Google
Benchmark records covering 1,134 timed calls**, plus **180 separate logical-work
observations**. GoogleTest checks structural work bounds, including contraction
visits, path-query visits, median-table size, and the hierarchical path's
recursive edge volume; it does not assert noisy wall-clock thresholds.

The benchmark uses `Complexity(benchmark::oAuto)` and `SetComplexityN(n + m)`,
the fitting feature described in the
[official Google Benchmark guide](https://google.github.io/benchmark/user_guide.html#calculating-asymptotic-complexity-big-o).
The [version 1.5.2 implementation](https://github.com/google/benchmark/blob/v1.5.2/src/complexity.cc)
selects its automatic model from CPU time, then fits manual time to that model.
Its [18 retained fitted models](complexity/builtin_complexity.json)
are 12 `N log N`, three `N²` for dense-random KKT, and three `N` for star KKT.
Those finite-window labels are not proofs of asymptotic complexity. Independent
fits to manual time give KKT full-window power exponents **1.175** for `m=4n`,
**1.379** for `m=32n`, and **1.001** for stars over 1,024–65,536 vertices.

Over 1,024–262,144 vertices, counted work per `N=n+m` grows **1.77x** for
`m=4n` and **3.06x** for `m=32n`, while the star and hierarchical-path controls
stay nearly flat. The [work components](complexity/work_per_input.png),
[normalized costs](complexity/normalized_costs.png), and
[local slopes](complexity/effective_exponents.png) show why lower constants
have not established general linear wall-clock scaling or eventual dominance.
The counters exclude allocator internals, hash probes, cache misses, and CPU
instructions; they are a diagnostic proxy, not a complete operation count.

This diagnostic uses arithmetic means across balanced seeds, a separate Bazel
`-O3` build, and registration-order timing. It is not pooled with the Make-based
paired medians above. The [metadata](complexity/metadata.json) retains exact
build profiles, binary hashes, and output provenance.

The [original KKT paper](https://people.csail.mit.edu/karger/Papers/mst.pdf)
proves expected linear time in a unit-cost random-access model with edge-weight
comparisons and linear-time verification; expectation is over the algorithm's
random choices for an input. That bound hides constants and does not model
allocator or cache costs. Comparing Big-O upper bounds alone does not guarantee
an actual crossover against another implementation. Finite fits and passing
work-bound tests neither prove the full theorem for this implementation nor
predict an eventual practical win.

## Large-instance campaign

The [complete fresh sweep](large_analysis/report.md) retains all **18 cases**,
three graph seeds, three sampling seeds, **one repetition and zero dedicated
warmups**, for **648 validated timed observations** across four algorithms.
[large_final.csv](large_final.csv) is the primary evidence. It includes up to
1,048,576 vertices and 33,554,432 edges. With only one timing per seed pair,
the sweep is exploratory: it does not measure within-pair repeatability, and
the nine trial blocks do not give exactly balanced algorithm positions.

KKT leads all competitors by both case and every graph-level paired median in
five cases: hubs at 65,536 and 262,144 vertices and all three stars. The hub
fixture is a star backbone plus random edges up to `m=4n`; weights are randomized
together, without planted light spokes. The separate [family diagnosis](FAMILY_DIAGNOSIS.md)
checks hubs through 65,536 vertices and shows sampling and filtering, while
stars finish through one contraction. These wins are useful measured cases, not evidence
that larger inputs generally favor KKT.

The losses remain substantial. The 1,048,576-vertex hub takes **1.269x**
Kruskal's runtime. All nine large random cases lose to Kruskal; the million-vertex
`m=4n` and `m=32n` cases take **3.143x** and **4.206x**, respectively. At
65,536 vertices and `m=512n`, KKT takes **9.935x** Borůvka's runtime.
Every complete case loses to Prim and Borůvka, with the 4,096-vertex complete
case taking **12.135x** Borůvka's runtime. The
[runtime curves](large_analysis/large_scaling.png),
[paired ratios](large_analysis/large_ratios.png),
[fixed-vertex density comparison](large_analysis/density.png), and
[all-case competitor plot](overall_analysis/large_final_competition.png)
retain those losses. Curves connect measured points; they do not establish
an unmeasured crossover.

The [historical before/after comparison](overall_analysis/report.md#large-suite)
reuses every observation from the earlier 648-result baseline. KKT's matched
case medians improve in **15/18 cases**, with final/baseline ratios down to
**0.311x**. All three complete cases regress: **1.090x** at 2,048 vertices,
**1.034x** at 4,096, and **1.037x** at 8,192. The
[change plot](overall_analysis/large_before_after.png) retains these regressions
and unchanged-competitor movement. This is historical evidence, not a freshly
rerun baseline: the [provenance review](LARGE_BASELINE_PROVENANCE.md) establishes
matching fixture bodies, timing protocol, compiler configuration, and core
behavior at source level, but the old executable hash is unavailable and
machine state cannot be reproduced. Winner claims above use only the fresh
run's contemporaneous competitor timings.

### Separate targeted confirmation

After observing the large sweep, exactly two cases were selected **post hoc**:
`hub_n262144` and `star_n1048576`. The same binary reran both with all four
algorithms, all three graph and sampling seeds, **four repetitions and one
warmup** per seed pair. All **288 timed outputs and 72 warmups** passed; the
four timed positions are balanced within every seed pair. The
[raw confirmation](large_confirmation.csv) and
[confirmation report](large_confirmation_analysis/report.md) remain separate
from the 18-case sweep and are not a representative recheck of the full matrix.

| Confirmation case | KKT (ms) | Kruskal (ms) | Prim (ms) | Borůvka (ms) | Paired KKT / Kruskal |
| --- | ---: | ---: | ---: | ---: | ---: |
| Hub, n=262,144 | 52.950 | 65.195 | 398.962 | 126.993 | 0.816x |
| Star, n=1,048,576 | 27.418 | 62.368 | 638.316 | 190.682 | 0.442x |

Displayed times are hierarchical medians; paired ratios are aggregated from
matched timings and need not equal the ratios of displayed times. Both cases
lead all competitors on every graph-level paired median. The KKT/Kruskal graph
ranges are **0.811–0.829x** for the hub and **0.426–0.478x** for the star.
One of the star's 36 individual KKT/Kruskal pairs is a loss and remains in
the data. The [confirmation runtimes](large_confirmation_analysis/large_scaling.png)
and [ratios](large_confirmation_analysis/large_ratios.png) show the two cases
without adding them to the primary curves. Three graph seeds and post hoc case
selection limit generalization; these ranges are not confidence intervals.
Exact primary and confirmation commands, executable hashes, output hashes,
and checked record counts are retained in the [campaign metadata](metadata.json).

## Reproduction

To reproduce this comparison, build the two revisions into separate output
directories with the same Make flags, then run each binary serially:

```sh
make -j4 test diverse-benchmark
./bin/diverse_benchmark --scale --repetitions 4 --warmups 1 > candidate.csv
python3 benchmark/analyze_optimization.py --baseline-csv baseline.csv --final-csv candidate.csv --output-dir comparison
```

The analyzer requires the entire 39-case matrix and preserves regressions.
The optional large comparison requires all 18 existing large cases using one
repetition and no explicit warmups, analyzed separately from this suite.
