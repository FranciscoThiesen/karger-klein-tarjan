# KKT versus compacting Borůvka: searching for a real crossover

12 October 2026 · Apple M3 Max · continuation of the [common-family study](../common-2026-10-11/README.md)

## What this comparison measures

The competitor repeatedly calls KKT's exact production `boruvka_step` until the
graph is empty. Both strategies start from the same tuple list, include input
conversion, temporary-input destruction and construction of the same reserved
edge-ID set. Neither receives the fixture's backbone or hierarchy metadata.
Production KKT, contraction and verification code are unchanged from the earlier
study. The [source-boundary audit](boundary_audit.json) also checks that the
compactor wrapper and timing function stayed identical across exploration
revisions.

This compares whole continuation strategies. Recursion, random-number generation,
filtering, storage lifetimes and output accumulation all count. It does not
isolate verifier instructions, and it does not establish that either competitor
is the fastest possible MST implementation.

## The missing structural condition

The earlier common families often collapsed into a tiny, sparse residual. More
Borůvka rounds were cheap. Here the hypothesis is different: **vertices merge
slowly while many distinct edges remain**. Repeated contraction must then scan
large residuals several times, creating an opportunity for sampling and
filtering.

The new generators use a path or a randomly embedded dyadic tree as a connected
backbone, plus uniformly sampled distinct shortcut pairs. There are exactly
`m = d*n` edges, so average degree is `2d`; these are asymptotically sparse inputs
at fixed `d`, even when their contracted residuals become dense. All vertex labels
and edge order are independently shuffled. All weights are distinct positive
integer ranks.

| Weight model | Construction | What it tests |
|---|---|---|
| Hierarchical path/tree | Backbone edges are cheaper than shortcuts; their ranks follow dyadic merge levels | Exact pairwise contraction with many surviving shortcuts; deliberately planted MST |
| Distance-ordered path/tree | Every edge is ranked by `floor(log2(u xor v))` before relabeling, with random order within levels | The same contraction schedule, with shortcut edges eligible for the MST |
| Cheap shuffled path | The backbone stays cheap, but its internal weight order is shuffled | Whether planting a cheap backbone is enough without exact dyadic ordering |
| Globally random path/tree | Random ranks across every edge of the identical topology | Separates weight ordering from topology, IDs, labels and input order |
| Legacy random | Unchanged earlier random generator at several densities | Continuity with ordinary random-graph results |

The distance ranks are order-equivalent to tie-broken hierarchical metric costs;
the stored integer ranks themselves are not claimed to satisfy the triangle
inequality. These remain **engineered hierarchical models**, not measured
application networks. Even the distance model retains most backbone edges in its
MST at large sizes; the certified overlap is logged rather than hidden.

