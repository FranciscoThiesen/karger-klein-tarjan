# Prospective lower-density distance/shuffled crossover study

Source declaration, 2026-10-15. This new matrix is fixed before its own results.
It follows the completed density-32 eighth-policy distance study and is an
evidence-led search, not an unbiased family survey. This document authorizes no
execution. Imports, tests, preflight, freeze and capture await explicit release;
no native implementation or generator changes are included.

## Fixed inputs, order and artifact

The exact 30-case [manifest](manifest.csv) contains both `leaf_distance4` and
`leaf_shuffled4`, intrusion zero, in these two separate ladders:

| m/n | Vertex counts n, in declared ascending order |
|---|---|
| 16 | 512; 2,048; 8,192; 32,768; 131,072; 524,288; 2,097,152 |
| 8 | 256; 1,024; 4,096; 16,384; 65,536; 262,144; 1,048,576; 4,194,304 |

Graph seeds are **23000003 and 23000029**; the one scalar private KKT sampler
seed is **3407**. [Seed checks](SEED_FRESHNESS.md) record the prospective source
and archived certificate-declaration search. Graph one follows the manifest:
density 16 then density 8, ascending n and adjacent distance/shuffled twins.
Graph two reverses that entire order, including densities and twin order.
Graph identity, order and host history remain confounded; no normalization can
remove that limitation. Unequal ladders are deliberate, and densities are never
pooled into a size curve or a crossover classification.

Use only the existing `eighth` artifact in
`/Users/random_person/Desktop/kkt-eighth-sampling`:

- Parent freeze: `benchmark/results/eighth-sampling-2026-10-15/freeze.json`.
- Parent freeze SHA-256: `2be7556d15b58f3f65cc380ac22b67c57fdf8aea747d651b9d648c6a1aa59d2f`.
- Binary: `bin/eighth-sampling/timing-build/eighth/retention_control`.
- Binary SHA-256: `954068775a83e1c42db62ffb6777c398dc05fd5792c60d2f293df6532130951a`.

The new collector invokes the unchanged parent's complete freeze checker,
including both parent variants and all ancestor source, overlay, recipe,
compiler/SDK/flags, object, binary and arm64/512-MiB-stack evidence. It adds only
its own source, protocol, manifest and schedule. No temporary override of
parent seed globals, incomplete parent proof, rebuild, source-domain extension
or change to the timed harness is allowed. Private sampling remains
`(rng() & 7) == 7`, one engine word per visited edge; compressed queries and the
existing reserve policy remain unchanged.

## Supported domain and graph meaning

The frozen attachment generator accepts powers of two from 32 through
4,194,304, and up to 134,217,728 edges below its integer weight ceiling. With
four-vertex cheap stars, q=n/4 core vertices contribute 3q local edges and
core_m=(4d−3)q, where d=m/n. Connectivity requires core_m≥q−1, and the simple
core limit requires q≥8d−5, equivalently n≥32d−20. Both minima satisfy this:

| d | n | q | core_m | possible core pairs | occupancy |
|---|---:|---:|---:|---:|---:|
| 16 | 512 | 128 | 7,808 | 8,128 | 122/127 |
| 8 | 256 | 64 | 1,856 | 2,016 | 58/63 |

Every later declared n has more simple-core capacity relative to its fixed
average core degree (122 or 58). The largest case in each ladder has exactly
33,554,432 edges. Both native CLI and Python manifest checks already admit all
these inputs. This is source reasoning, not a native generator or memory test.
The smallest cores are nearly complete; relative occupancy decreases at fixed
m/n as n grows. This is a finite-size feature of each valid fixed-parameter
family, not a change of density within a curve. The experiment does not isolate
asymptotic effects from cache or occupancy effects. At fixed d, the represented
input size is N=n+m=(d+1)n.

