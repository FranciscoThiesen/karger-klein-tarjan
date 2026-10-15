# Eighth-only distance/shuffled screen with frozen eighth-sampling KKT

All 1008 solver outputs passed exact MST validation: 864 timed calls and 144 checked warmups. Each algorithm occupies every timed position once per child. This is a fresh, separately declared two-graph-seed campaign; historical timing is not pooled.

Prospectively test the existing leaf_distance4/leaf_shuffled4 twins at all six declared sizes and density32, using the exact frozen eighth-sampling candidate with compressed verifier queries and unchanged five controls. Completed half-policy held-out data motivate this known family; no historical timing is pooled. Twins preserve topology, IDs, labels, physical order and cheap leaves; all core edge ranks change from dyadic ancestry ordering to shuffled ordering. Rank weights need not satisfy the triangle inequality; these are engineered constructions, not an application prevalence claim. No domain or resource-ceiling relaxation or new generator. This single-binary study cannot estimate the effect of changing sampling probability.

Compare KKT directly with all five competitors in the same child, graph seed, sampling seed and repetition. Pool all twelve paired trial ratios per case and retain each graph's six-trial median. No historical timing is pooled, normalized or replaced. Graph/trial ranges are descriptive, not confidence intervals.

All 0 clock-flagged calls and 0 capture/child UTC flags remain included. Wall and CPU clocks are separate; neither flags nor power events change the observations. RSS is a sampled process-group sum, not a continuous peak. Power-audit status: `archived_log_correlated`; verified sleep inhibition is not claimed.

| Case | Clock | KKT / compacting Boruvka | KKT / multigraph Boruvka | KKT / Kruskal | KKT / Prim | KKT / original Boruvka |
|---|---|---:|---:|---:|---:|---:|
| leaf_distance4_n1024_d32_p0 | wall | 1.3835 | 0.9377 | 0.8071 | 1.4347 | 1.7107 |
| leaf_distance4_n1024_d32_p0 | cpu | 1.3840 | 0.9379 | 0.8078 | 1.4352 | 1.7097 |
| leaf_shuffled4_n1024_d32_p0 | wall | 1.6107 | 1.8472 | 0.7238 | 1.7042 | 3.1655 |
| leaf_shuffled4_n1024_d32_p0 | cpu | 1.6093 | 1.8460 | 0.7237 | 1.7023 | 3.1670 |
| leaf_distance4_n4096_d32_p0 | wall | 0.9985 | 0.7979 | 0.7312 | 1.1819 | 1.4993 |
| leaf_distance4_n4096_d32_p0 | cpu | 0.9986 | 0.7980 | 0.7313 | 1.1818 | 1.4993 |
| leaf_shuffled4_n4096_d32_p0 | wall | 1.1957 | 1.4184 | 0.6511 | 1.3730 | 2.5505 |
| leaf_shuffled4_n4096_d32_p0 | cpu | 1.1954 | 1.4183 | 0.6511 | 1.3727 | 2.5511 |
| leaf_distance4_n16384_d32_p0 | wall | 0.7979 | 0.7177 | 0.7011 | 1.0386 | 1.2889 |
| leaf_distance4_n16384_d32_p0 | cpu | 0.7979 | 0.7199 | 0.7012 | 1.0388 | 1.2889 |
| leaf_shuffled4_n16384_d32_p0 | wall | 0.9370 | 1.2765 | 0.6231 | 1.2236 | 2.1110 |
| leaf_shuffled4_n16384_d32_p0 | cpu | 0.9369 | 1.2765 | 0.6232 | 1.2235 | 2.1094 |
| leaf_distance4_n65536_d32_p0 | wall | 0.5830 | 0.7875 | 0.8608 | 1.1396 | 1.1468 |
| leaf_distance4_n65536_d32_p0 | cpu | 0.5830 | 0.7877 | 0.8607 | 1.1439 | 1.1468 |
| leaf_shuffled4_n65536_d32_p0 | wall | 0.5893 | 1.1774 | 0.7042 | 1.3096 | 1.6873 |
| leaf_shuffled4_n65536_d32_p0 | cpu | 0.5893 | 1.1774 | 0.7042 | 1.3096 | 1.6872 |
| leaf_distance4_n262144_d32_p0 | wall | 0.2832 | 0.7195 | 0.9113 | 1.0206 | 0.9350 |
| leaf_distance4_n262144_d32_p0 | cpu | 0.2825 | 0.7201 | 0.9100 | 1.0180 | 0.9350 |
| leaf_shuffled4_n262144_d32_p0 | wall | 0.3287 | 1.2135 | 0.8552 | 1.3585 | 1.5610 |
| leaf_shuffled4_n262144_d32_p0 | cpu | 0.3281 | 1.2143 | 0.8553 | 1.3559 | 1.5606 |
| leaf_distance4_n1048576_d32_p0 | wall | 0.2225 | 0.6807 | 1.0292 | 0.9081 | 0.7200 |
| leaf_distance4_n1048576_d32_p0 | cpu | 0.2224 | 0.6804 | 1.0313 | 0.9080 | 0.7199 |
| leaf_shuffled4_n1048576_d32_p0 | wall | 0.2417 | 1.1561 | 0.8940 | 1.1147 | 1.2150 |
| leaf_shuffled4_n1048576_d32_p0 | cpu | 0.2417 | 1.1561 | 0.8941 | 1.1147 | 1.2150 |

Ratios below one favor KKT. Every trial pair, all five comparisons, both graph-seed medians, absolute runtimes, warmups, clock diagnostics and resource observations remain in the adjacent CSV tables. This separately declared campaign uses the exact frozen eighth binary, two weight twins, six sizes and fresh seeds. The largest n=1048576,d=32 input stays inside the existing n/m limits; no domain or RSS-ceiling relaxation was made. Finite measurements do not prove asymptotic dominance.

Evaluate every earlier/later measured size pair with exact rational graph medians. All four graph/clock medians must exceed one at the lower endpoint, be at most 0.90 at the upper endpoint, and remain at most 0.90 at every larger measured size. Keep all 150 endpoint pairs, all 60 point classifications and 10 family/comparator summaries. No monotonicity or interpolation assumption.

crossover_points.csv retains all sizes; crossover_brackets.csv retains every earlier/later endpoint pair. The primary bracket selects the earliest qualifying upper endpoint and then the closest measured loss below it. Earlier wins/reversals are not hidden. A win against multigraph Boruvka is not a win against Prim or original Boruvka. A lead only at the largest point has no measured persistence beyond it. Six repetitions reuse each of two graph/sampling realizations; a single sampler seed does not establish robustness across sampled forests.
