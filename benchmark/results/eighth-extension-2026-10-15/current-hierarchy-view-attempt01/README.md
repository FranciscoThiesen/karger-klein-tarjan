# Current retained-edge KKT root-stage explorer

[Open the standalone offline 3D viewer](index.html). It contains the complete
certified edge data for the ordered and shuffled n=1,024, m=32,768 fixtures
from the completed extension, with graph seed 17000011 and sampler seed 2801.
The display limits background context to 512 edges; the exported counts and
certificates use every edge. Geometry is explanatory, not an input metric.

Native export, independent graph/sample/filter checks, ten mocked test groups,
and the strict join to all 42 timing identities per fixture passed. The exporter
links the unchanged eight eighth-policy objects with one new diagnostic main.
It reconstructs the two root contractions, half/eighth samples, sample MSFs and
heavy-edge classifications; this is not a recorded recursive execution trace.

**Browser interaction and desktop/mobile visual QA remain pending.** CUA had
no usable browser surface; installed headless Chromium aborted before page
load with macOS bootstrap error 141. The failure was environmental and supplies
no evidence about rendered correctness. Do not describe the viewer as visually
validated. The [readiness receipt](../validation/root-view-readiness-attempt01.json)
binds passed checks and preserved failures; the [native receipt](../validation/root-view-attempt01/receipt.json)
and [assembly receipt](../validation/root-view-assembly-attempt01.json) retain
actual zero exits and empty owned groups.

For the ordered root, two contractions leave 128 vertices and 31,872 records.
Half sampling selects 15,802 records and leaves 247 F-light records; eighth selects
3,918 and leaves 1,043. The shuffled root has 68 vertices and 31,461 records, with
15,576/157 and 3,870/675 sample/light counts. These are one explanatory realization,
not average costs or a timing comparison between policies.
