# Direct-Edge density and core-weight-order search

## Prospective scope and fixed artifacts

This is a separate exploratory screen of denser leaf-attachment graphs. It is
prepared while the prior Edge/tuple timing campaign is still running; no timing
from this density screen exists at preparation. Its motivation is to test whether
KKT sampling and filtering become more useful as the reduced core has more edges,
and whether core weight ordering changes its competitiveness. A previously
observed gain from a contraction kernel is not evidence of a sampling advantage.

Reuse exactly the direct-Edge binary in the paired experiment's `freeze.json`:
parent SHA256 `f976a7d61650f5aaf8e7221c7684461e36bcb51492347f45a56497b6b1cee306`.
There is no rebuild, native source change, harness change or timing boundary
change. The parent strict checker must revalidate native source, recipes, all
production and harness object hashes, both paired build records, binary profiles
and all frozen runtime helpers. This study selects the exact parent `edge`
binary and its build proof. The new collector, this protocol and the new manifest
are separately hashed and frozen before capture. Earlier timing data is never
pooled into these observations.

## Eight fixed cases and matched controls

Use `leaf_hierarchy4` and `leaf_shuffled4`, each with density parameters 32 and 64
at 65,536 and 1,048,576 vertices, with zero intrusion. Here density is the
harness parameter `m/n`; these are not average degree values. The largest input
has 67,108,864 edges. Use exactly `manifest.csv` order: hierarchy/shuffled cases
are adjacent for each density and size. Each matched pair has the same topology,
edge IDs, labels and physical edge order; only core weight ranks differ. Both
families retain cheap leaf attachments. Shuffled core weights do not mean
independent random weights over all edges.

The collector must validate equal topology fingerprints and different weighted
input fingerprints for each hierarchy/shuffled pair at each graph seed, in
addition to the parent exact per-child MST certificate and result checks. This
prevents a missing or vacuous weight-order control from being accepted.

Graph seeds are **5000011 and 5000081**; starting KKT seed is **1217**. Reverse
the complete manifest case order for the second graph seed, which also reverses
the order of each matched family pair. Each child has one checked warmup and six
timed repetitions, balancing each solver once in every position. This gives
**16 children, 672 checked solver outputs, 576 timed calls and 96 warmups**.
The six repetitions are timings of the same graph and sampling realization,
not six independent random graph or KKT sampling draws.

All six solvers are mandatory: KKT, deduplicating compacting Boruvka,
retained-edge multigraph Boruvka, Kruskal, Prim and original Boruvka. The retained
multigraph control is central because it uses the same contraction kernel as
KKT; all other controls and all losses remain visible.

## Capture and resource gates

Preparation does not authorize capture. Root must first release nonperformance
validation after the prior timing run finishes. Complete the mocked full matrix
and negative tests and independent review, then freeze and commit the separate
study before explicit native release. No competing local builds, tests, plots
or counters may run during serial native timing.

Preserve every native command, raw child CSV, stderr certificate, process-group
RSS observation, clock endpoint, wrapper status and post-exit group observation.
Use the unchanged bounded monitor: sample about every two seconds, stop above
40 GiB sampled owned-group RSS, stop after three consecutive unavailable samples
or immediately on a poisoned sampler. Every normal child exit must be followed
by a bounded verified empty group before another launch. Unknown exit stops the
campaign; partial evidence is retained without silent replacement or recovery.
RSS is a sampled process-group sum, not a continuous peak or KKT-only allocation
measurement. The analysis rereads every raw file and hash and checks the exact
16-child/672-output matrix and exact combined-file concatenation.

No verified sleep-prevention claim exists. Retain all clock flags and correlate
a separately archived power log after capture. No timing is trimmed, replaced,
normalized with controls or adjusted for a power/clock event. The unchanged
power parser distinguishes actual Wake transitions from Wake Requests. An absent
logged overlap does not prove an awake or quiet host.

## Analysis and interpretation

Compare KKT directly with each of the other five solvers in the same native
child, graph and repetition, separately for wall and process CPU durations. The
primary case statistic is the median of all twelve paired trial ratios, with
each graph's six-trial median, individual ratios, ranges and absolute runtimes.
Publish all 960 clock-specific comparator pairs, 80 case medians and 160 graph
medians, retaining all five competitors. There is no normalization by control
timing and no pooling with the prior density-16 study for fitted curves.

A high-end strong lead requires each graph median at most **0.90** on both
clocks. An observed strong crossover bracket additionally requires each graph
median above one at the smaller measured size on both clocks. Comparisons must
use the same family, density and competitor. Report measured endpoint brackets,
not an interpolated threshold. Winning at both endpoints is a lead across the
measured range, not an observed crossover. Mixed or narrow wins remain
inconclusive. These two endpoint sizes cannot establish a durable crossover;
a promising result motivates a separately declared held-out/intermediate-size
confirmation. Do not change this screen or append cases in response to results.

This selected exploratory screen does not estimate asymptotic complexity, prove
linear running time, establish universal practical superiority, promote an
experimental path to production or justify a Wikipedia conclusion. Two graph
seeds and one sampling seed provide limited independent replication, and graph
seed is confounded with manifest-order reversal.
