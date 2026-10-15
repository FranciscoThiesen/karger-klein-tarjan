# Independent ReportLab fallback source review

Status: **PASS by source inspection only**, 2026-10-15. Reviewer:
`/root/multigraph_design`. No imports, tests, PDF rendering, browser use or
native execution were performed for this review. The distance performance
capture is active; all runtime gates remain deferred.

Reviewed current source identities:

| File | SHA-256 |
| --- | --- |
| `build_reportlab_pdf.py` | `b670b09cfef6e903ec3f739f52fe91c8e8da5446f124b27e8c4e37f70283ad73` |
| `test_reportlab_pdf.py` | `951309bd801fc71dbf33c121620683e9740a8a2f4e0607e48b3c0d5748f9931f` |
| `REPORTLAB_FALLBACK.md` | `fb0cc38352bdcc081b2be69f3023da2f739cbdd93376a1c8297a21a1d1184566` |

The adapter consumes the completed new-edition HTML and its original source,
asset and output digests. It binds the renderer, figure declaration and embedded
font files, then rechecks all inputs after layout. It preserves local/internal
links and simple main-body blocks; the generated contents navigation is the
only deliberate omission. PNG bytes must match both HTML and copied-asset
inventories. Figure placement uses declared physical width and minimum label
size, rejects labels below 8.5 pt and rejects a figure/caption too tall for one
page. Font glyph checks, fixed body/table/code sizes, actual A4 dimensions and
the actual one-to-forty-page gate are explicit. Exclusive output directories
retain failures instead of silently replacing an earlier edition.

Two source-review findings were repaired without execution. Table structural
non-whitespace is now rejected at table, group and row levels; unsupported list
start/reversed/type and item value/type attributes also fail instead of changing
the visible content or numbering. Eleven direct-parsed negative cases exercise
those checks without depending on an unrelated input-hash failure. The earlier
source/test/document version is preserved under
`before-structural-text-and-numbering-review/`.

The four prepared synthetic groups cover the actual accepted HTML path,
equations, glyphs, links, tables, PNG scaling, unsupported structures, input
drift, and actual PDF page-count/A4 boundaries. Their behavior remains
unvalidated until execution. A future bounded archival run, every-page visual
inspection, actual physical figure/font review, final tracked/copied-link gate,
and separate interactive-viewer/browser validation are still required. This
source review neither establishes a completed PDF nor replaces those gates.
