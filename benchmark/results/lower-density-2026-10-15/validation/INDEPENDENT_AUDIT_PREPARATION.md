# Independent lower-density arithmetic audit: source preparation

Prepared during the quiet Google Benchmark run. Neither this audit nor its six
mocked test groups has been imported, compiled, executed or hashed. No native
solver, partial timing output or current benchmark observation was read.

The two Python files adapt the independently validated density-32 distance
audit. They import only the Python standard library, not collector aggregators.
The literal new matrix is independently spelled out: density 16 has seven
sizes, density 8 has eight sizes; both families and both graph seeds are kept.

The audit independently reconstructs 60 children, 2,520 native outputs,
2,160 timed outputs, 360 warmups, 3,600 clock ratios, 1,980 summary medians,
150 point states, 490 earlier/later endpoint pairs and 20 crossover outcomes.
All 30 topology twins, all six solver rotations, both clocks, exact certificates,
raw concatenation, sampled resources, known-empty groups and the recursive
frozen native/helper/build artifact chain are checked. Exact `Fraction` values
drive ratios and crossover predicates; decimal comparison allows only the
existing narrow export tolerance. Densities never share a summary or bracket.

The tests independently enumerate the Cartesian raw matrix, use varied clocks
and durations, verify every numerical identity and median, and cover sustained
lead, late lead, reversal, recovered lead, parity, threshold equality, one-clock
epsilon and one-graph failures. Raw negatives preserve updated hashes and
concatenation where needed. Certificate version/type, source/artifact drift,
missing pins, table identity/value drift, unsigned integer and UTC domains are
also covered. Tests use temporary files and fake evidence only.

## Required before execution

After the quiet hold is explicitly released, install the package under the
existing eighth worktree, preserving source-preparation files. Independently
review and hash the final collector, protocol and manifest, then replace the
three explicit `None` declaration pins in `independent_numerical_audit.py`.
These are fail-closed placeholders, not wildcard bindings. Do not invent the
future freeze hash. Run the six mocked groups only after this binding step;
the declaration test intentionally requires the actual final source bytes.

Use exclusive archival receipts and preserve failed attempts. From
`/Users/random_person/Desktop/kkt-eighth-sampling`, the nonnative commands are:

```sh
/usr/bin/python3 -B benchmark/results/lower-density-2026-10-15/validation/test_independent_numerical_audit.py
```

After the entire released native capture, actual outer exit, empty-group proof,
and strict analysis have completed, use the actual precommitted freeze hash:

```sh
/usr/bin/python3 -B benchmark/results/lower-density-2026-10-15/validation/independent_numerical_audit.py \
  --capture benchmark/results/lower-density-2026-10-15/lower-density.json \
  --freeze benchmark/results/lower-density-2026-10-15/freeze.json \
  --freeze-sha256 ACTUAL_PRECOMMITTED_FREEZE_SHA256 \
  --analysis-dir benchmark/results/lower-density-2026-10-15/analysis \
  --output-dir benchmark/results/lower-density-2026-10-15/independent-audit-attempt01
```

Wrap each command separately using the existing nonnative archival guard at
`benchmark/results/heldout-families-2026-10-15/validation/run_postcapture_validation.py`,
with a fresh `--prefix`, `--source` for both audit files, and `--timeout 300`.
The guard is suitable for these nonnative operations only; it must not wrap the
native performance capture. A quiet release and the separate reviewed native
outer controller remain prerequisites for any performance execution.

The source-review receipt is independent of a future runtime PASS. No measured
crossovers, performance estimates or probability-effect estimates exist yet for
this declaration. Historical timings are not pooled.
