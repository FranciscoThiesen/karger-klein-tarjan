# Expected compactor edge volume on sparse attachments

This is a mathematical statement about the ideal graph model and the repeated
compactor's input-edge counts. It is not a timing prediction. The finite seeded
generator supplies realizations to compare with the model; its PRNG stream is
not a proof of uniform sampling over all shortcut subsets.

## Model and deterministic partitions

Fix the attachment block size `b` in `{4,16}` and integer density `d>=1`,
independently of `n`. More generally the argument allows any fixed integer
`b>=2`; it does not cover `b=1`, which has no initial star contraction. Let
`n=bq`, where `q` is a power of two, and require a feasible connected core:
`1<=B<=U` with `B,U` defined below. The original graph has `m=nd` edges:

\[
L=n-q,\qquad E=m-L=q[b(d-1)+1],\qquad
B=E-(q-1)=n(d-1)+1.
\]

There are `q` cheap local stars, each with `b` vertices and `b-1` edges. The core
contains the path on vertices `0,...,q-1` plus a **uniformly chosen subset of
exactly `B` distinct non-path pairs**. Its available shortcut population is

\[
U=\binom q2-(q-1)=\frac{(q-1)(q-2)}2.
\]

Each core edge becomes exactly one original external edge, either center to
center (`leaf`) or between chosen clones (`community`). Both endpoint modes
produce the same core after the first contraction. Every local edge is cheaper
than every external edge. Therefore the first contraction selects the local
stars and produces exactly `q` vertices and `E` edges, with no parallel external
edges to discard.

For **hierarchy** weights, all path edges precede the shortcuts, and the path
bridges have increasing dyadic levels. For **distance** weights, every core edge
is ordered by its endpoints' dyadic level. In both cases each current aligned
block's cheapest outgoing edge reaches its sibling block: the path guarantees
such an edge, and every edge leaving the sibling pair has a higher relevant
level. Thus later partitions are the deterministic aligned blocks of sizes
`s=1,2,4,...,q`. They do not depend on which shortcut subset was drawn. Unique
within-level ranks can change selected IDs but cannot change these partitions.

The calculation below applies to those two weight modes. Core-only shuffled
weights preserve the first star contraction but not later aligned partitions.
Global-random weights do not even guarantee the first star contraction.

## Exact expected quotient size

At core block size `s`, write `k=q/s`. Let `M_s` be the number of edges after
discarding internal edges and retaining one representative per quotient pair.
The `k-1` adjacent block pairs always have a path bridge. Each other block pair
contains exactly `s²` potential shortcuts, all from the population of size `U`.
Sampling without replacement therefore gives

\[
\boxed{\displaystyle
\mathbb E[M_s]
=(k-1)+\left[\binom k2-(k-1)\right]
\left[1-\frac{\binom{U-s^2}{B}}{\binom UB}\right].}
\]

Interpret the numerator as zero when there are fewer than `B` unmarked pairs.
Omit the second term entirely when its prefactor is zero; this covers `k=1,2`
without asking for a binomial coefficient with negative upper argument. The
formula counts both shortcut internalization and parallel-edge collapse. It
uses linearity of expectation, not independence between occupied quotient pairs.

At `s=1` it is exactly `q-1+B=E`. At `k=2` it is exactly one. The terminal `k=1`
quotient has no edges. If `V` denotes total edge-input volume, including the
original graph's first contraction, then

\[
\boxed{\displaystyle
\mathbb E[V]=m+\sum_{r=0}^{\log_2q-1}\mathbb E[M_{2^r}].}
\]

The terminal isolated quotient vertex is not an additional edge-bearing input.
`V` counts edge inputs; it does not multiply them by the number of internal
passes in a contraction or count other operations, allocations or cache misses.

## Fixed `b`, fixed `d>=2`: expected Θ(m log n) volume

Here `B=n(d-1)+1=Θ(m)` and `U=Θ(q²)`. Consider any dyadic `s` with

\[
k=q/s\ge4,\qquad \lambda=Bs^2/U\le1.
\]

The probability that none of the `s²` marked pairs is drawn satisfies

\[
P_0=\frac{\binom{U-s^2}{B}}{\binom UB}
\le \left(1-\frac{s^2}{U}\right)^B
\le e^{-\lambda}.
\]

If avoidance is impossible, `P_0=0` and the same upper bound holds. For
`0<=λ<=1`, concavity gives `1-exp(-λ) >= (1-exp(-1))λ`. Also, for `k>=4`,

