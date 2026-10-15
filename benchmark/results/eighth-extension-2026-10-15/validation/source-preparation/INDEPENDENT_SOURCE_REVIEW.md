# Independent source review

Reviewed by `/root/experiment_design` during the active paired eighth-sampling
performance hold. This is a source review only: no imports, syntax checks,
tests, builds, native calls, renders or partial timing reads were performed.

Reviewed the prepared collector, eleven mocked groups, protocol, manifest and
seed declaration. The only concrete finding was a protocol typo describing
the private acceptance predicate as `(rng() & 7) == 0`. The author corrected it
to `(rng() & 7) == 7`, matching the actual frozen header. No collector change
was needed for that correction.

No remaining source blocker was found:

- The full frozen parent proof runs without seed-global overrides and binds
  the exact eighth binary, source, objects, build recipe and ancestor evidence.
- The literal fourteen-case matrix, reversed second-graph order, local seeds,
  28 children and 1,176/1,008/168 output counts agree with the declaration.
- All fourteen topology twins require matching topology/order and distinct
  weighted fingerprints. The largest case remains at the existing n/m limits.
- Raw clocks, exact certificates, six-position balance, hashes, resource
  telemetry, known-empty groups and ordered concatenation remain checked.
  Guarded cleanup preserves prior unknown-exit state and restores SIGTERM.
- All 1,680 ratios and 140/280/168/336 summary counts are consistent. Exact
  rational crossover logic retains 70 points, 210 endpoint pairs and ten
  outcomes, requiring the lead at every larger measured size.
- The tests independently enumerate raw ratio identities and summary groups,
  all point/endpoint identities, threshold ties, opposite-clock/graph failures,
  reversals, raw schema/certificate corruption and lifecycle failures.

This does not establish executable correctness, source-installation readiness,
a favorable result or permission to run. After release, install only new
nonnative files, retain mocked-test attempts, confirm unchanged parent proof
and seed declaration, add the private power-log ignore patterns, prospectively
freeze, and wait for a separate quiet-capture release. The full result still
requires an independent raw audit and visual review.
