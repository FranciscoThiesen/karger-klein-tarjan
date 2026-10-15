# Independent source review

Reviewed on 2026-10-15 by `multigraph_design` while the separate held-out
performance capture was active. **Source review passed; no import, syntax
check, test, preflight, freeze or native run was performed by this reviewer.**
No partial held-out timing evidence was read. No reviewer-owned process remains.

Reviewed `benchmark/run_larger_hierarchy.py`, all ten groups in
`benchmark/test_larger_hierarchy.py`, and this study's protocol, manifest,
README, seed-freshness and feasibility notes. The local CSV writer header fix
and final preparation-neutral docstrings were included. No blocking source
defect was found.

- The complete unchanged compressed parent proof is checked before inherited
  artifacts are accepted. The new command and row validators use explicit
  local seeds, with no parent-module seed mutation.
- Six fixed cases, two graph seeds and one sampler produce 12 children and
  504 outputs: 432 timed and 72 checked warmups. Both graph orders, all six
  solver positions, six topology twins and nonidentical twin weights are
  enforced. Canonical table counts are 720/60/120/72/144.
- Exact integer-endpoint Fractions determine all four graph/clock medians at
  each size. All 30 points, 30 earlier/later pairs and 10 summaries remain.
  A strong bracket requires an earlier strict loss, an upper ratio at most
  0.90 everywhere, and strong leads at every larger measured point. Ties,
  reversals and leads already present at the smallest size remain distinct.
- Capture and reload preserve raw certificates, exact concatenation, clocks,
  source/build proof, bounded RSS evidence and a final known-empty group.
  First failure, poisoned sampling or an unknown group exit prevents another
  launch. Synthetic tests cover corrupted raw rows and certificates even
  when hashes or the combined CSV are updated consistently.
- Independent numerical test expectations are enumerated from raw identities
  with differing wall/CPU values, rather than derived from collector-produced
  pair rows. Boundary/reversal tests exercise the exact crossover rule.
- The 4M case exactly reaches existing inclusive n/m limits. The source and
  completed-study memory calculations are plausible planning evidence, not a
  fit guarantee; no ceiling, domain, certificate or solver relaxation is
  proposed. Failure must remain a reported outcome.

Execution gates remain pending: owner and independent mocked suites, final
artifact/fresh-seed proof, a prospective committed freeze, and a separate root
release. This receipt does not authorize performance execution or establish a
measured crossover, asymptotic bound or memory peak.

## Cleanup follow-up review

The later, still-unfrozen cleanup hardening and eleventh mocked group were
independently source-reviewed on the same date. No blocker was found. The
helper matches the separately reviewed combined collector: it marks exit
unknown before cleanup, ignores repeated SIGTERM only during the bounded
cleanup operation, records cleanup exceptions, restores the prior handler,
and clears unknown only with affirmative native-exit and empty-group proof.
A prior unknown remains unknown. The capture still records the original
failure and stops before another child.

The new mocked group checks cleanup-raised interruption, the ignored-handler
boundary without sending a real signal, failed sidecars, one-child stopping,
prior-unknown preservation and signal-handler restoration. The explicit
`signal` import and updated protocol/README agree. There are now eleven
prepared groups; none was imported or executed during this review. Frozen
ancestor helpers and the active held-out study remain untouched. No
reviewer-owned job is active.
