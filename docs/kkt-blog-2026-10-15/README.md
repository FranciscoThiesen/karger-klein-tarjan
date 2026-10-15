# Maybe KKT is not galactic after all

A focused, roughly 3,200-word article for chico.dev, with eight original figures and separately composed mobile versions. Prepared from the completed research; no new native timings were run for this editorial task.

- [Read the Markdown](POST.md).
- [Open the offline HTML preview](preview.html). It follows the site's narrow monospace layout and dark/light color palettes; color scheme follows the reader's system setting.
- [Copy-ready Jekyll package](chico-dev-kkt-post.zip), containing `_posts/` and `assets/`. Extract into a separate directory, then copy those two directories into the blog repository. The date is October 15, 2026; adjust it if publishing later.
- [Publication source](publish/_posts/2026-10-15-Maybe-KKT-Is-Not-Galactic-After-All.md).
- [Evidence and methods](downloads/EVIDENCE.md), [quantitative chart reproduction](downloads/kkt-blog-data.zip), and [checked concept diagrams](downloads/kkt-concepts.zip).

The article gives the strongest result early, explains KKT through a checked eight-vertex example, separates the original defects from later constant reductions, and uses the weight-shuffled twins to explain the crossover. Kruskal's wins, the lower-density reversal, and Google's N log N fits remain visible. The original 2022 code and January 2026 bitmap regression are explicitly distinguished.

## Publication and validation status

The site has not been changed or published. No PR was created. Research commits are on the local `codex/kkt-eighth-sampling` branch; a prior GitHub push was blocked by authentication. Before advertising native reproducibility from a public checkout, publish the associated research history. The included data downloads already reproduce the article's charts and diagrams independently of that checkout.

The article and evidence notes received an independent factual/source review. All eight desktop and eight mobile figure layouts were visually reviewed. Independent numerical checks recomputed the ratios and chart summaries from archived records. Isolated portable regeneration reproduced all 16 PNGs byte for byte; quantitative SVGs differed only in generated timestamps.

The Markdown was rendered with Kramdown 2.5.2 and its GFM parser. The builder checks eight figures, eight responsive sources, nonempty alt text, two tables, unique anchors, local links, publication-path rewrites, and ZIP hashes. The publication kit contains only accepted figures, scoped CSS, the post, and its three downloads; rejected figure layouts stay outside it.

The full HTML page has **not** received browser visual QA. Earlier local-file browser navigation was rejected by automatic approval review. No localhost, remote upload, alternate browser, or headless-browser workaround was used. The static page, generated figure pixels, and package structure were checked; those are distinct from a live Jekyll browser review.

## Rebuild the article package

From the repository root:

```sh
/usr/bin/python3 docs/kkt-blog-2026-10-15/scripts/build_blog.py
```

Requires Ruby with `kramdown` and `kramdown-parser-gfm`. This rebuilds `preview.html`, `publish/`, the publication ZIP, and `validation/build.json`; it does not run native solvers, fetch remote data, publish, or change benchmark records. It expects the accepted assets and portable downloads already present. Edit `POST.md`, then rebuild, rather than editing the generated Jekyll copy.

Chart generation from archived native evidence is in `scripts/plot_results.py`. The smaller downloaded replot command intentionally operates on the already exported tables. Its README explains the narrower scope. Concept checks and rendering are in `scripts/draw_concepts.py`.

The validation directory records exact hashes and scopes for factual, numerical, visual, and package checks. A passing chart replot is not evidence of a new benchmark run or a native rebuild.
