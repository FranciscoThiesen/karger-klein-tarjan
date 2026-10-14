# Five-solver capture

Strict validation passed for 25 cases, 1 graph seeds and 1 sampling seeds: 625 timed calls and 125 retained warmup calls. Each child has 5 timed repetitions and 1 warmups per algorithm.

All five positions are balanced within each timed seed pair. Every native reference has an independent MST certificate; every returned result must match that exact unique MST. Warmups are validated and retained, but excluded from timing summaries.

Ratios below one favor KKT. Each ratio is paired within the same graph, sampling seed and repetition, then aggregated by median over repetitions, sampling seeds and graphs in that order. Runtime summaries apply the same hierarchy separately to each algorithm; a ratio of those summaries is a different statistic. Graph and individual-trial ranges are descriptive spreads, not confidence intervals. Sampling seeds repeat identical inputs for deterministic competitors; they are not additional graph samples.

`compacting_boruvka` repeatedly uses production contraction; `boruvka` is the original public baseline. No other campaign is mixed into these comparisons, and no finite result establishes asymptotic dominance.

0 calls carry diagnostic clock flags, and 0 capture/child UTC interval flags are retained in provenance; all calls remain in every relevant table. Wall and process-CPU results are separate. Resource observations are periodic sums of process-group RSS in KiB, not continuous peaks or unique physical footprints. Polling itself can perturb measurements; the same rule is applied throughout this campaign.

