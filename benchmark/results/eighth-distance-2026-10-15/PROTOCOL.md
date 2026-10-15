# Prospective eighth-only dyadic-distance size ladder

**Source declaration only, 2026-10-15. No import, test, preflight, freeze or
native execution has been performed for this package.** Root accepted this
focused design after the completed half-policy held-out study and eighth
hierarchy extension. Selection is evidence-led; it is not an unbiased survey
or a previously unseen family. This preparation neither asserts a lead nor
authorizes a capture. If deferred,
retain this declaration as unexecuted. Any changed matrix needs a separate
prospective declaration.

## Fixed question and complete matrix

Does the existing eighth-sampling KKT implementation exhibit a sustained
measured size crossover against retained-edge Borůvka, or any of the other four
controls, on the dyadic-distance attachment family? Do shuffled core weights remove
that advantage? This is a single-binary size screen. It cannot estimate the
effect of changing sampling probability on these inputs without a new paired
half control. No historical timings enter any estimate here. The completed
half-policy distance ratios against retained-edge Boruvka were approximately
1.49 at 1K and 1.00 at 1M; the current hierarchy extension has no strict
losing smallest endpoint. These observations motivate this fixed new search,
not a prediction obtained by multiplying historical gains.

The exact twelve-row [manifest](manifest.csv) contains `leaf_distance4` and
`leaf_shuffled4`, each at **n = 1,024; 4,096; 16,384; 65,536; 262,144; 1,048,576**,
with **m/n = 32** and **intrusion = 0** throughout. Graph seeds are
**21000011 and 21000041**; one scalar KKT sampler seed is **3203**. The scoped
[freshness scan](SEED_FRESHNESS.md) is source/declaration evidence only.

Graph one follows the ascending-size manifest, with weight twins adjacent.
Graph two reverses the entire manifest, including twin order. Each child runs
KKT, compacting Borůvka, retained-edge multigraph Borůvka, Kruskal, Prim and
original Borůvka. The unchanged native harness certifies one warmup and six
timed calls per solver, rotating each solver through all six positions. Thus
**24 children produce 1,008 certified outputs: 864 timed and 144 warmups**.
Six repeats reuse one graph/forest realization; there are only two graph
realizations and one sampler seed, not twelve independent random inputs.
Graph seed remains confounded with full schedule reversal and host history.

These are engineered graphs with three cheap leaves attached to each core
vertex. Distance weights order every core edge, including shortcuts, by
`floor(log2(u xor v))`, with distinct randomized ranks within tiers. The forced
path ensures each dyadic sibling cut exists; full-graph contractions therefore
merge sibling blocks pairwise, although shortcuts can belong to the MST.
This is hierarchical distance **ordering**, not Euclidean distance or a claim
that rank weights satisfy the triangle inequality. The shuffled twin permutes core ranks,
retaining the cheap leaves. Require identical topology/order fingerprints and
different weighted fingerprints at all **12 size/graph twin pairs**. The
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
and arm64/stack-profile evidence. The distance study inherits the exact eighth
artifact; it adds its own source hash, protocol, manifest and schedule. It never
changes parent-module seed globals or frozen helper/native files. Private
sampling accepts `(rng() & 7) == 7`, one RNG word per visited edge, with the
existing reserve policy; compressed verifier queries remain enabled.

All cases stay inside the existing inclusive n≤4,194,304 and m≤134,217,728
limits. The largest listed case has n=1,048,576 and m=33,554,432. For any listed n, q=n/4 core
vertices have 3q leaf edges and 125q core edges. At n=1,024, q=256 and 32,000
core edges occupy 32,000/32,640 of all simple pairs: the smallest core is nearly
complete, with average core degree 250. Larger cores keep that average degree
but become proportionally sparser. This finite-density difference must not be
mistaken for a pure n-only scaling law or a natural-graph prevalence claim.

The family models a cheap periphery and hierarchical core costs, but its cheap
stars, forced path and balanced tier ordering are engineered. It is not an
application-data or natural-prevalence claim. At fixed density m=32n, input
size N=n+m=33n; finite timings are not an asymptotic complexity proof.

No resource estimate is a guarantee. Recursive lifetimes and sampled forests
can differ. No undeclared larger input, domain extension, generator change or
raised memory ceiling is authorized.

## Quiet capture and fail-closed evidence

After reviewed mocked gates and a prospective freeze, root must separately
release a quiet serial performance capture. The collector requires
`--released`. Use the inherited **40 GiB sampled process-group RSS ceiling**,
about two-second polling, bounded sampler request deadline, immediate stop on
sampler poison and stop after three consecutive unavailable observations.
Keep the inherited bounded TERM/KILL cleanup; no ceiling relaxation is allowed.
The frozen child loop has bounded polling and cleanup, but no per-child total
wall deadline. A later reviewed outer controller must declare and enforce a
truthful whole-capture deadline; do not label its budget as a child deadline.
RSS is sampled, not a continuous maximum.

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
exact 24-child schedule, all 1,008 raw rows and certificates, monitor telemetry,
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
| `paired_ratios` | 1,440 | 12 cases × 2 graphs × 6 repeats × 5 controls × 2 clocks |
| `comparisons` | 120 | 12 × 5 × 2 |
| `graph_comparisons` | 240 | 12 × 2 × 5 × 2 |
| `summary` | 144 | 12 × 6 solvers × 2 clocks |
| `graph_summary` | 288 | 12 × 2 × 6 × 2 |

For each family/control/size reconstruct all four graph/clock medians using
exact Fractions of integer timing endpoints. The median of six is the mean of
the two central ratios. Classify `strong_lead` iff all four≤9/10; `narrow_lead`
iff all four<1 but not strong; `loss` iff all four>1; otherwise `mixed_or_tied`.
Retain **60 point classifications** (2×5×6).

A strong observed crossover bracket requires an earlier `loss`, a later
`strong_lead` and `strong_lead` at **every larger measured size**. Preserve all
**150 earlier/later endpoint pairs** (2×5×15) and **10 family/control summaries**.
The representative bracket uses the earliest qualifying upper endpoint, then
the closest measured loss below it; all alternatives and earlier reversals
remain visible. An always-leading family has no observed loss-to-lead
crossover. A lead appearing only at 1M has no measured persistence beyond 1M.
No interpolation, monotonicity assumption, historical pooling, clock/drift
normalization or asymptotic dominance claim is permitted.

Retained-edge Borůvka is the primary filtering-overhead comparison, but a win
against it is not a win against Prim, Kruskal or original Borůvka. Publish all
ten family/control outcomes and both clocks, including losses and any reversal.
An independent raw audit must recompute the final ratios, summaries and exact
classifications without calling the collector's aggregation functions before
plots or conclusions are accepted.
