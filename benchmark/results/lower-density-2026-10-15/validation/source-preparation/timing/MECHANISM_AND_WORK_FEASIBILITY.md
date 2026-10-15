# Lower-density search: source reasoning and untimed companion feasibility

Source-only assessment during the Google performance hold. No new timings,
counter observations, native calls, imports, tests or artifact hashes were used.
This note proposes diagnostics; it does not authorize their execution.

## What lower density changes, and what it does not

The same eighth-policy binary already accepts both proposed families through
`benchmark/core_attachment_fixtures.hpp`. For block size four, q=n/4 is the core
vertex count. Exactly 3q cheap star edges precede all `(4d-3)q` core edges in
weight, with d=m/n. The simple-core domain is q>=8d-5. Thus the two minimum
power-of-two sizes are n512 at d16 and n256 at d8. Their core occupancies are
122/127 and 58/63. Both final endpoints have m=33,554,432, within the unchanged
n<=4,194,304 and m<=134,217,728 domain. Unique integer weights are exactly 1..m,
below the existing Prim/certificate sentinel. No native or memory-cap change is
needed; source legality alone does not prove observed memory fit.

Average core degree is 8d-6: 122 for d16 and 58 for d8, versus 250 for d32.
At fixed d, N=n+m=(d+1)n and average core degree are fixed proportionally, but
the fraction of possible core pairs present falls with n. Near-complete small
cores and sparse large cores are finite-size properties of this fixed family.
This experiment cannot separate those effects from cache behavior or overhead.

In `leaf_distance4`, every core edge is ranked by floor(log2(u xor v)), with
distinct random ranks inside each tier. The forced path connects every sibling
cut. The first full Boruvka step contracts the cheap stars. Thereafter every
dyadic sibling pair of full-graph components chooses its common minimum bridge:
all sibling edges have a lower tier than any exterior edge. The full retained
continuation therefore takes one star round plus log2(q) dyadic core rounds.
The KKT root uses the same first two steps, leaving exactly n/8 vertices and
(d-7/8)n records. This identity is for the ordered distance input, not its
shuffled twin or a sampled recursive subgraph. The implementation has no separate
small-n cutoff: after two nonempty steps it invokes its sampler.

One way to describe the expected retained volume without a CPU prediction is to
write M=(d-1)n+1 for the number of random nonpath core edges, and
P=(q-1)(q-2)/2 for the number of eligible nonpath pairs. Under ideal independent
uniform endpoint draws, the generator's rejection procedure yields a uniform
fixed-size set over those eligible pairs. A fixed finite MT seed instead defines
one deterministic set; it is not literally uniform over every possible subset.
After contraction into dyadic blocks of size b, the number of eligible internal
nonpath pairs is I_b=(q/b)*b*(b-1)/2-(q-q/b). Under that ideal endpoint model, the
expected number of crossing records retained is therefore

`q/b - 1 + M * (1 - I_b/P)`.

The path contributes q/b-1; parallel crossing records remain, and internal loops
are removed. Many records can consequently survive multiple full-graph dyadic
rounds. This source argument does not give the sampled recursion's round count,
the deduplicating continuation's work, or a timing advantage over all controls.

Under the ideal independent p=1/8 sampling lemma, the root's expected F-light
count is at most (n/8)/p=n. Relative to the ordered root input this upper bound
is 1/(d-7/8): 8/121 at d16 and 8/57 at d8. These are bounds, not predictions of
measured retention. The lemma assumes a correct sampled MSF and ideal Bernoulli
sampling; it does not assert sample connectivity, a random giant component or
formal independence of the seeded MT stream. Lower d makes this relative bound
less aggressive while reducing input work and admitting smaller legal n. A
small loss followed by a larger lead is plausible, but no crossover is assured.

The shuffled twin has identical topology, IDs, labels, tuple order, cheap leaves
and exact weight multiset; only core weight assignment changes. Distance here
means hierarchical ordering, not guaranteed triangle-inequality values or a
claim of natural application prevalence. The matched controls and all six
solvers must remain. Neither historical timing pooling nor an isolated causal
sampling-rate estimate belongs to this new single-binary study.

## Existing native diagnostic can be reused exactly

