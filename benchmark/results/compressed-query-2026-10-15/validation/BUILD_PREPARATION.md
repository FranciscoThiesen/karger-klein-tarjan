# Compressed-query build preparation — unexecuted

Prepared while the packed-sampling native capture is active. These files have
not been imported, syntax-checked, tested, compiled or executed. No checkout,
patch application or frozen-worktree edit was made. This is a prospective build
recipe, not a correctness or performance result.

## Installation after explicit release

Root owns the future isolated worktree, proposed location
`/Users/random_person/Desktop/kkt-compressed-queries`, based on Edge commit
`30728a3dedb9f6fc9b52289053e05d78a47ceffd`. It must retain the original scalar
sampler; do not base it on the packed implementation or combine reserve changes.
The original Edge freeze is
`/Users/random_person/Desktop/kkt-edge-verifier-view/benchmark/results/edge-view-2026-10-15/freeze.json`,
SHA256 `f976a7d61650f5aaf8e7221c7684461e36bcb51492347f45a56497b6b1cee306`.

After source review and authorization, install the three prepared C++ files
according to `/tmp/kkt-compressed-query-prep/README.md`. Install this directory's
`build_compressed_queries.py` at `benchmark/build_compressed_queries.py` and
`validate_final_objects.py` in the new study's `validation/` directory.
No helper or native source in a historical frozen worktree is changed.

The builder requires exactly the original native inventory plus
`verifier/experimental_compressed_queries.hpp` and
`test/compressed_query_test.cpp`. Only `verifier/verifier_v2.cpp` may differ.
It removes precisely the new conditional include and candidate dispatch text
in memory, then compares the entire remaining translation-unit text with the
original frozen verifier. The default reference function must be textually
unchanged. It checks base ancestry and the original scalar `kkt.cpp` hash.

## Build profiles and evidence

Use three separate profiles, preserving every failed attempt. Suggested future
invocations from the new worktree (do not execute during active timing):

```sh
python3 -B benchmark/build_compressed_queries.py --profile native-correctness --output benchmark/results/compressed-query-2026-10-15/validation --parent-freeze /Users/random_person/Desktop/kkt-edge-verifier-view/benchmark/results/edge-view-2026-10-15/freeze.json
python3 -B benchmark/build_compressed_queries.py --profile sanitizer-correctness --output benchmark/results/compressed-query-2026-10-15/validation --parent-freeze /Users/random_person/Desktop/kkt-edge-verifier-view/benchmark/results/edge-view-2026-10-15/freeze.json
python3 -B benchmark/build_compressed_queries.py --profile timing-build --output benchmark/results/compressed-query-2026-10-15/validation --parent-freeze /Users/random_person/Desktop/kkt-edge-verifier-view/benchmark/results/edge-view-2026-10-15/freeze.json
python3 -B benchmark/results/compressed-query-2026-10-15/validation/validate_final_objects.py --root /Users/random_person/Desktop/kkt-compressed-queries --validation benchmark/results/compressed-query-2026-10-15/validation
```

The native profiles explicitly use `/usr/bin/arch -arm64 /usr/bin/clang++`,
Apple Clang 15, the identical frozen-parent compiler identity and SDK, C++17,
O3, assertions, `-march=native`, retained-parallel contraction and Edge input.
Sanitizer correctness explicitly uses native Clang 22 at O1 with debug symbols,
ASan+UBSan, frame pointers, `ASAN_OPTIONS=detect_leaks=1:abort_on_error=1` and
`UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`. It therefore enables LSan's
leak check through ASan; no successful leak result is claimed before execution.
Correctness profiles add `KKT_ENABLE_WORK_STATS`. Timing objects do not.
Neither profile adds NDEBUG or the packed-sampling macro.

Both variants share seven physical production objects, including `kkt.o`.
Only `verifier_v2.o` is compiled twice; the compressed compile alone adds
`KKT_EXPERIMENT_COMPRESSED_QUERIES`. Test/harness main objects are shared too.
Every binary is checked as native arm64 with a 512 MiB main stack. Timing-build
has exactly twelve commands: seven shared compiles, two verifier compiles, one
shared six-solver harness compile, and two links. It executes neither binary.

