# Common graph models experiment

Validated **52 cases and 7,488 timed observations**, with three graph seeds, three sampling-seed labels, 4 repetitions, and one warmup per algorithm/seed pair. The complete requested matrix retains all thirteen families at sizes 4096, 16384, 65536, 262144. All families and the hub/random-4 controls were selected before these measurements; no family is dropped according to its result.

Median of repetitions for each graph/sampling-seed pair; median of the three sampling-seed values per graph; median of the three graph values. Paired ratios apply the same hierarchy to matched algorithm/reference elapsed-time ratios. Error bars span graph-level medians and are not confidence intervals.

Lower ratios favor KKT. Displayed runtime medians and paired ratios are aggregated separately; dividing displayed times need not reproduce the paired ratios.

| Case | KKT ms | Kruskal ms | Prim ms | Borůvka ms | KKT/Kruskal | KKT/Prim | KKT/Borůvka |
|---|---:|---:|---:|---:|---:|---:|---:|
| unbalanced_bipartite_16_n4096 | 0.323 | 0.691 | 1.730 | 0.526 | 0.461× | 0.187× | 0.620× |
| unbalanced_bipartite_16_n16384 | 1.415 | 3.265 | 9.860 | 2.461 | 0.433× | 0.148× | 0.574× |
| unbalanced_bipartite_16_n65536 | 5.996 | 14.288 | 46.651 | 10.655 | 0.421× | 0.128× | 0.571× |
| unbalanced_bipartite_16_n262144 | 28.542 | 61.995 | 290.424 | 55.557 | 0.463× | 0.094× | 0.514× |
| unbalanced_bipartite_256_n4096 | 0.540 | 0.654 | 1.700 | 0.749 | 0.814× | 0.317× | 0.723× |
| unbalanced_bipartite_256_n16384 | 2.130 | 3.139 | 9.739 | 3.209 | 0.673× | 0.219× | 0.665× |
| unbalanced_bipartite_256_n65536 | 7.656 | 14.180 | 47.046 | 13.225 | 0.541× | 0.165× | 0.586× |
| unbalanced_bipartite_256_n262144 | 37.927 | 62.498 | 263.930 | 67.161 | 0.606× | 0.145× | 0.569× |
| unbalanced_bipartite_sqrt_n4096 | 0.388 | 0.681 | 1.711 | 0.595 | 0.583× | 0.227× | 0.645× |
| unbalanced_bipartite_sqrt_n16384 | 1.757 | 3.096 | 8.863 | 2.654 | 0.568× | 0.196× | 0.676× |
| unbalanced_bipartite_sqrt_n65536 | 7.676 | 13.831 | 48.007 | 12.855 | 0.552× | 0.160× | 0.594× |
| unbalanced_bipartite_sqrt_n262144 | 42.970 | 62.028 | 301.832 | 73.258 | 0.689× | 0.142× | 0.547× |
| leaf_core_50_n4096 | 0.548 | 0.435 | 1.292 | 0.861 | 1.222× | 0.416× | 0.630× |
| leaf_core_50_n16384 | 2.538 | 1.934 | 6.633 | 4.291 | 1.293× | 0.381× | 0.604× |
| leaf_core_50_n65536 | 11.547 | 9.028 | 35.732 | 22.100 | 1.292× | 0.325× | 0.513× |
| leaf_core_50_n262144 | 59.044 | 40.249 | 218.758 | 140.466 | 1.469× | 0.258× | 0.404× |
| leaf_core_90_n4096 | 0.205 | 0.179 | 0.609 | 0.477 | 1.164× | 0.345× | 0.431× |
| leaf_core_90_n16384 | 0.959 | 0.975 | 3.325 | 2.451 | 0.986× | 0.295× | 0.390× |
| leaf_core_90_n65536 | 4.076 | 4.367 | 15.973 | 11.148 | 0.938× | 0.256× | 0.361× |
| leaf_core_90_n262144 | 18.887 | 19.835 | 101.532 | 69.198 | 0.943× | 0.187× | 0.272× |
| ring_cliques_16_n4096 | 0.852 | 1.416 | 1.795 | 1.179 | 0.594× | 0.477× | 0.722× |
| ring_cliques_16_n16384 | 3.627 | 6.310 | 7.527 | 6.160 | 0.572× | 0.482× | 0.584× |
| ring_cliques_16_n65536 | 17.930 | 28.961 | 36.994 | 35.949 | 0.620× | 0.480× | 0.488× |
| ring_cliques_16_n262144 | 129.953 | 129.063 | 206.906 | 222.739 | 1.006× | 0.619× | 0.586× |
| grid2d_random_n4096 | 0.551 | 0.357 | 1.000 | 0.957 | 1.552× | 0.560× | 0.563× |
| grid2d_random_n16384 | 2.348 | 1.660 | 4.654 | 5.053 | 1.425× | 0.503× | 0.462× |
| grid2d_random_n65536 | 9.995 | 7.538 | 23.055 | 24.395 | 1.329× | 0.440× | 0.413× |
| grid2d_random_n262144 | 43.941 | 33.395 | 145.817 | 155.169 | 1.320× | 0.302× | 0.285× |
| grid2d_distance_n4096 | 0.604 | 0.349 | 1.038 | 0.994 | 1.721× | 0.603× | 0.609× |
| grid2d_distance_n16384 | 2.501 | 1.618 | 4.815 | 5.223 | 1.564× | 0.528× | 0.484× |
| grid2d_distance_n65536 | 10.986 | 7.545 | 23.420 | 26.862 | 1.451× | 0.457× | 0.411× |
| grid2d_distance_n262144 | 47.972 | 33.440 | 150.917 | 187.640 | 1.459× | 0.329× | 0.256× |
| grid3d_random_n4096 | 0.646 | 0.511 | 1.545 | 1.025 | 1.246× | 0.417× | 0.627× |
| grid3d_random_n16384 | 2.894 | 2.356 | 7.897 | 5.341 | 1.216× | 0.366× | 0.528× |
| grid3d_random_n65536 | 13.610 | 11.108 | 52.180 | 30.902 | 1.237× | 0.264× | 0.447× |
| grid3d_random_n262144 | 59.606 | 48.069 | 267.995 | 173.733 | 1.242× | 0.226× | 0.355× |
| grid3d_distance_n4096 | 0.689 | 0.499 | 1.513 | 1.025 | 1.382× | 0.452× | 0.668× |
| grid3d_distance_n16384 | 3.036 | 2.331 | 7.417 | 5.419 | 1.305× | 0.407× | 0.565× |
| grid3d_distance_n65536 | 13.738 | 10.906 | 40.835 | 27.910 | 1.262× | 0.344× | 0.491× |
| grid3d_distance_n262144 | 64.511 | 49.012 | 254.978 | 175.785 | 1.334× | 0.256× | 0.366× |
| regular_8_n4096 | 0.916 | 0.704 | 1.934 | 1.025 | 1.308× | 0.465× | 0.905× |
| regular_8_n16384 | 4.278 | 3.220 | 9.886 | 5.367 | 1.336× | 0.433× | 0.797× |
| regular_8_n65536 | 21.350 | 14.911 | 60.628 | 28.968 | 1.436× | 0.350× | 0.714× |
| regular_8_n262144 | 110.063 | 64.610 | 366.633 | 179.520 | 1.712× | 0.303× | 0.641× |
| hub_n4096 | 0.542 | 0.724 | 2.159 | 0.840 | 0.754× | 0.257× | 0.657× |
| hub_n16384 | 2.495 | 3.356 | 12.603 | 4.124 | 0.740× | 0.200× | 0.608× |
| hub_n65536 | 10.804 | 14.756 | 61.224 | 18.099 | 0.733× | 0.175× | 0.603× |
| hub_n262144 | 51.431 | 64.286 | 381.745 | 117.010 | 0.799× | 0.133× | 0.441× |
| random_4_n4096 | 0.900 | 0.726 | 2.027 | 1.102 | 1.222× | 0.431× | 0.821× |
| random_4_n16384 | 4.139 | 3.215 | 10.844 | 5.222 | 1.304× | 0.376× | 0.808× |
| random_4_n65536 | 19.624 | 14.854 | 58.160 | 27.764 | 1.337× | 0.341× | 0.706× |
| random_4_n262144 | 107.357 | 64.721 | 367.060 | 167.878 | 1.647× | 0.295× | 0.611× |

