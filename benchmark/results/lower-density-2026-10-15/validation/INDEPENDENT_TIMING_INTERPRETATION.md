# Independent reading of the completed lower-density timing result

This is a source/table-text interpretation check, not a second execution of the
numerical audit. The [completed standalone raw audit](../independent-audit-attempt01/audit.json)
reports PASS for all 60 children, 2,520 outputs, 3,600 ratios, 1,980 summary
medians, 150 point states, 490 endpoint pairs and 20 classifications. It binds
timing freeze `0c49ed1d046d402ebccb6978ef5f9cdea02865758a1578a43003b189025aa520`.
No partial capture or historical timing was used for this reading.

## The requested retained-B crossover is present at density 16

For `leaf_distance4`, d=16, the prescribed strong bracket against retained-edge
Boruvka is **(512, 8,192] vertices**. At n=512 every graph median on both clocks
exceeds one (range 1.11916–1.19036), and all twelve trial pairs lose on each
clock. The intermediate n=2,048 point already gives a narrow lead: pooled
wall/CPU ratios 0.940215/0.940332 and all twelve trial pairs winning, but graph
medians exceed the 0.90 strong threshold.

At n=8,192 all four graph/clock medians are below 0.90 (0.819951–0.821838), and
that condition persists at all four larger measured points: 32,768; 131,072;
524,288; and 2,097,152. All sixty trial pairs across those five strong points
win on each clock; the retained trial maxima are also below 0.90. The strong
bracket is not an interpolated threshold, and its lower endpoint must remain
512 rather than substituting the already-winning 2,048 point.

At the largest density-16 size, m=33,554,432, the pooled KKT/retained-B ratios
are **0.708792201 wall / 0.708792397 CPU**, about 29.1% less time. The four graph
medians are 0.706646–0.711577. This is a direct comparison with the shared
retained-contraction control, not merely a win over quotient deduplication.

## The density-8 reversal must remain prominent

Density-8 ordered inputs have strong retained-B point leads at n=262,144 and
1,048,576, with pooled wall ratios 0.896108 and 0.834133. At n=4,194,304 the
pooled ratio is still 0.972608 wall / 0.972607 CPU, but the graph medians split:
about 0.94138 for G23000003 and 1.01594 wall / 1.01592 CPU for G23000029.
Only seven of twelve trial pairs win on each clock. The endpoint is mixed and
invalidates every earlier strong bracket's required persistence. Therefore
the declared density-8 retained-B crossover result is **false**, even though
earlier point leads and the largest pooled ratio look favorable.

The shuffled twins lose to retained B at every size in both density ladders.
These controls preserve topology, labels, IDs, physical order, cheap leaves and
weight multiset; they change core weight assignment. This supports a role for
weight organization on these generated instances, not application prevalence.

## Other controls and limits

The complete classification table has 13 true strong-crossover outcomes out of
20: all four family/density combinations against dedup B, Prim and original B,
plus the density-16 ordered retained-B outcome. None of the four Kruskal
comparisons has a sustained strong bracket. Some intermediate density-16
ordered points beat Kruskal, but the larger points lose; this is retained rather
than treated as an enduring win. No case is fastest against all five controls
by the pooled case medians. Shuffled cases still lose to retained B, density-8
ordered cases lose to Kruskal, and density-16 ordered cases retain either an
original-B or Kruskal median loss at every measured size.

The source-level expected-work argument and this observed finite bracket are
different claims. This campaign uses the same frozen eighth binary, two graph
seeds, one sampler seed, balanced six-solver repetitions and the predeclared
matrices. It does not isolate a probability change, prove all-seed robustness,
establish a general clock threshold, pool densities, or measure mechanism
counters. The separate fully matched work companion is prepared but not yet
executed at this review.

Read directly: [all case comparisons](../analysis-attempt01/comparisons.csv),
[exact graph/clock point states](../analysis-attempt01/crossover_points.csv),
[all endpoint pairs](../analysis-attempt01/crossover_brackets.csv),
[all 20 outcomes](../analysis-attempt01/crossover_summary.csv), and the
[complete generated summary](../analysis-attempt01/README.md). No source,
timing, baseline, protocol or frozen helper was changed during this review.
