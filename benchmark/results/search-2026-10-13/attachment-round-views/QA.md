# Viewer validation and browser limitation

Python and native-data checks passed. Browser visual and interaction QA remains incomplete.

- 16 independent synthetic family fixtures and 72 independently reconstructed quotient states passed. Four malformed exports were rejected by the round builder.
- The unchanged base validator also passed its 16 fixtures, 14 malformed exports, four invalid tree certificates and embedded-JSON escaping check.
- All 16 archived actual d=2 exports passed a fresh independent Python cycle certificate. Every one of their 99 native trace stages matched the reconstructed counts and original-component size moments. The gate checks full quotient representatives directly from original edges on the synthetic fixtures, using a separate slow vertex-by-edge minimum scan.
- Four additional n=1,024, d=16, graph-seed-5009/sampling-seed-149 exports passed certificate and round-ledger checks. Their native traces were not separately captured; do not extend the 99-stage native agreement claim to those four examples.

The attempted CUA Chrome and in-app browser surfaces were unavailable. Native Safari was in active use; interaction stopped on a reported user state change without navigating a task page. No task tab was identified or closed.

The authorized isolated Playwright attempts used fresh temporary profiles. Cached Chromium headless-shell aborted before loading any page with `MachPortRendezvousServer bootstrap_check_in` error 141/SIGTRAP. Installed Google Chrome then aborted at startup with SIGABRT. The runner reported both processes exited and temporary-directory cleanup completed. These are launch failures, not evidence of a viewer JavaScript failure. No screenshot, browser rendering or successful interaction check is claimed.

Failure artifacts and the prepared bounded interaction gate are in [attachment-rounds-browser](../validation/attachment-rounds-browser/). The gate covers all rounds, terminal counts, previous/next, range keyboard input, both layouts, edge/rank filters, selection, rotation, reset, PNG download, narrow viewport, JavaScript errors and external requests. Run it only between native timing captures. Generated HTML makes no external requests by source design and CSP; this has not been verified by a successfully running browser here.

No native solver, benchmark boundary, fixture generator or captured helper was changed for these viewers. Source/input/output hashes are retained in [attachment_rounds_validation.json](../validation/attachment_rounds_validation.json); d=16 hashes are in [render_validation.json](../attachment-views-d16/render_validation.json).
