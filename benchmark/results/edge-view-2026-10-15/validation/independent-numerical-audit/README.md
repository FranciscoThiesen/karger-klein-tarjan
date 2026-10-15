# Independent paired-six numerical review

PASS: read all 40 raw child CSVs, checking 1,680 outputs (1,440 timed, 240 warmup), six-position balance, adjacent/reversed variant schedule, exact input certificates, clock diagnostics and source/artifact hashes. No collector code was imported. All 1,440 Edge/tuple ratios and 2,400 within-variant KKT/comparator ratios, all 1,680 case/graph medians, ranges, counts and wins agree with strict analysis. Ratios and crossover predicates use exact rational arithmetic.

| Case | Edge / tuple KKT | Tuple KKT / multigraph B | Edge KKT / multigraph B |
|---|---:|---:|---:|
| leaf_hierarchy4_n65536_d16_p0 | 0.961134 | 1.116044 | 1.060483 |
| leaf_hierarchy4_n262144_d16_p0 | 0.952551 | 1.111552 | 1.059957 |
| leaf_hierarchy4_n2097152_d16_p0 | 0.965844 | 1.130493 | 1.093756 |
| leaf_distance4_n65536_d16_p0 | 0.944757 | 1.196773 | 1.132508 |
| leaf_distance4_n262144_d16_p0 | 0.952500 | 1.154320 | 1.092195 |
| leaf_distance4_n2097152_d16_p0 | 0.970652 | 1.145632 | 1.120311 |
| gnm_random_n4096_d16_p0 | 0.948475 | 1.786214 | 1.695823 |
| gnm_random_n1048576_d16_p0 | 0.955889 | 1.769989 | 1.692032 |
| gnm_random_n4096_d128_p0 | 0.932093 | 1.941034 | 1.809398 |
| gnm_random_n262144_d128_p0 | 0.949440 | 2.071799 | 1.974440 |

The table shows pooled twelve-trial wall ratios. Both clocks, every graph median, all six solvers’ cross-variant drift and both variants’ five direct KKT comparisons remain in the CSVs. Controls are never used to normalize KKT.

Clock flags retained: 0 call flags and 0 capture/child UTC flags.

Strong crossover brackets:

- tuple: gnm_random, d=16 versus compacting_boruvka: (4,096, 1,048,576] vertices.
- tuple: gnm_random, d=128 versus compacting_boruvka: (4,096, 262,144] vertices.
- tuple: leaf_distance4, d=16 versus compacting_boruvka: (65,536, 262,144] vertices.
- tuple: leaf_distance4, d=16 versus boruvka: (262,144, 2,097,152] vertices.
- tuple: leaf_hierarchy4, d=16 versus compacting_boruvka: (65,536, 262,144] vertices.
- tuple: leaf_hierarchy4, d=16 versus boruvka: (262,144, 2,097,152] vertices.
- edge: gnm_random, d=16 versus compacting_boruvka: (4,096, 1,048,576] vertices.
- edge: gnm_random, d=128 versus compacting_boruvka: (4,096, 262,144] vertices.
- edge: leaf_distance4, d=16 versus boruvka: (262,144, 2,097,152] vertices.
- edge: leaf_hierarchy4, d=16 versus boruvka: (262,144, 2,097,152] vertices.

Each bracket requires both graph medians above one at its lower measured size, at most 0.90 at its upper size on both clocks, and the same strong win at every still-larger tested size. Brackets are measured endpoints, not interpolated thresholds. All forty classifications, losses and inconclusive results remain available.
