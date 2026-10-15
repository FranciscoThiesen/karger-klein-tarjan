# Independent six-solver numerical review

PASS: independently read all 20 native child CSVs and certificate markers, checking 840 outputs (720 timed, 120 warmup), six-position balance, input identities, hashes and exact combined-file order. No collector or aggregation code was imported. All 100 case medians and 200 graph medians agree with the strict analyzer. The 1,200 paired ratios and crossover predicates were computed using exact rational arithmetic.

| Case | KKT / compacting B | KKT / multigraph B | KKT / Kruskal | KKT / Prim | KKT / original B |
|---|---:|---:|---:|---:|---:|
| leaf_hierarchy4_n65536_d16_p0 | 1.021905 | 1.124284 | 1.302099 | 1.625472 | 1.373020 |
| leaf_hierarchy4_n262144_d16_p0 | 0.614223 | 1.109232 | 1.484506 | 1.585644 | 1.190123 |
| leaf_hierarchy4_n2097152_d16_p0 | 0.380843 | 1.120290 | 1.937960 | 1.343301 | 0.816095 |
| leaf_distance4_n65536_d16_p0 | 1.055389 | 1.194413 | 1.328429 | 1.225431 | 1.436557 |
| leaf_distance4_n262144_d16_p0 | 0.642794 | 1.153045 | 1.492672 | 1.145288 | 1.212485 |
| leaf_distance4_n2097152_d16_p0 | 0.388964 | 1.144479 | 1.959327 | 0.989312 | 0.824666 |
| gnm_random_n4096_d16_p0 | 1.756350 | 1.816982 | 1.082111 | 0.818601 | 2.280207 |
| gnm_random_n1048576_d16_p0 | 0.448103 | 1.724113 | 1.513211 | 0.466733 | 1.197256 |
| gnm_random_n4096_d128_p0 | 2.053337 | 2.028656 | 0.878281 | 1.889717 | 4.639959 |
| gnm_random_n262144_d128_p0 | 0.450514 | 2.279511 | 1.337333 | 2.040259 | 3.522941 |

The table shows pooled twelve-trial wall ratios. CPU medians, each graph's six-trial median, all trials and all losses remain in the CSVs.

Declared strong crossover results:

- gnm_random, d=16 versus compacting_boruvka: (4,096, 1,048,576] vertices.
- gnm_random, d=128 versus compacting_boruvka: (4,096, 262,144] vertices.
- leaf_distance4, d=16 versus compacting_boruvka: (65,536, 262,144] vertices.
- leaf_distance4, d=16 versus boruvka: (262,144, 2,097,152] vertices.
- leaf_hierarchy4, d=16 versus compacting_boruvka: (65,536, 262,144] vertices.
- leaf_hierarchy4, d=16 versus boruvka: (262,144, 2,097,152] vertices.

Every bracket requires both graph medians above one at its lower measured point, both at most 0.90 at its upper point on both clocks, and that same win condition at every larger tested size. These are measured brackets, not interpolated thresholds. All twenty family/density/comparator classifications are retained in `strong_crossover_brackets.csv`.
