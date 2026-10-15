# Eighth-only hierarchy/shuffled screen with frozen eighth-sampling KKT

All 1176 solver outputs passed exact MST validation: 1008 timed calls and 168 checked warmups. Each algorithm occupies every timed position once per child. This is a fresh, separately declared two-graph-seed campaign; historical timing is not pooled.

Prospectively test the existing leaf_hierarchy4/leaf_shuffled4 twins at all seven declared sizes and density32, using the exact frozen eighth-sampling candidate with compressed verifier queries and unchanged five controls. The declaration did not inspect the paired eighth study's results. Twins preserve topology, IDs, labels, physical order and cheap leaves; core weights change. The largest input exactly reaches the existing n and m limits. No domain or resource-ceiling relaxation, new generator or historical pooling. This single-binary study cannot estimate the effect of changing sampling probability.

Compare KKT directly with all five competitors in the same child, graph seed, sampling seed and repetition. Pool all twelve paired trial ratios per case and retain each graph's six-trial median. No historical timing is pooled, normalized or replaced. Graph/trial ranges are descriptive, not confidence intervals.

All 0 clock-flagged calls and 0 capture/child UTC flags remain included. Wall and CPU clocks are separate; neither flags nor power events change the observations. RSS is a sampled process-group sum, not a continuous peak. Power-audit status: `archived_log_correlated`; verified sleep inhibition is not claimed.

| Case | Clock | KKT / compacting Boruvka | KKT / multigraph Boruvka | KKT / Kruskal | KKT / Prim | KKT / original Boruvka |
|---|---|---:|---:|---:|---:|---:|
| leaf_hierarchy4_n1024_d32_p0 | wall | 1.3856 | 0.9179 | 0.7980 | 1.8618 | 1.6937 |
| leaf_hierarchy4_n1024_d32_p0 | cpu | 1.3865 | 0.9195 | 0.7974 | 1.8576 | 1.6904 |
| leaf_shuffled4_n1024_d32_p0 | wall | 1.5474 | 1.3398 | 0.7332 | 1.6865 | 2.3556 |
| leaf_shuffled4_n1024_d32_p0 | cpu | 1.5459 | 1.3392 | 0.7354 | 1.6862 | 2.3548 |
| leaf_hierarchy4_n4096_d32_p0 | wall | 0.9819 | 0.7730 | 0.7224 | 1.5539 | 1.4628 |
| leaf_hierarchy4_n4096_d32_p0 | cpu | 0.9832 | 0.7727 | 0.7225 | 1.5576 | 1.4616 |
| leaf_shuffled4_n4096_d32_p0 | wall | 1.2130 | 1.3444 | 0.6568 | 1.4382 | 2.3389 |
| leaf_shuffled4_n4096_d32_p0 | cpu | 1.2150 | 1.3441 | 0.6575 | 1.4389 | 2.3383 |
| leaf_hierarchy4_n16384_d32_p0 | wall | 0.7973 | 0.6956 | 0.6906 | 1.3785 | 1.2679 |
| leaf_hierarchy4_n16384_d32_p0 | cpu | 0.7973 | 0.6955 | 0.6906 | 1.3783 | 1.2685 |
| leaf_shuffled4_n16384_d32_p0 | wall | 0.9822 | 1.1752 | 0.6405 | 1.2450 | 2.0618 |
| leaf_shuffled4_n16384_d32_p0 | cpu | 0.9820 | 1.1757 | 0.6404 | 1.2453 | 2.0613 |
| leaf_hierarchy4_n65536_d32_p0 | wall | 0.5959 | 0.7750 | 0.8834 | 1.6044 | 1.1512 |
| leaf_hierarchy4_n65536_d32_p0 | cpu | 0.5959 | 0.7750 | 0.8834 | 1.6045 | 1.1511 |
| leaf_shuffled4_n65536_d32_p0 | wall | 0.6233 | 1.3116 | 0.7344 | 1.3402 | 1.8998 |
| leaf_shuffled4_n65536_d32_p0 | cpu | 0.6232 | 1.3117 | 0.7344 | 1.3403 | 1.8996 |
| leaf_hierarchy4_n262144_d32_p0 | wall | 0.2943 | 0.7124 | 0.9470 | 1.4496 | 0.9592 |
| leaf_hierarchy4_n262144_d32_p0 | cpu | 0.2943 | 0.7124 | 0.9470 | 1.4496 | 0.9592 |
| leaf_shuffled4_n262144_d32_p0 | wall | 0.3431 | 1.2340 | 0.8861 | 1.3764 | 1.5967 |
| leaf_shuffled4_n262144_d32_p0 | cpu | 0.3432 | 1.2340 | 0.8861 | 1.3764 | 1.5967 |
| leaf_hierarchy4_n1048576_d32_p0 | wall | 0.2238 | 0.6713 | 1.0254 | 1.2579 | 0.7330 |
| leaf_hierarchy4_n1048576_d32_p0 | cpu | 0.2238 | 0.6713 | 1.0252 | 1.2579 | 0.7330 |
| leaf_shuffled4_n1048576_d32_p0 | wall | 0.2412 | 1.1571 | 0.9063 | 1.1140 | 1.1960 |
| leaf_shuffled4_n1048576_d32_p0 | cpu | 0.2412 | 1.1571 | 0.9063 | 1.1140 | 1.1960 |
| leaf_hierarchy4_n4194304_d32_p0 | wall | 0.2960 | 0.8414 | 1.6616 | 1.2638 | 0.7379 |
| leaf_hierarchy4_n4194304_d32_p0 | cpu | 0.2969 | 0.8413 | 1.6618 | 1.2640 | 0.7379 |
| leaf_shuffled4_n4194304_d32_p0 | wall | 0.3222 | 1.2482 | 1.4461 | 0.9182 | 0.9734 |
| leaf_shuffled4_n4194304_d32_p0 | cpu | 0.3222 | 1.2481 | 1.4453 | 0.9185 | 0.9734 |

Ratios below one favor KKT. Every trial pair, all five comparisons, both graph-seed medians, absolute runtimes, warmups, clock diagnostics and resource observations remain in the adjacent CSV tables. This separately declared campaign uses the exact frozen eighth binary, two weight twins, seven sizes and fresh seeds. The largest n=4194304,d=32 input exactly reaches the existing n/m limits; no domain or RSS-ceiling relaxation was made. Finite measurements do not prove asymptotic dominance.

Evaluate every earlier/later measured size pair with exact rational graph medians. All four graph/clock medians must exceed one at the lower endpoint, be at most 0.90 at the upper endpoint, and remain at most 0.90 at every larger measured size. Keep all 210 endpoint pairs, all 70 point classifications and 10 family/comparator summaries. No monotonicity or interpolation assumption.

crossover_points.csv retains all sizes; crossover_brackets.csv retains every earlier/later endpoint pair. The primary bracket selects the earliest qualifying upper endpoint and then the closest measured loss below it. Earlier wins/reversals are not hidden. A win against multigraph Boruvka is not a win against Prim or original Boruvka. A lead only at the largest point has no measured persistence beyond it. Six repetitions reuse each of two graph/sampling realizations; a single sampler seed does not establish robustness across sampled forests.
