# Five-solver capture

Strict validation passed for 16 cases, 1 graph seeds and 1 sampling seeds: 400 timed calls and 80 retained warmup calls. Each child has 5 timed repetitions and 1 warmups per algorithm.

All five positions are balanced within each timed seed pair. Every native reference has an independent MST certificate; every returned result must match that exact unique MST. Warmups are validated and retained, but excluded from timing summaries.

Ratios below one favor KKT. Each ratio is paired within the same graph, sampling seed and repetition, then aggregated by median over repetitions, sampling seeds and graphs in that order. Runtime summaries apply the same hierarchy separately to each algorithm; a ratio of those summaries is a different statistic. Graph and individual-trial ranges are descriptive spreads, not confidence intervals. Sampling seeds repeat identical inputs for deterministic competitors; they are not additional graph samples.

`compacting_boruvka` repeatedly uses production contraction; `boruvka` is the original public baseline. No other campaign is mixed into these comparisons, and no finite result establishes asymptotic dominance.

0 calls carry diagnostic clock flags, and 0 capture/child UTC interval flags are retained in provenance; all calls remain in every relevant table. Wall and process-CPU results are separate. Resource observations are periodic sums of process-group RSS in KiB, not continuous peaks or unique physical footprints. Polling itself can perturb measurements; the same rule is applied throughout this campaign.

| Case | Metric | KKT / compacting Borůvka | KKT / Kruskal | KKT / Prim | KKT / original Borůvka |
|---|---|---:|---:|---:|---:|
| leaf_hierarchy4_n1024_d2_p0 | wall | 2.3108 | 3.6563 | 0.9476 | 0.9183 |
| leaf_hierarchy4_n1024_d2_p0 | cpu | 2.3103 | 3.6216 | 0.9474 | 0.9217 |
| leaf_hierarchy16_n1024_d2_p0 | wall | 1.7932 | 2.0867 | 0.6071 | 0.5829 |
| leaf_hierarchy16_n1024_d2_p0 | cpu | 1.7805 | 2.0816 | 0.6032 | 0.5840 |
| leaf_distance4_n1024_d2_p0 | wall | 2.4587 | 3.7388 | 0.8678 | 0.9339 |
| leaf_distance4_n1024_d2_p0 | cpu | 2.4462 | 3.6852 | 0.8719 | 0.9353 |
| leaf_distance16_n1024_d2_p0 | wall | 1.7107 | 2.0555 | 0.5990 | 0.5818 |
| leaf_distance16_n1024_d2_p0 | cpu | 1.7222 | 2.0377 | 0.5985 | 0.5794 |
| leaf_shuffled4_n1024_d2_p0 | wall | 1.9371 | 2.2762 | 0.5750 | 0.7003 |
| leaf_shuffled4_n1024_d2_p0 | cpu | 1.9245 | 2.2917 | 0.5795 | 0.7034 |
| leaf_shuffled16_n1024_d2_p0 | wall | 1.2468 | 1.3706 | 0.4247 | 0.4507 |
| leaf_shuffled16_n1024_d2_p0 | cpu | 1.2619 | 1.3750 | 0.4224 | 0.4466 |
| leaf_random4_n1024_d2_p0 | wall | 1.5161 | 1.3381 | 0.3195 | 0.4387 |
| leaf_random4_n1024_d2_p0 | cpu | 1.5000 | 1.3636 | 0.3261 | 0.4444 |
| leaf_random16_n1024_d2_p0 | wall | 1.1208 | 0.8226 | 0.2876 | 0.3679 |
| leaf_random16_n1024_d2_p0 | cpu | 1.1282 | 0.8298 | 0.2880 | 0.3750 |
| community_hierarchy4_n1024_d2_p0 | wall | 2.2802 | 3.1875 | 0.6481 | 0.7623 |
| community_hierarchy4_n1024_d2_p0 | cpu | 2.2879 | 3.2128 | 0.6510 | 0.7650 |
| community_hierarchy16_n1024_d2_p0 | wall | 1.7116 | 1.7670 | 0.3219 | 0.5417 |
| community_hierarchy16_n1024_d2_p0 | cpu | 1.7073 | 1.7750 | 0.3224 | 0.5512 |
| community_distance4_n1024_d2_p0 | wall | 2.3904 | 3.2608 | 0.6576 | 0.8509 |
| community_distance4_n1024_d2_p0 | cpu | 2.3939 | 3.2245 | 0.6593 | 0.8558 |
| community_distance16_n1024_d2_p0 | wall | 1.8007 | 1.7055 | 0.3139 | 0.5843 |
| community_distance16_n1024_d2_p0 | cpu | 1.8065 | 1.7083 | 0.3178 | 0.5867 |
| community_shuffled4_n1024_d2_p0 | wall | 1.9106 | 2.0607 | 0.4023 | 0.6454 |
| community_shuffled4_n1024_d2_p0 | cpu | 1.9057 | 2.0435 | 0.4030 | 0.6467 |
| community_shuffled16_n1024_d2_p0 | wall | 1.3616 | 1.1462 | 0.2048 | 0.3965 |
| community_shuffled16_n1024_d2_p0 | cpu | 1.3514 | 1.1489 | 0.2061 | 0.4060 |
| community_random4_n1024_d2_p0 | wall | 1.8146 | 1.8607 | 0.3933 | 0.5436 |
| community_random4_n1024_d2_p0 | cpu | 1.8246 | 1.8571 | 0.3925 | 0.5445 |
| community_random16_n1024_d2_p0 | wall | 1.5510 | 1.6582 | 0.3634 | 0.4989 |
| community_random16_n1024_d2_p0 | cpu | 1.5800 | 1.6538 | 0.3613 | 0.5034 |

Every individual ratio, including losses, is in [paired_ratios.csv](paired_ratios.csv). [comparisons.csv](comparisons.csv) and [graph_comparisons.csv](graph_comparisons.csv) retain spreads and win/loss counts. [summary.csv](summary.csv) reports separate algorithm runtimes in nanoseconds. [validated_calls.csv](validated_calls.csv) includes warmups; [call_diagnostics.csv](call_diagnostics.csv) contains every clock flag. [resources.csv](resources.csv) reports sampled resource observations.

Raw capture: [attachment-smoke-timing.csv](../attachment-smoke-timing.csv). Exact raw/child/log/manifest hashes and the captured source/binary inventories are retained in [provenance.json](provenance.json).
