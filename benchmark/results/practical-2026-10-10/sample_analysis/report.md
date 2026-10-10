# KKT optimization: before/after evidence

Match by case, graph seed, KKT seed, repetition, and algorithm; divide final elapsed time by baseline elapsed time for each matched trial. Take the median over repetitions, then sampling seeds within each graph, then graph seeds. Final-run KKT/competitor ratios use the same hierarchy on contemporaneous four-algorithm trial blocks. Values below one favor final KKT for its before/after comparison or KKT versus its competitor. Graph ranges span three graph-level medians and are not confidence intervals.

Improving KKT and beating another MST implementation are separate outcomes. This report retains all cases, including regressions and final-run losses. There is no pooled mean speedup or workload-frequency interpretation of case counts.

## Diverse suite

Validated 39 identical cases and 5,616 complete, matched timed observations per phase (4 repetitions, 1 warmups per seed pair and algorithm). [baseline raw CSV](../contraction.csv) · [final raw CSV](../sample.csv).

KKT has a lower matched median runtime in **33/39 cases**, a higher runtime in **6**, and equal runtime in **0**. Final/baseline ratios range from **0.873× to 1.066×**.

| Unchanged timing control | Final/baseline case-ratio range | Cases outside ±5% |
|---|---:|---:|
| Kruskal | 0.728–1.140× | 8 |
| Prim | 0.904–1.073× | 6 |
| Borůvka | 0.887–1.102× | 5 |

The ±5% screen is a descriptive stability check, not a significance threshold or an automatic correction. Control movement can reflect scheduling, cache, allocator, thermal, or clock effects. It does not uniquely identify their cause.

Final KKT is below all three competitors by paired case medians in: `hub_n4096`, `hub_n16384`, `star_n16384`.

The stronger descriptive check—below every competitor on every graph-level median—holds in: `hub_n4096`, `hub_n16384`, `star_n16384`. Neither check establishes statistical certainty or performance on unmeasured inputs.

| Case | KKT final/baseline | Graph range | Final KKT/Kruskal | Final KKT/Prim | Final KKT/Borůvka |
|---|---:|---:|---:|---:|---:|
| random_4_n1024 | 0.874 | 0.845–0.969 | 1.418 | 0.440 | 0.914 |
| random_4_n4096 | 0.933 | 0.913–0.972 | 1.294 | 0.424 | 0.908 |
| random_4_n16384 | 0.935 | 0.924–0.959 | 1.372 | 0.401 | 0.839 |
| random_4_n65536 | 0.928 | 0.914–0.929 | 1.394 | 0.351 | 0.757 |
| random_32_n1024 | 1.002 | 0.979–1.029 | 0.536 | 0.687 | 1.633 |
| random_32_n4096 | 0.975 | 0.974–0.996 | 0.617 | 0.653 | 1.969 |
| random_32_n16384 | 0.954 | 0.954–0.960 | 0.834 | 0.748 | 2.144 |
| random_32_n65536 | 0.992 | 0.975–1.008 | 1.744 | 1.327 | 3.248 |
| random_128_n1024 | 0.988 | 0.974–0.996 | 0.346 | 0.855 | 1.940 |
| random_128_n4096 | 0.980 | 0.980–0.998 | 0.472 | 0.969 | 2.610 |
| random_128_n16384 | 1.066 | 1.007–1.138 | 1.178 | 2.156 | 4.841 |
| random_dense_anchor_n1000 | 1.040 | 1.019–1.074 | 0.279 | 0.953 | 1.507 |
| grid_n1024 | 0.901 | 0.839–0.907 | 2.120 | 0.631 | 0.816 |
| grid_n4096 | 0.954 | 0.942–0.985 | 1.628 | 0.556 | 0.630 |
| grid_n16384 | 0.971 | 0.930–0.972 | 1.580 | 0.543 | 0.523 |
| geometric_grid_n1024 | 0.891 | 0.883–0.925 | 1.401 | 0.475 | 0.867 |
| geometric_grid_n4096 | 0.948 | 0.938–0.960 | 1.093 | 0.436 | 0.713 |
| geometric_grid_n16384 | 0.971 | 0.968–0.972 | 1.072 | 0.436 | 0.579 |
| hub_n1024 | 0.873 | 0.861–0.983 | 1.053 | 0.316 | 0.799 |
| hub_n4096 | 0.978 | 0.974–0.985 | 0.802 | 0.271 | 0.694 |
| hub_n16384 | 0.983 | 0.982–0.985 | 0.797 | 0.246 | 0.679 |
| clustered_n1024 | 1.052 | 0.990–1.090 | 0.485 | 0.474 | 1.079 |
| clustered_n4096 | 0.969 | 0.966–1.020 | 0.562 | 0.515 | 1.115 |
| clustered_n16384 | 0.980 | 0.963–0.996 | 0.658 | 0.537 | 1.179 |
| planted_tree_n1024 | 1.017 | 0.978–1.092 | 1.638 | 0.473 | 1.004 |
| planted_tree_n4096 | 0.933 | 0.912–0.946 | 1.268 | 0.420 | 0.863 |
| planted_tree_n16384 | 0.920 | 0.910–0.924 | 1.299 | 0.391 | 0.867 |
| random_tree_n1024 | 0.968 | 0.925–0.990 | 3.542 | 0.613 | 0.506 |
| random_tree_n4096 | 0.979 | 0.942–0.991 | 2.127 | 0.604 | 0.454 |
| random_tree_n16384 | 0.973 | 0.925–0.996 | 1.857 | 0.631 | 0.398 |
| star_n1024 | 0.983 | 0.973–1.003 | 1.983 | 0.342 | 0.404 |
| star_n4096 | 1.034 | 1.031–1.060 | 1.219 | 0.236 | 0.412 |
| star_n16384 | 0.987 | 0.980–1.024 | 0.759 | 0.205 | 0.435 |
| hierarchical_path_n1024 | 0.994 | 0.968–1.014 | 12.162 | 2.439 | 0.999 |
| hierarchical_path_n4096 | 0.909 | 0.898–0.971 | 6.598 | 2.512 | 0.627 |
| hierarchical_path_n16384 | 0.950 | 0.932–0.974 | 4.913 | 2.632 | 0.484 |
| complete_n256 | 0.972 | 0.948–1.052 | 0.270 | 0.724 | 1.346 |
| complete_n512 | 0.985 | 0.937–0.996 | 0.252 | 0.874 | 1.570 |
| complete_n1024 | 0.976 | 0.965–0.987 | 0.279 | 1.061 | 2.508 |

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
