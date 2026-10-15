# Independent eighth-extension numerical audit

PASS: 28 children and 1,176 outputs, including 1,008 timed calls and 168 checked warmups. All 1,680 paired clock ratios and all 924 comparison/absolute medians, ranges and counts match the strict analyzer. All 70 point states, 210 endpoint pairs and 10 sustained-crossover summaries were independently recomputed with exact Fraction arithmetic. All 28 certificates, fourteen topology twins, raw/combined concatenation and known-empty process-group evidence were rechecked; the complete frozen parent artifact chain was reread. No collector code was imported.

| Family | Comparator | Strong measured bracket | Smallest state | Largest state |
|---|---|---|---|---|
| leaf_hierarchy4 | compacting_boruvka | (1,024, 16,384] | loss | strong_lead |
| leaf_hierarchy4 | multigraph_boruvka | none | narrow_lead | strong_lead |
| leaf_hierarchy4 | kruskal | none | strong_lead | loss |
| leaf_hierarchy4 | prim | none | loss | loss |
| leaf_hierarchy4 | boruvka | (65,536, 1,048,576] | loss | strong_lead |
| leaf_shuffled4 | compacting_boruvka | (4,096, 65,536] | loss | strong_lead |
| leaf_shuffled4 | multigraph_boruvka | none | loss | loss |
| leaf_shuffled4 | kruskal | none | strong_lead | loss |
| leaf_shuffled4 | prim | none | loss | narrow_lead |
| leaf_shuffled4 | boruvka | none | loss | narrow_lead |

Retained flags: 0 calls and 0 capture/child UTC flags.

A bracket requires loss on both graphs/clocks at the lower endpoint, at least a 10% lead at the upper endpoint, and the same lead at every larger measured point. All endpoints and earlier reversals remain in the tables. These are measured brackets, not interpolated crossings or proof of asymptotic dominance. Six repetitions reuse each graph realization and one fixed scalar sampling seed; they are not independent forest samples. No historical timing or control-based normalization is used, and a win against one comparator is not an all-solver win.
