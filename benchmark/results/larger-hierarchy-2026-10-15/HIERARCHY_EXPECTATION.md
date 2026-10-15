# Why hierarchy edges remain through many contractions

**Analytic expectation; source preparation only.** This note and the new
[figure script](../../plot_hierarchy_retention.py) were prepared while the
larger experiment was running, without reading its partial outputs or running
imports, checks or plotting. The eventual two-panel figure describes the ideal
uniform-chord model. It is not measured work, timing, CPU activity or memory.

The [existing full derivation](../density-search-2026-10-15/HIERARCHY_RETENTION.md)
explains why `leaf_hierarchy4` creates a long sequence of fixed partitions. The
generator places three cheap leaves around each core vertex. Its first full
Borůvka contraction removes those stars. The core's forced path has strictly
ranked edges ordered by dyadic boundary level, with every nonpath chord heavier
than every path edge. Each subsequent round therefore joins sibling blocks,
doubling their core size: 1, 2, 4, …, q. Label and physical-order shuffles do not
change those original-vertex component sets.

With n=4q and m=32n, there are 3q local edges, q−1 path edges and

\[
C=m-n+1=124q+1
\]

distinct nonpath chords. The eligible chord population is

\[
D={q\choose2}-(q-1)=\frac{(q-1)(q-2)}2.
\]

At block size b, the number of eligible nonpath pairs whose endpoints are
already inside one component is

\[
I_b=\frac qb{b\choose2}-\left(q-\frac qb\right).
\]

The subtraction removes internal path pairs, which were never eligible chords.
Thus I₁=I₂=0: even the first core pairing cannot remove a chord. If the C chords
form a uniform subset of the D eligible pairs, each pair has inclusion
probability C/D, and the expected remaining core edges are exactly

\[
\mathbb E[M(b)]=q/b-1+C\left(1-\frac{I_b}{D}\right).
\]

This uses a fixed partition independent of the chord draw. Sampling without
replacement changes dependence and variance, but not the expectation. Finite
`mt19937` seeds in the benchmark provide individual reproducible graphs, not an
enumeration of this ideal ensemble. No such formula is assigned to the shuffled
weight twin, whose chord weights can change the contraction partitions.

The proposed figure uses **full contraction rounds**, not residual outputs
after rounds. Round 1 has input m, before the local stars collapse. Rounds
2…L+1 have block sizes b=1,2,4,…,q/2, where L=log₂q. The last contraction consumes
the q/2-block input and produces an empty quotient. Its zero output is not an
extra input round. The three declared sizes therefore give:

| Original n | Core q | Core rounds L | Full contraction calls |
|---:|---:|---:|---:|
| 65,536 | 16,384 | 14 | 15 |
| 1,048,576 | 262,144 | 18 | 19 |
| 4,194,304 | 1,048,576 | 20 | 21 |

The left panel will plot each expected input divided by original m. The right
panel will accumulate those same discrete inputs. Every defined round remains;
curves stop at their own final contraction and are not extended to fake a tail.
Early normalized curves are expected to nearly overlap: all three cases have
the same density and lose few chords while their blocks are small. Their
different terminal rounds are part of the comparison, not missing data.
The accumulated endpoint has the exact closed form

\[
\frac{\mathbb E[V]}m=\frac1m\left[m+(2q-2-L)
+C\left(L-1+\frac{3q(L-2)+6}{(q-1)(q-2)}\right)\right].
\]

V counts one input-edge incidence per call, including the star call. It is
not the sum of all helper passes, bytes moved, allocations or instructions.
The retained-edge helper has additional count/output passes and an early
return when everything merges. KKT has its own sampling, recursion and
verification costs. Consequently the diagram explains an opportunity to avoid
repeated input volume; it does not locate a runtime crossover or predict which
solver wins.

There is a useful exact distinction between vertex and edge shrinkage here.
The first star contraction removes **75% of vertices but only 3/128 = 2.34375%
of edges**. After the next contraction, the quotient has n/8 vertices and
r=249n/8=(249/256)m edges: **87.5% of vertices are gone, but 97.265625% of edges
remain**. This is the two-contraction state where KKT samples. In the ideal
independent p=1/2 model, the sampled branch has expected r/2=(249/512)m edges.
The separate sampled-forest light-edge bound is at most 2(n/8)=m/128 in
expectation, or 0.78125% of original m. The latter is not an observed retained
count or a per-run guarantee, and it is not the size of the sampled branch.
It describes the filtering opportunity after that branch has been solved;
it does not remove the cost of solving and verifying it. The assumptions and
retained-parallel qualification are in the
[expected-work derivation](../edge-view-2026-10-15/THEORY.md).

At this fixed density, most edges are chords: C/m=31/32+1/m. Many remain
crossing until late in the hierarchy. Increasing n adds core rounds, whereas
raising density alone changes that chord fraction toward one without adding
rounds at fixed n. This distinction explains why a size extension tests a
different mechanism from a density extension. The finite compiled generator
stops at the existing n=2²² and m=2²⁷ limits; the plotted domain supplies no
unbounded empirical asymptotic claim.

After root releases nonperformance work, the script will first enumerate
eligible pairs at q=4,8,16,32 and check internal-pair/path counts directly. For
q=4 and q=8 it will also enumerate all chord subsets at several fixed sizes,
directly count their crossing edges, and compare their exact mean round and
total volumes with the formulas. This is a separate combinatorial sanity
check, not a native MST correctness gate. It has **not run at preparation**.

Future reproduction, only after release and into a fresh output directory:

```sh
/usr/bin/python3 -B benchmark/plot_hierarchy_retention.py \
  --output /tmp/hierarchy-expectation-new --released
```

The script reads only its declared source notes, generator/helper sources and
the prospective manifest/protocol. It never reads a timing capture or work
counter. It will retain exact rational CSV values, the enumeration receipt,
PNG/SVG/PDF, source/output hashes and a pending visual-review status. Actual
rendering and inspection of both panels are required before publication.
