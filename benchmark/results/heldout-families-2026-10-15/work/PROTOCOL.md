# Untimed work across the entire held-out family matrix

Prepared source-only on 2026-10-15 while held-out performance capture was active.
No partial performance output was read to choose this diagnostic matrix. The
held-out and separate larger performance captures have now completed, and root
has released mocked validation and prospective freeze preparation. The first
nine-group mocked attempt passed; retained attempt receipts identify subsequent
validation and preparation gates. Native diagnostic capture remains separately
scheduled and unexecuted. No native object or frozen helper is rebuilt or
changed, and diagnostic execution may not compete with performance timing.

## Fixed inputs and existing artifact

Run every one of the timing study's **36 cases at both graph seeds**, once:
leaf_distance4 / leaf_shuffled4, grid2d_metric / grid2d_random, and line_metric /
line_random, at n=1024, 4096, 16384, 65536, 262144 and 1048576; density 32 and
zero intrusion. Graph seeds remain 9000011 and 9000049, sampling seed 2003.
Follow the exact frozen timing schedule, including its rotated adjacent-family
size blocks and full reversal for graph two. This is **72 children**, with no
selection by timing or diagnostic outcome.

Use only the already built native instrumented compressed artifact at
`bin/compressed-query/native-correctness/compressed/retention_work`. It runs
KKT, deduplicating compacting Borůvka, and retained-edge multigraph Borůvka once
each, then independently replays both Borůvka contractions. The unchanged driver
is `benchmark/results/retention-control-2026-10-15/work/driver.cpp`, SHA-256
`ae08c5d199d83668d81f41a573452fea099c7e7cd5bd9bb4807c4a8ba9120e25`.
There is no new compile/link command and no uncompressed diagnostic variant.

Before preparing a new work freeze, strict-load the **completed** 72-child /
3,024-output timing capture. Require its freeze SHA-256
`6b120affb241e447ce5875645e7b746dfd1164a03aeabefffd4d42f5a01ba28f`.
This includes the complete timing source/helper/build/parent, raw row,
certificate, clock, resource and concatenation proof. Join every diagnostic
child to the exact weighted and topology fingerprints from that capture.
Fingerprint identity is required across timing's solvers, repetitions and
phases before constructing the diagnostic schedule.

Reuse the unchanged compressed-work checker, pinned at SHA-256
`6bba53051d5ce6565b6eaff43a9118f20d4eeb5491ac25686e2707c50233fda1`,
and its original work freeze, SHA-256
`6fe07ed1d07ab5fc0a374a4e2090022589e3f91ade3f15940c48a58b34549a2b`.
That checker reconstructs all 36 original instrumented compile/link commands,
both original verifier object sets, all nine main objects/executables, the
shared object identities, flags, compiler/SDK and complete original timing
parent proof. Select only its checked compressed artifact. Keeping the other
original objects as provenance dependencies does not execute them or pool any
historical measurements. Require the current held-out timing and instrumented
builds to have identical native source inventories and production toolchain.

The new freeze binds those inherited paths plus its own collector, protocol and
tests. Conflicting hashes for a repeated path are rejected. No original frozen
checker or source file is edited, and no source/helper seed globals are changed.

## Certificates, counter schema and round checks

Each native child independently certifies its reference MST and checks exact
MST edge IDs from all three solvers and both separate contraction replays.
Require the raw certificate, complete `retention_control_work_v1` JSON schema,
all expected input fields/fingerprints, `n-1` certified output items, exactly
three solver records and exactly two replay chains.

Keep the canonical **65 fields** per solver, with exact field/member names and
unsigned integer counters below 2^64. The two comparator `hash_insert_items`
fields remain `null`, explicitly unmeasured; KKT's measured field must equal
the certified MST size. Preserve all zero counters. Validate unwound recursion,
sampling/verifier volume equalities, accepted-sample bounds and contraction scan
bounds. The WorkStats boundary includes tuple-to-Edge input construction, solver
work and temporary input destruction; generation, certification, result checking
and replay are outside that boundary.

For each replay, require complete ordered round identities, exact chained
vertex/edge dimensions, shrinking bounds, terminal empty graph, selected-edge
sum `n-1`, and equality between replay sums and every corresponding cumulative
contraction field. These inputs are connected: each nonterminal quotient remains
connected, so selected edges equal the reduction in its vertex count. The last
singleton is removed by isolated-vertex cleanup; its terminal selected count
is therefore previous_vertices-1. Require the terminal zero-vertex/zero-edge
agreement and unsigned round fields. KKT's first two retained-contraction
dimensions must match the retained replay; if it finishes before a second
round, the root-after-two dimensions remain zero.

