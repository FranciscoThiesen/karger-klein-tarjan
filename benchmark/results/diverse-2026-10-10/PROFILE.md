# Follow-up diagnosis of the largest random case

These diagnostics ran **after** the primary measurements. They do not contribute
timing samples to the comparison plots, and algorithm code remained unchanged.

## Contraction effectiveness changes with graph size

The exact fixture generator and graph seed 17 produce these sizes after KKT's
first two Borůvka contraction steps:

| Profile | Initial n | Initial m | Remaining n | Remaining m | Edges retained |
| --- | ---: | ---: | ---: | ---: | ---: |
| Random m=32n | 1,024 | 32,768 | 56 | 1,535 | 4.7% |
| Random m=32n | 16,384 | 524,288 | 829 | 199,699 | 38.1% |
| Random m=32n | 65,536 | 2,097,152 | 3,376 | 1,458,796 | 69.6% |
| Dense random anchor | 1,000 | 400,000 | 51 | 1,275 | 0.3% |

Four times as many input edges from the 16K to 65K random case leaves **7.3 times
as many edges** after two contractions. Small dense instances benefit much more
from deleting parallel edges. This increases the work passed to recursive
sampling and verification in the larger instances; it helps explain why the
small-instance win against Kruskal does not persist. It is one contribution,
not a complete decomposition of the measured runtime growth.

The raw two-round counts are in [contraction_sizes.csv](contraction_sizes.csv).
They describe one graph seed and no wall-clock timing.

## Where the large case spends samples

A KKT-only driver reuses `random_32_n65536`, graph seed 17, and cycles sampling
seeds 0, 1, 7. `/usr/bin/sample` captured 3,824 main-thread samples over one
five-second window at a nominal one-millisecond interval.

| Inclusive group | Samples | Approximate share |
| --- | ---: | ---: |
| MST verifier | 1,915 | 50.1% |
| Borůvka contraction inside KKT | 1,138 | 29.8% |

Within those groups, path-maxima `init` and `visit` account for **23.4% of leaf
samples**, and hash insertion plus rehash account for **21.4%**. Caller stacks
place most of those hash operations in construction of the heavy-edge result
set. The inclusive and leaf percentages overlap and must not be added together.

This supports prioritizing the verifier's per-query traversal and heavy-edge
result representation, followed by contraction, in further optimization work.
One experiment would replace the internal hash-set exchange with edge positions
local to each subproblem while preserving the public API and its arbitrary-ID
support. Returning to a bitmap indexed by global edge IDs would reintroduce the
complexity problem repaired earlier. No such optimization is included here.

The raw [sampling profile](kkt_random32_n65536.sample.txt) and
[profile metadata](profile_metadata.json) preserve the evidence. This is one
fixture/window with optimized symbols and no line-level debug information.
The profile driver also destroys returned results; primary timing excludes
that destruction. Sample shares are approximate and are not exact wall-clock
phase percentages. No hardware cache-miss or bandwidth counters were recorded,
so a cache-based explanation would remain unverified.

## Reproduction

The diagnostic drivers include the benchmark translation unit to reuse its
exact fixture generator. From the repository root on macOS:

```sh
make -j4 diverse-benchmark
task_sdk="$(xcrun --show-sdk-path)"
/usr/bin/clang++ -std=c++17 -O3 -march=native -I. \
  -isysroot "$task_sdk" -L"$task_sdk/usr/lib" \
  benchmark/results/diverse-2026-10-10/contraction_sizes.cpp \
  .build/*/*.o -o /tmp/kkt-contraction-sizes
/tmp/kkt-contraction-sizes

/usr/bin/clang++ -std=c++17 -O3 -march=native -I. \
  -isysroot "$task_sdk" -L"$task_sdk/usr/lib" \
  benchmark/results/diverse-2026-10-10/profile_driver.cpp \
  .build/*/*.o -o /tmp/kkt-profile
/tmp/kkt-profile
```

Once the second program prints `READY pid=...`, run in another terminal:

```sh
/usr/bin/sample PID 5 1 -file profile.txt
```

The driver runs for approximately 20 seconds, then prints a checksum. Its loop
is solely for sampling; correctness was established separately by the main
certified benchmark.
