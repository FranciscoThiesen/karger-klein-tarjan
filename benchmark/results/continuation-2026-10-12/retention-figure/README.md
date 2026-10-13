# Expected and observed contraction retention

`contraction_retention.png`, `.svg` and `.pdf` compare the conditional expected
residual with separately collected production-contraction traces for path/tree
hierarchies at `n=524288/1048576`, `m=16n`, intrusion zero, seeds17/42.
There are156 selected input-round rows and eight final-zero points. The source
also contains25 nonhierarchical `low_path` rounds; those are explicitly excluded
from this mathematical overlay and recorded in provenance. They remain in the
complete benchmark evidence.

The mathematical curve is an expectation over uniform distinct shortcut draws,
conditional on a backbone. It is not fitted to these two graph seeds. Shading
separates guaranteed backbone component pairs from expected occupied
shortcut-only pairs; it does not show an uncertainty band. The sum of input
counts measures whole-contraction edge volume, not elapsed time or each loop's
edge visits. See [MECHANISM.md](../MECHANISM.md) for the derivation.

`retention.csv` retains every observed/model pair; `edge_volume.csv` retains
every graph's total. `provenance.json` records hashes, indexing, exclusions,
numerical methods, term bounds and saturation error. `check_math.py` independently
evaluates145 small cases with exact integer binomial coefficients and rational
arithmetic; `math_validation.json` records the result. `agreement_summary.json`
records maximal observed deviations with their case, seed and round.

Reproduce from the repository root:

```sh
python3 benchmark/plot_continuation_retention.py \
  benchmark/results/continuation-2026-10-12/million_trace.csv \
  --output-dir benchmark/results/continuation-2026-10-12/retention-figure
python3 benchmark/results/continuation-2026-10-12/retention-figure/check_math.py
```

The PNG was opened and visually inspected after generation: all four panels,
labels, annotation boxes, legend and caption are readable, with no clipping or
overlap. This is static scientific-figure QA and is separate from the optional
HTML viewer's documented browser-policy limitation.