KKT leads all competitors by paired case medians in: `unbalanced_bipartite_16_n4096`, `unbalanced_bipartite_16_n16384`, `unbalanced_bipartite_16_n65536`, `unbalanced_bipartite_16_n262144`, `unbalanced_bipartite_256_n4096`, `unbalanced_bipartite_256_n16384`, `unbalanced_bipartite_256_n65536`, `unbalanced_bipartite_256_n262144`, `unbalanced_bipartite_sqrt_n4096`, `unbalanced_bipartite_sqrt_n16384`, `unbalanced_bipartite_sqrt_n65536`, `unbalanced_bipartite_sqrt_n262144`, `leaf_core_90_n16384`, `leaf_core_90_n65536`, `leaf_core_90_n262144`, `ring_cliques_16_n4096`, `ring_cliques_16_n16384`, `ring_cliques_16_n65536`, `hub_n4096`, `hub_n16384`, `hub_n65536`, `hub_n262144`.
The stricter descriptive check, a lead on every graph-level median against every competitor, holds in: `unbalanced_bipartite_16_n4096`, `unbalanced_bipartite_16_n16384`, `unbalanced_bipartite_16_n65536`, `unbalanced_bipartite_16_n262144`, `unbalanced_bipartite_256_n4096`, `unbalanced_bipartite_256_n16384`, `unbalanced_bipartite_256_n65536`, `unbalanced_bipartite_256_n262144`, `unbalanced_bipartite_sqrt_n4096`, `unbalanced_bipartite_sqrt_n16384`, `unbalanced_bipartite_sqrt_n65536`, `unbalanced_bipartite_sqrt_n262144`, `leaf_core_90_n16384`, `leaf_core_90_n65536`, `leaf_core_90_n262144`, `ring_cliques_16_n4096`, `ring_cliques_16_n16384`, `ring_cliques_16_n65536`, `hub_n4096`, `hub_n16384`, `hub_n65536`, `hub_n262144`.

