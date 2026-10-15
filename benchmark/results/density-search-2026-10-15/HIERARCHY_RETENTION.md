# Why retained-edge Boruvka rescans hierarchy chords

Source-derived calculation, 2026-10-15. This note is a mathematical derivation, not a new timing or work-count run. Source paths below are relative to the measured repository root.

Consider `leaf_hierarchy4`, with n=4q original vertices, q a power of two, and m edges. There are 3q cheap leaf edges, q−1 core path edges, and

\[
C=m-3q-(q-1)=m-n+1
\]

distinct nonpath core chords. The eligible chord population has size

\[
D={q\choose2}-(q-1)=\frac{(q-1)(q-2)}2.
\]

## Why the partitions are fixed

The generator first inserts every core path edge (v−1,v). Its hierarchy level is the number of trailing zero bits in v. Path weights are assigned by increasing level; all chords occupy level 22, above every possible path level in the supported q≤2^20 domain. Shuffling within each level produces **distinct** ranks, not tied weights. Expanded local leaf weights occupy 1…3q, below every core edge. Labels and physical edge order are shuffled afterward. See `benchmark/core_attachment_fixtures.hpp:42-53,80-112,119-149`.

The first contraction merges exactly each star into one core vertex. Each leaf selects its only edge, and each center selects a cheaper local edge rather than a core edge. The selected local edges connect the entire star.

Inductively, after k core rounds, components are aligned contiguous blocks of b=2^k original core vertices. A block indexed j has path boundaries at jb and (j+1)b when they exist. Exactly one boundary has hierarchy level k; the other, if present, has higher level. Thus every block selects its unique level-k boundary to its sibling. All chords are heavier. Every round doubles block size, independently of chord endpoints and within-tier rank order. Renumbering changes component names, not these original-vertex sets. Distinct weights also make physical input order irrelevant to minimum-edge selection.

The retained-edge helper selects incident minima and deletes only edges whose endpoints enter the same component, preserving every crossing chord (`kkt/experimental_multigraph_contraction.hpp:28-50,93-135`). Its continuation repeats this helper until empty (`benchmark/retention_boruvka.hpp:12-25`). No parallel-edge deduplication is present in this argument.

## Exact expected retention

In the ideal generator model, independently uniform endpoint proposals reject loops and previously chosen pairs. Because the path pairs are inserted first, the C accepted chords form a uniform subset of the D eligible nonpath pairs. The canonical unordered-pair builder and unbiased bounded draw are at `benchmark/continuation_fixtures.hpp:52-61,77-90`; chord insertion is at `core_attachment_fixtures.hpp:91-95`.

For q/b aligned blocks, the number of eligible pairs internal to blocks is

\[
I_b=\frac qb{b\choose2}-\underbrace{\left(q-\frac qb\right)}_{\text{internal path pairs excluded from the chord population}}.
\]

Hence the expected internal fraction of chords is

\[
f(b)=\frac{I_b}{D}
=\frac{q(b-3+2/b)}{(q-1)(q-2)},
\qquad
\mathbb E[C_b]=C\,[1-f(b)].
\]

Sampling without replacement changes dependence and variance, but not this expectation: each eligible pair has inclusion probability C/D. The partition is fixed independently of the chord draw. Useful boundary checks are f(1)=f(2)=0 and f(q)=1. The zero at b=2 matters: a two-vertex aligned block contains only its excluded path pair, so no chord disappears in the first core round.

At stage b<q, exactly q/b−1 path edges also survive. Thus the expected residual edge count after the local contraction and k core rounds is

\[
\mathbb E[M_k]=q/2^k-1+C[1-f(2^k)].
\]

The implementation represents the final one-component quotient as empty, agreeing with M_L=0 for L=log2(q).

## Sum of rescanned chord incidences

The L core rounds read the residual inputs at k=0,…,L−1, including the state immediately before final contraction. Summing the geometric terms gives

