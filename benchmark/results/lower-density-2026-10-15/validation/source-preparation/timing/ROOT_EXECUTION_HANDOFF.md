# Lower-density study: unexecuted execution handoff

Every command below is pending. Execute only after root releases the applicable
phase and the current Google capture has fully exited with all groups empty.
Use the unchanged eighth binary; no build or native repair belongs to this
experiment. Root owns source commit, freeze commit and quiet scheduling.

## Installation and prospective gates

First finish independent source review, fill the audit's three final declaration
hash pins under an explicit nonperformance release, and preserve byte-identical
exclusive installation of the reviewed overlay. Do not overwrite existing files
or change frozen ancestors. Record installed bytes/hashes and actual results;
there is no current runtime receipt or freeze hash to reuse.

```sh
kkt_root=/Users/random_person/Desktop/kkt-eighth-sampling
kkt_study="$kkt_root/benchmark/results/lower-density-2026-10-15"
kkt_guard="$kkt_root/benchmark/results/heldout-families-2026-10-15/validation/run_postcapture_validation.py"
kkt_lower="$kkt_root/benchmark/run_lower_density.py"
kkt_outer="$kkt_study/validation/launch-preparation"
cd "$kkt_root"
```

Run the prepared nonnative groups in fresh exclusive attempts, inspect their
actual exits and empty-group proofs, and preserve any failure before repairs:

```sh
/usr/bin/python3 -B "$kkt_guard" \
  --prefix "$kkt_study/validation/collector-mocks-attempt01" --timeout 180 \
  --source "$kkt_lower" --source "$kkt_root/benchmark/test_lower_density.py" -- \
  /usr/bin/python3 -B "$kkt_root/benchmark/test_lower_density.py"
/usr/bin/python3 -B "$kkt_guard" \
  --prefix "$kkt_study/validation/audit-mocks-attempt01" --timeout 180 \
  --source "$kkt_study/validation/independent_numerical_audit.py" \
  --source "$kkt_study/validation/test_independent_numerical_audit.py" -- \
  /usr/bin/python3 -B "$kkt_study/validation/test_independent_numerical_audit.py"
/usr/bin/python3 -B "$kkt_guard" \
  --prefix "$kkt_study/validation/outer-mocks-attempt01" --timeout 180 \
  --source "$kkt_outer/run_capture_attempt.py" --source "$kkt_outer/test_run_capture_attempt.py" -- \
  /usr/bin/python3 -B "$kkt_outer/test_run_capture_attempt.py"
```

These tests mock native launches. They do not establish actual resource fit or
performance. Root may request an independent repeat under a new prefix; no
unrelated suite repetition is required. Plot preparation checks should use the
same complete synthetic tables; actual render/visual acceptance remains later.

After all source/gate evidence is committed, prospective preflight binds the
complete unchanged parent and exact local declaration:

```sh
/usr/bin/python3 -B "$kkt_guard" \
  --prefix "$kkt_study/validation/preflight-attempt01" --timeout 180 \
  --source "$kkt_lower" -- \
  /usr/bin/python3 -B "$kkt_lower" preflight \
  --parent-freeze "$kkt_root/benchmark/results/eighth-sampling-2026-10-15/freeze.json" \
  --manifest "$kkt_study/manifest.csv" --protocol "$kkt_study/PROTOCOL.md" \
  --freeze "$kkt_study/freeze.json"
```

Record the real new freeze SHA only after successful preflight and fresh strict
reload. No future SHA is invented here. Root commits that freeze. Before the
machine helper's after phase, ensure the exact private log path
`benchmark/results/lower-density-2026-10-15/lower-density-power-audit/pmset.log`
is ignored. No private power log is published.

## Quiet capture: a separate release

Before launch, run the bounded machine-before helper through the nonnative
guard and preserve its pass/exit proof:

```sh
/usr/bin/python3 -B "$kkt_guard" \
  --prefix "$kkt_study/validation/machine-before-attempt01" --timeout 180 \
  --source "$kkt_outer/machine_power.py" -- \
  /usr/bin/python3 -B "$kkt_outer/machine_power.py" --phase before
```

Set `kkt_lower_freeze_sha` to the actual committed freeze digest. Once all other
owned jobs have stopped and root releases quiet performance, the source-planned
outer invocation is:

```sh
/usr/bin/arch -arm64 /usr/bin/python3 -B -u "$kkt_outer/run_capture_attempt.py" \
  --freeze-sha256 "$kkt_lower_freeze_sha" --attempt capture-attempt01 --released
```

The exact 60-child/2520-row schedule must complete. The whole interval has a
fixed 54,000-second ceiling, not an expected duration or per-child timeout.
The native groups retain the 40-GiB sampled RSS ceiling and guarded cleanup.
Require actual outer exit0 and strict proof that every native and outer group
is empty; an empty outer group alone is insufficient. Retain all partial
attempts and stop after any failure. No size changes or automatic retry.

## Postcapture analysis, independent audit and figures

After actual completion and explicit diagnostic release, archive machine-after
via the same helper/guard with fresh `machine-after-attempt01`. Include the
power log below only if the bounded query passed; preserve a failed query and
omit that optional argument if it did not. Neither outcome proves inhibition.

```sh
/usr/bin/python3 -B "$kkt_guard" \
  --prefix "$kkt_study/validation/analysis-attempt01" --timeout 180 --source "$kkt_lower" -- \
  /usr/bin/python3 -B "$kkt_lower" analyze \
  --capture "$kkt_study/lower-density.json" --output-dir "$kkt_study/analysis-attempt01" \
  --power-log "$kkt_study/lower-density-power-audit/pmset.log"
/usr/bin/python3 -B "$kkt_guard" \
  --prefix "$kkt_study/validation/independent-audit-attempt01" --timeout 180 \
  --source "$kkt_study/validation/independent_numerical_audit.py" -- \
  /usr/bin/python3 -B "$kkt_study/validation/independent_numerical_audit.py" \
  --capture "$kkt_study/lower-density.json" --analysis-dir "$kkt_study/analysis-attempt01" \
  --freeze "$kkt_study/freeze.json" --freeze-sha256 "$kkt_lower_freeze_sha" \
  --output-dir "$kkt_study/independent-audit-attempt01"
/usr/bin/python3 -B "$kkt_guard" \
  --prefix "$kkt_study/validation/plots-attempt01" --timeout 180 \
  --source "$kkt_root/benchmark/plot_lower_density.py" -- \
  /usr/bin/python3 -B "$kkt_root/benchmark/plot_lower_density.py" \
  --capture "$kkt_study/lower-density.json" --output "$kkt_study/figures-attempt01" --released
```

The audit and outer/plot CLI spellings have been source-confirmed; no command
in this document has run. Require independent audit PASS before publication.
Inspect all four figures at original resolution:
four family/density panels, every seven/eight-size curve, every solver, both
graph medians, full trial ranges, all losses, matched clock axes and 0.9/1 ratio
lines. Review actual page-size exports separately if added later. Finite
brackets require four graph/clock medians and persistence at every later size
within that density; there is no interpolation or asymptotic dominance claim.
