# Compressing verifier requests by lower vertex and ancestor depth

Source-only assessment, 2026-10-15. No implementation, import, build, test, native execution, or timing was performed for this assessment. Source is `/Users/random_person/Desktop/kkt-edge-verifier-view`.

**Recommendation:** this is a sound, bounded next implementation experiment. It removes duplicate answer work and the per-edge query-record representation without changing sampling, the forest, the full branching tree, or Hagerup's traversal state. It has a clearer structural opportunity than changing a sampling reserve alone. That is a reason to test it, not evidence that it is faster or that it closes the remaining gap to retained-edge Boruvka.

## What the current implementation does

Let `m` be the number of query edges in one connected-tree verifier call; `n` the original component vertex count; `N` the reduced full branching tree vertex count; `Q` the number of proper endpoint-to-LCA requests, at most `2m`.

In `verifier/verifier_v2.cpp:348`, `compute_heavy_marks` performs three query-graph passes:

1. Cache one LCA ID per graph edge and count its proper endpoint requests.
2. Fill ranges of `{upper_ancestor, graph_edge_position}` records. Each record is two `int`s, 8 bytes on the measured target. The temporary LCA cache is then destroyed.
3. After solving the requests, compare each edge weight against its accumulated maximum and produce positional marks.

`tree_path_maxima::init` (`:213`) ORs the ancestor-depth bit of every request into `D[v]`. `visit` (`:232`) evaluates every request separately, then updates `maximum[edge_position]`. Repeated requests therefore already collapse in the traversal-state masks but still occupy separate records and repeat answer evaluation and scattered maximum writes.

For ordinary non-loop queries, original graph endpoints are leaves of the reduced tree and neither is their LCA, so `Q=2m` (subtract self-loops if present). IDs do not identify these requests; edge positions do.

## Why the compressed key is sufficient

For a fixed lower vertex `v`, each depth on its root path identifies exactly one ancestor. Consequently `(v, depth(ancestor))` determines the same proper ancestor path as `(v, ancestor_ID)`. Requests with this key have exactly the same answer even when their graph edges have different other endpoints, weights, IDs, or positions.

Maintain an immutable local-request mask `R[v]`, containing precisely those ancestor-depth bits requested at `v`. Keep the propagated mask `D[v]` separate:

```
D[v] = R[v] OR union over children z of (D[z] AND NOT bit(depth[v]))
```

This is the current recurrence. Replacing a list of repeated OR operations by `R[v]` leaves every `D[v]` unchanged. The existing traversal's `P`, `S`, `binary_search`, and recursion depend only on the tree, weights, and `D`; they do not depend on request multiplicity or the destination edge index. All of these states and binary-search outcomes therefore remain identical.

At vertex `v`, for every set bit `d` in `R[v]`, evaluate the unchanged answer expression once:

```
answer(v,d) = weight[P[median[down(bit(d), S_v)]]]
```

The same expression currently contributes to every corresponding edge maximum. Storing it once and later combining the two endpoint contributions produces exactly the same per-edge maximum and marks. This is a source-level equivalence argument for the existing implementation; it does not require a new proof of the underlying path-maxima algorithm.

**Do not use propagated `D` as the output-request mask.** It includes descendant requests needed by the traversal and excludes some local-versus-propagated distinctions. `R` must remain available through the final edge pass.

## Concrete representation and pass order

1. Precompute full-tree `depth` and `height` in one `O(N)` child/sibling traversal, retaining that depth array for the existing traversal. This requires an additional tree pass, not a second retained depth array. Avoid changing LCA internals in this first experiment; its current depth information is private (`lca/lca.hpp:12`).
2. Allocate zeroed `R[N]` and one `int` LCA-ID or LCA-depth cache per graph edge. In one graph pass, perform the same LCA query as before, cache it, and set the proper endpoints' bits. Keep logical expanded request count `Q` for diagnostics.
3. Build `offset[N+1]` by prefix-summing `popcount(R[v])`. Allocate `values[U]`, where `U=offset[N]`. Use `size_t` offsets, as the current query ranges do.
4. Run the existing bottom-up mask propagation, using local `R[v]` instead of reading records. Run the existing path-state traversal. Iterate only the set bits of `R[v]` in increasing depth order and fill the vertex's contiguous `values` range once.
5. Make one final sequential graph pass. For a requested depth `d`, its index within the vertex range is

