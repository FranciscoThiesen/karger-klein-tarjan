# Focused work and component diagnostics

Declared while the precision timing campaign is still active, before its
analysis and before these diagnostic captures. No native diagnostic, export,
build, test or plotting job runs concurrently with a timed campaign. This
plan adds mechanism observations; it neither selects confirmation candidates
nor changes the [timing protocol](PROTOCOL.md).

## Fixed selection

Use exactly the ten rows of [diagnostics.csv](diagnostics.csv), graph seed
3037 and KKT sampling seed 101. All cases have `m=16n` and zero intrusion.
Reuse the already screened inputs by regeneration and verify their exact
weighted and topology fingerprints against the timing captures. No held-out
graph or sampling seed is consumed.

| Family | Vertices | Edges | Purpose |
|---|---:|---:|---|
| `line_metric` | 1,048,576 | 16,777,216 | Original finite-gap spatial line |
| `line_wide_metric` | 1,048,576 | 16,777,216 | Matched topology with wider random gaps |
| `line_random` | 1,048,576 | 16,777,216 | Same line topology with globally random ranks |
| `grid2d_metric` | 1,048,576 | 16,777,216 | Variable local MST in jittered grid plus shortcuts |
| `grid2d_random` | 1,048,576 | 16,777,216 | Same grid topology and geometry, random ranks |
| `gnm_random` | 1,048,576 | 16,777,216 | Connected uniform-pair control without a scaffold |
| `hierarchical_path` | 1,048,576 | 16,777,216 | Known dyadic merge schedule as a structural anchor |
| `line_metric` | 8,388,608 | 134,217,728 | Largest screened original line, including its unfavorable observation |
| `line_wide_metric` | 8,388,608 | 134,217,728 | Largest screened precision ablation, regardless of its timing result |
| `hierarchical_path` | 4,194,304 | 67,108,864 | Largest screened hierarchy within its existing size domain |

The first seven rows compare mechanisms at a common size and density. The
line metric/random pair and grid metric/random pair preserve their respective
topology, labels, IDs, geometry and input order. The wide line preserves the
line topology, labels, IDs and input order but changes coordinates and ranks.
G(n,m) and the hierarchy are different graph constructions, not paired
reweightings of the spatial fixtures.

The three larger rows test whether the mechanisms persist at the largest
relevant screened sizes. Selection is based on these structural questions and
the declared size menu, not on dropping unfavorable timing observations.
Both the original narrow-line captures and the wide-gap ablation remain.

This does **not** diagnose every screen row. The 262K cases, the intermediate
2M line, 4M spatial/random cases, 8M G(n,m), and random-tree/density-four
controls retain their timing results but are outside this bounded diagnostic
budget. Observations at 1M and 8M cannot establish an intermediate transition
size or tell which unobserved round changed at 2M or 4M. The hierarchy is
compared at 1M and 4M, not extrapolated to 8M.

## Captures and validation

Run the existing [capture runner](../../run_crossover.py) serially, after all
timing has stopped, with the fixed manifest and seeds:

1. `--mode work`, using the separately instrumented
   `bin/continuation_search_work`, to `diagnostics_work.csv`.
2. `--mode trace`, using the uninstrumented `bin/continuation_search`, to
   `diagnostics_trace.csv`. This also emits `component_moments_v1` records
   in the adjacent log.

Use the existing accepted `--repetitions 2 --warmups 1` options for command
consistency; neither diagnostic mode executes the timing repetition/warmup
loops. Work mode runs KKT once and deterministic compaction once per case.
Trace mode runs compaction once per case and records every round. Thus expect
20 work rows and ten complete variable-length traces, not repeated timing
samples. The vertex-halving bound permits at most 208 trace rows across this
manifest; that is a validation upper bound, not an expected observed count.

Keep the existing independent reference-MST certificate and exact solver ID
checks on every regenerated graph. Do not skip certificates because an input
was certified during an earlier timing campaign. Each mode currently owns its
own generation/reference/certificate lifetime: this plan therefore performs
**20 setup/certificate executions**, instead of 54 for both modes over all
27 screen cases. No solver, timing boundary or captured fixture code changes
are needed to obtain this reduction.

Retain complete raw CSVs/logs/metadata and all failed or interrupted captures.
Record the actual binary/source/profile hashes rather than treating the
instrumented and native binaries as interchangeable. Validate full case/seed
coverage, exact fingerprints, certified outputs, round chaining, selected-edge
totals and terminal state. The component ledger must independently reconstruct
the original-vertex partition from selected original IDs. Cross-check trace
contraction input volume against the compactor's work counter and its first
two residual sizes against KKT's root-after-two counters. A discrepancy is a
validation failure, not an observation to omit.

Use the unchanged resource rule: one native process at a time, roughly 40 GiB
process-footprint ceiling and no sustained swap. If it is exceeded, stop and
retain the incomplete evidence. No resource failure is silently replaced with
a smaller case. These captures' wall times are operational diagnostics only,
never new solver-performance observations.

