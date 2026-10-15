# Independent complexity arithmetic audit — source review

Source review PASS after two corrections. No imports, tests, builds, native execution, rendering or partial extension timing reads were performed. Actual mocks, build/schema evidence, capture and audit execution remain pending.

| Reviewed source | SHA-256 |
|---|---|
| `audit_complexity.py` | `e77c8d85beb9d19a9e01ff7f152d58dce9dd707ac6035fb4071335d3162175e9` |
| `test_audit_complexity.py` | `d0772196c91729c099faeb74a38a69b0dd338146ba337a55c6f12e6f05355ba6` |
| `README.md` | `4613ac06a5782bc5883e5b940618e495cc67a1215e651b0a01ba0e4ec6d6c345` |

The literal schedule, exact 99 native rows and 68 library reports per curve agree with the declared 24 curves. Four clocks produce 3,168 two-call means. Twenty-four curves, four clocks, two windows and six models produce 1,152 fits, plus 24 Google selections. Canonical row/header order agrees with the original analyzer; graph/algorithm/sampler joins and topology twins remain checked. Native means use exact fractions, library means use the declared per-report units, and every mean/identity must match exactly.

Scaled `fsum` projection independently reconstructs each zero-intercept coefficient and RMS normalized by the observed mean. The selected-label replay preserves the [pinned v1.5.2 source](https://raw.githubusercontent.com/google/benchmark/v1.5.2/src/complexity.cc) model order and strict comparison, selecting on CPU seconds and fitting manual time to that CPU-selected model. Custom window selections use nanoseconds separately. The independent coefficient/RMS calculation uses different summation and logarithm paths, with explicit comparison tolerances. CPU-only exported RMS is distinguished from reconstructed manual RMS. The known quadratic CPU/near-linear manual fixture and rational projection test target those distinctions.

Complete provenance and lifecycle validation is delegated to the checked collector; independent calculations consume raw CSV/JSON rather than its arithmetic results. The review caught and the author fixed a deep-package import-path failure: `provenance_load` now adds the checked collector's parent directory temporarily, restoring prior `sys.path` and its owned module name on success, load failure and import failure. A sixth synthetic group covers those cases. Metadata/docstrings now acknowledge that strict provenance loading indirectly imports the original analyzer validator, while independent arithmetic reuses none of its computed values.

Hash checks bracket input reads and are repeated before success. Output-table identity/numeric mutations, incomplete/duplicated curves and rows, incorrect units/model selections, nonfinite/duplicate JSON and changing artifact bytes are rejected by the prepared gates. Exclusive output and a failed receipt preserve an unsuccessful audit.

The scope remains deliberately limited: size summaries, log-log slopes, adjacent slopes, clock flags, library-report copies and ordinary library aggregate arithmetic are bound but not independently recomputed. The audit does not re-prove native certificates, build correctness, asymptotic complexity or crossover claims. Six prepared mock groups and the actual final data path remain unexecuted; no further source blocker was identified.
