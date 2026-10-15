# Compressed-query verifier experiment: archived source preparation

This is the preparation record, preserved below. The implementation is now installed and passed the gates in [NATIVE_VALIDATION.md](NATIVE_VALIDATION.md). The source-level equivalence argument is archived in [SOURCE_ASSESSMENT.md](SOURCE_ASSESSMENT.md). The proposed per-call diagnostic observer was deferred to avoid changing the measured source: cumulative `U` remains derivable from the existing counters, and no intermediate trace or per-call distribution is claimed.

Prepared 2026-10-15. **Not applied, compiled, imported, tested, or timed.** The files in this directory are proposed source, not validated code. The current packed-sampling work and all frozen native inventories are untouched.

The accompanying source/theory note is `/tmp/kkt-compressed-verifier-assessment.md`. It explains the equivalence argument, bounded memory accounting, and limitations suitable for a later report. Current source examined: `/Users/random_person/Desktop/kkt-edge-verifier-view/verifier/verifier_v2.cpp`.

## Proposed source placement

In a later separately authorized worktree:

- Copy `experimental_compressed_queries.hpp` to `verifier/experimental_compressed_queries.hpp`.
- Apply `verifier-dispatch.patch` to `verifier/verifier_v2.cpp`.
- Copy `compressed_query_test.cpp` to `test/compressed_query_test.cpp`.

The patch is against the current direct-Edge verifier source. It adds a private `KKT_EXPERIMENT_COMPRESSED_QUERIES` branch in `test_graph::compute_heavy_marks`. The unselected reference body remains textually unchanged. The extra header is included only under that macro. Its copied `down`, binary search, path-state update, and child traversal deliberately preserve the existing expressions. This duplicates a small amount of private algorithm code to isolate the first experiment; a shared refactor can be considered separately after equivalence and performance are established.

No KKT sampler, RNG policy, reserve, contraction, forest construction, forest component wrapper, LCA implementation, public signature, or unrelated lifetime is changed. Keeping the LCA cache alive and replacing query-record/maxima storage is intrinsic to this representation experiment. Do not combine this with the packed sampler until the independent verifier effect is established.

## Exact semantics and work accounting

For each connected verifier call, let `Q` be the number of proper endpoint-to-LCA requests, including duplicates, and `U` the number of distinct `(lower vertex, ancestor depth)` requests. Every `add_request` increments the existing `verifier_queries` once, so it remains `Q`; it is **not** silently changed to `U`. The helper exposes `unique_requests()` for tests/untimed diagnostics without adding a production observer or altering the 65-field counter schema.

- `path_query_visits`: reference `4Q`; candidate `2Q+U` (setup `Q`, unique-answer computation `U`, final lookups `Q`). The new final rank lookup work is counted.
- `verifier_vertex_visits`: one additional visit per reduced-tree node for depth precomputation; prefix accounting remains one visit per node. Existing path-init and path-visit counts are unchanged.
- `verifier_edge_visits`: one fewer full query-graph pass per connected call. LCA query count remains one per edge, including self-loops, as before.
- `initialized_slots`: counts actual newly initialized arrays, including local masks, depth, propagated masks, offsets, cached LCAs, values, path stack, median table, and marks. It intentionally differs from the reference and counts elements, not bytes.
- FBT, LCA, propagated-mask/path-state behavior, binary-search calls/steps, sampler work, forest decisions, and KKT final IDs should remain identical between variants on identical inputs and seeds. The four changed fields are `verifier_vertex_visits`, `verifier_edge_visits`, `path_query_visits`, and `initialized_slots`; `verifier_queries` is explicitly unchanged. No additional existing field is expected to differ.

The local-mask lookup uses unsigned `bit(depth)-1` and popcount; its zero-depth rank is zero. A zero-request/all-self-loop call allocates zero answer values and performs no lookup. Assertions guard lifecycle, index bounds, proper-depth requests, absent bits, and output ranges. The caller's LCA still establishes actual ancestry; depth checks alone do not validate an arbitrary external tree request. This remains a private helper with the same valid-forest assumptions as the existing verifier.

The actual proposed allocation/counter placement also gives exact paired gates. Let `M=verifier_tree_edges`, `T=verifier_tree_calls`, `Nsum=fbt_output_vertices`, and `Q=verifier_queries` for a full KKT run. Infer cumulative `U` from the candidate's `path_query_visits - 2Q`; require `0 <= U <= Q`. Then require:

```
reference.path_query_visits == 4Q
reference.initialized_slots - candidate.initialized_slots == M + Q - U + T
reference.verifier_edge_visits - candidate.verifier_edge_visits == M
candidate.verifier_vertex_visits - reference.verifier_vertex_visits == Nsum
```

