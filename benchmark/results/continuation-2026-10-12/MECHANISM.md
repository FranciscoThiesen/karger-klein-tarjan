# Why delayed contraction could favor KKT

This note separates properties of the fixture and implementation from hypotheses
about elapsed time. It does not declare a confirmed winner. The initial screen
selects cases; the fresh-seed, two-campaign rule in [PROTOCOL.md](PROTOCOL.md)
governs confirmation. Every solver is unchanged and receives ordinary edge tuples.

## A hierarchy that keeps edges alive

Let `n` be a power of two and `m = d n`. Each fixture contains a connected
backbone with `n−1` edges plus `B = m−n+1` distinct random shortcuts. The backbone
connects the two halves of every aligned dyadic block once. `hierarchical_path`
uses consecutive vertices; `hierarchical_tree` chooses an endpoint uniformly
inside each half. A level-`r` backbone edge connects halves of size `2^r`.
All backbone weights precede shortcuts, and backbone ranks increase with level,
with randomized ordering within each level.

With zero intrusion, a production Borůvka round merges exactly the two sibling
blocks at the next level. Each block has exactly one backbone connection to its
sibling, and all connections leaving their parent are heavier. Inductively,
after `r` rounds there are `q = n/2^r` connected blocks of size `b = 2^r`.
The terminal single component is represented by an empty graph in the code.
Labels and tuple order do not change these partitions.

This is deliberately stronger than merely requiring many rounds. A path without
shortcuts also takes logarithmically many rounds, but its edge counts halve:
the total is less than `2n`. Here the shortcuts can survive many rounds as
distinct component pairs. The baseline scans, compacts and deduplicates them
using the same production `boruvka_step` that KKT calls.

## Exact expected residual and total edge volume

Condition on either backbone. The shortcut generator samples a uniform subset
of `B` unordered pairs from the `U = C(n,2)−(n−1)` pairs outside that tree.
At round `r`, the contracted backbone occupies exactly `q−1` component pairs.
Those pairs remain present regardless of shortcuts. Each of the other
`S = C(q,2)−(q−1)` component pairs has exactly `b²` eligible original shortcut
pairs. Its probability of receiving at least one shortcut is

\[
1-\frac{\binom{U-b^2}{B}}{\binom{U}{B}}.
\]

Therefore the exact expectation over shortcut draws is

\[
\boxed{\mathbb E[m_r]
=q-1+\left[\binom q2-(q-1)\right]
\left[1-\frac{\binom{U-b^2}{B}}{\binom UB}\right].}
\]

Use a zero numerator when `B > U−b²`. No independence between different
component-pair occupancy events is required: this is linearity of expectation.
The formula gives `m_0=m` and `m_r=1` when `q=2`. The sum of contraction-call
input edges is

\[
\mathbb E[V]=\sum_{r=0}^{\log_2 n-1}\mathbb E[m_r].
\]

This counts each round's input once. It is not the number of individual loops,
bytes transferred, CPU instructions, or KKT recursive input edges. The
implementation makes several passes and allocates additional arrays.

For fixed integer `d≥2` as `n` grows, `B=Θ(m)`. While `q²` is much larger than
`B`, most shortcuts still occupy distinct component pairs, and `E[m_r]=Θ(m)`.
The transition occurs at `q≈sqrt(B)`, after roughly
`log2(n/sqrt(B)) ≈ ½ log2(n/d)` rounds. Thereafter the simple-graph bound
`m_r≤C(q,2)` falls by about a factor of four per round. Thus this model has
`E[V]=Θ(m log n)` at fixed `d≥2`; allowing density to vary gives the scale
`Θ(m [1+log(n/d)])` in the feasible range `2≤d≤(n−1)/2`.
Increasing density at fixed `n` shortens the retention plateau. A nearly
complete graph is not the strongest normalized edge-volume stress case.

These asymptotic statements concern the mathematical family extended to
arbitrary sizes and sufficiently wide IDs/weights. The implemented generator
has explicit finite size and weight-domain limits. At `d=1`, there is only one
shortcut; the fixed-density lower-bound argument above does not apply.
Intrusions and globally randomized controls also need not preserve dyadic
partitions, so their actual traces must replace this formula.

## What sampling offers, and what it costs

