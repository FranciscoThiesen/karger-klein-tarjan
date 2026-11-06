# Checked conditional KKT cost model

**Checked on 5 November 2026 with Lean 4.24.0 and mathlib v4.24.0.**
The [validation record](verification-2026-11-05/VALIDATION.json) binds the exact
sources, dependencies and [successful Lake build](verification-2026-11-05/project-build.stdout).
All ten printed declarations depend only on `propext`, `Classical.choice` and
`Quot.sound`. There are no admitted goals or custom axioms in these sources.
This is not a verified C++ implementation or a proved KKT sampling lemma.

## What was checked

[`KKTRecurrence.lean`](KKTRecurrence.lean) checks the affine arithmetic step and
its half- and eighth-sampling specializations. The original prepared file did
not compile: `linarith` could not normalize two rational-division expressions
in the eighth-sampling proof. Explicit normalization repairs those tactic steps
without changing the theorem statements. The original failed run is retained in
[`original-check.stdout`](verification-2026-11-05/original-check.stdout); its
`sorryAx` diagnostic belongs to a failed compilation, not the final proof.

[`ExpectedWork.lean`](ExpectedWork.lean) adds a recursive model with finite joint
outcomes, nonnegative normalized probabilities, nonnegative local costs, and
strictly decreasing vertex ranks. Lean checks termination and the full affine
bound by strong induction, including the finite sums of correlated child costs.
The expected child-size bounds and the linear nonrecursive-work bound remain
explicit hypotheses. No independence between the two children is needed for
addition of expectations. The intended KKT instantiation uses `0 < p < 1`;
the general arithmetic lemma deliberately states only the inequalities it needs.

For sampling probability `p=1/8`, the sufficient budget is
`(8c/7)m + (46c/7)n`, provided every local call costs at most `c(m+n)` and the
required mean-size bounds hold. The proof therefore identifies exactly where an
unaccounted superlinear library operation would invalidate the implementation
argument. Empty-call overhead must be charged to the parent or added as a
constant to the public bound.

Additional checked results establish:

- The all-colliding chain walk has `n(n-1)/2` previous-node visits and no uniform
  linear bound in the unbounded natural-number model. Applying that model to
  libc++ requires the separately inspected bucket-walk correspondence. Actual
  fixed-width edge IDs limit the realizable input sizes.
- A uniform upper bound on each operation's cost preserves a linear total-cost
  bound. Equal cycle costs are unnecessary. The finite set in
  `sum_cost_le_uniform` indexes **operation occurrences**, such as positions in
  an execution trace, so repeated operations are counted separately.
- A deterministic 32-bit seed cannot cover all 33-bit sampling patterns. The
  probability argument connecting this cardinality fact to nondegenerate iid
  Bernoulli sampling is separate. It does not prove PRNG-induced slowdown.

## Reproduce

With Lean's toolchain manager installed, run:

```sh
cd lean/kkt_recurrence
lake exe cache get
lake build
```

`lean-toolchain`, `lakefile.toml` and `lake-manifest.json` pin the compiler,
mathlib commit and transitive dependency commits. Dependencies and compiled
outputs belong under the ignored `.lake/` directory. This run instead used a
temporary project with the same sources and pinned manifests; no toolchain or
compiled library was added to the repository. The official native arm64 release
archive's SHA-256 was checked against its GitHub release metadata. Mathlib's
official precompiled cache supplied dependencies; the final declarations were
elaborated and checked using Lean's ordinary default trust settings.

The final `project-build.*` logs are authoritative. The separately retained
`intermediate-ExpectedWork.*` logs predate the final collision-growth lemma.
The original uncompiled source is retained as
[`original-prepared-source.lean`](verification-2026-11-05/original-prepared-source.lean).
The broader implementation audit, native witnesses and timing investigation
remain in the separate local research checkout; they are not included in this
focused proof publication. This branch adds no production algorithm changes.
