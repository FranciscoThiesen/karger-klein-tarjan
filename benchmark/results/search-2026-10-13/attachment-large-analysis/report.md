# Five-solver capture

Strict validation passed for 10 cases, 1 graph seeds and 1 sampling seeds: 250 timed calls and 50 retained warmup calls. Each child has 5 timed repetitions and 1 warmups per algorithm.

All five positions are balanced within each timed seed pair. Every native reference has an independent MST certificate; every returned result must match that exact unique MST. Warmups are validated and retained, but excluded from timing summaries.

Ratios below one favor KKT. Each ratio is paired within the same graph, sampling seed and repetition, then aggregated by median over repetitions, sampling seeds and graphs in that order. Runtime summaries apply the same hierarchy separately to each algorithm; a ratio of those summaries is a different statistic. Graph and individual-trial ranges are descriptive spreads, not confidence intervals. Sampling seeds repeat identical inputs for deterministic competitors; they are not additional graph samples.

`compacting_boruvka` repeatedly uses production contraction; `boruvka` is the original public baseline. No other campaign is mixed into these comparisons, and no finite result establishes asymptotic dominance.

2 calls carry diagnostic clock flags, and 0 capture/child UTC interval flags are retained in provenance; all calls remain in every relevant table. Wall and process-CPU results are separate. Resource observations are periodic sums of process-group RSS in KiB, not continuous peaks or unique physical footprints. Polling itself can perturb measurements; the same rule is applied throughout this campaign.

| Case | Metric | KKT / compacting Borůvka | KKT / Kruskal | KKT / Prim | KKT / original Borůvka |
|---|---|---:|---:|---:|---:|
| leaf_hierarchy4_n524288_d16_p0 | wall | 0.8751 | 3.9821 | 2.8476 | 2.1323 |
| leaf_hierarchy4_n524288_d16_p0 | cpu | 0.8750 | 3.9804 | 2.8474 | 2.1319 |
| leaf_shuffled4_n2097152_d16_p0 | wall | 0.9892 | 4.6720 | 1.8352 | 2.4026 |
| leaf_shuffled4_n2097152_d16_p0 | cpu | 0.9889 | 4.6706 | 1.8353 | 2.3890 |
| leaf_random4_n2097152_d16_p0 | wall | 1.0190 | 3.6006 | 1.1105 | 2.1610 |
| leaf_random4_n2097152_d16_p0 | cpu | 1.0183 | 3.6011 | 1.1111 | 2.1600 |
| leaf_random4_n4194304_d16_p0 | wall | 1.0447 | 3.6249 | 1.2439 | 2.2050 |
| leaf_random4_n4194304_d16_p0 | cpu | 1.0447 | 3.6244 | 1.2438 | 2.2050 |
| leaf_shuffled4_n4194304_d16_p0 | wall | 0.9913 | 4.4554 | 2.3024 | 2.4909 |
| leaf_shuffled4_n4194304_d16_p0 | cpu | 0.9913 | 4.4547 | 2.3020 | 2.4909 |
| leaf_distance4_n4194304_d16_p0 | wall | 0.8302 | 4.7103 | 1.9181 | 1.4900 |
| leaf_distance4_n4194304_d16_p0 | cpu | 0.8300 | 4.7098 | 1.9179 | 1.4897 |
| leaf_distance4_n2097152_d16_p0 | wall | 0.8082 | 4.3166 | 2.0678 | 1.7307 |
| leaf_distance4_n2097152_d16_p0 | cpu | 0.8082 | 4.3167 | 2.0678 | 1.7307 |
| leaf_hierarchy4_n4194304_d16_p0 | wall | 0.8251 | 4.7739 | 2.3814 | 1.4849 |
| leaf_hierarchy4_n4194304_d16_p0 | cpu | 0.8250 | 4.7713 | 2.3802 | 1.4849 |
| leaf_hierarchy4_n2097152_d16_p0 | wall | 0.8134 | 4.2378 | 2.9120 | 1.7972 |
| leaf_hierarchy4_n2097152_d16_p0 | cpu | 0.8141 | 4.2377 | 2.9119 | 1.7972 |
| leaf_distance4_n524288_d16_p0 | wall | 0.8885 | 3.1511 | 2.1085 | 2.0259 |
| leaf_distance4_n524288_d16_p0 | cpu | 0.8885 | 3.1511 | 2.1085 | 2.0259 |

Every individual ratio, including losses, is in [paired_ratios.csv](paired_ratios.csv). [comparisons.csv](comparisons.csv) and [graph_comparisons.csv](graph_comparisons.csv) retain spreads and win/loss counts. [summary.csv](summary.csv) reports separate algorithm runtimes in nanoseconds. [validated_calls.csv](validated_calls.csv) includes warmups; [call_diagnostics.csv](call_diagnostics.csv) contains every clock flag. [resources.csv](resources.csv) reports sampled resource observations.

Raw capture: [attachment-large-timing.csv](../attachment-large-timing.csv). Exact raw/child/log/manifest hashes and the captured source/binary inventories are retained in [provenance.json](provenance.json).
