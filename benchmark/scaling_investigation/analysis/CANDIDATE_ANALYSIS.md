# Depth-query candidate analysis

The eight arithmetic groups, completed work capture, primary paired timing,
paired phases and six-input query-method control have passed strict analysis.
Allocation and the three-policy phase comparison are optional and have not run.
This code launches no native process. It reuses the candidate runner's full
build, original-source snapshot, prerequisites, raw schema, exact input,
resource and owned-exit checks. Arithmetic below is independently implemented.

```sh
/usr/bin/python3 -B benchmark/scaling_investigation/analysis/analyze_candidate.py \
  --work benchmark/results/scaling-investigation-2026-10-15/depth-work01/capture.json \
  --timing /absolute/path/to/completed/timing/capture.json \
  --output /absolute/path/to/new-analysis-directory
```

Every mode is optional, but at least one completed capture is required. Add
`--phase`, `--allocation`, `--inline-control` or `--inline-phase` for those
separately completed captures. Modes supplied together must use one build record.
Failed and partial captures are rejected, not trimmed. Each fresh output is
exclusive, with source, raw input and output digests and a final drift check.

The main timing matrix is 36 distinct inputs, one sampler seed (3001), two graphs,
six sizes and three families. One warmup and three timed calls in each of two
variants produce 288 raw rows and 108 paired observations per clock. Wall and
process CPU remain separate. Per-graph medians, pooled six-ratio case medians,
full ranges, every win/loss/tie and ratios of separately computed medians are
retained. This is fresh paired timing, with no historical timing pooling.

The inlining control has six inputs (G1/S3001 only) and three policies whose
process launch positions rotate across those cases. Each process runs one
warmup and three timed calls internally. It exports depth/reference, noinline/reference and
noinline/depth comparisons, retaining all 72 raw rows. The one-graph pooled
tables are explicitly marked as such; they are not additional graph samples.

`timing-fits.csv` applies the zero-intercept Google least-squares coefficient and
normalized-RMS formula to N and NlogN, separately by policy, family, graph and
clock. It includes both 18 individual native timed calls and six size means.
Balanced repetitions give the same coefficient; residual RMS differs because
within-size noise is retained only in the all-call objective. This is numerical
reanalysis of six sizes, not Google Benchmark's emitted BigO result and not
evidence of asymptotic order. All 1,152 fitted point/residual records remain.

Work compares all 72 candidate inputs against the preserved exact baseline.
All 65 counters are retained: only initialized_slots may change, and its saving
must equal the old lca_vertices. Both-zero ratios are undefined rather than
reported as zero or one. Phase deltas use untrimmed arithmetic means and include
outside-collector time so all exclusive differences sum exactly. Per-phase
ratios with a zero denominator remain explicit. Allocation labels separate
cumulative requested/usable bytes from peak/returned live usable bytes; none is
RSS or live requested bytes. Work, phase and allocation clocks are diagnostic,
not uninstrumented performance results.

Focused arithmetic gates:

```sh
cd benchmark/scaling_investigation/analysis
/usr/bin/python3 -B -m unittest -v test_analyze_candidate.py
```

These eight groups independently enumerate timing ratios across both clocks,
check all three control directions, reject missing/duplicated or mismatched raw
identities, verify a known linear fit, preserve 4,680 counter comparisons and
zeros, check exact phase additivity and allocation scope, and distinguish paired
medians from ratios of medians. Their completed execution is recorded below.

## Completed work gate and compact plots

The eight analysis groups passed in 0.191 s (actual exit 0, owned test group
observed empty). The first completed work analysis is
[depth-work-analysis-attempt01](depth-work-analysis-attempt01/): all 72 inputs,
144 raw rows and 4,680 counter comparisons pass. Exactly 4,608 fields are equal;
72 initialized-slot values decrease by precisely the corresponding old
`lca_vertices`. All 204 both-zero ratios are retained. These are work diagnostics,
not timing results. See the exclusive receipts under `validation/candidate-*`.

`plot_candidate.py` accepts completed timing only. It reuses strict raw
proof, independently recomputes the plotted canonical tables and rejects any
CSV discrepancy. It requires an exact work/timing identity join, including both
graph fingerprints, and keeps one sampler (3001) for the central comparison.

```sh
/usr/bin/python3 -B benchmark/scaling_investigation/analysis/plot_candidate.py \
  --work-analysis benchmark/scaling_investigation/analysis/depth-work-analysis-attempt01 \
  --timing-analysis /absolute/path/to/completed/candidate-analysis \
  --inline-analysis /absolute/path/to/completed/inline-analysis \
  --output /absolute/path/to/new-figure-directory
```

