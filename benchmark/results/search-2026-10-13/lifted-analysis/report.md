# Five-solver capture

Strict validation passed for 28 cases, 1 graph seeds and 1 sampling seeds: 700 timed calls and 140 retained warmup calls. Each child has 5 timed repetitions and 1 warmups per algorithm.

All five positions are balanced within each timed seed pair. Every native reference has an independent MST certificate; every returned result must match that exact unique MST. Warmups are validated and retained, but excluded from timing summaries.

Ratios below one favor KKT. Each ratio is paired within the same graph, sampling seed and repetition, then aggregated by median over repetitions, sampling seeds and graphs in that order. Runtime summaries apply the same hierarchy separately to each algorithm; a ratio of those summaries is a different statistic. Graph and individual-trial ranges are descriptive spreads, not confidence intervals. Sampling seeds repeat identical inputs for deterministic competitors; they are not additional graph samples.

`compacting_boruvka` repeatedly uses production contraction; `boruvka` is the original public baseline. No other campaign is mixed into these comparisons, and no finite result establishes asymptotic dominance.

0 calls carry diagnostic clock flags, and 0 capture/child UTC interval flags are retained in provenance; all calls remain in every relevant table. Wall and process-CPU results are separate. Resource observations are periodic sums of process-group RSS in KiB, not continuous peaks or unique physical footprints. Polling itself can perturb measurements; the same rule is applied throughout this campaign.

