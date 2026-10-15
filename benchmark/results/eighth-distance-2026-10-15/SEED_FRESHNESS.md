# Scoped seed nonreuse check

Prepared source-only on 2026-10-15 before any new distance input execution.
Proposed graph seeds are **21000011, 21000041**; sampler seed is **3203**.

The exact-token command below returned exit1 with no matching file names.
The exit means no matches, not an execution failure. It inspected declarations
and source only; no native solver, import, test, build or graph generator ran.

```sh
cd /Users/random_person/Desktop/kkt-eighth-sampling
rg -l -w --glob 'run_*.py' --glob 'collect.py' --glob 'PROTOCOL.md' \
  --glob '*DESIGN*.md' --glob '*PROPOSAL*.md' --glob 'manifest.csv' \
  --glob 'freeze.json' --glob '*seed*.json' '21000011|21000041|3203' \
  benchmark docs /tmp/kkt-current-complexity-prep \
  /tmp/kkt-hierarchical-metric-prep /tmp/kkt-eighth-extension-prep \
  /tmp/kkt-combined-prep /tmp/kkt-eighth-sampling-prep
```

This is not a global uniqueness proof and does not assert statistically
independent PRNG streams. Recheck the same declaration scope before prospective
freezing, excluding the new distance declaration itself and retaining exact
scope/command/status. Seed changes require a new declared matrix before data.
