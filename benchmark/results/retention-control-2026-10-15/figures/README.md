# Six-solver retention-control figures

The plotter strictly rereads and validates the complete 840-output capture. Both clocks, all ten cases, all five KKT comparators and all six absolute runtimes are retained.

- [Elapsed-time ratios](ratios_wall.png)
- [Process-CPU ratios](ratios_cpu.png)
- [Absolute elapsed times](times_wall.png)
- [Absolute process-CPU times](times_cpu.png)

Each PNG also has SVG and PDF versions. Solid ratio points are medians of all twelve paired trial ratios; faint triangles are each graph's six-trial median. Thin spans show the full trial range. Absolute-time medians use the corresponding durations directly. All ranges are descriptive, not confidence intervals. Curves connect tested sizes only; crossovers are not interpolated. Axes include every trial-range endpoint and share their limits across clocks within each family/density panel.

`plotted_values.json` contains exact graph and pooled summaries; `provenance.json` binds the raw evidence, helpers, plotting source, figure outputs and axis-coverage checks. Visual review is pending until all four PNGs have been inspected.

Subsequent [PNG visual review](QA.md) is complete.
