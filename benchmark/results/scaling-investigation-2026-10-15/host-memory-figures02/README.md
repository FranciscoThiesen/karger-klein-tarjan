# Accepted host calibration figure

[`host-memory.png`](host-memory.png) and [`host-memory.svg`](host-memory.svg)
show both clocks, all seven footprints, four access patterns, both size orders,
three measured values per cell, median curves and complete min–max ranges.
Warmups remain in `all-calls.csv` and are excluded from plotted medians.

The plot passed original-resolution visual QA. [VISUAL_QA.json](VISUAL_QA.json)
binds source/artifact hashes, Matplotlib 3.9.4, the actual zero exit and empty
group, and exact CSV equality to the earlier independently checked analysis.
The render command is archived in `../host-memory-figures02-guard/plot.json`.

Attempt01 is preserved as a presentation-only failure: default log autoscaling
left unnecessary empty space before the first footprint. The separate v2 source
adds exactly one `set_xlim` statement. All numerical and validation code stays
identical; the original source and outputs remain intact. No native calibration
was repeated. Use attempt02 in the report.

The chase metric includes emitted loop instructions and hot-stack position
stores. It is not pure load latency, a KKT cache-miss measurement or a measured
fraction of KKT CPU time. See the linked host note for the full interpretation.
