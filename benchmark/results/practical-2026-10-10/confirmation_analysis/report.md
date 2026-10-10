# KKT optimization: before/after evidence

Match by case, graph seed, KKT seed, repetition, and algorithm; divide final elapsed time by baseline elapsed time for each matched trial. Take the median over repetitions, then sampling seeds within each graph, then graph seeds. Final-run KKT/competitor ratios use the same hierarchy on contemporaneous four-algorithm trial blocks. Values below one favor final KKT for its before/after comparison or KKT versus its competitor. Graph ranges span three graph-level medians and are not confidence intervals.

Improving KKT and beating another MST implementation are separate outcomes. This report retains all cases, including regressions and final-run losses. There is no pooled mean speedup or workload-frequency interpretation of case counts.

## Diverse suite

Validated 39 identical cases and 5,616 complete, matched timed observations per phase (4 repetitions, 1 warmups per seed pair and algorithm). [baseline raw CSV](../reserve.csv) · [final raw CSV](../confirmation.csv).

KKT has a lower matched median runtime in **30/39 cases**, a higher runtime in **9**, and equal runtime in **0**. Final/baseline ratios range from **0.909× to 1.026×**.

| Unchanged timing control | Final/baseline case-ratio range | Cases outside ±5% |
|---|---:|---:|
| Kruskal | 0.885–1.046× | 5 |
| Prim | 0.913–1.052× | 4 |
| Borůvka | 0.917–1.045× | 4 |

The ±5% screen is a descriptive stability check, not a significance threshold or an automatic correction. Control movement can reflect scheduling, cache, allocator, thermal, or clock effects. It does not uniquely identify their cause.

Final KKT is below all three competitors by paired case medians in: `geometric_grid_n16384`, `hub_n1024`, `hub_n4096`, `hub_n16384`, `star_n4096`, `star_n16384`.

The stronger descriptive check—below every competitor on every graph-level median—holds in: `hub_n1024`, `hub_n4096`, `hub_n16384`, `star_n16384`. Neither check establishes statistical certainty or performance on unmeasured inputs.

| Case | KKT final/baseline | Graph range | Final KKT/Kruskal | Final KKT/Prim | Final KKT/Borůvka |
|---|---:|---:|---:|---:|---:|
| random_4_n1024 | 0.930 | 0.920–0.971 | 1.300 | 0.436 | 0.892 |
| random_4_n4096 | 1.011 | 0.990–1.015 | 1.219 | 0.419 | 0.857 |
| random_4_n16384 | 0.972 | 0.971–0.999 | 1.274 | 0.369 | 0.773 |
| random_4_n65536 | 0.999 | 0.992–1.017 | 1.319 | 0.330 | 0.692 |
| random_32_n1024 | 0.966 | 0.961–0.996 | 0.521 | 0.675 | 1.611 |
| random_32_n4096 | 1.007 | 0.973–1.010 | 0.602 | 0.609 | 1.868 |
| random_32_n16384 | 0.990 | 0.979–0.992 | 0.815 | 0.736 | 2.138 |
| random_32_n65536 | 1.018 | 0.950–1.018 | 1.753 | 1.356 | 3.313 |
| random_128_n1024 | 0.967 | 0.961–1.005 | 0.344 | 0.791 | 1.962 |
| random_128_n4096 | 0.970 | 0.965–1.025 | 0.487 | 1.012 | 2.811 |
| random_128_n16384 | 0.982 | 0.899–1.014 | 1.281 | 2.302 | 5.159 |
| random_dense_anchor_n1000 | 0.971 | 0.946–1.020 | 0.281 | 0.909 | 1.484 |
| grid_n1024 | 0.957 | 0.869–1.168 | 2.052 | 0.556 | 0.695 |
| grid_n4096 | 1.018 | 0.991–1.064 | 1.512 | 0.543 | 0.579 |
| grid_n16384 | 0.998 | 0.978–1.001 | 1.434 | 0.489 | 0.486 |
| geometric_grid_n1024 | 0.950 | 0.866–1.145 | 1.309 | 0.431 | 0.777 |
| geometric_grid_n4096 | 0.962 | 0.937–0.969 | 1.035 | 0.420 | 0.667 |
| geometric_grid_n16384 | 1.022 | 1.011–1.022 | 0.987 | 0.392 | 0.520 |
| hub_n1024 | 0.909 | 0.830–1.029 | 0.882 | 0.285 | 0.718 |
| hub_n4096 | 0.972 | 0.968–1.003 | 0.731 | 0.251 | 0.641 |
| hub_n16384 | 1.019 | 0.986–1.031 | 0.721 | 0.210 | 0.604 |
| clustered_n1024 | 1.005 | 0.869–1.036 | 0.460 | 0.475 | 1.047 |
| clustered_n4096 | 0.961 | 0.956–0.971 | 0.536 | 0.486 | 1.065 |
| clustered_n16384 | 0.982 | 0.980–0.989 | 0.637 | 0.523 | 1.157 |
| planted_tree_n1024 | 0.987 | 0.964–1.032 | 1.369 | 0.457 | 0.917 |
| planted_tree_n4096 | 0.979 | 0.961–1.000 | 1.185 | 0.394 | 0.803 |
| planted_tree_n16384 | 0.984 | 0.963–0.998 | 1.211 | 0.355 | 0.796 |
| random_tree_n1024 | 0.977 | 0.958–1.045 | 3.009 | 0.556 | 0.444 |
| random_tree_n4096 | 1.026 | 0.939–1.081 | 1.757 | 0.527 | 0.389 |
| random_tree_n16384 | 0.977 | 0.970–0.978 | 1.463 | 0.500 | 0.318 |
| star_n1024 | 0.995 | 0.985–1.013 | 1.424 | 0.250 | 0.291 |
| star_n4096 | 0.993 | 0.978–0.995 | 0.700 | 0.145 | 0.252 |
| star_n16384 | 0.992 | 0.956–0.998 | 0.391 | 0.111 | 0.227 |
| hierarchical_path_n1024 | 0.954 | 0.948–0.981 | 11.604 | 2.309 | 0.950 |
| hierarchical_path_n4096 | 0.955 | 0.915–1.039 | 5.749 | 2.291 | 0.597 |
| hierarchical_path_n16384 | 0.988 | 0.970–0.999 | 4.570 | 2.417 | 0.443 |
| complete_n256 | 0.983 | 0.937–1.019 | 0.269 | 0.728 | 1.293 |
| complete_n512 | 1.015 | 0.998–1.036 | 0.256 | 0.860 | 1.559 |
| complete_n1024 | 0.925 | 0.900–1.006 | 0.278 | 1.056 | 2.454 |

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
