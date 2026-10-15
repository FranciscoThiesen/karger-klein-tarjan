# Eighth extension: prospective launch handoff

Prepared during the separate untimed 48-child work run. **These two new scripts
have not been imported, syntax-checked, tested or executed.** Their source review
is separate from the already passed eleven collector mocks, six independent
numerical-audit mocks and full freeze proof. No native release is implied here.

## Fixed artifact and release boundary

Worktree `/Users/random_person/Desktop/kkt-eighth-sampling`; installed extension
declaration/readiness commit `d182cb7a`. The existing extension freeze is:

`benchmark/results/eighth-extension-2026-10-15/freeze.json`

SHA-256 `aa2f9ae7385105eb7185b864a1f46387f8a02ebe8b967f041d3d0cef5ffa7bc5`.
It records preflight source revision `bdecf0f6714a8c29713dfad0739148433314be16`;
later evidence commits do not replace its exact source/build/helper checks.
The parent eighth freeze SHA is
`2be7556d15b58f3f65cc380ac22b67c57fdf8aea747d651b9d648c6a1aa59d2f`.
The inherited timing binary is `bin/eighth-sampling/timing-build/eighth/retention_control`,
SHA `954068775a83e1c42db62ffb6777c398dc05fd5792c60d2f293df6532130951a`.
No rebuild, native source change, sampler change or helper replacement is needed.

Keep exactly fourteen declared cases: ordered/shuffled twins at
1,024; 4,096; 16,384; 65,536; 262,144; 1,048,576; 4,194,304 vertices, d32.
Graph seeds 17000011/17000047, sampler 2801; graph two reverses the full case
order. All six solvers have one checked warmup and six balanced timed calls:
**28 children, 1,176 outputs = 1,008 timed + 168 warmups**. Fourteen topology
twins, all five comparators, all 70 points/210 brackets/10 outcomes remain.

Before root schedules capture, require actual completion/zero exit and known
empty groups for the current 48-child diagnostic, its strict analysis, mocks,
independent counter audit and any plotting/other runtime jobs. Ask every agent
to hold execution. No partial current diagnostic receipt substitutes for actual
outer process completion. Finish any new wrapper validation before this hold.

## Timeout clarification — no frozen-file correction needed

Source inspection of the extension `PROTOCOL.md`, current readiness README,
`run_eighth_extension.py` and `retention_control.cpp` found **no claim or
implementation of a 1,800-second per-child deadline**. That deadline belongs
to the separate untimed work collector. Do not transfer it to performance.

The prepared outer controller allows `28*1800+600 = 51,000 seconds` (14 h 10 min)
for the complete Python capture command. This is a conservative overall safety
cap, **not** a per-child limit or a promised runtime. A single child can consume
more than 1,800 seconds under the unchanged collector. A new per-child wall cap
would require a separately declared collector change and is not included.
The collector retains the 40 GiB sampled-group RSS cap, roughly two-second
sampling, poison/three-unavailable stops, exact certificates, no next child on
failure, and bounded TERM/KILL cleanup. The outer wrapper gives inner cleanup
30 seconds before outer SIGKILL, then 5 seconds. It cannot infer that detached
native groups exited merely because the Python group exited.

## Install new launch sources only

After source review, root may archive the new files under a new, exclusive
validation directory. This touches no frozen parent source or helper. Run from
the worktree; never overwrite an existing destination or attempt artifact.

```sh
cd /Users/random_person/Desktop/kkt-eighth-sampling
/bin/mkdir benchmark/results/eighth-extension-2026-10-15/validation/launch-preparation
/bin/cp /tmp/kkt-eighth-extension-launch-prep/run_capture_attempt.py benchmark/results/eighth-extension-2026-10-15/validation/launch-preparation/
/bin/cp /tmp/kkt-eighth-extension-launch-prep/machine_power.py benchmark/results/eighth-extension-2026-10-15/validation/launch-preparation/
/bin/cp /tmp/kkt-eighth-extension-launch-prep/HANDOFF.md benchmark/results/eighth-extension-2026-10-15/validation/launch-preparation/
```

