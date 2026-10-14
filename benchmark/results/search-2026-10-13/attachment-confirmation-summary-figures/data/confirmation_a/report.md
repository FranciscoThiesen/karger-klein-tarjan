# Five-solver capture

Strict validation passed for 12 cases, 3 graph seeds and 2 sampling seeds: 1800 timed calls and 360 retained warmup calls. Each child has 5 timed repetitions and 1 warmups per algorithm.

All five positions are balanced within each timed seed pair. Every native reference has an independent MST certificate; every returned result must match that exact unique MST. Warmups are validated and retained, but excluded from timing summaries.

Ratios below one favor KKT. Each ratio is paired within the same graph, sampling seed and repetition, then aggregated by median over repetitions, sampling seeds and graphs in that order. Runtime summaries apply the same hierarchy separately to each algorithm; a ratio of those summaries is a different statistic. Graph and individual-trial ranges are descriptive spreads, not confidence intervals. Sampling seeds repeat identical inputs for deterministic competitors; they are not additional graph samples.

`compacting_boruvka` repeatedly uses production contraction; `boruvka` is the original public baseline. No other campaign is mixed into these comparisons, and no finite result establishes asymptotic dominance.

0 calls carry diagnostic clock flags, and 0 capture/child UTC interval flags are retained in provenance; all calls remain in every relevant table. Wall and process-CPU results are separate. Resource observations are periodic sums of process-group RSS in KiB, not continuous peaks or unique physical footprints. Polling itself can perturb measurements; the same rule is applied throughout this campaign.

| Case | Metric | KKT / compacting Borůvka | KKT / Kruskal | KKT / Prim | KKT / original Borůvka |
|---|---|---:|---:|---:|---:|
| leaf_distance4_n1048576_d16_p0 | wall | 0.8416 | 3.6627 | 2.1825 | 1.9352 |
| leaf_distance4_n1048576_d16_p0 | cpu | 0.8416 | 3.6623 | 2.1825 | 1.9350 |
| leaf_hierarchy4_n262144_d16_p0 | wall | 0.9792 | 2.2918 | 2.4389 | 1.8898 |
| leaf_hierarchy4_n262144_d16_p0 | cpu | 0.9792 | 2.2919 | 2.4389 | 1.8897 |
| leaf_shuffled4_n2097152_d16_p0 | wall | 0.9833 | 3.8961 | 2.6801 | 2.8581 |
| leaf_shuffled4_n2097152_d16_p0 | cpu | 0.9833 | 3.8961 | 2.6801 | 2.8581 |
| leaf_distance4_n262144_d16_p0 | wall | 0.9876 | 2.3044 | 1.7506 | 1.8877 |
| leaf_distance4_n262144_d16_p0 | cpu | 0.9876 | 2.3044 | 1.7506 | 1.8877 |
| leaf_hierarchy4_n65536_d16_p0 | wall | 1.2102 | 1.4966 | 1.8569 | 1.5889 |
| leaf_hierarchy4_n65536_d16_p0 | cpu | 1.2101 | 1.4966 | 1.8569 | 1.5889 |
| leaf_hierarchy4_n524288_d16_p0 | wall | 0.8823 | 3.0182 | 2.9227 | 1.9803 |
| leaf_hierarchy4_n524288_d16_p0 | cpu | 0.8823 | 3.0181 | 2.9227 | 1.9804 |
| leaf_distance4_n2097152_d16_p0 | wall | 0.8122 | 4.0925 | 2.0858 | 1.7297 |
| leaf_distance4_n2097152_d16_p0 | cpu | 0.8122 | 4.0925 | 2.0858 | 1.7297 |
| leaf_random4_n2097152_d16_p0 | wall | 1.0359 | 3.3023 | 1.7551 | 2.6411 |
| leaf_random4_n2097152_d16_p0 | cpu | 1.0359 | 3.3023 | 1.7551 | 2.6411 |
| leaf_distance4_n524288_d16_p0 | wall | 0.8908 | 3.0630 | 2.1116 | 1.9849 |
| leaf_distance4_n524288_d16_p0 | cpu | 0.8908 | 3.0630 | 2.1116 | 1.9850 |
| leaf_hierarchy4_n1048576_d16_p0 | wall | 0.8355 | 3.6643 | 3.0134 | 1.9538 |
| leaf_hierarchy4_n1048576_d16_p0 | cpu | 0.8355 | 3.6643 | 3.0134 | 1.9538 |
| leaf_hierarchy4_n2097152_d16_p0 | wall | 0.8153 | 4.1311 | 2.7892 | 1.7361 |
| leaf_hierarchy4_n2097152_d16_p0 | cpu | 0.8153 | 4.1311 | 2.7891 | 1.7362 |
| leaf_distance4_n65536_d16_p0 | wall | 1.1978 | 1.4498 | 1.3159 | 1.5414 |
| leaf_distance4_n65536_d16_p0 | cpu | 1.1978 | 1.4498 | 1.3158 | 1.5414 |

Every individual ratio, including losses, is in [paired_ratios.csv](paired_ratios.csv). [comparisons.csv](comparisons.csv) and [graph_comparisons.csv](graph_comparisons.csv) retain spreads and win/loss counts. [summary.csv](summary.csv) reports separate algorithm runtimes in nanoseconds. [validated_calls.csv](validated_calls.csv) includes warmups; [call_diagnostics.csv](call_diagnostics.csv) contains every clock flag. [resources.csv](resources.csv) reports sampled resource observations.

Raw capture: [attachment-confirmation-a-timing.csv](../attachment-confirmation-a-timing.csv). Exact raw/child/log/manifest hashes and the captured source/binary inventories are retained in [provenance.json](provenance.json).
