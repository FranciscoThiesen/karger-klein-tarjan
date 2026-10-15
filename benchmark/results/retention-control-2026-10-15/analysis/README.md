# Six-solver retained-edge Boruvka control

All 840 solver outputs passed exact MST validation: 720 timed calls and 120 checked warmups. Each algorithm occupies every timed position once per child. This is a fresh, separately declared two-graph-seed campaign; historical timing is not pooled.

Multigraph Boruvka uses the same retained-parallel contraction as candidate KKT; this separates repeated retained-edge contraction from KKT's sampling/filtering continuation. It is a whole-strategy comparison, not isolated phase timing.

Compare KKT with all five competitors within the same graph, starting KKT seed and repetition. Case median uses all twelve paired ratios; each graph also has its own six-trial median. No historical observations are pooled. Graph/trial ranges are descriptive, not confidence intervals.

All 0 clock-flagged calls and 0 capture/child UTC flags remain included. Wall and CPU clocks are separate; neither flags nor power events change the observations. RSS is a sampled process-group sum, not a continuous peak. Power-audit status: `archived_log_correlated`; verified sleep inhibition is not claimed.

| Case | Clock | KKT / compacting Boruvka | KKT / multigraph Boruvka | KKT / Kruskal | KKT / Prim | KKT / original Boruvka |
|---|---|---:|---:|---:|---:|---:|
| leaf_hierarchy4_n65536_d16_p0 | wall | 1.0219 | 1.1243 | 1.3021 | 1.6255 | 1.3730 |
| leaf_hierarchy4_n65536_d16_p0 | cpu | 1.0219 | 1.1243 | 1.3021 | 1.6254 | 1.3730 |
| leaf_hierarchy4_n262144_d16_p0 | wall | 0.6142 | 1.1092 | 1.4845 | 1.5856 | 1.1901 |
| leaf_hierarchy4_n262144_d16_p0 | cpu | 0.6143 | 1.1092 | 1.4845 | 1.5856 | 1.1901 |
| leaf_hierarchy4_n2097152_d16_p0 | wall | 0.3808 | 1.1203 | 1.9380 | 1.3433 | 0.8161 |
| leaf_hierarchy4_n2097152_d16_p0 | cpu | 0.3808 | 1.1203 | 1.9380 | 1.3433 | 0.8161 |
| leaf_distance4_n65536_d16_p0 | wall | 1.0554 | 1.1944 | 1.3284 | 1.2254 | 1.4366 |
| leaf_distance4_n65536_d16_p0 | cpu | 1.0554 | 1.1944 | 1.3284 | 1.2254 | 1.4365 |
| leaf_distance4_n262144_d16_p0 | wall | 0.6428 | 1.1530 | 1.4927 | 1.1453 | 1.2125 |
| leaf_distance4_n262144_d16_p0 | cpu | 0.6428 | 1.1530 | 1.4927 | 1.1453 | 1.2125 |
| leaf_distance4_n2097152_d16_p0 | wall | 0.3890 | 1.1445 | 1.9593 | 0.9893 | 0.8247 |
| leaf_distance4_n2097152_d16_p0 | cpu | 0.3890 | 1.1445 | 1.9593 | 0.9893 | 0.8247 |
| gnm_random_n4096_d16_p0 | wall | 1.7563 | 1.8170 | 1.0821 | 0.8186 | 2.2802 |
| gnm_random_n4096_d16_p0 | cpu | 1.7566 | 1.8172 | 1.0820 | 0.8184 | 2.2811 |
| gnm_random_n1048576_d16_p0 | wall | 0.4481 | 1.7241 | 1.5132 | 0.4667 | 1.1973 |
| gnm_random_n1048576_d16_p0 | cpu | 0.4481 | 1.7241 | 1.5132 | 0.4667 | 1.1973 |
| gnm_random_n4096_d128_p0 | wall | 2.0533 | 2.0287 | 0.8783 | 1.8897 | 4.6400 |
| gnm_random_n4096_d128_p0 | cpu | 2.0533 | 2.0286 | 0.8783 | 1.8897 | 4.6393 |
| gnm_random_n262144_d128_p0 | wall | 0.4505 | 2.2795 | 1.3373 | 2.0403 | 3.5229 |
| gnm_random_n262144_d128_p0 | cpu | 0.4505 | 2.2796 | 1.3373 | 2.0403 | 3.5228 |

Ratios below one favor KKT. Every trial pair, all five comparisons, both graph-seed medians, absolute runtimes, warmups, clock diagnostics and resource observations remain in the adjacent CSV tables. The code improvement versus reference KKT belongs to the separate earlier pilot; this campaign contains only candidate KKT and its five competitors. Finite measurements do not prove asymptotic dominance.
