# Fixed lower sampling probabilities: future isolated experiment

Source/theory preparation, 2026-10-15. No implementation, imports, tests, builds,
native execution, or timing analysis was performed for this proposal. It is not
part of the active held-out matrix, the larger hierarchy screen, or the separate
packed-plus-compressed proposal. Source inspected in
`/Users/random_person/Desktop/kkt-compressed-queries`.

## What follows from the sampling lemma

The [Karger–Klein–Tarjan paper, §2 Lemma 1](https://people.csail.mit.edu/karger/Papers/mst.pdf)
states its sampling bound for arbitrary independent inclusion probability p;
its algorithm in §3 chooses p=1/2 and removes duplicate quotient edges.
The fixed-p retained-parallel recurrence below is our extension, not an explicit
theorem about this implementation in the paper.

Assume an undirected loop-free multigraph with distinct weights, and count every
parallel record in m. Contraction must select safe MSF edges, delete resulting
loops, and omit isolated quotient vertices. Every nonisolated selected component
contains at least two vertices, so two Boruvka steps leave q≤n/4 vertices and
r≤m edge records. This remains true for disconnected inputs: components that
finish disappear; isolated original vertices cannot increase the surviving
quotient. The current implementation requires valid loop-free input. This
proposal does not add support for arbitrary input self-loops.

Select each of those r records independently with fixed 0<p<1. Let X be the
sample size; F its valid MSF; and Y the number of F-light records in the quotient.
Then E[X]=pr and E[Y]≤q/p. No connected-sample assumption is needed. In particular,
queries joining different components of F remain light.

A useful finite proof makes the disconnected and parallel cases explicit.
Process records in strictly increasing weight order. Let L_e indicate that e's
endpoints are disconnected in the forest of already accepted cheaper records,
and I_e its independent sampling bit. L_e is determined before I_e is exposed.
The final F-light status equals L_e, including when no final F-path exists.
Every accepted light record adds exactly one forest edge. Thus

    p E[Y] = E[sum_e L_e I_e] = E[|F|]
           = q - E[components(H)] ≤ q - components(G) ≤ q.

Here H retains the original q-vertex universe for the identity, including its
isolated vertices. The executable may compact those vertices afterward. Distinct
parallel records do not change the argument. Unique weights also make the sampled
MSF independent of the random choices used to compute it recursively.

## Recurrence and sufficient constants

Suppose nonrecursive work is at most c(m+n), uniformly over the fixed mask
choices. Each child has at most q vertices, even after isolation removal. Using
fresh independent randomness conditional on each recursive input, induct on n:

    E[T(n,m)] ≤ c(m+n) + E[T(q_H,X) + T(q_Y,Y)]
             ≤ c(m+n) + A(pr + q/p) + 2Bq
             ≤ (c+Ap)m + (c+A/(4p)+B/2)n.

Therefore the proposed conditions are sufficient:

    A ≥ c/(1-p),          B ≥ 2c + A/(2p).

Increase constants to cover finite nonempty base cases. An empty child's O(1)
dispatch is charged to its parent's local work; an initially empty problem adds
O(1). The fully literal bound is O(m+n+1), conventionally O(m+n) for nonempty
inputs. Both recursive arguments shrink in vertex count, irrespective of whether
either sample happens to be empty or full.

Choosing the displayed equalities gives:

| p | A/c | B/c |
|---|---:|---:|
| 1/2 | 2 | 4 |
| 1/4 | 4/3 | 14/3 |
| 1/8 | 8/7 | 46/7 |

Consequently each fixed probability has expected linear work, subject to linear
contraction, filtering and verification and the ideal independent sampling
model. Constants deteriorate near p=0 or p=1; this does not justify arbitrary
size-dependent p. The public result hash wrapper still needs expected hashing
cost. The finite seeded `mt19937` executable is deterministic and does not supply
literal independent coins conditional on all previous observations. This proof
is an algorithmic model statement, not a measured complexity or wall-time claim.
The paper's simple-graph O(n²) worst-case cap does not automatically transfer to
retained parallel records; no new high-probability claim is made here.

## Two different heuristics, neither a runtime prediction

A one-level proxy assigns equal unit cost to sample edges and light survivors:

    W(p) = pr + q/p;       p_proxy = sqrt(q/r)

when the minimizer lies in (0,1). Replacing r with m gives the coarser mp+q/p
proxy. In practice child costs differ, and local verification still examines the
parent quotient. Forest shape, disconnected remapping, recursive work, reserved
capacity and cache behavior are omitted. Smaller p trades fewer sample edges
against a weaker survivor bound; the bound is not the actual survivor count.

Separately, substituting m=dn into the uniform induction bound gives

    E[T] ≤ c n { [d + 1/(2p)]/(1-p) + 2 }.

Minimizing that expression with a common c gives

    2d p² + 2p - 1 = 0,
    p_bound = 1 / (1 + sqrt(1+2d)).

For d=32 this is approximately 0.11035, near 1/8. The displayed bound coefficients
at p=1/2,1/4,1/8 are respectively 68, 142/3, and 302/7 multiplying cn. These are
loose uniform potential bounds, not estimates of speedups or of actual constants.
Their optimizer differs from the one-level proxy because the bound accounts for
both recursive branches using worst-case vertex reduction throughout.

## Exact hierarchy root arithmetic

For the current `leaf_hierarchy4` at n=2^20 and d=32, the first contraction removes
all 3n/4 star edges. The next contraction pairs adjacent core vertices and removes
n/8 path edges. Every chord is a nonpath pair in a simple core, so none can lie
inside these two-vertex core blocks. Therefore, exactly (not just in expectation):

    m = 32n = 33,554,432
    q = n/8 = 131,072
    r = m - 7n/8 = (249/8)n = 32,636,928.

This follows from `benchmark/core_attachment_fixtures.hpp:80-111,119-134` and
`benchmark/results/density-search-2026-10-15/HIERARCHY_RETENTION.md`; it does not
apply to the shuffled-weight twin's second partition.

| p | E[X]=pr | E[Y] upper bound q/p | E[X]+upper bound |
|---|---:|---:|---:|
| 1/2 | 16,318,464 (15.5625n) | 262,144 (0.25n) | 16,580,608 (15.8125n) |
| 1/4 | 8,159,232 (7.78125n) | 524,288 (0.5n) | 8,683,520 (8.28125n) |
| 1/8 | 4,079,616 (3.890625n) | 1,048,576 (n) | 5,128,192 (4.890625n) |

At p=1/8 the survivor expectation is bounded by n, versus the original 32n
records; that is an expectation bound, not an outcome guarantee. This remains
valid when the sample is disconnected. Here q/r=1/249, so the one-level proxy
minimizer is 1/sqrt(249), approximately 0.06337, near 1/16; the coarse m-based
proxy gives exactly 1/16. Neither calculation selects a calibrated best p.

## Smallest proposed implementation and gates

The current scalar loop is `kkt/kkt.cpp:245-265`; it draws one `mt19937` word per
record, accepts odd words, preserves input order, assigns parent-position IDs only
for `sample_edges<true>`, and reserves floor(r/2) records. The public wrapper at
lines 268-270 calls `<false>`. The compressed study deliberately has no packed
sampler enabled.

A future isolated scalar experiment can change only the private acceptance
predicate, using compile-time low-bit all-ones masks:

    half:    (word & 1u) == 1u
    quarter: (word & 3u) == 3u
    eighth:  (word & 7u) == 7u

Under a fresh ideal uniform 32-bit word these probabilities are exact. At an
identical input and identical engine-entry state, the eighth sample is a subset
of the quarter sample, itself a subset of the legacy half sample, in original
position order. All three consume exactly r words and leave the engine in the
same state for that isolated call. An all-zero mask test would have the right
distribution but lose this useful nested coupling to the odd-word legacy path.

Only the private `<true>` instantiation should select the experimental mask;
the default and public `<false>` stream, IDs and metadata must remain unchanged.
Keep half-size reserve, emission, compaction, result handling and verifier code
unchanged. Do not combine the rate change with packed draws, bit scanning,
reservation changes or lifetime changes. A fresh same-source half-rate control
must be rebuilt if extracting the predicate refactors its translation unit.
Share all seven non-KKT production objects and the harness; only the candidate
KKT object selects the experimental rate. The first candidate can be fixed 1/8;
1/4 is a separately declared rate comparison, not a post-result fallback.

Required gates before any future performance release:

- Independent known-word oracle for masks 1/3/7, every low-three-bit pattern,
  empty/one/odd inputs and consecutive calls. Compare exact selected original
  positions, records, compaction and engine states; fingerprints alone are
  insufficient. Test public calls interleaved with private calls.
- Exercise the actual private dispatch, with a sample whose half and eighth
  outputs differ, and a wrong-policy negative gate. Public legacy results must
  match exactly; recursion-wide samples and engine exit states need not match.
- Reuse full KKT differential and independent MSF certificates, including
  disconnected, sparse, dense/parallel, extreme-weight/ID, and multiple-seed
  inputs within the current contract. Unique-MSF IDs must match across rates.
  Root contraction counts must agree on identical inputs; downstream sampling,
  filtering, verifier work and the other existing counters may legitimately
  change. Preserve the existing 65-field schema and meanings.
- Retain all declared graph/sampler seeds, baselines, losses and both clocks in
  any later prospective study. Untimed work diagnostics should report sample
  volume, survivors, forest/component structure and all existing counters.
  For this unchanged scalar one-word-per-record path, total sampling RNG words
  equal `sampling_edge_visits`; unlike packed sampling, no ceiling interval is
  required. Existing counters still do not measure vector reallocations.

Even though direct-call masks are nested, recursive inputs differ immediately:
later calls consume different numbers of words and attach them to different
records. There is no recursion-wide identical-stream or identical-work claim.
Packed sampling at a lower probability would be a separate future change with
its own bit allocation, tail handling and correctness/measurement gates.
