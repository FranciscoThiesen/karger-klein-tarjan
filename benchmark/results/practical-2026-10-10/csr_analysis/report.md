# KKT optimization: before/after evidence

Match by case, graph seed, KKT seed, repetition, and algorithm; divide final elapsed time by baseline elapsed time for each matched trial. Take the median over repetitions, then sampling seeds within each graph, then graph seeds. Final-run KKT/competitor ratios use the same hierarchy on contemporaneous four-algorithm trial blocks. Values below one favor final KKT for its before/after comparison or KKT versus its competitor. Graph ranges span three graph-level medians and are not confidence intervals.

Improving KKT and beating another MST implementation are separate outcomes. This report retains all cases, including regressions and final-run losses. There is no pooled mean speedup or workload-frequency interpretation of case counts.

## Diverse suite

Validated 39 identical cases and 5,616 complete, matched timed observations per phase (4 repetitions, 1 warmups per seed pair and algorithm). [baseline raw CSV](../mask.csv) · [final raw CSV](../csr.csv).

KKT has a lower matched median runtime in **36/39 cases**, a higher runtime in **3**, and equal runtime in **0**. Final/baseline ratios range from **0.680× to 1.065×**.

| Unchanged timing control | Final/baseline case-ratio range | Cases outside ±5% |
|---|---:|---:|
| Kruskal | 0.905–1.196× | 5 |
| Prim | 0.942–1.191× | 2 |
| Borůvka | 0.906–1.058× | 7 |

The ±5% screen is a descriptive stability check, not a significance threshold or an automatic correction. Control movement can reflect scheduling, cache, allocator, thermal, or clock effects. It does not uniquely identify their cause.

Final KKT is below all three competitors by paired case medians in: `hub_n4096`, `hub_n16384`, `star_n16384`.

The stronger descriptive check—below every competitor on every graph-level median—holds in: `hub_n4096`, `hub_n16384`. Neither check establishes statistical certainty or performance on unmeasured inputs.

| Case | KKT final/baseline | Graph range | Final KKT/Kruskal | Final KKT/Prim | Final KKT/Borůvka |
|---|---:|---:|---:|---:|---:|
| random_4_n1024 | 0.904 | 0.896–0.914 | 1.473 | 0.480 | 1.009 |
| random_4_n4096 | 0.874 | 0.864–0.886 | 1.335 | 0.481 | 0.990 |
| random_4_n16384 | 0.826 | 0.819–0.839 | 1.453 | 0.444 | 0.926 |
| random_4_n65536 | 0.817 | 0.810–0.821 | 1.526 | 0.386 | 0.846 |
| random_32_n1024 | 0.974 | 0.960–1.007 | 0.530 | 0.668 | 1.747 |
| random_32_n4096 | 0.920 | 0.903–0.930 | 0.627 | 0.692 | 2.018 |
| random_32_n16384 | 0.836 | 0.830–0.840 | 0.863 | 0.789 | 2.322 |
| random_32_n65536 | 0.680 | 0.669–0.685 | 1.825 | 1.343 | 3.440 |
| random_128_n1024 | 1.012 | 0.976–1.018 | 0.355 | 0.823 | 1.982 |
| random_128_n4096 | 0.959 | 0.937–0.978 | 0.478 | 0.956 | 2.659 |
| random_128_n16384 | 1.012 | 0.940–1.022 | 1.215 | 2.219 | 4.998 |
| random_dense_anchor_n1000 | 0.991 | 0.971–1.026 | 0.273 | 0.937 | 1.510 |
| grid_n1024 | 1.065 | 1.049–1.217 | 2.306 | 0.695 | 0.817 |
| grid_n4096 | 0.978 | 0.949–0.981 | 1.715 | 0.593 | 0.682 |
| grid_n16384 | 0.989 | 0.983–0.996 | 1.641 | 0.576 | 0.577 |
| geometric_grid_n1024 | 0.967 | 0.893–0.974 | 1.427 | 0.527 | 0.883 |
| geometric_grid_n4096 | 0.984 | 0.978–1.016 | 1.159 | 0.475 | 0.749 |
| geometric_grid_n16384 | 0.988 | 0.983–1.004 | 1.117 | 0.446 | 0.625 |
| hub_n1024 | 0.902 | 0.895–0.979 | 1.013 | 0.323 | 0.842 |
| hub_n4096 | 0.979 | 0.918–0.991 | 0.809 | 0.285 | 0.734 |
| hub_n16384 | 0.986 | 0.952–0.999 | 0.806 | 0.242 | 0.695 |
| clustered_n1024 | 0.934 | 0.929–0.967 | 0.473 | 0.486 | 1.044 |
| clustered_n4096 | 0.986 | 0.977–0.999 | 0.558 | 0.520 | 1.171 |
| clustered_n16384 | 0.960 | 0.948–0.970 | 0.673 | 0.532 | 1.262 |
| planted_tree_n1024 | 0.900 | 0.876–0.931 | 1.618 | 0.490 | 1.123 |
| planted_tree_n4096 | 0.893 | 0.884–0.894 | 1.339 | 0.452 | 0.940 |
| planted_tree_n16384 | 0.830 | 0.825–0.840 | 1.473 | 0.427 | 0.956 |
| random_tree_n1024 | 0.985 | 0.915–0.989 | 4.051 | 0.717 | 0.583 |
| random_tree_n4096 | 0.989 | 0.889–1.009 | 2.321 | 0.687 | 0.504 |
| random_tree_n16384 | 0.980 | 0.971–0.983 | 1.924 | 0.659 | 0.435 |
| star_n1024 | 0.977 | 0.959–0.989 | 2.442 | 0.432 | 0.537 |
| star_n4096 | 0.969 | 0.886–1.043 | 1.614 | 0.306 | 0.533 |
| star_n16384 | 0.999 | 0.997–1.014 | 0.943 | 0.260 | 0.547 |
| hierarchical_path_n1024 | 0.883 | 0.859–0.940 | 13.559 | 2.672 | 1.080 |
| hierarchical_path_n4096 | 0.889 | 0.883–0.930 | 7.102 | 2.607 | 0.697 |
| hierarchical_path_n16384 | 0.943 | 0.938–0.949 | 5.186 | 2.820 | 0.537 |
| complete_n256 | 0.984 | 0.960–0.990 | 0.270 | 0.759 | 1.448 |
| complete_n512 | 0.989 | 0.967–0.991 | 0.262 | 0.946 | 1.614 |
| complete_n1024 | 0.968 | 0.929–0.999 | 0.282 | 1.054 | 2.620 |

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
