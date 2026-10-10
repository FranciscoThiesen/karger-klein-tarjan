# KKT optimization: before/after evidence

Match by case, graph seed, KKT seed, repetition, and algorithm; divide final elapsed time by baseline elapsed time for each matched trial. Take the median over repetitions, then sampling seeds within each graph, then graph seeds. Final-run KKT/competitor ratios use the same hierarchy on contemporaneous four-algorithm trial blocks. Values below one favor final KKT for its before/after comparison or KKT versus its competitor. Graph ranges span three graph-level medians and are not confidence intervals.

Improving KKT and beating another MST implementation are separate outcomes. This report retains all cases, including regressions and final-run losses. There is no pooled mean speedup or workload-frequency interpretation of case counts.

## Diverse suite

Validated 39 identical cases and 5,616 complete, matched timed observations per phase (4 repetitions, 1 warmups per seed pair and algorithm). [baseline raw CSV](../csr.csv) · [final raw CSV](../contraction.csv).

KKT has a lower matched median runtime in **29/39 cases**, a higher runtime in **10**, and equal runtime in **0**. Final/baseline ratios range from **0.792× to 1.086×**.

| Unchanged timing control | Final/baseline case-ratio range | Cases outside ±5% |
|---|---:|---:|
| Kruskal | 0.893–1.186× | 3 |
| Prim | 0.955–1.108× | 3 |
| Borůvka | 0.959–1.119× | 3 |

The ±5% screen is a descriptive stability check, not a significance threshold or an automatic correction. Control movement can reflect scheduling, cache, allocator, thermal, or clock effects. It does not uniquely identify their cause.

Final KKT is below all three competitors by paired case medians in: `hub_n1024`, `hub_n4096`, `hub_n16384`, `star_n16384`.

The stronger descriptive check—below every competitor on every graph-level median—holds in: `hub_n1024`, `hub_n4096`, `hub_n16384`, `star_n16384`. Neither check establishes statistical certainty or performance on unmeasured inputs.

| Case | KKT final/baseline | Graph range | Final KKT/Kruskal | Final KKT/Prim | Final KKT/Borůvka |
|---|---:|---:|---:|---:|---:|
| random_4_n1024 | 1.086 | 0.990–1.109 | 1.327 | 0.491 | 0.948 |
| random_4_n4096 | 0.965 | 0.958–1.007 | 1.366 | 0.477 | 0.939 |
| random_4_n16384 | 0.989 | 0.985–0.995 | 1.455 | 0.438 | 0.893 |
| random_4_n65536 | 0.989 | 0.980–0.997 | 1.518 | 0.386 | 0.803 |
| random_32_n1024 | 1.020 | 0.968–1.036 | 0.528 | 0.669 | 1.711 |
| random_32_n4096 | 0.999 | 0.989–1.006 | 0.624 | 0.639 | 2.005 |
| random_32_n16384 | 0.994 | 0.953–1.016 | 0.862 | 0.780 | 2.261 |
| random_32_n65536 | 0.984 | 0.984–1.019 | 1.765 | 1.323 | 3.347 |
| random_128_n1024 | 0.995 | 0.986–0.998 | 0.350 | 0.812 | 1.947 |
| random_128_n4096 | 0.999 | 0.984–1.004 | 0.472 | 0.988 | 2.650 |
| random_128_n16384 | 0.957 | 0.915–0.980 | 1.093 | 2.083 | 4.599 |
| random_dense_anchor_n1000 | 0.993 | 0.992–1.008 | 0.273 | 0.952 | 1.436 |
| grid_n1024 | 0.917 | 0.888–0.993 | 2.026 | 0.699 | 0.839 |
| grid_n4096 | 1.008 | 0.920–1.052 | 1.705 | 0.602 | 0.635 |
| grid_n16384 | 0.981 | 0.975–1.013 | 1.643 | 0.557 | 0.550 |
| geometric_grid_n1024 | 0.986 | 0.912–0.991 | 1.406 | 0.518 | 0.872 |
| geometric_grid_n4096 | 0.980 | 0.980–1.007 | 1.123 | 0.477 | 0.753 |
| geometric_grid_n16384 | 0.981 | 0.972–0.994 | 1.090 | 0.439 | 0.596 |
| hub_n1024 | 1.071 | 0.969–1.083 | 0.939 | 0.337 | 0.780 |
| hub_n4096 | 1.001 | 0.976–1.051 | 0.838 | 0.284 | 0.724 |
| hub_n16384 | 0.980 | 0.968–0.985 | 0.809 | 0.239 | 0.672 |
| clustered_n1024 | 0.984 | 0.968–1.099 | 0.459 | 0.474 | 1.031 |
| clustered_n4096 | 1.017 | 0.989–1.032 | 0.564 | 0.531 | 1.132 |
| clustered_n16384 | 1.007 | 0.978–1.017 | 0.669 | 0.555 | 1.214 |
| planted_tree_n1024 | 0.991 | 0.964–1.019 | 1.738 | 0.492 | 1.097 |
| planted_tree_n4096 | 0.979 | 0.975–0.981 | 1.345 | 0.467 | 0.949 |
| planted_tree_n16384 | 0.991 | 0.988–1.007 | 1.416 | 0.421 | 0.929 |
| random_tree_n1024 | 0.882 | 0.838–0.893 | 3.660 | 0.627 | 0.525 |
| random_tree_n4096 | 0.953 | 0.939–0.964 | 2.078 | 0.610 | 0.476 |
| random_tree_n16384 | 0.965 | 0.949–0.972 | 1.859 | 0.634 | 0.397 |
| star_n1024 | 0.792 | 0.787–0.814 | 1.993 | 0.355 | 0.404 |
| star_n4096 | 0.804 | 0.797–0.807 | 1.352 | 0.240 | 0.393 |
| star_n16384 | 0.813 | 0.806–0.829 | 0.753 | 0.212 | 0.438 |
| hierarchical_path_n1024 | 0.957 | 0.949–0.966 | 12.647 | 2.371 | 1.019 |
| hierarchical_path_n4096 | 1.007 | 0.958–1.038 | 7.048 | 2.644 | 0.666 |
| hierarchical_path_n16384 | 0.977 | 0.962–0.989 | 5.129 | 2.774 | 0.501 |
| complete_n256 | 0.985 | 0.955–1.021 | 0.262 | 0.767 | 1.401 |
| complete_n512 | 1.000 | 0.956–1.049 | 0.265 | 0.890 | 1.540 |
| complete_n1024 | 1.031 | 0.991–1.063 | 0.290 | 1.129 | 2.671 |

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
