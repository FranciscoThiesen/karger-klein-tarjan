# KKT optimization: before/after evidence

Match by case, graph seed, KKT seed, repetition, and algorithm; divide final elapsed time by baseline elapsed time for each matched trial. Take the median over repetitions, then sampling seeds within each graph, then graph seeds. Final-run KKT/competitor ratios use the same hierarchy on contemporaneous four-algorithm trial blocks. Values below one favor final KKT for its before/after comparison or KKT versus its competitor. Graph ranges span three graph-level medians and are not confidence intervals.

Improving KKT and beating another MST implementation are separate outcomes. This report retains all cases, including regressions and final-run losses. There is no pooled mean speedup or workload-frequency interpretation of case counts.

## Diverse suite

Validated 39 identical cases and 5,616 complete, matched timed observations per phase (4 repetitions, 1 warmups per seed pair and algorithm). [baseline raw CSV](../owned.csv) · [final raw CSV](../reserve.csv).

KKT has a lower matched median runtime in **22/39 cases**, a higher runtime in **17**, and equal runtime in **0**. Final/baseline ratios range from **0.537× to 1.128×**.

| Unchanged timing control | Final/baseline case-ratio range | Cases outside ±5% |
|---|---:|---:|
| Kruskal | 0.898–1.361× | 9 |
| Prim | 0.887–1.112× | 12 |
| Borůvka | 0.969–1.134× | 13 |

The ±5% screen is a descriptive stability check, not a significance threshold or an automatic correction. Control movement can reflect scheduling, cache, allocator, thermal, or clock effects. It does not uniquely identify their cause.

Final KKT is below all three competitors by paired case medians in: `geometric_grid_n16384`, `hub_n1024`, `hub_n4096`, `hub_n16384`, `star_n4096`, `star_n16384`.

The stronger descriptive check—below every competitor on every graph-level median—holds in: `geometric_grid_n16384`, `hub_n1024`, `hub_n4096`, `hub_n16384`, `star_n4096`, `star_n16384`. Neither check establishes statistical certainty or performance on unmeasured inputs.

| Case | KKT final/baseline | Graph range | Final KKT/Kruskal | Final KKT/Prim | Final KKT/Borůvka |
|---|---:|---:|---:|---:|---:|
| random_4_n1024 | 1.031 | 1.018–1.081 | 1.288 | 0.452 | 0.878 |
| random_4_n4096 | 0.935 | 0.926–0.994 | 1.193 | 0.428 | 0.825 |
| random_4_n16384 | 0.987 | 0.960–0.987 | 1.279 | 0.390 | 0.789 |
| random_4_n65536 | 0.963 | 0.961–0.968 | 1.321 | 0.340 | 0.709 |
| random_32_n1024 | 1.034 | 0.998–1.040 | 0.520 | 0.638 | 1.618 |
| random_32_n4096 | 1.009 | 0.998–1.024 | 0.598 | 0.614 | 1.905 |
| random_32_n16384 | 1.024 | 1.022–1.038 | 0.820 | 0.754 | 2.117 |
| random_32_n65536 | 1.128 | 1.076–1.142 | 1.795 | 1.362 | 3.409 |
| random_128_n1024 | 1.024 | 0.987–1.056 | 0.344 | 0.783 | 1.908 |
| random_128_n4096 | 1.053 | 1.008–1.067 | 0.486 | 1.014 | 2.775 |
| random_128_n16384 | 1.076 | 1.052–1.141 | 1.310 | 2.409 | 5.277 |
| random_dense_anchor_n1000 | 1.031 | 1.025–1.047 | 0.282 | 0.996 | 1.499 |
| grid_n1024 | 1.112 | 0.910–1.173 | 2.143 | 0.579 | 0.718 |
| grid_n4096 | 0.967 | 0.901–0.987 | 1.508 | 0.537 | 0.571 |
| grid_n16384 | 0.937 | 0.930–0.945 | 1.433 | 0.504 | 0.480 |
| geometric_grid_n1024 | 0.961 | 0.870–1.034 | 1.240 | 0.456 | 0.805 |
| geometric_grid_n4096 | 0.992 | 0.968–1.005 | 1.056 | 0.432 | 0.665 |
| geometric_grid_n16384 | 0.928 | 0.913–0.945 | 0.966 | 0.391 | 0.521 |
| hub_n1024 | 1.087 | 0.995–1.194 | 0.865 | 0.295 | 0.741 |
| hub_n4096 | 0.957 | 0.932–0.976 | 0.752 | 0.246 | 0.644 |
| hub_n16384 | 0.936 | 0.919–0.946 | 0.703 | 0.215 | 0.612 |
| clustered_n1024 | 0.946 | 0.916–1.206 | 0.467 | 0.478 | 1.034 |
| clustered_n4096 | 1.007 | 0.984–1.012 | 0.543 | 0.493 | 1.092 |
| clustered_n16384 | 1.006 | 0.979–1.013 | 0.642 | 0.517 | 1.177 |
| planted_tree_n1024 | 0.906 | 0.835–0.947 | 1.432 | 0.449 | 0.916 |
| planted_tree_n4096 | 0.983 | 0.965–0.995 | 1.175 | 0.397 | 0.790 |
| planted_tree_n16384 | 0.965 | 0.949–0.967 | 1.218 | 0.357 | 0.777 |
| random_tree_n1024 | 0.851 | 0.850–0.873 | 3.051 | 0.537 | 0.436 |
| random_tree_n4096 | 0.929 | 0.819–1.044 | 1.763 | 0.527 | 0.381 |
| random_tree_n16384 | 0.841 | 0.831–0.842 | 1.500 | 0.506 | 0.327 |
| star_n1024 | 0.706 | 0.674–0.761 | 1.346 | 0.249 | 0.278 |
| star_n4096 | 0.627 | 0.608–0.641 | 0.647 | 0.139 | 0.249 |
| star_n16384 | 0.537 | 0.535–0.540 | 0.395 | 0.109 | 0.228 |
| hierarchical_path_n1024 | 1.002 | 0.986–1.019 | 12.063 | 2.319 | 0.913 |
| hierarchical_path_n4096 | 0.977 | 0.938–1.019 | 5.704 | 2.369 | 0.603 |
| hierarchical_path_n16384 | 0.953 | 0.947–0.961 | 4.516 | 2.444 | 0.457 |
| complete_n256 | 1.017 | 0.978–1.098 | 0.273 | 0.723 | 1.348 |
| complete_n512 | 1.028 | 1.004–1.047 | 0.251 | 0.810 | 1.552 |
| complete_n1024 | 1.042 | 1.025–1.135 | 0.292 | 1.087 | 2.611 |

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