Distance ranks order all core edges by floor(log2(u xor v)), randomized
distinctly within each tier; the forced core path supplies sibling-cut edges.
The full-graph contraction sequence merges dyadic sibling blocks. The shuffled
twin randomizes core ranks while retaining cheap leaves. Both twins share
topology, labels, original IDs, tuple order and the weight multiset. Require
equal topology/order fingerprints and different weighted fingerprints for all
**30 density/size/graph twin pairs**. These are engineered hierarchical rank
weights, not Euclidean distances or a triangle-inequality claim. This study
cannot isolate the effect of sampling probability or establish graph-family
prevalence in applications.

## Complete comparisons and failure handling

Every child runs KKT, compacting Borůvka, retained-edge multigraph Borůvka,
Kruskal, Prim and original Borůvka, using the unchanged wrapper and timer
boundaries. One certified warmup plus six certified timed calls per solver
rotate every solver through every position. The fixed **60 children produce
2,520 outputs: 2,160 timed and 360 warmups**. There are two graph realizations
and one sampler seed, not twelve independent random forests per case.

Quiet serial capture requires prospective source review, mocked gates, a source
commit, freeze and separate root release. Preserve the inherited **40 GiB
sampled process-group RSS ceiling**, bounded observations after waits of at
most about two seconds, poisoned-sampler stop, three-unavailable stop and
bounded TERM/KILL cleanup. RSS is sampled, not a continuous maximum. The
unchanged child loop has no total wall deadline. The separate outer wrapper
declares a **54,000-second complete-interval ceiling**, including cleanup,
strict reload and log hashing; it is neither a runtime prediction nor a child
deadline. It is fixed before results and does not relax the memory ceiling.

Keep every command, certificate, raw CSV, time log, RSS observation, clock
endpoint, exit and flag. Verify each owned native group empty before another
launch. On failure stop, retain evidence, mark uncertain exit before cleanup,
suppress repeated SIGTERM only during bounded cleanup, restore handlers and
clear uncertainty only on affirmative exit/empty proof. No failed case is
silently retried, substituted, dropped or reused in a later complete attempt.
Strict reload checks all 60 identities, 42 solver rows per child, exact combined
CSV concatenation and full proof. Clock or power flags never remove or adjust
observations. Any private power log needs an ignore rule before capture; no
successful caffeinate or verified sleep inhibition is assumed.

## Exact finite crossover rule and all outputs

Pair KKT/control within child, graph, sampler and repetition, separately for
steady wall and process CPU clocks. Report the median of all twelve paired
ratios per case and each graph's six-ratio median, with every range endpoint,
absolute time, warmup and loss. These are medians of ratios, not ratios of
medians. Ranges are descriptive, not confidence intervals.

| Table | Rows |
|---|---:|
| paired_ratios | 3,600 |
| comparisons | 300 |
| graph_comparisons | 600 |
| summary | 360 |
| graph_summary | 720 |
| crossover_points | 150 |
| crossover_brackets | 490 |
| crossover_summary | 20 |

For each family/density/control/size, use exact integer-duration Fractions for
all four graph/clock medians. Six-trial medians average the central two ratios.
`strong_lead` means all four≤9/10; `narrow_lead` means all four<1 but not strong;
`loss` means all four>1; everything else is `mixed_or_tied`.

A strong observed bracket requires an earlier loss, a later strong lead and a
strong lead at **every larger measured size within the same density ladder**.
Keep all 2×5×(21+28)=490 endpoint pairs, all 2×5×(7+8)=150 points and all
2×2×5=20 outcomes. The representative bracket uses the earliest qualifying
upper size and closest measured loss below it. Always-leading sequences have
no observed loss-to-lead crossing. A largest-size-only lead has no persistence
measured beyond that endpoint. Earlier reversals stay visible. No interpolation,
cross-density pooling, monotonicity, historical pooling or asymptotic dominance
claim is permitted.

Publish all five controls and both clocks; a retained-Borůvka win is not an
all-solver win. An independent raw audit must reconstruct ratios, summaries and
exact classifications without the collector's aggregation before conclusions.
Four standalone figures show both clocks for all-five ratios/all-six times,
with four family/density panels, all seven/eight sizes, graph medians, full
ranges and matched clock axes. No favorable result is a prerequisite for
publishing this complete fixed matrix.
