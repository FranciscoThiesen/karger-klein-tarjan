# Lower-density distance/shuffled screen with frozen eighth-sampling KKT

All 2520 solver outputs passed exact MST validation: 2160 timed calls and 360 checked warmups. Each algorithm occupies every timed position once per child. This is a fresh, separately declared two-graph-seed campaign; historical timing is not pooled.

Prospectively test the existing leaf_distance4/leaf_shuffled4 twins at the seven fixed density16 sizes and eight fixed density8 sizes, using the exact frozen eighth-sampling candidate with compressed verifier queries and unchanged five controls. The completed density32 study motivates these fixed lower-density ladders; no historical timing is pooled. Twins preserve topology, IDs, labels, physical order and cheap leaves; core edge ranks change from dyadic ancestry ordering to shuffled ordering. Rank weights need not satisfy the triangle inequality; these are engineered constructions, not an application prevalence claim. No native domain or memory-ceiling relaxation or new generator. Densities remain separate in all comparisons and crossover classifications. This single-binary study cannot estimate the effect of changing sampling probability.

Compare KKT directly with all five competitors in the same child, graph seed, sampling seed and repetition. Pool all twelve paired trial ratios per case and retain each graph's six-trial median. No historical timing is pooled, normalized or replaced. Graph/trial ranges are descriptive, not confidence intervals.

All 0 clock-flagged calls and 0 capture/child UTC flags remain included. Wall and CPU clocks are separate; neither flags nor power events change the observations. RSS is a sampled process-group sum, not a continuous peak. Power-audit status: `archived_log_correlated`; verified sleep inhibition is not claimed.

