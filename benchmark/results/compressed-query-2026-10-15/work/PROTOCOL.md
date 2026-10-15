# Prospective cumulative compressed-query diagnostics

This supplementary work matrix is declared before the compressed-query timing
results. No native diagnostic runs are authorized by this document. Prepare its
freeze only after the complete timing capture passes strict reanalysis; native
work requires a separate explicit root release and `--released`. Never overlap
diagnostics, tests, imports or analysis with native performance capture.

Reuse the unchanged three-solver driver
`benchmark/results/retention-control-2026-10-15/work/driver.cpp`, SHA-256
`ae08c5d199d83668d81f41a573452fea099c7e7cd5bd9bb4807c4a8ba9120e25`.
The native-correctness builder already linked it to both instrumented variants;
no driver, native source, frozen timing helper or counter field is changed here.
The driver is supplementary source outside the native inventory and is bound
explicitly by its fixed digest.

## Fixed inputs and provenance

Mirror all **24 timing children**, once each: six manifest cases, graph seeds
8000009 and 8000023, one sampling seed 1801, and reference/compressed variants.
The first graph follows manifest order, reference then compressed; the second
reverses cases and variant order. Retain every input and both variants without
selection based on performance or counter changes. Each child runs KKT,
deduplicating compacting Borůvka, and retained-edge multigraph Borůvka, for
**72 certified solver records** and two independent contraction round replays
per child. These are logical work measurements, not another timing study.

`prepare` must strict-load the completed timing capture and bind its full
source/build/helper/parent proof, raw fingerprints and exact schedule. Bind
this collector/protocol, both existing native-correctness build records, the
fixed supplementary driver, all eight production objects, nine target main
objects/executables, build recipe and log. Reconstruct the entire ordered
**36-command** native compile/link sequence, accepting no later object overwrite
or extra command. Seven production objects, including scalar `kkt.o`, and all
nine main objects are physically shared. Only compressed `verifier_v2.o` adds
`KKT_EXPERIMENT_COMPRESSED_QUERIES`; its hash must differ from the reference.
Compiler, SDK, common flags, base, parent freeze and native source inventory
must match the timing proof. Work executables are native arm64 with the same
512 MiB stack, assertions and work counters enabled.

Each diagnostic input must reproduce its timing weighted/topology fingerprint.
The unchanged native driver independently certifies the reference MST and
requires exact edge-ID equality from all three solvers, then validates exact
ID equality for both separate round replays. The collector checks the raw
certificate, complete JSON schema, every expected input field, `n-1` output
items and all 65 unsigned counter fields. The zero-intrusion input contract is
explicit because the driver omits that field from its output.

## Cumulative identities

For each of the 12 matched reference/compressed KKT pairs, require **61 fields
identical**. Exactly four fields may change, under these exact identities:

```
Q    = reference.verifier_queries          # unchanged logical proper requests
M    = reference.verifier_tree_edges       # cumulative connected-tree query edges
T    = reference.verifier_tree_calls
Nsum = reference.fbt_output_vertices
U    = compressed.path_query_visits - 2*Q

0 <= U <= Q
reference.path_query_visits = 4*Q
reference.initialized_slots - compressed.initialized_slots = M + Q - U + T
reference.verifier_edge_visits - compressed.verifier_edge_visits = M
compressed.verifier_vertex_visits - reference.verifier_vertex_visits = Nsum
```

The remaining path-query difference is therefore `2*Q-U`. A completed matrix
must contain a positive-Q witness, so accidentally using the reference query
path for both variants cannot pass merely through zero-query fixtures. Check
each completed pair immediately before another child may launch, and repeat
all checks during strict reload. No intermediate sample/forest trace is claimed;
unchanged sampling/recursion counters are cumulative equality checks.

U is the **sum of per-call distinct (vertex, ancestor-depth) requests** inferred
from existing counters, not globally unique requests across recursive graphs.
Q counts logical proper-ancestor requests; it is not silently redefined as U.
Report Q, U, U/Q, M, T, Nsum and all four reductions/additions. Normalize by the
original input edge count only when explicitly labeled. Q=0 produces a null
fraction with `both_zero` status. All 65 field differences remain present,
including zeros and any increased vertex work. No per-call distribution, vector
capacity, allocator behavior, bytes moved, cache effect, runtime attribution or
peak-memory saving follows from these aggregate counters.

For each case and graph, both Borůvka continuations' full counter records and
round sequences must agree between variants. Their final set-insert count is
`null`, explicitly unmeasured. Replay sums must match the actual helpers'
instrumented aggregates, and KKT's first two retained-contraction dimensions
must match the retained-edge replay. The WorkStats boundary includes tuple-to-
Edge input construction, the solver and temporary input destruction; generation,
certification, output checking and replay remain outside it.

## Fail-closed capture and outputs

Reuse the existing bounded owned-process-group monitor without altering frozen
helpers: 40 GiB sampled group RSS ceiling, roughly two-second observations,
stop after three unavailable samples or immediately on sampler poison, bounded
TERM/KILL cleanup, and confirmed empty group before another launch. Every child
has a 1,800-second native-exit deadline. Bound the wait by remaining budget and
check the observed exit immediately; post-exit verification does not extend the
budget. Retain the bounded post-wrapper empty-group observation in both raw RSS
and telemetry. Deadline, ordering, hashes, counts, certificates and resources
are checked again on reload. Unknown exit or any invalid output/pair stops the
matrix and preserves every failed partial; no overwrite, retry substitution or
recovery is automatic. Process durations and RSS are monitoring evidence, not
algorithm performance measurements.

Strict analysis exports 72 all-counter solver rows, every replay round,
**780 paired KKT field rows** (12×65) and **12 cumulative query rows**, retaining
both graph seeds separately. Metadata states `performance_claim=false` and
`memory_peak_claim=false`. No summary treats the two graphs as more independent
replications or converts cumulative U into a distribution.

Before native release, run and archive the dedicated mocked tests with source
hashes, exact invocation, stdout/stderr and status. Tests cover the complete
24-child schedule, summaries/zero rows, all four identities and unchanged-field
rejections, U boundaries/wrong dispatch, actual instrumented build provenance,
extra compile/flag/object/role/source drift, malformed JSON/schema/certificates,
comparator drift, late native exit and self-consistent reload, RSS failures,
poison, unknown exit, and refusal to launch a further child after failure.
Mock tests launch no native diagnostic or timing executable.
