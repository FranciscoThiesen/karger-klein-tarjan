# Independent complexity paper v2 source review

Status: **PASS by source inspection only**, 2026-10-15. Reviewer:
`/root/multigraph_design`. No Python import, test, rendering, hash walk, native
execution or partial distance-capture read was performed. Runtime and visual
gates remain pending.

Reviewed files: `plot_complexity_paper_v2.py`,
`test_plot_complexity_paper_v2.py`, `COMPLEXITY_PAPER_V2_PREPARATION.md`, the
preserved `COMPLEXITY_PAPER_V2_FONT.diff`, and section 4 of
`/tmp/kkt-current-complexity-execution-handoff.md`. This receipt records a
source review; installation must separately bind actual final file hashes.

The adapter differs from the preserved original only at eight explicit font
sizes: four 8.3 pt captions, one 8.4 pt row-label setting and three 8.2 pt captions
become 8.5 pt. All arithmetic, input/output binding, complete-value comparison,
model/clock distinctions, plot ordering and other layout settings are unchanged.
Nominal sizing now meets the PDF fallback's minimum before placement scaling.
Legibility and clipping are not established without actual rendering and
page-scale inspection.

The four prepared test groups use the installed analyzer's varied-clock
synthetic curves and the real standalone plot preparation. Only the native
evidence-loader boundary is replaced. The import interception delegates actual
standalone source execution before replacing that boundary, and restores module
state. The tests cover all 1,056 points, 288 model cells and 24 selections;
changed values/table copies despite updated output hashes; missing clock,
model, fit, point or selection coverage; and changed input/source/output bytes
or incomplete output inventory. Placeholder image bytes are explicitly
unrendered, not a native proof or image-validity claim.

One fixture defect was corrected during review: the CSV writer now explicitly
uses LF. Its original default CRLF strings would differ from `Path.read_text()`
normalization and reject the positive fixture before the intended checks. The
final source contains `lineterminator='\n'`; no production parser was weakened.

The updated handoff invokes the v2 filename and accurately keeps installation,
actual four-group results, bounded synthetic rendering, complete real-data
rendering, visual QA and final PDF placement as separate pending gates. The
frozen complexity measurement package and earlier adapters remain unchanged.