| Case | Clock | KKT / compacting Boruvka | KKT / multigraph Boruvka | KKT / Kruskal | KKT / Prim | KKT / original Boruvka |
|---|---|---:|---:|---:|---:|---:|
| leaf_distance4_n512_d16_p0 | wall | 1.6656 | 1.1423 | 1.1341 | 1.3164 | 1.7280 |
| leaf_distance4_n512_d16_p0 | cpu | 1.6639 | 1.1437 | 1.1374 | 1.3201 | 1.7237 |
| leaf_shuffled4_n512_d16_p0 | wall | 1.7007 | 1.5297 | 0.9316 | 1.4477 | 2.0906 |
| leaf_shuffled4_n512_d16_p0 | cpu | 1.7011 | 1.5283 | 0.9305 | 1.4418 | 2.0825 |
| leaf_distance4_n2048_d16_p0 | wall | 1.1416 | 0.9402 | 0.9046 | 1.0920 | 1.4037 |
| leaf_distance4_n2048_d16_p0 | cpu | 1.1412 | 0.9403 | 0.9044 | 1.0920 | 1.4044 |
| leaf_shuffled4_n2048_d16_p0 | wall | 1.3438 | 1.5163 | 0.7934 | 1.2425 | 2.0039 |
| leaf_shuffled4_n2048_d16_p0 | cpu | 1.3436 | 1.5168 | 0.7940 | 1.2414 | 2.0016 |
| leaf_distance4_n8192_d16_p0 | wall | 0.9295 | 0.8205 | 0.8252 | 0.9422 | 1.2145 |
| leaf_distance4_n8192_d16_p0 | cpu | 0.9296 | 0.8205 | 0.8251 | 0.9420 | 1.2147 |
| leaf_shuffled4_n8192_d16_p0 | wall | 1.0964 | 1.2481 | 0.7133 | 1.0760 | 1.7479 |
| leaf_shuffled4_n8192_d16_p0 | cpu | 1.0963 | 1.2472 | 0.7138 | 1.0759 | 1.7474 |
| leaf_distance4_n32768_d16_p0 | wall | 0.8329 | 0.7982 | 0.8916 | 0.8385 | 1.0778 |
| leaf_distance4_n32768_d16_p0 | cpu | 0.8329 | 0.7982 | 0.8916 | 0.8385 | 1.0778 |
| leaf_shuffled4_n32768_d16_p0 | wall | 0.9421 | 1.2578 | 0.7235 | 0.9802 | 1.5538 |
| leaf_shuffled4_n32768_d16_p0 | cpu | 0.9420 | 1.2578 | 0.7235 | 0.9802 | 1.5538 |
| leaf_distance4_n131072_d16_p0 | wall | 0.6077 | 0.8116 | 1.0093 | 0.8470 | 0.9563 |
| leaf_distance4_n131072_d16_p0 | cpu | 0.6077 | 0.8116 | 1.0093 | 0.8470 | 0.9563 |
| leaf_shuffled4_n131072_d16_p0 | wall | 0.7238 | 1.3057 | 0.9011 | 1.0618 | 1.4929 |
| leaf_shuffled4_n131072_d16_p0 | cpu | 0.7238 | 1.3057 | 0.9012 | 1.0618 | 1.4929 |
| leaf_distance4_n524288_d16_p0 | wall | 0.2996 | 0.7283 | 1.0500 | 0.7259 | 0.6820 |
| leaf_distance4_n524288_d16_p0 | cpu | 0.2996 | 0.7283 | 1.0500 | 0.7259 | 0.6820 |
| leaf_shuffled4_n524288_d16_p0 | wall | 0.3434 | 1.2115 | 0.9618 | 0.9429 | 1.1034 |
| leaf_shuffled4_n524288_d16_p0 | cpu | 0.3434 | 1.2115 | 0.9618 | 0.9429 | 1.1034 |
| leaf_distance4_n2097152_d16_p0 | wall | 0.2425 | 0.7088 | 1.2152 | 0.6281 | 0.5299 |
| leaf_distance4_n2097152_d16_p0 | cpu | 0.2425 | 0.7088 | 1.2152 | 0.6281 | 0.5299 |
| leaf_shuffled4_n2097152_d16_p0 | wall | 0.2729 | 1.1219 | 1.0815 | 0.7431 | 0.8186 |
| leaf_shuffled4_n2097152_d16_p0 | cpu | 0.2729 | 1.1219 | 1.0815 | 0.7431 | 0.8186 |
| leaf_distance4_n256_d8_p0 | wall | 2.1287 | 1.6169 | 2.3155 | 1.3477 | 1.8017 |
| leaf_distance4_n256_d8_p0 | cpu | 2.1129 | 1.5971 | 2.2704 | 1.3420 | 1.8133 |
| leaf_shuffled4_n256_d8_p0 | wall | 1.7957 | 1.7733 | 1.7181 | 1.2816 | 1.6649 |
| leaf_shuffled4_n256_d8_p0 | cpu | 1.8069 | 1.7672 | 1.7030 | 1.2871 | 1.6764 |
| leaf_distance4_n1024_d8_p0 | wall | 1.4429 | 1.2729 | 1.3689 | 0.9652 | 1.3702 |
| leaf_distance4_n1024_d8_p0 | cpu | 1.4428 | 1.2719 | 1.3698 | 0.9666 | 1.3689 |
| leaf_shuffled4_n1024_d8_p0 | wall | 1.4886 | 1.5656 | 1.0544 | 0.9803 | 1.4641 |
| leaf_shuffled4_n1024_d8_p0 | cpu | 1.4928 | 1.5669 | 1.0546 | 0.9816 | 1.4598 |
| leaf_distance4_n4096_d8_p0 | wall | 1.1603 | 1.0507 | 1.1106 | 0.8585 | 1.1458 |
| leaf_distance4_n4096_d8_p0 | cpu | 1.1600 | 1.0506 | 1.1104 | 0.8585 | 1.1458 |
| leaf_shuffled4_n4096_d8_p0 | wall | 1.2245 | 1.2580 | 0.8821 | 0.9033 | 1.2640 |
| leaf_shuffled4_n4096_d8_p0 | cpu | 1.2246 | 1.2586 | 0.8823 | 0.9036 | 1.2637 |
| leaf_distance4_n16384_d8_p0 | wall | 0.9662 | 0.9448 | 1.0390 | 0.7284 | 0.9716 |
| leaf_distance4_n16384_d8_p0 | cpu | 0.9662 | 0.9449 | 1.0389 | 0.7284 | 0.9716 |
| leaf_shuffled4_n16384_d8_p0 | wall | 1.0624 | 1.3340 | 0.8258 | 0.7790 | 1.2535 |
| leaf_shuffled4_n16384_d8_p0 | cpu | 1.0624 | 1.3338 | 0.8259 | 0.7789 | 1.2535 |
| leaf_distance4_n65536_d8_p0 | wall | 0.9062 | 0.9574 | 1.1233 | 0.6995 | 0.8871 |
| leaf_distance4_n65536_d8_p0 | cpu | 0.9062 | 0.9574 | 1.1233 | 0.6995 | 0.8871 |
| leaf_shuffled4_n65536_d8_p0 | wall | 0.9884 | 1.2607 | 0.8958 | 0.7640 | 1.1275 |
| leaf_shuffled4_n65536_d8_p0 | cpu | 0.9883 | 1.2608 | 0.8958 | 0.7639 | 1.1275 |
| leaf_distance4_n262144_d8_p0 | wall | 0.6258 | 0.8961 | 1.1833 | 0.6128 | 0.7358 |
| leaf_distance4_n262144_d8_p0 | cpu | 0.6258 | 0.8961 | 1.1833 | 0.6128 | 0.7358 |
| leaf_shuffled4_n262144_d8_p0 | wall | 0.7232 | 1.2594 | 0.9995 | 0.7183 | 1.0032 |
| leaf_shuffled4_n262144_d8_p0 | cpu | 0.7232 | 1.2595 | 0.9995 | 0.7183 | 1.0032 |
| leaf_distance4_n1048576_d8_p0 | wall | 0.3509 | 0.8341 | 1.2874 | 0.5218 | 0.4621 |
| leaf_distance4_n1048576_d8_p0 | cpu | 0.3509 | 0.8341 | 1.2874 | 0.5218 | 0.4621 |
| leaf_shuffled4_n1048576_d8_p0 | wall | 0.3588 | 1.2280 | 1.0440 | 0.5791 | 0.6770 |
| leaf_shuffled4_n1048576_d8_p0 | cpu | 0.3588 | 1.2280 | 1.0440 | 0.5791 | 0.6770 |
| leaf_distance4_n4194304_d8_p0 | wall | 0.3509 | 0.9726 | 1.8485 | 0.5267 | 0.4484 |
| leaf_distance4_n4194304_d8_p0 | cpu | 0.3509 | 0.9726 | 1.8485 | 0.5267 | 0.4484 |
| leaf_shuffled4_n4194304_d8_p0 | wall | 0.3199 | 1.1558 | 1.3355 | 0.5253 | 0.5419 |
| leaf_shuffled4_n4194304_d8_p0 | cpu | 0.3199 | 1.1558 | 1.3355 | 0.5253 | 0.5419 |

