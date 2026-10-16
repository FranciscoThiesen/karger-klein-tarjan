# Source audit of the current KKT scaling path

This is a source and accounting audit, not a new timing result. The reviewed production revision is `a8f506b8490ffafabb7caf0fa46978f87edb1799`. Source locations below refer to that revision, before any new instrumentation. No production code was changed for this audit.

**Finding:** I found no remaining unconditional `m log n` loop in the optimized path. The two conspicuous logarithmic loops—LCA sparse-table construction and Hagerup's per-vertex binary search—have linear aggregate bounds under the actual caller's invariants. This does **not** establish that every measured execution does linear work, or that each logical operation costs a size-independent amount of real CPU time. Recursive edge volume is randomized; allocation, locality and several other costs are absent from the 65 counters. Matching logical work and phase measurements to the exact Google fixtures is the next discriminating experiment.

## Which implementation this audits

The current Google driver links the eight recorded production objects from the eighth-sampling experiment. Its measured KKT path has:

| Translation unit | Relevant flags / behavior |
|---|---|
| `kkt/kkt.cpp` | `KKT_EXPERIMENT_RETAIN_PARALLEL`, `KKT_EXPERIMENT_EDGE_VIEW`, `KKT_EXPERIMENT_EIGHTH_SAMPLING`: retain every crossing quotient record; pass `Edge` queries directly; private scalar probability 1/8 |
| `verifier/verifier_v2.cpp` | `KKT_EXPERIMENT_COMPRESSED_QUERIES`: share requests by lower vertex and ancestor depth |
| `lca/lca.cpp` | Farach-Colton–Bender-style Euler/block RMQ; unchanged across those variants |
| Other five objects | Linked for the harness/other algorithms; linking union-find or Kruskal does not mean KKT calls them |

The authoritative recorded flags and object identities are in `benchmark/results/eighth-sampling-2026-10-15/validation/timing-build-eighth-build-record.json`; Google's reuse is recorded in `benchmark/results/current-complexity-2026-10-15/validation/build-attempt04/inner/build-record.json`. KKT object SHA is `8db016001ef1bd2173696f6942538819e0949e2b5e2825e2d7c093d979e6402b`; verifier is `e982c047394b1c131233b248d3e7d0733064e45fc66faba963eff3f0eac6f4e9`; LCA is `c7d6f8f4c332846ccfe17ccd1435fbfb2780de00f477a060655fb3af309b406c`. These are recorded historical identities, not a claim of a new native build in this worktree.

An ordinary default build is a different implementation: deduplicating contractions, tuple query conversion, individual requests, half sampling. A future diagnostic must explicitly enable all four relevant flags. `test/complexity_test.cpp` currently contains default-path equalities such as `path_query_visits == 4*verifier_queries`; that assertion is unsuitable for the compressed path. For the latter, visits are `2Q+U`, where Q is the logical request count and U the stored distinct requests.

The public timed boundary includes conversion from input tuples to `Edge`, KKT's internal temporaries and their destruction, RNG initialization, and construction of the final ID hash set. Returned-set validation and destruction occur afterward. See `benchmark/current_complexity/current_complexity.cpp:113–145` and `benchmark/retention_control.cpp:222–250`. Reference generation, sorting and cycle certification are outside that native interval. Google's process-CPU envelope additionally includes small loop/timer machinery; it must remain distinct from the explicitly recorded native CPU interval.

## Loop-by-loop accounting

Use v and e for one recursive graph; q and r for its quotient after two contractions; L for the original vertices of one verifier tree; T for its generated branching-tree vertices; E for its Euler-tour length; Q for logical ancestor requests and U for distinct compressed requests.

### Contraction, isolation, sampling and recursive assembly

