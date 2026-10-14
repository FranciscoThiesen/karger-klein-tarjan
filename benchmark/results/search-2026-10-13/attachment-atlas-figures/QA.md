# Actual-graph atlas QA

The generated PNG was opened and visually inspected after native timing was
stopped on 14 October 2026. All four panels, titles, per-panel counts, legend
and illustrative-coordinate disclaimer are visible without clipped content.
The ordered core trees remain distinguishable from the faint common context;
the shuffled controls visibly connect across the same coordinate clusters.
This makes the atlas useful as graph anatomy alongside the interactive views.
It is not a picture of measured large instances or KKT's internal execution.

All 768 local pendant edges and 255 core MST edges are drawn in each panel.
Individual pendant spokes are small at whole-page scale; this overview should
not replace the interactive zoom for inspecting individual local stars. The
denser-looking control MSTs contain the same number of selected edges as the
ordered trees. Every panel uses the same 192 actual core context IDs, chosen
without consulting weights or MST membership. Counts describe unique edges,
not drawing passes; context/MST overlaps are not double counted.

| Actual export | MST edges | Additional context | Visible unique edges | Hidden input edges | Core MST edges outside backbone |
|---|---:|---:|---:|---:|---:|
| leaf_hierarchy4 | 1,023 | 191 | 1,214 | 15,170 | 0 / 255 |
| leaf_distance4 | 1,023 | 188 | 1,211 | 15,173 | 86 / 255 |
| leaf_shuffled4 | 1,023 | 189 | 1,212 | 15,172 | 254 / 255 |
| leaf_random4 | 1,023 | 187 | 1,210 | 15,174 | 254 / 255 |

[Integration checks](../validation/atlas-integration-checks.json) passed four
independent Python MST cycle certificates, coordinate/context coupling,
complete visible/hidden partitions, invented/local context-ID rejection, and
five malformed provenance/certificate/coupling cases. Those malformed inputs
were temporary synthetic tests and are not benchmark observations.

The separate [output-ledger check](../validation/atlas-output-ledger-checks.json)
verified all 4,847 written visible-edge rows against the copied actual
endpoints, weights and IDs; required the exact union of each complete MST
and common context set; checked hidden counts; and verified every generation
artifact hash. No existing export, timing CSV or SVG was modified. Original
native source/binary hashes are retained from the native export archive, not
reverified against a current executable by the Python renderer.

The current README/provenance now record this completed PNG inspection. Their
original generation-time versions are retained as generation-README.md and
generation-provenance.json. The output-ledger check above binds that generation
state; this documented metadata amendment changes no graph, image or timing data. SVG and PDF were generated but have not been separately rendered
for format-specific QA. Use the inspected PNG in the report; inspect exported
vector formats separately before distributing them as final layout artifacts.

At the initial atlas inspection, the confirmation figure had not yet been rendered. Its independent
[figure-logic checks](../validation/confirmation-figure-logic-checks.json)
passed selected/control coverage, real and synthetic extreme range inclusion,
full individual-trial appendix bounds, and five protocol negatives. Because
the original B capture is failed, that code-only check explicitly used a
synthetic in-memory A copy as B scaffolding. It reports no B performance
outcome and does not authorize relabeling the interrupted capture as complete.

Source SHA-256 at validation/rendering:

```
render_attachment_atlas.py      729417091e07afb38090eca54c61886b1f74b347c2b37e78aee87193ed0a1648
plot_confirmation_summary.py   2a791780b3557682173e37c2e96891f82251685dccf5ee75eaa9d22c03954143
validate_plot_atlas.py          83393c93fc7920fa3e4ee5dd59655f73da60eca8a573f3b72fae4b35a293f7ca
```
