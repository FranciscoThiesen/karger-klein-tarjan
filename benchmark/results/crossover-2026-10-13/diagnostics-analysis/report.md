# Untimed crossover mechanism diagnostics

Untimed logical-work diagnostics for ten predeclared cases, one graph seed and one KKT sampling seed. Both algorithms' contraction input volume uses contraction_edges / original m. Other counts remain separate: they are not instructions, bytes, allocator costs or elapsed-time predictions. All recursive verifier edges are incidences, so retained/heavy fractions do not describe distinct original edges or only the root call.

Validated all ten declared cases, 20 work rows and ten complete compactor traces. Each trace stage has one valid original-component moment record. All graph fingerprints match their designated complete screen; these FNV fingerprints are consistency checks, not collision-proof graph equality certificates. Native captures independently certify the MST.

The common denominator is the original edge count m=16n. K/C below means KKT / compacting Borůvka columns, not a runtime ratio. Contraction volume uses the same input-edge counter for both algorithms; KKT recursive input volume is a separate metric. Instrumented and native capture binary hashes remain distinct in provenance.

| Case | Contraction edges/m K | C | Materializations/m K | C | Initialized slots/m K | C |
|---|---:|---:|---:|---:|---:|---:|
| line_metric_n1048576_d16_p0 | 3.1824 | 5.0805 | 5.9832 | 5.4079 | 10.4919 | 5.4225 |
| line_wide_metric_n1048576_d16_p0 | 3.1888 | 5.0853 | 5.9942 | 5.4126 | 10.5133 | 5.4278 |
| line_random_n1048576_d16_p0 | 2.8396 | 3.5670 | 4.9397 | 3.7927 | 8.1405 | 3.8283 |
| grid2d_metric_n1048576_d16_p0 | 3.0657 | 4.3342 | 5.6867 | 4.6285 | 9.8035 | 4.6548 |
| grid2d_random_n1048576_d16_p0 | 2.8375 | 3.5533 | 4.9410 | 3.7772 | 8.1429 | 3.8148 |
| gnm_random_n1048576_d16_p0 | 2.8377 | 3.5553 | 4.9440 | 3.7794 | 8.1494 | 3.8167 |
| hierarchical_path_n1048576_d16_p0 | 3.4223 | 7.9535 | 6.5229 | 8.3566 | 12.1046 | 8.5160 |
| line_metric_n8388608_d16_p0 | 3.3359 | 5.9262 | 6.2934 | 6.2311 | 11.1000 | 6.2683 |
| line_wide_metric_n8388608_d16_p0 | 3.3370 | 5.9589 | 6.2955 | 6.2892 | 11.1042 | 6.3012 |
| hierarchical_path_n4194304_d16_p0 | 3.4933 | 8.8918 | 6.6927 | 9.2950 | 12.4307 | 9.4543 |

| KKT case | Recursive input edges/m | Verifier edges/m | Retained light / verifier incidences | Removed heavy / verifier incidences |
|---|---:|---:|---:|---:|
| line_metric_n1048576_d16_p0 | 1.6846 | 1.3359 | 0.0124 | 0.9876 |
| line_wide_metric_n1048576_d16_p0 | 1.6859 | 1.3385 | 0.0124 | 0.9876 |
| line_random_n1048576_d16_p0 | 1.5007 | 0.9878 | 0.0069 | 0.9931 |
| grid2d_metric_n1048576_d16_p0 | 1.6330 | 1.2384 | 0.0111 | 0.9889 |
| grid2d_random_n1048576_d16_p0 | 1.5012 | 0.9887 | 0.0069 | 0.9931 |
| gnm_random_n1048576_d16_p0 | 1.5018 | 0.9899 | 0.0068 | 0.9932 |
| hierarchical_path_n1048576_d16_p0 | 1.7751 | 1.4593 | 0.0311 | 0.9689 |
| line_metric_n8388608_d16_p0 | 1.7301 | 1.4271 | 0.0116 | 0.9884 |
| line_wide_metric_n8388608_d16_p0 | 1.7304 | 1.4275 | 0.0116 | 0.9884 |
| hierarchical_path_n4194304_d16_p0 | 1.8009 | 1.5109 | 0.0300 | 0.9700 |

`filtered_edges` counts retained F-light incidences after verification, not removed edges. An edge can occur in more than one recursive verifier input. A zero verifier denominator is n/a (including deterministic compaction), not a measured zero retention fraction.

| Case | Compactor rounds | Root edges/m after two | q after two | q_eff after two | q_eff/q | Largest original component/n |
|---|---:|---:|---:|---:|---:|---:|
| line_metric_n1048576_d16_p0 | 9 | 0.9428 | 114908 | 98164.27 | 0.8543 | 0.000035 |
| line_wide_metric_n1048576_d16_p0 | 13 | 0.9428 | 115005 | 98169.02 | 0.8536 | 0.000038 |
| line_random_n1048576_d16_p0 | 8 | 0.9277 | 53650 | 33453.52 | 0.6236 | 0.000187 |
| grid2d_metric_n1048576_d16_p0 | 11 | 0.8901 | 99131 | 79147.94 | 0.7984 | 0.000056 |
| grid2d_random_n1048576_d16_p0 | 8 | 0.9266 | 53701 | 33375.47 | 0.6215 | 0.000159 |
| gnm_random_n1048576_d16_p0 | 8 | 0.9278 | 53738 | 33567.27 | 0.6246 | 0.000189 |
| hierarchical_path_n1048576_d16_p0 | 20 | 0.9529 | 262144 | 262144.00 | 1.0000 | 0.000004 |
| line_metric_n8388608_d16_p0 | 10 | 0.9442 | 919974 | 786363.53 | 0.8548 | 0.000005 |
| line_wide_metric_n8388608_d16_p0 | 15 | 0.9442 | 920199 | 785983.59 | 0.8541 | 0.000005 |
| hierarchical_path_n4194304_d16_p0 | 22 | 0.9531 | 1048576 | 1048576.00 | 1.0000 | 0.000001 |

Stage zero is the original graph. Stage r follows r compactor rounds; the final original partition has q=1 even though production stores an empty quotient with zero vertices. q_eff=n²/Σ(size²), and q_eff/q=1 only for equal component sizes. The first two residual dimensions match KKT's root counters; every compactor input/output volume matches its trace.

One graph and one sampling seed provide case-specific diagnostics. These ten cases do not cover intermediate spatial sizes, the density-four controls, random-tree control or 8M G(n,m). No intermediate transition or elapsed-time cause is inferred. Wider gaps change their relative ordering as well as tie frequency, so the precision ablation is not an isolated tie-rule change. The comparison concerns whole continuation strategies, not an isolated causal effect of sampling.

[Per-case table](case_summary.csv), [normalized algorithm work](normalized_work.csv), [complete validated work rows](validated_work.csv), [shared work aggregation](work_summary.csv), [original graph identities](input_matches.csv), [per-stage components](component_stages.csv), [component graph summaries](component_graphs.csv), [complete contraction rounds](contraction_rounds.csv), [provenance](provenance.json).

Inputs:

- [work_csv](../diagnostics_work.csv)
- [trace_csv](../diagnostics_trace.csv)
- [log](../diagnostics_trace.log)
- [manifest](../diagnostics.csv)
- [reference_config](../all_screens_comparison.json)
- [work_log](../diagnostics_work.log)
