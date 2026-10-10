# Measurement methods

This comparison uses the repository's KKT, Kruskal, Prim, and Borůvka at
`bed1842dfdd6b25d173bee16b83706b39b0e6e04`. Algorithm sources are unchanged.
`metadata.json` records the exact harness hashes, compiler, flags, machine,
measurement command, and run time. Raw observations are in `raw.csv`;
`run.log` preserves execution order and process resource statistics.

## Matrix

All inputs are connected, simple, undirected graphs with distinct positive
integer weights and dense unique edge IDs. Random generation uses `mt19937`
and explicit Fisher–Yates shuffles; small modulo bias is accepted for these
synthetic fixtures. Every graph's vertex labels and input edge order are
shuffled, including deterministic topologies. These are synthetic workloads,
not samples of real application traffic.

| Profile | Construction | Vertex counts |
| --- | --- | --- |
| Random, m=4n | Random recursive tree backbone, then uniformly proposed missing endpoint pairs; shuffled weights | 1,024; 4,096; 16,384; 65,536 |
| Random, m=32n | Same construction at greater density | 1,024; 4,096; 16,384; 65,536 |
| Random, m=128n | Same construction at greater density | 1,024; 4,096; 16,384 |
| Dense random anchor | Same construction, 400,000 edges | 1,000 |
| Grid | Square lattice, four neighbors, independent shuffled edge weights | 1,024; 4,096; 16,384 |
| Geometric grid | Eight-neighbor lattice with jittered coordinates; weights are unique ranks of squared Euclidean lengths | 1,024; 4,096; 16,384 |
| Hub | Star backbone plus random chords to m=4n; shuffled weights | 1,024; 4,096; 16,384 |
| Clustered | 16 connected clusters; internal-edge target is min(16n, half the available intracluster pairs); 15 heavy bridges form a chain between clusters | 1,024; 4,096; 16,384 |
| Planted tree | Random recursive spanning tree lighter than all remaining chords; m=4n | 1,024; 4,096; 16,384 |
| Random tree | Each new vertex attaches to a uniformly chosen earlier vertex; shuffled weights | 1,024; 4,096; 16,384 |
| Star | One hub connected to every other vertex; shuffled weights | 1,024; 4,096; 16,384 |
| Hierarchical path | Edge (i-1,i) has weight n*v2(i)+i; successive pair contractions are forced | 1,024; 4,096; 16,384 |
| Complete | Every unordered vertex pair; shuffled weights | 256; 512; 1,024 |

The random-tree distribution is a random recursive tree, not a uniform labeled
tree. Adding edges to that backbone does not produce a uniform connected
G(n,m) sample. Distance ranking preserves edge order for the geometric MST;
this graph is a local jittered grid, not a general random geometric graph.
The smallest clustered case has 16,128 internal edges plus 15 bridges; the
larger clustered cases reach the 16n internal-edge target.

The matrix contains 39 configurations and 117 generated fixtures: three graph
seeds (17, 42, 999) per configuration. Each fixture uses KKT seeds 0, 1, 7,
one warmup per algorithm/seed pair, and four measured repetitions. This yields
36 timings per algorithm/configuration and 5,616 timed observations in total.
The deterministic baselines ignore the KKT-seed label; those entries are
additional timing repetitions, not independent graphs.

## Timing boundary and execution order

All four algorithms receive the same tuple edge list. For KKT, the timed
wrapper constructs `problem(n, graph)`, runs KKT, and destroys that temporary
input before the end timestamp. Prim's internal adjacency construction,
Kruskal's internal copy/sort, and Borůvka's internal preparation are also timed.
Output construction is included; returned-output destruction, graph generation,
reference computation, certification, output checking, and CSV writing are not.
KKT returns an ID hash set; the other implementations return edge vectors.

This boundary includes more KKT setup than the earlier repair benchmark, and
the graph generator also differs. The two experiments' absolute timings are
not directly interchangeable.

Case order is shuffled with seed 20261010. Within each graph/KKT-seed pair,
the four timed positions rotate so every algorithm appears in each position
once over the four repetitions. Warmups use a fixed algorithm order. The run
uses one process with no concurrent agent build/test/plot jobs; the ordinary
desktop session has no CPU affinity, power control, or background-process
isolation. The clock is `std::chrono::steady_clock`.

## Correctness

Before timing each fixture, Kruskal's reference is independently certified:

1. Validate endpoints, simple-graph structure, dense IDs, and unique weights.
2. Check that its n-1 returned edges belong to the input and form a connected,
   acyclic tree, using a separate disjoint-set implementation.
3. Check every input edge against the maximum-weight edge on its tree path
   using a separate binary-lifting implementation. Any cheaper replacement
   rejects the reference as nonminimal.

Every timed and warmup output must exactly match that certified edge-ID set.
Vector results must also have the correct edge count and input-matching tuples
(up to endpoint orientation). Any mismatch aborts the benchmark with a nonzero
exit status; the analyzer rejects incomplete, failed, duplicated, or unbalanced
samples. The certificate has positive and negative tests, including a
nonminimal candidate, cycles, invalid tuples, duplicate IDs, and total costs
above INT_MAX. Certificate checks are outside measured intervals.

## Interpretation

These are the repository implementations, not tuned representatives of every
algorithm. Prim uses `std::set`; Kruskal scans all sorted edges even after its
tree is complete; Borůvka repeatedly reconstructs components and scans the
original edge list, including one final convergence scan. Their shared input
domain here is connected graphs with positive distinct weights below Prim's
sentinel. Long paths stop at 16,384 vertices because Borůvka's traversal is
recursive; the largest path was preflighted successfully.

Plots aggregate repetitions first, then sampling seeds within each graph, then
graph seeds. Paired ratios use that same hierarchy on matched timing ratios.
Min/max bars span three graph-level medians, not confidence intervals. Near-one
ratios are not claims of statistically significant differences. Cases where
KKT loses remain in every summary. Winner counts describe this chosen matrix;
they are not workload-weighted rankings. No asymptotic bound is inferred from
these finite measurements.

## Reproduction

From the repository root (Python requires NumPy and Matplotlib):

```sh
make -j4 test diverse-benchmark
./bin/diverse_benchmark --scale > raw.csv 2> run.log
python3 benchmark/analyze_diverse.py raw.csv --output-dir results
```

`--case hierarchical_path_n16384` selects one named case. To validate the
smaller 25-case fixture matrix with balanced repetitions:

```sh
./bin/diverse_benchmark --smoke > smoke.csv
python3 benchmark/analyze_diverse.py smoke.csv --expected-cases 25 --output-dir smoke-plots
```

Smoke density caps can make some small random profiles identical; smoke data
is only a correctness check and is excluded from the published scale results.
