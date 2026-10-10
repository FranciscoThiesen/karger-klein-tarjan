# Improving KKT without changing the benchmark

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

The final large-instance campaign retains the complete 18-case matrix. It uses
the earlier full 648-observation baseline after a source/protocol equivalence
review, with a fresh final run of all four algorithms. The
[baseline provenance note](LARGE_BASELINE_PROVENANCE.md) records exact hashes,
the unchanged fixture and timing bodies, and the limits of historical
before/after comparisons. Fresh final-run competitor timings determine its
winner claims.

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
