# Direct Edge-query verifier: implementation and correctness gates

This experiment removes only KKT's full `G_tuples` construction before each
positional verifier call. An internal `vector<Edge>` overload and the tuple
overload share a template implementation in `verifier_v2.cpp`. Field access uses
static overloads, with no layout casts or temporary tuple records. Forest
construction, forest component splitting, FBT reduction, random sampling,
filtering, edge order, isolation removal, and object lifetimes are unchanged.
The public tuple APIs retain their original signatures and behavior.

`KKT_EXPERIMENT_EDGE_VIEW` selects the direct path only in `kkt.cpp`; its absence
retains the tuple copy. Both variants use `KKT_EXPERIMENT_RETAIN_PARALLEL`.
The paired reference is the **newly refactored tuple implementation**, not an
identical copy of the frozen control binary. This study must use fresh paired
timings; previous timings cannot serve as its reference.

## Correctness results

All twelve instrumented test executions passed under native Apple Clang 15
and all twelve passed under native Homebrew Clang 22 with ASan, UBSan, and leak
detection enabled. Every executable was checked as arm64 with a 512 MiB main
stack before execution. The sanitizer environment was
`ASAN_OPTIONS=detect_leaks=1:abort_on_error=1` and
`UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`.

Each variant/profile passed:

- 1,248 direct positional path-walk oracle cases, checking both overloads and
  every verifier work counter. Cases include repeated IDs with different marks,
  parallel/reversed queries, strict equal-cost boundaries, negative and extreme
  costs/IDs, self-loops, disconnected forests, isolates, and empty inputs.
- 1,344 independently checked full-KKT records, covering 56 fixtures, three
  orders/ID layouts, and eight seeds. These include simple inputs creating
  parallel quotients, raw multigraphs, signed extreme weights, and disconnected,
  empty, and singleton graphs. The linked retained-parallel discriminator has
  four vertices and 96 edges after two root contractions.
- The unchanged multigraph suite: 770 quotient cases, 13,681 full KKT calls,
  117 exhaustive checks, 240 simple-input certificates, and four rejected
  deliberately invalid certificates.
- The unchanged regression, public contraction, simple, and attachment suites;
  the attachment suite includes 176 fixtures and 1,232 certified solver outputs.

For each profile, all 1,344 paired records have identical input fingerprints
and sorted MST IDs. All 65 work counters were compared: the only changes are

```
tuple.kkt_edge_visits - edge.kkt_edge_visits
  = tuple.edge_materializations - edge.edge_materializations
  = verifier_edges = sampling_edge_visits
```

There are 552 verifier-positive pairs; each changed counter saves 55,776 logical
operations in aggregate. All other 63 counters match exactly, including graph
volumes, recursion, sampling, filtering, and verifier work. A deliberately
tuple-linked candidate is rejected by the paired gate. Native and sanitizer
record files are byte-identical for each variant. No initialization-slot saving
is claimed: the removed `reserve` was not counted as initialized elements.

The two unchanged `retention_control_test.cpp` executions also passed when
linked against the final noninstrumented production objects. They exercise the
actual six-solver dispatch and independent certificates without timing calls.
Their commands, binary profiles, outputs, and hashes are recorded separately in
`final-object-harness-tests.json`.

## Reproduction and build binding

From the worktree root, with a fresh evidence output directory:

```sh
python3 -B benchmark/build_edge_verifier.py --profile native-correctness
python3 -B benchmark/build_edge_verifier.py --profile sanitizer-correctness
python3 -B benchmark/build_edge_verifier.py --profile timing-build
python3 -B benchmark/results/edge-view-2026-10-15/validation/validate_harness.py
```

The build script refuses to overwrite existing logs. Every compile, link, and
test invocation explicitly uses `/usr/bin/arch -arm64`; native flags are
`-std=c++17 -O3 -Wall -Wextra -march=native`, without `NDEBUG`. Work counters
appear only in correctness profiles. The sanitizer profile uses `-O1 -g`
and `-fsanitize=address,undefined -fno-omit-frame-pointer`.

The timing-build profile compiles seven shared production objects and the
unchanged `retention_control.cpp` harness object once. Both executables link
those same physical objects. Only `kkt.o` differs, with the direct variant adding
`-DKKT_EXPERIMENT_EDGE_VIEW`. Both use the same Apple Clang 15 compiler, SDK,
large stack, source inventory, and recipe inventory. Full compile/link commands,
source/object/binary hashes, and architecture/load commands are retained in
`timing-build-tuple-build-record.json` and `timing-build-edge-build-record.json`.

The timing executables have not been run by the implementation agent:

| Variant | Binary SHA-256 |
|---|---|
| Refactored tuple | `bd04b1c1813f1f5db67803d9d6213f28889c7bd781606239ab8daa0718aae141` |
| Direct Edge | `2e2e89b7e8465e563886deff0bf2a9e62d9f08aee27a60dfd433895e8eb3318f` |

Eliminating the copy removes one allocation and one full graph-record pass per
verifier invocation. It does not change asymptotic complexity, and these logical
counter savings do not establish a speedup or crossover. Native performance
remains gated by the root agent's prospective protocol, review, and freeze.

## Retained rejected attempt

The extra `../../edge-verifier-2026-10-15/validation/native-correctness-build.log`
is the first build attempt, before the artifact directory was standardized.
It accidentally included the unchanged timing-only harness test in the
instrumented suite. That source's explicit `#error` rejected work counters;
no tests or performance workloads ran from that attempt. The script now runs
the six counter-compatible suites and validates the harness separately against
the final noninstrumented objects. The rejection log is retained, not used as
successful evidence.
