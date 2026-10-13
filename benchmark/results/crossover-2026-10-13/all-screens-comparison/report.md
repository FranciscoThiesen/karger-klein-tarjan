# Crossover campaigns: retained wall and CPU evidence

Every campaign remains separate. Ratios pair KKT and compaction within each repetition, then take medians over repetitions, sampling seeds and graph seeds. Process CPU is a secondary diagnostic envelope; steady elapsed time remains primary. Clock flags retain every row. Repeated campaigns reuse the same graphs, not independent draws.

| Campaign | Role | Cases | Timed calls | Warmups | Flagged calls |
|---|---|---:|---:|---:|---:|
| discovery | screen | 19 | 76 | 38 | 0 |
| extension | screen | 3 | 12 | 6 | 0 |
| precision | screen | 5 | 20 | 10 | 0 |

## Frozen outcome

A selected group has a clear measured-range advantage only when the paired case ratio is ≤0.90 and every graph median is <1 at both frozen sizes, for wall and CPU separately in both runs. This is a descriptive rule, not a significance test or extrapolation. A lower-size observed loss/tie is listed separately; an all-winning range does not establish a crossover onset.

No frozen confirmation pair was supplied. All outcomes are exploratory.

## All wall cases

Graph ranges are observed ranges, not confidence intervals. Individual losses are retained.

| Campaign | Case | Paired ratio [graph range] | KKT ms | Compactor ms | KKT losses / pairs |
|---|---|---:|---:|---:|---:|
| discovery | line_random_n4194304_d16_p0 | 0.9746 [0.9746, 0.9746] | 19569.369 | 20080.079 | 0/2 |
| discovery | line_metric_n4194304_d16_p0 | 0.9078 [0.9078, 0.9078] | 21976.118 | 24206.865 | 0/2 |
| discovery | grid2d_metric_n4194304_d16_p0 | 0.9457 [0.9457, 0.9457] | 21066.345 | 22276.432 | 0/2 |
| discovery | gnm_random_n1048576_d16_p0 | 1.0132 [1.0132, 1.0132] | 3857.047 | 3807.139 | 2/2 |
| discovery | line_random_n1048576_d16_p0 | 1.0069 [1.0069, 1.0069] | 3766.116 | 3740.210 | 2/2 |
| discovery | grid2d_metric_n1048576_d16_p0 | 0.9552 [0.9552, 0.9552] | 4020.696 | 4209.166 | 0/2 |
| discovery | random_tree_n1048576_d16_p0 | 1.0107 [1.0107, 1.0107] | 3790.689 | 3750.591 | 2/2 |
| discovery | grid2d_random_n262144_d4_p0 | 1.2764 [1.2764, 1.2764] | 91.540 | 71.730 | 2/2 |
| discovery | line_random_n262144_d16_p0 | 1.1473 [1.1473, 1.1473] | 523.049 | 455.911 | 2/2 |
| discovery | line_metric_n262144_d16_p0 | 1.0541 [1.0541, 1.0541] | 595.520 | 565.017 | 2/2 |
| discovery | grid2d_random_n4194304_d16_p0 | 0.9817 [0.9817, 0.9817] | 20293.358 | 20671.129 | 0/2 |
| discovery | gnm_random_n262144_d16_p0 | 1.1518 [1.1518, 1.1518] | 530.289 | 460.418 | 2/2 |
| discovery | grid2d_random_n262144_d16_p0 | 1.0846 [1.0846, 1.0846] | 522.970 | 482.099 | 2/2 |
| discovery | grid2d_metric_n262144_d4_p0 | 1.3193 [1.3193, 1.3193] | 99.172 | 75.173 | 2/2 |
| discovery | line_metric_n1048576_d16_p0 | 0.9317 [0.9317, 0.9317] | 4190.771 | 4497.853 | 0/2 |
| discovery | hierarchical_path_n1048576_d16_p0 | 0.8122 [0.8122, 0.8122] | 4544.414 | 5595.234 | 0/2 |
| discovery | grid2d_random_n1048576_d16_p0 | 0.9969 [0.9969, 0.9969] | 3854.547 | 3867.162 | 1/2 |
| discovery | grid2d_metric_n262144_d16_p0 | 1.1122 [1.1122, 1.1122] | 576.964 | 518.800 | 2/2 |
| discovery | gnm_random_n4194304_d16_p0 | 0.9946 [0.9946, 0.9946] | 20287.118 | 20397.789 | 1/2 |
| extension | gnm_random_n8388608_d16_p0 | 0.9869 [0.9869, 0.9869] | 45089.340 | 45689.514 | 0/2 |
| extension | line_metric_n2097152_d16_p0 | 0.8880 [0.8880, 0.8880] | 9567.753 | 10774.593 | 0/2 |
| extension | line_metric_n8388608_d16_p0 | 0.9969 [0.9969, 0.9969] | 57111.161 | 57101.949 | 1/2 |
| precision | line_wide_metric_n1048576_d16_p0 | 0.8955 [0.8955, 0.8955] | 5265.906 | 5880.396 | 0/2 |
| precision | line_wide_metric_n8388608_d16_p0 | 0.9642 [0.9642, 0.9642] | 63282.218 | 65632.134 | 0/2 |
| precision | line_wide_metric_n262144_d16_p0 | 0.9824 [0.9824, 0.9824] | 839.183 | 854.200 | 0/2 |
| precision | line_wide_metric_n4194304_d16_p0 | 0.9339 [0.9339, 0.9339] | 27162.197 | 29083.647 | 0/2 |
| precision | hierarchical_path_n4194304_d16_p0 | 0.8643 [0.8643, 0.8643] | 31860.052 | 36861.259 | 0/2 |