Ratios below one favor KKT. Every trial pair, all five comparisons, both graph-seed medians, absolute runtimes, warmups, clock diagnostics and resource observations remain in the adjacent CSV tables. This separately declared campaign uses the exact frozen eighth binary, two weight twins, seven density16 sizes, eight density8 sizes and fresh seeds. The largest inputs n=2097152,d=16 and n=4194304,d=8 each have m=33554432; no domain or RSS-ceiling relaxation was made. Finite measurements do not prove asymptotic dominance.

Within each family/density/comparator evaluate every earlier/later measured size pair with exact rational graph medians. All four graph/clock medians must exceed one at the lower endpoint, be at most 0.90 at the upper endpoint, and remain at most 0.90 at every larger measured size in that density ladder. Keep all 490 endpoint pairs, all 150 point classifications and 20 family/density/comparator summaries. No monotonicity, interpolation or cross-density pooling.

crossover_points.csv retains all sizes; crossover_brackets.csv retains every earlier/later endpoint pair. The primary bracket selects the earliest qualifying upper endpoint and then the closest measured loss below it. Earlier wins/reversals are not hidden. A win against multigraph Boruvka is not a win against Prim or original Boruvka. A lead only at the largest point has no measured persistence beyond it. Six repetitions reuse each of two graph/sampling realizations; a single sampler seed does not establish robustness across sampled forests.
