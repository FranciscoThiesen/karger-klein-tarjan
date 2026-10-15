# Isolated next experiment: fully overwritten verifier query storage

Prepared read-only while the paired Edge-view capture is running. This is a
proposal, not an implementation, performance result, or production promotion.
The inspected worktree is `/Users/random_person/Desktop/kkt-edge-verifier-view`.
Its inspected revision is `2b66b7aed0164005f004fc49ffaeca357f31de82`.
No production source, executable, frozen helper, or captured evidence was changed.

## Recommendation and exact scope

Remove only the redundant value-initialization of `path_query` records in
`verifier/verifier_v2.cpp:375–376`. Keep the ancestor cache, offsets/cursors,
query count, query order, FBT, LCA, path traversals, maxima, marks, public APIs,
KKT sampling, filtering, and graph lifetimes unchanged.

The current code declares the two-int record at lines 189–191, resizes a fresh
`vector<path_query>` at 375, and then assigns every record at 384 or 388. The
first reads occur in `tree_path_maxima::init` at 221–223 and `visit` at 253–258.
Value-initialization produces zero values that the fill pass does not use.

Use an owning default-initialized array for this one scratch buffer, conceptually:

```cpp
const size_t query_count = query_offsets.back();
unique_ptr<path_query[]> queries(
    query_count ? new path_query[query_count] : nullptr);
```

The spelling matters: no parentheses after `[query_count]`; `make_unique<T[]>`
value-initializes the array and would retain the redundant work. Accessing
`vector::reserve` storage beyond its size is invalid and is not an alternative.
The record must remain trivially default-constructible; a static assertion can
make that expectation explicit. Its two fields receive assignments before use.

Give `tree_path_maxima` a borrowed `const path_query*` instead of a reference to
the vector (member at 198; constructor at 203–211). The offsets already bound
every query range. The owning array remains local to `compute_heavy_marks` until
after the synchronous verifier call. Keep an explicit `size_t query_count` for
the counter at 394. Do not optimize any other arrays in this experiment.

## Complete-write proof

Let `N = total_nodes`, `M = G.size()`, and let `c[u]` be the number of queries
whose lower endpoint is vertex `u`.

1. The first graph pass, lines 360–370, computes and stores exactly one LCA for
   each input position `i`. Each endpoint contributes one to its degree count
   precisely when its stored ancestor differs from that endpoint. Thus every
   contribution is either zero or one per endpoint, and total `Q <= 2M`.
2. The prefix pass at 372–374 establishes `offset[0] = 0` and
   `offset[u+1] - offset[u] = c[u]`. These ranges are disjoint and their union is
   exactly `[0, Q)`; `Q = offset[N]`.
3. The cursor vector at 377 begins as an exact copy of those offsets. The fill
   pass at 380–390 uses the same unchanged input records, cached ancestors, and
   endpoint predicates as the counting pass. Therefore it performs exactly
   `c[u]` writes for each `u`, in the same original graph order as today.
4. Each write to `u` uses the next cursor value and advances it once. It writes
   exactly `offset[u], ..., offset[u+1]-1`, without holes, duplicates, or overlap
   with another endpoint's range. Final cursor `u` is `offset[u+1]`.
5. Each assignment supplies both `upper` and `edge`. Only after this entire fill
   phase completes do the traversals read those records. Every read index is
   within one of the filled ranges, so no indeterminate member is observed.

This proof does not depend on edge IDs, uniqueness of query costs, graph input
order, or the number of endpoint queries being exactly two.

### Edge cases and bounds

- **Zero queries:** avoid even a zero-length allocation by keeping a null owner.
  Every offset is zero, so both traversal loops execute zero iterations and
  never dereference the pointer. The verifier can still process a nonempty tree.
- **Self-loops:** both endpoints equal their LCA, so counting and filling both
  contribute zero. The existing final self-loop guard at 406 keeps the mark
  light; the maximum array's initialization is unchanged.
