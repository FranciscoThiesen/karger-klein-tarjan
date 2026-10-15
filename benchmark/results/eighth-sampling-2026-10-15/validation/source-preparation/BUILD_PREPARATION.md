# Deferred eighth-sampling build and validation

Status: source-only, unimported and unexecuted, 2026-10-15. No syntax check,
mock test, compiler, sanitizer or native solver has run for this package.
Root must release a separate quiet phase and create an isolated worktree,
proposed `/Users/random_person/Desktop/kkt-eighth-sampling`, based on the
original compressed implementation. Active performance takes precedence.

## Install and mock before compiling

After authorization, validate the full compressed parent proof and the exact
one-existing-file/three-new-native-files overlay. Copy the reviewed overlay
to the isolated worktree without touching the original frozen parent helpers,
native source, receipts, objects or binaries. Pin prospective source/protocol
bytes before any performance. The native overlay hashes are fixed in the
builder and collector; they have not changed since the native source review.

Run the seven builder mock groups, preserving exclusive attempt logs and
before/after source hashes, through the established bounded owned-group
controller. No mock is supposed to launch a native solver:

```
python3 -B -m unittest discover -s benchmark -p test_eighth_build.py -v
```

The separate collector mock command is declared in the collector's protocol.
These tests are not a substitute for actual native gates. The builder mocks
check all 1,344 record identities, strict integer/schema domains, cross-rate
MSF/root agreement and changed-work witness, exact 65-field half replay,
original-parent helper restoration, the independently spelled twelve-command
timing recipe, focused native output counts, source allowlist, and final
receipt/shared-artifact/predicate-policy negatives.

## Native profiles, sequentially

From the future isolated worktree, archive each invocation separately:

```
python3 -B benchmark/build_eighth_sampling.py --profile native-correctness --output benchmark/results/eighth-sampling-2026-10-15/validation
python3 -B benchmark/build_eighth_sampling.py --profile sanitizer-correctness --output benchmark/results/eighth-sampling-2026-10-15/validation
python3 -B benchmark/build_eighth_sampling.py --profile timing-build --output benchmark/results/eighth-sampling-2026-10-15/validation
python3 -B benchmark/results/eighth-sampling-2026-10-15/validation/validate_final_objects.py --output benchmark/results/eighth-sampling-2026-10-15/validation
```

Run a later command only after the earlier gate passes and every owned group
is known empty. Retain all rejected logs, objects and receipts; investigate
before applying a reviewed repair and a separately recorded next attempt.
Use the established bounded outer controller as well as the inherited inner
`SerialGuard`: 40 GiB sampled group RSS, two-second checks, three unavailable
observations, poison stop, 300-second build/test child deadline, SIGTERM
through `finally`, and bounded cleanup with explicit exit proof. Unknown exit
forbids advancement. No performance or work driver is executed by any profile.

Native correctness uses AppleClang 15, C++17/O3, assertions enabled, explicit
`/usr/bin/arch -arm64`, the same parent SDK and a 512 MiB main stack. Sanitizer
correctness uses native Clang 22, C++17/O1/debug, ASan/UBSan and
`ASAN_OPTIONS=detect_leaks=1:abort_on_error=1`,
`UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`. Objects are separate from
each other and from final uninstrumented timing objects. SDK/profile and
actual native file/load-command proofs are recorded.

Each correctness profile defines **20 positive executable runs** (ten per
variant) and **four wrong-policy negatives** (two sampling, two compressed
verifier). Existing eight suites are unchanged; two focused sampler tests
are added. The predicate suite must print exactly three groups. The private
integration test must report 132 cases, each replayed, a positive half/eighth
witness and its requested linked policy. Every actual public/private call
also checks existing instrumentation when enabled. Both compressed-query
tests must report 252 positional cases and seven malformed lookups with
actual policy `compressed`; their opposite `reference` request must fail.
Sanitizer diagnostics do not qualify as expected wrong-policy failures.

The full-KKT suite emits 1,344 exact fixture/order/seed records per variant.
Require equal input fingerprints, sorted certified MSF IDs and root-after-two
dimensions across rates. Require a changed recursive-work witness and reject
substitution of half records for the candidate. All 65 fields remain present,
but the rate change legitimately changes downstream work. The fresh half
records must exactly match all 65 fields and identities in the pinned parent
compressed-half correctness output. This is logical replay, not assembly or
timing equivalence. There is no extra compressed/uncompressed interaction
matrix: both variants share one unchanged compressed verifier.

The native correctness profile also builds two same-source instrumented work
drivers without running them. Those binaries require a separate later work
protocol and release. The sanitizer profile does not build a work driver.

## Timing proof and actual final objects

Timing build has exactly twelve commands: seven shared production compiles,
half/eighth KKT compiles, one shared six-solver harness main compile and two
links. Only shared `verifier_v2.cpp` adds compressed-query selection; only
eighth `kkt.cpp` adds eighth sampling selection. Both binaries physically share
all seven non-KKT objects, including the verifier, and the same main object.
There is no work instrumentation, packed macro, changed reserve, NDEBUG or
sanitizer flag in this profile. The two links introduce neither sampling nor
query-selection macros. Timing executables are built but never run here.

Receipts `validation/timing-build-{half,eighth}-build-record.json` use schema
`eighth_sampling_build_v1`, explicit variants and compressed-verifier policy.
Both top level and executable descriptors bind `sampling_policy`,
`private_acceptance_mask` (1 or 7), and `sampling_words_per_visited_edge` (1),
with exact value types. These fields describe policy; the pinned source,
exact commands, private oracle and actual-object gates establish it.

The final gate first revalidates original parent/source/recipe/build/artifact
proof and the exact timing command sequence. It independently recompiles both
KKT objects with exactly the original flags and requires byte identity to
each actual final object. Each actual eight-object set runs the unchanged
six-solver certificate test. A separate same-flags source-inclusion sampler
test runs with the seven actual shared objects and opposite-policy negatives.
This is **four positive runs, two negatives and two byte-identical rebuilds**.

The source-inclusion oracle deliberately does not link the separate `kkt.o`,
so it must not be described as observing its private RNG directly. The claim
combines pinned source/macros, exact byte-identical recompilation, the separate
same-flags private/public oracle, and certificates from the actual final
production objects. All inputs/artifacts are rechecked after the gate.

No source-only status or printed success literal is evidence that these gates
passed. Only later retained receipts can establish that. Root decides whether
to freeze and release the fixed 48-child timing study after those receipts
and independent review are complete; an outcome is not presumed.
