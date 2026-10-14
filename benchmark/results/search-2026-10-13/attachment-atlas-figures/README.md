# Actual small-graph atlas

![Certified MSTs and fixed sparse context](actual_graph_atlas.png)

These are separately generated n1024/d16/g5009/s149 illustrations, not timed graphs or downsampled large inputs. The complete topology, IDs, labels and input order are identical across the four exports; only ranks change. Every certified MST edge is visible. A fixed set of 192 actual core-edge IDs supplies context independently of weights or MST membership. Some context edges are already MST edges, so the number of additional visible edges varies by panel. Exact visibility counts and IDs are in panel_counts.csv and visible_edges.csv; no omitted edge is removed from the copied inputs.

The dyadic/star positions and fixed camera use the same construction as the interactive viewer. They are illustrative, not physical geometry; edge length is not weight. No contractions, sampling, filtering, runtime or large-input behavior are shown.

All four inputs were independently cycle-certified again by the existing Python validator before plotting. Native export provenance is copied; original native source/binary hashes are retained from that archive, not reverified here. This renderer does not execute native solvers.

The PNG was visually inspected by two reviewers: all four panels, counts, legend and illustrative-coordinate labels are readable without clipping. [QA notes](QA.md), [independent integration checks](../validation/atlas-integration-checks.json), and [output-ledger checks](../validation/atlas-output-ledger-checks.json) record the evidence. SVG/PDF were generated but not separately rendered for format-specific inspection. This graph-anatomy overview complements the interactive views and work traces; it is not a mechanism demonstration. The original generation-time README/provenance are retained as generation-README.md and generation-provenance.json; this metadata-only amendment changes no image, export or timing input.
