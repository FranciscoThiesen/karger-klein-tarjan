# Searching beyond the dyadic hierarchy

Started 13 October 2026 UTC (12 October locally), following the
[confirmed hierarchy experiment](../continuation-2026-10-12/README.md).
This protocol is written before timing the new fixtures.

## Questions and fixed baseline

Does a crossover appear for globally random weights, or geometric costs on a
local network with long-range shortcuts, as the vertex count increases? Does
the contraction-input edge volume explain its direction? Neither production
solver changes. The comparator repeatedly calls the exact same `boruvka_step`
as KKT and returns the same reserved edge-ID set.

Geometric models are synthetic open paths/grids with uniformly proposed distinct
shortcut pairs. They are not road datasets, radius graphs or nearest-neighbor
random geometric graphs. All edge weights rank actual distances (with a fixed
tie rule) or a global random permutation; there is no explicit cheap backbone
weight class. A 1D distance MST is nevertheless forced to use adjacent points.
The 2D case tests a variable local MST. Random twins preserve coordinates,
topology, labels, IDs and input order. Exact definitions and structural tests
accompany the fixture source.

## Initial discovery

The shuffled `discovery.csv` has 19 cases: five families at n=262,144,
1,048,576 and 4,194,304 with m=16n, previous hierarchical-path and random-tree anchors,
and metric/random 2D shortcut controls at n=262,144,m=4n. The five families
are line metric/random, 2D grid-plus-shortcuts metric/random, and connected
G(n,m) with globally random ranks. G(n,m) samples uniform distinct unordered
pairs without a scaffold; reject the entire topology if disconnected, with a
bounded retry count. Density at least 16 keeps rejection practical in this size
range. Conditioning on connectivity is explicit. The anchors at n=1,048,576
retain the previous hierarchy and random-weight dyadic-tree topologies.
The shuffle uses seed
20261013. Existing fixtures retain their exact previous generation.

Use graph seed 3037, sampling seed 101, one checked warmup and two balanced
repetitions per algorithm. This is intentionally a **single-graph pilot** to
locate potential crossovers and measure resource cost, not confirmation. Retain
all 76 timed outputs and 38 warmups, including losses. Stop only for a failed
correctness check, resource failure or external interruption; preserve partial
captures. Any extension is dated and labeled exploratory before it runs.

At most one native measurement process runs at a time. Builds, tests, plotting
and instrumented work run outside timed campaigns. Largest initial input has
67,108,864 edges; do not exceed roughly 40 GiB observed process footprint or
cause sustained swap. A resource stop is not a successful measurement.

## Selecting and confirming a crossover

Select at most two new family/density groups with the strongest large-size
discovery results. A globally random weight model is a distinct family from
its distance twin. A crossover requires an observed smaller-size loss or tie
and a larger-size advantage; do not infer an onset from an all-winning range.
Freeze candidate groups, adjacent large sizes, controls and native binary
before using any confirmation seeds. An extra intermediate size may be screened
to bracket the crossing, with all such exploration retained.

Fresh graph seeds: 1000003,1000033,1000037. Fresh sampling seeds: 211,307.
Four balanced repetitions and one checked warmup. Run two complete campaigns,
the second in reverse case order, keeping them separate. Graph and sampling
seeds are reused in the repeat; it is not another independent graph sample.

A **clear advantage in the measured range** requires paired KKT/compactor
case medians at most 0.90 at the two adjacent largest selected sizes in BOTH
campaigns, and every graph-level median below 1. Require the same direction
and threshold for process-CPU diagnostic medians as a robustness check.
The result is descriptive, not a confidence interval, significance test or a
proof of dominance at every larger size. Near-ties and failures remain results.

Separately check promising cases against the unchanged public Kruskal, Prim
and original Borůvka implementations. This adjunct uses each public return
representation and the same tuple-input boundary as `diverse_benchmark`, with
four fully rotated repetitions and checked warmups. It does not replace the
compacting-Borůvka baseline or its frozen confirmation rule. One-graph adjunct
results are exploratory; a win only over compaction must not be called fastest
among all these algorithms. Freeze the adjunct source before the main pilot.

## Timing, sleep and correctness

Preserve the existing steady-clock solver interval: tuple conversion,
temporary-input destruction and output construction are included; reference
construction, certification, checking and returned-result destruction are not.
New per-call UTC and process-CPU readings enclose that interval and log every
warmup/timed call after validation. Their envelopes contain a little extra
clock-read overhead; process CPU is not substituted for elapsed time.

Validate the complete call schedule and one-to-one match of log/CSV durations.
Retain realtime reversals and large wall-versus-CPU gaps as descriptive flags.
No automatic removal, clipping or replacement is allowed. Audit power events
against per-call UTC intervals after each campaign. If a sleep intersects a
timed call, retain the whole campaign and label its power limitation. A new
complete campaign may be collected, labeled as such; it must not silently
replace the original or rescue a failed frozen two-run rule.

Each reference MST has an independent structure/connectivity/cycle certificate.
Every timed output, warmup and instrumented output must match the unique exact
MST IDs. Separately collected traces and work counters diagnose mechanisms;
their durations are not performance observations. Record source, binary,
manifest, runner and raw-output hashes and exact revisions before/after each
capture. Never compare models by silently pooling different build profiles.

## Public interpretation

The earlier astronomical crossover was an extrapolation from fitted runtimes,
not an algorithmic lower bound. New repository experiments can test that model
and document a correction, but cannot establish universal practicality or
independent published consensus. Literature and present empirical findings
will be identified separately. No Wikipedia edit is part of this experiment.
