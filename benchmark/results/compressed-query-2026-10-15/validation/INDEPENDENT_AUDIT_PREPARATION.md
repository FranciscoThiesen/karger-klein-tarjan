# Independent compressed-query audit preparation

`independent_numerical_audit.py` is a standalone standard-library audit. It imports no collector or aggregation module. Preparation does not establish a performance result: no compressed timing capture has been audited yet.

The fixed audit expects 24 native children, 1,008 outputs (864 timed, 144 warmups), two graph seeds 8000009/8000023, scalar sampling seed 1801, six timed repetitions and one warmup. It reconstructs 864 all-solver compressed/reference clock ratios and 1,440 within-variant KKT/comparator clock ratios directly from raw child CSV integers. Exact `Fraction` arithmetic determines all 2,016 case/realization/marginal medians, ranges, win counts and 30 crossover classifications. CSV decimal comparison allows ordinary floating-point rounding; exported rational numerators/denominators preserve exact values. Both graph medians on both clocks must satisfy the declared endpoint rule.

It separately checks declared recursive artifact hashes, source inventory, verifier-only object differences, fixed scalar/default-reference proof metadata, the exact 24-child adjacent/reversed schedule, all 42 rows per child, solver rotation, fingerprints, four topology twins, certificates, native exits, resource logs, final empty groups, clock flags and exact child-to-combined CSV concatenation. This supplements the frozen collector's full compiler/recipe proof rather than replacing it. It makes no power-log coverage or verified sleep-inhibition claim.

Preparation checks passed:

- Five synthetic groups in `independent-audit-preparation-tests.py`: independent raw Cartesian pair identities/ratios, graph and singleton-sampler aggregation, duplicate/missing/foreign realization rejection, exact crossover thresholds (including a rational amount above 0.90), unsigned clock domains, explicit UTC, and strict table identity checks. No collector or native module was imported. Attempt 01 command/status/source hashes are in `independent-audit-preparation-attempt01.json`; output is in the matching `.log`.
- A read-only recursive declared-artifact hash audit of the completed compressed freeze and ancestors passed for 375 files. The receipt is `independent-audit-parent-proof-attempt01.json`. It did not execute a native binary or assess any timing data.

After the root releases post-capture analysis and strict analysis succeeds, run from the worktree:

```sh
python3 -B benchmark/results/compressed-query-2026-10-15/validation/independent_numerical_audit.py --capture benchmark/results/compressed-query-2026-10-15/paired.json --analysis-dir benchmark/results/compressed-query-2026-10-15/analysis --output-dir benchmark/results/compressed-query-2026-10-15/validation/independent-numerical-audit
```

Archive that invocation, output, status and source hash in a fresh attempt receipt. The audit refuses to overwrite its output directory. Preserve and investigate a failed attempt before retrying. Do not confuse synthetic preparation passes with the still-pending full raw-data audit.
