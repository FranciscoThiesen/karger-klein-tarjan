# Paired KKT multigraph-contraction screen

All 1,200 native outputs passed exact MST validation: 1,000 timed calls and 200 retained warmups. This is a fresh two-graph-seed screen; it does not reuse historical timing samples.

Ratios below one favor the multigraph build. Each pair shares graph, starting KKT seed and repetition. Variant case summaries take the median of all ten trial ratios; each graph has its own five-trial median. Ranges are not confidence intervals. Internal sampling trajectories can differ. Unchanged competitors are retained as controls, never used to normalize timings.

All 0 flagged calls and 0 capture/child UTC flags remain included. Wall and process CPU clocks are separate. RSS is a periodic process-group sum, not a continuous peak. Power audit status: `archived_log_correlated`; sleep inhibition is not asserted.

| Case | Clock | Candidate KKT / reference KKT | Graph median range |
|---|---|---:|---:|
| leaf_hierarchy4_n65536_d16_p0 | wall | 0.8920 | 0.8885–0.8955 |
| leaf_hierarchy4_n65536_d16_p0 | cpu | 0.8920 | 0.8885–0.8955 |
| leaf_hierarchy4_n1048576_d16_p0 | wall | 0.4794 | 0.4675–0.4865 |
| leaf_hierarchy4_n1048576_d16_p0 | cpu | 0.4794 | 0.4675–0.4865 |
| leaf_distance4_n65536_d16_p0 | wall | 0.9247 | 0.9152–0.9285 |
| leaf_distance4_n65536_d16_p0 | cpu | 0.9247 | 0.9152–0.9285 |
| leaf_distance4_n1048576_d16_p0 | wall | 0.4816 | 0.4759–0.4873 |
| leaf_distance4_n1048576_d16_p0 | cpu | 0.4816 | 0.4759–0.4873 |
| leaf_shuffled4_n262144_d16_p0 | wall | 0.5898 | 0.5730–0.5904 |
| leaf_shuffled4_n262144_d16_p0 | cpu | 0.5898 | 0.5730–0.5905 |
| leaf_random4_n262144_d16_p0 | wall | 0.6555 | 0.5942–0.7027 |
| leaf_random4_n262144_d16_p0 | cpu | 0.6555 | 0.5942–0.7027 |
| lifted_hierarchy4_n262144_d64_p0 | wall | 0.8676 | 0.8567–0.8725 |
| lifted_hierarchy4_n262144_d64_p0 | cpu | 0.8676 | 0.8567–0.8725 |
| lifted_random4_n262144_d64_p0 | wall | 0.4597 | 0.4555–0.4673 |
| lifted_random4_n262144_d64_p0 | cpu | 0.4597 | 0.4555–0.4673 |
| gnm_random_n65536_d128_p0 | wall | 0.5678 | 0.5662–0.5681 |
| gnm_random_n65536_d128_p0 | cpu | 0.5678 | 0.5662–0.5681 |
| gnm_random_n262144_d16_p0 | wall | 0.6224 | 0.6170–0.6233 |
| gnm_random_n262144_d16_p0 | cpu | 0.6224 | 0.6170–0.6233 |

All five same-algorithm variant comparisons are in `variant_comparisons.csv`; the complete trial pairs are in `variant_pairs.csv`. Each variant's KKT versus all four MST competitors is retained in its `reference/` or `multigraph/` tables; these separately labeled tables keep the original median-over-repetitions, then sampling-seeds, then graph-seeds aggregation. No finite pilot establishes asymptotic dominance or justifies selecting only favorable families.