These follow from unchanged outer work and the per-tree initialization difference `m+Q-U+1`. Per-tree arrays before common path/median storage total `4N+2+Q+3m` initialized slots in the reference and `4N+1+U+2m` in this proposal. `path_init_vertices` remains identical. This permits cumulative unique-request diagnostics without any new field or observer; per-call distributions would still require supplementary observations. These are logical slot/visit identities, not allocation bytes or RSS.

The first version initializes values normally and retains assertions. Both choices are part of the measured implementation if it proceeds to timing; do not disable only the candidate's checks to improve its result. Allocation peaks must be assessed from actual overlapping lifetimes, not only the difference between `8Q` query records and `4U` values.

## Focused test design

`compressed_query_test.cpp` is intended to be compiled once with the common work-statistics/assertion flags and linked separately against each verifier variant. Its runtime argument is `reference` or `compressed`.

1. Independent forest walks check every graph-edge position for both tuple and Edge overloads and the public ID-set adapters. Cases include duplicate requests and IDs, signed ID extremes, `INT_MIN`/`INT_MAX` weights, strict-equality boundaries, reversed/permuted input, multiple components, isolates, cross-component edges, self-loops, and empty inputs.
2. Direct helper checks use an independently walked seven-node full branching tree with requests at both ancestor depths, including internal lower endpoints. Twelve requests produce ten unique answers. Separate mask checks reach depth 30 without constructing an infeasibly large median table. Zero requests are explicit.
3. Seven child-process negative cases require SIGABRT from the actual assertion guards: zero/missing request bits, negative/unsupported depth, lookup before solve, proper-but-unrequested ancestor, and nonproper ancestor. Parent `waitpid` reaps every negative test. The outer correctness runner must still own and bound the whole process group.
4. **Actual linked-dispatch discriminator:** a four-vertex star reduces to one new root; 12 directed non-loop queries have `Q=24,U=4`. The public marks call must have `verifier_queries=24`, `path_query_visits=96` for reference or `52` for candidate, `path_max_height=1`, and 12 LCA queries, while matching the oracle. Passing the wrong runtime policy must fail. This does not merely test an unused helper.

The manually derived number of positional `check_marks` calls is 252: four fixed `orders` groups plus 24 generated groups, each making nine checks. There are seven malformed-lookup cases and two actual-dispatch fixtures. Counts and all assumptions require verification after compilation; none is a completed test result.

## Later build, equivalence, and evidence plan

1. Independently review this source and patch context before applying it. Verify the patch and focused tests in a new worktree; preserve all frozen timing artifacts. Keep the scalar sampling policy and retained-edge contraction/direct-Edge path fixed in both variants.
2. Use the same native ARM compiler/SDK, assertions, stack limit, bounded group monitor, and seven shared non-verifier production objects. Compile `verifier_v2.cpp` twice, with the sole variant difference `-DKKT_EXPERIMENT_COMPRESSED_QUERIES`; all other production objects, including `kkt.o`, must be byte-identical/shared. The unchanged six-solver driver object must also be shared. Record exact sources, commands, objects, binaries, and parent freeze provenance.
3. Run both focused policies, then wrong-policy negatives, the existing independent direct-mark oracle, existing 1,344 full-KKT records, and existing contraction/regression/certificate tests. Repeat with native ASan+UBSan. Keep failed attempts and owned-group exit evidence. No performance executable runs as part of this build/gate stage.
4. For paired full-KKT records, require exact fixture/order/seed identity, input fingerprint, sorted certified MST IDs, and all unchanged counters. Permit only the four explicitly changed counter names listed above, and require the exact accounting identities above rather than accepting arbitrary differences. Existing `edge_verifier_view_test.cpp` requires equality between tuple and Edge counters inside each variant; that should continue to hold. Require an actual-work difference on at least one positive query fixture to reject a reference-linked candidate.
5. Full output equivalence and unchanged RNG policy do not by themselves directly observe every intermediate sample/forest. If the stronger claim of identical intermediate values is made in the report, add a compile-off supplementary trace or use an independently reviewed existing trace that records sampling engine states, ordered sample positions, forest IDs, and heavy-mark positions; compare exactly. Alternatively state the narrower observed gates and the source-level determinism argument separately.
6. Before timing, collect untimed per-call `Q`, `U`, graph/tree sizes, and depth as supplementary diagnostics. The current helper accessor can support a separately compiled observer, but no such observer has been implemented here. If a timing study is approved, use fresh paired trials and the unchanged retained-edge Boruvka baseline, retain all families/losses, and compare both clocks. No claim of speedup, lower RSS, or crossover is justified by this preparation.
