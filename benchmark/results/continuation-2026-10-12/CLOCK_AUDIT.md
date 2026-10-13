# Clock and power-state audit

This postprocessing audit retains all **2,944 measured calls and 932 checked warmups** from four completed screens, primary confirmation, reverse-order confirmation, and sensitivity. No observation was removed, adjusted, or replaced. The interrupted pre-hash-repair extension is not a completed campaign and remains separately archived.

Three captures contain logged sleeps. The million screen has a **1,030-second clamshell sleep** but no comparably long recorded solver call; primary and repeat have **918- and 308-second maintenance sleeps** and one very long recorded control call each. These campaigns are not sleep-controlled replications. The predeclared summaries still include those calls.

## Run clocks

`UTC` is the difference between runner start/end UTC timestamps. `Monotonic` is the runner’s `time.monotonic()` elapsed field, named `wall_seconds_including_setup` in the original metadata. `time real` comes from `/usr/bin/time -l`. These all include setup in their execution scope, but they demonstrably do not count suspension alike. Millisecond-level discrepancies also include slightly different timestamp boundaries and rounding.

| Campaign | Measured / warmup calls | UTC seconds | Runner monotonic seconds | UTC − monotonic | `time real` seconds | Logged sleep seconds |
|---|---:|---:|---:|---:|---:|---:|
| [discovery](discovery_timing.json) | 384 / 192 | 177.920880 | 177.920295 | +0.000585 | 177.91 | 0 |
| [extension](extension_fast_timing.json) | 192 / 96 | 727.767948 | 727.766692 | +0.001256 | 727.76 | 0 |
| [large-random](large_random_timing.json) | 32 / 16 | 256.074237 | 256.075517 | -0.001280 | 256.07 | 0 |
| [million](million_timing.json) | 80 / 40 | 1580.962647 | 551.320332 | +1029.642315 | 1581.04 | 1030 |
| [confirmation](confirmation_timing.json) | 1080 / 270 | 5676.532593 | 4759.558535 | +916.974058 | 5676.52 | 918 |
| [confirmation-repeat](confirmation_repeat_timing.json) | 1080 / 270 | 5198.893737 | 4890.840482 | +308.053255 | 5198.86 | 308 |
| [sensitivity](sensitivity_timing.json) | 96 / 48 | 930.882613 | 930.886624 | -0.004011 | 930.87 | 0 |

The four screens and sensitivity use the same clock choices as confirmation. Sensitivity’s UTC and runner-monotonic durations agree within **0.0041 seconds**, and the narrow power-log query found no sleep/wake event within that interval. This is evidence against a multi-minute suspension gap there, not proof of isolated or controlled machine conditions. Its p0 baseline is from the earlier million screen, so the separate-run caveat remains material.

## Recorded timing extremes

As a descriptive check, divide each call by the median for its own campaign, case, graph seed and algorithm, pooling sampling seeds and repetitions. A 1.5× threshold flags two calls; it is an audit aid, not a statistical outlier test or an exclusion rule. The maximum relative call in each other campaign is: discovery 1.463×, extension 1.132×, large-random 1.053×, million 1.038×, sensitivity 1.170×.

| Run | Case / graph seed / sampling seed / repetition | Algorithm | Seconds | Same-group median seconds | Relative to median |
|---|---|---|---:|---:|---:|
| confirmation | `low_path_n1048576_d16_p0` / 131071 / 29 / 3 | kkt | 922.624889916 | 4.594724 | 200.801× |
| confirmation-repeat | `random_path_n1048576_d16_p0` / 104729 / 11 / 3 | compacting_boruvka | 312.622067125 | 3.762801 | 83.082× |

Primary’s sleep runs from **2026-10-13 01:51:53 to 02:07:11 UTC** (918 seconds), and repeat’s from **03:10:03 to 03:15:11 UTC** (308 seconds). Their intervals and clock gaps are consistent with the long native `std::chrono::steady_clock` observations including suspension. No per-call UTC timestamps were retained, so exact event-to-call alignment is not proven; these durations must not be interpreted as active solver compute time.

