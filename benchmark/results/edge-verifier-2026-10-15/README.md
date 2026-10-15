# Retained rejected build attempt

The first direct Edge verifier correctness build used this preliminary artifact
directory. Its log records a compile-time rejection because the instrumented
build included the unchanged timing-only harness test, which explicitly forbids
work counters. No tests or performance workloads ran from this attempt.

Successful final evidence is in
`../edge-view-2026-10-15/validation/CANDIDATE_VALIDATION.md`. The six instrumented
suites and the separate noninstrumented harness gate preserve that restriction.
