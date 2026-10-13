# Figure coverage and visual review

The recorded figure validation retains **27 case/campaign observations per metric**: discovery 19, extension 3, precision 5. A separate lightweight count confirms 27 wall rows and 27 CPU rows in `figure_points.csv` (54 data rows), matching the 27 rows in each strict comparison case-summary table. Campaigns remain separately labeled; no observations were removed or adjusted.

All ten PNGs have been visually inspected. The main reviewer checked `crossover_ratios_wall.png` and `crossover_cost_per_edge_wall.png`. An independent reviewer opened the other eight: both control figures, all four complete-case appendix pages, `crossover_ratios_cpu.png`, and `crossover_cost_per_edge_cpu.png`.

Titles, axes, units, family names, reference lines, legends and footnotes are readable without clipping or overlap. The line panel distinguishes narrow and wide gaps and explicitly identifies their different coordinates. Campaign markers/styles remain distinct. The large narrow-line trial spread, smaller-input losses, density controls and hierarchy/random anchors remain visible. All-case plots span two pages per metric; the three observations on the second page are retained.

These are single-graph screens. Trial ranges are not confidence intervals, connecting segments are not asymptotic fits, and the 0.90 line is not a confirmation verdict. SVG and PDF exports were generated from the same figure objects but were not separately rendered in this review. No figure regeneration or benchmark execution was performed for this QA pass.

[Figure guide](README.md), [numeric points](figure_points.csv), [provenance](provenance.json), [strict comparison](../all-screens-comparison/report.md).
