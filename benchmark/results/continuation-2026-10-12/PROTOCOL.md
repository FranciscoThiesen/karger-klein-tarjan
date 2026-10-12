# Finding a KKT advantage over compacting Borůvka

This is an exploratory search followed by a frozen, independently seeded
confirmation. It extends the 20-case ablation without changing either production
KKT or the repeated-production-contraction baseline. Every loss is retained.

## Hypothesis, before timing

The earlier favorable graphs often leave a tiny sparse residual. Continuing
contraction is cheap there. A different regime may favor KKT: Borůvka merges
only pairs while many distinct residual edges remain, so several rounds repeat
large edge scans; sampling might remove those edges more cheaply.

Test a light dyadic backbone plus random heavy shortcuts. The hierarchy forces
exact pairwise contraction, independently of vertex labels and edge order.
Use both a path backbone and randomized edges connecting recursive half-blocks.
This is an intentionally constructed, planted-weight stress family. It is not
claimed to represent common unconditioned random graphs or application data.
All comparisons use the unmodified general solvers; neither knows the backbone.

Controls keep the exact topology, IDs, labels and input order but globally
randomize weight ranks; a cheap path with shuffled backbone weights tests
whether the hierarchy matters beyond planting an easy MST. Unchanged legacy
random4/32/128 fixtures test the missing density range. All graphs are simple,
connected and have distinct weights, with independent MST certification.

## Discovery

`discovery.csv` fixes the initial case matrix before any timing. Graph seeds
17,42; sampling seeds0,1; two balanced repetitions; one checked warmup per
algorithm/seed. These observations select candidates, not confirm a claim.
The file's order is deterministically shuffled with Python seed20261012.
One timed process runs at a time, with builds/tests/plots outside timing.

Screen sizes16,384 and65,536. Density m/n is4,16,64 for the two hierarchical
families;16 for cheap-path and random-weight controls;4,32,128 for unchanged
legacy random graphs. All initial rows and any explicitly labeled later
exploration remain archived. Do not silently replace an unsuccessful screen.

## Confirmation rule fixed before seeing discovery

Promote up to two hierarchical density choices with the strongest repeatable
discovery ratios; include both backbone shapes and their random-weight twins,
the cheap-but-shuffled path control, and legacy random controls. Choose sizes
65,536 and262,144 initially; add1,048,576 only if the time/memory cost inferred
from screening is practical. Freeze the exact manifest before any holdout run.

Fresh graph seeds:2027,4099,8191,104729,131071. Fresh sampling seeds:11,29,97.
Four balanced repetitions and one checked warmup. Run two complete campaigns;
the second reverses the frozen first campaign's case order. Keep both runs
separate. The holdout seeds may not be used for candidate selection.

Call a selected family a **clear practical winner within the measured range**
only if matched KKT/compacting-Borůvka case ratios are at most0.90 at two
adjacent largest tested sizes in both campaigns, and all five graph-level
ratios are below1 in both. This is a descriptive robustness threshold, not a
significance test or proof beyond the sampled graphs/machine. If it fails,
report the weaker/negative result. Further adaptation requires newly labeled
exploration, not relabeling holdout measurements as confirmation.

After selection, perturb the hierarchy by uniformly promoting exactly
floor(n*p/1000) random shortcut edges into the cheap ordering, with p=1,10,100.
This is a count relative to n, not a fraction of all m edges. Keep same-topology
twins and all perturbation losses. Treat this as a separate sensitivity study;
it cannot rescue a failed predeclared confirmation claim.

## Measurement and diagnosis

Both algorithms start from the same tuple list, include conversion and temporary
input destruction, and return the same reserved ID set. Generation, reference
certification, output validation and destruction of the returned set are outside
timing. Algorithm order alternates within every seed block. Every timed call
and warmup must match the exact unique certified MST IDs.

Form ratios within matched repetition blocks, then take medians over repetitions,
sampling seeds and graph seeds. Preserve individual losses, graph ranges, order
strata and run drift. Repetitions/sampling seeds are not extra graph draws.

Separate trace and instrumented binaries record residual n/m at every compacting
round and the existing work registry for both solvers. Compare the same
`contraction_edges` counter for both; KKT recursive-input volume is a different
quantity. Report verifier input/light volume and materializations separately.
Counters omit allocator internals/cache effects and do not identify a measured
hardware bottleneck. Never use instrumented durations as performance evidence.

Record source, binary, manifest and raw-output SHA-256 hashes, exact commands,
compiler/profile and platform. This remains an ordinary Apple M3 Max desktop
experiment without controlled affinity/power state. The stronger baseline is
the whole compacting continuation strategy; it differs from KKT in storage
lifetimes, RNG, recursion and filtering, not only verifier instructions.

## Labeled exploration extension after the initial screen

The complete initial 24-case screen found no ratio at or below 0.90. The best
hierarchies were density64 at n65,536 (ratios0.929 and0.935), improving from
losses at n16,384. Before any fresh-seed confirmation, `extension.csv` screens
n131,072 and262,144 at density64 for both original hierarchy shapes and new
`distance_path`/`distance_tree` variants. It includes distance variants at65,536
and original hierarchy density16 at262,144 as a lower-density control.
It retains discovery seeds17,42, sampling0,1 and two repetitions; these are
additional selection data, never holdout evidence. Order uses seed20261013.

Distance variants keep the exact corresponding path/tree topology but rank
**all** edges by floor(log2(u xor v)) before vertex relabeling, randomizing
within each level. Shortcut edges may now enter the MST. This remains an
engineered hierarchical model. Integer rank weights are order-equivalent to a
tie-broken dyadic distance; they are not themselves claimed to obey the triangle
inequality. The fraction of backbone edges in the certified MST is logged.

Based on the observed size trend and the cost of 67-million-edge million-vertex
density64 fixtures, the confirmation size menu now includes131,072 between the
previously specified65,536 and262,144. Its exact manifest remains to be frozen
before holdout. The same win threshold and fresh seed banks remain unchanged;
all lower-size results and controls remain visible. No solver has changed.

### Interrupted setup and equivalent generator repair

The first extension attempt (`extension_timing.*`) was intentionally stopped
with SIGTERM after unusually slow setup on its first large graph. It contains
no complete timing rows and is excluded from all performance summaries; the
failure metadata is retained. The continuation fixture used the older Builder's
identity hash of packed endpoints with a power-of-two-sized table, which can
cluster keys by their lower endpoint bits. The replacement mixes both endpoints
in a fixture-local hash table; membership decisions, RNG draws and output order
must match the previous generator exactly. It changes no measured solver code.
A fresh complete run will use `extension_fast_timing.*`. Setup-stage durations
are now logged separately to distinguish generation from reference certification;
these diagnostics are not solver performance measurements.

### Larger unchanged random controls

Before holdout, `large_random_screen.csv` extends the unchanged legacy random
fixtures to262,144 vertices at densities32 and128, with the same discovery
seed banks and repetitions. This explicitly tests whether high-density ordinary
random weights show a crossover too; it is additional exploration, never a
confirmation run. The legacy generator is unchanged, including its setup cost.