![KKT against all competitors on every measured model](family_ratios.png)

All individual loss counts, ties, and graph-level ratio ranges remain in [comparisons.csv](comparisons.csv). [summary.csv](summary.csv) retains every algorithm's runtime, and [graph_summary.csv](graph_summary.csv) retains every graph seed.

## Separate logical-work diagnosis

The untimed probe certifies its reference MST independently and checks exact KKT IDs. Work summaries use arithmetic means across sampling seeds within each graph and then across the three graphs. They are separate from timing medians and cannot establish that sampling caused a runtime advantage.

At n=262,144, root reduction and recursion are:

| Family | Mean maximum degree | Mean leaves | Root edges retained | Sampling calls, range | Σm/m, mean | Heavy fraction, mean |
|---|---:|---:|---:|---:|---:|---:|
| Bipartite · 16-vertex side | 65849.0 | 0.0 | <0.01% | 1–1 | 1.0000 | 40.00% |
| Bipartite · 256-vertex side | 4285.7 | 0.0 | 0.18% | 2–3 | 1.0010 | 93.31% |
| Bipartite · floor(√n)-vertex side | 2184.0 | 0.0 | 0.76% | 3–3 | 1.0041 | 96.63% |
| Core with 50% attached leaves | 26.7 | 131132.0 | 60.24% | 7–7 | 1.3484 | 95.90% |
| Core with ≥90% attached leaves | 36.0 | 235930.0 | 23.59% | 5–7 | 1.1458 | 91.66% |
| Ring of 16-vertex cliques | 17.0 | 0.0 | 0.98% | 5–8 | 1.0164 | 0.31% |
| 2D grid · random weights | 4.0 | 0.0 | 10.75% | 14–15 | 1.1417 | 31.92% |
| 2D grid · distance weights | 4.0 | 0.0 | 13.62% | 14–15 | 1.1818 | 31.49% |
| 3D grid · random weights | 6.0 | 0.0 | 15.72% | 8–15 | 1.1330 | 72.15% |
| 3D grid · distance weights | 6.0 | 0.0 | 18.31% | 11–14 | 1.1621 | 70.14% |
| 8-regular graph | 8.0 | 0.0 | 75.88% | 7–7 | 1.4577 | 96.35% |
| Hub control | 262143.0 | 661.3 | 5.76% | 3–3 | 1.0411 | 78.74% |
| Random m=4n control | 27.0 | 321.3 | 75.42% | 7–7 | 1.4364 | 96.69% |

