# Fixed complexity capture launcher — independent source review

Source review PASS; no blocking lifecycle, declaration or provenance defect identified. This is a manual source review only. No imports, mocked tests, native processes, library acquisition, build, rendering or partial extension-timing reads were performed.

| Reviewed source | SHA-256 |
|---|---|
| `run_capture_attempt.py` | `ce0c3e1b835c940110f9c2695a48b79497fdb57d3c669d8afe7d15c5c8d9721e` |
| `test_run_capture_attempt.py` | `04adc1c974d8519f4ec3d87da0da1e7def00d115f50bb8a379e5b44573563694` |
| `CAPTURE_PREPARATION.md` | `f11fbdbe6bfb7396475beedd5e03c398adf7b5424cf7fc69e350fe9d3b0ecf50` |

The literal 24-curve schedule agrees with the reviewed collector: three families, two graph seeds, two sampler seeds and two algorithms, preserving ascending/descending graph-confounded size order and balanced algorithm order. Every curve contains eleven sizes and three callbacks with one warmup plus two timed solves: 2,376 raw calls, 1,584 timed and 792 warmups. The supplied future freeze digest, fixed eleven-size ladder, 3,600-second curve deadline, 40GiB rule and full artifact proof are required before launch. No future successful freeze or smoke evidence is invented.

The archival launcher uses the persistent `benchmark/current_complexity` package and a fresh exclusive attempt. Its 87,000-second complete-interval ceiling is an upper bound, not a runtime prediction. A late observed zero exit fails; fresh strict reload is bounded by the remaining interval and final elapsed time includes log hashing. Actual subprocess status and complete strict reload are both required. The 24 child identities/statuses/empty-group proofs are checked; an empty outer Python group alone never clears detached native uncertainty. Source/input hashes are retained and rechecked, and the complete collector-bound inventory is merged without conflicting digest replacement.

Repeated SIGTERM is suppressed during bounded outer cleanup, previous signal handlers/timers are restored, and uncertainty is set before Popen. Failures preserve output and never silently retry. Five focused mocked groups are prepared, including wrong freeze/count/identity, nonzero status, failed strict proof, reused outputs, late intervals and cleanup/timer restoration. These tests and actual lifecycle behavior remain unexecuted. Successful capture would still require the separate independent fit analysis and visual gates before reporting complexity findings.
