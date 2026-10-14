# Figure QA

All four generated PNGs were opened and visually inspected after rendering:
`volume_scaling.png`, `round_occupancy.png`, `weight_controls.png` and
`all_selected_records.png`. Labels, legends, both signed-deviation panels,
the logarithmic control trajectories and all 16 case labels are readable.
No clipped plotted data, cropped labels or missing panels were observed.
SVG counterparts were generated from the same Matplotlib figures; they have
not been separately rendered in another viewer.

The size-scaling figure retains both nearly overlapping KKT weight-mode curves.
Identical compactor curves are combined only after an exact equality check.
The occupancy plot preserves signed model deviations. The control plot uses
actual rounds through completion and does not assign a dyadic expectation to
shuffled or global-random weights. All 16 selected cases remain in the horizontal
comparison, `data.csv`, and the analysis report's case table.

Every figure labels its graph/sampling seeds and states that these are untimed
logical counters with no time fit or extrapolation. Normalized contraction
volumes do not include the cost of every algorithmic event and are not runtime
ratios. Native production sources and timed data were not changed to make these
figures.