* `experimental_multigraph_contraction.hpp:18–135`: three complete edge passes for a nonterminal contraction, or one for the terminal fast return. Successor walks mark and finalize each vertex once. Output reservation is the exact crossing count. The pass bounds are deterministic O(v+e), including parallel records; there is no sorting, hashing or union-find here.
* `kkt.cpp:189–240`: isolation computes degrees, scans vertices, and optionally rewrites endpoints in the already-owned vector. The rvalue path is used by sampling/filtering. No recursive full-vector copy is hidden by the by-value owned helper: the caller moves its temporary into it.
* `kkt.cpp:247–273`: exactly one MT19937 result per visited input edge, then a constant-time mask test. `rng` is passed by reference. It is initialized once in public `kkt`, not restarted at recursive calls. The eighth experiment still reserves `floor(r/2)` slots; it does not reserve r/8 and does not pack bits from one word.
* `kkt.cpp:307–397`: contractions append selected IDs to vectors. A sample's temporary IDs are positions in its parent G; forest recovery indexes G directly, once per returned forest edge. No recursive root-ID bitmap, ID hash lookup, sorted join or whole-parent search remains. `problem` moves owned vectors; `G = move(reduced2)` and the final owned isolation are transfers, not element copies.
* Result-vector geometric growth can relocate previous IDs, but is amortized storage work, not an extra search for each edge. The present counters do not record those implicit relocations. The final public hash set is constructed only once at the public root.

Each child has at most v/4 vertices: two contractions halve the nonisolated population, and later normalization only removes vertices. Consequently total recursive vertex volume is deterministically at most `2*n` and recursion depth is O(log n). A logarithmic recursion depth does not itself imply `n log n` work; disjoint levels' vertex volume falls geometrically. There may be many calls, but each nonempty call has at least two vertices, so their number is O(n).

Recursive **edge** volume needs a separate argument. With ideal independent fixed-p sampling, expected sample size is pr and expected F-light edge count is at most q/p, including disconnected sampled forests and retained parallel edges. The familiar induction is therefore available if local verifier/storage work is linear. Actual MT streams and a handful of graph/sampling seeds are not an empirical average over the theorem's full probability space.

One useful deterministic check uses correctness of the sampled MSF F: every sampled edge outside F is F-heavy. Thus for each call, sample size X and retained size Y obey `X+Y <= r+|F|`. The corresponding existing cumulative counter check is:

```text
sampled_edges + filtered_edges
    <= sampling_edge_visits + verifier_forest_edges
```

This is a necessary invariant, not a replacement for the MST certificate. It also gives a worst-realization bound: if M_d and V_d are the total edge/vertex input volumes at recursion depth d, then `M_(d+1) <= M_d + V_d/4` and `V_d <= n/2^d`. Hence each level has at most m+n/2 edges, for O(log n) levels: O((m+n) log n) edge volume is a valid deterministic upper bound without the sampling expectation. It must not be confused with an observed lower bound or the expected-linear theorem.

### Forest partitioning and full branching trees

`verifier_v2.cpp:489–628` has two different constant-cost paths. A forest with n−1 edges goes directly to tree verification. A nonempty disconnected forest builds adjacency, labels components, remaps vertices, materializes each component's forest and within-component graph queries, verifies relevant components, and scatters marks back. Its explicit loops are O(v+e): it does **not** rescan all e edges independently for each component. Cross-component graph edges remain unmarked/light without a path query. Empty forest/graph paths exit early.

The partition branch nonetheless has a large constant: additional graph scans, tuple writes, nested-vector growth, and many allocations. A discontinuous change from connected to disconnected forest can change runtime without changing a Big-O bound. Existing aggregate partition identities help, but per-call component sizes and counts would localize this directly.

`fbt_reduction` (`verifier_v2.cpp:72–176`) receives a **tree**, not the original dense query graph. At each round its contracted active graph is again a tree, so active edges equal active vertices minus one and both shrink geometrically. Total round-vertex volume is less than 2L, total active-edge volume less than 2L, output T<2L. Fresh IDs mean the capacity-2L arrays are never cleared once per round. `current_graph` retains old adjacency vectors, but each vertex ID is active in only one round; their combined live contents remain O(L). The initial forest-edge copy and constructed tuples are explicitly counted.

