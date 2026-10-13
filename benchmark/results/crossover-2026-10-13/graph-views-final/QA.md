# Graph illustration validation and visual QA

The five exact `n=128,m=512` fixtures were generated with graph seed 3037.
The temporary native exporter independently certified each reference MST,
checked production KKT with sampling seed 101, and executed ten production
contraction calls. Independent C++ and Python original-edge ledgers agree.
Python also checked all original tuples and IDs, path/grid scaffolds, exact
distance ranks, paired topology/order/geometry, and minimum retained edge for
every reconstructed quotient pair.

The final renderer reused that certified export. It did not compile or run
the native producer again. [Final provenance](provenance.json) binds the
[original native provenance](../graph-views/provenance.json) and copied data.
All native sources and the timed binaries remained untouched.

Two positive data checks and nine malformed-data rejection checks passed.
The extra positive case permutes every quotient's arbitrary vertex labels
while preserving incidences; all summaries remain identical. The negative
cases cover IDs, weights, label maps, coordinates, MST membership, selected
IDs, component membership and retained quotient edges. Exact cases and hashes
are recorded in [validation_checks.json](validation_checks.json). SVG XML also
parses successfully.

All ten panels of the actual [PNG](graph_views.png) were visually inspected:

- Both narrow/wide metric lines, the random-weight line, and both grid
  variants are present with their correct original geometry.
- The original grid annotations overlapped the highest vertex row. The final
  renderer reserves white space above the grid; labels and vertices are now
  separate, with no clipping or overlapping titles/captions.
- The 1D vertices stay at their actual x coordinates and y=0. The captions
  explicitly identify curved edge routing as a display convention.
- Component colors, retained-edge overlays, MST highlights, numeric summaries,
  tick labels and the bottom legend/caveat are legible. Superscripts and the
  summation glyph render correctly.
- The small-instance caveat and rank-weight/paired-geometry distinctions are
  visible. Nothing in the figure presents these examples as the large timed
  inputs or a causal explanation of their timings.

The [SVG](graph_views.svg) is emitted from the same Matplotlib figure as the
inspected PNG. Only trailing line whitespace is normalized in SVG output;
geometry and text are unchanged. This final figure supersedes the first
render visually; the original export and first PNG remain archived.

After two contractions, the component counts in row order are 12, 15, 6, 12
and 10. Retained edge counts are 65, 99, 15, 62 and 39. Full-precision effective
counts and largest-component fractions are retained in
[graph_summary.csv](graph_summary.csv), rather than inferred from image colors.
