# Post-Google lower-density installation and validation checklist

Source-only consolidation, 2026-10-15. Nothing in this checklist has run.
The active Google capture must finish with actual outer exit and affirmative
empty-group proof, followed by root's explicit nonperformance release, before
installation, hashing, imports or any command below. No rebuild is needed.

## 1. Install once, preserve preparation and freeze boundaries

Use the existing eighth worktree, `/Users/random_person/Desktop/kkt-eighth-sampling`.
Reject an existing destination file; preserve exact source bytes except the
explicit timing-audit pin update described below. Record original and installed
hashes after release. Do not modify any frozen ancestor, native source, object,
binary or old helper. Do not execute the incomplete `/tmp` overlays directly:
their root-relative imports intentionally require the installed worktree.

| Source | Destination under the eighth worktree |
|---|---|
| `/tmp/kkt-lower-density-prep/overlay/` | Same relative paths under the worktree root: three new `benchmark/*.py` files and `benchmark/results/lower-density-2026-10-15/` |
| `/tmp/kkt-lower-density-work-prep/overlay/` | Same relative paths, adding only `benchmark/results/lower-density-2026-10-15/work/` |
| `/tmp/kkt-lower-density-work-audit-prep/audit_counters.py` | `benchmark/results/lower-density-2026-10-15/work/audit_counters.py` |
| `/tmp/kkt-lower-density-work-audit-prep/test_audit_counters.py` | `benchmark/results/lower-density-2026-10-15/work/test_audit_counters.py` |

Archive the three packages' top-level README/handoff/feasibility/review notes
under separate `validation/source-preparation/{timing,work,work-audit}/`
subdirectories in the new study. Preserve their names inside each subdirectory;
in particular, do not overwrite one package's `INDEPENDENT_SOURCE_REVIEW.md`
with another's. The overlay already contains the timing review receipts and
the native-capable timing outer under `validation/launch-preparation/`.

Use these shell variables only after release:

```sh
kkt_root=/Users/random_person/Desktop/kkt-eighth-sampling
kkt_study="$kkt_root/benchmark/results/lower-density-2026-10-15"
kkt_work="$kkt_study/work"
kkt_guard="$kkt_root/benchmark/results/heldout-families-2026-10-15/validation/run_postcapture_validation.py"
kkt_outer="$kkt_study/validation/launch-preparation"
cd "$kkt_root"
```

Fill the three currently `None` entries in installed
`validation/independent_numerical_audit.py::DECLARATION_SHA256` with the actual
final installed hashes of:

- `benchmark/run_lower_density.py`
- `benchmark/results/lower-density-2026-10-15/PROTOCOL.md`
- `benchmark/results/lower-density-2026-10-15/manifest.csv`

Preserve the original unpinned source and a before/after receipt; independently
check those three exact bindings. The mock suite intentionally rejects missing
pins. Do not alter the existing eighth-parent SHA
`2be7556d15b58f3f65cc380ac22b67c57fdf8aea747d651b9d648c6a1aa59d2f`.
No future timing or work freeze SHA exists yet. The existing eighth *work*
freeze is a different artifact: read and verify its actual SHA after release,
rather than substituting the timing-parent digest.

Install the private power-log ignore rule before any machine-after query:
`benchmark/results/lower-density-2026-10-15/lower-density-power-audit/pmset.log`.
Preserve the machine helper's explicit no-inhibition qualification.

## 2. Run all six prepared mocked suites with exclusive receipts

These are nonnative mocks: 11+6+6 timing groups and 9+6+5 work groups, **43
groups total**, not 43 native correctness cases. The nine work groups include
the plotter's canonical-data mutations; no extra plot-test file is missing.
The new timing plotter's source review is preserved; actual rendering and
visual QA require completed timing data.

