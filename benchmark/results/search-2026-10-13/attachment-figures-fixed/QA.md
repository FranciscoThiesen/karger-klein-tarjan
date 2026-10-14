# Attachment figure visual audit

All 24 final PNGs were opened as images and inspected after regeneration: six paired-ratio pages and six absolute-runtime pages for each of wall and process CPU time. Each figure also has SVG and PDF exports (72 image artifacts total). Visual inspection covered PNG renderings; separate PDF/SVG rendering was not performed.

| Metric | Paired ratios | Separate runtimes | Finding |
|---|---|---|---|
| Wall | Pages 01–06 | Pages 01–06 | Pass |
| Process CPU | Pages 01–06 | Pages 01–06 | Pass |

Titles, mathematical exponents, units, family/density labels, legends, trial-range bars and single-size controls are readable. The 1.0 and 0.90 reference lines are identified on ratio figures. Algorithm colors/markers agree across the bundle. Near-overlapping points and very small ranges remain visible to the extent allowed by the displayed log scale; exact observations remain in the linked tables. No clipping or label overlap remains.

A first unpublished render had a legend/x-label overlap on the two-panel final ratio page. The single-row bottom margin was increased from 0.18 to 0.27, then all figures were regenerated into this fresh directory. The original and replacement provenance records bind the exact same analysis input hashes. The [superseded-layout record](../validation/attachment-figure-layout/README.md) retains two affected draft PNGs and their original provenance. Raw and derived timing data were unchanged.

Each metric retains all 80 cases over 32 family/density panels: four comparator ratios and five absolute runtimes per case, for 1,440 plotted median values across both metrics. The source tables contain 640 comparison rows and 800 runtime-summary rows. The titles explicitly identify one graph seed, one sampling seed, five timed repetitions and one checked warmup per algorithm. Min–max bars describe individual trial ranges, not confidence intervals; lines merely connect measured sizes. These are discovery results and do not establish fresh-seed confirmation.

Reproduction (from repository root, to a fresh directory):

```sh
python3 benchmark/plot_mst_search.py --analysis-dir benchmark/results/search-2026-10-13/attachment-analysis --output-dir /tmp/kkt-attachment-figures --include-cpu
```

[Figure and input hashes](provenance.json) bind this bundle to the strictly validated analysis.