The already built executable is
`bin/eighth-sampling/native-correctness/eighth/retention_work` in the eighth
worktree. Its source is the unchanged
`benchmark/results/retention-control-2026-10-15/work/driver.cpp`.
The frontend accepts every attachment family via `benchmark_attachments::known`,
n<=2^22, d<=512, zero intrusion and m<=2^27. Both new ladders are supported;
the earlier spatial-family frontend repair is irrelevant here. Reuse the exact
instrumented binary, eight production objects and diagnostic main; no rebuild,
new main, source overlay or relink is necessary.

The established eighth-work `collect.py.check_freeze` reruns the full completed
eighth timing/native/readiness chain and all 43 instrumented compile/link
commands, eleven targets per variant, shared objects, source/recipe/compiler/SDK
bindings and typed half/eighth policies. A new work adapter can call that proof
unmodified, then select its `variants['eighth']` descriptor. Independently
strict-load the future completed lower-density timing capture with
`run_lower_density.load`, bind its full proof, and compare the reused diagnostic
source/toolchain/artifact identity with that timing parent. Do not override
parent globals or reuse the old 48-child schedule as the new matrix.

The unchanged `check_output`, `query_diagnostics`, `command`, `resources` and
guarded cleanup helpers are suitable for the new input identities. The new
adapter must supply its own 60-child completeness check and summary, rather
than calling the old paired-rate `complete` or `summarize` functions. All
60 new case/graph/sampler fingerprints must match the future timing rows;
the matched topology check must retain all 30 density/size/graph twins.

## Prospective whole-matrix outputs and gates

Run exactly one eighth-policy diagnostic child for each of the 30 fixed cases
and two graphs, using G23000003/G23000029 and S3407 in the timing order. One
child creates the graph, certifies an independent Kruskal MST, runs instrumented
KKT/deduplicating/retained continuations, and independently replays both
continuations outside WorkStats. That yields:

- 60 raw JSON records and 60 exact reference certificates;
- 180 solver rows, covering 11,700 declared counter cells, including 120
  deliberately null uninstrumented comparator hash-insert counts;
- 120 full comparator replay chains, plus all their rounds (round total is an
  observation, not a fixed count);
- 60 cumulative Q/U/engine-word rows and 30 topology twin checks.

Preserve all 65 fields, zeros and increases. Check connected n-1 MSF cardinality
and exact IDs, unsigned typed counters, unwound recursion, scan bounds, sampling
and verifier visit identities, complete shrinking replay chains, selected-edge
counts and their sums against instrumented helpers. KKT's first two contractions
must match retained replay; the ordered distance root dimensions above can be
an additional independently declared diagnostic identity. The shuffled root
must be checked against its own replay, not that distance formula.

For each solve, Q is cumulative verifier requests and U=path_query_visits-2Q is
the sum of unique requests within individual verifier-tree calls, with
0<=U<=Q. U/Q is undefined at Q=0. Scalar sampler engine words equal cumulative
sampling_edge_visits exactly. These counts are not global query uniqueness,
allocation bytes, CPU instructions or a cause decomposition. With one policy
and one sampler, there are no half/eighth field pairs, no repeated comparator
cross-rate equality gate, and no 61+4 same-recursion compression comparison.

Retain the existing 40 GiB sampled RSS rule, approximately two-second polling,
three-unavailable/poison stop, 1,800-second per-child native-exit deadline with
post-wait validation, guarded bounded cleanup and affirmative empty group before
the next child. Require exclusive attempts, complete frozen evidence, exact
timing joins and strict reload. A fresh truthful outer controller must separately
bound the complete 60-child run; its value is a prospective scheduling choice,
not a runtime estimate. An independent raw counter audit should reconstruct all
four exports (`work`, `rounds`, `round_chains`, `query_work`) before mechanism
claims. No partial timing or favorable cases select diagnostics.

Qualitatively this is substantial untimed work, not a cheap CSV postprocess:
every input includes generation, reference sorting/certification, three solver
calls and two full replays. It has fewer solver invocations per input than the
42-output timing harness but adds instrumentation and replay costs, so timing
duration cannot be inferred by multiplying a call-count ratio. Large cases
will dominate the work. Keep it separate from performance; use actual monitored
completion, not a promised finish time.