```sh
/usr/bin/python3 -B "$kkt_guard" \
  --prefix "$kkt_study/validation/collector-mocks-attempt01" --timeout 300 \
  --source "$kkt_root/benchmark/run_lower_density.py" \
  --source "$kkt_root/benchmark/test_lower_density.py" -- \
  /usr/bin/python3 -B "$kkt_root/benchmark/test_lower_density.py"

/usr/bin/python3 -B "$kkt_guard" \
  --prefix "$kkt_study/validation/audit-mocks-attempt01" --timeout 300 \
  --source "$kkt_study/validation/independent_numerical_audit.py" \
  --source "$kkt_study/validation/test_independent_numerical_audit.py" -- \
  /usr/bin/python3 -B "$kkt_study/validation/test_independent_numerical_audit.py"

/usr/bin/python3 -B "$kkt_guard" \
  --prefix "$kkt_study/validation/outer-mocks-attempt01" --timeout 300 \
  --source "$kkt_outer/run_capture_attempt.py" \
  --source "$kkt_outer/test_run_capture_attempt.py" -- \
  /usr/bin/python3 -B "$kkt_outer/test_run_capture_attempt.py"

/usr/bin/python3 -B "$kkt_guard" \
  --prefix "$kkt_study/validation/work-collector-mocks-attempt01" --timeout 300 \
  --source "$kkt_work/collect.py" --source "$kkt_work/test_collect.py" \
  --source "$kkt_work/plot_work.py" --source "$kkt_work/PROTOCOL.md" -- \
  /usr/bin/python3 -B "$kkt_work/test_collect.py"

/usr/bin/python3 -B "$kkt_guard" \
  --prefix "$kkt_study/validation/work-outer-mocks-attempt01" --timeout 300 \
  --source "$kkt_work/run_capture_attempt.py" \
  --source "$kkt_work/test_run_capture_attempt.py" -- \
  /usr/bin/python3 -B "$kkt_work/test_run_capture_attempt.py"

/usr/bin/python3 -B "$kkt_guard" \
  --prefix "$kkt_study/validation/work-audit-mocks-attempt01" --timeout 300 \
  --source "$kkt_work/audit_counters.py" \
  --source "$kkt_work/test_audit_counters.py" -- \
  /usr/bin/python3 -B "$kkt_work/test_audit_counters.py"
```

Inspect every log and actual wrapper exit, and require each receipt's
`validation=pass`, `exit_status=0`, `owned_groups_verified_empty=true` and empty
group members. A receipt alone does not replace polling the launched wrapper
to actual completion. Preserve every failed attempt and source snapshot before
a repair; rerun affected gates under a fresh attempt suffix, never overwrite.
Any independent repeat requested by root uses a separate `*-independent-*`
prefix.

**Parallelism:** after installation/pinning is complete and sources are held
stable, these six suites may run as separate guarded processes in parallel
during a nonperformance window: their fake captures live in temporary trees,
their receipt prefixes are distinct, and Python uses `-B`. They need no future
real lower-density capture. Do not edit source while a guard is hashing it.
Run preflight/freeze mutation and commits sequentially after their relevant
gates. All mocks, analysis, renderers and native diagnostics must stop before
any quiet performance release.

## 3. Commit and freeze the timing declaration before launching it

Root reviews the installed/pinned source, exact 30-case manifest, source review
receipts and passing gates, then commits the timing declaration and validation
evidence. Work source/gates may be committed separately now, but its freeze
cannot be prepared yet. Use the timing preflight command in
[`ROOT_EXECUTION_HANDOFF.md`](/tmp/kkt-lower-density-prep/ROOT_EXECUTION_HANDOFF.md)
with the exact existing eighth timing freeze and new protocol/manifest.
The preflight reconstructs the full unchanged parent proof; no native solver
is run. Independently strict-reload the new freeze, record its actual digest,
and commit that freeze in a separate prospective commit before any capture.
Do not change the matrix, seeds, collector or protocol after freezing.

Machine-before is a bounded nonnative command. Once every other runtime is
stopped and root separately releases performance, the native-capable timing
outer is:

```sh
/usr/bin/arch -arm64 /usr/bin/python3 -B -u "$kkt_outer/run_capture_attempt.py" \
  --freeze-sha256 "$kkt_lower_freeze_sha" --attempt capture-attempt01 --released
```

