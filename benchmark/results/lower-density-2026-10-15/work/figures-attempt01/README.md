# Lower-density diagnostic figures

These six supplementary figures show cumulative logical work for the completed fixed 60-input diagnostic matrix. They do not measure runtime, CPU cycles, allocator bytes, cache misses or causal contributions to the timing results. The independent raw counter audit passed all 11,700 counter cells, 120 complete comparator replay chains (1,236 round rows), 60 query summaries and 30 topology-twin checks. See the [audit](../independent-counter-audit-attempt01/audit.json), [protocol](../PROTOCOL.md) and [canonical analysis](../analysis-attempt01/provenance.json).

| Figure | Scope |
|---|---|
| [Distance, d=16](counts_leaf_distance4_d16.png) · [PDF](counts_leaf_distance4_d16.pdf) | Eight counters, seven sizes, all three solvers |
| [Shuffled, d=16](counts_leaf_shuffled4_d16.png) · [PDF](counts_leaf_shuffled4_d16.pdf) | Same counters and sizes for the matched weight-shuffled controls |
| [Distance, d=8](counts_leaf_distance4_d8.png) · [PDF](counts_leaf_distance4_d8.pdf) | Eight counters, eight sizes, all three solvers |
| [Shuffled, d=8](counts_leaf_shuffled4_d8.png) · [PDF](counts_leaf_shuffled4_d8.pdf) | Same counters and sizes for the matched weight-shuffled controls |
| [Comparator continuation rounds](comparator_rounds.png) · [PDF](comparator_rounds.pdf) | Both full Borůvka replays across all four family/density groups |
| [Cumulative query compression](query_compression.png) · [PDF](query_compression.pdf) | Both graphs' within-call unique-query ratio across all four groups |

The four counter figures normalize each whole-solve count by the original input edge count m. They include the eight predeclared fields for KKT with private scalar sampling probability 1/8, deduplicating Borůvka and retained-edge Borůvka. Down/up triangles identify graph seeds 23000003/23000029; segments show their full range and lines their median. The sampler seed is 3407 throughout. Seven d=16 sizes and eight d=8 sizes remain separate, with every measured size explicitly labeled. Lines guide the eye between measured sizes and do not estimate unmeasured instances or a crossover location.

The scope includes tuple-to-Edge construction, the solver and temporary input destruction. Generation, independent certification and comparator replay lie outside the counter scope. KKT values include all recursive calls. Comparator sampling and verifier counts are zero by construction; coincident zero series overlap visually but both remain in the plotted data. Logical Edge materializations exclude uninstrumented vector relocation work. Different counted operations need not have equal machine cost.

The round figure counts full comparator continuations, not KKT recursion depths. The deduplicating and retained-edge round series coincide for these inputs and therefore overplot; neither has been omitted. The complete per-round inputs, outputs and selected-edge counts remain in the canonical tables.

For query compression, Q sums verifier queries and U = path_query_visits − 2Q sums unique requests within individual verifier-tree calls. U/Q is a ratio of cumulative counts, not global query uniqueness or an average of per-call ratios. Undefined Q=0 cases are retained by the export and would be annotated rather than replaced with zero. Scalar MT engine-word consumption equals sampling_edge_visits exactly for this implementation; it is not an m/32 estimate.

The plots preserve 1,440 selected counter observations, 120 comparator round totals and 60 query observations. All 65 fields per solver remain in the [canonical CSVs](../analysis-attempt01/work.csv), including 120 explicitly null unmeasured comparator hash-counter cells. Zero is not substituted for these nulls. [Plotted counts](plotted_counts.csv), [rounds](plotted_rounds.csv) and [queries](plotted_queries.csv) are archived alongside the figures.

Rendering completed on the first attempt with actual exit 0, an empty owned process group and unchanged script hashes; no native solver was launched. All six PNGs were inspected at original resolution and passed the separate [visual QA receipt](VISUAL_QA.json). The producer's immutable provenance retains its initial `visual_review: pending`; the separate receipt records the subsequent review. This is supplementary figure QA, not a claim about readability after arbitrary page resizing. See [render provenance](provenance.json) and the [guard receipt](../../validation/work-plots-attempt01.json).
