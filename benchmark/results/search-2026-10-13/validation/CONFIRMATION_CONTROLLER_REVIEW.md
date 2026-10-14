# Source-only confirmation-controller review

Reviewed `run_attachment_confirmation.py`, `CONFIRMATION_EXECUTION.md`, the
frozen native wrapper/analyzer CLI and lifecycle, and the two declared
manifests while the larger pilot was still running. No imports, tests,
subprocesses, benchmark runs or plots were executed for this review.

The fixed grid and accounting are correct: 12 cases, three graph seeds, two
sampling seeds, five timed repetitions and one warmup for all five algorithms.
That is 72 native seed-pair processes, 1,800 timed observations and 360 checked
warmups per campaign. Each complete case contains 150 timed observations.
The provisional ratios correctly take a median over repetitions, then sampling
seeds, then graph seeds; they do not divide separate runtime medians. The
frozen native rotation puts every algorithm in every timed position once.

The manifests contain the same exact case set and reverse only complete case
order. Repeated B graphs are correctly described as dependent repeated inputs.
No timing row, warmup, loss or clock flag is filtered or adjusted. Monitoring
only reads the growing JSON/CSV and queries swap and battery state; strict
analysis and the full power-log query occur after the wrapper exits. This
extra monitoring is disclosed and identical in both campaigns, rather than
claimed to have zero overhead. There is no performance-based stopping rule.

The earlier failed caffeinate assertions are inherited truthfully, with no
claim that sleep prevention is active. A successful power audit means the log
was parseable and complete enough for that audit, not that no sleep event or
clock flag occurred; all events and flags must remain reportable. The script
does not use flags to delete observations.

## Preflight hardening requested before release

1. Campaign A currently requires only the large capture sidecar's pass status
   and equal binary hash. Require its completed successful strict analysis and
   bind the preceding raw/metadata/provenance hashes. Check the frozen native,
   Makefile and capture-helper inventories as well, so the confirmation is not
   merely attributed to whatever source files happen to exist at launch.
2. Campaign B currently has no code-level dependency on successful A. Require
   A's successful controller, complete 72-process/1,800+360 capture, strict
   analysis and inspected power audit before consuming B seeds. Compare
   binary, profile and source/build/helper inventories across A and B.
3. Bind both manifest files and the protocol declaration to their pre-large
   frozen commit/hashes. Checking reversal alone would accept a jointly
   reordered pair. Record these preflight hashes in controller provenance.

The execution note already imposes parent release after strict validation, so
these are fail-closed defenses against an accidental premature invocation,
not findings that the intended operator schedule has changed. The author and
parent were notified before any confirmation execution.

On interruption the controller signals the wrapper, whose existing handler
terminates its separately owned native process group. If the wrapper does not
exit within the controller's 30-second wait, the controller records a warning
rather than proving that the native process ended. Preserve the explicit
requirement to inspect/stop that process before any new capture. A later
campaign must not bypass a failed predecessor.

Browser processes, plotting, builds and instrumented work must remain stopped
throughout each released native capture. None is launched by this controller.

## Updated source re-review after the large pilot

The three requested preflight defenses are now implemented. `validated_prior`
checks complete successful capture and strict-analysis matrices, raw and
derived hashes, matching captured metadata, all current native sources, the
Makefile, six frozen helpers, binary, architecture and stack. B additionally
requires a successful A controller and validated power audit, and refuses a
prior cleanup warning. Both manifests and the declaration are bound to the
prospective commit `d641ca8`. Final campaign analysis receives the same binding
before the controller can pass. Progress now reads only the six completed
child CSVs for each newly finished case. No schedule or measurement boundary
changed in this update.

One final small artifact-binding omission was sent to the author: include
`power/audit.json` itself, and preferably `analysis/provenance.json`, in the
controller's retained-artifact digest registry. Existing code verifies their
inputs and structure but does not compare the A audit result against an
A-recorded output digest. Subject to this small addition and the author's
execution-free gates, source review finds the controller ready for release.

The author subsequently added both output files to the retained digest
registry and integrated the controller under the result directory. A
`--preflight-only` mode returns before creating campaign artifacts or launching
the wrapper. Source reinspection confirms these changes. No outstanding
source-review blocker remains; execution-free gate results belong to the
author's separate validation record.

## Independent completed large-pilot data spot-check

After the parent announced timing OFF, a bounded standard-library read of the
300 raw calls recomputed all 80 case/metric/comparator paired median and
trial-range entries. Every entry matched the strict analysis exactly. No
native process or reserved seed was invoked.

KKT wins eight of ten compactor case medians, with six at most 0.90 and 37 of
50 individual timed comparisons below one. KKT loses all 50 timed comparisons
to each of Kruskal, Prim and original Boruvka, on both clocks. At 2M the
hierarchy/distance compactor ratios are 0.813424/0.808168; at the separately
declared 4M stress points they are 0.825106/0.830208. This is not monotonic
improvement. Hierarchy at 512K has median 0.875067 but maximum trial 0.970303;
not every individual ordered-case comparison meets the 10% threshold.

The two clock flags are retained in the shuffled4, 2M case: original Boruvka's
warmup has 9.078889458 s steady versus 6.179232 s process CPU; KKT's timed
repetition zero has 24.016168667 s steady versus 14.564061 s process CPU.
The latter remains a loss on both paired clocks (1.723951 wall, 1.170447 CPU).
The power audit records no nominal sleep overlap, which does not identify the
cause of either gap. Neither row is removed, and no sleep-free, contention-free
or constant-frequency condition is inferred.
