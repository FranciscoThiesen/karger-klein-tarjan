# Lower-density paper figures — source preparation only

No imports, tests, hashes, render, installation, or native calls have run for
this package. Actual lower-density data and its complete independent audit do
not yet exist. The reviewed standalone plotter remains unchanged.

`plot_lower_density_paper.py` adapts the existing distance paper layout. It
requires the actual lower-density collector's strict completed-capture reload,
the completed independent audit with exact typed counts, and hash-bound
standalone figures and plotted values. It reconstructs canonical tables and
requires exact equality with the standalone tables, including all 150 point
classifications, 490 earlier/later endpoint pairs and 20 crossover summaries.
It never recalculates a favorable subset or combines densities.

Eight figures split density 16/8 × ratio/absolute time × wall/CPU, each with the
two matched families stacked. Every canvas is 7.1 × 8.8 inches, with no tight
bounding-box resize and no font below 8.5 points. All seven/eight size labels
remain visible in the source layout, rotated 25 degrees with inward-facing
endpoint alignment. Actual label overlap and page-scale readability still need
visual QA. Each panel's y limits agree across clocks for the same density and
family; they include all graph medians and trial endpoints. Curves connect
measured sizes only. Graph/order confounding and descriptive ranges are explicit.

The data equality gate retains 660 pooled points (308 at density 16 and 352 at
density 8), 1,320 graph medians, and 1,320 trial-range endpoints. Figure outputs
include PNG/SVG/PDF plus every original canonical table in `plotted_values.json`
and explicit drawn points/coverage in `paper_points.json`. Output provenance
continues to say `rendered_pending_visual_qa` until a separate review.

Four prepared synthetic groups exercise the actual standalone `prepare()` and
publication loader. Only the native collector and style-index dependency are
test doubles. They check the full density/clock/solver matrix, losses as well as
wins, exact values, rehashed numerical/classification mutations, missing series,
wrong density, duplicate graph identities, source/output/capture hash drift,
typed audit counts, strict JSON, and import-path restoration. These are not
native certification or rendering tests; the synthetic receipts cannot serve as
real study evidence.

Future installation, after explicit root release, is into the existing
`docs/kkt-report/publication-tools/` directory with no overwrites. Run the mocks
under the existing archival nonnative guard using a fresh attempt prefix:

```sh
/usr/bin/python3 -B docs/kkt-report/publication-tools/test_plot_lower_density_paper.py \
  --standalone-source benchmark/plot_lower_density.py
```

After the complete native study, strict analysis, independent audit, and
standalone plots have passed, a separately released render command is:

```sh
/usr/bin/python3 -B docs/kkt-report/publication-tools/plot_lower_density_paper.py \
  --capture benchmark/results/lower-density-2026-10-15/lower-density.json \
  --source-plot benchmark/plot_lower_density.py \
  --standalone benchmark/results/lower-density-2026-10-15/figures-attempt01 \
  --audit benchmark/results/lower-density-2026-10-15/independent-audit-attempt01/audit.json \
  --output benchmark/results/lower-density-2026-10-15/paper-figures-attempt01 --released
```

Commands above are unexecuted. Use the actual completed audit destination if the
root handoff chooses another fresh path; never overwrite previous attempts.
