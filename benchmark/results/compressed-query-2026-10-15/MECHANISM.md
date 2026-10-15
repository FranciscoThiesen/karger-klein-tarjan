# Why compressed verifier requests may help dense cores

Deterministic analysis, 2026-10-15. This note contains bounds and implementation hypotheses, **not measured benchmark query counts, memory use, runtime gains, or crossover evidence**. The implementation subsequently passed [native and sanitizer validation](validation/NATIVE_VALIDATION.md); performance capture remains pending.

Sources: `verifier/verifier_v2.cpp:63-173,175-273,348-410,458-597` and `verifier/median_table.hpp:14-31` in `/Users/random_person/Desktop/kkt-edge-verifier-view`; candidate helper [`verifier/experimental_compressed_queries.hpp`](../../../verifier/experimental_compressed_queries.hpp). The hierarchy construction/contraction facts are derived in [the hierarchy retention derivation](../density-search-2026-10-15/HIERARCHY_RETENTION.md) from `benchmark/core_attachment_fixtures.hpp`.

## Which vertices and edges the bounds describe

Consider **one connected component of the sampled forest passed to the tree verifier**, not the original benchmark graph. Let:

- `r` be that component's vertex count before full-branching-tree reduction.
- `m` be the number of verifier graph edges whose endpoints lie in it, including any loops; write `m0` for its non-loop edges.
- `N` be the reduced full branching tree's vertex count and `h` its root-to-leaf height.
- `Q` be the logical proper-endpoint-to-LCA requests made for these edges, including duplicates.
- `U` be the distinct `(lower vertex, ancestor depth)` requests.

The reduction repeatedly groups at least two active vertices and gives **every** active vertex a fresh parent in each round. Consequently `N<2r`, `h<=floor(log2(r))`, and the `r` original component vertices are leaves at the same depth `h`. This equal-depth fact follows from this implementation's synchronized reduction; it should not be asserted for an arbitrary full branching tree.

The forest wrapper sends only within-component graph edges into these tree calls. Edges joining different sampled-forest components remain unmarked and generate no tree requests. Empty forests, empty query sets, and singleton components with no forest edge take existing early-return paths. Their work must not be inserted into these component formulas as if a full tree call occurred.

## Unique requests: a general bound and the stronger production bound

On a fixed vertex's root path, each ancestor depth identifies exactly one ancestor. If `R[v]` is its local request-depth mask, the proposed helper stores

```
U = sum_v popcount(R[v]).
```

A vertex at depth `d` has exactly `d` proper ancestor depths, so for any valid request set on the reduced tree,

```
U <= min(Q, sum_v depth(v)) <= min(Q, N*h).
```

This is a deterministic bound for the particular tree and requests. It makes no randomness assumption. It also explains why propagated masks `D[v]` cannot substitute for local masks `R[v]`: `D` carries descendant requests needed for the traversal, whereas `R` specifies answers actually requested at this vertex.

Production verifier queries have a stronger restriction: their lower endpoints are among the `r` original component vertices, all reduced-tree leaves. A non-loop edge joins two distinct leaves, so its LCA is proper for both endpoints. A loop has no proper endpoint request. Therefore

```
Q = 2*m0,
U <= sum_{v among original component vertices} min(deg0(v), h)
  <= min(2*m0, r*h),
```

where `deg0(v)` counts incident non-loop query edges with multiplicity. Parallel edges and repeated endpoint pairs count repeatedly in `Q` and degree but may reuse exactly the same answer. Different opposite endpoints can also reuse an answer whenever their LCAs with `v` have the same depth.

For `Q>0`, writing `average_degree = 2*m0/r` gives

```
U/Q <= min(1, h/average_degree).
```

If all queries are loops, `Q=U=0`; the ratio is undefined, not zero-valued evidence. Across multiple forest components, sum the per-component bounds: `Q_total=2*sum m0_i` and `U_total<=sum r_i*h_i`. Do not use the full verifier graph edge count as `sum m0_i` when edges cross forest components.

These bounds do not guarantee `U=O(r)` as graph sizes grow: `h` can grow with `r`, and sparse request sets can have `U=Q`. The implementation remains linear because it visits only set bits and `U<=Q<=2m`, not because it scans all `h` depths for every vertex. Its word masks also retain the existing supported-height constraint.

## Why cheap leaf attachments create an opportunity

Cheap leaf attachments contract away early, while many expensive edges among the surviving core vertices remain as separate physical edges. The verifier can thus receive many incident query edges per remaining vertex. There are only `h` possible proper ancestor depths at each such vertex, regardless of its query degree. Once average degree is much larger than `h`, substantial duplicate requests are unavoidable by the bound above.

This mechanism is about the **graph presented to the verifier after contraction and the forest's reduced tree**. The original benchmark density alone does not establish the duplicate ratio; forest components and the retained internal edge count matter. Neither does the bound require that the original input contain parallel edges: contractions can create parallel edges, and distinct neighbors can share one ancestor-depth request even without parallelism.

