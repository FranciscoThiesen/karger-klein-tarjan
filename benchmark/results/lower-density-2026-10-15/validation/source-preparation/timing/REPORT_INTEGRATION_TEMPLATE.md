# Lower-density report integration — conditional template

**Source preparation only. No lower-density result is claimed here.** This text
uses the fixed declaration and source, not partial timings. Do not insert the
result slots into the consolidated report until complete capture, strict
analysis, independent numerical audit and figure QA have passed. If the study
fails, report the failed attempt and leave the performance conclusions pending;
do not substitute completed partial cases for this matrix.

Place the completed section after the existing density-32 distance study. Keep
its campaign separate, retain the earlier losses and reversals, and update the
opening conclusion only after reading all 20 new comparator outcomes. The
publication figures are eight separate density/clock/view pages. The report
plan selects the two wall-ratio pages, one at each density, while linking all
eight pages and the complete tables within the overall 40-page limit. Data and unfavorable results
must not be omitted to meet that limit.

## Paste-ready section: lower fixed densities

The next fixed experiment asks whether the same KKT implementation has a
measured losing-to-winning crossover at lower edge densities. It reuses the
unchanged eighth-sampling executable and all six implementations. No graph
generator, solver, timer boundary or memory ceiling changes. Density 16 covers
512, 2,048, 8,192, 32,768, 131,072, 524,288 and 2,097,152 vertices. Density 8
covers 256, 1,024, 4,096, 16,384, 65,536, 262,144, 1,048,576 and 4,194,304.
Both ladders contain distance-ranked and shuffled twins, with two fresh graph
seeds (23000003/23000029) and one fixed KKT seed (3407). The matrix was chosen
after the earlier density-32 results and fixed before its own measurements;
this is a targeted follow-up, not an unbiased survey of graph families.
The 60 declared children produce 2,520 certified
outputs, including 2,160 timed calls and 360 warmups. **[Replace this last
sentence with actual completion/failure status; cite the committed capture,
freeze, strict analysis and independent audit.]**

Each ladder is a valid fixed-parameter family: m=dn and represented input size
N=n+m=(d+1)n. Its average core degree stays fixed, but the fraction of possible
core edges present decreases as n grows. The smallest core is almost complete:
122/127 of possible pairs at density 16, and 58/63 at density 8. These are
finite-size properties of the declared family, not a change of density within
a curve. The sweep does not isolate asymptotic effects from occupancy, cache
behavior or other machine-dependent constants. The two ladders are analyzed
separately; equal maximum edge counts do not make their differing vertex
counts and topologies equivalent inputs. This comparison does not replace the
separate Google Benchmark complexity fit or prove an asymptotic runtime bound.

The ordered weights rank core edges by dyadic ancestry, with distinct random
order inside each tier. Cheap four-vertex stars surround the core. Its shuffled
twin preserves topology, original IDs, labels, tuple order, cheap leaves and the
weight multiset, while changing the assignment of core weights. These are
engineered hierarchical rank weights. “Distance” here does not assert Euclidean
geometry or the triangle inequality, and this is not evidence that road,
nearest-neighbor or ordinary spatial graphs have the same behavior.

**[Insert the complete outcome table below and links to all 30 cases and both
clocks.]** Ratios below one favor KKT. Each displayed pooled point is the median
of twelve within-repetition KKT/control ratios, not a ratio of separate runtime
medians. Both graph medians and every trial-range endpoint remain visible.
Ranges are descriptive, not confidence intervals. Repetitions reuse the same
two graphs and fixed sampler seed. Graph two reverses the entire schedule, so
graph identity and order/host history remain confounded.

For one family, density, comparator and size, let the four values be the two
graphs' six-trial median ratios for wall and CPU time. Six-trial medians average
the central two exact integer-duration ratios. A point is **strong** only if
all four are ≤0.9; **narrow** if all four are <1 but not strong; **loss** if all
four are >1; otherwise it is **mixed or tied**. A strong observed bracket
(n_low,n_high] requires a measured loss at n_low, a strong point at n_high, and
strong points at every larger measured size in that same ladder. This is a
finite bracket, not an interpolated threshold or a proof of future dominance.
The representative bracket uses the earliest qualifying upper size and closest
measured loss below it. All 150 point states, 490 endpoint pairs and 20 outcomes
remain available, including earlier reversals and individual trial losses.

