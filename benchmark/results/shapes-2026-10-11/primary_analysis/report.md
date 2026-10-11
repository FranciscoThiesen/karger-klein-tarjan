# Graph-shape experiment

Validated **24 cases and 3,456 timed observations**, with three graph seeds, three sampling-seed labels, 4 repetitions, and one warmup per algorithm/seed pair. The complete requested matrix retains all eight families at sizes 4096, 16384, 65536. Six added shapes and the hub/random-4 controls were selected before these measurements; no family is dropped according to its result.

Median of repetitions for each graph/sampling-seed pair; median of the three sampling-seed values per graph; median of the three graph values. Paired ratios apply the same hierarchy to matched algorithm/reference elapsed-time ratios. Error bars span graph-level medians and are not confidence intervals.

Lower ratios favor KKT. Displayed runtime medians and paired ratios are aggregated separately; dividing displayed times need not reproduce the paired ratios.

| Case | KKT ms | Kruskal ms | Prim ms | Borůvka ms | KKT/Kruskal | KKT/Prim | KKT/Borůvka |
|---|---:|---:|---:|---:|---:|---:|---:|
| preferential_attachment_n4096 | 0.677 | 0.694 | 2.043 | 0.931 | 0.960× | 0.329× | 0.746× |
| preferential_attachment_n16384 | 3.240 | 3.234 | 10.816 | 4.372 | 1.004× | 0.301× | 0.734× |
| preferential_attachment_n65536 | 15.682 | 14.530 | 60.077 | 21.860 | 1.081× | 0.264× | 0.721× |
| small_world_n4096 | 0.756 | 0.728 | 1.841 | 1.076 | 1.042× | 0.410× | 0.695× |
| small_world_n16384 | 3.184 | 3.267 | 9.043 | 5.226 | 0.968× | 0.345× | 0.611× |
| small_world_n65536 | 14.032 | 14.797 | 46.443 | 27.460 | 0.944× | 0.301× | 0.504× |
| multi_hub_n4096 | 0.315 | 0.689 | 1.678 | 0.501 | 0.461× | 0.190× | 0.624× |
| multi_hub_n16384 | 1.366 | 3.215 | 8.688 | 2.239 | 0.433× | 0.154× | 0.614× |
| multi_hub_n65536 | 5.853 | 14.015 | 44.939 | 9.958 | 0.416× | 0.131× | 0.596× |
| community_sparse_n4096 | 0.700 | 0.717 | 1.754 | 0.968 | 0.956× | 0.398× | 0.700× |
| community_sparse_n16384 | 3.359 | 3.174 | 10.095 | 5.207 | 1.071× | 0.345× | 0.661× |
| community_sparse_n65536 | 17.465 | 14.635 | 55.538 | 28.211 | 1.192× | 0.316× | 0.611× |
| balanced_bipartite_n4096 | 0.874 | 0.704 | 2.012 | 1.019 | 1.243× | 0.431× | 0.831× |
| balanced_bipartite_n16384 | 4.187 | 3.234 | 10.872 | 4.643 | 1.297× | 0.384× | 0.885× |
| balanced_bipartite_n65536 | 19.152 | 14.727 | 57.711 | 27.036 | 1.311× | 0.332× | 0.711× |
| balanced_binary_tree_n4096 | 0.252 | 0.129 | 0.433 | 0.612 | 1.937× | 0.582× | 0.418× |
| balanced_binary_tree_n16384 | 1.204 | 0.737 | 2.017 | 3.308 | 1.630× | 0.598× | 0.373× |
| balanced_binary_tree_n65536 | 5.067 | 3.386 | 9.053 | 15.396 | 1.487× | 0.564× | 0.329× |
| hub_n4096 | 0.526 | 0.710 | 2.035 | 0.835 | 0.733× | 0.255× | 0.647× |
| hub_n16384 | 2.338 | 3.219 | 11.269 | 3.814 | 0.731× | 0.210× | 0.605× |
| hub_n65536 | 10.700 | 14.529 | 58.277 | 17.787 | 0.735× | 0.182× | 0.601× |
| random_4_n4096 | 0.870 | 0.711 | 2.000 | 1.029 | 1.216× | 0.443× | 0.866× |
| random_4_n16384 | 4.163 | 3.221 | 10.845 | 5.113 | 1.279× | 0.385× | 0.814× |
| random_4_n65536 | 19.616 | 14.639 | 58.558 | 26.984 | 1.334× | 0.334× | 0.726× |