The KKT sampling lemma bounds expected F-light edges by `v/p` when every edge
of a graph with `v` vertices is sampled independently with probability `p` and
`F` is the sample's minimum spanning forest. At the root of the zero-intrusion
hierarchy, two contractions leave `v=n/4`; half sampling therefore leaves at
most `n/2` F-light edges in expectation, even when the residual still contains
nearly `m` edges. The theorem concerns expectation under independent random
choices and a unit-cost comparison model. A finite `mt19937` stream and a few
seeds do not themselves prove those assumptions or an elapsed-time crossover.
[Karger, Klein and Tarjan, sampling lemma and expected-time analysis](https://people.csail.mit.edu/karger/Papers/mst.pdf)

The implementation must first solve the sample, build its forest representation,
classify edges, materialize the retained graph and recurse. Its recursive
storage lifetimes also differ from the iterative baseline, which releases each
old input after contraction. A smaller retained graph does not imply those
costs have paid for themselves. Compare their common `contraction_edges`
counter, verifier inputs and materializations in separate untimed runs; do not
equate a mixture of logical events with instructions or memory stalls.

## Weight controls and the distance-order extension

All paired variants preserve endpoints, IDs, vertex labels and input order.
`low_path` keeps every backbone edge cheaper than every shortcut but shuffles
the backbone priorities. `random_path` and `random_tree` shuffle all edge
weights globally. They distinguish dyadic ordering from topology and from
merely planting a cheap tree. Intrusion settings promote exactly
`floor(n*p/1000)` uniformly chosen shortcuts into the backbone's cheap ordering,
preserving relative backbone priorities. This is a count relative to `n`, not
a percentage of all edges; selected intrusions need not enter the MST.

`distance_path` and `distance_tree` order **all** edges by
`floor(log2(u xor v))` on original labels, with random ordering within each
level. Shortcut edges compete with the backbone. The unique MST chooses the
minimum crossing edge between the children of each internal dyadic block;
these choices need not be backbone IDs. Both distance variants nevertheless
contract the same dyadic partitions as their zero-intrusion hierarchical twins,
so every compactor vertex/edge count, and the expectation above, is identical
for a fixed shared topology. Surviving IDs and data-dependent work can differ.

These ranks are order-equivalent to costs
`D(u,v)=2^floor(log2(u xor v))+epsilon_uv`, where distinct positive perturbations
are smaller than `1/4`. Set diagonal costs to zero. The unperturbed complete
distance is an ultrametric: any triple's largest value is attained at least twice.
The remaining nonzero side is at least one, so these perturbations preserve
ordinary triangle inequalities. Distinct perturbations generally break the
ultrametric inequality. The stored integer ranks themselves are **not** claimed
to satisfy triangle inequalities; the metric realization only explains their
ordering. Missing pairs can receive compatible perturbations to complete that
metric. The solver never receives or uses this hidden representation.

This is still an engineered hierarchical model, not a road, geometric-neighbor
or measured application graph. With uniform shortcuts it can remain close to
the planted backbone. For sibling halves of size `b`, the number of alternatives
to their backbone edge has mean `B(b²−1)/U`. The probability of replacing that
backbone edge is at most `min(1,B(b²−1)/U)`. Summing over `n/(2b)` blocks at each
dyadic scale gives an expected `O(sqrt(nd))` replaced backbone edges when
`d≥2` and `d` is small relative to `n`. A non-predetermined MST is consequently
not evidence that a constant fraction of it differs from the backbone. The
certified MST/backbone overlap is an empirical diagnostic. Sampling may also
preserve more hierarchy in these distance-weighted graphs, increasing its own
costs; the extension does not guarantee a larger KKT advantage.

## Interpreting the initial density-64 crossing

The [initial discovery report](discovery-analysis/report.md) records paired
KKT/compactor ratios changing from `1.1912` to `0.9348` for the path and from
`1.1731` to `0.9286` for the tree as `n` grows from `16,384` to `65,536` at
`d=64`. These are selection observations, below the protocol's required effect
size for a clear winner; they do not establish holdout success.

The edge-volume model already predicts a relative improvement with size,
without assuming a cache boundary. For illustration, replacing the exact
hypergeometric no-hit probability by `(1−B/U)^(b²)` gives approximately
`E[V]/m=4.29` and `5.27` at these two sizes. This approximation is not a measured
trace. Four times as many edges therefore imply about `4.91` times as much
compactor input-edge volume. Under constant per-edge costs and linear KKT
work, that alone would multiply KKT/compactor time by about `4.29/5.27=0.815`;
the observed paired-ratio changes are about `0.785` and `0.792`. The direction
and much of the relative trend are consistent with the structural hypothesis.

Absolute times also show important effects beyond that simple count: compactor
time grows about `10.4×`, while KKT grows about `8.2×`, over the same `4×` edge
increase. If each edge has four 32-bit fields, one edge array's payload grows
from `16 MiB` to `64 MiB`, before copies, buckets, forest tables and recursive
storage. Cache locality, bandwidth, allocation, branch behavior or system
conditions could change the cost per logical event. No per-solver hardware
counters were collected. Process-level `/usr/bin/time` instruction/cycle totals
include generation, certification and both algorithms; they cannot attribute
hardware behavior to one solver. This experiment therefore cannot assign the
crossing to caches, identify a cache level, or separate these effects. The
evidence supports testing both
structural edge-volume growth and changing machine costs; it does not justify
choosing a cache-only or an asymptotics-only explanation.