- **Empty graphs/forests and singleton components:** existing early returns in
  `verify_tree_marks` and the forest wrapper remain unchanged. Components with
  no tree or no queries continue to skip this machinery.
- **Disconnected forests:** the wrapper still creates local tuple subgraphs,
  preserving original parent graph positions in their ID field. Each local
  tree performs this same range construction independently. Mapping local marks
  back through the positional IDs is unchanged; query records continue to use
  the local graph position, never the original ID.
- **Index types:** keep offsets, cursors, and `query_count` as `size_t`. The
  current `int M`/`int edge` convention already requires an input query graph
  representable by `int`; do not introduce a wider-contract claim or silently
  narrow `Q` to `int`. On the existing arm64 workload limits, `Q <= 2M` is
  representable in `size_t`. No new multiplication/index arithmetic is needed.
- **Allocation failure:** normal `new[]` failure propagates; existing local
  vectors and the unique owner unwind through RAII. Even if later construction
  throws, deleting an array of trivial records does not read its fields. Do not
  add manual lifetime management, `malloc`, placement writes, or raw ownership.
  Allocation-size failures may have a different standard exception type from
  `vector::resize`; promise safe propagation, not identical failure messages.

## Counter semantics and required differential result

Only this line's logical initialization charge disappears:

```text
old.initialized_slots - new.initialized_slots = old.verifier_queries
```

All other **64** WorkStats fields must be exactly equal for the same input and
seed, including `verifier_queries`, `verifier_tree_edges`, `path_query_visits`,
all LCA/FBT/path counters, sampling/filtering, recursion, and materializations.
Both graph overloads must return byte-identical marks, and full KKT must return
identical sorted MST IDs. There is no expected reduction in allocation size,
query-record fill work, or `path_query_visits` in this experiment. Explicit
assignment remains; only the preceding zero initialization is removed.

Completed retention-control diagnostics illustrate the size of this term:

| Case, graph seed 3000001, KKT seed 809 | Query records | Initialized slots | Query share |
|---|---:|---:|---:|
| leaf_hierarchy4, n=2097152, m=16n | 118031656 | 316791332 | 37.26% |
| leaf_distance4, n=2097152, m=16n | 124345568 | 333066047 | 37.33% |
| gnm_random, n=1048576, m=16n | 54786556 | 142037658 | 38.57% |
| gnm_random, n=262144, m=128n | 113745408 | 285649713 | 39.82% |

Source: the already completed
`benchmark/results/retention-control-2026-10-15/work/raw_work.csv`. These are
cumulative records across tree verifier calls, not a single allocation. They
come from earlier graph/sampling seeds and are not observations from the active
Edge-view capture. Direct Edge access does not itself change initialization
counters. These heterogeneous logical counts do not predict percentage speedup;
the compiler, allocator, page behavior, and memory system must be measured later.

## Correctness gates: retain existing tests and add one targeted gate

The existing direct positional oracle is valuable and should remain unchanged:
1,248 cases exercise both graph representations, duplicate IDs with different
marks, equality boundaries, signed extremes, loops, ordering and disconnection.
The existing full KKT suites add exhaustive, independent cycle-certificate,
multigraph, and multiple-seed checks. Retain all of them in native and native
Clang 22 ASan/UBSan/leak profiles.

However, result equality and ASan/UBSan alone do not prove that every query slot
was initialized before its first read. Add a narrow **test-only write-coverage
gate**, excluded from all timing objects:

- For each constructed query buffer, record an independent byte per slot.
- Before each production fill write, verify its index is below `Q` and has not
  been written before; mark it once. Catch an invalid index before doing the write.
- After filling, require every byte is one and each endpoint cursor equals
  `offset[u+1]`. For `Q == 0`, require no writes and zero endpoint ranges.
- Run it with both tuple and Edge query overloads on connected and disconnected
  fixtures, all-loop connected queries, empty cases, many parallel queries,
  reversed/interleaved order, isolated components and extreme weights/IDs.