```
rank(v,d) = popcount(R[v] & (bit(d) - 1))
value = values[offset[v] + rank(v,d)]
```

Combine the valid halves starting from `INT_MIN`, and apply the unchanged strict comparison with edge cost. Retaining the LCA cache through traversal replaces the old per-edge maximum array; it avoids another graph pass or repeated LCA queries.

Caching the ancestor ID permits the original explicit `ancestor != endpoint` test. Caching only its depth is also correct: because it is the true LCA, `depth[endpoint] > cached_depth` is exactly the proper-ancestor test. Prefer the clearest version for the first experiment; both caches are one `int` per edge.

Use a normal initialized values vector initially. Eliminating its initialization is a separate change. Each entry is written once by construction, but combining allocation changes into this experiment would complicate review and counter interpretation.

## Contracts and integer safety

- **Proper ancestors:** test whether a half exists before computing its rank or reading its value. In diagnostic builds, require that the requested bit is present and that the index lies in this vertex's range. A missing bit is an invariant violation, not a zero-valued answer.
- **Self-loops:** preserve the existing API behavior: no path requests and an unmarked result. Explicitly skip them before lookup (`verifier_v2.cpp:405`; independent oracle at `test/edge_verifier_view_test.cpp:46`). Do not silently replace this with a mathematical convention for an empty path.
- **Disconnected forests:** keep `heavy_edge_marks_impl` unchanged (`verifier_v2.cpp:458`). It passes only edges within each forest component to a tree verifier and leaves cross-component edges unmarked. Singleton/empty-forest/empty-query fast paths must remain unchanged.
- **IDs and positions:** never use edge IDs as keys or value destinations. The public tuple and Edge overloads and component positional scatter must preserve arbitrary and repeated IDs (`:571-594`, `:602-621`).
- **Weights:** retain strict `maximum < cost` and `INT_MIN` as the identity for combining absent halves. Zero is wrong for negative weights. Include `INT_MIN`, `INT_MAX`, and equality boundaries in the oracle gates.
- **Masks in C++17:** use a fixed unsigned word for new local-mask operations, e.g. `uint32_t{1} << d`; require the supported depth before shifting. The lower-bit rank mask is `bit(d)-1`, including zero when `d==0`. Call trailing-zero intrinsics only on nonzero masks, and iterate by clearing the lowest set bit. `std::popcount` is C++20; use the project's C++17-compatible builtin/helper. Do not introduce a shift by the word width.
- **Preserve the existing state arithmetic:** converting all of `down`, `S`, `D`, and median indexing to unsigned is a separate proof/change. The current median-table contract is `0 <= height < numeric_limits<int>::digits`, i.e. height at most 30 on the target (`verifier/median_table.hpp:15`). Enforce the applicable bound before new mask construction; a generic claim that any height below 32 is safe is too broad for the unchanged solver.
- **No larger input contract:** existing graph/FBT vertex IDs and `M` use `int`. This experiment should neither promise arbitrary-sized graphs nor silently truncate masks or offsets. Keep all existing valid-input assumptions and assertions.

The reduced-tree height bound comes from this actual reduction, not just from calling a tree full branching: every active component has a selected incident tree edge, each resulting component contains at least two old active vertices, and every active vertex receives a new parent in each round (`verifier_v2.cpp:94-167`). Active counts at least halve, so height is at most `floor(log2(n))`, and `N<2n`. Original vertices advance together and are leaves. The existing median table has at most `2n` entries under this bound. The bounded benchmark vertex counts are well inside the current signed-mask height domain.

## Complexity and memory opportunity

There are no hashes or sorting steps. The new work consists of the depth pass `O(N)`, one setup graph pass `O(m)` with unchanged LCA count, mask/prefix construction `O(N)`, unchanged mask propagation and path-state traversal, `O(U)` answer evaluations, and one final graph pass `O(m)`.

```
U = sum_v popcount(R[v]) <= Q <= 2m
```

Thus the representation change preserves the existing `O(N+m)` verifier bound under its word-operation model. Do not claim `U=O(n)` universally: distinct depths at one endpoint can differ, and `U` can equal `Q`. Enumerating only requested set bits is important; blindly scanning every depth at every vertex introduces `O(N*height)` work in a growing-word analysis. The original median table and tree traversal remain unchanged.

