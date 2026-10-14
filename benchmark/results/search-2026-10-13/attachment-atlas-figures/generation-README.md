# Actual small-graph atlas

![Certified MSTs and fixed sparse context](actual_graph_atlas.png)

These are separately generated n1024/d16/g5009/s149 illustrations, not timed graphs or downsampled large inputs. The complete topology, IDs, labels and input order are identical across the four exports; only ranks change. Every certified MST edge is visible. A fixed set of 192 actual core-edge IDs supplies context independently of weights or MST membership. Some context edges are already MST edges, so the number of additional visible edges varies by panel. Exact visibility counts and IDs are in panel_counts.csv and visible_edges.csv; no omitted edge is removed from the copied inputs.

The dyadic/star positions and fixed camera use the same construction as the interactive viewer. They are illustrative, not physical geometry; edge length is not weight. No contractions, sampling, filtering, runtime or large-input behavior are shown.

All four inputs were independently cycle-certified again by the existing Python validator before plotting. Native export provenance is copied; original native source/binary hashes are retained from that archive, not reverified here. This renderer does not execute native solvers.

Visual QA remains pending. Keep this optional figure only if all four panels are readable at report width. It complements the interactive views and work traces; it cannot replace them as a mechanism demonstration.
