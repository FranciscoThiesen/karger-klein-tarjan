# What the Lean verification establishes

On 5 November 2026 the previously prepared arithmetic source was actually run
through Lean. The first run failed in two eighth-sampling tactic steps. The
mathematical statements were sound; explicit normalization of rational division
made the proof scripts elaborate. The repaired source and a new recursive cost
model pass a pinned Lean 4.24.0 / mathlib v4.24.0 build. The
[record](../../lean/kkt_recurrence/verification-2026-11-05/VALIDATION.json) contains
the source hashes, dependency commits, initial failure and successful output.

This is a useful formal result, with a specific boundary. The model defines a
finite randomized recursion with two possibly correlated children. Its outcome
weights are nonnegative and normalized; its children have strictly smaller
vertex counts. Lean checks the recursion's termination and proves an affine
expected-work bound by strong induction. For KKT, the caller must still supply
the expected child-size inequalities, linear local work and graph correctness.
We have not verified a C++ translation or proved the sampling lemma in Lean.

The central conditional statement is:

\[
\begin{aligned}
\mathbb E[m_S]&\le p m,& \mathbb E[m_L]&\le n/(4p),\\
\mathbb E[n_S]&\le n/4,& \mathbb E[n_L]&\le n/4,\\
W_{\rm local}(G)&\le c(m+n).
\end{aligned}
\]

With the necessary strictly decreasing ranks, these hypotheses imply the full
bound `E[W] ≤ a m + b n` when `c+ap ≤ a` and
`c+a/(4p)+b/2 ≤ b`. At `p=1/8`, sufficient coefficients are
`a=8c/7` and `b=46c/7`. These are proof budgets, not fitted runtime constants.

This exposes three distinct implementation boundaries:

1. **Uncharged library work.** The public result's chained hash-set insertion
   can visit all previously inserted nodes when IDs collide. Lean separately
   proves the count `n(n-1)/2` and that this abstract count has no uniform linear
   bound. The empirical libc++ witness remains in the separate local research
   checkout and is not included in this proof-only publication. No libc++
   implementation is automatically extracted into Lean. An implementation-level proof
   must account for that conversion or impose a justified ID/hash contract.
2. **Randomness.** The ideal independent sampling law is a premise. Lean checks
   that no map from 32-bit seeds can cover all 33-bit patterns. Consequently a
   finite deterministic seed is not literally an arbitrary-length iid stream;
   this is a missing probability-model correspondence, not evidence that the
   measured benchmark's growth is caused by the generator.
3. **Cost per operation.** Lean checks that if every charged operation costs at
   most a fixed `C`, a linear work bound remains a linear cost bound. The costs
   need not be equal. A cache transition that raises the cost and then plateaus
   can change constants and a finite-range curve fit without contradicting
   asymptotic linearity. The proof makes no claim about measured cache misses,
   wall-clock time, scheduling or unbounded memory hierarchies.

The final build prints ten declarations' axiom dependencies, all limited to
Lean's ordinary `propext`, `Classical.choice` and `Quot.sound`. It contains no
`sorryAx`, custom KKT axioms or native-evaluation shortcut. Standard precompiled
mathlib dependencies and Lean's default import trust were used. Reproduction
instructions and exact remaining scope are in the
[Lean project README](../../lean/kkt_recurrence/README.md).
