# New-edition renderer preparation

**Source only; unimported, untested and unrendered.** Prepared while another
native study runs. No browser, dependency installation or PDF authoring has
occurred for this renderer. Root has since completed the PDF skill's one-time
artifact-start marker before a separate work-figure PDF; **do not repeat it**
for this report. This does not replace the independent source review or later runtime
and every-page visual checks.

`build_current_report.py` is a focused adaptation of the historical report
builder. It never calls the old populator, graph exporter or synthesis renderer.
It accepts a finalized Markdown draft and explicit paths; refuses an existing
output directory; writes a new `REPORT.md`, self-contained-figure `report.html`,
copied `assets/`, and an optional `report.pdf`. Historical report files remain
untouched. Metadata records exact input/output/figure hashes, versions and the
command, with failed attempts retained.

## Offline equations

The current draft contains exactly three display formulas. Their reviewed
literal equivalents are:

| Original meaning | Offline Markdown/HTML text |
|---|---|
| Sufficient recurrence coefficients | A ≥ c / (1 − p), B ≥ 2c + A / (2p). |
| Distinct endpoint/ancestor queries | U ≤ min(Q, Σᵥ depth(v)) ≤ min(Q, B·h). |
| Internal nonpath chords | I_b = (c / b) · choose(b, 2) − (c − c / b). |

These are literal display translations, not a general symbolic parser. The
first preserves both denominator parentheses. The second sums depths over v.
The third expands only the notation for the binomial coefficient, not its
value or model. Primary output Markdown contains readable Unicode blockquotes,
so it does not depend on MathJax, KaTeX or a CDN. The receipt retains original
TeX and replacement text. Unknown/untranslated TeX fails before publication;
new formulas need a separate reviewed mapping. Page-scale glyph QA is still
required, including ≥, ≤, Σᵥ and the minus sign.

## Future invocation after root releases nonperformance rendering

Finalize the draft's evidence cutoff first. The current `/tmp` draft is not
automatically a publication source; later completed work may change it.
Archive this renderer and its source review under a new report-edition folder
or publication tools path without replacing any historical script.

The Python environment needs `Markdown`; PDF output additionally needs
`playwright`, an installed Chromium, and `pypdf`. Their actual availability and
versions remain to be checked after timing. No dependency installation is
authorized or performed by this prepared script.

Example **HTML/Markdown preparation**, deliberately not yet executed:

```sh
/usr/bin/python3 -B /tmp/kkt-current-report-publish-prep/build_current_report.py --source /tmp/kkt-current-report-draft.md --asset-base /Users/random_person/Desktop/kkt-eighth-sampling --repo-root /Users/random_person/Desktop/kkt-eighth-sampling --output-dir /Users/random_person/Desktop/kkt-eighth-sampling/docs/kkt-report/current-2026-10-15/attempt01 --historical-viewer /Users/random_person/Desktop/kkt-eighth-sampling/docs/kkt-report/graph-explorer.html --allow-external-local-links
```

The explicit final flag acknowledges the packed-study link in a separate
worktree. It causes a visible disclosure and metadata dependency list; this
is not a fully portable evidence bundle. Prefer copying that study's selected
reviewed publication evidence into the intended repository, updating the draft
link, and **omitting** the flag for the final edition. All within-repository
local links become relative to the new output; images are copied by hash.
Being under the repository directory is only a location check: a linked file
may be ignored, untracked, or omitted from a publication copy. Metadata therefore
never treats that location as verified bundle portability. Before publication,
check that each linked evidence file is tracked or explicitly copied into the
edition and test the resulting artifact outside its original checkout. Native
build receipts can still contain original-machine paths and objects; relative
report links do not make those proofs a portable rebuild bundle. Local ignored
executables should be named as local artifacts rather than published hyperlinks.
All original evidence files remain unchanged.

The optional `--historical-viewer` explorer is linked and labeled n256, graphseed42, sample seed0,
deduplicating contraction and half sampling. It is not embedded as a p8 trace.
Viewer data/behavior QA remains a separate acceptance check, even if a previous
receipt exists for an older artifact hash.

