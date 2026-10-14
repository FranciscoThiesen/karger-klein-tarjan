# Separately labeled monitor recovery

The original confirmation B remains failed. This capture covers only its two unstarted cases. RSS monitoring uses the recorded libproc recovery adapter; native timing and row validation are unchanged. Per-observation sampler duration and sampling gaps are retained in provenance.

# Five-solver capture

Strict validation passed for 2 cases, 3 graph seeds and 2 sampling seeds: 300 timed calls and 60 retained warmup calls. Each child has 5 timed repetitions and 1 warmups per algorithm.

All five positions are balanced within each timed seed pair. Every native reference has an independent MST certificate; every returned result must match that exact unique MST. Warmups are validated and retained, but excluded from timing summaries.

Ratios below one favor KKT. Each ratio is paired within the same graph, sampling seed and repetition, then aggregated by median over repetitions, sampling seeds and graphs in that order. Runtime summaries apply the same hierarchy separately to each algorithm; a ratio of those summaries is a different statistic. Graph and individual-trial ranges are descriptive spreads, not confidence intervals. Sampling seeds repeat identical inputs for deterministic competitors; they are not additional graph samples.

`compacting_boruvka` repeatedly uses production contraction; `boruvka` is the original public baseline. No other campaign is mixed into these comparisons, and no finite result establishes asymptotic dominance.

0 calls carry diagnostic clock flags, and 0 capture/child UTC interval flags are retained in provenance; all calls remain in every relevant table. Wall and process-CPU results are separate. Resource observations are periodic sums of process-group RSS in KiB, not continuous peaks or unique physical footprints. Polling itself can perturb measurements; the same rule is applied throughout this campaign.

| Case | Metric | KKT / compacting Borůvka | KKT / Kruskal | KKT / Prim | KKT / original Borůvka |
|---|---|---:|---:|---:|---:|
| leaf_hierarchy4_n262144_d16_p0 | wall | 0.8746 | 2.5842 | 2.4607 | 1.9172 |
| leaf_hierarchy4_n262144_d16_p0 | cpu | 0.8745 | 2.5807 | 2.4571 | 1.9205 |
| leaf_distance4_n1048576_d16_p0 | wall | 0.8202 | 4.0723 | 1.9918 | 1.8451 |
| leaf_distance4_n1048576_d16_p0 | cpu | 0.8212 | 4.0626 | 2.0019 | 1.8388 |

Every individual ratio, including losses, is in [paired_ratios.csv](paired_ratios.csv). [comparisons.csv](comparisons.csv) and [graph_comparisons.csv](graph_comparisons.csv) retain spreads and win/loss counts. [summary.csv](summary.csv) reports separate algorithm runtimes in nanoseconds. [validated_calls.csv](validated_calls.csv) includes warmups; [call_diagnostics.csv](call_diagnostics.csv) contains every clock flag. [resources.csv](resources.csv) reports sampled resource observations.

Raw capture: [attachment-confirmation-b-recovery-timing.csv](../attachment-confirmation-b-recovery-timing.csv). Exact raw/child/log/manifest hashes and the captured source/binary inventories are retained in [provenance.json](provenance.json).