| Case | Metric | KKT / compacting Borůvka | KKT / Kruskal | KKT / Prim | KKT / original Borůvka |
|---|---|---:|---:|---:|---:|
| lifted_distance2_n262144_d16_p0 | wall | 1.0786 | 1.6554 | 0.6214 | 0.9576 |
| lifted_distance2_n262144_d16_p0 | cpu | 1.0786 | 1.6553 | 0.6214 | 0.9576 |
| lifted_distance4_n65536_d64_p0 | wall | 1.0273 | 1.1736 | 1.0056 | 1.5092 |
| lifted_distance4_n65536_d64_p0 | cpu | 1.0272 | 1.1736 | 1.0056 | 1.5094 |
| lifted_hierarchy2_n1048576_d64_p0 | wall | 0.9274 | 2.4906 | 1.7777 | 1.5534 |
| lifted_hierarchy2_n1048576_d64_p0 | cpu | 0.9274 | 2.4915 | 1.7777 | 1.5534 |
| lifted_hierarchy4_n65536_d64_p0 | wall | 1.0250 | 1.0957 | 1.2375 | 1.4782 |
| lifted_hierarchy4_n65536_d64_p0 | cpu | 1.0249 | 1.0957 | 1.2375 | 1.4782 |
| lifted_random2_n1048576_d64_p0 | wall | 1.0367 | 3.5900 | 2.4151 | 5.2035 |
| lifted_random2_n1048576_d64_p0 | cpu | 1.0369 | 3.5900 | 2.4153 | 5.2034 |
| lifted_hierarchy4_n1048576_d64_p0 | wall | 1.0048 | 1.9501 | 1.6409 | 1.4675 |
| lifted_hierarchy4_n1048576_d64_p0 | cpu | 1.0048 | 1.9501 | 1.6410 | 1.4676 |
| lifted_hierarchy4_n1048576_d16_p0 | wall | 1.0469 | 1.8521 | 0.8220 | 0.7205 |
| lifted_hierarchy4_n1048576_d16_p0 | cpu | 1.0469 | 1.8521 | 0.8220 | 0.7205 |
| lifted_random4_n1048576_d64_p0 | wall | 1.0351 | 3.4253 | 2.3502 | 4.7270 |
| lifted_random4_n1048576_d64_p0 | cpu | 1.0351 | 3.4251 | 2.3502 | 4.7266 |
| lifted_distance2_n65536_d64_p0 | wall | 1.0625 | 1.0982 | 0.9421 | 1.4052 |
| lifted_distance2_n65536_d64_p0 | cpu | 1.0625 | 1.0984 | 0.9421 | 1.4052 |
| lifted_hierarchy4_n262144_d16_p0 | wall | 1.0667 | 1.0462 | 0.5554 | 0.6200 |
| lifted_hierarchy4_n262144_d16_p0 | cpu | 1.0667 | 1.0462 | 0.5554 | 0.6200 |
| lifted_distance4_n65536_d16_p0 | wall | 1.2256 | 0.6251 | 0.3233 | 0.4658 |
| lifted_distance4_n65536_d16_p0 | cpu | 1.2255 | 0.6251 | 0.3233 | 0.4658 |
| lifted_distance4_n1048576_d64_p0 | wall | 1.0025 | 1.9564 | 1.3373 | 1.4745 |
| lifted_distance4_n1048576_d64_p0 | cpu | 1.0025 | 1.9564 | 1.3373 | 1.4745 |
| lifted_distance2_n65536_d16_p0 | wall | 1.2238 | 0.9357 | 0.4215 | 0.7107 |
| lifted_distance2_n65536_d16_p0 | cpu | 1.2238 | 0.9357 | 0.4215 | 0.7107 |
| lifted_random4_n1048576_d16_p0 | wall | 1.0276 | 2.5981 | 0.8260 | 2.0983 |
| lifted_random4_n1048576_d16_p0 | cpu | 1.0276 | 2.5981 | 0.8259 | 2.0984 |
| lifted_distance4_n1048576_d16_p0 | wall | 1.0554 | 1.8541 | 0.7110 | 0.7136 |
| lifted_distance4_n1048576_d16_p0 | cpu | 1.0554 | 1.8541 | 0.7110 | 0.7136 |
| lifted_distance2_n1048576_d64_p0 | wall | 0.9293 | 2.4386 | 1.4135 | 1.6361 |
| lifted_distance2_n1048576_d64_p0 | cpu | 0.9293 | 2.4386 | 1.4136 | 1.6361 |
| lifted_hierarchy2_n1048576_d16_p0 | wall | 1.0246 | 2.3780 | 0.9014 | 0.8279 |
| lifted_hierarchy2_n1048576_d16_p0 | cpu | 1.0246 | 2.3780 | 0.9014 | 0.8279 |
| lifted_hierarchy2_n262144_d16_p0 | wall | 1.1000 | 1.4135 | 0.7011 | 0.8580 |
| lifted_hierarchy2_n262144_d16_p0 | cpu | 1.1000 | 1.4135 | 0.7011 | 0.8580 |
| lifted_hierarchy2_n65536_d64_p0 | wall | 1.0513 | 1.1277 | 1.3287 | 1.4373 |
| lifted_hierarchy2_n65536_d64_p0 | cpu | 1.0513 | 1.1277 | 1.3287 | 1.4373 |
| lifted_distance4_n262144_d64_p0 | wall | 1.0002 | 1.7315 | 1.4202 | 1.8398 |
| lifted_distance4_n262144_d64_p0 | cpu | 1.0003 | 1.7315 | 1.4202 | 1.8398 |
| lifted_hierarchy2_n65536_d16_p0 | wall | 1.2404 | 0.9406 | 0.5159 | 0.7012 |
| lifted_hierarchy2_n65536_d16_p0 | cpu | 1.2404 | 0.9406 | 0.5160 | 0.7012 |
| lifted_hierarchy4_n262144_d64_p0 | wall | 1.0155 | 1.7831 | 1.8623 | 1.8946 |
| lifted_hierarchy4_n262144_d64_p0 | cpu | 1.0155 | 1.7830 | 1.8623 | 1.8946 |
| lifted_distance2_n262144_d64_p0 | wall | 0.9817 | 2.0784 | 1.5422 | 2.0936 |
| lifted_distance2_n262144_d64_p0 | cpu | 0.9818 | 2.0783 | 1.5422 | 2.0936 |
| lifted_hierarchy4_n65536_d16_p0 | wall | 1.1671 | 0.6170 | 0.3531 | 0.4502 |
| lifted_hierarchy4_n65536_d16_p0 | cpu | 1.1672 | 0.6170 | 0.3531 | 0.4502 |
| lifted_distance2_n1048576_d16_p0 | wall | 1.0319 | 2.3733 | 0.7253 | 0.8355 |
| lifted_distance2_n1048576_d16_p0 | cpu | 1.0319 | 2.3733 | 0.7253 | 0.8355 |
| lifted_distance4_n262144_d16_p0 | wall | 1.0915 | 1.0647 | 0.4893 | 0.6343 |
| lifted_distance4_n262144_d16_p0 | cpu | 1.0915 | 1.0647 | 0.4893 | 0.6343 |
| lifted_random2_n1048576_d16_p0 | wall | 1.0195 | 3.0694 | 0.9446 | 2.4168 |
| lifted_random2_n1048576_d16_p0 | cpu | 1.0195 | 3.0694 | 0.9446 | 2.4168 |
| lifted_hierarchy2_n262144_d64_p0 | wall | 0.9741 | 2.1000 | 2.1306 | 2.1063 |
| lifted_hierarchy2_n262144_d64_p0 | cpu | 0.9741 | 2.1000 | 2.1306 | 2.1064 |

Every individual ratio, including losses, is in [paired_ratios.csv](paired_ratios.csv). [comparisons.csv](comparisons.csv) and [graph_comparisons.csv](graph_comparisons.csv) retain spreads and win/loss counts. [summary.csv](summary.csv) reports separate algorithm runtimes in nanoseconds. [validated_calls.csv](validated_calls.csv) includes warmups; [call_diagnostics.csv](call_diagnostics.csv) contains every clock flag. [resources.csv](resources.csv) reports sampled resource observations.

Raw capture: [lifted-timing.csv](../lifted-timing.csv). Exact raw/child/log/manifest hashes and the captured source/binary inventories are retained in [provenance.json](provenance.json).
