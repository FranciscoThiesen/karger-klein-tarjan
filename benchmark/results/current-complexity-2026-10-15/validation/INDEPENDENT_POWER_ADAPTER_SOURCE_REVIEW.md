# Power-association adapter source review

Source-only PASS after the query/log provenance correction. Reviewed
`associate_power.py`, the collector's strict load and native row validator,
`audit_attachment_recovery_power.py`, and the underlying
`audit_mst_search_power.py` parser/correlator. No imports, tests, hashes, native
execution, power queries, or partial timing reads were performed for this review.

The adapter first requires the pinned collector's complete 24-curve proof and
2,376 native call rows. It requires a successful archived `pmset -g log` query,
strictly parses its receipt, pins the receipt before reading, and retains both
that initial digest and the receipt's log digest through the final recheck.
The corrected parser excludes wake-request records. The unchanged correlator
uses UTC endpoints; transient identity aliases are not published. Every native
field and row is retained, with only the six disclosed diagnostic fields added.
The emitted CSV is hash-bound in the audit receipt. No raw private power events
are copied into the published output.

This review establishes source consistency, not an executed audit or evidence
of successful sleep inhibition, complete log retention, stable thermals, or
host idleness. Actual postcapture execution and archived tool exit remain
pending. No additional numerical mock is requested for this narrow adapter:
its interval arithmetic is the unchanged, previously tested correlator.
