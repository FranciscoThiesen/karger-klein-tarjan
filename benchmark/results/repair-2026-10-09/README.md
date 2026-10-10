# Repair measurements, 2026-10-09

On this Apple M3 Max, the final KKT implementation is **2.22–4.54x faster**
than the starting revision across these 13 cases (median of 27 matched timing
ratios per case). It still loses to Kruskal on sparse random graphs,
hierarchical paths, and the largest random graph at m/n = 32. This is a
constant-factor improvement on the measured workloads, not evidence that KKT
is universally faster or a timing-based proof of linear complexity.

## Revisions and environment

| CSV | Algorithm source revision | Change |
| --- | --- | --- |
| `original.csv` | `693c6a5f0945982ef3460e27632687e55cfb8de9` | Starting implementation |
| `core_repairs.csv` | `ca0bb2bdb6496039bdef38fd0f3369a73f3b3ea5` | Subproblem-local edge tracking, linear median table, continuing RNG stream, test/build repairs |
| `contraction.csv` | `e45e86188377d6f11d141499038cab8ec79a6e45` | Flat contraction storage and stamped parallel-edge buckets |
| `verifier.csv` | `a3a439533f970a3cd7f1b17ddbe0e99c7f5e4648` | Dense verifier arrays, fewer copies, direct tree construction |

All phases use `benchmark/scaling_benchmark.cpp` from `ca0bb2b`.
Its SHA-256 is `8e653cf585341be3ca421a21da4d369c0882d2d14143515321a6e716a38d20e6`.
The later Bazel dependency repair does not alter algorithm or benchmark code.

- CPU/architecture: Apple M3 Max, native arm64.
- OS: macOS 26.6.2, build 25G83.
- Compiler: `/usr/bin/clang++`, Apple clang 15.0.0 (`clang-1500.3.9.4`).
- Language/optimization: `-std=c++17 -O3 -march=native`.
- SDK: `/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk`, passed with `-isysroot` and `-L<SDK>/usr/lib`.
- Measurement command: `./bin/scaling_benchmark --scale > <phase>.csv`.
- Process order: original, core repairs, contraction, verifier. No concurrent
  builds or other agent benchmarks were running during these measurements.
  This was an ordinary desktop session, without CPU pinning or power control.

For the original revision, sources were extracted with `git archive` to a
separate directory and compiled with the common harness and the same compiler,
optimization, and SDK flags. Its include path and KKT, verifier_v2, LCA,
Kruskal, and union-find sources came from that extraction. Subsequent phases
used `make -j4 scaling-benchmark` at their listed revisions.

## Workloads and timing boundary

Each case uses graph seeds 17, 42, 999; KKT seeds 0, 1, 7; one warmup of each
algorithm per seed pair; and three measured repetitions. There are 27 timings
per algorithm per case, 702 observations per phase, and 2,808 raw observations
in total. All results passed exact edge-ID comparison with Kruskal on
unique-weight graphs. Execution order alternates between algorithms.

The random graphs are simple and connected, beginning with a random spanning
tree and then adding missing edges. Weights are shuffled unique integers.
Hierarchical paths use edge (i-1, i) with weight n*v2(i)+i, where v2 counts
factors of two. They force repeated pair contractions; input edge order is
shuffled by graph seed. The duplicated random cases in vertex and density
series are separate measurements and are retained.

Timing includes the public algorithm call and construction of its return
value. Input construction, validation, and return-value destruction are
excluded. KKT returns an ID hash set and Kruskal returns an edge vector, so
these are public-API comparisons, not equalized output representations.

## Results

Times below are medians in milliseconds. Speedup is the median of matched
original/final KKT ratios, which can differ from the ratio of the displayed
medians. The complete `summary.csv` also includes every intermediate phase,
paired ratios, slower-pair counts, and Kruskal controls.

