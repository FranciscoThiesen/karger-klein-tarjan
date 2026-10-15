# Independent lower-density numerical audit

PASS: 60 children and 2,520 outputs, including 2,160 timed calls and 360 checked warmups. All 3,600 paired clock ratios and all 1,980 comparison/absolute medians, ranges and counts match the strict analyzer. All 150 point states, 490 endpoint pairs and 20 sustained-crossover summaries were independently recomputed with exact Fraction arithmetic. All 60 certificates, thirty topology twins, raw/combined concatenation and known-empty process-group evidence were rechecked; the complete frozen parent artifact chain was reread. No collector code was imported.

| Family | Density | Comparator | Strong measured bracket | Smallest state | Largest state |
|---|---|---|---|---|---|
| leaf_distance4 | 16 | compacting_boruvka | (2,048, 32,768] | loss | strong_lead |
| leaf_distance4 | 16 | multigraph_boruvka | (512, 8,192] | loss | strong_lead |
| leaf_distance4 | 16 | kruskal | none | loss | loss |
| leaf_distance4 | 16 | prim | (2,048, 32,768] | loss | strong_lead |
| leaf_distance4 | 16 | boruvka | (32,768, 524,288] | loss | strong_lead |
| leaf_shuffled4 | 16 | compacting_boruvka | (8,192, 131,072] | loss | strong_lead |
| leaf_shuffled4 | 16 | multigraph_boruvka | none | loss | loss |
| leaf_shuffled4 | 16 | kruskal | none | narrow_lead | loss |
| leaf_shuffled4 | 16 | prim | (131,072, 2,097,152] | loss | strong_lead |
| leaf_shuffled4 | 16 | boruvka | (524,288, 2,097,152] | loss | strong_lead |
| leaf_distance4 | 8 | compacting_boruvka | (4,096, 262,144] | loss | strong_lead |
| leaf_distance4 | 8 | multigraph_boruvka | none | loss | mixed_or_tied |
| leaf_distance4 | 8 | kruskal | none | loss | loss |
| leaf_distance4 | 8 | prim | (256, 4,096] | loss | strong_lead |
| leaf_distance4 | 8 | boruvka | (4,096, 65,536] | loss | strong_lead |
| leaf_shuffled4 | 8 | compacting_boruvka | (16,384, 262,144] | loss | strong_lead |
| leaf_shuffled4 | 8 | multigraph_boruvka | none | loss | loss |
| leaf_shuffled4 | 8 | kruskal | none | loss | loss |
| leaf_shuffled4 | 8 | prim | (256, 16,384] | loss | strong_lead |
| leaf_shuffled4 | 8 | boruvka | (65,536, 1,048,576] | loss | strong_lead |

Retained flags: 0 calls and 0 capture/child UTC flags.

A bracket requires loss on both graphs/clocks at the lower endpoint, at least a 10% lead at the upper endpoint, and the same lead at every larger measured point. All endpoints and earlier reversals remain in the tables. These are measured brackets, not interpolated crossings or proof of asymptotic dominance. Six repetitions reuse each graph realization and one fixed scalar sampling seed; they are not independent forest samples. Densities are separate groups throughout; no historical timing or control-based normalization is used, and a win against one comparator is not an all-solver win.
