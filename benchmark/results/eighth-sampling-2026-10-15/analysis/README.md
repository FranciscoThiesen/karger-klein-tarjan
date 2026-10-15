# Eighth sampling with compressed verifier queries fixed

All 2,016 solver outputs passed exact MST validation: 1,728 timed calls and 288 checked warmups. Every solver occupies every timed position once per child. Historical timings are not pooled.

Test private scalar sampling with acceptance mask 7 instead of mask 1, with compressed verifier queries fixed in both fresh variants. The same compressed verifier object, six other non-KKT objects and harness object are shared. Only eighth kkt.o selects EIGHTH_SAMPLING; both variants contain the same pure-predicate refactor. Public sampling remains the legacy scalar half stream. Both policies draw once per edge and reserve m/2. Private samples and recursive work differ; identical cumulative counters across rates are neither expected nor required. No packed sampling, set-bit iteration, reserve change or historical timing pooling. Smaller samples can weaken filtering; no speedup is assumed.

Pair all six half/eighth solver durations by case, graph seed, sampling seed and repetition; compare KKT directly with all five controls within each variant. Case medians pool 24 paired ratios; four graph/sampler realization medians use six each; graph and sampler marginal medians use twelve each. Both clocks, all trials and losses remain included.

For each variant/family/control, all four graph/sampler realization medians on both clocks must exceed one at the smaller endpoint and be at most 9/10 at the larger endpoint. Medians and thresholds are reconstructed as exact Fractions of integer endpoints. Keep all 30 classifications, including narrow leads, mixed outcomes and reversals. Two endpoints do not establish persistence beyond the measured larger size or an asymptotic crossover.

All 0 clock-flagged calls and 0 UTC flags remain included. RSS is a sampled process-group sum, not a continuous peak. Power audit: `archived_log_correlated`. Verified sleep inhibition is not claimed.

| Case | Clock | Eighth / half KKT | Realization median minimum | Realization median maximum |
|---|---|---:|---:|---:|
| leaf_hierarchy4_n65536_d32_p0 | wall | 0.70977 | 0.69499 | 0.71926 |
| leaf_hierarchy4_n65536_d32_p0 | cpu | 0.70977 | 0.69500 | 0.71927 |
| leaf_shuffled4_n65536_d32_p0 | wall | 0.68019 | 0.67261 | 0.68443 |
| leaf_shuffled4_n65536_d32_p0 | cpu | 0.68020 | 0.67261 | 0.68444 |
| leaf_hierarchy4_n1048576_d32_p0 | wall | 0.69269 | 0.68574 | 0.70214 |
| leaf_hierarchy4_n1048576_d32_p0 | cpu | 0.69270 | 0.68574 | 0.70214 |
| leaf_shuffled4_n1048576_d32_p0 | wall | 0.71311 | 0.69063 | 0.72391 |
| leaf_shuffled4_n1048576_d32_p0 | cpu | 0.71311 | 0.69063 | 0.72391 |
| gnm_random_n4096_d16_p0 | wall | 0.75383 | 0.73169 | 0.81339 |
| gnm_random_n4096_d16_p0 | cpu | 0.75380 | 0.73178 | 0.81333 |
| gnm_random_n1048576_d16_p0 | wall | 0.74988 | 0.74114 | 0.75537 |
| gnm_random_n1048576_d16_p0 | cpu | 0.74988 | 0.74114 | 0.75536 |

Ratios below one favor eighth sampling. Each variant’s direct KKT comparisons with all five solvers, absolute runtimes, every paired trial, all realization, graph and sampling marginal medians and diagnostics remain in the CSV tables. The variant_pairs, variant_comparisons and realization_variant_comparisons tables include all six algorithms so unchanged-solver drift is visible alongside KKT improvement. Realization/trial ranges are descriptive, not confidence intervals; finite measurements do not establish asymptotic dominance.
