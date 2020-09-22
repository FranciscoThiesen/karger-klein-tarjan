## A C++ implementation of Karger-Klein-Tarjan Algorithm, using T. Hagerup mst verification algorithm as sub-routine.

The objectives of this projects are the following:

1. Provide a C++ implementation of [Karger, Klein & Tarjan algorithm](http://cs.brown.edu/research/pubs/pdfs/1995/Karger-1995-RLT.pdf) for finding MSTs in expected linear time available.
2. Benchmark the implementation against standard MST methods (Kruskal, Prim, Boruvka)

### Assumptions regarding input graphs:
1. All implementations of this project assume that the edge weights are unique, this is mentioned on the KKT paper as a requirement
and it simplifies the design/analysis of the algorithm.
2. We are at all times dealing with __undirected graphs__!!

### How to build the project

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
1. Build the project as described above

2. Run the following command at your command line:
    
    ```bash
    $ bazel run benchmark:mst_benchmark -c opt
    ```

### Benchmark Comments
All MST algorithms have been tested with random undirected connected graphs with unique discrete edge weights.
The runtime complexity has been estimated automatically by using [google/benchmark](https://github.com/google/benchmark#asymptotic-complexity)

### Results
1. The KKT implementation provided here is also linear in practice, please see the result file under the benchmark dir.
2. All the other tested algorithms don't have linear complexity in theory and this is also true for the benchmark graph instances.
3. The KKT algorithm still performed poorly compared to the other algorithms, because of it's huge constant factor.
