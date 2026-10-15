# Eighth-sampling post-capture handoff

Prepared from source during the active 48-child timing capture. **None of the commands below has been executed for this handoff.** Do not run them until root has observed actual timing-controller exit zero, complete 48/2,016 capture validation, empty owned groups, and released nonperformance work. Do not inspect partial timings to decide this sequence or its cases. No active worktree file was changed by this preparation.

## Execution conventions

Use the existing installed interpreter and exact worktree. Run each numbered stage sequentially and inspect its receipt before advancing. These are command examples for a later released session, not an autorun script.

```sh
cd /Users/random_person/Desktop/kkt-eighth-sampling
eighth_study=benchmark/results/eighth-sampling-2026-10-15
eighth_work="$eighth_study/work"
eighth_guard=benchmark/results/heldout-families-2026-10-15/validation/run_postcapture_validation.py
```

The validation guard accepts only explicit `/usr/bin/python3 -B ...` commands. It writes exclusive `.json`, `.stdout`, `.stderr` artifacts, hashes the named sources before/after, records the actual child exit, and checks its owned process group with a bounded OS query. Require both the outer tool/session's **actual exit zero** and receipt `validation="pass"`, `exit_status=0`, `owned_groups_verified_empty=true`, empty `group_exit_verification.members`, and unchanged source hashes. A yielded session ID or a printed PASS line is not completion. Preserve nonempty stderr, including normal unittest output. For any failure, retain the entire attempt and pre-repair sources, diagnose it, and use a new receipt/output suffix; never overwrite/relabel attempt01.

The guard hardcodes `native_solver_execution=false`: use it only for mocks, analysis, audit, figure generation, and read-only proof/freezing. **Never use it around the native work capture.** A separate truthful bounded wrapper is prepared below. Its success also proves every separately sessioned native child through the work collector's final strict reload.

No interpreter/package installation is needed or authorized by this document. Plotting requires Matplotlib in `/usr/bin/python3`; record the actual version from figure provenance. Module imports must resolve from this installed worktree. Invoke the specified test files directly with `-B`, not ambiguous historical `unittest discover`/`collect` aliases. The new native wrapper must be installed beside this study's `collect.py`, not executed from `/tmp`.

## 1. Close timing and run strict analysis

Root first polls the original capture session to its actual exit, retains the final controller receipt, and completes the existing machine/power postflight. Verify that the capture refers to frozen SHA `2be7556d15b58f3f65cc380ac22b67c57fdf8aea747d651b9d648c6a1aa59d2f`. Retain clock flags and power provenance; do not trim or adjust rows. These instructions do not themselves perform or claim a sleep-log query.

```sh
/usr/bin/python3 -B "$eighth_guard" \
  --prefix "$eighth_study/validation/strict-analysis-attempt01" --timeout 300 \
  --source benchmark/run_eighth_sampling.py \
  --source "$eighth_study/freeze.json" --source "$eighth_study/eighth.json" \
  -- /usr/bin/python3 -B benchmark/run_eighth_sampling.py analyze \
  --capture "$eighth_study/eighth.json" --output-dir "$eighth_study/analysis"
```

If root already produced and archived strict analysis, inspect that complete receipt and reuse the resulting directory; do not rerun into it. Root plans to append `--power-log eighth-power-audit/pmset.log` (resolved to the actual postflight location) to the analyzer command only after the actual successful postflight query. This full power log remains private/ignored. Passing the file alone does not establish query success or retention coverage.

Expected strict result: 48 children, 2,016 certified outputs (1,728 timed/288 warmups), 1,728 all-six eighth/half clock ratios, 2,880 within-variant KKT/comparator clock ratios, and 30 crossover classifications. Every input, loss, warmup, flag and full clock endpoint remains retained. Four graph/sampler realizations per case are two graphs crossed with two sampler seeds; repeated trials are not independent new graphs.

## 2. Six independent numerical-audit mocks, then actual audit

