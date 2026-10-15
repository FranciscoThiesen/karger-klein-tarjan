# KKT multigraph contraction: preregistered exploratory screen

This experiment follows the attachment crossover study at `206ff84`. It tests
one implementation change: retain every crossing edge in KKT's two internal
Boruvka contractions instead of building a simple quotient. The public
`boruvka_step` and all four comparison solvers remain unchanged. The candidate
is opt-in through `KKT_EXPERIMENT_RETAIN_PARALLEL`; the default build is the
reference. This is a multigraph variant of KKT, since the published algorithm
explicitly removes parallel quotient edges.

## Hypothesis and limits

The old step allocates and initializes bucket links proportional to the input
edge count, then traverses crossing edges again to deduplicate. The candidate
removes those arrays and that traversal. It counts crossing edges in the
existing degree pass and reserves exactly that many output records. On the
first contraction of ordered four-vertex leaf attachments, no parallel pairs
exist: deduplication cannot reduce that quotient. Later contractions and
other families can produce many parallel edges; retaining them may increase
sampling, recursion, copying, and verifier work substantially.

The candidate emits crossing records in original input order, whereas the
reference uses bucket order. A shared starting sampling seed therefore does
not imply identical sampled subsets or recursion trees. This screen measures
the entire candidate, not a pure isolated allocation effect. Work counters,
if collected, describe a separate instrumented correctness run and do not
change the timing build.
After timing has ended, run the untimed `multigraph_work.cpp` companion for
both variants on all ten cases at graph seed 2000003 and KKT seed 607. Match
input fingerprints against the measured inputs and require identical
compactor work counts across builds. These counters count specified source
operations, not instructions, bytes, elapsed time, or distinct original edges.

The ideal independent-coin sampling argument extends to parallel records:
accepted edges still form a forest, and expected F-light edges remain bounded
by `(n-1)/p` for a connected graph. This is an inference from the original
proof, not a claim that the published contraction is unchanged or that a
finite-state PRNG supplies mathematically independent randomness. No finite
timing fit proves asymptotic complexity.
The reference for the contraction and sampling proof is
[Karger, Klein and Tarjan, sections 2–4](https://people.csail.mit.edu/karger/Papers/mst.pdf).

## Cases, schedule, and stopping rule

`manifest.csv` is the complete ten-case screen. It includes small and large
ordered leaf attachments, weight-shuffled and random-weight attachment
controls, lifted graphs with many parallel quotient edges, and sparse/dense
connected G(n,m) graphs. All input graphs are simple, all have `m=n*d`, and
all weights and edge IDs satisfy the existing checked native harness contract.
No generator, weight rule, validation gate, or timed solver boundary changes.

Graph seeds are **2000003 and 2000029**; KKT starts each call at seed **607**.
Each native child runs all five solvers with one checked warmup and five
timed repetitions. The existing harness balances the five algorithm positions.
For the first graph seed, visit manifest order and run `reference` then
`multigraph` adjacently on each input. For the second seed, reverse both case
order and variant order. Thus the complete screen is **40 native children,
1,200 checked solver outputs, 1,000 timed and 200 warmup**.

Native children run serially. Other agent builds, tests, plots and local
analysis stop before release. The collector uses bounded libproc RSS sampling
of only each owned process group, normally every two seconds; stop above a
sampled 40 GiB or after three consecutive unavailable samples. A timed-out
sampler is permanently poisoned and cannot advance to another child. Cleanup
and waiting are bounded; an unknown native exit stops the capture. Sampled
RSS is not a continuous maximum. Partial failures remain failed, retain all
raw artifacts, and are not silently resumed or pooled as complete captures.

`caffeinate` failed to create a sleep-prevention assertion before this screen.
The separate recorded attempt and `pmset -g assertions` show no active
assertion. Do not describe this run as sleep-inhibited. Retain UTC, steady
clock, process CPU, flags and a post-run power-event correlation. Never
remove, adjust, or replace observations because they are slow or flagged.

## Correctness and provenance gates before release

An independent oracle checks the multigraph quotient, while the existing
simple-quotient oracle stays unchanged. Full KKT must agree with independent
minimum spanning forest results on raw parallel inputs and contraction-created
parallel edges, disconnected graphs, isolates, empty/singleton inputs,
reversed/shuffled edge order, signed/sparse/extreme IDs, and multiple seeds.
Run native and ASan/UBSan checks and check the candidate contraction's at-most
three input-edge scans with instrumentation. The production certificate's
simple-input requirement stays intact.

Both binaries are built from the same final source inventory with native
Apple Clang, identical optimization/assertion settings and the same 512 MiB
main stack. Only the candidate macro and isolated build/output directories
differ. Preserve compiler identity, exact commands, logs, Makefile/source
hashes, binary hashes and Mach-O profile. The default compacting implementation
must remain source-identical. Source identity alone is not an assertion that
the linker emits identical machine addresses or that hardware placement is
controlled.

The runner's negative/mock tests, source, this protocol, manifest, build
records and hash-bound freeze are committed before root releases native
timing. Capture must recheck frozen inputs before each child, independently
validate each emitted result/certificate, and preserve raw CSV, logs, RSS,
commands, hashes and any partial failure. Reanalysis must reread raw files
and verify provenance rather than trusting summary columns.

## Analysis and decision rule

For each case, seed and repetition, compute candidate/reference KKT time for
both steady elapsed and process CPU clocks. Report the median of all ten
paired timed ratios and each five-repetition graph-seed median. Also report
KKT versus each of compacting Boruvka, Kruskal, Prim and original Boruvka
within each variant, every control, dispersion and clock/power flags.

The candidate earns a fresh-seed follow-up only if **both large ordered
attachment cases have at least 5% lower median paired time on both clocks,
and every graph-seed median improves**. Two seeds are an exploratory screen,
not a robust confirmation or an independently established universal speedup.
Retain all dense/bundled regressions. Do not promote a global implementation
change if controls have material regressions; a family-specific experiment
does not justify an input-specific shortcut or weakened baseline. A failure
of this gate is useful negative evidence and will be reported as such.

The original goal remains a clear, reproducible crossover. A reduction versus
the old KKT is distinct from winning against compacting Boruvka, and winning
against that comparator is distinct from beating all classical solvers.
Publish the complete matrix and bounded claims in Markdown with static
scientific plots. Keep this screen separate from the historical confirmation
data and the literature; unpublished measurements are not Wikipedia sources.
