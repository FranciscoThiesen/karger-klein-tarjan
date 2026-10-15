# Scoped source/declaration seed search

Source-only scan on 2026-10-15, before inspecting any active eighth timing observations. Proposed and now declared graph seeds are 19000013 and 19000043; sampler seeds are 3001 and 3011.

Two bounded read-only `rg` searches used the numeric-token expression:

```text
(^|[^0-9])(19000013|19000043|3001|3011)([^0-9]|$)
```

The first scanned `benchmark`, `kkt` and `test` under `/Users/random_person/Desktop/kkt-eighth-sampling`; the second scanned `/tmp/kkt-eighth-extension-prep`, `/tmp/kkt-hierarchical-metric-prep`, `/tmp/kkt-combined-prep` and `/tmp/kkt-eighth-sampling-prep`. Both were restricted to `*.py`, `*.cpp`, `*.hpp`, `*PROTOCOL.md`, exact `manifest.csv` and `*SEED*.md`. Both returned exit 1 and no matches. Raw timing CSVs, capture sidecars and private logs were outside these scopes. This package did not yet contain the proposed seed literals during the scan.

This supports freshness relative to those local source/declaration scopes, not global uniqueness or statistical independence. Rerun the same source-only check excluding this package before a later freeze if additional studies have been declared in the meantime. Do not change seeds after seeing this matrix's measurements.