Records are `PROFILE-{reference,compressed}-build-record.json`, schema
`compressed_query_build_v1`, with exact argv, source and recipe inventories,
compiler/SDK, parent freeze, original reference-text/scalar-policy gates,
object paths/hashes, executable/main-object/link proofs and logs. Timing
records expose the sole harness executable's fields at top level, matching the
paired collector's earlier pattern. Build/object directories are profile
specific and must not already exist; rejected evidence is not overwritten.

All compiler, linker and correctness processes run in owned groups under the
unchanged bounded monitor: 40 GiB sampled group RSS, two-second polling,
three consecutive unavailable observations, immediate sampler-poison stop,
300-second per-command deadline, bounded termination, and verified group exit
before any later launch. SIGTERM raises into cleanup; a second SIGTERM is
ignored only while bounded cleanup/evidence writing finishes. The previous
handler is restored. SIGINT already raises KeyboardInterrupt into the same
finally path. Monitor/cleanup evidence is retained for failed commands.

## Correctness gates

Each native/sanitizer profile builds eight common test mains and links/runs
all eight against both verifier variants: the new compressed test, the existing
direct-Edge verifier oracle/full KKT record test, multigraph contraction,
regression, contraction, simple, core attachment and independent MST certificate.
The focused test receives `reference` or `compressed` as a runtime expectation.
It must report exactly 252 positional cases and seven assertion-rejected malformed
lookups, plus its actual linked-policy discriminator. Counts remain proposed
until verified by compilation/execution.

Both focused binaries then receive the wrong policy. Require exit 1 with the
specific wrong-linked-query-representation diagnostic; a sanitizer error is not
an accepted negative. The focused star witness derives Q=24 and U=4 and requires
96 reference or 52 compressed path-query visits. It also covers all-loop Q=U=0.
The direct verifier oracle continues checking both tuple and Edge overloads
within each variant; its within-variant work equality remains mandatory.

Each profile emits 1,344 full-KKT records per variant over 56 fixtures, three
orders and eight seeds. Require matching input fingerprints and sorted unique
MST IDs, the exact field/member-bound 65-counter registry, and exact equality of
61 fields. The four differences must satisfy all of the following on every
record, including zero-work cases:

- Q = `verifier_queries`, M = `verifier_tree_edges`, T = `verifier_tree_calls`,
  Nsum = `fbt_output_vertices`; these fields are among the 61 invariants.
- U = candidate `path_query_visits` − 2Q, with 0 ≤ U ≤ Q.
- Reference `path_query_visits` = 4Q.
- Reference minus candidate `initialized_slots` = M + Q − U + T.
- Reference minus candidate `verifier_edge_visits` = M.
- Candidate minus reference `verifier_vertex_visits` = Nsum.

Require at least one positive Q witness with reduced path-query visits. Feeding
the reference record stream into both sides must be rejected. The report records
all derived cumulative U values. It does not silently redefine `verifier_queries`,
add an observer or require a per-call trace. Equality of intermediate sample/forest
values is not directly observed: report exact input/result/counter gates and the
source-level determinism argument separately.

After timing-build, `validate_final_objects.py` compiles the unchanged
`retention_control_test.cpp` once without counters and links/runs it with each
actual final eight-object set. It rechecks records, source and object hashes
before and after and preserves its own command, binary, stdout/stderr and group
proof. Timing executables remain unexecuted. This validates the final linked
objects' correctness without adding instrumentation to measured binaries.

## Untimed work driver

The native-correctness profile also compiles the unchanged supplementary driver
at `benchmark/results/retention-control-2026-10-15/work/driver.cpp` once and links
it to both instrumented object sets. Its original source SHA256 must be
`ae08c5d199d83668d81f41a573452fea099c7e7cd5bd9bb4807c4a8ba9120e25`.
It is recorded as `untimed_work_never_executed`; the builder never launches it.
This establishes same-source work and timing profiles without rebuilding a
different production implementation later. A separately authorized bounded
collector can use those work binaries after timings, deriving cumulative U from
the existing counters. No per-call observer is required for this experiment.

## Review status and pending work

This preparation remains source-only. Root requested SIGTERM cleanup routing
and a field/member-bound registry regex; both are included. A later independent
source review, syntax/mock lifecycle checks, actual patch application, focused
compilation, all native/sanitizer suites and final-object gates remain required.
A failed hypothesis, compilation, assertion, sanitizer or accounting identity
must be retained and investigated; do not weaken a gate or adjust measured
boundaries to manufacture a favorable result. No speedup, memory reduction,
practical crossover or production promotion follows from prepared source.
