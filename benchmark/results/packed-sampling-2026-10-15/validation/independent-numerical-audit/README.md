# Independent packed-sampling numerical audit

PASS: 48 raw children, 2,016 outputs (1,728 timed and 288 warmup), 1,728 all-solver packed/scalar clock pairs and 2,880 within-variant KKT/comparator clock pairs. All 3,024 case, realization, graph-marginal and sampling-marginal medians, their ranges/counts/wins, and all 30 crossover classifications agree with strict analysis. All four topology twins, exact certificates, balanced schedule, clocks, raw/combined concatenation, resource records and empty-group evidence were rechecked. No collector code was imported. Ratios and crossover predicates use exact rational arithmetic.

| Case | Packed / scalar KKT | Scalar KKT / multigraph B | Packed KKT / multigraph B |
|---|---:|---:|---:|
| leaf_hierarchy4_n65536_d32_p0 | 0.872729 | 1.027910 | 0.895701 |
| leaf_shuffled4_n65536_d32_p0 | 0.866087 | 1.720006 | 1.459575 |
| leaf_hierarchy4_n1048576_d32_p0 | 0.918966 | 1.093530 | 1.004827 |
| leaf_shuffled4_n1048576_d32_p0 | 0.913831 | 1.823223 | 1.704134 |
| gnm_random_n4096_d16_p0 | 0.822856 | 1.625585 | 1.333819 |
| gnm_random_n1048576_d16_p0 | 0.913378 | 1.709488 | 1.555317 |

Table: pooled 24-trial wall ratios. CSVs retain both clocks, all six solvers, all five direct comparators, all four realization medians and both marginal dimensions. Six repetitions reuse each realization; two graph seeds cross two sampler seeds, so there are not four independent graphs or 24 independent samples. Private scalar/packed streams differ despite matching initial seed numbers. Unchanged controls are never used to normalize KKT.

Retained flags: 0 calls and 0 capture/child UTC flags.

Strong observed crossover brackets:

- scalar: gnm_random, d=16, versus compacting_boruvka: (4,096, 1,048,576] vertices.
- packed: gnm_random, d=16, versus compacting_boruvka: (4,096, 1,048,576] vertices.

Each bracket requires all four realization medians above one at the smaller measured endpoint and at most 0.90 at the larger endpoint on both clocks. These are exploratory observed endpoints, not interpolated thresholds or proof of durable/asymptotic dominance. Every loss, narrow/mixed result and lead at both endpoints remains in the tables.
