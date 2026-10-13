# A lower bound for repeated contraction on the hierarchy

For the zero-intrusion hierarchical fixtures, the idealized random-graph model
has expected contraction input-edge volume **Θ(m log n)** at fixed density
`m=dn`, `d>1`. This is a family-specific lower bound, not merely the general
`O(m log n)` upper bound for Borůvka. It explains a possible asymptotic work
advantage for KKT without predicting a wall-clock crossover or a monotonic
speedup on finite inputs.

The argument below was checked against the current fixture and contraction
sources. It requires no new timed run. The [earlier exact occupancy
formula](../continuation-2026-10-12/MECHANISM.md) gives the corresponding finite
expectation; this appendix makes its asymptotic lower bound explicit.

## Model and source correspondence

Let `n` be a power of two, fix an integer `d≥2`, and put

\[
m=dn,\qquad B=m-(n-1),\qquad U=\binom n2-(n-1).
\]

There is a tree backbone and a uniformly chosen size-`B` subset of its `U`
non-backbone unordered vertex pairs. In
[continuation_fixtures.hpp](../../continuation_fixtures.hpp), `Builder::add`
canonicalizes endpoints and rejects loops and duplicates. The shortcut loop
draws both endpoints uniformly and repeats rejected proposals. Under independent
uniform random draws, every remaining eligible unordered pair has the same
proposal probability, so this produces precisely sampling without replacement.
For `hierarchical_tree`, condition on the already generated backbone before
applying this argument. The path backbone is deterministic.

At intrusion zero, all backbone edges are cheaper than every shortcut; backbone
ranks increase by hierarchy level, with distinct randomized ranks within each
level. Each aligned dyadic block has exactly one backbone connection between
its two children. Inductively, every current block selects that sibling
connection before any edge leaving their parent. Thus after `r` rounds the
partition is exactly

\[
q=n/2^r\text{ blocks of size }b=2^r.
\]

It is independent of the shortcut draw. This holds for both hierarchical path
and tree, despite the latter's randomized backbone endpoints. Relabeling vertices
and shuffling input edges preserve the partition. Intrusions, `low_path` and
global-random weight controls are outside this argument.

The production [boruvka_step](../../../kkt/kkt.cpp) deletes internal edges and
keeps one minimum-weight edge per surviving component pair. Therefore its
residual edge count is exactly the number of occupied quotient pairs. The
[compacting continuation](../../continuation_search.cpp) repeats this same
primitive until no edges remain. The code represents the final connected
component by an empty graph; below, `m_r` denotes the edge count after `r`
rounds, before that round's next contraction call.

## Few shortcuts are lost in the early rounds

Fix a round and its balanced partition. Let `I` be the number of sampled
shortcuts internal to a block. Each block's induced backbone is a tree, so the
number of eligible internal shortcut pairs is

\[
A=q\binom b2-(n-q).
\]

Consequently

\[
\mathbb E[I]=B\frac A U\le B\frac{qb^2}{2U}=O(B/q).
\]

For each unordered pair of distinct blocks `i,j`, let `k_ij` be the number of
eligible original pairs between them; `k_ij≤b²`. Let `X` count unordered pairs
of sampled shortcuts joining the same pair of blocks. Sampling without
replacement gives

\[
\mathbb E[X]
=\frac{B(B-1)}{U(U-1)}\sum_{i<j}\binom{k_{ij}}2
\le\frac{B(B-1)}{U(U-1)}\binom q2\binom{b^2}2
=O(B^2/q^2).
\]

If a quotient pair receives `k` sampled shortcuts, deduplication loses `k−1`
of them, at most `C(k,2)`. Every distinct occupied shortcut pair is present in
the residual graph, even when it is also a backbone pair. Hence there is no
additional backbone-collision subtraction, and deterministically

\[
m_r\ge B-I-X.
\]

No independence between occupancy events for different block pairs is needed.

## A logarithmic number of near-full scans

Fix any `0<ε<1/2`. Uniformly for
`0≤r≤floor((1/2−ε)log₂n)`, we have `q≥n^(1/2+ε)`. At fixed `d≥2`,
`B=Θ(n)=Θ(m)`, so

\[
\frac{\mathbb E[I]}B=O(n^{-1/2-\varepsilon}),\qquad
\frac{\mathbb E[X]}B=O(n^{-2\varepsilon}).
\]

It follows that `E[m_r]≥B−o(B)` throughout Θ(log n) rounds. For the total
contraction-call input volume

\[
V=\sum_{r=0}^{\log_2n-1}m_r,
\qquad
\boxed{\mathbb E[V]=\Theta(m\log n)}.
\]

The lower bound follows by summing those early rounds. The upper bound is
deterministic: there are `log₂n` rounds and `m_r≤m`. This distinction matters:
many rounds alone would not suffice, since a hierarchy consisting only of its
backbone has a geometric edge-count sum and therefore only linear volume.

Every production contraction scans its input edges. Its minimum selection,
component labeling and endpoint-bucket deduplication take `O(n_r+m_r)` work;
`sum n_r<2n`. Thus the contraction work itself has the same expected
Θ(m log n) growth under unit-cost array and integer operations. Input conversion
and selected-ID accumulation are linear. Final public hash-set construction
has its usual average-cost hashing qualification. This argument concerns the
specific repeated-compacting strategy, not a lower bound for every MST
algorithm or every Borůvka implementation.

## Limits of the conclusion

The expectation is over the idealized uniform shortcut model. The executable
uses deterministic `mt19937` streams initialized from a finite seed. Its
rejection rule implements unbiased bounded draws under the ideal random-source
assumption; a finite PRNG seed bank is not a proof of independent uniform
sampling over every possible size-`B` subset. The derived bound is a theorem
about the mathematical family, while the archived traces check particular
generated realizations.

The current hierarchy generator additionally limits `n≤2^22`, density to
`1…512`, and `m<0x3f3f3f3f`. An `n→∞` claim extends the family beyond these
guards using sufficiently wide IDs, weights and memory. Its operation count
uses a word-RAM with words large enough for these values and constant-cost
comparisons and indexing. It does not analyze arbitrary-precision arithmetic
or a fixed machine with unlimited addressable memory. At `d=1`, there is only
one shortcut and `B=Θ(m)` fails; that case is deliberately excluded.

Combined with the standard expected-linear KKT bound under its algorithmic and
randomness assumptions, this supplies an asymptotic operation-count separation
on this engineered family. It supplies neither the implementations' constants
nor a hardware-independent threshold. Counter events, allocation, memory
access patterns and elapsed time are different observables.

The current [screen summaries](all-screens-comparison/wall_case_summary.csv)
illustrate that limit: hierarchical-path KKT/compactor paired wall ratios are
`0.8122` at 1,048,576 vertices and `0.8643` at 4,194,304 vertices (`d=16`),
corresponding to about **18.8%** and **13.6%** less time. These are separate
campaigns with one graph seed and two repetitions each. The smaller relative
lead at the larger size does not contradict the expected work bound, and the
bound does not justify replacing either measured result with a monotonic trend.
