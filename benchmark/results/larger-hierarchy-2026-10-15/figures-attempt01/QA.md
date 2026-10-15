# Figure visual QA

PASS. `multigraph_design` inspected all 4 PNGs at original resolution and all 8 panels. All four original-resolution PNGs are readable: two family panels each, all six absolute-time or five comparator series, both graph medians, complete trial ranges, neutral KKT legends, threshold captions and all measured endpoints. Wall and CPU panels use matching bounds; no clipping or overlap was found. Lines connect measurements without implying an interpolated crossover.

All declared source/input and output hashes were independently rechecked. SVG/PDF counterparts were generated and hashed, not separately rasterized. The renderer's pending-review provenance is preserved; this later [QA receipt](QA.json) records visual approval.

Root independently inspected all four timing PNGs, including the CPU ratio image at original resolution, and also passed them: all six absolute/all five comparison series, axes, legends, captions and trial ranges are visible; the retained-edge Borůvka reversal and original-Borůvka crossing are clear. No clipping was found.
