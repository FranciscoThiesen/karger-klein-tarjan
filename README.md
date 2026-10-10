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

The older Google Benchmark comparison remains available:

```bash
bazel run benchmark:mst_benchmark -c opt
```

`benchmark/benchmark_result.txt` contains historical results predating the
current repairs. Its fixed vertex count and automatic complexity fits do not
establish linear scaling when both vertices and edges grow. The current legacy
harness no longer reports those fitted complexity labels.
