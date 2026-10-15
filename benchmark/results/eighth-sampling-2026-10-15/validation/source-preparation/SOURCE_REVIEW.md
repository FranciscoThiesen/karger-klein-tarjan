# Independent source review

2026-10-15; reviewer `/root/multigraph_candidate`.

Source review **PASS, no blocker found**. This is a manual source assessment,
not an imported, compiled, sanitizer-tested or measured result. No patch was
applied, no repository/worktree created or modified, no native command run,
and no partial active timing read for this review.

Reviewed `native.patch`, the overlay KKT source and predicate header, both test
sources, `README.md`, and `STUDY_PROPOSAL.md`. The reviewer confirmed:

- The actual overlay KKT diff matches `native.patch`; only private `<true>`
  selects mask 7 under the experiment macro. Default and public paths retain
  odd-word mask 1, with exactly one `rng()` per position.
- Reservation, emission, order, ID/legacy metadata and work accounting remain
  unchanged outside the intended predicate selection.
- The independent modulo oracle, original-position subset comparison using
  IDs despite differing compaction, exact per-call engine replay, interleaved
  public calls, empty/extreme fixtures and 132 cases each replayed are coherent.
- Runtime opposite-policy negatives, native/sanitizer validation and actual
  final-object proof are explicitly deferred.
- The fixed study counts are consistent: 48 children, 2,016 outputs, 1,728
  cross-variant clock pairs, 2,880 direct comparator clock pairs and 30
  endpoint classifications. Cross-rate cumulative counters may differ.

Outstanding gates: authorized isolated installation and patch/source proof,
all focused and existing correctness tests, Clang 22 sanitizer tests, full
same-source artifact/final-object proof, a future independently reviewed
collector/protocol freeze, and a separate root performance release. None is
implied by this review.

## Deferred build extension review

Later on 2026-10-15, `/root/multigraph_candidate` independently reviewed
`overlay/benchmark/build_eighth_sampling.py`, its seven prepared mocked test
groups in `test_eighth_build.py`, the final-object validation script, and the
updated preparation scope. **Source review PASS, no blocker found.**

The review confirmed one fixed compressed verifier, 20 positives and four
clean wrong-policy negatives per correctness profile, exact 65-field parent
half replay, and cross-rate equality of 1,344 input/MSF/root records while
permitting downstream work differences. It checked the exact twelve-command
timing recipe, seven physically shared non-KKT objects and shared main, the
same-flags byte-identical KKT rebuilds, and the distinction between actual
final-object certificates and the separate source-inclusion RNG oracle.
Inherited native/sanitizer guards and post-run source/object rechecks remain
intact. No imports, mocks, builds or native execution were performed.

The updated scope deliberately removes the earlier optional 2-by-2 verifier
experiment: the compressed verifier is unchanged and shared throughout.
Neither this source review nor the earlier native overlay review satisfies
the outstanding executed validation or performance-release gates.

## Dedicated outer-controller review

Later on 2026-10-15, the same reviewer examined the new bounded outer build
controller and its four prepared mocked groups. An initial review found that
an already-exited child could bypass the loop's deadline check. The controller
now records and checks an integer monotonic exit-observation timestamp after
the loop; a positive-budget, late zero-exit mock covers that exact branch.
The fresh collector is also explicitly included in the outer source inventory.

Final source rereview **PASS, no remaining blocker found**. The reviewer
confirmed nested command/outcome counts of 67, 64, 12 and 15, bounded cleanup
cooperation, exclusive receipts, and conservative unknown-state handling for
detached sessions. The independent review history is retained in
`INDEPENDENT_SOURCE_REVIEW.md`. No import, mock, build or native execution has
occurred; these reviews do not replace the deferred runtime gates.
