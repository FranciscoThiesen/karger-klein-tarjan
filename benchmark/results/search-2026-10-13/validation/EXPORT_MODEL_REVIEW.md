# Attachment exporter and occupancy-model source review

Reviewed, without importing, compiling, executing or rendering:

- `/tmp/kkt-core-attachments/export_attachment_view.cpp`
- `benchmark/attachment_occupancy.py`
- Their relevant contracts in the outside draft fixture header,
  `benchmark/mst_certificate.hpp`, and the timing/work fingerprint routines.

This is a source review during the active density capture. It is not a passing
build, self-test, exported fixture, or measured model-to-trace comparison.

## Finding: nonblocking domain hole in the standalone quotient helper

`expected_core_quotient()` validates positive dyadic dimensions and shortcut
capacity, but does not enforce the exactly representable integer range before
its `exact_core_count` and `no_nonadjacent_pairs` return branches. The lower
`zero_probability()` helper does enforce `MAX_EXACT_FLOAT_INTEGER`; those
branches bypass it.

For example, the accepted call with `core_vertices=2**54`, `shortcuts=0`, and
`core_block_size=1` forms `float(2**54 - 1)`, which rounds to `2**54`. Its method
is still `exact_core_count`, and the comment says that it preserves the known
integer exactly. This example follows directly from binary64 spacing; it was
not executed during this review.

The study CLI is unaffected: `attachment_expectation()` restricts original
`n` to at most `2**22`, block size to four or sixteen, and `m` to `2**27`.
Consequently its largest core has `q=2**20`, the shortcut population is below
`2**39`, and exact core-edge counts are below `2**27`. They fit within the
stated float-integer domain. Before treating the helper as a general API,
enforce its supported count/population range before the special returns, or
explicitly restrict its public contract to the attachment-study domain.

No blocking defect was found for the declared study inputs.

## Occupancy mathematics and indexing

The formula matches the generated ideal model. For `q` core vertices and a
uniform subset of `B` shortcuts from the `U=C(q,2)-(q-1)` non-path pairs, a
partition into aligned blocks of size `s` has `k=q/s` components. The `k-1`
adjacent component pairs are already occupied by path bridges. Each other
component pair has exactly `s*s` eligible shortcut slots, so its absence
probability is `C(U-s*s,B)/C(U,B)`. Linearity of expectation therefore gives
the implemented expected edge count. Independence between different quotient
pairs is unnecessary. Shortcut internalization and parallel-pair collisions
are both accounted for.

The deterministic-partition assumption is justified for both structured
weight modes. Cheap local stars force the first contraction into the declared
blocks. Thereafter each aligned dyadic child has a path bridge to its sibling
at a cheaper rank tier than any edge leaving the parent. For distance ranks,
other edges inside that sibling pair may replace the path bridge, but the two
children still choose the same minimum representative and merge. Hence the
partition does not depend on which random shortcuts were selected. This
argument does not apply after the first round to the shuffled-core control,
or generally to the globally random control; the script correctly excludes
both from its model applicability.

`attachment_expectation()` counts the original `m`-edge star-contraction input
once, followed by the core inputs at block sizes `1,2,...,q/2`. Its total
number of rounds is `1+log2(q)`. The final input has two vertices and one
edge. Its output has zero stored vertices and edges, matching the production
removal of the final isolated quotient vertex, while the reconstructed
original partition has one component of size `n`. The emitted distinction is
correct. Output counts are not mistakenly added a second time to the volume.

The result is expected **compactor contraction-input edge volume**, not KKT's
recursive volume or elapsed time. The declared uniform-subset expectation is
also distinct from any one finite seeded PRNG realization. Its model must be
compared with captured traces before claiming agreement on actual inputs.

## Numerical scope

The shorter hypergeometric product is correct by symmetry. It uses
`min(B,h)` factors with numerator decrement represented as
`1-max(B,h)/(U-i)`. The impossible-avoidance case `B+h>U` is handled before
the product. `log1p`, `expm1`, and `fsum` avoid the main cancellation and
summation problems for the supported inputs.

The cutoff is scaled by the number of nonadjacent quotient pairs, rather
than bounding a probability alone. Since `P0 <= exp(-B*h/U)`, its extra two
natural-log units leave margin below the requested omitted-count tolerance.
Returning the tolerance as a budget, rather than reporting an underflowed
zero as a rigorous bound, is appropriate. Summing the per-input budgets gives
the declared volume truncation budget. These are truncation bounds only;
the script correctly disclaims floating-point roundoff certification.

Setting the tolerance to zero disables the deliberate exponential cutoff.
It does not turn the calculation into exact rational arithmetic or prevent
ordinary floating-point underflow. The existing numerical-scope wording
should stay attached to reported digits. The bounded combinatorial and tiny
graph self-tests are useful independent checks in source, but remain unrun
in this review.

## Exporter certificate, identity and limitations

The exporter validates the fixture domain before generation and adds a
visual-export cap of 4,096 vertices and 65,536 edges. Known family names are
the only strings emitted into JSON identifiers, so its direct JSON string
formatting is safe for that closed domain. The MST weight sum uses 64 bits.

The reference comes from Kruskal, but acceptance depends on the independent
cycle certificate. That certificate first checks simple topology, connected
spanning-tree membership, dense unique IDs and unique positive weights, then
checks every original edge against a tree-path maximum. KKT must return the
same unique ID set. The certificate runs before `by_id` indexing, so the
later unchecked vector subscripts rely on a validation already established
for the same immutable graph, rather than on unchecked fixture IDs.

The metadata checks independently invert the vertex-label permutation and
compare each local star and each projected external edge to the actual
tuples. Core IDs and ranks must be permutations of their stated domains.
Core ranks are compared to actual costs for hierarchy, distance and
shuffled-core modes; the global-random exception is correctly explained in
the emitted `core_rank_note`. The layout note explicitly says that the graph
has no intrinsic geometry.

Both fingerprints use the same FNV-1a byte sequence as `mst_search.cpp` and
the work driver: original `n`, then the ordered endpoint words, optional
weight word, and ID word. Thus a same-case export can be matched to those
captures without a different hashing convention. The main JSON stores these
64-bit fingerprints as decimal strings so JavaScript does not round them.
The stderr marker uses an integer JSON value, which needs an integer-safe
parser if consumed separately; Python's normal JSON integer parser suffices.

Two export limitations matter for downstream claims:

1. This is an export of the actual input and certified MST, not a production
   contraction trace. It contains no `boruvka_step` selected-ID ledger or
   measured quotient arrays. A drawing based on block metadata can illustrate
   the analytically forced first partition for cheap-star modes, but cannot
   be described as an exported production trajectory. In particular the
   same partition claim is invalid for the global-random controls.
2. The certificate marker is written before the final JSON is flushed, and
   source/compiler/binary hashes are not embedded in this standalone JSON.
   An archival wrapper must retain successful exit status, complete parseable
   output, the exact fixture-header/exporter build inputs and binary identity.
   A pass marker alone is not evidence that stdout completed successfully,
   nor does it bind a later rebuilt exporter to the same source.

Neither limitation invalidates the intended bounded educational export.
They constrain its caption and archive, rather than the MST calculation.
