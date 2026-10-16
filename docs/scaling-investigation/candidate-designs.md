# Separate representation experiments

Design only, 2026-10-15. No production patch or benchmark is supplied here. Candidate A changes local lifetimes in `kkt_internal`. Candidate B changes only the LCA sparse-table representation. Candidate C caches prior minimum costs in the retained contraction kernel, conditional on phase evidence. Candidate D specializes the verifier's LCA answer to the ancestor depth it consumes. None changes the sampler, contraction policy, public result type, graph families or timing boundary.

## A. Release dead local buffers before the next expensive stage

### Required invariants

Keep the public `problem& P` completely owned by the caller: do not move from, clear, relabel or compact P in place. Its graph, metadata and ID namespace survive unchanged. Keep all operations that can affect the algorithm in the same order: two contractions, selected-ID appends, root counter assignments, sample generation, sampled recursion, forest recovery, verification, survivor filtering, isolation and remaining recursion. Preserve the exact RNG engine stream, intermediate edge order, selected-ID sequence and all 65 existing WorkStats fields.

This is a lifetime-only change. Do not alter any `reserve`, add an extra counting pass, introduce reusable scratch storage, replace the output set or flatten another data structure in this patch. Allocation/deallocation order and live memory are intended to change; allocation failure timing can therefore change. Equal logical work does not imply equal allocator behavior.

### Scope arrangement

`problem` has a default empty constructor and implicit vector moves. Empty output holders can cross scope boundaries without copying any edge records or incrementing existing logical counters. A concrete arrangement is:

```text
kkt_internal(P, rng, result):
    keep the existing recursion scope and empty-input guard
    int remaining_vertices = 0
    vector<Edge> relevant_edges

    {   // everything needed to produce the remaining graph
        problem G
        {
            problem reduced1
            {
                [edges1, first] = the unchanged first contraction(P)
                append edges1 to result
                reduced1 = move(first)
            }   // edges1 and moved-from first die before contraction two
            retain the existing reduced1 terminal return
            {
                [edges2, second] = unchanged second contraction(reduced1)
                append edges2 to result
                preserve the two root-counter assignments here
                G = move(second)
            }   // edges2 dies
        }       // reduced1's edge storage dies before sampling
        retain the existing post-second-contraction terminal return

        vector<unsigned char> heavy_marks
        {
            vector<tuple<int,int,int,int>> H_MSF
            {
                vector<int> sampled_ids
                {
                    problem H = unchanged sample_edges<true>(G, rng)
                    kkt_internal(H, rng, sampled_ids)
                }   // H dies before forest recovery
                recover H_MSF from G using sampled_ids, unchanged
            }       // sampled_ids dies before verification
            heavy_marks = unchanged verifier(G, H_MSF)
        }           // H_MSF dies before survivor filtering

        unchanged reserve and stable filtering into relevant_edges
        remaining_vertices = G.num_vertices
    }               // G and heavy_marks die before isolate normalization

    problem G_remaining = unchanged owned isolate normalization(
        problem(remaining_vertices, move(relevant_edges), P.max_edge_id))
    kkt_internal(G_remaining, rng, result)
```

The pseudocode names are illustrative; existing counter statements belong beside exactly the same semantic operations as before. `root_after_two_*` must still be assigned after contraction two even if it is terminal, and must remain untouched when contraction one terminates. The original early returns stay ordinary function returns inside nested blocks; no lambda or synthetic recursive invocation is needed.

For the non-Edge-view build, any temporary tuple copy belongs inside the verification block and must outlive the verifier call. It can die alongside H_MSF. If this experiment is deliberately limited to the existing experimental path, an explicit opt-in should select it and the unchanged reference body should remain available. Avoid accidentally claiming all default combinations were tested when only the optimized flag set was built.

Why the releases are safe:

* The second contraction owns its output records; they do not reference reduced1's elements.
* Sampled recursion returns parent-position IDs by value. Recovery reads G, not H's possibly renumbered vertices.
* H_MSF stores its own tuples. The verifier returns an owning mark vector and keeps no borrowed forest/query references after return.
* Stable filtering copies every required surviving record into relevant_edges. Isolation only needs those records, the saved vertex count and P's metadata.
* Result stores integer IDs, never pointers into any released vector.

Do not use `clear()` as evidence that capacity was released; it retains capacity. Avoid `shrink_to_fit()` because it can move live contents and is nonbinding. Lexical destruction is sufficient and makes the ownership proof visible. A vector move transfers storage; it must not accidentally become assignment from an lvalue or pass through the tuple-conversion constructor.