`kkt_lower_freeze_sha` must be the actual committed **new timing** freeze SHA.
Require the whole 60-child matrix, 2,520 outputs (2,160 timed/360 warmups), actual
outer exit and all native/outer groups empty. Its 54,000-second ceiling covers
the complete outer interval; it does not introduce a per-child wall deadline.
The generic nonnative guard must **not** wrap this native capture.

## 4. Complete and audit timing before preparing work freeze

Follow the existing timing handoff sequentially: actual outer completion and
empty groups, machine-after, strict analysis, independent numerical audit,
then plots/QA. Use these canonical artifact paths consistently:

- capture: `$kkt_study/lower-density.json`
- strict tables: `$kkt_study/analysis-attempt01/`
- arithmetic audit: `$kkt_study/independent-audit-attempt01/audit.json`
- timing figures: `$kkt_study/figures-attempt01/`

The timing audit takes explicit `--freeze`, `--freeze-sha256`, `--analysis-dir`
and `--output-dir`; do not rely on its older generic defaults. Pass `--power-log`
to analysis only after the bounded power query actually succeeded. A failed
query is retained and the optional argument omitted; neither proves inhibition.
The required timing audit checks all 3,600 ratios, 1,980 summary medians,
150 point states, 490 earlier/later pairs and 20 outcomes without density
pooling. No work freeze or mechanism capture may use partial timing, unaudited
tables, selected winners, or substituted graph fingerprints.

After strict analysis, the independent timing audit must finish before the
timing figure release and before work-freeze preparation. Once that audit has
passed, timing plots/visual QA and nonnative work-freeze preparation can overlap
if root permits; they write disjoint outputs. Stop them before another timed
capture. No performance result is inferred from the work preparation.

## 5. Prepare and commit the separate untimed work freeze

Only after stage 4's completed timing audit, run the concrete guarded `collect.py
prepare` invocation in the [work README](/tmp/kkt-lower-density-work-prep/README.md).
It binds the canonical timing capture/audit above and the actual existing
`benchmark/results/eighth-sampling-2026-10-15/work/freeze.json` digest, selects
the existing typed eighth instrumented artifact, and reconstructs the entire
old parent proof. No native build or call belongs to this step.

Independently strict-reload `work/freeze.json`, record the real new **work** SHA,
and have root commit the work declaration/gates (if not already committed),
then the freeze, before a separate native diagnostic release. The two new
freezes and the existing parent-work freeze are three distinct artifacts.

```sh
/usr/bin/arch -arm64 /usr/bin/python3 -B -u "$kkt_work/run_capture_attempt.py" \
  --freeze-sha256 "$kkt_work_freeze_sha" --attempt attempt01 --released
```

This truthful native-capable outer requires all 60 inputs/180 certified solver
outputs/120 comparator replay chains and actual exit plus every detached
native/outer group empty. Its whole-interval ceiling is 108,600 seconds; the
unchanged inner deadline is 1,800 seconds per input and the RSS cap is 40 GiB.
These are safety bounds, not runtime predictions. No diagnostic execution may
overlap a performance capture. Never use the generic nonnative guard here.

## 6. Work verification, independent audit, figures and report

After the native work outer actually exits with affirmative group proof,
follow the concrete work README commands: strict `verify`, strict `analyze`,
independent `audit_counters.py`, then `plot_work.py` and visual QA. Use
`capture-attempt01.json`, `analysis-attempt01/`,
`independent-counter-audit-attempt01/` and `figures-attempt01/` inside `work/`.
The independent audit accepts an arbitrary fresh output directory; this fixes
the name consistently for this handoff.

Require all 11,700 raw counter cells, 120 null comparator hash cells, 120 full
chains, 60 Q/U/engine-word records, 30 twins and all exact count/m values. There
is only the eighth policy, so no cross-rate 61+4 identity or paired-rate counter
claim applies. Publish every case and all zeros/unmeasured fields; instrumented
durations are lifecycle evidence, not performance. Independent audit must pass
before mechanism claims. Source prep, mocked gates and actual-data validation
remain separately labelled throughout.
