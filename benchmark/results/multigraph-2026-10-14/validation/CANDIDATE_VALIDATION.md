# Candidate implementation and correctness gates

These are correctness checks, not performance measurements. The only production
dispatch change is at KKT's two internal contraction calls, guarded by
`KKT_EXPERIMENT_RETAIN_PARALLEL`. The opt-in helper lives in
`kkt/experimental_multigraph_contraction.hpp`. The default build and the public
`boruvka_step` retain their previous behavior. A source extraction verifies the
entire public step is byte-identical to `HEAD`.

The helper retains every crossing edge, including all parallel records, with
original costs and IDs. It removes loops created by contraction, renumbers
nonisolated quotient components in the same component order, canonicalizes
endpoints, and emits records in original input order. It counts crossing edges
during its degree pass and reserves that exact count. Consequently output order,
sampling draws assigned to edges, and recursive subproblems can differ from the
reference. It is not an isolated allocation-only ablation.

## Passing gates

The final new test passed with native Apple Clang 15 at `-O3`, and independently
with native Homebrew Clang 22.1.8 at `-O1` under AddressSanitizer,
UndefinedBehaviorSanitizer, and leak detection:

- **770 quotient cases** against a separate per-vertex scan/relabel-union oracle.
  This compares exact selected IDs/order, every retained quotient record/order,
  endpoint compaction, legacy metadata, and input preservation.
- **13,681 full KKT calls**, using 16 sampling seeds and ordered, reversed, and
  shuffled input; dense parallel inputs, simple inputs creating parallel
  quotients, disconnected components, isolates, empty/singleton graphs,
  signed/sparse/extreme IDs, zero/oversized legacy metadata, and signed weights
  including `INT_MIN` and `INT_MAX`.
- Every result matches a separate sorted/relabel minimum-forest oracle and
  passes a multigraph-aware explicit-tree-walk cycle certificate. **117 tiny
  cases** additionally use exhaustive subset enumeration. **240 simple-input
  results** pass the existing production benchmark certificate unchanged.
- Four deliberately invalid forests are rejected by the new certificate.
  A separate intentionally wrong-linked binary, with the test macro enabled
  but default KKT implementation, is rejected by the linked-dispatch assertion.
- Instrumented helper calls require at most **3m edge visits**, **4n initialized
  scratch slots**, **2n successor arcs**, and exact output/materialization
  counters. A full-KKT complete-graph fixture requires four root quotient
  vertices and **96 retained edges after two rounds**, where the default simple
  quotient has six; it also requires actual verifier invocation.

Existing gates also passed in both native optimized and native sanitizer builds:
the eight simple tests, fifteen regression groups, the unchanged **214-case
public simple-quotient oracle**, and all attachment validation checks. The latter
cover 176 fixtures, 1,197 independent contraction stages, 1,060 sorted/slow minimum
crosschecks, 1,232 certified solver outputs, 66 endpoint-twin trajectories, 24
all-field counter pairs, 13 distance-core chord cases, 20 rejected dimensions,
and 32 allocation-free maximum-edge checks. The independent production
certificate positive/negative suite additionally passed in the optimized build.

The new untimed work harness compiled against the instrumented candidate and
passed the three requested small fixtures: `leaf_hierarchy4/512/16`,
`lifted_hierarchy4/256/16`, and `gnm_random/64/16`, all with graph seed 2000003 and
KKT seed 607. These smoke observations are not timing evidence.

`candidate-native-linked-signed.json` binds the final optimized new-test binary;
`candidate-clang22-sanitizer-tests.json` records all five final sanitizer suites.
Earlier optimized logs precede the linked-dispatch/signed-weight additions and
are retained separately. `native-correctness-profiles.json` verifies all ten
final correctness binaries are arm64 and records the public-step source hash.

## Build records and retained setup failures

The reference and candidate timing binaries use the same final source inventory,
Apple Clang 15, `-std=c++17 -O3 -Wall -Wextra -march=native`, and a 512 MiB main
stack. Assertions remain enabled; work counters and sanitizers are absent.
The candidate alone adds `-DKKT_EXPERIMENT_RETAIN_PARALLEL`. Exact commands,
compiler/SDK identity, logs, source/Makefile/object/binary hashes, and Mach-O
profiles are in `reference-build-record.json` and `multigraph-build-record.json`.
All **seven non-KKT object files are byte-identical** across these builds;
`native-object-comparison.json` records that check. This does not claim identical
linked addresses or hardware placement.

The first Python-driven Apple compiler invocation inherited a translated
x86_64 process personality. Its timing binary failed the arm64 profile gate
before execution. The corresponding Apple sanitizer binaries were also x86_64:
the first reported unsupported leak detection, and disabling leak detection
produced SIGILL during sanitizer startup, before tests ran. These failed logs
are retained; they do not establish a problem in the candidate or in native
Apple sanitizer support. Corrected timing builds explicitly use
`/usr/bin/arch -arm64 /usr/bin/make -B`; the successful sanitizer builds use the
native Homebrew Clang 22 toolchain. No rejected binary supplies performance data.

No native performance run was launched by the implementation agent. Root owns
the final freeze, commit, and timing release.
