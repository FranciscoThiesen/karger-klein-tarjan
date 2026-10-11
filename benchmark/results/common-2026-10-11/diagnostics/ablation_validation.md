# Ablation analysis validation

The analyzer accepted both complete 1,440-row timing matrices (`primary.csv` and `repeat.csv`) and the contraction traces for all 60 graphs in `trace.csv`. The independently collected common and shape work matrices passed their existing complete-matrix validators. For all 60 traces, input fingerprints and graph sizes after two contractions (or earlier termination) match the corresponding work observations for all three KKT seeds. Intermediate edge contents are not compared, and the timing CSV itself does not contain a per-call fingerprint.

`ablation_validation.py` is the portable archived parser/math test. It accepted complete synthetic matrices with known ratios and nested medians, and rejected **43 malformed cases**. These include missing and duplicate observations, invalid case dimensions/seeds/algorithms, incorrect order, failed validation, nonpositive/noninteger/overflow durations, missing trace graphs/rounds, broken trace chains, invalid contraction sizes and selected counts, and mismatched work fingerprints/root graph sizes. The work-validator bridge tests use minimal synthetic dictionaries; the real analyzer run separately invokes the full shared work validators on the real inputs. Exact logs are in `ablation_validation.log` and `ablation_analysis.log`.

Reproduce from the repository root:

```sh
python3 benchmark/results/common-2026-10-11/diagnostics/ablation_validation.py
python3 benchmark/analyze_ablation.py \
  --timing-csv benchmark/results/common-2026-10-11/diagnostics/primary.csv \
  --confirmation-csv benchmark/results/common-2026-10-11/diagnostics/repeat.csv \
  --trace-csv benchmark/results/common-2026-10-11/diagnostics/trace.csv \
  --common-work-csv benchmark/results/common-2026-10-11/work.csv \
  --shapes-work-csv benchmark/results/shapes-2026-10-11/work.csv \
  --output-dir benchmark/results/common-2026-10-11/diagnostics/ablation_analysis
```

Both rendered PNGs were visually inspected after generation: all 20 runtime cases and all seven trace families are present, labels/captions are readable, graph ranges and the 1× line are visible, and there is no clipping or overlapping content. The runtime plot's tick labels were improved to show 1.0× through 1.6× explicitly within its narrow logarithmic range. The corresponding SVG and PDF artifacts use the same figure objects. `git diff --check` passed.

The principal result is an attribution limit: continued production compaction has lower case medians in **18/20 cases in both runs**. KKT has a case-median lead in both runs only for `unbalanced_bipartite_16_n65536` (0.9894× and 0.9909×), with one confirmation graph above 1×. The largest 16-side bipartite case changes sides between runs. No case has a KKT lead on every graph in both runs.

This compares whole continuation strategies: production compaction repeated to completion versus KKT's sampling, verifier, recursion, RNG, and storage lifetimes. It does not isolate individual verifier instructions. The raw data, all individual losses, graph ranges, and algorithm-specific run drift are retained.
