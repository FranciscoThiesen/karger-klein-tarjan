# How sampling can disrupt the hierarchy without resembling the true MST

Source-derived mathematics, prepared 2026-10-15 during the larger-hierarchy
performance hold. No imports, tests, native runs, plots or partial timing
inspection were performed for this note. Its exact identities use the ideal
independent Bernoulli sampling model; finite seeded `mt19937` executions are
deterministic realizations, not a proof of that model. The nominal rate here
is **p = 1/2**. This note does not change any active study or sampling policy.

The key distinction is between finding the true MST immediately and obtaining
a forest that can certify many edges as too heavy. KKT needs the second from
its sampled subproblem. A sampled forest containing many chords outside the
true MST can still discard almost all of a dense parent graph.

## The exact quotient being discussed

Use `leaf_hierarchy4`, with `n` original vertices and no intrusions. The source
first creates `n/4` core vertices, each with three cheap leaves. It inserts the
entire core path and assigns its edges increasing hierarchy tiers; every
nonpath core chord is above every path tier. All final weights are distinct
ranks. Label and record-order shuffles do not change these facts.

After the first full Borůvka step each star becomes one core vertex. After the
second, adjacent pairs of core vertices merge. Write

```
q = n/8                 surviving quotient vertices
r = m - 7n/8           surviving edge records
```

The quotient has exactly `q−1` cheap edges forming a path, plus high chords.
None of the original nonpath chords can be internal to a two-core-vertex
block, whose only possible pair is the excluded path pair. Thus no chord is
deleted in that second full step. Different original chords may now have the
same quotient endpoints; **count every parallel record**. Contraction deletes
loops, and sampling below concerns this loop-free quotient. The hierarchy's
supported powers of two make these block counts exact.

All path edges are below all chords, so the unique MST `T` of this quotient
is precisely its cheap path. These are quotient-level statements, not a claim
that the original graph consists of only `q` vertices. The implementation can
remove isolated sampled vertices; the derivation keeps the original quotient
universe of all `q` vertices when counting components.

## Missing cheap edges create many path components

Independently include each quotient record with probability `p`, obtaining
the sampled graph `H`. Let:

- `S` be the number of sampled cheap path edges;
- `c_H` be the number of connected components of `H`, including isolated
  vertices in the full `q`-vertex universe;
- `F` be the exact minimum spanning forest of `H`;
- `C_F` be the number of high chords in `F`.

The sampled cheap path alone is a forest. Removing a path edge raises its
component count by one, so its component count is **exactly `q−S`**. In the
ideal model,

\[
S\sim\operatorname{Binomial}(q-1,p),\qquad
\mathbb E[q-S]=q-p(q-1).
\]

At half sampling, its expected component count is `(q+1)/2`. This is the
cheap-path subgraph's component count, **not** the full sampled graph's
component count: sampled chords may join those pieces.

Every sampled cheap path edge belongs to `F`. To see this, process sampled
edges by increasing weight. All sampled path edges occur before any chord,
and any subset of a path is acyclic, so all `S` are accepted. Since every
spanning forest of `H` has `q−c_H` edges,

\[
\boxed{C_F=q-c_H-S},\qquad
\boxed{\mathbb E[C_F]=q-\mathbb E[c_H]-p(q-1)}.
\]

The sampled forest does not need to approximate the true path edge for edge.
For any **connected realization** of `H`, it has
`C_F=q−1−S` non-original-MST chords. A realization that retains about half the
path edges and is connected consequently uses about half a tree's worth of
chords to reconnect them. More generally, if `E[c_H]` is small compared with
`q`, the displayed expectation is close to `(1−p)q`. This note does not prove
that the generated sampled graphs are connected, have a giant component,
or have small `E[c_H]`.

There is a conditioning trap here: in general
`E[S | H connected]` is **not** `p(q−1)`. Connectivity depends on both the path
and chord samples. Thus the exact conditional identity is

\[
\mathbb E[C_F\mid H\text{ connected}]
=q-1-\mathbb E[S\mid H\text{ connected}],
\]

not automatically `(1−p)(q−1)`. The simple “about half” explanation applies
when the realization also has a near-half path count, or under an explicitly
justified further assumption; it is not an unconditional connectivity claim.

## A forest far from the MST can still filter effectively