The opportunity is not exclusive to the hierarchy construction. Any residual graph with high within-component degree and a shallow reduced forest tree satisfies the same bound, including uniform random inputs when they produce such residuals. Conversely, a sparse graph family does not gain a guaranteed large duplicate reduction from this argument. The implementation must remain graph-independent; the bounds describe when its representation is promising, not a family-selection heuristic.

For the specifically engineered `leaf_hierarchy4` construction, a useful conditional calculation is available. Let the original benchmark have `n` vertices and `m_original=n*d` edges, with `n` a supported power of two. The `q=n/4` core vertices have three cheaper attachments each, a cheaper hierarchy-ranked core path, and `C=m_original-n+1` distinct nonpath chords. The first contraction removes the attachments; the second pairs adjacent core vertices. No nonpath chord is internal to one such two-vertex block. Thus after these two root contractions:

```
r_root = n/8,
m_root = m_original - 7*n/8,
average_degree_root = 2*m_root/r_root = 16*d - 14.
```

**If the sampled forest is connected on this root residual graph**, the root verifier has `Q=2*m_root` and

```
U/Q <= floor(log2(n/8)) / (16*d - 14).
```

For a purely illustrative substitution `n=1,048,576,d=32`, this upper bound is `17/498`, about 3.4%; for the same `n,d=64`, it is `17/1010`, about 1.7%. These are conditional worst-case bounds on the number of distinct answers relative to expanded requests, **not observed counts for either study or any particular seed**. A sampled forest with multiple components requires the component-wise formula instead. The exact root dimension formula belongs to `leaf_hierarchy4`, not automatically to distance-weighted, shuffled-weight, road, grid, or arbitrary leaf-attached inputs.

At fixed core size, increasing retained density raises `Q` while `r*h` stays bounded. Increasing core size also increases the possible tree height, so density and size have different effects. All `O(m)` edge scans and LCA queries remain; compressing answers does not make the verifier's entire cost proportional to `U`.

## The allocation lifetimes matter

The following are nominal live array-element bytes on the target (`int`/mask 4 bytes, `size_t` 8 bytes), excluding vector headers, capacity beyond size, allocator overhead, traversal stack, and unchanged external graph/tree/LCA storage. Let `K` denote the common bytes for the path stack and median table once allocated.

| Phase | Current implementation | Proposed implementation |
| --- | ---: | ---: |
| Current query-record construction, before tree solver creation | `8Q + 4m + 16(N+1)` | Not applicable: no query-record fill pass or copied cursor array |
| Proposed request setup, before values/path/median allocation | Not applicable | `4m + 20N + 8` |
| Answer traversal, before output marks | `8Q + 4m + 16N + 8 + K` | `4U + 4m + 20N + 8 + K` |
| Final graph pass, including live output marks | `8Q + 5m + 16N + 8 + K` | `4U + 5m + 20N + 8 + K` |

The current construction holds query records, one cached ancestor per edge, offsets, and a copied offset/cursor array. It destroys the ancestor cache and copied offsets **before** constructing depth, propagated masks, and the per-edge maximum array. The proposal precomputes depth, keeps a separate local mask, retains its cached ancestor array through traversal, and stores unique values. It has no per-edge maximum array. Thus the proposal's cached `4m` bytes replace the current maximum's `4m` bytes during traversal; they must not be counted as both an added cache and a retained maximum.

The final-phase nominal array difference, current minus proposed, is

```
8Q - 4U - 4N bytes.
```

For `Q=2m`, even `U=Q` reduces this phase's arrays by `8m-4N` bytes; a very sparse query set on a large tree can instead lose to the new local-mask cost. Smaller `U` increases the potential saving. This formula describes particular arrays at one phase. It is not a global peak allocation/RSS formula: all enclosing recursive graphs, component buffers, LCA state, allocator capacity/retention, and phase overlap still have to be included in an actual memory assessment.

The initialized-slot work counter is a different quantity. Under the proposed allocation placement, its per-tree reduction is exactly `m+Q-U+1` slots because the removed copied offset array and maximum offset the added local masks and values. Slots are heterogeneous elements; this identity cannot be interpreted as bytes.

## Plausible execution effects, and what remains uncertain

The current code evaluates every request and updates `maximum[edge_position]` while traversing vertices. Those edge positions can be scattered across a large graph array. The proposal computes each unique answer once, writing a contiguous range for that vertex. Different vertex ranges are visited in tree traversal order, so these writes are **not necessarily globally sequential by array index**.

The final graph pass reads the graph and cached LCAs sequentially, performs popcount-based ranks, gathers one or two compact per-vertex answers, and writes marks sequentially. It removes the query-record fill pass: three full graph passes inside `compute_heavy_marks` become two, while the number of LCA queries stays the same. A small unique-answer working set may make repeated indexed reads cheaper than scattered writes to `maximum[m]`; deleting query records also reduces initialization and memory traffic.

These are hypotheses about constants, not measured causal explanations. The candidate adds a depth pass, local-mask storage, guard/rank work, and dependent value reads. Low-duplication inputs may gain little, and the existing Hagerup traversal, median table, LCA work, forest construction, sampling, contractions, and public result handling remain. Exact oracle equivalence and paired work identities should be established first; only a separately released timing experiment against the same retained-edge Boruvka and other unchanged solvers can determine whether this helps in practice.
