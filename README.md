## A minimalist README

The objectives of this projects are the following:

1. Make a C++ implementation of the [Karger, Klein & Tarjan algorithm](http://cs.brown.edu/research/pubs/pdfs/1995/Karger-1995-RLT.pdf) for finding MSTs in expected linear time available.
2. Benchmark the implementation against standard MST methods (Kruskal, Prim, Boruvka)



### How to build the project

1. Install [Bazel](https://bazel.build/)

2. Run the following command on your command line:

   ```bash
   $ bazel build :all
   ```



### How to run the tests

1. Build the project in the way described above

2. Run the following command at your command line:

   ```bash
   $ bazel test :all
   ```

   

### TODO

1. Implement the Karger, Klein & Tarjan algorithm by making use of the already implemented linear-time verifier.
2. Benchmark it against Boruvka, Prim and Kruskal
3. Improve comments