KKT leads all competitors by paired case medians in: `preferential_attachment_n4096`, `small_world_n16384`, `small_world_n65536`, `multi_hub_n4096`, `multi_hub_n16384`, `multi_hub_n65536`, `community_sparse_n4096`, `hub_n4096`, `hub_n16384`, `hub_n65536`.
The stricter descriptive check, a lead on every graph-level median against every competitor, holds in: `preferential_attachment_n4096`, `small_world_n16384`, `small_world_n65536`, `multi_hub_n4096`, `multi_hub_n16384`, `multi_hub_n65536`, `community_sparse_n4096`, `hub_n4096`, `hub_n16384`, `hub_n65536`.

![KKT against all competitors on every measured shape](shape_ratios.png)

All individual loss counts, ties, and graph-level ratio ranges remain in [comparisons.csv](comparisons.csv). [summary.csv](summary.csv) retains every algorithm's runtime, and [graph_summary.csv](graph_summary.csv) retains every graph seed.

## Separate logical-work diagnosis

The untimed probe certifies its reference MST independently and checks exact KKT IDs. Work summaries use arithmetic means across sampling seeds within each graph and then across the three graphs. They are separate from timing medians and cannot establish that sampling caused a runtime advantage.

At n=65,536, root reduction and recursion are:

| Family | Mean maximum degree | Mean leaves | Root edges retained | Sampling calls, range | Σm/m, mean | Heavy fraction, mean |
|---|---:|---:|---:|---:|---:|---:|
| Preferential attachment | 820.3 | 0.0 | 49.44% | 3–3 | 1.2612 | 97.07% |
| Small world | 12.7 | 0.0 | 10.97% | 7–7 | 1.1096 | 74.35% |
| Sixteen hubs | 16533.7 | 0.0 | <0.01% | 1–1 | 1.0000 | 14.81% |
| Sparse communities | 25.3 | 81.7 | 48.23% | 7–7 | 1.2716 | 94.34% |
| Balanced bipartite | 25.7 | 79.0 | 72.88% | 4–7 | 1.4018 | 96.41% |
| Balanced binary tree | 3.0 | 32768.0 | 6.80% | 4–5 | 1.1065 | 0.00% |
| Hub control | 65535.0 | 166.7 | 6.05% | 2–3 | 1.0429 | 79.06% |
| Random m=4n control | 26.0 | 80.0 | 73.08% | 6–7 | 1.4041 | 96.40% |

![Contraction and recursive edge volume](shape_work.png)

Zero root-retained edges includes a finish after the first contraction. Heavy fractions divide summed heavy-edge incidences by verifier input incidences within each observation before averaging; they are not fractions of distinct original edges. Σm includes every recursive KKT input, including the root, but omits repeated internal passes. [work_summary.csv](work_summary.csv) retains all sizes and execution regimes; [graph_work_summary.csv](graph_work_summary.csv) retains graph-level means.

## Limits

These are synthetic models, not representative application datasets or a workload-weighted ranking. Three graph seeds are the independent graph samples; sampling labels and repetitions are not extra graphs. Graph ranges are descriptive, not confidence intervals, and no statistical significance or asymptotic crossover is claimed. Lines connect measured sizes only. Family weights are distinct and randomized; topology labels alone do not describe every real graph with a similar name.

All four algorithms use the common tuple-edge-list boundary. KKT conversion and temporary input destruction are included; fixture generation, reference certification, result checks, and returned-result destruction are excluded. The rotating order is balanced within each graph/sampling pair. Ordinary desktop scheduling, cache/allocator state, and power/thermal variation can still affect measurements. Consult campaign metadata for binary, source, and build provenance.
