# Packed-sampling untimed work diagnostics

All 48 declared children completed and produced 144 certified solver outputs. Every native result matched the independently certified MST exactly. All 48 owned groups were observed empty before continuation; strict reanalysis accepted the complete frozen matrix, fingerprints, resource evidence, raw files and build provenance.

The nine mocked collector test groups passed on attempt 01 before capture. No performance timing is reported here. Diagnostic durations and sampled RSS include generation, certification, all three solvers and replay overhead.

All 65 KKT fields are retained in `counter_difference_summary.csv` and every individual difference is in `paired_kkt_work.csv` (24 pairs × 65 fields = 1,560 rows). Each summary field records decreases, equality, increases, all difference ranges and all defined count-ratio ranges. Zero denominators remain explicit. Both comparator implementations have exactly equal counters and replay rounds across variants and sampler seeds for every fixed case/graph pair.

The table below gives medians of the four paired packed/scalar count ratios for each case. These are logical work counts, not speedups, instructions or bytes. The WorkStats boundary includes tuple-to-Edge input construction, the solver and temporary input destruction; certification, output checking and round replays are outside it.

| Case | Sampling edge visits | Verifier queries | Path-query visits | Initialized slots | Edge materializations |
|---|---:|---:|---:|---:|---:|
| gnm_random_n1048576_d16_p0 | 1.000351 | 1.000351 | 1.000351 | 1.000340 | 1.007386 |
| gnm_random_n4096_d16_p0 | 1.001728 | 1.001728 | 1.001728 | 1.001435 | 0.981273 |
| leaf_hierarchy4_n1048576_d32_p0 | 0.996996 | 0.996994 | 0.996994 | 0.997101 | 0.999967 |
| leaf_hierarchy4_n65536_d32_p0 | 1.001463 | 1.001468 | 1.001468 | 1.001477 | 0.999075 |
| leaf_shuffled4_n1048576_d32_p0 | 1.010041 | 1.010041 | 1.010041 | 1.009966 | 1.007384 |
| leaf_shuffled4_n65536_d32_p0 | 0.987090 | 0.987089 | 0.987089 | 0.987465 | 0.996903 |

The scalar sampler consumes exactly `sampling_edge_visits` engine words. For packed sampling, the existing aggregate counters only establish `ceil(M/32) <= W <= min(M, floor((M+31*C)/32))`, where M and C are that packed run’s sampled-input volume and call count. Candidate and reference volumes may differ. The next table retains the minimum lower bound and maximum upper bound over all four paired realizations in each case. It does not pretend that aggregate M/32 is an observed exact count.

| Case | Packed/scalar engine-word ratio: enclosing bounds |
|---|---:|
| gnm_random_n1048576_d16_p0 | [0.02995736, 0.03185511] |
| gnm_random_n4096_d16_p0 | [0.02760348, 0.03194399] |
| leaf_hierarchy4_n1048576_d32_p0 | [0.03101054, 0.03124149] |
| leaf_hierarchy4_n65536_d32_p0 | [0.03103616, 0.03240453] |
| leaf_shuffled4_n1048576_d32_p0 | [0.03015750, 0.03243477] |
| leaf_shuffled4_n65536_d32_p0 | [0.02763088, 0.03238691] |

Packed sampling changes which MT bits supply Bernoulli decisions, so samples and recursive work may change even with the same seed. These diagnostics measure that changed work for every declared realization; they do not isolate CPU cost per engine draw or establish asymptotic complexity. Logical materialization counters do not include implicit vector-growth relocation or allocator costs. Consult the separate paired timing analysis for runtime evidence.
