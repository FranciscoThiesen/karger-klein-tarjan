# Dedicated bounded outer controller

Source-only, unexecuted. New file:
`overlay/benchmark/results/eighth-sampling-2026-10-15/validation/run_build_phase.py`.
Its four mocked groups are in `overlay/benchmark/test_eighth_controller.py`.
Do not use the generic `run_postcapture_validation.py` for native correctness:
that script states `native_solver_execution=false` unconditionally.

The original compressed validation directory retains native/sanitizer/final
controller receipts, recording approximately 37.25, 100.28 and 3.50 seconds,
but those receipts do not identify a reusable archived outer controller
function. The new script makes that lifecycle explicit without editing any
frozen helper or native source. Historical durations are only context for
finite guard budgets, not promised runtimes.

The script accepts a fixed phase, a new attempt prefix and `--released`.
It constructs the exact command itself; arbitrary commands, performance and
work-driver phases are not accepted. Command budgets are 180 seconds for each
mock phase and native correctness, 300 for sanitizers, and 120 for timing-build
or final-object validation. These are total phase deadlines, separate from
the inherited 300-second per-child inner limit. A missed deadline fails the
phase rather than silently increasing its budget. An integer monotonic exit
observation is checked even when the child already exited before the first
poll-loop body, so exit0 cannot bypass the phase deadline.

The outer Python process gets its own session/group and bounded RSS monitoring.
Inner `SerialGuard` compiler/test children get separate sessions, so observing
an empty outer group alone is insufficient. On TERM, the builder's installed
handler must reach its inner `finally`. The outer cleanup therefore allows
30 seconds before KILL: the inner guard can need 10 seconds TERM, 5 seconds
KILL and 5 seconds for its bounded group observation. Outer KILL then has a
5-second wait, followed by the bounded group observation. SIGTERM is ignored
during bounded outer cleanup and restored afterward. No indefinite wait is
used, and a poisoned sampler fails closed.

Successful completion requires actual exit0, source hashes unchanged, outer
empty-group proof, and complete inner guard receipts matched by command and
actual exit status to all compile/link/test records. Expected inner groups:
native67, sanitizer64, timing12, final15. Positives exit0 and deliberate policy
negatives exit1. Each nested group must have affirmative native/group exit,
matching return code and an empty bounded group observation. No mock declares
native solver execution; successful correctness/final receipts do declare it
and report the actual inner counts. Timing-build reports zero solver runs.

An abnormal outer completion preserves the outer cleanup evidence but
deliberately **does not** claim that every detached native session has exited.
It leaves `all_owned_groups_verified_empty=false` and native execution unknown
until the specific inner evidence is audited. Never advance to another phase
based only on an empty outer group. A killed builder may not have saved an
active inner child's receipt. Preserve its partial files and resolve the
owned-session status before any further launch.

Each prefix creates four exclusive files: `.invocation.json`, `.stdout`,
`.stderr`, and final `.json`. Existing artifacts are rejected before launch.
The final receipt includes wall deadline, actual exit, UTC/monotonic endpoints,
source hashes, bounded monitor observations/events, cleanup proof and complete
inner receipt hashes. Signals, timeouts, provider failures and cleanup errors
remain failed evidence. There are no benchmark durations or confidence claims.

After isolated installation and root release, use the commands in the updated
root handoff. The controller's own four tests replace all subprocess calls
with mocks; they can be the first fixed phase. That bootstrap is still an
executed test gate, not a source-only pass. Independent source review passed
after the deadline correction; see `INDEPENDENT_SOURCE_REVIEW.md`. All four
mocked groups remain unexecuted and must pass after release before native
phases.
