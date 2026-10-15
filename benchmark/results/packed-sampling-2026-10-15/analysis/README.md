# Paired private packed-sampling experiment

All 2,016 solver outputs passed exact MST validation: 1,728 timed calls and 288 checked warmups. Every solver occupies every timed position once per child. Historical timings are not pooled.

Consume all 32 bits of each mt19937 word only in private recursive sampling. Both binaries include the same callback refactor and retain-parallel/direct-Edge paths. Only packed kkt.o selects the new sampler. Public sampling is unchanged, but private seeded samples and recursive work differ; identical recursive counters are neither expected nor required. No reserve change, set-bit iteration or historical timing pooling.

Pair all six scalar/packed solver durations by case, graph seed, sampling seed and repetition; compare KKT directly with all five controls within each variant. Case medians pool 24 paired ratios; four graph/sampler realization medians use six each; graph and sampler marginal medians use twelve each. Both clocks, all trials and losses remain included.

All 0 clock-flagged calls and 0 UTC flags remain included. RSS is a sampled process-group sum, not a continuous peak. Power audit: `archived_log_correlated`. Verified sleep inhibition is not claimed.

| Case | Clock | Packed / scalar KKT | Realization median minimum | Realization median maximum |
|---|---|---:|---:|---:|
| leaf_hierarchy4_n65536_d32_p0 | wall | 0.87273 | 0.86747 | 0.88905 |
| leaf_hierarchy4_n65536_d32_p0 | cpu | 0.87273 | 0.86748 | 0.88903 |
| leaf_shuffled4_n65536_d32_p0 | wall | 0.86609 | 0.78140 | 0.87849 |
| leaf_shuffled4_n65536_d32_p0 | cpu | 0.86608 | 0.78139 | 0.87849 |
| leaf_hierarchy4_n1048576_d32_p0 | wall | 0.91897 | 0.91470 | 0.92093 |
| leaf_hierarchy4_n1048576_d32_p0 | cpu | 0.91896 | 0.91470 | 0.92093 |
| leaf_shuffled4_n1048576_d32_p0 | wall | 0.91383 | 0.89642 | 0.92253 |
| leaf_shuffled4_n1048576_d32_p0 | cpu | 0.91383 | 0.89641 | 0.92253 |
| gnm_random_n4096_d16_p0 | wall | 0.82286 | 0.80581 | 0.87209 |
| gnm_random_n4096_d16_p0 | cpu | 0.82297 | 0.80576 | 0.87194 |
| gnm_random_n1048576_d16_p0 | wall | 0.91338 | 0.89691 | 0.92034 |
| gnm_random_n1048576_d16_p0 | cpu | 0.91338 | 0.89691 | 0.92034 |

Ratios below one favor packed sampling. Each variant’s direct KKT comparisons with all five solvers, absolute runtimes, every paired trial, all realization, graph and sampling marginal medians and diagnostics remain in the CSV tables. The variant_pairs, variant_comparisons and realization_variant_comparisons tables include all six algorithms so unchanged-solver drift is visible alongside KKT improvement. Realization/trial ranges are descriptive, not confidence intervals; finite measurements do not establish asymptotic dominance.
