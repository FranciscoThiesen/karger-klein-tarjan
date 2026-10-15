# Focused offline PDF fallback

Source prepared; no imports, test execution or PDF rendering yet. ReportLab
5.0.1, pypdf 6.14.2 and Markdown 3.9 were separately probed as available under
`/usr/bin/python3` 3.9.6. Chromium cannot currently start, and WeasyPrint and
wkhtmltopdf are unavailable. No dependency installation is proposed. The PDF
skill marker already ran once for this task; **do not repeat it**.

`build_reportlab_pdf.py` consumes the completed new-edition `report.html` and
`render_metadata.json` produced by `build_current_report.py` **without** its
`--pdf` switch. It does not edit that HTML, primary Markdown, historical report,
draft substance or any figure. It uses the accepted offline equation and ASCII
hyphen translations verbatim, resolves the same local evidence and figures,
and rechecks their original hashes. It does not attempt to interpret arbitrary
CSS: supported report blocks are explicitly converted, unknown content fails.
The duplicate HTML contents navigation is omitted; all body sections, tables,
equations, captions and evidence links remain. Nested lists need a separately
reviewed layout rather than silently flattening them. Non-whitespace text
between table structural elements is rejected. Custom list `start`, `reversed`,
`type`, and item `value`/`type` attributes are rejected, including a redundant
explicit `start="1"`, so unsupported numbering/markers cannot silently change.

The new exclusive output directory contains `report.pdf` and `pdf_metadata.json`.
A4 body text is 10pt, code/captions/footer 9pt, tables 8.5pt. Embedded DejaVu font
files are hashed and missing glyphs fail. Tables wrap cell text and repeat the
header; no horizontal table scaling is allowed. Figures and captions must fit
one page at their declared readable size. The PDF must actually contain 1..40
A4 pages as read by pypdf; too many pages fails and retains the attempt. There
is no font reduction or removal of losses to force the cap.

This narrow fallback accepts copied **PNG** figures. Choose the existing,
reviewed equivalent PNG or newly audited paper-layout PNG in the finalized
Markdown before running the accepted HTML renderer. An SVG-only figure fails,
rather than silently rasterizing with an unverified dependency. Figure label
sizes are source declarations and still require actual page-scale visual QA.

Supply a JSON figure declaration covering every unique image SHA in the HTML
renderer metadata, for example:

```json
{
  "schema": "kkt_pdf_figure_layout_v1",
  "figures": {
    "ACTUAL_FULL_IMAGE_SHA256": {
      "nominal_width_inches": 7.1,
      "minimum_label_pt": 8.5,
      "basis": "Reviewed paper plot source and its actual figure receipt"
    }
  }
}
```

The declared minimum label size is multiplied by the actual placement scale;
the result must remain at least 8.5pt. Wide standalone figures cannot pass by
claiming their canvas is narrower. Use the paper layouts, preserve original
supplements and inspect each page at real viewing size. An unusually dense
diagram can require a separate legible paper arrangement; it must not receive
an invented label-size declaration.

After nonperformance rendering is released, run the four focused groups through
the existing bounded nonnative validation guard with exclusive receipts:

```sh
/usr/bin/python3 -B /tmp/kkt-current-report-publish-prep/test_reportlab_pdf.py --artifacts-dir /tmp/kkt-current-report-publish-validation-2026-10-15/reportlab-fixtures-attempt01
```

The positive fixture exercises the actual accepted Markdown/HTML preprocessing,
all three equations, wrapping table, lists, long code, local/internal links,
PNG and Unicode glyphs. Negatives cover bound input drift, unsupported content,
missing glyphs, image coverage/size/assets and the actual 0/1/40/41-page and A4
boundaries. Direct parsed-structure negatives check stray text at table/group/
row levels and custom list starts, item values, reversal and marker types.
Synthetic PDFs and all failed artifacts remain at the supplied
exclusive fixture path. Runtime behavior is unvalidated until those tests run.

Final invocation after the report's Google/distance sections and paper assets
are finalized (not executed during a quiet timing campaign):

```sh
/usr/bin/python3 -B /tmp/kkt-current-report-publish-prep/build_reportlab_pdf.py --edition /ABS/NEW/HTML/EDITION --figure-layout /ABS/FIGURE_LAYOUT.json --output-dir /ABS/NEW/PDF/ATTEMPT
```

Run this inside a bounded archival guard as well. The renderer itself is not
an outer process supervisor. Root must rasterize and inspect **every actual
final page**, check no table/figure clipping and all glyph/label sizes, then
bind that QA to the final PDF hash. Metadata remains
`rendered_pending_visual_qa`. This PDF route neither validates the browser HTML
nor resolves the interactive viewer's blocked browser gate. The separate
tracked/copied publication-link checker is still required; local PDF links
alone are not portable native build proofs.

The initial source-only version is preserved under
`before-structural-text-and-numbering-review/`. These focused review fixes and
their added negatives remain unexecuted during the quiet distance capture.
