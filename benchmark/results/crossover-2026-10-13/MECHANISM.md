# Seeking a crossover beyond the forced hierarchy

This is a mechanism and experiment-design note, written before the new pilot
results. It distinguishes mathematical properties of the fixtures from possible
runtime effects. The algorithms remain unchanged: KKT is compared with repeated
calls to the same production `boruvka_step`, including minimum parallel-edge
deduplication. A crossover against this implementation would not establish that
KKT is faster than Kruskal, Prim, or the best available MST implementation.
The two-algorithm pilot tests a continuation mechanism, not broad practical
dominance or a universal answer to the algorithm's large-constant reputation.

## What the previous experiment actually explains

The useful quantity is the sum of contraction-call input edges,
`V = sum_r m_r`, rather than the number of rounds alone. A path can take many
rounds while its edge counts halve, giving only linear total volume. The
engineered hierarchy kept a large uniform shortcut background alive as distinct
component pairs for several rounds. Its exact occupancy model and restrictions
are in the [previous derivation](../continuation-2026-10-12/MECHANISM.md).

The separately collected counters at `n=1,048,576`, `m=16n` show the following.
These are means over the archived discovery graphs and KKT sampling seeds,
not observations from the new pilot or the held-out timing seeds.

| Previous input | Compactor V/m | KKT contraction input/m | KKT edge materializations/m | Compactor edge materializations/m |
|---|---:|---:|---:|---:|
| Hierarchical path, no intrusion | 7.9536 | 3.4193 | 6.5183 | 8.3569 |
| Cheap path with shuffled path weights | 5.0889 | 3.1844 | 5.9899 | 5.4187 |
| Hierarchical path, 100 promoted chords per 1,000 vertices | 4.5372 | 3.2102 | 6.0491 | 4.7288 |

Source: [all prior work summaries](../continuation-2026-10-12/final-comparison/work_summary.csv).
An edge materialization counts a recorded construction or replacement; it is
not a measured byte transfer. KKT also performs sampling, isolation removal,
verification and recursive bookkeeping. Its smaller contraction volume therefore
does not by itself imply lower elapsed time. In the promoted case, shortcuts
numbering only about 0.625% of all input edges were moved into the cheap
backbone ordering, yet the compactor's volume fell substantially while KKT's
changed much less.

The earlier common-family traces offer useful negative controls. At 262,144
vertices, compactor `V/m` was 1.0825 for rings of cliques, 1.7712 for the local
3D distance grid, 3.1465 for the connected random graph with `m=4n`, and 3.2587
for the 8-regular fixture. The small-world fixture at 65,536 vertices had
`V/m=1.4739`. None produced a consistent graph-level KKT lead in both runs.
See the [complete ablation, including losses](../common-2026-10-11/diagnostics/ablation_analysis/report.md).
These different sizes and densities are examples of mechanisms, not a fitted
universal threshold for a win.

