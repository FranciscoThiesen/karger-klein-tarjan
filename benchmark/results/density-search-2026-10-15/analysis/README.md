# Direct-Edge density and core-weight-order search

All 672 solver outputs passed exact MST validation: 576 timed calls and 96 checked warmups. Each algorithm occupies every timed position once per child. This is a fresh, separately declared two-graph-seed campaign; historical timing is not pooled.

Test denser leaf-attachment graphs with ordered versus shuffled core ranks using the exact frozen direct-Edge KKT binary. Matched hierarchy/shuffled cases have identical topology, IDs, labels and physical edge order; both retain cheap leaf attachments. Shuffled core ranks do not mean globally random edge weights.

Compare KKT directly with all five competitors in the same child, graph seed, sampling seed and repetition. Pool all twelve paired trial ratios per case and retain each graph's six-trial median. No historical timing is pooled, normalized or replaced. Graph/trial ranges are descriptive, not confidence intervals.

All 0 clock-flagged calls and 0 capture/child UTC flags remain included. Wall and CPU clocks are separate; neither flags nor power events change the observations. RSS is a sampled process-group sum, not a continuous peak. Power-audit status: `archived_log_correlated`; verified sleep inhibition is not claimed.

| Case | Clock | KKT / compacting Boruvka | KKT / multigraph Boruvka | KKT / Kruskal | KKT / Prim | KKT / original Boruvka |
|---|---|---:|---:|---:|---:|---:|
| leaf_hierarchy4_n65536_d32_p0 | wall | 0.8240 | 1.0548 | 1.1474 | 2.1064 | 1.5472 |
| leaf_hierarchy4_n65536_d32_p0 | cpu | 0.8240 | 1.0548 | 1.1475 | 2.1064 | 1.5473 |
| leaf_shuffled4_n65536_d32_p0 | wall | 0.9682 | 1.8534 | 1.0617 | 1.9210 | 2.6241 |
| leaf_shuffled4_n65536_d32_p0 | cpu | 0.9682 | 1.8534 | 1.0617 | 1.9210 | 2.6240 |
| leaf_hierarchy4_n1048576_d32_p0 | wall | 0.3672 | 1.0937 | 1.6858 | 2.0522 | 1.2106 |
| leaf_hierarchy4_n1048576_d32_p0 | cpu | 0.3672 | 1.0938 | 1.6858 | 2.0522 | 1.2106 |
| leaf_shuffled4_n1048576_d32_p0 | wall | 0.4064 | 1.7367 | 1.5019 | 1.8224 | 1.8653 |
| leaf_shuffled4_n1048576_d32_p0 | cpu | 0.4064 | 1.7367 | 1.5019 | 1.8224 | 1.8653 |
| leaf_hierarchy4_n65536_d64_p0 | wall | 0.6793 | 1.0417 | 1.0976 | 2.8240 | 1.7036 |
| leaf_hierarchy4_n65536_d64_p0 | cpu | 0.6793 | 1.0417 | 1.0976 | 2.8239 | 1.7036 |
| leaf_shuffled4_n65536_d64_p0 | wall | 0.7543 | 1.8397 | 0.9970 | 2.5942 | 2.9609 |
| leaf_shuffled4_n65536_d64_p0 | cpu | 0.7543 | 1.8397 | 0.9971 | 2.5942 | 2.9608 |
| leaf_hierarchy4_n1048576_d64_p0 | wall | 0.3724 | 1.1198 | 1.6705 | 2.8677 | 1.4738 |
| leaf_hierarchy4_n1048576_d64_p0 | cpu | 0.3723 | 1.1195 | 1.6703 | 2.8671 | 1.4732 |
| leaf_shuffled4_n1048576_d64_p0 | wall | 0.4085 | 1.8858 | 1.4897 | 2.5778 | 2.4122 |
| leaf_shuffled4_n1048576_d64_p0 | cpu | 0.4085 | 1.8858 | 1.4897 | 2.5778 | 2.4122 |

Ratios below one favor KKT. Every trial pair, all five comparisons, both graph-seed medians, absolute runtimes, warmups, clock diagnostics and resource observations remain in the adjacent CSV tables. This campaign uses the exact prior direct-Edge binary with fresh graph/sampling seeds and denser cases. Finite measurements do not prove asymptotic dominance.
