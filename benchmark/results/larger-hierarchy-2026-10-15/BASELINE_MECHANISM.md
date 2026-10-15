# Why fewer retained edges need not mean a faster Borůvka implementation

Source-derived accounting, without execution or partial timing reads. These
differences do not establish instruction, bandwidth, cache or allocation
hotspots.

The [original implementation](../../../boruvka/boruvka.cpp) keeps the original
tuple vector unchanged. Each iteration resets two original-n arrays, traverses
the accumulated selected-edge forest to label components, then scans all m
original edges once. An already-internal edge stops after its component
comparison. Crossing edges update component minima. A per-iteration hash set
suppresses duplicate selections, and selected edges extend the forest and
tuple result. It never rewrites all surviving graph edges into a new quotient.
Original-n vertex passes, forest traversal and hashing still cost work.

The [retained-edge helper](../../../kkt/experimental_multigraph_contraction.hpp)
instead operates on compact vertices and loop-free crossing records. A
nonterminal call traverses its entire input three times: select minima, count
crossing degrees, then emit relabeled crossing edges into a freshly reserved
vector. It initializes component/degree/remapping arrays and walks the selected
successor graph. The [continuation](../../../benchmark/retention_boruvka.hpp)
moves each quotient into place, releases the previous vector and accumulates
selected IDs before constructing the returned hash set. If all vertices merge,
the helper returns immediately after selection/component labeling, avoiding
the two output-related edge passes.

For connected, loop-free, unique-weight inputs with distinct IDs, productive round
partitions agree: internal-edge deletion, relabeling and heavier-parallel-edge
removal preserve component minima. Numbering/result order may differ.
The deduplicating `compacting_boruvka` wrapper uses the same continuation but
calls public `boruvka_step`, additionally bucketing and traversing crossing
edges to keep each endpoint pair's minimum. Smaller later quotients come
with extra work.

There is an exact termination difference. Original Borůvka assigns
`graph_cc = cur_cc` **after** adding selections, but `cur_cc` describes the
forest **before** those additions. For connected n>1, after R productive rounds
it performs one further iteration: discover one component, scan all m edges
as internal, select nothing, then exit. Thus its edge-loop count is exactly
`m(R+1)`.

For the declared hierarchy, write n=4q and L=log₂q. The star round and L
dyadic core rounds give R=L+1, so original Borůvka examines exactly
`m(L+2)=m log₂n` original-edge records: **16m, 20m and 22m** at n=65,536,
1,048,576 and 4,194,304. This is deterministic source accounting, not a timing
measurement. If V sums retained-compactor round inputs and t is its final
round input, its helper performs exactly **3V−2t** edge-loop iterations and
emits **V−m** quotient records. The harness additionally constructs m initial
Edge records, giving V explicit graph-record constructions overall. These
counts exclude vertex work, result operations and allocator internals.

The [timed wrapper](../../../benchmark/retention_control.cpp) preserves public
APIs: compactors include tuple-to-Edge conversion and temporary input
destruction; original Borůvka consumes tuples directly. Returned-result
validation/destruction occurs afterward. A larger retained input count can
therefore coexist with less rebuilding work; only measurements can resolve
the tradeoff. Original Borůvka may loop forever on disconnected inputs after
each component is spanned. All declared timed cases are connected; this
limitation is not exercised here, and its behavior is not a general MSF API.
