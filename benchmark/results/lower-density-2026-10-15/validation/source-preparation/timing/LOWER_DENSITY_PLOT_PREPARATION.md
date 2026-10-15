# Lower-density standalone figure preparation

`overlay/benchmark/plot_lower_density.py` is source-only, unimported and
unexecuted. It adapts the completed distance plotter to four separate
family/density panels: distance/shuffled at m/n=16 with seven sizes, and
distance/shuffled at m/n=8 with eight sizes. All fixed sizes, five comparator
ratios, six absolute solver series and both clocks remain. Densities are never
pooled; panel bounds include both clocks, all trial endpoints and graph medians.

After complete strict capture and independent numerical audit PASS, the CLI is
`--capture CAPTURE.json --output FRESH_DIRECTORY --released`. It strictly reloads
all60children/2520outputs, then reconstructs and validates canonical tables:
3600paired ratios,300comparison medians,600graph comparison medians,360absolute
medians,720graph absolute medians,150point classifications,490endpoint pairs and
20crossover summaries. The4figures contain16panels,660pooled points,1320graph
medians and1320trial-range endpoints. PNG/SVG/PDF and the complete canonical
`plotted_values.json` are written exclusively with source/input/output hashes.

The new2×2layout is15.5×11.8in. All seven/eight explicit size labels are retained;
range spans and the two graph markers have the same meaning as in the completed
distance figures. Legends are checked explicitly. Ratio panels include parity
and0.90threshold lines, while captions require an earlier loss and persistent
strong leads at every larger measured size within the same density. Lines do
not interpolate a crossover. Graph seed and full schedule reversal remain
confounded. Repetitions reuse fixed graph and sampler states and are not
independent graph draws.

Source review, actual preparation/render gates and inspection of all four PNGs
are separate steps. No figure currently exists, and no layout or final-page
acceptance is claimed. A future paper adapter, if requested, must preserve these
same canonical values rather than recompute or omit unfavorable series.
