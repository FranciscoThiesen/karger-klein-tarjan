# Untimed fixture-generation hash repair

The continuation-only pair set previously inherited the shared builder's
identity integer hash. With power-of-two bucket counts, bucket selection can
use only the low endpoint bits of `(u << 32) | v`, creating long collision
chains. The new local builder mixes both endpoints before hashing. Its insertion
logic, acceptance decisions, RNG streams and graph outputs are unchanged. No
production MST algorithm or shared fixture generator was modified.

`before.hpp` is the exact header from commit `e1467be`; `after.hpp` is the
repaired header. `compare.cpp` includes both in separate namespaces and compares
every ordered edge tuple and every metadata vector, then records fingerprints.
The comparison passed **489 fixtures** spanning all seven families, three graph
seeds, sizes 32–4,096, densities 1/4/32 where feasible, and valid intrusion
settings 0/1/125/1000. See `comparison.log` and `fingerprints.csv`.

The separate generation-only diagnostic uses
`hierarchical_path_n65536_d64_p0`, seed 17: 4,194,304 edges. It also passed exact
tuple/metadata equality and produced fingerprint `11132971751564732402` for
both versions. `generation_times.csv` records 12.283067500 seconds before and
0.605206709 seconds after. These are **fixture setup durations**, not solver
timings. Generation and certification are outside the MST benchmark clock.

This diagnostic makes one old-then-new call, retaining the old returned graph
for comparison. It has no repetitions, order balancing or hardware counters;
it establishes a large setup bottleneck and checks the repair, not a controlled
solver speedup. Its `-O2` build is also separate from the production benchmark
profile. Neither result should be mixed into algorithm timing tables.

Run from the repository root:

```sh
kkt_hash_sdk=$(xcrun --show-sdk-path)
/usr/bin/clang++ -std=c++17 -O2 -Wall -Wextra \
  -isysroot "$kkt_hash_sdk" -I benchmark \
  benchmark/results/continuation-2026-10-12/fixture-hash-repair/compare.cpp \
  -L"$kkt_hash_sdk/usr/lib" -o /tmp/kkt_fixture_hash_compare
/tmp/kkt_fixture_hash_compare
/tmp/kkt_fixture_hash_compare --generation-only
```

The archived `build.log` is empty because compilation completed without
diagnostics. Both executions exited successfully; their standard error is
retained in `comparison.log` and `generation.log`.
