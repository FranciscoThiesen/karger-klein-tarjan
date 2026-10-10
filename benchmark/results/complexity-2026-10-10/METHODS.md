# Complexity diagnostics

This experiment separates the number of explicit operations from the time
required to execute them. It does not infer a theorem from a fitted curve.
The base revision is `5d57f8322041ddcaed49a6cfd5ac3dff7d820667`; algorithm
changes in this experiment add counters only. `metadata.json` records the
exact source hashes, build profile, machine, commands, and completion status.

## GoogleTest: deterministic regression gates

`//:complexity_test` links separate libraries compiled with
`KKT_ENABLE_WORK_STATS`. Its six tests check:

- A star finishes in one contraction, with no sampling or verifier work.
- Nested counter collectors restore their previous scope.
- Relabeling edges with billion-scale sparse IDs changes none of the counters.
- Hierarchical paths have geometrically bounded recursive edge volume.
- Median-table construction stays below twice the original leaf count on
  full branching trees of increasing height.
- Instrumented random runs return the independently certified MST and satisfy
  local pass-count bounds.

Tests deliberately do not assert a wall-clock slope or an expected randomized
bound for each individual seed. Such assertions would confuse expectation with
a deterministic guarantee. The existing correctness suites also run against
the normal libraries.

## Work observations

`work_sweep --large` emits 180 observations: four families, five sizes,
three graph seeds (`17,42,999`), and three sampling seeds (`0,1,7`). Sizes are
1,024, 4,096, 16,384, 65,536, and 262,144 vertices. The families are random
graphs with `m=4n` and `m=32n`, stars, and hierarchical paths. All use the
existing shared graph generator, with identical draw order and fixture rules.
Random graphs are random recursive trees supplemented with missing endpoint
pairs, not uniform samples from all connected graphs. Weights are distinct.

Each collection scope includes conversion from the tuple graph to KKT's input,
the complete KKT call, and temporary input destruction. Reference construction
and certification are outside the scope. Every result must exactly match the
unique MST's edge-ID set. The independent certificate checks source edges,
connectivity, acyclicity, and the cycle optimality condition using binary
lifting. A cost sum alone is insufficient.

The 65 counters cover recursive input volumes, contraction and isolation
passes, sampling, verifier components, full branching tree construction,
path searches, LCA preprocessing/queries, explicit initialized slots, edge
materializations, and hash API calls. `work_metrics.hpp` defines a work proxy
as a sum of selected logical events. Different events have equal weight in
this proxy; visiting an edge and copying it can both count. Input volumes,
call totals, and other overlapping summary counters are excluded.

The proxy is not an instruction count or a complete cost model. It excludes
allocator internals, vector growth copies, deallocation, hash collisions and
rehashing, and cache/memory latency. Hash lookups and insertions count API
items, not internal probes. Initialized slots are elements, not bytes. Raw
component counters are retained so the arbitrary weights of the sum do not
hide the individual trends. Arithmetic means across the balanced seeds
estimate sampled expected work; nine observations per point are limited
evidence about the full randomized distribution.

## Google Benchmark: elapsed-time observations

The normal, uninstrumented `complexity_benchmark` measures KKT and Kruskal on
the two random families and stars. Seven doubling sizes run from 1,024 to
65,536 vertices. Each family/algorithm/graph-seed registration has three
repetitions, each consisting of three calls cycling sampling seeds `0,1,7`.
Thus the 378 raw JSON iteration records represent 1,134 checked MST calls.
Each record averages the three sampling-seed calls; it does not preserve
individual sampling-seed timing. For Kruskal these are repeated calls.

Timing uses `steady_clock` through `UseManualTime`. It includes KKT's tuple
conversion and temporary input destruction. Returned-result destruction and
validation are excluded for both algorithms. The certificate is constructed
before each repetition. There are no additional warmups. Sizes and algorithms
run in registration order, not alternating paired order; this is a scaling
diagnostic, not a close-race confirmation experiment. No builds, tests,
instrumented sweeps, or plots run concurrently with timing. The ordinary
desktop session has no controlled affinity, power state, or thermal state.

This run uses Bazel's optimized arm64 profile plus `-O3`, with assertions
disabled. It does not use Make's `-march=native` profile. Timings from previous
experiments are not pooled. Google Benchmark 1.5.2 cannot read
`hw.cpufrequency` on this machine and reports an invalid 24 MHz value; its
frequency/scaling metadata is ignored. Manual durations do not use that value.