The KKT sampling lemma supplies the complementary mechanism: a sample retaining
each edge independently with probability `p` has an MSF for which the expected
number of F-light edges is at most `v/p`. With `p=1/2`, sampling can remove most
edges of a dense quotient without waiting for its vertices to merge. The
implementation must first construct and solve that sample and perform the
heavy-edge test, so this theorem does not supply a small practical constant.
[Karger, Klein and Tarjan, original paper](https://people.csail.mit.edu/karger/Papers/mst.pdf).

## The paired spatial fixtures

The [fixture header](../../crossover_fixtures.hpp) provides the four original
spatial families below, the later wide-gap line ablation, and a separate
connected random-graph control. Every graph is
connected, simple and undirected, with exactly `m=dn` edges and
unique integer weight ranks. Topology, geometry, weights, label permutation and
input order use separate deterministic random streams. The original metric/random twins
share every endpoint, edge ID, coordinate, label and input position; only
weight ranks change.

* `line_metric`: start at `x_0=0` and draw each consecutive positive gap
  uniformly from the integers 1 through 1,024. Include the path, then sample
  uniformly distinct non-path pairs until there are `dn` edges. Rank all edges
  by `(absolute coordinate distance, original edge ID)`.
* `line_random`: the identical line-and-shortcut topology, with a global random
  permutation of edge ranks.
* `grid2d_metric`: for `n=2^k`, use an open rectangular grid of width
  `2^ceil(k/2)` and height `2^floor(k/2)`. Each original point `(x,y)` becomes
  `(1024x+j_x,1024y+j_y)`, with independent integer jitters in `[-200,200]`.
  Include horizontal and vertical nearest lattice neighbors, then uniformly
  sample distinct non-scaffold pairs to reach `dn` edges. Rank by
  `(exact squared Euclidean length, original edge ID)`.
* `grid2d_random`: the identical grid-and-shortcut topology, with globally
  randomized ranks.

The grid scaffold contains `2n−width−height` edges. The line scaffold contains
`n−1`. The integer ranks preserve the ordering of geometric distances with
deterministic tie-breaking; the stored ranks are not themselves claimed to
satisfy the triangle inequality. The grid model is a jittered lattice with
uniform global shortcuts, not a radius random geometric graph, a k-nearest
neighbor graph, or a measured road network. At `d=16`, roughly seven eighths
of its edges are added shortcuts. That is a deliberate stress on local
contraction, not a claim about the edge distribution of typical spatial data.

### The line MST is forced, although its merge schedule is not dyadic

For `u<v`, the geometric shortcut length is the sum of positive gaps between
them. If it skips at least one intermediate vertex, it is strictly larger than
every edge on the corresponding path segment. It is therefore the unique
heaviest edge of that cycle and cannot belong to the MST. All consecutive path
edges form the unique MST.

Inductively, every Borůvka component is an interval. For any shortcut leaving
that interval, the path to its other endpoint crosses an adjacent boundary gap
that is strictly cheaper than the shortcut. Consequently every minimum outgoing
edge is an adjacent gap, and the contraction partitions are exactly those of
the weighted path alone. Shortcut draws do not affect these partitions.

This is a geometric realization of the cheap-path mechanism, not a removal of
the planted-MST limitation. Unlike the hierarchy, random gap order does not
force each component to merge with exactly one equal-sized sibling. In an ideal
path with iid continuous gap weights, the expected first-round number of
components is `n/3` for `n>=3`: the two end edges are mutual minima with
probability 1/2, and each other edge with probability 1/3. The implementation's
finite integer gaps and ID tie-break require their own trace; later rounds also
have correlated boundary weights and are not iid redraws.

### A finite gap alphabet limits this line model's continuation

The current metric line has a further structural restriction: its gaps belong
to the fixed alphabet `{1,...,K}`, with `K=1024`. Path edge `(i−1,i)` is inserted
with original ID `i−1`, before any shortcut. Sorting by `(distance,original ID)`
therefore orders equal path gaps from left to right. Subsequent vertex-label
and input-order shuffles do not alter that weight order. The public integer
weight ranks remain distinct; this restriction is not an ambiguity between
equal-cost MSTs.

Every contraction component is an interval, as proved above. Consider the
smallest raw gap still present among its path boundaries. In any consecutive
block of boundaries with that raw gap, the component immediately to the right
of each boundary selects that boundary: its alternative on the right either
has a larger raw gap or the same gap with a larger original ID. All boundaries
of the currently smallest raw-gap value disappear in this round. Shortcuts
cannot change this choice because every shortcut is more expensive than the
path boundary it crosses. Thus each round eliminates at least one distinct
remaining gap value, and the whole compaction finishes within `K` rounds. The
usual vertex-halving argument also applies, giving at most
`min(K,floor(log2(n)))` rounds for `n>=2`.

Writing `V=sum_r m_r`, no quotient contains more edges than the original, so
`V<=Km`. Vertex halving gives `sum_r n_r<=2n`; consequently the repeated
contraction scanning/materialization work is `O(Km+n)` in the unit-cost RAM
model. The current contraction uses deterministic endpoint bucketing, rather
than a hash table; final ID-set output construction separately assumes
constant-cost hashing on average. These counts do not model allocation or
cache latency. For **fixed** `K=1024`, this family has a linear
contraction-work bound in its input size. It cannot establish an asymptotic
logarithmic disadvantage for compaction, although the two implementations can
still cross in practical elapsed time. Once only equal maximum-gap boundaries
remain, their monotone rank order merges the entire remainder in one round.
Many such boundaries may already have disappeared in earlier rounds, so this
proof alone does not locate the event or quantify its edge-volume cost.

At 8,388,608 vertices, the ordinary bound is 23 rounds, much smaller than 1024.
The alphabet bound alone therefore does not explain a measured plateau or a
particular number of rounds at that size. The completed per-round diagnostics
below distinguish the observed late merge from the bulk of edge-volume work.

The separately declared [precision ablation](PRECISION_ABLATION.md) has now
completed after the extension screen. Its new, retained `line_wide_metric`
fixture draws positive gaps uniformly from `{1,...,2^32}` while preserving
the same topology, IDs, label permutation and edge order through separate
random streams. At the current 8M size limit the largest possible coordinate
is `(2^23−1)·2^32 < 2^55`, so absolute distances fit safely in signed 64-bit
arithmetic; there is no need to square line distances. The wider alphabet
still permits equal gaps and retains the forced-path-MST limitation. It is
also a fixed-alphabet model asymptotically. All original narrow-line results,
including unfavorable observations, remain retained.

The completed wide-line screen uses graph seed 3037, sampling seed 101 and two
timed repetitions per solver at each size. Its paired KKT/compactor elapsed-time
ratios are:

| Vertices, `m=16n` | Paired elapsed-time ratio |
|---|---:|
| 262,144 | 0.9824 |
| 1,048,576 | 0.8955 |
| 4,194,304 | 0.9339 |
| 8,388,608 | 0.9642 |

The [case summaries](all-screens-comparison/wall_case_summary.csv) and
[individual pairs](all-screens-comparison/wall_paired_pairs.csv) retain the
other screens and both repetitions, with campaign identity preserved. The
wide-line lead is not monotonic, and it is already present at the smallest
measured size, so these points do not locate a crossover onset. No new family
was [selected for fresh-seed confirmation](SELECTION_DECISION.md).

The [validated gap diagnostics](GAP_FINDINGS.md) now match all 47 production
rounds across four narrow/wide line graphs, with 51 states including the initial
ones. Narrow gaps do cause a late rapid collapse: the one-million graph reaches
42 components with all 41 boundary gaps equal to 1,024, then finishes. At eight
million it goes from 300 components, with 298 of 299 gaps equal to 1,024, to two
components and then one. Yet all edge inputs from stage 8 onward account for
less than 0.093% of each graph's total compactor volume, including the longer
wide-gap tails. Total narrow/wide `V/m` is 5.080535/5.085271 at one million and
5.926172/5.958874 at eight million: wide gaps increase total volume by only
0.0932% and 0.5518%, respectively. Most of those small differences arise before
stage 8. The terminal event cannot explain the bulk edge-volume cost.

These findings do not isolate a tie-based runtime mechanism. Widening the gaps
changes the order of unequal gaps and the geometry as well as tie frequency;
both alphabets also remain fixed asymptotically. The checks establish component
statistics and structural work, not the cause of wall-time differences between
separately captured campaigns.
The existing `low_path` control, with a uniform permutation of distinct cheap
backbone ranks, is another useful path-order sanity check; it is a separate
fixture, not an assumed byte-identical geometric input.

### The grid MST varies, but nearly all global shortcuts are still heavy

The grid contains cycles, so its MST is not a predetermined list of scaffold
edge IDs. There is nonetheless a strong geometric restriction. Every scaffold
edge has squared length at most

`1424² + 400² = 2,187,776`.

Any pair whose original lattice coordinates differ by at least two in either
axis has length at least `2048−400=1648`, exceeding every scaffold edge. Its
cycle with any scaffold path excludes it from the MST. Thus only shortcuts
between diagonally neighboring lattice cells can potentially change the
scaffold MST. There are exactly `D=2(width−1)(height−1)` such non-scaffold pairs.
Writing `c=2n−width−height`, `B=dn−c` and `U=C(n,2)−c`, the expected number of
sampled diagonal shortcuts is exactly `BD/U`, asymptotically `4(d−2)` at fixed
`d>2`. Not every sampled diagonal belongs to the MST.

This gives the grid experiment a precise interpretation: a variable local MST
with many long edges that are expensive for geometric reasons. At fixed
density, only a vanishing fraction of the shortcuts can change that local MST.
It is a useful relaxation of a forced tree and forced dyadic schedule, but it
still favors a light connected core over a global background.

## Unequal component sizes: a conditional occupancy model

Consider a connected scaffold `C` with `c` edges and `B` uniform shortcuts drawn
without replacement from its `U=C(n,2)−c` missing pairs. Suppose the contraction
partition is determined independently of those shortcut draws. Let its
components have original sizes `a_1,...,a_q`, and let `H` be the set of distinct
component pairs already joined by a scaffold edge.

Every pair in `H` survives. For any other pair `(i,j)`, all `a_i a_j` original
pairs are eligible shortcut slots. Linearity of expectation gives the exact
conditional formula

\[
\mathbb E[m_r\mid C,\{C_i\}]
=|H|+\sum_{\substack{i<j\\(i,j)\notin H}}
\left(1-\frac{\binom{U-a_i a_j}{B}}{\binom UB}\right).
\]

Use a zero numerator when there are insufficient remaining slots. No
independence between different component-pair occupancy events is required.
For the metric line, partitions depend only on gaps, so this conditioning is
valid. It is also valid for a separately specified cheap connected scaffold
with every shortcut assigned a heavier priority. It is **not automatically
valid** for globally random weights: then the very shortcuts being modeled help
choose the partition. The metric grid can also select diagonal shortcuts, so
the formula is not an exact theorem for that fixture's observed partition.
An independent held-out set of edges could test conditional occupancy without
this dependence; those edges would be a diagnostic, not extra solver input.

The equal-sized hierarchy is the special case `a_i=n/q`. Unequal sizes matter.
Define the effective component count

\[
q_{\mathrm{eff}}=\frac{n^2}{\sum_i a_i^2}\le q.
\]

For an idealized unrestricted uniform endpoint pair, the probability that both
endpoints fall in one component is approximately `1/q_eff`. The component-pair
probability is approximately `2a_i a_j/n²`; the sum of its squares is

\[
\frac{2[(\sum_i a_i^2)^2-\sum_i a_i^4]}{n^4}
\le \frac{2}{q_{\mathrm{eff}}^2}.
\]

Consequently, a birthday-collision estimate for `B` independent background
edges has relative duplicate loss of order at most `B/q_eff²`, before accounting
for scaffold slots and sampling without replacement. For reasonably balanced
components, appreciable deduplication begins around `q_eff≈sqrt(B)`. This is a
diagnostic approximation, not an equality or general lower bound: a dominant
component can invalidate the balanced-occupancy picture. It explains why raw
component count alone can conceal rapid collapse caused by large components.

If components grow by a roughly constant factor `a>1` per round while remaining
balanced, the background plateau lasts about `log_a(n/sqrt(B))` rounds. This
suggests logarithmically increasing normalized volume at fixed density, but
does not prove that actual random-weight or geometric partitions satisfy those
conditions. Recording original-size second moments, maximum component size and
per-round input/output edges would test the premise directly.

## Why ordinary random and local graphs can behave differently

There is an exact first-round identity for any fixed simple graph with iid
continuous weights and no isolated vertices. Each selected-edge component has
one edge chosen by both endpoints. Edge `(u,v)` has this property precisely
when it is minimum among the `deg(u)+deg(v)−1` incident edges. Therefore the
expected number of selected components is

\[
\sum_{\{u,v\}\in E}\frac{1}{\deg(u)+\deg(v)-1}.
\]

For a `D`-regular graph this is `nD/[2(2D−1)]`, approximately `n/4` at high
degree, versus `n/2` for the forced hierarchy. The terminal one-component case
is subsequently represented by an empty graph in this implementation. This
identity is for the first selected forest; quotient weights and topology become
correlated, so repeatedly substituting `n/4` is not a theorem.

Pure locality often leaves much less repeated work to eliminate. A planar
simple graph remains planar after contraction and parallel-edge removal.
Its quotient has at most `3q−6` edges when `q>=3`; because the vertex count at
least halves, the sum of quotient edge counts is `O(n)`. Thus an ordinary
planar grid has no logarithmic edge-volume disadvantage for KKT to exploit.
Three-dimensional geometric graphs are not covered by that planar argument,
but the previous local 3D fixture also shrank its edge volume rapidly.

The earlier small-world model has only a modest global shortcut fraction and
iid weights: local edges disappear quickly, and light global edges can merge
far-apart regions early. Raising the global edge budget and correlating cost
with physical length is a different hypothesis. The new paired grid separates
this weight effect from topology; it does not characterize all small-world
models. A later multiscale test could distribute shortcuts across logarithmic
distance bands and vary overlap of their cost distributions. Such a test should
retain the same topology while shuffling weights, and avoid assuming that a
community label by itself forces slow contraction.

## Bounded next decisions and literature context

The 19-case pilot covers the four spatial families and `gnm_random` at
`n={262144,1048576,4194304}`, `d=16`, plus one-million-vertex `hierarchical_path`
and `random_tree` anchors and the grid pair at `n=262144,d=4`.
The `gnm_random` control draws a uniform subset of `m` distinct unordered pairs
without a scaffold, rejecting the entire topology and redrawing if disconnected.
It therefore represents `G(n,m)` conditioned on connectivity, with globally
randomized weight ranks. The generator requires `d>=16` and has a bounded retry
limit; exhausting that limit fails generation rather than silently connecting or
replacing the graph. As elsewhere, uniform sampling describes the random model
implemented using deterministic seeded pseudorandom streams.

The retained `random_tree` anchor means the existing tree scaffold joining
dyadic half-blocks through random endpoints, plus uniform shortcuts and globally
randomized weights; it is not a bare tree or an exact `G(n,m)` draw. Keeping it
separate avoids confusing a change of graph model with a change of size.
The pilot has one graph seed, one KKT seed and balanced algorithm order.
It is a screening experiment,
not confirmation. All cases, losses, setup costs and resource limits belong in
the accompanying protocol; promising cases require fresh graph/sampling seeds
and separately reported confirmation rather than pooled best runs.

A selected family also needs a separately labeled comparison with the existing
classical baselines under the same input and timing boundary before claiming
practical leadership. Historical measurements make this a substantive issue:
the earlier random-32 fixture at 1,048,576 vertices and 33,554,432 edges took
about 2.385 seconds with Kruskal and 10.014 seconds with KKT, using that
campaign's aggregation. These are different graphs and an earlier campaign,
so they are not substituted for measurements of the new fixtures or scaled into
an exact prediction. See the [archived four-algorithm summary](../practical-2026-10-10/large_analysis/summary.csv).
Reference-construction-plus-certification setup times cannot supply this
comparison because they do not isolate the Kruskal solver interval.

The previous one-million-vertex globally randomized tree twin was already near
a tie in both held-out runs (ratios 1.0030 and 1.0059). The randomized path twin
lost narrowly (1.0290 and 1.0315); the cheap shuffled path led modestly (0.9554
and 0.9640). These motivate larger fixed-density probes, but the previous
campaign's desktop-sleep and clock limitations still apply to those observations.
They are not extrapolated crossover guarantees. See the
[retained prior results and clock caveat](../continuation-2026-10-12/README.md).

Filtering is a broader engineering idea than this KKT implementation. The
primary [Filter-Kruskal paper](https://ae.iti.kit.edu/documents/teaching/algorithm-engineering/ss22/fkruskal.pdf)
studies random weights and geometric nearest-neighbor inputs, and explicitly
accounts for representation conversion. The more recent
[Engineering Massively Parallel MST Algorithms](https://arxiv.org/abs/2302.12199)
finds filtering useful for poor-locality/high-degree graphs, while exploiting
local contraction on spatially local graphs. Its distributed communication
costs and different filtering algorithm do not predict the constants of this
single-process implementation. These papers support testing locality and
weight correlation separately, not importing a published speedup.

Finally, a close match between an occupancy model and observed edge counts
would establish a structural explanation, not a hardware explanation. No
per-solver cache, bandwidth or allocation measurements are available here.
Whole-process counters include setup, certificates and both algorithms.
Changes in seconds per recorded edge can reflect memory layout, access order,
allocation, working-set size or machine conditions; none should be identified
as the cause from total elapsed time alone.