### Diagnostic phase semantics

The uninstrumented end-to-end boundary is unchanged. Earlier frees remain inside the solver interval, so the total includes them rather than moving cleanup outside timing.

For the simplest paired diagnostic, retain existing phase names and let these local destructions fall into the current exclusive `recursion` residual, as they do on exit today. Do not move a `KKT_PHASE(forest_recovery)` guard merely to make its measured share smaller. The allocation hook attributes allocation/free to the phase active at the event, not to the phase that originally allocated the object; a negative phase-local live balance is not by itself an error. Global live-byte accounting must reconcile.

If a named teardown category is needed, add it symmetrically to both reference and candidate diagnostic builds. Its RAII guard must be constructed **before** the owners it is intended to time, or use an explicitly timed destruction operation. A guard constructed after a vector is destroyed first and therefore excludes that vector's destructor. Nested exclusive timing must stop the parent clock, restore it afterward and count child time only once. Diagnostic phase instrumentation is not included in the performance binary.

Validate three distinct facts: (1) all 65 logical fields and exact RNG/results agree; (2) relevant live buffers have ended at the intended boundary; (3) the uninstrumented total improves or does not. Peak requested/usable allocation bytes, allocation count and sampled RSS answer different questions. An allocator can retain freed pages, so lower live buffers need not immediately lower RSS. Early release may change later address reuse; that is an intended consequence, not proof of a particular cache mechanism.

### Focused gates

Use the existing native/sanitizer independent MSF cases, including disconnected and bundled inputs, sparse public IDs and early termination after either contraction. Compare full input bytes/metadata before and after each call. Differentially compare ordered selected IDs where instrumented, public ID sets, RNG final state/word counts, sample/filter graph fingerprints and all 65 counters. A small owner-lifetime observer can record which stage contains each buffer without running a performance campaign. Keep observer output supplementary and compile it off in timing builds.

## B. Flatten the LCA sparse table in level-major order

### Exact transformation

The present [LCA implementation](../../lca/lca.cpp) stores `st[block][level]` as `vector<vector<int>>`, but builds it with level outermost and block innermost. Each cell contains an **Euler-tour position**, not a vertex or a height. Preserve that representation and every `min_by_h` operand order, including its tie choice.

Let `B=block_cnt` and `K=log_2[B]+1`. Replace only st with one owning `vector<int>` of B·K cells and address

`cell(level, block) = st[size_t(level)*B + block]`.

Keep the same rectangular domain, base scan, recurrence, copied tail cells and query formulas:

```text
base:       cell(0,b) = minimum Euler position of block b
recurrence: cell(l,i) = min_by_h(cell(l-1,i), cell(l-1,i+2^(l-1)))
            when the second block exists; otherwise copy cell(l-1,i)
query:      cell(l,bl+1) and cell(l,br-2^l)
```

The base scan currently tests the first element of each block before reading its initialized cell; preserve the condition and zero initialization. Retain current treatment of the partial final Euler block. Do not change `blocks`, the microtables, first-visit arrays, Euler traversal or block size in the same patch. Use size_t for the flattened product/index and verify supported sizes before allocation. A default-constructed LCA still becomes queryable only after successful construction/assignment of its preprocessing state.

### Finite memory and access costs

The integer payload remains exactly `sizeof(int) * B * K`. The original table additionally owns B vector headers and B independently allocated payloads; constructing `st.assign(B, vector<int>(K))` also uses a temporary K-element vector. The flat table uses one allocation for its payload. The structural saving is approximately `B*sizeof(vector<int>)`, plus avoided allocation metadata and temporary storage; the latter are allocator-dependent. Do not turn this into an RSS claim. Record actual `sizeof` values and usable allocations for the tested C++ library instead of assuming the standard fixes a vector header at 24 bytes.

Level-major storage follows the existing build's inner loop. Its two predecessor ranges are contiguous, and both upper-level query answers use the same level. It removes the row-pointer load before each cell lookup. These are concrete access changes, not a guaranteed speedup: query block positions may still be far apart, the level-zero pass now writes a dense first plane, and all other LCA/FBT indirections remain. A flat block-major representation is a possible later control if measurements need to separate allocation removal from transposition; it is not necessary to bundle both into the first candidate.

This table is already asymptotically linear: B≈E/log E and K≈log B. Flattening changes finite constants and storage locality, not the algorithmic bound. It also does not fix a disconnected-verifier query-copy path.

### Counter and correctness policy

