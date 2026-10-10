# Larger-instance experiment

This experiment extends the [diverse comparison](../diverse-2026-10-10/README.md)
without changing any MST implementation. Algorithm sources are those at
`93406577df5653572c1d795fcf471202145071f1` (unchanged since `bed1842`). The large
preset adds 18 configurations:

| Family | Vertex counts | Edge counts |
| --- | --- | --- |
| Random, `m = 4n` | 65,536; 262,144; 1,048,576 | 262,144 through 4,194,304 |
| Random, `m = 32n` | 65,536; 262,144; 1,048,576 | 2,097,152 through 33,554,432 |
| Random, `m = 128n` | 65,536; 262,144 | 8,388,608; 33,554,432 |
| Random, `m = 512n` | 65,536 | 33,554,432 |
| Hub | 65,536; 262,144; 1,048,576 | `4n` |
| Star | 65,536; 262,144; 1,048,576 | `n - 1` |
| Complete | 2,048; 4,096; 8,192 | `n(n - 1)/2` |

The random families use the previous generator: a random recursive tree ensures
connectivity, then uniformly proposed missing endpoint pairs fill the target.
Weights are a shuffled permutation of `1..m`; vertex labels and edge order are
shuffled. These are synthetic connected simple graphs, not uniform samples
from all connected graphs. Hub adds random chords to a star; star itself is a
tree. The fixed-vertex density sweep uses the four random cases at 65,536
vertices. It is separate from the fixed-`m/n` size sweeps.

## Timing and correctness

All algorithms start from the same tuple edge list. KKT's conversion into its
internal input and destruction of that temporary input are timed. Algorithm
work and output construction are timed; result validation and returned-result
destruction are outside the interval. Fixture generation, reference Kruskal,
and an independent MST certificate are outside the algorithm timing.

The certificate checks graph validity, source tuples, connectivity, acyclicity,
and the cycle optimality condition using independent binary lifting. Every
timed output must match the certified unique MST's complete edge-ID set;
vector outputs also have their endpoint/weight tuples checked. All sums in
the certificate use 64 bits. No result is accepted solely because its cost
matches Kruskal. `validation=pass` is written only after this check succeeds.

The main sweep uses graph seeds `17,42,999`, KKT seeds `0,1,7`, and one measured
call per graph/sampling-seed/algorithm block: nine observations per algorithm
and configuration. Deterministic baselines are remeasured in each block for
matched comparisons. There are no explicit warmup calls in this large sweep;
fixture generation and certification precede measurements. This differs from
the smaller experiment's one warmup and four repetitions per seed pair.

Within a block, the four algorithms run consecutively in rotating order:
`(position + repetition + graph_seed_index + sampling_seed_index) % 4`.
With one repetition, each algorithm occupies each position either two or
three times over the nine blocks. This is nearly, but not exactly, balanced.
Only one benchmark process runs at a time. Builds, tests, and plotting are
paused during measurement. The ordinary desktop session has no CPU affinity
or controlled power/thermal state. The machine has 128 GiB RAM.

Aggregation first takes the median across repetitions, then across sampling
seeds within each graph, then across graph seeds. Ratios apply that hierarchy
to matched elapsed-time ratios. Plot ranges span graph-level medians, not
confidence intervals. One-repetition data captures graph/sampling variation
but cannot estimate repeatability of an identical input and sampling stream.
Close races receive a separate confirmation run and are reported separately.
No smaller-experiment timings are mixed into these aggregates.

## Targeted confirmation

The preliminary sweep selected five cases for additional timing: hubs at
65,536 and 262,144 vertices, and stars at 65,536, 262,144, and 1,048,576 vertices.
These cover the close KKT/Kruskal races and the adjacent star size where KKT
falls behind. Each case runs in a fresh process with the same three graph
seeds and three KKT seeds, one warmup and four timed repetitions per seed
pair. Each algorithm consequently occupies every position equally within
each seed pair. The confirmation contains 720 timed outputs and 180 checked
warmups; it is analyzed separately from the 648-output main sweep.

On a star, KKT's first contraction finishes the tree, so the sampling seed
does not change execution. Its seed-labeled trials are already repetitions
of the same input; confirmation adds warmups and balanced positions. Near-one
ratios remain close races, not claims of statistical significance. Clear
random/complete-graph losses and the million-vertex hub loss are retained in
the main sweep without an expensive duplicate confirmation.

## Reproduction

From the repository root:

```sh
make -j4 test diverse-benchmark
/usr/bin/time -l ./bin/diverse_benchmark --large --repetitions 1 --warmups 0 > raw.csv 2> run.log
python3 benchmark/analyze_large.py raw.csv --output-dir large-plots --expected-cases 18
```

To reproduce one confirmation case:

```sh
./bin/diverse_benchmark --large --case hub_n65536 --repetitions 4 --warmups 1 > confirmation.csv
python3 benchmark/analyze_large.py confirmation.csv --output-dir confirmation-plots --expected-cases 1 --repetitions 4 --warmups 1
```

All five confirmation commands and their run order are recorded in
`confirmation/metadata.json`. The combined `confirmation/raw.csv` concatenates
their outputs with a single header.

`--case ID`, `--graph-seed SEED`, and `--kkt-seed SEED` allow individual cases
or pilots to be run. Main results require all three graph and sampling seeds.
The pilot is retained separately and excluded from the main aggregates.
`metadata.json` records exact commands, source hashes, compiler flags, machine,
and completion status. `/usr/bin/time -l` logs whole-process elapsed time and
peak resident memory, including fixture generation and correctness checks;
these are not per-algorithm memory measurements.

This experiment can locate an observed crossover in the measured families and
size range. It cannot establish that KKT will eventually dominate at arbitrary
sizes. There are no real-world datasets here, and no changes to the repository's
baseline implementations were made to make this comparison.
