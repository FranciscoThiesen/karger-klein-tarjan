# Private scalar one-eighth sampling: source preparation

Prepared 2026-10-15 during the larger-hierarchy performance hold. These files
have **not** been applied to a repository, imported, compiled, tested, frozen,
or benchmarked. No worktree has been created. No active timing output was read.
Source review is not executed validation; every gate below remains deferred.

This is a separate experiment from packed sampling and from the prepared
packed-plus-compressed combination. It changes the private sampling rate while
retaining one `std::mt19937` draw per visited edge, the half-size reservation,
the compressed verifier, retained parallel edges, direct Edge input and all
other solver code. It makes no speedup claim.

## Prepared files and exact boundary

- `overlay/kkt/kkt.cpp`: compressed-parent source with one new include,
  a compile-time private-policy selector, and a shared predicate replacing the
  existing odd-word condition. No callback or loop refactor is needed.
- `overlay/kkt/experimental_eighth_sampling.hpp`: a pure inline predicate.
  `accept_scalar_sample_word<false>(word)` accepts odd words;
  `<true>` accepts `(word & 7u) == 7u`.
- `overlay/test/eighth_sampling_test.cpp`: three deterministic finite-word
  predicate groups, including all low-three-bit residues, the first 65,536
  words, high-bit/extreme patterns, and scripted scalar call boundaries.
- `overlay/test/eighth_sampling_integration_test.cpp`: actual private-template
  dispatch, independent modulo/compaction oracle, exact engine-state replay,
  input immutability, signed extreme IDs/costs/legacy metadata, public calls
  interleaved with private calls, empty inputs and sizes through 625. It defines
  132 private/public cases, each replayed, for 264 actual sample invocations
  per executable, and requires a positive half/eighth discrimination witness.
- `native.patch`: the small change to the existing `kkt/kkt.cpp` only; install
  the new header/tests as well. The full overlay file is supplied for review.
- `STUDY_PROPOSAL.md`: the prospective fixed comparison and deferred gates.
- `SOURCE_REVIEW.md`: independent read-only review passed; execution remains
  deferred. The original receipt covers native overlay and the first proposal;
  the new builder/final-object source review is separate.
- `overlay/benchmark/build_eighth_sampling.py`,
  `overlay/benchmark/test_eighth_build.py`, and
  `overlay/benchmark/results/eighth-sampling-2026-10-15/validation/validate_final_objects.py`:
  deferred native/sanitizer builds, seven mocked build-gate groups and actual
  final-object validation. See `BUILD_PREPARATION.md` for the exact commands.

The future variants are named `half` and `eighth`. Only the latter KKT compile
adds `-DKKT_EXPERIMENT_EIGHTH_SAMPLING`. With that macro the selector is
`use_eighth = use_parent_positions`; without it, it is always false. Thus the
public wrapper's `<false>` instantiation retains the legacy half policy in
both builds. `H.reserve(P.graph_edges.size() / 2)` is textually unchanged.
The same post-loop instrumentation, metadata construction and isolated-vertex
compaction are untouched. This is not a reservation optimization.

The source is copied from the implementation bound by the compressed parent
freeze at
`/Users/random_person/Desktop/kkt-compressed-queries/benchmark/results/compressed-query-2026-10-15/freeze.json`
(SHA-256 `bd65da13058d3e9cfa58919a0fe5e02b8a46b1d0b8fe7f05801692d5a0866df9`).
Full original source/helper/build/artifact proof must be freshly checked after
release. The current prepared source has not run that proof or a patch check.

## Semantics and limitations

For a fresh ideal uniform 32-bit word, the acceptance probabilities are exactly
1/2 and 1/8. The eighth event is a subset of the half event for each word. At
the same graph and engine-entry state, both direct sampling calls consume
exactly `m` words, retain accepted positions in input order, and leave exactly
the same engine state. Empty input consumes none. There is no packed word,
bit tail, or residual state between calls; all unused bits are discarded for
each edge, as in the current scalar path. Size 31/32/33 boundaries therefore
must not change word consumption; 623/624/625 also exercise MT refill boundaries.

The oracle uses modulo rather than the production bit mask. It independently
reconstructs stable vertex compaction, every Edge field, parent-position IDs,
and legacy metadata. Its requested policy is a runtime argument, independent
of the production macro, so opposite-policy invocations must fail. The direct
test's instrumentation assertions check existing field meanings only when
`KKT_ENABLE_WORK_STATS` is enabled; the same test also supports final
uninstrumented flags.

These local coupling properties do **not** imply equal recursive engine exit
states or equal work: sampled inputs differ, subsequent call lengths and
forests differ, and later engine words are attached to different edges.
Finite deterministic MT seeds do not establish the ideal independent-coin
model. A smaller expected sample trades against a weaker light-edge survivor
bound and changed recursive forest structure. Reserving `m/2` also leaves
capacity proportional to the parent size even when only about `m/8` records
are accepted. No lower memory peak or runtime improvement follows by itself.

The reviewed theory source is the current
`docs/kkt-report/FIXED_SAMPLING_PROBABILITY.md` in the compressed worktree.
It gives the fixed-probability expected-linear-work argument and its
assumptions. This preparation adds no theoretical guarantee and does not
choose a fallback rate after observing results.

## Deferred installation

Only after root authorizes a new isolated worktree descending from the pinned
compressed implementation: verify the complete parent proof, preserve existing
user work, check/apply `native.patch` or copy the identical prepared KKT overlay,
and add the three new header/test files. Recheck the native source allowlist:
one changed existing production file (`kkt/kkt.cpp`) and exactly these three
native additions. No packed source/header is installed. Keep parent helpers
and their original artifacts intact. Builder/final-object and collector source
preparation now lives only in this temporary overlay. Nothing has been copied
into an actual repository or executed. The prepared gates must pass after a
separate release before timing is considered.
