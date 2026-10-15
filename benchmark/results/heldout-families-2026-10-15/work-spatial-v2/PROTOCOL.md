# Fresh diagnostic capture after spatial frontend repair

This is a separate frontend-only repair and a fresh diagnostic declaration.
The preceding `../work/capture-attempt01.json` remains failed: two attachment
inputs passed, then the older driver rejected `grid2d_metric` before graph
generation or any solver invocation. Its whitelist accepted attachment
families and `gnm_random` only. The frozen work collector, protocol, freeze,
driver and failed evidence remain unchanged. The failure audit verified all
four launched process groups empty. No failed output is relabelled as passed.

The previous mock suite validated supplied outputs and inherited artifact
integrity, but did not execute each declared frontend family. That coverage
gap is repaired with mandatory small native frontend gates before freezing
this declaration; it does not justify changing solver or counter checks.

## One frontend change and complete native proof

Copy the original diagnostic driver into this deep results directory. Change
only its non-attachment whitelist to also accept `line_metric`, `line_random`,
`grid2d_metric` and `grid2d_random`. The unchanged crossover generator already
implements these families and is used by the completed timing harness. Keep
the three solver calls, certificate, 65 counter fields, contraction replays,
input limits and metadata emission byte-for-byte unchanged.

Compile only this new main and link it to the exact eight existing compressed
instrumented production object paths. No production object, timing binary,
native header, generator, existing main or frozen helper is rebuilt or edited.
Use the original AppleClang15 arm64/O3/assertions/work-stats flags, SDK and
512 MiB stack. Exactly two compile/link commands are allowed. Bind source
delta, source/header inventory, compiler/SDK, command logs, original object
paths and hashes, new main/binary hashes and architecture profile, and actual
build process-group exits in `build-record.json`.

The first new-main build failed before solver gates because injected
`LIBRARY_PATH=/usr/local/lib` selected an x86 libunwind for the arm64 link;
`CPATH=/usr/local/include` was also injected. Preserve that failed build and
its group-exit proof. The fresh attempt explicitly removes only these two
search-path environment variables for compile/link commands and records their
removed values and policy. Compiler, SDK, flags and all eight original object
paths remain unchanged; the correction does not rewrite the parent build's
historical environment or claim it was recorded there.

Before preparation, run every declared family at n1024,d32, both graph seeds
9000011 and9000049, sampling seed2003: twelve complete native inputs. Each
must match its completed timing weighted/topology fingerprints and pass the
unchanged exact MST certificate, all three solver IDs, full65 counter schema,
both replay chains, connected selected-edge counts and cumulative Q/U checks.
Require actual exit0 and affirmative empty-group evidence for every gate.
These gates are correctness checks, not timing observations or extra graph
realizations. Preserve all failed gate/build attempts and stop on unknown exit.

## Same full matrix; fresh capture

The entire original schedule remains fixed: six existing families at n1024,
4096,16384,65536,262144,1048576, d32 and zero intrusion; both graph seeds and
sampling seed above. Preserve the original rotated adjacent twin blocks and
reverse graph-two order. Run **all72 children anew**, including the first two
inputs that passed with the old frontend. Reuse zero prior successful outputs.
Do not select by timing, work result or family.

The adapter strict-loads the old work freeze
`db107c2370735e7bdcec777320ea069374c8247d8d02ba67684528541561bcaf`, whose full
completed timing and original instrumented build proof remain mandatory.
It additionally checks the new main/build/gate evidence and binds its own
collector, tests and protocol in `heldout_spatial_work_freeze_v1`. The artifact
changes only at the driver frontend and its new binary; all production object
identities are compared to the checked parent again.

Capture and analysis retain the existing `heldout_work_capture_v1` and
`heldout_work_analysis_v1` schemas because their row and measurement meanings
are unchanged. A narrowly scoped freeze-check override selects the new bound
artifact; it restores the original function even through nesting or exceptions.
Parent proof always uses the saved original entry point, not an overridden
shortcut. No seed, schedule, validator or resource constant is patched.

All inherited checks and boundaries in [the original protocol](../work/PROTOCOL.md)
remain in force: three certified solvers,65 unsigned counters with comparator
hash-insertion counters explicitly null, full chained replay validation,
36 topology twins and exact timing joins,40GiB sampled RSS, two-second bounded
observations, three-unavailable/poison stop,1800-second native deadline, guarded
cleanup, and post-exit known-empty group before another child. Strict reload
rechecks every child, hash, certificate, clock interval and resource receipt.

Complete outputs remain216 solver rows/14,040 counter cells,144 unmeasured hash
cells,144 replay-chain summaries, all observed round rows and72 cumulative Q/U
rows. `U` is the sum of per-verifier-call distinct requests inferred from the
fixed compressed representation, not global uniqueness. There is no executed
uncompressed reference,61+4 paired compression gate, per-algorithm timing or
peak-memory claim. Monitoring durations are diagnostic only.

## Commands and release boundary

Run mocked adapter gates and the twelve native frontend gates before preparing
the freeze. Archive exact commands, source hashes, actual exits and empty-group
observations. Commit this repair, declaration and validation evidence separately
from the original declaration; then commit the new prospective freeze before
root separately releases the full capture.

```sh
/usr/bin/python3 -B benchmark/results/heldout-families-2026-10-15/work-spatial-v2/test_collect.py
/usr/bin/python3 -B benchmark/results/heldout-families-2026-10-15/work-spatial-v2/collect.py prepare --freeze benchmark/results/heldout-families-2026-10-15/work-spatial-v2/freeze.json
/usr/bin/python3 -B benchmark/results/heldout-families-2026-10-15/work-spatial-v2/collect.py capture --freeze benchmark/results/heldout-families-2026-10-15/work-spatial-v2/freeze.json --output benchmark/results/heldout-families-2026-10-15/work-spatial-v2/capture-attempt01.json --released
/usr/bin/python3 -B benchmark/results/heldout-families-2026-10-15/work-spatial-v2/collect.py analyze --capture benchmark/results/heldout-families-2026-10-15/work-spatial-v2/capture-attempt01.json --output-dir benchmark/results/heldout-families-2026-10-15/work-spatial-v2/analysis-attempt01
```

These are prospective commands. Read retained receipts for executed status.
