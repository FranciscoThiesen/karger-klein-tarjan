# Larger hierarchy: prospective screen

**Mock validation passed; performance remains unexecuted.** The owner ran all
eleven mocked groups successfully on the first attempt after the separate
72-child held-out capture completed. The prospective freeze passed after declaration commit `2fa464d`; no native
solver call has started yet. The package was originally prepared while that capture was
active, without reading its partial results. It neither modifies that protocol
nor depends on its outcome.

The [protocol](PROTOCOL.md) and [manifest](manifest.csv) fix both hierarchy and
shuffled core at 65,536/1,048,576/4,194,304 vertices, density 32, two graph seeds
11000009/11000027 and scalar sampler 2203. [Feasibility](FEASIBILITY.md) explains
why the last point is plausible within 40 GiB without guaranteeing memory use.

New files are `benchmark/run_larger_hierarchy.py` and
`benchmark/test_larger_hierarchy.py`. They adapt the reviewed held-out collector
structure while using local command/row validation; no parent-module seed
globals are changed. The full unchanged compressed parent proof remains in
force. All parent helpers, native files and existing study artifacts remain
untouched.

Eleven mocked groups cover the literal six-case schedule and 504 outputs,
all six positions, full parent artifacts, local seeds without parent overrides,
the exact 4M/134M domain limit, disallowed 8M or changed cases, all six topology
twins, independent Fraction ratios/medians, sustained/reversed/boundary brackets,
malformed/truncated raw rows and certificates, known-empty owned groups,
monitor failures/poison, interrupted cleanup, repeated SIGTERM suppression,
handler restoration and stopping before another child. The owner run passed
in 6.968 seconds with exit status zero and its owned process group verified
empty. [Attempt 01](validation/owner-mocks-attempt01.json) preserves the exact
command, unchanged source hashes, stdout/stderr and exit proof. The
[independent first attempt](validation/independent-mocks-attempt01.json) also
passed all eleven groups with unchanged source hashes and an empty owned
process group; [source review](INDEPENDENT_SOURCE_REVIEW.md) passed.

The [readiness check](validation/readiness-attempt01.json) also passed the full
unchanged compressed parent proof, exact candidate binary/profile binding,
six-case/twelve-child schedule and a fresh prior-declaration seed audit. It
created no freeze. Root still owns source commit, prospective preflight,
machine/power checks and the separate performance release. Actual 4M resource
fit remains untested.

Reproduction and future commands; **capture still requires a separate release**:

```sh
python3 -B benchmark/test_larger_hierarchy.py
python3 -B benchmark/run_larger_hierarchy.py preflight \
  --parent-freeze benchmark/results/compressed-query-2026-10-15/freeze.json \
  --manifest benchmark/results/larger-hierarchy-2026-10-15/manifest.csv \
  --protocol benchmark/results/larger-hierarchy-2026-10-15/PROTOCOL.md \
  --freeze benchmark/results/larger-hierarchy-2026-10-15/freeze.json
```

Preserve first and subsequent test attempts, exact commands, logs, source hashes
and owned-group exit receipts. Obtain independent review, recheck seed nonreuse
and private-power-log ignore rules, and commit the final declaration and freeze
before a separate root release for serial performance capture:

```sh
python3 -B benchmark/run_larger_hierarchy.py capture \
  --freeze benchmark/results/larger-hierarchy-2026-10-15/freeze.json \
  --output benchmark/results/larger-hierarchy-2026-10-15/larger.csv --released
```

After all groups are known empty, strict analysis uses a fresh output directory:

```sh
python3 -B benchmark/run_larger_hierarchy.py analyze \
  --capture benchmark/results/larger-hierarchy-2026-10-15/larger.json \
  --output-dir benchmark/results/larger-hierarchy-2026-10-15/analysis
```

Expected complete outputs: 12 children, 504 checked rows, 720 paired clock ratios,
60 case/120 graph comparisons, 72 case/144 graph absolute summaries, 30 point states,
30 endpoint pairs and 10 family/control summaries. No shortened matrix, domain
extension, solver omission, peak-memory guarantee or runtime prediction is
part of the preparation.

The [preflight receipt](validation/preflight-attempt01.json) records exit zero
and an empty owned group. The [freeze](freeze.json) has SHA-256
`d4600df2dee18c98d263a9bc043d2881c16a6cc253d9c99047aede4aaa334f27`;
it binds the complete inherited native proof and all twelve planned children.
Root will separately release performance after all nonperformance jobs exit.
