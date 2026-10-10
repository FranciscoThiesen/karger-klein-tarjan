# KKT optimization: before/after evidence

Match by case, graph seed, KKT seed, repetition, and algorithm; divide final elapsed time by baseline elapsed time for each matched trial. Take the median over repetitions, then sampling seeds within each graph, then graph seeds. Final-run KKT/competitor ratios use the same hierarchy on contemporaneous four-algorithm trial blocks. Values below one favor final KKT for its before/after comparison or KKT versus its competitor. Graph ranges span three graph-level medians and are not confidence intervals.

Improving KKT and beating another MST implementation are separate outcomes. This report retains all cases, including regressions and final-run losses. There is no pooled mean speedup or workload-frequency interpretation of case counts.

## Diverse suite

Validated 39 identical cases and 5,616 complete, matched timed observations per phase (4 repetitions, 1 warmups per seed pair and algorithm). [baseline raw CSV](../baseline.csv) · [final raw CSV](../mask.csv).

KKT has a lower matched median runtime in **38/39 cases**, a higher runtime in **1**, and equal runtime in **0**. Final/baseline ratios range from **0.583× to 1.000×**.

| Unchanged timing control | Final/baseline case-ratio range | Cases outside ±5% |
|---|---:|---:|
| Kruskal | 0.790–1.028× | 6 |
| Prim | 0.887–1.028× | 6 |
| Borůvka | 0.936–1.043× | 1 |

The ±5% screen is a descriptive stability check, not a significance threshold or an automatic correction. Control movement can reflect scheduling, cache, allocator, thermal, or clock effects. It does not uniquely identify their cause.

Final KKT is below all three competitors by paired case medians in: `hub_n4096`, `hub_n16384`, `star_n16384`.

The stronger descriptive check—below every competitor on every graph-level median—holds in: `hub_n4096`, `hub_n16384`, `star_n16384`. Neither check establishes statistical certainty or performance on unmeasured inputs.

| Case | KKT final/baseline | Graph range | Final KKT/Kruskal | Final KKT/Prim | Final KKT/Borůvka |
|---|---:|---:|---:|---:|---:|
| random_4_n1024 | 0.761 | 0.758–0.821 | 1.625 | 0.518 | 1.084 |
| random_4_n4096 | 0.740 | 0.724–0.748 | 1.535 | 0.533 | 1.059 |
| random_4_n16384 | 0.713 | 0.711–0.727 | 1.798 | 0.534 | 1.078 |
| random_4_n65536 | 0.704 | 0.696–0.706 | 1.910 | 0.481 | 1.018 |
| random_32_n1024 | 0.897 | 0.887–0.923 | 0.545 | 0.713 | 1.759 |
| random_32_n4096 | 0.790 | 0.778–0.793 | 0.692 | 0.754 | 2.207 |
| random_32_n16384 | 0.627 | 0.626–0.646 | 1.047 | 0.963 | 2.743 |
| random_32_n65536 | 0.583 | 0.578–0.588 | 2.695 | 2.061 | 5.310 |
| random_128_n1024 | 0.949 | 0.942–0.963 | 0.353 | 0.851 | 2.012 |
| random_128_n4096 | 0.834 | 0.831–0.893 | 0.493 | 1.024 | 2.732 |
| random_128_n16384 | 0.756 | 0.754–0.836 | 1.220 | 2.292 | 5.005 |
| random_dense_anchor_n1000 | 0.908 | 0.897–0.968 | 0.280 | 0.972 | 1.479 |
| grid_n1024 | 0.939 | 0.773–1.047 | 2.542 | 0.688 | 0.849 |
| grid_n4096 | 0.944 | 0.903–1.002 | 1.761 | 0.613 | 0.683 |
| grid_n16384 | 0.944 | 0.920–0.950 | 1.687 | 0.583 | 0.559 |
| geometric_grid_n1024 | 0.949 | 0.904–1.080 | 1.641 | 0.581 | 0.968 |
| geometric_grid_n4096 | 0.940 | 0.914–0.948 | 1.178 | 0.475 | 0.774 |
| geometric_grid_n16384 | 0.947 | 0.936–0.953 | 1.157 | 0.455 | 0.619 |
| hub_n1024 | 0.967 | 0.917–1.144 | 1.052 | 0.351 | 0.853 |
| hub_n4096 | 0.905 | 0.857–0.976 | 0.840 | 0.280 | 0.736 |
| hub_n16384 | 0.875 | 0.867–0.919 | 0.837 | 0.248 | 0.705 |
| clustered_n1024 | 0.987 | 0.931–1.000 | 0.496 | 0.491 | 1.077 |
| clustered_n4096 | 0.933 | 0.927–0.949 | 0.574 | 0.531 | 1.137 |
| clustered_n16384 | 0.826 | 0.818–0.827 | 0.695 | 0.572 | 1.252 |
| planted_tree_n1024 | 0.777 | 0.732–0.849 | 1.818 | 0.565 | 1.163 |
| planted_tree_n4096 | 0.753 | 0.736–0.764 | 1.520 | 0.516 | 1.062 |
| planted_tree_n16384 | 0.748 | 0.746–0.753 | 1.731 | 0.525 | 1.159 |
| random_tree_n1024 | 0.961 | 0.942–1.009 | 3.792 | 0.782 | 0.595 |
| random_tree_n4096 | 0.990 | 0.879–1.008 | 2.530 | 0.678 | 0.514 |
| random_tree_n16384 | 0.964 | 0.954–0.997 | 1.969 | 0.657 | 0.431 |
| star_n1024 | 1.000 | 0.982–1.021 | 2.533 | 0.448 | 0.530 |
| star_n4096 | 0.953 | 0.936–0.959 | 1.661 | 0.329 | 0.535 |
| star_n16384 | 0.963 | 0.949–0.993 | 0.936 | 0.263 | 0.541 |
| hierarchical_path_n1024 | 0.993 | 0.991–0.998 | 13.482 | 3.149 | 1.184 |
| hierarchical_path_n4096 | 0.976 | 0.951–0.994 | 6.744 | 2.892 | 0.730 |
| hierarchical_path_n16384 | 0.958 | 0.948–0.961 | 5.568 | 2.950 | 0.555 |
| complete_n256 | 0.990 | 0.966–0.990 | 0.277 | 0.752 | 1.373 |
| complete_n512 | 0.990 | 0.948–1.022 | 0.255 | 0.892 | 1.651 |
| complete_n1024 | 0.907 | 0.890–0.927 | 0.301 | 1.145 | 2.751 |

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
