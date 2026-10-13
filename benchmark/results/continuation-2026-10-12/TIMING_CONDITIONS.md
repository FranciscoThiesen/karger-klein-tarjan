# Timing conditions and retained extreme observations

Every raw observation is retained in the matched pairs, loss counts and prescribed nested medians. No filtered campaign is substituted. These are desktop measurements; power states and concurrent services were not controlled.

| Campaign | UTC elapsed s | Runner monotonic s | Difference s | /usr/bin/time real s |
|---|---:|---:|---:|---:|
| confirmation | 5676.532593 | 4759.558535 | 916.974058 | 5676.52 |
| confirmation-repeat | 5198.893737 | 4890.840482 | 308.053255 | 5198.86 |
| sensitivity | 930.882613 | 930.886624 | -0.004011 | 930.87 |

The runner’s `wall_seconds_including_setup` field uses Python monotonic time. The native harness records `std::chrono::steady_clock` intervals. A clock’s name is not evidence that its intervals exclude host suspension. Root confirmed Sleep/DarkWake events in the primary capture; these records do not independently align native calls with power logs.

Individual calls longer than 60 seconds (a descriptive flag, never an exclusion rule):

| Campaign | Case | Algorithm | Graph seed | KKT seed | Repetition | Order | Seconds |
|---|---|---|---:|---:|---:|---:|---:|
| confirmation | low_path_n1048576_d16_p0 | kkt | 131071 | 29 | 3 | 0 | 922.624889916 |
| confirmation-repeat | random_path_n1048576_d16_p0 | compacting_boruvka | 104729 | 11 | 3 | 1 | 312.622067125 |

The primary extreme is a KKT loss on the low-path control; the repeat extreme is a compactor loss on the random-path control. They remain in `final-comparison/paired_pairs.csv`. Neither occurs in a selected hierarchy case. This does not establish that the candidate calls were free of other system effects.

The paired case criterion is a predeclared descriptive rule, not a confidence interval or a significance test. Separate algorithm medians drift between runs; their quotients are not the prescribed paired ratios. Raw, metadata and `/usr/bin/time` log hashes plus complete per-case summaries are in `timing_conditions.json`.
