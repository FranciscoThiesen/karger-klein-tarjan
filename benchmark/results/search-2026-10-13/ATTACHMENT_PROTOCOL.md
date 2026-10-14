# Extension: preserve edges while shrinking vertices

Declared 14 October 2026 UTC, while the original frozen lifted pilot is still
running. No attachment fixture has been built, executed or timed at declaration.
The first 15 completed lifted cases have no qualifying large-size advantage;
complete-bundle contraction removes most edges and often leaves KKT near the
compactor. The entire original 53-case plan will finish before this extension
is built. Their results will remain separate and intact.

## New question and exact controls

Can inexpensive vertex reduction leave an edge-rich, slowly merging core,
reducing KKT's vertex-related constants while preserving the repeated edge
scans that filtering can avoid? Does a sparse version also compete with
Kruskal, Prim and original Borůvka?

Use q=n/b core vertices, block size b=4 or 16, n-q cheap star edges, and
E=nd-n+q core edges. The core is a path plus uniformly proposed distinct
shortcut pairs. Every core edge expands to ONE original edge. Thus the first
ordered contraction retains E edges instead of E/b² for bundle lifting.
At d=2 it retains 62.5% (b=4) or 53.125% (b=16); at d=16, 95.3125% or
94.140625%. The exact capacity condition is q>=2b(d-1)+3. These are engineered
weighted families, not application datasets.

`leaf` external edges join star centers. `community` external edges select
each endpoint uniformly among that core vertex's clones. Independent RNG
streams preserve the same core pairs, weights, IDs, label permutation and
physical ID order across this endpoint ablation. With cheap local stars,
their first physical quotient is identical, although first-pass locality and
the classical solvers' traversals can differ.

Four weight modes exist for each endpoint mode and block size:

- `hierarchy`: cheap local stars; core path ranks increase by dyadic level,
  all shortcuts above the core tree. The MST is deliberately structured.
- `distance`: cheap local stars; all core ranks follow endpoint dyadic
  separation, shuffled within each tier. Shortcuts may enter the MST.
  These are rank-based hierarchy costs, not claimed Euclidean distances.
- `shuffled`: cheap local stars; independently shuffled ranks over ALL core
  edges. This isolates core ordering while preserving the first contraction.
- `random`: globally shuffled ranks over ALL original edges, including stars.
  This also removes the initial cheap-weight partition.

Within each endpoint mode and b,n,d,graph seed, all four weight variants share
original topology, IDs, labels and input order. Every solver receives only the
ordinary expanded edge list, never block metadata. No production solver or
comparator is changed.

## Frozen discovery matrix

`attachment-pilot.csv` contains 80 cases, shuffled with seed 202610141:

- Eight ordered families: leaf/community × hierarchy/distance × b=4/16,
  each at n=16,384,65,536,262,144,1,048,576 and d=2,16 (64 cases).
- Both shuffled-core and global-random controls for each endpoint mode and
  b at n=1,048,576 and both densities (16 cases).

Use discovery graph seed 5009 and sampling seed 149, as in the original
screens. These are not holdout samples. Maximum m is 16,777,216. Every case
gets all five solvers, one checked warmup and five fully rotated repetitions.
Retain all 2,000 timed outputs and 400 warmups, including every loss. All
measurement boundaries, clocks, correctness gates and resource rules follow
the [original protocol](PROTOCOL.md). Freeze and record the new binary/source
revision before execution; do not pool it with the earlier binary's cases.

Independent validation must precede timing: exact counts, ranks and topology;
all control pairings; full selected-ID and quotient-vector comparisons against
an independent contraction oracle; expected dyadic partitions for hierarchy
and distance; first-star partitions only for shuffled; all five solvers against
independently certified MSTs; a distance case whose MST uses core shortcuts;
and input-capacity guards. Check center/community counter equality in a
separate instrumented build. Counter runs and visualization exports occur
outside every timed campaign.

## Selection, confirmation and interpretation

The original three fresh graph seeds, two sampling seeds and two-campaign
confirmation rule remain unused and unchanged. Select at most two groups
from the combined exploration. Prefer a group potentially competitive with
all four comparators; otherwise rank by the strongest large-size compactor
advantage. Freeze exact selected sizes, controls and case orders in a later
note before any holdout seed is used. Intermediate or larger exploratory
points may be declared separately to bracket a crossing; preserve them all.

A clear advantage still requires paired medians <=0.90 at two adjacent
largest selected sizes in both campaigns, all graph medians <1, and matching
process-CPU direction/threshold. State separately which comparator passes.
An observed smaller-size loss is necessary to locate a crossover. An
all-winning sampled range, a single discovery graph, or a work-count argument
does not establish that onset or dominance at every larger size.

The balanced core model permits an expected quotient-edge-count calculation
that accounts for shortcut internalization and parallel-pair collisions.
Compare it with independent traces to explain the mechanism. It models ideal
uniform subset sampling; finite PRNG draws and elapsed time are separate
quantities. Larger b reduces verifier vertices but also makes the quotient
reach its simple-graph capacity sooner. Both effects must remain visible.