Keep `lca_sparse_cells == B*K`, every query count, all tree/graph work and all output/RNG identities identical. Unlike candidate A, exact equality of **all** 65 fields would misdescribe changed initialization: the current sparse-table code charges `initialized_slots += B*(K+1)+K` when K is the actual number of levels (`log_2[B]+1`), equivalently the source expression `B*(log_2[B]+2)+log_2[B]+1`. A flat zero-initialized B*K vector naturally charges B*K, a decrease of **B+K** abstract slots for this particular statement pair. These counters are not byte counts. Either document that single expected delta or explicitly introduce a separate representation-neutral logical counter; do not preserve fictitious vector-header initialization to manufacture equality.

For a narrowly exact paired gate, expose per-call B/K in a diagnostic record and check cumulative initialized-slot delta `-sum(B+K)` while all other current counters agree. Keep implicit allocations/reallocation diagnostics separate. This delta assumes the replacement makes no other new counted initialization and retains all current Euler/microtable arrays and counter statements.

Test every LCA answer against an independent parent-walk oracle on small trees, including ties in vertex depths and partial final blocks. Include sizes around changes in `block_size` and `K`, one vertex, paths, stars, balanced and irregular trees. Then run the verifier direct-mark oracle and full KKT differential gates to catch an incorrect Euler-position/vertex conversion. Compare both flags off/on with the same production objects other than LCA, and report the inherited public result and timing boundary unchanged.

The two candidates should be tested separately, then combined only if each has a useful independently measured result. The first targets retained live buffers; the second targets many allocations and sparse-table addressing. Their gains cannot be assumed additive.

## C. Cache prior minimum costs in the retained kernel

This is conditional on `minimum_scan` dominating or showing increasing time per visited edge. The exact target is [retain_parallel_step](../../kkt/experimental_multigraph_contraction.hpp), not the public deduplicating `boruvka_step` used by an older rejected cache experiment.

Today each endpoint consults `smallest_incident_edge[vertex]`, then fetches the prior cost through `P.graph_edges[index].cost`. The latter address depends on the first lookup. Although input edges stream consecutively, the current minima can be scattered over the entire m-record edge vector.

A narrow replacement is one per-vertex record `{index, cost}`, initialized with `index=-1` and a defined arbitrary cost. Preserve this comparison literally:

```text
if minimum[vertex].index == -1 or edge.cost < minimum[vertex].cost:
    minimum[vertex].index = current_edge_position
    minimum[vertex].cost = edge.cost
```

Do not use `INT_MAX` as an absent-value sentinel: supported extreme costs must still install their first incident edge. Keep strict `<`, endpoint processing order and input iteration order. Equal-cost edges retain the first encountered edge exactly as today, even though the full solver's principal valid-input contract uses unique ordering. All later selected-ID and successor-walk logic reads the stored **index**, retaining its present access to the actual edge endpoints/ID. No vertex or edge reordering is involved.

The current minima index payload is `sizeof(int)*n`. Its cost lookups have an address span of `sizeof(Edge)*m`, normally 16m bytes in this native representation. The proposed paired state is normally 8n bytes, with the cost located beside its index. At m=16n or 32n, that paired state's span is 32 or 64 times smaller than the edge-vector span. This is an address-span contrast, **not** a 32×/64× reduction in actual traffic: there are at most n current minimum entries, some vertices share the same edge, old minima may still be cached, and the stream itself touches the edge vector regardless. The proposal adds cost writes at every successful replacement and doubles per-vertex minimum payload. All can offset its saved dependent cost loads.

Report replacement counts, absent-minimum versus present-minimum checks, allocation bytes and scan time separately. The existing `contraction_edge_visits` remains exactly m for this pass; all selected IDs, component IDs, quotient records, RNG states and recursion volumes should match. `initialized_slots` needs an explicit policy: a paired state contains an extra initialized cost field per vertex. If counting scalar fields, add n, and gate that known delta; if preserving a logical-record convention, document the convention and supply typed-byte diagnostics. Do not claim the 65 fields are complete memory accounting either way.

A separate cost array beside the existing index vector would make an even smaller source patch, but introduces a second array/header/allocation and may fetch index and cost from different cache lines. Choose one representation before measurement; do not silently switch after inspecting results. Preserve the old comparison in an opt-out reference build. If this shared retained helper also changes the retained-B comparator, apply and report it symmetrically or give the altered implementation an explicit identity; do not weaken or silently change the control.

Use focused kernel differential tests for first incident edge, repeated endpoints, extreme signed weights and tied minima, then full solver certificates. The optimization should be evaluated separately from candidate A and B. A faster minimum scan would explain its own phase improvement; it would not establish that all remaining normalized-time growth is cache or TLB latency.

