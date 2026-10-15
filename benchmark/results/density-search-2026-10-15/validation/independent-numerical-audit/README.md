# Independent density-search numerical review

PASS: independently read all 16 native child CSVs and certificate markers, checking 672 outputs (576 timed, 96 warmup), six-position balance, input identities, eight nonvacuous topology-matched weight-control pairs, hashes and exact combined-file order. No collector or aggregation code was imported. All 80 case medians and 160 graph medians agree with the strict analyzer. The 960 paired ratios and crossover predicates were computed using exact rational arithmetic.

| Case | KKT / compacting B | KKT / multigraph B | KKT / Kruskal | KKT / Prim | KKT / original B |
|---|---:|---:|---:|---:|---:|
| leaf_hierarchy4_n65536_d32_p0 | 0.823989 | 1.054751 | 1.147438 | 2.106405 | 1.547248 |
| leaf_shuffled4_n65536_d32_p0 | 0.968206 | 1.853431 | 1.061728 | 1.921041 | 2.624092 |
| leaf_hierarchy4_n1048576_d32_p0 | 0.367231 | 1.093749 | 1.685783 | 2.052176 | 1.210631 |
| leaf_shuffled4_n1048576_d32_p0 | 0.406396 | 1.736701 | 1.501914 | 1.822371 | 1.865293 |
| leaf_hierarchy4_n65536_d64_p0 | 0.679270 | 1.041730 | 1.097625 | 2.823957 | 1.703609 |
| leaf_shuffled4_n65536_d64_p0 | 0.754320 | 1.839718 | 0.997049 | 2.594223 | 2.960857 |
| leaf_hierarchy4_n1048576_d64_p0 | 0.372421 | 1.119768 | 1.670527 | 2.867724 | 1.473753 |
| leaf_shuffled4_n1048576_d64_p0 | 0.408544 | 1.885822 | 1.489711 | 2.577762 | 2.412153 |

The table shows pooled twelve-trial wall ratios. CPU medians, each graph's six-trial median, all trials and all losses remain in the CSVs.

Declared strong crossover results:

No declared strong observed crossover bracket was found.

Every bracket requires both graph medians above one at its lower measured point, both at most 0.90 at its upper point on both clocks, and that same win condition at every larger tested size. These are measured brackets, not interpolated thresholds. All twenty family/density/comparator classifications are retained in `strong_crossover_brackets.csv`. Two endpoint sizes provide exploratory brackets, not evidence of a durable crossover; held-out/intermediate-size confirmation is separate.
