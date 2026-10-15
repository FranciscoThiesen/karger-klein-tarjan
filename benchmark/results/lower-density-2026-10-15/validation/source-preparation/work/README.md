# Lower-density untimed companion: unexecuted source package

Prepared under a performance hold. No file in this new package has been imported,
compiled, tested, hashed or run. Existing frozen/native files are untouched.
The overlay adds only `benchmark/results/lower-density-2026-10-15/work/` files.
It requires the separately reviewed lower-density timing package already in the
same eighth worktree. Do not run directly in this incomplete /tmp overlay: its
ROOT-relative imports intentionally resolve installed unchanged parent helpers.

Files are `collect.py`, `test_collect.py`, `plot_work.py`, `PROTOCOL.md`,
`run_capture_attempt.py` and `test_run_capture_attempt.py`.
The collector calls the full existing eighth-work proof without scoped overrides,
joins the future complete independently audited timing matrix and reuses the
existing native diagnostic executable. Its lifecycle was copied as source from
the validated eighth-work collector, with local 60/180 schedule/schema changes.
No native build is proposed. The prepared mocked groups use fake processes and
temporary evidence; actual runtime validation awaits explicit release.

After source review and exclusive installation, run mocks through the existing
nonnative archival guard. The study paths below are relative to
`/Users/random_person/Desktop/kkt-eighth-sampling`:

```sh
/usr/bin/python3 -B benchmark/results/lower-density-2026-10-15/work/test_collect.py
/usr/bin/python3 -B benchmark/results/lower-density-2026-10-15/work/test_run_capture_attempt.py
```

After complete timing, strict analysis and independent audit, use the actual
existing parent-work freeze hash (read/verify only after the quiet hold):

```sh
/usr/bin/python3 -B benchmark/results/lower-density-2026-10-15/work/collect.py prepare \
  --timing-capture benchmark/results/lower-density-2026-10-15/lower-density.json \
  --timing-audit benchmark/results/lower-density-2026-10-15/independent-audit-attempt01/audit.json \
  --parent-work-freeze benchmark/results/eighth-sampling-2026-10-15/work/freeze.json \
  --parent-work-freeze-sha256 ACTUAL_EXISTING_EIGHTH_WORK_FREEZE_SHA256 \
  --freeze benchmark/results/lower-density-2026-10-15/work/freeze.json
```

Root commits the new declaration, gates and freeze before a separate diagnostic
release. The prepared truthful native outer wrapper has a fixed 108,600-second
whole-interval ceiling (60*1800+600, not a prediction), actual exit/empty-group
proof and six mocked groups. The generic nonnative archival guard must not wrap
native capture. Invoke the outer only after its source/runtime gates pass,
supplying the actual newly committed work freeze SHA:

```sh
/usr/bin/arch -arm64 /usr/bin/python3 -B -u \
  benchmark/results/lower-density-2026-10-15/work/run_capture_attempt.py \
  --freeze-sha256 ACTUAL_NEW_WORK_FREEZE_SHA256 --attempt attempt01 --released
```

After actual completion/empty-group proof, use exclusive nonnative archival
guard receipts for each command below. Install the separately reviewed raw
audit beside `collect.py` before invoking its command; never replace an existing
attempt directory.

```sh
/usr/bin/python3 -B benchmark/results/lower-density-2026-10-15/work/collect.py verify \
  --capture benchmark/results/lower-density-2026-10-15/work/capture-attempt01.json
/usr/bin/python3 -B benchmark/results/lower-density-2026-10-15/work/collect.py analyze \
  --capture benchmark/results/lower-density-2026-10-15/work/capture-attempt01.json \
  --output-dir benchmark/results/lower-density-2026-10-15/work/analysis-attempt01
/usr/bin/python3 -B benchmark/results/lower-density-2026-10-15/work/audit_counters.py \
  --capture benchmark/results/lower-density-2026-10-15/work/capture-attempt01.json \
  --analysis-dir benchmark/results/lower-density-2026-10-15/work/analysis-attempt01 \
  --output-dir benchmark/results/lower-density-2026-10-15/work/independent-counter-audit-attempt01
/usr/bin/python3 -B benchmark/results/lower-density-2026-10-15/work/plot_work.py \
  --capture benchmark/results/lower-density-2026-10-15/work/capture-attempt01.json \
  --analysis-dir benchmark/results/lower-density-2026-10-15/work/analysis-attempt01 \
  --output-dir benchmark/results/lower-density-2026-10-15/work/figures-attempt01 --released
```

The plotter creates six standalone figures plus exact plotted CSVs, after
checking all canonical tables against strict raw reload; every plotted point
is rechecked after rendering. Actual data/visual QA remains pending. No plot
or instrumented duration supplies performance evidence.

The standalone independent raw-counter audit and five focused mocked groups are
source-prepared by a peer in `/tmp/kkt-lower-density-work-audit-prep`; no runtime
PASS is claimed by this preparation. The nine collector/plot mocked groups,
six outer groups and five independent audit groups remain unexecuted, as do all
actual artifacts and plots. Independent source-only reviews of the collector,
plotter and outer are retained beside this README.