Copy the separate source-review receipt too when available. Both scripts use
the fixed worktree path, not their installation directory. The controller adds
`ROOT/benchmark` to `sys.path`, preserving the existing import aliases. Use the
system `/usr/bin/python3 -B`, not a new environment or an ad hoc module alias.
No import or execution of these new files has yet established runtime support.

## Fresh full proof and machine-before

The full proof has already passed independently; a fresh read-only proof just
before release detects drift. The guard archives exact argv, source hashes,
stdout/stderr, actual child exit and a bounded empty-owned-group observation.
Use a new exclusive prefix; do not rerun an existing attempt in place.

```sh
/usr/bin/python3 -B benchmark/results/heldout-families-2026-10-15/validation/run_postcapture_validation.py --prefix benchmark/results/eighth-extension-2026-10-15/validation/launch-freeze-proof-attempt01 --timeout 300 --source benchmark/run_eighth_extension.py --source benchmark/results/eighth-extension-2026-10-15/freeze.json -- /usr/bin/python3 -B -c 'import sys; from pathlib import Path; sys.path.insert(0,str(Path("benchmark").resolve())); import run_eighth_extension as e; p=Path("benchmark/results/eighth-extension-2026-10-15/freeze.json"); e.analysis.hash_check(p,"aa2f9ae7385105eb7185b864a1f46387f8a02ebe8b967f041d3d0cef5ffa7bc5"); f,c=e.check_freeze(p); assert len(c)==14 and len(f["schedule"])==28; print("Full inherited proof PASS; no native solver executed")'
/usr/bin/python3 -B benchmark/results/heldout-families-2026-10-15/validation/run_postcapture_validation.py --prefix benchmark/results/eighth-extension-2026-10-15/validation/machine-before-attempt01 --timeout 180 --source benchmark/results/eighth-extension-2026-10-15/validation/launch-preparation/machine_power.py -- /usr/bin/python3 -B benchmark/results/eighth-extension-2026-10-15/validation/launch-preparation/machine_power.py --phase before
```

Inspect both actual tool exits and receipts: validation pass, exit zero,
`owned_groups_verified_empty=true`, group members empty, before/after hashes
identical. Machine queries each have a 15-second bound; one failure retains
metadata and stops. Architecture metadata can describe a translated Python
process; frozen binary proof still independently requires native arm64.

Earlier caffeinate attempts failed. Do not claim sleep prevention, rerun an
unbounded keep-awake command, change power settings or synthesize success.
The metadata always records `sleep_inhibition_verified=false`. Existing private
ignore patterns cover `eighth-extension-2026-10-15/*-power-audit/pmset.log` and
`events.json`; the postflight script verifies the log is ignored before writing.

## Root's explicit quiet native release

Only after every runtime helper has stopped and root releases the run:

```sh
/usr/bin/python3 -B -u benchmark/results/eighth-extension-2026-10-15/validation/launch-preparation/run_capture_attempt.py --released
```

This is the truthful native/performance controller. **Do not wrap it in the
nonnative validation guard**, whose receipt labels native execution false.
Use `exec_command` with a short initial yield, retain its returned session ID,
and poll that exact session until the tool returns an actual exit code. Do not
terminate it merely because the first tool call yields. Do not infer completion
from a complete-looking sidecar or a log line. Root may inspect lightweight
status; no agents should build, test, render, analyze or run other native work
during the capture. No partial timing conclusions.

Output names are fixed and exclusive:

- `extension.csv`, `extension.json`, `extension_cases/` (unchanged native raw evidence).
- `controller-attempt01.invocation.json`, `.json`, `.stdout`, `.stderr`.

