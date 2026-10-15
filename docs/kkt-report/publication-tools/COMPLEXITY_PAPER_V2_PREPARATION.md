# Complexity paper v2: source preparation

The original `plot_complexity_paper.py` and its historical review remain intact.
`plot_complexity_paper_v2.py` differs only in eight explicit font-size settings:
four normalized-figure captions increase from 8.3 to 8.5 points, model row labels
from 8.4 to 8.5, and three model captions from 8.2 to 8.5. All explicit text sizes
are now at least 8.5 points at the declared 7.05 by 9 inch figure size. Numeric,
provenance, output, plot ordering and all other layout logic remain unchanged.
This is a nominal-size source check, not a rendered readability claim; subsequent
PDF placement must not scale labels below the publication minimum.

The original preparation note describes its historical unexecuted state. A real
library build and schema smoke now exist, but the fresh complexity measurement,
analysis and figures still await their separate release. No figure is invented.

`test_plot_complexity_paper_v2.py` adds four small, unexecuted synthetic groups:

1. Complete 1,056-point, 288-cell, 24-choice paper input, reusing the existing
   24-curve analyzer fixture and real standalone `prepare()`.
2. Changed plotted values and a changed canonical-table copy, even with their
   output hashes recomputed.
3. Missing fit, entire clock, model, normalization clock or Google-choice
   coverage.
4. Changed source, standalone output or inherited input bytes, and a missing
   output-inventory entry.

Only `load_evidence()` is mocked. The test imports the actual standalone source
and exercises its complete preparation and the paper loader's exact-value and
hash checks. Placeholder image bytes are explicitly synthetic and unrendered;
they test binding only, never valid images or native provenance. No native call,
capture receipt, visual pass or independent arithmetic audit is fabricated.
The suite does not render or replace the required real native proof.

After root releases diagnostics, preserve a byte-identical installation of the
v2 adapter and its test in `ROOT/docs/kkt-report/publication-tools/`, recording
actual source hashes and installation equality. The future test command is:

```sh
/usr/bin/python3 -B "$kkt_guard" \
  --prefix "$kkt_study/validation/paper-v2-mocks-attempt01" --timeout 180 \
  --source "$kkt_root/docs/kkt-report/publication-tools/plot_complexity_paper_v2.py" \
  --source "$kkt_root/docs/kkt-report/publication-tools/test_plot_complexity_paper_v2.py" \
  --source "$kkt_pkg/plot_complexity.py" --source "$kkt_pkg/analyze_complexity.py" \
  --source "$kkt_pkg/test_analyze_complexity.py" -- \
  /usr/bin/python3 -B "$kkt_root/docs/kkt-report/publication-tools/test_plot_complexity_paper_v2.py" \
  --complexity-package "$kkt_pkg"
```

This command has not run. Independent source review passed after correcting the
synthetic CSV writer to use LF explicitly; see
`INDEPENDENT_COMPLEXITY_PAPER_V2_SOURCE_REVIEW.md`. No imports, tests, hashes or
renders were performed. Actual mock results, bounded rendering with zero
residuals and wide ranges, original-resolution visual inspection and actual
PDF-page/minimum-label QA remain separate gates. The final real figures
must retain every point, model and loss case and fit the report's 40-page limit.
