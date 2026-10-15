# Larger hierarchy/shuffled screen with frozen compressed KKT

All 504 solver outputs passed exact MST validation: 432 timed calls and 72 checked warmups. Each algorithm occupies every timed position once per child. This is a fresh, separately declared two-graph-seed campaign; historical timing is not pooled.

Test the existing leaf_hierarchy4/leaf_shuffled4 twins at all three declared sizes and density32, using the exact frozen compressed-query candidate and unchanged five controls. Twins preserve topology, IDs, labels, physical order and cheap leaves; core weights change. The largest input exactly reaches the existing n and m limits. No domain or resource-ceiling relaxation, new generator, historical pooling or change to the independent held-out study.

Compare KKT directly with all five competitors in the same child, graph seed, sampling seed and repetition. Pool all twelve paired trial ratios per case and retain each graph's six-trial median. No historical timing is pooled, normalized or replaced. Graph/trial ranges are descriptive, not confidence intervals.

All 0 clock-flagged calls and 0 capture/child UTC flags remain included. Wall and CPU clocks are separate; neither flags nor power events change the observations. RSS is a sampled process-group sum, not a continuous peak. Power-audit status: `archived_log_correlated`; verified sleep inhibition is not claimed.

| Case | Clock | KKT / compacting Boruvka | KKT / multigraph Boruvka | KKT / Kruskal | KKT / Prim | KKT / original Boruvka |
|---|---|---:|---:|---:|---:|---:|
| leaf_hierarchy4_n65536_d32_p0 | wall | 0.8077 | 1.1181 | 1.2702 | 2.2681 | 1.6442 |
| leaf_hierarchy4_n65536_d32_p0 | cpu | 0.8077 | 1.1181 | 1.2702 | 2.2681 | 1.6442 |
| leaf_shuffled4_n65536_d32_p0 | wall | 0.8607 | 1.7382 | 1.1059 | 1.9909 | 2.5197 |
| leaf_shuffled4_n65536_d32_p0 | cpu | 0.8607 | 1.7382 | 1.1059 | 1.9909 | 2.5197 |
| leaf_hierarchy4_n1048576_d32_p0 | wall | 0.3191 | 0.9674 | 1.5101 | 1.7631 | 1.0111 |
| leaf_hierarchy4_n1048576_d32_p0 | cpu | 0.3191 | 0.9674 | 1.5101 | 1.7630 | 1.0111 |
| leaf_shuffled4_n1048576_d32_p0 | wall | 0.3386 | 1.5199 | 1.3048 | 1.5310 | 1.5613 |
| leaf_shuffled4_n1048576_d32_p0 | cpu | 0.3386 | 1.5199 | 1.3047 | 1.5309 | 1.5612 |
| leaf_hierarchy4_n4194304_d32_p0 | wall | 0.3924 | 1.0786 | 2.1109 | 1.6817 | 0.8861 |
| leaf_hierarchy4_n4194304_d32_p0 | cpu | 0.3923 | 1.0784 | 2.1106 | 1.6816 | 0.8860 |
| leaf_shuffled4_n4194304_d32_p0 | wall | 0.3994 | 1.5337 | 1.6799 | 1.3598 | 1.2785 |
| leaf_shuffled4_n4194304_d32_p0 | cpu | 0.3991 | 1.5342 | 1.6796 | 1.3586 | 1.2778 |

Ratios below one favor KKT. Every trial pair, all five comparisons, both graph-seed medians, absolute runtimes, warmups, clock diagnostics and resource observations remain in the adjacent CSV tables. This separately declared campaign uses the exact frozen compressed binary, two weight twins, three sizes and fresh seeds. The largest n=4194304,d=32 input exactly reaches the existing n/m limits; no domain or RSS-ceiling relaxation was made. Finite measurements do not prove asymptotic dominance.

Evaluate every earlier/later measured size pair with exact rational graph medians. All four graph/clock medians must exceed one at the lower endpoint, be at most 0.90 at the upper endpoint, and remain at most 0.90 at every larger measured size. Keep all 30 endpoint pairs, all 30 point classifications and 10 family/comparator summaries. No monotonicity or interpolation assumption.

crossover_points.csv retains all sizes; crossover_brackets.csv retains every earlier/later endpoint pair. The primary bracket selects the earliest qualifying upper endpoint and then the closest measured loss below it. Earlier wins/reversals are not hidden. A win against multigraph Boruvka is not a win against Prim or original Boruvka. A lead only at the largest point has no measured persistence beyond it. Six repetitions reuse each of two graph/sampling realizations; a single sampler seed does not establish robustness across sampled forests.