```sh
/usr/bin/python3 -B "$eighth_guard" \
  --prefix "$eighth_study/validation/audit-mocks-attempt01" --timeout 300 \
  --source "$eighth_study/validation/independent_numerical_audit.py" \
  --source "$eighth_study/validation/test_independent_numerical_audit.py" \
  -- /usr/bin/python3 -B "$eighth_study/validation/test_independent_numerical_audit.py"
```

Require all **six** groups to pass, then:

```sh
/usr/bin/python3 -B "$eighth_guard" \
  --prefix "$eighth_study/validation/audit-actual-attempt01" --timeout 300 \
  --source "$eighth_study/validation/independent_numerical_audit.py" \
  --source "$eighth_study/eighth.json" \
  -- /usr/bin/python3 -B "$eighth_study/validation/independent_numerical_audit.py" \
  --capture "$eighth_study/eighth.json" --analysis-dir "$eighth_study/analysis" \
  --output-dir "$eighth_study/validation/independent-numerical-audit-attempt01"
```

Require `independent-numerical-audit-attempt01/audit.json` validation PASS as well as wrapper success. The standalone standard-library audit reconstructs 4,608 ratios, 3,024 summary rows, 60 point states and 30 endpoint classifications from raw integers using exact Fractions; it imports no collector aggregation. It independently rereads native schema/schedule/certificates, clocks/resources/groups, concatenation, twins and ancestor/native artifact hashes. The previous source-only review is not a substitute for these runtime gates.

## 3. Ten figures and explicit visual QA

```sh
/usr/bin/python3 -B "$eighth_guard" \
  --prefix "$eighth_study/validation/plot-attempt01" --timeout 600 \
  --source benchmark/plot_eighth_sampling.py \
  --source benchmark/plot_retention_control.py \
  --source benchmark/run_eighth_sampling.py --source "$eighth_study/eighth.json" \
  -- /usr/bin/python3 -B benchmark/plot_eighth_sampling.py \
  --capture "$eighth_study/eighth.json" --output "$eighth_study/figures-attempt01" --released
```

Expect PNG/SVG/PDF for each of `variant_gains`, `half_ratios`, `eighth_ratios`, `half_times`, `eighth_times`, on both `wall` and `cpu`: **10 figures/30 panels**. Each figure has three family panels containing six cases. Check figure provenance, all six controls, full trial ranges, four realization medians, matched wall/CPU axes, unchanged-control drift, and canonical crossover tables. Then inspect **all ten PNGs at original resolution** and save a separate visual QA receipt with filenames/hashes. Generated provenance deliberately says visual review pending. A numerical PASS does not clear clipping, labels or legibility. Preserve failed renders/layout sources and write a fresh figure attempt if repair is needed.

## 4. Install the separately reviewed native-work wrapper; run 13 work mocks

Source-only wrapper prepared at `/tmp/kkt-eighth-postcapture-prep/run_capture_attempt.py`, with independent source PASS at `/tmp/kkt-eighth-postcapture-prep/INDEPENDENT_WRAPPER_SOURCE_REVIEW.md`. It is a narrow adaptation of the completed spatial diagnostic wrapper: exact 48/144/96 counts, new schema `eighth_sampling_work_controller_v1`, truthful native mode, same 7,200-second controller deadline, post-wait deadline check, SIGTERM/finally cleanup, and final full strict-load proof. No collector/native/helper edit is required. It has not been imported or executed.

After release and review, install without replacing an existing file:

```sh
test ! -e "$eighth_work/run_capture_attempt.py"
cp -n /tmp/kkt-eighth-postcapture-prep/run_capture_attempt.py "$eighth_work/run_capture_attempt.py"
```

The two commands are separate checks: confirm the first succeeded and the copy actually matches the reviewed source. `cp -n` must not be used to silently accept an old wrapper. Do not run the spatial wrapper unchanged: its final expected count is 72.

```sh
/usr/bin/python3 -B "$eighth_guard" \
  --prefix "$eighth_work/mocks-attempt01" --timeout 300 \
  --source "$eighth_work/collect.py" --source "$eighth_work/test_collect.py" \
  --source "$eighth_work/PROTOCOL.md" --source "$eighth_work/run_capture_attempt.py" \
  -- /usr/bin/python3 -B "$eighth_work/test_collect.py"
```