Every active component is attached to a new parent in every round. Therefore all original vertices become leaves at the same depth h, each internal vertex has at least two children, and `2^h <= L`. This equal-depth property matters; an arbitrary unbalanced full branching tree would not suffice for the median-table bound.

### Median table and the apparent Hagerup logarithm

`median_table.hpp:15–31` allocates `2^(h+1)` integers and fills one entry in constant work, using the previously computed inner mask. Since `2^h <= L`, storage and work are at most 2L. The historical per-mask bit scan is gone. Repeated tables in distinct components add O(sum L), not a table proportional to the root graph each time.

`experimental_compressed_queries.hpp:54–64` really contains a binary-search loop. One vertex can take O(log h) steps, but charging that worst case to every vertex is unnecessarily pessimistic. Let q_v count requests originating in the subtree of v. Initialization only unions descendant request bits and removes expired depths; `down` chooses at most one predecessor per requested depth. Thus the searched mask has at most q_v bits, and the vertex costs O(1+log2(1+q_v)).

At distance i above the equal-depth leaves, there are t_i≤L/2^i vertices and their disjoint subtrees contain at most Q requests. Concavity gives

```text
sum_level log2(1+q_v) <= t_i*log2(1+Q/t_i)
                         <= (L/2^i)*log2(1+(Q/L)*2^i).
```

Use `log2(1+a*2^i) <= log2(1+a)+i`, then sum the two geometric series. Total search work is O(L+L*log2(1+Q/L)) ⊆ O(L+Q). In the compressed implementation the same argument can charge distinct requests U, while request addition and lookup still cost O(Q). This source-derived argument was independently checked by the theory reviewer. It applies to the equal-depth FBT caller, not arbitrary external child/sibling arrays.

The remaining compressed loops explicitly traverse tree vertices, requested set bits, and graph endpoints. `__builtin_popcount`/`ctz` and bit arithmetic operate on fixed-width machine words; they do not loop over vertex IDs. Median and path masks require the checked height domain (`h < numeric_limits<int>::digits`); this is a represented-input/word-RAM assumption, not an arbitrary-size theorem about C++ integers.

A conservative deterministic regression bound, including the ceiling in binary-search halving, is `path_binary_search_steps <= 4*fbt_input_vertices + 3*verifier_queries`. Indeed the per-vertex ceiling adds at most T<2L; the geometric sum contributes at most `2L + (2/ln(2))*Q`. Sum this inequality over verified tree components. The theory reviewer independently checked this constant and the recursive-volume identity above. This proposed assertion has not been executed as a new test here.

### LCA: a sparse table without an n log n build

`lca.cpp:23–107` builds an Euler tour of E=2T−1 entries, a linear log table, and blocks of size `b=max(1,floor(log2(E))/2)`. There are `B=ceil(E/b)` blocks. The visible nested sparse-table loop builds

```text
B * (floor(log2(B))+1)
```

cells, which is O(E), because B=O(E/log E). It is not a sparse table over all E individual positions. Microtables have at most `2^(b−1)` possible shapes and b² cells per materialized shape; worst aggregate O(sqrt(E)*log²(E)) is also O(E), with tiny cases handled by b=1. Only shapes actually encountered are built. `LCA::query` (`121–142`) uses a bounded number of table accesses, divisions/modulo operations and minima, with no search loop.

Those bounds hide finite-size factors and access patterns. Block-size changes at thresholds, `B log B / E` is not constant at finite E, and actual shape diversity can change. The nested vectors allocate B sparse rows and b rows per encountered microshape. Query lookup involves dependent accesses through first-visit, block tables, Euler tour and height arrays. Linear operation count does not mean those accesses have the same cache/TLB latency at 1K and 1M vertices. Existing LCA counters already expose cells, shapes, Euler entries and query counts; their normalized trends should be inspected before changing this code.

## Work absent from the 65 counters

