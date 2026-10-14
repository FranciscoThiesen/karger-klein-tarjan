# Offline attachment graph viewer

Ready source files:

- `render_attachment_view.py`: standard-library Python validator and self-contained HTML builder.
- `render_attachment_view_test.py`: independent synthetic schema and certificate checks.
- `export_attachment_view.cpp`: native exporter draft, owned by the parent for integration/build.

The HTML contains the actual exported input edge tuples, certified MST IDs and
original-to-label mapping. Its canvas supplies perspective rotation, zoom, dyadic
clusters or a core ring, local stars, MST/other-edge toggles, local/core toggles,
an actual weight-rank threshold, vertex inspection and a PNG download. It defaults
to the MST so the structure remains legible; all other input edges remain available.
Both layouts use original block IDs, so paired variants share coordinates.
Every graph edge shown is real. Layout coordinates are explicitly illustrative,
have no physical interpretation, and do not encode weights or measured speed.

There are no CDN, font, script or data requests. The document includes its own
CSS, JavaScript and JSON. Its content-security policy denies external resources.
The embedded JSON escapes HTML-sensitive characters; 64-bit fingerprints remain
decimal strings. The controls use actual input weights even for global-random
families, whose diagnostic core ranks do not describe the actual cost order.

## Validation status

After the parent announced that native timing was off, the following command
completed successfully on 2026-10-13:

```sh
python3 /tmp/kkt-core-attachments/render_attachment_view_test.py
```

Result: 16 synthetic family cases passed, 14 malformed exports were rejected,
4 invalid MST certificates were rejected, and the embedded-JSON injection
check passed. The independent synthetic graphs exercise both endpoint modes,
all four weight modes, and both block sizes. Their MSTs are selected by a
separate sorted-edge DSU; the renderer independently checks connectivity,
acyclicity, total weight and every input edge's cycle condition. No synthetic
HTML is published as native solver evidence.

**Not yet verified:** compatibility with actual native exporter output,
JavaScript execution, browser interaction, layout legibility, responsive
behavior, PNG download and offline network behavior. These require the parent's
integration/build and browser QA. The exporter itself does not embed a build
revision; archive its binary/source provenance next to the JSON before using
an export in the report. The Python certificate verifies the graph and MST,
but cannot independently prove which native executable produced the JSON.

## Integration checks for the parent

After building the exporter under the chosen revision, suggested commands are:

```sh
bin/export_attachment_view --family community_distance16 --n 1024 --density 2 --graph-seed 5009 --kkt-seed 149 > community_distance16.json 2> community_distance16.certificate.log
python3 /tmp/kkt-core-attachments/render_attachment_view.py community_distance16.json --validate-only
python3 /tmp/kkt-core-attachments/render_attachment_view.py community_distance16.json --output community_distance16.html
```

Retain the exporter certificate marker, JSON, build revision/hash and validation
output. Repeat the schema/certificate validation with at least the leaf endpoint,
hierarchy, core-only shuffled and global-random controls, and both block sizes.
The exports are exact small instances, not miniature substitutes for benchmark
measurements or estimates of their elapsed time.

Open the generated HTML locally. Inspect the default graph at desktop and narrow
widths; check that the dyadic clusters and local stars are legible. Exercise each
edge toggle independently and together, both coordinate layouts, rank endpoints,
drag/keyboard rotation, wheel/keyboard zoom, selection, auto-rotation, reset and
PNG download. Verify the visible edge count equals `n-1` for the default full-rank
MST, `m` with all graph edges enabled, and zero when both edge groups are disabled.
Vertex degrees intentionally refer to the complete input/MST, not the filters.
Check browser console and network panel for errors or network requests. Save
screenshots of the default and an all-edge view with provenance before report use.

## Occupancy helper follow-up

`benchmark/attachment_occupancy.py self-test` also passed after the capture ended:
5,525 exact probability checks, 32 enumerated quotient expectations, 6 valid and
7 invalid attachment dimensions, one count-scaled cutoff check, 4 oversized-core
rejections and 3 exact-count boundary checks. `expected_core_quotient` now rejects
`q*q > 2**53-1` before any exact-result shortcut. This conservative uniform bound
keeps all pair populations, possible slot counts and exact edge counts within
the supported float-integer domain. Some much larger theoretical cases could be
handled specially, but this helper intentionally does not support them; the
attachment CLI has `q <= 2**20`, well inside the bound. Ordinary float roundoff
remains distinct from the explicitly reported truncation bound.