For the fixed compressed implementation, report cumulative
`Q=verifier_queries`, `M=verifier_tree_edges`, `T=verifier_tree_calls`,
`Nsum=fbt_output_vertices`, and infer
`U=path_query_visits-2*Q`, requiring `0 <= U <= Q`. Require at least one positive
Q in the complete matrix. `U/Q` is null with an explicit status when Q=0.
U sums distinct lower-vertex/ancestor-depth requests separately in each
connected verifier call. It is neither global uniqueness nor a per-call
distribution. These are representation consistency checks for the already
proved artifact. **There is no 61-equal/four-delta pair gate in this extension**,
because no uncompressed variant is executed. Do not invent observed savings
against an unexecuted reference or infer allocator/cache behavior.

Recheck the 36 matched topology twins and their distinct weight fingerprints,
as well as all individual timing/work joins. Keep all families, sizes and seeds
separate; diagnostic graph realizations are not extra timing replicates.

## Bounded serial lifecycle and output counts

Preserve the existing 40 GiB sampled process-group RSS cap, approximately
two-second observations, bounded provider calls, poison stop, three-unavailable
limit and 1,800-second native-exit deadline. Limit each wait to remaining budget
and reject a late observed exit. Record a successful empty-owned-group sample
after wrapper exit before another child may launch. Unknown exit or invalid
output stops the schedule and preserves the failed partial; no overwrite,
automatic recovery, favorable omission or raised ceiling.

The new collector marks exit unknown before bounded cleanup and suppresses
SIGTERM during that cleanup. It records cleanup exceptions and restores the
handler. Unknown clears only with affirmative native-exit and group-exit proof
and an explicit false may-still-run flag; a prior unknown remains unknown.
Frozen monitor helpers stay unchanged. Full schedule, hashes, exits, intervals,
resource observations, certificates and counter checks repeat on strict reload.

Complete analysis contains:

- `work.csv`: **216** solver rows × 65 counter fields = **14,040** cells;
  **144** comparator hash cells are explicitly unmeasured.
- `round_chains.csv`: **144** replay-chain summaries, two per input.
- `rounds.csv`: every individual replay round. Its row count depends on the
  graphs and is recorded after capture, never fixed or trimmed prospectively.
- `query_work.csv`: **72** cumulative Q/U diagnostic rows and labeled
  normalization by original input edges.
- `provenance.json`: exact bound inputs, output counts and
  `performance_claim=false`, `memory_peak_claim=false`.

Process durations and sampled RSS exist solely for monitoring. They are not
per-algorithm timing or peak-memory measurements. No timing ratio, performance
crossover, regression fit, or all-six-solvers ranking is produced here.

## Validation and separately released capture commands

Only after root releases nonperformance validation, archive the mocked suite's
exact command, source hashes, stdout/stderr, exit status and known-empty process
group. Preserve any failed attempts and investigate them before changes.

```
python3 -B benchmark/results/heldout-families-2026-10-15/work/test_collect.py
python3 -B benchmark/results/heldout-families-2026-10-15/work/collect.py prepare --timing-capture benchmark/results/heldout-families-2026-10-15/heldout.json --freeze benchmark/results/heldout-families-2026-10-15/work/freeze.json
```

Commit source, test evidence and the prospective freeze before a separate quiet
diagnostic release. `capture --released` still needs root scheduling; the flag
alone is not permission to compete with another study.

```
python3 -B benchmark/results/heldout-families-2026-10-15/work/collect.py capture --freeze benchmark/results/heldout-families-2026-10-15/work/freeze.json --output benchmark/results/heldout-families-2026-10-15/work/capture-attempt01.json --released
python3 -B benchmark/results/heldout-families-2026-10-15/work/collect.py analyze --capture benchmark/results/heldout-families-2026-10-15/work/capture-attempt01.json --output-dir benchmark/results/heldout-families-2026-10-15/work/analysis-attempt01
```

Capture and analysis commands remain prospective until separately released.
Read the retained mock and preparation receipts for actual validation status;
the command recipes alone are not evidence of diagnostic results.
