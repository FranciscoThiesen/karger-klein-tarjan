# KKT optimization: before/after evidence

Match by case, graph seed, KKT seed, repetition, and algorithm; divide final elapsed time by baseline elapsed time for each matched trial. Take the median over repetitions, then sampling seeds within each graph, then graph seeds. Final-run KKT/competitor ratios use the same hierarchy on contemporaneous four-algorithm trial blocks. Values below one favor final KKT for its before/after comparison or KKT versus its competitor. Graph ranges span three graph-level medians and are not confidence intervals.

Improving KKT and beating another MST implementation are separate outcomes. This report retains all cases, including regressions and final-run losses. There is no pooled mean speedup or workload-frequency interpretation of case counts.

## Diverse suite

Validated 39 identical cases and 5,616 complete, matched timed observations per phase (4 repetitions, 1 warmups per seed pair and algorithm). [baseline raw CSV](../sample.csv) · [final raw CSV](../owned.csv).

KKT has a lower matched median runtime in **29/39 cases**, a higher runtime in **10**, and equal runtime in **0**. Final/baseline ratios range from **0.834× to 1.033×**.

| Unchanged timing control | Final/baseline case-ratio range | Cases outside ±5% |
|---|---:|---:|
| Kruskal | 0.704–1.141× | 5 |
| Prim | 0.857–1.101× | 4 |
| Borůvka | 0.850–1.017× | 4 |

The ±5% screen is a descriptive stability check, not a significance threshold or an automatic correction. Control movement can reflect scheduling, cache, allocator, thermal, or clock effects. It does not uniquely identify their cause.

Final KKT is below all three competitors by paired case medians in: `hub_n1024`, `hub_n4096`, `hub_n16384`, `star_n16384`.

The stronger descriptive check—below every competitor on every graph-level median—holds in: `hub_n4096`, `hub_n16384`, `star_n16384`. Neither check establishes statistical certainty or performance on unmeasured inputs.

