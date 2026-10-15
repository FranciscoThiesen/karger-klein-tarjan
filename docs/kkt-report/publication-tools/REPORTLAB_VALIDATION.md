# ReportLab fallback: completed synthetic validation

The twelve reviewed source/document/history files were copied byte-for-byte
into this directory without overwriting any existing file. The exact inventory
and hashes are in `REPORTLAB_INSTALLATION.json`; the existing HTML renderer is
the unchanged accepted dependency. Historical report/native/helper files were
not edited. The preparatory documents deliberately retain their original
source-only status; this note records the later execution.

All first attempts passed:

| Gate | Result | Actual exit | Guard seconds | Owned group |
|---|---|---|---|---|
| Exclusive source install | 12 files, reviewed pins match | 0 | 0.068967 | 87001, empty |
| Synthetic fallback checks | Four groups, 0.750 test seconds | 0 | 0.915375 | 89189, empty |
| Poppler page rasterization | One 120-DPI PNG | 0 | 0.425972 | 93004, empty |

Receipts and exact stdout/stderr are under `validation/` with prefixes
`reportlab-install-attempt01`, `reportlab-synthetic-attempt01`, and
`reportlab-raster-controller-attempt01`. All bounded guards recorded zero exit,
unchanged source hashes and an affirmative empty owned process group.

The positive fixture exercises the actual Markdown/HTML preprocessing, all
three reviewed equations, visible ASCII hyphens and preserved mathematical
minus, embedded glyphs, seven-column table, links, numbered/bulleted lists,
wrapped long code, PNG/caption and footer. Negative cases reject input drift,
unsupported structure, missing glyphs, custom numbering, stray structural
table text, insufficient figure label size and wrong copied assets. Actual
blank PDFs exercise zero/one/40/41-page and non-A4 boundaries.

The positive PDF contains **one actual A4 page**. Its full-page PNG was inspected
at original resolution: all content is present and readable with no observed
clipping, overlap or missing glyph. `validation/REPORTLAB_SYNTHETIC_QA.json`
binds the PDF, page image and reviewed code hashes. Synthetic fixtures and all
negative-case artifacts remain preserved under
`validation/reportlab-fixtures-attempt01/`.

This validates the small synthetic path, not the final report. The real edition
still needs finalized Google/distance sections, accepted physical-size paper
figures, complete tracked/copied evidence links, a fresh bounded render,
**actual total at most 40 pages**, and visual inspection of every final page.
No final report, browser or native solver was run. The browser/interactive-viewer
limitation remains separate; a successful PDF does not resolve it. The PDF skill
marker was not repeated.
