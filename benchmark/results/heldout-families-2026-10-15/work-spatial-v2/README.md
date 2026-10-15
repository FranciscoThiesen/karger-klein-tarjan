# Spatial diagnostic frontend: validated, full capture pending

The new frontend passes all twelve small native inputs: every declared family
at n=1024,d=32 and both graph seeds. All 36 solver outputs, 65 counter fields,
24 replay chains, certificates and completed-timing fingerprints passed.
Only the copied driver's family whitelist changed. Its new main links the
same eight existing compressed instrumented production objects; none was
rebuilt. This is diagnostic validation, not a performance result.

The first new-main link attempt failed because injected library search paths
selected an x86 libunwind for the arm64 target. Its evidence is retained.
Attempt02 clears only `LIBRARY_PATH` and `CPATH` for compile/link, records their
removed values, and uses unchanged compiler, SDK and flags. Both commands and
all twelve gates exited0 with affirmative empty-group proof. See
[FRONTEND_BUILD_VALIDATION.md](FRONTEND_BUILD_VALIDATION.md).

The adapter's six mocked groups passed in 6.878 seconds on attempt02. The
first mock attempt's two failures came from incompatible fake executable
sentinels in the test fixture; its logs and exact test source snapshot remain.
Only those fixture strings/comments changed. The actual collector and native
sources were unchanged by that test repair. Preparation and a fresh-process
strict freeze reload both passed, with actual exit0 and known-empty wrapper
groups. Independent source review is retained separately. A final independent
readiness check also passed in `independent-readiness-attempt01`, including
the full original proof inside and outside adapter scope, all artifact
identities, the fixed schedule and restoration of the inherited checker.

- Freeze SHA-256:
  `cd6e7a349f689879af04b6b458bfd9a6db16ecfdf10e8fd93b134310e8e09663`.
- New binary SHA-256:
  `83819e7b22a47cf5174ae2507cf71c88dbc6f9a9153e2b37a948bddea1608e96`.
- Build record SHA-256:
  `2c93d8504ed4d984d0baa72cff502387f67d4fec9733ff264a650eca43eee365`.
- Bound files: 464. Scheduled full capture: 72 fresh inputs, 216 solver outputs,
  144 replay chains and 72 cumulative query summaries. Prior outputs reused: 0.

The old [failed attempt](../work/FAILED_ATTEMPT01.md) remains failed. Its first
two successes are not part of this new capture. All six families, six sizes
and both graph seeds remain fixed, without selection by outcome.

After root commits this repair/declaration and its freeze, a separate release
may run the reviewed archival controller from the compressed worktree root:

```sh
/usr/bin/python3 -B benchmark/results/heldout-families-2026-10-15/work-spatial-v2/run_capture_attempt.py --released
/usr/bin/python3 -B benchmark/results/heldout-families-2026-10-15/work-spatial-v2/collect.py analyze --capture benchmark/results/heldout-families-2026-10-15/work-spatial-v2/capture-attempt01.json --output-dir benchmark/results/heldout-families-2026-10-15/work-spatial-v2/analysis-attempt01
```

Full capture and analysis are pending. Process durations and sampled RSS are
monitoring evidence only; no per-algorithm timing or peak-memory claim is made.
