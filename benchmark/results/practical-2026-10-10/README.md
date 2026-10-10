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
Kruskal and Prim's paired ratios rise by about 19%. This run does not isolate how much
of that case's KKT regression comes from the code change. All control movement
and graph ranges remain in the [before/after plot](csr_analysis/diverse_before_after.png)
and raw comparisons; the ranges are not confidence intervals.

By paired runtime ratios, KKT still has three case-level leads over all competitors: hubs with 4,096
and 16,384 vertices and the 16,384-vertex star. Only the two hubs lead on
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
