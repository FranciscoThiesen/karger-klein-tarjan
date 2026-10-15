# Proposed larger hierarchy/shuffled screen

This preserves the original assessment written before package preparation.
The subsequent [source-only seed audit](SEED_FRESHNESS.md) supersedes the
"not yet audited" seed status below; the [protocol](PROTOCOL.md) is the current
prospective declaration. The feasibility calculations and limitations are unchanged.

Source-only feasibility note, 2026-10-15. No imports, analysis program, build,
freeze, solver or monitoring job was run for this proposal. No partial results
from the active 72-child held-out study were read. This does not modify or
extend that study. All observed numbers below come from the completed
compressed-query experiment.

## Recommendation and fixed proposed scope

A separate guarded screen is plausible at the existing 40 GiB sampled group
RSS ceiling. The largest point is within the exact frozen binary's input
domain; completed-run scaling leaves about 8 GiB of nominal margin. Neither
source inspection nor sampled RSS guarantees that it will fit. A resource
failure must stop the campaign and remain a reported outcome.

Use the existing compressed binary without rebuilding:
`/Users/random_person/Desktop/kkt-compressed-queries/bin/compressed-query/timing-build/compressed/retention_control`,
SHA-256 `74e604830c4c730395cd6c9e9dc61287a6d88a34cc89983bb4ee61dc3272a1b2`.
Retain its full parent freeze/build/source/helper proof. It uses scalar sampling,
retained parallel edges, the Edge verifier view and compressed queries.

| Families | n | m/n | Intrusion |
|---|---|---:|---:|
| `leaf_hierarchy4`, `leaf_shuffled4` | 65,536; 1,048,576; 4,194,304 | 32 | 0 |

Two graph seeds and one scalar sampling seed must be fixed prospectively.
Proposed values are **11000009, 11000027; sampler 2203**. Their nonreuse is
**not yet audited**; verify against prior declared/captured inputs before any
freeze. Any correction must be made before observing this screen's outputs.

All six solvers remain: KKT, deduplicating compacting Borůvka, retained-edge
Borůvka, Kruskal, Prim and original Borůvka. With one checked warmup and six
balanced timed repetitions, this means six cases × two graphs = **12 children,
504 certified outputs (432 timed, 72 warmups)**. Follow increasing n with twins
adjacent for graph one; reverse the entire manifest for graph two. Require all
six topology-twin checks and different weighted fingerprints. Keep every lower
point, both twins, all five comparisons, both clocks and every loss. Do not
combine these fresh observations with historical timings.

## Source domain and representation

The CLI limits are n≤2^22 and m≤2^27 in `benchmark/retention_control.cpp`;
`core_attachment_fixtures.hpp::edge_count` and `run_mst_search.py::load_manifest`
accept these bounds inclusively. At the largest point:

- n=4,194,304; m=134,217,728, exactly the existing edge ceiling.
- q=n/4=1,048,576 core vertices; 3q=3,145,728 local leaf edges.
- core_m=m−3q=131,072,000=125q, well below q(q−1)/2.
- All IDs and unique positive ranks fit the existing signed-int/Prim-sentinel
  contract. Hierarchy path levels stop at 19, below chord tier 22.

No input-domain relaxation is needed. Conversely, 8M vertices at density32
would be outside this frozen binary's domain. Preserve all assertions, native
arm64 profile, 512 MiB stack, input generation, certificate and timing boundaries.

## Memory feasibility, not a bound

Completed `compressed-query-2026-10-15/analysis/resources.csv` reports these
whole-child sampled peaks for the compressed binary at n=1,048,576,d=32:

| Family | Graph seed | Observed KiB | Fourfold planning value KiB |
|---|---:|---:|---:|
| Hierarchy | 8000009 | 8,315,444 | 33,261,776 |
| Hierarchy | 8000023 | 8,276,532 | 33,106,128 |
| Shuffled | 8000009 | 8,128,496 | 32,513,984 |
| Shuffled | 8000023 | 8,132,668 | 32,530,672 |

These fourfold values are approximately **31.0–31.7 GiB**, versus a ceiling of
41,943,040 KiB = 40 GiB. The largest leaves 8,681,264 KiB, about **8.28 GiB**;
a further 25% above that simple scaling would be about 39.65 GiB. This is a
sensitivity illustration, not a confidence bound or a predicted peak.

Source allocation sizes support caution. At m=2^27, nominal 16-byte graph/Edge
records occupy 2 GiB per full copy, and the harness's retained 8-byte per-edge
pointer index occupies 1 GiB. Prim stores 2m directed 12-byte records (3 GiB of
live elements before spare capacity); its vectors and allocator overhead are
additional. Certification has m-sized pointer, weight and endpoint arrays, plus
O(n log n) tables. The two lifting tables alone grow to 8n×23 bytes, 0.71875 GiB;
this is 64 MiB above a naive fourfold scaling from the 1M, 21-level tables.

These allocations have different lifetimes and must not simply be summed into
a claimed peak. KKT retains enclosing graphs across recursion; half-reserved
sample vectors can grow; the generator uses node-based pair storage; freed
allocations need not immediately leave RSS. The completed whole-child samples
cover generation, certification and all six solvers, without attributing a peak
to any one phase. Two-second sampling can miss transients. Host memory pressure,
new seeds, capacities and additional recursion levels can invalidate scaling.

Use the unchanged bounded monitor, 40 GiB ceiling, three-unavailable/poison stop,
owned-group cleanup and verified empty groups before advancing. Do not skip
certification, drop a solver, increase the ceiling or substitute a smaller case
after a failure. No performance release is implied by this note.

## Why size provides a useful question

The source-derived hierarchy calculation is already recorded in
`density-search-2026-10-15/HIERARCHY_RETENTION.md`. Put L=log2(q), C=m−n+1.
Under its ideal uniform chord model, retained-edge Borůvka has

```text
E[V] = m + (2q−2−L)
       + C [L−1 + (3q(L−2)+6)/((q−1)(q−2))],
```

where V counts contraction-input edges, not all scans, allocations or time.
For d=32 the leading E[V]/m values at the proposed sizes are 13.609375,
17.484375 and 19.421875, with small positive finite-q corrections. Exact expected
values are approximately 13.6115, 17.4846 and 19.4219. Total deterministic rounds
are 15, 19 and 21. From 1M to 4M this adds roughly **11.1% input-edge work per original
edge**, while the original edge count itself rises fourfold.

Completed 1M hierarchy replays observed 17.48494m and 17.48456m over 19 rounds.
Their shuffled twins observed 7.31683m and 7.51768m over 8 rounds. These observations
support the mechanism: ordered merges retain heavy crossing chords for repeated
rounds. The hierarchy formula does not apply to the shuffled partitions. KKT
has its own growing verification/contraction costs; neither this logical-volume
derivation nor fourfold memory scaling predicts a runtime winner.

Predeclare an observed strong bracket separately for each of the five controls:
an earlier measured loss on both graph seeds and clocks, a later median ratio
≤0.90 on all four graph/clock combinations, and the same strong criterion at
every still-larger measured point. Retain all three endpoint pairs for each
family/control and all point classifications. A lead only at 4M has no measured
persistence beyond 4M; a lead at all points is not an observed crossover. Being
faster than retained-edge Borůvka is not being fastest among all six solvers.
