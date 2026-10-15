# Independent complexity paper adapter source review

Source-only review on 15 October 2026: **PASS; no release-blocking source issue
found.** Reviewed `plot_complexity_paper.py` and
`COMPLEXITY_PAPER_PREPARATION.md` against the prepared standalone
`/tmp/kkt-current-complexity-prep/plot_complexity.py`. The author identified the
reviewed versions with hash prefixes `8660259e` and `15e0c633`, respectively;
this reviewer did not run a fresh hash or any code during the performance hold.
Full source hashes must be retained at the eventual runtime gate.

The original strict `load_evidence` interface receives the required explicit
analysis/analyzer/collector paths and hashes. Its own source identity remains
the standalone module's path, so the exact equality with the standalone input
inventory is appropriate. The adapter additionally binds its own source and
the standalone provenance. All 22 standalone outputs are required: fifteen
image exports, six canonical CSVs and the plotted-value JSON. The CSV copies
are compared with freshly checked canonical content. Initial/final hash checks
and exclusive output/failure receipts preserve the original artifacts.

Normalized-point ordering matches the standalone render loop exactly:
four clocks × three families × two algorithms × four graph/sampler
realizations × eleven sizes = **1,056 points**. The model-cell order also
matches: two windows × 24 curves × six models = **288 cells**, retaining all
24 exported Google choices. Deep exact comparisons reject changed types or
values, not merely unequal row counts; identities are also unique before
drawing. Complete rendered point/cell inventories are checked against the
original values again after drawing and after JSON serialization.

The six canvases are explicitly 7.05×9 inches, saved without tight-bounding-box
rescaling. Four pages stack the three normalized family panels and preserve
both algorithms, all four realizations, every size and full ranges. Common
full-range y limits are reused across clocks. The remaining two pages retain
the full 24×6 residual matrix for each window with common color limits and
one selected-model outline per row. No loss, range, model or realization is
removed for page width.

Clock labels and captions preserve the distinct native versus library timer
envelopes and six-call versus three-two-call-mean ranges. Full-window outlines
are the actual exported Google CPU choices; upper-six outlines are explicitly
custom CPU selections, not built-in results. The shared CPU-selected/manual
coefficient semantics and CPU-only exported RMS remain qualified. The adapter
performs no new fit or pooling and does not claim an independent raw audit.

Runtime and visual acceptance remain outstanding. In particular, review long
24-row labels, colorbar bounds, eight overlaid realization curves, legends and
captions at the actual printed size. Principal plot text is about 9–10 points;
matrix row labels are 8.4 points and some captions 8.2 points, as disclosed by
the preparation note. Those smaller labels need deliberate page-scale QA or
enlargement, not an assumption of readability. No import, test, synthetic
render, browser, native job or partial timing-result read occurred. The final
report's actual <=40-page and every-page checks remain separate gates.
