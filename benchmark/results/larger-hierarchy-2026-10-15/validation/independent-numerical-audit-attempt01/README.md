# Independent larger-hierarchy numerical audit

PASS: 12 children and 504 outputs, including 432 timed calls and 72 checked warmups. All 720 paired clock ratios and all 396 comparison/absolute medians, ranges and counts match the strict analyzer. All 30 point states, 30 endpoint pairs and 10 sustained-crossover summaries were independently recomputed with exact Fraction arithmetic. All 12 certificates, six topology twins, raw/combined concatenation and known-empty process-group evidence were rechecked; the complete frozen parent artifact chain was reread. No collector code was imported.

| Family | Comparator | Strong measured bracket | Smallest state | Largest state |
|---|---|---|---|---|
| leaf_hierarchy4 | compacting_boruvka | none | strong_lead | strong_lead |
| leaf_hierarchy4 | multigraph_boruvka | none | loss | loss |
| leaf_hierarchy4 | kruskal | none | loss | loss |
| leaf_hierarchy4 | prim | none | loss | loss |
| leaf_hierarchy4 | boruvka | (1,048,576, 4,194,304] | loss | strong_lead |
| leaf_shuffled4 | compacting_boruvka | none | strong_lead | strong_lead |
| leaf_shuffled4 | multigraph_boruvka | none | loss | loss |
| leaf_shuffled4 | kruskal | none | loss | loss |
| leaf_shuffled4 | prim | none | loss | loss |
| leaf_shuffled4 | boruvka | none | loss | loss |

Retained flags: 0 calls and 0 capture/child UTC flags.

A bracket requires loss on both graphs/clocks at the lower endpoint, at least a 10% lead at the upper endpoint, and the same lead at every larger measured point. All endpoints and earlier reversals remain in the tables. These are measured brackets, not interpolated crossings or proof of asymptotic dominance. Six repetitions reuse each graph realization and one fixed scalar sampling seed; they are not independent forest samples. No historical timing or control-based normalization is used, and a win against one comparator is not an all-solver win.
