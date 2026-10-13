# Unchanged KKT versus continued production contraction

Validated 384 timed calls across 24 manifest cases; 192 additional checked warmup calls are not timing rows.

KKT has a lower paired case median in **3/24** cases; all graph medians favor KKT in **3/24**. These are this run's descriptive results, not automatic confirmation of a selected hypothesis.

Every ratio divides matched call times first, then takes medians across repetitions, sampling seeds and graph seeds. Independent timing medians need not divide to the paired ratio. Graph ranges are not confidence intervals. Order-stratified summaries and every individual loss/tie are retained.

| Case | KKT / compaction [graph range] | KKT ms | Compaction ms | KKT losses / pairs |
|---|---:|---:|---:|---:|
| hierarchical_tree_n65536_d4_p0 | 1.4204 [1.4062, 1.4347] | 29.585 | 20.827 | 8/8 |
| hierarchical_tree_n16384_d64_p0 | 1.1731 [1.1603, 1.1859] | 71.597 | 61.028 | 8/8 |
| legacy_random_n65536_d128_p0 | 1.0357 [1.0347, 1.0367] | 1257.352 | 1214.535 | 7/8 |
| legacy_random_n16384_d4_p0 | 1.3517 [1.3485, 1.3550] | 3.924 | 2.903 | 8/8 |
| hierarchical_path_n65536_d4_p0 | 1.4171 [1.4160, 1.4182] | 30.374 | 21.435 | 8/8 |
| hierarchical_path_n65536_d64_p0 | 0.9348 [0.9218, 0.9478] | 602.861 | 645.067 | 1/8 |
| hierarchical_tree_n16384_d16_p0 | 1.2464 [1.2411, 1.2517] | 19.486 | 15.635 | 8/8 |
| random_path_n65536_d16_p0 | 1.3030 [1.2540, 1.3521] | 73.767 | 56.696 | 8/8 |
| legacy_random_n16384_d128_p0 | 0.9853 [0.9733, 0.9973] | 112.559 | 114.912 | 5/8 |
| legacy_random_n16384_d32_p0 | 1.2339 [1.2119, 1.2558] | 22.700 | 18.416 | 8/8 |
| random_tree_n16384_d16_p0 | 1.3086 [1.3071, 1.3100] | 12.400 | 9.477 | 8/8 |
| hierarchical_tree_n16384_d4_p0 | 1.5154 [1.5143, 1.5164] | 6.719 | 4.435 | 8/8 |
| low_path_n65536_d16_p0 | 1.2597 [1.2015, 1.3180] | 87.674 | 69.877 | 8/8 |
| random_tree_n65536_d16_p0 | 1.3169 [1.3124, 1.3214] | 73.231 | 55.660 | 8/8 |
| low_path_n16384_d16_p0 | 1.3571 [1.3491, 1.3651] | 15.996 | 11.793 | 8/8 |
| random_path_n16384_d16_p0 | 1.3093 [1.2971, 1.3215] | 12.459 | 9.517 | 8/8 |
| hierarchical_path_n16384_d64_p0 | 1.1912 [1.1908, 1.1916] | 73.285 | 61.527 | 8/8 |
| hierarchical_tree_n65536_d16_p0 | 1.1374 [1.1349, 1.1399] | 103.911 | 91.372 | 8/8 |
| hierarchical_tree_n65536_d64_p0 | 0.9286 [0.9170, 0.9402] | 587.766 | 633.610 | 0/8 |
| legacy_random_n65536_d4_p0 | 1.3361 [1.3302, 1.3420] | 18.873 | 14.125 | 8/8 |
| legacy_random_n65536_d32_p0 | 1.1608 [1.1391, 1.1825] | 179.646 | 155.082 | 8/8 |
| hierarchical_path_n16384_d16_p0 | 1.2036 [1.1442, 1.2630] | 20.189 | 17.048 | 7/8 |
| hierarchical_path_n16384_d4_p0 | 1.5312 [1.5104, 1.5521] | 6.755 | 4.412 | 8/8 |
| hierarchical_path_n65536_d16_p0 | 1.0894 [1.0720, 1.1068] | 107.445 | 98.916 | 7/8 |

![Every runtime case](runtime_ratios.png)

The comparison uses identical production contraction code and reserved ID-set output. It measures whole continuation strategies, including recursive/iterative storage lifetimes, RNG, sampling and verification. Engineered hierarchy, cheap-backbone and hierarchical-distance cases are stress tests, not representative application graphs. Globally randomized weight controls share topology/IDs/order only; their full weighted fingerprints are not required to match.

Timing and instrumented work are separate runs. Work means average sampling seeds within graphs, then graph seeds. The logical proxy sums mixed loop/table/storage/hash-API events, omitting allocator internals, collisions, deallocation and cache behavior; it is not CPU instructions.

Input hashes, exact manifest and ordered seed banks are recorded in analysis_inputs.json. Build/machine provenance comes from the accompanying runner metadata, not from timing CSV alone.
