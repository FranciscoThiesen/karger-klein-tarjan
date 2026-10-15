# Current-candidate complexity analysis — source preparation only

`analyze_complexity.py` and `test_analyze_complexity.py` have been written but have **not been imported, syntax-checked, tested or run**. They provide no timing, native API, library availability or complexity result. The active eighth study and its frozen artifacts are untouched.

The analyzer accepts only the declared 24 curves. It calls the source-hash-bound collector's `load()` for the complete parent/build/native-group proof, then independently rereads every raw CSV, callback certificate and untouched Google Benchmark JSON. It rechecks hashes before/after reads and after analysis, rejects duplicate JSON keys/nonfinite values, and refuses to overwrite an output directory. A genuinely executed schema-smoke receipt must bind the exact driver, binary, library and analyzer sources, the pinned Google Benchmark commit, real smoke artifacts, empty groups, and the exported `SCHEMA_CONTRACT`. The receipt is a future release gate; none is fabricated here. `validate_build.py`, the `build_library_main.py` producer and their focused mock fixtures now exist as unexecuted source preparation. Actual library acquisition/build, real final-binary schema receipts and all runtime validation remain absent prerequisites; a bounded archival outer invocation is also required before the producer can run. The earlier analysis-source review's document hash identifies the prior preparation wording; analyzer and analysis-test source semantics are unchanged by these status corrections.

The source-declared library format is based on upstream [JSON reporter](https://raw.githubusercontent.com/google/benchmark/v1.5.2/src/json_reporter.cc), [complexity fitting](https://raw.githubusercontent.com/google/benchmark/v1.5.2/src/complexity.cc), [statistics](https://raw.githubusercontent.com/google/benchmark/v1.5.2/src/statistics.cc), and run-name source. Each curve is expected to contain 33 iteration reports, 33 ordinary aggregate reports, and one BigO/RMS pair. Ordinary reports are in milliseconds; the coefficient row's separately declared unit is nanoseconds. RMS exports CPU only. These exact field/name/order/unit expectations remain smoke-dependent: a mismatch must stop validation and prompt a reviewed correction before freezing or capturing, not trigger permissive fallback parsing.

The six zero-intercept model rows are retained for every clock and window. Model order is constant, log₂N, N, Nlog₂N, N², N³; strict improvement replaces the current best, retaining the earlier model on equal scores. Google reconstructs its selection from library CPU times in seconds, and fits manual time using that CPU-selected model. Its coefficients and CPU RMS must agree with the reconstruction. The analyzer reports reconstructed manual RMS separately, because it is not exported. Floating-point tolerances are declared in `SCHEMA_CONTRACT`; native two-call means also retain exact rational numerators/denominators. Independent per-clock selections use nanoseconds and are explicitly separate diagnostics; a machine-rounding disagreement near a model tie cannot silently relabel Google's reported choice.

The output counts are fixed:

| Table | Rows | Meaning |
|---|---:|---|
| `means.csv` | 3,168 | 24 curves × 11 sizes × 3 repetitions × 4 clocks |
| `model_fits.csv` | 1,152 | 24 × 4 × 2 windows × 6 models |
| `size_summaries.csv` | 1,056 | Six native calls, or three library two-call means, per size/clock |
| `log_log_slopes.csv` | 192 | Descriptive full-eleven/upper-six log regressions |
| `adjacent_slopes.csv` | 960 | Ten adjacent observed size pairs per curve/clock |
| `google_selection.csv` | 24 | CPU-selected model and both same-model coefficients |

The full window has 33 two-call means and the predetermined upper-six window has 18. N is the actual n+m. Clock flags and all source rows remain; no trial is removed or adjusted. Full library context and ordinary aggregate rows are retained, but those ordinary aggregate numbers are not fit inputs or claimed as independently recomputed summaries. Native process CPU and library process CPU cover different timer envelopes and are not forced equal. Raw-call ranges are never assigned to the three library means.

Six prepared synthetic groups cover the independently spelled schedule/fingerprint twins; malformed calls/certificates/unsupported versions and retained clock flags; complete library identities, units and CPU/manual model distinction; rational least squares, all six known models and strict ties; independent Cartesian mean/model identities and all table cardinalities; and hash drift, conflicting inventories, typed mandatory smoke declarations and artifact substitution. Synthetic data is clearly labeled and cannot establish the real native timer integration, result lifetime, source/library correctness or group cleanup. Collector lifecycle tests remain separately owned.

After root releases execution, required next steps are source review, actual synthetic execution with exclusive attempts, a validated library build and real linked correctness/schema smoke, full provenance/freeze checks, and a separate quiet performance release. A possible future command is:

```sh
python3 -B analyze_complexity.py --capture /absolute/capture.json \
  --collector /absolute/collect.py --collector-sha256 REVIEWED_SHA256 \
  --output-dir /absolute/new-analysis-attempt01
```

This command is illustrative and has not run. All observations would remain finite-range diagnostics, separate by family, algorithm, graph seed, sampler seed and clock. They cannot prove an asymptotic bound, establish a universal expectation or retroactively turn the old revision's Google Benchmark fits into a current result.
