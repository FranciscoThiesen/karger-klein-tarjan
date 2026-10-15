# Independent source review of the larger-study numerical audit

Reviewed by `multigraph_design` on 2026-10-15 during the separate larger-study
performance capture. **Source-only PASS; no import, syntax check, synthetic
test, native execution or partial timing result was inspected by this review.**
Runtime validation remains required after root releases nonperformance work.

Reviewed files and SHA-256:

| Source | SHA-256 |
|---|---|
| `independent_numerical_audit.py` | `f44cd2403c947a7b2d152371ab69b57d8c49440a81d0989e280b3ccf01753d36` |
| `test_independent_numerical_audit.py` | `53fe0d9b208809a8936b75d714a3c23f573452663f4da61095d34dab3d33665d` |
| `INDEPENDENT_AUDIT_PREPARATION.md` | `5f84c7313a261580784913a6b1abf4d40b9bf6cb93e40c71142611da27a51d1b` |

The literal six-case declaration, two graph seeds, single sampler, reversed
second-graph order and pinned freeze agree with the prospective protocol.
The complete matrix gives 12 children, 504 outputs (432 timed and 72 warmups),
720 clock-paired comparisons, 396 case/graph comparison and absolute medians,
six topology twins, and 30 point / 30 interval / 10 summary classifications.

The audit independently enumerates raw solver groups and derives ratios and
medians with `Fraction`; it imports no collector aggregation. Crossover gates
use all four graph/clock medians, exact `<= 9/10` versus strict `> 1`, every
larger measured point, and the declared earliest-upper/closest-lower choice.
Integer time endpoints, table identity sets, complete counts, certificates,
raw concatenation, flags and known-empty resource evidence are retained.
The recursive artifact reread supplements the frozen collector's stricter
source/build-recipe proof rather than replacing that proof.

The five prepared synthetic groups include independent Cartesian pair and
median expectations with unequal wall/CPU values, three-size reversal and
late-lead cases, an exact-threshold epsilon case, full raw capture negatives,
temporary artifact drift and same-identity numerical table mutations. The
temporary raw root is canonicalized, retaining the held-out fixture fix.
No blocking adaptation defect was found. This receipt is not an executed-test
pass or a conclusion about the still-running performance campaign.
