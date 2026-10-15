# Direct-Edge density-search figures

Strictly revalidated all 672 outputs from 16 native children. Both clocks, all eight cases, all five KKT comparators and all six absolute runtimes remain visible.

- [Elapsed-time ratios](ratios_wall.png)
- [Process-CPU ratios](ratios_cpu.png)
- [Absolute elapsed times](times_wall.png)
- [Absolute process-CPU times](times_cpu.png)

Each figure has four family/density panels: ordered or shuffled core ranks at m/n = 32 or 64. Both families retain cheap leaf attachments; shuffled core ranks are not globally random weights. Matched families share topology, IDs, labels and edge order.

Solid points are pooled twelve-trial medians; triangles are the two graph medians; thin spans show every trial-range endpoint. Ranges are descriptive, not confidence intervals. All losses and clock-flagged observations remain included. Ratio values below one favor KKT. Each absolute-time median is computed from durations directly; controls never normalize KKT.

Axes include every trial-range endpoint and use the same limits across clocks within each panel. Lines connect only the two tested sizes; no exact crossing point is interpolated. Two endpoints provide exploratory brackets, not evidence of durable asymptotic dominance. The prior density-16 data is not pooled. Each graph/sampling realization is timed six times.

PNG, SVG and PDF versions are retained. `plotted_values.json` preserves graph and case summaries; `provenance.json` binds raw evidence, source, immutable renderer, outputs and coverage checks. Visual review remains pending until all four PNGs are inspected.
