# Five-solver capture

Strict validation passed for 1 cases, 1 graph seeds and 1 sampling seeds: 25 timed calls and 5 retained warmup calls. Each child has 5 timed repetitions and 1 warmups per algorithm.

All five positions are balanced within each timed seed pair. Every native reference has an independent MST certificate; every returned result must match that exact unique MST. Warmups are validated and retained, but excluded from timing summaries.

Ratios below one favor KKT. Each ratio is paired within the same graph, sampling seed and repetition, then aggregated by median over repetitions, sampling seeds and graphs in that order. Runtime summaries apply the same hierarchy separately to each algorithm; a ratio of those summaries is a different statistic. Graph and individual-trial ranges are descriptive spreads, not confidence intervals. Sampling seeds repeat identical inputs for deterministic competitors; they are not additional graph samples.

`compacting_boruvka` repeatedly uses production contraction; `boruvka` is the original public baseline. No other campaign is mixed into these comparisons, and no finite result establishes asymptotic dominance.

0 calls carry diagnostic clock flags, and 0 capture/child UTC interval flags are retained in provenance; all calls remain in every relevant table. Wall and process-CPU results are separate. Resource observations are periodic sums of process-group RSS in KiB, not continuous peaks or unique physical footprints. Polling itself can perturb measurements; the same rule is applied throughout this campaign.

| Case | Metric | KKT / compacting Borůvka | KKT / Kruskal | KKT / Prim | KKT / original Borůvka |
|---|---|---:|---:|---:|---:|
| lifted_distance2_n256_d8_p0 | wall | 2.3100 | 1.8173 | 0.5574 | 1.1000 |
| lifted_distance2_n256_d8_p0 | cpu | 2.3226 | 1.8250 | 0.5581 | 1.0896 |

Every individual ratio, including losses, is in [paired_ratios.csv](paired_ratios.csv). [comparisons.csv](comparisons.csv) and [graph_comparisons.csv](graph_comparisons.csv) retain spreads and win/loss counts. [summary.csv](summary.csv) reports separate algorithm runtimes in nanoseconds. [validated_calls.csv](validated_calls.csv) includes warmups; [call_diagnostics.csv](call_diagnostics.csv) contains every clock flag. [resources.csv](resources.csv) reports sampled resource observations.

Raw capture: [native-smoke-retry.csv](../native-smoke-retry.csv). Exact raw/child/log/manifest hashes and the captured source/binary inventories are retained in [provenance.json](provenance.json).
