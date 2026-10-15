# Lower-density work mock validation

All 20 mocked groups passed on the first attempts. No native solver, build, work prepare/freeze or commit was executed. These are synthetic gates; no actual lower-density timing or diagnostic result is claimed.

| Suite | Groups | Wrapper seconds | Owned group | Actual exit | Empty group |
|---|---:|---:|---:|---:|---|
| collector | 9 | 4.599244 | 1029 | 0 | yes |
| outer | 6 | 0.211875 | 1031 | 0 | yes |
| audit | 5 | 0.292489 | 1030 | 0 | yes |

The nine collector/plot groups cover the complete 60-input synthetic schedule, full original-parent proof entry points, exact 11,700 normalizations, fingerprints/twins, native schema/certificates/rounds, per-input deadlines, RSS/unknown exits/poison, guarded cleanup, terminal failure retention and plot-table mutations. The six outer groups cover actual exit versus strict completion proof, literal schedule/counts, exclusive receipts, whole-interval deadlines, uncertain spawn/metadata interruption, and signal/timer restoration. The five independent audit groups reconstruct all raw counter cells, nulls, replay/query/root constraints, every canonical table and exact normalized values, plus import restoration.

Each exclusive guard receipt binds stdout/stderr and unchanged before/after source hashes. Logs were inspected; all wrappers returned actual exit 0 and recorded affirmative empty-group observations. All 14 installed files still match the byte-for-byte installation receipt. The independent audit remains a separate arithmetic implementation; it reuses strict load only for provenance/lifecycle.

Files: `work-installation-attempt01.json`, `work-{collector,outer,audit}-mocks-attempt01.{json,stdout,stderr}`, and `work-mock-validation-attempt01.json`.

Actual work prepare requires the future complete lower-density timing capture and its completed independent arithmetic audit. Root owns declaration/freeze commits and any separately released native diagnostic run.
