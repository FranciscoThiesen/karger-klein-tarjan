# Fresh-seed crossover study with a shared-contraction Boruvka control

## Prospective design and relationship to the discovery screen

The complete ten-case multigraph screen passed its declared gate: candidate KKT
improved every case and all 100 paired trials on both clocks. At 1,048,576
vertices, both ordered leaf-attachment cases took about 48% of reference KKT
and 40% of deduplicating compacting Boruvka time. Kruskal remained faster on
every screen case median. All discovery losses remain published separately.

Those results motivated these selected families and sizes. A five-solver paired
follow-up adapter was prepared and mock-tested, but **never frozen or run**.
Before any follow-up timing, that plan was superseded by this six-solver study:
give repeated Boruvka the exact same retained-parallel contraction as candidate
KKT. This controls for the shared kernel improvement and tests whether sampling
adds an advantage. It does not weaken or replace the existing four comparators.
There is no reference-KKT timing in this study; that comparison is in the
completed discovery screen and must not be pooled with this new study.

## Solvers, sources and correctness

Every input compares `kkt`, `compacting_boruvka`, `multigraph_boruvka`, `kruskal`,
`prim` and original `boruvka`. Candidate KKT retains parallel quotient records
in input order. The new multigraph Boruvka repeats that same contraction until
empty. Its continuation changes only the step call relative to the existing
deduplicating compactor. All eight production object files, including KKT, are
byte-identical to the screen candidate. The new native driver, helper, gate and
make fragment are declared additions; all parent native sources stay unchanged.

Use native arm64 Apple Clang 15, C++17, `-O3 -Wall -Wextra -march=native`,
assertions enabled, candidate macro enabled, no work counters and a 512 MiB
main stack. Freeze source, build, binary, protocol, manifest and runtime-helper
hashes and commit the study before releasing native timing. Independent review
must confirm the shared timing boundaries and six-position balance.

All three ID-returning solvers include tuple-to-problem conversion and temporary
input destruction in the timed interval; returned-result destruction and result
validation are outside. Existing tuple-returning solvers keep their API and
boundaries. Graph generation and the independent reference MST/cycle certificate
are outside timing. Every solver output, including warmups, must pass the same
exact-weight, membership, cardinality and acyclicity checks. The independent
native gate also covers raw multigraphs, sparse IDs, unique signed weights and extremes,
exhaustive tiny optima, corrupted results and invalid repetitions. Native and
ASan/UBSan/leak gates must pass before timing.

## Frozen cases and serial schedule

The ten cases and order are in `manifest.csv`. Graph seeds are **3000001 and
3000029**, with starting KKT seed **809**. The second graph seed reverses case
order. One binary runs all six solvers on each input, with **six timed repetitions
and one checked warmup per solver**. Cyclic solver order places every solver
once in every position. This gives **20 children, 840 checked outputs, 720 timed
and 120 warmup**. The largest inputs contain 33,554,432 edges. No threshold,
family shortcut or solver-specific input is introduced.

Only one native performance child may run at a time. No competing local builds,
plots, correctness suites or work diagnostics run during capture. The collector
must validate the complete expected schedule and retain every raw CSV, stderr,
command, wall/CPU timestamp and result certificate. Case order reversal is
confounded with graph seed; balanced positions do not eliminate host drift.

## Resources, clocks and retained failures

Use bounded owned-process-group RSS sampling every two seconds, a 40 GiB sampled
stop, and stop after three unavailable samples or any poisoned sampler. After
normal wrapper exit, require a bounded verified empty-group observation before
advancing. Cleanup must be bounded. Partial failures remain incomplete and must
not be silently resumed or relabeled as complete. Reanalysis rereads raw evidence,
checks hashes, source/build identity, schedule, certificates, RSS and clocks.

Both ordinary and explicit-native `caffeinate` attempts failed. No verified
sleep-inhibition assertion exists. Retain every slow sample and clock flag;
correlate an archived machine power log after capture. Publish only scoped audit
summaries, not unrelated full machine history. Never trim, normalize, correct or
replace timings. No absence of logged sleep proves stable frequency, thermals,
memory residency or an otherwise quiet host. Periodic process-group RSS is not
a continuous peak or a KKT-only memory measurement.

## Declared analysis and crossover rule

For every case and all five comparators, compute KKT/comparator ratios paired
by graph and repetition, separately for steady elapsed and process CPU clocks.
The primary case summary is the median of all twelve paired trial ratios;
retain each graph's six-trial median and all individual pairs and ranges. The
screen used a different declared competitor summary and remains separate.

A **strong observed crossover bracket** requires a measured smaller point where
**each graph median exceeds 1 on both clocks**, followed by a larger point where
**each graph median is at most 0.90 on both clocks**, with every still-larger
tested point also satisfying that win rule. Compare sizes only within the same
family and density. Report measured bracket endpoints, never an interpolated
threshold. Wins at both endpoints indicate a lead over the measured range,
not an observed crossover. Mixed cases stay inconclusive. Report all five
comparators even when KKT loses; the stronger multigraph Boruvka is central.

Two fresh graph seeds and one fresh sampling seed give limited replication,
not confidence intervals or universal guarantees. Selected follow-up families
are not evidence of broad dominance. This study does not run Google Benchmark
complexity fitting or prove linear wall time. It tests finite practical behavior.
The production default remains unchanged, and these unpublished results are
not independent evidence for a Wikipedia classification.
