# Half/eighth work diagnostics: prepared and validated, capture pending

The fixed [protocol](PROTOCOL.md) and [freeze](freeze.json) are ready for root review and commit. No native diagnostic capture has been launched. This preparation used only source installation, synthetic mocks, completed-timing validation and artifact hashing; no native solver or performance run occurred. All owned validation processes exited zero and their groups were affirmatively observed empty.

The freeze SHA-256 is **`e9b556e7d92bb0c73597a185112170ed649752957e64a484f44770887a331d04`**. A [fresh-process full proof](freeze-proof-attempt01.stdout) checked 483 bound files and the exact 48-input/144-output schedule against completed `../eighth.json`, SHA `016bea1dfad7ed26299b1f029995ef351c16d68287dea3946c0bd53c7e79d899`. The same six cases, two graph seeds, two sampler seeds and two rates are retained regardless of timing outcomes. Each child certifies KKT and both contraction continuations, with two full comparator replays.

| Gate | Result | Actual exit / observed empty group | Evidence |
|---|---|---|---|
| Reviewed source installation | PASS, exclusive copies with matching hashes | No child process launched | [Installation receipt](install-attempt01.json) |
| Collector mocks | 13 groups PASS, 2.108 seconds | 0 / 47222 | [Receipt](mocks-attempt01.json), [test log](mocks-attempt01.stderr) |
| Independent counter-audit mocks | Six groups PASS, 1.327 seconds | 0 / 47248 | [Receipt](counter-audit-mocks-attempt01.json), [test log](counter-audit-mocks-attempt01.stderr) |
| Prospective freeze preparation | PASS | 0 / 47259 | [Receipt](prepare-attempt01.json), [output](prepare-attempt01.stdout) |
| Fresh full freeze proof | PASS, 483 bindings | 0 / 47274 | [Receipt](freeze-proof-attempt01.json), [output](freeze-proof-attempt01.stdout) |

All four guarded operations passed on their first attempts, with unchanged before/after source hashes. The collector/mock tool session was 56867 and the counter-audit/mock session was 85085; both were polled to actual exit zero. The preparation and fresh-proof commands completed with actual exit zero in their initial calls. No failed attempts or source repairs occurred during installation/validation. The original source-preparation notes remain historical; this README records the subsequent completed gates.

The native proof reconstructs all 43 instrumented compile/link commands and all 11 targets per variant, requires the original successful native/sanitizer/final-object gates, and checks the complete timing ancestor proof. It reuses the existing diagnostic executables without rebuilding:

| Policy | Existing `retention_work` SHA-256 |
|---|---|
| Half | `a933fe0d798a9b5722364d82a2778791cf7e8c738c701eccfb78a5d3f94cf852` |
| Eighth | `19146f6ae4453b200c7b76aff329e39c951ad534256e63ef48edac0ddeda1921` |

Seven non-KKT production objects and the driver main are physically shared. The shared main SHA is `b41d20f7be950c6b57f23f6f52708073b700566efda2f5b65ed4aa4a22c6058a`; only the KKT object selects the rate. Both policies use the same compressed verifier and one scalar engine word per visited sampling edge. No frozen timing/native/helper file changed.

After root reviews/commits this declaration and separately releases diagnostics, the exact capture command from the eighth worktree root is:

```sh
/usr/bin/python3 -B benchmark/results/eighth-sampling-2026-10-15/work/run_capture_attempt.py --released
```

The [source-reviewed native wrapper](INDEPENDENT_WRAPPER_SOURCE_REVIEW.md) writes exclusive `capture-controller-attempt01` artifacts and `capture-attempt01.json`, imposes its 7,200-second outer deadline, and requires final strict proof of all separately sessioned native groups. The collector retains its 40-GiB resource ceiling, two-second poll, bounded monitor/cleanup and 1,800-second child deadline. A completed sidecar alone is insufficient: actual outer exit zero and affirmative empty-group evidence remain required. The generic postcapture validation wrapper must never wrap this native capture because it labels its work non-native.

Strict work analysis and the [independent raw-counter audit](audit_counters.py) remain pending until all 48 diagnostic children complete. Expected outputs are 144 solver rows × 65 fields (9,360 cells, including 96 deliberately null comparator hash counts), 96 replay chains, 48 cumulative query/engine records and 1,560 half/eighth paired fields. Recursive work may legitimately differ across rates; preserve zero denominators, increases and decreases, and do not impose the earlier compression study's 61+4 equal-work identities. Instrumented durations and RSS are not algorithm performance measurements. The exact sequential commands and review links are preserved in [the postcapture handoff](POSTCAPTURE_HANDOFF.md).