| Case | KKT final/baseline | Graph range | Final KKT/Kruskal | Final KKT/Prim | Final KKT/Borůvka |
|---|---:|---:|---:|---:|---:|
| random_4_n1024 | 1.027 | 0.930–1.131 | 1.393 | 0.447 | 0.950 |
| random_4_n4096 | 1.013 | 0.980–1.015 | 1.276 | 0.442 | 0.913 |
| random_4_n16384 | 1.001 | 0.973–1.004 | 1.360 | 0.408 | 0.849 |
| random_4_n65536 | 0.989 | 0.979–0.995 | 1.403 | 0.347 | 0.742 |
| random_32_n1024 | 0.987 | 0.965–1.003 | 0.521 | 0.669 | 1.708 |
| random_32_n4096 | 0.982 | 0.978–1.002 | 0.615 | 0.640 | 1.930 |
| random_32_n16384 | 0.959 | 0.956–0.963 | 0.809 | 0.704 | 2.094 |
| random_32_n65536 | 0.890 | 0.869–0.981 | 1.581 | 1.218 | 3.223 |
| random_128_n1024 | 1.006 | 0.995–1.013 | 0.355 | 0.800 | 2.021 |
| random_128_n4096 | 1.003 | 0.979–1.025 | 0.484 | 0.951 | 2.735 |
| random_128_n16384 | 1.011 | 0.980–1.054 | 1.265 | 2.248 | 4.880 |
| random_dense_anchor_n1000 | 0.971 | 0.967–0.986 | 0.275 | 0.931 | 1.480 |
| grid_n1024 | 0.834 | 0.806–0.841 | 2.509 | 0.557 | 0.742 |
| grid_n4096 | 0.985 | 0.935–0.986 | 1.611 | 0.545 | 0.630 |
| grid_n16384 | 0.980 | 0.961–0.996 | 1.570 | 0.538 | 0.528 |
| geometric_grid_n1024 | 1.016 | 1.009–1.036 | 1.474 | 0.469 | 0.873 |
| geometric_grid_n4096 | 0.993 | 0.979–1.002 | 1.096 | 0.437 | 0.715 |
| geometric_grid_n16384 | 0.975 | 0.969–0.999 | 1.076 | 0.416 | 0.582 |
| hub_n1024 | 1.022 | 0.875–1.166 | 0.932 | 0.307 | 0.790 |
| hub_n4096 | 0.971 | 0.968–0.976 | 0.789 | 0.268 | 0.704 |
| hub_n16384 | 0.977 | 0.970–0.985 | 0.786 | 0.244 | 0.672 |
| clustered_n1024 | 1.028 | 0.941–1.028 | 0.491 | 0.486 | 1.095 |
| clustered_n4096 | 0.975 | 0.967–1.001 | 0.555 | 0.485 | 1.125 |
| clustered_n16384 | 0.993 | 0.988–1.021 | 0.671 | 0.518 | 1.194 |
| planted_tree_n1024 | 1.033 | 0.982–1.051 | 1.419 | 0.446 | 0.985 |
| planted_tree_n4096 | 0.972 | 0.972–0.972 | 1.217 | 0.407 | 0.867 |
| planted_tree_n16384 | 0.986 | 0.978–0.990 | 1.298 | 0.396 | 0.866 |
| random_tree_n1024 | 0.996 | 0.934–1.009 | 3.515 | 0.632 | 0.537 |
| random_tree_n4096 | 0.980 | 0.832–1.021 | 2.028 | 0.580 | 0.438 |
| random_tree_n16384 | 0.959 | 0.952–0.977 | 1.804 | 0.615 | 0.392 |
| star_n1024 | 0.980 | 0.978–0.993 | 1.973 | 0.349 | 0.412 |
| star_n4096 | 0.966 | 0.963–0.980 | 1.179 | 0.245 | 0.409 |
| star_n16384 | 0.977 | 0.977–0.991 | 0.769 | 0.208 | 0.439 |
| hierarchical_path_n1024 | 0.943 | 0.915–0.998 | 12.010 | 2.379 | 0.996 |
| hierarchical_path_n4096 | 1.000 | 0.984–1.019 | 6.146 | 2.562 | 0.618 |
| hierarchical_path_n16384 | 0.986 | 0.958–1.007 | 4.810 | 2.581 | 0.490 |
| complete_n256 | 0.959 | 0.948–0.968 | 0.265 | 0.767 | 1.434 |
| complete_n512 | 0.985 | 0.985–1.000 | 0.257 | 0.846 | 1.603 |
| complete_n1024 | 0.990 | 0.980–0.995 | 0.285 | 1.093 | 2.538 |

![All diverse before/after changes](diverse_before_after.png)

![Final diverse KKT comparison](diverse_final_competition.png)

## Interpretation and provenance

- Three graph seeds are the independent graph-level units. Sampling seeds and repetitions do not create additional independent graphs. Star sampling-seed labels do not change its KKT path.
- Before/after pairing aligns graph and sampling-seed labels plus repetition/order labels. It does not pair clock noise, temperature, or simultaneous machine state. Ratios of separately aggregated runtimes need not equal the matched-ratio medians reported here.
- Both phases retain the common tuple-edge-list timing boundary, including KKT conversion and temporary-input destruction. Source/certificate validation and returned-result destruction remain outside timing. The CSVs validate exact MST results through the unchanged harness.
- CSV validation cannot establish compiler, binary, fixture-source, or core-source identity. Consult the campaign metadata for exact revisions, hashes, flags, executable order, and host. Any algorithm intentionally changed beyond KKT must be identified before treating it as an unchanged control.
- These are repository implementations on synthetic graphs. A lead over Kruskal alone is not a lead over Prim and Borůvka. Small observed advantages warrant confirmation; neither these ratios nor fitted curves prove asymptotic complexity or an eventual crossover.

## Derived data

- `before_after.csv` and `graph_before_after.csv`: changes for all four algorithms, including losses.
- `matched_trials.csv`: every matched pair of raw durations and its final/baseline ratio.
- `phase_summary.csv`, `phase_graph_summary.csv`, and `phase_comparisons.csv`: reusable per-phase aggregates.
- `assessment.csv`: KKT changes and final-run comparisons against all three competitors for every case.
- `analysis.json`: input hashes, counts, retained regressions, descriptive winners, and control movement.
- Figures are also saved as SVG and PDF. The raw input CSVs are linked above; no old-run values are silently added.