- Add negative tests for a deliberately missing slot, duplicate write and
  out-of-range index to show that the audit itself rejects violations.

This gate should be a small separately enabled validation hook/helper, not a
new timed pass. Its bookkeeping is test instrumentation, not WorkStats. Do not
silently count its initialization as algorithm work or leave it enabled in
performance binaries. Keep the independent mark oracle as the behavior check;
the coverage gate establishes the prerequisite for using uninitialized storage.

Paired instrumented full KKT then verifies the exact one-counter delta above
on identical graph fingerprints and seeds, including a positive-query fixture
that rejects a candidate accidentally linked to the old zero-initializing path.
Require all temporary borrows to stay within their owning buffer's lifetime.

## Isolated build design

Create a new worktree only after the current capture and its evidence checks
finish. Use the direct Edge KKT path for **both** variants. Compile all production
objects except `verifier/verifier_v2.o` once and link those same physical objects
into both binaries, including `kkt.o`, which has both
`KKT_EXPERIMENT_RETAIN_PARALLEL` and `KKT_EXPERIMENT_EDGE_VIEW` enabled.

Compile only `verifier_v2.cpp` twice, with a dedicated query-storage selection
macro present only for the candidate. Link the unchanged six-solver harness from
one shared object. Use the same Apple Clang/SDK/options/512 MiB stack and no work
counters, audit hooks, sanitizers or NDEBUG in timed objects. Freeze the actual
eight-object inventories and every compile/link command; require seven shared
object path/hash identities and different verifier object hashes.

For a particularly clean ablation, make the borrowed pointer interface common
to both verifier variants: tuple/reference query storage remains the existing
value-initialized vector and passes `.data()`, while the candidate array passes
`.get()`. That common representation change can alter the reference's codegen.
Explicitly call it a **newly refactored verifier reference** and run fresh paired
timings; do not use the current frozen Edge-view binary's timings as its baseline.
This is the same disclosure principle used for the earlier tuple/Edge overload.
After release, inspect emitted native code to confirm the baseline performs the
redundant clearing and the candidate removes it; a changed logical counter alone
does not prove the compiler emitted fewer memory writes.

## Why not choose the other two changes first?

**Lifetime shortening** is plausible for memory pressure. `reduced1` is last
read by the second contraction at `kkt/kkt.cpp:322` but remains alive until the
recursive frame returns. `H` is last needed by the sampled recursion at 342 but
its large edge vector remains live during verification and the final recursion.
Explicit scopes could release each earlier without changing any WorkStats field.
They would alter allocation/free timing and possibly allocator reuse, not remove
the existing query initialization. Preserve the caller-owned `P` and the parent
`G` needed for sampled-result position recovery. Assess this as its own memory
experiment; current counters do not measure lifetime bytes or prove a speedup.

**Stable in-place filtering** at `kkt/kkt.cpp:372–385` could reuse owned `G`
storage, remove the `relevant_edges.reserve(G.size())` allocation, preserve light
edge order, and then move the graph into isolation removal. It must not mutate
caller-owned input, move before verification/forest recovery, or change metadata.
It also retains large vector capacity, so do not infer RSS savings from capacity.
Actual moved/copied survivors must still count as materializations; an assignment
is not free merely because storage is reused. Avoid self-assigning a light prefix.

The completed large hierarchy diagnostic retains only 760495 edges across final
branches, compared with 59018275 verifier input edges and 118031656 query records.
Large distance has 761975 filtered edges; sparse Gnm 114443; dense Gnm 28454.
Thus removing all survivor copies would affect much less counted work than the
query initialization, although removing retained allocations could still matter.
The filtering experiment has a separate ownership/lifetime effect and must not
be bundled with query storage.

Other tempting query changes are also separate: removing the ancestor array by
recomputing LCAs trades initialization for another LCA pass; avoiding the cursor
copy or changing fill direction can alter query order. Neither is needed for this
proposal. Recursive result IDs are already vectors and are not a target.
