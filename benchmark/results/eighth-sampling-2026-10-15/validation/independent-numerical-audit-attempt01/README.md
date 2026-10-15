# Independent eighth-sampling numerical audit

PASS: 48 raw children, 2,016 outputs (1,728 timed and 288 warmup), 1,728 all-solver eighth/half clock pairs and 2,880 within-variant KKT/comparator clock pairs. All 3,024 case, realization, graph-marginal and sampling-marginal medians, their ranges/counts/wins, and all 30 crossover classifications agree with strict analysis. All four topology twins, exact certificates, balanced schedule, clocks, raw/combined concatenation, resource records and empty-group evidence were rechecked. No collector code was imported. Ratios and crossover predicates use exact rational arithmetic.

| Case | Eighth / half KKT | Half KKT / multigraph B | Eighth KKT / multigraph B |
|---|---:|---:|---:|
| leaf_hierarchy4_n65536_d32_p0 | 0.709768 | 1.104719 | 0.789110 |
| leaf_shuffled4_n65536_d32_p0 | 0.680192 | 1.725856 | 1.179393 |
| leaf_hierarchy4_n1048576_d32_p0 | 0.692694 | 0.962035 | 0.664766 |
| leaf_shuffled4_n1048576_d32_p0 | 0.713110 | 1.563846 | 1.147221 |
| gnm_random_n4096_d16_p0 | 0.753829 | 1.705860 | 1.274798 |
| gnm_random_n1048576_d16_p0 | 0.749879 | 1.513275 | 1.138405 |

Table: pooled 24-trial wall ratios. CSVs retain both clocks, all six solvers, all five direct comparators, all four realization medians and both marginal dimensions. Six repetitions reuse each realization; two graph seeds cross two sampler seeds, so there are not four independent graphs or 24 independent samples. Both policies draw one word per visited edge, but changed acceptance and recursion can produce different later streams despite matching initial seed numbers. Compressed verification is fixed. Unchanged controls are never used to normalize KKT.

Retained flags: 0 calls and 0 capture/child UTC flags.

Strong observed crossover brackets:

- half: gnm_random, d=16, versus compacting_boruvka: (4,096, 1,048,576] vertices.
- eighth: gnm_random, d=16, versus compacting_boruvka: (4,096, 1,048,576] vertices.
- eighth: gnm_random, d=16, versus boruvka: (4,096, 1,048,576] vertices.
- eighth: leaf_hierarchy4, d=32, versus boruvka: (65,536, 1,048,576] vertices.

Each bracket requires all four realization medians above one at the smaller measured endpoint and at most 0.90 at the larger endpoint on both clocks. These are exploratory observed endpoints, not interpolated thresholds or proof of durable/asymptotic dominance. Every loss, narrow/mixed result and lead at both endpoints remains in the tables.
