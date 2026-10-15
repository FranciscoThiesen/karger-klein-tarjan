# Packed sampling A: implementation and correctness

This is an opt-in experiment, not a promoted default or a performance result.
`KKT_EXPERIMENT_PACKED_SAMPLING` changes only private recursive samples. Each
nonempty block of at most 32 edges consumes one MT19937 output word, tests its
bits from least to most significant, and emits selected records in input order.
The last block discards unused bits. Calls share the existing recursive engine;
there is no residual-bit cache. A sample of `m` records therefore draws
`m / 32 + (m % 32 != 0)` words instead of `m` words.

Public `random_sampling` retains the exact one-draw-per-edge stream, original
IDs, metadata, and vertex compaction. The default private path is also scalar.
Both variants keep `reserve(m/2)`, retained-parallel contraction and direct
Edge verifier queries. This experiment does not change lifetimes, filtering,
query storage, the engine, fixture generation, or comparator code.

Uniform independent 32-bit words would provide independent half-selection
bits. This is a statement about that ideal sampling model, not a claim that
the deterministic MT19937 stream has literal independence. Candidate seeds
produce different samples and recursive work. The correctness contract remains
loop-free valid MSF inputs with distinct weights; sampler and verifier tests
also exercise their separate endpoint/ID/weight contracts.

The callback refactor is present in the freshly built scalar reference too.
Historical binaries and their timings are not reused. Seven non-KKT production
objects, including the verifier, and the six-solver main object are physically
shared. Only packed `kkt.o` receives the extra macro.

## Completed correctness gates

Apple Clang 15 native and Clang 22 ASan+UBSan builds each passed all eight
standalone suites for both variants. Sanitizers use
`ASAN_OPTIONS=detect_leaks=1:abort_on_error=1` and
`UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`.

| Gate | Evidence per variant and compiler profile |
|---|---|
| Packed helper | Four groups: scripted masks, exhaustive eight-bit subsets, exact MT state/replay, interleaved sources |
| Actual private function | 54 private/public calls; 12 distinct masks on inputs larger than 32 edges; consecutive partial blocks, empty calls, sparse extreme IDs, compaction, metadata, input preservation and exact engine state |
| Independent verifier and MSF oracle | 1,248 positional cases and 1,344 full KKT cases |
| Multigraph contraction/MSF | 770 quotient cases, 13,681 solver calls, 117 exhaustive cases, 240 simple-input certificates, four certificate rejection cases |
| Existing regression/contraction/simple | Public-stream regressions plus unchanged public contraction and small MST suites |
| Attachment fixtures | 176 fixtures and 1,232 certified solver outputs |

All 1,344 scalar/packed paired inputs and sorted MST ID sets match exactly.
Recursive counters differ in 539 pairs, as allowed. The 65-field schema and
nonnegative values are checked; all fixture/order/seed identities must occur
in their exact expected sequence. Substituting scalar records for the packed
records is rejected. Giving either private integration executable the wrong
runtime sampling policy is also rejected. The direct integration TU includes
the actual `kkt.cpp` and links the seven other objects, avoiding a production
test hook; the full-solver paired gate checks separately linked KKT objects.

Both final, uninstrumented timing object sets also passed the unchanged
`retention_control_test.cpp` correctness suite. **Neither timing executable
was executed.** The compiler, SDK, complete commands, source/recipe/object and
binary hashes, Mach-O arm64 profile, and 512 MiB stack are retained in the
build receipts. Each serial build/test child has a 300-second deadline,
40 GiB sampled owned-group RSS cap, bounded monitoring, and confirmed-empty
cleanup before the next child.

The unchanged supplementary retention-control work driver is linked separately
against the two instrumented object sets. Its small smoke gates are recorded in
`../work/build-record.json`; no large work matrix is run here. That driver emits
all 65 KKT fields, fixture fingerprints, and exact equality with an independently
certified unique MST. Its counter scope includes tuple-to-Edge construction and
the solver; certification and comparator round replay are outside the scope.

## Captured commands

These are the exact captured commands, run serially from the worktree root.
They refuse to overwrite existing evidence. A reproduction should use a fresh
checkout/build directory, or a fresh `--output` path for the main builder;
the two supplementary scripts intentionally bind this study's receipts.

```sh
python3 -B benchmark/build_packed_sampling.py --profile native-correctness
python3 -B benchmark/build_packed_sampling.py --profile sanitizer-correctness
python3 -B benchmark/build_packed_sampling.py --profile timing-build
python3 -B benchmark/results/packed-sampling-2026-10-15/validation/validate_harness.py
python3 -B benchmark/results/packed-sampling-2026-10-15/validation/build_work.py
```

All native compiler/link/test commands explicitly use `/usr/bin/arch -arm64`.
The source review by `multigraph_design` found no blocker. These gates establish
correctness and build isolation on the recorded cases; any speedup or crossover
requires the separately frozen, multi-seed performance study.