The separate optional `--current-viewer /absolute/path/to/verified-current-viewer.html`
links a new retained-parallel root-stage reconstruction. Its disclosure names
both ordered/shuffled n1024, density32, intrusion0 inputs, graph seed17000011,
sampler seed2801 and half/eighth root samples. It explicitly is not a full
recursive execution trace, a rerun of the half solver, or a timing/small-input
speed claim. Both viewer options can be supplied; neither changes the other's
labels or files. The current link is usable only after the new viewer's separate
native artifact/export proof, independent graph checks and browser QA pass.
The renderer binds the linked HTML's bytes but does not perform those proofs.
Its current source preparation is `/tmp/kkt-current-hierarchy-view-prep`;
there is no claim that a finished viewer already exists. Put the accepted
self-contained viewer inside the publication repository before linking it.

For the HTML and its printed PDF, text-node U+2010 through U+2015 dashes become
ASCII U+002D hyphens. Numeric/named character references to those code points
receive the same treatment. U+2212 mathematical minus remains unchanged.
URLs, IDs, HTML attributes, styles/scripts and existing figure bytes remain
unchanged; the primary Markdown retains its original typography. Metadata
records the policy and replacement count. Figures need their own page-scale
glyph/label QA; this text policy does not rewrite a bound plot.

For PDF, create a **fresh attempt directory** and add `--pdf`. Root has read and
announced the PDF skill and has already run its required marker once during
this task. **Do not run it again.** Use a bounded execution guard
and retain actual process exit/group receipts; the renderer itself does not
supervise an outer process deadline.

Print layout flows through section headings; it does not manufacture a page
per Markdown section or inherit hard-coded old navigation anchors. There is
no universal figure-height cap: new paper figures have explicit page-width
dimensions so a height cap cannot silently shrink their labels. Oversized
figures remain a page-layout failure to fix, not permission to clip. It waits
for fonts/images, blocks unexpected HTTP(S) resource requests, prints A4, and
checks the actual `pypdf` page count is **1…40 inclusive**. A failure keeps the
attempt and its failed metadata; choose a new output directory after repair.
Rendering success is labeled `rendered_pending_visual_qa`, never full QA PASS.

## Focused deferred checks

Before accepting a final artifact, validate these specific adaptation points:

- All three equations translate correctly; an unfamiliar or malformed equation
  is rejected. Inspect the rendered glyphs and fraction grouping.
- Check all six U+2010–U+2015 code points, their numeric/named references, and
  U+2212: visible dashes become ASCII, minus remains a minus, and link/asset
  targets remain byte-identical. Check the historical/current viewer sections
  separately and together against their own accepted artifact receipts.
- Refuse existing output directories, missing figures/links and unresolved
  placeholders. Preserve a failed PDF attempt rather than overwrite it.
- Confirm inline and reference-style evidence links, generated heading anchors,
  copied image counts, captions and initial/final input hashes. External local
  links require deliberate opt-in/disclosure; no relative link assumes a
  separate worktree will travel with a repository archive. Verify every local
  evidence path is tracked or explicitly included in the publication bundle;
  directory membership alone does not pass that check.
- Browser-inspect desktop/mobile HTML, image loading, text/table overflow,
  navigation and every linked viewer's actual controls/data labels. The
  renderer's PDF-load checks are not a browser-interaction or mobile QA result.
- Check final total PDF pages, then rasterize and visually inspect **every
  page**, including cover/references/appendices. Match final PDF/HTML/Markdown
  and raster hashes in a new edition receipt. Original-size chart QA does not
  replace page-scale legibility. The cap cannot be met by shrinking charts
  until unreadable or deleting loss cases.

The script's link rewriter intentionally targets this draft's ordinary inline
links/images and one-line reference definitions; unsupported syntax should be
reviewed before adoption rather than treated as a general Markdown-publishing
framework. Supplementary local-document fragment targets need final link QA;
same-page generated anchors are checked automatically.

The previous renderer, README and independent review are preserved unchanged
under `before-hyphens-current-viewer/`; their recorded review hashes describe
that version. This follow-up is still source-only. See
`PUBLICATION_FIGURE_PLAN.md` before a PDF attempt: wide standalone figure QA
does not establish readable labels when scaled onto A4.
