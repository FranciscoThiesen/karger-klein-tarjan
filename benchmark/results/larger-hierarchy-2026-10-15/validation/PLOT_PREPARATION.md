# Larger hierarchy plot preparation

Prepared during native capture on 2026-10-15. **Source-only preparation and
independent review PASS; no import, syntax check, rendering or timing-data
analysis has been performed for this plotter.** Execution waits for root's
post-capture release and completed strict plus independent numerical audits.

Reviewed plotter SHA-256:
`af8096760abdc1cfb75cf7c6b2aad0c8e3214186f5ae808e46b96770772710ff`.

The new [plotter](../../../plot_larger_hierarchy.py) adapts the successfully
rendered held-out figure code without changing any frozen helper, native
source, protocol or artifact. It strictly reloads the complete 12-child / 504
output capture, then preserves the canonical 720 paired rows, 60/120 ratio
summaries, 72/144 absolute summaries and 30/30/10 crossover tables. No partial
capture path or historical timing input is provided.

Four figures will show wall/CPU ratios and absolute times across both families
and all three sizes. Every figure has two panels; all five comparisons or all
six absolute solver series remain, including both six-trial graph medians and
the full trial ranges. Pooled points use twelve trials, not twelve independent
graphs. Clock axes share bounds, and every plotted median/range endpoint is
checked to lie inside them. Legends retain a neutral KKT label; the caption
defines parity and the prospective strong threshold without interpolating a
crossover or calling descriptive ranges confidence intervals.

`experiment_design` independently reviewed the complete plotter source and
found no blocker. The changed 15.5×7.4-inch, two-panel layout still needs actual
rendering and inspection of all four PNGs after release. The output directory
must be fresh; canonical tables and input/output hashes are preserved. A
render-time pending QA status is not visual approval.
