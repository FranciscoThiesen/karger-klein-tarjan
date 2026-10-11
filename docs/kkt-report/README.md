# Report and visual artifacts

Read [Making KKT practical](REPORT.md), or open [the offline HTML edition](report.html)
in a browser. The [standalone 3D explorer](graph-explorer.html) contains all graph
data and code locally. The HTML files need no server, account, or internet connection.
Evidence links outside those files resolve in a repository checkout; the figures
and interactive graphs themselves remain usable when the HTML is copied elsewhere.

The write-up distinguishes source-level bounds, finite timing fits, measured
algorithm comparisons, and the continuation-strategy ablation. Its print companion
is generated at `output/pdf/kkt-practical-report.pdf`; the checked page count and
content hashes are in [render_metadata.json](render_metadata.json).

To regenerate after running the strict evidence analyzers:

```sh
python3 docs/kkt-report/build_graph_views.py
python3 docs/kkt-report/build_synthesis_figures.py
python3 docs/kkt-report/populate_report.py
python3 docs/kkt-report/build_report.py --pdf
python3 docs/kkt-report/verify_report.py --screenshots /tmp/kkt-report-qa
```

The input is the retained `benchmark/results/common-2026-10-11` analysis output,
plus explicitly referenced historical results. `REPORT.template.md` holds the
prose; `populate_report.py` fills the numerical tables and result interpretation.
Update those sources before regenerating `REPORT.md`. Report generation never
executes a timed algorithm. Run it outside measurement campaigns.

The generation environment used Python 3.9, NumPy 1.26.4, Matplotlib 3.9.4,
NetworkX 3.2.1, Markdown 3.9, Playwright 1.60.0 with Chromium 148, and pypdf 6.14.2. Install the
Chromium browser with `python3 -m playwright install chromium`. Static figures are
retained as PNG and SVG. Layout generation is deterministic; nonspatial graph
positions are explanatory layouts, while mesh positions derive from the actual
generator coordinates. Every drawing uses all vertices and edges of its stated
256-vertex instance.

Browser validation checks both editions across all seven families and five stages,
keyboard controls, desktop/mobile width, local images and links, and zero external
network requests. The PDF is additionally rendered and visually inspected page by
page. Those checks validate presentation; correctness of MSTs, contractions and
heavy-edge labels comes from the separate C++ certificates and oracles.
