# Paired Edge-view verifier experiment

All 1,680 solver outputs passed exact MST validation: 1,440 timed calls and 240 checked warmups. Every solver occupies every timed position once per child. Historical timings are not pooled.

Remove the verifier input tuple materialization only. Both binaries use the refactored verifier, identical shared production objects and the unchanged six-solver driver; only kkt.o dispatches through the Edge-view macro. Historical control timings are not pooled or used as the refactored tuple baseline.

Edge/tuple ratios pair each of all six algorithms by graph seed, sampling seed and repetition across adjacent children, retaining unchanged-solver drift alongside KKT gain. Each variant also compares KKT directly against all five competitors in its own child. Case medians pool all twelve paired ratios; graph medians use six. Both clocks, all trials and losses remain included.

All 0 clock-flagged calls and 0 UTC flags remain included. RSS is a sampled process-group sum, not a continuous peak. Power audit: `archived_log_correlated`. Verified sleep inhibition is not claimed.

| Case | Clock | Edge / tuple KKT | Graph median minimum | Graph median maximum |
|---|---|---:|---:|---:|
| leaf_hierarchy4_n65536_d16_p0 | wall | 0.96113 | 0.95770 | 0.96398 |
| leaf_hierarchy4_n65536_d16_p0 | cpu | 0.96113 | 0.95771 | 0.96398 |
| leaf_hierarchy4_n262144_d16_p0 | wall | 0.95255 | 0.94859 | 0.95579 |
| leaf_hierarchy4_n262144_d16_p0 | cpu | 0.95255 | 0.94858 | 0.95580 |
| leaf_hierarchy4_n2097152_d16_p0 | wall | 0.96584 | 0.96584 | 0.96851 |
| leaf_hierarchy4_n2097152_d16_p0 | cpu | 0.96584 | 0.96584 | 0.96851 |
| leaf_distance4_n65536_d16_p0 | wall | 0.94476 | 0.94278 | 0.94673 |
| leaf_distance4_n65536_d16_p0 | cpu | 0.94475 | 0.94275 | 0.94675 |
| leaf_distance4_n262144_d16_p0 | wall | 0.95250 | 0.94781 | 0.95871 |
| leaf_distance4_n262144_d16_p0 | cpu | 0.95251 | 0.94781 | 0.95871 |
| leaf_distance4_n2097152_d16_p0 | wall | 0.97065 | 0.96685 | 1.01374 |
| leaf_distance4_n2097152_d16_p0 | cpu | 0.97065 | 0.96684 | 1.01374 |
| gnm_random_n4096_d16_p0 | wall | 0.94848 | 0.94629 | 0.97434 |
| gnm_random_n4096_d16_p0 | cpu | 0.94843 | 0.94613 | 0.97450 |
| gnm_random_n1048576_d16_p0 | wall | 0.95589 | 0.95108 | 0.95964 |
| gnm_random_n1048576_d16_p0 | cpu | 0.95589 | 0.95108 | 0.95964 |
| gnm_random_n4096_d128_p0 | wall | 0.93209 | 0.92919 | 0.93309 |
| gnm_random_n4096_d128_p0 | cpu | 0.93210 | 0.92921 | 0.93307 |
| gnm_random_n262144_d128_p0 | wall | 0.94944 | 0.94625 | 0.94944 |
| gnm_random_n262144_d128_p0 | cpu | 0.94944 | 0.94625 | 0.94944 |

Ratios below one favor the Edge path. Each variant’s direct KKT comparisons with all five solvers, absolute runtimes, every paired trial, all graph medians and diagnostics remain in the CSV tables. The variant_pairs, variant_comparisons and graph_variant_comparisons tables include all six algorithms so unchanged-solver drift is visible alongside KKT improvement. Graph/trial ranges are descriptive, not confidence intervals; finite measurements do not establish asymptotic dominance.
