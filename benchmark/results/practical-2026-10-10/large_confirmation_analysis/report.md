# Large-instance benchmark analysis

This **repeated measurement** contains 2 cases and 288 validated timed observations. Each case has three graph seeds, three KKT seeds, 4 measured repetition(s) per seed pair, and 1 warmup(s) per algorithm/seed pair.

| Baseline | Cases where KKT has lower paired median | KKT / baseline runtime range |
| --- | ---: | ---: |
| Kruskal | 2/2 | 0.442–0.816× |
| Prim | 2/2 | 0.043–0.131× |
| Borůvka | 2/2 | 0.141–0.421× |

Lower ratios are better for KKT. Ratios are aggregated from matched timings, not calculated by dividing the displayed aggregate runtimes.

KKT is below all three baselines by paired hierarchical medians in: `hub_n262144`, `star_n1048576`.

Case counts refer only to the chosen matrix, not a workload-weighted ranking or a claim of statistical significance.

## Aggregation and interpretation

Median of repetitions for each graph/sampling-seed pair; median of the three sampling-seed values per graph; median of the three graph values. Paired ratios apply the same hierarchy to matched algorithm/reference elapsed-time ratios. Error bars span graph-level medians and are not confidence intervals.

Repeated observations measure within-pair variation, but only three graph seeds contribute to each case. If the repetition count is a multiple of four, each algorithm occupies all four timed positions equally within every seed pair. Graph-level ranges remain descriptive and are not confidence intervals.

Deterministic baselines ignore the KKT-seed label; those observations are repeated timings of the same graph. Fixed topologies can vary only through labels, weights, or input order. Matched ratios align fixture/seed/trial blocks, not simultaneous execution or machine state.

Only observations from the supplied CSV are used. Earlier experiments and separate confirmation runs are never mixed automatically. A density sweep holds vertex count fixed; a size sweep holds the profile's edge/vertex ratio fixed where applicable. Complete graphs increase both vertex count and density. Lines connect measured points and do not establish an unmeasured crossover or an asymptotic bound.

## Timing boundary

All algorithms start from the same tuple edge list. KKT's problem conversion and temporary-input destruction are included, as are the baselines' internal preparation and all return-value construction. Fixture generation, certified-reference computation, output checking, CSV writing, and returned-output destruction are excluded. Outputs retain native representations: an ID hash set for KKT and edge vectors for the other implementations.

These results compare the repository implementations on the measured machine. Desktop scheduling, memory/cache behavior, allocator state, and power/thermal state remain possible influences. Nanosecond clock units are not a guarantee of nanosecond accuracy.

## Artifacts

- `summary.csv`: per-case/algorithm hierarchical runtime medians, graph-level ranges, and relative Kruskal timings.
- `graph_summary.csv`: all graph-level summaries.
- `comparisons.csv`: paired ratios against every baseline and individual loss counts.
- `large_scaling.{png,svg,pdf}`: runtime by size and profile.
- `large_ratios.{png,svg,pdf}`: KKT/baseline ratios, with the 1× crossing marked.

## Retained KKT losses

**Kruskal:** None in this input.

**Prim:** None in this input.

**Borůvka:** None in this input.
