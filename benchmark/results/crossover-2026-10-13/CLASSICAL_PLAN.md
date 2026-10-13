# Predeclared classical adjunct

Declared after the discovery and extension captures and before any real
classical-adjunct timing. The precision capture is still running.

Use three discovery inputs with graph seed 3037 and KKT seed 101:

- `hierarchical_path`, n=1,048,576, m=16n: previously confirmed favorable shape.
- `line_metric`, n=4,194,304, m=16n: largest initial geometric-line candidate.
- `grid2d_metric`, n=1,048,576, m=16n: variable local MST geometric control.

The manifest fixes this order. Run unchanged public KKT, Kruskal, Prim and
original Boruvka, with one checked warmup and four fully rotated repetitions.
Bind graph fingerprints to `discovery_timing.csv`. Use the already built and
frozen `crossover_baselines` binary and `run_crossover_baselines.py` wrapper;
archive their hashes and full source inventory. Run only after the precision
capture finishes, with no simultaneous native measurement, build or rendering.
All outputs must pass the independent MST certificate and exact edge-ID checks.
Retain every timing, including losses and flagged clocks.

This is a selected, single-graph exploratory adjunct, not another confirmation
campaign. Original Boruvka here is distinct from compacting Boruvka in the
main experiment. Public return representations differ, as in the repository's
original diverse benchmark: KKT returns IDs, classical solvers return tuples.
Do not combine absolute KKT times from separate executables/campaigns into
paired compactor comparisons. Report the within-adjunct medians and all raw
observations, with wall time primary and process CPU secondary.