\[
A=\binom k2-(k-1)\ge k^2/8,
\qquad U\le q^2/2,
\qquad \frac{As^2}{U}\ge\frac14.
\]

Consequently every such round has

\[
\mathbb E[M_s]\ge A(1-e^{-\lambda})
\ge \frac{1-e^{-1}}4 B
\ge \frac{1-e^{-1}}8 m,
\]

where the last step uses `B/m >= (d-1)/d >= 1/2`. These deliberately loose
constants suffice for the lower bound.

The number of these early dyadic inputs is

\[
R=\max\left\{0,\ 1+\left\lfloor
\log_2\min\left(\frac q4,\sqrt{\frac UB}\right)
\right\rfloor\right\}.
\]

For fixed `b,d`, `U/B=Θ(q)`, so `R=(1/2)log₂q-O_{b,d}(1)=Θ(log n)` as
`n` grows. Summing the preceding per-round lower bound yields
`E[V]=Ω(m log n)`. No concentration or independence across rounds is required.

For the upper bound, contraction never increases the number of surviving
edges. There are exactly `log₂q` edge-bearing core inputs, each with at most
`E<=m` edges. Hence

\[
V\le m+E\log_2q\le m(1+\log_2q)
\]

for every graph realization. Together these bounds prove

\[
\boxed{\mathbb E[V]=\Theta(m\log n)}
\]

for this idealized fixed-parameter family with `d>=2`. Because `m=nd` and `d`
is fixed, it is also `Θ(n log n)`. This is an asymptotic statement about the
mathematical family, not an assertion that the finite capped benchmark range
already exhibits the limiting regime.

## Constants, capacity and two useful contrasts

The exact feasible-core condition is

\[
E\le\binom q2
\quad\Longleftrightarrow\quad q\ge2b(d-1)+3.
\]

Near that boundary the core is relatively dense and many parallel quotient
pairs can collapse early. The asymptotic lower-bound constant does not identify
a useful finite-size threshold. The exact occupancy expression is preferable
for comparison with finite traces.

The first retained fraction is

\[
\rho=E/m=1-\frac{b-1}{bd}.
\]

For larger `n` at fixed `b,d`, the early-round count above behaves as

\[
R=\tfrac12\log_2n-\log_2b
-\tfrac12\log_2[2(d-1)]+O(1).
\]

Larger `b` reduces the core's vertex count but also reduces the number of rounds
covered by the high-retained-volume bound. Changing `b` or `d` therefore changes
constants as well as the simple-core capacity. This theorem does not apply
unchanged when those parameters grow with `n`.

**Complete-bundle lift.** If each core edge is expanded into all `b²` clone
pairs while the same original `n,m,L` are retained, the first quotient contains
`E_bundle=(m-L)/b²=ρm/b²` edges, when the dimensions are integral and feasible.
The sparse attachment keeps all `m-L` external edges instead. In particular,

\[
V_{\mathrm{bundle}}\le m+\frac{\rho m}{b^2}\log_2q.
\]

The bundle collapse can substantially reduce subsequent repeated edge volume.
It need not change the asymptotic order for fixed `b`: if the feasible bundle
core still has `Θ(m)` shortcuts, the same occupancy argument gives a logarithmic
factor with a smaller coefficient. Several sparse attachment settings have no
connected large-`q` bundle counterpart at the same density. In addition to
divisibility, that counterpart needs `(m-L)/b²>=q-1`; asymptotically, integer
`d` must be at least `b+1` for fixed `b>1`.

**Density `d=1`.** There is exactly one core shortcut, `B=1`. Every quotient has
at most its `k-1` path edges plus that one surviving shortcut, so `M_s<=k=q/s`.
Thus, deterministically,

\[
m\le V\le m+\sum_{r=0}^{\log_2q-1}q/2^r
=m+2q-2=\Theta(m).
\]

The logarithmic lower-bound mechanism is absent at `d=1`; it is not merely a
case omitted from the proof.

## What this does and does not establish

The result identifies repeated edge-input work that filtering could avoid on
these deliberately structured weight families. It establishes neither the
actual implementation's running-time complexity nor a finite wall-clock
crossover for KKT. It does not measure KKT's filtering, recursion, verifier or
allocation constants. It also provides no dominance claim over Kruskal, Prim
or the noncompacting Borůvka implementation: they have different work and
locality costs. Those comparisons require the retained measured results and
correctness checks, including losing instances and shuffled controls.