**[Result sentence: identify exactly which comparator/family/density qualifies,
give the bracket and largest-size wall/CPU paired ratios, the range of the four
graph/clock medians, and individual trial wins/losses. Also state the strongest
contradicting controls and any all-size loss sequence.]** A win over retained
Borůvka does not establish an all-solver win. Deduplicating Borůvka, original
Borůvka, Kruskal and Prim remain independently reported controls. Absolute
runtimes are shown alongside ratios; historical campaigns are not pooled into
these curves or used to estimate an isolated implementation effect.

## Required complete outcome table

Fill every row from `crossover_summary.csv`, the full point sequences and
`comparisons.csv`/`graph_comparisons.csv`. “No bracket” must distinguish always
leading, never strong, mixed, or a reversed earlier lead. Add a final-endpoint
qualification whenever no larger size tests persistence. Do not put a dash
where a measured loss belongs.

| d | Weight assignment | Comparator | Complete state sequence and bracket/no-bracket reason | Largest-size wall / CPU paired ratio |
|---:|---|---|---|---|
| 16 | Dyadic distance ranks | Retained-edge Borůvka | [pending] | [pending] |
| 16 | Dyadic distance ranks | Deduplicating Borůvka | [pending] | [pending] |
| 16 | Dyadic distance ranks | Original Borůvka | [pending] | [pending] |
| 16 | Dyadic distance ranks | Kruskal | [pending] | [pending] |
| 16 | Dyadic distance ranks | Prim | [pending] | [pending] |
| 16 | Shuffled ranks | Retained-edge Borůvka | [pending] | [pending] |
| 16 | Shuffled ranks | Deduplicating Borůvka | [pending] | [pending] |
| 16 | Shuffled ranks | Original Borůvka | [pending] | [pending] |
| 16 | Shuffled ranks | Kruskal | [pending] | [pending] |
| 16 | Shuffled ranks | Prim | [pending] | [pending] |
| 8 | Dyadic distance ranks | Retained-edge Borůvka | [pending] | [pending] |
| 8 | Dyadic distance ranks | Deduplicating Borůvka | [pending] | [pending] |
| 8 | Dyadic distance ranks | Original Borůvka | [pending] | [pending] |
| 8 | Dyadic distance ranks | Kruskal | [pending] | [pending] |
| 8 | Dyadic distance ranks | Prim | [pending] | [pending] |
| 8 | Shuffled ranks | Retained-edge Borůvka | [pending] | [pending] |
| 8 | Shuffled ranks | Deduplicating Borůvka | [pending] | [pending] |
| 8 | Shuffled ranks | Original Borůvka | [pending] | [pending] |
| 8 | Shuffled ranks | Kruskal | [pending] | [pending] |
| 8 | Shuffled ranks | Prim | [pending] | [pending] |

## Conditional interpretation guide

- **Earlier loss → sustained strong suffix:** “A strong observed crossover
  bracket exists against [named comparator] on [family, d] over the declared
  sizes.” Give all four endpoint medians and the measured suffix; do not say
  KKT dominates beyond the endpoint indefinitely.
- **Smallest point already leads:** report the advantage, but say no losing
  lower endpoint was observed. This answers usefulness, not the crossover
  question under this protocol.
- **Only the maximum becomes strong:** the formal bracket can qualify, but
  persistence beyond that endpoint is untested. Do not describe an empty later
  set as demonstrated stability.
- **Lead reverses or graphs/clocks disagree:** preserve the whole sequence and
  mixed classifications. A pooled ratio <0.9 alone does not meet the rule.
- **Deduplicating control loses but retained control wins:** deduplication cost
  is a plausible part of the implementation comparison; the sampling/verifier
  continuation has not repaid its cost relative to that shared retained kernel.
- **Retained control loses but another solver wins:** practical relative KKT
  advantage exists against the named control; the fastest available measured
  implementation is still [solver]. Test an “all-control” claim against all
  five controls on all four graph/clock medians, and retain individual losses.
- **No qualifying bracket or all losses:** publish that result without adding
  sizes, changing thresholds, dropping a control, or relabeling a narrower lead
  as the promised strong crossover. A later experiment needs a new declaration.

## Conditional mechanism paragraph: only after the untimed audit passes

The separate diagnostic repeats all 60 exact timing inputs with instrumentation
and independent raw-counter reconstruction. It retains 180 solver records and
all 11,700 counter cells, 120 complete comparator replay chains, 60 cumulative
query rows and all zero/unmeasured values. **[State actual completion/audit
status; otherwise omit measured-work statements and call this pending.]**

