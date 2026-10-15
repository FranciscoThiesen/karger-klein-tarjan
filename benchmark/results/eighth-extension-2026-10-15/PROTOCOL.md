# Prospective eighth-only hierarchy size extension

**Source declaration only, 2026-10-15. No import, test, preflight, freeze or
native execution has been performed for this package.** The matrix and seeds
were selected before inspecting any paired eighth-sampling timing results.
The future decision to run waits for that study's complete validated results;
this preparation neither asserts a lead nor authorizes a capture. If deferred,
retain this declaration as unexecuted. Any changed matrix needs a separate
prospective declaration.

## Fixed question and complete matrix

Does the existing eighth-sampling KKT implementation exhibit a sustained
measured size crossover against retained-edge Borůvka, or any of the other four
controls, on the hierarchy attachment family? Do shuffled core weights remove
that advantage? This is a single-binary size screen. It cannot estimate the
effect of changing sampling probability; that question belongs to the paired
half/eighth study. No historical timings enter any estimate here.

The exact fourteen-row [manifest](manifest.csv) contains `leaf_hierarchy4` and
`leaf_shuffled4`, each at **n = 1,024; 4,096; 16,384; 65,536; 262,144; 1,048,576;
4,194,304**, with **m/n = 32** and **intrusion = 0** throughout. Graph seeds are
**17000011 and 17000047**; one scalar KKT sampler seed is **2801**. The scoped
[freshness scan](SEED_FRESHNESS.md) is source/declaration evidence only.

Graph one follows the ascending-size manifest, with weight twins adjacent.
Graph two reverses the entire manifest, including twin order. Each child runs
KKT, compacting Borůvka, retained-edge multigraph Borůvka, Kruskal, Prim and
original Borůvka. The unchanged native harness certifies one warmup and six
timed calls per solver, rotating each solver through all six positions. Thus
**28 children produce 1,176 certified outputs: 1,008 timed and 168 warmups**.
Six repeats reuse one graph/forest realization; there are only two graph
realizations and one sampler seed, not twelve independent random inputs.
Graph seed remains confounded with full schedule reversal and host history.

These are engineered graphs with three cheap leaves attached to each core
vertex. Hierarchy weights put every core path edge below every chord and order
path ranks by dyadic boundary level. The shuffled twin permutes core ranks,
retaining the cheap leaves. Require identical topology/order fingerprints and
different weighted fingerprints at all **14 size/graph twin pairs**. The
generator, independent certificate, unique IDs and validation are unchanged.

## Exact inherited artifact and supported domain

Use the existing candidate without rebuilding:

- Worktree: `/Users/random_person/Desktop/kkt-eighth-sampling`.
- Parent freeze: `benchmark/results/eighth-sampling-2026-10-15/freeze.json`.
- Parent freeze SHA-256: `2be7556d15b58f3f65cc380ac22b67c57fdf8aea747d651b9d648c6a1aa59d2f`.
- Variant: `eighth`; executable: `bin/eighth-sampling/timing-build/eighth/retention_control`.

The new collector invokes the unchanged eighth collector's complete strict
freeze checker. Both parent variants and all ancestor proofs remain checked,
including exact source, overlay, compiler/SDK/flags, recipe/log, object, binary
and arm64/stack-profile evidence. The extension inherits the exact eighth
artifact; it adds its own source hash, protocol, manifest and schedule. It never
changes parent-module seed globals or frozen helper/native files. Private
sampling accepts `(rng() & 7) == 7`, one RNG word per visited edge, with the
existing reserve policy; compressed verifier queries remain enabled.

All cases stay inside the existing inclusive n≤4,194,304 and m≤134,217,728
limits. The largest reaches both limits exactly. For any listed n, q=n/4 core
vertices have 3q leaf edges and 125q core edges. At n=1,024, q=256 and 32,000
core edges occupy 32,000/32,640 of all simple pairs: the smallest core is nearly
complete, with average core degree 250. Larger cores keep that average degree
but become proportionally sparser. This finite-density difference must not be
mistaken for a pure n-only scaling law or a natural-graph prevalence claim.

