# Separate work lower bounds for the classical implementations

The [attachment occupancy argument](ATTACHMENT_BOUND.md) establishes an
expected lower bound for repeated compacting Boruvka. It does not itself
establish a Kruskal lower bound. Two separate implementation facts support
the narrower comparisons below. They concern logical work under explicit
models, not a measured wall-clock crossover.

## Kruskal's mandatory full comparison sort

The [current Kruskal implementation](../../../kruskal/kruskal.cpp) copies all
`m` input edge tuples and sorts the entire copy by weight before running
union-find. Its comparator reads only the two weights and returns their
strict ordering. There is no partial-sort shortcut or use of the integer
weights as direct array indices.

Fix any graph with `m` distinct edge weights. Suppose its physical edge order
is an **independent uniform permutation**, conditional on that weighted graph,
and the sorting implementation obtains ordering information only through
comparisons. A binary comparison decision tree that sorts these tuples must
distinguish `m!` possible orders. The average leaf depth under the uniform
distribution is at least `log₂(m!)`, so the mandatory sort requires

\[
\mathbb E[\text{comparisons}]\ge\log_2(m!)=\Omega(m\log m).
\]

This lower bound applies conditional on each fixed weighted graph, and hence
also after averaging over other graph-generation randomness. Random shortcut
placement or random weights are not needed for this argument; the ideal
independent uniform physical order is sufficient.

That distribution is an assumption about the ideal model, **not a property
proved for the finite captured seed bank**. The
[attachment generator](../../../benchmark/core_attachment_fixtures.hpp)
finishes with a shuffle using a separate order engine, but all its engines
are deterministic functions of one finite graph seed. Separate engines do
not establish probabilistic independence, and a 32-bit seed cannot span all
`m!` permutations for large `m`. The decision-tree argument therefore does not
prove this average lower bound for the particular recorded seeds.

The conclusion concerns the full comparison sort performed by this
implementation. It is not a lower bound for finding an MST or for every
implementation called Kruskal. These fixtures use exactly the integer ranks
`1..m`; another implementation could exploit that universe using direct
placement/counting or another non-comparison ordering method. The comparison
lower bound would not apply to that alternative.

## Original Boruvka's repeated scans

The [original Boruvka implementation](../../../boruvka/boruvka.cpp) retains
the original edge array. Every iteration scans all `m` edges, including edges
that have become internal to a selected component. It first recomputes
components from the selected forest, then chooses their cheapest outgoing
edges.

For the hierarchy and distance attachment modes, let `n=bq`, with fixed block
size `b>1` and dyadic `q`. Every local star edge is cheaper than every core
edge. The first merging round therefore forms exactly the `q` star blocks.
The [deterministic partition argument](ATTACHMENT_BOUND.md#model-and-deterministic-partitions)
then applies: each aligned block's cheapest outgoing edge reaches its sibling,
and unique weights make both siblings choose the same edge across their cut.
Each later merging round halves the number of blocks. Keeping internal edges
and heavier parallel representatives does not change those cut minima.

There are exactly `1+log₂(q)` merging rounds. In this source, there is also
one terminal iteration: `graph_cc = cur_cc` records the component count
**before** the newly selected edges are incorporated. After the last merge,
the stored count is still two. The next iteration finds one component, scans
all original edges again, selects none and exits. Thus the original-edge
loop performs exactly

\[
\boxed{m\,[\log_2(n/b)+2]}
\]

visits on these ordered families. This is a **source-derived count**, not a
new measured counter result. It gives a deterministic `Ω(m log n)` work lower
bound for fixed `b`, for every feasible shortcut realization and within-level
rank order. It holds for both leaf and community endpoints, and even at
`d=1`; it does not apply to the shuffled-core or global-random weight controls.
It needs neither the occupancy expectation nor an ideal random input order.
The argument assumes enough stack and memory for the recursive component
traversal to complete; a crash is not a successful execution or a timing win.

## What follows conditionally for KKT

The [KKT theorem](https://www.cs.cmu.edu/~guyb/paralg/papers/KargerKleinTarjan95.pdf)
gives expected `O(m+n)` work when its required primitives have the stated
linear costs in the unit-cost RAM model. Connected inputs give `O(m)`.
If an implementation realizes those assumptions, its expectation over
algorithm randomness has that bound for each fixed input. Averaging the
per-input bound over a graph distribution preserves it.

Under that condition, these separate comparator lower bounds establish an
asymptotic expected-work separation: from this full-sorting Kruskal under the
ideal permutation assumption, and from original Boruvka on the ordered
attachment family. For fixed density `d`, `m=nd`, so `log m` and `log n`
differ only by a constant. This compares KKT's upper bound with justified
comparator lower bounds, rather than merely comparing two upper bounds.
It is not a formal proof that every primitive in the current KKT executable
meets the theorem's assumptions; the
[implementation and work audit](../complexity-2026-10-10/README.md)
records that distinction.

These statements concern an ideal scalable algorithm with sufficient memory
and word size, not literal execution to infinity with fixed integer, edge
and stack limits. They compare expectations of logical work and their ratios,
not the expectation of a per-instance runtime ratio. They provide no finite
crossover location on this machine, no monotonic speedup, no guarantee for
every seed or every larger input, and no Prim lower bound.

The [retained measurements](README.md) remain authoritative for the tested
range, including every loss to the classical implementations. Contiguous
scans, efficient sorting, memory traffic and KKT's verifier and allocation
costs can dominate over that entire range. An asymptotic work separation does
not identify when, or whether within the machine's feasible inputs, those
costs will yield a practical crossover.