Source reasoning predicts the ordered input's first two full-graph contractions
leave n/8 vertices and (d−7/8)n crossing records. Retained Borůvka keeps distinct
parallel crossing records, so small quotient vertex counts alone do not imply
small edge scans. Deduplicating Borůvka may remove many such records, paying for
its quotient construction. KKT shares the retained contractions, then pays for
sampling, the sampled MSF and heavy-edge filtering. Its complete recursive
work, rather than the root shrinkage alone, determines these logical counts.

**[Insert matched per-input work evidence, including increases: contraction
edge scans, cumulative sampling volume/engine words, verifier and path-query
visits, materializations and initialization; compare both full replay totals
and round counts.]** Normalize counts by original m while keeping raw totals.
Q is cumulative verifier requests; U=path_query_visits−2Q sums unique requests
within individual verifier calls. U/Q remains undefined when Q=0. Scalar
engine words equal cumulative sampling_edge_visits exactly. No cross-rate
counter equality applies to this single-policy study.

Agreement between fewer repeated edge visits and a timing lead supports that
source-level mechanism; it does not measure CPU instructions, cache misses,
memory bandwidth, allocator costs or a percentage of runtime explained.
If counts improve while runtime worsens, report the mismatch. These diagnostics
cover KKT and the two compacting continuations, not a measured decomposition
of Prim, Kruskal or original Borůvka. Untimed process durations are not timing
replicates. Any ideal independent-sampling F-light bound is a theoretical bound,
not a prediction of this seeded sample or proof of sampled connectivity.

## Optional source-derived root proxy — not a runtime prediction

The exact root dimensions also hold for `leaf_distance4`, not just the
path-hierarchy weighting. Write q₀=n/4 for the generator's core size and
q=n/8 for the quotient after two retained contractions. Every core vertex has
three star leaves. Their 3n/4 edge weights are below every core-edge weight,
so the first round contracts exactly those four-vertex stars. The simple core
contains the full consecutive-vertex path. Its distance tiers are
floor(log₂(u xor v)); tier zero consists exactly of the sibling pairs
(2j,2j+1), all present on that path. Each core vertex therefore has exactly one
lowest-tier neighbor. The second round merges these sibling pairs and removes
exactly n/8 additional edge records. Simplicity rules out extra records inside
one pair; the surviving path connects the quotient, so isolated-vertex
normalization removes nothing further for the declared sizes. Consequently,

\[
q=n/8,\qquad r=m-7n/8=(d-7/8)n.
\]

This argument survives every permitted tie-rank shuffle, vertex relabeling and
physical edge-order shuffle. It does not establish the same dimensions for
the weight-shuffled control, subsequent sampled graphs or later recursion.

Under the ideal independent Bernoulli sampling model, a rate p gives expected
sample size pr and expected F-light survivors at most q/p. The latter bound
allows a disconnected sampled MSF. Thus pr+q/p is a one-level upper-bound
proxy for the two child edge counts. Its continuous minimizer is

\[
p_* = \sqrt{q/r}=1/\sqrt{8d-7}.
\]

| Fixed d | Proxy minimizer p_* | Proxy at p=1/8, divided by m | Proxy at p=1/2, divided by m |
|---:|---:|---:|---:|
| 8 | 1/√57 ≈ 0.13245 | 121/512 ≈ 0.23633 | 61/128 ≈ 0.47656 |
| 16 | 1/11 ≈ 0.09091 | 185/1024 ≈ 0.18066 | 125/256 ≈ 0.48828 |
| 32 | 1/√249 ≈ 0.06337 | 313/2048 ≈ 0.15283 | 253/512 ≈ 0.49414 |

The two normalized expressions are 1/8+57/(64d) and 1/2−3/(16d).
This source-level proxy makes the already fixed eighth-rate policy plausible
even at d=8. It is neither a calibrated runtime model nor a claim that p=1/8
is optimal. It omits vertex work, contraction/filtering costs, recursive input
structure, allocation, hardware effects and the possible looseness of the
survivor bound. The actual seeded MT stream is not literally independent
randomness. No policy, size, seed or threshold changes follow from this
calculation; measured outcomes and their losses remain pending.

## Source basis and pending evidence

Reviewed as text only: the prospective lower-density `PROTOCOL.md`,
`run_lower_density.py` exact-Fraction classification code,
`benchmark/core_attachment_fixtures.hpp`, its simple-core `Builder` in
`benchmark/continuation_fixtures.hpp`, the retained quotient construction in
`kkt/experimental_multigraph_contraction.hpp`, the two root calls in
`kkt/kkt.cpp`, the existing consolidated draft,
and `MECHANISM_AND_WORK_FEASIBILITY.md`. No script was imported or executed;
no hash walk, render, native job or partial timing read was used. This template
adds no result and changes neither the experiment nor the current report.
