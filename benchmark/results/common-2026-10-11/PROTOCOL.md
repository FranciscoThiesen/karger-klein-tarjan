# Fixed plan before timing

The previous 24-case shapes study motivated this experiment. Its results are
retained separately; this matrix is exploratory follow-up, not an independent
out-of-sample confirmation of the previous family-selection hypotheses.

- Thirteen families: eleven new model variants plus unchanged `hub` and
  `random_4` controls. Four sizes: 4,096, 16,384, 65,536, 262,144 vertices.
- New models: bipartite peripheral-degree-four graphs with small partitions
  16, 256, and floor(sqrt(n)); random sparse cores with 50%/90% attached leaves;
  a ring of 16-vertex cliques; paired random/distance weighted 2D and 3D open
  grids; and a connected degree-eight switched regular graph.
- Every family and size remains in the report regardless of outcome. The
  regular graph and random control test the limits of the small-core hypothesis.
  Fixed small partitions, leaf fractions, clique size and grid dimensions are
  model parameters, not claims of real-world representativeness.
- The grid pairs have identical topology, labels, edge order and coordinates.
  Only the edge-weight assignment differs. Distance ranks preserve the exact
  squared-distance order, breaking ties by original edge ID.
- Three graph seeds (17,42,999), three KKT seeds (0,1,7), four repetitions,
  one checked warmup per algorithm/seed pair. Balanced rotating algorithm order.
  All four repository algorithms use the existing tuple-input timing boundary.
- One separately instrumented work campaign: 468 observations over156 graphs.
  Two complete, separately retained timing campaigns: each7,488 timed outputs
  plus1,872 checked warmups. No pooling or choice of the faster campaign.
- Every graph's reference MST receives an independent structure/cycle-optimality
  certificate; every timed output and warmup must match the unique MST IDs.
- Native Make -O3 -march=native, Apple clang15, Apple M3 Max. Instrumentation is
  excluded from timed binaries. Ordinary desktop activity remains uncontrolled.
  Builds, tests, plots and timed processes execute in separate phases.

Additional diagnostics, selected before these results:

1. Google Benchmark's existing `Complexity(oAuto)` / `SetComplexityN(n+m)` /
   `UseManualTime` harness gains a separate `--common` mode for bipartite16,
   ring-cliques16, 3D-distance, 90%-leaf core and regular8. Nine doubling sizes
   1,024..262,144; two algorithms; three graph seeds; three batches of three
   calls each. 810 raw timing records represent2,430 calls. Bazel -O3/NDEBUG
   is a different build profile from the primary comparison. Built-in model
   labels and independently fitted manual-time curves are both retained.
2. A separate ablation compares KKT against repeated *production* compacting
   Boruvka steps, returning the same reserved ID hash set. Families:
   bipartite16, ring-cliques16, 3D-distance, 90%-leaf core, regular8, random4
   at4,096/65,536/262,144; small-world at4,096/65,536 (existing size support).
   Twenty cases,3graph x3sampling-seed labels x4repeats x2algorithms =1,440
   timed calls plus360warmups per run. Two runs, losses retained. The ablation
   does not change the four-algorithm ranking or become an optimized competitor
   silently; it tests whether switching to sampling pays for itself here.
3. Full small graph views at256 vertices, graph seed42 and sampling seed0.
   Production contraction outputs checked against an independent DSU reduction;
   forest-heavy labels checked by explicit path maxima. These are explanatory
   instances, not miniature substitutes for the timing matrix.

The same three graph seeds are a small descriptive sample. Min/max graph ranges
are not confidence intervals. Repeated calls and sampling seeds are not new
graphs. A finite timing fit cannot establish an asymptotic bound.
