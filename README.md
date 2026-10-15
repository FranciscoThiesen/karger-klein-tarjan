## A C++ implementation for an Expected Linear-Time Minimum Spanning Tree Algorithm(Karger-Klein-Tarjan + Hagerup Minimum Spanning Tree Verification as a sub-routine)

This was the product of my CS undergraduate thesis. I was studying randomized algorithms and I couldn't find any reasonable implementation of Karger-Klein-Tarjan algorithm (at least a public one), so I decided to implement it myself and make it public.


The objectives of this projects are the following:

1. Provide a C++ implementation of [Karger, Klein & Tarjan algorithm](http://cs.brown.edu/research/pubs/pdfs/1995/Karger-1995-RLT.pdf) for finding MSTs in expected linear time available.
2. Benchmark the implementation against standard MST methods (Kruskal, Prim, Boruvka)

### Assumptions regarding input graphs:
1. All implementations of this project assume that the edge weights are unique, this is mentioned on the KKT paper as a requirement
and it simplifies the design/analysis of the algorithm.
2. We are at all times dealing with __undirected graphs__!!

### How to build the project

For a dependency-free C++17 build and correctness tests, run:

```bash
make -j4 test
```

Objects are written to `.build/` so they do not collide with Bazel's `BUILD`
file on case-insensitive filesystems. On macOS, Make uses the system Clang
and its SDK; `CXX`, `CPPFLAGS`, `CXXFLAGS`, and `LDFLAGS` can be overridden.
`make debug` builds separate sanitizer binaries in `bin/debug/`.

Alternatively, use Bazel:

1. Install [Bazel](https://bazel.build/)

2. Run the following command on your command line:

   ```bash
   $ bazel build :all
   ```


### How to run tests
1. Build the project in the way described above

2. Run the following command at your command line:

   ```bash
   $ bazel test :all --cache_test_results=no
   ```

### How to run benchmarks

The [15 October investigation](docs/kkt-report/current-2026-10-15/README.md)
collects the implementation repairs, current Google Benchmark fits, six-solver
comparisons, graph visualizations and audited work counts. The distance-ranked
family at m=16n crosses from a loss to a sustained strong lead over retained-edge
compacting Borůvka between 512 and 8,192 vertices, reaching a KKT/Borůvka time
ratio of 0.709 at 2,097,152 vertices. Shuffled controls lose, the density-8 lead
reverses at its largest size, and Kruskal wins all four largest endpoints.
These are measured implementation-specific results; the current complexity
curves receive N log N fits, not confirmation of linear runtime.

The [earlier in-depth KKT report](docs/kkt-report/REPORT.md) explains the original
complexity defects, historical Google Benchmark fits, and repeated comparisons
across 11 new graph variants and two unchanged controls. Its [offline HTML edition](docs/kkt-report/report.html)
includes an interactive 3D explorer of certified contraction and filtering
results. The [raw evidence and protocol](benchmark/results/common-2026-10-11/README.md)
retain every measured case, including a compacting-Borůvka ablation that
compares repeated production contraction with KKT continuation.

The [compacting-Borůvka follow-up](benchmark/results/continuation-2026-10-12/README.md)
finds a repeated KKT advantage on engineered hierarchical graphs: 17–19% less
median time at one million vertices and 16.8 million edges. Both solvers are
unchanged. The report retains ordinary random-graph losses, shows how cheap
shortcut perturbations remove the advantage, and documents desktop power-state
interruptions in the timing campaigns.

The [larger-instance and mechanism study](benchmark/results/crossover-2026-10-13/README.md)
extends the search to 8.4 million vertices and 134 million edges. The hierarchy
still favors KKT over compaction at four million vertices; geometric and random
families show smaller, inconsistent gains. The report explains the hierarchy's
repeated edge scans, retains the failed baseline stack run, and shows that
Kruskal and original Borůvka win the three selected classical comparisons.

The [earlier implementation investigation](benchmark/results/practical-2026-10-10/README.md)
records six accepted optimizations, a rejected experiment, fresh complexity
diagnostics, and repeated comparisons with Kruskal, Prim, and Borůvka.
It retains the original fixtures, correctness gates, and all measured losses;
the reports below also preserve the earlier implementations' results.

The [graph-shape follow-up](benchmark/results/shapes-2026-10-11/README.md)
adds preferential attachment, small-world, multiple-hub, sparse-community,
bipartite, and balanced-tree fixtures. Run `./bin/diverse_benchmark --shapes`
for the complete new matrix, or `--smoke-shapes` for its correctness smoke run.
The report includes repeated comparisons and separate contraction counters.

The [four-algorithm comparison](benchmark/results/diverse-2026-10-10/README.md)
covers 39 configurations across random graphs, grids, hubs, clusters, trees,
paths, and complete graphs, with correctness checks and downloadable plots:

```bash
make -j4 diverse-benchmark
./bin/diverse_benchmark --scale > diverse.csv
python3 benchmark/analyze_diverse.py diverse.csv --output-dir diverse-plots
```

Plotting requires NumPy and Matplotlib. These timings include KKT's conversion
from the common edge-list input; see the comparison's methods for details.

The [larger-instance follow-up](benchmark/results/large-2026-10-10/README.md)
extends seven profiles to 1,048,576 vertices and 33,554,432 edges, with a
separate density sweep at fixed vertex count:

```bash
./bin/diverse_benchmark --large --repetitions 1 --warmups 0 > large.csv
python3 benchmark/analyze_large.py large.csv --output-dir large-plots --expected-cases 18
```

This exploratory sweep varies graph and sampling seeds. Close results need
additional repetitions; its timing protocol differs from the smaller sweep.

The [complexity diagnostics](benchmark/results/complexity-2026-10-10/README.md)
separate logical work from elapsed time. GoogleTest checks deterministic work
bounds and correctness; Google Benchmark fits finite timing ranges:

```bash
bazel test //:complexity_test -c opt --enable_bzlmod=false
bazel run //benchmark:work_sweep -c opt --enable_bzlmod=false -- --large > work.csv
bazel run //benchmark:complexity_benchmark -c opt --enable_bzlmod=false -- --benchmark_out=timing.json --benchmark_out_format=json
python3 benchmark/analyze_complexity.py --work-csv work.csv --timing-json timing.json --output-dir complexity-plots
```

The work sweep also builds with `make work-sweep`. Instrumentation is enabled
only in dedicated libraries; normal builds have no counter collection. Neither
passing tests nor a fitted complexity label proves an asymptotic bound.

The dependency-free scaling benchmark varies vertex count at fixed densities,
varies density at fixed vertex count, and includes hierarchical paths:

```bash
make -j4 scaling-benchmark
./bin/scaling_benchmark --smoke > smoke.csv
./bin/scaling_benchmark --scale > scaling.csv
```

The default scale preset uses three graph seeds, three KKT sampling seeds,
one warmup, and three repetitions per seed pair. Use `--repetitions N` and
`--warmups N` to change those counts. Every timed result is checked against
Kruskal's exact edge-ID set on distinct-weight inputs; failures return a nonzero
exit status. Keep the complete CSV, including slow cases.

Both algorithms time their public call with input construction, validation,
and result destruction excluded. Algorithm order alternates. Record the source
revision, compiler version, build flags, CPU/OS, and command with each run.
For example, `make -B -n scaling-benchmark` prints the build commands without
executing them. Measurements describe those workloads and do not prove an
asymptotic bound.

The [2026-10-09 repair measurements](benchmark/results/repair-2026-10-09/README.md)
retain raw timings, exact revisions, and remaining losses. On the measured
Apple M3 Max workloads, repaired KKT is 2.2–4.5x faster than the starting
implementation; Kruskal still wins several sparse and hierarchical-path cases.

The older Google Benchmark comparison remains available:

```bash
bazel run benchmark:mst_benchmark -c opt
```

`benchmark/benchmark_result.txt` contains historical results predating the
current repairs. Its fixed vertex count and automatic complexity fits do not
establish linear scaling when both vertices and edges grow. The current legacy
harness no longer reports those fitted complexity labels.
