# Distance ladder paper figures

`plot_distance_paper.py` is a separate presentation adapter. Source prepared
during the quiet distance capture; it has not been imported, syntax-checked,
tested or rendered. It does not read partial results and does not modify the
frozen collector, native binaries, earlier figure adapters or earlier images.

After the complete distance capture, strict analysis, independent numerical
audit and original four-figure generation pass, this adapter rereads those
bound artifacts and invokes the original strict loader and plot preparation.
The raw-derived canonical tables must exactly equal the original
`plotted_values.json`, including all 60 point classifications, 150 endpoint
pairs and ten crossover summaries. The independent audit is a prerequisite,
not a role claimed by the presentation adapter.

Four 7.1 by 8.8 inch figures retain the two family panels, all six sizes, both
clocks, every five-comparator ratio and every six-solver absolute time. The 264
pooled summaries each include both graph medians and both full-trial-range
endpoints. CPU and wall plots have identical family-specific axis bounds. The
corrected explicit right margin preserves the final six-digit-size label; the
larger lower margin separates the legend and three-line caption. All labels
are at least 8.5 pt at their declared physical canvas width. Actual visual QA,
including endpoint labels and final page-size placement, remains mandatory.

Example **future** invocation under the existing bounded nonnative guard:

```sh
/usr/bin/python3 -B docs/kkt-report/publication-tools/plot_distance_paper.py \
  --capture benchmark/results/eighth-distance-2026-10-15/distance.json \
  --source-plot benchmark/plot_eighth_distance.py \
  --standalone benchmark/results/eighth-distance-2026-10-15/figures-attempt01 \
  --audit benchmark/results/eighth-distance-2026-10-15/validation/independent-numerical-audit-attempt01/audit.json \
  --output benchmark/results/eighth-distance-2026-10-15/figures-paper-attempt01 \
  --released
```

The exact completed original/audit output paths must be verified before use;
this example does not assert those future artifacts exist. The output directory
is exclusive. Failures retain partial artifacts and a failure receipt. Successful
rendering remains `rendered_pending_visual_qa` and does not establish a final PDF
page count, interactive-viewer validity or any performance result.
