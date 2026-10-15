# Concept illustrations

Three explanations, each with a 720px desktop layout and a separately arranged
360px mobile layout. SVG text is converted to vector paths so client font
fallback cannot change the layout. The PNG counterparts are rendered at 2×.
Use `-mobile.svg` below 600px; use the desktop SVG otherwise. Every version has
an opaque `#fbfaf7` background and works on the site's dark or paper theme.

| Asset stem | Desktop logical size | Mobile logical size |
|---|---:|---:|
| `concept-id-budget` | 720×590 | 360×900 |
| `concept-sample-filter` | 720×930 | 360×1230 |
| `concept-weight-order` | 720×790 | 360×1130 |

## Captions and alternative text

**ID budget.** “The recursive graph can shrink while an array indexed by
original edge IDs stays the size of the root. The repair keeps original IDs
as data and uses local positions and selected-ID vectors. These array extents
and counts are schematic, not measured bytes or timings.”

Alt: “Three progressively smaller recursive inputs have the same long orange
tracking arrays in the old design, while the teal local bookkeeping shrinks.”

**Sample and filter.** “A constructed eight-vertex witness: the sample's tree
contains three edges outside the original MST, yet it certifies 18 of the
28 input edges as heavy. The 10 survivors still contain the exact original
MST. An edge of weight 11 loses to a forest path whose largest weight is 8.
This chosen sample illustrates correctness, not a typical draw or timing.”

Alt: “The full graph has 28 edges. Its chosen seven-edge sample tree contains
four original MST edges in teal and three other edges in orange. Filtering
keeps ten edges including the complete original MST. A small cycle shows
why weight 11 is discarded against path weights 8 and 2.”

**Weight organization.** “Both constructed toys have the same 32 vertices,
52 edges, IDs, edge order, and weight multiset. Thin teal edges attach three
cheap leaves to each core vertex. Bold teal edges are the cheapest core ranks.
Their deliberate reassignment changes the full Borůvka component counts from
32→8→4→2→1 to 32→8→1. Crossing counts retain parallel records after contraction.
The star permutation is a chosen example, not the benchmark's random shuffled
realization; the complete core is also much denser than the asymptotic family.”

Alt: “The same leaf-attached complete eight-vertex core is drawn twice. Cheap
core ranks form a hierarchical path on the left and a star on the right.
The path requires four contraction rounds, the star two. The ordered graph
still has 24 crossing records at four components and 16 at two.”

## Checks and source scope

Run from the repository root:

```sh
/usr/bin/python3 -B docs/kkt-blog-2026-10-15/scripts/draw_concepts.py
```

The generator checks unique weights, exact weight-multiset/topology/ID/order
equality, full cut-minimum Borůvka partitions and crossing-record counts,
Kruskal trees, an independent path/cycle certificate, and every forest-path
heavy mark. All graph records and computed partitions are retained in
[`assets/concept-checks.json`](assets/concept-checks.json). Renderer bounding
boxes also require every label to fit its canvas. These are Python toy checks;
no native solver, benchmark, browser, or publishing operation is called.

Historical ID storage was checked directly at `693c6a5:kkt/kkt.cpp`:
`used_edges`, `kkt_h_result`, result storage and merge loops depend on
`max_edge_id`. The local-domain repair is explained in the final report's
section 2. The sampling fixture follows the checked constructed witness in
[`SAMPLING_MECHANISM.md`](../../benchmark/results/larger-hierarchy-2026-10-15/SAMPLING_MECHANISM.md).
The attachment structure was checked against
[`core_attachment_fixtures.hpp`](../../benchmark/core_attachment_fixtures.hpp).
The complete-core/star pair is an explanatory construction, not a claim that
the seeded benchmark generator produces this instance.

`multigraph_candidate` independently reviewed the source and arithmetic:
28/7/10/18, three non-MST sample edges, the two exact component sequences and
their crossing counts. That peer review did not execute or view the figures.
The owner inspected all six final PNGs at original resolution. Final image
hashes and the scope of that check are in
[`validation/concepts-qa.json`](validation/concepts-qa.json).

The first layout exposed a clipped ID heading and overlong mobile captions.
Its source and images are preserved in `validation/concepts-layout-attempt01/`.
The final version wraps those labels, shows a concrete cycle proof, and keeps
crossing counts on mobile. Final SVG and PNG assets share the same drawing
code; no browser rendering is claimed.