Require all **13** groups to pass. They mock process launch; no native solver should run. On a fixture defect preserve the rejected attempt and source snapshot before repair; do not alter frozen native or timing helpers.

The supplementary independent counter audit and its six mocks should also be installed before committing the work declaration. Source-only files `/tmp/kkt-eighth-postcapture-prep/audit_counters.py` and `test_audit_counters.py` passed independent source review, recorded in `/tmp/kkt-eighth-postcapture-prep/INDEPENDENT_COUNTER_AUDIT_SOURCE_REVIEW.md`. No imports or runtime tests were performed for that review. After nonperformance release:

```sh
test ! -e "$eighth_work/audit_counters.py"
test ! -e "$eighth_work/test_audit_counters.py"
cp -n /tmp/kkt-eighth-postcapture-prep/audit_counters.py "$eighth_work/audit_counters.py"
cp -n /tmp/kkt-eighth-postcapture-prep/test_audit_counters.py "$eighth_work/test_audit_counters.py"

/usr/bin/python3 -B "$eighth_guard" \
  --prefix "$eighth_work/counter-audit-mocks-attempt01" --timeout 300 \
  --source "$eighth_work/audit_counters.py" --source "$eighth_work/test_audit_counters.py" \
  -- /usr/bin/python3 -B "$eighth_work/test_audit_counters.py"
```

Check each no-overwrite/install step separately and require all **six** counter-audit groups to pass. These use only the standard library and temporary synthetic files, with no collector imports or native launches. The actual counter audit waits for the completed work analysis in step 7.

## 5. Prepare the work freeze, then independently recheck its full proof

```sh
/usr/bin/python3 -B "$eighth_guard" \
  --prefix "$eighth_work/prepare-attempt01" --timeout 300 \
  --source "$eighth_work/collect.py" --source "$eighth_work/PROTOCOL.md" \
  --source "$eighth_study/eighth.json" \
  -- /usr/bin/python3 -B "$eighth_work/collect.py" prepare \
  --timing-capture "$eighth_study/eighth.json" --freeze "$eighth_work/freeze.json"
```

`prepare` performs the full completed timing/readiness/source/build/object/binary proof and writes an exclusive freeze. It launches no native executable. It binds the existing native-correctness `half`/`eighth` `retention_work` binaries; **no rebuild** is needed. The unchanged frontend supports every declared attachment/G(n,m) case. Readiness must prove all 43 instrumented compile/link commands and 11 targets per variant, exact typed masks 1/7, one word per sampling edge, compressed verifier, seven shared non-KKT objects and shared driver main.

Run a fresh proof after freezing. This uses a distinct import alias and the installed file location; it is read-only:

```sh
/usr/bin/python3 -B "$eighth_guard" \
  --prefix "$eighth_work/freeze-proof-attempt01" --timeout 300 \
  --source "$eighth_work/collect.py" --source "$eighth_work/PROTOCOL.md" \
  --source "$eighth_work/freeze.json" --source "$eighth_work/run_capture_attempt.py" \
  -- /usr/bin/python3 -B -c 'import importlib.util,json; from pathlib import Path; p=Path("benchmark/results/eighth-sampling-2026-10-15/work/collect.py").resolve(strict=True); s=importlib.util.spec_from_file_location("eighth_work_freeze_readiness",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); f=p.parent/"freeze.json"; d=m.check_freeze(f); print(json.dumps({"validation":"pass","freeze":str(f),"freeze_sha256":m.native.sha(f),"expected_children":d["expected_children"],"expected_solver_outputs":d["expected_solver_outputs"],"schedule_count":len(d["schedule"]),"bound_files":len(d["bound_sha256"]),"native_solver_execution":False},indent=2))'
```

Have an independent reviewer inspect the complete proof/receipts and exact freeze SHA. Root then commits the reviewed work source/protocol/test/validation package and prospective freeze before separately releasing native diagnostics. Keep the historical PREPARATION.md clear about which gates were unexecuted when written; add current status separately. Do not mutate frozen sources during capture.

## 6. Separately release and run the fixed 48-child native work capture

Only after root's explicit release and after every analysis/test/render process has exited:

