# Blog chart data

Accepted assets: `../../assets/quantitative-attempt04/`. Every chart has a 720-pixel desktop layout and an independently arranged 360-pixel mobile layout, SVG plus 2x PNG. Publication should select the mobile asset below 600 pixels. Earlier rendering attempts are validation history, not publication assets.

- `crossover.csv`: all seven density-16 sizes, ordered and shuffled weights, both clocks. `value` is the median of twelve paired KKT/retained-B ratios; `g1` and `g2` are six-trial graph medians. `minimum` and `maximum` retain every trial endpoint. Fraction strings retain the exact medians.
- `endpoints.csv`: all six algorithms at all four largest endpoints, both clocks, durations in nanoseconds. Every endpoint has 33,554,432 edges. The plot displays seconds rounded to three decimals; this table retains the canonical values and ranges.
- `endpoint_ratios.csv`: all five paired KKT/comparator ratios for those four endpoints, both clocks, with graph medians and ranges. A ratio of separate duration medians must not replace this statistic.
- `volume.csv`: both graph inputs for all thirty cases and both KKT/retained-B contraction-input counters. `count` is cumulative `contraction_edges`; `per_m` divides it by the original edge count. KKT sums recursive calls, retained B sums its full chain. These counts are not equivalent units of CPU cost.
- `complexity.csv`: all 264 native-process-CPU size summaries (three families, two algorithms, two graph seeds, two sampler labels, eleven sizes). Each summary contains six native calls. Retained B ignores the sampler label and repeats two distinct graph inputs. Graph 1 traverses sizes upward, graph 2 downward. No realization curves are pooled.
- `google_choices.csv`: all 24 exported Google Benchmark library-process-CPU model selections. These library clock intervals differ from the native-clock plot. All select N log N over the measured domain; this is not an asymptotic proof.
- `reversal.csv`: ordered density-8 paired ratios at its last three sizes, both clocks and full ranges.
- `partition.csv`: both ordered density-8, 4M graph inputs. `base` is twice the connected verifier-query volume plus twice the FBT edge count; `partition` is the exact remaining verifier-edge counter. This is cumulative work, not an elapsed-time decomposition. Graph 1 is seed 23000003; graph 2 is 23000029.

The producer checks its used files against completed independent audit inventories, independently recomputes all 1,980 lower-density timing summaries from integer calls, checks all sixty partition identities, and rebuilds all 264 plotted native CPU summaries from raw calls. It creates no new timing, model fit, trimming, or historical pooling. The separate independent numeric review and the visual review live in the blog `validation/` directory. `provenance.json` hashes the producer, inputs, literal CSVs and all figure assets. Its original-machine evidence paths are not a portable native rebuild claim.

Reproduce only in the full evidence checkout, with a fresh output attempt name:

```sh
/usr/bin/python3 -B docs/kkt-blog-2026-10-15/scripts/plot_results.py --attempt quantitative-new-attempt
```

The desktop/mobile plots select the wall clock for ratio narratives and show both clocks in the endpoint comparison. Their tables preserve CPU counterparts. Full study reports retain every family, comparator and measured size beyond these editorial views. Lines connect observed sizes; they do not estimate a continuous threshold or confidence interval.
