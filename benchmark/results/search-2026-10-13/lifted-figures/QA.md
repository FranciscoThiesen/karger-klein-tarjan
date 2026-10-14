# Lifted-pilot figure QA

The reviewer opened these eight original PNG files directly, without resizing, rerendering or executing analysis during the subsequent density capture:

- `campaign_01_wall_paired_ratios_02.png`
- `campaign_01_wall_runtimes_01.png`
- `campaign_01_wall_runtimes_02.png`
- `campaign_01_cpu_paired_ratios_01.png`
- `campaign_01_cpu_paired_ratios_02.png`
- `campaign_01_cpu_runtimes_01.png`
- `campaign_01_cpu_runtimes_02.png`
- `illustrative_lifted_hierarchy.png`

The parent separately inspected `campaign_01_wall_paired_ratios_01.png` and reported it clear. Together these checks cover all nine rendered PNGs. SVG and PDF exports were not independently opened in this QA pass.

No clipping, overlapping text, missing glyphs or unreadable legends were found. Wall and CPU pages retain the same panel/family ordering, colors and comparator definitions. Logarithmic axes, ratio references at 1 and 0.9, observed-trial error bars, and the one-graph/one-sampling-seed protocol are labeled. The controls measured at only one size correctly appear as isolated points, without invented trends. Runtime pages keep all five algorithms; near-overlapping KKT/compactor curves are consistent with their near-equal values, not missing series. The schematic clearly identifies its invented small layout and contains no measured fixture or timing claim. No source or image change is requested from this review.

The completed pilot contains **28 cases, 700 timed calls and 140 retained warmup calls**, with zero reported clock flags. It found **no case-median KKT/compacting-Borůvka ratio at or below 0.9**. The best wall ratio is **0.927429** for `lifted_hierarchy2_n1048576_d64_p0`; its CPU ratio is **0.927437**. At that same case KKT/Kruskal is 2.4906, KKT/Prim 1.7777 and KKT/original-Borůvka 1.5534 on wall time. Thus this screen does not establish a clear advantage over all four competitors or a confirmed crossover. All comparisons, including losses, remain in the [analysis table](../lifted-analysis/comparisons.csv). This is a one-graph-seed, one-sampling-seed pilot with five repetitions, not a population-level conclusion or a proof that a larger crossover cannot exist.
