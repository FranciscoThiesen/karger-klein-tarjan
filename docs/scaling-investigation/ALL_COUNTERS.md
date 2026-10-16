# All 65 counters: operation mix is not perfectly flat

This follow-up checks all 65 baseline work fields, not just the seven previously
selected for count-space fits. The input is the exact baseline side of the
completed candidate work comparison: 72 inputs, 4,680 field values, 780 six-size
curves and 195 family/field summaries. Full source/raw/build proof is inherited
from that strict comparison and rechecked by
[inspect_all_work.py](../../benchmark/scaling_investigation/analysis/inspect_all_work.py).
No solver, benchmark or automatic complexity fit was run.

The complete [output directory](../../benchmark/scaling_investigation/analysis/all-work-fields-attempt01/)
retains every point, endpoint change, maximum intermediate normalized value,
zero denominator and semantic category. Among the 780 curves, 396 have a larger
endpoint value/N, 345 smaller and 39 equal. There are 204 zero points: 30 curves
are all zero and 11 start at zero but become nonzero somewhere. Counts of calls,
maxima, root volumes and final recursion state are distinguished from cumulative
loop events; none is silently treated as an instruction count.

The clearest substantial finite shifts are in query-related work. Each range
below spans four graph/sampler curves, comparing value/N at 1M with value/N at
1K. These are increases in selected counts, not CPU fractions.

| Field | Ordered hierarchy | Shuffled weights | Connected G(n,m) |
|---|---:|---:|---:|
| `path_query_visits` | +4.16–7.51% | +8.24–16.46% | +9.15–19.51% |
| `verifier_queries` | +3.84–7.19% | +8.09–16.26% | +9.00–19.23% |
| `initialized_slots` | +4.99–8.19% | +7.25–15.40% | +6.48–17.13% |

`path_query_visits` is the largest positive absolute normalized change in this
inventory: +0.179–0.313 events/N for hierarchy, +0.332–0.617 for shuffled and
+0.347–0.676 for random. In the compressed verifier it equals `2Q + U`, where Q
is the logical request volume and U the stored distinct requests. It overlaps
with the query-volume counter; those two increases cannot be added as disjoint
work. Initialized slots count heterogeneous explicit initialization elements,
not bytes or implicit allocator work.

Other large positive changes include contraction edge visits (up to +0.414/N),
verifier edge visits (+0.334/N), and explicit edge materializations (+0.238/N).
The [full ranking](../../benchmark/scaling_investigation/analysis/all-work-fields-attempt01/ranked-normalized-changes.csv)
is by absolute count/N change, not estimated CPU cost: an edge visit, initialized
slot and request event are different units.

Binary-search steps deserve separate disclosure. Among defined endpoint ratios,
the largest rise is **2.204×** for hierarchy, but its absolute endpoint increment
is only **0.002601 steps/N**. Five of the twelve curves start at zero, so those
multiplicative changes remain undefined rather than being reported as infinite
or omitted. Intermediate peaks are retained too; the largest hierarchy peak
increment is 0.004565/N. A small logical count is not proof of a small CPU cost,
and the step counter does not include every instruction around the search.

Six verifier-arc curves have a zero small-input denominator; one returns to zero
at the largest size after nonzero intermediate sizes. The all-point export
preserves this behavior instead of relying only on endpoint ratios. Final
`current_depth` and hash-lookup calls are zero on all twelve curves; other zeros
include cases that never enter the disconnected-forest arc loop.

This strengthens the interpretation rather than replacing the earlier fit result.
All seven selected counters can prefer a through-origin N curve under the
large-size-weighted objective while their finite coefficients still move.
Changes of roughly 5–20% in the query/initialization mix can contribute to the
clock curve alongside rising measured time per declared event. The evidence
does not establish memory behavior as the sole cause, and these overlapping
counts cannot partition the total runtime. Direct KKT hardware-miss measurements
remain absent; a separate host calibration would illustrate the machine's
possible access costs, not attribute a measured share of KKT's CPU time.
