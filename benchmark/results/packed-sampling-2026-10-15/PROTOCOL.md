# Private packed-sampling prospective experiment

## Question and fixed comparison

Can consuming all 32 bits of each `mt19937` word reduce KKT's constants while
preserving its randomized sampling policy? This experiment compares a freshly
built callback-refactored scalar reference with Candidate A, which consumes bits
in increasing position, emits edges in their original order, and discards the
unused suffix at each sample-call boundary. The same engine continues through
recursion. Empty samples consume no word. Public `sample_edges<false>` retains
its one-draw-per-edge stream; only private recursive sampling opts in.

The scalar and packed private seeded subsets, recursive paths and work counters
will differ. For ideal uniform independent 32-bit words, these are both unbiased
independent Bernoulli half samples; this statement does not assert literal
independence or identical subset distributions over finite deterministic
`mt19937` seeds. Matching seed numbers pair reproducible initial engines, not
identical sampled subgraphs. No speedup is assumed from the reduced number of
engine calls. Candidate B set-bit iteration and vector-reservation changes are
excluded. Identical 65-field recursive work counters are not a correctness gate.

Both binaries have identical source inventories, retained-parallel contraction,
direct-Edge verifier queries, flags and seven physically shared non-KKT objects
plus one shared six-solver harness object. Only `kkt.o` adds
`KKT_EXPERIMENT_PACKED_SAMPLING`. The fresh scalar includes the same callback
refactor. The new builder records exact compiler/link argv, source/recipe hashes,
object paths/hashes, native arm64 profile and 512 MiB stack. The original Edge
freeze SHA256 is
`f976a7d61650f5aaf8e7221c7684461e36bcb51492347f45a56497b6b1cee306`;
its full native/build/helper proof is checked in its original worktree. Copied
runtime helpers are bound by unique basename and hash to that parent, with only
the historical helper path mapping temporarily scoped and always restored.
Only `kkt/kkt.cpp` changes from parent production sources; the added packed
header and two tests are declared explicitly. Frozen parent files are untouched.
Historical observations are never pooled or used as this study's reference.

## Fixed inputs and counterbalancing

Use exactly six cases in `manifest.csv`: `leaf_hierarchy4` and `leaf_shuffled4`
each at n=65,536 and 1,048,576 with density m/n=32; `gnm_random` at n=4,096 and
1,048,576 with m/n=16. Intrusion is zero. No cases or observations will be added
in response to the results. Hierarchy/shuffled twins share topology, labels,
IDs and physical edge order; only core weight ranks differ. Both retain cheap
leaf attachments, so shuffled does not mean globally random weights. Require
equal topology fingerprints and unequal weighted fingerprints for every twin.
Require identical graph fingerprints across all sampling seeds and variants.

Graph seeds are **7000003, 7000017**, sampling seeds **1601, 1613**. Iterate graph
seed, sampling seed, manifest cases, adjacent scalar/packed children. Reverse
case order for the second graph seed. Use scalar then packed when the sum of
graph-seed index and sampling-seed index is even; otherwise packed then scalar.
Thus each variant goes first twice per case. Variant order remains confounded
with the graph-by-sampler combination, and case-order reversal with graph seed;
this is counterbalancing, not randomization or a causal elimination of host drift.

Each child runs one checked warmup and six timed repetitions. Solver rotation
places each solver once in each timed position. All six are mandatory: KKT,
deduplicating compacting Boruvka, retained-edge multigraph Boruvka, Kruskal,
Prim and original Boruvka. This is **48 children, 2,016 checked outputs,
1,728 timed calls and 288 warmups**. Six repetitions time the same graph and
sampling realization. The four crossed graph/sampling realizations per case
share two graphs; they are not four independent graph draws or 24 independent
sampling draws. Unchanged deterministic controls are retained under both seeds
to expose drift.

## Correctness, capture and release gates

Before freeze: independent scripted-word mapping and boundary tests, public
stream regression tests, actual private-dispatch witnesses, exact MST edge-ID
comparison against the independent certificate, native and sanitizer gates,
and linked final-object correctness. Samples and work may differ while exact
MST certificates must agree. The collector's complete mocked matrix and negative
provenance/identity/resource tests must pass independent review. Root then
freezes and commits the separate source/protocol/build proof before explicitly
releasing native capture. `--released` is mandatory. No competing local builds,
tests, plots or counters run during timing.

Retain every command, raw CSV, stderr certificate, RSS sample, clock endpoint,
wrapper status and post-exit empty-owned-group observation. Reuse the unchanged
bounded monitor: 40 GiB sampled owned-group RSS ceiling, roughly two-second
polling, stop after three consecutive unavailable observations, and stop
immediately on sampler poison. Unknown group exit forbids another launch;
bounded termination and all partial evidence are retained. Sampled process-group
RSS is neither a continuous peak nor KKT-only memory. No raw overwrite/recovery
or successful sleep-inhibition claim is permitted. Archive and correlate a power
log after capture; Wake Requests are not wake transitions. No absent logged
overlap proves a quiet or awake host.

Strict reanalysis rereads hashes, source/build/helper proof, schedule, algorithms,
seeds, all 42 rows per child, independent certificate, fingerprints, raw/combined
CSV equality, bounded monitoring and final empty-group evidence. Preserve all
clock flags and losses; do not trim, replace, normalize or adjust timings.

## Prespecified summaries and interpretation

For wall and process CPU clocks separately, pair packed/scalar durations of all
six solvers by case, graph, sampling seed and repetition: **1,728 clock pairs**.
Within each binary compare KKT with all five competitors: **2,880 clock pairs**.
Case medians pool all **24 paired ratios**, not medians of medians. Retain all
individual ratios, all four six-trial realization medians and ranges, both
12-trial graph marginals and both 12-trial sampling marginals. Absolute durations
receive the same summaries, with medians computed from durations directly.
Unchanged-control drift accompanies the KKT gain; it never normalizes KKT.

A strong observed crossover requires the same variant, family, density and
competitor: all four realization medians are above one at the small endpoint,
and at most **0.90** at the large endpoint, on **both clocks**. A strong lead at
both endpoints is not a crossover. A narrow lead, a mixed result, or losing at
both endpoints stays visible. Report only tested endpoint brackets; no exact
threshold is interpolated. These selected endpoints are exploratory and cannot
establish durable/asymptotic dominance or empirical O(n). Any promising lead
requires a separate held-out/intermediate-size declaration. This screen alone
cannot justify a Wikipedia classification or production promotion.

Plots will preserve all cases, all competitors, both clocks, pooled medians,
four realization medians and full individual-trial ranges with matched clock
axes. Graph and sampling marginal tables remain available for sensitivity checks.