| Case | Metric | KKT / compacting Borůvka | KKT / Kruskal | KKT / Prim | KKT / original Borůvka |
|---|---|---:|---:|---:|---:|
| distance_tree_n262144_d16_p0 | wall | 0.9412 | 2.5421 | 0.8734 | 1.8183 |
| distance_tree_n262144_d16_p0 | cpu | 0.9412 | 2.5422 | 0.8734 | 1.8183 |
| distance_tree_n262144_d64_p0 | wall | 0.8724 | 3.4834 | 2.4510 | 3.6916 |
| distance_tree_n262144_d64_p0 | cpu | 0.8724 | 3.4835 | 2.4509 | 3.6916 |
| distance_tree_n65536_d128_p0 | wall | 0.9548 | 2.4857 | 2.9888 | 3.6736 |
| distance_tree_n65536_d128_p0 | cpu | 0.9548 | 2.4857 | 2.9888 | 3.6736 |
| hierarchical_tree_n65536_d512_p0 | wall | 0.9913 | 3.0227 | 9.6608 | 5.2012 |
| hierarchical_tree_n65536_d512_p0 | cpu | 0.9913 | 3.0227 | 9.6608 | 5.2011 |
| gnm_random_n262144_d128_p0 | wall | 1.0415 | 3.1464 | 4.6976 | 8.2317 |
| gnm_random_n262144_d128_p0 | cpu | 1.0415 | 3.1462 | 4.6974 | 8.2313 |
| distance_tree_n262144_d128_p0 | wall | 0.8817 | 3.6410 | 3.7393 | 4.3080 |
| distance_tree_n262144_d128_p0 | cpu | 0.8818 | 3.6410 | 3.7393 | 4.3081 |
| hierarchical_tree_n65536_d128_p0 | wall | 0.9684 | 2.5254 | 4.3275 | 3.7692 |
| hierarchical_tree_n65536_d128_p0 | cpu | 0.9684 | 2.5253 | 4.3274 | 3.7692 |
| hierarchical_tree_n262144_d16_p0 | wall | 0.9242 | 2.5843 | 1.2274 | 1.8128 |
| hierarchical_tree_n262144_d16_p0 | cpu | 0.9242 | 2.5843 | 1.2275 | 1.8128 |
| distance_tree_n65536_d16_p0 | wall | 1.1995 | 1.6739 | 0.6863 | 1.4764 |
| distance_tree_n65536_d16_p0 | cpu | 1.1995 | 1.6739 | 0.6863 | 1.4764 |
| distance_tree_n16384_d64_p0 | wall | 1.2542 | 1.2227 | 1.2075 | 2.3184 |
| distance_tree_n16384_d64_p0 | cpu | 1.2542 | 1.2226 | 1.2075 | 2.3184 |
| random_tree_n262144_d128_p0 | wall | 1.0319 | 3.1467 | 4.7787 | 8.1376 |
| random_tree_n262144_d128_p0 | cpu | 1.0319 | 3.1466 | 4.7787 | 8.1376 |
| distance_tree_n65536_d64_p0 | wall | 1.0325 | 1.9189 | 1.6312 | 2.5860 |
| distance_tree_n65536_d64_p0 | cpu | 1.0325 | 1.9189 | 1.6312 | 2.5860 |
| distance_tree_n16384_d16_p0 | wall | 1.2740 | 1.4497 | 0.6927 | 1.5973 |
| distance_tree_n16384_d16_p0 | cpu | 1.2740 | 1.4497 | 0.6928 | 1.5969 |
| hierarchical_tree_n262144_d64_p0 | wall | 0.8665 | 3.4424 | 3.4632 | 3.6752 |
| hierarchical_tree_n262144_d64_p0 | cpu | 0.8665 | 3.4424 | 3.4633 | 3.6770 |
| hierarchical_tree_n65536_d64_p0 | wall | 0.9989 | 1.9562 | 2.4412 | 2.6586 |
| hierarchical_tree_n65536_d64_p0 | cpu | 0.9989 | 1.9562 | 2.4412 | 2.6586 |
| distance_tree_n16384_d128_p0 | wall | 1.1865 | 1.3274 | 1.8747 | 2.9007 |
| distance_tree_n16384_d128_p0 | cpu | 1.1865 | 1.3274 | 1.8747 | 2.9007 |
| hierarchical_tree_n65536_d16_p0 | wall | 1.1854 | 1.7028 | 0.9552 | 1.4888 |
| hierarchical_tree_n65536_d16_p0 | cpu | 1.1854 | 1.7027 | 0.9552 | 1.4888 |
| hierarchical_tree_n16384_d512_p0 | wall | 1.0738 | 1.9129 | 6.8188 | 4.8091 |
| hierarchical_tree_n16384_d512_p0 | cpu | 1.0738 | 1.9129 | 6.8187 | 4.8091 |
| hierarchical_tree_n16384_d16_p0 | wall | 1.3109 | 1.4358 | 0.9304 | 1.5684 |
| hierarchical_tree_n16384_d16_p0 | cpu | 1.3104 | 1.4359 | 0.9302 | 1.5682 |
| random_tree_n65536_d512_p0 | wall | 1.0152 | 2.3643 | 7.4991 | 8.1192 |
| random_tree_n65536_d512_p0 | cpu | 1.0152 | 2.3643 | 7.4990 | 8.1192 |
| distance_tree_n65536_d512_p0 | wall | 1.0043 | 3.0379 | 7.5002 | 5.0689 |
| distance_tree_n65536_d512_p0 | cpu | 1.0043 | 3.0379 | 7.5001 | 5.0689 |
| hierarchical_tree_n16384_d64_p0 | wall | 1.2287 | 1.2360 | 1.7095 | 2.3010 |
| hierarchical_tree_n16384_d64_p0 | cpu | 1.2287 | 1.2360 | 1.7095 | 2.3010 |
| hierarchical_tree_n262144_d128_p0 | wall | 0.8878 | 3.6317 | 5.3360 | 4.3335 |
| hierarchical_tree_n262144_d128_p0 | cpu | 0.8878 | 3.6316 | 5.3360 | 4.3335 |
| hierarchical_tree_n16384_d128_p0 | wall | 1.1800 | 1.3127 | 2.6127 | 2.8703 |
| hierarchical_tree_n16384_d128_p0 | cpu | 1.1800 | 1.3127 | 2.6127 | 2.8702 |
| distance_tree_n16384_d512_p0 | wall | 1.0956 | 1.9951 | 5.6057 | 5.0533 |
| distance_tree_n16384_d512_p0 | cpu | 1.0956 | 1.9951 | 5.6056 | 5.0532 |

Every individual ratio, including losses, is in [paired_ratios.csv](paired_ratios.csv). [comparisons.csv](comparisons.csv) and [graph_comparisons.csv](graph_comparisons.csv) retain spreads and win/loss counts. [summary.csv](summary.csv) reports separate algorithm runtimes in nanoseconds. [validated_calls.csv](validated_calls.csv) includes warmups; [call_diagnostics.csv](call_diagnostics.csv) contains every clock flag. [resources.csv](resources.csv) reports sampled resource observations.

Raw capture: [density-timing.csv](../density-timing.csv). Exact raw/child/log/manifest hashes and the captured source/binary inventories are retained in [provenance.json](provenance.json).