```sh
/usr/bin/python3 -B "$eighth_work/run_capture_attempt.py" --released
```

The wrapper launches exactly `collect.py capture --freeze work/freeze.json --output work/capture-attempt01.json --released`. It writes `capture-controller-attempt01.invocation.json`, `.json`, `.stdout`, `.stderr`, plus the collector sidecar and all raw child/certificate/RSS files. Capture has 40-GiB/2-second resource sampling, three-unavailable/poison stop, 1,800-second per-native deadline, guarded bounded cleanup and known-empty group proof; outer budget is 7,200 seconds. Record the external tool session ID and **poll it to actual exit zero**. A completed sidecar alone is not enough.

Require outer receipt `validation="pass"`, `exit_status=0`, `all_owned_groups_verified_empty=true`, exact 48 children/144 solver outputs/96 replay chains, and unchanged wrapper/collector/freeze hashes. Require affirmative outer cleanup fields plus strict child evidence for all 48 separately sessioned native groups. Failure/unknown exit remains unknown even if the outer Python group is empty; stop all subsequent launches until separately resolved. Preserve failed sidecars and logs. Do not reuse partial successes in a later fresh capture. The instrumented process durations and RSS are diagnostic only, not algorithm performance measurements.

## 7. Strict work verification and five-table analysis

```sh
/usr/bin/python3 -B "$eighth_guard" \
  --prefix "$eighth_work/verify-attempt01" --timeout 300 \
  --source "$eighth_work/collect.py" --source "$eighth_work/capture-attempt01.json" \
  -- /usr/bin/python3 -B "$eighth_work/collect.py" verify \
  --capture "$eighth_work/capture-attempt01.json"

/usr/bin/python3 -B "$eighth_guard" \
  --prefix "$eighth_work/analysis-controller-attempt01" --timeout 300 \
  --source "$eighth_work/collect.py" --source "$eighth_work/capture-attempt01.json" \
  -- /usr/bin/python3 -B "$eighth_work/collect.py" analyze \
  --capture "$eighth_work/capture-attempt01.json" --output-dir "$eighth_work/analysis-attempt01"
```

`verify` takes **`--capture`**, not `--freeze`. Expected five CSVs: `work` (144 solver rows × 65 fields), `rounds` (actual count derived), `round_chains` (96), `query_work` (48), `paired_kkt_work` (1,560). Comparator hash-insert counts remain null/unmeasured. Preserve zeros, increases and undefined zero-denominator ratios. Both scalar policies must use exactly one RNG word per visited sampling edge. Across rates, KKT work legitimately differs: **do not require the compression study's 61+4 counter identities**. Comparator counters/round chains must match across policy and sampler for a fixed graph. Q/U is cumulative verifier work, not per-call timing.

## 8. Actual independent raw-counter audit

After the six counter-audit mock groups from step 4 passed and strict work analysis is complete:

```sh
/usr/bin/python3 -B "$eighth_guard" \
  --prefix "$eighth_work/counter-audit-actual-attempt01" --timeout 300 \
  --source "$eighth_work/audit_counters.py" --source "$eighth_work/capture-attempt01.json" \
  -- /usr/bin/python3 -B "$eighth_work/audit_counters.py" \
  --capture "$eighth_work/capture-attempt01.json" \
  --analysis-dir "$eighth_work/analysis-attempt01" \
  --output-dir "$eighth_work/independent-counter-audit-attempt01"
```

Require `independent-counter-audit-attempt01/audit.json` PASS with 48 inputs, 144 solver rows, 9,360 cells including 96 null comparator hash counts, 96 chains, 48 query rows, 1,560 paired KKT field rows and four topology twins. Exact rational exports preserve 1,608 U/Q and cross-rate field records, including null ratio statuses; no equal-work claim across sampling rates. The audit separately rehashes full bound proof artifacts and validates raw identities/certificates/resources, but it does not replace the preceding collector's independent native build/dispatch proof. A final mechanism README must retain every family/case and distinguish exact counter facts, hypotheses and measured uninstrumented timing. Confirm every runtime job is stopped before any later performance release.
