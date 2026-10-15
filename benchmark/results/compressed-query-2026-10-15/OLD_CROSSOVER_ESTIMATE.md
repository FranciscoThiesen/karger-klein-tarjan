# What the old astronomical crossover estimate meant

The original [2022 implementation post](https://chico.dev/Linear-Time-MST/)
reported fitted models `T_B(N) = 4.67 N log2(N)` and `T_K(N) = 2357 N`,
with `N=m+n`. Its astronomical estimate explicitly assumed those fitted
formulas would continue to describe larger inputs. The
[Wikipedia listing](https://en.wikipedia.org/wiki/Galactic_algorithm#Minimum_spanning_trees)
currently cites that post and the repository for the practical claim
(checked 2026-10-15).

Algebraically, the intersection of the two models satisfies

```
log2(N*) = 2357 / 4.67
N* = 2^(2357 / 4.67), approximately 9 × 10^151.
```

This calculation is conditional on the models. It is not an experimentally
observed crossing, an algorithmic lower bound, or a graph-independent threshold.
The distinction matters for three separate reasons.

First, an asymptotic upper bound is not a timing equation. An `O(m log n)`
Borůvka bound does not say that a particular family takes a matching number
of rounds or retains a matching number of edges per round. Faster component
merging can make the actual family behave much better. A theoretical separation
requires suitable lower-bound behavior as well as KKT's expected upper bound.

Second, a finite fit does not establish its model beyond the measured range.
Changes in residual graph size, memory access, cache capacity, allocation and
input density can alter the effective constants or slopes. The model's `N`
also combines vertices and edges; changing their relationship changes the
interpretation. Our paired studies preserve family and density when comparing
sizes, and report measured brackets rather than extrapolated intersections.

Third, the implementation and comparator matter. The source repairs described
in [the main report](../../../docs/kkt-report/REPORT.md) removed work that did
not scale with the current recursive subproblem, as well as expensive copies
and bookkeeping. Recent experiments separately change contraction, verifier
input representation, random-bit use and query storage. A constant fitted to
the earlier program cannot be carried over to those programs. Retained-edge
Borůvka is also a stronger control than assuming every contraction must
deduplicate parallel edges.

Even within the hypothetical models `aN` and `bN log2(N)`, the predicted
threshold is exponentially sensitive: `N*=2^(a/b)`. A perturbation δ in the
coefficient ratio multiplies the predicted threshold by `2^δ`. This is one
reason an enormous extrapolated number should not be reported as a precise
physical boundary.

The appropriate replacement is evidence scoped to a revision, graph generator,
parameters, seeds, timing boundary, hardware and comparator. A measured lead
at both tested sizes is a lead over that range; a losing-to-winning bracket is
a crossover observation. Neither establishes universal dominance. The local
benchmarks and this explanation are original implementation research, not an
independent published validation of a revised encyclopedic classification.
