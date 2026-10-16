# Packed argmin for the retained contraction scan

Source-only candidate, separate from the depth-query experiment. The target is [retain_parallel_step](../../kkt/experimental_multigraph_contraction.hpp), not the older deduplicating contraction. Nothing is implemented or benchmarked here.

The current ascending input scan stores one minimum edge index per vertex. For a present minimum, comparing a new cost reads that index and then gathers the old cost from the edge vector. A packed unsigned 64-bit word could store the ordered cost and input index together:

```cpp
const std::uint64_t key =
    (std::uint64_t(std::uint32_t(edge.cost) ^ UINT32_C(0x80000000)) << 32)
    | std::uint32_t(input_index);
```

Initialize every vertex word to `UINT64_MAX`; replace it only when `key < minimum[vertex]`. Compute the key once per streamed edge and retain the existing endpoint order. Later phases check the sentinel before converting the low 32 bits back to the original index.

For the supported signed-32-bit cost domain, conversion to `uint32_t` is defined modulo 2³². Flipping its high bit maps `INT_MIN,…,INT_MAX` monotonically onto `0,…,UINT32_MAX`. Unsigned word order is therefore lexicographic `(signed cost, input index)`. Since input positions increase, equal costs retain the first occurrence exactly as the current strict-`<` scan does. Revisiting the same edge through its other endpoint, including a repeated endpoint at the helper boundary, cannot replace an equal key. `INT_MAX` is valid: its high word is all ones, but a valid nonnegative index below `INT_MAX` cannot produce the all-ones sentinel. Use unsigned widening **before** the shift; signed shifts or shifting a 32-bit operand by 32 would be invalid. Compile-time width checks and the existing supported edge-count domain must be explicit in a future implementation.

The original selected-index sequence, selected external IDs, successor walks, component numbering and stable quotient records would then be identical. Consequently the RNG trajectory and all logical work fields can remain identical. `initialized_slots` currently counts initialized vector elements, not bytes: n uint64 keys are still n entries. Report the doubled element width separately rather than implying identical initialized bytes. A two-field or two-array cost cache would need its own accounting decision and is a different candidate.

On the current ABI, packed state is 8n bytes versus the present 4n-byte index array; it replaces a dependent old-cost gather whose possible address span is the 16m-byte edge vector. At m=16n/32n, the latter span is 32/64 times larger than the packed state. This is not a traffic or speedup factor. The edge stream remains, endpoint-state accesses remain indirect, and the larger vertex state could itself harm locality. The packed comparison may compile to a conditional select or remain branched; generated code, replacement stores and register pressure need inspection. Subsequent successor walks still gather edge endpoints by the decoded index.

Keep this an isolated opt-in; do not combine it with lifetime changes, reserve changes, reordering or candidate D during its first assessment. The retained-B comparator shares the helper, so preserve an explicit implementation identity or change both paths symmetrically in an explicitly declared comparison. First compare exact selected indices/quotients on signed extremes, equal costs, isolates and repeated endpoints, then valid full-solver MSFs, RNG and all counters. Only a fresh paired uninstrumented test can establish whether a cheaper minimum scan improves end-to-end time.
