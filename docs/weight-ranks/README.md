# Optional stable ranks for tied integer weights

The public KKT solver requires distinct weights. This header-only experimental
adapter accepts repeated **signed 32-bit** weights and constructs a separate
problem with globally distinct costs in `(original cost, input position)` order:

```cpp
#include "kkt/experimental_weight_ranks.hpp"

const problem input = /* undirected, loop-free graph; unique edge IDs */;
auto ranked = kkt_experiment::with_stable_weight_ranks(input);
auto ids = kkt_edge_ids(ranked, 42);
```

Every returned ID still refers to the original input. Endpoints, record order,
IDs, vertex count and legacy metadata are preserved; the original problem is
unchanged. Disconnected graphs, isolates, parallel edges, signed costs and
sparse or negative IDs are supported under the solver's remaining input
contract. Endpoint validity and the complete graph/index contract are not
validated. The adapter rejects an edge count above `INT_MAX` before copying.

Use **original weights** when computing or reporting the result's cost. Ranks
are internal ordering keys, not the original objective values. Accumulate
original costs in a sufficiently wide type, such as `std::int64_t` for these
32-bit edge/index bounds; the legacy `get_solution_cost` helper returns `int`.

The refinement gives one deterministic MSF among possibly several equal-cost
answers. Kruskal using `(original weight, input position)` is its independent
reference order. Stable ranks stay in the cost field through recursive
contraction and sample-ID renaming. Choosing a first tied minimum locally would
not suffice if the verifier continued comparing only the original equal costs.

## Work and costs

Four stable least-significant-digit passes sort edge positions by 8-bit chunks
of the signed cost, with its sign bit flipped. Stability preserves input
position as the tie breaker. The adapter then writes each position's rank to
the copied graph. It performs no ID hashing or comparison sort.

This is deterministic `O(m + 256)` work and additional storage in the fixed
32-bit word model. It allocates a copied edge vector, two `int` position vectors,
and a 256-entry histogram. For nonempty input, the optional `weight_rank_work`
receipt reports `4m` histogram visits, `4m` scatter visits, `m` copied records,
`m` rank writes, `3m` index initialization/write slots and 1,024 histogram and
prefix slots each. These are logical counts, not CPU instruction counts or
complete allocator costs. Empty inputs skip the radix passes.

Preprocessing is opt-in; neither solver API calls it automatically. Any timing
comparison must include the input copy, ranking, allocation and destruction.
No wall-clock improvement, hardware-complexity conclusion or complete C++/Lean
proof is claimed by this change. The solver's other expected-work assumptions
remain separate.

## Checks

```sh
make -j2 weight-rank-test
```

The standalone test is also included in `make test`. A Bazel `weight_rank_test`
target is declared, but the retained execution uses Make.

The tests compare the radix order with a separate comparison-sort oracle, then
compare every selected edge ID against an independent Kruskal/DSU implementation
using original costs. Cases include signed byte boundaries and extremes,
repeated weights, reversed input order, disconnected and parallel edges, large
signed IDs, isolates, seeded random graphs, recursive hierarchical paths and
nonmutation. Output IDs must be unique, and original costs are accumulated in
64 bits, including a valid result exceeding the 32-bit sum range.

Both retained executions pass **169 fixtures and 507 solver calls** each.
The [validation receipt](validation/CHECKS.json) records exact source hashes,
commands and actual binary architectures. Native Apple Clang and native arm64
Homebrew LLVM ASan/UBSan run the focused target against the public solver at
parent commit `039a8d8e098b71df7aa3c0b48d874dbb19055b72`. The adapter is byte-for-byte
the same header used in the separate research witness; no experimental
contraction or verifier implementation is imported into this branch.
