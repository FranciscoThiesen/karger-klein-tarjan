# Untimed work comparison after the multigraph screen

All **20 diagnostic children and 40 solver outputs passed**. Each child generated and independently certified the same input used in the timing screen, then checked KKT and compacting Boruvka against that unique MST. All 20 weighted/topology fingerprints match `screen.csv`. The unchanged compactor has **identical values for all 65 counters on every one of the ten cases**. These checks and diagnostics are separate from the 1,200 timing-screen outputs.

Each case uses graph seed **2000003** and KKT seed **607**, once per variant. These are logical-operation observations for those inputs, not timings, bytes, instructions, a randomness average, or evidence that every seed behaves identically. All counters include recursive subproblems. Input ordering and sampling trajectories differ between variants.

The two large attachment cases reduce contraction edge visits to **0.860x and 0.885x**, despite increasing contraction input volume to **1.145x and 1.175x**. Their sampling/verifier input grows to **1.276x and 1.337x**. Removing the deduplication traversal can therefore save contraction work even while downstream work increases. This supports a mechanism for the measured gains, but does not separate allocation, locality, output ordering, and sampling effects.

The bundled hierarchy control shows the danger: its root quotient has **16.011x** as many edges after two rounds; cumulative sampling/verifier input grows **20.342x**, initialized slots **5.225x**, and materializations **4.989x**. These counted downstream increases demonstrate a parallel-edge amplification risk; nevertheless, this measured control still ran about 13% faster in the paired timing screen. Counts alone do not establish a runtime regression or reject global promotion. Broader coverage is needed before deciding whether to enable the candidate globally.

## Candidate/reference counter ratios

Below 1 means fewer counted events. “Contraction input” counts edge incidences across every contraction call; “scans” counts actual contraction edge visits. “Initialized slots” covers all explicitly initialized KKT/verifier storage, not just contraction scratch space. Sampling and verifier input-edge counts are equal by this implementation’s call structure.

| Family | n | d | Contraction input | Scans | Initialized slots | Sampling/verifier input | Materializations |
|---|---:|---:|---:|---:|---:|---:|---:|
| leaf_hierarchy4 | 65,536 | 16 | 1.203 | 0.894 | 0.953 | 1.476 | 1.285 |
| leaf_hierarchy4 | 1,048,576 | 16 | 1.145 | 0.860 | 0.867 | 1.276 | 1.188 |
| leaf_distance4 | 65,536 | 16 | 1.262 | 0.950 | 1.038 | 1.613 | 1.373 |
| leaf_distance4 | 1,048,576 | 16 | 1.175 | 0.885 | 0.906 | 1.337 | 1.231 |
| leaf_shuffled4 | 262,144 | 16 | 1.262 | 0.942 | 1.049 | 1.673 | 1.394 |
| leaf_random4 | 262,144 | 16 | 1.472 | 1.069 | 1.384 | 2.548 | 1.715 |
| lifted_hierarchy4 | 262,144 | 64 | 3.303 | 2.479 | 5.225 | 20.342 | 4.989 |
| lifted_random4 | 262,144 | 64 | 1.536 | 1.142 | 1.410 | 2.373 | 1.749 |
| gnm_random | 65,536 | 128 | 1.629 | 1.206 | 1.953 | 4.119 | 2.116 |
| gnm_random | 262,144 | 16 | 1.293 | 0.957 | 1.096 | 1.761 | 1.439 |

## Actual quotient after the root’s first two contractions

The quotient vertex count is unchanged in every pair. The edge count includes every retained parallel record in the candidate and only the cheapest record per quotient pair in the reference.

| Family | n | d | Quotient vertices | Reference edges | Candidate edges | Edge ratio |
|---|---:|---:|---:|---:|---:|---:|
| leaf_hierarchy4 | 65,536 | 16 | 8,192 | 980,388 | 991,232 | 1.011 |
| leaf_hierarchy4 | 1,048,576 | 16 | 131,072 | 15,848,603 | 15,859,712 | 1.001 |
| leaf_distance4 | 65,536 | 16 | 8,192 | 980,388 | 991,232 | 1.011 |
| leaf_distance4 | 1,048,576 | 16 | 131,072 | 15,848,603 | 15,859,712 | 1.001 |
| leaf_shuffled4 | 262,144 | 16 | 16,457 | 3,855,246 | 3,948,444 | 1.024 |
| leaf_random4 | 262,144 | 16 | 3,505 | 2,293,982 | 3,933,977 | 1.715 |
| lifted_hierarchy4 | 262,144 | 64 | 32,768 | 1,002,843 | 16,056,320 | 16.011 |
| lifted_random4 | 262,144 | 64 | 13,060 | 11,619,316 | 16,491,886 | 1.419 |
| gnm_random | 65,536 | 128 | 3,351 | 3,308,148 | 8,322,776 | 2.516 |
| gnm_random | 262,144 | 16 | 13,483 | 3,742,172 | 3,945,215 | 1.054 |

Exact counts and ratios for twelve counters are in [counter_comparisons.csv](counter_comparisons.csv). [all_counters.csv](all_counters.csv) retains every counter for both algorithms and both variants. Individual checked results and RSS observations are under [cases/](cases/).

## Capture and provenance

Both diagnostic executables are native arm64, use a 512 MiB main stack, and enable logical work instrumentation. They use the same C++/header inventory as the timing screen. Commands, compiler/SDK identity, object/source/binary hashes and profiles are in [reference-build.json](reference-build.json) and [multigraph-build.json](multigraph-build.json). The reference links the separately compiled default-KKT counter object; the candidate links the candidate object. Shared non-KKT counter objects are identical.

The serial diagnostic capture ran from `2026-10-15T05:20:19.045422+00:00` to `2026-10-15T05:22:59.816342+00:00`. All twenty native exits are known and zero. The bounded libproc monitor sampled only each owned process group, with a 40 GiB ceiling, two-second polling, a 600-second child timeout, and bounded cleanup. There were no unavailable RSS observations; the largest sampled process-group RSS was **3.527 GiB**. Sampling can miss brief peaks. This footprint covers generation, independent certification, and both solvers; it is not a KKT-only memory estimate.

Capture/process duration is resource bookkeeping and is not used as a solver performance measurement. No power or performance conclusion is drawn from these diagnostic durations.

Run `python3 -B benchmark/results/multigraph-2026-10-14/work/capture_work.py --reanalyze` from the repository root to reread raw results, verify hashes/fingerprints and counter schemas, verify exact compactor equality, and regenerate the tables. [analysis.json](analysis.json) binds the derived tables to the raw capture and timing screen. The capture script refuses to overwrite an existing capture.
