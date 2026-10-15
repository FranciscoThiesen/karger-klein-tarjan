# Fresh-seed crossover follow-up — superseded before execution

**Status: prepared and mock-tested, but never frozen or timed.** Before any
follow-up timing, this plan was replaced by the six-solver
[shared-contraction control study](../retention-control-2026-10-15/PROTOCOL.md).
The text below preserves the unexecuted design; it is not measured evidence.

The complete exploratory screen passed its declared gate before this follow-up
was designed: both ordered attachment cases at 1,048,576 vertices reduced KKT
time by about 52%, on both clocks and both graph seeds. Every screen case
improved over reference KKT. The candidate took about 40% of compacting
Boruvka's time on the large ordered cases, while the 65,536-vertex versions
still lost on each graph median. G(n,m) also showed substantial leads over
compacting Boruvka. These observations motivate this selected follow-up; they
are discovery evidence, not independent confirmation of a subsequently chosen
claim. All screen cases and every classical-solver loss remain published.

## Frozen inputs and schedule

Use the exact same two native binaries, source inventory, build records,
optimization flags, assertion settings, stack, native solver harness and
certificate as the screen. The only changed experimental inputs are the ten
cases in `followup-manifest.csv`, graph seeds **3000001 and 3000029**, and
starting KKT seed **809**. There is no production-code change between studies.
No threshold or input-family shortcut is added to either algorithm.

The manifest expands the ordered hierarchy/distance attachment families to
2,097,152 vertices and 33,554,432 edges, repeats the small losing point on fresh
inputs, and measures an intermediate size. The four G(n,m) cases test the
ordinary connected random graph model at fixed density 16 or 128, with a
small and large point for each. These are selected families, not a replacement
for the original diverse screen or proof of broad superiority.

As before, run reference then multigraph adjacently in manifest order for the
first graph seed; reverse both case order and variant order for the second.
Each child runs all five solvers, one checked warmup and five timed repetitions
with balanced native algorithm positions: **40 children, 1,200 checked outputs,
1,000 timed and 200 warmup**. Pair variant results by input and repetition.
Identical starting seeds do not imply identical internal sampling trajectories.

The new adapter must leave the original screen runner byte-for-byte unchanged.
Its freeze includes the adapter itself and all original runtime helpers. Restore
module configuration after adapter calls so importing it cannot silently change
original screen analysis. Run its complete mocked schedule and failure/drift
tests; commit the adapter, this declaration and the follow-up freeze before
releasing serial native timing. Both studies remain independently reanalyzable.

## Resource, correctness and retention rules

All original [screen protocol](PROTOCOL.md) correctness, clock, input matching,
resource and retention rules apply. In particular: serial native children;
no competing local builds/plots/work counters; bounded owned-group libproc RSS
sampling every two seconds; 40 GiB sampled stop; three unavailable samples
or a poisoned sampler stop; and a bounded empty-group observation after every
normal wrapper exit. No unverified exit may advance. Retain partial failures
without relabeling them complete or silently resuming.

The explicit arm64 retry of `caffeinate` also failed after the screen. There is
still no verified sleep-prevention assertion. Keep every sample and every
clock flag, and correlate a newly archived power log after native timing ends.
Never trim, correct or replace a slow observation. No absence of logged sleep
proves stable frequency, thermal state, memory residency or an otherwise quiet
host. Work diagnostics run separately after timing; they are not measurements
of instructions or elapsed time.

## What would count as a crossover

Report KKT versus every comparator, on both steady elapsed and process CPU
clocks, for both variants. A **strong observed crossover bracket** for a family
and comparator requires a measured smaller point where **each graph-seed
median ratio exceeds 1 on both clocks**, and a measured larger point where
**each graph-seed median ratio is at most 0.90 on both clocks**, with every
still-larger tested point also meeting that winning condition. Ratios are
paired by repetition within each input. Report the bracket endpoints; do not
interpolate an exact threshold across unmeasured sizes. A win at both points
is a measured lead, not an observed crossover. Inconclusive or mixed cases
stay inconclusive, and no comparator is omitted for being faster.

Candidate/reference implementation summaries retain the median of all ten
paired timed ratios plus each graph's median, as in the screen. Existing
within-variant comparator summaries retain their declared median-of-graph-
medians statistic; trial pairs and graph ranges remain available. The bracket
criterion uses each graph median directly and cannot be rescued by pooling
seeds or clocks. Two fresh graph seeds and one fresh sampling seed are a
limited replication, not a confidence interval or a universal guarantee.

Even a strong observed crossover proves neither asymptotic dominance nor a
future wall-time threshold. Default KKT remains unchanged during this branch's
experiments; promotion requires broader evidence than these selected families.
This is a multigraph variant of published KKT, and unpublished results are not
Wikipedia evidence.
