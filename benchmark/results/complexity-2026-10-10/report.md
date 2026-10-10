# Measured complexity diagnostics

Validated 180 logical-work observations (20 graph cases × 3 graph seeds × 3 KKT seeds) and 378 raw timing records (126 benchmark instances × 3 repetitions). Each timing record averages exactly three invocations, cycling KKT seeds 0, 1, 7: 1,134 timed calls total. All measured MST outputs passed the harness's checks; the work CSV records `pass` and the timing JSON contains no benchmark errors.

Work and timing summaries use arithmetic means: mean across sampling seeds or repetition batches within each graph, then mean across graph seeds 17, 42, 999. Every graph receives equal weight. The three seeds are a small empirical sample, not an exact expectation. Graph ranges are descriptive min/max values, not confidence intervals. Repeated timings are not additional independent graphs.

## Counted work

| Family | Events/N at n=1,024 | Events/N at n=262,144 | Change | Power p, full / upper half |
|---|---:|---:|---:|---:|
| Random, m = 4n | 19.568 | 34.947 | 1.786× | 1.103 / 1.055 |
| Random, m = 32n | 13.407 | 40.779 | 3.042× | 1.208 / 1.165 |
| Star | 8.000 | 8.000 | 1.000× | 1.000 / 1.000 |
| Hierarchical path | 36.568 | 36.223 | 0.991× | 0.999 / 0.999 |

## Uninstrumented manual time

| Family | Algorithm | ns/N at n=1,024 | ns/N at n=65,536 | Power p, full / upper half |
|---|---|---:|---:|---:|
| Random, m = 4n | KKT | 45.915 | 119.834 | 1.222 / 1.157 |
| Random, m = 4n | Kruskal | 17.332 | 45.158 | 1.215 / 1.102 |
| Random, m = 32n | KKT | 24.365 | 283.352 | 1.573 / 1.744 |
| Random, m = 32n | Kruskal | 46.837 | 58.866 | 1.052 / 1.058 |
| Star | KKT | 15.942 | 20.191 | 1.060 / 1.081 |
| Star | Kruskal | 6.888 | 22.856 | 1.345 / 1.244 |

KKT / Kruskal ratios below divide the arithmetic mean times; they are not means of paired ratios. Values below 1 favor KKT. Losses are retained.

| Family | Smallest-size ratio | Largest-size ratio | Range over all seven sizes |
|---|---:|---:|---:|
| Random, m = 4n | 2.649 | 2.654 | 2.222–2.654 |
| Random, m = 32n | 0.520 | 4.814 | 0.520–4.814 |
| Star | 2.315 | 0.883 | 0.883–2.456 |

## Interpretation and limits

- Input size is `N = n + m`. Each family has fixed density, and fits never pool families. The counter window spans n=1,024…262,144 (five points); timing spans n=1,024…65,536 (seven points). Upper-half fits use the largest three and four points respectively.
- The four fixed models are `cN`, `cN ln N`, `cN (ln N)^2`, and `cN²`, each fitted by least squares in original units with zero intercept. `rmse_over_mean_observed` divides the original-unit RMSE by the mean observed cost; `pointwise_relative_rmse` is the RMS of each point's relative residual. The free-power model fits `ln cost = ln c + p ln N`. Both fitting objectives and all model errors are retained; no best fit is declared to be an actual Big-O bound.
- Local slopes compare adjacent arithmetic means. Curvature, short windows, cache and memory effects, allocation, and timing noise can change effective exponents. Flat work/N is evidence about the counted work on these fixtures, not a proof of expected linear time on all graphs.
- The work proxy adds distinct logical events: loop visits, table writes, explicit initialization slots, edge materializations, and hash API items. It can count a visit and a copy separately. It excludes hash probes/collisions/rehashing, allocator internals, implicit growth copies, deallocation work, cache misses, and CPU instructions. Recursive input volume is a separate diagnostic and is not added again to the proxy.
- Star and hierarchical-path fixtures are structural controls. The star finishes on its first contraction, so KKT seed labels do not create different execution paths there. The hierarchical path probes repeated recursive contraction; it has logical counters only in this protocol.
- Runtime measures the common edge-list boundary, including KKT input conversion and temporary input destruction. Fixture generation, oracle/certificate work, result checks, and returned-result destruction are outside manual timing. Counter collection runs separately; time/work combines matched fixture sizes and is a diagnostic ratio, not the latency of a single operation.
- Google Benchmark 1.5.2 chooses its automatic Big-O model from CPU time, then fits manual time to that same model. Builtin rows are preserved in `builtin_complexity.json`, separately from the independent manual-time fits. The library's CPU-frequency metadata is not used. These timings are not automatically combined with earlier benchmark protocols.
- Benchmark instances run in registration order, without randomized algorithm order or a paired timing schedule. Order, warm-cache behavior, thermal drift, and clock noise can affect comparisons. Three repetition batches provide repeated measurements, not statistical certainty. The build and host protocol must be taken from the accompanying experiment metadata, not inferred from older Make-based measurements.

## Artifacts

- `work_summary.csv` and `graph_work_summary.csv`: overall and per-graph arithmetic counter means.
- `timing_summary.csv`, `graph_timing_summary.csv`, and `timing_repetitions.csv`: means and normalized raw timing records.
- `effective_exponents.csv` and `model_fits.csv`: adjacent slopes and every finite-window fit.
- `work_per_input.{png,svg,pdf}`: counted work components divided by input size.
- `normalized_costs.{png,svg,pdf}`: recursive volume, runtime/input, and runtime/work proxy.
- `effective_exponents.{png,svg,pdf}`: local work and runtime slopes.
- `builtin_complexity.json`: 36 builtin Big-O/RMS records, retained without using their selected models.
