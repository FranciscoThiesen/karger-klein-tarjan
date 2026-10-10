# Diverse-graph benchmark analysis

Validated **5,616 observations across 39 cases**. Every measured result passed; all graph/sample/repetition/algorithm cells and balanced execution positions are present.

| Baseline | Cases where KKT is faster | KKT / baseline runtime range |
| --- | ---: | ---: |
| Kruskal | 14/39 | 0.264–14.780× |
| Prim | 31/39 | 0.256–3.108× |
| Borůvka | 16/39 | 0.426–7.843× |

Ratios below one favor KKT. Case counts describe this chosen matrix; they are not a weighted overall ranking or estimates of production workload frequency.

## Aggregation

Median of repetitions for each graph/sampling-seed pair; median of the three sampling-seed values per graph; median of the three graph values. Paired ratios apply the same hierarchy to matched algorithm/reference elapsed-time ratios. Error bars span graph-level medians and are not confidence intervals.

Only three graph seeds contribute to each case. Sampling seeds and repeated timings do not create additional independent graphs. For deterministic topologies, graph seeds may vary weights or input order rather than topology. KKT seed labels have no effect on deterministic baselines. Paired ratios align workloads and trial blocks, not simultaneous machine state.

## Timing and limits

The harness times the common edge-list entry boundary, including KKT's conversion to its problem representation and each algorithm's internal preparation. Fixture generation, oracle work, validation, output, and return-value destruction are outside timing. The algorithms retain their native output representations: KKT returns an ID hash set; the others return edge vectors.

Execution order is balanced, but desktop scheduling, cache state, allocator state, power, and temperature can still affect measurements. Graph-level min/max bars describe the observed spread and are not confidence intervals. Nanosecond clock units do not imply nanosecond measurement accuracy. Results compare these implementations and synthetic fixtures on the measured machine; they do not prove asymptotic complexity or locate unmeasured crossover thresholds.

## Files

- `summary.csv`: one row per case/algorithm, with hierarchical runtime medians and graph-level ranges.
- `graph_summary.csv`: graph-level aggregates, preserving all three seeds.
- `comparisons.csv`: matched runtime ratios against every baseline, including all slower observations.
- `relative_runtime.{png,svg,pdf}`: every case relative to Kruskal; blue is faster, red is slower.
- `runtime_by_family.{png,svg,pdf}`: scaling by graph family, with independent logarithmic panel scales.
- `density_comparison.{png,svg,pdf}`: KKT's paired ratio against each baseline at measured random-graph densities.

## Retained KKT losses

**Kruskal:** `random_4_n1024`, `random_4_n4096`, `random_4_n16384`, `random_4_n65536`, `random_32_n16384`, `random_32_n65536`, `random_128_n16384`, `grid_n1024`, `grid_n4096`, `grid_n16384`, `geometric_grid_n1024`, `geometric_grid_n4096`, `geometric_grid_n16384`, `hub_n1024`, `planted_tree_n1024`, `planted_tree_n4096`, `planted_tree_n16384`, `random_tree_n1024`, `random_tree_n4096`, `random_tree_n16384`, `star_n1024`, `star_n4096`, `hierarchical_path_n1024`, `hierarchical_path_n4096`, `hierarchical_path_n16384`

**Prim:** `random_32_n16384`, `random_32_n65536`, `random_128_n4096`, `random_128_n16384`, `hierarchical_path_n1024`, `hierarchical_path_n4096`, `hierarchical_path_n16384`, `complete_n1024`

**Borůvka:** `random_4_n1024`, `random_4_n4096`, `random_4_n16384`, `random_4_n65536`, `random_32_n1024`, `random_32_n4096`, `random_32_n16384`, `random_32_n65536`, `random_128_n1024`, `random_128_n4096`, `random_128_n16384`, `random_dense_anchor_n1000`, `geometric_grid_n1024`, `clustered_n1024`, `clustered_n4096`, `clustered_n16384`, `planted_tree_n1024`, `planted_tree_n4096`, `planted_tree_n16384`, `hierarchical_path_n1024`, `complete_n256`, `complete_n512`, `complete_n1024`
