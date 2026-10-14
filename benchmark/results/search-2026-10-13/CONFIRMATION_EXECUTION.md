# Pending serial confirmation execution

Do not start a campaign until parent explicitly releases the native slot after the large pilot and its strict analysis finish. The frozen protocol is `benchmark/results/search-2026-10-13/ATTACHMENT_CONFIRMATION.md`. Validation-only execution uses `--preflight-only`; that path cannot create campaign files or launch capture.

The archived controller passed syntax validation, the [actual completed-large preflight](validation/confirmation-a-preflight.json), and [3 positive plus 36 malformed-input gates](validation/confirmation-controller-validation-v2.json), with zero native processes launched. The [test source](validation/validate_confirmation_controller.py) uses synchronized in-memory metadata variants to reach semantic failures instead of only stale-hash failures. The earlier 31-negative checkpoint is retained separately; the `v2` result is the final expanded suite. These checks do not consume a reserved graph or sampling seed.

To repeat read-only prerequisites before a separately authorized capture:

```sh
python3 -B benchmark/results/search-2026-10-13/run_attachment_confirmation.py --repo /Users/random_person/Desktop/karger-klein-tarjan --campaign a --preflight-only
```

Run campaign A, wait for exit, inspect strict analysis and the power audit, then run B. Each has 12 cases × 3 graph seeds × 2 sampling seeds × (5 timed repetitions + 1 checked warmup) × 5 solvers: 1,800 timed calls and 360 warmups. B reverses complete case order only; graphs repeat and are not new independent samples. No plotting, compiling, browser activity or instrumented work may overlap either capture.

```sh
python3 benchmark/results/search-2026-10-13/run_attachment_confirmation.py --repo /Users/random_person/Desktop/karger-klein-tarjan --campaign a --released
```

After A ends, check `attachment-confirmation-a-controller.json`, `attachment-confirmation-a-analysis/provenance.json` and `attachment-confirmation-a-power-audit/audit.json`. If successful, run:

```sh
python3 benchmark/results/search-2026-10-13/run_attachment_confirmation.py --repo /Users/random_person/Desktop/karger-klein-tarjan --campaign b --released
```

The controller invokes the frozen `run_mst_search.py` unchanged, using `bin/large_stack/mst_search`, graph seeds `1000039,1000081,1000099`, sampling seeds `401,503`, five repetitions, one warmup, a sampled 40 GiB process-group RSS ceiling and the existing two-second RSS polling rule. It refuses existing output names and checks the complete manifest and exact reversed order. Both manifests and the declaration must match their pre-large-pilot commit `d641ca8`; this binding is checked with read-only Git access before consuming any confirmation seed.

A requires the completed ten-case large capture and its successful strict analysis, exact 250 timed/50 warmup counts, and every registered raw/derived hash. The current complete C++ inventory, Makefile, six capture helpers and binary must match that capture. B additionally requires A's successful controller, strict 72-child/1,800-timed/360-warmup analysis and power audit; all associated hashes and source inventories must still match. A and B must use this identical controller source. Unknown or nonzero exit status, missing evidence, altered inputs or incomplete audits stop execution rather than permitting the next campaign.

It inherits the explicit earlier failed idle/AC sleep-assertion record into a separately named campaign record; it does not claim sleep prevention or retry assertions. Every approximately 50 seconds it logs swap/power observations and prints progress. Completed-case ratios use the documented median-over-repetitions, then sampling seeds, then graphs; these progress calculations remain provisional until the strict analyzer passes. All original warmups, losses and clock flags remain in capture artifacts. The power-history log is queried once after timing and remains ignored under the existing repository rule.

Source review and validation without launching native solvers are required before the first campaign. The controller is archived with this study and does not replace the strict capture validator. Its only potentially interfering live activity beyond the existing wrapper is lightweight sidecar reading, the six completed child CSVs when a new case finishes, and two environment commands per roughly 50 seconds. A and B use the identical monitoring rule. An incomplete sidecar write retains the last valid progress snapshot and marks it stale. The strict analyzer and power audit run only after the native wrapper exits. There is no performance-based stopping or case substitution.

Report each campaign separately. For each comparator and both wall/CPU, the declared rule requires paired case medians ≤0.90 at n=1,048,576 and 2,097,152 for each selected family, all graph-level medians <1 at those points, plus a smaller measured loss/tie to describe a bracketed onset. The descriptive rule is not a confidence interval or universal extrapolation. If capture/analysis fails, stop and preserve all partial evidence rather than reusing its output path. Cleanup asks the existing wrapper to terminate its owned native process group. If that does not finish within 30 seconds, the controller records that native processes may still be running: do not start another capture until the group is independently confirmed stopped.
