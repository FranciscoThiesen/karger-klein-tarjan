# Held-out figure QA

PASS. Both `multigraph_design` and `root` visually inspected all four PNGs at original resolution: ratios_wall, ratios_cpu, times_wall and times_cpu. All 24 panels, six size labels, solver legends, neutral KKT label, both graph markers, full-range spans and matched wall/CPU limits were checked. The fourth ratio-caption line is readable with no legend overlap or clipping. All declared input and output hashes were rechecked.

PNG images have SVG/PDF counterparts; those formats were generated and hashed, not separately rasterized. `provenance.json` records the renderer's initial pending-review status; this later [QA receipt](QA.json) completes visual review.