`SetComplexityN` receives `N=n+m`. Each automatic fit contains only one fixed
density/family and graph seed. In the pinned version, `oAuto` selects its model
using CPU time, then fits manual time to the same model. Those builtin labels
are retained separately. The analysis instead fits exported manual durations
directly. [Version-specific fitting source](https://raw.githubusercontent.com/google/benchmark/v1.5.2/src/complexity.cc).

## Analysis and interpretation

The analyzer requires the complete seed/size/repetition matrices, validates
dimensions and correctness markers, rejects duplicates and error records,
and excludes JSON aggregate rows from sample means. Arithmetic means are
used for both work and timing. Range bands describe observed graph-seed
variation, not confidence intervals.

It exports adjacent effective exponents `log(y2/y1)/log(N2/N1)`, full-range
and upper-half log-log power fits, and zero-intercept fits to `N`, `N log N`,
`N log² N`, and `N²`. Model residuals and power exponents characterize only
the measured range. Neither the best residual nor an exponent near one proves
an asymptotic class. Time per work proxy compares arithmetic means at shared
sizes, not timings of the instrumented binary.

## Source-level bound and remaining assumptions

The KKT theorem is about expected linear work on a unit-cost RAM. Two Borůvka
contractions shrink the vertex count before the two recursive children;
sampling and heavy-edge filtering bound their expected combined size. The
implementation must also make each local phase linear in its current input.
[Karger, Klein, and Tarjan, Sections 3–4](https://www.cs.cmu.edu/~guyb/paralg/papers/KargerKleinTarjan95.pdf).

The audit found current-input scans in contraction and filtering, geometrically
shrinking full branching tree construction, and linear asymptotic LCA table
sizes. For this construction all original leaves have equal depth and every
internal node has at least two children. Height `h` therefore needs at least
`2^h` leaves, bounding the repaired median table's `2^(h+1)-1` loop iterations
by fewer than twice the leaf count. That property would not follow from
branching alone in an arbitrary unbalanced tree.

The path verifier's binary-search loop is not individually constant time.
Komlós bounds its aggregate comparisons on a full branching tree by
`3L + L log2((Q+L)/L)`, which is `O(L+Q)`. The code's per-node query-depth masks
and candidate filtering correspond to that amortization; treating every node
as paying the worst search depth would be too pessimistic.
[Komlós, Section 2, printed page 61](https://www.cs.princeton.edu/courses/archive/fall09/cos521/Handouts/linear.pdf).

This is a source-to-proof audit, not a formal proof of the complete C++ program.
It still assumes constant-time machine-word operations, suitable sampling,
and expected constant-time hash operations. The code uses finite integer IDs
and word masks; neither execution nor extrapolation extends to arbitrary
mathematical input sizes. Big-O upper bounds alone do not establish a practical
crossover on every family. An eventual advantage follows from appropriate
tight bounds and a common cost model, not merely two advertised upper bounds.

## Reproduction

Use the commands in the repository README. For the exact macOS environment,
the recorded Bazel invocation additionally selects the SDK and arm64 target:

```sh
task_sdk="$(xcrun --show-sdk-path)"
bazel test //:complexity_test //benchmark:complexity_benchmark //benchmark:work_sweep \
  -c opt --enable_bzlmod=false --cpu=darwin_arm64 \
  --repo_env=CC=/usr/bin/clang --repo_env=CXX=/usr/bin/clang++ \
  --copt=-O3 --copt=-arch --copt=arm64 --linkopt=-arch --linkopt=arm64 \
  --copt=-isysroot --copt="$task_sdk" --linkopt=-isysroot --linkopt="$task_sdk" \
  --linkopt="-L$task_sdk/usr/lib" --linkopt="-L$task_sdk/usr/lib/system"
./bazel-bin/benchmark/complexity_benchmark --benchmark_out=timing.json --benchmark_out_format=json
./bazel-bin/benchmark/work_sweep --large > work.csv
python3 benchmark/analyze_complexity.py --work-csv work.csv --timing-json timing.json --output-dir complexity-plots
```

Run the two binaries serially. Use `make work-sweep` and `bin/work_sweep`
when only logical counters are needed without the Google libraries.
