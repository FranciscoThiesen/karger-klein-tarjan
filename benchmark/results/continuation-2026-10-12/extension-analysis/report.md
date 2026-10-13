# Unchanged KKT versus continued production contraction

Validated 192 timed calls across 12 manifest cases; 96 additional checked warmup calls are not timing rows.

KKT has a lower paired case median in **12/12** cases; all graph medians favor KKT in **11/12**. These are this run's descriptive results, not automatic confirmation of a selected hypothesis.

Every ratio divides matched call times first, then takes medians across repetitions, sampling seeds and graph seeds. Independent timing medians need not divide to the paired ratio. Graph ranges are not confidence intervals. Order-stratified summaries and every individual loss/tie are retained.

| Case | KKT / compaction [graph range] | KKT ms | Compaction ms | KKT losses / pairs |
|---|---:|---:|---:|---:|
| hierarchical_path_n262144_d64_p0 | 0.8640 [0.8565, 0.8715] | 3820.750 | 4422.803 | 0/8 |
| distance_path_n65536_d64_p0 | 0.9831 [0.9649, 1.0013] | 492.381 | 501.616 | 2/8 |
| hierarchical_tree_n131072_d64_p0 | 0.8939 [0.8908, 0.8970] | 1441.107 | 1615.300 | 0/8 |
| distance_tree_n131072_d64_p0 | 0.9089 [0.9082, 0.9095] | 1488.085 | 1637.330 | 0/8 |
| distance_path_n131072_d64_p0 | 0.9191 [0.9109, 0.9273] | 1490.105 | 1621.822 | 0/8 |
| hierarchical_tree_n262144_d16_p0 | 0.9218 [0.9196, 0.9240] | 699.112 | 758.937 | 0/8 |
| hierarchical_path_n131072_d64_p0 | 0.9339 [0.9229, 0.9450] | 1503.144 | 1609.985 | 0/8 |
| hierarchical_path_n262144_d16_p0 | 0.9377 [0.9340, 0.9413] | 684.056 | 729.691 | 0/8 |
| distance_path_n262144_d64_p0 | 0.8612 [0.8575, 0.8648] | 3767.224 | 4375.160 | 0/8 |
| hierarchical_tree_n262144_d64_p0 | 0.8690 [0.8629, 0.8751] | 3780.324 | 4350.347 | 0/8 |
| distance_tree_n262144_d64_p0 | 0.8675 [0.8647, 0.8703] | 3794.964 | 4374.733 | 0/8 |
| distance_tree_n65536_d64_p0 | 0.9841 [0.9832, 0.9851] | 496.485 | 504.495 | 0/8 |

![Every runtime case](runtime_ratios.png)

The comparison uses identical production contraction code and reserved ID-set output. It measures whole continuation strategies, including recursive/iterative storage lifetimes, RNG, sampling and verification. Engineered hierarchy, cheap-backbone and hierarchical-distance cases are stress tests, not representative application graphs. Globally randomized weight controls share topology/IDs/order only; their full weighted fingerprints are not required to match.

Timing and instrumented work are separate runs. Work means average sampling seeds within graphs, then graph seeds. The logical proxy sums mixed loop/table/storage/hash-API events, omitting allocator internals, collisions, deallocation and cache behavior; it is not CPU instructions.

![Contraction edge volume](contraction_edge_volume.png)

Contraction volumes compare `contraction_edges` for both algorithms, not KKT recursive input volume. Verification input edges, copies, initialized slots and the full proxy remain separate columns. Traces validate complete contraction chains, selected-edge accounting and exact dyadic halving for unperturbed hierarchy cases. Crosschecks compare fingerprints and root-after-two dimensions; full intermediate edge lists are not exported.

Input hashes, exact manifest and ordered seed banks are recorded in analysis_inputs.json. Build/machine provenance comes from the accompanying runner metadata, not from timing CSV alone.
