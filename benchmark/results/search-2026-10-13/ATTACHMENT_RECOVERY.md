# Recovery of the interrupted second confirmation campaign

Declared 14 October 2026 UTC after stopping the failed wrapper and before
running any recovery case. The original
[confirmation declaration](ATTACHMENT_CONFIRMATION.md), manifests, captures
and controller records remain unchanged. This is an explicit execution
deviation, not a retrospectively successful frozen campaign.

## What failed and what survives

Campaign A completed successfully. Campaign B's wrapper finalized 59 of its
72 scheduled native children. Child 60 produced all 30 passing output rows
and its `/usr/bin/time` footer, but the RSS sampler remained blocked in `ps`.
Its last successful observation was at 07:18:39 UTC. The native child finished
at approximately 08:18:50 UTC, and the wrapper still could not advance.

A narrowly scoped `libproc` query identified `/bin/ps` PID 17278 as a direct
child of the owned wrapper PID 74412. Sending that helper `SIGKILL` at
08:25:41 UTC did not restore progress. The wrapper received `SIGTERM` at
08:29:20 UTC and recorded both the interruption and native child 60's exit
status of zero. The controller then exited with `validation: failed`.
The signal did not interrupt a measured solver call. Its purpose was to
stop a stalled wrapper after the native case had finished.

The original B CSV, sidecar, child files and failed controller are retained
byte-for-byte after their finalization. In particular, the original combined
CSV contains 59 children; it will not be rewritten to include child 60.
A separate prefix validator must check all 60 native child files, their
recorded exit statuses, independent reference certificates, exact identities,
clock records and hashes. It must label the last child's unfinalized wrapper
status accurately. No completed native case is rerun or replaced.

The scoped intervention evidence is retained in
[the initial probe](validation/attachment-monitor-recovery-probe.json),
[the helper signal record](validation/attachment-monitor-recovery-action.json),
[the follow-up probe](validation/attachment-monitor-recovery-result.json)
and [the wrapper stop record](validation/attachment-monitor-stop.json).
The initial probe's `child_bytes_returned` field is a mislabeled raw API
return value, not a byte-count assertion; child identities were read from
the populated PID array and independently rechecked before signaling.

## The remaining schedule is fixed

The [recovery manifest](attachment-confirmation-b-recovery.csv) contains
only the two unfinished cases, in their original order:

1. `leaf_hierarchy4`, n=262,144, d=16, p=0.
2. `leaf_distance4`, n=1,048,576, d=16, p=0.

For each case, retain graph seeds 1000039, 1000081, 1000099 in that order,
and sampling seeds 401, 503 within each graph. Keep all five solvers, one
checked warmup and five rotated timed repetitions. These are precisely the
remaining 12 native children: 300 timed calls and 60 warmups. Recovery child
1 corresponds to original schedule position 61; child 12 to position 72.
No family, parameter, seed or repetition is selected using confirmation
outcomes. The recovery may stop on a correctness, provenance or resource
failure; it may not silently skip a case or replace a measurement.

## Monitoring repair and unchanged native work

The recovery adapter is a new helper. The six frozen capture/analysis
helpers, production C++ sources, Makefile and native executable remain
unchanged. The executable SHA-256 is
`8188f6b8717a0a4b4261369ac589ca0a65f2247ebfbfb8c56f98a544bd156faf`.
Native commands, public-call boundaries, algorithm rotation, correctness
checks and all clocks remain those of the original harness. The new helper
and its explicit deviation metadata must be hash-bound in both capture and
analysis; it must not claim the original six-helper inventory alone.

The adapter replaces external `ps` calls with scoped macOS `libproc`
process-group RSS observations. It retains the 40 GiB sampled ceiling and
three-consecutive-unavailable rule for ordinary provider errors, and adds
fail-closed handling of a sampler timeout: a late result cannot become a
fresh sample or authorize another native child. Provider duration, timeout
and observation gaps must be recorded. Cleanup uses checked deadlines and
does not wait indefinitely for a helper to exit. Scheduling delays remain
possible; these are not hard real-time guarantees or a continuous RSS bound.
An unknown native exit prevents further native execution.

The repair requires synthetic success, timeout, stale-result, unavailable,
ceiling and cleanup checks before release. No native performance case is
used to tune the repair. The source, declaration, manifest and validation
evidence must be committed before starting recovery timing. Builds, tests,
plotting, browser activity and instrumented work remain stopped during that
timing, as in the original protocol.

## How results will be reported

Keep three separately labeled parts: complete A, interrupted B prefix and
recovery tail. Validate that the latter two have disjoint exact identities
and together cover the original 72-child B schedule, including every control
and every flagged call. Pair ratios only within their actual native child;
use the original repetition-to-sampling-seed-to-graph median nesting. Do
not pool A with B or manufacture a passing original B controller record.

The original strict confirmation assessor must continue rejecting failed B.
A separate assessment may report whether the **numerical upper-size rule**
holds for A and interrupted-B-plus-recovery: case medians at most 0.90 at
both upper selected sizes, every graph median below one, both clocks, with
smaller-size loss/tie and onset brackets reported separately. It must also
state that **frozen campaign B did not complete as declared**, regardless of
the numerical outcome. Retain the broad timing disturbance and monitoring
gaps prominently. Neither successful recovery nor agreement between clocks
establishes a quiet host or explains the disturbance's cause.

Power-log correlation will use the actual recorded intervals of each part.
Full power-history logs and event lists remain local and ignored; scoped
summaries, hashes and call associations are publishable. The failed
`caffeinate` assertions remain a limitation: sleep inhibition was not verified.
The prefix audit also corrects a parsing distinction without editing the
frozen helper: `Wake Requests` schedules a wake and is not itself a wake
transition. Its corrected interval overlaps the 805-second Prim call with
an 803-second logged clamshell sleep. The initial audit is retained as
superseded diagnostic evidence; the recovery audit must use the corrected
transition interpretation too. No timing row is adjusted or excluded.
