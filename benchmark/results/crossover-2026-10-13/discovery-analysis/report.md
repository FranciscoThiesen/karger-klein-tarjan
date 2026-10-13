# Unchanged KKT versus continued production contraction

Validated 76 timed calls across 19 manifest cases; 38 additional checked warmup calls are not timing rows.

KKT has a lower paired case median in **9/19** cases; all graph medians favor KKT in **9/19**. These are this run's descriptive results, not automatic confirmation of a selected hypothesis.

Every ratio divides matched call times first, then takes medians across repetitions, sampling seeds and graph seeds. Independent timing medians need not divide to the paired ratio. Graph ranges are not confidence intervals. Order-stratified summaries and every individual loss/tie are retained.

| Case | KKT / compaction [graph range] | KKT ms | Compaction ms | KKT losses / pairs |
|---|---:|---:|---:|---:|
| line_random_n4194304_d16_p0 | 0.9746 [0.9746, 0.9746] | 19569.369 | 20080.079 | 0/2 |
| line_metric_n4194304_d16_p0 | 0.9078 [0.9078, 0.9078] | 21976.118 | 24206.865 | 0/2 |
| grid2d_metric_n4194304_d16_p0 | 0.9457 [0.9457, 0.9457] | 21066.345 | 22276.432 | 0/2 |
| gnm_random_n1048576_d16_p0 | 1.0132 [1.0132, 1.0132] | 3857.047 | 3807.139 | 2/2 |
| line_random_n1048576_d16_p0 | 1.0069 [1.0069, 1.0069] | 3766.116 | 3740.210 | 2/2 |
| grid2d_metric_n1048576_d16_p0 | 0.9552 [0.9552, 0.9552] | 4020.696 | 4209.166 | 0/2 |
| random_tree_n1048576_d16_p0 | 1.0107 [1.0107, 1.0107] | 3790.689 | 3750.591 | 2/2 |
| grid2d_random_n262144_d4_p0 | 1.2764 [1.2764, 1.2764] | 91.540 | 71.730 | 2/2 |
| line_random_n262144_d16_p0 | 1.1473 [1.1473, 1.1473] | 523.049 | 455.911 | 2/2 |
| line_metric_n262144_d16_p0 | 1.0541 [1.0541, 1.0541] | 595.520 | 565.017 | 2/2 |
| grid2d_random_n4194304_d16_p0 | 0.9817 [0.9817, 0.9817] | 20293.358 | 20671.129 | 0/2 |
| gnm_random_n262144_d16_p0 | 1.1518 [1.1518, 1.1518] | 530.289 | 460.418 | 2/2 |
| grid2d_random_n262144_d16_p0 | 1.0846 [1.0846, 1.0846] | 522.970 | 482.099 | 2/2 |
| grid2d_metric_n262144_d4_p0 | 1.3193 [1.3193, 1.3193] | 99.172 | 75.173 | 2/2 |
| line_metric_n1048576_d16_p0 | 0.9317 [0.9317, 0.9317] | 4190.771 | 4497.853 | 0/2 |
| hierarchical_path_n1048576_d16_p0 | 0.8122 [0.8122, 0.8122] | 4544.414 | 5595.234 | 0/2 |
| grid2d_random_n1048576_d16_p0 | 0.9969 [0.9969, 0.9969] | 3854.547 | 3867.162 | 1/2 |
| grid2d_metric_n262144_d16_p0 | 1.1122 [1.1122, 1.1122] | 576.964 | 518.800 | 2/2 |
| gnm_random_n4194304_d16_p0 | 0.9946 [0.9946, 0.9946] | 20287.118 | 20397.789 | 1/2 |

![Every runtime case](runtime_ratios.png)

The comparison uses identical production contraction code and reserved ID-set output. It measures whole continuation strategies, including recursive/iterative storage lifetimes, RNG, sampling and verification. Engineered hierarchy, cheap-backbone and hierarchical-distance cases are stress tests, not representative application graphs. Globally randomized weight controls share topology/IDs/order only; their full weighted fingerprints are not required to match.

Timing and instrumented work are separate runs. Work means average sampling seeds within graphs, then graph seeds. The logical proxy sums mixed loop/table/storage/hash-API events, omitting allocator internals, collisions, deallocation and cache behavior; it is not CPU instructions.

Input hashes, exact manifest and ordered seed banks are recorded in analysis_inputs.json. Build/machine provenance comes from the accompanying runner metadata, not from timing CSV alone.