| Series / family | n | m | Original KKT ms | Final KKT ms | Final Kruskal ms | Paired KKT speedup |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dense case / random | 1,000 | 400,000 | 16.518 | 5.073 | 21.436 | 3.28x |
| density growth / random | 4,096 | 16,384 | 3.376 | 1.349 | 0.702 | 2.48x |
| density growth / random | 4,096 | 131,072 | 17.583 | 5.184 | 6.560 | 3.32x |
| density growth / random | 4,096 | 524,288 | 62.662 | 13.985 | 28.677 | 4.54x |
| vertex growth / hierarchical path | 1,024 | 1,023 | 0.519 | 0.197 | 0.013 | 2.64x |
| vertex growth / hierarchical path | 4,096 | 4,095 | 2.088 | 0.730 | 0.091 | 2.84x |
| vertex growth / hierarchical path | 16,384 | 16,383 | 8.602 | 3.190 | 0.652 | 2.69x |
| vertex growth / random | 1,024 | 4,096 | 0.625 | 0.229 | 0.107 | 2.75x |
| vertex growth / random | 1,024 | 32,768 | 2.584 | 0.744 | 1.418 | 3.57x |
| vertex growth / random | 4,096 | 16,384 | 3.361 | 1.403 | 0.717 | 2.37x |
| vertex growth / random | 4,096 | 131,072 | 17.111 | 5.224 | 6.590 | 3.29x |
| vertex growth / random | 16,384 | 65,536 | 17.101 | 7.719 | 3.221 | 2.22x |
| vertex growth / random | 16,384 | 524,288 | 131.357 | 42.335 | 28.888 | 3.12x |

The verifier-only change improves hierarchical-path paired medians by
1.77–1.97x. It takes about 0.2% longer on the density-series (4096, 524288)
case and 2.0% longer on the vertex-series (1024, 32768) case by paired medians;
both losses remain in the summary. The final path cases remain about
4.9–15.4x slower than Kruskal by ratio of medians. A practical crossover depends on graph shape,
density, size, and machine; no hybrid cutoff was introduced.

Kruskal is unchanged across phases, but its paired control ratios range
0.989–1.211x for original/final, 0.774–1.033x for core/contraction, and
0.976–1.207x for contraction/verifier. The small cases are particularly noisy.
Matched seeds align workloads, not machine state. Three repetitions per
seed pair do not establish confidence intervals, and no adjustment by the
control timings has been applied. All observations, including individual
losses, remain in the CSVs.

## Reproduce the summary and validation

From the repository root:

```sh
python3 benchmark/results/repair-2026-10-09/summarize.py --require-all \
  --output benchmark/results/repair-2026-10-09/summary.csv
make -j4 test
```

The summary script rejects missing, duplicate, failed, or unmatched samples.
It checks the full seed/repetition matrix and reports control drift and losses.

The final code passed all 8 lightweight tests and 12 regression groups,
including exact Kruskal comparisons across arbitrary IDs and input orders,
4,194,302 exhaustive median-table entries, direct-path heavy-edge checks,
RNG-state checks, empty forests, and LCA input lifetimes. All four legacy
GoogleTest suites also passed as native builds. UBSan passed all regression
groups with `-O1 -g -fsanitize=undefined -fno-sanitize-recover=all`.
AddressSanitizer could not initialize on this machine (runtime assertion
before main); it is not counted as a successful check.

After the separate GoogleTest platform-label repair, all five Bazel test
targets passed with Bazel 7.3.1 in optimized mode. The installed Bazel runs
under Rosetta, so native testing on this particular machine used:

```sh
task_sdk="$(xcrun --show-sdk-path)"
bazel test //:all -c opt --enable_bzlmod=false --cpu=darwin_arm64 \
  --repo_env=CC=/usr/bin/clang --repo_env=CXX=/usr/bin/clang++ \
  --copt=-arch --copt=arm64 --linkopt=-arch --linkopt=arm64 \
  --copt=-isysroot --copt="$task_sdk" \
  --linkopt=-isysroot --linkopt="$task_sdk" \
  --linkopt="-L$task_sdk/usr/lib" --linkopt="-L$task_sdk/usr/lib/system" \
  --test_output=errors
```

The complexity repairs are structural: recursive edge bookkeeping is sized
to each subproblem, and the verifier median table performs constant work per
entry. Contraction deduplication now uses deterministic O(n+m) bucket scans.
The whole KKT implementation still assumes expected constant-time hash-set
operations and the randomized sampling model. Finite timing data does not
establish those assumptions or replace the algorithm's analysis.
