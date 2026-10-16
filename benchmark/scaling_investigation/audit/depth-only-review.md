# Depth-only verifier review

Source-only review, 2026-10-15. No production edits, imports, tests or native runs. This note reviews candidate D's contract; the actual patch and runtime gates remain separate.

**Finding:** a private depth-returning LCA/RMQ is sufficient for the compressed verifier. It is a representation change with a plausible reduction in dependent loads, not an asymptotic improvement or a measured speedup.

`compressed_tree_path_maxima::add_request` and `lookup` (`verifier/experimental_compressed_queries.hpp:118` and `:150`) use `upper` only for bounds and `depth_[upper]`. On the unique root-to-lower path, a depth identifies exactly one ancestor. Supplying that exact depth preserves the request bit, rank, propagated masks, traversal, maximum value and heavy mark. Keep the existing ID-taking methods and their bounds as wrappers; generic helper callers need not be leaves.

In `test_graph::compute_heavy_marks` (`verifier/verifier_v2.cpp:354`), query endpoints are original vertices of the tree passed to `fbt_reduction`. Every original vertex becomes a leaf; only fresh IDs become parents. Thus distinct endpoints have a proper LCA for **both** endpoints. The optimized caller may submit two depth requests without comparing an ancestor ID against the endpoints. Equal leaf depth is not needed for this particular implication; leafness suffices. Both depth traversals start the same root at zero, so the RMQ depth equals the compressed helper's depth.

The disconnected wrapper remaps each connected component before calling this path. Cross-component records remain unmarked. A singleton component with no tree edge is skipped. Preserve every early return. A self-loop must still issue its existing LCA query, add zero path requests, and remain unmarked; skipping its LCA call would change the existing counter and is a separate optimization. Original query IDs are opaque: classification remains positional, including repeated IDs whose parallel records have different marks. The public ID-set wrapper retains its existing collapse semantics.

The proposed private RMQ preserves the Euler order, first visits, block sizes, masks and microtable argmin positions. Euler entries store depths instead of IDs; sparse cells store minimum depths instead of Euler positions. In the original mask code, `min_by_h(i-1,i)==i-1` holds exactly when the earlier depth is strictly smaller; the proposed direct comparison preserves it. Equal-depth sparse winners may lose node identity because this private API returns only depth. Partial final blocks and microtable tie rules must remain unchanged.

Remove only the private LCA `height[T]` initialization: the expected aggregate counter delta is **new.initialized_slots = old.initialized_slots − old.lca_vertices**, with all other 64 fields identical. The compressed helper's own depth array stays. Existing counters do not measure reduced dependency chains or cache misses. Do not combine flattening, byte depths, changed reserves or shortened lifetimes.

Focused gates before measurement:

1. All-pair depth answers against a parent-walk oracle on singleton, path, star, balanced and irregular trees; sizes around Euler block/level transitions, equal minima and partial blocks. Test both endpoint orders and self queries.
2. Depth-taking helper requests versus ID-taking requests and an independent path maximum; zero requests, repeated requests, root depth, deepest proper depth, invalid/absent request guards.
3. Existing tuple/Edge positional mark oracles: loops, repeated IDs, signed/extreme weights, disconnected forests, isolates and reversed records. Include an actual linked dispatcher witness; helper-only tests cannot establish production selection.
4. Full KKT native/sanitizer differential cases under its loop-free, distinct-ID, unique-weight contract: unchanged input, exact MSF IDs, sampling engine/order and all counters except the exact initialization delta. Fresh same-source controls must disclose any shared refactor.

The baseline phase capture remains untouched. Patch review and actual runtime evidence are pending.