During answer traversal, ignoring common arrays and allocation overhead:

| Representation | Edge/query-dependent bytes on this target |
| --- | ---: |
| Current | `8Q + 4m` for query records and accumulated edge maxima |
| Proposed | `4U + 4m` for unique values and retained LCA cache |

The proposed version additionally retains `4N` bytes of local masks; common offsets, depth, propagated masks, tree state, and output marks remain. At `Q=2m`, even without duplicate requests (`U=Q`), edge/query-dependent storage falls from `20m` to `12m` bytes before adding local masks. With many duplicates, it can fall further. For a very sparse query set over a large tree the new local-mask cost can outweigh these savings. These are explicit-array sizes during this phase, **not measured allocation peak or RSS percentages**. Construction has different live-array peaks: the old code also has a temporary second offset array and LCA cache while filling records.

Within `compute_heavy_marks`, full query-graph passes fall from three to two and each edge still receives one LCA query. The outer disconnected-component wrapper retains its own scans and materialization. No claim that the whole verifier has only two scans is intended.

The final pass trades random writes into a large `maximum[m]` array for two indexed reads from compact per-vertex values and popcounts. Sparse requests can have little deduplication; the depth pass, local masks, rank work, and dependent value loads can offset the savings. Hardware cache behavior, duplicate ratios, and compiler code generation must be measured. Nothing here establishes a runtime improvement or a crossover against retained-edge Boruvka.

## Correctness and accounting gates before timing

1. Reuse and extend the independent explicit forest-walk positional oracle (`test/edge_verifier_view_test.cpp:33`). Compare the reference and candidate tuple/Edge marks per position, plus public ID-set adapters. Include repeated endpoint pairs with differing costs/IDs; many distinct opposite endpoints sharing one lower-vertex/depth key; different depths at one vertex; root and nearest-ancestor depths; sparse unique requests; equal weights; negative/extreme weights; reversed/permuted edges; self-loops; disconnected trees/isolates/cross-component edges; and empty calls. Keep the current valid forest contract.
2. Independently exercise rank indexing at depth zero and the highest supported mask positions, noncontiguous masks, zero masks, and all-present masks. These helper-level boundary checks must not allocate a giant median table merely to reach a high bit. Test that every requested value is written exactly once and no unrequested slot is accessed. Actual tree fixtures should exercise both halves and the proper-ancestor guard.
3. Add a linked-candidate discriminator: on a fixture with `U<Q`, verify that the compiled candidate dispatch actually uses unique-request storage and emits the expected `Q`, `U`, and masks/ranges. A correct result alone cannot detect an accidentally linked reference path. Keep optional observations compiled out of performance builds.
4. In diagnostic comparisons, require identical propagated `D` and path traversal/binary-search behavior. Full KKT runs must retain exactly the same sampling engine states, sample edges/order, forests, heavy marks, recursion results, and final IDs for each seed. Retained-edge contraction and all competitors remain unchanged. An independent MST certificate and sanitizer run are still required.
5. Do **not** require all 65 work counters to stay equal: this optimization intentionally changes query visits, initialization, and graph scans. Preserve `verifier_queries` as the expanded logical request count `Q`, and report `U`/duplicate fraction separately. Define actual-execution counter placements before collection; the old request-visits count is `4Q` across construction/init/visit, while the new version must account honestly for setup, unique answer visits, and final rank lookups. FBT/LCA counts, structural traversal counts, and binary-search counts/steps should remain identical; mask/depth-pass visits and initialized slots should reflect the added/removed work. No heterogeneous counter sum should be treated as CPU time.
6. Keep the first implementation isolated under one macro or equivalent private dispatch with a fresh reference build from the same source and toolchain. Use the frozen six-solver harness and unchanged retained-edge Boruvka control. Start with exact-equivalence correctness gates and untimed diagnostics; only then consider a separately released paired timing study.

The highest-value early diagnostic is the distribution of `U/Q` and unique-answer working-set size by verifier call, together with retained-reference edge/query counts. It directly tests whether the duplicate-sharing mechanism is active. It does not need new graph families or any weakening of the existing competitors.