No resource estimate is a guarantee. Completed different-policy 4M evidence
demonstrates supported input generation, not this policy's future peak RSS or
runtime. Recursive lifetimes and sampled forests can differ. No 8M input,
domain extension, generator change or raised memory ceiling is authorized.

## Quiet capture and fail-closed evidence

After reviewed mocked gates and a prospective freeze, root must separately
release a quiet serial performance capture. The collector requires
`--released`. Use the inherited **40 GiB sampled process-group RSS ceiling**,
about two-second polling, bounded sampler request deadline, immediate stop on
sampler poison and stop after three consecutive unavailable observations.
Keep the inherited bounded TERM/KILL cleanup; no timeout or ceiling relaxation
is allowed. RSS is sampled, not a continuous maximum.

Preserve every native argv, child CSV, independent certificate, `/usr/bin/time
-l` log, RSS record, clock endpoint, exit status and flagged call. After wrapper
exit, obtain a bounded observation proving the owned group empty before any
next launch. On failure/interruption mark exit unknown before cleanup, suppress
repeated SIGTERM only inside bounded cleanup, restore the previous handler and
clear unknown only after affirmative native-exit and group-empty proof. A
prior unknown state remains unknown. No subsequent child follows failure.

Never overwrite partial evidence, silently retry, substitute a size, remove a
solver, skip certification or drop a loss. A resource failure stops and is
reported for this fixed matrix. Any released retry uses a fresh attempt and
retains all earlier evidence. Strict reload verifies the full parent proof,
exact 28-child schedule, all 1,176 raw rows and certificates, monitor telemetry,
empty-group evidence and exact ordered combined CSV concatenation. Clock flags
never trim or adjust observations. Optional archived power-log correlation is
diagnostic and does not establish verified sleep inhibition. Private power
logs require study-specific ignore rules before capture.

## All comparisons and exact sustained brackets

Pair KKT with every control within the same child/graph/sampler/repetition, on
wall and process CPU clocks separately. Pool all twelve paired ratios per case;
retain each graph's six-ratio median. These are medians of paired ratios, not
ratios of runtime medians. Keep every trial endpoint, full ranges, absolute
times, warmups and both graph medians. Ranges are descriptive, not confidence
intervals or evidence from twelve independent graphs.

| Canonical table | Rows | Derivation |
|---|---:|---|
| `paired_ratios` | 1,680 | 14 cases × 2 graphs × 6 repeats × 5 controls × 2 clocks |
| `comparisons` | 140 | 14 × 5 × 2 |
| `graph_comparisons` | 280 | 14 × 2 × 5 × 2 |
| `summary` | 168 | 14 × 6 solvers × 2 clocks |
| `graph_summary` | 336 | 14 × 2 × 6 × 2 |

For each family/control/size reconstruct all four graph/clock medians using
exact Fractions of integer timing endpoints. The median of six is the mean of
the two central ratios. Classify `strong_lead` iff all four≤9/10; `narrow_lead`
iff all four<1 but not strong; `loss` iff all four>1; otherwise `mixed_or_tied`.
Retain **70 point classifications** (2×5×7).

A strong observed crossover bracket requires an earlier `loss`, a later
`strong_lead` and `strong_lead` at **every larger measured size**. Preserve all
**210 earlier/later endpoint pairs** (2×5×21) and **10 family/control summaries**.
The representative bracket uses the earliest qualifying upper endpoint, then
the closest measured loss below it; all alternatives and earlier reversals
remain visible. An always-leading family has no observed loss-to-lead
crossover. A lead appearing only at 4M has no measured persistence beyond 4M.
No interpolation, monotonicity assumption, historical pooling, clock/drift
normalization or asymptotic dominance claim is permitted.

Retained-edge Borůvka is the primary filtering-overhead comparison, but a win
against it is not a win against Prim, Kruskal or original Borůvka. Publish all
ten family/control outcomes and both clocks, including losses and any reversal.
An independent raw audit must recompute the final ratios, summaries and exact
classifications without calling the collector's aggregation functions before
plots or conclusions are accepted.
