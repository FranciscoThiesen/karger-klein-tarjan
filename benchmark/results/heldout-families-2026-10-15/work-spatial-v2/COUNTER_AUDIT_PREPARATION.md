# Independent counter audit preparation

Prepared during the fresh diagnostic capture; not imported or executed yet.
The four focused synthetic test groups and actual audit require a separate
nonperformance release after capture and strict analysis complete.

`audit_counters.py` uses the strict loader only for provenance and lifecycle.
It independently rereads the raw JSON and reconstructs all four CSV tables,
without calling the collector's aggregation functions. It checks every one of
14,040 counter cells, 144 unmeasured hash-count nulls, 144 complete connected
replay chains and all round sums, 72 cumulative Q/U identities and all six
per-original-edge normalizations. Exact integer fractions are retained for the
432 normalizations; table floats must match their rounded decimal exports
exactly. The literal 72-input Cartesian set and 36 topology twins are checked.

The prepared tests exercise all 65 counter-domain checks and all 65 first-row
counter-table mutations, replay errors, zero/boundary query cases, row order and
truncation, duplicate JSON/CSV keys and nonfinite JSON. They run no native code.
Use the existing postcapture wrapper with exclusive attempt names for both
commands, retaining failure logs and known-empty owned-group evidence.

```sh
/usr/bin/python3 -B benchmark/results/heldout-families-2026-10-15/work-spatial-v2/test_audit_counters.py
/usr/bin/python3 -B benchmark/results/heldout-families-2026-10-15/work-spatial-v2/audit_counters.py --capture benchmark/results/heldout-families-2026-10-15/work-spatial-v2/capture-attempt01.json --analysis-dir benchmark/results/heldout-families-2026-10-15/work-spatial-v2/analysis-attempt01 --output-dir benchmark/results/heldout-families-2026-10-15/work-spatial-v2/independent-counter-audit-attempt01
```

No runtime, peak-memory or causal speedup claim follows from this counter audit.
