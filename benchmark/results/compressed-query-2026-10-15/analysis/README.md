# Paired compressed-query verifier experiment

All 1,008 solver outputs passed exact MST validation: 864 timed calls and 144 checked warmups. Every solver occupies every timed position once per child. Historical timings are not pooled.

Compress verifier endpoint-to-ancestor requests by lower vertex and ancestor depth. Scalar sampling, RNG stream, retained-edge contraction, direct-Edge queries and all seven non-verifier objects are fixed; only verifier.o changes. Reference and candidate should preserve exact results and the planned work identities. No reserve, sampler, unrelated lifetime or baseline changes, and no historical timing pooling.

Pair all six reference/compressed solver durations by case, graph seed, fixed sampling seed and repetition; compare KKT directly with all five controls within each variant. Case medians pool all twelve paired ratios; each of the two graph realizations uses six. The single sampling marginal equals the case median and is not an independent realization. Both clocks, all trials and losses remain included.

All 0 clock-flagged calls and 0 UTC flags remain included. RSS is a sampled process-group sum, not a continuous peak. Power audit: `archived_log_correlated`. Verified sleep inhibition is not claimed.

| Case | Clock | Compressed / reference KKT | Realization median minimum | Realization median maximum |
|---|---|---:|---:|---:|
| leaf_hierarchy4_n65536_d32_p0 | wall | 1.07489 | 1.07241 | 1.08096 |
| leaf_hierarchy4_n65536_d32_p0 | cpu | 1.07488 | 1.07239 | 1.08096 |
| leaf_shuffled4_n65536_d32_p0 | wall | 1.02609 | 1.02039 | 1.03367 |
| leaf_shuffled4_n65536_d32_p0 | cpu | 1.02611 | 1.02036 | 1.03367 |
| leaf_hierarchy4_n1048576_d32_p0 | wall | 0.88771 | 0.88755 | 0.88798 |
| leaf_hierarchy4_n1048576_d32_p0 | cpu | 0.88771 | 0.88755 | 0.88798 |
| leaf_shuffled4_n1048576_d32_p0 | wall | 0.85362 | 0.85106 | 0.85654 |
| leaf_shuffled4_n1048576_d32_p0 | cpu | 0.85362 | 0.85106 | 0.85652 |
| gnm_random_n4096_d16_p0 | wall | 1.03838 | 1.03254 | 1.06313 |
| gnm_random_n4096_d16_p0 | cpu | 1.03827 | 1.03260 | 1.06277 |
| gnm_random_n1048576_d16_p0 | wall | 0.91627 | 0.91560 | 0.91683 |
| gnm_random_n1048576_d16_p0 | cpu | 0.91626 | 0.91560 | 0.91683 |

Ratios below one favor compressed verifier queries. Each variant’s direct KKT comparisons with all five solvers, absolute runtimes, every paired trial, all realization, graph and sampling marginal medians and diagnostics remain in the CSV tables. The variant_pairs, variant_comparisons and realization_variant_comparisons tables include all six algorithms so unchanged-solver drift is visible alongside KKT improvement. Realization/trial ranges are descriptive, not confidence intervals; finite measurements do not establish asymptotic dominance.
