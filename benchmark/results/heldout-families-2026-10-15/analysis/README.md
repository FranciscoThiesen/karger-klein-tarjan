# Held-out families with the frozen compressed-query candidate

All 3024 solver outputs passed exact MST validation: 2592 timed calls and 432 checked warmups. Each algorithm occupies every timed position once per child. This is a fresh, separately declared two-graph-seed campaign; historical timing is not pooled.

Test existing leaf-distance/shuffled, grid-metric/random and line-metric/random families across all six declared sizes, including 1024. Use the exact frozen compressed-query candidate and unchanged controls. Rank twins preserve topology, IDs, labels and physical order. Leaf-shuffled retains cheap leaves; spatial random modes shuffle all ranks. No new generator or historical pooling.

Compare KKT directly with all five competitors in the same child, graph seed, sampling seed and repetition. Pool all twelve paired trial ratios per case and retain each graph's six-trial median. No historical timing is pooled, normalized or replaced. Graph/trial ranges are descriptive, not confidence intervals.

All 0 clock-flagged calls and 0 capture/child UTC flags remain included. Wall and CPU clocks are separate; neither flags nor power events change the observations. RSS is a sampled process-group sum, not a continuous peak. Power-audit status: `archived_log_correlated`; verified sleep inhibition is not claimed.

