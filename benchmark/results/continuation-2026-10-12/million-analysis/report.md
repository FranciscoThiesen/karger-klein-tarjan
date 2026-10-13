# Unchanged KKT versus continued production contraction

Validated 80 timed calls across 5 manifest cases; 40 additional checked warmup calls are not timing rows.

KKT has a lower paired case median in **5/5** cases; all graph medians favor KKT in **5/5**. These are this run's descriptive results, not automatic confirmation of a selected hypothesis.

Every ratio divides matched call times first, then takes medians across repetitions, sampling seeds and graph seeds. Independent timing medians need not divide to the paired ratio. Graph ranges are not confidence intervals. Order-stratified summaries and every individual loss/tie are retained.

| Case | KKT / compaction [graph range] | KKT ms | Compaction ms | KKT losses / pairs |
|---|---:|---:|---:|---:|
| hierarchical_tree_n1048576_d16_p0 | 0.8142 [0.8134, 0.8151] | 4482.961 | 5506.213 | 0/8 |
| hierarchical_path_n524288_d16_p0 | 0.8681 [0.8607, 0.8756] | 1823.740 | 2101.077 | 0/8 |
| hierarchical_tree_n524288_d16_p0 | 0.8584 [0.8556, 0.8612] | 1817.249 | 2116.921 | 0/8 |
| hierarchical_path_n1048576_d16_p0 | 0.8122 [0.8088, 0.8156] | 4519.195 | 5564.099 | 0/8 |
| low_path_n1048576_d16_p0 | 0.9311 [0.9267, 0.9354] | 4205.333 | 4517.604 | 0/8 |

![Every runtime case](runtime_ratios.png)

The comparison uses identical production contraction code and reserved ID-set output. It measures whole continuation strategies, including recursive/iterative storage lifetimes, RNG, sampling and verification. Engineered hierarchy, cheap-backbone and hierarchical-distance cases are stress tests, not representative application graphs. Globally randomized weight controls share topology/IDs/order only; their full weighted fingerprints are not required to match.

Timing and instrumented work are separate runs. Work means average sampling seeds within graphs, then graph seeds. The logical proxy sums mixed loop/table/storage/hash-API events, omitting allocator internals, collisions, deallocation and cache behavior; it is not CPU instructions.

![Contraction edge volume](contraction_edge_volume.png)

Contraction volumes compare `contraction_edges` for both algorithms, not KKT recursive input volume. Verification input edges, copies, initialized slots and the full proxy remain separate columns. Traces validate complete contraction chains, selected-edge accounting and exact dyadic halving for unperturbed hierarchy cases. Crosschecks compare fingerprints and root-after-two dimensions; full intermediate edge lists are not exported.

Input hashes, exact manifest and ordered seed banks are recorded in analysis_inputs.json. Build/machine provenance comes from the accompanying runner metadata, not from timing CSV alone.