The two central three-family figures separate wall and process CPU clocks. Both
reference/depth time curves divide time/N by the **same reference 1K time/N for
that graph**. Logical `kkt_edges/N` divides by its own 1K count/N. The two
normalizations are explicit: their overlay is not a measurement of time per
logical event. Candidate gains at the smallest input remain visible. Every
three-call range and both graph curves remain; 216 plotted summaries and 432
normalized individual times are exported with exact rational numerators and
denominators. The next two figures show every paired ratio versus size; optional
inline figures show all three pair directions for all six endpoint inputs.

The noinline control applies to the query method alone. Both depth variants
retain the helper API and its inlining changes; this is not pure representation
isolation. Object inspection also finds the default depth query method itself
out of line, so an observed gain cannot be described as solely query-body
inlining. Native timing and compiler effects must be interpreted together.

Three focused plot-data tests in `test_plot_candidate.py` passed in 0.193 s
(actual exit 0, owned group 54585 empty; receipt
`validation/candidate-plot-mocks-attempt01.json`).
They enumerate exact normalizations from integers, preserve small-input gains,
reject mismatched work identities and retain a deliberately losing trial. Plot
rendering completed in the explicitly released quiet interval: six PNGs and six
SVGs, with all six PNGs directly inspected. The output directory is
`figures-depth-attempt01/`, and the source/output-bound visual receipt is
`validation/candidate-figures-visual-review-attempt01.json` (render actual exit
0).

The completed primary timing output is `depth-timing-analysis-attempt01/`
(actual exit 0), with all 288 raw rows, 216 clock-pair records,
96 two-model fit rows and 1,152 residual rows. The small exact-ratio summary
`depth-timing-summary-attempt01/` retains all five losing clock observations and
every graph/case median. Its producer is `inspect_candidate_timing.py`; the
invocation/result binding is `validation/candidate-timing-analysis-attempt01.json`.
See the main [results narrative](../../../docs/scaling-investigation/RESULTS.md)
for interpretation. Phase output is `depth-phase-analysis-attempt01/` and its
all-input exact additive summary is `depth-phase-summary-attempt01/`.
Inline output is `depth-inline-analysis-attempt01/` (72 raw rows, 108 clock-pair
records, actual exit 0). All capture-specific observations stay
separate; the control is not pooled into the primary timing campaign.

## Actual Google Benchmark export

`analyze_candidate_google.py` is a separate adapter for a complete six-curve
Google run. It preserves the actual emitted BigO/RMS records and exact original
JSON bytes. It does not replace the library's model choices with the custom
six-size fits above. The library selects its model using process CPU and then
fits the manual-clock coefficient using that same model. Only the CPU RMS is
exported by this library; the adapter does not invent a manual RMS field.

The declared scope is three families, fresh reference/depth variants, one graph
seed (19000013), one sampler (3001) and all eleven ascending sizes 1K–1M. The
594 native rows include 198 warmups and 396 timed calls. Across the two native
clocks, the adapter exports 396 matched callback/iteration ratios, 66 case
summaries, 396 exact two-call means and 132 absolute-time summaries. These are
separate process curves paired by labels, not simultaneous observations. Ratios
of separate medians, all ranges and every win/loss remain explicit. Coefficients
are compared only if the two library-selected models agree.

The following commands were executed after the parent's post-capture release.
All four synthetic groups passed in 0.071 s; the archival wrapper exited 0 with
an empty owned group (`validation/google-analysis-mocks-attempt01.json`).

```sh
cd benchmark/scaling_investigation/analysis
/usr/bin/python3 -B -m unittest -v test_analyze_candidate_google.py
```

```sh
/usr/bin/python3 -B benchmark/scaling_investigation/analysis/analyze_candidate_google.py \
  --capture benchmark/results/scaling-investigation-2026-10-15/depth-google01/capture.json \
  --output benchmark/scaling_investigation/analysis/depth-google-analysis-attempt01
```

The adapter uses the Google runner's full current build, source, historical
fingerprint, certificate, clock, resource and process-exit proof. It additionally
checks the raw Cartesian matrix and derives its arithmetic independently. Source
and output hashes are pinned and rechecked. Historical timings are never pooled
into these fresh curves. Actual strict analysis passed in 1.813 s with exit 0
and an empty owned group (`validation/google-analysis-actual-attempt01.json`).
All six actual library choices are NlgN. The separately
computed integer-raw summary is `depth-google-summary-attempt01/`, produced by
`inspect_candidate_google.py`; its guarded execution also passed with exit 0
and empty owned group (`validation/google-summary-attempt01.json`). It verifies
every exported pair and both median definitions against
the 594 original rows. Main interpretation, including all campaign differences
and losses, is in [RESULTS.md](../../../docs/scaling-investigation/RESULTS.md).