| Case | Clock | KKT / compacting Boruvka | KKT / multigraph Boruvka | KKT / Kruskal | KKT / Prim | KKT / original Boruvka |
|---|---|---:|---:|---:|---:|---:|
| leaf_distance4_n1024_d32_p0 | wall | 2.1727 | 1.4906 | 1.2704 | 2.3132 | 2.6778 |
| leaf_distance4_n1024_d32_p0 | cpu | 2.1720 | 1.4911 | 1.2701 | 2.3102 | 2.6777 |
| leaf_shuffled4_n1024_d32_p0 | wall | 2.2136 | 2.1394 | 1.0146 | 2.3667 | 3.7148 |
| leaf_shuffled4_n1024_d32_p0 | cpu | 2.2127 | 2.1409 | 1.0137 | 2.3649 | 3.7061 |
| grid2d_metric_n1024_d32_p0 | wall | 1.9763 | 1.8314 | 1.1119 | 0.9657 | 2.9431 |
| grid2d_metric_n1024_d32_p0 | cpu | 1.9752 | 1.8306 | 1.1114 | 0.9660 | 2.9515 |
| grid2d_random_n1024_d32_p0 | wall | 1.8350 | 2.1542 | 0.9221 | 1.1808 | 3.2463 |
| grid2d_random_n1024_d32_p0 | cpu | 1.8345 | 2.1531 | 0.9220 | 1.1815 | 3.2467 |
| line_metric_n1024_d32_p0 | wall | 1.9189 | 1.6630 | 1.1051 | 0.5143 | 2.6006 |
| line_metric_n1024_d32_p0 | cpu | 1.9171 | 1.6636 | 1.1053 | 0.5146 | 2.6012 |
| line_random_n1024_d32_p0 | wall | 2.0701 | 1.8394 | 1.0452 | 1.3022 | 2.9416 |
| line_random_n1024_d32_p0 | cpu | 2.0678 | 1.8398 | 1.0454 | 1.3030 | 2.9388 |
| grid2d_metric_n4096_d32_p0 | wall | 1.6868 | 1.7833 | 1.0588 | 0.8604 | 2.7461 |
| grid2d_metric_n4096_d32_p0 | cpu | 1.6868 | 1.7835 | 1.0590 | 0.8604 | 2.7457 |
| grid2d_random_n4096_d32_p0 | wall | 1.8714 | 1.7003 | 0.9801 | 1.0996 | 2.6392 |
| grid2d_random_n4096_d32_p0 | cpu | 1.8711 | 1.7003 | 0.9803 | 1.0997 | 2.6395 |
| line_metric_n4096_d32_p0 | wall | 1.7516 | 1.7630 | 1.1614 | 0.5017 | 2.7494 |
| line_metric_n4096_d32_p0 | cpu | 1.7513 | 1.7627 | 1.1615 | 0.5016 | 2.7490 |
| line_random_n4096_d32_p0 | wall | 1.7743 | 2.0287 | 0.9526 | 1.0534 | 3.1674 |
| line_random_n4096_d32_p0 | cpu | 1.7746 | 2.0285 | 0.9527 | 1.0534 | 3.1677 |
| leaf_distance4_n4096_d32_p0 | wall | 1.6626 | 1.3283 | 1.2270 | 1.9434 | 2.4884 |
| leaf_distance4_n4096_d32_p0 | cpu | 1.6626 | 1.3284 | 1.2271 | 1.9434 | 2.4875 |
| leaf_shuffled4_n4096_d32_p0 | wall | 1.7454 | 1.6802 | 0.9434 | 2.0579 | 3.0345 |
| leaf_shuffled4_n4096_d32_p0 | cpu | 1.7455 | 1.6798 | 0.9433 | 2.0580 | 3.0330 |
| line_metric_n16384_d32_p0 | wall | 1.4702 | 1.7699 | 1.1495 | 0.3849 | 2.5640 |
| line_metric_n16384_d32_p0 | cpu | 1.4702 | 1.7699 | 1.1494 | 0.3849 | 2.5642 |
| line_random_n16384_d32_p0 | wall | 1.5878 | 1.8272 | 1.0075 | 0.9668 | 2.7728 |
| line_random_n16384_d32_p0 | cpu | 1.5878 | 1.8271 | 1.0075 | 0.9668 | 2.7726 |
| leaf_distance4_n16384_d32_p0 | wall | 1.3413 | 1.1895 | 1.1822 | 1.7418 | 2.1430 |
| leaf_distance4_n16384_d32_p0 | cpu | 1.3413 | 1.1896 | 1.1822 | 1.7418 | 2.1431 |
| leaf_shuffled4_n16384_d32_p0 | wall | 1.5406 | 1.9843 | 1.0212 | 1.9921 | 3.3521 |
| leaf_shuffled4_n16384_d32_p0 | cpu | 1.5406 | 1.9838 | 1.0212 | 1.9919 | 3.3518 |
| grid2d_metric_n16384_d32_p0 | wall | 1.4580 | 1.6905 | 1.0866 | 0.7678 | 2.4573 |
| grid2d_metric_n16384_d32_p0 | cpu | 1.4580 | 1.6905 | 1.0866 | 0.7678 | 2.4571 |
| grid2d_random_n16384_d32_p0 | wall | 1.5087 | 1.7933 | 0.9527 | 0.9118 | 2.6843 |
| grid2d_random_n16384_d32_p0 | cpu | 1.5083 | 1.7933 | 0.9524 | 0.9117 | 2.6843 |
| leaf_distance4_n65536_d32_p0 | wall | 0.8791 | 1.1811 | 1.3270 | 1.7650 | 1.7251 |
| leaf_distance4_n65536_d32_p0 | cpu | 0.8791 | 1.1811 | 1.3270 | 1.7650 | 1.7251 |
| leaf_shuffled4_n65536_d32_p0 | wall | 0.9431 | 1.7047 | 1.0779 | 1.9795 | 2.4532 |
| leaf_shuffled4_n65536_d32_p0 | cpu | 0.9431 | 1.7047 | 1.0779 | 1.9795 | 2.4531 |
| grid2d_metric_n65536_d32_p0 | wall | 0.9862 | 1.8366 | 1.2441 | 0.7122 | 2.2571 |
| grid2d_metric_n65536_d32_p0 | cpu | 0.9862 | 1.8366 | 1.2441 | 0.7125 | 2.2571 |
| grid2d_random_n65536_d32_p0 | wall | 0.9081 | 1.9056 | 1.0535 | 0.8608 | 2.4021 |
| grid2d_random_n65536_d32_p0 | cpu | 0.9081 | 1.9056 | 1.0535 | 0.8608 | 2.4020 |
| line_metric_n65536_d32_p0 | wall | 0.9548 | 1.7559 | 1.3119 | 0.3633 | 2.1538 |
| line_metric_n65536_d32_p0 | cpu | 0.9548 | 1.7559 | 1.3119 | 0.3634 | 2.1538 |
| line_random_n65536_d32_p0 | wall | 0.9221 | 1.7583 | 1.0141 | 0.8442 | 2.2624 |
| line_random_n65536_d32_p0 | cpu | 0.9221 | 1.7583 | 1.0140 | 0.8442 | 2.2624 |
| grid2d_metric_n262144_d32_p0 | wall | 0.4651 | 1.5028 | 1.3082 | 0.6870 | 1.6980 |
| grid2d_metric_n262144_d32_p0 | cpu | 0.4651 | 1.5028 | 1.3082 | 0.6870 | 1.6980 |
| grid2d_random_n262144_d32_p0 | wall | 0.4621 | 1.8389 | 1.1829 | 0.8414 | 2.0879 |
| grid2d_random_n262144_d32_p0 | cpu | 0.4621 | 1.8389 | 1.1829 | 0.8414 | 2.0879 |
| line_metric_n262144_d32_p0 | wall | 0.4585 | 1.7035 | 1.3190 | 0.3195 | 1.8840 |
| line_metric_n262144_d32_p0 | cpu | 0.4585 | 1.7035 | 1.3190 | 0.3195 | 1.8840 |
| line_random_n262144_d32_p0 | wall | 0.4688 | 1.6523 | 1.2003 | 0.8446 | 1.8839 |
| line_random_n262144_d32_p0 | cpu | 0.4688 | 1.6523 | 1.2003 | 0.8446 | 1.8839 |
| leaf_distance4_n262144_d32_p0 | wall | 0.4376 | 1.0652 | 1.3701 | 1.5144 | 1.4187 |
| leaf_distance4_n262144_d32_p0 | cpu | 0.4376 | 1.0652 | 1.3701 | 1.5144 | 1.4187 |
| leaf_shuffled4_n262144_d32_p0 | wall | 0.4497 | 1.9756 | 1.1853 | 1.8898 | 2.4631 |
| leaf_shuffled4_n262144_d32_p0 | cpu | 0.4497 | 1.9756 | 1.1854 | 1.8898 | 2.4631 |
| line_metric_n1048576_d32_p0 | wall | 0.3581 | 1.6387 | 1.5460 | 0.1723 | 1.2717 |
| line_metric_n1048576_d32_p0 | cpu | 0.3581 | 1.6387 | 1.5460 | 0.1723 | 1.2717 |
| line_random_n1048576_d32_p0 | wall | 0.3600 | 1.5402 | 1.3380 | 0.5389 | 1.4166 |
| line_random_n1048576_d32_p0 | cpu | 0.3600 | 1.5402 | 1.3380 | 0.5389 | 1.4166 |
| leaf_distance4_n1048576_d32_p0 | wall | 0.3307 | 0.9960 | 1.5426 | 1.3348 | 1.0336 |
| leaf_distance4_n1048576_d32_p0 | cpu | 0.3307 | 0.9959 | 1.5426 | 1.3348 | 1.0336 |
| leaf_shuffled4_n1048576_d32_p0 | wall | 0.3433 | 1.5772 | 1.3238 | 1.5920 | 1.5550 |
| leaf_shuffled4_n1048576_d32_p0 | cpu | 0.3433 | 1.5772 | 1.3238 | 1.5920 | 1.5550 |
| grid2d_metric_n1048576_d32_p0 | wall | 0.3691 | 1.4106 | 1.4791 | 0.4405 | 1.1762 |
| grid2d_metric_n1048576_d32_p0 | cpu | 0.3691 | 1.4106 | 1.4791 | 0.4405 | 1.1762 |
| grid2d_random_n1048576_d32_p0 | wall | 0.3589 | 1.5645 | 1.3327 | 0.5553 | 1.4406 |
| grid2d_random_n1048576_d32_p0 | cpu | 0.3589 | 1.5645 | 1.3327 | 0.5553 | 1.4406 |

Ratios below one favor KKT. Every trial pair, all five comparisons, both graph-seed medians, absolute runtimes, warmups, clock diagnostics and resource observations remain in the adjacent CSV tables. This campaign uses the exact frozen compressed binary with fresh graph/sampling seeds and six existing graph families. The n=1024 attachment core is nearly complete despite constant average core degree 250; large cores occupy a smaller fraction of possible pairs. Finite measurements do not prove asymptotic dominance.

Evaluate every earlier/later measured size pair with exact rational graph medians. All four graph/clock medians must exceed one at the lower endpoint, be at most 0.90 at the upper endpoint, and remain at most 0.90 at every larger measured size. Keep all 450 endpoint pairs, all 180 point classifications and 30 family/comparator summaries. No monotonicity or interpolation assumption.

crossover_points.csv retains all sizes; crossover_brackets.csv retains every earlier/later endpoint pair. The primary bracket selects the earliest qualifying upper endpoint and then the closest measured loss below it. Earlier wins/reversals are not hidden. A win against multigraph Boruvka is not a win against Prim or original Boruvka. Rank values need not satisfy metric inequalities. Six repetitions reuse each of two graph/sampling realizations; a single sampler seed does not establish robustness across sampled forests.