\[
\sum_{k=0}^{L-1}f(2^k)
=1-\frac{3q(L-2)+6}{(q-1)(q-2)}.
\]

Therefore the expected chord contribution to round-input volume is

\[
\mathbb E[V_{\rm chords}]
=C\left[L-1+\frac{3q(L-2)+6}{(q-1)(q-2)}\right]
=\Theta(C\log q).
\]

Alternatively, every pre-final block size b≤q/2 has f(b)<1/2, so C L/2≤E[V_chords]≤C L. This immediately establishes the order of growth without a limiting approximation.

Including the initial m-edge star-contraction input and the core path contributions gives the exact expected **contraction input-edge volume**

\[
\boxed{
\mathbb E[V]
=m+(2q-2-L)
+C\left[L-1+\frac{3q(L-2)+6}{(q-1)(q-2)}\right].
}
\]

This V counts each input edge once per contraction call. It is not the number of all internal edge passes, copied bytes or CPU instructions. The helper usually performs additional count/output passes; its final all-merged round returns early. Those details affect constants, not this input-volume bound.

For the recorded n=2,097,152, d=16 case, substitution gives q=524,288, L=19, m=33,554,432 and C=31,457,281. The formula predicts E[V]/m approximately **17.90634**. This is consistent in scale with the independently recorded finite-seed summary rounded to **17.907m** (`benchmark/results/retention-control-2026-10-15/work/WORK_TABLE.md`). The formula is a topology-ensemble expectation; 17.907 is an observed summary of two fixed seeds, not an evaluation or proof of that expectation.

Density increases C/m=1−1/d+1/m toward one, but **does not increase the round count at fixed n**: the hierarchy still has L core rounds plus one initial star round. To leading order at large q,

\[
\frac{\mathbb E[V]}m
=1+\frac1{2d}+\left(1-\frac1d\right)(L-1)
+O\!\left(\frac{L}{q}\right).
\]

Thus density can increase chord persistence per input edge only toward a finite plateau at fixed q. For q=524,288 the leading values for d=16,32,64 are about 17.90625, 18.453125 and 18.726563, respectively; the exact formula adds the small finite-q correction. Absolute work still rises with m, and KKT's own edge work rises too. Increasing n, in contrast, adds one core round for each doubling. Neither observation locates a runtime crossover.

For fixed density d=m/n>1, C=(d−1)n+1=Theta(m), so the growing ideal family has expected retained-edge continuation volume Theta(m log q). At d=1, C=1 and that conclusion does not apply. In contrast, the KKT expected-linear theorem uses sampling and filtering to bound expected total recursive work by O(m+n), under linear primitive costs and independent random sampling; its strict-weight premise holds for these distinct ranks. For the retained-parallel variant, use the [separate recurrence qualification](../edge-view-2026-10-15/THEORY.md). See [Karger, Klein and Tarjan, sampling lemma and expected-time analysis, sections 2–4](https://people.csail.mit.edu/karger/Papers/mst.pdf). The mathematical family can be extended by adding hierarchy levels above the current fixed domain; the finite compiled generator itself is not an unbounded asymptotic experiment.

## Scope of the conclusion

This explains an opportunity for KKT: many heavy chords remain crossing a deterministic hierarchy for almost log2(q) rounds, although filtering can discard them. It does not establish a measured timing advantage, a causal allocation/cache account or a finite crossover threshold. Retained-edge scans can have much smaller constants than KKT verification.

The expectation is over the ideal uniform random chord model. The actual source uses deterministic `mt19937` streams from finite seeds; the recorded two seeds are individual reproducible draws, not exhaustive sampling of all C-subsets and not an exact expectation. Their measured retained counts should be compared with the formula as observations, with all deviations retained. Do not transfer the fixed-partition argument to shuffled/random weight controls: chords can then determine the selected minima and component partitions. This is an engineered hierarchy stress family, not representative application data.
