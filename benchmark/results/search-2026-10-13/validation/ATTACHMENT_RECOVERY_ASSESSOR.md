# Interrupted-prefix and recovery assessment gates

No native solver was launched by these checks. The original B capture and
controller remain `validation: failed`; none of their files was rewritten.

The original strict confirmation assessor is now retained as
[`assess_attachment_confirmation.py`](../../../assess_attachment_confirmation.py).
Its [20-test semantic suite](confirmation_assessor_selftest.json) passes,
including nested versus flattened medians, every upper-size/campaign/clock
threshold, strict graph-median gates, separate onset brackets, retained
controls and flags, and malformed provenance. The failed original B remains
unacceptable to the original strict capture loader.

[`assess_attachment_recovery.py`](../../../assess_attachment_recovery.py)
validates the exact first 60 B child files: **1,800 calls, 1,500 timed and 300
warmups**. Every child has recorded native exit status zero, the exact expected
schedule, an independent reference-certificate marker, valid clocks and bound
raw/log/resource hashes. Native child 60 is included while its wrapper status
remains explicitly `not_finalized`. The original combined CSV is independently
checked to contain precisely children 1–59, or 1,770 calls. This discrepancy is
preserved rather than repaired in place.

The [nine recovery tests](attachment-recovery-assessor-tests-final.json) include
multiple rehashed/in-memory semantic negatives: missing children, unknown or
nonzero native exits, forged last-child success, lost interruption, changed
seeds/certificates/source inventories, overlapping child intervals, modified
combined coverage, incomplete call/clock grids and wrong source-part labels.
Independent arithmetic checks distinguish the correct nested median **3.5**
from a flattened median **4.0**. All controls and both clocks remain present.

The [completed A recheck](confirmation_a_independent_assessment.json) passes:
2,160 calls, 2,880 paired rows, 288 graph summaries and 96 case summaries, with
zero flagged calls. The B prefix retains 149 flagged calls.

The [scoped prefix power audit](../attachment-confirmation-b-prefix-power-audit/audit.json)
uses one post-stop `pmset -g log` query, which exited zero in 6.67 seconds.
The new audit distinguishes `Wake Requests` scheduling notices from actual
Wake transitions. Its regression proves that such a notice does not prematurely
close a Sleep interval. The frozen auditor is unchanged. The superseded first
audit and its initial source are retained separately for diagnosis; use the
corrected audit linked above. It identifies one 803-second logged clamshell
interval overlapping the retained Prim call at `leaf_hierarchy4`, n=2,097,152,
graph seed 1000099, sampling seed 503, timed repetition 4. This is timestamp
correlation, not a duration correction or attribution of every part of the call.
Full power history and event inventories remain local and ignored. A separate corrected-parser recheck of the already archived A power log confirms zero overlaps across all 2,160 calls; no additional power query was made for A.

[`assess_attachment_composite.py`](../../../assess_attachment_composite.py)
is the separate future assessment path. It requires the exact remaining 12
successful recovery children and their power audit, revalidates A and the
prefix, checks unchanged native/source/build identity, and retains all source
parts explicitly. It independently recomputes paired repetition → sampling
seed → graph medians and compares them with the shared aggregation helper.
Its numerical rule includes all four competitors, both clocks, both upper
sizes and every graph median; onset is separate. It will report the frozen B
execution failure regardless of the numerical outcome.

The real recovery/composite execution is **pending**: no tail measurements
existed when these gates ran. Synthetic tests do not claim a successful tail.

After the declared tail capture and scoped audit complete, the command is:

```sh
python3 -B benchmark/assess_attachment_composite.py \
  --repo-root . \
  --prefix-dir benchmark/results/search-2026-10-13/attachment-confirmation-b-prefix-analysis \
  --tail-csv <completed-recovery.csv> \
  --tail-power-audit <completed-recovery-power-audit/audit.json> \
  --composite-dir benchmark/results/search-2026-10-13/attachment-confirmation-b-composite-analysis \
  --output-dir benchmark/results/search-2026-10-13/attachment-confirmation-recovery-assessment
```
