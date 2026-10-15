# Eighth study: deferred root execution handoff

**Do not run during the performance hold.** All commands below are prospective;
the new package has only source-review passes. Root owns release, installation,
attempt receipts, commits, freeze and any later timing. The frozen compressed
source plus its three new native additions is the exact baseline contract.

## Isolated install after release

Use the compressed freeze commit `fbdf4a8`, resolving it to a full commit before
creating the worktree. This contains the frozen native/helper/build sources;
later reports and captures are not needed in the new checkout. The original
compressed worktree and all ancestor artifacts must remain at their original
paths for full parent validation.

```sh
set -e
TASK_PARENT=/Users/random_person/Desktop/kkt-compressed-queries
TASK_TREE=/Users/random_person/Desktop/kkt-eighth-sampling
TASK_PREP=/tmp/kkt-eighth-sampling-prep
TASK_BASE=$(git -C "$TASK_PARENT" rev-parse --verify 'fbdf4a8^{commit}')
test ! -e "$TASK_TREE"
git -C "$TASK_PARENT" worktree add -b codex/kkt-eighth-sampling "$TASK_TREE" "$TASK_BASE"
cd "$TASK_TREE"
git apply --check "$TASK_PREP/native.patch"
test ! -e kkt/experimental_eighth_sampling.hpp
test ! -e test/eighth_sampling_test.cpp
test ! -e test/eighth_sampling_integration_test.cpp
test ! -e benchmark/build_eighth_sampling.py
test ! -e benchmark/run_eighth_sampling.py
test ! -e benchmark/results/eighth-sampling-2026-10-15
git apply "$TASK_PREP/native.patch"
cp "$TASK_PREP/overlay/kkt/experimental_eighth_sampling.hpp" kkt/
cp "$TASK_PREP/overlay/test/eighth_sampling_test.cpp" test/
cp "$TASK_PREP/overlay/test/eighth_sampling_integration_test.cpp" test/
cp -R "$TASK_PREP/overlay/benchmark/." benchmark/
cmp -s "$TASK_PREP/overlay/kkt/kkt.cpp" kkt/kkt.cpp
git diff --check
TASK_VALIDATION="$TASK_TREE/benchmark/results/eighth-sampling-2026-10-15/validation"
TASK_PARENT_FREEZE="$TASK_PARENT/benchmark/results/compressed-query-2026-10-15/freeze.json"
```

If the branch/destination already exists, stop and inspect it; do not reset or
overwrite it. Record `TASK_BASE` in the install receipt. The parent freeze SHA
must be `bd65da13058d3e9cfa58919a0fe5e02b8a46b1d0b8fe7f05801692d5a0866df9`.
Builder and collector independently check its full original proof, not only
that digest. Only existing `kkt/kkt.cpp` may differ in the native inventory;
the header and two named tests are the only native additions.

## Mock and build commands

Run each command through the dedicated prepared outer attempt controller, with
exclusive invocation/stdout/stderr/status/hash/group-exit receipts under
`TASK_VALIDATION`. Do not start the next command after a failure or an unknown
owned-group exit. These are command arguments for that controller, not advice
to run concurrent bare-shell processes. The inner build guard also enforces
40 GiB RSS, two-second bounded observations, three unavailable samples,
poison stop, a 300-second child deadline and SIGTERM/finally cleanup.

```sh
TASK_CONTROLLER="$TASK_VALIDATION/run_build_phase.py"
python3 -B "$TASK_CONTROLLER" --phase controller-mocks --prefix "$TASK_VALIDATION/controller-mocks-attempt01" --released
python3 -B "$TASK_CONTROLLER" --phase build-mocks --prefix "$TASK_VALIDATION/build-mocks-attempt01" --released
python3 -B "$TASK_CONTROLLER" --phase collector-mocks --prefix "$TASK_VALIDATION/collector-mocks-attempt01" --released
python3 -B "$TASK_CONTROLLER" --phase native-correctness --prefix "$TASK_VALIDATION/native-controller-attempt01" --released
python3 -B "$TASK_CONTROLLER" --phase sanitizer-correctness --prefix "$TASK_VALIDATION/sanitizer-controller-attempt01" --released
python3 -B "$TASK_CONTROLLER" --phase timing-build --prefix "$TASK_VALIDATION/timing-controller-attempt01" --released
python3 -B "$TASK_CONTROLLER" --phase final-objects --prefix "$TASK_VALIDATION/final-controller-attempt01" --released
```

