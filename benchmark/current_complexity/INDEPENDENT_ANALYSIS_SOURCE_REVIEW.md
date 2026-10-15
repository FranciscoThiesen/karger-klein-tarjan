# Independent analysis source review

**SOURCE REVIEW PASS**, 2026-10-15, by `/root/multigraph_candidate`. This is a manual source and primary-source review. No import, syntax check, test, library download, native execution or partial timing read occurred. Real schema/build validation and execution remain pending.

| Reviewed source | SHA-256 |
|---|---|
| `analyze_complexity.py` | `4ccd57d906c3fea7191f6819a6bf57e3aecdfa966b7eb0a11737752cdfc19c3f` |
| `test_analyze_complexity.py` | `67e519995e8f1db0d6ab5bf953417d0c67266aa190f6e32da047e3dbc8e7f255` |
| `ANALYSIS_PREPARATION.md` | `8f783b914a6048c9a5b1b08f20835f8cfa19a3ab2873500030640f53d5064eec` |

The literal 24-curve schedule, 99 calls/33 certificates per curve, 66 graph identities and 22 topology twins agree with the declaration. The independent native parser checks exact ordered identities, numeric domains, positive clocks and all callback certificates. One review finding was repaired: it now inspects every `complexity_certificate` marker and rejects unsupported versions or malformed prefixes instead of ignoring extra v2 markers. Typed specification and smoke-contract checks prevent bool/integer aliases. Native and library arithmetic is reread from raw evidence; the collector is used for provenance/lifecycle, not aggregation.

I checked the model order, zero-intercept least-squares coefficient, mean-normalized RMS, strict tie rule, CPU-selected model and same-model manual fit against upstream [complexity.cc](https://raw.githubusercontent.com/google/benchmark/v1.5.2/src/complexity.cc). The separately parsed coefficient unit and CPU-only exported RMS agree with [json_reporter.cc](https://raw.githubusercontent.com/google/benchmark/v1.5.2/src/json_reporter.cc). Name suffix, directed registration order, three ordinary aggregates and their repetition count agree with [benchmark_register.cc](https://raw.githubusercontent.com/google/benchmark/v1.5.2/src/benchmark_register.cc), [benchmark_runner.cc](https://raw.githubusercontent.com/google/benchmark/v1.5.2/src/benchmark_runner.cc) and [statistics.cc](https://raw.githubusercontent.com/google/benchmark/v1.5.2/src/statistics.cc). These source expectations still need a real linked smoke; no receipt is synthesized.

All four clocks and both fixed windows retain 3,168 means, 1,152 model fits, 1,056 size summaries, 192 log-log slopes, 960 adjacent slopes and 24 built-in selections. Native means retain exact rational numerators/denominators. The six-call native ranges are distinguished from three library two-call means. Library CPU is not forced equal to the narrower native CPU interval. All flags remain and are independently reconciled with the collector. Ordinary aggregates are retained/schema-checked but explicitly not claimed as independently reconstructed statistics or fit inputs.

Six prepared mock groups cover the separate Cartesian identities and rational arithmetic, a quadratic CPU/near-linear wall witness, known models and strict ties, domains/units/unsupported certificates, missing or duplicate reports, graph joins, hash drift and mandatory real-smoke binding. They have not run and cannot establish native timer/lifetime correctness. No further source blocker was found in this scope.
