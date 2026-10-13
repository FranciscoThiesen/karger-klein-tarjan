# Figure validation and visual review

The figure builder revalidated the recorded raw captures, input hashes and all plotted comparison tables before rendering. The output includes all 19 case/campaign observations for each of the wall and process-CPU metrics (38 rows in `figure_points.csv`). No observations were removed or adjusted.

One valid capture and eight malformed inputs were checked independently using temporary copies of the comparison directory. The malformed cases covered removed observations, a boolean count, configuration and raw-input hash mismatches, missing and duplicate cases, an altered ratio, and a nonfinite ratio. All eight were rejected; the exact results are in [validation_checks.json](validation_checks.json).

All eight final PNGs were opened and visually inspected: ratios, separate solver cost per edge, density controls/anchors, and the complete case appendix, for both metrics. Titles, axes, family names, units, reference lines, legends and footnotes are readable without clipping or overlap. An unused future precision-ablation panel was removed from the cost dashboard. Each figure also has SVG and PDF exports; those formats were generated from the same figure objects, but were not separately rendered for this review.

The discovery figures describe one graph and two timed repetitions per case. Trial ranges are not confidence intervals. The future wide-gap line is supported by the plotting source but is absent from this campaign; its rendered appearance will require review after its data is available.

Reproduction:

```sh
python3 benchmark/build_crossover_figures.py \
  --comparison-dir benchmark/results/crossover-2026-10-13/discovery-comparison \
  --output-dir benchmark/results/crossover-2026-10-13/discovery-figures
```