## Quantities to explain

For compaction, retain every round's input/output vertex and edge counts,
selected-edge counts and the independently checked ledger's component moments,
and report `V/m`, where
`V=sum_r m_r` sums **input** edge counts. Round count alone is insufficient:
many rounds on a rapidly shrinking sparse graph can still have small `V/m`.

For each partition report the component count `q`,
`q_eff=n²/sum_i size_i²`, largest original-component fraction, and residual
`m_r/m`. Add `q/q_eff` or the second moment alongside the largest fraction to
distinguish balanced contractions from concentration in a few large components.
At termination, the original partition has one component even when the
production quotient represents completion with zero vertices. State whether
an edge count describes the input or output of the associated round.

For KKT report contraction input volume, recursive input volume, sampling and
verifier edge volumes, retained F-light incidences, edge materializations and
the root's residual after two contractions. Any light/heavy fraction aggregated
across recursive verifier calls is a fraction of those **edge incidences**,
not the fraction of distinct original edges removed at the root. The existing
work proxy is not a measurement of bytes transferred, allocator cost, cache
misses or hash probes; a smaller work count need not imply a runtime win.

The narrow/wide comparison can test whether their actual merge schedules,
component concentration and retained-edge volumes differ at these sizes.
The finite-alphabet proof does not by itself explain a measured plateau. The
wide-gap model changes the relative gap ordering as well as tie frequency,
so this is not an isolated intervention on the tie-breaking rule. Both metric
line MSTs are forced paths. The grid MST varies, but the metric grid still has
an overwhelmingly heavy global shortcut background. Preserve these model
limitations when connecting traces to the [mechanism note](MECHANISM.md).

One graph and one sampling seed support case-specific explanations, not
population means, confidence intervals, a theorem about all larger inputs,
or proof that sampling alone caused a speedup. The repeated-compaction
comparison combines sampling, verification and a different recursion schedule;
its counters describe that whole implementation. A crossover against this
baseline is separate from the predeclared [classical adjunct](CLASSICAL_PLAN.md).

## Cost estimate from completed captures

These are scheduling estimates, not additional benchmarks. The existing logs
separate generation from reference construction/certification; both costs are
outside solver timing. Rounded observed values are:

| Already captured fixture | Generation (s) | Reference plus certificate (s) | Total setup per mode (s) |
|---|---:|---:|---:|
| Narrow metric line, 1M | 4.8 | 11.0 | 15.8 |
| Random line, 1M | 3.2 | 7.6 | 10.8 |
| Metric grid, 1M | 4.7 | 10.0 | 14.7 |
| Random grid, 1M | 3.3 | 8.0 | 11.3 |
| G(n,m), 1M | 3.3 | 7.6 | 10.8 |
| Hierarchy, 1M | 3.4 | 10.8 | 14.1 |
| Narrow metric line, 4M | 21.6 | 56.1 | 77.7 |
| Narrow metric line, 8M | 46.0 | 152.7 | 198.7 |

Sources: [discovery setup log](discovery_timing.log) and
[extension setup log](extension_timing.log). The six observed 1M selections
sum to about 77.5 seconds of setup per mode. Provisionally allow 16–25 seconds
for wide-line 1M setup, 200–300 seconds for wide-line 8M, and 60–100 seconds
for hierarchy 4M. These three allowances are extrapolations from completed
captures; they deliberately do not consume the still-running precision
campaign's partial timings.

That gives approximately 18–24 minutes of setup across both diagnostic modes.
Existing 1M solver calls take roughly 4–6 seconds; the narrow 8M calls span
roughly 50–64 seconds. Twenty instrumented solver calls plus ten native trace
calls and ledger reconstruction add meaningful cost. Reserve **about 35–50
minutes total**, with no guaranteed completion deadline: instrumented overhead,
memory pressure and desktop conditions can change this estimate. The completed
8M extension recorded about 24.0 GiB maximum RSS; the trace's additional ID
mapping and selected-ID storage still require resource observation rather than
assuming identical peak memory.

Running all 27 cases in both modes would repeat many expensive certificates
without answering a distinct planned mechanism question. Sharing a cached
reference across the two modes could save setup, but would require a new
capture implementation and new validation; it is not part of this plan.

## Small graph illustrations

After timed activity ends, run
[build_crossover_graph_views.py](../../build_crossover_graph_views.py) to
export and certify actual `n=128,d=4` line/grid fixtures and their first two
production contractions, then inspect the resulting PNG/SVG. Its C++ exporter
is compiled in a temporary directory outside the repository. Full original
tuples, coordinates, label maps, MST IDs, selected-ID ledgers and residual
representatives are retained and checked. These educational examples explain
geometry and component definitions; they are not substitutes for the large
diagnostic inputs or evidence of a large-instance timing mechanism.
