# Deferred build shape — not executed

Source preparation only. The Google Benchmark source/library paths below are unresolved placeholders, and there is no current validated library artifact. This is a reviewable command specification, not a runnable build receipt.

Working directory: `/Users/random_person/Desktop/kkt-eighth-sampling`.

Parent record: `benchmark/results/eighth-sampling-2026-10-15/validation/timing-build-eighth-build-record.json`.

Parent freeze: `benchmark/results/eighth-sampling-2026-10-15/freeze.json`, expected SHA-256 `2be7556d15b58f3f65cc380ac22b67c57fdf8aea747d651b9d648c6a1aa59d2f` (confirm exact stored path and full proof after release).

Compile the new main once with this argv shape:

```text
/usr/bin/arch -arm64 /usr/bin/clang++
-isysroot /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk
-std=c++17 -O3 -Wall -Wextra -march=native
-DKKT_EXPERIMENT_RETAIN_PARALLEL -DKKT_EXPERIMENT_EDGE_VIEW
-I/Users/random_person/Desktop/kkt-eighth-sampling
-I<verified-google-benchmark-v1.5.2>/include
-c <installed-new-main-path>/current_complexity.cpp
-o <fresh-build-dir>/current_complexity.o
```

The new main does not compile KKT or verifier implementation and therefore must not claim that adding a policy macro to it proves linked dispatch. The eighth KKT and compressed verifier policies are inherited from the exact frozen production objects and their completed correctness/readiness proof.

Link with the same compiler/SDK/profile, the new main, and the eight **actual physical paths** in `object_paths` (all seven `shared` objects and `eighth/kkt/kkt.o`). Exclude the old `retention_control.o` main. Add the newly validated static `libbenchmark.a`, its documented platform link dependencies, the SDK's `usr/lib` path, and `-Wl,-stack_size,0x20000000`. Obtain link dependencies from the verified version's build; do not guess that a previously installed Homebrew library is equivalent. The actual final command and environment must be archived before freeze.

Use `LIBRARY_PATH`/`CPATH` removal only if the recorded isolated build environment requires it, recording the old values and exact policy as the prior frontend repair did. Do not silently normalize unrelated environment variables or alter frozen object paths. Preserve failed attempts separately.

Future invocation shape (declared seeds, exclusive output directory still unset):

```text
<new-native-binary> leaf_hierarchy4 kkt 19000013 3001 ascending <exclusive-attempt>/raw.csv <exclusive-attempt>/google.json
```

The driver accepts only its seven positional arguments; it internally fixes Google Benchmark's JSON format and registration, with no filtering/list-only or repetition overrides. The future outer collector must check all 24 literal commands, 11 sizes × 3 callbacks × (1 warmup + 2 timed calls) per child, all markers, full JSON/raw equivalence and owned-group exit. It must preserve the parent proof and final source/library/objects/binary hashes before and after capture.

The collector, analyzer, read-only `validate_build.py` and `build_library_main.py` producer are now source-prepared, unexecuted, in this package. `BUILD_GATE_PLAN.md` records the exact acquisition/build and two actual-final-binary schema curves. Independent review/mocks, real library acquisition/build/smoke and an archival outer phase wrapper remain release work. The collector explicitly refuses preflight without real bound build/smoke evidence and the producer recipe; see `COLLECTOR_ANALYSIS_CONTRACT.md`. No smoke-test binary, build success or benchmark library is fabricated by this preparation.