The million-screen sleep runs from **2026-10-13 00:14:16 to 00:31:26 UTC** (1,030 seconds), matching its +1,029.642-second clock gap. Its raw measured calls and logged setup phases have no corresponding long observation. Warmup durations and other untimed work were not individually recorded; the suspension cannot be assigned to one of those phases. This screen retains all 80 measured calls.

## Effect on interpretation

Independent recomputation from raw matched pairs agrees with every case summary in `final-comparison/confirmation_cases.csv`: first take medians across repetitions, then sampling seeds, then graph seeds. Both preselected hierarchy families pass the frozen ≤0.90 case-median and <1.0 every-graph rule at both sizes in both runs. There are **0/240 individual selected-case losses in primary and 1/240 in repeat**. The two extreme calls occur in controls. All control losses and the single selected-case loss remain in the summaries.

Absolute run-to-run times also drift; these are ratios of independently aggregated algorithm time medians, not paired speedups:

| Selected case | Repeat / primary KKT median | Repeat / primary compactor median |
|---|---:|---:|
| `hierarchical_path_n1048576_d16_p0` | 1.1303× | 1.1091× |
| `hierarchical_tree_n524288_d16_p0` | 1.2782× | 1.2539× |
| `hierarchical_path_n524288_d16_p0` | 0.8926× | 0.8696× |
| `hierarchical_tree_n1048576_d16_p0` | 1.0366× | 1.0353× |

Reversed case order and pairing reduce some drift effects but do not identify their cause. The runs used a shared desktop, without verified persistent sleep prevention, affinity or machine isolation. Passing the retained-data rule supports the bounded empirical result; it is not a sleep-controlled replication, a confidence interval, or a cache/CPU-state diagnosis.

## Sleep-prevention attempts and evidence

The [background `caffeinate` record](awake_assertion.json) establishes an attempt, not a persistent assertion. The process was later absent while the watched job remained active; its exact failure cause is unknown. The [foreground retry](foreground_awake_assertion.json) failed immediately with exit status 1 and `Failed to create PreventUserIdleSystemSleep assertion`; [stderr](awake_assertion.log) is retained. No successful persistent power assertion can be inferred for sensitivity either.

The audit recomputed all raw/log SHA-256 values and matched them to capture metadata, checked positive successful rows and counts, and independently compared confirmation summaries. [Machine-readable audit](clock_audit.json) includes exact timestamps, narrow power-log results for all seven timing campaigns, hashes, setup totals and diagnostic methods. Standalone excerpts: [million](million_power_events.log), [primary](primary_power_events.log), [repeat](repeat_power_events.log). The fresh power query retained only event lines inside the exact run intervals; absence of a listed event is not a guarantee of complete power control.

No solver, build, timed capture, raw CSV, capture metadata, selection threshold, or aggregation rule changed during this audit.

## Untimed sensitivity captures

These later captures contain **logical work counters and contraction stages only**. They add no solver-timing observations and do not change the seven-campaign totals above. No capture duration here is used as performance evidence.

| Capture | Validated rows | UTC seconds | Runner monotonic seconds | UTC − monotonic | `time real` seconds | Logged sleep seconds |
|---|---:|---:|---:|---:|---:|---:|
| [work](sensitivity_work.json) | 36 | 371.487467 | 371.484536 | +0.002931 | 371.48 | 0 |
| [trace](sensitivity_trace.json) | 130 | 1173.928378 | 256.655822 | +917.272557 | 1173.92 | 918 |

The trace capture contains a logged **918-second maintenance sleep**. Its log also records a **922.725-second fixture-generation phase** for `hierarchical_tree_n1048576_d16_p10`, graph seed 42, consistent with suspension during setup. There are no per-phase UTC timestamps for exact alignment. This is a setup/clock observation, not an algorithm slowdown. The work capture’s clocks agree within 0.003 seconds.

All 36 work rows and 130 trace rows remain unchanged and passed their capture checks. The [machine-readable audit](clock_audit.json) records exact metadata/raw/log hashes, verifies raw/log hashes against both capture metadata files, and retains the narrow power-event records; the [trace power excerpt](sensitivity_trace_power_events.log) is also archived.