Accept successful controller completion only when actual tool exit is 0,
controller receipt says pass/exit0, its outer cleanup proves empty, strict
load verifies all 28 native empty-group receipts and 1,176 rows, and
`all_owned_groups_verified_empty=true`. The controller rehashes its source,
frozen collector, freeze, machine-before and all strict-load raw inputs.
Record the actual tool session ID/exit separately as `controller-execution.json`
with receipt/capture hashes. This external observation cannot be manufactured
inside the controller. On any failure retain all evidence, stop further work,
and audit every launched group. Unknown detached group state remains unknown;
do not start postflight/another capture on an assumed cleanup success.

## Postflight, power and complete analysis

After actual outer exit and all owned native groups are known empty:

```sh
/usr/bin/python3 -B benchmark/results/heldout-families-2026-10-15/validation/run_postcapture_validation.py --prefix benchmark/results/eighth-extension-2026-10-15/validation/machine-after-attempt01 --timeout 240 --source benchmark/results/eighth-extension-2026-10-15/validation/launch-preparation/machine_power.py -- /usr/bin/python3 -B benchmark/results/eighth-extension-2026-10-15/validation/launch-preparation/machine_power.py --phase after
```

This writes exclusive machine-after metadata and, only at an ignored location,
`extension-power-audit/pmset.log`, `pmset.stderr`, `query.json`. The query has a
60-second bound, actual return code and both file hashes. If it fails/times
out, retain its partial log/query failure and **omit `--power-log`** below; do
not relabel a partial log as a successful power query. Machine-before/after
are host context, not proof of equal thermal or background-load conditions.

With a successful archived power query:

```sh
/usr/bin/python3 -B benchmark/results/heldout-families-2026-10-15/validation/run_postcapture_validation.py --prefix benchmark/results/eighth-extension-2026-10-15/validation/analysis-attempt01 --timeout 600 --source benchmark/run_eighth_extension.py -- /usr/bin/python3 -B benchmark/run_eighth_extension.py analyze --capture benchmark/results/eighth-extension-2026-10-15/extension.json --output-dir benchmark/results/eighth-extension-2026-10-15/analysis --power-log benchmark/results/eighth-extension-2026-10-15/extension-power-audit/pmset.log
/usr/bin/python3 -B benchmark/results/heldout-families-2026-10-15/validation/run_postcapture_validation.py --prefix benchmark/results/eighth-extension-2026-10-15/validation/independent-numerical-audit-attempt01 --timeout 600 --source benchmark/results/eighth-extension-2026-10-15/validation/independent_numerical_audit.py -- /usr/bin/python3 -B benchmark/results/eighth-extension-2026-10-15/validation/independent_numerical_audit.py --capture benchmark/results/eighth-extension-2026-10-15/extension.json --freeze benchmark/results/eighth-extension-2026-10-15/freeze.json --freeze-sha256 aa2f9ae7385105eb7185b864a1f46387f8a02ebe8b967f041d3d0cef5ffa7bc5 --analysis-dir benchmark/results/eighth-extension-2026-10-15/analysis --output-dir benchmark/results/eighth-extension-2026-10-15/validation/independent-numerical-audit-attempt01
/usr/bin/python3 -B benchmark/results/heldout-families-2026-10-15/validation/run_postcapture_validation.py --prefix benchmark/results/eighth-extension-2026-10-15/validation/plots-attempt01 --timeout 600 --source benchmark/plot_eighth_extension.py -- /usr/bin/python3 -B benchmark/plot_eighth_extension.py --capture benchmark/results/eighth-extension-2026-10-15/extension.json --output benchmark/results/eighth-extension-2026-10-15/figures-attempt01 --released
```

Run these sequentially, inspecting each actual exit/guard receipt before the
next. Inspect all four figure PNGs at original resolution. Publish all five
comparators/both clocks and all losses. The sustained rule requires all four
graph/clock medians to show a smaller loss and a later ≤0.90 lead that holds at
every larger measured size. Preserve all brackets and reversals. A lead only
at the largest size has no measured persistence beyond it. No result, crossover
or dominance claim is accepted until the complete matrix and independent raw
audit pass. No historical timings are pooled into this extension.
