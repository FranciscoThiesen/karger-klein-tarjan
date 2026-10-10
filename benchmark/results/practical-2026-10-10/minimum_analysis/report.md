# KKT optimization: before/after evidence

Match by case, graph seed, KKT seed, repetition, and algorithm; divide final elapsed time by baseline elapsed time for each matched trial. Take the median over repetitions, then sampling seeds within each graph, then graph seeds. Final-run KKT/competitor ratios use the same hierarchy on contemporaneous four-algorithm trial blocks. Values below one favor final KKT for its before/after comparison or KKT versus its competitor. Graph ranges span three graph-level medians and are not confidence intervals.

Improving KKT and beating another MST implementation are separate outcomes. This report retains all cases, including regressions and final-run losses. There is no pooled mean speedup or workload-frequency interpretation of case counts.

## Diverse suite

Validated 39 identical cases and 5,616 complete, matched timed observations per phase (4 repetitions, 1 warmups per seed pair and algorithm). [baseline raw CSV](../owned.csv) · [final raw CSV](../minimum.csv).

KKT has a lower matched median runtime in **27/39 cases**, a higher runtime in **12**, and equal runtime in **0**. Final/baseline ratios range from **0.920× to 1.213×**.

| Unchanged timing control | Final/baseline case-ratio range | Cases outside ±5% |
|---|---:|---:|
| Kruskal | 0.892–1.520× | 5 |
| Prim | 0.861–1.171× | 6 |
| Borůvka | 0.935–1.167× | 4 |

The ±5% screen is a descriptive stability check, not a significance threshold or an automatic correction. Control movement can reflect scheduling, cache, allocator, thermal, or clock effects. It does not uniquely identify their cause.

Final KKT is below all three competitors by paired case medians in: `hub_n1024`, `hub_n4096`, `hub_n16384`, `star_n16384`.

The stronger descriptive check—below every competitor on every graph-level median—holds in: `hub_n4096`, `hub_n16384`, `star_n16384`. Neither check establishes statistical certainty or performance on unmeasured inputs.

| Case | KKT final/baseline | Graph range | Final KKT/Kruskal | Final KKT/Prim | Final KKT/Borůvka |
|---|---:|---:|---:|---:|---:|
| random_4_n1024 | 0.936 | 0.831–1.037 | 1.338 | 0.449 | 0.989 |
| random_4_n4096 | 0.973 | 0.973–1.012 | 1.253 | 0.417 | 0.904 |
| random_4_n16384 | 0.978 | 0.961–0.993 | 1.314 | 0.401 | 0.854 |
| random_4_n65536 | 0.988 | 0.970–0.989 | 1.383 | 0.331 | 0.729 |
| random_32_n1024 | 0.979 | 0.959–1.001 | 0.514 | 0.685 | 1.655 |
| random_32_n4096 | 0.977 | 0.960–0.995 | 0.606 | 0.614 | 1.863 |
| random_32_n16384 | 0.998 | 0.995–1.009 | 0.807 | 0.713 | 2.128 |
| random_32_n65536 | 1.060 | 0.999–1.135 | 1.727 | 1.249 | 3.154 |
| random_128_n1024 | 0.978 | 0.976–1.002 | 0.347 | 0.788 | 1.944 |
| random_128_n4096 | 0.988 | 0.964–0.994 | 0.477 | 0.931 | 2.624 |
| random_128_n16384 | 0.976 | 0.963–1.011 | 1.235 | 2.235 | 5.178 |
| random_dense_anchor_n1000 | 0.992 | 0.971–1.003 | 0.275 | 0.943 | 1.498 |
| grid_n1024 | 1.213 | 1.157–1.370 | 2.085 | 0.594 | 0.760 |
| grid_n4096 | 1.003 | 0.991–1.006 | 1.607 | 0.567 | 0.623 |
| grid_n16384 | 1.012 | 0.968–1.017 | 1.547 | 0.519 | 0.534 |
| geometric_grid_n1024 | 0.966 | 0.861–0.986 | 1.266 | 0.491 | 0.851 |
| geometric_grid_n4096 | 0.993 | 0.980–1.006 | 1.111 | 0.446 | 0.713 |
| geometric_grid_n16384 | 0.989 | 0.960–0.991 | 1.071 | 0.416 | 0.570 |
| hub_n1024 | 0.964 | 0.853–1.124 | 0.966 | 0.308 | 0.813 |
| hub_n4096 | 0.973 | 0.969–1.003 | 0.778 | 0.268 | 0.707 |
| hub_n16384 | 0.995 | 0.987–1.009 | 0.792 | 0.231 | 0.662 |
| clustered_n1024 | 0.920 | 0.901–0.978 | 0.461 | 0.477 | 1.037 |
| clustered_n4096 | 0.976 | 0.975–0.985 | 0.551 | 0.495 | 1.109 |
| clustered_n16384 | 0.966 | 0.959–0.978 | 0.651 | 0.497 | 1.167 |
| planted_tree_n1024 | 0.922 | 0.776–0.968 | 1.489 | 0.435 | 0.971 |
| planted_tree_n4096 | 0.973 | 0.966–1.005 | 1.183 | 0.408 | 0.851 |
| planted_tree_n16384 | 0.982 | 0.982–0.999 | 1.279 | 0.366 | 0.861 |
| random_tree_n1024 | 1.002 | 0.971–1.021 | 3.499 | 0.592 | 0.486 |
| random_tree_n4096 | 1.016 | 0.979–1.052 | 2.061 | 0.593 | 0.466 |
| random_tree_n16384 | 1.005 | 1.003–1.020 | 1.763 | 0.619 | 0.398 |
| star_n1024 | 1.001 | 0.988–1.004 | 1.957 | 0.330 | 0.407 |
| star_n4096 | 1.026 | 1.012–1.034 | 1.235 | 0.230 | 0.403 |
| star_n16384 | 1.009 | 0.979–1.027 | 0.758 | 0.212 | 0.445 |
| hierarchical_path_n1024 | 1.001 | 0.997–1.001 | 11.072 | 2.363 | 0.966 |
| hierarchical_path_n4096 | 1.022 | 0.979–1.055 | 5.978 | 2.525 | 0.632 |
| hierarchical_path_n16384 | 0.986 | 0.978–0.995 | 4.807 | 2.517 | 0.481 |
| complete_n256 | 1.000 | 0.962–1.032 | 0.260 | 0.757 | 1.454 |
| complete_n512 | 0.993 | 0.981–1.022 | 0.256 | 0.820 | 1.610 |
| complete_n1024 | 0.971 | 0.966–0.989 | 0.277 | 1.058 | 2.503 |

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
