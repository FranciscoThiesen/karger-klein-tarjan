# Density-pilot figure QA

Opened all eight original PNG files directly, serially, with no resizing or
rerendering:

- `campaign_01_wall_paired_ratios_01.png`
- `campaign_01_wall_paired_ratios_02.png`
- `campaign_01_wall_runtimes_01.png`
- `campaign_01_wall_runtimes_02.png`
- `campaign_01_cpu_paired_ratios_01.png`
- `campaign_01_cpu_paired_ratios_02.png`
- `campaign_01_cpu_runtimes_01.png`
- `campaign_01_cpu_runtimes_02.png`

All eight are readable. No clipped titles, labels, legends or error bars;
overlapping text; or missing glyphs were found. Panel order, colors and
comparator definitions agree between wall and CPU pages. The titles identify
one graph seed, one sampling seed, five repetitions and one checked warmup.
Logarithmic axes and parity/0.9 references are labeled. Runtime panels show
all five algorithms; nearly overlapping KKT/compactor series correspond to
near-equal measured values. Single-size controls appear as isolated points.
The unused sixth panel on page two is blank intentionally, with no missing
case implied. Footers correctly describe trial min–max ranges as observed
spread, not confidence intervals, and avoid fitted or interpolated crossovers.

The strict tables retain 25 cases, 625 timed calls and 125 warmups. Four
case-median KKT/compactor ratios are at most 0.90 on both wall and CPU time:
hierarchical-tree and distance-tree at n=262,144, densities 64 and 128.
Their best wall median is 0.866514 for hierarchy/density64. Each group has
only one tested size meeting that threshold; these are discovery leads,
not completed fresh-seed confirmation. KKT loses all 125 paired timed trials
to Kruskal and all 125 to original Borůvka, on both metrics. The plots preserve
these negative comparisons and all three random controls.

No image or source change is requested. SVG/PDF exports were not independently
opened in this QA pass. The completed [power audit](../density-power-audit/audit.json)
records zero flagged calls and no recorded power-event overlap, while retaining
the failed sleep-inhibition assertion; visual clarity does not strengthen
that environmental evidence.