An edge is `F`-heavy when its endpoints have an `F`-path whose maximum weight
is strictly smaller than the edge. Edges with no such path remain light.
All original MST edges remain `F`-light. For a path edge `e`, remove `e` from
`T`: every other edge crossing that cut is a higher chord. If `F` contains
`e`, its path maximum equals its weight. If not, any `F`-path between its
endpoints uses a higher chord, or there is no path. Neither case makes `e`
heavy. Thus filtering always retains all `q−1` true path edges.

Let `Y` count all `F`-light records, including parallel records and sampled
forest edges. The usual sampling lemma has the following exact expectation
identity in this distinct-weight setting:

\[
\boxed{p\,\mathbb E[Y]=q-\mathbb E[c_H]},\qquad
\mathbb E[Y]\le \frac{q-1}{p}\le\frac q p.
\]

A short proof also explains why resembling `T` is unnecessary. Expose sample
bits in increasing edge-weight order. Let `L_e` indicate that the endpoints
of `e` are disconnected by the already sampled cheaper edges. This depends
only on earlier sample bits, and `e` is finally `F`-light exactly when `L_e=1`.
The independent current bit `I_e` decides whether that light edge enters
the sampled MSF. Consequently

\[
p\,\mathbb E[Y]
=\mathbb E\!\left[\sum_e L_e I_e\right]
=\mathbb E[|F|]
=q-\mathbb E[c_H].
\]

This includes disconnected `H`; no path between components means light, not
heavy. It also includes distinct parallel edges: later heavier parallel
records can be certified by an earlier connection. Unique weights make the
sampled MSF well defined, independent of the recursive random choices used
to compute it correctly.

Combining the two boxed identities gives another useful interpretation:

\[
\boxed{\mathbb E[Y-(q-1)]=\frac{\mathbb E[C_F]}p}.
\]

The left side counts surviving **chords**, because every true path edge is
retained. At `p=1/2`, the expected number of surviving chords is twice the
expected number of chords accepted into the sampled MSF, and at most `q−1`.
There may be many wrong-tree chords in `F`, yet the entire filtered graph has
only about a tree or two's edge count in expectation. These are expectation
identities, not equalities for each realized filtered graph.

For the source-declared `d=m/n=32` root quotient, `r=249q`. Therefore half
sampling gives

\[
\frac{\mathbb E[Y]}r
\le\frac{2(q-1)}{249q}
<\frac2{249}\approx0.00803213.
\]

That is an expected retained fraction below **0.804% of quotient records**
(the limiting value is about 0.8032%), despite the sampled forest potentially
using many chords outside `T`. It is a theoretical upper bound under ideal
sampling, not a measured pruning ratio, a probability guarantee, or a runtime
speedup. Obtaining `F` and checking the parent still cost work; the private
half sample itself has expected `r/2` records, much larger than `F`.

## A small constructed witness, not a benchmark

Take eight quotient vertices and the following path-edge weights, preserving
the hierarchy order:

```
vertex:    0 --- 1 --- 2 --- 3 --- 4 --- 5 --- 6 --- 7
weight:       1     5     2     7     3     6     4
sample:      keep  omit  keep  omit  keep  omit  keep
```

Add all nonpath pairs as chords. Give `(0,2)`, `(2,4)`, `(4,6)` weights 8, 9,
10 respectively and every other chord a distinct weight from 11 through 28.
Consider the possible sample containing just the four marked cheap edges
and those three chords. `H=F` is a connected seven-edge tree: three of its
seven edges are absent from the original unique MST.

Nevertheless, all 18 chords with weights 11 through 28 are `F`-heavy, since
every `F`-path has maximum at most 10. The seven true path edges and the three
selected chords remain light: filtering keeps 10 of 28 records and preserves
the unique MST exactly. This hand-constructed sample illustrates the logical
mechanism; it is not a typicality estimate or a measured family result.

It also gives a concrete example of possible round disruption. Full-graph
Borůvka first pairs the eight vertices, then pairs those four blocks, then
merges the last two: three rounds. On the displayed sample the first round
still forms four pairs, but the three remaining chords have increasing
weights 8, 9, 10 along the pair chain. The left pair chooses 8, the next also
chooses 8, the third chooses 9 and the fourth chooses 10. Their union connects
all four blocks in that second round. This proves that missing hierarchy
links **can** defeat the exact two-at-a-time pattern. It does not establish
the expected sampled round count or a CPU advantage.

## Why the dyadic proof stops applying, and where it still applies

