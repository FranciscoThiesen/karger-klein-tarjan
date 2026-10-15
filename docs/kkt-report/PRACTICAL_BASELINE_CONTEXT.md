# What the six-solver comparison establishes

A win in these studies is a win over the named implementations, graph families,
sizes and configurations. It is not a comparison against every practical MST
method.

Osipov, Sanders and Singler's 2009 Filter-Kruskal algorithm partitions edges by
weight, solves the lighter part, then removes heavy edges whose endpoints are
already connected. Its analysis for arbitrary graphs with randomly permuted
distinct weights gives expected time O(m + n log n log(m/n)). Their experiments
include tuned Prim variants, geometric graphs, lollipop graphs and image
segmentation inputs. They discuss large constants in general sampled-forest
filtering, but do not benchmark this KKT implementation. Filter-Kruskal is a
different algorithm; those results neither validate nor refute our measured
KKT crossovers. [Author-hosted paper, sections 1–4](https://ae.iti.kit.edu/documents/teaching/algorithm-engineering/ss22/fkruskal.pdf),
[publication record](https://epubs.siam.org/doi/10.1137/1.9781611972894.5).

We have not implemented or measured Filter-Kruskal in these campaigns. It is a
useful future comparator before making a broader claim about the fastest
practical MST solver. Adding it would require a new declared study; the current
six-solver matrix remains fixed. The present investigation asks whether KKT can
repay its filtering overhead against repeated contraction and the repository's
classical implementations.

Brodal and colleagues' 2021 study provides related evidence for tuning the
sampling rate, but solves **external-memory connected components**. It tests
fixed rates 1/2, 1/4, 1/8 and 1/16, as well as adaptive rates near estimated
V/E, on random, grid, geometric and hyperbolic graphs. The fixed-rate variants
also omit the root contraction; comparison with their default therefore does
not isolate the rate change. Their connected-components adaptation replaces
MST verification with contraction, and the conclusion leaves empirical MSF
comparison for future work. This is motivation for our sampling-rate question,
not weighted-MST validation. [Primary paper, sections 4, 7.3 and 8](https://drops.dagstuhl.de/opus/volltexte/2021/13795/pdf/LIPIcs-SEA-2021-23.pdf).

*Engineering Massively Parallel MST Algorithms* supplies actual MST
experiments: its distributed Filter-Borůvka can outperform its unfiltered
version, particularly on G(n,m), while filtering adds overhead after effective
local preprocessing on highly local graphs. Its filtering partitions by
weight, following Filter-Kruskal, and its contraction implementation removes
parallel edges. It does not test KKT's Bernoulli sampled-MSF filtering or our
sequential retained-edge comparator. Distributed communication, partitioning
and preprocessing also contribute to its results. [Primary paper, sections IV–V and VII-A](https://arxiv.org/pdf/2302.12199).

Neither paper supplies an empirical validation of our hierarchy-retention
proof; that argument is our derivation from the declared generator and
contraction semantics. The bounded literature search found no directly
verified weighted-MST KKT experiment comparing smaller sampling rates. This
is not a claim that none exists, and neither related study predicts our result.