The [mechanism derivation](MECHANISM.md) gives the exact expected residual-edge
formula. At fixed density greater than one, the idealized hierarchy can force
expected Θ(m log n) total contraction-input volume. KKT's filtering targets that
volume: a half-sample's MSF leaves only O(n) expected light edges. That is a
structural explanation, not a wall-clock crossover guarantee. See the
[original sampling lemma](https://people.csail.mit.edu/karger/Papers/mst.pdf).

## Evidence discipline

The [protocol](PROTOCOL.md) separates adaptive discovery from fresh-seed
confirmation. Initial discovery, its larger extensions and all losing controls
remain archived. Selection uses graph seeds 17 and 42, sampling seeds 0 and 1,
two balanced repetitions and one checked warmup. Additional size/density screens
are explicitly dated in the protocol before holdout.

Confirmation uses five fresh graph seeds (2027, 4099, 8191, 104729, 131071), three
fresh sampling seeds (11, 29, 97), four balanced repetitions and one checked
warmup. The second complete campaign reverses the first campaign's case order.
The predeclared descriptive threshold requires KKT/compaction ≤0.90 at the two
largest tested sizes of a selected family/density in **both** runs, with every
graph-level ratio below one. Failure cannot be rescued by pooling runs or by a
later sensitivity test.

Ratios are formed within matched calls, then summarized by medians over
repetitions, sampling seeds and graph seeds, in that order. Repetitions and
sampling seeds are not extra independent graphs. Graph ranges are descriptive,
not confidence intervals; the threshold is not a statistical significance test.
Independent time medians need not divide to the reported paired ratio.

A Kruskal reference receives an independent structure/connectivity/cycle-property
certificate. Every timed output, warmup and instrumented output must match its
exact unique MST IDs. Generation, reference construction, certification, result
checks and returned-set destruction are outside timing. Instrumented work and
contraction traces are captured separately. No instrumented duration is used as
performance evidence.

Only one timed process runs at a time; builds, tests and plotting occur between
timing campaigns. This is still an ordinary desktop experiment, without
controlled CPU affinity or power state. A [pre-confirmation snapshot](preconfirmation_host.json)
records active background services; the machine was not isolated. The [environment](environment.json),
build logs, exact runner commands, source/binary/manifest hashes and raw CSVs
bound every claim to this implementation and machine.

## Useful limits of the counters

For the screened hierarchical-path graph at n=262,144 and m=64n, averaging the
recorded graph/sampling seeds gives 53.56 million contraction-input edges for
KKT and 104.85 million for the compactor. But KKT also sends 22.23 million edges
through verifier inputs across its recursion, retaining about 190,045 light
edges. Edge materializations remain much closer: 100.37 versus 111.95 million.

The mixed logical-work proxy is actually **1.298 times larger for KKT** on that
case, despite its lower measured time. That proxy adds unlike visits,
initializations, table cells and API operations; it is not CPU instructions,
bytes transferred or a calibrated cost model. The same `contraction_edges`
counter is comparable between solvers; recursive-input volume is a different
quantity. No per-solver hardware measurements establish a cache bottleneck.
Whole-process instruction/cycle totals include setup and both solvers.

## Explore the mechanism

The [offline interactive explorer](visualization/index.html) contains seven
complete, certified n=64, m=256 fixtures. Compare weight variants, move through
actual production contraction stages and inspect component membership, selected
edges and residual edges. Layout positions are schematic; small pictures explain
the mechanism and are not timing evidence.

The exporter checks each stage against independent minimum-edge, disjoint-set
and parallel-edge oracles. Automated JavaScript checks cover 492 control
combinations and 984 rendered panel states. Browser appearance remains
unverified: headless Chrome failed and the browser tool denied local-file
navigation. [QA details](visualization/QA.md) retain those limitations.

## Setup repair and retained failures

The first extension attempt, `extension_timing.*`, was intentionally interrupted
after unusually slow fixture setup. It has no complete timing rows and is
excluded from performance analysis. Its failure metadata and the strict
analyzer's rejection remain archived.

A fixture-local mixed hash replaces an endpoint identity hash whose buckets
could cluster keys. It changes no RNG draws, membership decisions, graph order
or solver code. Exact comparisons cover 489 fixtures and a 4.19-million-edge
case. That large **generation-only** check improved from 12.283 to 0.605 seconds;
it is not a KKT speedup. [The archive](fixture-hash-repair/README.md) preserves the
old/new source, exact-output checks and one-call, old-then-new limitation.
Initial smoke captures predate runner hardening and are correctness/setup
checks, not performance evidence for the final conclusions.

Native correctness suites and the new 251-fixture suite passed; the latter
checks 753 KKT outputs. Analyzer tests include five accepted and 71 rejected
inputs; cross-campaign checks include five accepted and 32 rejected inputs.
Bazel failed during JVM/server startup before executing tests, including a
batch-mode retry. Both logs are retained; no new Bazel success is claimed.

## Reproduce the confirmation

The selection was committed as `7b4b3c5` before fresh-seed timing. The
[selection record](confirmation_selection.json) binds candidate groups, sizes,
seed banks, discovery files, manifests and the frozen native binary. Rebuilding
on another machine produces a different binary; it is a new replication, not
the archived campaign.

```sh
make -j4 bin/continuation_search bin/continuation_search_work bin/continuation_test
./bin/continuation_test
python3 benchmark/results/continuation-2026-10-12/run_capture.py \
  --binary bin/continuation_search \
  --manifest benchmark/results/continuation-2026-10-12/confirmation.csv \
  --output /tmp/kkt-confirmation.csv \
  --graph-seeds 2027,4099,8191,104729,131071 \
  --sampling-seeds 11,29,97 --repetitions 4 --warmups 1
```

Run the same command with `confirmation_reverse.csv` and a different fresh
output path for the second campaign. Run the campaigns serially, without
concurrent builds or analysis. The capture script refuses to overwrite evidence.
Its metadata contains the exact expanded command, source hashes, binary hash,
manifest hash and output hash. Graph generation and correctness checks are
included in whole-process wall time but excluded from solver durations.
