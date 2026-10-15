# Independent counter audit

Both first attempts passed after the complete 72-child capture and strict
analysis. The four mocked groups cover exact Q/U arithmetic and zero cases,
all 65 counter domains, round-chain consistency, every counter table cell,
ordering/truncation, duplicate JSON keys, non-finite numbers and CSV headers.

The actual audit independently reconstructed the four analysis tables from raw
JSON, using the collector only for provenance and lifecycle validation. It
matched all **14,040 counter cells** (216 solver rows × 65 fields), **144 null
comparator hash counters**, **144 replay chains / 1,188 rounds**, **72 cumulative
Q/U records**, **432 exact rational normalizations** and **36 topology twins**.
All raw inputs match their declared timing fingerprints. Analysis tables and
metadata were hashed before and after validation; frozen ancestors and other
audit inputs were rechecked before success.

The exact commands and source hashes are archived in
[mock receipt](counter-audit-mocks-attempt01.json) and
[actual receipt](counter-audit-actual-attempt01.json), with separate stdout and
stderr. Both wrappers exited zero, and independent process-table checks found
their owned groups 43120 and 43138 empty. No native solver was launched by
either audit. The [machine-readable result](independent-counter-audit-attempt01/audit.json)
also binds every validated input; its sibling CSV retains exact numerator and
denominator values. These checks validate logical work accounting and do not
establish a timing or memory-peak claim.