The controller constructs the previously declared exact inner commands: local
builder with `--profile PHASE --output "$TASK_VALIDATION" --parent-freeze
"$TASK_PARENT_FREEZE"`, or the local final validator with `--output
"$TASK_VALIDATION"`; all run with the same Python executable and `-B`. It
rejects arbitrary command arguments. `CONTROLLER_PREPARATION.md` documents
bounded cleanup cooperation and nested-session evidence. The generic
postcapture wrapper is not used for native phases.

Expected declared mock counts are **4 controller, 7 builder and 14 collector groups**;
confirm the final reviewed source before running. Each native/sanitizer profile
expects **20 positive suites + 4 clean wrong-policy negatives**, 1,344 matched
full-KKT records, exact 65-field parent half replay and a positive changed-work
witness. Timing-build performs **12 compile/link commands and no driver run**.
Final-object validation expects **4 positives + 2 negatives + 2 byte-identical
KKT rebuilds**, with actual final-object certificates plus the explicitly
separate same-flags source-inclusion oracle. No extra 2-by-2 verifier variant.

All profiles use fresh `.build/eighth-sampling/{profile}` and
`bin/eighth-sampling/{profile}` directories and refuse overwrites. Final gate
uses `final-object-gate` under those namespaces. Preserve rejected profile
directories and logs; any repaired retry needs a separately retained attempt.
The final script has no `--parent-freeze` option: it uses and validates the
same original compressed path pinned in `build_eighth_sampling.PARENT_PATH`.

## Runtime and path constraints

- Use the proven Python 3.9-or-later interpreter in a **fresh process**. Run
  from the canonical new worktree root (`pwd -P`), not from `/tmp/overlay`.
  The prepared files depend on the unchanged local `benchmark/` helper copies.
- `unittest discover -s benchmark` and direct builder scripts put the local
  benchmark directory on the import path. The final script adds it explicitly.
  An outer Python controller importing the builder must first insert the new
  worktree's canonical `benchmark` path; do not prepend the parent worktree
  or reuse a process that already imported a same-named parent module.
- The inherited builder's `ROOT` and new builder's `ROOT` must be the same
  canonical worktree. Parent-helper rebinding changes only equal-hash path
  spellings during the original checker and restores them. It is not a way
  to bypass parent source or artifact verification.
- Normalize temporary mock paths with `Path(...).resolve()` when comparing
  identities: macOS `/var` and `/private/var` aliasing must not be mistaken for
  two different artifacts. Do not weaken actual capture path validation.
- Native compiler is `/usr/bin/clang++`, AppleClang 15 matching the parent's
  compiler text and SDK. Sanitizer compiler is
  `/opt/homebrew/opt/llvm/bin/clang++`, Clang 22. Both are explicitly launched
  through `/usr/bin/arch -arm64`; a translated Python process must not cause
  implicit x86 compilation. The profile checks arm64 binaries and 512 MiB
  main stack. Assertions remain enabled; no NDEBUG or packed macro is allowed.
- No third-party plotting package is needed for these gates. Do not execute
  the timing binary or prepared work drivers as a build check. Keep original
  ancestor native objects, binaries, logs and helpers available for the full
  source/build proof; missing evidence is a failed gate, not a reconstruction
  license during capture.

After all gates and independent reviews pass, stop and report exact receipts,
binary hashes and known-empty owned groups. Root then reviews private-log
exclusions, commits the source/protocol/evidence, creates and checks the new
freeze, commits that freeze, and separately releases the fixed 48-child study.
The collector protocol contains prospective preflight/capture arguments;
none is authorized by this handoff alone.
