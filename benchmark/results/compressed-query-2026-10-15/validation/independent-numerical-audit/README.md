# Independent compressed-query numerical audit

PASS: 24 raw children, 1,008 outputs (864 timed and 144 warmup), 864 all-solver compressed/reference clock pairs and 1,440 within-variant KKT/comparator clock pairs. All 2,016 case, realization, graph-marginal and sampling-marginal medians, their ranges/counts/wins, and all 30 crossover classifications agree with strict analysis. All four topology twins, exact certificates, balanced schedule, clocks, raw/combined concatenation, resource records and empty-group evidence were rechecked. No collector code was imported. Ratios and crossover predicates use exact rational arithmetic.

| Case | Compressed / reference KKT | Reference KKT / multigraph B | Compressed KKT / multigraph B |
|---|---:|---:|---:|
| leaf_hierarchy4_n65536_d32_p0 | 1.074894 | 1.037734 | 1.116744 |
| leaf_shuffled4_n65536_d32_p0 | 1.026095 | 1.753435 | 1.755943 |
| leaf_hierarchy4_n1048576_d32_p0 | 0.887712 | 1.095476 | 0.970733 |
| leaf_shuffled4_n1048576_d32_p0 | 0.853624 | 1.897636 | 1.617073 |
| gnm_random_n4096_d16_p0 | 1.038379 | 1.799754 | 1.870049 |
| gnm_random_n1048576_d16_p0 | 0.916268 | 1.760441 | 1.599749 |

Table: pooled 12-trial wall ratios. CSVs retain both clocks, all six solvers, all five direct comparators, both graph-realization medians and the singleton sampling marginal. Six repetitions reuse each realization; two graph seeds share fixed scalar sampling seed 1801, so twelve timings are not twelve independent samples. The singleton sampling marginal equals the pooled case median. Both variants use the same scalar stream policy; equality of intermediate forests is not directly observed here. Unchanged controls are never used to normalize KKT.

Retained flags: 0 calls and 0 capture/child UTC flags.

Strong observed crossover brackets:

- reference: gnm_random, d=16, versus compacting_boruvka: (4,096, 1,048,576] vertices.
- compressed: gnm_random, d=16, versus compacting_boruvka: (4,096, 1,048,576] vertices.

Each bracket requires both graph-realization medians above one at the smaller measured endpoint and at most 0.90 at the larger endpoint on both clocks. These are exploratory observed endpoints, not interpolated thresholds or proof of durable/asymptotic dominance. Every loss, narrow/mixed result and lead at both endpoints remains in the tables.
