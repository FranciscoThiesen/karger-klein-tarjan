# Held-out diagnostic work: ready for separate release

The nine mocked collector groups passed, and the prospective freeze passed a
fresh strict reload against the completed 72-child timing capture and the
unchanged original compressed instrumented build. No native diagnostic was
executed and no object was rebuilt. Root must commit this preparation and
separately schedule capture.

`mocks-attempt01` passed all nine groups in 2.180 seconds. After updating only
the protocol's historical preparation status, `mocks-attempt02` passed all
nine groups in 2.235 seconds. Both attempts are retained. The collector and
test source were unchanged. Preparation and an independent fresh-process
freeze reload passed as `prepare-attempt01` and `check-freeze-attempt01`.
Each attempt has exclusive stdout/stderr, exact commands and source hashes,
actual exit0, and an affirmative empty-owned-group observation. No attempt
failed or was overwritten.

The collector, protocol and nine test groups received independent manual
source review from `/root/multigraph_candidate` before executed validation.
That source review found no blocking issue; it is distinct from the executed
mock and provenance gates above.

- Freeze: `freeze.json`, SHA-256
  `db107c2370735e7bdcec777320ea069374c8247d8d02ba67684528541561bcaf`.
- Bound provenance: 428 files, including full completed timing and original
  instrumented source/build/artifact proofs.
- Existing binary: `bin/compressed-query/native-correctness/compressed/retention_work`,
  SHA-256 `16a4fceba6d537ad40b5e56ecb449907624cbb22d84c74436712886462d000ea`.
- Declared diagnostic scope: 72 inputs, 216 certified solver outputs, all 65
  counters, 144 independently checked replay chains, and 72 cumulative Q/U
  summaries. Round counts are observed rather than fixed in advance.

After root's separate diagnostic release, from the canonical compressed
worktree root:

```sh
/usr/bin/python3 -B benchmark/results/heldout-families-2026-10-15/work/collect.py capture --freeze benchmark/results/heldout-families-2026-10-15/work/freeze.json --output benchmark/results/heldout-families-2026-10-15/work/capture-attempt01.json --released
/usr/bin/python3 -B benchmark/results/heldout-families-2026-10-15/work/collect.py analyze --capture benchmark/results/heldout-families-2026-10-15/work/capture-attempt01.json --output-dir benchmark/results/heldout-families-2026-10-15/work/analysis-attempt01
```

The commands are prospective. All families and seeds remain in the declared
matrix. Monitoring durations and sampled RSS are not per-algorithm timing or
peak-memory measurements, and this one-variant extension cannot directly
measure savings against an unexecuted uncompressed reference.
