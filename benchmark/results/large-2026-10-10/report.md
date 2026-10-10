# Large-instance benchmark analysis

This **exploratory sweep** contains 18 cases and 648 validated timed observations. Each case has three graph seeds, three KKT seeds, 1 measured repetition(s) per seed pair, and 0 warmup(s) per algorithm/seed pair.

| Baseline | Cases where KKT has lower paired median | KKT / baseline runtime range |
| --- | ---: | ---: |
| Kruskal | 4/18 | 0.769–11.424× |
| Prim | 9/18 | 0.148–10.767× |
| Borůvka | 6/18 | 0.484–20.614× |

Lower ratios are better for KKT. Ratios are aggregated from matched timings, not calculated by dividing the displayed aggregate runtimes.

KKT is below all three baselines by paired hierarchical medians in: `hub_n65536`, `star_n65536`, `star_n262144`.

Case counts refer only to the chosen matrix, not a workload-weighted ranking or a claim of statistical significance.

## Aggregation and interpretation

Median of repetitions for each graph/sampling-seed pair; median of the three sampling-seed values per graph; median of the three graph values. Paired ratios apply the same hierarchy to matched algorithm/reference elapsed-time ratios. Error bars span graph-level medians and are not confidence intervals.

**There is only one timing per graph/KKT-seed pair.** The graph and KKT seeds vary, but within-pair repeatability is unmeasured. Close races require a separate repeated run; this sweep alone does not confirm a crossover. The nine trial blocks do not give every algorithm exactly the same number of appearances in every timed position, although the schedule rotates positions across graph/sampling seeds.

There are no dedicated warmups. Fixture construction and certified-reference computation precede timing, so these are not controlled cold-cache measurements. The Kruskal reference call may affect cache/allocator state. Rotation limits systematic order effects but cannot remove them.

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
- `density.{png,svg,pdf}`: ratios at fixed vertex counts as density changes.

## Retained KKT losses

**Kruskal:** `random_4_n65536`, `random_4_n262144`, `random_4_n1048576`, `random_32_n65536`, `random_32_n262144`, `random_32_n1048576`, `random_128_n65536`, `random_128_n262144`, `random_512_n65536`, `hub_n262144`, `hub_n1048576`, `star_n1048576`, `complete_n4096`, `complete_n8192`

**Prim:** `random_32_n65536`, `random_32_n262144`, `random_32_n1048576`, `random_128_n65536`, `random_128_n262144`, `random_512_n65536`, `complete_n2048`, `complete_n4096`, `complete_n8192`

**Borůvka:** `random_4_n65536`, `random_4_n262144`, `random_4_n1048576`, `random_32_n65536`, `random_32_n262144`, `random_32_n1048576`, `random_128_n65536`, `random_128_n262144`, `random_512_n65536`, `complete_n2048`, `complete_n4096`, `complete_n8192`
