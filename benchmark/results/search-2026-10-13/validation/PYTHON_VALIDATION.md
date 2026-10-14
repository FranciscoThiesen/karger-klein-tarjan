# Five-solver capture and analysis checks

The final runner and analyzer passed eight positive standard-library checks and
29 malformed-input checks, archived in [python_selftest_v2.json](python_selftest_v2.json).
[python_validation_v2.json](python_validation_v2.json) binds those checks to the
source and both pilot-manifest hashes. The original v1 records are retained.

The positive cases cover a complete synthetic capture with certificate and RSS
provenance; distinct lift-factor topology groups; nested graph/sampling medians
that differ from pooled medians; paired ratios that differ from ratios of
separate runtime medians; and a UTC correction that remains flagged and retained
while monotonic endpoints establish execution order. Malformed cases exercise
missing/duplicate calls, rotation and clock identities, certification, input
fingerprints, lifted fixture bounds, failed metadata, production source records,
stack profile, and resource observations. RSS mutations update the recorded log
hash before validation, so their rejection is semantic rather than a stale-hash
test. Both files also passed `py_compile` and `git diff --check`.

The first native integration attempt produced 30 correct native outputs but the
wrapper rejected its benign `generation_seconds=... reference_certificate_seconds=...`
diagnostic as though it were a malformed certificate. Its failed metadata and
child evidence remain under `native-smoke-timing*`. The fix recognizes certificate
markers at the beginning of a log line; v2 adds a positive regression case for
the diagnostic. No performance observations were selected from that failed run.

The fresh [native smoke retry](native-smoke-retry.csv) and its
[strict analysis](native-smoke-retry-analysis/report.md) passed with 25 timed calls,
five retained warmups, and 40 paired wall/CPU comparisons. This tiny run validates
integration and output semantics; it is not performance evidence for a graph
family. [Independent peer review](PEER_REVIEW.md) separately checked aggregation,
clock retention and protocol details.

The runner freezes C++ source, Makefile, binary, manifest and imported Python
helper hashes throughout capture. It inspects the native arm64 executable's
512 MiB stack before launching a child. RSS is a periodic process-group sum,
not a continuous memory peak; missing short-lived samples are recorded without
pretending that zero is an observed peak of the solver. Every call, warmup,
clock flag, sampled resource record and partial failure remains available.
