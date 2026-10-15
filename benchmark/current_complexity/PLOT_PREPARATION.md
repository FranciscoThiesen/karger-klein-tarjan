# Current complexity figures — source preparation only

`plot_complexity.py` has been written but not imported, syntax-checked, tested or rendered. No current library build, native complexity curve, fitted outcome or visual acceptance is implied. The active extension capture and all frozen sources are untouched.

The prospective output is five standalone figures, each PNG/SVG/PDF:

1. Native steady-wall T/(n+m), three family panels.
2. Native process-CPU T/(n+m), the same panels.
3. Library manual T/(n+m), retained separately.
4. Library process-CPU T/(n+m), retained separately.
5. All 24 curves' six-model normalized RMS residuals: full eleven-size Google CPU selection beside the explicitly custom upper-six-size selection.

Every normalized panel contains both algorithms and all four graph/sampler realizations at every one of eleven sizes. Each native point shows the median and complete min–max of six calls. Each library point instead summarizes three library two-call means; it is not assigned a nonexistent six-call library range. There are 1,056 displayed normalized points in total. The four figures share positive log-y limits derived from every full range, with padding and endpoint assertions, and each normalized median must equal its original median divided by N. Lines connect observations, not fitted/extrapolated thresholds. Colors encode algorithm and markers encode realization; explicit figure legends and range captions are part of the source. Captions disclose G1's ascending size order and G2's descending order, which confound graph realization with order. The separately named library CPU clock has a different timer envelope.

The model figure retains 24 rows and six columns in each of two panels, 288 cells. Each fit uses one curve's 33 full-window or 18 upper-window two-call library CPU means. The full panel outlines the actual validated Google `oAuto` CPU choice; the upper panel outlines the separately computed custom minimum. Google fits the manual coefficient to its CPU-selected model and exports CPU RMS only. The source does not relabel the upper fit as built-in, independently select a built-in manual model, pool realizations, or infer a crossover from a ratio of medians. Reconstructed residuals are displayed in percent, with exact underlying values retained.

The plotter requires explicit reviewed analyzer/collector paths and hashes, the complete analysis directory and an exclusive output directory. It verifies the analysis receipt and complete input/output inventories, invokes the unchanged collector's strict reload, revalidates the genuine build/schema-smoke proof, rereads every raw/library curve through the checked analyzer, and compares all six canonical CSV tables and both JSON artifacts to reconstruction before rendering. This deliberately **reuses** the analyzer; it is not another independent numerical audit. All source/ancestor/raw/table hashes are checked before and after use. The ordinary library context/reports and all clock flags stay bound. No row is removed or adjusted.

All six complete analysis CSVs, including all four clocks and every model/window, are copied unchanged into the figure output's `analysis_tables/`. `plotted_values.json` records every plotted point, model cell, outline scope and all 24 Google selections. Metadata records source/input/output hashes and Matplotlib version. Failure preserves the new attempt, and success is only `rendered_pending_visual_qa`. The plotter does not acquire a library, compile code, launch native solvers or overwrite old evidence; strict provenance checking can invoke the inherited bounded read-only metadata tools. A bounded archival outer invocation is still required.

Example future command, **not executed**, from the intended frozen eighth worktree after the genuine capture/analysis and a separate plotting release:

```sh
/usr/bin/python3 -B /tmp/kkt-current-complexity-prep/plot_complexity.py \
  --analysis /absolute/completed-analysis \
  --analyzer /tmp/kkt-current-complexity-prep/analyze_complexity.py \
  --analyzer-sha256 REVIEWED_ANALYZER_SHA256 \
  --collector /tmp/kkt-current-complexity-prep/collect.py \
  --collector-sha256 REVIEWED_COLLECTOR_SHA256 \
  --output-dir /absolute/new-figures-attempt01 --released
```

Remaining gates are substantive rather than tests that repeat plotting statements: peer source review; real collector/analyzer/library schema acceptance; a bounded synthetic rendering check with separated clocks, distinct realizations, zero residuals and widely separated full-range endpoints; refusal of changed/missing source tables or incomplete realization identities; and original-resolution visual inspection of all five PNGs. Check 24 model labels, all outlined choices, legends, range endpoints, no clipping, and the full-versus-upper distinction. Any use in the maximum-40-page report additionally requires page-scale legibility. Source preparation does not establish those results.
