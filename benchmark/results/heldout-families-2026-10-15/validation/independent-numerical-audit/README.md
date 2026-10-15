# Independent held-out-family numerical audit

PASS: 72 children and 3,024 outputs, including 2,592 timed calls and 432 checked warmups. All 4,320 paired clock ratios and all 2,376 comparison/absolute medians, ranges and counts match the strict analyzer. All 180 point states, 450 endpoint pairs and 30 sustained-crossover summaries were independently recomputed with exact Fraction arithmetic. All 72 certificates, 36 topology twins, raw/combined concatenation and known-empty process-group evidence were rechecked; the complete frozen parent artifact chain was reread. No collector code was imported.

| Family | Comparator | Strong measured bracket | Smallest state | Largest state |
|---|---|---|---|---|
| leaf_distance4 | compacting_boruvka | (16,384, 262,144] | loss | strong_lead |
| leaf_distance4 | multigraph_boruvka | none | loss | narrow_lead |
| leaf_distance4 | kruskal | none | loss | loss |
| leaf_distance4 | prim | none | loss | loss |
| leaf_distance4 | boruvka | none | loss | loss |
| leaf_shuffled4 | compacting_boruvka | (16,384, 262,144] | loss | strong_lead |
| leaf_shuffled4 | multigraph_boruvka | none | loss | loss |
| leaf_shuffled4 | kruskal | none | loss | loss |
| leaf_shuffled4 | prim | none | loss | loss |
| leaf_shuffled4 | boruvka | none | loss | loss |
| grid2d_metric | compacting_boruvka | (16,384, 262,144] | loss | strong_lead |
| grid2d_metric | multigraph_boruvka | none | loss | loss |
| grid2d_metric | kruskal | none | loss | loss |
| grid2d_metric | prim | none | mixed_or_tied | strong_lead |
| grid2d_metric | boruvka | none | loss | loss |
| grid2d_random | compacting_boruvka | (16,384, 262,144] | loss | strong_lead |
| grid2d_random | multigraph_boruvka | none | loss | loss |
| grid2d_random | kruskal | none | narrow_lead | loss |
| grid2d_random | prim | (4,096, 65,536] | loss | strong_lead |
| grid2d_random | boruvka | none | loss | loss |
| line_metric | compacting_boruvka | (16,384, 262,144] | loss | strong_lead |
| line_metric | multigraph_boruvka | none | loss | loss |
| line_metric | kruskal | none | loss | loss |
| line_metric | prim | none | strong_lead | strong_lead |
| line_metric | boruvka | none | loss | loss |
| line_random | compacting_boruvka | (16,384, 262,144] | loss | strong_lead |
| line_random | multigraph_boruvka | none | loss | loss |
| line_random | kruskal | none | loss | loss |
| line_random | prim | (4,096, 65,536] | loss | strong_lead |
| line_random | boruvka | none | loss | loss |

Retained flags: 0 calls and 0 capture/child UTC flags.

A bracket requires loss on both graphs/clocks at the lower endpoint, at least a 10% lead at the upper endpoint, and the same lead at every larger measured point. All endpoints and earlier reversals remain in the tables. These are measured brackets, not interpolated crossings or proof of asymptotic dominance. Six repetitions reuse each graph realization and one fixed scalar sampling seed; they are not independent forest samples. No historical timing or control-based normalization is used, and a win against one comparator is not an all-solver win.
