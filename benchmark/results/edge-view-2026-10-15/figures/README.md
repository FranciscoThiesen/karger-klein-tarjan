# Paired Edge-query verifier figures

The strict collector rereads all 1,680 outputs, raw certificates, process-group observations, source/build bindings and clock flags before plotting. Historical timings are absent.

- [All six Edge/tuple elapsed-time ratios](variant_gains_wall.png)
- [All six Edge/tuple CPU-time ratios](variant_gains_cpu.png)
- [Edge KKT / all five comparators, elapsed](edge_ratios_wall.png)
- [Edge KKT / all five comparators, CPU](edge_ratios_cpu.png)

Each figure also has SVG and PDF versions. Solid points pool all twelve paired ratios; faint graph points use six ratios each. Thin spans show the full trial range. All losses and flagged calls remain included. Axes contain every trial range and share limits across clocks. Unchanged-solver drift is shown without normalizing KKT. Ranges are descriptive, not confidence intervals; connecting lines do not interpolate crossovers. Exact source values and hashes are preserved alongside the figures. Visual review is pending.
