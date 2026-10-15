# Independent current-complexity arithmetic audit

This is **source-only preparation**. Neither script has been imported,
syntax-checked or executed. No current-candidate Google Benchmark timing exists
yet. The real library/build/schema-smoke gates, full frozen capture, strict
analysis, a released test run and an independently reviewed archival invocation
must all precede an actual audit. These files do not fabricate those receipts.

`audit_complexity.py` independently rereads the 24 declared curves, each with
99 native rows and 68 Google Benchmark JSON reports. The fixed declaration is
three families, two algorithms, two graph seeds and two sampler seeds, with
eleven sizes. The second graph seed reverses the size order; algorithm order
alternates by graph/sampler parity. No realizations are pooled into a fit.

The arithmetic check covers these canonical tables in full:

| Table | Rows | Independent evidence |
|---|---:|---|
| `means.csv` | 3,168 | Two native calls per mean, or each library iteration report's unit conversion; all four clocks |
| `model_fits.csv` | 1,152 | Six zero-intercept models, four clocks, 24 curves, full-eleven and upper-six windows |
| `google_selection.csv` | 24 | CPU-selected model, CPU coefficient/RMS, manual coefficient on that same model, and separately reconstructed manual RMS |

Native means use exact rational arithmetic before conversion to the canonical
float. Library means are independently converted from each iteration report's
milliseconds. Mean values, native rational numerators/denominators, all row
identities/order and selected labels must match exactly. The manual means must
also join their two native steady-clock calls under the original declared
1 ns / 5e-12 relative conversion allowance.

Each coefficient and normalized RMS is independently calculated from scaled
dot products with `math.fsum` and `math.log2`, rather than the analyzer's
sequential accumulation. Coefficients use a 2e-10 relative tolerance and no
absolute allowance; RMS uses the same relative tolerance plus 1e-12 absolute
allowance near zero. These are arithmetic comparison tolerances, not confidence
intervals or model-acceptance thresholds. All six residuals remain visible.

Discrete selections require special care: Google v1.5.2 selects on library CPU
**seconds**, in its fixed six-model order, with strict `<` replacement. The
canonical custom fits select on their own clock's nanosecond means. A second,
explicit source-order calculation reproduces those discrete decisions; the
numeric coefficient/RMS evidence remains independently recomputed using the
different scaled calculation. This independent reconstruction neither calls
original analyzer arithmetic nor uses its computed values. Google exports the manual coefficient under the selected
CPU model and only CPU RMS. The audit never invents an exported manual RMS or
calls an upper-six custom fit a built-in result. The pinned source version is
`73d4d5e8d6d449fc8663765a42aa8aeeee844489` (v1.5.2), as required by the real
schema-smoke/build proof.

The completed collector's `load()` is reused solely for original artifacts,
build/smoke/certificate identities, native exit/resource evidence and the full
frozen matrix. That strict loader internally invokes its existing analyzer
schema validator; this audit does not consume its arithmetic results. It then
independently rereads raw CSV/JSON and checks all declared row/name/clock/model
identities, fingerprints and topology twins. The hash-bound complete inputs,
all eight canonical outputs, provenance and audit source are checked before and
after reading and again before success. A failed audit keeps its exclusive
output directory and failed receipt.

Scope is deliberately narrow: the other three CSV tables (`size_summaries`,
`log_log_slopes`, `adjacent_slopes`) and `clock_flags.json`/`library_reports.json`
remain hash-bound but are **not independently arithmetically recomputed here**.
Ordinary library mean/median/stddev aggregate reports are schema-checked and
retained, not used as fit observations or independently recomputed. This audit
does not independently reimplement MST certificates, process monitoring, or
the already separate build validation. It cannot prove asymptotic complexity,
thermal stability, a universal expectation, or a crossover from fitted models.

Six prepared test groups contain a full synthetic 24-curve matrix and known
quadratic CPU/linear manual traces, exact rational projection checks, all four
clock identities and both windows, malformed schema/unit/policy negatives,
same-identity numerical and duplicate/missing-row mutations, hash changes
during reading/final checking, and scoped deep-package sibling imports with
path restoration after success, load failure and import failure. They import
only this audit and tiny synthetic modules, never the original analyzer or
collector. Their fixture does not claim to be a real native capture
or schema-smoke receipt. No tests have run.

After explicit nonperformance release, use an exclusive bounded outer log/exit
receipt for the mock command:

```text
/usr/bin/python3 -B /tmp/kkt-current-complexity-audit-prep/test_audit_complexity.py
```

Only after a genuine completed capture and analysis, use the actual installed
collector path and its frozen SHA-256 (not an invented placeholder digest):

```text
/usr/bin/python3 -B <INSTALLED_AUDIT>/audit_complexity.py \
  --capture <COMPLETED_CAPTURE_JSON> \
  --collector <FROZEN_PACKAGE>/collect.py \
  --collector-sha256 <ACTUAL_FROZEN_COLLECTOR_SHA256> \
  --analysis <COMPLETE_STRICT_ANALYSIS_DIRECTORY> \
  --output-dir <NEW_EXCLUSIVE_AUDIT_ATTEMPT> --released
```

The parent remains responsible for execution release, bounded archival
invocation, actual test/audit status and interpretation. No execution follows
from this source preparation.