## D. Return ancestor depths directly to the compressed verifier

This is a consumer-specific representation experiment, separate from flattening the sparse table. It returns the information actually used by the filtering algorithm, an application of the practical-filtering principle discussed in [the research note](research.md). It does not replace exact LCA/path maxima with an approximate filter.

### Contract and equivalence

In `test_graph`, the queried vertices are the original vertices of one connected forest component. `fbt_reduction` retains those vertices as leaves and gives fresh IDs to every parent. Thus distinct query endpoints are distinct FBT leaves: neither can be the other's ancestor, and their LCA is a **proper** ancestor of both. The disconnected wrapper first maps a query into its own connected component; cross-component queries never enter this tree query loop and remain unmarked. Empty forests retain their existing early return.

The compressed helper currently consumes an ancestor ID only to evaluate `depth_[upper]` in `add_request` and `lookup`. Add private depth-taking operations with explicit `0 <= upper_depth < depth_[lower]` validation, retaining the existing ID-taking methods as wrappers for their current helper contract. In the opt-in `test_graph` path, cache the returned ancestor **depth** for each graph edge. For a nonloop, submit and later look up both endpoint requests at that depth. Self-loops must still remain unmarked and add no requests. Keep their LCA invocation in the gather pass if requiring the existing `lca_queries` count to match; skipping it is an additional change, not necessary for this candidate.

This substitution preserves each requested mask bit, the propagated masks, traversal state, unique-request ordering, path-maximum value and final heavy mark. It therefore preserves the filtered edge order, selected IDs, RNG stream and recursive trajectory. The special leaf assumption belongs to this caller, not to the generic `LCA` API or arbitrary direct helper inputs.

### Private depth-RMQ representation

Leave generic `LCA::query` and its ID-returning semantics unchanged. A separately selected private class can use the same Euler traversal, block size, first-visit indices, masks and microtable shape, with these precise changes:

* Store an Euler **depth** at each visit instead of its vertex ID. DFS already carries that integer depth; no additional depth traversal is required.
* Remove this LCA object's `height[T]` array. Keep the compressed path helper's own depth array: it is still needed by its traversal and guards.
* Keep each microtable cell as the relative **argmin position**. Build it with direct Euler-depth comparisons, preserving the reference's strict-comparison/tie order and handling of a partial final block. The existing up/down mask condition becomes `euler_depth[i-1] < euler_depth[i]`.
* Store each sparse-table cell as a **minimum depth**, rather than an Euler position. Base-block minima and recurrence become integer minima. Queries convert their two boundary microtable positions to Euler depths and combine these with the middle-block minimum depths. Equal-depth tie identity is irrelevant to the returned value; the microtable still retains its reference tie convention.

An all-vertex parent-walk oracle can validate this private depth query even though the optimized consumer queries leaves. Use `size_t` for allocation/index products and retain the supported integer bounds. Keep nested sparse-table storage in this first experiment; a flat table, compact byte depths or fused FBT construction would confound it with separate representation changes.

### Costs and gates

For a tree with T FBT vertices and E=2T−1 Euler entries, the Euler integer payload/capacity is unchanged; `height[T]` is removed. The nominal saving is `sizeof(int)*T` plus one vector header and its allocation overhead, not a graph-sized saving. The per-edge cached array remains one integer per query edge. Sparse-table and microtable payload sizes remain unchanged. Query comparisons avoid the `height[euler_tour[position]]` dependent chain, and middle-block comparisons need only the stored depths. First-visit, block-mask and microtable accesses remain indirect; this is neither a cache-miss count nor a predicted timing gain.

With no other changes, all logical counters should match except `initialized_slots`, which decreases by T per LCA construction because `height.assign(T,0)` disappears. `lca_euler_entries`, block visits, sparse/micro cells, queries, Q/U and all path-search counters retain their present meanings. Require the exact cumulative initialization delta, not a permissive list of changed fields. Keep the existing generic LCA counters untouched when the opt-in is absent.

Focused gates should compare depth answers against independent parent walking on singleton, path, star, balanced and irregular trees; include block-size transitions, equal-depth minima and partial final blocks. Differential direct-mark tests must cover Edge/tuple inputs, loops, repeated external IDs, extreme/negative weights and disconnected forests. Full KKT cases retain its valid loop-free, distinct-ID/uniquely-ordered contract. Require identical marks, input bytes, selected IDs, RNG and the stated counter identity, plus an actual dispatch discriminator proving the private depth implementation was selected. Any later speed comparison uses fresh paired uninstrumented runs after the baseline diagnostics finish.