The counter header explicitly limits its claim (`common/work_stats.hpp:8–12,43–45`). It is not an instruction, byte-traffic or allocator model.

| Missing/distorted work | Relevant source | What to record separately |
|---|---|---|
| Prior-minimum random edge loads; branch outcomes | retained contraction 28–37 | Successful replacements, present-minimum comparisons; phase CPU plus a separate profiler if available |
| Implicit vector growth/relocation | samples, result IDs, FBT/component adjacency and partition vectors | Capacity-change events, old live element count, element width; distinguish logical relocation from actual bytes copied |
| Allocator calls, allocator metadata, page faults, release work | all vectors and final hash set | Allocation count/bytes and live requested-capacity watermark by exclusive phase; process memory/fault observations separately |
| Different slot widths | initialized_slots mixes bytes, ints, size_t and vector headers | Typed nominal-byte accounting; do not multiply all slots by four |
| Hash buckets, comparisons, node allocations and rehash internals | `kkt.cpp:406–415` | Time final reserve+insert separately; returned bucket_count/load/max bucket occupancy outside the timed region if useful |
| MT initialization/state transitions | `kkt.cpp:260–262,407` | Existing sampling visits are exact engine-word count for this scalar path; root initialization is fixed work; instruction cost needs profiling |
| Deallocation and nested-vector header destruction | scopes in verifier, LCA, recursive KKT | Explicit teardown phase or exclusive residual with stated boundaries |
| Hardware cache/TLB misses, bandwidth and prefetch | scattered and sequential arrays | Only claim these after suitable profiling; counter ratios alone cannot identify them |

There is no union-find inverse-Ackermann factor or comparison sort in the optimized KKT path. The remaining public `unordered_set<int>` depends on average constant-time hash behavior and allocates result nodes. `reserve(selected_ids.size())` avoids repeated growth but does not avoid node construction or collisions. It does not provide a worst-case guarantee for adversarial IDs. The timed fixtures use dense unique IDs; sparse-ID counter equality tests prove bookkeeping independence, not equal hash costs for every ID assignment.

## Buffer lifetimes: a concrete repair candidate, not yet implemented

The recursive function currently keeps the following storage alive beyond its last semantic use:

| Storage | Last required use | Currently retained until |
|---|---|---|
| `edges1`, `edges2` | insertion into result, lines323/334 | function exit |
| `reduced1.graph_edges` | second contraction, line330 | after final recursive call |
| `H.graph_edges` | sampled recursive call, line350 | after final recursive call |
| `kkt_h_result` | forest recovery, line362 | after final recursive call |
| `H_MSF` | verifier, line367 | after final recursive call |
| `G.graph_edges`, `heavy_marks` | survivor filtering/normalization, lines380–393 | after final recursive call |

If the first quotient has e1 records and the second has r, immediately before final recursion the frame can retain Edge capacities of at least `e1 + r + floor(r/2) + r`, plus its caller-owned input, sampled-result IDs, forest tuples and r mark bytes. The last r is the survivor vector's full-r reservation, even if its size is much smaller. This is **nominal reserved capacity**, not a measured allocation/RSS bound: allocators may round, virtual pages may be untouched, and sample growth can increase its capacity.

The safest initial one-issue experiment is shorter lexical ownership: release reduced1 after the second contraction; release H after its recursive MSF IDs return; release forest IDs after forest construction; release the forest after verification; release G and marks after constructing the remaining problem and before recursing. Preserve public P, all edge/ID orders, RNG draws, samples, selected results and all 65 existing counters. No in-place filtering, reservation-policy change, bit packing or different sampler should accompany that experiment. Plain int/Edge/vector destruction does not throw; for successful allocations these scope changes preserve the mathematical computation. Peak-memory behavior and allocation-failure timing may change and should be disclosed.

