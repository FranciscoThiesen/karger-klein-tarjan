# Actual small graph illustrations

These are exact n=128, m=512 fixtures with graph seed3037, not the large timed inputs. The native exporter certified the reference MST independently and checked production KKT (seed101). It then called production `boruvka_step` twice; separate original-edge ledgers reconstruct membership. Python rechecks the ledgers, the cheapest crossing edge for every quotient pair, and metric ranks against the exported exact coordinates.

Left: all original edges, with the certified MST highlighted. Right: original vertices colored by their component after two contractions; dark edges are the retained quotient representatives drawn at their original endpoints, and faint colored edges show the selected forest. Components have not been relocated to invented centroids.

Line vertices retain exact x positions and y=0. Arcs only route edges visibly; arc height is not a geometric coordinate. Grid edges are straight in the actual jittered coordinates. Metric weights are distance ranks, not raw metric lengths. Narrow-line/random and grid/random twins share geometry; wide-line coordinates differ.

`q_eff=n²/Σ size²`; q counts reconstructed original components even if a terminal quotient uses zero vertices. These small examples illustrate definitions and do not explain a large-instance performance result by themselves.

[Full original data and both rounds](graph_data.json), [component summaries](graph_summary.csv), [source/compiler/export provenance](provenance.json).

![Actual fixtures and contractions](graph_views.png)

[Vector SVG](graph_views.svg)