## All cpu cases

Graph ranges are observed ranges, not confidence intervals. Individual losses are retained.

| Campaign | Case | Paired ratio [graph range] | KKT ms | Compactor ms | KKT losses / pairs |
|---|---|---:|---:|---:|---:|
| discovery | line_random_n4194304_d16_p0 | 0.9746 [0.9746, 0.9746] | 19569.366 | 20080.053 | 0/2 |
| discovery | line_metric_n4194304_d16_p0 | 0.9078 [0.9078, 0.9078] | 21975.628 | 24206.728 | 0/2 |
| discovery | grid2d_metric_n4194304_d16_p0 | 0.9457 [0.9457, 0.9457] | 21066.227 | 22276.417 | 0/2 |
| discovery | gnm_random_n1048576_d16_p0 | 1.0131 [1.0131, 1.0131] | 3856.834 | 3807.142 | 2/2 |
| discovery | line_random_n1048576_d16_p0 | 1.0069 [1.0069, 1.0069] | 3766.110 | 3740.215 | 2/2 |
| discovery | grid2d_metric_n1048576_d16_p0 | 0.9552 [0.9552, 0.9552] | 4020.699 | 4209.123 | 0/2 |
| discovery | random_tree_n1048576_d16_p0 | 1.0107 [1.0107, 1.0107] | 3790.691 | 3750.594 | 2/2 |
| discovery | grid2d_random_n262144_d4_p0 | 1.2764 [1.2764, 1.2764] | 91.541 | 71.731 | 2/2 |
| discovery | line_random_n262144_d16_p0 | 1.1474 [1.1474, 1.1474] | 523.050 | 455.902 | 2/2 |
| discovery | line_metric_n262144_d16_p0 | 1.0541 [1.0541, 1.0541] | 595.521 | 565.018 | 2/2 |
| discovery | grid2d_random_n4194304_d16_p0 | 0.9817 [0.9817, 0.9817] | 20293.292 | 20671.107 | 0/2 |
| discovery | gnm_random_n262144_d16_p0 | 1.1518 [1.1518, 1.1518] | 530.290 | 460.420 | 2/2 |
| discovery | grid2d_random_n262144_d16_p0 | 1.0846 [1.0846, 1.0846] | 522.971 | 482.096 | 2/2 |
| discovery | grid2d_metric_n262144_d4_p0 | 1.3193 [1.3193, 1.3193] | 99.172 | 75.174 | 2/2 |
| discovery | line_metric_n1048576_d16_p0 | 0.9317 [0.9317, 0.9317] | 4190.774 | 4497.854 | 0/2 |
| discovery | hierarchical_path_n1048576_d16_p0 | 0.8122 [0.8122, 0.8122] | 4544.343 | 5595.228 | 0/2 |
| discovery | grid2d_random_n1048576_d16_p0 | 0.9969 [0.9969, 0.9969] | 3854.539 | 3867.166 | 1/2 |
| discovery | grid2d_metric_n262144_d16_p0 | 1.1122 [1.1122, 1.1122] | 576.966 | 518.801 | 2/2 |
| discovery | gnm_random_n4194304_d16_p0 | 0.9946 [0.9946, 0.9946] | 20287.114 | 20397.785 | 1/2 |
| extension | gnm_random_n8388608_d16_p0 | 0.9869 [0.9869, 0.9869] | 45089.107 | 45689.395 | 0/2 |
| extension | line_metric_n2097152_d16_p0 | 0.8880 [0.8880, 0.8880] | 9567.657 | 10774.574 | 0/2 |
| extension | line_metric_n8388608_d16_p0 | 0.9981 [0.9981, 0.9981] | 57058.210 | 56980.891 | 1/2 |
| precision | line_wide_metric_n1048576_d16_p0 | 0.8955 [0.8955, 0.8955] | 5259.812 | 5873.839 | 0/2 |
| precision | line_wide_metric_n8388608_d16_p0 | 0.9642 [0.9642, 0.9642] | 63208.774 | 65558.402 | 0/2 |
| precision | line_wide_metric_n262144_d16_p0 | 0.9826 [0.9826, 0.9826] | 838.372 | 853.226 | 0/2 |
| precision | line_wide_metric_n4194304_d16_p0 | 0.9337 [0.9337, 0.9337] | 27133.072 | 29058.038 | 0/2 |
| precision | hierarchical_path_n4194304_d16_p0 | 0.8643 [0.8643, 0.8643] | 31824.988 | 36821.825 | 0/2 |

Every case, graph, pair and execution-order stratum is retained in `wall_*.csv` and `cpu_*.csv`. The CPU tables retain the shared aggregation column names but their nanoseconds and ratios are process CPU. `call_clocks.csv` contains every checked warmup and timed record. Original files are unchanged; hashes and source provenance are in [comparison_inputs.json](comparison_inputs.json).

Frozen and runner timestamps are recorded evidence, not independent authentication. Across screens, automatic code equality checks cover the listed production libraries; changed harness bodies need separate review. The confirmation pair requires identical full source inventories, binary and capture/analysis hashes. Fingerprints are consistency checks, not collision-proof graph certificates. Classical-baseline adjunct evidence is separate.
