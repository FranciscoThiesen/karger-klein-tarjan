# Fixed complexity capture launcher — source preparation only

`run_capture_attempt.py` and five focused mocked groups are unimported and unexecuted. They install beside the build/schema wrappers under `benchmark/results/current-complexity-2026-10-15/validation/`, and import only the reviewed persistent package at `ROOT/benchmark/current_complexity`. They do not acquire a library, build a binary, create a freeze, run a schema smoke or infer current complexity results. Those remain actual prerequisites.

The launcher accepts an explicit `--freeze-sha256` for the genuine future `current-complexity-2026-10-15/freeze.json`. No unknown future digest is invented. It checks that hash and the collector's complete existing proof before any launch, then retains the bound freeze, package/launcher, binary, library, smoke and parent inventories. The fixed 24-curve schedule is three families × two algorithms × two graph seeds × two sampler seeds, each containing eleven sizes, three callbacks and one warmup plus two timed calls per callback: 2,376 calls, 1,584 timed and 792 warmup. The schedule and native thresholds are checked literally; nothing is pooled with historical timing.

Each native curve remains under the unchanged collector's 3,600-second observed-exit deadline and sampled 40GiB group cap. The outer complete-interval ceiling is **24×3,600+600 = 87,000 seconds**, not an expected duration or requested wait. It includes launch, cleanup, full strict reload and log hashing, excluding final receipt serialization. A late actual zero exit or late complete interval fails. A remaining-budget POSIX timer bounds the strict reload. The outer Python group is separately sampled after waits of at most two seconds, with the same bounded provider, three-unavailable stop condition and 40GiB group cap; no combined memory-peak claim is made.

An exclusive attempt directory retains the invocation, raw capture/curves, stdout/stderr and final receipt. Existing attempts are rejected. Uncertainty is set before Popen; interrupted or nonzero collectors cannot receive a successful detached-group claim merely because the outer group is empty. Repeated SIGTERM is suppressed during bounded outer cleanup (30-second TERM grace, five-second KILL grace), then the prior handler is restored. Only an actual collector zero exit plus its full strict reload of all 24 groups/2,376 calls clears detached uncertainty. Invalid/incomplete raw evidence and unknown group exit stop the attempt. Further launches after an unknown state require that state to be resolved; the launcher does not silently retry or overwrite failures.

The five prepared mock groups cover persistent argv and supplied-freeze enforcement; exact completion counts/identities/groups; actual exit versus independent strict proof; exclusive failure preservation and late intervals; and cleanup/timer restoration. They launch no processes and do not establish native lifecycle behavior. Peer source review, later mocked execution and final genuine freeze validation are still required.

Future command, not executed, from the fixed eighth worktree after all gates and root's separate quiet performance release:

```sh
/usr/bin/arch -arm64 /usr/bin/python3 -B \
  benchmark/results/current-complexity-2026-10-15/validation/run_capture_attempt.py \
  --freeze-sha256 ACTUAL_REVIEWED_FREEZE_SHA256 --attempt attempt01 --released
```

Successful completion does not itself supply model fits or visual acceptance. The checked analyzer must run afterward, preserving all four clocks, all six models, flags and losses. Google Benchmark's raw host metadata is retained without treating macOS tick-frequency or scaling fields as proof of physical CPU frequency, stable thermals or an idle machine.
