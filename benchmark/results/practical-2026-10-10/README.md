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