There is an additional ownership limit: borrowed P itself remains stored in its caller's `G_remaining` (or H) throughout the call, even after the current contraction no longer needs it. The simple scope change cannot free another frame's input. Consuming internal inputs while preserving the public immutable input would be a different, more invasive follow-up; do not silently bundle it with local lifetime shortening.

Reservation policy is a separate experiment. Eighth sampling still reserves half the input, and filtering reserves every input edge. Smaller reservations can lower spare capacity but reintroduce growth and moves. Full sample reserve, previously considered for half sampling, is especially not an obvious remedy for the current eighth policy. Measure actual capacity/relocations before selecting a rule. Do not change RNG consumption to force a fixed sample count.

The rejected minimum-cost cache is also separate. Its archived patch (`benchmark/results/practical-2026-10-10/minimum_candidate.patch`) modifies **public deduplicating** `boruvka_step` against `ba39977`; metadata/evidence commit `db0717e` confirms that baseline. It did not test the current private retained kernel, eighth sampling, compressed verifier or Google fixtures. Its lack of consistent benefit remains evidence against assuming a win, not a direct negative result for this exact path. Reconsider it only if contraction dominates; keep comparator policy and shared-code effects explicit.

## Instrumentation that can answer the question

Use diagnostic-only, nested **exclusive** clocks, not a clock call on each edge/query. Keep the uninstrumented timing binary as the performance reference. Suggested boundaries:

1. Public tuple conversion; RNG/root setup; first and second contraction separately.
2. Sampling and its isolate normalization; sampled recursive child tracked separately.
3. Forest recovery; disconnected partition construction/scatter.
4. Verifier FBT construction; child/adjacency construction; LCA preprocessing.
5. Request gathering (includes LCA queries); compressed offsets/values setup; median construction; path propagation/traversal; mark evaluation.
6. Survivor filtering and normalization; final recursive child separately.
7. Public set reserve/insert; owned-input/internal teardown; explicit unclassified residual.

A parent phase must not count child time again. Likewise a broad verifier clock must subtract its nested phases. Timestamp scopes must include or separately report local destructor work; placing a timer destructor before the vector destructors silently loses teardown. Preserve outer/native intervals so exclusive sums plus residual can be checked. Phase instrumentation itself changes execution cost; percentages from it are diagnostic, not an uncontaminated decomposition of old timings.

Record each recursive call's parent/branch/depth, v/e, two quotient sizes, sample size, forest size/components, filtering result, and major vector sizes/capacities at boundaries. For tree verification record L/T/h/E, LCA b/B/shapes/cells, Q/U and binary-search steps. This distinguishes increased recursive volume, a connected-to-disconnected transition and increased time per unit of similar work. Aggregate counters alone lose these associations.

Use exactly the completed Google families, densities, eleven sizes and both graph/sampler seeds first. Normalize by actual N=n+m; retain every seed and all small/large observations. Fit individual work categories as well as time, rather than summing heterogeneous counts into a supposed CPU model. Repeating a deterministic graph/seed six times estimates timing variation, not six independent recursive work realizations. The selected `NlgN` model is the best of the library's finite candidate set, not a proof of Θ(N log N); for example that set does not include N log log N, a cache-threshold model, or a mixture with an intercept.

## Remaining proof and measurement limits

The expected-linear recurrence needs valid loop-free undirected inputs, a valid uniquely ordered sampled MSF, independent ideal sampling for its probabilistic proof, linear local verifier work, represented integer/word operations, and expected constant-time public hashing. Equal-depth FBT invariants and component-local normalization establish the local array/table bounds above. The measured MT19937 stream is deterministic, C++ allocation is not a unit-cost RAM primitive, and a fixed finite family/seed matrix is not a universal expectation. None of those distinctions licenses dismissing the observed rising time/N; they identify what the next measurements must resolve.

At this audit stage, lifetime shortening is the clearest semantics-preserving memory experiment. LCA layout/adjacency flattening, contraction minima caching and public output representation are conditional follow-ups to phase evidence. No production repair, benchmark result or cause of the fitted NlogN curve is claimed here.