On the full hierarchy quotient, each aligned block has its lower-tier
boundary to its sibling present. That boundary is below every competing
outside edge. This forces the repeated doubling partition and causes many
high chords to be rescanned by retained-edge Borůvka.

Sampling can delete a block's required cheap boundary. Its selected minimum
may then be a different cheap boundary or a high chord. The original
fixed-partition induction no longer applies to that sampled graph. Larger or
irregular merged components are possible, as the witness shows. Faster
shrinkage is a **mechanism hypothesis** for a particular observed sampled
continuation; it needs matched traces to establish frequency or relevance.
No random-giant-component theorem, logarithmic-round improvement, cache model
or CPU-time conclusion follows from the component-count identities alone.

Conversely, the filtered parent retains **every** original cheap path edge.
Its chords remain higher, so the full dyadic merge proof still applies to
that filtered graph. Filtering does not break that graph's weight hierarchy;
its guaranteed advantage is a much smaller expected edge set to process.
The sampled branch can lose forced boundaries while the filtered branch
keeps them. These are distinct mechanisms and should not be conflated.

## Why `leaf_distance4` needs a separate explanation

In `leaf_distance4`, every core edge, including chords, is ranked by
`floor(log2(u xor v))`, with distinct randomized order within each tier. This
is not the hierarchy generator's “all chords last” rule. Lower-tier chords
can connect vertices within a hierarchical region after a path link is
missing, rather than forcing a connection through a globally high chord.
The sampled forest and contraction partitions can consequently differ in a
different way; there is no timing prediction here.

For clarity, this comparison is at the first post-two-full-contraction
quotient in both families. `leaf_distance4` also first collapses the cheap
stars, then contracts the tier-zero core pairs: each such two-vertex pair's
only possible edge is its forced path edge. Thus it too has `q=n/8` vertices
and `q−1` remaining path edges at this point, but lacks the hierarchy family's
global separation of all path weights below all chord weights.

The sampled path alone still has `q−S` components, but sampled path edges
need not all belong to `F`, and the original full MST need not be the path:
a cheaper within-tier chord can be accepted before a path edge that would
close a cycle. Thus the special `C_F=q−c_H−S` identity and all-path-survival
argument must **not** be transferred to this family. The general sampling
identity for `Y`, and survival of the actual unique MST's edges, still hold.
These are order-based generators, not a claim that final rank weights are
metric distances.

## What would connect this explanation to an implementation result

The existing counter studies can report cumulative sampled-edge volume,
sampled-forest size/components, verifier input and survivor volume. Their
cumulative fields are not a root sampled-path/chord trace. Attribution would
need a separately authorized untimed observation on the exact same graph and
sampling realization, retaining original core-block/edge identities and the
sampled and filtered branches' partitions. Keep every declared family and
control, certificates and losses. Do not pool historical timings, compare
unmatched sample realizations, or infer branch round traces from cumulative
counts. Such observation must run after performance and cannot change the
frozen timed implementation.

The following source notes provide the existing context, without new timing
claims from this preparation:

- [Fixed sampling probabilities and the finite sampling-lemma proof](/Users/random_person/Desktop/kkt-compressed-queries/docs/kkt-report/FIXED_SAMPLING_PROBABILITY.md),
  which cites the [Karger–Klein–Tarjan paper, Lemma 1](https://people.csail.mit.edu/karger/Papers/mst.pdf).
- [Exact hierarchy retention and repeated chord scans](/Users/random_person/Desktop/kkt-compressed-queries/benchmark/results/density-search-2026-10-15/HIERARCHY_RETENTION.md).
- [Generator source](/Users/random_person/Desktop/kkt-compressed-queries/benchmark/core_attachment_fixtures.hpp):
  forced path/tier assignment, original single-edge core pairs, cheap leaves,
  and independent label/order shuffles.

No new analytic plot has been rendered. A later schematic may show the
eight-vertex witness and an analytic curve `E[Y] <= (q−1)/p`, clearly labeled
as a bound rather than observations. Any observed curve belongs in a
separately validated figure with its own raw provenance.

Independent source review by `/root/multigraph_candidate` passed on
2026-10-15: the three expectation identities, conditioning/disconnected
universe caveats, complete toy-edge accounting and 3-to-2 round witness were
checked, along with the source-based distance-tier distinction. The reviewer
performed no imports, tests, runtime calculations or timing reads. This is
a mathematical/source assessment, not an executable or performance result.