![Contraction and recursive edge volume](family_work.png)

Zero root-retained edges includes a finish after the first contraction. Heavy fractions divide summed heavy-edge incidences by verifier input incidences within each observation before averaging; they are not fractions of distinct original edges. Σm includes every recursive KKT input, including the root, but omits repeated internal passes. [work_summary.csv](work_summary.csv) retains all sizes and execution regimes; [graph_work_summary.csv](graph_work_summary.csv) retains graph-level means.

## Paired spatial weighting

Each random/distance pair shares the same graph topology, coordinates, labels, IDs, and input order by construction; only the unique weight ranks change. Distance ranks use squared jittered-coordinate distances with an ID tie-break. The fixture tests verify the pairing; CSV degree metrics are an additional consistency check, not a proof of equal topology.

Relative effects below are `(KKT/competitor with distance weights) / (KKT/competitor with random weights)`, formed within matched graph/sampling/repetition observations before applying the timing aggregation. Below 1× means the distance ordering improves KKT's relative runtime, not necessarily that KKT beats the competitor.

At n=262,144:

| Grid | Competitor | Paired relative effect | Graph-level range |
|---|---|---:|---:|
| 2D | Kruskal | 1.085× | 1.077–1.106× |
| 2D | Prim | 1.084× | 1.038–1.106× |
| 2D | Borůvka | 0.895× | 0.888–0.966× |
| 3D | Kruskal | 1.063× | 1.061–1.075× |
| 3D | Prim | 1.129× | 1.108–1.133× |
| 3D | Borůvka | 1.062× | 1.033–1.092× |

![Paired effect of distance versus random weight ordering](spatial_weighting.png)

[spatial_comparisons.csv](spatial_comparisons.csv) retains these relative effects and each algorithm's own distance/random runtime ratio, including all sizes and individual losses/ties. [spatial_graph_summary.csv](spatial_graph_summary.csv) retains every graph seed.

## Core and leaf parameters

The smaller bipartite sides have 16, 256, or floor(√n) vertices; every other vertex has four distinct neighbors on that side. Attached-leaf models use cores of floor(n/2) or floor(n/10) vertices with 4c core edges and one edge per added leaf. The nominal 90% setting therefore has a leaf attachment fraction at least 90%, with integer rounding. At n=65,536, the fixed-256 and floor(√n) variants are byte-identical weighted inputs per graph seed; their separately retained timings are an intentional parameter alias, not independent graph evidence. Other parameter settings change both graph instances and edge counts; they do not hold every other property fixed.

![Runtime ratios by core and attached-leaf parameters](core_leaf_parameters.png)

## Limits

These are synthetic models, not representative application datasets or a workload-weighted ranking. Three graph seeds are the independent graph samples; sampling labels and repetitions are not extra graphs. Graph ranges are descriptive, not confidence intervals, and no statistical significance or asymptotic crossover is claimed. Lines connect measured sizes only. Every family has distinct weights. Grid distance variants order weights by geometry; the other variants shuffle weight ranks. Topology labels alone do not describe every real graph with a similar name.

All four algorithms use the common tuple-edge-list boundary. KKT conversion and temporary input destruction are included; fixture generation, reference certification, result checks, and returned-result destruction are excluded. The rotating order is balanced within each graph/sampling pair. Ordinary desktop scheduling, cache/allocator state, and power/thermal variation can still affect measurements. Consult campaign metadata for binary, source, and build provenance.
