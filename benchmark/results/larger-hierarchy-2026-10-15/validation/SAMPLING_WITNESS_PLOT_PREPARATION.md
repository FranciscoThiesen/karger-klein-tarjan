# Eight-vertex sampling-witness figure preparation

Prepared 2026-10-15 during the separate larger performance capture.
**Source-only and independently reviewed; no import, graph check, rendering,
native call or partial timing inspection has occurred.** Root must release
nonperformance work before execution. Visual review remains required.

Source snapshots:

| File | SHA-256 |
|---|---|
| `benchmark/plot_sampling_witness.py` | `326eb5a51bf359ffa741c139d27bdc51be9d288478028698bd74a9fde0bc1489` |
| `SAMPLING_MECHANISM.md` | `41541fc7d3598195113780f2c6d241aa91e7c5d1ffae769e0d15bc539c47422a` |

The [new script](../../../plot_sampling_witness.py) constructs the note's
eight-vertex complete graph, preserving path ranks 1/5/2/7/3/6/4 and selected
chord weights 8/9/10. Remaining chords receive unique ranks 11 through 28 in
lexicographic endpoint order. The chosen seven-edge sample is explicit; it
is not a typical random draw or a captured KKT sample.

Before plotting, stdlib Kruskal, a separate forest BFS maximum calculation,
and simultaneous-component-minimum Borůvka derive the edge memberships and
contraction partitions. They must agree on the MST and reproduce 28 parent
edges, 7 sampled-forest edges, 10 light survivors, 18 removed heavy edges,
3 non-MST sampled chords, and 3/2/3 full/sample/filtered rounds. Figure labels
use these computed values; the hand counts are rejection gates, not substitute
data. Complete edge weights, memberships, path maxima and round traces are
saved. These tiny-graph checks do not validate the native C++ implementation.

One three-panel figure will show the parent, chosen sampled forest and filtered
parent with the same deterministic circular layout. Every graph edge is drawn;
weights 1–10 are labeled and other chord weights are preserved in the CSV.
Original-MST edges and sampled non-MST chords have distinct color/line styles.
The caption explicitly labels a constructed illustration, without timing,
typicality, geometric-distance or performance claims. PNG/SVG/PDF and source/
output hashes will be retained in a fresh output directory.

Independent mathematical/source review by `experiment_design` passed after
reading the complete script. It found no blocker in the graph construction,
strict heavy predicate, independent algorithms, round counts or claim scope.
No imports or execution were performed by either reviewer. All three panels
must be visually inspected after actual rendering.

Deferred reproduction:

```sh
/usr/bin/python3 -B benchmark/plot_sampling_witness.py \
  --output /tmp/sampling-witness-new --released
```
