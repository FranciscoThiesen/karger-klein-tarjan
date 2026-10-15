# Compressed-query logical work diagnostics

All 24 diagnostic children and 72 solver outputs passed certification. Strict reload and independent raw-counter reconstruction passed all 12 matched pairs. Both Borůvka continuations have identical counter records and round sequences across variants (24 comparator-pair checks). The collector and every native process group were confirmed empty. These are untimed diagnostics; process durations are not performance observations.

Of 65 KKT fields, 61 are exactly unchanged on every pair. This includes sampling, recursion, contraction, verifier logical-query volume and final output work. The remaining four fields satisfy the declared identities exactly:

```text
U = compressed.path_query_visits - 2Q
reference.path_query_visits = 4Q
initialized slots saved = M + Q - U + T
path-query visits saved = 2Q - U
verifier edge visits saved = M
verifier vertex visits added = Nsum
```

Here Q is logical proper-ancestor requests, M cumulative connected-tree query-edge volume, T connected-tree verifier calls, and Nsum cumulative FBT output vertices. U sums per-call distinct (vertex,ancestor-depth) requests. It is not globally unique across recursive graphs and is not a per-call distribution.

Across the 12 graph/case pairs, U/Q ranges from 0.002696 to 0.008738, with descriptive median 0.005194. All 12 have positive Q. Every individual value remains below.

| Case | Graph seed | Q | U | U/Q | M | T | Nsum |
|---|---:|---:|---:|---:|---:|---:|---:|
| gnm_random_n1048576_d16_p0 | 8000009 | 54744556 | 295878 | 0.005405 | 27372278 | 8 | 68981 |
| gnm_random_n1048576_d16_p0 | 8000023 | 54408720 | 293315 | 0.005391 | 27204360 | 8 | 68787 |
| gnm_random_n4096_d16_p0 | 8000009 | 169934 | 644 | 0.003790 | 84967 | 3 | 270 |
| gnm_random_n4096_d16_p0 | 8000023 | 169710 | 848 | 0.004997 | 84855 | 3 | 266 |
| leaf_hierarchy4_n1048576_d32_p0 | 8000009 | 121675642 | 948715 | 0.007797 | 60837821 | 35 | 270093 |
| leaf_hierarchy4_n1048576_d32_p0 | 8000023 | 121252804 | 1059511 | 0.008738 | 60626402 | 35 | 269522 |
| leaf_hierarchy4_n65536_d32_p0 | 8000009 | 7089092 | 58779 | 0.008291 | 3544546 | 19 | 16830 |
| leaf_hierarchy4_n65536_d32_p0 | 8000023 | 7057508 | 59774 | 0.008470 | 3528754 | 17 | 16754 |
| leaf_shuffled4_n1048576_d32_p0 | 8000009 | 113491254 | 436405 | 0.003845 | 56745627 | 10 | 88518 |
| leaf_shuffled4_n1048576_d32_p0 | 8000023 | 117339692 | 371075 | 0.003162 | 58669846 | 10 | 88137 |
| leaf_shuffled4_n65536_d32_p0 | 8000009 | 6295310 | 16970 | 0.002696 | 3147655 | 6 | 5430 |
| leaf_shuffled4_n65536_d32_p0 | 8000023 | 6725504 | 21084 | 0.003135 | 3362752 | 7 | 5536 |

Full-counter compressed/reference ratios below summarize all 12 pairs; ranges are descriptive. The added vertex traversal is retained explicitly.

| Counter | Decreased / equal / increased pairs | Min ratio | Median ratio | Max ratio |
|---|---:|---:|---:|---:|
| verifier_vertex_visits | 0 / 0 / 12 | 1.744396 | 2.000000 | 2.000000 |
| verifier_edge_visits | 12 / 0 / 0 | 0.667000 | 0.667321 | 0.668787 |
| path_query_visits | 12 / 0 / 0 | 0.500674 | 0.501298 | 0.502185 |
| initialized_slots | 12 / 0 / 0 | 0.412430 | 0.423616 | 0.428960 |

[All 65-field summary](counter_difference_summary.csv), [all 780 paired field rows](paired_kkt_work.csv), [12 query pairs](query_compression.csv), [all solver work](work.csv), [round replays](rounds.csv), and [independent reconstruction](report.json) preserve zeros, both graph seeds, every case and increased work. Comparator final-set insertion remains explicitly unmeasured/null.

The WorkStats boundary includes tuple-to-Edge construction, solver work and temporary input destruction; generation, certification, result checking and independent round replay are outside it. These aggregate logical counts measure neither bytes moved nor allocations, cache effects or peak memory. They do not establish runtime causality.

The [prospective protocol](../PROTOCOL.md), [freeze](../freeze.json), [readiness check](../readiness.json), [execution receipt](../capture-attempt01-execution.json) and [strict analysis receipt](../analysis-attempt01-execution.json) bind the existing instrumented objects and timing fingerprints. No binary was rebuilt. Reproduce canonical analysis with `python3 -B collect.py analyze --capture capture-attempt01.json --output-dir FRESH_DIRECTORY` from the work directory; existing analysis output refuses overwrite.
