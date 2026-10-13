# What the old astronomical crossover does and does not mean

The linked 11 October 2026 [Wikipedia revision](https://en.wikipedia.org/w/index.php?oldid=1379699280&title=Galactic_algorithm#Minimum_spanning_trees)
links the implementation and the author's 2022 post for its numerical
`9 × 10^151` threshold. That estimate is not a property proved about KKT.
It is a consequence of extending two fitted implementation-time formulas far
outside their measurement range.

The [original post](https://chico.dev/Linear-Time-MST/) reports fitted costs
`2357 N` for KKT and `4.67 N log₂ N` for Borůvka, using `N=n+m`. Equating them
gives `log₂ N = 2357/4.67 ≈ 504.7`. The post explicitly conditions the conclusion
on those formulas continuing to hold and notes that another test set changes
the estimates. Its public conclusion should retain those qualifications.

## Three different reasons to revisit that estimate

First, the audited old code did not faithfully realize all the required local
work bounds. Descendants paid for bookkeeping sized by the original edge-ID
range, and verifier median-table construction did repeated nonconstant work
per mask. Recursive sampling also restarted the same random stream. These are
documented source defects, not merely a disappointing fitted constant. The
[implementation archaeology](../../../docs/kkt-report/REPORT.md)
and its exact revision links distinguish structural repairs from later
allocation, storage and hash-cost reductions.

Second, the historical benchmark held the vertex count at 10,000 while varying
edge count. A density sweep is not a vertex-scaling experiment. In particular,
`m log n` with fixed n scales proportionally to m; a fitted `N log N` coefficient
cannot be treated as an independently established law for growing n. For a
simple graph at fixed n, even the possible edge count has a finite ceiling.
These facts do not erase the measured old timings, but they limit extrapolation.

Third, compacting Borůvka has highly family-dependent work. A useful quantity
is `V = Σ_r m_r`, the sum of edges entering its contraction rounds. If edges
shrink geometrically, `V=O(m)`: the asymptotic upper bounds alone provide no
inevitable KKT crossover on that family. If a balanced hierarchy lets nearly m
edges survive many rounds, `V` can instead grow like `m log n`. The previous
hierarchy experiment deliberately tested that latter regime, with vertex
labels and input order shuffled. Its repeated measured advantage is a finite
counterexample to applying the old fitted threshold indiscriminately to the
repaired implementation.

Even an exact idealized model `aN` versus `bN log₂ N` has threshold
`N*=2^(a/b)`. Small changes in the ratio of constants therefore move the predicted
threshold by enormous factors. This algebra explains the fragility of an
astronomical extrapolation; it does not validate that model for present data.

## What the present evidence supports

The [prior held-out experiment](../continuation-2026-10-12/README.md) reports
17–19% less median KKT time than repeated production compaction at roughly one
million vertices and 16.8 million edges on two engineered hierarchy families.
It preserves random-control losses and the desktop power-state limitations.
It does not show that KKT is faster than every practical MST implementation,
or that all large graph families eventually favor this implementation.

Nor did KKT's reputation begin with this repository. The primary
[Bazlamaçcı–Hindi empirical study](https://doi.org/10.1016/S0305-0548(00)00007-1)
predates the blog and reports practical concerns about more complex MST
algorithms in its own implementation/hardware setting. The later
[Filter-Kruskal paper](https://ae.iti.kit.edu/documents/teaching/algorithm-engineering/ss22/fkruskal.pdf)
develops a different practical filtering strategy. A successful filtering
algorithm is not automatically evidence about the constants of this KKT code.

A defensible author-side correction is: **the astronomical number was a
conditional extrapolation from one earlier implementation and benchmark;
subsequent repairs and controlled graph-family comparisons reveal much smaller
crossovers against a specific competitor.** Any broader claim should name the
competitors, workloads, source revisions, machine and measurement limitations.

The new experiments in this directory are primary repository evidence, not
independent published verification. They can support a reproducible correction
to the author's own account and invite replication. They should not be silently
presented as an established literature consensus on Wikipedia. No Wikipedia
content was edited during this investigation.
